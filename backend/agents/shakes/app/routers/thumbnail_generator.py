from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..services.thumbnail_generator_service import ThumbnailGeneratorService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/thumbnail-generator", tags=["Thumbnail Generator"])

# Pydantic Models
class GenerateThumbnailRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    thumbnail_style: str = Field(..., description="Thumbnail style")
    design_preferences: Dict[str, Any] = Field(..., description="Design preferences")
    optimization_goals: List[str] = Field(..., description="Optimization goals")

class OptimizeThumbnailRequest(BaseModel):
    thumbnail_id: int = Field(..., description="Thumbnail ID")
    optimization_goals: List[str] = Field(..., description="Optimization goals")
    performance_data: Dict[str, Any] = Field(..., description="Performance data")

class AnalyzeThumbnailPerformanceRequest(BaseModel):
    thumbnail_id: int = Field(..., description="Thumbnail ID")
    analysis_period_days: int = Field(default=30, description="Analysis period in days")
    performance_metrics: List[str] = Field(default=[], description="Performance metrics")

class CreateThumbnailVariationsRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    variation_count: int = Field(..., description="Number of variations")
    style_variations: List[str] = Field(..., description="Style variations")

# Dependency
async def get_thumbnail_generator_service() -> ThumbnailGeneratorService:
    """Get thumbnail generator service instance"""
    service = ThumbnailGeneratorService()
    await service.initialize()
    return service

# Endpoints
@router.post("/generate", response_model=Dict[str, Any], status_code=201)
async def generate_thumbnail(
    request: GenerateThumbnailRequest,
    service: ThumbnailGeneratorService = Depends(get_thumbnail_generator_service)
):
    """Generate click-worthy thumbnail for content"""
    try:
        result = await service.generate_thumbnail(
            content_piece_id=request.content_piece_id,
            thumbnail_style=request.thumbnail_style,
            design_preferences=request.design_preferences,
            optimization_goals=request.optimization_goals
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate thumbnail")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Thumbnail generation failed: {str(e)}"
        )

@router.post("/optimize", response_model=Dict[str, Any], status_code=200)
async def optimize_thumbnail(
    request: OptimizeThumbnailRequest,
    service: ThumbnailGeneratorService = Depends(get_thumbnail_generator_service)
):
    """Optimize thumbnail for better performance"""
    try:
        result = await service.optimize_thumbnail(
            thumbnail_id=request.thumbnail_id,
            optimization_goals=request.optimization_goals,
            performance_data=request.performance_data
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to optimize thumbnail")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Thumbnail optimization failed: {str(e)}"
        )

@router.post("/analyze-performance", response_model=Dict[str, Any], status_code=200)
async def analyze_thumbnail_performance(
    request: AnalyzeThumbnailPerformanceRequest,
    service: ThumbnailGeneratorService = Depends(get_thumbnail_generator_service)
):
    """Analyze thumbnail performance and engagement"""
    try:
        result = await service.analyze_thumbnail_performance(
            thumbnail_id=request.thumbnail_id,
            analysis_period_days=request.analysis_period_days,
            performance_metrics=request.performance_metrics
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to analyze thumbnail performance")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Thumbnail performance analysis failed: {str(e)}"
        )

@router.post("/create-variations", response_model=Dict[str, Any], status_code=201)
async def create_thumbnail_variations(
    request: CreateThumbnailVariationsRequest,
    service: ThumbnailGeneratorService = Depends(get_thumbnail_generator_service)
):
    """Create multiple thumbnail variations for A/B testing"""
    try:
        result = await service.create_thumbnail_variations(
            content_piece_id=request.content_piece_id,
            variation_count=request.variation_count,
            style_variations=request.style_variations
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to create thumbnail variations")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Thumbnail variation creation failed: {str(e)}"
        )

@router.get("/thumbnail-styles")
async def get_thumbnail_styles():
    """Get available thumbnail styles for generation"""
    return {
        "thumbnail_styles": [
            {
                "id": "minimalist",
                "name": "Minimalist",
                "description": "Clean, simple design with minimal elements",
                "characteristics": ["clean_lines", "white_space", "simple_typography", "focused_content"],
                "best_for": ["professional_content", "educational_videos", "product_showcases"],
                "engagement_level": "medium"
            },
            {
                "id": "bold_contrast",
                "name": "Bold Contrast",
                "description": "High contrast design with bold colors and typography",
                "characteristics": ["vibrant_colors", "bold_typography", "high_contrast", "attention_grabbing"],
                "best_for": ["entertainment_content", "gaming_videos", "lifestyle_content"],
                "engagement_level": "high"
            },
            {
                "id": "text_focused",
                "name": "Text Focused",
                "description": "Thumbnail centered around compelling text and headlines",
                "characteristics": ["large_text", "readable_fonts", "text_hierarchy", "clear_messaging"],
                "best_for": ["news_content", "tutorials", "educational_content"],
                "engagement_level": "high"
            },
            {
                "id": "image_centric",
                "name": "Image Centric",
                "description": "Thumbnail focused on compelling imagery",
                "characteristics": ["large_images", "visual_storytelling", "emotional_appeal", "aesthetic_focus"],
                "best_for": ["travel_content", "food_videos", "lifestyle_content"],
                "engagement_level": "high"
            },
            {
                "id": "branded",
                "name": "Branded",
                "description": "Thumbnail incorporating brand elements and identity",
                "characteristics": ["brand_colors", "logo_placement", "brand_typography", "consistent_style"],
                "best_for": ["corporate_content", "brand_channels", "professional_content"],
                "engagement_level": "medium"
            },
            {
                "id": "trending",
                "name": "Trending",
                "description": "Thumbnail following current design trends",
                "characteristics": ["modern_design", "trending_colors", "contemporary_style", "social_media_inspired"],
                "best_for": ["social_media_content", "trending_topics", "viral_content"],
                "engagement_level": "high"
            }
        ]
    }

