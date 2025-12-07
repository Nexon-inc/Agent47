from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from ..database.models import IntegrationAuditLog, IntegrationAuditAction, IntegrationAuditSeverity

logger = logging.getLogger(__name__)

class IntegrationAuditLogger:
    """Manages audit logging for integration access and security events"""
    
    def __init__(self):
        self._initialized = False
        self._db = None
    
    async def initialize(self):
        """Initialize integration audit logger"""
        if self._initialized:
            return
        
        try:
            from ..database.connection import get_database
            self._db = get_database()
            self._initialized = True
            
            logger.info("Integration audit logger initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize integration audit logger: {e}")
            raise
    
    async def log_action(
        self,
        user_id: int,
        integration_name: str,
        action: IntegrationAuditAction,
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
        severity: IntegrationAuditSeverity = None
    ) -> bool:
        """Log an integration audit event"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self._db.get_session() as session:
                # Determine severity if not provided
                if not severity:
                    if not success:
                        severity = IntegrationAuditSeverity.HIGH
                    elif action in [IntegrationAuditAction.CREDENTIALS_STORED, IntegrationAuditAction.INTEGRATION_CONNECTED]:
                        severity = IntegrationAuditSeverity.MEDIUM
                    else:
                        severity = IntegrationAuditSeverity.LOW
                
                # Create audit log entry
                audit_log = IntegrationAuditLog(
                    user_id=user_id,
                    integration_name=integration_name,
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
                
                logger.debug(f"Integration audit log created: {action.value} for user {user_id}, integration {integration_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to log integration audit action: {e}")
            return False
    
    async def log_credentials_stored(
        self,
        user_id: int,
        integration_name: str,
        scopes: List[str],
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """Log credentials storage event"""
        return await self.log_action(
            user_id=user_id,
            integration_name=integration_name,
            action=IntegrationAuditAction.CREDENTIALS_STORED,
            description=f"Stored credentials for {integration_name} with scopes: {', '.join(scopes)}",
            success=True,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            scopes_used=scopes,
            severity=IntegrationAuditSeverity.MEDIUM
        )
    
    async def log_integration_accessed(
        self,
        user_id: int,
        integration_name: str,
        agent_name: str,
        scopes_used: List[str],
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        duration_ms: int = None
    ) -> bool:
        """Log integration access event"""
        return await self.log_action(
            user_id=user_id,
            integration_name=integration_name,
            action=IntegrationAuditAction.INTEGRATION_ACCESSED,
            description=f"Agent {agent_name} accessed {integration_name} integration",
            success=True,
            agent_name=agent_name,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            scopes_used=scopes_used,
            duration_ms=duration_ms,
            severity=IntegrationAuditSeverity.LOW
        )
    
    async def log_api_call(
        self,
        user_id: int,
        integration_name: str,
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
            integration_name=integration_name,
            action=IntegrationAuditAction.API_CALL_MADE,
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
            severity=IntegrationAuditSeverity.HIGH if not success else IntegrationAuditSeverity.LOW
        )
    
    async def log_integration_connected(
        self,
        user_id: int,
        integration_name: str,
        scopes: List[str],
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """Log integration connection event"""
        return await self.log_action(
            user_id=user_id,
            integration_name=integration_name,
            action=IntegrationAuditAction.INTEGRATION_CONNECTED,
            description=f"User connected to {integration_name} with scopes: {', '.join(scopes)}",
            success=True,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            scopes_used=scopes,
            severity=IntegrationAuditSeverity.MEDIUM
        )
    
    async def log_integration_disconnected(
        self,
        user_id: int,
        integration_name: str,
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """Log integration disconnection event"""
        return await self.log_action(
            user_id=user_id,
            integration_name=integration_name,
            action=IntegrationAuditAction.INTEGRATION_DISCONNECTED,
            description=f"User disconnected from {integration_name}",
            success=True,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=IntegrationAuditSeverity.MEDIUM
        )
    
    async def log_security_event(
        self,
        user_id: int,
        integration_name: str,
        description: str,
        severity: IntegrationAuditSeverity = IntegrationAuditSeverity.HIGH,
        metadata: Dict[str, Any] = None,
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """Log security-related event"""
        return await self.log_action(
            user_id=user_id,
            integration_name=integration_name,
            action=IntegrationAuditAction.INTEGRATION_ACCESSED,  # Generic action for security events
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
        integration_name: str = None,
        action: IntegrationAuditAction = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get audit logs for a user"""
        if not self._initialized:
            await self.initialize()
        
        try:
            from sqlalchemy import select, and_, desc
            
            async with self._db.get_session() as session:
                query = select(IntegrationAuditLog).where(
                    IntegrationAuditLog.user_id == user_id
                )
                
                if integration_name:
                    query = query.where(IntegrationAuditLog.integration_name == integration_name)
                
                if action:
                    query = query.where(IntegrationAuditLog.action == action)
                
                query = query.order_by(desc(IntegrationAuditLog.timestamp))
                query = query.offset(offset).limit(limit)
                
                result = await session.execute(query)
                logs = result.scalars().all()
                
                return [log.to_dict() for log in logs]
                
        except Exception as e:
            logger.error(f"Failed to get audit logs for user {user_id}: {e}")
            return []
    
    async def get_security_events(
        self,
        severity: IntegrationAuditSeverity = None,
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
                
                query = select(IntegrationAuditLog).where(
                    and_(
                        IntegrationAuditLog.timestamp >= cutoff_time,
                        IntegrationAuditLog.severity.in_([IntegrationAuditSeverity.HIGH, IntegrationAuditSeverity.CRITICAL])
                    )
                )
                
                if severity:
                    query = query.where(IntegrationAuditLog.severity == severity)
                
                query = query.order_by(desc(IntegrationAuditLog.timestamp))
                query = query.limit(limit)
                
                result = await session.execute(query)
                logs = result.scalars().all()
                
                return [log.to_dict() for log in logs]
                
        except Exception as e:
            logger.error(f"Failed to get security events: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check integration audit logger health"""
        try:
            if not self._initialized:
                return False
            
            # Test database connection
            async with self._db.get_session() as session:
                from sqlalchemy import select
                await session.execute(select(IntegrationAuditLog).limit(1))
            
            return True
            
        except Exception as e:
            logger.error(f"Integration audit logger health check failed: {e}")
            return False

# Global instance
integration_audit_logger = IntegrationAuditLogger()

async def get_integration_audit_logger() -> IntegrationAuditLogger:
    """Get the global integration audit logger instance"""
    if not integration_audit_logger._initialized:
        await integration_audit_logger.initialize()
    return integration_audit_logger
