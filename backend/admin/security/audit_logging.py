from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from core.database import get_database
from core.logs import get_logger
from core.config import get_settings
from core.cache import get_redis

class AuditEventType(Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ACCESS = "access"
    SECURITY_EVENT = "security_event"
    SYSTEM_CHANGE = "system_change"

class AuditSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"

@dataclass
class AuditEvent:
    id: str
    event_type: AuditEventType
    severity: AuditSeverity
    status: AuditStatus
    user_id: Optional[str]
    ip_address: str
    resource_type: str
    resource_id: str
    action: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)

class AuditLogging:
    def __init__(self):
        self.config = get_settings()
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()
    
    async def log_event(self, event_type: AuditEventType, severity: AuditSeverity, 
                       status: AuditStatus, user_id: Optional[str], ip_address: str,
                       resource_type: str, resource_id: str, action: str, 
                       details: Dict[str, Any]) -> AuditEvent:
        """Log an audit event"""
        try:
            event_id = f"audit_{datetime.utcnow().timestamp()}_{event_type.value}"
            
            event = AuditEvent(
                id=event_id,
                event_type=event_type,
                severity=severity,
                status=status,
                user_id=user_id,
                ip_address=ip_address,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                details=details
            )
            
            await self._store_audit_event(event)
            
            if severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
                await self._send_audit_alert(event)
            
            self.logger.info(f"Audit event logged: {event_type.value} - {action}")
            return event
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
            raise
    
    async def _store_audit_event(self, event: AuditEvent):
        """Store audit event in database"""
        try:
            await self.db.execute(
                """
                INSERT INTO audit_events 
                (id, event_type, severity, status, user_id, ip_address, resource_type, 
                resource_id, action, details, timestamp)
                VALUES (:id, :event_type, :severity, :status, :user_id, :ip_address, 
                :resource_type, :resource_id, :action, :details, :timestamp)
                    """,
                    {
                    "id": event.id,
                    "event_type": event.event_type.value,
                    "severity": event.severity.value,
                    "status": event.status.value,
                    "user_id": event.user_id,
                    "ip_address": event.ip_address,
                    "resource_type": event.resource_type,
                    "resource_id": event.resource_id,
                    "action": event.action,
                    "details": event.details,
                    "timestamp": event.timestamp
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to store audit event: {e}")
            raise
    
    async def _send_audit_alert(self, event: AuditEvent):
        """Send audit alert for high severity events"""
        try:
            alert_data = {
                "type": "audit_alert",
                "event_id": event.id,
                "severity": event.severity.value,
                "action": event.action,
                "timestamp": event.timestamp.isoformat()
            }
            await self.redis.publish("admin:audit_alerts", alert_data)
        except Exception as e:
            self.logger.error(f"Failed to send audit alert: {e}")
    
    async def get_audit_events(self, user_id: Optional[str] = None, 
                             event_type: Optional[AuditEventType] = None,
                             days: int = 30, limit: int = 100) -> List[AuditEvent]:
        """Get audit events with filtering"""
        try:
            query = "SELECT * FROM audit_events WHERE timestamp >= :since"
            params = {"since": datetime.utcnow() - timedelta(days=days)}
            
            if user_id:
                query += " AND user_id = :user_id"
                params["user_id"] = user_id
            
            if event_type:
                query += " AND event_type = :event_type"
                params["event_type"] = event_type.value
            
            query += " ORDER BY timestamp DESC LIMIT :limit"
            params["limit"] = limit
            
            rows = await self.db.fetch_all(query, params)
            
            events = []
            for row in rows:
                event = AuditEvent(
                    id=row["id"],
                    event_type=AuditEventType(row["event_type"]),
                    severity=AuditSeverity(row["severity"]),
                    status=AuditStatus(row["status"]),
                    user_id=row["user_id"],
                    ip_address=row["ip_address"],
                    resource_type=row["resource_type"],
                    resource_id=row["resource_id"],
                    action=row["action"],
                    details=row["details"],
                    timestamp=row["timestamp"]
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get audit events: {e}")
            return []
    
    async def get_security_events(self, days: int = 7) -> List[AuditEvent]:
        """Get security-related audit events"""
        return await self.get_audit_events(
            event_type=AuditEventType.SECURITY_EVENT, 
            days=days, 
            limit=500
        )
    
    async def cleanup_old_logs(self, days: int = 365):
        """Clean up old audit logs"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            await self.db.execute(
                "DELETE FROM audit_events WHERE timestamp < :cutoff_date",
                {"cutoff_date": cutoff_date}
            )
            self.logger.info(f"Cleaned up audit logs older than {days} days")
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")

# Singleton instance
_audit_logging = None

def get_audit_logging() -> AuditLogging:
    global _audit_logging
    if _audit_logging is None:
        _audit_logging = AuditLogging()
    return _audit_logging

def init_audit_logging():
    """Initialize audit logging system"""
    global _audit_logging
    _audit_logging = AuditLogging()
    return _audit_logging
