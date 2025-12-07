import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.event_bus.kafka_manager import EventBus
# NLPUtils removed - using AI Service Manager instead
from ..database import get_shakes_database
from ..models import ContentProject, ContentPiece, PlatformType

logger = logging.getLogger(__name__)

class SocialMediaContentService:
    """Service for creating platform-specific social media content with AI optimization"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
    
    async def initialize(self):
        """Initialize social media content service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Social media content service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize social media content service: {e}")
            raise
    
    async def create_social_media_content(
        self,
        user_id: int,
        platform: str,
        content_type: str,
        topic: str,
        target_audience: str,
        tone: str,
        call_to_action: str,
        hashtags: List[str] = None,
        image_description: str = None
    ) -> Dict[str, Any]:
        """Create platform-optimized social media content"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Create content project
                project = ContentProject(
                    user_id=user_id,
                    title=f"Social Media: {topic}",
                    description=f"AI-generated {platform} content about {topic}",
                    content_type="social_media",
                    platform=platform,
                    target_audience=target_audience,
                    tone=tone,
                    keywords=hashtags or [],
                    status="draft"
                )
                session.add(project)
                await session.flush()
                
                # Generate platform-specific content
                content_prompt = self._create_platform_content_prompt(
                    platform, content_type, topic, target_audience, tone, call_to_action, hashtags
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [
                    {"role": "system", "content": "You are an AI assistant that creates engaging social media content."},
                    {"role": "user", "content": content_prompt}
                ]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.8)
                social_content = ai_response.text_content if ai_response.success else ""
                
                # Generate image description if requested
                image_desc = ""
                if image_description:
                    image_prompt = self._create_image_description_prompt(topic, platform, tone)
                    messages = [
                        {"role": "system", "content": "You are an AI assistant that creates image descriptions for social media."},
                        {"role": "user", "content": image_prompt}
                    ]
                    ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.7)
                    image_desc = ai_response.text_content if ai_response.success else ""
                
                # Create content piece
                content_piece = ContentPiece(
                    project_id=project.id,
                    title=topic,
                    content=social_content,
                    content_type="social_media",
                    platform=platform,
                    word_count=len(social_content.split()),
                    character_count=len(social_content),
                    reading_time=1,
                    status="draft",
                    ai_generated=True
                )
                session.add(content_piece)
                await session.flush()
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.social_content_created", {
                    "project_id": project.id,
                    "content_piece_id": content_piece.id,
                    "user_id": user_id,
                    "platform": platform,
                    "topic": topic,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "project_id": project.id,
                    "content_piece_id": content_piece.id,
                    "social_content": social_content,
                    "image_description": image_desc,
                    "platform_optimizations": self._get_platform_optimizations(platform),
                    "hashtag_suggestions": self._generate_hashtag_suggestions(topic, platform),
                    "posting_tips": self._get_posting_tips(platform, content_type),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Social media content creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_content_series(
        self,
        user_id: int,
        platform: str,
        series_topic: str,
        post_count: int,
        content_style: str,
        target_audience: str,
        tone: str
    ) -> Dict[str, Any]:
        """Create a series of related social media posts"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Create content project for series
                project = ContentProject(
                    user_id=user_id,
                    title=f"Content Series: {series_topic}",
                    description=f"AI-generated {post_count}-post series for {platform}",
                    content_type="social_media",
                    platform=platform,
                    target_audience=target_audience,
                    tone=tone,
                    status="draft"
                )
                session.add(project)
                await session.flush()
                
                # Generate series outline
                series_prompt = self._create_series_outline_prompt(
                    series_topic, post_count, content_style, platform
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates social media series outlines."}, {"role": "user", "content": series_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
                series_outline = ai_response.text_content if ai_response.success else ""
                
                # Generate individual posts
                posts = []
                for i in range(post_count):
                    post_prompt = self._create_series_post_prompt(
                        series_topic, i + 1, post_count, content_style, platform, target_audience, tone
                    )
                    messages = [{"role": "system", "content": "You are an AI assistant that creates social media posts."}, {"role": "user", "content": post_prompt}]
                    ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
                    post_content = ai_response.text_content if ai_response.success else ""
                    
                    # Create content piece for each post
                    content_piece = ContentPiece(
                        project_id=project.id,
                        title=f"{series_topic} - Part {i + 1}",
                        content=post_content,
                        content_type="social_media",
                        platform=platform,
                        word_count=len(post_content.split()),
                        character_count=len(post_content),
                        reading_time=1,
                        status="draft",
                        ai_generated=True
                    )
                    session.add(content_piece)
                    await session.flush()
                    
                    posts.append({
                        "post_number": i + 1,
                        "content_piece_id": content_piece.id,
                        "content": post_content,
                        "scheduled_day": i + 1
                    })
                
                await session.commit()
                
                return {
                    "success": True,
                    "project_id": project.id,
                    "series_outline": series_outline,
                    "posts": posts,
                    "platform": platform,
                    "post_count": post_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content series creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_for_platform(
        self,
        content_piece_id: int,
        target_platform: str
    ) -> Dict[str, Any]:
        """Optimize existing content for a specific platform"""
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
                
                # Generate platform-optimized version
                optimization_prompt = self._create_platform_optimization_prompt(
                    content_piece.content, target_platform, content_piece.platform
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that optimizes social media content."}, {"role": "user", "content": optimization_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
                optimized_content = ai_response.text_content if ai_response.success else ""
                
                # Update content piece
                content_piece.content = optimized_content
                content_piece.platform = target_platform
                content_piece.word_count = len(optimized_content.split())
                content_piece.character_count = len(optimized_content)
                content_piece.updated_at = datetime.utcnow()
                
                await session.commit()
                
                return {
                    "success": True,
                    "optimized_content": optimized_content,
                    "target_platform": target_platform,
                    "platform_specific_tips": self._get_platform_optimizations(target_platform),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Platform optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_platform_content_prompt(
        self, platform: str, content_type: str, topic: str, target_audience: str,
        tone: str, call_to_action: str, hashtags: List[str]
    ) -> str:
        """Create prompt for platform-specific content generation"""
        platform_guidelines = self._get_platform_guidelines(platform)
        
        return f"""
        Create {content_type} content for {platform} about "{topic}".
        
        Platform Guidelines:
        {platform_guidelines}
        
        Requirements:
        - Target audience: {target_audience}
        - Tone: {tone}
        - Call-to-action: {call_to_action}
        - Hashtags: {', '.join(hashtags) if hashtags else 'Generate relevant hashtags'}
        - Optimize for {platform} best practices
        - Include emojis where appropriate
        - Make it engaging and shareable
        
        Generate the complete {platform} post content.
        """
    
    def _create_image_description_prompt(self, topic: str, platform: str, tone: str) -> str:
        """Create prompt for image description generation"""
        return f"""
        Create an image description for a {platform} post about "{topic}".
        
        Requirements:
        - Tone: {tone}
        - Platform: {platform}
        - Include visual elements, colors, and composition
        - Make it engaging and descriptive
        - Keep it under 100 characters for accessibility
        
        Generate the image description.
        """
    
    def _create_series_outline_prompt(
        self, series_topic: str, post_count: int, content_style: str, platform: str
    ) -> str:
        """Create prompt for content series outline"""
        return f"""
        Create an outline for a {post_count}-post content series about "{series_topic}" for {platform}.
        
        Content Style: {content_style}
        Platform: {platform}
        
        Requirements:
        - Each post should build on the previous one
        - Include clear progression and learning path
        - Make each post valuable on its own
        - Consider {platform} best practices
        - Include post themes and key messages
        
        Generate a structured outline for the series.
        """
    
    def _create_series_post_prompt(
        self, series_topic: str, post_number: int, total_posts: int,
        content_style: str, platform: str, target_audience: str, tone: str
    ) -> str:
        """Create prompt for individual series post"""
        return f"""
        Create post {post_number} of {total_posts} in a series about "{series_topic}" for {platform}.
        
        Content Style: {content_style}
        Platform: {platform}
        Target Audience: {target_audience}
        Tone: {tone}
        
        Requirements:
        - This is post {post_number} of {total_posts}
        - Make it valuable on its own while fitting the series
        - Follow {platform} best practices
        - Include engaging hook and clear value
        - Add call-to-action appropriate for this post number
        
        Generate the complete post content.
        """
    
    def _create_platform_optimization_prompt(
        self, original_content: str, target_platform: str, original_platform: str
    ) -> str:
        """Create prompt for platform optimization"""
        target_guidelines = self._get_platform_guidelines(target_platform)
        
        return f"""
        Optimize this {original_platform} content for {target_platform}:
        
        Original Content:
        {original_content}
        
        {target_platform} Guidelines:
        {target_guidelines}
        
        Requirements:
        - Adapt content for {target_platform} best practices
        - Maintain the core message and value
        - Optimize length, format, and style
        - Include platform-specific elements
        - Ensure it performs well on {target_platform}
        
        Generate the {target_platform}-optimized version.
        """
    
    def _get_platform_guidelines(self, platform: str) -> str:
        """Get platform-specific content guidelines"""
        guidelines = {
            "facebook": """
            - Optimal post length: 40-80 characters for engagement
            - Use questions to encourage comments
            - Include visual content descriptions
            - Post timing: 1-4 PM for best engagement
            - Use Facebook-specific features like polls
            """,
            "instagram": """
            - Caption length: 125-138 characters for preview
            - Use line breaks for readability
            - Include relevant hashtags (5-15)
            - Emphasize visual storytelling
            - Use Instagram-specific emojis and trends
            """,
            "twitter": """
            - Character limit: 280 characters
            - Use concise, impactful language
            - Include relevant hashtags (1-3)
            - Encourage retweets and replies
            - Use Twitter-specific features like threads
            """,
            "linkedin": """
            - Professional tone and language
            - Longer, thought-leadership content
            - Include industry insights and expertise
            - Use LinkedIn-specific hashtags
            - Encourage professional networking
            """,
            "tiktok": """
            - Short, engaging content (15-60 seconds)
            - Use trending sounds and hashtags
            - Include clear call-to-action
            - Focus on entertainment value
            - Use TikTok-specific features and trends
            """
        }
        
        return guidelines.get(platform.lower(), "General social media best practices apply.")
    
    def _get_platform_optimizations(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific optimization tips"""
        optimizations = {
            "facebook": {
                "optimal_length": "40-80 characters",
                "best_times": ["1-4 PM", "7-9 PM"],
                "content_types": ["questions", "videos", "images", "links"],
                "engagement_tips": ["ask questions", "use polls", "share stories"]
            },
            "instagram": {
                "optimal_length": "125-138 characters",
                "best_times": ["2-3 PM", "8-9 PM"],
                "content_types": ["carousels", "reels", "stories", "posts"],
                "engagement_tips": ["use hashtags", "post stories", "engage with comments"]
            },
            "twitter": {
                "optimal_length": "280 characters",
                "best_times": ["9-11 AM", "1-3 PM"],
                "content_types": ["tweets", "threads", "polls", "spaces"],
                "engagement_tips": ["use hashtags", "retweet others", "join conversations"]
            },
            "linkedin": {
                "optimal_length": "1000-2000 characters",
                "best_times": ["8-10 AM", "5-6 PM"],
                "content_types": ["articles", "posts", "polls", "videos"],
                "engagement_tips": ["share insights", "comment on others", "build network"]
            },
            "tiktok": {
                "optimal_length": "15-60 seconds",
                "best_times": ["6-10 PM", "12-2 PM"],
                "content_types": ["videos", "duets", "challenges", "trends"],
                "engagement_tips": ["use trending sounds", "participate in challenges", "engage with comments"]
            }
        }
        
        return optimizations.get(platform.lower(), {})
    
    def _generate_hashtag_suggestions(self, topic: str, platform: str) -> List[str]:
        """Generate relevant hashtag suggestions"""
        base_hashtags = [topic.lower().replace(" ", ""), f"#{topic.lower().replace(' ', '')}"]
        
        platform_hashtags = {
            "instagram": ["#instagood", "#photooftheday", "#love", "#fashion", "#beautiful"],
            "twitter": ["#trending", "#news", "#tech", "#business", "#innovation"],
            "linkedin": ["#business", "#leadership", "#innovation", "#networking", "#professional"],
            "facebook": ["#facebook", "#social", "#community", "#friends", "#family"],
            "tiktok": ["#fyp", "#viral", "#trending", "#foryou", "#tiktok"]
        }
        
        return base_hashtags + platform_hashtags.get(platform.lower(), [])
    
    def _get_posting_tips(self, platform: str, content_type: str) -> List[str]:
        """Get platform-specific posting tips"""
        tips = {
            "facebook": [
                "Post when your audience is most active (1-4 PM)",
                "Use Facebook Insights to track performance",
                "Engage with comments within the first hour",
                "Mix content types for variety"
            ],
            "instagram": [
                "Post consistently at optimal times",
                "Use Instagram Stories for daily engagement",
                "Engage with relevant hashtags and accounts",
                "Create a cohesive visual aesthetic"
            ],
            "twitter": [
                "Tweet multiple times per day for visibility",
                "Use trending hashtags strategically",
                "Engage with your followers' tweets",
                "Keep content concise and impactful"
            ],
            "linkedin": [
                "Post during business hours for professional audience",
                "Share industry insights and thought leadership",
                "Engage with your network's content",
                "Use LinkedIn-specific features like polls"
            ],
            "tiktok": [
                "Post 1-3 times per day for algorithm favor",
                "Use trending sounds and hashtags",
                "Engage with comments and duets",
                "Create authentic, entertaining content"
            ]
        }
        
        return tips.get(platform.lower(), ["Focus on consistent posting and engagement"])
