from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.competitor_ad_tracking_service import CompetitorAdTrackingService

router = APIRouter(prefix="/competitor-ad-tracking", tags=["Competitor Ad Tracking"])

class CompetitorTrackingRequest(BaseModel):
    competitor_name: str = Field(..., description="Name of competitor to track")
    platform: str = Field(default="all", description="Platform to track")

class StrategyAnalysisRequest(BaseModel):
    competitor_names: List[str] = Field(..., description="List of competitors to analyze")

# Dependency
async def get_competitor_ad_tracking_service() -> CompetitorAdTrackingService:
    service = CompetitorAdTrackingService()
    await service.initialize()
    return service

@router.post("/track-ads")
async def track_competitor_ads(
    request: CompetitorTrackingRequest,
    service: CompetitorAdTrackingService = Depends(get_competitor_ad_tracking_service)
):
    """Track competitor ads across platforms"""
    try:
        result = await service.track_competitor_ads(
            user_id=1,  # TODO: Get from authentication
            competitor_name=request.competitor_name,
            platform=request.platform
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["tracking_data"],
                "message": f"Ad tracking completed for {request.competitor_name}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ad tracking failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track competitor ads: {str(e)}"
        )

@router.post("/analyze-strategies")
async def analyze_ad_strategies(
    request: StrategyAnalysisRequest,
    service: CompetitorAdTrackingService = Depends(get_competitor_ad_tracking_service)
):
    """Analyze ad strategies across multiple competitors"""
    try:
        result = await service.analyze_ad_strategies(
            user_id=1,  # TODO: Get from authentication
            competitor_names=request.competitor_names
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["strategy_data"],
                "message": f"Strategy analysis completed for {len(request.competitor_names)} competitors"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Strategy analysis failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze ad strategies: {str(e)}"
        )

@router.get("/platforms")
async def get_tracking_platforms(service: CompetitorAdTrackingService = Depends(get_competitor_ad_tracking_service)):
    """Get supported platforms for ad tracking"""
    platforms = [
        {
            "id": "facebook",
            "name": "Facebook",
            "description": "Facebook and Instagram ads",
            "tracking_capabilities": ["Ad content", "Spend estimates", "Reach estimates"]
        },
        {
            "id": "google_ads",
            "name": "Google Ads",
            "description": "Google Search and Display ads",
            "tracking_capabilities": ["Ad content", "Keywords", "Spend estimates"]
        },
        {
            "id": "linkedin",
            "name": "LinkedIn",
            "description": "LinkedIn advertising",
            "tracking_capabilities": ["Ad content", "Targeting", "Spend estimates"]
        },
        {
            "id": "twitter",
            "name": "Twitter",
            "description": "Twitter advertising",
            "tracking_capabilities": ["Ad content", "Engagement", "Spend estimates"]
        }
    ]
    
    return {
        "status": "success",
        "data": platforms,
        "message": f"Retrieved {len(platforms)} tracking platforms"
    }
