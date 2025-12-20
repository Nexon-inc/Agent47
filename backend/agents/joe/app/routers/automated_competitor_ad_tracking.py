from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.automated_competitor_ad_tracking_service import AutomatedCompetitorAdTrackingService
from core.authentication.auth_manager import AuthManager

router = APIRouter(prefix="/automated-competitor-ad-tracking", tags=["Automated Competitor Ad Tracking"])

class CompetitorAdTrackingRequest(BaseModel):
    competitor_urls: List[str] = Field(..., description="List of competitor URLs to track")
    platforms: List[str] = Field(default=["facebook", "google", "linkedin"], description="Advertising platforms to monitor")

class AdStrategyAnalysisRequest(BaseModel):
    tracking_data: Dict[str, Any] = Field(..., description="Data from competitor ad tracking")
    analysis_focus: str = Field(default="comprehensive", description="Focus area for strategy analysis")

# Dependencies
async def get_automated_competitor_ad_tracking_service() -> AutomatedCompetitorAdTrackingService:
    service = AutomatedCompetitorAdTrackingService()
    await service.initialize()
    return service

async def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    """Get current user ID from authentication token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        # Extract token from "Bearer <token>" format
        token = authorization.replace("Bearer ", "")
        auth_manager = AuthManager()
        user_data = await auth_manager.verify_token(token)
        return user_data.get("user_id")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")

@router.post("/track-competitor-ads")
async def track_competitor_ads(
    request: CompetitorAdTrackingRequest,
    service: AutomatedCompetitorAdTrackingService = Depends(get_automated_competitor_ad_tracking_service),
    user_id: int = Depends(get_current_user_id)
):
    """Track competitor ad campaigns across specified platforms"""
    try:
        result = await service.track_competitor_ads(
            user_id=user_id,
            competitor_urls=request.competitor_urls,
            platforms=request.platforms
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["tracking_data"],
                "message": f"Tracked ads for {len(request.competitor_urls)} competitors successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Competitor ad tracking failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track competitor ads: {str(e)}"
        )

@router.post("/analyze-ad-strategies")
async def analyze_ad_strategies(
    request: AdStrategyAnalysisRequest,
    service: AutomatedCompetitorAdTrackingService = Depends(get_automated_competitor_ad_tracking_service),
    user_id: int = Depends(get_current_user_id)
):
    """Analyze competitor ad strategies and provide insights"""
    try:
        result = await service.analyze_ad_strategies(
            user_id=user_id,
            tracking_data=request.tracking_data,
            analysis_focus=request.analysis_focus
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["analysis_data"],
                "message": "Ad strategy analysis completed successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ad strategy analysis failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze ad strategies: {str(e)}"
        )

@router.get("/supported-platforms")
async def get_supported_platforms(service: AutomatedCompetitorAdTrackingService = Depends(get_automated_competitor_ad_tracking_service)):
    """Get supported advertising platforms for competitor tracking"""
    supported_platforms = [
        {
            "platform_id": "facebook",
            "name": "Facebook Ads",
            "description": "Facebook and Instagram advertising campaigns",
            "data_types": ["ad_creative", "targeting", "performance_metrics", "budget_info"],
            "tracking_capabilities": "High - Comprehensive ad library access"
        },
        {
            "platform_id": "google_ads",
            "name": "Google Ads",
            "description": "Google Search, Display, and YouTube advertising",
            "data_types": ["search_terms", "ad_copy", "landing_pages", "performance_data"],
            "tracking_capabilities": "Medium - Limited transparency but good insights"
        },
        {
            "platform_id": "linkedin",
            "name": "LinkedIn Ads",
            "description": "Professional networking platform advertising",
            "data_types": ["sponsored_content", "targeting", "engagement_metrics"],
            "tracking_capabilities": "Medium - Good for B2B insights"
        },
        {
            "platform_id": "twitter",
            "name": "Twitter Ads",
            "description": "Twitter platform advertising campaigns",
            "data_types": ["promoted_tweets", "targeting", "engagement_data"],
            "tracking_capabilities": "Medium - Good for real-time insights"
        },
        {
            "platform_id": "tiktok",
            "name": "TikTok Ads",
            "description": "TikTok platform advertising",
            "data_types": ["video_ads", "targeting", "performance_metrics"],
            "tracking_capabilities": "Low - Limited transparency"
        }
    ]
    
    return {
        "status": "success",
        "data": supported_platforms,
        "message": f"Retrieved {len(supported_platforms)} supported platforms"
    }
