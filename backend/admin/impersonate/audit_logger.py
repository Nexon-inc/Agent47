import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text

from core.database import get_database, DatabaseManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class AuditEventType(Enum):
    SESSION_CREATED = "session_created"
    SESSION_TERMINATED = "session_terminated"
    SESSION_SUSPENDED = "session_suspended"
    SESSION_RESUMED = "session_resumed"
    USER_ACCESS = "user_access"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    PERMISSION_CHANGE = "permission_change"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"
    SYSTEM_EVENT = "system_event"

class AuditSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    INFO = "info"

@dataclass
class AuditEvent:
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    status: AuditStatus
    admin_user_id: str
    target_user_id: Optional[str]
    session_id: Optional[str]
    description: str
    details: Dict[str, Any]
    ip_address: str
    user_agent: str
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class AuditQuery:
    query_id: str
    event_types: List[AuditEventType]
    severity_levels: List[AuditSeverity]
    admin_user_ids: List[str]
    target_user_ids: List[str]
    start_date: datetime
    end_date: datetime
    limit: int
    offset: int

class AuditLogger(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.retention_days = 365
        self.cleanup_interval_hours = 24
        self.batch_size = 1000
        self.event_queue: List[AuditEvent] = []
        self.queue_lock = asyncio.Lock()

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing AuditLogger...")
            self.database = get_database()
            await self._setup_audit_tables()
            await self._start_cleanup_task()
            await self._start_batch_processor()
            self.logger.info("AuditLogger initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize AuditLogger: {str(e)}")
            return False

    async def _setup_audit_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(255) UNIQUE NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    admin_user_id VARCHAR(255) NOT NULL,
                    target_user_id VARCHAR(255),
                    session_id VARCHAR(255),
                    description TEXT NOT NULL,
                    details JSONB NOT NULL,
                    ip_address INET NOT NULL,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS audit_queries (
                    id SERIAL PRIMARY KEY,
                    query_id VARCHAR(255) UNIQUE NOT NULL,
                    event_types JSONB NOT NULL,
                    severity_levels JSONB NOT NULL,
                    admin_user_ids JSONB,
                    target_user_ids JSONB,
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    limit_count INTEGER NOT NULL,
                    offset_count INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(255) NOT NULL
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_events_event_type 
                ON audit_events(event_type);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_events_severity 
                ON audit_events(severity);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_events_admin_user_id 
                ON audit_events(admin_user_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_events_target_user_id 
                ON audit_events(target_user_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_events_session_id 
                ON audit_events(session_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp 
                ON audit_events(timestamp);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_events_ip_address 
                ON audit_events(ip_address);
            """)
            
            await session.commit()

    async def _start_cleanup_task(self):
        asyncio.create_task(self._cleanup_old_events())

    async def _start_batch_processor(self):
        asyncio.create_task(self._process_event_queue())

    async def _cleanup_old_events(self):
        while True:
            try:
                await self._cleanup_old_events_internal()
                await asyncio.sleep(self.cleanup_interval_hours * 3600)
            except Exception as e:
                self.logger.error(f"Error in audit cleanup task: {str(e)}")
                await asyncio.sleep(3600)

    async def _process_event_queue(self):
        while True:
            try:
                await self._process_event_batch()
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"Error in audit batch processor: {str(e)}")
                await asyncio.sleep(30)

    async def _cleanup_old_events_internal(self):
        if not self.database:
            return
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                DELETE FROM audit_events 
                WHERE timestamp < :cutoff_date
            """, {"cutoff_date": cutoff_date})
            
            deleted_count = result.rowcount
            await session.commit()
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old audit events")

    async def _process_event_batch(self):
        if not self.event_queue:
            return
        
        async with self.queue_lock:
            if not self.event_queue:
                return
            
            batch = self.event_queue[:self.batch_size]
            self.event_queue = self.event_queue[self.batch_size:]
        
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                for event in batch:
                    await session.execute("""
                        INSERT INTO audit_events (
                            event_id, event_type, severity, status, admin_user_id, target_user_id,
                            session_id, description, details, ip_address, user_agent, metadata
                        ) VALUES (
                            :event_id, :event_type, :severity, :status, :admin_user_id, :target_user_id,
                            :session_id, :description, :details, :ip_address, :user_agent, :metadata
                        )
                    """, {
                        "event_id": event.event_id,
                        "event_type": event.event_type.value,
                        "severity": event.severity.value,
                        "status": event.status.value,
                        "admin_user_id": event.admin_user_id,
                        "target_user_id": event.target_user_id,
                        "session_id": event.session_id,
                        "description": event.description,
                        "details": event.details,
                        "ip_address": event.ip_address,
                        "user_agent": event.user_agent,
                        "metadata": event.metadata
                    })
                
                await session.commit()
                self.logger.debug(f"Processed batch of {len(batch)} audit events")
                
        except Exception as e:
            self.logger.error(f"Failed to process audit event batch: {str(e)}")
            async with self.queue_lock:
                self.event_queue.extend(batch)

    async def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        status: AuditStatus,
        admin_user_id: str,
        description: str,
        details: Dict[str, Any],
        ip_address: str,
        user_agent: str,
        target_user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        event_id = f"audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(admin_user_id) % 10000}"
        
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            status=status,
            admin_user_id=admin_user_id,
            target_user_id=target_user_id,
            session_id=session_id,
            description=description,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        async with self.queue_lock:
            self.event_queue.append(event)
        
        if severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
            self.logger.warning(f"High severity audit event: {event_type.value} - {description}")
        
        return event_id

    async def log_session_event(
        self,
        event_type: AuditEventType,
        admin_user_id: str,
        target_user_id: str,
        session_id: str,
        description: str,
        details: Dict[str, Any],
        ip_address: str,
        user_agent: str,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        status: AuditStatus = AuditStatus.SUCCESS
    ) -> str:
        return await self.log_event(
            event_type=event_type,
            severity=severity,
            status=status,
            admin_user_id=admin_user_id,
            description=description,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            target_user_id=target_user_id,
            session_id=session_id,
            metadata={"session_event": True}
        )

    async def log_data_access(
        self,
        admin_user_id: str,
        target_user_id: str,
        data_type: str,
        action: str,
        ip_address: str,
        user_agent: str,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        return await self.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.MEDIUM,
            status=AuditStatus.SUCCESS,
            admin_user_id=admin_user_id,
            description=f"Data access: {action} {data_type} for user {target_user_id}",
            details=details or {"data_type": data_type, "action": action},
            ip_address=ip_address,
            user_agent=user_agent,
            target_user_id=target_user_id,
            session_id=session_id,
            metadata={"data_access": True}
        )

    async def log_data_modification(
        self,
        admin_user_id: str,
        target_user_id: str,
        data_type: str,
        action: str,
        changes: Dict[str, Any],
        ip_address: str,
        user_agent: str,
        session_id: Optional[str] = None
    ) -> str:
        return await self.log_event(
            event_type=AuditEventType.DATA_MODIFICATION,
            severity=AuditSeverity.HIGH,
            status=AuditStatus.SUCCESS,
            admin_user_id=admin_user_id,
            description=f"Data modification: {action} {data_type} for user {target_user_id}",
            details={"data_type": data_type, "action": action, "changes": changes},
            ip_address=ip_address,
            user_agent=user_agent,
            target_user_id=target_user_id,
            session_id=session_id,
            metadata={"data_modification": True}
        )

    async def log_security_event(
        self,
        admin_user_id: str,
        event_description: str,
        severity: AuditSeverity,
        details: Dict[str, Any],
        ip_address: str,
        user_agent: str,
        target_user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        return await self.log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            severity=severity,
            status=AuditStatus.WARNING if severity == AuditSeverity.HIGH else AuditStatus.INFO,
            admin_user_id=admin_user_id,
            description=event_description,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            target_user_id=target_user_id,
            session_id=session_id,
            metadata={"security_event": True}
        )

    async def query_events(
        self,
        event_types: Optional[List[AuditEventType]] = None,
        severity_levels: Optional[List[AuditSeverity]] = None,
        admin_user_ids: Optional[List[str]] = None,
        target_user_ids: Optional[List[str]] = None,
        session_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[AuditEvent]:
        if not self.database:
            return []
        
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if event_types:
            conditions.append("event_type = ANY(:event_types)")
            params["event_types"] = [et.value for et in event_types]
        
        if severity_levels:
            conditions.append("severity = ANY(:severity_levels)")
            params["severity_levels"] = [sl.value for sl in severity_levels]
        
        if admin_user_ids:
            conditions.append("admin_user_id = ANY(:admin_user_ids)")
            params["admin_user_ids"] = admin_user_ids
        
        if target_user_ids:
            conditions.append("target_user_id = ANY(:target_user_ids)")
            params["target_user_ids"] = target_user_ids
        
        if session_ids:
            conditions.append("session_id = ANY(:session_ids)")
            params["session_ids"] = session_ids
        
        if start_date:
            conditions.append("timestamp >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            conditions.append("timestamp <= :end_date")
            params["end_date"] = end_date
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT event_id, event_type, severity, status, admin_user_id, target_user_id,
                       session_id, description, details, ip_address, user_agent, timestamp, metadata
                FROM audit_events
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT :limit OFFSET :offset
            """, params)
            
            events = []
            for row in result:
                event = AuditEvent(
                    event_id=row.event_id,
                    event_type=AuditEventType(row.event_type),
                    severity=AuditSeverity(row.severity),
                    status=AuditStatus(row.status),
                    admin_user_id=row.admin_user_id,
                    target_user_id=row.target_user_id,
                    session_id=row.session_id,
                    description=row.description,
                    details=row.details or {},
                    ip_address=row.ip_address,
                    user_agent=row.user_agent,
                    timestamp=row.timestamp,
                    metadata=row.metadata or {}
                )
                events.append(event)
            
            return events

    async def get_audit_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if not self.database:
            return {}
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT 
                    COUNT(*) as total_events,
                    COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_events,
                    COUNT(CASE WHEN severity = 'high' THEN 1 END) as high_events,
                    COUNT(CASE WHEN severity = 'medium' THEN 1 END) as medium_events,
                    COUNT(CASE WHEN severity = 'low' THEN 1 END) as low_events,
                    COUNT(CASE WHEN event_type = 'session_created' THEN 1 END) as session_created,
                    COUNT(CASE WHEN event_type = 'session_terminated' THEN 1 END) as session_terminated,
                    COUNT(CASE WHEN event_type = 'data_access' THEN 1 END) as data_access,
                    COUNT(CASE WHEN event_type = 'data_modification' THEN 1 END) as data_modification,
                    COUNT(CASE WHEN event_type = 'security_event' THEN 1 END) as security_events,
                    COUNT(DISTINCT admin_user_id) as unique_admins,
                    COUNT(DISTINCT target_user_id) as unique_targets
                FROM audit_events
                WHERE timestamp BETWEEN :start_date AND :end_date
            """, {"start_date": start_date, "end_date": end_date})
            
            row = result.fetchone()
            if not row:
                return {}
            
            return {
                "total_events": row.total_events,
                "critical_events": row.critical_events,
                "high_events": row.high_events,
                "medium_events": row.medium_events,
                "low_events": row.low_events,
                "session_created": row.session_created,
                "session_terminated": row.session_terminated,
                "data_access": row.data_access,
                "data_modification": row.data_modification,
                "security_events": row.security_events,
                "unique_admins": row.unique_admins,
                "unique_targets": row.unique_targets
            }

    async def get_user_audit_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        if not self.database:
            return {}
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT 
                    COUNT(*) as total_events,
                    COUNT(CASE WHEN admin_user_id = :user_id THEN 1 END) as as_admin,
                    COUNT(CASE WHEN target_user_id = :user_id THEN 1 END) as as_target,
                    COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_events,
                    COUNT(CASE WHEN severity = 'high' THEN 1 END) as high_events,
                    COUNT(CASE WHEN event_type = 'data_access' THEN 1 END) as data_access,
                    COUNT(CASE WHEN event_type = 'data_modification' THEN 1 END) as data_modification,
                    MAX(timestamp) as last_activity
                FROM audit_events
                WHERE (admin_user_id = :user_id OR target_user_id = :user_id)
                AND timestamp >= :start_date
            """, {"user_id": user_id, "start_date": start_date})
            
            row = result.fetchone()
            if not row:
                return {}
            
            return {
                "user_id": user_id,
                "total_events": row.total_events,
                "as_admin": row.as_admin,
                "as_target": row.as_target,
                "critical_events": row.critical_events,
                "high_events": row.high_events,
                "data_access": row.data_access,
                "data_modification": row.data_modification,
                "last_activity": row.last_activity.isoformat() if row.last_activity else None
            }

    async def export_audit_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        events = await self.query_events(
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        stats = await self.get_audit_stats(start_date, end_date)
        
        export_data = {
            "export_info": {
                "generated_at": datetime.utcnow().isoformat(),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "format": format,
                "total_events": len(events)
            },
            "statistics": stats,
            "events": [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "severity": event.severity.value,
                    "status": event.status.value,
                    "admin_user_id": event.admin_user_id,
                    "target_user_id": event.target_user_id,
                    "session_id": event.session_id,
                    "description": event.description,
                    "details": event.details,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "timestamp": event.timestamp.isoformat(),
                    "metadata": event.metadata
                }
                for event in events
            ]
        }
        
        return export_data

_audit_logger: Optional[AuditLogger] = None

async def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
        await _audit_logger.initialize()
    return _audit_logger

async def init_audit_logger() -> AuditLogger:
    return await get_audit_logger()
