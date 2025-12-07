from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.cms_integration_service import CMSIntegrationService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/cms-integration", tags=["CMS Integration"])

# Pydantic Models
class ConnectCMSPlatformRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    platform_name: str = Field(..., description="Platform name")
    connection_config: Dict[str, Any] = Field(..., description="Connection configuration")
    platform_type: str = Field(default="cms", description="Platform type")

class PublishContentToCMSRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    platform_name: str = Field(..., description="Platform name")
    publishing_options: Dict[str, Any] = Field(..., description="Publishing options")

class SyncContentFromCMSRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    platform_name: str = Field(..., description="Platform name")
    sync_options: Dict[str, Any] = Field(..., description="Sync options")

class OptimizeContentForPlatformRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    platform_name: str = Field(..., description="Platform name")
    optimization_goals: List[str] = Field(..., description="Optimization goals")

# Dependency
async def get_cms_integration_service() -> CMSIntegrationService:
    """Get CMS integration service instance"""
    service = CMSIntegrationService()
    await service.initialize()
    return service

# Endpoints
@router.post("/connect-platform", response_model=Dict[str, Any], status_code=201)
async def connect_cms_platform(
    request: ConnectCMSPlatformRequest,
    service: CMSIntegrationService = Depends(get_cms_integration_service)
):
    """Connect to CMS platform"""
    try:
        result = await service.connect_cms_platform(
            user_id=request.user_id,
            platform_name=request.platform_name,
            connection_config=request.connection_config,
            platform_type=request.platform_type
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to connect to CMS platform")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CMS platform connection failed: {str(e)}"
        )

@router.post("/publish-content", response_model=Dict[str, Any], status_code=201)
async def publish_content_to_cms(
    request: PublishContentToCMSRequest,
    service: CMSIntegrationService = Depends(get_cms_integration_service)
):
    """Publish content to connected CMS platform"""
    try:
        result = await service.publish_content_to_cms(
            content_piece_id=request.content_piece_id,
            platform_name=request.platform_name,
            publishing_options=request.publishing_options
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to publish content to CMS")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content publishing failed: {str(e)}"
        )

@router.post("/sync-content", response_model=Dict[str, Any], status_code=201)
async def sync_content_from_cms(
    request: SyncContentFromCMSRequest,
    service: CMSIntegrationService = Depends(get_cms_integration_service)
):
    """Sync content from CMS platform"""
    try:
        result = await service.sync_content_from_cms(
            user_id=request.user_id,
            platform_name=request.platform_name,
            sync_options=request.sync_options
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to sync content from CMS")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content sync failed: {str(e)}"
        )

@router.get("/platform-structure/{user_id}/{platform_name}", response_model=Dict[str, Any], status_code=200)
async def get_platform_content_structure(
    user_id: int,
    platform_name: str,
    service: CMSIntegrationService = Depends(get_cms_integration_service)
):
    """Get content structure and capabilities of platform"""
    try:
        result = await service.get_platform_content_structure(
            user_id=user_id,
            platform_name=platform_name
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get platform structure")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Platform structure retrieval failed: {str(e)}"
        )

@router.post("/optimize-content", response_model=Dict[str, Any], status_code=200)
async def optimize_content_for_platform(
    request: OptimizeContentForPlatformRequest,
    service: CMSIntegrationService = Depends(get_cms_integration_service)
):
    """Optimize content for specific platform"""
    try:
        result = await service.optimize_content_for_platform(
            content_piece_id=request.content_piece_id,
            platform_name=request.platform_name,
            optimization_goals=request.optimization_goals
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to optimize content for platform")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content platform optimization failed: {str(e)}"
        )

