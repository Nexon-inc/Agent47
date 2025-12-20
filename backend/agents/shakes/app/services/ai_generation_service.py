import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ContentProject, ContentPiece

logger = logging.getLogger(__name__)

class AIContentGenerationService:
    """Service for AI-powered content generation across multiple formats"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
    
    async def initialize(self):
        """Initialize AI content generation service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            
            self._initialized = True
            logger.info("AI content generation service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI content generation service: {e}")
            raise
    
    async def generate_content(
        self,
        user_id: int,
        content_type: str,
        topic: str,
        target_audience: str,
        tone: str,
        word_count_target: int,
        platform: str,
        keywords: List[str],
        content_goals: List[str]
    ) -> Dict[str, Any]:
        """Generate AI-powered content based on specifications"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Use the new AI service manager for content generation
            content_prompt = self._build_content_prompt(
                content_type, topic, target_audience, tone, 
                word_count_target, platform, keywords, content_goals
            )
            
            messages = [
                {"role": "system", "content": "You are a professional content creator specializing in engaging, high-quality content across multiple platforms."},
                {"role": "user", "content": content_prompt}
            ]
            
            # Generate content using AI service manager
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=word_count_target * 2,  # Allow for longer generation
                temperature=0.7
            )
            
            if not response.success:
                return {
                    "success": False,
                    "error": f"Content generation failed: {response.error}",
                    "fallback_used": response.fallback_used
                }
            
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Create content project
                project = ContentProject(
                    user_id=user_id,
                    title=f"AI Generated: {topic}",
                    description=f"AI-generated {content_type} about {topic}",
                    content_type=content_type,
                    target_audience=target_audience,
                    tone=tone,
                    status="draft"
                )
                session.add(project)
                await session.flush()
                
                # Create content piece with generated content
                content_piece = ContentPiece(
                    project_id=project.id,
                    title=f"{content_type.title()}: {topic}",
                    content=response.text_content,
                    content_type=content_type,
                    platform=platform,
                    status="generated",
                    metadata={
                        "target_audience": target_audience,
                        "tone": tone,
                        "word_count_target": word_count_target,
                        "keywords": keywords,
                        "content_goals": content_goals,
                        "ai_model_used": response.service_used,
                        "fallback_used": response.fallback_used,
                        "response_time_ms": response.response_time_ms
                    }
                )
                session.add(content_piece)
                await session.commit()
                
                return {
                    "success": True,
                    "project_id": project.id,
                    "content_id": content_piece.id,
                    "content": response.text_content,
                    "metadata": {
                        "ai_model_used": response.service_used,
                        "fallback_used": response.fallback_used,
                        "response_time_ms": response.response_time_ms
                    }
                }
                
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_content_prompt(
        self,
        content_type: str,
        topic: str,
        target_audience: str,
        tone: str,
        word_count_target: int,
        platform: str,
        keywords: List[str],
        content_goals: List[str]
    ) -> str:
        """Build a comprehensive content generation prompt"""
        prompt = f"""Create a {content_type} about "{topic}" with the following specifications:

Target Audience: {target_audience}
Tone: {tone}
Word Count Target: {word_count_target} words
Platform: {platform}
Keywords to include: {', '.join(keywords)}
Content Goals: {', '.join(content_goals)}

Please create engaging, high-quality content that:
1. Speaks directly to the target audience
2. Maintains the specified tone throughout
3. Naturally incorporates the provided keywords
4. Achieves the stated content goals
5. Is optimized for the specified platform
6. Meets the word count target

