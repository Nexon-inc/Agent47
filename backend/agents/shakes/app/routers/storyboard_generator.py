from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..services.storyboard_generator_service import StoryboardGeneratorService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/storyboard-generator", tags=["Storyboard Generator"])

# Pydantic Models
class GenerateStoryboardRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    storyboard_type: str = Field(..., description="Storyboard type")
    visual_style: str = Field(..., description="Visual style")
    duration_minutes: int = Field(default=2, description="Duration in minutes")
    scene_count: int = Field(default=8, description="Number of scenes")

class GenerateVideoStoryboardRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    video_format: str = Field(..., description="Video format")
    target_audience: str = Field(..., description="Target audience")
    video_goals: List[str] = Field(..., description="Video goals")

class GenerateCampaignStoryboardRequest(BaseModel):
    campaign_concept: str = Field(..., description="Campaign concept")
    campaign_goals: List[str] = Field(..., description="Campaign goals")
    target_audience: str = Field(..., description="Target audience")
    campaign_duration_days: int = Field(..., description="Campaign duration in days")
    content_variations: int = Field(default=3, description="Number of content variations")

class OptimizeStoryboardRequest(BaseModel):
    storyboard_data: Dict[str, Any] = Field(..., description="Storyboard data")
    optimization_goals: List[str] = Field(..., description="Optimization goals")
    constraints: Dict[str, Any] = Field(..., description="Constraints")

# Dependency
async def get_storyboard_generator_service() -> StoryboardGeneratorService:
    """Get storyboard generator service instance"""
    service = StoryboardGeneratorService()
    await service.initialize()
    return service

# Endpoints
@router.post("/generate", response_model=Dict[str, Any], status_code=200)
async def generate_storyboard(
    request: GenerateStoryboardRequest,
    service: StoryboardGeneratorService = Depends(get_storyboard_generator_service)
):
    """Generate AI-powered storyboard for content"""
    try:
        result = await service.generate_storyboard(
            content_piece_id=request.content_piece_id,
            storyboard_type=request.storyboard_type,
            visual_style=request.visual_style,
            duration_minutes=request.duration_minutes,
            scene_count=request.scene_count
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate storyboard")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Storyboard generation failed: {str(e)}"
        )

@router.post("/video", response_model=Dict[str, Any], status_code=200)
async def generate_video_storyboard(
    request: GenerateVideoStoryboardRequest,
    service: StoryboardGeneratorService = Depends(get_storyboard_generator_service)
):
    """Generate storyboard specifically for video content"""
    try:
        result = await service.generate_video_storyboard(
            content_piece_id=request.content_piece_id,
            video_format=request.video_format,
            target_audience=request.target_audience,
            video_goals=request.video_goals
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate video storyboard")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video storyboard generation failed: {str(e)}"
        )

@router.post("/campaign", response_model=Dict[str, Any], status_code=200)
async def generate_campaign_storyboard(
    request: GenerateCampaignStoryboardRequest,
    service: StoryboardGeneratorService = Depends(get_storyboard_generator_service)
):
    """Generate storyboard for marketing campaign"""
    try:
        result = await service.generate_campaign_storyboard(
            campaign_concept=request.campaign_concept,
            campaign_goals=request.campaign_goals,
            target_audience=request.target_audience,
            campaign_duration_days=request.campaign_duration_days,
            content_variations=request.content_variations
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate campaign storyboard")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Campaign storyboard generation failed: {str(e)}"
        )

@router.post("/optimize", response_model=Dict[str, Any], status_code=200)
async def optimize_storyboard(
    request: OptimizeStoryboardRequest,
    service: StoryboardGeneratorService = Depends(get_storyboard_generator_service)
):
    """Optimize existing storyboard based on goals and constraints"""
    try:
        result = await service.optimize_storyboard(
            storyboard_data=request.storyboard_data,
            optimization_goals=request.optimization_goals,
            constraints=request.constraints
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to optimize storyboard")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Storyboard optimization failed: {str(e)}"
        )

@router.get("/storyboard-types")
async def get_storyboard_types():
    """Get available storyboard types"""
    return {
        "storyboard_types": [
            {
                "id": "narrative",
                "name": "Narrative Storyboard",
                "description": "Traditional storyboard for narrative content",
                "best_for": ["storytelling", "brand_narratives", "educational_content"],
                "scene_structure": "beginning_middle_end",
                "visual_focus": "story_flow"
            },
            {
                "id": "explainer",
                "name": "Explainer Storyboard",
                "description": "Storyboard for explanatory and educational content",
                "best_for": ["product_demos", "tutorials", "how_to_content"],
                "scene_structure": "problem_solution_benefit",
                "visual_focus": "clarity_and_understanding"
            },
            {
                "id": "promotional",
                "name": "Promotional Storyboard",
                "description": "Storyboard for marketing and promotional content",
                "best_for": ["advertisements", "product_launches", "sales_content"],
                "scene_structure": "attention_interest_desire_action",
                "visual_focus": "persuasion_and_conversion"
            },
            {
                "id": "social_media",
                "name": "Social Media Storyboard",
                "description": "Storyboard optimized for social media platforms",
                "best_for": ["instagram_stories", "tiktok_videos", "social_campaigns"],
                "scene_structure": "hook_engagement_call_to_action",
                "visual_focus": "engagement_and_sharing"
            }
        ]
    }

