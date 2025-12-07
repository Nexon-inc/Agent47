from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.sentiment_tracking_service import SentimentTrackingService

router = APIRouter(prefix="/sentiment-tracking", tags=["Sentiment Tracking"])

class SentimentTrackingRequest(BaseModel):
    keywords: List[str] = Field(..., description="Keywords to track sentiment for")
    platforms: List[str] = Field(default=["twitter", "reddit", "reviews"], description="Platforms to monitor")
    time_period: str = Field(default="7d", description="Time period for tracking")

class SentimentHistoryRequest(BaseModel):
    keyword: str = Field(..., description="Keyword to get history for")
    days: int = Field(default=30, description="Number of days to retrieve")

# Dependency
async def get_sentiment_tracking_service() -> SentimentTrackingService:
    service = SentimentTrackingService()
    await service.initialize()
    return service

@router.post("/track")
async def track_sentiment(
    request: SentimentTrackingRequest,
    service: SentimentTrackingService = Depends(get_sentiment_tracking_service)
):
    """Track sentiment for given keywords across platforms"""
    try:
        result = await service.track_sentiment(
            user_id=1,  # TODO: Get from authentication
            keywords=request.keywords,
            platforms=request.platforms,
            time_period=request.time_period
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["sentiment_data"],
                "message": f"Sentiment tracking completed for {len(request.keywords)} keywords"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Sentiment tracking failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track sentiment: {str(e)}"
        )

@router.get("/history/{keyword}")
async def get_sentiment_history(
    keyword: str,
    days: int = 30,
    service: SentimentTrackingService = Depends(get_sentiment_tracking_service)
):
    """Get sentiment history for a specific keyword"""
    try:
        result = await service.get_sentiment_history(
            user_id=1,  # TODO: Get from authentication
            keyword=keyword,
            days=days
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["history"],
                "message": f"Retrieved sentiment history for '{keyword}' over {days} days"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get sentiment history: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sentiment history: {str(e)}"
        )

@router.get("/trending-sentiment")
async def get_trending_sentiment(service: SentimentTrackingService = Depends(get_sentiment_tracking_service)):
    """Get trending sentiment topics"""
    trending_topics = [
        {
            "topic": "artificial intelligence",
            "sentiment": "positive",
            "sentiment_score": 0.85,
            "mention_count": 1250,
            "trend_direction": "increasing"
        },
        {
            "topic": "climate change",
            "sentiment": "negative",
            "sentiment_score": 0.35,
            "mention_count": 890,
            "trend_direction": "stable"
        },
        {
            "topic": "remote work",
            "sentiment": "positive",
            "sentiment_score": 0.72,
            "mention_count": 650,
            "trend_direction": "decreasing"
        }
    ]
    
    return {
        "status": "success",
        "data": trending_topics,
        "message": f"Retrieved {len(trending_topics)} trending sentiment topics"
    }
