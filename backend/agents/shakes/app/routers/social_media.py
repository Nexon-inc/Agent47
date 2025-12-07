from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.social_media_service import SocialMediaContentService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter()

# Pydantic models for request/response
class CreateSocialMediaRequest(BaseModel):
    platform: str = Field(..., description="Target social media platform")
    content_type: str = Field(..., description="Type of content to create")
    topic: str = Field(..., min_length=1, max_length=200, description="Main topic of the content")
    target_audience: str = Field(..., description="Target audience for the content")
    tone: str = Field(..., description="Desired tone for the content")
    call_to_action: str = Field(..., description="Call-to-action for the content")
    hashtags: Optional[List[str]] = Field(default=None, description="Hashtags to include")
    image_description: Optional[str] = Field(default=None, description="Request for image description")

class ContentSeriesRequest(BaseModel):
    platform: str = Field(..., description="Target social media platform")
    series_topic: str = Field(..., description="Main topic for the content series")
    post_count: int = Field(..., ge=2, le=20, description="Number of posts in the series")
    content_style: str = Field(..., description="Style of content for the series")
    target_audience: str = Field(..., description="Target audience for the series")
    tone: str = Field(..., description="Desired tone for the series")

class PlatformOptimizationRequest(BaseModel):
    target_platform: str = Field(..., description="Platform to optimize content for")

class SocialMediaResponse(BaseModel):
    project_id: int
    content_piece_id: int
    social_content: str
    image_description: str
    platform_optimizations: Dict[str, Any]
    hashtag_suggestions: List[str]
    posting_tips: List[str]
    timestamp: str

class ContentSeriesResponse(BaseModel):
    project_id: int
    series_outline: str
    posts: List[Dict[str, Any]]
    platform: str
    post_count: int
    timestamp: str

class OptimizationResponse(BaseModel):
    optimized_content: str
    target_platform: str
    platform_specific_tips: Dict[str, Any]
    timestamp: str

# Dependency
async def get_social_media_service() -> SocialMediaContentService:
    service = SocialMediaContentService()
    await service.initialize()
    return service

