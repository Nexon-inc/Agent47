from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import RedirectResponse
from typing import Dict, Any, List, Optional
import logging
import uuid

from .secure_integration_service import get_secure_integration_service
from .integration_configs import get_integration_config_manager
from .integration_credentials_manager import get_integration_credentials_manager
from .integration_audit_logger import get_integration_audit_logger, IntegrationAuditAction, IntegrationAuditSeverity
from ..authentication.auth_manager import get_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

async def get_current_user_id(request: Request) -> int:
    """Extract user ID from JWT token"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        token = auth_header.split(" ")[1]
        auth_manager = await get_auth_manager()
        payload = auth_manager.verify_token(token)
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        return user_id
        
    except Exception as e:
        logger.error(f"Failed to extract user ID from token: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")

@router.get("/")
async def get_integrations(
    integration_type: Optional[str] = Query(None, description="Filter by integration type")
):
    """Get list of all available integrations for connection"""
    try:
        config_manager = await get_integration_config_manager()
        configs = config_manager.get_all_configs()
        
        integrations = []
        for name, config in configs.items():
            if integration_type and config.integration_type.value != integration_type:
                continue
                
            integrations.append({
                "name": config.name,
                "display_name": config.display_name,
                "integration_type": config.integration_type.value,
                "description": config.description,
                "scopes": config.scopes,
                "supported_features": config.supported_features,
                "icon_url": config.icon_url,
                "color": config.color,
                "is_available": True
            })
        
        return integrations
    except Exception as e:
        logger.error(f"Failed to get integrations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve integrations")

@router.get("/available")
async def get_available_integrations(
    integration_type: Optional[str] = Query(None, description="Filter by integration type")
):
    """Get list of all available integrations for connection"""
    try:
        config_manager = await get_integration_config_manager()
        configs = config_manager.get_all_configs()
        
        integrations = []
        for name, config in configs.items():
            if integration_type and config.integration_type.value != integration_type:
                continue
                
            integrations.append({
                "name": config.name,
                "display_name": config.display_name,
                "integration_type": config.integration_type.value,
                "description": config.description,
                "provider": config.provider,
                "api_version": config.api_version,
                "pricing_tier": config.pricing_tier,
                "rate_limits": config.rate_limits,
                "supported_features": config.supported_features,
                "authentication_methods": config.authentication_methods,
                "scopes": config.scopes,
                "supports_oauth": config.supports_oauth,
                "supports_api_key": config.supports_api_key,
                "supports_bearer_token": config.supports_bearer_token
            })
        
        return {
            "success": True,
            "integrations": integrations,
            "total": len(integrations)
        }
        
    except Exception as e:
        logger.error(f"Failed to get available integrations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available integrations")

@router.post("/connect/{integration_name}")
async def connect_integration(
    integration_name: str,
    credentials: Dict[str, Any],
    user_id: int = Depends(get_current_user_id),
    request: Request = None
):
    """Connect to an integration by providing credentials"""
    try:
        config_manager = await get_integration_config_manager()
        credentials_manager = await get_integration_credentials_manager()
        audit_logger = await get_integration_audit_logger()
        
        # Validate integration exists
        try:
            config = config_manager.get_config(integration_name)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Integration '{integration_name}' not found")
        
        # Validate required credentials based on integration type
        required_fields = []
        if config.supports_api_key and not config.supports_oauth:
            required_fields = ["api_key"]
        elif config.supports_oauth:
            required_fields = ["access_token"]
        elif config.supports_bearer_token:
            required_fields = ["bearer_token"]
        
        missing_fields = [field for field in required_fields if not credentials.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required credentials: {', '.join(missing_fields)}"
            )
        
        # Store credentials
        store_result = await credentials_manager.store_credentials(
            user_id=user_id,
            integration_name=integration_name,
            credentials_data=credentials,
            scopes=credentials.get("scopes", config.scopes)
        )
        
        if not store_result["success"]:
            raise HTTPException(status_code=400, detail=store_result["error"])
        
        # Log connection
        await audit_logger.log_integration_connected(
            user_id=user_id,
            integration_name=integration_name,
            scopes=credentials.get("scopes", config.scopes),
            request_id=str(uuid.uuid4()),
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        # Broadcast integration connection via WebSocket
        try:
            from backend.core.realtime.websocket_router import broadcast_notification
            await broadcast_notification(user_id, {
                "id": f"integration_{integration_name}_{user_id}",
                "type": "platform_update",
                "title": "Integration Connected",
                "message": f"Successfully connected to {integration_name}",
                "metadata": {
                    "integration_name": integration_name,
                    "credentials_id": store_result.get("credentials_id")
                }
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast integration connection: {e}")
        
        return {
            "success": True,
            "message": f"Successfully connected to {integration_name}",
            "integration": integration_name,
            "expires_at": store_result.get("expires_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to connect integration: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect integration")

@router.get("/oauth/{integration_name}")
async def initiate_oauth_connection(
    integration_name: str,
    user_id: int = Depends(get_current_user_id),
    request: Request = None
):
    """Initiate OAuth connection to an integration"""
    try:
        config_manager = await get_integration_config_manager()
        
        # Validate integration exists and supports OAuth
        try:
            config = config_manager.get_config(integration_name)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Integration '{integration_name}' not found")
        
        if not config.supports_oauth:
            raise HTTPException(status_code=400, detail=f"Integration '{integration_name}' does not support OAuth")
        
        # Generate OAuth URL
        state = str(uuid.uuid4())
        oauth_url = config_manager.get_oauth_url(integration_name, state)
        
        # Log OAuth initiation
        audit_logger = await get_integration_audit_logger()
        await audit_logger.log_action(
            user_id=user_id,
            integration_name=integration_name,
            action=IntegrationAuditAction.INTEGRATION_CONNECTED,
            description=f"User initiated OAuth connection to {integration_name}",
            success=True,
            request_id=state,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        return {
            "success": True,
            "oauth_url": oauth_url,
            "integration": integration_name,
            "scopes": config.scopes,
            "state": state
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate OAuth connection: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth connection")

@router.get("/callback/{integration_name}")
async def handle_oauth_callback(
    integration_name: str,
    code: str = Query(..., description="Authorization code from integration"),
    state: str = Query(..., description="State parameter for security"),
    error: Optional[str] = Query(None, description="Error from integration"),
    error_description: Optional[str] = Query(None, description="Error description from integration"),
    user_id: int = Depends(get_current_user_id),
    request: Request = None
):
    """Handle OAuth callback from integration"""
    try:
        config_manager = await get_integration_config_manager()
        credentials_manager = await get_integration_credentials_manager()
        audit_logger = await get_integration_audit_logger()
        
        # Handle OAuth errors
        if error:
            logger.warning(f"OAuth error from {integration_name}: {error} - {error_description}")
            await audit_logger.log_security_event(
                user_id=user_id,
                integration_name=integration_name,
                description=f"OAuth error: {error} - {error_description}",
                severity=IntegrationAuditSeverity.HIGH,
                request_id=state,
                ip_address=request.client.host if request else None,
                user_agent=request.headers.get("user-agent") if request else None
            )
            return RedirectResponse(
                url=f"/dashboard?error=oauth_error&integration={integration_name}&error_code={error}",
                status_code=302
            )
        
        # Get integration config
        config = config_manager.get_config(integration_name)
        
        # Exchange code for tokens (simplified - would need actual OAuth implementation)
        # This is a placeholder - real implementation would make HTTP request to token endpoint
        credentials_data = {
            "access_token": f"oauth_token_{code}",
            "expires_in": 3600,
            "scopes": config.scopes
        }
        
        # Store credentials
        store_result = await credentials_manager.store_credentials(
            user_id=user_id,
            integration_name=integration_name,
            credentials_data=credentials_data,
            scopes=config.scopes
        )
        
        if not store_result["success"]:
            await audit_logger.log_security_event(
                user_id=user_id,
                integration_name=integration_name,
                description=f"Failed to store OAuth credentials: {store_result['error']}",
                severity=IntegrationAuditSeverity.HIGH,
                request_id=state,
                ip_address=request.client.host if request else None,
                user_agent=request.headers.get("user-agent") if request else None
            )
            return RedirectResponse(
                url=f"/dashboard?error=token_exchange_failed&integration={integration_name}",
                status_code=302
            )
        
        # Broadcast integration connection via WebSocket
        try:
            from backend.core.realtime.websocket_router import broadcast_notification
            await broadcast_notification(user_id, {
                "id": f"integration_{integration_name}_{user_id}",
                "type": "platform_update",
                "title": "Integration Connected",
                "message": f"Successfully connected to {integration_name}",
                "metadata": {
                    "integration_name": integration_name,
                    "credentials_id": store_result.get("credentials_id")
                }
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast integration connection: {e}")
        
        # Log successful connection
        await audit_logger.log_integration_connected(
            user_id=user_id,
            integration_name=integration_name,
            scopes=config.scopes,
            request_id=state,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        # Broadcast integration connection via WebSocket
        try:
            from backend.core.realtime.websocket_router import broadcast_notification
            await broadcast_notification(user_id, {
                "id": f"integration_{integration_name}_{user_id}",
                "type": "platform_update",
                "title": "Integration Connected",
                "message": f"Successfully connected to {integration_name}",
                "metadata": {
                    "integration_name": integration_name,
                    "credentials_id": store_result.get("credentials_id")
                }
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast integration connection: {e}")
        
        # Redirect to success page
        return RedirectResponse(
            url=f"/dashboard?success=integration_connected&integration={integration_name}",
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"Failed to handle OAuth callback for {integration_name}: {e}")
        return RedirectResponse(
            url=f"/dashboard?error=callback_failed&integration={integration_name}",
            status_code=302
        )

@router.get("/connected")
async def get_connected_integrations(user_id: int = Depends(get_current_user_id)):
    """Get user's connected integrations"""
    try:
        credentials_manager = await get_integration_credentials_manager()
        integrations = await credentials_manager.get_user_integrations(user_id)
        
        return {
            "success": True,
            "integrations": integrations,
            "total": len(integrations)
        }
        
    except Exception as e:
        logger.error(f"Failed to get connected integrations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get connected integrations")

