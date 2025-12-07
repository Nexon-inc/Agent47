from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.blog_writing_service import BlogWritingService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter()

# Pydantic models for request/response
class CreateBlogPostRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200, description="Main topic of the blog post")
    target_audience: str = Field(..., description="Target audience for the content")
    word_count_target: int = Field(..., ge=100, le=10000, description="Target word count for the blog post")
    tone: str = Field(..., description="Desired tone for the content")
    keywords: List[str] = Field(..., min_items=1, max_items=20, description="Keywords to optimize for")
    research_depth: str = Field(default="comprehensive", description="Depth of research required")

class EnhanceBlogPostRequest(BaseModel):
    enhancement_type: str = Field(..., description="Type of enhancement to apply")
    enhancement_params: Dict[str, Any] = Field(default={}, description="Parameters for enhancement")

class BlogPostResponse(BaseModel):
    project_id: int
    content_piece_id: int
    blog_content: str
    seo_analysis: Dict[str, Any]
    word_count: int
    reading_time: int
    timestamp: str

class EnhancementResponse(BaseModel):
    enhanced_content: str
    word_count: int
    reading_time: int
    timestamp: str

class AnalyticsResponse(BaseModel):
    content_metrics: Dict[str, Any]
    seo_metrics: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    timestamp: str

# Dependency
async def get_blog_writing_service() -> BlogWritingService:
    service = BlogWritingService()
    await service.initialize()
    return service

