from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
from ..services.social_media_service import SocialMediaService
from ..models import SupportChannel, TicketPriority, TicketStatus, TicketCategory

router = APIRouter()

# Pydantic models for request/response
class CollaborationInquiryRequest(BaseModel):
    description: str
    platform: str
    reach: Optional[int] = None
    engagement_rate: Optional[float] = None
    brand_category: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    contact_preference: Optional[str] = None

class SocialEngagementRequest(BaseModel):
    platform: str
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

async def get_social_service() -> SocialMediaService:
    """Dependency to get social media service"""
    service = SocialMediaService()
    await service.initialize()
    return service

@router.post("/prioritize/{customer_id}/{platform}", response_model=Dict[str, Any])
async def prioritize_social_channels(
    customer_id: int,
    platform: str,
    social_service: SocialMediaService = Depends(get_social_service)
):
    """Prioritize high-engagement social media channels"""
    try:
        result = await social_service.prioritize_social_channels(
            customer_id=customer_id,
            platform=platform
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaboration/{customer_id}", response_model=Dict[str, Any])
async def track_collaboration_inquiry(
    customer_id: int,
    request: CollaborationInquiryRequest,
    social_service: SocialMediaService = Depends(get_social_service)
):
    """Track brand collaboration inquiry"""
    try:
        result = await social_service.track_collaboration_inquiries(
            customer_id=customer_id,
            inquiry_data=request.dict()
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/engagement/{customer_id}/{platform}", response_model=Dict[str, Any])
async def analyze_social_engagement(
    customer_id: int,
    platform: str,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    social_service: SocialMediaService = Depends(get_social_service)
):
    """Analyze social media engagement metrics"""
    try:
        result = await social_service.analyze_social_engagement(
            customer_id=customer_id,
            platform=platform,
            date_from=date_from,
            date_to=date_to
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/{platform}", response_model=Dict[str, Any])
async def get_social_insights(
    platform: str,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    social_service: SocialMediaService = Depends(get_social_service)
):
    """Get social media insights and trends"""
    try:
        result = await social_service.get_social_insights(
            platform=platform,
            date_from=date_from,
            date_to=date_to
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms", response_model=Dict[str, Any])
async def get_available_social_platforms(
    social_service: SocialMediaService = Depends(get_social_service)
):
    """Get list of available social media platforms"""
    try:
        platforms = list(social_service._social_clients.keys())
        return {
            "success": True,
            "platforms": platforms,
            "count": len(platforms),
            "message": f"Found {len(platforms)} social media platforms configured"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/{platform}", response_model=Dict[str, Any])
async def check_social_platform_health(
    platform: str,
    social_service: SocialMediaService = Depends(get_social_service)
):
    """Check health status of social media platform"""
    try:
        # Check if platform is configured
        if platform not in social_service._social_clients:
            return {
                "success": False,
                "platform": platform,
                "status": "not_configured",
                "message": f"Social platform {platform} is not configured"
            }
        
        # Perform actual health check for the platform
        health_result = await social_service.check_platform_health(platform)
        
        return health_result
    except Exception as e:
        return {
            "success": False,
            "platform": platform,
            "status": "error",
            "error": str(e)
        }

@router.get("/collaborations", response_model=Dict[str, Any])
async def get_collaboration_inquiries(
    customer_id: Optional[int] = Query(None),
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    social_service: SocialMediaService = Depends(get_social_service)
):
    """Get collaboration inquiries with filters"""
    try:
        # Get collaboration inquiries from the service
        result = await social_service.get_collaboration_inquiries(
            customer_id=customer_id,
            platform=platform,
            status=status
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends/{platform}", response_model=Dict[str, Any])
async def get_social_trends(
    platform: str,
    trend_type: str = Query("engagement", description="Type of trend to analyze"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    social_service: SocialMediaService = Depends(get_social_service)
):
    """Get social media trends and patterns"""
    try:
        # Get social media trends from the service
        result = await social_service.get_social_trends(
            platform=platform,
            trend_type=trend_type,
            date_from=date_from,
            date_to=date_to
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
