from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from ..services.advanced_analytics_service import AdvancedAnalyticsService
from ..deps import get_current_user
from core.database.models import User

router = APIRouter(prefix="/advanced-analytics", tags=["Advanced Analytics"])

@router.get("/sentiment-heatmap/{platform}")
async def generate_sentiment_heatmap(
    platform: str,
    date_range: str = "30d",
    current_user: User = Depends(get_current_user),
    advanced_analytics_service: AdvancedAnalyticsService = Depends()
):
    """Generate audience sentiment heatmap visualization data"""
    try:
        await advanced_analytics_service.initialize()
        result = await advanced_analytics_service.generate_sentiment_heatmap(
            current_user.id,
            platform,
            date_range
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cross-platform-stories")
async def cross_platform_story_sync(
    story_content: Dict[str, Any],
    target_platforms: List[str],
    current_user: User = Depends(get_current_user),
    advanced_analytics_service: AdvancedAnalyticsService = Depends()
):
    """Sync Stories/Reels across multiple platforms with platform-specific adaptations"""
    try:
        await advanced_analytics_service.initialize()
        result = await advanced_analytics_service.cross_platform_story_sync(
            current_user.id,
            story_content,
            target_platforms
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/influencer-collaborations")
async def find_influencer_collaborations(
    criteria: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    advanced_analytics_service: AdvancedAnalyticsService = Depends()
):
    """Find potential influencer collaboration opportunities"""
    try:
        await advanced_analytics_service.initialize()
        result = await advanced_analytics_service.find_influencer_collaborations(
            current_user.id,
            criteria
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/story-specs/{platform}")
async def get_platform_story_specs(platform: str):
    """Get platform-specific story specifications"""
    specs = {
        "instagram": {
            "text_limit": 2200,
            "tone": "visual, engaging, trendy",
            "hashtag_limit": 30,
            "media_specs": {
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "duration": "15s",
                "format": "mp4"
            }
        },
        "tiktok": {
            "text_limit": 150,
            "tone": "trendy, youthful, viral",
            "hashtag_limit": 20,
            "media_specs": {
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "duration": "15s-60s",
                "format": "mp4"
            }
        },
        "snapchat": {
            "text_limit": 250,
            "tone": "casual, fun, ephemeral",
            "hashtag_limit": 10,
            "media_specs": {
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "duration": "10s",
                "format": "mp4"
            }
        },
        "youtube_shorts": {
            "text_limit": 100,
            "tone": "informative, engaging, searchable",
            "hashtag_limit": 15,
            "media_specs": {
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "duration": "15s-60s",
                "format": "mp4"
            }
        }
    }
    
    if platform in specs:
        return {"platform": platform, "specs": specs[platform]}
    else:
        return {"platform": platform, "specs": "Platform not supported for story sync"}

@router.get("/collaboration-types")
async def get_collaboration_types():
    """Get available collaboration types for influencer partnerships"""
    return {
        "collaboration_types": [
            {
                "type": "guest_post",
                "description": "Create content for each other's platforms",
                "best_for": "Instagram, LinkedIn",
                "engagement_potential": "High"
            },
            {
                "type": "cross_promotion",
                "description": "Promote each other's content",
                "best_for": "All platforms",
                "engagement_potential": "Medium"
            },
            {
                "type": "joint_live_stream",
                "description": "Collaborate on live content",
                "best_for": "Instagram, TikTok, YouTube",
                "engagement_potential": "Very High"
            },
            {
                "type": "hashtag_challenge",
                "description": "Create viral hashtag challenges",
                "best_for": "TikTok, Instagram",
                "engagement_potential": "Very High"
            },
            {
                "type": "product_review",
                "description": "Review each other's products/services",
                "best_for": "YouTube, Instagram",
                "engagement_potential": "High"
            }
        ]
    }