@router.post("/create", response_model=Dict[str, Any])
async def create_social_media_content(
    request: CreateSocialMediaRequest,
    service: SocialMediaContentService = Depends(get_social_media_service)
):
    """Create platform-optimized social media content"""
    try:
        result = await service.create_social_media_content(
            user_id=1,  # TODO: Get from authentication
            platform=request.platform,
            content_type=request.content_type,
            topic=request.topic,
            target_audience=request.target_audience,
            tone=request.tone,
            call_to_action=request.call_to_action,
            hashtags=request.hashtags,
            image_description=request.image_description
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Social media content for {request.platform} created successfully",
                "data": {
                    "project_id": result["project_id"],
                    "content_piece_id": result["content_piece_id"],
                    "social_content": result["social_content"],
                    "image_description": result["image_description"],
                    "platform_optimizations": result["platform_optimizations"],
                    "hashtag_suggestions": result["hashtag_suggestions"],
                    "posting_tips": result["posting_tips"],
                    "timestamp": result["timestamp"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/series", response_model=Dict[str, Any])
async def create_content_series(
    request: ContentSeriesRequest,
    service: SocialMediaContentService = Depends(get_social_media_service)
):
    """Create a series of related social media posts"""
    try:
        result = await service.create_content_series(
            user_id=1,  # TODO: Get from authentication
            platform=request.platform,
            series_topic=request.series_topic,
            post_count=request.post_count,
            content_style=request.content_style,
            target_audience=request.target_audience,
            tone=request.tone
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Content series with {request.post_count} posts created successfully",
                "data": {
                    "project_id": result["project_id"],
                    "series_outline": result["series_outline"],
                    "posts": result["posts"],
                    "platform": result["platform"],
                    "post_count": result["post_count"],
                    "timestamp": result["timestamp"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{content_piece_id}/optimize", response_model=Dict[str, Any])
async def optimize_for_platform(
    content_piece_id: int,
    request: PlatformOptimizationRequest,
    service: SocialMediaContentService = Depends(get_social_media_service)
):
    """Optimize existing content for a specific platform"""
    try:
        result = await service.optimize_for_platform(
            content_piece_id=content_piece_id,
            target_platform=request.target_platform
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Content optimized for {request.target_platform} successfully",
                "data": {
                    "optimized_content": result["optimized_content"],
                    "target_platform": result["target_platform"],
                    "platform_specific_tips": result["platform_specific_tips"],
                    "timestamp": result["timestamp"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms")
async def get_supported_platforms():
    """Get list of supported social media platforms"""
    platforms = [
        {
            "value": "facebook",
            "label": "Facebook",
            "description": "Social networking platform for personal and business use",
            "content_types": ["posts", "stories", "videos", "polls", "events"],
            "character_limits": {"posts": "unlimited", "stories": "unlimited"},
            "best_practices": ["engage with audience", "use visual content", "post consistently"]
        },
        {
            "value": "instagram",
            "label": "Instagram",
            "description": "Visual platform for photos, videos, and stories",
            "content_types": ["posts", "stories", "reels", "carousels", "igtv"],
            "character_limits": {"captions": "2200", "stories": "unlimited"},
            "best_practices": ["high-quality visuals", "use hashtags", "post stories daily"]
        },
        {
            "value": "twitter",
            "label": "Twitter",
            "description": "Microblogging platform for short-form content",
            "content_types": ["tweets", "threads", "polls", "spaces", "fleets"],
            "character_limits": {"tweets": "280", "threads": "unlimited"},
            "best_practices": ["be concise", "use hashtags", "engage with trends"]
        },
        {
            "value": "linkedin",
            "label": "LinkedIn",
            "description": "Professional networking platform for business content",
            "content_types": ["posts", "articles", "polls", "videos", "newsletters"],
            "character_limits": {"posts": "3000", "articles": "unlimited"},
            "best_practices": ["professional tone", "share insights", "build network"]
        },
        {
            "value": "tiktok",
            "label": "TikTok",
            "description": "Short-form video platform for entertainment and trends",
            "content_types": ["videos", "duets", "challenges", "trends", "live"],
            "character_limits": {"captions": "2200", "videos": "15s-10m"},
            "best_practices": ["trending content", "authentic videos", "engage with community"]
        },
        {
            "value": "pinterest",
            "label": "Pinterest",
            "description": "Visual discovery platform for ideas and inspiration",
            "content_types": ["pins", "boards", "stories", "live", "shopping"],
            "character_limits": {"pin descriptions": "500", "board descriptions": "500"},
            "best_practices": ["high-quality images", "detailed descriptions", "organize boards"]
        },
        {
            "value": "snapchat",
            "label": "Snapchat",
            "description": "Ephemeral messaging and content platform",
            "content_types": ["snaps", "stories", "spotlight", "maps", "filters"],
            "character_limits": {"captions": "250", "stories": "24 hours"},
            "best_practices": ["authentic content", "use filters", "daily stories"]
        },
        {
            "value": "threads",
            "label": "Threads",
            "description": "Text-based conversation platform by Meta",
            "content_types": ["posts", "replies", "reposts", "quotes"],
            "character_limits": {"posts": "500", "replies": "500"},
            "best_practices": ["conversational tone", "engage with community", "share thoughts"]
        }
    ]
    
    return {
        "status": "success",
        "data": platforms,
        "message": f"Retrieved {len(platforms)} supported platforms"
    }

@router.get("/content-types")
async def get_content_types():
    """Get available content types for social media"""
    content_types = [
        {
            "value": "post",
            "label": "Post",
            "description": "Standard social media post with text and media",
            "platforms": ["facebook", "instagram", "twitter", "linkedin"],
            "best_use": "General updates, announcements, and engagement"
        },
        {
            "value": "story",
            "label": "Story",
            "description": "Temporary content that disappears after 24 hours",
            "platforms": ["instagram", "facebook", "snapchat"],
            "best_use": "Behind-the-scenes, daily updates, and temporary content"
        },
        {
            "value": "video",
            "label": "Video",
            "description": "Moving visual content with audio",
            "platforms": ["all"],
            "best_use": "Tutorials, entertainment, and engaging content"
        },
        {
            "value": "carousel",
            "label": "Carousel",
            "description": "Multiple images or slides in one post",
            "platforms": ["instagram", "facebook", "linkedin"],
            "best_use": "Step-by-step guides, product showcases, and detailed content"
        },
        {
            "value": "reel",
            "label": "Reel",
            "description": "Short-form vertical video content",
            "platforms": ["instagram", "facebook"],
            "best_use": "Trending content, entertainment, and viral potential"
        },
        {
            "value": "poll",
            "label": "Poll",
            "description": "Interactive content for audience engagement",
            "platforms": ["instagram", "twitter", "facebook", "linkedin"],
            "best_use": "Audience research, engagement, and community building"
        },
        {
            "value": "thread",
            "label": "Thread",
            "description": "Series of connected posts",
            "platforms": ["twitter", "threads"],
            "best_use": "Long-form content, detailed explanations, and storytelling"
        }
    ]
    
    return {
        "status": "success",
        "data": content_types,
        "message": f"Retrieved {len(content_types)} content types"
    }

@router.get("/best-practices/{platform}")
async def get_platform_best_practices(platform: str):
    """Get best practices for a specific platform"""
    practices = {
        "facebook": {
            "posting_frequency": "1-2 times per day",
            "optimal_times": ["1-4 PM", "7-9 PM"],
            "content_mix": ["40% entertaining", "30% informative", "20% promotional", "10% community"],
            "engagement_tips": [
                "Ask questions to encourage comments",
                "Use Facebook Live for real-time engagement",
                "Create Facebook Groups for community building",
                "Use Facebook Insights to track performance"
            ],
            "algorithm_factors": [
                "Engagement rate (likes, comments, shares)",
                "Post timing and frequency",
                "Content type and format",
                "User interaction history"
            ]
        },
        "instagram": {
            "posting_frequency": "1-2 times per day",
            "optimal_times": ["2-3 PM", "8-9 PM"],
            "content_mix": ["50% visual", "30% engaging", "20% promotional"],
            "engagement_tips": [
                "Post Instagram Stories daily",
                "Use relevant hashtags (5-15 per post)",
                "Engage with your audience's content",
                "Create a consistent visual aesthetic"
            ],
            "algorithm_factors": [
                "Engagement rate and timing",
                "User relationship and interaction",
                "Content quality and relevance",
                "Hashtag usage and discovery"
            ]
        },
        "twitter": {
            "posting_frequency": "3-5 times per day",
            "optimal_times": ["9-11 AM", "1-3 PM"],
            "content_mix": ["60% informative", "25% engaging", "15% promotional"],
            "engagement_tips": [
                "Use trending hashtags strategically",
                "Retweet and engage with others' content",
                "Create Twitter threads for longer content",
                "Participate in Twitter Spaces and conversations"
            ],
            "algorithm_factors": [
                "Engagement rate and recency",
                "User relationship and interaction",
                "Content relevance and quality",
                "Hashtag usage and trending topics"
            ]
        },
        "linkedin": {
            "posting_frequency": "1-2 times per day",
            "optimal_times": ["8-10 AM", "5-6 PM"],
            "content_mix": ["70% informative", "20% engaging", "10% promotional"],
            "engagement_tips": [
                "Share industry insights and expertise",
                "Comment on others' posts to build network",
                "Use LinkedIn-specific hashtags",
                "Create long-form articles for thought leadership"
            ],
            "algorithm_factors": [
                "Professional relevance and expertise",
                "Network engagement and relationships",
                "Content quality and value",
                "Professional activity and consistency"
            ]
        }
    }
    
    platform_practices = practices.get(platform.lower())
    if not platform_practices:
        raise HTTPException(status_code=404, detail=f"Best practices not found for platform: {platform}")
    
    return {
        "status": "success",
        "data": platform_practices,
        "message": f"Retrieved best practices for {platform}"
    }
