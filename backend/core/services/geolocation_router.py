"""
Geo-location Router for Business Targeting
API endpoints for location-based business targeting and marketing
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, Dict, Any, List
import logging
from pydantic import BaseModel

from ..authentication.auth_manager import get_current_active_user
from ..database.models import User
from .geolocation_service import get_geolocation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/geolocation", tags=["geolocation"])

class TargetBusinessesRequest(BaseModel):
    location: str
    business_type: Optional[str] = None
    radius_meters: int = 5000
    filters: Optional[Dict[str, Any]] = None

class CreateCampaignRequest(BaseModel):
    campaign_name: str
    target_locations: List[str]
    campaign_type: str = "outreach"
    agent_key: Optional[str] = None

class AmplifyReachRequest(BaseModel):
    base_location: str
    expansion_radius_km: int = 10
    business_type: Optional[str] = None

@router.post("/target-businesses")
async def target_businesses_by_location(
    request: TargetBusinessesRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Find businesses in a location for targeting"""
    try:
        geolocation_service = await get_geolocation_service()
        result = await geolocation_service.target_businesses_by_location(
            user_id=current_user.id,
            location=request.location,
            business_type=request.business_type,
            radius_meters=request.radius_meters,
            filters=request.filters
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to target businesses")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to target businesses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to target businesses: {str(e)}"
        )

@router.post("/create-campaign")
async def create_geo_targeted_campaign(
    request: CreateCampaignRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Create a geo-targeted campaign for business outreach"""
    try:
        geolocation_service = await get_geolocation_service()
        result = await geolocation_service.create_geo_targeted_campaign(
            user_id=current_user.id,
            campaign_name=request.campaign_name,
            target_locations=request.target_locations,
            campaign_type=request.campaign_type,
            agent_key=request.agent_key
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to create campaign")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}"
        )

@router.post("/amplify-reach")
async def amplify_reach_by_location(
    request: AmplifyReachRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Amplify reach by expanding to nearby locations"""
    try:
        geolocation_service = await get_geolocation_service()
        result = await geolocation_service.amplify_reach_by_location(
            user_id=current_user.id,
            base_location=request.base_location,
            expansion_radius_km=request.expansion_radius_km,
            business_type=request.business_type
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to amplify reach")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to amplify reach: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to amplify reach: {str(e)}"
        )

@router.get("/analytics/{location}")
async def get_location_analytics(
    location: str,
    timeframe_days: int = 30,
    current_user: User = Depends(get_current_active_user)
):
    """Get analytics for a specific location"""
    try:
        geolocation_service = await get_geolocation_service()
        result = await geolocation_service.get_location_analytics(
            user_id=current_user.id,
            location=location,
            timeframe_days=timeframe_days
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to get location analytics")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get location analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get location analytics: {str(e)}"
        )
