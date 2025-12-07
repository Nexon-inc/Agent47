import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text

from backend.core.database import get_database, DatabaseManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class SessionStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"

class SessionType(Enum):
    IMPERSONATION = "impersonation"
    SUPPORT = "support"
    DEBUGGING = "debugging"
    TRAINING = "training"
    INVESTIGATION = "investigation"

@dataclass
class SessionInfo:
    session_id: str
    admin_user_id: str
    target_user_id: str
    session_type: SessionType
    status: SessionStatus
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    metadata: Dict[str, Any]

@dataclass
class SessionActivity:
    activity_id: str
    session_id: str
    activity_type: str
    description: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    metadata: Dict[str, Any]

class SessionTracker(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.active_sessions: Dict[str, SessionInfo] = {}
        self.session_timeout_hours = 2
        self.max_concurrent_sessions = 10
        self.activity_retention_days = 90
        self.cleanup_interval_minutes = 30

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing SessionTracker...")
            self.database = get_database()
            await self._setup_session_tables()
            await self._load_active_sessions()
            await self._start_cleanup_task()
            self.logger.info("SessionTracker initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize SessionTracker: {str(e)}")
            return False

    async def _setup_session_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS impersonation_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    admin_user_id VARCHAR(255) NOT NULL,
                    target_user_id VARCHAR(255) NOT NULL,
                    session_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address INET NOT NULL,
                    user_agent TEXT,
                    metadata JSONB,
                    ended_at TIMESTAMP,
                    end_reason VARCHAR(100)
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS session_activities (
                    id SERIAL PRIMARY KEY,
                    activity_id VARCHAR(255) UNIQUE NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    activity_type VARCHAR(100) NOT NULL,
                    description TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address INET,
                    user_agent TEXT,
                    metadata JSONB,
                    FOREIGN KEY (session_id) REFERENCES impersonation_sessions(session_id)
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_impersonation_sessions_admin_user 
                ON impersonation_sessions(admin_user_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_impersonation_sessions_target_user 
                ON impersonation_sessions(target_user_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_impersonation_sessions_status 
                ON impersonation_sessions(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_impersonation_sessions_expires_at 
                ON impersonation_sessions(expires_at);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_activities_session_id 
                ON session_activities(session_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_activities_timestamp 
                ON session_activities(timestamp);
            """)
            
            await session.commit()

    async def _load_active_sessions(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT session_id, admin_user_id, target_user_id, session_type, status,
                       created_at, expires_at, last_activity, ip_address, user_agent, metadata
                FROM impersonation_sessions
                WHERE status = 'active' AND expires_at > CURRENT_TIMESTAMP
            """)
            
            for row in result:
                session_info = SessionInfo(
                    session_id=row.session_id,
                    admin_user_id=row.admin_user_id,
                    target_user_id=row.target_user_id,
                    session_type=SessionType(row.session_type),
                    status=SessionStatus(row.status),
                    created_at=row.created_at,
                    expires_at=row.expires_at,
                    last_activity=row.last_activity,
                    ip_address=row.ip_address,
                    user_agent=row.user_agent,
                    metadata=row.metadata or {}
                )
                self.active_sessions[session_info.session_id] = session_info

    async def _start_cleanup_task(self):
        asyncio.create_task(self._cleanup_expired_sessions())

    async def _cleanup_expired_sessions(self):
        while True:
            try:
                await self._cleanup_expired_sessions_internal()
                await asyncio.sleep(self.cleanup_interval_minutes * 60)
            except Exception as e:
                self.logger.error(f"Error in session cleanup task: {str(e)}")
                await asyncio.sleep(300)

    async def _cleanup_expired_sessions_internal(self):
        if not self.database:
            return
        
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session_info in self.active_sessions.items():
            if now > session_info.expires_at:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.terminate_session(session_id, "expired")
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    async def create_session(
        self,
        admin_user_id: str,
        target_user_id: str,
        session_type: SessionType,
        ip_address: str,
        user_agent: str,
        duration_hours: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        try:
            if len(self.active_sessions) >= self.max_concurrent_sessions:
                self.logger.warning("Maximum concurrent sessions reached")
                return None
            
            session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(admin_user_id) % 10000}"
            
            if duration_hours is None:
                duration_hours = self.session_timeout_hours
            
            expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
            
            session_info = SessionInfo(
                session_id=session_id,
                admin_user_id=admin_user_id,
                target_user_id=target_user_id,
                session_type=session_type,
                status=SessionStatus.ACTIVE,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                last_activity=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO impersonation_sessions (
                        session_id, admin_user_id, target_user_id, session_type, status,
                        expires_at, ip_address, user_agent, metadata
                    ) VALUES (
                        :session_id, :admin_user_id, :target_user_id, :session_type, :status,
                        :expires_at, :ip_address, :user_agent, :metadata
                    )
                """, {
                    "session_id": session_info.session_id,
                    "admin_user_id": session_info.admin_user_id,
                    "target_user_id": session_info.target_user_id,
                    "session_type": session_info.session_type.value,
                    "status": session_info.status.value,
                    "expires_at": session_info.expires_at,
                    "ip_address": session_info.ip_address,
                    "user_agent": session_info.user_agent,
                    "metadata": session_info.metadata
                })
                await session.commit()
            
            self.active_sessions[session_id] = session_info
            
            await self._log_activity(
                session_id, 
                "session_created", 
                f"Impersonation session created for user {target_user_id}",
                ip_address,
                user_agent
            )
            
            self.logger.info(f"Impersonation session created: {session_id}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to create session: {str(e)}")
            return None

    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        if session_id in self.active_sessions:
            session_info = self.active_sessions[session_id]
            if datetime.utcnow() > session_info.expires_at:
                await self.terminate_session(session_id, "expired")
                return None
            return session_info
        
        if not self.database:
            return None
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT session_id, admin_user_id, target_user_id, session_type, status,
                       created_at, expires_at, last_activity, ip_address, user_agent, metadata
                FROM impersonation_sessions
                WHERE session_id = :session_id
            """, {"session_id": session_id})
            
            row = result.fetchone()
            if not row:
                return None
            
            session_info = SessionInfo(
                session_id=row.session_id,
                admin_user_id=row.admin_user_id,
                target_user_id=row.target_user_id,
                session_type=SessionType(row.session_type),
                status=SessionStatus(row.status),
                created_at=row.created_at,
                expires_at=row.expires_at,
                last_activity=row.last_activity,
                ip_address=row.ip_address,
                user_agent=row.user_agent,
                metadata=row.metadata or {}
            )
            
            if session_info.status == SessionStatus.ACTIVE and datetime.utcnow() <= session_info.expires_at:
                self.active_sessions[session_id] = session_info
            
            return session_info

    async def update_activity(
        self,
        session_id: str,
        ip_address: str,
        user_agent: str
    ) -> bool:
        try:
            if session_id not in self.active_sessions:
                return False
            
            session_info = self.active_sessions[session_id]
            
            if datetime.utcnow() > session_info.expires_at:
                await self.terminate_session(session_id, "expired")
                return False
            
            session_info.last_activity = datetime.utcnow()
            session_info.ip_address = ip_address
            session_info.user_agent = user_agent
            
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE impersonation_sessions 
                    SET last_activity = :last_activity, ip_address = :ip_address, user_agent = :user_agent
                    WHERE session_id = :session_id
                """, {
                    "session_id": session_id,
                    "last_activity": session_info.last_activity,
                    "ip_address": ip_address,
                    "user_agent": user_agent
                })
                await session.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update session activity: {str(e)}")
            return False

    async def terminate_session(
        self,
        session_id: str,
        reason: str = "manual",
        terminated_by: Optional[str] = None
    ) -> bool:
        try:
            session_info = None
            if session_id in self.active_sessions:
                session_info = self.active_sessions[session_id]
                del self.active_sessions[session_id]
            
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE impersonation_sessions 
                    SET status = :status, ended_at = :ended_at, end_reason = :end_reason
                    WHERE session_id = :session_id
                """, {
                    "session_id": session_id,
                    "status": SessionStatus.TERMINATED.value,
                    "ended_at": datetime.utcnow(),
                    "end_reason": reason
                })
                await session.commit()
            
            if session_info:
                await self._log_activity(
                    session_id,
                    "session_terminated",
                    f"Session terminated: {reason}",
                    session_info.ip_address,
                    session_info.user_agent,
                    {"terminated_by": terminated_by, "reason": reason}
                )
            
            self.logger.info(f"Session terminated: {session_id} - {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to terminate session: {str(e)}")
            return False

    async def suspend_session(self, session_id: str, reason: str = "suspended") -> bool:
        try:
            if session_id not in self.active_sessions:
                return False
            
            session_info = self.active_sessions[session_id]
            session_info.status = SessionStatus.SUSPENDED
            
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE impersonation_sessions 
                    SET status = :status
                    WHERE session_id = :session_id
                """, {
                    "session_id": session_id,
                    "status": SessionStatus.SUSPENDED.value
                })
                await session.commit()
            
            await self._log_activity(
                session_id,
                "session_suspended",
                f"Session suspended: {reason}",
                session_info.ip_address,
                session_info.user_agent,
                {"reason": reason}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to suspend session: {str(e)}")
            return False

    async def resume_session(self, session_id: str) -> bool:
        try:
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT session_id, admin_user_id, target_user_id, session_type, status,
                           created_at, expires_at, last_activity, ip_address, user_agent, metadata
                    FROM impersonation_sessions
                    WHERE session_id = :session_id AND status = 'suspended'
                """, {"session_id": session_id})
                
                row = result.fetchone()
                if not row:
                    return False
                
                if datetime.utcnow() > row.expires_at:
                    await self.terminate_session(session_id, "expired")
                    return False
                
                await session.execute("""
                    UPDATE impersonation_sessions 
                    SET status = :status, last_activity = :last_activity
                    WHERE session_id = :session_id
                """, {
                    "session_id": session_id,
                    "status": SessionStatus.ACTIVE.value,
                    "last_activity": datetime.utcnow()
                })
                await session.commit()
                
                session_info = SessionInfo(
                    session_id=row.session_id,
                    admin_user_id=row.admin_user_id,
                    target_user_id=row.target_user_id,
                    session_type=SessionType(row.session_type),
                    status=SessionStatus.ACTIVE,
                    created_at=row.created_at,
                    expires_at=row.expires_at,
                    last_activity=datetime.utcnow(),
                    ip_address=row.ip_address,
                    user_agent=row.user_agent,
                    metadata=row.metadata or {}
                )
                
                self.active_sessions[session_id] = session_info
                
                await self._log_activity(
                    session_id,
                    "session_resumed",
                    "Session resumed",
                    session_info.ip_address,
                    session_info.user_agent
                )
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to resume session: {str(e)}")
            return False

    async def _log_activity(
        self,
        session_id: str,
        activity_type: str,
        description: str,
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        if not self.database:
            return
        
        try:
            activity_id = f"activity_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(session_id) % 10000}"
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO session_activities (
                        activity_id, session_id, activity_type, description, 
                        ip_address, user_agent, metadata
                    ) VALUES (
                        :activity_id, :session_id, :activity_type, :description, 
                        :ip_address, :user_agent, :metadata
                    )
                """, {
                    "activity_id": activity_id,
                    "session_id": session_id,
                    "activity_type": activity_type,
                    "description": description,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "metadata": metadata or {}
                })
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log session activity: {str(e)}")

    async def get_session_activities(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionActivity]:
        if not self.database:
            return []
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT activity_id, session_id, activity_type, description, 
                       timestamp, ip_address, user_agent, metadata
                FROM session_activities
                WHERE session_id = :session_id
                ORDER BY timestamp DESC
                LIMIT :limit OFFSET :offset
            """, {"session_id": session_id, "limit": limit, "offset": offset})
            
            activities = []
            for row in result:
                activity = SessionActivity(
                    activity_id=row.activity_id,
                    session_id=row.session_id,
                    activity_type=row.activity_type,
                    description=row.description,
                    timestamp=row.timestamp,
                    ip_address=row.ip_address,
                    user_agent=row.user_agent,
                    metadata=row.metadata or {}
                )
                activities.append(activity)
            
            return activities

    async def get_active_sessions(
        self,
        admin_user_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionInfo]:
        if not self.database:
            return []
        
        conditions = ["status = 'active'"]
        params = {"limit": limit, "offset": offset}
        
        if admin_user_id:
            conditions.append("admin_user_id = :admin_user_id")
            params["admin_user_id"] = admin_user_id
        
        if target_user_id:
            conditions.append("target_user_id = :target_user_id")
            params["target_user_id"] = target_user_id
        
        where_clause = "WHERE " + " AND ".join(conditions)
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT session_id, admin_user_id, target_user_id, session_type, status,
                       created_at, expires_at, last_activity, ip_address, user_agent, metadata
                FROM impersonation_sessions
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """, params)
            
            sessions = []
            for row in result:
                session_info = SessionInfo(
                    session_id=row.session_id,
                    admin_user_id=row.admin_user_id,
                    target_user_id=row.target_user_id,
                    session_type=SessionType(row.session_type),
                    status=SessionStatus(row.status),
                    created_at=row.created_at,
                    expires_at=row.expires_at,
                    last_activity=row.last_activity,
                    ip_address=row.ip_address,
                    user_agent=row.user_agent,
                    metadata=row.metadata or {}
                )
                sessions.append(session_info)
            
            return sessions

    async def get_session_stats(
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
                    COUNT(*) as total_sessions,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_sessions,
                    COUNT(CASE WHEN status = 'terminated' THEN 1 END) as terminated_sessions,
                    COUNT(CASE WHEN session_type = 'impersonation' THEN 1 END) as impersonation_sessions,
                    COUNT(CASE WHEN session_type = 'support' THEN 1 END) as support_sessions,
                    COUNT(CASE WHEN session_type = 'debugging' THEN 1 END) as debugging_sessions,
                    COUNT(DISTINCT admin_user_id) as unique_admins,
                    COUNT(DISTINCT target_user_id) as unique_targets,
                    AVG(EXTRACT(EPOCH FROM (COALESCE(ended_at, CURRENT_TIMESTAMP) - created_at))/3600) as avg_duration_hours
                FROM impersonation_sessions
                WHERE created_at BETWEEN :start_date AND :end_date
            """, {"start_date": start_date, "end_date": end_date})
            
            row = result.fetchone()
            if not row:
                return {}
            
            return {
                "total_sessions": row.total_sessions,
                "active_sessions": row.active_sessions,
                "terminated_sessions": row.terminated_sessions,
                "impersonation_sessions": row.impersonation_sessions,
                "support_sessions": row.support_sessions,
                "debugging_sessions": row.debugging_sessions,
                "unique_admins": row.unique_admins,
                "unique_targets": row.unique_targets,
                "avg_duration_hours": float(row.avg_duration_hours) if row.avg_duration_hours else 0.0
            }

    async def cleanup_old_activities(self):
        if not self.database:
            return
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.activity_retention_days)
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                DELETE FROM session_activities 
                WHERE timestamp < :cutoff_date
            """, {"cutoff_date": cutoff_date})
            
            deleted_count = result.rowcount
            await session.commit()
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old session activities")

_session_tracker: Optional[SessionTracker] = None

async def get_session_tracker() -> SessionTracker:
    global _session_tracker
    if _session_tracker is None:
        _session_tracker = SessionTracker()
        await _session_tracker.initialize()
    return _session_tracker

async def init_session_tracker() -> SessionTracker:
    return await get_session_tracker()
