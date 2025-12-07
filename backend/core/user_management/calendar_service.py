import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta, date
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from backend.core.event_bus.kafka_manager import EventBus, get_kafka
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.cache.redis_manager import init_redis

logger = logging.getLogger(__name__)

class EventType(Enum):
    MEETING = "meeting"
    TASK = "task"
    REMINDER = "reminder"
    DEADLINE = "deadline"
    AGENT_SCHEDULED = "agent_scheduled"
    TEAM_EVENT = "team_event"
    PERSONAL = "personal"
    WORK = "work"

class EventStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"

class RecurrenceType(Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

@dataclass
class CalendarEvent:
    id: str
    user_id: int
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    event_type: EventType
    status: EventStatus
    created_at: datetime
    updated_at: datetime
    location: Optional[str] = None
    attendees: List[str] = None
    recurrence_type: RecurrenceType = RecurrenceType.NONE
    recurrence_end: Optional[datetime] = None
    reminder_minutes: int = 15
    is_all_day: bool = False
    color: str = "#3B82F6"
    metadata: Dict[str, Any] = None
    agent_id: Optional[str] = None
    team_id: Optional[str] = None

@dataclass
class CalendarSettings:
    user_id: int
    timezone: str = "UTC"
    working_hours_start: str = "09:00"
    working_hours_end: str = "17:00"
    working_days: List[int] = None  # 0=Monday, 6=Sunday
    default_reminder_minutes: int = 15
    auto_schedule_agent_tasks: bool = True
    allow_agent_scheduling: bool = True
    team_calendar_visibility: bool = True
    created_at: datetime = None
    updated_at: datetime = None

class CalendarService:
    """Service for calendar management and scheduling"""
    
    def __init__(self):
        self.event_bus: Optional[EventBus] = None
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.redis_client = None
        self._initialized = False
        self.events: Dict[str, CalendarEvent] = {}
        self.settings: Dict[int, CalendarSettings] = {}
    
    async def initialize(self):
        """Initialize calendar service"""
        if self._initialized:
            return
        
        try:
            kafka_manager = await get_kafka()
            self.event_bus = kafka_manager.event_bus
            self.ai_service_manager = await get_ai_service_manager()
            self.redis_client = await init_redis()
            
            # Subscribe to calendar events
            await self._setup_event_handlers()
            
            self._initialized = True
            logger.info("Calendar service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize calendar service: {e}")
            raise
    
    async def _setup_event_handlers(self):
        """Setup event handlers for calendar events"""
        self.event_bus.register_handler("calendar.event_created", self._handle_event_created)
        self.event_bus.register_handler("calendar.event_updated", self._handle_event_updated)
        self.event_bus.register_handler("calendar.event_deleted", self._handle_event_deleted)
        self.event_bus.register_handler("agent.task_scheduled", self._handle_agent_task_scheduled)
        
        # Subscribe to topics
        await self.event_bus.subscribe_to_topic("calendar.event_created")
        await self.event_bus.subscribe_to_topic("calendar.event_updated")
        await self.event_bus.subscribe_to_topic("calendar.event_deleted")
        await self.event_bus.subscribe_to_topic("agent.task_scheduled")
    
    async def create_event(
        self,
        user_id: int,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        event_type: EventType = EventType.PERSONAL,
        location: Optional[str] = None,
        attendees: List[str] = None,
        recurrence_type: RecurrenceType = RecurrenceType.NONE,
        recurrence_end: Optional[datetime] = None,
        reminder_minutes: int = 15,
        is_all_day: bool = False,
        color: str = "#3B82F6",
        metadata: Dict[str, Any] = None,
        agent_id: Optional[str] = None,
        team_id: Optional[str] = None
    ) -> CalendarEvent:
        """Create a new calendar event"""
        if not self._initialized:
            await self.initialize()
        
        event_id = f"event_{user_id}_{datetime.utcnow().timestamp()}"
        
        event = CalendarEvent(
            id=event_id,
            user_id=user_id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            event_type=event_type,
            status=EventStatus.SCHEDULED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            location=location,
            attendees=attendees or [],
            recurrence_type=recurrence_type,
            recurrence_end=recurrence_end,
            reminder_minutes=reminder_minutes,
            is_all_day=is_all_day,
            color=color,
            metadata=metadata or {},
            agent_id=agent_id,
            team_id=team_id
        )
        
        self.events[event_id] = event
        
        # Publish event creation
        await self.event_bus.publish_event("calendar.event_created", {
            "event": asdict(event),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Calendar event created: {event_id} for user {user_id}")
        return event
    
    async def update_event(
        self,
        event_id: str,
        user_id: int,
        **updates
    ) -> Optional[CalendarEvent]:
        """Update a calendar event"""
        if not self._initialized:
            await self.initialize()
        
        if event_id not in self.events:
            logger.error(f"Event {event_id} not found")
            return None
        
        event = self.events[event_id]
        
        # Check permissions
        if event.user_id != user_id:
            logger.warning(f"User {user_id} attempted to update event {event_id} without permission")
            return None
        
        # Update fields
        for field, value in updates.items():
            if hasattr(event, field):
                setattr(event, field, value)
        
        event.updated_at = datetime.utcnow()
        
        # Publish event update
        await self.event_bus.publish_event("calendar.event_updated", {
            "event": asdict(event),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Calendar event updated: {event_id}")
        return event
    
    async def delete_event(self, event_id: str, user_id: int) -> bool:
        """Delete a calendar event"""
        if not self._initialized:
            await self.initialize()
        
        if event_id not in self.events:
            return False
        
        event = self.events[event_id]
        
        # Check permissions
        if event.user_id != user_id:
            logger.warning(f"User {user_id} attempted to delete event {event_id} without permission")
            return False
        
        # Publish event deletion
        await self.event_bus.publish_event("calendar.event_deleted", {
            "event_id": event_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        del self.events[event_id]
        logger.info(f"Calendar event deleted: {event_id}")
        return True
    
    async def get_user_events(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[EventType] = None,
        team_id: Optional[str] = None
    ) -> List[CalendarEvent]:
        """Get events for a user within a date range"""
        if not self._initialized:
            await self.initialize()
        
        user_events = []
        
        for event in self.events.values():
            # Filter by user
            if event.user_id != user_id:
                continue
            
            # Filter by team if specified
            if team_id and event.team_id != team_id:
                continue
            
            # Filter by event type if specified
            if event_type and event.event_type != event_type:
                continue
            
            # Filter by date range if specified
            if start_date and event.end_time < start_date:
                continue
            if end_date and event.start_time > end_date:
                continue
            
            user_events.append(event)
        
        # Sort by start time
        user_events.sort(key=lambda x: x.start_time)
        return user_events
    
    async def get_team_events(
        self,
        team_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CalendarEvent]:
        """Get events for a team within a date range"""
        if not self._initialized:
            await self.initialize()
        
        team_events = []
        
        for event in self.events.values():
            # Filter by team
            if event.team_id != team_id:
                continue
            
            # Filter by date range if specified
            if start_date and event.end_time < start_date:
                continue
            if end_date and event.start_time > end_date:
                continue
            
            team_events.append(event)
        
        # Sort by start time
        team_events.sort(key=lambda x: x.start_time)
        return team_events
    
    async def schedule_agent_task(
        self,
        user_id: int,
        agent_id: str,
        task_title: str,
        task_description: str,
        scheduled_time: datetime,
        duration_minutes: int = 60,
        priority: str = "medium"
    ) -> CalendarEvent:
        """Schedule an agent task in the calendar"""
        if not self._initialized:
            await self.initialize()
        
        end_time = scheduled_time + timedelta(minutes=duration_minutes)
        
        event = await self.create_event(
            user_id=user_id,
            title=f"[{agent_id.upper()}] {task_title}",
            description=task_description,
            start_time=scheduled_time,
            end_time=end_time,
            event_type=EventType.AGENT_SCHEDULED,
            agent_id=agent_id,
            color=self._get_agent_color(agent_id),
            metadata={
                "task_priority": priority,
                "duration_minutes": duration_minutes,
                "auto_scheduled": True
            }
        )
        
        # Publish agent task scheduled event
        await self.event_bus.publish_event("agent.task_scheduled", {
            "event": asdict(event),
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return event
    
    async def get_upcoming_events(
        self,
        user_id: int,
        hours_ahead: int = 24
    ) -> List[CalendarEvent]:
        """Get upcoming events for a user"""
        now = datetime.utcnow()
        future_time = now + timedelta(hours=hours_ahead)
        
        return await self.get_user_events(
            user_id=user_id,
            start_date=now,
            end_date=future_time
        )
    
    async def get_today_events(self, user_id: int) -> List[CalendarEvent]:
        """Get today's events for a user"""
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        return await self.get_user_events(
            user_id=user_id,
            start_date=start_of_day,
            end_date=end_of_day
        )
    
    async def check_conflicts(
        self,
        user_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_event_id: Optional[str] = None
    ) -> List[CalendarEvent]:
        """Check for scheduling conflicts"""
        user_events = await self.get_user_events(user_id)
        conflicts = []
        
        for event in user_events:
            if exclude_event_id and event.id == exclude_event_id:
                continue
            
            # Check for overlap
            if (event.start_time < end_time and event.end_time > start_time):
                conflicts.append(event)
        
        return conflicts
    
    async def suggest_optimal_time(
        self,
        user_id: int,
        duration_minutes: int,
        preferred_times: List[datetime] = None,
        working_hours_only: bool = True
    ) -> Optional[datetime]:
        """Suggest optimal time for scheduling"""
        if not self._initialized:
            await self.initialize()
        
        # Get user settings
        settings = await self.get_user_settings(user_id)
        
        # Get next 7 days of events
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=7)
        existing_events = await self.get_user_events(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Find available slots
        available_slots = []
        
        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            
            # Skip weekends if working hours only
            if working_hours_only and current_date.weekday() >= 5:
                continue
            
            # Check working hours
            work_start = datetime.combine(
                current_date.date(),
                datetime.strptime(settings.working_hours_start, "%H:%M").time()
            )
            work_end = datetime.combine(
                current_date.date(),
                datetime.strptime(settings.working_hours_end, "%H:%M").time()
            )
            
            # Find gaps in schedule
            current_time = work_start
            while current_time + timedelta(minutes=duration_minutes) <= work_end:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                # Check for conflicts
                conflicts = await self.check_conflicts(
                    user_id=user_id,
                    start_time=current_time,
                    end_time=slot_end
                )
                
                if not conflicts:
                    available_slots.append(current_time)
                
                current_time += timedelta(minutes=30)  # Check every 30 minutes
        
        # Return the earliest available slot
        return available_slots[0] if available_slots else None
    
    async def get_user_settings(self, user_id: int) -> CalendarSettings:
        """Get calendar settings for a user"""
        if user_id not in self.settings:
            # Create default settings
            self.settings[user_id] = CalendarSettings(
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        return self.settings[user_id]
    
    async def update_user_settings(
        self,
        user_id: int,
        **updates
    ) -> CalendarSettings:
        """Update calendar settings for a user"""
        if not self._initialized:
            await self.initialize()
        
        if user_id not in self.settings:
            self.settings[user_id] = CalendarSettings(
                user_id=user_id,
                created_at=datetime.utcnow()
            )
        
        settings = self.settings[user_id]
        
        # Update fields
        for field, value in updates.items():
            if hasattr(settings, field):
                setattr(settings, field, value)
        
        settings.updated_at = datetime.utcnow()
        
        logger.info(f"Calendar settings updated for user {user_id}")
        return settings
    
    def _get_agent_color(self, agent_id: str) -> str:
        """Get color for agent events"""
        agent_colors = {
            "aria": "#F97316",  # Orange
            "clara": "#8B5CF6",  # Purple
            "eric": "#F59E0B",  # Amber
            "jackie": "#EC4899",  # Pink
            "shakes": "#10B981",  # Green
            "joe": "#3B82F6",  # Blue
            "purity": "#6366F1",  # Indigo
        }
        return agent_colors.get(agent_id, "#6B7280")  # Gray default
    
    async def _handle_event_created(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle event creation"""
        try:
            event_info = event_data.get("data", {}).get("event", {})
            logger.info(f"Calendar event created: {event_info.get('id')}")
        except Exception as e:
            logger.error(f"Error handling event creation: {e}")
    
    async def _handle_event_updated(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle event update"""
        try:
            event_info = event_data.get("data", {}).get("event", {})
            logger.info(f"Calendar event updated: {event_info.get('id')}")
        except Exception as e:
            logger.error(f"Error handling event update: {e}")
    
    async def _handle_event_deleted(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle event deletion"""
        try:
            event_id = event_data.get("data", {}).get("event_id")
            logger.info(f"Calendar event deleted: {event_id}")
        except Exception as e:
            logger.error(f"Error handling event deletion: {e}")
    
    async def _handle_agent_task_scheduled(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle agent task scheduling"""
        try:
            event_info = event_data.get("data", {}).get("event", {})
            agent_id = event_data.get("data", {}).get("agent_id")
            logger.info(f"Agent task scheduled: {agent_id} - {event_info.get('title')}")
        except Exception as e:
            logger.error(f"Error handling agent task scheduling: {e}")

# Global calendar service instance
calendar_service = CalendarService()

async def get_calendar_service() -> CalendarService:
    return calendar_service

async def init_calendar():
    await calendar_service.initialize()

async def close_calendar():
    # Cleanup if needed
    pass
