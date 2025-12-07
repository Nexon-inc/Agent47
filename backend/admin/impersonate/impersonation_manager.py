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

class ImpersonationStatus(Enum):
    ACTIVE = "active"
    ENDED = "ended"
    EXPIRED = "expired"
    REVOKED = "revoked"

class ImpersonationReason(Enum):
    SUPPORT = "support"
    DEBUGGING = "debugging"
    TRAINING = "training"
    INVESTIGATION = "investigation"
    TESTING = "testing"

@dataclass
class ImpersonationSession:
    session_id: str
    admin_user_id: str
    target_user_id: str
    reason: ImpersonationReason
    status: ImpersonationStatus
    created_at: datetime
    expires_at: datetime
    ended_at: Optional[datetime]
    metadata: Dict[str, Any]

class ImpersonationManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.active_sessions = {}
        self.session_timeout_hours = 2
        self.max_concurrent_sessions = 5

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing ImpersonationManager...")
            self.database = get_database()
            await self._setup_impersonation_tables()
            await self._load_active_sessions()
            self.logger.info("ImpersonationManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize ImpersonationManager: {str(e)}")
            return False

    async def _setup_impersonation_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS impersonation_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    admin_user_id VARCHAR(255) NOT NULL,
                    target_user_id VARCHAR(255) NOT NULL,
                    reason VARCHAR(50) NOT NULL,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    ended_at TIMESTAMP,
                    metadata JSONB,
                    notes TEXT
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS impersonation_actions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    action_type VARCHAR(50) NOT NULL,
                    action_details JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS impersonation_audit_logs (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    admin_user_id VARCHAR(255) NOT NULL,
                    target_user_id VARCHAR(255) NOT NULL,
                    action VARCHAR(100) NOT NULL,
                    details JSONB,
                    ip_address INET,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_impersonation_sessions_admin 
                ON impersonation_sessions(admin_user_id)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_impersonation_sessions_target 
                ON impersonation_sessions(target_user_id)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_impersonation_sessions_status 
                ON impersonation_sessions(status)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_impersonation_audit_timestamp 
                ON impersonation_audit_logs(timestamp)
            """))
            
            await session.commit()

    async def _load_active_sessions(self):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT session_id, admin_user_id, target_user_id, reason, status,
                           created_at, expires_at, ended_at, metadata
                    FROM impersonation_sessions 
                    WHERE status = 'active' AND expires_at > CURRENT_TIMESTAMP
                """))
                
                for row in result.fetchall():
                    impersonation_session = ImpersonationSession(
                        session_id=row[0],
                        admin_user_id=row[1],
                        target_user_id=row[2],
                        reason=ImpersonationReason(row[3]),
                        status=ImpersonationStatus(row[4]),
                        created_at=row[5],
                        expires_at=row[6],
                        ended_at=row[7],
                        metadata=row[8] or {}
                    )
                    self.active_sessions[row[0]] = impersonation_session
        except Exception as e:
            self.logger.error(f"Failed to load active sessions: {str(e)}")

    async def start_impersonation(self, admin_user_id: str, target_user_id: str,
                                reason: ImpersonationReason, notes: str = None) -> Dict[str, Any]:
        if not self.database:
            return {"error": "Database not initialized"}
        
        if await self._has_active_session(admin_user_id):
            return {"error": "Admin already has an active impersonation session"}
        
        if await self._is_user_being_impersonated(target_user_id):
            return {"error": "User is already being impersonated"}
        
        if await self._get_admin_session_count(admin_user_id) >= self.max_concurrent_sessions:
            return {"error": "Maximum concurrent sessions reached"}
        
        session_id = f"imp_{admin_user_id}_{target_user_id}_{int(datetime.utcnow().timestamp())}"
        expires_at = datetime.utcnow() + timedelta(hours=self.session_timeout_hours)
        
        try:
            impersonation_session = ImpersonationSession(
                session_id=session_id,
                admin_user_id=admin_user_id,
                target_user_id=target_user_id,
                reason=reason,
                status=ImpersonationStatus.ACTIVE,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                ended_at=None,
                metadata={"notes": notes} if notes else {}
            )
            
            await self._save_session(impersonation_session)
            self.active_sessions[session_id] = impersonation_session
            
            await self._log_audit_action(session_id, admin_user_id, target_user_id, 
                                       "start_impersonation", {"reason": reason.value, "notes": notes})
            
            return {
                "success": True,
                "session_id": session_id,
                "target_user_id": target_user_id,
                "expires_at": expires_at.isoformat(),
                "message": "Impersonation session started successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start impersonation: {str(e)}")
            return {"error": str(e)}

    async def _save_session(self, session: ImpersonationSession):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session_db:
                await session_db.execute(text("""
                    INSERT INTO impersonation_sessions (
                        session_id, admin_user_id, target_user_id, reason, status,
                        created_at, expires_at, ended_at, metadata, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """), (
                    session.session_id,
                    session.admin_user_id,
                    session.target_user_id,
                    session.reason.value,
                    session.status.value,
                    session.created_at,
                    session.expires_at,
                    session.ended_at,
                    session.metadata,
                    session.metadata.get("notes")
                ))
                await session_db.commit()
        except Exception as e:
            self.logger.error(f"Failed to save session: {str(e)}")

    async def _has_active_session(self, admin_user_id: str) -> bool:
        if not self.database:
            return False
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM impersonation_sessions 
                    WHERE admin_user_id = %s AND status = 'active' AND expires_at > CURRENT_TIMESTAMP
                """), (admin_user_id,))
                
                count = result.scalar()
                return count > 0
        except Exception as e:
            self.logger.error(f"Failed to check active session: {str(e)}")
            return False

    async def _is_user_being_impersonated(self, target_user_id: str) -> bool:
        if not self.database:
            return False
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM impersonation_sessions 
                    WHERE target_user_id = %s AND status = 'active' AND expires_at > CURRENT_TIMESTAMP
                """), (target_user_id,))
                
                count = result.scalar()
                return count > 0
        except Exception as e:
            self.logger.error(f"Failed to check if user is being impersonated: {str(e)}")
            return False

    async def _get_admin_session_count(self, admin_user_id: str) -> int:
        if not self.database:
            return 0
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM impersonation_sessions 
                    WHERE admin_user_id = %s AND status = 'active'
                """), (admin_user_id,))
                
                return result.scalar()
        except Exception as e:
            self.logger.error(f"Failed to get admin session count: {str(e)}")
            return 0

    async def end_impersonation(self, session_id: str, admin_user_id: str, reason: str = None) -> bool:
        if session_id not in self.active_sessions:
            return False
        
        try:
            session = self.active_sessions[session_id]
            
            if session.admin_user_id != admin_user_id:
                return False
            
            session.status = ImpersonationStatus.ENDED
            session.ended_at = datetime.utcnow()
            
            await self._update_session(session)
            await self._log_audit_action(session_id, admin_user_id, session.target_user_id,
                                       "end_impersonation", {"reason": reason})
            
            del self.active_sessions[session_id]
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to end impersonation: {str(e)}")
            return False

    async def _update_session(self, session: ImpersonationSession):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session_db:
                await session_db.execute(text("""
                    UPDATE impersonation_sessions 
                    SET status = %s, ended_at = %s
                    WHERE session_id = %s
                """), (session.status.value, session.ended_at, session.session_id))
                await session_db.commit()
        except Exception as e:
            self.logger.error(f"Failed to update session: {str(e)}")

    async def get_impersonation_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        if session.expires_at < datetime.utcnow():
            session.status = ImpersonationStatus.EXPIRED
            await self._update_session(session)
            del self.active_sessions[session_id]
            return {"error": "Session has expired"}
        
        return {
            "session_id": session.session_id,
            "admin_user_id": session.admin_user_id,
            "target_user_id": session.target_user_id,
            "reason": session.reason.value,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "metadata": session.metadata
        }

    async def log_action(self, session_id: str, action_type: str, action_details: Dict[str, Any]) -> bool:
        if session_id not in self.active_sessions:
            return False
        
        try:
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO impersonation_actions (session_id, action_type, action_details)
                    VALUES (%s, %s, %s)
                """), (session_id, action_type, action_details))
                await session.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log action: {str(e)}")
            return False

    async def _log_audit_action(self, session_id: str, admin_user_id: str, target_user_id: str,
                              action: str, details: Dict[str, Any]):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO impersonation_audit_logs (
                        session_id, admin_user_id, target_user_id, action, details
                    ) VALUES (%s, %s, %s, %s, %s)
                """), (session_id, admin_user_id, target_user_id, action, details))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to log audit action: {str(e)}")

    async def get_admin_sessions(self, admin_user_id: str) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT session_id, target_user_id, reason, status, created_at, 
                           expires_at, ended_at, metadata
                    FROM impersonation_sessions 
                    WHERE admin_user_id = %s
                    ORDER BY created_at DESC
                """), (admin_user_id,))
                
                sessions = []
                for row in result.fetchall():
                    sessions.append({
                        "session_id": row[0],
                        "target_user_id": row[1],
                        "reason": row[2],
                        "status": row[3],
                        "created_at": row[4].isoformat(),
                        "expires_at": row[5].isoformat(),
                        "ended_at": row[6].isoformat() if row[6] else None,
                        "metadata": row[7]
                    })
                
                return sessions
        except Exception as e:
            self.logger.error(f"Failed to get admin sessions: {str(e)}")
            return []

    async def get_target_user_sessions(self, target_user_id: str) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT session_id, admin_user_id, reason, status, created_at, 
                           expires_at, ended_at, metadata
                    FROM impersonation_sessions 
                    WHERE target_user_id = %s
                    ORDER BY created_at DESC
                """), (target_user_id,))
                
                sessions = []
                for row in result.fetchall():
                    sessions.append({
                        "session_id": row[0],
                        "admin_user_id": row[1],
                        "reason": row[2],
                        "status": row[3],
                        "created_at": row[4].isoformat(),
                        "expires_at": row[5].isoformat(),
                        "ended_at": row[6].isoformat() if row[6] else None,
                        "metadata": row[7]
                    })
                
                return sessions
        except Exception as e:
            self.logger.error(f"Failed to get target user sessions: {str(e)}")
            return []

    async def get_session_actions(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT action_type, action_details, timestamp
                    FROM impersonation_actions 
                    WHERE session_id = %s
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """), (session_id, limit))
                
                actions = []
                for row in result.fetchall():
                    actions.append({
                        "action_type": row[0],
                        "action_details": row[1],
                        "timestamp": row[2].isoformat()
                    })
                
                return actions
        except Exception as e:
            self.logger.error(f"Failed to get session actions: {str(e)}")
            return []

    async def get_impersonation_statistics(self) -> Dict[str, Any]:
        if not self.database:
            return {}
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        COUNT(*) as total_sessions,
                        COUNT(*) FILTER (WHERE status = 'active') as active_sessions,
                        COUNT(*) FILTER (WHERE status = 'ended') as ended_sessions,
                        COUNT(*) FILTER (WHERE status = 'expired') as expired_sessions,
                        COUNT(DISTINCT admin_user_id) as unique_admins,
                        COUNT(DISTINCT target_user_id) as unique_targets,
                        AVG(EXTRACT(EPOCH FROM (ended_at - created_at))/3600) FILTER (WHERE ended_at IS NOT NULL) as avg_session_duration_hours
                    FROM impersonation_sessions 
                    WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
                """))
                
                row = result.fetchone()
                if row:
                    return {
                        "total_sessions": row[0],
                        "active_sessions": row[1],
                        "ended_sessions": row[2],
                        "expired_sessions": row[3],
                        "unique_admins": row[4],
                        "unique_targets": row[5],
                        "avg_session_duration_hours": row[6] or 0
                    }
                return {}
        except Exception as e:
            self.logger.error(f"Failed to get impersonation statistics: {str(e)}")
            return {}

    async def cleanup_expired_sessions(self):
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if session.expires_at < datetime.utcnow():
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            session = self.active_sessions[session_id]
            session.status = ImpersonationStatus.EXPIRED
            await self._update_session(session)
            await self._log_audit_action(session_id, session.admin_user_id, session.target_user_id,
                                       "session_expired", {"expired_at": datetime.utcnow().isoformat()})
            del self.active_sessions[session_id]

    async def revoke_session(self, session_id: str, admin_user_id: str, reason: str) -> bool:
        if session_id not in self.active_sessions:
            return False
        
        try:
            session = self.active_sessions[session_id]
            session.status = ImpersonationStatus.REVOKED
            session.ended_at = datetime.utcnow()
            
            await self._update_session(session)
            await self._log_audit_action(session_id, admin_user_id, session.target_user_id,
                                       "session_revoked", {"reason": reason})
            
            del self.active_sessions[session_id]
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to revoke session: {str(e)}")
            return False

    async def get_audit_logs(self, admin_user_id: str = None, target_user_id: str = None, 
                           limit: int = 100) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                query = """
                    SELECT session_id, admin_user_id, target_user_id, action, details, 
                           ip_address, user_agent, timestamp
                    FROM impersonation_audit_logs 
                """
                params = []
                
                conditions = []
                if admin_user_id:
                    conditions.append("admin_user_id = %s")
                    params.append(admin_user_id)
                
                if target_user_id:
                    conditions.append("target_user_id = %s")
                    params.append(target_user_id)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY timestamp DESC LIMIT %s"
                params.append(limit)
                
                result = await session.execute(text(query), params)
                
                logs = []
                for row in result.fetchall():
                    logs.append({
                        "session_id": row[0],
                        "admin_user_id": row[1],
                        "target_user_id": row[2],
                        "action": row[3],
                        "details": row[4],
                        "ip_address": row[5],
                        "user_agent": row[6],
                        "timestamp": row[7].isoformat()
                    })
                
                return logs
        except Exception as e:
            self.logger.error(f"Failed to get audit logs: {str(e)}")
            return []

    async def shutdown(self):
        self.logger.info("Shutting down ImpersonationManager...")
        await self.cleanup_expired_sessions()
        self.logger.info("ImpersonationManager shutdown complete")
