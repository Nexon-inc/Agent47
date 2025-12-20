from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import RedirectResponse
from typing import Dict, Any, List, Optional
import logging
import uuid

from .oauth_service import get_oauth_service
from .platform_configs import get_platform_config_manager
from .audit_logger import get_audit_logger
from ..authentication.auth_manager import get_auth
from ..user_management.user_manager import get_user_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/platforms", tags=["platforms"])

async def get_current_user_id(request: Request) -> int:
    """Extract user ID from JWT token"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        token = auth_header.split(" ")[1]
        auth_manager = await get_auth()
        payload = auth_manager.verify_token(token)
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        return user_id
        
    except Exception as e:
        logger.error(f"Failed to extract user ID from token: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")

@router.get("/")
async def get_platforms():
    """Get list of all available platforms for connection"""
    try:
        config_manager = await get_platform_config_manager()
        configs = config_manager.get_all_configs()
        
        platforms = []
        for name, config in configs.items():
            platforms.append({
                "name": config.name,
                "display_name": config.display_name,
                "platform_type": config.platform_type.value,
                "description": f"Connect your {config.display_name} account",
                "scopes": config.scopes,
                "supported_features": config.supported_features,
                "supports_workspaces": config.supports_workspaces,
                "icon_url": config.icon_url,
                "color": config.color,
                "is_available": True
            })
        
        return platforms
    except Exception as e:
        logger.error(f"Failed to get platforms: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve platforms")

@router.get("/available")
async def get_available_platforms():
    """Get list of all available platforms for connection"""
    try:
        config_manager = await get_platform_config_manager()
        configs = config_manager.get_all_configs()
        
        platforms = []
        for name, config in configs.items():
            platforms.append({
                "name": config.name,
                "display_name": config.display_name,
                "platform_type": config.platform_type.value,
                "description": f"Connect your {config.display_name} account",
                "scopes": config.scopes,
                "supported_features": config.supported_features,
                "supports_workspaces": config.supports_workspaces,
                "max_users_per_app": config.max_users_per_app
            })
        
        return {
            "success": True,
            "platforms": platforms,
            "total": len(platforms)
        }
        
    except Exception as e:
        logger.error(f"Failed to get available platforms: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available platforms")

@router.get("/connect/{platform_name}")
async def initiate_platform_connection(
    platform_name: str,
    user_id: int = Depends(get_current_user_id),
    request: Request = None
):
    """Initiate OAuth connection to a platform"""
    try:
        oauth_service = await get_oauth_service()
        config_manager = await get_platform_config_manager()
        
        # Validate platform exists
        try:
            config = config_manager.get_config(platform_name)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Platform '{platform_name}' not found")
        
        # Generate authorization URL
        auth_result = oauth_service.get_authorization_url(user_id, platform_name)
        
        if not auth_result["success"]:
            raise HTTPException(status_code=400, detail=auth_result["error"])
        
        # Log connection attempt
        audit_logger = await get_audit_logger()
        from .audit_logger import AuditAction
        await audit_logger.log_action(
            user_id=user_id,
            platform_name=platform_name,
            action=AuditAction.PLATFORM_CONNECTED,
            description=f"User initiated connection to {platform_name}",
            success=True,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        return {
            "success": True,
            "auth_url": auth_result["auth_url"],
            "platform": platform_name,
            "scopes": auth_result["scopes"],
            "state": auth_result["state"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate platform connection: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate platform connection")

@router.get("/callback/{platform_name}")
async def handle_oauth_callback(
    platform_name: str,
    code: str = Query(..., description="Authorization code from platform"),
    state: str = Query(..., description="State parameter for security"),
    error: Optional[str] = Query(None, description="Error from platform"),
    error_description: Optional[str] = Query(None, description="Error description from platform"),
    request: Request = None
):
    """Handle OAuth callback from platform"""
    try:
        oauth_service = await get_oauth_service()
        
        # Handle OAuth errors
        if error:
            logger.warning(f"OAuth error from {platform_name}: {error} - {error_description}")
            return RedirectResponse(
                url=f"/dashboard?error=oauth_error&platform={platform_name}&error_code={error}",
                status_code=302
            )
        
        # Validate state parameter
        state_data = oauth_service.validate_state(state)
        if not state_data:
            logger.error(f"Invalid state parameter for {platform_name}")
            return RedirectResponse(
                url=f"/dashboard?error=invalid_state&platform={platform_name}",
                status_code=302
            )
        
        user_id = state_data["user_id"]
        
        # Handle platform-specific parameters
        additional_params = {}
        if platform_name == "shopify":
            shop = request.query_params.get("shop")
            if shop:
                additional_params["shop"] = shop
        
        # Exchange code for tokens
        token_result = await oauth_service.exchange_code_for_tokens(
            platform_name, code, state, additional_params
        )
        
        if not token_result["success"]:
            logger.error(f"Token exchange failed for {platform_name}: {token_result['error']}")
            return RedirectResponse(
                url=f"/dashboard?error=token_exchange_failed&platform={platform_name}&error_message={token_result['error']}",
                status_code=302
            )
        
        # Log successful connection
        audit_logger = await get_audit_logger()
        await audit_logger.log_platform_connected(
            user_id=user_id,
            platform_name=platform_name,
            scopes=token_result["scopes"],
            request_id=str(uuid.uuid4()),
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        # Broadcast platform connection via WebSocket
        try:
            from core.realtime.websocket_router import broadcast_notification
            await broadcast_notification(user_id, {
                "id": f"platform_{platform_name}_{user_id}",
                "type": "platform_update",
                "title": "Platform Connected",
                "message": f"Successfully connected to {platform_name}",
                "metadata": {
                    "platform_name": platform_name,
                    "workspace": token_result.get('workspace_name', '')
                }
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast platform connection: {e}")
        
        # Redirect to success page
        return RedirectResponse(
            url=f"/dashboard?success=platform_connected&platform={platform_name}&workspace={token_result.get('workspace_name', '')}",
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"Failed to handle OAuth callback for {platform_name}: {e}")
        return RedirectResponse(
            url=f"/dashboard?error=callback_failed&platform={platform_name}",
            status_code=302
        )

@router.get("/connected")
async def get_connected_platforms(user_id: int = Depends(get_current_user_id)):
    """Get user's connected platforms"""
    try:
        oauth_service = await get_oauth_service()
        platforms = await oauth_service.get_user_platforms(user_id)
        
        return {
            "success": True,
            "platforms": platforms,
            "total": len(platforms)
        }
        
    except Exception as e:
        logger.error(f"Failed to get connected platforms: {e}")
        raise HTTPException(status_code=500, detail="Failed to get connected platforms")