Make the content compelling, informative, and actionable."""
        
        return prompt
    
    async def generate_content_batch(
        self,
        user_id: int,
        content_specifications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate multiple content pieces in batch"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Create batch project
                batch_project = ContentProject(
                    user_id=user_id,
                    title="AI Generated Content Batch",
                    description="Batch of AI-generated content pieces",
                    content_type="content_batch",
                    status="draft"
                )
                session.add(batch_project)
                await session.flush()
                
                generated_pieces = []
                for spec in content_specifications:
                    content_type = spec.get("content_type", "generic")
                    topic = spec.get("topic", "")
                    target_audience = spec.get("target_audience", "general")
                    tone = spec.get("tone", "professional")
                    word_count_target = spec.get("word_count_target", 500)
                    platform = spec.get("platform", "general")
                    keywords = spec.get("keywords", [])
                    content_goals = spec.get("content_goals", [])
                    
                    # Generate content
                    if content_type == "blog_post":
                        content = await self._generate_blog_content(topic, target_audience, tone, word_count_target, keywords, content_goals)
                    elif content_type == "social_media":
                        content = await self._generate_social_content(topic, target_audience, tone, platform, keywords, content_goals)
                    elif content_type == "email":
                        content = await self._generate_email_content(topic, target_audience, tone, word_count_target, keywords, content_goals)
                    elif content_type == "ad_copy":
                        content = await self._generate_ad_copy(topic, target_audience, tone, platform, keywords, content_goals)
                    else:
                        content = await self._generate_generic_content(topic, target_audience, tone, word_count_target, content_type, keywords, content_goals)
                    
                    # Create content piece
                    content_piece = ContentPiece(
                        project_id=batch_project.id,
                        title=f"{topic} - {content_type}",
                        content=content,
                        content_type=content_type,
                        platform=platform,
                        word_count=len(content.split()),
                        character_count=len(content),
                        reading_time=self._calculate_reading_time(content),
                        status="draft",
                        ai_generated=True
                    )
                    session.add(content_piece)
                    await session.flush()
                    
                    generated_pieces.append({
                        "content_piece_id": content_piece.id,
                        "content_type": content_type,
                        "platform": platform,
                        "content": content,
                        "word_count": content_piece.word_count,
                        "reading_time": content_piece.reading_time
                    })
                
                await session.commit()
                
                return {
                    "success": True,
                    "project_id": batch_project.id,
                    "generated_pieces": generated_pieces,
                    "total_pieces": len(generated_pieces),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"AI content batch generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def enhance_content(
        self,
        content_piece_id: int,
        enhancement_type: str,
        enhancement_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance existing content with AI"""
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
                
                # Generate enhancement
                enhancement_prompt = self._create_enhancement_prompt(
                    content_piece.content, content_piece.content_type, enhancement_type, enhancement_params
                )
                # Use AI Service Manager instead of NLPUtils
                if not self.ai_service_manager:
                    self.ai_service_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that enhances content."}, {"role": "user", "content": enhancement_prompt}]
                ai_response = await self.ai_service_manager.generate_text(messages=messages, max_tokens=3000, temperature=0.7)
                enhanced_content = ai_response.text_content if ai_response.success else ""
                
                # Update content piece
                content_piece.content = enhanced_content
                content_piece.word_count = len(enhanced_content.split())
                content_piece.character_count = len(enhanced_content)
                content_piece.reading_time = self._calculate_reading_time(enhanced_content)
                content_piece.updated_at = datetime.utcnow()
                
                await session.commit()
                
                return {
                    "success": True,
                    "enhanced_content": enhanced_content,
                    "enhancement_type": enhancement_type,
                    "word_count": content_piece.word_count,
                    "reading_time": content_piece.reading_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content enhancement failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_blog_content(
        self, topic: str, target_audience: str, tone: str, word_count_target: int, keywords: List[str], content_goals: List[str]
    ) -> str:
        """Generate blog post content"""
        prompt = f"""
        Write a comprehensive blog post about: {topic}
        
        Target Audience: {target_audience}
        Tone: {tone}
        Target Word Count: {word_count_target}
        Keywords to include: {', '.join(keywords)}
        Content Goals: {', '.join(content_goals)}
        
        Structure:
        1. Engaging introduction
        2. Main content with subheadings
        3. Practical examples or case studies
        4. Actionable takeaways
        5. Strong conclusion with call-to-action
        
        Requirements:
        - Include all specified keywords naturally
        - Maintain consistent {tone} tone throughout
        - Provide valuable, actionable information
        - Use engaging subheadings
        - Include relevant examples
        - End with clear next steps for readers
        
        Generate the complete blog post.
        """
        # Use AI Service Manager instead of NLPUtils
        if not self.ai_service_manager:
            self.ai_service_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates blog posts."}, {"role": "user", "content": prompt}]
        ai_response = await self.ai_service_manager.generate_text(messages=messages, max_tokens=4000, temperature=0.7)
        return ai_response.text_content if ai_response.success else ""
    
    async def _generate_social_content(
        self, topic: str, target_audience: str, tone: str, platform: str, keywords: List[str], content_goals: List[str]
    ) -> str:
        """Generate social media content"""
        prompt = f"""
        Create engaging social media content for {platform} about: {topic}
        
        Target Audience: {target_audience}
        Tone: {tone}
        Platform: {platform}
        Keywords: {', '.join(keywords)}
        Goals: {', '.join(content_goals)}
        
        Platform-specific requirements:
        - {platform} character limits and best practices
        - Platform-appropriate hashtags
        - Engaging hook to capture attention
        - Clear call-to-action
        - Visual content suggestions if applicable
        
        Generate the complete social media post.
        """
        # Use AI Service Manager instead of NLPUtils
        if not self.ai_service_manager:
            self.ai_service_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates blog posts."}, {"role": "user", "content": prompt}]
        ai_response = await self.ai_service_manager.generate_text(messages=messages, max_tokens=4000, temperature=0.7)
        return ai_response.text_content if ai_response.success else ""
    
    async def _generate_email_content(
        self, topic: str, target_audience: str, tone: str, word_count_target: int, keywords: List[str], content_goals: List[str]
    ) -> str:
        """Generate email content"""
        prompt = f"""
        Write an email about: {topic}
        
        Target Audience: {target_audience}
        Tone: {tone}
        Target Word Count: {word_count_target}
        Keywords: {', '.join(keywords)}
        Goals: {', '.join(content_goals)}
        
        Structure:
        1. Compelling subject line
        2. Engaging opening
        3. Main message with value
        4. Clear call-to-action
        5. Professional closing
        
        Requirements:
        - Mobile-friendly formatting
        - Clear, scannable content
        - Strong subject line
        - Compelling call-to-action
        - Professional yet {tone} tone
        
        Generate the complete email.
        """
        # Use AI Service Manager instead of NLPUtils
        if not self.ai_service_manager:
            self.ai_service_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates blog posts."}, {"role": "user", "content": prompt}]
        ai_response = await self.ai_service_manager.generate_text(messages=messages, max_tokens=4000, temperature=0.7)
        return ai_response.text_content if ai_response.success else ""
    
    async def _generate_ad_copy(
        self, topic: str, target_audience: str, tone: str, platform: str, keywords: List[str], content_goals: List[str]
    ) -> str:
        """Generate ad copy"""
        prompt = f"""
        Create compelling ad copy for {platform} about: {topic}
        
        Target Audience: {target_audience}
        Tone: {tone}
        Platform: {platform}
        Keywords: {', '.join(keywords)}
        Goals: {', '.join(content_goals)}
        
        Include:
        1. Attention-grabbing headline
        2. Compelling value proposition
        3. Social proof or benefits
        4. Strong call-to-action
        5. Platform-specific optimizations
        
        Requirements:
        - Follow {platform} ad guidelines
        - Focus on benefits over features
        - Create urgency or scarcity if appropriate
        - Use power words and emotional triggers
        - Clear, action-oriented CTA
        
        Generate the complete ad copy.
        """
        # Use AI Service Manager instead of NLPUtils
        if not self.ai_service_manager:
            self.ai_service_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates blog posts."}, {"role": "user", "content": prompt}]
        ai_response = await self.ai_service_manager.generate_text(messages=messages, max_tokens=4000, temperature=0.7)
        return ai_response.text_content if ai_response.success else ""
    
    async def _generate_generic_content(
        self, topic: str, target_audience: str, tone: str, word_count_target: int, content_type: str, keywords: List[str], content_goals: List[str]
    ) -> str:
        """Generate generic content"""
        prompt = f"""
        Create {content_type} content about: {topic}
        
        Target Audience: {target_audience}
        Tone: {tone}
        Target Word Count: {word_count_target}
        Content Type: {content_type}
        Keywords: {', '.join(keywords)}
        Goals: {', '.join(content_goals)}
        
        Requirements:
        - Appropriate for {content_type} format
        - Engaging and informative
        - Include specified keywords naturally
        - Maintain {tone} tone throughout
        - Meet word count target
        - Achieve specified goals
        
        Generate the complete {content_type} content.
        """
        # Use AI Service Manager instead of NLPUtils
        if not self.ai_service_manager:
            self.ai_service_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates blog posts."}, {"role": "user", "content": prompt}]
        ai_response = await self.ai_service_manager.generate_text(messages=messages, max_tokens=4000, temperature=0.7)
        return ai_response.text_content if ai_response.success else ""
    
    def _create_enhancement_prompt(
        self, content: str, content_type: str, enhancement_type: str, enhancement_params: Dict[str, Any]
    ) -> str:
        """Create prompt for content enhancement"""
        return f"""
        Enhance this {content_type} content with {enhancement_type}:
        
        Original Content:
        {content}
        
        Enhancement Type: {enhancement_type}
        Parameters: {enhancement_params}
        
        Requirements:
        - Improve {enhancement_type} aspects
        - Maintain original message and tone
        - Enhance readability and engagement
        - Apply enhancement parameters
        - Keep content authentic and valuable
        
        Generate the enhanced content.
        """
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes"""
        words = len(content.split())
        words_per_minute = 200
        reading_time = max(1, round(words / words_per_minute))
        return reading_time


# Backwards-compatible alias: some modules import AIGenerationService
AIGenerationService = AIContentGenerationService
