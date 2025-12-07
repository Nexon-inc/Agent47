import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ContentProject, ContentPiece, ScheduledContent

logger = logging.getLogger(__name__)

class SocialMediaAutomationService:
    """Service for social media content automation and scheduling"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 2000,
            "temperature": 0.7
        }
    
    async def initialize(self):
        """Initialize social media automation service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Social media automation service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize social media automation service: {e}")
            raise
    
    async def create_automation_campaign(
        self,
        user_id: int,
        campaign_name: str,
        platforms: List[str],
        content_themes: List[str],
        posting_frequency: str,
        target_audience: str,
        campaign_duration_days: int,
        tone: str
    ) -> Dict[str, Any]:
        """Create automated social media campaign"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Create campaign project
                campaign_project = ContentProject(
                    user_id=user_id,
                    title=f"Automation Campaign: {campaign_name}",
                    description=f"Automated social media campaign across {', '.join(platforms)}",
                    content_type="automation_campaign",
                    target_audience=target_audience,
                    tone=tone,
                    status="active"
                )
                session.add(campaign_project)
                await session.flush()
                
                # Generate campaign strategy
                strategy_prompt = self._create_campaign_strategy_prompt(
                    campaign_name, platforms, content_themes, posting_frequency,
                    target_audience, campaign_duration_days, tone
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates social media campaign strategies."}, {"role": "user", "content": strategy_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
                campaign_strategy = ai_response.text_content if ai_response.success else ""
                
                # Generate content calendar
                content_calendar = await self._generate_content_calendar(
                    platforms, content_themes, posting_frequency, campaign_duration_days, target_audience, tone
                )
                
                # Create scheduled content pieces
                scheduled_posts = []
                for post_plan in content_calendar:
                    # Generate content for each platform
                    for platform in platforms:
                        content_prompt = self._create_content_prompt(
                            post_plan["theme"], post_plan["content_type"], platform,
                            target_audience, tone, post_plan["posting_time"]
                        )
                        # Use AI Service Manager instead of NLPUtils
                        ai_manager = await get_ai_service_manager()
                        messages = [{"role": "system", "content": f"You are an AI assistant that creates social media content for {platform}."}, {"role": "user", "content": content_prompt}]
                        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
                        content = ai_response.text_content if ai_response.success else ""
                        
                        # Create content piece
                        content_piece = ContentPiece(
                            project_id=campaign_project.id,
                            title=f"{post_plan['theme']} - {platform}",
                            content=content,
                            content_type=post_plan["content_type"],
                            platform=platform,
                            word_count=len(content.split()),
                            character_count=len(content),
                            reading_time=self._calculate_reading_time(content),
                            status="scheduled",
                            ai_generated=True
                        )
                        session.add(content_piece)
                        await session.flush()
                        
                        # Create scheduled content
                        scheduled_content = ScheduledContent(
                            content_piece_id=content_piece.id,
                            scheduled_time=post_plan["posting_time"],
                            platform=platform,
                            status="pending",
                            automation_enabled=True
                        )
                        session.add(scheduled_content)
                        await session.flush()
                        
                        scheduled_posts.append({
                            "content_piece_id": content_piece.id,
                            "scheduled_content_id": scheduled_content.id,
                            "platform": platform,
                            "theme": post_plan["theme"],
                            "content_type": post_plan["content_type"],
                            "scheduled_time": post_plan["posting_time"].isoformat(),
                            "content": content
                        })
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.automation_campaign_created", {
                    "project_id": campaign_project.id,
                    "user_id": user_id,
                    "campaign_name": campaign_name,
                    "platforms": platforms,
                    "total_posts": len(scheduled_posts),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "project_id": campaign_project.id,
                    "campaign_name": campaign_name,
                    "campaign_strategy": campaign_strategy,
                    "scheduled_posts": scheduled_posts,
                    "total_posts": len(scheduled_posts),
                    "platforms": platforms,
                    "campaign_duration_days": campaign_duration_days,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Automation campaign creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def schedule_content(
        self,
        content_piece_id: int,
        platforms: List[str],
        scheduled_times: List[datetime],
        automation_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Schedule content for multiple platforms"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ContentPiece).where(ContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Create scheduled content for each platform
                scheduled_posts = []
                for i, platform in enumerate(platforms):
                    scheduled_time = scheduled_times[i] if i < len(scheduled_times) else scheduled_times[0]
                    
                    scheduled_content = ScheduledContent(
                        content_piece_id=content_piece_id,
                        scheduled_time=scheduled_time,
                        platform=platform,
                        status="pending",
                        automation_enabled=automation_settings.get("enabled", True),
                        automation_settings=automation_settings
                    )
                    session.add(scheduled_content)
                    await session.flush()
                    
                    scheduled_posts.append({
                        "scheduled_content_id": scheduled_content.id,
                        "platform": platform,
                        "scheduled_time": scheduled_time.isoformat(),
                        "status": "pending"
                    })
                
                await session.commit()
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "scheduled_posts": scheduled_posts,
                    "total_scheduled": len(scheduled_posts),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content scheduling failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_posting_times(
        self,
        user_id: int,
        platform: str,
        target_audience: str,
        content_type: str
    ) -> Dict[str, Any]:
        """Optimize posting times based on audience and platform"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Generate optimal posting times
            optimization_prompt = self._create_posting_time_optimization_prompt(
                platform, target_audience, content_type
            )
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that analyzes and optimizes social media campaigns."}, {"role": "user", "content": optimization_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
            optimization_analysis = ai_response.text_content if ai_response.success else ""
            
            # Generate recommended posting schedule
            schedule_prompt = self._create_schedule_recommendation_prompt(
                platform, target_audience, content_type, optimization_analysis
            )
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that creates optimal social media posting schedules."}, {"role": "user", "content": schedule_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
            recommended_schedule = ai_response.text_content if ai_response.success else ""
            
            return {
                "success": True,
                "platform": platform,
                "target_audience": target_audience,
                "content_type": content_type,
                "optimization_analysis": optimization_analysis,
                "recommended_schedule": recommended_schedule,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Posting time optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_content_calendar(
        self, platforms: List[str], content_themes: List[str], posting_frequency: str,
        campaign_duration_days: int, target_audience: str, tone: str
    ) -> List[Dict[str, Any]]:
        """Generate content calendar for campaign"""
        calendar = []
        start_date = datetime.utcnow()
        
        # Calculate posting frequency
        if posting_frequency == "daily":
            posts_per_day = 1
        elif posting_frequency == "twice_daily":
            posts_per_day = 2
        elif posting_frequency == "every_other_day":
            posts_per_day = 0.5
        else:
            posts_per_day = 1
        
        total_posts = int(campaign_duration_days * posts_per_day)
        
        # Generate content plan
        for i in range(total_posts):
            theme = content_themes[i % len(content_themes)]
            content_type = self._get_content_type_for_theme(theme)
            
            # Calculate posting time
            days_offset = i // posts_per_day
            hours_offset = (i % posts_per_day) * 8  # 8 hours apart for multiple daily posts
            posting_time = start_date + timedelta(days=days_offset, hours=hours_offset)
            
            calendar.append({
                "theme": theme,
                "content_type": content_type,
                "posting_time": posting_time,
                "day": days_offset + 1
            })
        
        return calendar
    
    def _get_content_type_for_theme(self, theme: str) -> str:
        """Get appropriate content type for theme"""
        theme_content_map = {
            "educational": "how_to",
            "promotional": "product_showcase",
            "behind_scenes": "story",
            "user_generated": "testimonial",
            "trending": "news_update",
            "inspirational": "quote",
            "interactive": "poll_question"
        }
        return theme_content_map.get(theme, "general_post")
    
    def _create_campaign_strategy_prompt(
        self, campaign_name: str, platforms: List[str], content_themes: List[str],
        posting_frequency: str, target_audience: str, campaign_duration_days: int, tone: str
    ) -> str:
        """Create prompt for campaign strategy"""
        return f"""
        Create a comprehensive social media automation strategy for:
        
        Campaign Name: {campaign_name}
        Platforms: {', '.join(platforms)}
        Content Themes: {', '.join(content_themes)}
        Posting Frequency: {posting_frequency}
        Target Audience: {target_audience}
        Campaign Duration: {campaign_duration_days} days
        Tone: {tone}
        
        Include:
        1. Campaign objectives and goals
        2. Platform-specific strategies
        3. Content mix and themes
        4. Posting schedule optimization
        5. Engagement tactics
        6. Performance metrics to track
        7. Automation best practices
        
        Format as comprehensive campaign strategy document.
        """
    
    def _create_content_prompt(
        self, theme: str, content_type: str, platform: str, target_audience: str, tone: str, posting_time: datetime
    ) -> str:
        """Create prompt for automated content generation"""
        return f"""
        Create {content_type} content for {platform} with theme: {theme}
        
        Target Audience: {target_audience}
        Tone: {tone}
        Platform: {platform}
        Posting Time: {posting_time.strftime('%A, %B %d at %I:%M %p')}
        
        Requirements:
        - Align with {theme} theme
        - Optimize for {platform} best practices
        - Use {tone} tone consistently
        - Include relevant hashtags
        - Add engaging call-to-action
        - Consider posting time context
        
        Generate the complete social media post.
        """
    
    def _create_posting_time_optimization_prompt(
        self, platform: str, target_audience: str, content_type: str
    ) -> str:
        """Create prompt for posting time optimization"""
        return f"""
        Analyze optimal posting times for {platform}:
        
        Platform: {platform}
        Target Audience: {target_audience}
        Content Type: {content_type}
        
        Provide:
        1. Best posting times for {platform}
        2. Audience activity patterns
        3. Content type considerations
        4. Time zone recommendations
        5. Frequency optimization
        6. Platform-specific insights
        
        Format as comprehensive posting time analysis.
        """
    
    def _create_schedule_recommendation_prompt(
        self, platform: str, target_audience: str, content_type: str, optimization_analysis: str
    ) -> str:
        """Create prompt for schedule recommendations"""
        return f"""
        Create posting schedule recommendations based on this analysis:
        
        Platform: {platform}
        Target Audience: {target_audience}
        Content Type: {content_type}
        
        Analysis:
        {optimization_analysis}
        
        Provide:
        1. Weekly posting schedule
        2. Daily time slots
        3. Content type distribution
        4. Frequency recommendations
        5. Seasonal adjustments
        6. A/B testing suggestions
        
        Format as actionable posting schedule.
        """
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes"""
        words = len(content.split())
        words_per_minute = 200
        reading_time = max(1, round(words / words_per_minute))
        return reading_time
