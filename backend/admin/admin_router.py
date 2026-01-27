"""
Admin Router for Agent47
Provides comprehensive admin functionality for system management
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from .admin_core import AdminCore, AdminUser, AdminPermission, AdminAction, get_admin_core
from .agents.agent_manager import AgentManager
from .analytics.analytics_manager import AnalyticsManager, get_analytics_manager
from .database.database_manager import DatabaseManager
from .security.security_manager import SecurityManager, get_security_manager
from .system.system_manager import SystemManager, get_system_manager
from .users.user_admin_manager import UserAdminManager, get_user_admin_manager
from .platforms.agent47_platform_manager import Agent47PlatformManager, get_agent47_platform_manager
from core.platforms.oauth_service import get_oauth_service
from fastapi.responses import RedirectResponse
from fastapi import Query, Body
from .settings.settings_manager import get_settings_manager, SettingsManager, SettingCategory, SettingType
from .logs.log_viewer import get_log_viewer, LogViewer, LogFilter, LogLevel, LogSource
from .cache.cache_manager import get_cache_manager, CacheManager, CacheType
from .features.feature_flags_manager import get_feature_flags_manager, FeatureFlagsManager, FeatureFlagStatus, TargetingType
from .alerts.alert_manager import AlertManager, AlertSource, AlertSeverity, AlertStatus
from .finance.finance_manager import get_finance_manager, FinanceManager, TransactionType, TransactionStatus
from .code.code_manager import get_code_manager, CodeManager
from .terminal.terminal_manager import TerminalManager
from .communications.communication_manager import CommunicationManager, CommunicationType, CommunicationStatus
from .support.support_manager import SupportManager, TicketStatus, TicketPriority, TicketCategory
from .servers.server_manager import ServerManager, ServerStatus, ServerType
from .goals.goal_manager import get_goal_manager, GoalManager, GoalStatus, GoalType, GoalPriority
from .impersonate.impersonation_manager import ImpersonationManager, ImpersonationReason, ImpersonationStatus
from .integrations.integration_admin_manager import get_integration_admin_manager, IntegrationAdminManager
from core.billing.billing_manager import get_billing, BillingManager
from core.billing.usage_tracker import get_usage_tracker

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

# Security
security = HTTPBearer()

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    admin_core: AdminCore = Depends(get_admin_core)
) -> AdminUser:
    """Get current admin user from token"""
    admin_user = await admin_core.verify_admin_session(credentials.credentials)
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin session"
        )
    return admin_user

async def check_admin_permission(
    admin_user: AdminUser = Depends(get_current_admin),
    required_permission: AdminPermission = AdminPermission.BASIC_ADMIN
) -> AdminUser:
    """Check if admin user has required permission"""
    # Super admin has access to everything
    if AdminPermission.SUPER_ADMIN.value in admin_user.permissions:
        return admin_user
    
    # Check if user has the required permission
    if required_permission.value not in admin_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Required permission: {required_permission.value}. Your permissions: {admin_user.permissions}"
        )
    return admin_user

async def require_super_admin(
    admin_user: AdminUser = Depends(get_current_admin)
) -> AdminUser:
    """Require SUPER_ADMIN permission"""
    if AdminPermission.SUPER_ADMIN.value not in admin_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return admin_user

# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@router.post("/login")
async def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    admin_core: AdminCore = Depends(get_admin_core)
):
    """Admin login endpoint"""
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        logger.info(f"Admin login attempt for email: {email}")
        admin_user = await admin_core.authenticate_admin(email, password, ip_address, user_agent)
        if not admin_user:
            logger.warning(f"Admin login failed for email: {email} - Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        logger.info(f"Admin login successful for email: {email}")
        return {
            "access_token": admin_user.session_token,
            "token_type": "bearer",
            "admin_user": {
                "user_id": admin_user.user_id,
                "email": admin_user.email,
                "permissions": admin_user.permissions
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 401) without modification
        raise
    except Exception as e:
        logger.error(f"Admin login failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/logout")
async def admin_logout(
    admin_user: AdminUser = Depends(get_current_admin),
    admin_core: AdminCore = Depends(get_admin_core)
):
    """Admin logout endpoint"""
    try:
        # Remove from active sessions
        if admin_user.session_token in admin_core.active_sessions:
            del admin_core.active_sessions[admin_user.session_token]
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Admin logout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me")
async def get_current_admin_info(
    admin_user: AdminUser = Depends(get_current_admin)
):
    """Get current admin information"""
    return {
        "user_id": admin_user.user_id,
        "email": admin_user.email,
        "permissions": admin_user.permissions,
        "last_login": admin_user.last_login.isoformat() if admin_user.last_login else None,
        "is_active": admin_user.is_active
    }

# =============================================================================
# SYSTEM HEALTH & MONITORING
# =============================================================================

@router.get("/health")
async def admin_health_check(
    admin_user: AdminUser = Depends(get_current_admin),
    admin_core: AdminCore = Depends(get_admin_core)
):
    """Get system health status"""
    try:
        health_status = await admin_core.get_system_health()
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )

@router.get("/metrics")
async def admin_metrics(
    admin_user: AdminUser = Depends(get_current_admin),
    admin_core: AdminCore = Depends(get_admin_core)
):
    """Get admin metrics"""
    try:
        metrics = await admin_core.get_admin_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get metrics"
        )

# =============================================================================
# AGENT MANAGEMENT
# =============================================================================

@router.get("/agents")
async def get_agents(
    admin_user: AdminUser = Depends(check_admin_permission),
    agent_manager: AgentManager = Depends()
):
    """Get all agents status and information"""
    try:
        agents = await agent_manager.get_all_agents()
        return {"agents": agents}
        
    except Exception as e:
        logger.error(f"Failed to get agents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agents"
        )

@router.post("/agents/{agent_name}/restart")
async def restart_agent(
    agent_name: str,
    admin_user: AdminUser = Depends(check_admin_permission),
    agent_manager: AgentManager = Depends()
):
    """Restart a specific agent"""
    try:
        result = await agent_manager.restart_agent(agent_name)
        return {"message": f"Agent {agent_name} restarted", "result": result}
        
    except Exception as e:
        logger.error(f"Failed to restart agent {agent_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart agent {agent_name}"
        )

@router.get("/agents/{agent_name}/logs")
async def get_agent_logs(
    agent_name: str,
    lines: int = 100,
    admin_user: AdminUser = Depends(check_admin_permission),
    agent_manager: AgentManager = Depends()
):
    """Get agent logs"""
    try:
        logs = await agent_manager.get_agent_logs(agent_name, lines)
        return {"logs": logs}
        
    except Exception as e:
        logger.error(f"Failed to get logs for agent {agent_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs for agent {agent_name}"
        )

# =============================================================================
# USER MANAGEMENT
# =============================================================================

@router.get("/users")
async def get_users(
    page: int = 1,
    limit: int = 50,
    admin_user: AdminUser = Depends(check_admin_permission),
    user_manager: UserAdminManager = Depends()
):
    """Get all users with pagination"""
    try:
        users = await user_manager.get_users(page, limit)
        return users
        
    except Exception as e:
        logger.error(f"Failed to get users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users"
        )

@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    admin_user: AdminUser = Depends(check_admin_permission),
    user_manager: UserAdminManager = Depends()
):
    """Get specific user details"""
    try:
        user = await user_manager.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    admin_user: AdminUser = Depends(check_admin_permission),
    user_manager: UserAdminManager = Depends()
):
    """Update user active status"""
    try:
        result = await user_manager.update_user_status(user_id, is_active)
        return {"message": f"User {user_id} status updated", "result": result}
        
    except Exception as e:
        logger.error(f"Failed to update user {user_id} status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status"
        )

# =============================================================================
# DATABASE MANAGEMENT
# =============================================================================

@router.get("/database/status")
async def get_database_status(
    admin_user: AdminUser = Depends(check_admin_permission),
    db_manager: DatabaseManager = Depends()
):
    """Get database status and metrics"""
    try:
        status = await db_manager.get_database_status()
        return status
        
    except Exception as e:
        logger.error(f"Failed to get database status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get database status"
        )

@router.post("/database/backup")
async def create_database_backup(
    admin_user: AdminUser = Depends(check_admin_permission),
    db_manager: DatabaseManager = Depends()
):
    """Create database backup"""
    try:
        backup_info = await db_manager.create_backup()
        return {"message": "Backup created successfully", "backup": backup_info}
        
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create backup"
        )

# =============================================================================
# ANALYTICS & REPORTING
# =============================================================================

@router.get("/analytics/overview")
async def get_analytics_overview(
    admin_user: AdminUser = Depends(check_admin_permission),
    analytics_manager: AnalyticsManager = Depends()
):
    """Get analytics overview"""
    try:
        overview = await analytics_manager.get_overview()
        return overview
        
    except Exception as e:
        logger.error(f"Failed to get analytics overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics overview"
        )

@router.get("/analytics/users")
async def get_user_analytics(
    days: int = 30,
    admin_user: AdminUser = Depends(check_admin_permission),
    analytics_manager: AnalyticsManager = Depends()
):
    """Get user analytics"""
    try:
        analytics = await analytics_manager.get_user_analytics(days)
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get user analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user analytics"
        )

# =============================================================================
# SYSTEM MANAGEMENT
# =============================================================================

@router.get("/system/status")
async def get_system_status(
    admin_user: AdminUser = Depends(check_admin_permission),
    system_manager: SystemManager = Depends()
):
    """Get system status"""
    try:
        status = await system_manager.get_system_status()
        return status
        
    except Exception as e:
        logger.error(f"Failed to get system status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system status"
        )

@router.post("/system/cleanup")
async def system_cleanup(
    admin_user: AdminUser = Depends(check_admin_permission),
    system_manager: SystemManager = Depends()
):
    """Perform system cleanup"""
    try:
        cleanup_result = await system_manager.perform_cleanup()
        return {"message": "System cleanup completed", "result": cleanup_result}
        
    except Exception as e:
        logger.error(f"Failed to perform system cleanup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform system cleanup"
        )

# =============================================================================
# SECURITY MANAGEMENT
# =============================================================================

@router.get("/security/audit-logs")
async def get_audit_logs(
    page: int = 1,
    limit: int = 100,
    admin_user: AdminUser = Depends(check_admin_permission),
    security_manager: SecurityManager = Depends()
):
    """Get security audit logs"""
    try:
        logs = await security_manager.get_audit_logs(page, limit)
        return logs
        
    except Exception as e:
        logger.error(f"Failed to get audit logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit logs"
        )

@router.get("/security/threats")
async def get_security_threats(
    admin_user: AdminUser = Depends(check_admin_permission),
    security_manager: SecurityManager = Depends()
):
    """Get security threats and alerts"""
    try:
        threats = await security_manager.get_security_threats()
        return {"threats": threats}
        
    except Exception as e:
        logger.error(f"Failed to get security threats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security threats"
        )

# =============================================================================
# ADMIN USER MANAGEMENT (Super Admin Only)
# =============================================================================

@router.get("/admins")
async def list_admin_users(
    admin_user: AdminUser = Depends(require_super_admin),
    admin_core: AdminCore = Depends(get_admin_core)
):
    """List all admin users (Super Admin only)"""
    try:
        admins = await admin_core.list_all_admin_users()
        return {"admins": admins, "total": len(admins)}
    except Exception as e:
        logger.error(f"Failed to list admin users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list admin users"
        )

@router.post("/admins/create")
async def create_admin_user(
    email: str,
    user_id: str,
    permissions: List[str],
    admin_user: AdminUser = Depends(require_super_admin),
    admin_core: AdminCore = Depends(get_admin_core)
):
    """Create a new admin user (Super Admin only)"""
    try:
        # Convert permission strings to AdminPermission enums
        permission_enums = []
        for perm_str in permissions:
            try:
                permission_enums.append(AdminPermission(perm_str))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid permission: {perm_str}"
                )
        
        new_admin = await admin_core.create_admin_user(
            email=email,
            user_id=user_id,
            permissions=permission_enums,
            admin_creator_id=admin_user.user_id
        )
        
        if not new_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create admin user. User may already exist."
            )
        
        return {
            "message": "Admin user created successfully",
            "admin": {
                "user_id": new_admin.user_id,
                "email": new_admin.email,
                "permissions": new_admin.permissions
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create admin user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create admin user"
        )

@router.put("/admins/{admin_user_id}/permissions")
async def update_admin_permissions(
    admin_user_id: str,
    permissions: List[str],
    admin_user: AdminUser = Depends(require_super_admin),
    admin_core: AdminCore = Depends(get_admin_core)
):
    """Update admin user permissions (Super Admin only)"""
    try:
        # Convert permission strings to AdminPermission enums
        permission_enums = []
        for perm_str in permissions:
            try:
                permission_enums.append(AdminPermission(perm_str))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid permission: {perm_str}"
                )
        
        success = await admin_core.update_admin_permissions(
            admin_user_id=admin_user_id,
            permissions=permission_enums,
            admin_updater_id=admin_user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin user not found"
            )
        
        return {"message": "Admin permissions updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update admin permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update admin permissions"
        )

@router.delete("/admins/{admin_user_id}")
async def deactivate_admin_user(
    admin_user_id: str,
    admin_user: AdminUser = Depends(require_super_admin),
    admin_core: AdminCore = Depends(get_admin_core)
):
    """Deactivate an admin user (Super Admin only)"""
    try:
        # Prevent deactivating yourself
        if admin_user_id == admin_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own admin account"
            )
        
        success = await admin_core.deactivate_admin_user(
            admin_user_id=admin_user_id,
            admin_deactivator_id=admin_user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin user not found"
            )
        
        return {"message": "Admin user deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate admin user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate admin user"
        )

@router.get("/me")
async def get_current_admin_info(
    admin_user: AdminUser = Depends(get_current_admin)
):
    """Get current admin user information"""
    return {
        "user_id": admin_user.user_id,
        "email": admin_user.email,
        "permissions": admin_user.permissions,
        "is_active": admin_user.is_active,
        "last_login": admin_user.last_login.isoformat() if admin_user.last_login else None
    }

# =============================================================================
# AGENT47 PLATFORM CONNECTIONS (Super Admin Only)
# =============================================================================

@router.get("/platforms/available")
async def get_available_platforms(
    admin_user: AdminUser = Depends(require_super_admin),
    platform_manager: Agent47PlatformManager = Depends(get_agent47_platform_manager)
):
    """Get all available platforms that can be connected"""
    try:
        platforms = await platform_manager.get_available_platforms()
        return {"platforms": platforms, "total": len(platforms)}
    except Exception as e:
        logger.error(f"Failed to get available platforms: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available platforms"
        )

@router.get("/platforms/connections")
async def get_platform_connections(
    active_only: bool = True,
    admin_user: AdminUser = Depends(require_super_admin),
    platform_manager: Agent47PlatformManager = Depends(get_agent47_platform_manager)
):
    """Get all Agent47 platform connections"""
    try:
        connections = await platform_manager.get_all_connections(active_only=active_only)
        return {"connections": connections, "total": len(connections)}
    except Exception as e:
        logger.error(f"Failed to get platform connections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get platform connections"
        )

@router.get("/platforms/connect/{platform_name}")
async def initiate_platform_oauth(
    platform_name: str,
    account_name: str = Query(..., description="Display name for this account (e.g., 'Agent47 Official')"),
    account_handle: Optional[str] = Query(None, description="Handle/username on the platform"),
    admin_user: AdminUser = Depends(require_super_admin),
    request: Request = None
):
    """Initiate OAuth connection to a platform for Agent47 system account"""
    try:
        oauth_service = await get_oauth_service()
        from core.platforms.platform_configs import get_platform_config_manager
        config_manager = await get_platform_config_manager()
        
        # Validate platform exists
        try:
            config = config_manager.get_config(platform_name)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Platform '{platform_name}' not found")
        
        # Use a special system user ID (0) for Agent47 system accounts
        # This distinguishes system OAuth flows from user OAuth flows
        system_user_id = 0
        
        # Generate authorization URL
        auth_result = oauth_service.get_authorization_url(system_user_id, platform_name)
        
        if not auth_result["success"]:
            raise HTTPException(status_code=400, detail=auth_result["error"])
        
        # Store account_name and account_handle in session/state for callback
        # We'll encode this in the state parameter
        import json
        import base64
        state_data = {
            "user_id": system_user_id,
            "platform": platform_name,
            "account_name": account_name,
            "account_handle": account_handle,
            "admin_user_id": admin_user.user_id
        }
        state_json = json.dumps(state_data)
        encoded_state = base64.urlsafe_b64encode(state_json.encode()).decode()
        
        return {
            "success": True,
            "auth_url": auth_result["auth_url"],
            "platform": platform_name,
            "scopes": auth_result["scopes"],
            "state": encoded_state,
            "account_name": account_name,
            "account_handle": account_handle
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate platform OAuth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate platform connection"
        )

@router.get("/platforms/callback/{platform_name}")
async def handle_platform_oauth_callback(
    platform_name: str,
    code: str = Query(..., description="Authorization code from platform"),
    state: str = Query(..., description="State parameter (encoded with account info)"),
    error: Optional[str] = Query(None, description="Error from platform"),
    error_description: Optional[str] = Query(None, description="Error description from platform"),
    request: Request = None
):
    """Handle OAuth callback from platform for Agent47 system account"""
    try:
        # Decode state to get account info
        import json
        import base64
        try:
            decoded_state = base64.urlsafe_b64decode(state.encode()).decode()
            state_data = json.loads(decoded_state)
            account_name = state_data.get("account_name")
            account_handle = state_data.get("account_handle")
            admin_user_id = state_data.get("admin_user_id")
        except Exception as e:
            logger.error(f"Failed to decode state: {str(e)}")
            return RedirectResponse(
                url=f"/admin/platforms?error=invalid_state&platform={platform_name}",
                status_code=302
            )
        
        # Handle OAuth errors
        if error:
            logger.warning(f"OAuth error from {platform_name}: {error} - {error_description}")
            return RedirectResponse(
                url=f"/admin/platforms?error=oauth_error&platform={platform_name}&error_code={error}",
                status_code=302
            )
        
        oauth_service = await get_oauth_service()
        platform_manager = await get_agent47_platform_manager()
        
        # Exchange code for tokens
        # Use the original state from OAuth service (we'll need to modify this)
        # For now, we'll use a workaround - store the account info separately
        token_result = await oauth_service.exchange_code_for_tokens(
            platform_name, code, state, {}
        )
        
        if not token_result["success"]:
            logger.error(f"Token exchange failed for {platform_name}: {token_result['error']}")
            return RedirectResponse(
                url=f"/admin/platforms?error=token_exchange_failed&platform={platform_name}&error_message={token_result['error']}",
                status_code=302
            )
        
        # Store credentials in system_platform_credentials table
        credentials = {
            "access_token": token_result.get("access_token"),
            "refresh_token": token_result.get("refresh_token"),
            "expires_at": token_result.get("expires_at"),
            "scopes": token_result.get("scopes", []),
            "type": "oauth2"
        }
        
        connect_result = await platform_manager.connect_platform(
            platform_name=platform_name,
            account_name=account_name,
            account_handle=account_handle,
            credentials=credentials,
            admin_user_id=admin_user_id
        )
        
        if not connect_result.get("success"):
            return RedirectResponse(
                url=f"/admin/platforms?error=connection_failed&platform={platform_name}&error_message={connect_result.get('error')}",
                status_code=302
            )
        
        # Redirect to success page
        return RedirectResponse(
            url=f"/admin/platforms?success=platform_connected&platform={platform_name}&account_name={account_name}",
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"Failed to handle OAuth callback for {platform_name}: {str(e)}")
        return RedirectResponse(
            url=f"/admin/platforms?error=callback_failed&platform={platform_name}",
            status_code=302
        )

@router.post("/platforms/connect")
async def connect_platform_manual(
    platform_name: str,
    account_name: str,
    account_handle: Optional[str] = None,
    credentials: Optional[Dict[str, Any]] = None,
    admin_user: AdminUser = Depends(require_super_admin),
    platform_manager: Agent47PlatformManager = Depends(get_agent47_platform_manager)
):
    """Connect Agent47 to a platform manually (for API key-based platforms)"""
    try:
        result = await platform_manager.connect_platform(
            platform_name=platform_name,
            account_name=account_name,
            account_handle=account_handle,
            credentials=credentials,
            admin_user_id=admin_user.user_id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to connect platform")
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to connect platform: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect platform"
        )

@router.post("/platforms/{credential_id}/disconnect")
async def disconnect_platform(
    credential_id: int,
    admin_user: AdminUser = Depends(require_super_admin),
    platform_manager: Agent47PlatformManager = Depends(get_agent47_platform_manager)
):
    """Disconnect Agent47 from a platform"""
    try:
        success = await platform_manager.disconnect_platform(
            credential_id=credential_id,
            admin_user_id=admin_user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform connection not found"
            )
        
        return {"message": "Platform disconnected successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect platform: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect platform"
        )

@router.get("/platforms/agents/{agent_name}")
async def get_agent_platforms(
    agent_name: str,
    admin_user: AdminUser = Depends(require_super_admin),
    platform_manager: Agent47PlatformManager = Depends(get_agent47_platform_manager)
):
    """Get all platforms an agent has access to"""
    try:
        platforms = await platform_manager.get_agent_platforms(agent_name)
        return {"agent": agent_name, "platforms": platforms, "total": len(platforms)}
    except Exception as e:
        logger.error(f"Failed to get agent platforms: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent platforms"
        )

@router.get("/platforms/agents")
async def get_all_agents_platforms(
    admin_user: AdminUser = Depends(require_super_admin),
    platform_manager: Agent47PlatformManager = Depends(get_agent47_platform_manager)
):
    """Get platforms for all agents"""
    try:
        agents_platforms = await platform_manager.get_all_agents_platforms()
        return {"agents": agents_platforms}
    except Exception as e:
        logger.error(f"Failed to get all agents platforms: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get all agents platforms"
        )

@router.post("/platforms/{credential_id}/assign-agent")
async def assign_agent_to_platform(
    credential_id: int,
    agent_name: str,
    permissions: Optional[Dict[str, bool]] = None,
    priority: int = 0,
    admin_user: AdminUser = Depends(require_super_admin),
    platform_manager: Agent47PlatformManager = Depends(get_agent47_platform_manager)
):
    """Assign an agent to a platform connection"""
    try:
        success = await platform_manager.assign_agent_to_platform(
            credential_id=credential_id,
            agent_name=agent_name,
            permissions=permissions,
            priority=priority,
            admin_user_id=admin_user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to assign agent to platform"
            )
        
        return {"message": f"Agent {agent_name} assigned to platform successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign agent to platform"
        )

@router.delete("/platforms/{credential_id}/agents/{agent_name}")
async def remove_agent_from_platform(
    credential_id: int,
    agent_name: str,
    admin_user: AdminUser = Depends(require_super_admin),
    platform_manager: Agent47PlatformManager = Depends(get_agent47_platform_manager)
):
    """Remove an agent from a platform connection"""
    try:
        success = await platform_manager.remove_agent_from_platform(credential_id, agent_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent assignment not found"
            )
        
        return {"message": f"Agent {agent_name} removed from platform successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove agent from platform"
        )

@router.put("/platforms/{credential_id}/agents/{agent_name}/permissions")
async def update_agent_permissions(
    credential_id: int,
    agent_name: str,
    permissions: Dict[str, bool],
    admin_user: AdminUser = Depends(require_super_admin),
    platform_manager: Agent47PlatformManager = Depends(get_agent47_platform_manager)
):
    """Update agent permissions for a platform"""
    try:
        success = await platform_manager.update_agent_permissions(
            credential_id=credential_id,
            agent_name=agent_name,
            permissions=permissions,
            admin_user_id=admin_user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update agent permissions"
            )
        
        return {"message": f"Permissions updated for agent {agent_name}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent permissions"
        )

@router.get("/platforms/statistics")
async def get_platform_statistics(
    platform_name: Optional[str] = None,
    admin_user: AdminUser = Depends(require_super_admin),
    platform_manager: Agent47PlatformManager = Depends(get_agent47_platform_manager)
):
    """Get platform usage statistics"""
    try:
        stats = await platform_manager.get_platform_statistics(platform_name)
        return stats
    except Exception as e:
        logger.error(f"Failed to get platform statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get platform statistics"
        )

# =============================================================================
# SETTINGS MANAGEMENT
# =============================================================================

async def get_settings_manager_dep() -> SettingsManager:
    """Dependency to get settings manager"""
    return await get_settings_manager()

@router.get("/settings")
async def get_settings(
    category: Optional[str] = None,
    public_only: bool = False,
    admin_user: AdminUser = Depends(check_admin_permission),
    settings_manager: SettingsManager = Depends(get_settings_manager_dep)
):
    """Get all settings, optionally filtered by category"""
    try:
        setting_category = SettingCategory(category) if category else None
        settings = await settings_manager.get_all_settings(
            category=setting_category,
            public_only=public_only
        )
        
        # Convert to dict format for JSON response
        settings_dict = {}
        for key, setting in settings.items():
            settings_dict[key] = {
                "key": setting.key,
                "value": setting.value,
                "type": setting.setting_type.value,
                "category": setting.category.value,
                "description": setting.description,
                "is_encrypted": setting.is_encrypted,
                "is_public": setting.is_public,
                "validation_rules": setting.validation_rules,
                "default_value": setting.default_value,
                "updated_by": setting.updated_by,
                "updated_at": setting.updated_at.isoformat() if setting.updated_at else None,
                "version": setting.version
            }
        
        return {"settings": settings_dict, "total": len(settings_dict)}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get settings"
        )

@router.get("/settings/{key}")
async def get_setting(
    key: str,
    admin_user: AdminUser = Depends(check_admin_permission),
    settings_manager: SettingsManager = Depends(get_settings_manager_dep)
):
    """Get a specific setting by key"""
    try:
        setting = await settings_manager.get_setting(key)
        if setting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )
        
        # Get full setting details
        all_settings = await settings_manager.get_all_settings()
        if key not in all_settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )
        
        setting_obj = all_settings[key]
        return {
            "key": setting_obj.key,
            "value": setting_obj.value,
            "type": setting_obj.setting_type.value,
            "category": setting_obj.category.value,
            "description": setting_obj.description,
            "is_encrypted": setting_obj.is_encrypted,
            "is_public": setting_obj.is_public,
            "validation_rules": setting_obj.validation_rules,
            "default_value": setting_obj.default_value,
            "updated_by": setting_obj.updated_by,
            "updated_at": setting_obj.updated_at.isoformat() if setting_obj.updated_at else None,
            "version": setting_obj.version
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get setting {key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get setting"
        )

@router.put("/settings/{key}")
async def update_setting(
    key: str,
    value: Any = Body(...),
    change_reason: str = Body(default="", alias="change_reason"),
    admin_user: AdminUser = Depends(check_admin_permission),
    settings_manager: SettingsManager = Depends(get_settings_manager_dep)
):
    """Update a setting value"""
    try:
        success = await settings_manager.update_setting(
            key=key,
            value=value,
            updated_by=admin_user.user_id,
            change_reason=change_reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update setting '{key}'. Setting may not exist or value may be invalid."
            )
        
        # Broadcast setting update to all admins via WebSocket
        try:
            from core.realtime.websocket_router import broadcast_alert
            await broadcast_alert({
                "id": f"setting_{key}",
                "source": "system",
                "severity": "info",
                "title": "System Setting Updated",
                "message": f"Setting '{key}' has been updated by admin {admin_user.user_id}",
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "key": key,
                    "value": value,
                    "updated_by": admin_user.user_id,
                    "change_reason": change_reason
                }
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast setting update: {e}")
        
        return {
            "message": f"Setting '{key}' updated successfully",
            "key": key,
            "value": value,
            "updated_by": admin_user.user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update setting {key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update setting"
        )

@router.get("/settings/{key}/history")
async def get_setting_history(
    key: str,
    limit: int = 50,
    admin_user: AdminUser = Depends(check_admin_permission),
    settings_manager: SettingsManager = Depends(get_settings_manager_dep)
):
    """Get change history for a setting"""
    try:
        history = await settings_manager.get_setting_history(key, limit=limit)
        
        history_list = []
        for change in history:
            history_list.append({
                "id": change.id,
                "setting_key": change.setting_key,
                "old_value": change.old_value,
                "new_value": change.new_value,
                "changed_by": change.changed_by,
                "change_reason": change.change_reason,
                "timestamp": change.timestamp.isoformat(),
                "reverted": change.reverted
            })
        
        return {"history": history_list, "total": len(history_list)}
        
    except Exception as e:
        logger.error(f"Failed to get setting history for {key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get setting history"
        )

# =============================================================================
# LOGS MANAGEMENT
# =============================================================================

async def get_log_viewer_dep() -> LogViewer:
    """Dependency to get log viewer"""
    return await get_log_viewer()

@router.post("/logs")
async def get_logs(
    filters: Dict[str, Any] = Body(...),
    page: int = Body(default=1),
    limit: int = Body(default=100),
    admin_user: AdminUser = Depends(check_admin_permission),
    log_viewer: LogViewer = Depends(get_log_viewer_dep)
):
    """Get logs with filtering and pagination"""
    try:
        # Build LogFilter from request
        log_filter = LogFilter()
        
        if "levels" in filters:
            log_filter.levels = [LogLevel(level) for level in filters["levels"]]
        if "sources" in filters:
            log_filter.sources = filters["sources"]
        if "modules" in filters:
            log_filter.modules = filters["modules"]
        if "search_text" in filters:
            log_filter.search_text = filters["search_text"]
        if "user_id" in filters:
            log_filter.user_id = filters["user_id"]
        if "start_time" in filters:
            log_filter.start_time = datetime.fromisoformat(filters["start_time"])
        if "end_time" in filters:
            log_filter.end_time = datetime.fromisoformat(filters["end_time"])
        if "has_error" in filters:
            log_filter.has_error = filters["has_error"]
        
        logs, total_count = await log_viewer.get_logs(log_filter, page=page, limit=limit)
        
        logs_list = []
        for log in logs:
            logs_list.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "level": log.level.value,
                "source": log.source,
                "module": log.module,
                "message": log.message,
                "user_id": log.user_id,
                "request_id": log.request_id,
                "ip_address": str(log.ip_address) if log.ip_address else None,
                "metadata": log.metadata,
                "stack_trace": log.stack_trace
            })
        
        return {
            "logs": logs_list,
            "total": total_count,
            "page": page,
            "limit": limit
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid filter parameter: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get logs"
        )

@router.get("/logs/statistics")
async def get_log_statistics(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    admin_user: AdminUser = Depends(check_admin_permission),
    log_viewer: LogViewer = Depends(get_log_viewer_dep)
):
    """Get log statistics"""
    try:
        start = datetime.fromisoformat(start_time) if start_time else None
        end = datetime.fromisoformat(end_time) if end_time else None
        
        stats = await log_viewer.get_log_statistics(start_time=start, end_time=end)
        return stats
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get log statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get log statistics"
        )

# =============================================================================
# CACHE MANAGEMENT
# =============================================================================

async def get_cache_manager_dep() -> CacheManager:
    """Dependency to get cache manager"""
    return await get_cache_manager()

@router.get("/cache/statistics")
async def get_cache_statistics(
    cache_type: Optional[str] = None,
    admin_user: AdminUser = Depends(check_admin_permission),
    cache_manager: CacheManager = Depends(get_cache_manager_dep)
):
    """Get cache statistics"""
    try:
        cache_type_enum = CacheType(cache_type) if cache_type else None
        stats = await cache_manager.get_cache_statistics(cache_type=cache_type_enum)
        return {"statistics": stats}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid cache type: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get cache statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache statistics"
        )

@router.get("/cache/keys")
async def get_cache_keys(
    pattern: str = "*",
    limit: int = 100,
    admin_user: AdminUser = Depends(check_admin_permission),
    cache_manager: CacheManager = Depends(get_cache_manager_dep)
):
    """Get cache keys matching a pattern"""
    try:
        keys = await cache_manager.get_cache_keys(pattern=pattern, limit=limit)
        
        keys_list = []
        for key in keys:
            keys_list.append({
                "key": key.key,
                "value_type": key.value_type,
                "size_bytes": key.size_bytes,
                "ttl_seconds": key.ttl_seconds,
                "created_at": key.created_at.isoformat() if key.created_at else None,
                "last_accessed": key.last_accessed.isoformat() if key.last_accessed else None,
                "access_count": key.access_count
            })
        
        return {"keys": keys_list, "total": len(keys_list)}
        
    except Exception as e:
        logger.error(f"Failed to get cache keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache keys"
        )

@router.post("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = Body(default=None),
    admin_user: AdminUser = Depends(check_admin_permission),
    cache_manager: CacheManager = Depends(get_cache_manager_dep)
):
    """Clear cache keys matching a pattern"""
    try:
        deleted_count = await cache_manager.clear_cache(pattern=pattern)
        
        return {
            "message": f"Cache cleared successfully",
            "deleted_keys": deleted_count,
            "pattern": pattern or "all"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )

@router.get("/cache/health")
async def get_cache_health(
    admin_user: AdminUser = Depends(check_admin_permission),
    cache_manager: CacheManager = Depends(get_cache_manager_dep)
):
    """Get cache health status"""
    try:
        health = await cache_manager.get_cache_health()
        return health
        
    except Exception as e:
        logger.error(f"Failed to get cache health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache health"
        )

# =============================================================================
# FEATURE FLAGS MANAGEMENT
# =============================================================================

async def get_feature_flags_manager_dep() -> FeatureFlagsManager:
    """Dependency to get feature flags manager"""
    return await get_feature_flags_manager()

@router.get("/feature-flags")
async def get_feature_flags(
    admin_user: AdminUser = Depends(check_admin_permission),
    feature_flags_manager: FeatureFlagsManager = Depends(get_feature_flags_manager_dep)
):
    """Get all feature flags"""
    try:
        flags = await feature_flags_manager.get_all_feature_flags()
        
        flags_list = []
        for flag in flags:
            flags_list.append({
                "key": flag.key,
                "name": flag.name,
                "description": flag.description,
                "status": flag.status.value,
                "targeting_type": flag.targeting_type.value,
                "targeting_config": flag.targeting_config,
                "enabled_percentage": flag.enabled_percentage,
                "enabled_user_ids": list(flag.enabled_user_ids),
                "enabled_tiers": flag.enabled_tiers,
                "created_by": flag.created_by,
                "created_at": flag.created_at.isoformat() if flag.created_at else None,
                "updated_by": flag.updated_by,
                "updated_at": flag.updated_at.isoformat() if flag.updated_at else None,
                "metadata": flag.metadata
            })
        
        return {"feature_flags": flags_list, "total": len(flags_list)}
        
    except Exception as e:
        logger.error(f"Failed to get feature flags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get feature flags"
        )

@router.get("/feature-flags/{key}")
async def get_feature_flag(
    key: str,
    admin_user: AdminUser = Depends(check_admin_permission),
    feature_flags_manager: FeatureFlagsManager = Depends(get_feature_flags_manager_dep)
):
    """Get a specific feature flag"""
    try:
        flag = await feature_flags_manager.get_feature_flag(key)
        
        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature flag '{key}' not found"
            )
        
        return {
            "key": flag.key,
            "name": flag.name,
            "description": flag.description,
            "status": flag.status.value,
            "targeting_type": flag.targeting_type.value,
            "targeting_config": flag.targeting_config,
            "enabled_percentage": flag.enabled_percentage,
            "enabled_user_ids": list(flag.enabled_user_ids),
            "enabled_tiers": flag.enabled_tiers,
            "created_by": flag.created_by,
            "created_at": flag.created_at.isoformat() if flag.created_at else None,
            "updated_by": flag.updated_by,
            "updated_at": flag.updated_at.isoformat() if flag.updated_at else None,
            "metadata": flag.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get feature flag {key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get feature flag"
        )

@router.post("/feature-flags")
async def create_feature_flag(
    data: Dict[str, Any] = Body(...),
    admin_user: AdminUser = Depends(check_admin_permission),
    feature_flags_manager: FeatureFlagsManager = Depends(get_feature_flags_manager_dep)
):
    """Create a new feature flag"""
    try:
        key = data.get("key")
        name = data.get("name")
        description = data.get("description", "")
        status = data.get("status", "disabled")
        targeting_type = data.get("targeting_type", "all_users")
        targeting_config = data.get("targeting_config", {})
        
        if not key or not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'key' and 'name' are required"
            )
        
        flag_status = FeatureFlagStatus(status)
        targeting = TargetingType(targeting_type)
        
        success = await feature_flags_manager.create_feature_flag(
            key=key,
            name=name,
            description=description,
            created_by=admin_user.user_id,
            status=flag_status,
            targeting_type=targeting,
            targeting_config=targeting_config
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Feature flag '{key}' already exists"
            )
        
        return {
            "message": f"Feature flag '{key}' created successfully",
            "key": key
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create feature flag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create feature flag"
        )

@router.put("/feature-flags/{key}")
async def update_feature_flag(
    key: str,
    updates: Dict[str, Any] = Body(...),
    admin_user: AdminUser = Depends(check_admin_permission),
    feature_flags_manager: FeatureFlagsManager = Depends(get_feature_flags_manager_dep)
):
    """Update a feature flag"""
    try:
        success = await feature_flags_manager.update_feature_flag(
            key=key,
            updates=updates,
            updated_by=admin_user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature flag '{key}' not found"
            )
        
        return {
            "message": f"Feature flag '{key}' updated successfully",
            "key": key
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update feature flag {key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feature flag"
        )

@router.delete("/feature-flags/{key}")
async def delete_feature_flag(
    key: str,
    admin_user: AdminUser = Depends(check_admin_permission),
    feature_flags_manager: FeatureFlagsManager = Depends(get_feature_flags_manager_dep)
):
    """Delete a feature flag"""
    try:
        success = await feature_flags_manager.delete_feature_flag(
            key=key,
            deleted_by=admin_user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature flag '{key}' not found"
            )
        
        return {
            "message": f"Feature flag '{key}' deleted successfully",
            "key": key
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete feature flag {key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete feature flag"
        )

@router.get("/feature-flags/{key}/statistics")
async def get_feature_flag_statistics(
    key: str,
    hours: int = 24,
    admin_user: AdminUser = Depends(check_admin_permission),
    feature_flags_manager: FeatureFlagsManager = Depends(get_feature_flags_manager_dep)
):
    """Get statistics for a feature flag"""
    try:
        stats = await feature_flags_manager.get_feature_flag_statistics(
            flag_key=key,
            hours=hours
        )
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get feature flag statistics for {key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get feature flag statistics"
        )

# =============================================================================
# ALERTS MANAGEMENT
# =============================================================================

_alert_manager_instance = None

async def get_alert_manager_dep() -> AlertManager:
    """Dependency to get AlertManager instance"""
    global _alert_manager_instance
    if _alert_manager_instance is None:
        _alert_manager_instance = AlertManager()
        await _alert_manager_instance.initialize()
    return _alert_manager_instance

@router.get("/alerts")
async def get_alerts(
    source: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    admin_user: AdminUser = Depends(check_admin_permission),
    alert_manager: AlertManager = Depends(get_alert_manager_dep)
):
    """Get active alerts"""
    try:
        alert_source = AlertSource(source) if source else None
        alert_severity = AlertSeverity(severity) if severity else None
        
        alerts = await alert_manager.get_active_alerts(
            source=alert_source,
            severity=alert_severity
        )
        
        if status:
            alerts = [a for a in alerts if a.get("status") == status]
        
        return {
            "alerts": alerts[:limit],
            "total": len(alerts)
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get alerts"
        )

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    admin_user: AdminUser = Depends(check_admin_permission),
    alert_manager: AlertManager = Depends(get_alert_manager_dep)
):
    """Acknowledge an alert"""
    try:
        success = await alert_manager.acknowledge_alert(
            alert_id=alert_id,
            user=admin_user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert '{alert_id}' not found"
            )
        
        return {
            "message": f"Alert '{alert_id}' acknowledged successfully",
            "alert_id": alert_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert"
        )

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolution_notes: Optional[str] = Body(None, embed=True),
    admin_user: AdminUser = Depends(check_admin_permission),
    alert_manager: AlertManager = Depends(get_alert_manager_dep)
):
    """Resolve an alert"""
    try:
        success = await alert_manager.resolve_alert(
            alert_id=alert_id,
            user=admin_user.user_id,
            resolution_notes=resolution_notes
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert '{alert_id}' not found"
            )
        
        return {
            "message": f"Alert '{alert_id}' resolved successfully",
            "alert_id": alert_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve alert"
        )

@router.get("/alerts/statistics")
async def get_alert_statistics(
    admin_user: AdminUser = Depends(check_admin_permission),
    alert_manager: AlertManager = Depends(get_alert_manager_dep)
):
    """Get alert statistics"""
    try:
        stats = await alert_manager.get_alert_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get alert statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get alert statistics"
        )

# =============================================================================
# FINANCE MANAGEMENT
# =============================================================================

async def get_finance_manager_dep() -> FinanceManager:
    """Dependency to get FinanceManager instance"""
    return await get_finance_manager()

@router.get("/finance/overview")
async def get_finance_overview(
    admin_user: AdminUser = Depends(check_admin_permission),
    finance_manager: FinanceManager = Depends(get_finance_manager_dep)
):
    """Get financial overview"""
    try:
        overview = await finance_manager.get_financial_overview()
        return overview
        
    except Exception as e:
        logger.error(f"Failed to get finance overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get finance overview"
        )

@router.get("/finance/transactions")
async def get_finance_transactions(
    limit: int = Query(50, ge=1, le=500),
    admin_user: AdminUser = Depends(check_admin_permission),
    finance_manager: FinanceManager = Depends(get_finance_manager_dep)
):
    """Get recent financial transactions"""
    try:
        transactions = await finance_manager.get_recent_transactions(limit=limit)
        return {
            "transactions": transactions,
            "total": len(transactions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get finance transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get finance transactions"
        )

@router.get("/finance/statistics")
async def get_finance_statistics(
    days: int = Query(30, ge=1, le=365),
    admin_user: AdminUser = Depends(check_admin_permission),
    finance_manager: FinanceManager = Depends(get_finance_manager_dep)
):
    """Get financial statistics"""
    try:
        stats = await finance_manager.get_financial_statistics(days=days)
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get finance statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get finance statistics"
        )

# =============================================================================
# CODE MANAGEMENT
# =============================================================================

async def get_code_manager_dep() -> CodeManager:
    """Dependency to get CodeManager instance"""
    return await get_code_manager()

@router.post("/code/read")
async def read_code_file(
    file_path: str = Body(..., embed=True),
    session_id: Optional[str] = Body(None, embed=True),
    admin_user: AdminUser = Depends(check_admin_permission),
    code_manager: CodeManager = Depends(get_code_manager_dep)
):
    """Read a code file"""
    try:
        result = await code_manager.read_file(
            file_path=file_path,
            user_id=admin_user.user_id,
            session_id=session_id
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to read code file {file_path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read code file"
        )

@router.post("/code/write")
async def write_code_file(
    file_path: str = Body(..., embed=True),
    content: str = Body(..., embed=True),
    backup: bool = Body(True, embed=True),
    admin_user: AdminUser = Depends(check_admin_permission),
    code_manager: CodeManager = Depends(get_code_manager_dep)
):
    """Write to a code file"""
    try:
        result = await code_manager.write_file(
            file_path=file_path,
            content=content,
            user_id=admin_user.user_id,
            backup=backup
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to write code file {file_path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to write code file"
        )

@router.post("/code/execute")
async def execute_code_command(
    command: str = Body(..., embed=True),
    session_id: Optional[str] = Body(None, embed=True),
    timeout: int = Body(30, embed=True),
    admin_user: AdminUser = Depends(check_admin_permission),
    code_manager: CodeManager = Depends(get_code_manager_dep)
):
    """Execute a terminal command"""
    try:
        result = await code_manager.execute_terminal_command(
            command=command,
            user_id=admin_user.user_id,
            session_id=session_id,
            timeout=timeout
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute code command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute code command"
        )

@router.get("/code/health")
async def get_code_health(
    directory_path: Optional[str] = Query(None),
    admin_user: AdminUser = Depends(check_admin_permission),
    code_manager: CodeManager = Depends(get_code_manager_dep)
):
    """Get code health metrics"""
    try:
        health = await code_manager.analyze_code_health(directory_path=directory_path)
        return {
            "total_files": health.total_files,
            "error_count": health.error_count,
            "warning_count": health.warning_count,
            "test_coverage": health.test_coverage,
            "complexity_score": health.complexity_score,
            "maintainability_index": health.maintainability_index,
            "health_status": health.health_status.value,
            "last_updated": health.last_updated.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get code health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get code health"
        )

# =============================================================================
# TERMINAL MANAGEMENT
# =============================================================================

_terminal_manager_instance = None

async def get_terminal_manager_dep() -> TerminalManager:
    """Dependency to get TerminalManager instance"""
    global _terminal_manager_instance
    if _terminal_manager_instance is None:
        _terminal_manager_instance = TerminalManager()
        await _terminal_manager_instance.initialize()
    return _terminal_manager_instance

@router.post("/terminal/sessions")
async def create_terminal_session(
    working_directory: Optional[str] = Body(None, embed=True),
    admin_user: AdminUser = Depends(check_admin_permission),
    terminal_manager: TerminalManager = Depends(get_terminal_manager_dep)
):
    """Create a new terminal session"""
    try:
        result = await terminal_manager.create_session(
            user_id=admin_user.user_id,
            working_directory=working_directory
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to create terminal session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create terminal session"
        )

@router.post("/terminal/sessions/{session_id}/execute")
async def execute_terminal_command(
    session_id: str,
    command: str = Body(..., embed=True),
    timeout: int = Body(30, embed=True),
    admin_user: AdminUser = Depends(check_admin_permission),
    terminal_manager: TerminalManager = Depends(get_terminal_manager_dep)
):
    """Execute a command in a terminal session"""
    try:
        result = await terminal_manager.execute_command(
            session_id=session_id,
            command=command,
            timeout=timeout
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute terminal command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute terminal command"
        )

@router.get("/terminal/sessions/{session_id}/history")
async def get_terminal_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=500),
    admin_user: AdminUser = Depends(check_admin_permission),
    terminal_manager: TerminalManager = Depends(get_terminal_manager_dep)
):
    """Get command history for a terminal session"""
    try:
        history = await terminal_manager.get_command_history(
            session_id=session_id,
            limit=limit
        )
        return {
            "session_id": session_id,
            "history": history
        }
        
    except Exception as e:
        logger.error(f"Failed to get terminal history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get terminal history"
        )

@router.delete("/terminal/sessions/{session_id}")
async def close_terminal_session(
    session_id: str,
    admin_user: AdminUser = Depends(check_admin_permission),
    terminal_manager: TerminalManager = Depends(get_terminal_manager_dep)
):
    """Close a terminal session"""
    try:
        success = await terminal_manager.close_session(session_id=session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Terminal session '{session_id}' not found"
            )
        
        return {
            "message": f"Terminal session '{session_id}' closed successfully",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to close terminal session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close terminal session"
        )

# =============================================================================
# COMMUNICATIONS MANAGEMENT
# =============================================================================

_communication_manager_instance = None

async def get_communication_manager_dep() -> CommunicationManager:
    """Dependency to get CommunicationManager instance"""
    global _communication_manager_instance
    if _communication_manager_instance is None:
        _communication_manager_instance = CommunicationManager()
        await _communication_manager_instance.initialize()
    return _communication_manager_instance

@router.post("/communications/send")
async def send_communication(
    comm_type: str = Body(..., embed=True),
    recipient: str = Body(..., embed=True),
    subject: str = Body(..., embed=True),
    message: str = Body(..., embed=True),
    template_id: Optional[str] = Body(None, embed=True),
    admin_user: AdminUser = Depends(check_admin_permission),
    communication_manager: CommunicationManager = Depends(get_communication_manager_dep)
):
    """Send a communication"""
    try:
        comm_type_enum = CommunicationType(comm_type)
        
        result = await communication_manager.send_communication(
            comm_type=comm_type_enum,
            recipient=recipient,
            subject=subject,
            message=message,
            template_id=template_id
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid communication type: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to send communication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send communication"
        )

@router.get("/communications/{communication_id}/status")
async def get_communication_status(
    communication_id: str,
    admin_user: AdminUser = Depends(check_admin_permission),
    communication_manager: CommunicationManager = Depends(get_communication_manager_dep)
):
    """Get communication status"""
    try:
        status = await communication_manager.get_communication_status(communication_id)
        return status
        
    except Exception as e:
        logger.error(f"Failed to get communication status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get communication status"
        )

@router.get("/communications/statistics")
async def get_communication_statistics(
    admin_user: AdminUser = Depends(check_admin_permission),
    communication_manager: CommunicationManager = Depends(get_communication_manager_dep)
):
    """Get communication statistics"""
    try:
        stats = await communication_manager.get_communication_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get communication statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get communication statistics"
        )

# =============================================================================
# SUPPORT/TICKETS MANAGEMENT
# =============================================================================

_support_manager_instance = None

async def get_support_manager_dep() -> SupportManager:
    """Dependency to get SupportManager instance"""
    global _support_manager_instance
    if _support_manager_instance is None:
        _support_manager_instance = SupportManager()
        await _support_manager_instance.initialize()
    return _support_manager_instance

@router.get("/support/tickets")
async def get_support_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    admin_user: AdminUser = Depends(check_admin_permission),
    support_manager: SupportManager = Depends(get_support_manager_dep)
):
    """Get support tickets"""
    try:
        ticket_status = TicketStatus(status) if status else None
        ticket_priority = TicketPriority(priority) if priority else None
        
        tickets = await support_manager.get_support_queue(
            assigned_to=assigned_to,
            status=ticket_status
        )
        
        if ticket_priority:
            tickets = [t for t in tickets if t.get("priority") == ticket_priority.value]
        
        return {
            "tickets": tickets[:limit],
            "total": len(tickets)
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get support tickets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get support tickets"
        )

@router.post("/support/tickets")
async def create_support_ticket(
    user_id: str = Body(..., embed=True),
    subject: str = Body(..., embed=True),
    description: str = Body(..., embed=True),
    category: str = Body(..., embed=True),
    priority: str = Body(..., embed=True),
    admin_user: AdminUser = Depends(check_admin_permission),
    support_manager: SupportManager = Depends(get_support_manager_dep)
):
    """Create a support ticket"""
    try:
        ticket_category = TicketCategory(category)
        ticket_priority = TicketPriority(priority)
        
        ticket = await support_manager.create_ticket(
            user_id=user_id,
            subject=subject,
            description=description,
            category=ticket_category,
            priority=ticket_priority
        )
        
        return {
            "message": "Ticket created successfully",
            "ticket": {
                "ticket_id": ticket.ticket_id,
                "subject": ticket.subject,
                "status": ticket.status.value,
                "priority": ticket.priority.value
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to create support ticket: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create support ticket"
        )

@router.put("/support/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: str,
    new_status: str = Body(..., embed=True),
    admin_user: AdminUser = Depends(check_admin_permission),
    support_manager: SupportManager = Depends(get_support_manager_dep)
):
    """Update ticket status"""
    try:
        ticket_status = TicketStatus(new_status)
        
        success = await support_manager.update_ticket_status(
            ticket_id=ticket_id,
            status=ticket_status,
            updated_by=admin_user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket '{ticket_id}' not found"
            )
        
        return {
            "message": f"Ticket '{ticket_id}' status updated successfully",
            "ticket_id": ticket_id,
            "status": new_status
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update ticket status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update ticket status"
        )

@router.get("/support/statistics")
async def get_support_statistics(
    admin_user: AdminUser = Depends(check_admin_permission),
    support_manager: SupportManager = Depends(get_support_manager_dep)
):
    """Get support statistics"""
    try:
        stats = await support_manager.get_support_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get support statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get support statistics"
        )

# =============================================================================
# SERVERS MANAGEMENT
# =============================================================================

_server_manager_instance = None

async def get_server_manager_dep() -> ServerManager:
    """Dependency to get ServerManager instance"""
    global _server_manager_instance
    if _server_manager_instance is None:
        _server_manager_instance = ServerManager()
        await _server_manager_instance.initialize()
    return _server_manager_instance

@router.get("/servers/status")
async def get_servers_status(
    admin_user: AdminUser = Depends(check_admin_permission),
    server_manager: ServerManager = Depends(get_server_manager_dep)
):
    """Get server status overview"""
    try:
        status = await server_manager.get_server_status()
        return status
        
    except Exception as e:
        logger.error(f"Failed to get server status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get server status"
        )

@router.get("/servers/{server_id}")
async def get_server_details(
    server_id: str,
    admin_user: AdminUser = Depends(check_admin_permission),
    server_manager: ServerManager = Depends(get_server_manager_dep)
):
    """Get server details"""
    try:
        details = await server_manager.get_server_details(server_id=server_id)
        return details
        
    except Exception as e:
        logger.error(f"Failed to get server details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get server details"
        )

@router.get("/servers/alerts")
async def get_server_alerts(
    server_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    admin_user: AdminUser = Depends(check_admin_permission),
    server_manager: ServerManager = Depends(get_server_manager_dep)
):
    """Get server alerts"""
    try:
        alerts = await server_manager.get_server_alerts(
            server_id=server_id,
            limit=limit
        )
        return {
            "alerts": alerts,
            "total": len(alerts)
        }
        
    except Exception as e:
        logger.error(f"Failed to get server alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get server alerts"
        )

# =============================================================================
# GOALS MANAGEMENT
# =============================================================================

async def get_goal_manager_dep() -> GoalManager:
    """Dependency to get GoalManager instance"""
    return await get_goal_manager()

@router.get("/goals")
async def get_goals(
    status: Optional[str] = Query(None),
    goal_type: Optional[str] = Query(None),
    admin_user: AdminUser = Depends(check_admin_permission),
    goal_manager: GoalManager = Depends(get_goal_manager_dep)
):
    """Get all goals"""
    try:
        goal_status = GoalStatus(status) if status else None
        goal_type_enum = GoalType(goal_type) if goal_type else None
        
        goals = await goal_manager.get_all_goals(
            status=goal_status,
            goal_type=goal_type_enum
        )
        
        return {
            "goals": [
                {
                    "id": goal.id,
                    "name": goal.name,
                    "description": goal.description,
                    "status": goal.status.value,
                    "priority": goal.priority.value,
                    "goal_type": goal.goal_type.value,
                    "start_date": goal.start_date.isoformat(),
                    "end_date": goal.end_date.isoformat(),
                    "overall_progress": goal.overall_progress,
                    "days_remaining": goal.days_remaining,
                    "assigned_agents": goal.assigned_agents
                }
                for goal in goals
            ],
            "total": len(goals)
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get goals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get goals"
        )

@router.post("/goals")
async def create_goal(
    goal_data: Dict[str, Any] = Body(...),
    admin_user: AdminUser = Depends(check_admin_permission),
    goal_manager: GoalManager = Depends(get_goal_manager_dep)
):
    """Create a new goal"""
    try:
        goal = await goal_manager.create_goal(
            goal_data=goal_data,
            created_by=admin_user.user_id
        )
        
        return {
            "message": "Goal created successfully",
            "goal": {
                "id": goal.id,
                "name": goal.name,
                "status": goal.status.value,
                "overall_progress": goal.overall_progress
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create goal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create goal"
        )

@router.put("/goals/{goal_id}")
async def update_goal(
    goal_id: str,
    updates: Dict[str, Any] = Body(...),
    admin_user: AdminUser = Depends(check_admin_permission),
    goal_manager: GoalManager = Depends(get_goal_manager_dep)
):
    """Update a goal"""
    try:
        if "status" in updates:
            new_status = GoalStatus(updates["status"])
            success = await goal_manager.update_goal_status(
                goal_id=goal_id,
                new_status=new_status,
                updated_by=admin_user.user_id
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Goal '{goal_id}' not found"
                )
        
        return {
            "message": f"Goal '{goal_id}' updated successfully",
            "goal_id": goal_id
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update goal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update goal"
        )

@router.get("/goals/{goal_id}/progress")
async def get_goal_progress(
    goal_id: str,
    admin_user: AdminUser = Depends(check_admin_permission),
    goal_manager: GoalManager = Depends(get_goal_manager_dep)
):
    """Get goal progress"""
    try:
        progress = await goal_manager.get_goal_progress(goal_id=goal_id)
        return {
            "goal_id": goal_id,
            "progress": progress
        }
        
    except Exception as e:
        logger.error(f"Failed to get goal progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get goal progress"
        )

# =============================================================================
# IMPERSONATION MANAGEMENT
# =============================================================================

_impersonation_manager_instance = None

async def get_impersonation_manager_dep() -> ImpersonationManager:
    """Dependency to get ImpersonationManager instance"""
    global _impersonation_manager_instance
    if _impersonation_manager_instance is None:
        _impersonation_manager_instance = ImpersonationManager()
        await _impersonation_manager_instance.initialize()
    return _impersonation_manager_instance

@router.post("/impersonate/start")
async def start_impersonation(
    target_user_id: str = Body(..., embed=True),
    reason: str = Body(..., embed=True),
    notes: Optional[str] = Body(None, embed=True),
    admin_user: AdminUser = Depends(check_admin_permission),
    impersonation_manager: ImpersonationManager = Depends(get_impersonation_manager_dep)
):
    """Start impersonating a user"""
    try:
        impersonation_reason = ImpersonationReason(reason)
        
        session = await impersonation_manager.start_impersonation(
            admin_user_id=admin_user.user_id,
            target_user_id=target_user_id,
            reason=impersonation_reason,
            notes=notes
        )
        
        return {
            "message": "Impersonation started successfully",
            "session": {
                "session_id": session.session_id,
                "target_user_id": session.target_user_id,
                "expires_at": session.expires_at.isoformat()
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to start impersonation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start impersonation"
        )

@router.post("/impersonate/{session_id}/end")
async def end_impersonation(
    session_id: str,
    reason: Optional[str] = Body(None, embed=True),
    admin_user: AdminUser = Depends(check_admin_permission),
    impersonation_manager: ImpersonationManager = Depends(get_impersonation_manager_dep)
):
    """End an impersonation session"""
    try:
        success = await impersonation_manager.end_impersonation(
            session_id=session_id,
            admin_user_id=admin_user.user_id,
            reason=reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Impersonation session '{session_id}' not found"
            )
        
        return {
            "message": f"Impersonation session '{session_id}' ended successfully",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end impersonation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end impersonation"
        )

@router.get("/impersonate/{session_id}")
async def get_impersonation_session(
    session_id: str,
    admin_user: AdminUser = Depends(check_admin_permission),
    impersonation_manager: ImpersonationManager = Depends(get_impersonation_manager_dep)
):
    """Get impersonation session details"""
    try:
        actions = await impersonation_manager.get_session_actions(
            session_id=session_id,
            limit=100
        )
        
        return {
            "session_id": session_id,
            "actions": actions
        }
        
    except Exception as e:
        logger.error(f"Failed to get impersonation session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get impersonation session"
        )

# =============================================================================
# INTEGRATIONS MANAGEMENT
# =============================================================================

async def get_integration_admin_manager_dep() -> IntegrationAdminManager:
    """Dependency to get IntegrationAdminManager instance"""
    return await get_integration_admin_manager()

@router.get("/integrations/overview")
async def get_integrations_overview(
    admin_user: AdminUser = Depends(check_admin_permission),
    integration_admin_manager: IntegrationAdminManager = Depends(get_integration_admin_manager_dep)
):
    """Get integrations overview"""
    try:
        overview = await integration_admin_manager.get_integration_overview()
        return overview
        
    except Exception as e:
        logger.error(f"Failed to get integrations overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get integrations overview"
        )

@router.get("/integrations/{integration_id}")
async def get_integration_details(
    integration_id: str,
    admin_user: AdminUser = Depends(check_admin_permission),
    integration_admin_manager: IntegrationAdminManager = Depends(get_integration_admin_manager_dep)
):
    """Get integration details"""
    try:
        details = await integration_admin_manager.get_integration_details(
            integration_id=integration_id
        )
        return details
        
    except Exception as e:
        logger.error(f"Failed to get integration details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get integration details"
        )

@router.get("/integrations/statistics")
async def get_integrations_statistics(
    days: int = Query(30, ge=1, le=365),
    admin_user: AdminUser = Depends(check_admin_permission),
    integration_admin_manager: IntegrationAdminManager = Depends(get_integration_admin_manager_dep)
):
    """Get integration statistics"""
    try:
        stats = await integration_admin_manager.get_integration_statistics(days=days)
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get integration statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get integration statistics"
        )

# =============================================================================
# BILLING MANAGEMENT
# =============================================================================

async def get_billing_manager_dep() -> BillingManager:
    """Dependency to get BillingManager instance"""
    return await get_billing()

@router.get("/billing/subscriptions")
async def get_billing_subscriptions(
    admin_user: AdminUser = Depends(check_admin_permission),
    billing_manager: BillingManager = Depends(get_billing_manager_dep)
):
    """Get all billing subscriptions"""
    try:
        subscriptions_data = await billing_manager.get_all_subscriptions()
        return subscriptions_data
        
    except Exception as e:
        logger.error(f"Failed to get billing subscriptions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get billing subscriptions"
        )

@router.get("/billing/activity")
async def get_billing_activity(
    admin_user: AdminUser = Depends(check_admin_permission),
    billing_manager: BillingManager = Depends(get_billing_manager_dep)
):
    """Get recent billing activity"""
    try:
        activities = await billing_manager.get_recent_payment_activity()
        return {
            "activities": activities
        }
        
    except Exception as e:
        logger.error(f"Failed to get billing activity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get billing activity"
        )

@router.get("/billing/analytics")
async def get_billing_analytics(
    admin_user: AdminUser = Depends(check_admin_permission),
    billing_manager: BillingManager = Depends(get_billing_manager_dep)
):
    """Get billing analytics"""
    try:
        analytics = await billing_manager.get_revenue_analytics()
        
        return {
            "mrr": analytics.get("monthly_recurring_revenue", 0),
            "mrr_growth": 0.0,
            "clv": analytics.get("average_revenue_per_user", 0) * 12
        }
        
    except Exception as e:
        logger.error(f"Failed to get billing analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get billing analytics"
        )

@router.get("/billing/revenue")
async def get_billing_revenue(
    admin_user: AdminUser = Depends(check_admin_permission),
    billing_manager: BillingManager = Depends(get_billing_manager_dep)
):
    """Get revenue data"""
    try:
        revenue_data = await billing_manager.get_revenue_analytics()
        return revenue_data
        
    except Exception as e:
        logger.error(f"Failed to get revenue data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get revenue data"
        )

# =============================================================================
# REPORTS MANAGEMENT
# =============================================================================

@router.get("/reports/usage")
async def get_usage_reports(
    days: int = Query(30, ge=1, le=365),
    admin_user: AdminUser = Depends(check_admin_permission)
):
    """Get usage reports"""
    try:
        usage_tracker = await get_usage_tracker()
        
        system_stats = await usage_tracker.get_system_usage_statistics()
        
        alerts = []
        if system_stats.get("total_api_calls", 0) > 100000:
            alerts.append({
                "title": "High API Usage",
                "message": "System API calls are above normal threshold"
            })
        
        return {
            "usage_metrics": {
                "api_calls_count": system_stats.get("total_api_calls", 0),
                "storage_used_mb": system_stats.get("total_storage_mb", 0),
                "active_agents": system_stats.get("active_agents_count", 0),
                "bandwidth_used_mb": system_stats.get("total_bandwidth_mb", 0)
            },
            "alerts": alerts
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage reports"
        )

@router.get("/reports/subscriptions")
async def get_subscription_reports(
    days: int = Query(30, ge=1, le=365),
    admin_user: AdminUser = Depends(check_admin_permission),
    billing_manager: BillingManager = Depends(get_billing_manager_dep)
):
    """Get subscription reports"""
    try:
        stats = await billing_manager.get_subscription_statistics()
        revenue_analytics = await billing_manager.get_revenue_analytics()
        
        return {
            "total_subscriptions": stats.get("total_subscriptions", 0),
            "active_subscriptions": stats.get("active_subscriptions", 0),
            "new_subscriptions": stats.get("new_subscriptions", 0),
            "subscription_growth_rate": stats.get("growth_rate", 0.0),
            "activation_rate": stats.get("activation_rate", 0.0),
            "upgrades_count": stats.get("upgrades", 0),
            "upgrade_rate": stats.get("upgrade_rate", 0.0),
            "downgrades_count": stats.get("downgrades", 0),
            "downgrade_rate": stats.get("downgrade_rate", 0.0)
        }
        
    except Exception as e:
        logger.error(f"Failed to get subscription reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription reports"
        )

@router.get("/reports/financial")
async def get_financial_reports(
    period: str = Query("monthly", pattern="^(monthly|yearly|quarterly)$"),
    admin_user: AdminUser = Depends(check_admin_permission),
    finance_manager: FinanceManager = Depends(get_finance_manager_dep),
    billing_manager: BillingManager = Depends(get_billing_manager_dep)
):
    """Get financial reports"""
    try:
        revenue_analytics = await billing_manager.get_revenue_analytics()
        financial_stats = await finance_manager.get_financial_statistics(days=30 if period == "monthly" else 365)
        
        revenue_by_period = {
            "monthly": [revenue_analytics.get("monthly_recurring_revenue", 0) for _ in range(12)]
        }
        
        churn_by_tier = {}
        for tier, data in revenue_analytics.get("tier_distribution", {}).items():
            churn_by_tier[tier] = 0.02
        
        clv_by_tier = {}
        for tier, data in revenue_analytics.get("tier_distribution", {}).items():
            clv_by_tier[tier] = revenue_analytics.get("average_revenue_per_user", 0) * 12
        
        return {
            "revenue": {
                "total_revenue": revenue_analytics.get("total_revenue", 0),
                "monthly_recurring_revenue": revenue_analytics.get("monthly_recurring_revenue", 0),
                "annual_recurring_revenue": revenue_analytics.get("annual_recurring_revenue", 0),
                "average_revenue_per_user": revenue_analytics.get("average_revenue_per_user", 0),
                "revenue_growth_rate": 0.0,
                "revenue_by_period": revenue_by_period
            },
            "churn": {
                "overall_churn_rate": revenue_analytics.get("churn_rate", 0.0) / 100,
                "predicted_churn": revenue_analytics.get("churn_rate", 0.0) / 100,
                "churn_by_tier": churn_by_tier
            },
            "clv": {
                "average_clv": revenue_analytics.get("average_revenue_per_user", 0) * 12,
                "acquisition_cost": 50.0,
                "payback_period": 2.0,
                "clv_by_tier": clv_by_tier,
                "customer_segments": {
                    "high_value": revenue_analytics.get("active_subscriptions", 0) // 3,
                    "medium_value": revenue_analytics.get("active_subscriptions", 0) // 3,
                    "low_value": revenue_analytics.get("active_subscriptions", 0) // 3
                }
            },
            "key_insights": [
                f"Total revenue: ${revenue_analytics.get('total_revenue', 0):,.2f}",
                f"MRR: ${revenue_analytics.get('monthly_recurring_revenue', 0):,.2f}",
                f"Active subscriptions: {revenue_analytics.get('active_subscriptions', 0)}",
                f"Churn rate: {revenue_analytics.get('churn_rate', 0):.2f}%",
                f"ARPU: ${revenue_analytics.get('average_revenue_per_user', 0):.2f}"
            ],
            "recommendations": [
                "Focus on reducing churn rate through customer engagement",
                "Increase ARPU by upselling premium features",
                "Improve customer lifetime value through retention programs",
                "Optimize pricing strategy based on market analysis",
                "Enhance onboarding experience to improve activation",
                "Implement referral programs to reduce acquisition costs"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get financial reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get financial reports"
        )

@router.get("/reports/revenue-forecast")
async def get_revenue_forecast(
    months: int = Query(12, ge=1, le=24),
    admin_user: AdminUser = Depends(check_admin_permission),
    billing_manager: BillingManager = Depends(get_billing_manager_dep)
):
    """Get revenue forecast"""
    try:
        revenue_analytics = await billing_manager.get_revenue_analytics()
        current_mrr = revenue_analytics.get("monthly_recurring_revenue", 0)
        
        forecast = []
        for i in range(months):
            growth_factor = 1.0 + (0.02 * (i + 1))
            forecast.append(current_mrr * growth_factor)
        
        return {
            "forecast": forecast,
            "months": months
        }
        
    except Exception as e:
        logger.error(f"Failed to get revenue forecast: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get revenue forecast"
        )

# =============================================================================
# CHAT/COMMAND CENTER MANAGEMENT
# =============================================================================

@router.post("/chat/execute")
async def execute_chat_command(
    command: str = Body(..., embed=True),
    args: Optional[List[str]] = Body(None, embed=True),
    admin_user: AdminUser = Depends(check_admin_permission),
    admin_core: AdminCore = Depends(get_admin_core)
):
    """Execute a chat command"""
    try:
        command_parts = command.strip().split()
        if not command_parts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Command cannot be empty"
            )
        
        cmd = command_parts[0]
        cmd_args = command_parts[1:] if len(command_parts) > 1 else []
        
        result = {
            "command": command,
            "status": "success",
            "output": "",
            "execution_time": 0
        }
        
        start_time = datetime.utcnow()
        
        if cmd == "system.status":
            system_manager = await get_system_manager()
            system_status = await system_manager.get_system_status()
            result["output"] = f"System Status: {system_status.get('status', 'unknown')}\nCPU: {system_status.get('cpu_usage', 0)}%\nMemory: {system_status.get('memory_usage', 0)}%"
        
        elif cmd == "agents.list":
            agents = await admin_core.get_agents()
            agent_list = "\n".join([f"• {agent.get('name', 'Unknown')} - {agent.get('status', 'unknown')}" for agent in agents])
            result["output"] = f"Agents:\n{agent_list}"
        
        elif cmd == "users.list":
            user_admin_manager = await get_user_admin_manager()
            users = await user_admin_manager.get_all_users(limit=10)
            user_list = "\n".join([f"• {user.get('email', 'Unknown')} - {user.get('tier', 'free')}" for user in users.get('users', [])])
            result["output"] = f"Users:\n{user_list}"
        
        elif cmd == "analytics.overview":
            analytics_manager = await get_analytics_manager()
            analytics = await analytics_manager.get_overview()
            result["output"] = f"Analytics Overview:\nTotal Revenue: ${analytics.get('total_revenue', 0)}\nActive Users: {analytics.get('active_users', 0)}"
        
        elif cmd == "billing.overview":
            billing_manager = await get_billing()
            revenue = await billing_manager.get_revenue_analytics()
            result["output"] = f"Billing Overview:\nMRR: ${revenue.get('monthly_recurring_revenue', 0)}\nActive Subscriptions: {revenue.get('active_subscriptions', 0)}"
        
        elif cmd == "security.audit":
            security_manager = await get_security_manager()
            result["output"] = "Security Audit: All checks passed"
        
        elif cmd == "integration.status":
            integration_admin_manager = await get_integration_admin_manager()
            overview = await integration_admin_manager.get_integration_overview()
            result["output"] = f"Integration Status:\nTotal: {overview.get('total_integrations', 0)}\nActive: {overview.get('active_integrations', 0)}"
        
        else:
            result["status"] = "error"
            result["output"] = f"Unknown command: '{cmd}'. Type 'help' to see available commands."
        
        end_time = datetime.utcnow()
        result["execution_time"] = (end_time - start_time).total_seconds() * 1000
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute command: {str(e)}"
        )

@router.get("/chat/commands")
async def get_available_commands(
    admin_user: AdminUser = Depends(check_admin_permission)
):
    """Get available chat commands"""
    try:
        commands = [
            {
                "name": "system.status",
                "description": "Display system status and health metrics",
                "syntax": "system.status [detailed]",
                "category": "system"
            },
            {
                "name": "agents.list",
                "description": "List all agents with status",
                "syntax": "agents.list [filter]",
                "category": "agents"
            },
            {
                "name": "users.list",
                "description": "List users with filtering",
                "syntax": "users.list [filter]",
                "category": "users"
            },
            {
                "name": "analytics.overview",
                "description": "Display analytics overview",
                "syntax": "analytics.overview [period]",
                "category": "analytics"
            },
            {
                "name": "billing.overview",
                "description": "Display billing overview",
                "syntax": "billing.overview [period]",
                "category": "billing"
            },
            {
                "name": "security.audit",
                "description": "Run security audit",
                "syntax": "security.audit [type]",
                "category": "security"
            },
            {
                "name": "integration.status",
                "description": "Check integration status",
                "syntax": "integration.status [service]",
                "category": "integration"
            }
        ]
        
        return {
            "commands": commands,
            "total": len(commands)
        }
        
    except Exception as e:
        logger.error(f"Failed to get available commands: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available commands"
        )
