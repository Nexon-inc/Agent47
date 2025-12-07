from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.content_repurposing_service import ContentRepurposingService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/content-repurposing", tags=["Content Repurposing"])

# Pydantic Models
class RepurposeContentRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    source_content_id: int = Field(..., description="ID of source content to repurpose")
    target_format: str = Field(..., description="Target content format")
    target_platform: str = Field(..., description="Target platform")
    repurposing_goals: List[str] = Field(..., description="Goals for repurposing")
    target_audience: str = Field(..., description="Target audience")
    tone_adjustment: str = Field(default="maintain", description="Tone adjustment approach")

class RepurposeContentResponse(BaseModel):
    success: bool
    project_id: int
    content_piece_id: int
    source_content_id: int
    repurposed_content: str
    platform_optimizations: str
    target_format: str
    target_platform: str
    word_count: int
    reading_time: int
    timestamp: str

# Dependency
async def get_content_repurposing_service() -> ContentRepurposingService:
    """Get content repurposing service instance"""
    service = ContentRepurposingService()
    await service.initialize()
    return service

# Endpoints
@router.post("/repurpose", response_model=RepurposeContentResponse, status_code=201)
async def repurpose_content(
    request: RepurposeContentRequest,
    service: ContentRepurposingService = Depends(get_content_repurposing_service)
):
    """Repurpose existing content into new format and platform"""
    try:
        result = await service.repurpose_content(
            user_id=request.user_id,
            source_content_id=request.source_content_id,
            target_format=request.target_format,
            target_platform=request.target_platform,
            repurposing_goals=request.repurposing_goals,
            target_audience=request.target_audience,
            tone_adjustment=request.tone_adjustment
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to repurpose content")
            )
        
        return RepurposeContentResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content repurposing failed: {str(e)}"
        )

@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported content formats for repurposing"""
    return {
        "supported_formats": [
            {
                "id": "blog_post",
                "name": "Blog Post",
                "description": "Long-form articles and blog posts",
                "best_for": ["thought_leadership", "seo_content", "educational_content"],
                "typical_length": [800, 2000, 3000],
                "key_elements": ["headline", "introduction", "body", "conclusion", "cta"]
            },
            {
                "id": "social_media",
                "name": "Social Media Post",
                "description": "Platform-specific social media content",
                "best_for": ["engagement", "brand_awareness", "community_building"],
                "typical_length": [50, 280, 500],
                "key_elements": ["hook", "content", "hashtags", "cta"]
            },
            {
                "id": "email",
                "name": "Email Content",
                "description": "Email newsletters and marketing emails",
                "best_for": ["nurturing", "promotions", "updates"],
                "typical_length": [200, 500, 1000],
                "key_elements": ["subject", "preheader", "body", "cta"]
            },
            {
                "id": "ad_copy",
                "name": "Ad Copy",
                "description": "Advertising and promotional copy",
                "best_for": ["conversions", "sales", "lead_generation"],
                "typical_length": [25, 100, 300],
                "key_elements": ["headline", "description", "cta"]
            },
            {
                "id": "video_script",
                "name": "Video Script",
                "description": "Scripts for video content",
                "best_for": ["storytelling", "tutorials", "entertainment"],
                "typical_length": [300, 800, 1500],
                "key_elements": ["hook", "story", "call_to_action"]
            }
        ]
    }

@router.get("/repurposing-strategies")
async def get_repurposing_strategies():
    """Get content repurposing strategies and best practices"""
    return {
        "repurposing_strategies": [
            {
                "strategy": "pillar_content_approach",
                "name": "Pillar Content Approach",
                "description": "Create one comprehensive piece and repurpose into multiple formats",
                "best_for": ["thought_leadership", "educational_content"],
                "formats": ["blog_post", "social_media", "email", "video_script"],
                "benefits": ["consistency", "efficiency", "comprehensive_coverage"]
            },
            {
                "strategy": "platform_optimization",
                "name": "Platform Optimization",
                "description": "Adapt content specifically for each platform's requirements",
                "best_for": ["multi_platform_presence", "audience_engagement"],
                "formats": ["social_media", "email", "ad_copy"],
                "benefits": ["platform_alignment", "better_engagement", "audience_fit"]
            },
            {
                "strategy": "audience_segmentation",
                "name": "Audience Segmentation",
                "description": "Repurpose content for different audience segments",
                "best_for": ["diverse_audiences", "personalization"],
                "formats": ["email", "social_media", "blog_post"],
                "benefits": ["personalization", "relevance", "engagement"]
            }
        ]
    }

@router.get("/platform-requirements")
async def get_platform_requirements():
    """Get platform-specific requirements for content repurposing"""
    return {
        "platform_requirements": [
            {
                "platform": "facebook",
                "character_limits": {"post": 63206, "ad_headline": 40, "ad_description": 125},
                "best_practices": ["visual_content", "engagement_focus", "storytelling"],
                "content_types": ["text", "image", "video", "link"],
                "optimization_tips": ["use_emojis", "ask_questions", "include_cta"]
            },
            {
                "platform": "twitter",
                "character_limits": {"tweet": 280, "thread": 280},
                "best_practices": ["concise_messaging", "hashtag_usage", "real_time_relevance"],
                "content_types": ["text", "image", "video", "poll"],
                "optimization_tips": ["use_hashtags", "engage_trends", "thread_for_longer_content"]
            },
            {
                "platform": "linkedin",
                "character_limits": {"post": 3000, "article": 125000},
                "best_practices": ["professional_tone", "industry_insights", "thought_leadership"],
                "content_types": ["text", "image", "video", "article", "poll"],
                "optimization_tips": ["professional_voice", "industry_keywords", "engage_professionals"]
            },
            {
                "platform": "instagram",
                "character_limits": {"caption": 2200, "bio": 150},
                "best_practices": ["visual_storytelling", "authentic_content", "community_building"],
                "content_types": ["image", "video", "story", "reel", "igtv"],
                "optimization_tips": ["visual_first", "use_hashtags", "authentic_voice"]
            }
        ]
    }
