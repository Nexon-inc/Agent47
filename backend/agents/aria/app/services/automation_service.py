from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.core.database.connection import get_supabase
from backend.core.database.models import UserSelectedAgent
from ..models import ScheduledPost, PostStatus
from .scheduling_service import SchedulingService
from .content_service import ContentService


class AutomationService:
    """Service for automating social media tasks over multiple days"""
    
    def __init__(self):
        self.scheduling = SchedulingService()
        self.content = ContentService()
    
    async def initialize(self):
        await self.scheduling.initialize()
        if not self.content.ai_service_manager:
            await self.content.initialize()
    
    async def create_multi_day_automation(
        self,
        user_id: int,
        task_type: str,
        task_config: Dict[str, Any],
        days: int = 7,
        platforms: Optional[List[str]] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Create automation for a specific task over multiple days
        
        Args:
            user_id: User ID
            task_type: Type of task (content_creation, posting, engagement, etc.)
            task_config: Configuration for the task (topic, tone, hashtags, etc.)
            days: Number of days to automate (default 7)
            platforms: List of platforms to post to
            db: Database session
        
        Returns:
            Dict with automation details and scheduled posts
        """
        try:
            if not db:
                # If no db session provided, create our own
                db_obj = await get_supabase()
                async with db_obj.get_session() as session:
                    return await self._create_automation_with_session(
                        user_id, task_type, task_config, days, platforms, session
                    )
            
            # Enable automation on the agent
            await self._enable_automation(user_id, db)
            
            scheduled_posts = []
            automation_details = {
                "task_type": task_type,
                "days": days,
                "platforms": platforms or ["instagram"],
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=days)).isoformat(),
                "posts_created": 0
            }
            
            # Generate and schedule posts for each day
            for day in range(days):
                scheduled_date = datetime.now() + timedelta(days=day)
                
                # Calculate optimal posting time (e.g., 9 AM, 12 PM, 6 PM)
                posting_times = self._get_optimal_posting_times(scheduled_date)
                
                # Create posts for each optimal time
                for post_time in posting_times:
                    try:
                        # Generate content based on task type
                        if task_type == "content_creation" or task_type == "posting":
                            post_data = await self._generate_automated_content(
                                user_id, task_config, day, db
                            )
                            
                            # Create scheduled post
                            scheduled_post = await self._create_automated_post(
                                user_id=user_id,
                                caption=post_data.get("caption"),
                                hashtags=post_data.get("hashtags", []),
                                platforms=platforms or ["instagram"],
                                scheduled_at=post_time,
                                task_config=task_config,
                                db=db
                            )
                            
                            scheduled_posts.append(scheduled_post)
                            automation_details["posts_created"] += 1
                            
                    except Exception as e:
                        # Log error but continue with other posts
                        automation_details.setdefault("errors", []).append({
                            "day": day,
                            "time": post_time.isoformat(),
                            "error": str(e)
                        })
            
            automation_details["scheduled_posts"] = scheduled_posts
            automation_details["success"] = True
            automation_details["message"] = f"Automation created: {automation_details['posts_created']} posts scheduled over {days} days"
            
            return automation_details
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create automation: {str(e)}"
            }
    
    async def _create_automation_with_session(
        self,
        user_id: int,
        task_type: str,
        task_config: Dict[str, Any],
        days: int,
        platforms: Optional[List[str]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create automation with a provided session (handles commit)"""
        try:
            # Enable automation on the agent
            await self._enable_automation(user_id, db)
            
            scheduled_posts = []
            automation_details = {
                "task_type": task_type,
                "days": days,
                "platforms": platforms or ["instagram"],
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=days)).isoformat(),
                "posts_created": 0
            }
            
            # Generate and schedule posts for each day
            for day in range(days):
                scheduled_date = datetime.now() + timedelta(days=day)
                posting_times = self._get_optimal_posting_times(scheduled_date)
                
                for post_time in posting_times:
                    try:
                        post_data = await self._generate_automated_content(
                            user_id, task_config, day, db
                        )
                        
                        scheduled_post = await self._create_automated_post(
                            user_id=user_id,
                            caption=post_data.get("caption"),
                            hashtags=post_data.get("hashtags", []),
                            platforms=platforms or ["instagram"],
                            scheduled_at=post_time,
                            task_config=task_config,
                            db=db
                        )
                        
                        scheduled_posts.append(scheduled_post)
                        automation_details["posts_created"] += 1
                    except Exception as e:
                        automation_details.setdefault("errors", []).append({
                            "day": day,
                            "time": post_time.isoformat(),
                            "error": str(e)
                        })
            
            await db.commit()
            
            automation_details["scheduled_posts"] = scheduled_posts
            automation_details["success"] = True
            automation_details["message"] = f"Automation created: {automation_details['posts_created']} posts scheduled over {days} days"
            
            return automation_details
            
        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "error": f"Failed to create automation: {str(e)}"
            }
    
    async def _generate_automated_content(
        self,
        user_id: int,
        task_config: Dict[str, Any],
        day: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate content for automated posting"""
        try:
            # Extract topic and add day-specific variation
            topic = task_config.get("topic", "")
            tone = task_config.get("tone", "professional")
            
            # Add day-specific context
            day_context = f"Day {day + 1} of content series"
            enhanced_topic = f"{topic} - {day_context}"
            
            # Generate caption
            brief = {
                "topic": enhanced_topic,
                "tone": tone,
                "day": day + 1,
                "total_days": task_config.get("days", 7)
            }
            
            caption_result = await self.content.generate_caption(user_id, brief)
            caption = caption_result.get("caption", "")
            
            # Generate hashtags
            hashtags = await self.content.suggest_hashtags(
                user_id,
                topic,
                n=task_config.get("hashtag_count", 10)
            )
            
            return {
                "caption": caption,
                "hashtags": hashtags,
                "day": day + 1
            }
            
        except Exception as e:
            # Fallback content
            return {
                "caption": f"{task_config.get('topic', 'Content')} - Day {day + 1}",
                "hashtags": task_config.get("default_hashtags", []),
                "day": day + 1
            }
    
    async def _create_automated_post(
        self,
        user_id: int,
        caption: str,
        hashtags: List[str],
        platforms: List[str],
        scheduled_at: datetime,
        task_config: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a scheduled post for automation"""
        try:
            # Generate unique idempotency key
            idempotency_key = f"auto_{user_id}_{scheduled_at.timestamp()}"
            
            # Create post payload
            payload = {
                "idempotency_key": idempotency_key,
                "platform_targets": platforms,
                "caption": caption,
                "hashtags": hashtags,
                "media_refs": task_config.get("media_refs", []),
                "scheduled_at": scheduled_at.isoformat(),
                "timezone": task_config.get("timezone", "UTC")
            }
            
            # Use scheduling service to create the post
            result = await self.scheduling.create_scheduled_post(user_id, payload)
            
            return {
                "scheduled_post_id": result.get("id"),
                "scheduled_at": scheduled_at.isoformat(),
                "platforms": platforms,
                "status": result.get("status")
            }
            
        except Exception as e:
            raise Exception(f"Failed to create automated post: {str(e)}")
    
    def _get_optimal_posting_times(self, date: datetime) -> List[datetime]:
        """Get optimal posting times for a given date"""
        # Default optimal times: 9 AM, 12 PM, 6 PM
        base_date = date.replace(hour=9, minute=0, second=0, microsecond=0)
        
        times = [
            base_date,  # 9 AM
            base_date + timedelta(hours=3),  # 12 PM
            base_date + timedelta(hours=9),  # 6 PM
        ]
        
        # Only include future times
        return [t for t in times if t > datetime.now()]
    
    async def _enable_automation(self, user_id: int, db: AsyncSession):
        """Enable automation for the user's Aria agent"""
        try:
            # Get user's Aria agent selection
            query = select(UserSelectedAgent).where(
                UserSelectedAgent.user_id == user_id,
                UserSelectedAgent.agent_key == "aria"
            )
            result = await db.execute(query)
            agent_selection = result.scalar_one_or_none()
            
            if agent_selection:
                agent_selection.automation_enabled = True
                await db.commit()
            else:
                # Create agent selection if it doesn't exist
                agent_selection = UserSelectedAgent(
                    user_id=user_id,
                    agent_key="aria",
                    status="active",
                    automation_enabled=True
                )
                db.add(agent_selection)
                await db.commit()
                
        except Exception as e:
            # Log error but don't fail automation setup
            pass
    
    async def get_automation_status(self, user_id: int, db: AsyncSession = None) -> Dict[str, Any]:
        """Get current automation status for user"""
        try:
            if not db:
                db_obj = await get_supabase()
                async with db_obj.get_session() as session:
                    return await self._get_automation_status_internal(user_id, session)
            else:
                return await self._get_automation_status_internal(user_id, db)
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_automation_status_internal(self, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Internal method to get automation status"""
        query = select(UserSelectedAgent).where(
            UserSelectedAgent.user_id == user_id,
            UserSelectedAgent.agent_key == "aria"
        )
        result = await db.execute(query)
        agent_selection = result.scalar_one_or_none()
        
        if agent_selection:
            return {
                "success": True,
                "automation_enabled": agent_selection.automation_enabled,
                "status": agent_selection.status,
                "created_at": agent_selection.created_at.isoformat() if agent_selection.created_at else None
            }
        else:
            return {
                "success": False,
                "automation_enabled": False,
                "message": "No agent selection found"
            }
    
    async def disable_automation(self, user_id: int, db: AsyncSession = None) -> Dict[str, Any]:
        """Disable automation for user"""
        try:
            if not db:
                db_obj = await get_supabase()
                async with db_obj.get_session() as session:
                    return await self._disable_automation_internal(user_id, session)
            else:
                return await self._disable_automation_internal(user_id, db)
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _disable_automation_internal(self, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Internal method to disable automation"""
        query = select(UserSelectedAgent).where(
            UserSelectedAgent.user_id == user_id,
            UserSelectedAgent.agent_key == "aria"
        )
        result = await db.execute(query)
        agent_selection = result.scalar_one_or_none()
        
        if agent_selection:
            agent_selection.automation_enabled = False
            await db.commit()
            return {
                "success": True,
                "message": "Automation disabled successfully"
            }
        else:
            return {
                "success": False,
                "message": "No automation found to disable"
            }