@router.get("/supported-platforms")
async def get_supported_platforms():
    """Get list of supported CMS and platform integrations"""
    return {
        "supported_platforms": [
            {
                "id": "wordpress",
                "name": "WordPress",
                "type": "cms",
                "description": "Popular open-source CMS platform",
                "features": ["publish", "sync", "media_upload", "seo", "scheduling"],
                "content_types": ["post", "page", "product", "custom_post"],
                "api_support": "REST API",
                "authentication": "API Key, OAuth"
            },
            {
                "id": "shopify",
                "name": "Shopify",
                "type": "ecommerce",
                "description": "E-commerce platform for online stores",
                "features": ["publish", "sync", "product_management", "inventory"],
                "content_types": ["product", "page", "blog_post", "collection"],
                "api_support": "GraphQL, REST API",
                "authentication": "API Key, OAuth"
            },
            {
                "id": "squarespace",
                "name": "Squarespace",
                "type": "website_builder",
                "description": "Website builder and hosting platform",
                "features": ["publish", "sync", "media_upload", "design"],
                "content_types": ["page", "blog_post", "product", "event"],
                "api_support": "REST API",
                "authentication": "API Key"
            },
            {
                "id": "webflow",
                "name": "Webflow",
                "type": "website_builder",
                "description": "Visual web design and development platform",
                "features": ["publish", "sync", "design", "cms"],
                "content_types": ["page", "blog_post", "collection_item"],
                "api_support": "REST API",
                "authentication": "API Key"
            },
            {
                "id": "contentful",
                "name": "Contentful",
                "type": "headless_cms",
                "description": "Headless content management system",
                "features": ["publish", "sync", "content_modeling", "api"],
                "content_types": ["entry", "asset", "space"],
                "api_support": "REST API, GraphQL",
                "authentication": "API Key, OAuth"
            },
            {
                "id": "ghost",
                "name": "Ghost",
                "type": "cms",
                "description": "Modern publishing platform for content creators",
                "features": ["publish", "sync", "newsletter", "membership"],
                "content_types": ["post", "page", "tag", "author"],
                "api_support": "REST API",
                "authentication": "API Key"
            }
        ]
    }

@router.get("/integration-features")
async def get_integration_features():
    """Get available integration features and capabilities"""
    return {
        "integration_features": [
            {
                "id": "publish",
                "name": "Content Publishing",
                "description": "Publish content directly to connected platforms",
                "capabilities": [
                    "Direct content publishing",
                    "Scheduled publishing",
                    "Draft and published states",
                    "Content formatting",
                    "Media upload and management"
                ],
                "supported_platforms": ["wordpress", "shopify", "squarespace", "webflow", "contentful", "ghost"]
            },
            {
                "id": "sync",
                "name": "Content Synchronization",
                "description": "Sync content between Shakes and connected platforms",
                "capabilities": [
                    "Bidirectional content sync",
                    "Real-time updates",
                    "Conflict resolution",
                    "Version control",
                    "Change tracking"
                ],
                "supported_platforms": ["wordpress", "shopify", "squarespace", "webflow", "contentful", "ghost"]
            },
            {
                "id": "media_upload",
                "name": "Media Upload",
                "description": "Upload and manage media files on connected platforms",
                "capabilities": [
                    "Image and video upload",
                    "Media optimization",
                    "Alt text management",
                    "Media organization",
                    "CDN integration"
                ],
                "supported_platforms": ["wordpress", "shopify", "squarespace", "webflow", "contentful"]
            },
            {
                "id": "seo",
                "name": "SEO Optimization",
                "description": "Optimize content for search engines on connected platforms",
                "capabilities": [
                    "Meta tag management",
                    "SEO analysis",
                    "Keyword optimization",
                    "Schema markup",
                    "Sitemap generation"
                ],
                "supported_platforms": ["wordpress", "shopify", "squarespace", "webflow", "ghost"]
            },
            {
                "id": "scheduling",
                "name": "Content Scheduling",
                "description": "Schedule content publication on connected platforms",
                "capabilities": [
                    "Future publishing",
                    "Recurring content",
                    "Time zone support",
                    "Bulk scheduling",
                    "Schedule management"
                ],
                "supported_platforms": ["wordpress", "shopify", "squarespace", "ghost"]
            }
        ]
    }

@router.get("/integration-best-practices")
async def get_integration_best_practices():
    """Get best practices for CMS and platform integration"""
    return {
        "integration_best_practices": [
            {
                "category": "connection_management",
                "title": "Connection Management",
                "practices": [
                    "Use secure authentication methods",
                    "Regularly update API credentials",
                    "Monitor connection health",
                    "Implement error handling and retry logic",
                    "Test connections before production use"
                ]
            },
            {
                "category": "content_optimization",
                "title": "Content Optimization",
                "practices": [
                    "Optimize content for each platform's requirements",
                    "Use platform-specific formatting and features",
                    "Ensure mobile responsiveness",
                    "Optimize images and media for each platform",
                    "Follow platform-specific SEO best practices"
                ]
            },
            {
                "category": "synchronization",
                "title": "Synchronization",
                "practices": [
                    "Establish clear sync rules and priorities",
                    "Handle conflicts gracefully",
                    "Maintain data consistency",
                    "Monitor sync performance",
                    "Implement backup and recovery procedures"
                ]
            },
            {
                "category": "performance",
                "title": "Performance",
                "practices": [
                    "Optimize API calls and reduce latency",
                    "Implement caching where appropriate",
                    "Monitor integration performance",
                    "Use batch operations when possible",
                    "Implement rate limiting and throttling"
                ]
            }
        ]
    }
