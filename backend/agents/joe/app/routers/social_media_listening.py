from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from ..database import get_joe_database
from core.event_bus.kafka_manager import get_event_bus
from core.cache.redis_manager import get_redis
from ..services.social_media_listening_service import SocialMediaListeningService

router = APIRouter()

class BrandMentionsRequest(BaseModel):
    brand: str = Field(..., description="Brand to track mentions for")
    platforms: List[str] = Field(..., description="Social media platforms to monitor")
    timeframe: str = Field(default="7d", description="Timeframe for tracking")

class HashtagMonitoringRequest(BaseModel):
    hashtags: List[str] = Field(..., description="Hashtags to monitor")
    platforms: List[str] = Field(..., description="Platforms to monitor")

class ConversationAnalysisRequest(BaseModel):
    keywords: List[str] = Field(..., description="Keywords to analyze conversations for")
    platforms: List[str] = Field(..., description="Platforms to analyze")

@router.post("/brand-mentions")
async def track_brand_mentions(
    request: BrandMentionsRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Track brand mentions across social media platforms"""
    try:
        service = SocialMediaListeningService(db, event_bus, redis)
        result = await service.track_brand_mentions(
            brand=request.brand,
            platforms=request.platforms,
            timeframe=request.timeframe
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Tracking brand mentions for {request.brand} across {len(request.platforms)} platforms"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Brand mentions tracking failed: {str(e)}")

@router.post("/hashtag-monitoring")
async def monitor_hashtags(
    request: HashtagMonitoringRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Monitor specific hashtags across platforms"""
    try:
        service = SocialMediaListeningService(db, event_bus, redis)
        result = await service.monitor_hashtags(
            hashtags=request.hashtags,
            platforms=request.platforms
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Monitoring {len(request.hashtags)} hashtags across {len(request.platforms)} platforms"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hashtag monitoring failed: {str(e)}")

@router.post("/conversation-analysis")
async def analyze_conversations(
    request: ConversationAnalysisRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Analyze conversations and discussions around keywords"""
    try:
        service = SocialMediaListeningService(db, event_bus, redis)
        result = await service.analyze_conversations(
            keywords=request.keywords,
            platforms=request.platforms
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Analyzed conversations for {len(request.keywords)} keywords across {len(request.platforms)} platforms"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversation analysis failed: {str(e)}")

@router.post("/generate-report")
async def generate_listening_report(
    brand: str,
    timeframe: str = "30d",
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Generate comprehensive social media listening report"""
    try:
        service = SocialMediaListeningService(db, event_bus, redis)
        result = await service.generate_listening_report(
            brand=brand,
            timeframe=timeframe
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Generated listening report for {brand} over {timeframe}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
