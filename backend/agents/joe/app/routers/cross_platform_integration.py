"""
Cross-Platform Integration Router

This router handles multi-platform connectivity and data synchronization endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.cross_platform_integration_service import CrossPlatformIntegrationService

router = APIRouter(prefix="/cross-platform-integration", tags=["Cross Platform Integration"])

class PlatformConnectionRequest(BaseModel):
    platform_config: Dict[str, Any] = Field(..., description="Platform configuration for connection")

class DataSyncRequest(BaseModel):
    sync_config: Dict[str, Any] = Field(..., description="Data synchronization configuration")

# Dependency
async def get_cross_platform_integration_service() -> CrossPlatformIntegrationService:
    service = CrossPlatformIntegrationService()
    await service.initialize()
    return service

@router.post("/connect-platform")
async def connect_platform(
    request: PlatformConnectionRequest,
    service: CrossPlatformIntegrationService = Depends(get_cross_platform_integration_service)
):
    """Connect to a new platform"""
    try:
        result = await service.connect_platform(
            user_id=1,  # TODO: Get from authentication
            platform_config=request.platform_config
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["connection_data"],
                "message": f"Successfully connected to platform"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Platform connection failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect platform: {str(e)}"
        )

@router.post("/sync-data")
async def sync_data_across_platforms(
    request: DataSyncRequest,
    service: CrossPlatformIntegrationService = Depends(get_cross_platform_integration_service)
):
    """Synchronize data across connected platforms"""
    try:
        result = await service.sync_data_across_platforms(
            user_id=1,  # TODO: Get from authentication
            sync_config=request.sync_config
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["sync_data"],
                "message": "Cross-platform data synchronization completed"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data synchronization failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to synchronize data: {str(e)}"
        )

@router.get("/supported-platforms")
async def get_supported_platforms(service: CrossPlatformIntegrationService = Depends(get_cross_platform_integration_service)):
    """Get list of supported platforms for integration"""
    platforms = [
        {
            "id": "google_analytics",
            "name": "Google Analytics",
            "description": "Web analytics and reporting platform",
            "integration_type": "api",
            "data_types": ["traffic", "demographics", "behavior", "conversions"]
        },
        {
            "id": "facebook_insights",
            "name": "Facebook Insights",
            "description": "Social media analytics and audience insights",
            "integration_type": "api",
            "data_types": ["page_insights", "post_insights", "audience", "engagement"]
        },
        {
            "id": "twitter_analytics",
            "name": "Twitter Analytics",
            "description": "Twitter performance and audience analytics",
            "integration_type": "api",
            "data_types": ["tweet_activity", "audience_insights", "engagement"]
        },
        {
            "id": "linkedin_insights",
            "name": "LinkedIn Insights",
            "description": "Professional network analytics and audience data",
            "integration_type": "api",
            "data_types": ["company_insights", "audience", "content_performance"]
        },
        {
            "id": "semrush",
            "name": "SEMrush",
            "description": "SEO and competitive research platform",
            "integration_type": "api",
            "data_types": ["keyword_research", "competitor_analysis", "backlink_data"]
        }
    ]
    
    return {
        "status": "success",
        "data": platforms,
        "message": f"Retrieved {len(platforms)} supported platforms"
    }
