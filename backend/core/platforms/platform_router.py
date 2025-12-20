from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging
from .platform_manager import PlatformManager
from .models import PlatformType, PlatformStatus, CredentialStatus
from ..authentication.auth_manager import get_current_user
from ..user_management.user_manager import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/platforms", tags=["platforms"])

class PlatformResponse(BaseModel):
    id: int
    name: str
    display_name: str
    platform_type: str
    description: str
    api_version: str
    base_url: str
    status: str
    rate_limits: Dict[str, Any]
    supported_features: Dict[str, Any]
    authentication_methods: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class PlatformConnectionResponse(BaseModel):
    id: int
    user_id: int
    platform_id: int
    platform_name: str
    display_name: str
    status: str
    connected_at: Optional[datetime]
    last_sync: Optional[datetime]
    credentials_status: str
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]

class PlatformMetricsResponse(BaseModel):
    platform_id: int
    platform_name: str
    posts_count: int
    followers_count: int
    engagement_rate: float
    last_activity: Optional[datetime]
    health_score: float
    error_count: int
    success_rate: float

class ConnectPlatformRequest(BaseModel):
    platform_id: int
    credentials: Dict[str, Any]

class DisconnectPlatformRequest(BaseModel):
    platform_id: int

@router.get("/", response_model=List[PlatformResponse])
async def get_available_platforms(
    platform_type: Optional[str] = Query(None, description="Filter by platform type"),
    current_user: User = Depends(get_current_user)
):
    """Get all available platforms"""
    try:
        platform_manager = PlatformManager()
        await platform_manager.initialize()
        
        platforms = await platform_manager.get_available_platforms(
            platform_type=platform_type
        )
        
        return [
            PlatformResponse(
                id=platform.id,
                name=platform.name,
                display_name=platform.display_name,
                platform_type=platform.platform_type.value,
                description=platform.description,
                api_version=platform.api_version,
                base_url=platform.base_url,
                status=platform.status.value,
                rate_limits=platform.rate_limits,
                supported_features=platform.supported_features,
                authentication_methods=platform.authentication_methods,
                created_at=platform.created_at,
                updated_at=platform.updated_at
            )
            for platform in platforms
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get platforms: {str(e)}"
        )

@router.get("/connected", response_model=List[PlatformConnectionResponse])
async def get_connected_platforms(
    current_user: User = Depends(get_current_user)
):
    """Get user's connected platforms"""
    try:
        platform_manager = PlatformManager()
        await platform_manager.initialize()
        
        connections = await platform_manager.get_user_platform_connections(current_user.id)
        
        return [
            PlatformConnectionResponse(
                id=conn.id,
                user_id=conn.user_id,
                platform_id=conn.platform_id,
                platform_name=conn.platform_name,
                display_name=conn.display_name,
                status=conn.status.value,
                connected_at=conn.connected_at,
                last_sync=conn.last_sync,
                credentials_status=conn.credentials_status.value,
                error_message=conn.error_message,
                metadata=conn.meta_data
            )
            for conn in connections
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get connected platforms: {str(e)}"
        )

@router.get("/metrics", response_model=List[PlatformMetricsResponse])
async def get_platform_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get metrics for user's connected platforms"""
    try:
        platform_manager = PlatformManager()
        await platform_manager.initialize()
        
        metrics = await platform_manager.get_user_platform_metrics(current_user.id)
        
        return [
            PlatformMetricsResponse(
                platform_id=metric.platform_id,
                platform_name=metric.platform_name,
                posts_count=metric.posts_count,
                followers_count=metric.followers_count,
                engagement_rate=metric.engagement_rate,
                last_activity=metric.last_activity,
                health_score=metric.health_score,
                error_count=metric.error_count,
                success_rate=metric.success_rate
            )
            for metric in metrics
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get platform metrics: {str(e)}"
        )

@router.post("/connect")
async def connect_platform(
    request: ConnectPlatformRequest,
    current_user: User = Depends(get_current_user)
):
    """Connect a platform"""
    try:
        platform_manager = PlatformManager()
        await platform_manager.initialize()
        
        connection = await platform_manager.connect_platform(
            user_id=current_user.id,
            platform_id=request.platform_id,
            credentials=request.credentials
        )
        
        # Broadcast platform connection via WebSocket
        try:
            from core.realtime.websocket_router import broadcast_notification
            await broadcast_notification(current_user.id, {
                "id": f"platform_{request.platform_id}_{current_user.id}",
                "type": "platform_update",
                "title": "Platform Connected",
                "message": "Platform connected successfully",
                "metadata": {
                    "platform_id": request.platform_id,
                    "connection_id": connection.id
                }
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast platform connection: {e}")
        
        return {
            "success": True,
            "connection_id": connection.id,
            "message": "Platform connected successfully"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect platform: {str(e)}"
        )

@router.post("/disconnect")
async def disconnect_platform(
    request: DisconnectPlatformRequest,
    current_user: User = Depends(get_current_user)
):
    """Disconnect a platform"""
    try:
        platform_manager = PlatformManager()
        await platform_manager.initialize()
        
        success = await platform_manager.disconnect_platform(
            user_id=current_user.id,
            platform_id=request.platform_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform connection not found"
            )
        
        # Broadcast platform disconnection via WebSocket
        try:
            from core.realtime.websocket_router import broadcast_notification
            await broadcast_notification(current_user.id, {
                "id": f"platform_{request.platform_id}_{current_user.id}",
                "type": "platform_update",
                "title": "Platform Disconnected",
                "message": "Platform disconnected successfully",
                "metadata": {
                    "platform_id": request.platform_id
                }
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast platform disconnection: {e}")
        
        return {
            "success": True,
            "message": "Platform disconnected successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect platform: {str(e)}"
        )

@router.post("/test-connection")
async def test_platform_connection(
    platform_id: int,
    current_user: User = Depends(get_current_user)
):
    """Test platform connection"""
    try:
        platform_manager = PlatformManager()
        await platform_manager.initialize()
        
        result = await platform_manager.test_platform_connection(
            user_id=current_user.id,
            platform_id=platform_id
        )
        
        return {
            "success": result["success"],
            "message": result["message"],
            "details": result.get("details", {})
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test platform connection: {str(e)}"
        )

@router.post("/sync")
async def sync_platform_data(
    platform_id: int,
    current_user: User = Depends(get_current_user)
):
    """Sync data from a platform"""
    try:
        platform_manager = PlatformManager()
        await platform_manager.initialize()
        
        result = await platform_manager.sync_platform_data(
            user_id=current_user.id,
            platform_id=platform_id
        )
        
        return {
            "success": result["success"],
            "message": result["message"],
            "synced_items": result.get("synced_items", 0)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync platform data: {str(e)}"
        )

@router.get("/health")
async def get_platform_health(
    current_user: User = Depends(get_current_user)
):
    """Get health status of all connected platforms"""
    try:
        platform_manager = PlatformManager()
        await platform_manager.initialize()
        
        health_status = await platform_manager.get_platform_health_status(current_user.id)
        
        return {
            "success": True,
            "health_status": health_status
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get platform health: {str(e)}"
        )

@router.post("/generate-mock-data")
async def generate_mock_platform_data(
    current_user: User = Depends(get_current_user)
):
    """Generate mock platform data for demonstration"""
    try:
        platform_manager = PlatformManager()
        await platform_manager.initialize()
        
        await platform_manager.generate_mock_user_data(current_user.id)
        
        return {
            "success": True,
            "message": "Mock platform data generated successfully",
            "user_id": current_user.id
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate mock platform data: {str(e)}"
        )
