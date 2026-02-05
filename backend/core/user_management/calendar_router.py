from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field
from core.user_management.calendar_service import (
    get_calendar_service,
    CalendarService,
    EventType,
    EventStatus,
    RecurrenceType
)
from core.authentication.auth_manager import get_current_user
from core.user_management.user_manager import User

router = APIRouter(prefix="/api/v1/calendar", tags=["calendar"])

class CalendarEventCreateRequest(BaseModel):
    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    event_type: str = Field(default="personal", description="Event type")
    location: Optional[str] = Field(None, description="Event location")
    attendees: Optional[List[str]] = Field(None, description="Event attendees")
    recurrence_type: str = Field(default="none", description="Recurrence type")
    recurrence_end: Optional[datetime] = Field(None, description="Recurrence end date")
    reminder_minutes: int = Field(default=15, description="Reminder time in minutes")
    is_all_day: bool = Field(default=False, description="Is all day event")
    color: str = Field(default="#3B82F6", description="Event color")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    agent_id: Optional[str] = Field(None, description="Associated agent ID")
    team_id: Optional[str] = Field(None, description="Associated team ID")

class CalendarEventUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_time: Optional[datetime] = Field(None, description="Event start time")
    end_time: Optional[datetime] = Field(None, description="Event end time")
    event_type: Optional[str] = Field(None, description="Event type")
    location: Optional[str] = Field(None, description="Event location")
    attendees: Optional[List[str]] = Field(None, description="Event attendees")
    recurrence_type: Optional[str] = Field(None, description="Recurrence type")
    recurrence_end: Optional[datetime] = Field(None, description="Recurrence end date")
    reminder_minutes: Optional[int] = Field(None, description="Reminder time in minutes")
    is_all_day: Optional[bool] = Field(None, description="Is all day event")
    color: Optional[str] = Field(None, description="Event color")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    status: Optional[str] = Field(None, description="Event status")

class CalendarEventResponse(BaseModel):
    id: str
    user_id: int
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    event_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    location: Optional[str]
    attendees: List[str]
    recurrence_type: str
    recurrence_end: Optional[datetime]
    reminder_minutes: int
    is_all_day: bool
    color: str
    metadata: Dict[str, Any]
    agent_id: Optional[str]
    team_id: Optional[str]

class CalendarSettingsRequest(BaseModel):
    timezone: Optional[str] = Field(None, description="User timezone")
    working_hours_start: Optional[str] = Field(None, description="Working hours start")
    working_hours_end: Optional[str] = Field(None, description="Working hours end")
    working_days: Optional[List[int]] = Field(None, description="Working days (0=Monday)")
    default_reminder_minutes: Optional[int] = Field(None, description="Default reminder time")
    auto_schedule_agent_tasks: Optional[bool] = Field(None, description="Auto schedule agent tasks")
    allow_agent_scheduling: Optional[bool] = Field(None, description="Allow agent scheduling")
    team_calendar_visibility: Optional[bool] = Field(None, description="Team calendar visibility")

class AgentTaskScheduleRequest(BaseModel):
    agent_id: str = Field(..., description="Agent ID")
    task_title: str = Field(..., description="Task title")
    task_description: str = Field(..., description="Task description")
    scheduled_time: datetime = Field(..., description="Scheduled time")
    duration_minutes: int = Field(default=60, description="Duration in minutes")
    priority: str = Field(default="medium", description="Task priority")