@router.post("/disconnect/{platform_name}")
async def disconnect_platform(
    platform_name: str,
    user_id: int = Depends(get_current_user_id),
    request: Request = None
):
    """Disconnect user from a platform"""
    try:
        oauth_service = await get_oauth_service()
        
        # Revoke tokens
        revoke_result = await oauth_service.revoke_user_tokens(user_id, platform_name)
        
        if not revoke_result["success"]:
            raise HTTPException(status_code=400, detail=revoke_result["error"])
        
        # Log disconnection
        audit_logger = await get_audit_logger()
        await audit_logger.log_platform_disconnected(
            user_id=user_id,
            platform_name=platform_name,
            request_id=str(uuid.uuid4()),
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        # Broadcast platform disconnection via WebSocket
        try:
            from core.realtime.websocket_router import broadcast_notification
            await broadcast_notification(user_id, {
                "id": f"platform_{platform_name}_{user_id}",
                "type": "platform_update",
                "title": "Platform Disconnected",
                "message": f"Successfully disconnected from {platform_name}",
                "metadata": {
                    "platform_name": platform_name
                }
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast platform disconnection: {e}")
        
        return {
            "success": True,
            "message": f"Successfully disconnected from {platform_name}",
            "platform": platform_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect platform: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect platform")

@router.post("/refresh/{platform_name}")
async def refresh_platform_tokens(
    platform_name: str,
    user_id: int = Depends(get_current_user_id),
    request: Request = None
):
    """Refresh platform tokens"""
    try:
        oauth_service = await get_oauth_service()
        
        # Refresh tokens
        refresh_result = await oauth_service.refresh_user_tokens(user_id, platform_name)
        
        if not refresh_result["success"]:
            raise HTTPException(status_code=400, detail=refresh_result["error"])
        
        # Log refresh
        audit_logger = await get_audit_logger()
        await audit_logger.log_action(
            user_id=user_id,
            platform_name=platform_name,
            action="token_refreshed",
            description=f"Refreshed tokens for {platform_name}",
            success=True,
            request_id=str(uuid.uuid4()),
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        return {
            "success": True,
            "message": f"Successfully refreshed tokens for {platform_name}",
            "platform": platform_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh platform tokens: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh platform tokens")

@router.get("/validate/{platform_name}")
async def validate_platform_access(
    platform_name: str,
    user_id: int = Depends(get_current_user_id),
    scopes: Optional[List[str]] = Query(None, description="Required scopes to validate")
):
    """Validate user's access to a platform"""
    try:
        oauth_service = await get_oauth_service()
        
        # Validate access
        has_access = await oauth_service.validate_platform_access(
            user_id, platform_name, scopes
        )
        
        if not has_access:
            raise HTTPException(
                status_code=403, 
                detail=f"User does not have valid access to {platform_name}"
            )
        
        return {
            "success": True,
            "has_access": True,
            "platform": platform_name,
            "scopes": scopes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate platform access: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate platform access")

@router.get("/health")
async def health_check():
    """Check platform service health"""
    try:
        oauth_service = await get_oauth_service()
        config_manager = await get_platform_config_manager()
        audit_logger = await get_audit_logger()
        
        oauth_health = await oauth_service.health_check()
        audit_health = await audit_logger.health_check()
        
        return {
            "success": True,
            "oauth_service": oauth_health,
            "config_manager": True,
            "audit_logger": audit_health,
            "overall_health": oauth_health and audit_health
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "overall_health": False
        }

@router.get("/metrics")
async def get_platform_metrics(request: Request):
    """Get platform usage metrics for the current user"""
    try:
        user_id = await get_current_user_id(request)
        
        # For now, return mock metrics
        # In a real implementation, this would query the database for actual usage data
        return {
            "total_platforms": 0,
            "connected_platforms": 0,
            "total_posts": 0,
            "total_engagement": 0,
            "platforms": []
        }
        
    except Exception as e:
        logger.error(f"Failed to get platform metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve platform metrics")
