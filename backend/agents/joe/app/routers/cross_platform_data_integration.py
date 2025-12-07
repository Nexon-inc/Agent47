from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.cross_platform_data_integration_service import CrossPlatformDataIntegrationService
from backend.core.authentication.auth_manager import AuthManager

router = APIRouter(prefix="/cross-platform-data-integration", tags=["Cross-Platform Data Integration"])

class PlatformIntegrationRequest(BaseModel):
    platforms: List[str] = Field(..., description="List of platforms to integrate data from")
    data_types: List[str] = Field(..., description="Types of data to integrate")
    integration_config: Dict[str, Any] = Field(..., description="Configuration for data integration")

class DashboardCreationRequest(BaseModel):
    integration_results: Dict[str, Any] = Field(..., description="Results from platform data integration")
    dashboard_config: Dict[str, Any] = Field(..., description="Configuration for dashboard creation")

# Dependencies
async def get_cross_platform_data_integration_service() -> CrossPlatformDataIntegrationService:
    service = CrossPlatformDataIntegrationService()
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

@router.post("/integrate-platform-data")
async def integrate_platform_data(
    request: PlatformIntegrationRequest,
    service: CrossPlatformDataIntegrationService = Depends(get_cross_platform_data_integration_service),
    user_id: int = Depends(get_current_user_id)
):
    """Integrate data from multiple platforms into unified insights"""
    try:
        result = await service.integrate_platform_data(
            user_id=user_id,
            platforms=request.platforms,
            data_types=request.data_types,
            integration_config=request.integration_config
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["integration_data"],
                "message": f"Successfully integrated data from {len(request.platforms)} platforms"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Platform data integration failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to integrate platform data: {str(e)}"
        )

@router.post("/create-unified-dashboard")
async def create_unified_dashboard(
    request: DashboardCreationRequest,
    service: CrossPlatformDataIntegrationService = Depends(get_cross_platform_data_integration_service),
    user_id: int = Depends(get_current_user_id)
):
    """Create unified dashboard from integrated platform data"""
    try:
        result = await service.create_unified_dashboard(
            user_id=user_id,
            integration_results=request.integration_results,
            dashboard_config=request.dashboard_config
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["dashboard_data"],
                "message": "Unified dashboard created successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Dashboard creation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create unified dashboard: {str(e)}"
        )

@router.get("/supported-platforms")
async def get_supported_platforms(service: CrossPlatformDataIntegrationService = Depends(get_cross_platform_data_integration_service)):
    """Get supported platforms for data integration"""
    supported_platforms = [
        {
            "platform_id": "social_media",
            "name": "Social Media Platforms",
            "description": "Facebook, Instagram, Twitter, LinkedIn, TikTok",
            "data_types": ["posts", "comments", "engagement", "sentiment", "reach"],
            "integration_methods": ["API", "Web scraping", "Third-party tools"],
            "data_freshness": "Real-time to hourly"
        },
        {
            "platform_id": "web_analytics",
            "name": "Web Analytics",
            "description": "Google Analytics, Adobe Analytics, Mixpanel",
            "data_types": ["traffic", "conversions", "user_behavior", "page_views"],
            "integration_methods": ["API", "Data export", "Webhook"],
            "data_freshness": "Real-time to daily"
        },
        {
            "platform_id": "news_apis",
            "name": "News and Media",
            "description": "Google News, Reuters, Associated Press",
            "data_types": ["articles", "mentions", "sentiment", "topics"],
            "integration_methods": ["RSS feeds", "API", "Web scraping"],
            "data_freshness": "Hourly to daily"
        },
        {
            "platform_id": "ecommerce",
            "name": "E-commerce Platforms",
            "description": "Shopify, WooCommerce, Amazon, eBay",
            "data_types": ["sales", "products", "reviews", "inventory"],
            "integration_methods": ["API", "Data export", "Webhook"],
            "data_freshness": "Real-time to daily"
        },
        {
            "platform_id": "crm_systems",
            "name": "CRM Systems",
            "description": "Salesforce, HubSpot, Pipedrive, Zoho",
            "data_types": ["leads", "contacts", "deals", "activities"],
            "integration_methods": ["API", "Data sync", "Webhook"],
            "data_freshness": "Real-time to hourly"
        }
    ]
    
    return {
        "status": "success",
        "data": supported_platforms,
        "message": f"Retrieved {len(supported_platforms)} supported platforms"
    }