@router.post("/disconnect/{integration_name}")
async def disconnect_integration(
    integration_name: str,
    user_id: int = Depends(get_current_user_id),
    request: Request = None
):
    """Disconnect user from an integration"""
    try:
        credentials_manager = await get_integration_credentials_manager()
        audit_logger = await get_integration_audit_logger()
        
        # Revoke credentials
        revoke_result = await credentials_manager.revoke_credentials(user_id, integration_name)
        
        if not revoke_result["success"]:
            raise HTTPException(status_code=400, detail=revoke_result["error"])
        
        # Log disconnection
        await audit_logger.log_integration_disconnected(
            user_id=user_id,
            integration_name=integration_name,
            request_id=str(uuid.uuid4()),
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        # Broadcast integration disconnection via WebSocket
        try:
            from backend.core.realtime.websocket_router import broadcast_notification
            await broadcast_notification(user_id, {
                "id": f"integration_{integration_name}_{user_id}",
                "type": "platform_update",
                "title": "Integration Disconnected",
                "message": f"Successfully disconnected from {integration_name}",
                "metadata": {
                    "integration_name": integration_name
                }
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast integration disconnection: {e}")
        
        return {
            "success": True,
            "message": f"Successfully disconnected from {integration_name}",
            "integration": integration_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect integration: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect integration")

@router.post("/refresh/{integration_name}")
async def refresh_integration_credentials(
    integration_name: str,
    user_id: int = Depends(get_current_user_id),
    request: Request = None
):
    """Refresh integration credentials"""
    try:
        credentials_manager = await get_integration_credentials_manager()
        audit_logger = await get_integration_audit_logger()
        
        # Refresh credentials
        refresh_result = await credentials_manager.refresh_credentials(user_id, integration_name)
        
        if not refresh_result["success"]:
            raise HTTPException(status_code=400, detail=refresh_result["error"])
        
        # Log refresh
        await audit_logger.log_action(
            user_id=user_id,
            integration_name=integration_name,
            action=IntegrationAuditAction.CREDENTIALS_REFRESHED,
            description=f"Refreshed credentials for {integration_name}",
            success=True,
            request_id=str(uuid.uuid4()),
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        return {
            "success": True,
            "message": f"Successfully refreshed credentials for {integration_name}",
            "integration": integration_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh integration credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh integration credentials")

@router.get("/validate/{integration_name}")
async def validate_integration_access(
    integration_name: str,
    user_id: int = Depends(get_current_user_id),
    scopes: Optional[List[str]] = Query(None, description="Required scopes to validate")
):
    """Validate user's access to an integration"""
    try:
        credentials_manager = await get_integration_credentials_manager()
        
        # Validate access
        has_access = await credentials_manager.validate_credential_access(
            user_id, integration_name, scopes
        )
        
        if not has_access:
            raise HTTPException(
                status_code=403, 
                detail=f"User does not have valid access to {integration_name}"
            )
        
        return {
            "success": True,
            "has_access": True,
            "integration": integration_name,
            "scopes": scopes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate integration access: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate integration access")

@router.get("/audit-logs")
async def get_integration_audit_logs(
    user_id: int = Depends(get_current_user_id),
    integration_name: Optional[str] = Query(None, description="Filter by integration"),
    action: Optional[str] = Query(None, description="Filter by action"),
    limit: int = Query(100, description="Number of logs to return"),
    offset: int = Query(0, description="Number of logs to skip")
):
    """Get user's integration audit logs"""
    try:
        audit_logger = await get_integration_audit_logger()
        
        # Convert action string to enum if provided
        action_enum = None
        if action:
            try:
                action_enum = IntegrationAuditAction(action)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
        
        logs = await audit_logger.get_user_audit_logs(
            user_id=user_id,
            integration_name=integration_name,
            action=action_enum,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "logs": logs,
            "total": len(logs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get integration audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get integration audit logs")

@router.get("/health")
async def health_check():
    """Check integration service health"""
    try:
        config_manager = await get_integration_config_manager()
        credentials_manager = await get_integration_credentials_manager()
        audit_logger = await get_integration_audit_logger()
        integration_service = await get_secure_integration_service()
        
        config_health = config_manager is not None
        credentials_health = credentials_manager is not None
        audit_health = await audit_logger.health_check()
        service_health = await integration_service.health_check()
        
        return {
            "success": True,
            "config_manager": config_health,
            "credentials_manager": credentials_health,
            "audit_logger": audit_health,
            "integration_service": service_health,
            "overall_health": config_health and credentials_health and audit_health and service_health
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "overall_health": False
        }

@router.get("/usage")
async def get_integration_usage(request: Request):
    """Get integration usage statistics for the current user"""
    try:
        user_id = await get_current_user_id(request)
        
        from ..database.connection import get_database
        from sqlalchemy import select, func, and_
        from datetime import datetime, timedelta
        from .models import IntegrationCredentials, IntegrationUsage, Integration
        
        db = get_database()
        
        # Get all connected integrations for this user
        async with db.get_session() as session:
            credentials_query = select(IntegrationCredentials).where(
                IntegrationCredentials.user_id == user_id
            )
            credentials_result = await session.execute(credentials_query)
            credentials_list = credentials_result.scalars().all()
            
            # Get usage data for the last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            usage_query = select(
                IntegrationUsage.integration_id,
                func.sum(IntegrationUsage.api_calls_count).label("total_calls"),
                func.sum(IntegrationUsage.data_processed_mb).label("total_data"),
                func.sum(IntegrationUsage.cost_usd).label("total_cost")
            ).where(
                and_(
                    IntegrationUsage.user_id == user_id,
                    IntegrationUsage.created_at >= thirty_days_ago
                )
            ).group_by(IntegrationUsage.integration_id)
            
            usage_result = await session.execute(usage_query)
            usage_data = {row.integration_id: row for row in usage_result.all()}
            
            # Build integration usage list
            integrations_usage = []
            total_api_calls = 0
            active_count = 0
            
            for cred in credentials_list:
                # Get integration details
                integration_query = select(Integration).where(Integration.id == cred.integration_id)
                integration_result = await session.execute(integration_query)
                integration = integration_result.scalar_one_or_none()
                
                if not integration:
                    continue
                
                # Get usage for this integration
                usage = usage_data.get(cred.integration_id)
                api_calls = usage.total_calls if usage else 0
                total_api_calls += api_calls
                
                # Check if active (has valid credentials and was used recently)
                is_active = (
                    cred.status.value == "valid" and 
                    (cred.last_used is None or cred.last_used >= thirty_days_ago)
                )
                if is_active:
                    active_count += 1
                
                integrations_usage.append({
                    "integration_id": integration.id,
                    "integration_name": integration.name,
                    "display_name": integration.display_name,
                    "status": cred.status.value,
                    "api_calls": api_calls,
                    "data_processed_mb": usage.total_data if usage else 0.0,
                    "cost_usd": usage.total_cost if usage else 0.0,
                    "last_used": cred.last_used.isoformat() if cred.last_used else None,
                    "connected_at": cred.created_at.isoformat() if cred.created_at else None
                })
        
        return {
            "total_integrations": len(credentials_list),
            "active_integrations": active_count,
            "total_api_calls": total_api_calls,
            "total_automations": 0,  # Would need to query task/automation tables
            "integrations": integrations_usage
        }
        
    except Exception as e:
        logger.error(f"Failed to get integration usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve integration usage")

@router.get("/stats")
async def get_integration_stats(request: Request):
    """Get integration statistics for the current user"""
    try:
        user_id = await get_current_user_id(request)
        
        from ..database.connection import get_database
        from sqlalchemy import select, func, and_
        from datetime import datetime, timedelta
        from .models import IntegrationCredentials
        from ..database.models import IntegrationAuditLog, IntegrationAuditAction
        
        db = get_database()
        
        async with db.get_session() as session:
            # Get all connected integrations
            credentials_query = select(IntegrationCredentials).where(
                IntegrationCredentials.user_id == user_id
            )
            credentials_result = await session.execute(credentials_query)
            credentials_list = credentials_result.scalars().all()
            
            connected_count = len(credentials_list)
            
            # Get connection attempts from audit logs
            audit_query = select(
                func.count(IntegrationAuditLog.id).label("total_attempts"),
                func.sum(func.cast(IntegrationAuditLog.success == "true", int)).label("successful"),
                func.sum(func.cast(IntegrationAuditLog.success == "false", int)).label("failed")
            ).where(
                and_(
                    IntegrationAuditLog.user_id == user_id,
                    IntegrationAuditLog.action == IntegrationAuditAction.INTEGRATION_CONNECTED
                )
            )
            
            audit_result = await session.execute(audit_query)
            audit_stats = audit_result.first()
            
            total_attempts = audit_stats.total_attempts if audit_stats else 0
            successful_connections = audit_stats.successful if audit_stats else 0
            failed_connections = audit_stats.failed if audit_stats else 0
            
            # Calculate success rate
            success_rate = (successful_connections / total_attempts * 100) if total_attempts > 0 else 0
            
            # Get last used timestamp from credentials
            last_used = None
            if credentials_list:
                last_used_times = [c.last_used for c in credentials_list if c.last_used]
                if last_used_times:
                    last_used = max(last_used_times)
        
        return {
            "total_integrations": connected_count,  # Total connected
            "connected_integrations": connected_count,
            "failed_connections": failed_connections,
            "success_rate": round(success_rate, 2),
            "last_used": last_used.isoformat() if last_used else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get integration stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve integration stats")
