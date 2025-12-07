from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from ..database.models import PlatformAuditLog, AuditAction, AuditSeverity

logger = logging.getLogger(__name__)

class AuditLogger:
    """Manages audit logging for platform access and security events"""
    
    def __init__(self):
        self._initialized = False
        self._db = None
    
    async def initialize(self):
        """Initialize audit logger"""
        if self._initialized:
            return
        
        try:
            from ..database.connection import get_database
            self._db = get_database()
            self._initialized = True
            
            logger.info("Platform audit logger initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize audit logger: {e}")
            raise
    
    async def log_action(
        self,
        user_id: int,
        platform_name: str,
        action: AuditAction,
        description: str,
        success: bool = True,
        agent_name: str = None,
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        metadata: Dict[str, Any] = None,
        scopes_used: List[str] = None,
        error_message: str = None,
        response_code: int = None,
        duration_ms: int = None,
        severity: AuditSeverity = None
    ) -> bool:
        """Log an audit event"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self._db.get_session() as session:
                # Determine severity if not provided
                if not severity:
                    if not success:
                        severity = AuditSeverity.HIGH
                    elif action in [AuditAction.TOKEN_STORED, AuditAction.PLATFORM_CONNECTED]:
                        severity = AuditSeverity.MEDIUM
                    else:
                        severity = AuditSeverity.LOW
                
                # Create audit log entry
                audit_log = PlatformAuditLog(
                    user_id=user_id,
                    platform_name=platform_name,
                    action=action,
                    severity=severity,
                    request_id=request_id,
                    agent_name=agent_name,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    description=description,
                    metadata=metadata or {},
                    scopes_used=scopes_used or [],
                    success="success" if success else "failure",
                    error_message=error_message,
                    response_code=response_code,
                    duration_ms=duration_ms
                )
                
                session.add(audit_log)
                await session.commit()
                
                logger.debug(f"Audit log created: {action.value} for user {user_id}, platform {platform_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")
            return False
    
    async def log_token_stored(
        self,
        user_id: int,
        platform_name: str,
        scopes: List[str],
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """Log token storage event"""
        return await self.log_action(
            user_id=user_id,
            platform_name=platform_name,
            action=AuditAction.TOKEN_STORED,
            description=f"Stored tokens for {platform_name} with scopes: {', '.join(scopes)}",
            success=True,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            scopes_used=scopes,
            severity=AuditSeverity.MEDIUM
        )
    
    async def log_token_accessed(
        self,
        user_id: int,
        platform_name: str,
        agent_name: str,
        scopes_used: List[str],
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        duration_ms: int = None
    ) -> bool:
        """Log token access event"""
        return await self.log_action(
            user_id=user_id,
            platform_name=platform_name,
            action=AuditAction.TOKEN_ACCESSED,
            description=f"Agent {agent_name} accessed {platform_name} tokens",
            success=True,
            agent_name=agent_name,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            scopes_used=scopes_used,
            duration_ms=duration_ms,
            severity=AuditSeverity.LOW
        )
    
    async def log_api_call(
        self,
        user_id: int,
        platform_name: str,
        agent_name: str,
        api_endpoint: str,
        method: str,
        success: bool,
        response_code: int = None,
        error_message: str = None,
        scopes_used: List[str] = None,
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        duration_ms: int = None
    ) -> bool:
        """Log API call event"""
        description = f"Agent {agent_name} made {method} call to {api_endpoint}"
        if not success:
            description += f" - Failed: {error_message}"
        
        return await self.log_action(
            user_id=user_id,
            platform_name=platform_name,
            action=AuditAction.API_CALL_MADE,
            description=description,
            success=success,
            agent_name=agent_name,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            scopes_used=scopes_used,
            error_message=error_message,
            response_code=response_code,
            duration_ms=duration_ms,
            severity=AuditSeverity.HIGH if not success else AuditSeverity.LOW
        )
    
    async def log_platform_connected(
        self,
        user_id: int,
        platform_name: str,
        scopes: List[str],
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """Log platform connection event"""
        return await self.log_action(
            user_id=user_id,
            platform_name=platform_name,
            action=AuditAction.PLATFORM_CONNECTED,
            description=f"User connected to {platform_name} with scopes: {', '.join(scopes)}",
            success=True,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            scopes_used=scopes,
            severity=AuditSeverity.MEDIUM
        )
    
    async def log_platform_disconnected(
        self,
        user_id: int,
        platform_name: str,
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """Log platform disconnection event"""
        return await self.log_action(
            user_id=user_id,
            platform_name=platform_name,
            action=AuditAction.PLATFORM_DISCONNECTED,
            description=f"User disconnected from {platform_name}",
            success=True,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=AuditSeverity.MEDIUM
        )
    
    async def log_security_event(
        self,
        user_id: int,
        platform_name: str,
        description: str,
        severity: AuditSeverity = AuditSeverity.HIGH,
        metadata: Dict[str, Any] = None,
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """Log security-related event"""
        return await self.log_action(
            user_id=user_id,
            platform_name=platform_name,
            action=AuditAction.TOKEN_ACCESSED,  # Generic action for security events
            description=description,
            success=False,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
            severity=severity
        )
    
    async def get_user_audit_logs(
        self,
        user_id: int,
        platform_name: str = None,
        action: AuditAction = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get audit logs for a user"""
        if not self._initialized:
            await self.initialize()
        
        try:
            from sqlalchemy import select, and_, desc
            
            async with self._db.get_session() as session:
                query = select(PlatformAuditLog).where(
                    PlatformAuditLog.user_id == user_id
                )
                
                if platform_name:
                    query = query.where(PlatformAuditLog.platform_name == platform_name)
                
                if action:
                    query = query.where(PlatformAuditLog.action == action)
                
                query = query.order_by(desc(PlatformAuditLog.timestamp))
                query = query.offset(offset).limit(limit)
                
                result = await session.execute(query)
                logs = result.scalars().all()
                
                return [log.to_dict() for log in logs]
                
        except Exception as e:
            logger.error(f"Failed to get audit logs for user {user_id}: {e}")
            return []
    
    async def get_security_events(
        self,
        severity: AuditSeverity = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get security events for monitoring"""
        if not self._initialized:
            await self.initialize()
        
        try:
            from sqlalchemy import select, and_, desc
            
            async with self._db.get_session() as session:
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                
                query = select(PlatformAuditLog).where(
                    and_(
                        PlatformAuditLog.timestamp >= cutoff_time,
                        PlatformAuditLog.severity.in_([AuditSeverity.HIGH, AuditSeverity.CRITICAL])
                    )
                )
                
                if severity:
                    query = query.where(PlatformAuditLog.severity == severity)
                
                query = query.order_by(desc(PlatformAuditLog.timestamp))
                query = query.limit(limit)
                
                result = await session.execute(query)
                logs = result.scalars().all()
                
                return [log.to_dict() for log in logs]
                
        except Exception as e:
            logger.error(f"Failed to get security events: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check audit logger health"""
        try:
            if not self._initialized:
                return False
            
            # Test database connection
            async with self._db.get_session() as session:
                from sqlalchemy import select
                await session.execute(select(PlatformAuditLog).limit(1))
            
            return True
            
        except Exception as e:
            logger.error(f"Audit logger health check failed: {e}")
            return False

# Global instance
audit_logger = AuditLogger()

async def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance"""
    if not audit_logger._initialized:
        await audit_logger.initialize()
    return audit_logger
