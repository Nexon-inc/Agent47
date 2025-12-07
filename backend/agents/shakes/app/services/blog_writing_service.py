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
from ..models import ContentProject, ContentPiece, SEOAnalysis

logger = logging.getLogger(__name__)

class BlogWritingService:
    """Service for AI-powered blog and article writing with research and optimization"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
    
    async def initialize(self):
        """Initialize blog writing service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Blog writing service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize blog writing service: {e}")
            raise
    
    async def create_blog_post(
        self,
        user_id: int,
        topic: str,
        target_audience: str,
        word_count_target: int,
        tone: str,
        keywords: List[str],
        research_depth: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Create a comprehensive blog post with AI-powered research and writing"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Create content project
                project = ContentProject(
                    user_id=user_id,
                    title=f"Blog: {topic}",
                    description=f"AI-generated blog post about {topic}",
                    content_type="blog_post",
                    platform="blog",
                    target_audience=target_audience,
                    tone=tone,
                    keywords=keywords,
                    word_count_target=word_count_target,
                    status="draft"
                )
                session.add(project)
                await session.flush()
                
                # Generate research outline using AI Service Manager
                research_prompt = self._create_research_prompt(topic, target_audience, research_depth)
                ai_manager = await get_ai_service_manager()
                messages = [
                    {"role": "system", "content": "You are an AI assistant that creates research outlines for blog posts."},
                    {"role": "user", "content": research_prompt}
                ]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
                research_outline = ai_response.text_content if ai_response.success else ""
                
                # Generate blog content using AI Service Manager
                content_prompt = self._create_content_prompt(
                    topic, target_audience, word_count_target, tone, keywords, research_outline
                )
                messages = [
                    {"role": "system", "content": "You are an AI assistant that writes high-quality blog posts."},
                    {"role": "user", "content": content_prompt}
                ]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=4000, temperature=0.7)
                blog_content = ai_response.text_content if ai_response.success else ""
                
                # Create content piece
                content_piece = ContentPiece(
                    project_id=project.id,
                    title=topic,
                    content=blog_content,
                    content_type="blog_post",
                    platform="blog",
                    word_count=len(blog_content.split()),
                    character_count=len(blog_content),
                    reading_time=len(blog_content.split()) // 200,
                    status="draft",
                    ai_generated=True
                )
                session.add(content_piece)
                await session.flush()
                
                # Generate SEO analysis
                seo_prompt = self._create_seo_prompt(blog_content, keywords)
                # Use AI Service Manager for SEO analysis
                ai_manager = await get_ai_service_manager()
                messages = [
                    {"role": "system", "content": "You are an AI assistant that analyzes SEO for blog content."},
                    {"role": "user", "content": seo_prompt}
                ]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
                seo_analysis = ai_response.text_content if ai_response.success else "{}"
                
                # Create SEO analysis record
                seo_record = SEOAnalysis(
                    project_id=project.id,
                    content_piece_id=content_piece.id,
                    keyword_density=self._calculate_keyword_density(blog_content, keywords),
                    readability_score=self._calculate_readability_score(blog_content),
                    seo_score=self._calculate_seo_score(blog_content, keywords),
                    meta_title=self._generate_meta_title(topic, keywords),
                    meta_description=self._generate_meta_description(blog_content, keywords),
                    h1_tags=self._extract_headings(blog_content, "h1"),
                    h2_tags=self._extract_headings(blog_content, "h2"),
                    h3_tags=self._extract_headings(blog_content, "h3"),
                    analyzed_at=datetime.utcnow()
                )
                session.add(seo_record)
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.blog_post_created", {
                    "project_id": project.id,
                    "content_piece_id": content_piece.id,
                    "user_id": user_id,
                    "topic": topic,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "project_id": project.id,
                    "content_piece_id": content_piece.id,
                    "blog_content": blog_content,
                    "seo_analysis": {
                        "keyword_density": seo_record.keyword_density,
                        "readability_score": seo_record.readability_score,
                        "seo_score": seo_record.seo_score,
                        "meta_title": seo_record.meta_title,
                        "meta_description": seo_record.meta_description
                    },
                    "word_count": content_piece.word_count,
                    "reading_time": content_piece.reading_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Blog post creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def enhance_blog_post(
        self,
        content_piece_id: int,
        enhancement_type: str,
        enhancement_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance existing blog post with additional features"""
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
                
                enhanced_content = content_piece.content
                
                if enhancement_type == "add_call_to_action":
                    enhanced_content = await self._add_call_to_action(enhanced_content, enhancement_params)
                elif enhancement_type == "improve_intro":
                    enhanced_content = await self._improve_introduction(enhanced_content, enhancement_params)
                elif enhancement_type == "add_statistics":
                    enhanced_content = await self._add_statistics(enhanced_content, enhancement_params)
                elif enhancement_type == "enhance_conclusion":
                    enhanced_content = await self._enhance_conclusion(enhanced_content, enhancement_params)
                
                # Update content piece
                content_piece.content = enhanced_content
                content_piece.word_count = len(enhanced_content.split())
                content_piece.character_count = len(enhanced_content)
                content_piece.reading_time = len(enhanced_content.split()) // 200
                content_piece.updated_at = datetime.utcnow()
                
                await session.commit()
                
                return {
                    "success": True,
                    "enhanced_content": enhanced_content,
                    "word_count": content_piece.word_count,
                    "reading_time": content_piece.reading_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Blog post enhancement failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_blog_analytics(
        self,
        content_piece_id: int
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for a blog post"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece and related data
                content_result = await session.execute(
                    select(ContentPiece).where(ContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Get SEO analysis
                seo_result = await session.execute(
                    select(SEOAnalysis).where(SEOAnalysis.content_piece_id == content_piece_id)
                )
                seo_analysis = seo_result.scalar_one_or_none()
                
                # Calculate content quality metrics
                quality_metrics = await self._calculate_content_quality(content_piece.content)
                
                return {
                    "success": True,
                    "content_metrics": {
                        "word_count": content_piece.word_count,
                        "character_count": content_piece.character_count,
                        "reading_time": content_piece.reading_time,
                        "ai_generated": content_piece.ai_generated,
                        "status": content_piece.status.value
                    },
                    "seo_metrics": {
                        "keyword_density": seo_analysis.keyword_density if seo_analysis else {},
                        "readability_score": seo_analysis.readability_score if seo_analysis else 0,
                        "seo_score": seo_analysis.seo_score if seo_analysis else 0,
                        "meta_title": seo_analysis.meta_title if seo_analysis else "",
                        "meta_description": seo_analysis.meta_description if seo_analysis else ""
                    },
                    "quality_metrics": quality_metrics,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Blog analytics retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_research_prompt(self, topic: str, target_audience: str, research_depth: str) -> str:
        """Create prompt for research outline generation"""
        return f"""
        Create a comprehensive research outline for a blog post about "{topic}" targeting {target_audience}.
        Research depth: {research_depth}
        
        Include:
        1. Key subtopics to cover
        2. Important statistics and data points
        3. Expert opinions and quotes
        4. Current trends and developments
        5. Common questions and concerns
        6. Actionable insights and takeaways
        
        Format as a structured outline with bullet points.
        """
    
    def _create_content_prompt(
        self, topic: str, target_audience: str, word_count: int, tone: str, 
        keywords: List[str], research_outline: str
    ) -> str:
        """Create prompt for blog content generation"""
        return f"""
        Write a comprehensive blog post about "{topic}" based on this research outline:
        {research_outline}
        
        Requirements:
        - Target audience: {target_audience}
        - Word count: approximately {word_count} words
        - Tone: {tone}
        - Include these keywords naturally: {', '.join(keywords)}
        - Structure with clear headings (H1, H2, H3)
        - Include introduction, body sections, and conclusion
        - Make it engaging and informative
        - Include call-to-action at the end
        
        Write the complete blog post with proper formatting.
        """
    
    def _create_seo_prompt(self, content: str, keywords: List[str]) -> str:
        """Create prompt for SEO analysis"""
        return f"""
        Analyze this blog content for SEO optimization:
        
        Content: {content[:1000]}...
        
        Keywords to optimize for: {', '.join(keywords)}
        
        Provide:
        1. Keyword density analysis
        2. Readability score (0-100)
        3. Overall SEO score (0-100)
        4. Meta title suggestions
        5. Meta description suggestions
        6. Heading structure analysis
        7. Internal linking opportunities
        8. Schema markup suggestions
        
        Format as JSON with these fields.
        """
    
    def _calculate_keyword_density(self, content: str, keywords: List[str]) -> Dict[str, float]:
        """Calculate keyword density in content"""
        word_count = len(content.lower().split())
        density = {}
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            keyword_count = content.lower().count(keyword_lower)
            density[keyword] = round((keyword_count / word_count) * 100, 2)
        
        return density
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate Flesch Reading Ease score"""
        sentences = len([s for s in content.split('.') if s.strip()])
        words = len(content.split())
        syllables = sum(len([c for c in word if c in 'aeiouy']) for word in content.lower().split())
        
        if sentences == 0 or words == 0:
            return 0.0
        
        score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        return max(0.0, min(100.0, score))
    
    def _calculate_seo_score(self, content: str, keywords: List[str]) -> float:
        """Calculate overall SEO score"""
        score = 0.0
        
        # Keyword presence
        keyword_score = sum(1 for keyword in keywords if keyword.lower() in content.lower())
        score += (keyword_score / len(keywords)) * 30
        
        # Content length
        word_count = len(content.split())
        if word_count >= 1500:
            score += 20
        elif word_count >= 1000:
            score += 15
        elif word_count >= 500:
            score += 10
        
        # Heading structure
        if "# " in content or "<h1>" in content:
            score += 15
        if "## " in content or "<h2>" in content:
            score += 10
        if "### " in content or "<h3>" in content:
            score += 5
        
        # Meta information
        if len(content) > 160:
            score += 10
        
        return min(100.0, score)
    
    def _generate_meta_title(self, topic: str, keywords: List[str]) -> str:
        """Generate SEO-optimized meta title"""
        title = f"{topic} - Complete Guide"
        if keywords:
            title += f" | {keywords[0].title()}"
        return title[:60]
    
    def _generate_meta_description(self, content: str, keywords: List[str]) -> str:
        """Generate SEO-optimized meta description"""
        description = content[:150].strip()
        if keywords:
            description += f" Learn about {', '.join(keywords[:2])}."
        return description[:160]
    
    def _extract_headings(self, content: str, heading_type: str) -> List[str]:
        """Extract headings from content"""
        headings = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if heading_type == "h1" and (line.startswith('# ') or line.startswith('<h1>')):
                headings.append(line.replace('# ', '').replace('<h1>', '').replace('</h1>', ''))
            elif heading_type == "h2" and (line.startswith('## ') or line.startswith('<h2>')):
                headings.append(line.replace('## ', '').replace('<h2>', '').replace('</h2>', ''))
            elif heading_type == "h3" and (line.startswith('### ') or line.startswith('<h3>')):
                headings.append(line.replace('### ', '').replace('<h3>', '').replace('</h3>', ''))
        
        return headings
    
    async def _add_call_to_action(self, content: str, params: Dict[str, Any]) -> str:
        """Add call-to-action to blog content"""
        cta_prompt = f"""
        Add a compelling call-to-action to this blog post:
        
        {content}
        
        CTA type: {params.get('cta_type', 'general')}
        CTA style: {params.get('cta_style', 'encouraging')}
        
        Add the CTA at the end of the post, making it natural and engaging.
        """
        
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [
            {"role": "system", "content": "You are an AI assistant that creates compelling call-to-action content."},
            {"role": "user", "content": cta_prompt}
        ]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.7)
        cta_response = ai_response.text_content if ai_response.success else ""
        return content + "\n\n" + cta_response
    
    async def _improve_introduction(self, content: str, params: Dict[str, Any]) -> str:
        """Improve the introduction of blog content"""
        intro_prompt = f"""
        Improve the introduction of this blog post:
        
        {content}
        
        Make it more engaging, hook the reader, and clearly state what they'll learn.
        Keep the rest of the content unchanged.
        """
        
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [
            {"role": "system", "content": "You are an AI assistant that improves blog post introductions."},
            {"role": "user", "content": intro_prompt}
        ]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=300, temperature=0.7)
        improved_content = ai_response.text_content if ai_response.success else content
        return improved_content
    
    async def _add_statistics(self, content: str, params: Dict[str, Any]) -> str:
        """Add relevant statistics to blog content"""
        stats_prompt = f"""
        Add relevant statistics and data points to this blog post:
        
        {content}
        
        Statistics focus: {params.get('focus', 'general')}
        Add 3-5 relevant statistics with proper citations.
        Integrate them naturally into the content.
        """
        
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [
            {"role": "system", "content": "You are an AI assistant that adds statistics to blog content."},
            {"role": "user", "content": stats_prompt}
        ]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.7)
        enhanced_content = ai_response.text_content if ai_response.success else content
        return enhanced_content
    
    async def _enhance_conclusion(self, content: str, params: Dict[str, Any]) -> str:
        """Enhance the conclusion of blog content"""
        conclusion_prompt = f"""
        Enhance the conclusion of this blog post:
        
        {content}
        
        Make it more impactful, summarize key points, and provide clear next steps.
        Keep the rest of the content unchanged.
        """
        
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [
            {"role": "system", "content": "You are an AI assistant that enhances blog post conclusions."},
            {"role": "user", "content": conclusion_prompt}
        ]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=300, temperature=0.7)
        enhanced_content = ai_response.text_content if ai_response.success else content
        return enhanced_content
    
    async def _calculate_content_quality(self, content: str) -> Dict[str, Any]:
        """Calculate comprehensive content quality metrics"""
        return {
            "readability_score": self._calculate_readability_score(content),
            "sentence_count": len([s for s in content.split('.') if s.strip()]),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "average_sentence_length": len(content.split()) / max(1, len([s for s in content.split('.') if s.strip()])),
            "complex_word_ratio": self._calculate_complex_word_ratio(content),
            "content_structure_score": self._calculate_structure_score(content)
        }
    
    def _calculate_complex_word_ratio(self, content: str) -> float:
        """Calculate ratio of complex words (3+ syllables)"""
        words = content.lower().split()
        complex_words = sum(1 for word in words if len([c for c in word if c in 'aeiouy']) >= 3)
        return round((complex_words / len(words)) * 100, 2) if words else 0.0
    
    def _calculate_structure_score(self, content: str) -> float:
        """Calculate content structure score"""
        score = 0.0
        
        # Check for clear sections
        if 'introduction' in content.lower() or 'intro' in content.lower():
            score += 20
        if 'conclusion' in content.lower():
            score += 20
        
        # Check for bullet points or lists
        if '-' in content or '*' in content or '1.' in content:
            score += 15
        
        # Check for examples
        if 'example' in content.lower() or 'for instance' in content.lower():
            score += 15
        
        # Check for actionable content
        if 'step' in content.lower() or 'tip' in content.lower() or 'action' in content.lower():
            score += 15
        
        # Check for proper formatting
        if '\n\n' in content:
            score += 15
        
        return min(100.0, score)
