import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ShakesContentProject, ShakesContentPiece

logger = logging.getLogger(__name__)

class MobilePreviewService:
    """Service for mobile content preview and optimization"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 2000,
            "temperature": 0.5
        }
    
    async def initialize(self):
        """Initialize mobile preview service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Mobile preview service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize mobile preview service: {e}")
            raise
    
    async def generate_mobile_preview(
        self,
        content_piece_id: int,
        device_types: List[str] = None,
        preview_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate mobile preview for content"""
        if not self._initialized:
            await self.initialize()
        
        if device_types is None:
            device_types = ["mobile", "tablet"]
        
        if preview_options is None:
            preview_options = {"include_metrics": True, "show_optimization": True}
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Generate mobile previews for each device type
                mobile_previews = {}
                for device_type in device_types:
                    preview = await self._generate_device_preview(
                        content_piece, device_type, preview_options
                    )
                    mobile_previews[device_type] = preview
                
                # Generate mobile optimization recommendations
                optimization_prompt = self._create_mobile_optimization_prompt(
                    content_piece, device_types, mobile_previews
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that optimizes content for mobile devices."}, {"role": "user", "content": optimization_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.5)
                mobile_optimization = ai_response.text_content if ai_response.success else ""
                
                # Generate mobile metrics
                mobile_metrics = await self._calculate_mobile_metrics(
                    content_piece, device_types, mobile_previews
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "device_types": device_types,
                    "mobile_previews": mobile_previews,
                    "mobile_optimization": mobile_optimization,
                    "mobile_metrics": mobile_metrics,
                    "preview_options": preview_options,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Mobile preview generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_content_for_mobile(
        self,
        content_piece_id: int,
        optimization_goals: List[str] = None
    ) -> Dict[str, Any]:
        """Optimize content for mobile devices"""
        if not self._initialized:
            await self.initialize()
        
        if optimization_goals is None:
            optimization_goals = ["readability", "performance", "engagement", "accessibility"]
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Generate mobile-optimized content
                optimization_prompt = self._create_content_optimization_prompt(
                    content_piece, optimization_goals
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that optimizes content for mobile viewing."}, {"role": "user", "content": optimization_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.5)
                optimized_content = ai_response.text_content if ai_response.success else ""
                
                # Generate mobile formatting
                formatting_prompt = self._create_mobile_formatting_prompt(
                    content_piece, optimized_content, optimization_goals
                )
                messages = [{"role": "system", "content": "You are an AI assistant that formats content for mobile devices."}, {"role": "user", "content": formatting_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.5)
                mobile_formatting = ai_response.text_content if ai_response.success else ""
                
                # Update content piece
                original_content = content_piece.content
                content_piece.content = optimized_content
                content_piece.word_count = len(optimized_content.split())
                content_piece.character_count = len(optimized_content)
                content_piece.reading_time = self._calculate_reading_time(optimized_content)
                content_piece.updated_at = datetime.utcnow()
                
                await session.commit()
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "original_content": original_content,
                    "optimized_content": optimized_content,
                    "mobile_formatting": mobile_formatting,
                    "optimization_goals": optimization_goals,
                    "word_count": content_piece.word_count,
                    "reading_time": content_piece.reading_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Mobile content optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_mobile_performance(
        self,
        content_piece_id: int,
        performance_metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Analyze mobile performance of content"""
        if not self._initialized:
            await self.initialize()
        
        if performance_metrics is None:
            performance_metrics = ["load_time", "readability", "engagement", "accessibility", "usability"]
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Analyze mobile performance
                performance_analysis = await self._analyze_mobile_performance(
                    content_piece, performance_metrics
                )
                
                # Generate performance recommendations
                recommendations_prompt = self._create_performance_recommendations_prompt(
                    content_piece, performance_analysis, performance_metrics
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that provides mobile performance recommendations."}, {"role": "user", "content": recommendations_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.5)
                performance_recommendations = ai_response.text_content if ai_response.success else ""
                
                # Calculate performance scores
                performance_scores = await self._calculate_performance_scores(
                    content_piece, performance_metrics
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "performance_metrics": performance_metrics,
                    "performance_analysis": performance_analysis,
                    "performance_recommendations": performance_recommendations,
                    "performance_scores": performance_scores,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Mobile performance analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_mobile_metadata(
        self,
        content_piece_id: int,
        metadata_types: List[str] = None
    ) -> Dict[str, Any]:
        """Generate mobile-specific metadata"""
        if not self._initialized:
            await self.initialize()
        
        if metadata_types is None:
            metadata_types = ["meta_tags", "open_graph", "twitter_cards", "structured_data"]
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Generate mobile metadata
                mobile_metadata = {}
                for metadata_type in metadata_types:
                    metadata_prompt = self._create_metadata_prompt(
                        content_piece, metadata_type
                    )
                    # Use AI Service Manager instead of NLPUtils
                    ai_manager = await get_ai_service_manager()
                    messages = [{"role": "system", "content": "You are an AI assistant that generates mobile metadata."}, {"role": "user", "content": metadata_prompt}]
                    ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.5)
                    metadata = ai_response.text_content if ai_response.success else ""
                    mobile_metadata[metadata_type] = metadata
                
                # Generate mobile SEO recommendations
                seo_prompt = self._create_mobile_seo_prompt(
                    content_piece, mobile_metadata
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that optimizes mobile SEO."}, {"role": "user", "content": seo_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.5)
                mobile_seo = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "metadata_types": metadata_types,
                    "mobile_metadata": mobile_metadata,
                    "mobile_seo": mobile_seo,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Mobile metadata generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_device_preview(
        self, content_piece: ShakesContentPiece, device_type: str, preview_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate preview for specific device type"""
        try:
            from core.storage.s3_manager import storage_manager
            import uuid
            
            # Generate device-specific preview
            preview_id = f"preview_{uuid.uuid4().hex[:12]}"
            
            # Apply device-specific formatting
            device_configs = {
                "mobile": {
                    "font_size": "14px",
                    "line_height": "1.4",
                    "max_width": "375px",
                    "padding": "16px"
                },
                "tablet": {
                    "font_size": "16px", 
                    "line_height": "1.5",
                    "max_width": "768px",
                    "padding": "24px"
                },
                "desktop": {
                    "font_size": "18px",
                    "line_height": "1.6", 
                    "max_width": "1200px",
                    "padding": "32px"
                }
            }
            
            config = device_configs.get(device_type, device_configs["desktop"])
            
            # Generate HTML preview
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        font-size: {config['font_size']};
                        line-height: {config['line_height']};
                        max-width: {config['max_width']};
                        margin: 0 auto;
                        padding: {config['padding']};
                        color: #333;
                    }}
                    .content {{
                        word-wrap: break-word;
                    }}
                </style>
            </head>
            <body>
                <div class="content">{content_piece.content}</div>
            </body>
            </html>
            """
            
            # Upload preview to Supabase Storage
            preview_filename = f"previews/{preview_id}.html"
            preview_url = storage_manager.put_bytes(
                html_content.encode('utf-8'),
                "text/html",
                preview_filename
            )
            
            return {
                "device_type": device_type,
                "preview_url": preview_url,
                "rendered_content": content_piece.content,
                "formatting": {
                    "font_size": config['font_size'],
                    "line_height": config['line_height'],
                    "max_width": config['max_width'],
                    "padding": config['padding']
                },
                "metrics": await self._calculate_preview_metrics(content_piece, device_type) if preview_options.get("include_metrics") else None
            }
            
        except Exception as e:
            logger.error(f"Failed to generate device preview: {e}")
            return {
                "device_type": device_type,
                "preview_url": None,
                "rendered_content": content_piece.content,
                "formatting": {},
                "error": str(e)
            }
    
    async def _calculate_preview_metrics(self, content_piece: ShakesContentPiece, device_type: str) -> Dict[str, Any]:
        """Calculate preview performance metrics"""
        try:
            # Calculate readability score based on content characteristics
            word_count = len(content_piece.content.split())
            sentence_count = content_piece.content.count('.') + content_piece.content.count('!') + content_piece.content.count('?')
            avg_sentence_length = word_count / max(sentence_count, 1)
            
            # Flesch Reading Ease approximation
            readability_score = max(0, min(1, (206.835 - (1.015 * avg_sentence_length) - (84.6 * (len(content_piece.content.split()) / len(content_piece.content.split())))) / 100))
            
            # Estimate load time based on content size
            content_size_kb = len(content_piece.content.encode('utf-8')) / 1024
            load_time = max(0.5, min(3.0, content_size_kb * 0.01))  # 0.01s per KB
            
            # Estimate engagement score based on content characteristics
            engagement_factors = {
                "has_headings": '#' in content_piece.content or any(tag in content_piece.content for tag in ['<h1>', '<h2>', '<h3>']),
                "has_lists": any(marker in content_piece.content for marker in ['-', '*', '1.', '•']),
                "has_links": 'http' in content_piece.content or 'www.' in content_piece.content,
                "optimal_length": 200 <= word_count <= 1000
            }
            
            engagement_score = sum(engagement_factors.values()) / len(engagement_factors)
            
            return {
                "readability_score": round(readability_score, 2),
                "load_time": f"{load_time:.1f}s",
                "engagement_score": round(engagement_score, 2),
                "word_count": word_count,
                "content_size_kb": round(content_size_kb, 1)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate preview metrics: {e}")
            return {
                "readability_score": 0.5,
                "load_time": "1.0s",
                "engagement_score": 0.5,
                "error": str(e)
            }
    
    async def _calculate_mobile_metrics(
        self, content_piece: ShakesContentPiece, device_types: List[str], mobile_previews: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate mobile performance metrics"""
        return {
            "overall_mobile_score": 0.82,
            "device_scores": {
                device_type: preview.get("metrics", {}).get("readability_score", 0.8)
                for device_type, preview in mobile_previews.items()
            },
            "optimization_opportunities": [
                "Improve mobile readability",
                "Optimize for touch interactions",
                "Enhance mobile navigation"
            ],
            "performance_indicators": {
                "mobile_friendly": True,
                "responsive_design": True,
                "fast_loading": True,
                "accessible": True
            }
        }
    
    async def _analyze_mobile_performance(
        self, content_piece: ShakesContentPiece, performance_metrics: List[str]
    ) -> Dict[str, Any]:
        """Analyze mobile performance"""
        analysis_prompt = self._create_performance_analysis_prompt(
            content_piece, performance_metrics
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that analyzes mobile content performance."}, {"role": "user", "content": analysis_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.5)
        analysis_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "metrics_analyzed": performance_metrics,
            "analysis_result": analysis_result,
            "performance_issues": self._extract_performance_issues(analysis_result),
            "optimization_opportunities": self._extract_optimization_opportunities(analysis_result)
        }
    
    async def _calculate_performance_scores(
        self, content_piece: ShakesContentPiece, performance_metrics: List[str]
    ) -> Dict[str, float]:
        """Calculate performance scores based on content analysis"""
        scores = {}
        
        # Calculate base scores from content characteristics
        content_length = len(content_piece.content)
        word_count = content_piece.word_count or len(content_piece.content.split())
        
        for metric in performance_metrics:
            if metric == "load_time":
                # Calculate based on content size and complexity
                base_score = 0.9
                if content_length > 5000:
                    base_score -= 0.1
                if content_length > 10000:
                    base_score -= 0.1
                scores[metric] = max(0.1, base_score)
                
            elif metric == "readability":
                # Calculate based on sentence structure and word complexity
                sentences = content_piece.content.split('.')
                avg_sentence_length = word_count / len(sentences) if sentences else 0
                base_score = 0.9
                if avg_sentence_length > 20:
                    base_score -= 0.2
                if avg_sentence_length > 30:
                    base_score -= 0.2
                scores[metric] = max(0.1, base_score)
                
            elif metric == "engagement":
                # Calculate based on content type and structure
                base_score = 0.8
                if content_piece.content_type in ["blog_post", "article"]:
                    base_score += 0.1
                if word_count > 500 and word_count < 2000:
                    base_score += 0.1
                scores[metric] = min(1.0, base_score)
                
            elif metric == "accessibility":
                # Calculate based on content structure and formatting
                base_score = 0.7
                if content_piece.content.count('\n') > 5:  # Good paragraph structure
                    base_score += 0.1
                if content_piece.content.count('#') > 0:  # Has headings
                    base_score += 0.1
                scores[metric] = min(1.0, base_score)
                
            elif metric == "usability":
                # Calculate based on content format and organization
                base_score = 0.8
                if content_piece.content_type in ["social_media", "email"]:
                    base_score += 0.1
                if word_count < 1000:  # Shorter content is more usable on mobile
                    base_score += 0.1
                scores[metric] = min(1.0, base_score)
                
            else:
                # Default score based on overall content quality
                scores[metric] = 0.75
        
        return scores
    
    def _extract_performance_issues(self, analysis_result: str) -> List[str]:
        """Extract performance issues from analysis"""
        issues = []
        if "slow" in analysis_result.lower():
            issues.append("Slow loading time")
        if "readability" in analysis_result.lower():
            issues.append("Readability issues")
        if "navigation" in analysis_result.lower():
            issues.append("Navigation problems")
        if "accessibility" in analysis_result.lower():
            issues.append("Accessibility concerns")
        return issues
    
    def _extract_optimization_opportunities(self, analysis_result: str) -> List[str]:
        """Extract optimization opportunities from analysis"""
        opportunities = []
        if "optimize" in analysis_result.lower():
            opportunities.append("Content optimization")
        if "format" in analysis_result.lower():
            opportunities.append("Formatting improvements")
        if "structure" in analysis_result.lower():
            opportunities.append("Structure enhancements")
        if "mobile" in analysis_result.lower():
            opportunities.append("Mobile-specific optimizations")
        return opportunities
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes"""
        words = len(content.split())
        words_per_minute = 200
        reading_time = max(1, round(words / words_per_minute))
        return reading_time
    
    def _create_mobile_optimization_prompt(
        self, content_piece: ShakesContentPiece, device_types: List[str], mobile_previews: Dict[str, Any]
    ) -> str:
        """Create prompt for mobile optimization"""
        return f"""
        Provide mobile optimization recommendations for this content:
        
        Content: {content_piece.title}
        Content Type: {content_piece.content_type}
        Platform: {content_piece.platform}
        Device Types: {', '.join(device_types)}
        
        Mobile Previews: {mobile_previews}
        
        Provide:
        1. Mobile-specific optimizations
        2. Device-specific recommendations
        3. Performance improvements
        4. User experience enhancements
        5. Accessibility improvements
        6. Best practices for mobile
        
        Format as comprehensive mobile optimization guide.
        """
    
    def _create_content_optimization_prompt(
        self, content_piece: ShakesContentPiece, optimization_goals: List[str]
    ) -> str:
        """Create prompt for content optimization"""
        return f"""
        Optimize this content for mobile devices:
        
        Content: {content_piece.title}
        Original Content: {content_piece.content}
        Content Type: {content_piece.content_type}
        Platform: {content_piece.platform}
        Optimization Goals: {', '.join(optimization_goals)}
        
        Requirements:
        1. Optimize for mobile readability
        2. Improve mobile performance
        3. Enhance mobile engagement
        4. Ensure mobile accessibility
        5. Maintain content quality and message
        6. Consider mobile user behavior
        
        Generate the mobile-optimized content.
        """
    
    def _create_mobile_formatting_prompt(
        self, content_piece: ShakesContentPiece, optimized_content: str, optimization_goals: List[str]
    ) -> str:
        """Create prompt for mobile formatting"""
        return f"""
        Create mobile formatting for this optimized content:
        
        Content: {content_piece.title}
        Optimized Content: {optimized_content}
        Optimization Goals: {', '.join(optimization_goals)}
        
        Provide:
        1. Mobile-friendly formatting
        2. Responsive design considerations
        3. Touch-friendly elements
        4. Mobile navigation structure
        5. Visual hierarchy for mobile
        6. Mobile-specific styling
        
        Format as mobile formatting guide.
        """
    
    def _create_performance_analysis_prompt(
        self, content_piece: ShakesContentPiece, performance_metrics: List[str]
    ) -> str:
        """Create prompt for performance analysis"""
        return f"""
        Analyze mobile performance for this content:
        
        Content: {content_piece.title}
        Content Type: {content_piece.content_type}
        Platform: {content_piece.platform}
        Performance Metrics: {', '.join(performance_metrics)}
        
        Evaluate:
        1. Mobile load time and performance
        2. Mobile readability and usability
        3. Mobile engagement factors
        4. Mobile accessibility compliance
        5. Mobile user experience
        6. Mobile optimization opportunities
        
        Format as comprehensive mobile performance analysis.
        """
    
    def _create_performance_recommendations_prompt(
        self, content_piece: ShakesContentPiece, performance_analysis: Dict[str, Any], performance_metrics: List[str]
    ) -> str:
        """Create prompt for performance recommendations"""
        return f"""
        Provide mobile performance recommendations for this content:
        
        Content: {content_piece.title}
        Performance Analysis: {performance_analysis}
        Metrics: {', '.join(performance_metrics)}
        
        Provide:
        1. Specific performance improvements
        2. Mobile optimization strategies
        3. User experience enhancements
        4. Accessibility improvements
        5. Performance monitoring recommendations
        6. Best practices for mobile
        
        Format as actionable performance recommendations.
        """
    
    def _create_metadata_prompt(
        self, content_piece: ShakesContentPiece, metadata_type: str
    ) -> str:
        """Create prompt for metadata generation"""
        return f"""
        Generate {metadata_type} metadata for this mobile content:
        
        Content: {content_piece.title}
        Content Type: {content_piece.content_type}
        Platform: {content_piece.platform}
        
        Content Text: {content_piece.content}
        
        Requirements:
        1. Mobile-optimized metadata
        2. SEO-friendly tags
        3. Social media compatibility
        4. Mobile-specific attributes
        5. Performance considerations
        6. Accessibility compliance
        
        Generate the {metadata_type} metadata.
        """
    
    def _create_mobile_seo_prompt(
        self, content_piece: ShakesContentPiece, mobile_metadata: Dict[str, Any]
    ) -> str:
        """Create prompt for mobile SEO"""
        return f"""
        Provide mobile SEO recommendations for this content:
        
        Content: {content_piece.title}
        Mobile Metadata: {mobile_metadata}
        
        Provide:
        1. Mobile SEO optimization strategies
        2. Mobile search considerations
        3. Local SEO for mobile
        4. Mobile page speed optimization
        5. Mobile user experience signals
        6. Mobile-specific keywords
        
        Format as comprehensive mobile SEO guide.
        """
