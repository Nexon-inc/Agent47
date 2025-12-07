from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
import json

from ..services.emerging_channels_service import EmergingChannelsService
from ..database import get_eric_database

router = APIRouter()

class ChannelIntegrationRequest(BaseModel):
    channel_name: str
    brand_id: int
    api_credentials: Dict[str, Any] = {}
    webhook_url: str = ""
    settings: Dict[str, Any] = {}

class ContentGenerationRequest(BaseModel):
    channel_name: str
    product: str
    audience: str
    key_benefits: str

class PerformanceTrackingRequest(BaseModel):
    integration_id: str
    metrics_data: Dict[str, Any]

class IntegrationResponse(BaseModel):
    success: bool
    integration: Dict[str, Any]

class ContentResponse(BaseModel):
    success: bool
    content: Dict[str, Any]

class PerformanceResponse(BaseModel):
    success: bool
    performance_record: Dict[str, Any]

class SupportedChannelsResponse(BaseModel):
    success: bool
    supported_channels: Dict[str, Any]

class ChannelIntegrationsResponse(BaseModel):
    success: bool
    integrations: List[Dict[str, Any]]

@router.post("/emerging-channels/setup", response_model=IntegrationResponse)
async def setup_channel_integration(request: ChannelIntegrationRequest):
    """Setup integration with an emerging sales channel"""
    try:
        service = EmergingChannelsService()
        channel_data = request.dict()
        result = await service.setup_channel_integration(channel_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emerging-channels/generate-content", response_model=ContentResponse)
async def generate_channel_content(request: ContentGenerationRequest):
    """Generate content optimized for specific emerging channels"""
    try:
        service = EmergingChannelsService()
        content_data = request.dict()
        result = await service.generate_channel_content(request.channel_name, content_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emerging-channels/track-performance", response_model=PerformanceResponse)
async def track_channel_performance(request: PerformanceTrackingRequest):
    """Track performance metrics for integrated channels"""
    try:
        service = EmergingChannelsService()
        result = await service.track_channel_performance(request.integration_id, request.metrics_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emerging-channels/supported", response_model=SupportedChannelsResponse)
async def get_supported_channels():
    """Get list of supported emerging channels"""
    try:
        service = EmergingChannelsService()
        result = await service.get_supported_channels()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emerging-channels/integrations", response_model=ChannelIntegrationsResponse)
async def get_channel_integrations(
    brand_id: int = Query(..., description="Brand ID")
):
    """Get all channel integrations for a brand"""
    try:
        service = EmergingChannelsService()
        result = await service.get_channel_integrations(brand_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emerging-channels/test-connection")
async def test_channel_connection(
    channel_name: str = Query(..., description="Channel name"),
    api_credentials: str = Query(..., description="API credentials as JSON string")
):
    """Test connection to a specific channel"""
    try:
        service = EmergingChannelsService()
        credentials = json.loads(api_credentials)
        
        if channel_name == "tiktok":
            is_connected = await service._test_tiktok_connection(credentials)
        elif channel_name == "instagram_reels":
            is_connected = await service._test_instagram_connection(credentials)
        elif channel_name == "linkedin_live":
            is_connected = await service._test_linkedin_connection(credentials)
        elif channel_name == "clubhouse":
            is_connected = await service._test_clubhouse_connection(credentials)
        elif channel_name == "telegram":
            is_connected = await service._test_telegram_connection(credentials)
        elif channel_name == "discord":
            is_connected = await service._test_discord_connection(credentials)
        else:
            raise HTTPException(status_code=400, detail="Unsupported channel")
        
        return {
            "success": True,
            "channel_name": channel_name,
            "connection_status": "connected" if is_connected else "failed",
            "tested_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emerging-channels/trending-hashtags")
async def get_trending_hashtags(
    platform: str = Query(..., description="Platform name")
):
    """Get trending hashtags for a specific platform"""
    try:
        service = EmergingChannelsService()
        hashtags = await service._get_trending_hashtags(platform)
        
        return {
            "success": True,
            "platform": platform,
            "trending_hashtags": hashtags,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emerging-channels/performance-insights")
async def get_performance_insights(
    integration_id: str = Query(..., description="Integration ID")
):
    """Get performance insights for a channel integration"""
    try:
        service = EmergingChannelsService()
        insights_key = f"performance_insights:{integration_id}"
        insights_data = await service.redis_manager.get(insights_key)
        
        if insights_data:
            insights = json.loads(insights_data)
            return {
                "success": True,
                "integration_id": integration_id,
                "insights": insights
            }
        else:
            return {
                "success": True,
                "integration_id": integration_id,
                "insights": {
                    "engagement_trend": "unknown",
                    "reach_trend": "unknown",
                    "recommendations": ["No performance data available yet"]
                }
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emerging-channels/channel-analytics")
async def get_channel_analytics(
    brand_id: int = Query(..., description="Brand ID"),
    period: str = Query("month", description="Time period")
):
    """Get analytics across all integrated channels"""
    try:
        service = EmergingChannelsService()
        integrations_result = await service.get_channel_integrations(brand_id)
        
        if not integrations_result["success"]:
            raise HTTPException(status_code=400, detail=integrations_result["error"])
        
        analytics = {
            "total_integrations": len(integrations_result["integrations"]),
            "active_channels": [],
            "total_reach": 0,
            "total_engagement": 0,
            "total_conversions": 0,
            "channel_performance": {}
        }
        
        for integration in integrations_result["integrations"]:
            channel_name = integration["channel_name"]
            integration_id = integration["integration_id"]
            
            performance_keys = await service.redis_manager.keys(f"channel_performance:*{integration_id}*")
            
            if performance_keys:
                latest_performance = await service.redis_manager.get(performance_keys[-1])
                if latest_performance:
                    performance_data = json.loads(latest_performance)
                    metrics = performance_data.get("metrics", {})
                    
                    analytics["total_reach"] += metrics.get("reach", 0)
                    analytics["total_engagement"] += metrics.get("engagement", 0)
                    analytics["total_conversions"] += metrics.get("conversions", 0)
                    
                    analytics["channel_performance"][channel_name] = {
                        "reach": metrics.get("reach", 0),
                        "engagement": metrics.get("engagement", 0),
                        "conversions": metrics.get("conversions", 0),
                        "engagement_rate": metrics.get("engagement_rate", 0)
                    }
            
            analytics["active_channels"].append(channel_name)
        
        return {
            "success": True,
            "analytics": analytics,
            "period": period
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emerging-channels/bulk-content-generation")
async def generate_bulk_content(
    channels: List[str] = Body(..., description="List of channels"),
    content_data: Dict[str, Any] = Body(..., description="Content data")
):
    """Generate content for multiple channels at once"""
    try:
        service = EmergingChannelsService()
        results = {}
        
        for channel in channels:
            result = await service.generate_channel_content(channel, content_data)
            results[channel] = result
        
        return {
            "success": True,
            "bulk_results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emerging-channels/channel-recommendations")
async def get_channel_recommendations(
    brand_id: int = Query(..., description="Brand ID"),
    industry: str = Query(..., description="Industry"),
    target_audience: str = Query(..., description="Target audience")
):
    """Get channel recommendations based on industry and audience"""
    try:
        service = EmergingChannelsService()
        
        recommendations = {
            "primary_channels": [],
            "secondary_channels": [],
            "reasoning": {}
        }
        
        # Industry-based recommendations
        if industry.lower() in ["technology", "saas", "startup"]:
            recommendations["primary_channels"] = ["linkedin_live", "discord"]
            recommendations["secondary_channels"] = ["telegram", "instagram_reels"]
            recommendations["reasoning"]["linkedin_live"] = "Professional networking platform ideal for B2B tech companies"
            recommendations["reasoning"]["discord"] = "Community building platform popular with tech-savvy audiences"
        
        elif industry.lower() in ["fashion", "beauty", "lifestyle"]:
            recommendations["primary_channels"] = ["instagram_reels", "tiktok"]
            recommendations["secondary_channels"] = ["telegram", "discord"]
            recommendations["reasoning"]["instagram_reels"] = "Visual platform perfect for fashion and beauty content"
            recommendations["reasoning"]["tiktok"] = "Trending platform with high engagement for lifestyle content"
        
        elif industry.lower() in ["finance", "consulting", "professional_services"]:
            recommendations["primary_channels"] = ["linkedin_live", "clubhouse"]
            recommendations["secondary_channels"] = ["telegram", "discord"]
            recommendations["reasoning"]["linkedin_live"] = "Professional platform for thought leadership and networking"
            recommendations["reasoning"]["clubhouse"] = "Audio platform for professional discussions and networking"
        
        else:
            recommendations["primary_channels"] = ["instagram_reels", "linkedin_live"]
            recommendations["secondary_channels"] = ["telegram", "discord"]
            recommendations["reasoning"]["general"] = "Balanced approach for broad industry appeal"
        
        return {
            "success": True,
            "recommendations": recommendations,
            "industry": industry,
            "target_audience": target_audience
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/emerging-channels/integrations/{integration_id}")
async def remove_channel_integration(integration_id: str):
    """Remove a channel integration"""
    try:
        service = EmergingChannelsService()
        integration_key = f"channel_integration:{integration_id}"
        
        integration_data = await service.redis_manager.get(integration_key)
        if not integration_data:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        await service.redis_manager.delete(integration_key)
        
        await service._publish_integration_event("channel_integration_removed", {
            "integration_id": integration_id,
            "removed_at": datetime.utcnow().isoformat()
        })
        
        return {
            "success": True,
            "message": "Integration removed successfully",
            "integration_id": integration_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/emerging-channels/integrations/{integration_id}")
async def update_channel_integration(
    integration_id: str,
    update_data: Dict[str, Any] = Body(..., description="Update data")
):
    """Update channel integration settings"""
    try:
        service = EmergingChannelsService()
        integration_key = f"channel_integration:{integration_id}"
        
        integration_data = await service.redis_manager.get(integration_key)
        if not integration_data:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        integration = json.loads(integration_data)
        
        # Update allowed fields
        if "api_credentials" in update_data:
            integration["api_credentials"] = update_data["api_credentials"]
        if "webhook_url" in update_data:
            integration["webhook_url"] = update_data["webhook_url"]
        if "settings" in update_data:
            integration["settings"] = update_data["settings"]
        
        integration["updated_at"] = datetime.utcnow()
        
        await service.redis_manager.set(
            integration_key,
            json.dumps(integration, default=str),
            expire=86400 * 365
        )
        
        await service._publish_integration_event("channel_integration_updated", {
            "integration_id": integration_id,
            "updated_at": integration["updated_at"]
        })
        
        return {
            "success": True,
            "message": "Integration updated successfully",
            "integration": integration
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