@router.post("/create", response_model=Dict[str, Any])
async def create_blog_post(
    request: CreateBlogPostRequest,
    service: BlogWritingService = Depends(get_blog_writing_service)
):
    """Create a comprehensive blog post with AI-powered research and writing"""
    try:
        result = await service.create_blog_post(
            user_id=1,  # TODO: Get from authentication
            topic=request.topic,
            target_audience=request.target_audience,
            word_count_target=request.word_count_target,
            tone=request.tone,
            keywords=request.keywords,
            research_depth=request.research_depth
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Blog post '{request.topic}' created successfully",
                "data": {
                    "project_id": result["project_id"],
                    "content_piece_id": result["content_piece_id"],
                    "blog_content": result["blog_content"],
                    "seo_analysis": result["seo_analysis"],
                    "word_count": result["word_count"],
                    "reading_time": result["reading_time"],
                    "timestamp": result["timestamp"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{content_piece_id}/enhance", response_model=Dict[str, Any])
async def enhance_blog_post(
    content_piece_id: int,
    request: EnhanceBlogPostRequest,
    service: BlogWritingService = Depends(get_blog_writing_service)
):
    """Enhance existing blog post with additional features"""
    try:
        result = await service.enhance_blog_post(
            content_piece_id=content_piece_id,
            enhancement_type=request.enhancement_type,
            enhancement_params=request.enhancement_params
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Blog post enhanced successfully with {request.enhancement_type}",
                "data": {
                    "enhanced_content": result["enhanced_content"],
                    "word_count": result["word_count"],
                    "reading_time": result["reading_time"],
                    "timestamp": result["timestamp"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{content_piece_id}/analytics", response_model=Dict[str, Any])
async def get_blog_analytics(
    content_piece_id: int,
    service: BlogWritingService = Depends(get_blog_writing_service)
):
    """Get comprehensive analytics for a blog post"""
    try:
        result = await service.get_blog_analytics(content_piece_id)
        
        if result["success"]:
            return {
                "status": "success",
                "message": "Blog analytics retrieved successfully",
                "data": {
                    "content_metrics": result["content_metrics"],
                    "seo_metrics": result["seo_metrics"],
                    "quality_metrics": result["quality_metrics"],
                    "timestamp": result["timestamp"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tone-options")
async def get_tone_options():
    """Get available tone options for blog writing"""
    tone_options = [
        {
            "value": "professional",
            "label": "Professional",
            "description": "Formal, business-like tone suitable for corporate content",
            "examples": ["industry reports", "business blogs", "academic content"]
        },
        {
            "value": "casual",
            "label": "Casual",
            "description": "Relaxed, conversational tone for friendly engagement",
            "examples": ["personal blogs", "lifestyle content", "community posts"]
        },
        {
            "value": "friendly",
            "label": "Friendly",
            "description": "Warm, approachable tone that builds rapport",
            "examples": ["customer service blogs", "how-to guides", "welcome content"]
        },
        {
            "value": "authoritative",
            "label": "Authoritative",
            "description": "Confident, expert tone that establishes credibility",
            "examples": ["expert analysis", "thought leadership", "industry insights"]
        },
        {
            "value": "humorous",
            "label": "Humorous",
            "description": "Witty, entertaining tone that adds personality",
            "examples": ["entertainment blogs", "creative content", "brand personality"]
        },
        {
            "value": "inspirational",
            "label": "Inspirational",
            "description": "Motivational, uplifting tone that inspires action",
            "examples": ["success stories", "motivational content", "transformation blogs"]
        },
        {
            "value": "educational",
            "label": "Educational",
            "description": "Clear, instructional tone for learning content",
            "examples": ["tutorials", "guides", "educational blogs"]
        },
        {
            "value": "conversational",
            "label": "Conversational",
            "description": "Natural, dialogue-like tone for engagement",
            "examples": ["Q&A blogs", "discussion posts", "interactive content"]
        }
    ]
    
    return {
        "status": "success",
        "data": tone_options,
        "message": f"Retrieved {len(tone_options)} tone options"
    }

@router.get("/research-depth-options")
async def get_research_depth_options():
    """Get available research depth options for blog writing"""
    research_options = [
        {
            "value": "basic",
            "label": "Basic Research",
            "description": "Essential information and common knowledge",
            "estimated_time": "1-2 hours",
            "suitable_for": ["quick posts", "basic guides", "introductory content"]
        },
        {
            "value": "standard",
            "label": "Standard Research",
            "description": "Comprehensive coverage with reliable sources",
            "estimated_time": "3-5 hours",
            "suitable_for": ["regular blog posts", "how-to guides", "industry content"]
        },
        {
            "value": "comprehensive",
            "label": "Comprehensive Research",
            "description": "In-depth analysis with expert insights and data",
            "estimated_time": "6-10 hours",
            "suitable_for": ["featured posts", "expert analysis", "pillar content"]
        },
        {
            "value": "expert",
            "label": "Expert Research",
            "description": "Deep dive with original research and expert interviews",
            "estimated_time": "10+ hours",
            "suitable_for": ["white papers", "research reports", "authoritative content"]
        }
    ]
    
    return {
        "status": "success",
        "data": research_options,
        "message": f"Retrieved {len(research_options)} research depth options"
    }

@router.get("/enhancement-types")
async def get_enhancement_types():
    """Get available enhancement types for blog posts"""
    enhancement_types = [
        {
            "value": "add_call_to_action",
            "label": "Add Call-to-Action",
            "description": "Include compelling call-to-action buttons or text",
            "parameters": {
                "cta_type": ["general", "download", "subscribe", "contact", "purchase"],
                "cta_style": ["encouraging", "urgent", "benefit-focused", "question-based"]
            }
        },
        {
            "value": "improve_intro",
            "label": "Improve Introduction",
            "description": "Enhance the opening to better hook readers",
            "parameters": {
                "hook_type": ["question", "statistic", "story", "problem", "benefit"],
                "tone_adjustment": ["more engaging", "clearer", "more specific"]
            }
        },
        {
            "value": "add_statistics",
            "label": "Add Statistics",
            "description": "Include relevant data points and statistics",
            "parameters": {
                "focus": ["industry", "trends", "performance", "comparison", "growth"],
                "source_preference": ["recent", "reputable", "industry-specific"]
            }
        },
        {
            "value": "enhance_conclusion",
            "label": "Enhance Conclusion",
            "description": "Strengthen the ending with better takeaways",
            "parameters": {
                "conclusion_type": ["summary", "actionable", "thought-provoking", "encouraging"],
                "include_next_steps": [True, False]
            }
        }
    ]
    
    return {
        "status": "success",
        "data": enhancement_types,
        "message": f"Retrieved {len(enhancement_types)} enhancement types"
    }
