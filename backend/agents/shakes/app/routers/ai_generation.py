from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.ai_generation_service import AIContentGenerationService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/ai-generation", tags=["AI Content Generation"])

# Pydantic Models
class GenerateContentRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    content_type: str = Field(..., description="Type of content to generate")
    topic: str = Field(..., description="Main topic or subject")
    target_audience: str = Field(..., description="Target audience")
    tone: str = Field(..., description="Content tone")
    word_count_target: int = Field(..., description="Target word count")
    platform: str = Field(..., description="Target platform")
    keywords: List[str] = Field(default=[], description="Keywords to include")
    content_goals: List[str] = Field(default=[], description="Content goals")

class GenerateContentResponse(BaseModel):
    success: bool
    project_id: int
    content_piece_id: int
    generated_content: str
    content_type: str
    platform: str
    word_count: int
    reading_time: int
    timestamp: str

class BatchGenerateRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    content_specifications: List[Dict[str, Any]] = Field(..., description="List of content specifications")

class EnhanceContentRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID to enhance")
    enhancement_type: str = Field(..., description="Type of enhancement")
    enhancement_params: Dict[str, Any] = Field(default={}, description="Enhancement parameters")

# Dependency
async def get_ai_generation_service() -> AIContentGenerationService:
    """Get AI content generation service instance"""
    service = AIContentGenerationService()
    await service.initialize()
    return service

# Endpoints
@router.post("/generate", response_model=GenerateContentResponse, status_code=201)
async def generate_content(
    request: GenerateContentRequest,
    service: AIContentGenerationService = Depends(get_ai_generation_service)
):
    """Generate AI-powered content based on specifications"""
    try:
        result = await service.generate_content(
            user_id=request.user_id,
            content_type=request.content_type,
            topic=request.topic,
            target_audience=request.target_audience,
            tone=request.tone,
            word_count_target=request.word_count_target,
            platform=request.platform,
            keywords=request.keywords,
            content_goals=request.content_goals
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate content")
            )
        
        return GenerateContentResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content generation failed: {str(e)}"
        )

@router.post("/batch-generate", response_model=Dict[str, Any], status_code=201)
async def batch_generate_content(
    request: BatchGenerateRequest,
    service: AIContentGenerationService = Depends(get_ai_generation_service)
):
    """Generate multiple content pieces in batch"""
    try:
        result = await service.generate_content_batch(
            user_id=request.user_id,
            content_specifications=request.content_specifications
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate content batch")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch content generation failed: {str(e)}"
        )

@router.post("/enhance", response_model=Dict[str, Any], status_code=200)
async def enhance_content(
    request: EnhanceContentRequest,
    service: AIContentGenerationService = Depends(get_ai_generation_service)
):
    """Enhance existing content with AI"""
    try:
        result = await service.enhance_content(
            content_piece_id=request.content_piece_id,
            enhancement_type=request.enhancement_type,
            enhancement_params=request.enhancement_params
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to enhance content")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content enhancement failed: {str(e)}"
        )

@router.get("/content-types")
async def get_content_types():
    """Get list of supported content types for AI generation"""
    return {
        "content_types": [
            {
                "id": "blog_post",
                "name": "Blog Post",
                "description": "Long-form articles and blog posts",
                "best_for": ["seo", "thought_leadership", "education"],
                "typical_length": [800, 2000, 3000],
                "key_elements": ["headline", "introduction", "body", "conclusion"]
            },
            {
                "id": "social_media",
                "name": "Social Media Post",
                "description": "Platform-specific social media content",
                "best_for": ["engagement", "brand_awareness", "community"],
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
                "id": "product_description",
                "name": "Product Description",
                "description": "Product and service descriptions",
                "best_for": ["ecommerce", "sales", "product_showcase"],
                "typical_length": [100, 300, 500],
                "key_elements": ["features", "benefits", "specifications"]
            },
            {
                "id": "press_release",
                "name": "Press Release",
                "description": "Official announcements and news",
                "best_for": ["pr", "announcements", "media_relations"],
                "typical_length": [300, 600, 1000],
                "key_elements": ["headline", "dateline", "body", "boilerplate"]
            }
        ]
    }

@router.get("/enhancement-types")
async def get_enhancement_types():
    """Get list of available content enhancement types"""
    return {
        "enhancement_types": [
            {
                "id": "grammar_improvement",
                "name": "Grammar Improvement",
                "description": "Fix grammar, spelling, and syntax issues",
                "best_for": ["professional_content", "formal_documents"],
                "improvements": ["grammar_fixes", "spelling_corrections", "syntax_improvements"]
            },
            {
                "id": "tone_adjustment",
                "name": "Tone Adjustment",
                "description": "Adjust content tone and voice",
                "best_for": ["brand_consistency", "audience_alignment"],
                "improvements": ["tone_consistency", "voice_alignment", "style_improvements"]
            },
            {
                "id": "readability_enhancement",
                "name": "Readability Enhancement",
                "description": "Improve content readability and flow",
                "best_for": ["user_experience", "engagement"],
                "improvements": ["sentence_structure", "paragraph_flow", "clarity_improvements"]
            },
            {
                "id": "seo_optimization",
                "name": "SEO Optimization",
                "description": "Optimize content for search engines",
                "best_for": ["search_visibility", "organic_traffic"],
                "improvements": ["keyword_integration", "meta_optimization", "structure_improvements"]
            },
            {
                "id": "engagement_boost",
                "name": "Engagement Boost",
                "description": "Increase content engagement potential",
                "best_for": ["social_media", "marketing_content"],
                "improvements": ["hook_improvements", "cta_enhancement", "emotional_appeal"]
            }
        ]
    }

@router.get("/generation-tips")
async def get_generation_tips():
    """Get tips for effective AI content generation"""
    return {
        "generation_tips": [
            {
                "category": "topic_selection",
                "title": "Topic Selection",
                "tips": [
                    "Choose specific, focused topics rather than broad subjects",
                    "Consider your target audience's interests and pain points",
                    "Research trending topics in your industry",
                    "Ensure topics align with your content goals"
                ]
            },
            {
                "category": "audience_targeting",
                "title": "Audience Targeting",
                "tips": [
                    "Define clear audience personas",
                    "Use language appropriate for your audience's level",
                    "Consider audience demographics and psychographics",
                    "Tailor content to audience preferences and behaviors"
                ]
            },
            {
                "category": "tone_consistency",
                "title": "Tone Consistency",
                "tips": [
                    "Maintain consistent tone across all content",
                    "Align tone with your brand voice",
                    "Consider platform-specific tone requirements",
                    "Use tone to build brand personality"
                ]
            },
            {
                "category": "keyword_integration",
                "title": "Keyword Integration",
                "tips": [
                    "Use keywords naturally throughout content",
                    "Avoid keyword stuffing",
                    "Include long-tail keywords for better targeting",
                    "Balance keyword density with readability"
                ]
            }
        ]
    }