@router.get("/visual-styles")
async def get_visual_styles():
    """Get available visual styles for storyboards"""
    return {
        "visual_styles": [
            {
                "id": "modern",
                "name": "Modern",
                "description": "Clean, contemporary visual style",
                "characteristics": ["minimalist", "clean_lines", "bold_colors", "geometric_shapes"],
                "best_for": ["tech_products", "corporate_content", "professional_brands"]
            },
            {
                "id": "vintage",
                "name": "Vintage",
                "description": "Retro and nostalgic visual style",
                "characteristics": ["warm_colors", "textured_backgrounds", "classic_typography", "nostalgic_elements"],
                "best_for": ["heritage_brands", "lifestyle_content", "creative_projects"]
            },
            {
                "id": "playful",
                "name": "Playful",
                "description": "Fun and energetic visual style",
                "characteristics": ["bright_colors", "rounded_shapes", "animated_elements", "friendly_typography"],
                "best_for": ["children_content", "entertainment", "casual_brands"]
            },
            {
                "id": "elegant",
                "name": "Elegant",
                "description": "Sophisticated and refined visual style",
                "characteristics": ["subtle_colors", "elegant_typography", "refined_composition", "luxury_elements"],
                "best_for": ["luxury_brands", "high_end_products", "premium_content"]
            }
        ]
    }

@router.get("/video-formats")
async def get_video_formats():
    """Get available video formats for storyboards"""
    return {
        "video_formats": [
            {
                "id": "square",
                "name": "Square (1:1)",
                "description": "Square format for social media platforms",
                "dimensions": "1080x1080",
                "best_for": ["instagram", "facebook", "linkedin"],
                "characteristics": ["balanced_composition", "mobile_optimized", "social_media_friendly"]
            },
            {
                "id": "landscape",
                "name": "Landscape (16:9)",
                "description": "Wide format for traditional video platforms",
                "dimensions": "1920x1080",
                "best_for": ["youtube", "vimeo", "website_embeds"],
                "characteristics": ["cinematic", "desktop_optimized", "traditional_video"]
            },
            {
                "id": "portrait",
                "name": "Portrait (9:16)",
                "description": "Vertical format for mobile-first platforms",
                "dimensions": "1080x1920",
                "best_for": ["tiktok", "instagram_stories", "snapchat"],
                "characteristics": ["mobile_first", "vertical_scrolling", "mobile_optimized"]
            },
            {
                "id": "cinematic",
                "name": "Cinematic (21:9)",
                "description": "Ultra-wide format for cinematic content",
                "dimensions": "2560x1080",
                "best_for": ["cinematic_content", "presentations", "premium_videos"],
                "characteristics": ["cinematic", "immersive", "premium_quality"]
            }
        ]
    }

@router.get("/optimization-goals")
async def get_optimization_goals():
    """Get available optimization goals for storyboards"""
    return {
        "optimization_goals": [
            {
                "id": "engagement",
                "name": "Increase Engagement",
                "description": "Optimize storyboard for higher engagement",
                "focus_areas": ["hook_optimization", "visual_appeal", "emotional_connection"],
                "metrics": ["view_completion_rate", "engagement_rate", "shares"]
            },
            {
                "id": "clarity",
                "name": "Improve Clarity",
                "description": "Optimize storyboard for better message clarity",
                "focus_areas": ["message_simplification", "visual_hierarchy", "information_flow"],
                "metrics": ["comprehension_rate", "message_retention", "user_feedback"]
            },
            {
                "id": "conversion",
                "name": "Drive Conversion",
                "description": "Optimize storyboard for conversion goals",
                "focus_areas": ["call_to_action", "persuasion_elements", "trust_building"],
                "metrics": ["conversion_rate", "click_through_rate", "sales"]
            },
            {
                "id": "brand_consistency",
                "name": "Enhance Brand Consistency",
                "description": "Optimize storyboard for brand alignment",
                "focus_areas": ["brand_voice", "visual_identity", "message_alignment"],
                "metrics": ["brand_recognition", "brand_sentiment", "consistency_score"]
            }
        ]
    }

@router.get("/storyboard-best-practices")
async def get_storyboard_best_practices():
    """Get best practices for storyboard creation"""
    return {
        "storyboard_best_practices": [
            {
                "category": "planning",
                "title": "Planning Best Practices",
                "practices": [
                    "Define clear objectives and target audience",
                    "Create a logical flow and narrative structure",
                    "Plan for appropriate duration and pacing",
                    "Consider platform-specific requirements",
                    "Include key messages and call-to-actions"
                ]
            },
            {
                "category": "visual_design",
                "title": "Visual Design Best Practices",
                "practices": [
                    "Maintain consistent visual style throughout",
                    "Use clear and readable typography",
                    "Ensure proper color contrast and accessibility",
                    "Include relevant and engaging visuals",
                    "Optimize for different screen sizes"
                ]
            },
            {
                "category": "content_structure",
                "title": "Content Structure Best Practices",
                "practices": [
                    "Start with a strong hook to capture attention",
                    "Maintain clear information hierarchy",
                    "Use transitions to connect scenes smoothly",
                    "Include appropriate pacing and timing",
                    "End with a clear call-to-action"
                ]
            },
            {
                "category": "optimization",
                "title": "Optimization Best Practices",
                "practices": [
                    "Test different versions for performance",
                    "Optimize for specific platform algorithms",
                    "Consider audience preferences and behavior",
                    "Monitor and analyze performance metrics",
                    "Iterate based on feedback and data"
                ]
            }
        ]
    }
