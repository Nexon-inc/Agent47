from typing import Dict, Any, List, Optional
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.utils.database_utils import DatabaseUtils
from core.utils.cache_utils import CacheUtils
from core.utils.event_bus_utils import EventBusUtils
from core.utils.integration_utils import IntegrationUtils
from core.config import settings
from ..database import get_shakes_database

class ThumbnailGeneratorService:
    """Service for generating click-worthy thumbnails for videos and content"""
    
    def __init__(self):
        self.db_utils = DatabaseUtils()
        self.cache_utils = CacheUtils()
        self.event_bus = EventBusUtils()
        self.integration_utils = IntegrationUtils()
        self.model_config = {"model": "grok-llm", "temperature": 0.7, "max_tokens": 2000}
        
    async def initialize(self):
        """Initialize service dependencies"""
        await self.db_utils.initialize()
        await self.cache_utils.initialize()
        await self.event_bus.initialize()
        await self.integration_utils.initialize()
    
    async def generate_thumbnail(self, content_piece_id: int, thumbnail_style: str, 
                               design_preferences: Dict[str, Any], 
                               optimization_goals: List[str]) -> Dict[str, Any]:
        """Generate click-worthy thumbnail for content"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                content_piece = await session.get("content_pieces", content_piece_id)
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                thumbnail_prompt = await self._create_thumbnail_prompt(
                    content_piece, thumbnail_style, design_preferences, optimization_goals
                )
                
                thumbnail_design = await self._generate_thumbnail_design(
                    thumbnail_prompt, design_preferences
                )
                
                thumbnail_metadata = {
                    "content_piece_id": content_piece_id,
                    "thumbnail_style": thumbnail_style,
                    "design_preferences": design_preferences,
                    "optimization_goals": optimization_goals,
                    "generated_at": datetime.utcnow(),
                    "thumbnail_data": thumbnail_design
                }
                
                thumbnail_id = await self._save_thumbnail(thumbnail_metadata, session)
                
                await self.event_bus.publish_event("thumbnail_generated", {
                    "content_piece_id": content_piece_id,
                    "thumbnail_id": thumbnail_id,
                    "thumbnail_style": thumbnail_style
                })
                
                return {
                    "success": True,
                    "thumbnail_id": thumbnail_id,
                    "thumbnail_design": thumbnail_design,
                    "optimization_insights": await self._get_optimization_insights(thumbnail_design),
                    "performance_predictions": await self._predict_thumbnail_performance(thumbnail_design)
                }
                
        except Exception as e:
            return {"success": False, "error": f"Thumbnail generation failed: {str(e)}"}
    
    async def optimize_thumbnail(self, thumbnail_id: int, optimization_goals: List[str],
                               performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize thumbnail for better performance"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                thumbnail = await session.get("thumbnails", thumbnail_id)
                if not thumbnail:
                    return {"success": False, "error": "Thumbnail not found"}
                
                optimization_analysis = await self._analyze_thumbnail_performance(
                    thumbnail, performance_data
                )
                
                optimized_design = await self._apply_optimization_changes(
                    thumbnail, optimization_goals, optimization_analysis
                )
                
                updated_thumbnail = await self._update_thumbnail_design(
                    thumbnail_id, optimized_design, session
                )
                
                await self.event_bus.publish_event("thumbnail_optimized", {
                    "thumbnail_id": thumbnail_id,
                    "optimization_goals": optimization_goals,
                    "performance_improvement": optimization_analysis.get("improvement_score")
                })
                
                return {
                    "success": True,
                    "optimized_thumbnail": updated_thumbnail,
                    "optimization_analysis": optimization_analysis,
                    "performance_improvements": await self._calculate_performance_improvements(
                        thumbnail, updated_thumbnail
                    )
                }
                
        except Exception as e:
            return {"success": False, "error": f"Thumbnail optimization failed: {str(e)}"}
    
    async def analyze_thumbnail_performance(self, thumbnail_id: int, 
                                          analysis_period_days: int,
                                          performance_metrics: List[str]) -> Dict[str, Any]:
        """Analyze thumbnail performance and engagement"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                thumbnail = await session.get("thumbnails", thumbnail_id)
                if not thumbnail:
                    return {"success": False, "error": "Thumbnail not found"}
                
                performance_data = await self._collect_thumbnail_metrics(
                    thumbnail_id, analysis_period_days, performance_metrics
                )
                
                performance_analysis = await self._analyze_thumbnail_metrics(
                    performance_data, performance_metrics
                )
                
                engagement_insights = await self._generate_engagement_insights(
                    performance_analysis
                )
                
                optimization_recommendations = await self._generate_optimization_recommendations(
                    performance_analysis, engagement_insights
                )
                
                return {
                    "success": True,
                    "performance_data": performance_data,
                    "performance_analysis": performance_analysis,
                    "engagement_insights": engagement_insights,
                    "optimization_recommendations": optimization_recommendations,
                    "benchmark_comparison": await self._compare_to_benchmarks(performance_analysis)
                }
                
        except Exception as e:
            return {"success": False, "error": f"Thumbnail performance analysis failed: {str(e)}"}
    
    async def create_thumbnail_variations(self, content_piece_id: int, 
                                        variation_count: int,
                                        style_variations: List[str]) -> Dict[str, Any]:
        """Create multiple thumbnail variations for A/B testing"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                content_piece = await session.get("content_pieces", content_piece_id)
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                thumbnail_variations = []
                for i in range(variation_count):
                    variation_style = style_variations[i % len(style_variations)]
                    
                    variation_design = await self._generate_thumbnail_variation(
                        content_piece, variation_style, i
                    )
                    
                    variation_metadata = {
                        "content_piece_id": content_piece_id,
                        "variation_index": i,
                        "variation_style": variation_style,
                        "generated_at": datetime.utcnow(),
                        "thumbnail_data": variation_design
                    }
                    
                    variation_id = await self._save_thumbnail_variation(variation_metadata, session)
                    thumbnail_variations.append({
                        "variation_id": variation_id,
                        "variation_style": variation_style,
                        "thumbnail_design": variation_design
                    })
                
                await self.event_bus.publish_event("thumbnail_variations_created", {
                    "content_piece_id": content_piece_id,
                    "variation_count": variation_count,
                    "variation_ids": [v["variation_id"] for v in thumbnail_variations]
                })
                
                return {
                    "success": True,
                    "thumbnail_variations": thumbnail_variations,
                    "testing_recommendations": await self._generate_testing_recommendations(
                        thumbnail_variations
                    ),
                    "performance_predictions": await self._predict_variation_performance(
                        thumbnail_variations
                    )
                }
                
        except Exception as e:
            return {"success": False, "error": f"Thumbnail variation creation failed: {str(e)}"}
    
    async def _create_thumbnail_prompt(self, content_piece: Dict[str, Any], 
                                     thumbnail_style: str, design_preferences: Dict[str, Any],
                                     optimization_goals: List[str]) -> str:
        """Create prompt for thumbnail generation"""
        prompt = f"""
        Generate a click-worthy thumbnail for the following content:
        
        Content Title: {content_piece.get('title', '')}
        Content Type: {content_piece.get('content_type', '')}
        Platform: {content_piece.get('platform', '')}
        Target Audience: {content_piece.get('target_audience', '')}
        
        Thumbnail Style: {thumbnail_style}
        Design Preferences: {design_preferences}
        Optimization Goals: {optimization_goals}
        
        Create a thumbnail that:
        1. Captures attention and encourages clicks
        2. Represents the content accurately
        3. Follows platform-specific best practices
        4. Optimizes for the specified goals
        5. Uses appropriate colors, fonts, and imagery
        
        Provide detailed design specifications including:
        - Color scheme and palette
        - Typography and text placement
        - Image composition and layout
        - Visual elements and effects
        - Platform-specific optimizations
        """
        
        return prompt
    
    async def _generate_thumbnail_design(self, prompt: str, 
                                       design_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate thumbnail design using AI"""
        try:
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that generates thumbnail design specifications in JSON format."}, {"role": "user", "content": prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
            response = ai_response.text_content if ai_response.success else ""
            
            design_specifications = await self._parse_design_specifications(response)
            
            return {
                "design_specifications": design_specifications,
                "visual_elements": await self._extract_visual_elements(design_specifications),
                "color_palette": await self._extract_color_palette(design_specifications),
                "typography": await self._extract_typography(design_specifications),
                "layout_composition": await self._extract_layout_composition(design_specifications)
            }
            
        except Exception as e:
            return {"error": f"Thumbnail design generation failed: {str(e)}"}
    
    async def _save_thumbnail(self, thumbnail_metadata: Dict[str, Any], session) -> int:
        """Save thumbnail to database"""
        thumbnail_data = {
            "content_piece_id": thumbnail_metadata["content_piece_id"],
            "thumbnail_style": thumbnail_metadata["thumbnail_style"],
            "design_preferences": thumbnail_metadata["design_preferences"],
            "optimization_goals": thumbnail_metadata["optimization_goals"],
            "thumbnail_data": thumbnail_metadata["thumbnail_data"],
            "generated_at": thumbnail_metadata["generated_at"],
            "status": "active"
        }
        
        result = await session.execute(
            "INSERT INTO thumbnails (content_piece_id, thumbnail_style, design_preferences, optimization_goals, thumbnail_data, generated_at, status) VALUES (:content_piece_id, :thumbnail_style, :design_preferences, :optimization_goals, :thumbnail_data, :generated_at, :status) RETURNING id",
            thumbnail_data
        )
        
        return result.scalar()
    
    async def _get_optimization_insights(self, thumbnail_design: Dict[str, Any]) -> Dict[str, Any]:
        """Get optimization insights for thumbnail"""
        return {
            "click_through_potential": await self._assess_click_through_potential(thumbnail_design),
            "attention_grabbing_elements": await self._identify_attention_elements(thumbnail_design),
            "platform_optimization": await self._assess_platform_optimization(thumbnail_design),
            "accessibility_score": await self._assess_accessibility(thumbnail_design),
            "brand_consistency": await self._assess_brand_consistency(thumbnail_design)
        }
    
    async def _predict_thumbnail_performance(self, thumbnail_design: Dict[str, Any]) -> Dict[str, Any]:
        """Predict thumbnail performance metrics"""
        return {
            "predicted_ctr": await self._predict_click_through_rate(thumbnail_design),
            "predicted_engagement": await self._predict_engagement_rate(thumbnail_design),
            "predicted_shares": await self._predict_share_rate(thumbnail_design),
            "performance_confidence": await self._calculate_performance_confidence(thumbnail_design)
        }
