import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ContentProject, ContentPiece, SEOAnalysis

logger = logging.getLogger(__name__)

class SEOOptimizationService:
    """Service for comprehensive SEO optimization and keyword integration"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 3000,
            "temperature": 0.5
        }
    
    async def initialize(self):
        """Initialize SEO optimization service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("SEO optimization service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SEO optimization service: {e}")
            raise
    
    async def optimize_content_seo(
        self,
        content_piece_id: int,
        target_keywords: List[str],
        content_type: str,
        platform: str
    ) -> Dict[str, Any]:
        """Optimize content for SEO with target keywords"""
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
                
                # Generate SEO-optimized content
                seo_prompt = self._create_seo_optimization_prompt(
                    content_piece.content, target_keywords, content_type, platform
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that optimizes content for SEO."}, {"role": "user", "content": seo_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=3000, temperature=0.5)
                optimized_content = ai_response.text_content if ai_response.success else ""
                
                # Generate meta title and description
                meta_prompt = self._create_meta_generation_prompt(
                    content_piece.title, target_keywords, content_type
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that generates SEO meta titles and descriptions."}, {"role": "user", "content": meta_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.5)
                meta_content = ai_response.text_content if ai_response.success else ""
                
                # Parse meta content
                meta_title = self._extract_meta_title(meta_content)
                meta_description = self._extract_meta_description(meta_content)
                
                # Update content piece
                content_piece.content = optimized_content
                content_piece.word_count = len(optimized_content.split())
                content_piece.character_count = len(optimized_content)
                content_piece.updated_at = datetime.utcnow()
                
                # Update or create SEO analysis
                seo_result = await session.execute(
                    select(SEOAnalysis).where(SEOAnalysis.content_piece_id == content_piece_id)
                )
                seo_analysis = seo_result.scalar_one_or_none()
                
                if seo_analysis:
                    seo_analysis.keyword_density = self._calculate_keyword_density(optimized_content, target_keywords)
                    seo_analysis.readability_score = self._calculate_readability_score(optimized_content)
                    seo_analysis.seo_score = self._calculate_seo_score(optimized_content, target_keywords)
                    seo_analysis.meta_title = meta_title
                    seo_analysis.meta_description = meta_description
                    seo_analysis.h1_tags = self._extract_headings(optimized_content, "h1")
                    seo_analysis.h2_tags = self._extract_headings(optimized_content, "h2")
                    seo_analysis.h3_tags = self._extract_headings(optimized_content, "h3")
                    seo_analysis.analyzed_at = datetime.utcnow()
                else:
                    seo_analysis = SEOAnalysis(
                        content_piece_id=content_piece_id,
                        keyword_density=self._calculate_keyword_density(optimized_content, target_keywords),
                        readability_score=self._calculate_readability_score(optimized_content),
                        seo_score=self._calculate_seo_score(optimized_content, target_keywords),
                        meta_title=meta_title,
                        meta_description=meta_description,
                        h1_tags=self._extract_headings(optimized_content, "h1"),
                        h2_tags=self._extract_headings(optimized_content, "h2"),
                        h3_tags=self._extract_headings(optimized_content, "h3"),
                        analyzed_at=datetime.utcnow()
                    )
                    session.add(seo_analysis)
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.seo_optimization_completed", {
                    "content_piece_id": content_piece_id,
                    "target_keywords": target_keywords,
                    "seo_score": seo_analysis.seo_score,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "optimized_content": optimized_content,
                    "seo_analysis": {
                        "keyword_density": seo_analysis.keyword_density,
                        "readability_score": seo_analysis.readability_score,
                        "seo_score": seo_analysis.seo_score,
                        "meta_title": seo_analysis.meta_title,
                        "meta_description": seo_analysis.meta_description,
                        "headings": {
                            "h1": seo_analysis.h1_tags,
                            "h2": seo_analysis.h2_tags,
                            "h3": seo_analysis.h3_tags
                        }
                    },
                    "optimization_tips": self._generate_optimization_tips(seo_analysis.seo_score),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"SEO optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_keyword_strategy(
        self,
        topic: str,
        industry: str,
        target_audience: str,
        content_type: str
    ) -> Dict[str, Any]:
        """Generate comprehensive keyword strategy for content"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Generate keyword research
            keyword_prompt = self._create_keyword_research_prompt(
                topic, industry, target_audience, content_type
            )
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            
            # Generate keyword strategy
            messages = [{"role": "system", "content": "You are an AI assistant that creates SEO keyword strategies."}, {"role": "user", "content": keyword_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.5)
            keyword_strategy = ai_response.text_content if ai_response.success else ""
            
            # Generate long-tail keyword variations
            longtail_prompt = self._create_longtail_keyword_prompt(topic, industry)
            messages = [{"role": "system", "content": "You are an AI assistant that generates longtail keywords."}, {"role": "user", "content": longtail_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.5)
            longtail_keywords = ai_response.text_content if ai_response.success else ""
            
            # Generate semantic keyword clusters
            semantic_prompt = self._create_semantic_keyword_prompt(topic, industry)
            messages = [{"role": "system", "content": "You are an AI assistant that generates semantic keywords."}, {"role": "user", "content": semantic_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.5)
            semantic_keywords = ai_response.text_content if ai_response.success else ""
            
            return {
                "success": True,
                "keyword_strategy": keyword_strategy,
                "longtail_keywords": self._parse_keyword_list(longtail_keywords),
                "semantic_keywords": self._parse_keyword_list(semantic_keywords),
                "keyword_difficulty_analysis": self._analyze_keyword_difficulty(topic, industry),
                "content_optimization_tips": self._generate_content_optimization_tips(content_type),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Keyword strategy generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_content_seo(
        self,
        content: str,
        target_keywords: List[str]
    ) -> Dict[str, Any]:
        """Analyze content for SEO performance"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Calculate SEO metrics
            keyword_density = self._calculate_keyword_density(content, target_keywords)
            readability_score = self._calculate_readability_score(content)
            seo_score = self._calculate_seo_score(content, target_keywords)
            
            # Analyze content structure
            content_structure = self._analyze_content_structure(content)
            
            # Generate optimization recommendations
            recommendations = self._generate_seo_recommendations(
                content, target_keywords, seo_score, readability_score
            )
            
            return {
                "success": True,
                "seo_metrics": {
                    "keyword_density": keyword_density,
                    "readability_score": readability_score,
                    "seo_score": seo_score,
                    "content_structure": content_structure
                },
                "optimization_recommendations": recommendations,
                "keyword_opportunities": self._identify_keyword_opportunities(content, target_keywords),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Content SEO analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_localized_seo(
        self,
        content: str,
        target_keywords: List[str],
        location: str,
        language: str
    ) -> Dict[str, Any]:
        """Generate localized SEO optimization for regional markets"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Generate localized keywords
            localized_prompt = self._create_localized_keyword_prompt(
                target_keywords, location, language
            )
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            
            # Generate localized keywords
            messages = [{"role": "system", "content": "You are an AI assistant that generates localized keywords."}, {"role": "user", "content": localized_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.5)
            localized_keywords = ai_response.text_content if ai_response.success else ""
            
            # Generate localized content variations
            localized_content_prompt = self._create_localized_content_prompt(
                content, location, language, localized_keywords
            )
            messages = [{"role": "system", "content": "You are an AI assistant that localizes content for SEO."}, {"role": "user", "content": localized_content_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.5)
            localized_content = ai_response.text_content if ai_response.success else ""
            
            # Generate local SEO schema markup
            schema_prompt = self._create_local_schema_prompt(location, language)
            messages = [{"role": "system", "content": "You are an AI assistant that generates JSON-LD schema markup."}, {"role": "user", "content": schema_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
            schema_markup = ai_response.text_content if ai_response.success else ""
            
            return {
                "success": True,
                "localized_keywords": self._parse_keyword_list(localized_keywords),
                "localized_content": localized_content,
                "local_schema_markup": schema_markup,
                "local_seo_tips": self._generate_local_seo_tips(location, language),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Localized SEO generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_seo_optimization_prompt(
        self, content: str, target_keywords: List[str], content_type: str, platform: str
    ) -> str:
        """Create prompt for SEO content optimization"""
        return f"""
        Optimize this content for SEO with target keywords:
        
        Original Content:
        {content}
        
        Target Keywords: {', '.join(target_keywords)}
        Content Type: {content_type}
        Platform: {platform}
        
        Requirements:
        - Naturally integrate target keywords throughout the content
        - Maintain readability and user experience
        - Optimize heading structure (H1, H2, H3)
        - Include semantic variations of keywords
        - Ensure proper keyword density (1-2% per keyword)
        - Add internal linking opportunities
        - Optimize for featured snippets where possible
        
        Generate the SEO-optimized version while maintaining the original message and quality.
        """
    
    def _create_meta_generation_prompt(
        self, title: str, target_keywords: List[str], content_type: str
    ) -> str:
        """Create prompt for meta title and description generation"""
        return f"""
        Generate SEO-optimized meta title and description for this content:
        
        Title: {title}
        Target Keywords: {', '.join(target_keywords)}
        Content Type: {content_type}
        
        Requirements:
        - Meta title: 50-60 characters, include primary keyword
        - Meta description: 150-160 characters, include primary and secondary keywords
        - Make them compelling and click-worthy
        - Include call-to-action where appropriate
        
        Format as:
        Meta Title: [title here]
        Meta Description: [description here]
        """
    
    def _create_keyword_research_prompt(
        self, topic: str, industry: str, target_audience: str, content_type: str
    ) -> str:
        """Create prompt for keyword research strategy"""
        return f"""
        Create a comprehensive keyword strategy for:
        
        Topic: {topic}
        Industry: {industry}
        Target Audience: {target_audience}
        Content Type: {content_type}
        
        Include:
        1. Primary keywords (high search volume, high intent)
        2. Secondary keywords (medium search volume, good intent)
        3. Long-tail keywords (low search volume, high conversion)
        4. Question-based keywords
        5. Local keywords if applicable
        6. Keyword difficulty assessment
        7. Content optimization recommendations
        
        Format as a structured strategy document.
        """
    
    def _create_longtail_keyword_prompt(self, topic: str, industry: str) -> str:
        """Create prompt for long-tail keyword generation"""
        return f"""
        Generate long-tail keyword variations for:
        
        Topic: {topic}
        Industry: {industry}
        
        Include:
        - Question-based keywords (how, what, why, when, where)
        - Specific problem-solving keywords
        - Comparison keywords
        - Location-based keywords
        - Product/service specific keywords
        
        Format as a list of keywords with search intent.
        """
    
    def _create_semantic_keyword_prompt(self, topic: str, industry: str) -> str:
        """Create prompt for semantic keyword generation"""
        return f"""
        Generate semantic keyword clusters for:
        
        Topic: {topic}
        Industry: {industry}
        
        Include:
        - Related terms and synonyms
        - Industry-specific terminology
        - User intent variations
        - Topic clusters and subtopics
        - LSI (Latent Semantic Indexing) keywords
        
        Format as keyword clusters with relationships.
        """
    
    def _create_localized_keyword_prompt(
        self, target_keywords: List[str], location: str, language: str
    ) -> str:
        """Create prompt for localized keyword generation"""
        return f"""
        Generate localized keyword variations for:
        
        Target Keywords: {', '.join(target_keywords)}
        Location: {location}
        Language: {language}
        
        Include:
        - Location-specific keyword variations
        - Local dialect and slang terms
        - Regional search patterns
        - Cultural context variations
        - Local business terminology
        
        Format as a list of localized keywords with search volume estimates.
        """
    
    def _create_localized_content_prompt(
        self, content: str, location: str, language: str, localized_keywords: str
    ) -> str:
        """Create prompt for localized content generation"""
        return f"""
        Adapt this content for local audience:
        
        Original Content:
        {content}
        
        Location: {location}
        Language: {language}
        Localized Keywords: {localized_keywords}
        
        Requirements:
        - Adapt cultural references and examples
        - Include local terminology and expressions
        - Optimize for local search patterns
        - Maintain SEO optimization with localized keywords
        - Ensure cultural sensitivity and relevance
        
        Generate the localized version of the content.
        """
    
    def _create_local_schema_prompt(self, location: str, language: str) -> str:
        """Create prompt for local SEO schema markup"""
        return f"""
        Generate local SEO schema markup for:
        
        Location: {location}
        Language: {language}
        
        Include:
        - LocalBusiness schema
        - Place schema
        - Organization schema
        - BreadcrumbList schema
        - Local SEO specific markup
        
        Format as valid JSON-LD schema markup.
        """
    
    def _extract_meta_title(self, meta_content: str) -> str:
        """Extract meta title from generated content"""
        lines = meta_content.split('\n')
        for line in lines:
            if line.strip().startswith('Meta Title:'):
                return line.replace('Meta Title:', '').strip()
        return ""
    
    def _extract_meta_description(self, meta_content: str) -> str:
        """Extract meta description from generated content"""
        lines = meta_content.split('\n')
        for line in lines:
            if line.strip().startswith('Meta Description:'):
                return line.replace('Meta Description:', '').strip()
        return ""
    
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
        """Calculate comprehensive SEO score"""
        score = 0.0
        
        # Keyword optimization (40 points)
        keyword_score = sum(1 for keyword in keywords if keyword.lower() in content.lower())
        score += (keyword_score / len(keywords)) * 40
        
        # Content length (20 points)
        word_count = len(content.split())
        if word_count >= 1500:
            score += 20
        elif word_count >= 1000:
            score += 15
        elif word_count >= 500:
            score += 10
        
        # Heading structure (20 points)
        if "# " in content or "<h1>" in content:
            score += 10
        if "## " in content or "<h2>" in content:
            score += 5
        if "### " in content or "<h3>" in content:
            score += 5
        
        # Readability (10 points)
        readability = self._calculate_readability_score(content)
        if readability >= 60:
            score += 10
        elif readability >= 40:
            score += 5
        
        # Meta information (10 points)
        if len(content) > 160:
            score += 10
        
        return min(100.0, score)
    
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
    
    def _analyze_content_structure(self, content: str) -> Dict[str, Any]:
        """Analyze content structure for SEO"""
        return {
            "word_count": len(content.split()),
            "sentence_count": len([s for s in content.split('.') if s.strip()]),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "heading_count": {
                "h1": len(self._extract_headings(content, "h1")),
                "h2": len(self._extract_headings(content, "h2")),
                "h3": len(self._extract_headings(content, "h3"))
            },
            "average_sentence_length": len(content.split()) / max(1, len([s for s in content.split('.') if s.strip()])),
            "has_internal_links": "http" in content or "www." in content,
            "has_images": "![alt]" in content or "<img" in content
        }
    
    def _generate_optimization_tips(self, seo_score: float) -> List[str]:
        """Generate SEO optimization tips based on score"""
        tips = []
        
        if seo_score < 50:
            tips.extend([
                "Focus on keyword optimization and integration",
                "Improve content structure with proper headings",
                "Increase content length and depth",
                "Add meta title and description"
            ])
        elif seo_score < 75:
            tips.extend([
                "Optimize keyword density and placement",
                "Enhance heading structure and hierarchy",
                "Improve content readability",
                "Add internal and external links"
            ])
        else:
            tips.extend([
                "Maintain current optimization level",
                "Focus on user experience and engagement",
                "Monitor performance and make incremental improvements",
                "Consider advanced SEO techniques like schema markup"
            ])
        
        return tips
    
    def _generate_seo_recommendations(
        self, content: str, keywords: List[str], seo_score: float, readability_score: float
    ) -> List[str]:
        """Generate specific SEO recommendations"""
        recommendations = []
        
        # Keyword recommendations
        for keyword in keywords:
            if keyword.lower() not in content.lower():
                recommendations.append(f"Add primary keyword '{keyword}' to content")
        
        # Content structure recommendations
        if not any(line.strip().startswith('# ') for line in content.split('\n')):
            recommendations.append("Add H1 heading with primary keyword")
        
        if len(content.split()) < 1000:
            recommendations.append("Increase content length for better SEO performance")
        
        # Readability recommendations
        if readability_score < 40:
            recommendations.append("Simplify language and sentence structure")
        elif readability_score < 60:
            recommendations.append("Improve readability with shorter sentences")
        
        return recommendations
    
    def _identify_keyword_opportunities(self, content: str, target_keywords: List[str]) -> List[str]:
        """Identify additional keyword opportunities"""
        opportunities = []
        
        # Check for missing keyword variations
        for keyword in target_keywords:
            variations = [
                keyword + " guide",
                keyword + " tips",
                keyword + " examples",
                keyword + " best practices"
            ]
            
            for variation in variations:
                if variation.lower() not in content.lower():
                    opportunities.append(f"Add keyword variation: '{variation}'")
        
        return opportunities[:5]  # Limit to top 5 opportunities
    
    def _analyze_keyword_difficulty(self, topic: str, industry: str) -> Dict[str, str]:
        """Analyze keyword difficulty for topic and industry"""
        # This would typically integrate with SEO tools like Ahrefs or SEMrush
        # For now, return estimated difficulty based on common patterns
        
        difficulty_map = {
            "high": ["competitive terms", "broad topics", "popular products"],
            "medium": ["specific topics", "long-tail keywords", "industry terms"],
            "low": ["niche topics", "local keywords", "specific problems"]
        }
        
        return {
            "estimated_difficulty": "medium",
            "reasoning": f"Topic '{topic}' in '{industry}' industry typically has medium competition",
            "recommendation": "Focus on long-tail variations and specific use cases"
        }
    
    def _generate_content_optimization_tips(self, content_type: str) -> List[str]:
        """Generate content-specific optimization tips"""
        tips_map = {
            "blog_post": [
                "Use descriptive headings with keywords",
                "Include internal links to related content",
                "Add meta description with call-to-action",
                "Optimize images with alt text and keywords"
            ],
            "social_media": [
                "Include relevant hashtags",
                "Use platform-specific optimization",
                "Add engaging visuals",
                "Include clear call-to-action"
            ],
            "website_content": [
                "Optimize page title and meta description",
                "Use proper heading hierarchy",
                "Include schema markup",
                "Optimize for featured snippets"
            ]
        }
        
        return tips_map.get(content_type, ["Focus on keyword optimization and user experience"])
    
    def _generate_local_seo_tips(self, location: str, language: str) -> List[str]:
        """Generate local SEO optimization tips"""
        return [
            f"Include location-specific keywords for {location}",
            f"Use {language} language variations and local terminology",
            "Add local business schema markup",
            "Include location in title tags and meta descriptions",
            "Optimize for local search patterns and user intent",
            "Add location-specific internal links",
            "Include local business information and contact details"
        ]
    
    def _parse_keyword_list(self, keyword_content: str) -> List[str]:
        """Parse keyword list from generated content"""
        # Extract keywords from generated content
        lines = keyword_content.split('\n')
        keywords = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-'):
                # Clean up the keyword
                keyword = line.split(':')[-1].strip() if ':' in line else line
                if keyword and len(keyword) > 2:
                    keywords.append(keyword)
        
        return keywords[:20]  # Limit to top 20 keywords