@router.post("/events", response_model=CalendarEventResponse)
async def create_event(
    request: CalendarEventCreateRequest,
    current_user: User = Depends(get_current_user),
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Create a new calendar event"""
    try:
        event = await calendar_service.create_event(
            user_id=current_user.id,
            title=request.title,
            description=request.description,
            start_time=request.start_time,
            end_time=request.end_time,
            event_type=EventType(request.event_type.lower()),
            location=request.location,
            attendees=request.attendees,
            recurrence_type=RecurrenceType(request.recurrence_type.lower()),
            recurrence_end=request.recurrence_end,
            reminder_minutes=request.reminder_minutes,
            is_all_day=request.is_all_day,
            color=request.color,
            metadata=request.metadata,
            agent_id=request.agent_id,
            team_id=request.team_id
        )
        
        return CalendarEventResponse(
            id=event.id,
            user_id=event.user_id,
            title=event.title,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            event_type=event.event_type.value,
            status=event.status.value,
            created_at=event.created_at,
            updated_at=event.updated_at,
            location=event.location,
            attendees=event.attendees,
            recurrence_type=event.recurrence_type.value,
            recurrence_end=event.recurrence_end,
            reminder_minutes=event.reminder_minutes,
            is_all_day=event.is_all_day,
            color=event.color,
            metadata=event.metadata,
            agent_id=event.agent_id,
            team_id=event.team_id
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}"
        )

@router.put("/events/{event_id}", response_model=CalendarEventResponse)
async def update_event(
    event_id: str,
    request: CalendarEventUpdateRequest,
    current_user: User = Depends(get_current_user),
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Update a calendar event"""
    try:
        updates = {}
        if request.title is not None:
            updates["title"] = request.title
        if request.description is not None:
            updates["description"] = request.description
        if request.start_time is not None:
            updates["start_time"] = request.start_time
        if request.end_time is not None:
            updates["end_time"] = request.end_time
        if request.event_type is not None:
            updates["event_type"] = EventType(request.event_type.lower())
        if request.location is not None:
            updates["location"] = request.location
        if request.attendees is not None:
            updates["attendees"] = request.attendees
        if request.recurrence_type is not None:
            updates["recurrence_type"] = RecurrenceType(request.recurrence_type.lower())
        if request.recurrence_end is not None:
            updates["recurrence_end"] = request.recurrence_end
        if request.reminder_minutes is not None:
            updates["reminder_minutes"] = request.reminder_minutes
        if request.is_all_day is not None:
            updates["is_all_day"] = request.is_all_day
        if request.color is not None:
            updates["color"] = request.color
        if request.metadata is not None:
            updates["metadata"] = request.metadata
        if request.status is not None:
            updates["status"] = EventStatus(request.status.lower())
        
        event = await calendar_service.update_event(
            event_id=event_id,
            user_id=current_user.id,
            **updates
        )
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        return CalendarEventResponse(
            id=event.id,
            user_id=event.user_id,
            title=event.title,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            event_type=event.event_type.value,
            status=event.status.value,
            created_at=event.created_at,
            updated_at=event.updated_at,
            location=event.location,
            attendees=event.attendees,
            recurrence_type=event.recurrence_type.value,
            recurrence_end=event.recurrence_end,
            reminder_minutes=event.reminder_minutes,
            is_all_day=event.is_all_day,
            color=event.color,
            metadata=event.metadata,
            agent_id=event.agent_id,
            team_id=event.team_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update event: {str(e)}"
        )

@router.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Delete a calendar event"""
    try:
        success = await calendar_service.delete_event(
            event_id=event_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        return {"success": True, "message": "Event deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete event: {str(e)}"
        )

@router.get("/events", response_model=List[CalendarEventResponse])
async def get_events(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_type: Optional[str] = None,
    team_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Get user's calendar events"""
    try:
        events = await calendar_service.get_user_events(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            event_type=EventType(event_type.lower()) if event_type else None,
            team_id=team_id
        )
        
        return [
            CalendarEventResponse(
                id=event.id,
                user_id=event.user_id,
                title=event.title,
                description=event.description,
                start_time=event.start_time,
                end_time=event.end_time,
                event_type=event.event_type.value,
                status=event.status.value,
                created_at=event.created_at,
                updated_at=event.updated_at,
                location=event.location,
                attendees=event.attendees,
                recurrence_type=event.recurrence_type.value,
                recurrence_end=event.recurrence_end,
                reminder_minutes=event.reminder_minutes,
                is_all_day=event.is_all_day,
                color=event.color,
                metadata=event.metadata,
                agent_id=event.agent_id,
                team_id=event.team_id
            )
            for event in events
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get events: {str(e)}"
        )

@router.get("/events/today", response_model=List[CalendarEventResponse])
async def get_today_events(
    current_user: User = Depends(get_current_user),
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Get today's events"""
    try:
        events = await calendar_service.get_today_events(current_user.id)
        
        return [
            CalendarEventResponse(
                id=event.id,
                user_id=event.user_id,
                title=event.title,
                description=event.description,
                start_time=event.start_time,
                end_time=event.end_time,
                event_type=event.event_type.value,
                status=event.status.value,
                created_at=event.created_at,
                updated_at=event.updated_at,
                location=event.location,
                attendees=event.attendees,
                recurrence_type=event.recurrence_type.value,
                recurrence_end=event.recurrence_end,
                reminder_minutes=event.reminder_minutes,
                is_all_day=event.is_all_day,
                color=event.color,
                metadata=event.metadata,
                agent_id=event.agent_id,
                team_id=event.team_id
            )
            for event in events
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get today's events: {str(e)}"
        )

@router.get("/events/upcoming", response_model=List[CalendarEventResponse])
async def get_upcoming_events(
    hours_ahead: int = 24,
    current_user: User = Depends(get_current_user),
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Get upcoming events"""
    try:
        events = await calendar_service.get_upcoming_events(
            user_id=current_user.id,
            hours_ahead=hours_ahead
        )
        
        return [
            CalendarEventResponse(
                id=event.id,
                user_id=event.user_id,
                title=event.title,
                description=event.description,
                start_time=event.start_time,
                end_time=event.end_time,
                event_type=event.event_type.value,
                status=event.status.value,
                created_at=event.created_at,
                updated_at=event.updated_at,
                location=event.location,
                attendees=event.attendees,
                recurrence_type=event.recurrence_type.value,
                recurrence_end=event.recurrence_end,
                reminder_minutes=event.reminder_minutes,
                is_all_day=event.is_all_day,
                color=event.color,
                metadata=event.metadata,
                agent_id=event.agent_id,
                team_id=event.team_id
            )
            for event in events
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get upcoming events: {str(e)}"
        )

@router.post("/events/agent-schedule", response_model=CalendarEventResponse)
async def schedule_agent_task(
    request: AgentTaskScheduleRequest,
    current_user: User = Depends(get_current_user),
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Schedule an agent task"""
    try:
        event = await calendar_service.schedule_agent_task(
            user_id=current_user.id,
            agent_id=request.agent_id,
            task_title=request.task_title,
            task_description=request.task_description,
            scheduled_time=request.scheduled_time,
            duration_minutes=request.duration_minutes,
            priority=request.priority
        )
        
        return CalendarEventResponse(
            id=event.id,
            user_id=event.user_id,
            title=event.title,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            event_type=event.event_type.value,
            status=event.status.value,
            created_at=event.created_at,
            updated_at=event.updated_at,
            location=event.location,
            attendees=event.attendees,
            recurrence_type=event.recurrence_type.value,
            recurrence_end=event.recurrence_end,
            reminder_minutes=event.reminder_minutes,
            is_all_day=event.is_all_day,
            color=event.color,
            metadata=event.metadata,
            agent_id=event.agent_id,
            team_id=event.team_id
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule agent task: {str(e)}"
        )

@router.get("/events/conflicts")
async def check_conflicts(
    start_time: datetime,
    end_time: datetime,
    exclude_event_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Check for scheduling conflicts"""
    try:
        conflicts = await calendar_service.check_conflicts(
            user_id=current_user.id,
            start_time=start_time,
            end_time=end_time,
            exclude_event_id=exclude_event_id
        )
        
        return {
            "has_conflicts": len(conflicts) > 0,
            "conflicts": [
                {
                    "id": event.id,
                    "title": event.title,
                    "start_time": event.start_time,
                    "end_time": event.end_time
                }
                for event in conflicts
            ]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check conflicts: {str(e)}"
        )

@router.get("/suggest-time")
async def suggest_optimal_time(
    duration_minutes: int,
    preferred_times: Optional[List[datetime]] = None,
    working_hours_only: bool = True,
    current_user: User = Depends(get_current_user),
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Suggest optimal time for scheduling"""
    try:
        optimal_time = await calendar_service.suggest_optimal_time(
            user_id=current_user.id,
            duration_minutes=duration_minutes,
            preferred_times=preferred_times,
            working_hours_only=working_hours_only
        )
        
        return {
            "suggested_time": optimal_time,
            "available": optimal_time is not None
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest optimal time: {str(e)}"
        )

@router.get("/settings")
async def get_calendar_settings(
    current_user: User = Depends(get_current_user),
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Get calendar settings"""
    try:
        settings = await calendar_service.get_user_settings(current_user.id)
        
        return {
            "user_id": settings.user_id,
            "timezone": settings.timezone,
            "working_hours_start": settings.working_hours_start,
            "working_hours_end": settings.working_hours_end,
            "working_days": settings.working_days,
            "default_reminder_minutes": settings.default_reminder_minutes,
            "auto_schedule_agent_tasks": settings.auto_schedule_agent_tasks,
            "allow_agent_scheduling": settings.allow_agent_scheduling,
            "team_calendar_visibility": settings.team_calendar_visibility,
            "created_at": settings.created_at,
            "updated_at": settings.updated_at
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get calendar settings: {str(e)}"
        )

@router.put("/settings")
async def update_calendar_settings(
    request: CalendarSettingsRequest,
    current_user: User = Depends(get_current_user),
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Update calendar settings"""
    try:
        updates = {}
        if request.timezone is not None:
            updates["timezone"] = request.timezone
        if request.working_hours_start is not None:
            updates["working_hours_start"] = request.working_hours_start
        if request.working_hours_end is not None:
            updates["working_hours_end"] = request.working_hours_end
        if request.working_days is not None:
            updates["working_days"] = request.working_days
        if request.default_reminder_minutes is not None:
            updates["default_reminder_minutes"] = request.default_reminder_minutes
        if request.auto_schedule_agent_tasks is not None:
            updates["auto_schedule_agent_tasks"] = request.auto_schedule_agent_tasks
        if request.allow_agent_scheduling is not None:
            updates["allow_agent_scheduling"] = request.allow_agent_scheduling
        if request.team_calendar_visibility is not None:
            updates["team_calendar_visibility"] = request.team_calendar_visibility
        
        settings = await calendar_service.update_user_settings(
            user_id=current_user.id,
            **updates
        )
        
        return {
            "user_id": settings.user_id,
            "timezone": settings.timezone,
            "working_hours_start": settings.working_hours_start,
            "working_hours_end": settings.working_hours_end,
            "working_days": settings.working_days,
            "default_reminder_minutes": settings.default_reminder_minutes,
            "auto_schedule_agent_tasks": settings.auto_schedule_agent_tasks,
            "allow_agent_scheduling": settings.allow_agent_scheduling,
            "team_calendar_visibility": settings.team_calendar_visibility,
            "created_at": settings.created_at,
            "updated_at": settings.updated_at
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update calendar settings: {str(e)}"
        )