@router.get("/design-preferences")
async def get_design_preferences():
    """Get available design preferences for thumbnails"""
    return {
        "design_preferences": [
            {
                "id": "color_scheme",
                "name": "Color Scheme",
                "description": "Color palette and scheme preferences",
                "options": ["warm_colors", "cool_colors", "monochrome", "vibrant", "pastel", "brand_colors"],
                "impact": "high"
            },
            {
                "id": "typography",
                "name": "Typography",
                "description": "Font and text styling preferences",
                "options": ["sans_serif", "serif", "display_fonts", "handwritten", "bold", "elegant"],
                "impact": "medium"
            },
            {
                "id": "layout",
                "name": "Layout",
                "description": "Layout and composition preferences",
                "options": ["centered", "left_aligned", "right_aligned", "grid_based", "asymmetric", "rule_of_thirds"],
                "impact": "high"
            },
            {
                "id": "visual_elements",
                "name": "Visual Elements",
                "description": "Additional visual elements and effects",
                "options": ["gradients", "shadows", "borders", "overlays", "icons", "illustrations"],
                "impact": "medium"
            },
            {
                "id": "image_style",
                "name": "Image Style",
                "description": "Image processing and styling preferences",
                "options": ["natural", "enhanced", "filtered", "artistic", "vintage", "modern"],
                "impact": "high"
            }
        ]
    }

@router.get("/optimization-goals")
async def get_optimization_goals():
    """Get available optimization goals for thumbnails"""
    return {
        "optimization_goals": [
            {
                "id": "click_through_rate",
                "name": "Click Through Rate",
                "description": "Optimize for higher click-through rates",
                "metrics": ["ctr", "impressions", "clicks"],
                "strategies": ["attention_grabbing", "curiosity_gap", "emotional_appeal"]
            },
            {
                "id": "engagement",
                "name": "Engagement",
                "description": "Optimize for higher engagement rates",
                "metrics": ["likes", "comments", "shares", "watch_time"],
                "strategies": ["relatable_content", "emotional_connection", "clear_value_proposition"]
            },
            {
                "id": "brand_awareness",
                "name": "Brand Awareness",
                "description": "Optimize for brand recognition and awareness",
                "metrics": ["brand_recall", "brand_mentions", "brand_searches"],
                "strategies": ["consistent_branding", "logo_placement", "brand_colors"]
            },
            {
                "id": "conversion",
                "name": "Conversion",
                "description": "Optimize for conversion and action",
                "metrics": ["conversion_rate", "sign_ups", "purchases", "downloads"],
                "strategies": ["clear_cta", "value_proposition", "urgency_indicators"]
            },
            {
                "id": "accessibility",
                "name": "Accessibility",
                "description": "Optimize for accessibility and inclusivity",
                "metrics": ["accessibility_score", "color_contrast", "readability"],
                "strategies": ["high_contrast", "readable_fonts", "alt_text", "inclusive_design"]
            }
        ]
    }

@router.get("/performance-metrics")
async def get_performance_metrics():
    """Get available performance metrics for thumbnails"""
    return {
        "performance_metrics": [
            {
                "id": "engagement_metrics",
                "name": "Engagement Metrics",
                "description": "Metrics related to user engagement",
                "metrics": ["click_through_rate", "impression_rate", "engagement_rate", "watch_time"],
                "measurement": "percentage_and_duration",
                "importance": "high"
            },
            {
                "id": "visual_metrics",
                "name": "Visual Metrics",
                "description": "Metrics related to visual performance",
                "metrics": ["color_effectiveness", "contrast_ratio", "readability_score", "aesthetic_appeal"],
                "measurement": "score_based",
                "importance": "medium"
            },
            {
                "id": "brand_metrics",
                "name": "Brand Metrics",
                "description": "Metrics related to brand performance",
                "metrics": ["brand_recognition", "brand_consistency", "brand_sentiment", "brand_recall"],
                "measurement": "survey_based",
                "importance": "medium"
            },
            {
                "id": "conversion_metrics",
                "name": "Conversion Metrics",
                "description": "Metrics related to conversion performance",
                "metrics": ["conversion_rate", "action_completion", "goal_achievement", "roi"],
                "measurement": "percentage_and_value",
                "importance": "high"
            }
        ]
    }
