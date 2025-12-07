import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from datetime import datetime, timedelta
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ContentProject, ContentPiece, ContentCalendar, ScheduledContent

logger = logging.getLogger(__name__)

class ContentCalendarService:
    """Service for content calendar management and scheduling"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 3000,
            "temperature": 0.6
        }
    
    async def initialize(self):
        """Initialize content calendar service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Content calendar service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize content calendar service: {e}")
            raise
    
    async def create_content_calendar(
        self,
        user_id: int,
        calendar_name: str,
        calendar_description: str,
        start_date: datetime,
        end_date: datetime,
        content_themes: List[str],
        posting_frequency: str,
        target_audience: str
    ) -> Dict[str, Any]:
        """Create a comprehensive content calendar"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Create calendar
                content_calendar = ContentCalendar(
                    user_id=user_id,
                    calendar_name=calendar_name,
                    calendar_description=calendar_description,
                    start_date=start_date,
                    end_date=end_date,
                    content_themes=content_themes,
                    posting_frequency=posting_frequency,
                    target_audience=target_audience,
                    is_active=True
                )
                session.add(content_calendar)
                await session.flush()
                
                # Generate calendar strategy
                strategy_prompt = self._create_calendar_strategy_prompt(
                    calendar_name, calendar_description, start_date, end_date,
                    content_themes, posting_frequency, target_audience
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates content calendar strategies."}, {"role": "user", "content": strategy_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
                calendar_strategy = ai_response.text_content if ai_response.success else ""
                
                # Generate content plan
                content_plan = await self._generate_content_plan(
                    start_date, end_date, content_themes, posting_frequency, target_audience
                )
                
                # Create scheduled content entries
                scheduled_entries = []
                for plan_item in content_plan:
                    scheduled_content = ScheduledContent(
                        calendar_id=content_calendar.id,
                        scheduled_time=plan_item["scheduled_time"],
                        content_type=plan_item["content_type"],
                        theme=plan_item["theme"],
                        platform=plan_item["platform"],
                        status="planned",
                        notes=plan_item.get("notes", "")
                    )
                    session.add(scheduled_content)
                    await session.flush()
                    
                    scheduled_entries.append({
                        "scheduled_content_id": scheduled_content.id,
                        "scheduled_time": plan_item["scheduled_time"].isoformat(),
                        "content_type": plan_item["content_type"],
                        "theme": plan_item["theme"],
                        "platform": plan_item["platform"],
                        "status": "planned"
                    })
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.content_calendar_created", {
                    "calendar_id": content_calendar.id,
                    "user_id": user_id,
                    "calendar_name": calendar_name,
                    "total_entries": len(scheduled_entries),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "calendar_id": content_calendar.id,
                    "calendar_name": calendar_name,
                    "calendar_strategy": calendar_strategy,
                    "content_plan": content_plan,
                    "scheduled_entries": scheduled_entries,
                    "total_entries": len(scheduled_entries),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content calendar creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def schedule_content(
        self,
        calendar_id: int,
        content_piece_id: int,
        scheduled_time: datetime,
        platform: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Schedule content in the calendar"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get calendar
                calendar_result = await session.execute(
                    select(ContentCalendar).where(ContentCalendar.id == calendar_id)
                )
                calendar = calendar_result.scalar_one_or_none()
                
                if not calendar:
                    return {"success": False, "error": "Calendar not found"}
                
                # Get content piece
                content_result = await session.execute(
                    select(ContentPiece).where(ContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Create scheduled content
                scheduled_content = ScheduledContent(
                    calendar_id=calendar_id,
                    content_piece_id=content_piece_id,
                    scheduled_time=scheduled_time,
                    platform=platform,
                    status="scheduled",
                    notes=notes
                )
                session.add(scheduled_content)
                await session.flush()
                
                await session.commit()
                
                return {
                    "success": True,
                    "scheduled_content_id": scheduled_content.id,
                    "calendar_id": calendar_id,
                    "content_piece_id": content_piece_id,
                    "scheduled_time": scheduled_time.isoformat(),
                    "platform": platform,
                    "status": "scheduled",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content scheduling failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_calendar_view(
        self,
        calendar_id: int,
        view_type: str = "month",
        start_date: datetime = None
    ) -> Dict[str, Any]:
        """Get calendar view with scheduled content"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get calendar
                calendar_result = await session.execute(
                    select(ContentCalendar).where(ContentCalendar.id == calendar_id)
                )
                calendar = calendar_result.scalar_one_or_none()
                
                if not calendar:
                    return {"success": False, "error": "Calendar not found"}
                
                # Calculate date range based on view type
                if start_date is None:
                    start_date = datetime.utcnow()
                
                if view_type == "week":
                    end_date = start_date + timedelta(days=7)
                elif view_type == "month":
                    end_date = start_date + timedelta(days=30)
                else:
                    end_date = start_date + timedelta(days=7)
                
                # Get scheduled content
                scheduled_result = await session.execute(
                    select(ScheduledContent).where(
                        and_(
                            ScheduledContent.calendar_id == calendar_id,
                            ScheduledContent.scheduled_time >= start_date,
                            ScheduledContent.scheduled_time <= end_date
                        )
                    ).order_by(ScheduledContent.scheduled_time)
                )
                scheduled_content = scheduled_result.scalars().all()
                
                # Format calendar view
                calendar_view = []
                for item in scheduled_content:
                    calendar_view.append({
                        "scheduled_content_id": item.id,
                        "scheduled_time": item.scheduled_time.isoformat(),
                        "content_type": item.content_type,
                        "theme": item.theme,
                        "platform": item.platform,
                        "status": item.status,
                        "notes": item.notes,
                        "content_piece_id": item.content_piece_id
                    })
                
                return {
                    "success": True,
                    "calendar_id": calendar_id,
                    "calendar_name": calendar.calendar_name,
                    "view_type": view_type,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "scheduled_content": calendar_view,
                    "total_scheduled": len(calendar_view),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Calendar view retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_calendar(
        self,
        calendar_id: int,
        optimization_goals: List[str]
    ) -> Dict[str, Any]:
        """Optimize calendar for better performance"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get calendar
                calendar_result = await session.execute(
                    select(ContentCalendar).where(ContentCalendar.id == calendar_id)
                )
                calendar = calendar_result.scalar_one_or_none()
                
                if not calendar:
                    return {"success": False, "error": "Calendar not found"}
                
                # Get scheduled content
                scheduled_result = await session.execute(
                    select(ScheduledContent).where(ScheduledContent.calendar_id == calendar_id)
                )
                scheduled_content = scheduled_result.scalars().all()
                
                # Generate optimization recommendations
                optimization_prompt = self._create_optimization_prompt(
                    calendar, scheduled_content, optimization_goals
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that provides content calendar optimization recommendations."}, {"role": "user", "content": optimization_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
                optimization_recommendations = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "calendar_id": calendar_id,
                    "optimization_goals": optimization_goals,
                    "optimization_recommendations": optimization_recommendations,
                    "current_scheduled_count": len(scheduled_content),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Calendar optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_content_plan(
        self, start_date: datetime, end_date: datetime, content_themes: List[str],
        posting_frequency: str, target_audience: str
    ) -> List[Dict[str, Any]]:
        """Generate content plan for calendar"""
        content_plan = []
        current_date = start_date
        
        # Calculate posting frequency
        if posting_frequency == "daily":
            days_between = 1
        elif posting_frequency == "twice_daily":
            days_between = 0.5
        elif posting_frequency == "every_other_day":
            days_between = 2
        else:
            days_between = 1
        
        # Generate plan
        while current_date <= end_date:
            for theme in content_themes:
                content_plan.append({
                    "scheduled_time": current_date,
                    "content_type": self._get_content_type_for_theme(theme),
                    "theme": theme,
                    "platform": self._get_platform_for_theme(theme),
                    "notes": f"Content for {theme} theme targeting {target_audience}"
                })
            
            current_date += timedelta(days=days_between)
        
        return content_plan
    
    def _get_content_type_for_theme(self, theme: str) -> str:
        """Get appropriate content type for theme"""
        theme_content_map = {
            "educational": "blog_post",
            "promotional": "social_media",
            "behind_scenes": "social_media",
            "user_generated": "social_media",
            "trending": "blog_post",
            "inspirational": "social_media"
        }
        return theme_content_map.get(theme, "social_media")
    
    def _get_platform_for_theme(self, theme: str) -> str:
        """Get appropriate platform for theme"""
        theme_platform_map = {
            "educational": "linkedin",
            "promotional": "facebook",
            "behind_scenes": "instagram",
            "user_generated": "instagram",
            "trending": "twitter",
            "inspirational": "instagram"
        }
        return theme_platform_map.get(theme, "facebook")
    
    def _create_calendar_strategy_prompt(
        self, calendar_name: str, calendar_description: str, start_date: datetime,
        end_date: datetime, content_themes: List[str], posting_frequency: str, target_audience: str
    ) -> str:
        """Create prompt for calendar strategy"""
        return f"""
        Create a comprehensive content calendar strategy for:
        
        Calendar Name: {calendar_name}
        Description: {calendar_description}
        Start Date: {start_date.strftime('%Y-%m-%d')}
        End Date: {end_date.strftime('%Y-%m-%d')}
        Content Themes: {', '.join(content_themes)}
        Posting Frequency: {posting_frequency}
        Target Audience: {target_audience}
        
        Include:
        1. Content strategy overview
        2. Theme distribution and timing
        3. Platform-specific considerations
        4. Audience engagement tactics
        5. Content mix recommendations
        6. Performance optimization tips
        7. Seasonal and trending opportunities
        
        Format as comprehensive calendar strategy document.
        """
    
    def _create_optimization_prompt(
        self, calendar: ContentCalendar, scheduled_content: List[ScheduledContent], optimization_goals: List[str]
    ) -> str:
        """Create prompt for calendar optimization"""
        return f"""
        Optimize this content calendar for better performance:
        
        Calendar: {calendar.calendar_name}
        Content Themes: {', '.join(calendar.content_themes)}
        Posting Frequency: {calendar.posting_frequency}
        Target Audience: {calendar.target_audience}
        Scheduled Content Count: {len(scheduled_content)}
        
        Optimization Goals: {', '.join(optimization_goals)}
        
        Provide:
        1. Content timing optimization
        2. Theme distribution improvements
        3. Platform strategy enhancements
        4. Audience engagement tactics
        5. Performance improvement recommendations
        6. Content mix adjustments
        
        Format as actionable optimization recommendations.
        """
