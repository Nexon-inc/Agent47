"""
Google Maps Router
API endpoints for Google Maps integration
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List, Dict, Any
import logging
from pydantic import BaseModel

from ..authentication.auth_manager import get_current_active_user
from ..database.models import User
from .google_maps_service import get_google_maps_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/maps", tags=["google-maps"])

class SearchBusinessesRequest(BaseModel):
    query: str
    location: Optional[str] = None
    radius: Optional[int] = None

class ContactBusinessRequest(BaseModel):
    place_id: str
    agent_key: str
    message: str
    contact_method: str = "phone"

class NearbyBusinessesRequest(BaseModel):
    latitude: float
    longitude: float
    radius: int = 1000
    business_type: Optional[str] = None

@router.post("/search-businesses")
async def search_businesses(
    request: SearchBusinessesRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Search for businesses using Google Maps"""
    try:
        maps_service = await get_google_maps_service()
        result = await maps_service.search_businesses(
            query=request.query,
            location=request.location,
            radius=request.radius,
            user_id=current_user.id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Business search failed")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Business search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Business search failed: {str(e)}"
        )

@router.get("/business/{place_id}")
async def get_business_details(
    place_id: str,
    fields: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a business"""
    try:
        maps_service = await get_google_maps_service()
        
        field_list = None
        if fields:
            field_list = fields.split(",")
        
        result = await maps_service.get_business_details(
            place_id=place_id,
            fields=field_list
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to get business details")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get business details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get business details: {str(e)}"
        )

@router.post("/contact-business")
async def contact_business(
    request: ContactBusinessRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Contact a business using agent voice"""
    try:
        maps_service = await get_google_maps_service()
        result = await maps_service.contact_business(
            place_id=request.place_id,
            agent_key=request.agent_key,
            message=request.message,
            user_id=current_user.id,
            contact_method=request.contact_method
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to contact business")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to contact business: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to contact business: {str(e)}"
        )

@router.post("/nearby-businesses")
async def find_nearby_businesses(
    request: NearbyBusinessesRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Find businesses near a location"""
    try:
        maps_service = await get_google_maps_service()
        result = await maps_service.find_nearby_businesses(
            latitude=request.latitude,
            longitude=request.longitude,
            radius=request.radius,
            business_type=request.business_type,
            user_id=current_user.id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to find nearby businesses")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to find nearby businesses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find nearby businesses: {str(e)}"
        )

