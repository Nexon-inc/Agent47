import asyncio
import uuid
import json
from typing import Dict, Any, List, Optional, Set
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
    IDLE = "idle"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    EXPIRED = "expired"

class SessionType(Enum):
    TERMINAL = "terminal"
    SSH = "ssh"
    WEB_CONSOLE = "web_console"
    API = "api"
    BATCH = "batch"

class SessionPermission(Enum):
    READ_ONLY = "read_only"
    EXECUTE = "execute"
    ADMIN = "admin"
    ROOT = "root"

@dataclass
class TerminalSession:
    session_id: str
    user_id: str
    session_type: SessionType
    status: SessionStatus
    permissions: List[SessionPermission]
    host: str
    port: int
    working_directory: str
    environment_vars: Dict[str, str]
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    max_idle_minutes: int
    command_history: List[str]
    output_buffer: str
    metadata: Dict[str, Any]

@dataclass
class SessionCommand:
    command_id: str
    session_id: str
    command: str
    executed_at: datetime
    exit_code: Optional[int]
    duration_seconds: Optional[int]
    output: str
    error: str
    metadata: Dict[str, Any]

@dataclass
class SessionEvent:
    event_id: str
    session_id: str
    event_type: str
    description: str
    timestamp: datetime
    metadata: Dict[str, Any]

class TerminalSessionManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.active_sessions: Dict[str, TerminalSession] = {}
        self.session_connections: Dict[str, Any] = {}
        self.user_sessions: Dict[str, Set[str]] = {}
        self.session_timeouts: Dict[str, datetime] = {}
        self.max_sessions_per_user = 5
        self.default_session_timeout_minutes = 60
        self.max_idle_minutes = 30
        self.cleanup_interval_minutes = 5

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing TerminalSessionManager...")
            self.database = get_database()
            await self._setup_session_tables()
            await self._load_active_sessions()
            await self._start_background_tasks()
            self.logger.info("TerminalSessionManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize TerminalSessionManager: {str(e)}")
            return False

    async def _setup_session_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS terminal_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    user_id VARCHAR(255) NOT NULL,
                    session_type VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    permissions JSONB DEFAULT '[]'::jsonb,
                    host VARCHAR(255) NOT NULL,
                    port INTEGER NOT NULL,
                    working_directory VARCHAR(500) NOT NULL,
                    environment_vars JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    max_idle_minutes INTEGER DEFAULT 30,
                    command_history JSONB DEFAULT '[]'::jsonb,
                    output_buffer TEXT,
                    metadata JSONB DEFAULT '{}'::jsonb
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS session_commands (
                    id SERIAL PRIMARY KEY,
                    command_id VARCHAR(255) UNIQUE NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    command TEXT NOT NULL,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    exit_code INTEGER,
                    duration_seconds INTEGER,
                    output TEXT,
                    error TEXT,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    FOREIGN KEY (session_id) REFERENCES terminal_sessions(session_id)
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS session_events (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(255) UNIQUE NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    description TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    FOREIGN KEY (session_id) REFERENCES terminal_sessions(session_id)
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_sessions_user_id 
                ON terminal_sessions(user_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_sessions_status 
                ON terminal_sessions(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_sessions_expires_at 
                ON terminal_sessions(expires_at);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_sessions_last_activity 
                ON terminal_sessions(last_activity);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_commands_session_id 
                ON session_commands(session_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_commands_executed_at 
                ON session_commands(executed_at);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_events_session_id 
                ON session_events(session_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_events_timestamp 
                ON session_events(timestamp);
            """)
            
            await session.commit()

    async def _load_active_sessions(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT session_id, user_id, session_type, status, permissions, host, port,
                       working_directory, environment_vars, created_at, last_activity, expires_at,
                       max_idle_minutes, command_history, output_buffer, metadata
                FROM terminal_sessions
                WHERE status IN ('active', 'idle') AND expires_at > CURRENT_TIMESTAMP
            """)
            
            for row in result:
                terminal_session = TerminalSession(
                    session_id=row.session_id,
                    user_id=row.user_id,
                    session_type=SessionType(row.session_type),
                    status=SessionStatus(row.status),
                    permissions=[SessionPermission(p) for p in row.permissions],
                    host=row.host,
                    port=row.port,
                    working_directory=row.working_directory,
                    environment_vars=row.environment_vars or {},
                    created_at=row.created_at,
                    last_activity=row.last_activity,
                    expires_at=row.expires_at,
                    max_idle_minutes=row.max_idle_minutes,
                    command_history=row.command_history or [],
                    output_buffer=row.output_buffer or "",
                    metadata=row.metadata or {}
                )
                self.active_sessions[row.session_id] = terminal_session
                
                if row.user_id not in self.user_sessions:
                    self.user_sessions[row.user_id] = set()
                self.user_sessions[row.user_id].add(row.session_id)

    async def _start_background_tasks(self):
        asyncio.create_task(self._session_cleanup_task())
        asyncio.create_task(self._idle_session_monitor())

    async def _session_cleanup_task(self):
        while True:
            try:
                await self._cleanup_expired_sessions()
                await asyncio.sleep(self.cleanup_interval_minutes * 60)
            except Exception as e:
                self.logger.error(f"Error in session cleanup task: {str(e)}")
                await asyncio.sleep(300)

    async def _idle_session_monitor(self):
        while True:
            try:
                await self._check_idle_sessions()
                await asyncio.sleep(60)
            except Exception as e:
                self.logger.error(f"Error in idle session monitor: {str(e)}")
                await asyncio.sleep(60)

    async def _cleanup_expired_sessions(self):
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if now > session.expires_at:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.terminate_session(session_id, "expired")
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    async def _check_idle_sessions(self):
        now = datetime.utcnow()
        idle_sessions = []
        
        for session_id, session in self.active_sessions.items():
            idle_time = now - session.last_activity
            if idle_time > timedelta(minutes=session.max_idle_minutes):
                idle_sessions.append(session_id)
        
        for session_id in idle_sessions:
            await self.suspend_session(session_id, "idle_timeout")

    async def create_session(
        self,
        user_id: str,
        session_type: SessionType,
        permissions: List[SessionPermission],
        host: str = "localhost",
        port: int = 22,
        working_directory: str = "/tmp",
        environment_vars: Optional[Dict[str, str]] = None,
        session_timeout_minutes: Optional[int] = None,
        max_idle_minutes: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        try:
            if user_id in self.user_sessions and len(self.user_sessions[user_id]) >= self.max_sessions_per_user:
                self.logger.warning(f"User {user_id} has reached maximum session limit")
                return None
            
            session_id = str(uuid.uuid4())
            
            if session_timeout_minutes is None:
                session_timeout_minutes = self.default_session_timeout_minutes
            if max_idle_minutes is None:
                max_idle_minutes = self.max_idle_minutes
            
            expires_at = datetime.utcnow() + timedelta(minutes=session_timeout_minutes)
            
            session = TerminalSession(
                session_id=session_id,
                user_id=user_id,
                session_type=session_type,
                status=SessionStatus.ACTIVE,
                permissions=permissions,
                host=host,
                port=port,
                working_directory=working_directory,
                environment_vars=environment_vars or {},
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                expires_at=expires_at,
                max_idle_minutes=max_idle_minutes,
                command_history=[],
                output_buffer="",
                metadata=metadata or {}
            )
            
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            async with self.database.get_session() as session_db:
                await session_db.execute("""
                    INSERT INTO terminal_sessions (
                        session_id, user_id, session_type, status, permissions, host, port,
                        working_directory, environment_vars, expires_at, max_idle_minutes, metadata
                    ) VALUES (
                        :session_id, :user_id, :session_type, :status, :permissions, :host, :port,
                        :working_directory, :environment_vars, :expires_at, :max_idle_minutes, :metadata
                    )
                """, {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "session_type": session.session_type.value,
                    "status": session.status.value,
                    "permissions": [p.value for p in session.permissions],
                    "host": session.host,
                    "port": session.port,
                    "working_directory": session.working_directory,
                    "environment_vars": session.environment_vars,
                    "expires_at": session.expires_at,
                    "max_idle_minutes": session.max_idle_minutes,
                    "metadata": session.metadata
                })
                await session_db.commit()
            
            self.active_sessions[session_id] = session
            
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = set()
            self.user_sessions[user_id].add(session_id)
            
            await self._log_session_event(session_id, "session_created", "Terminal session created")
            
            self.logger.info(f"Terminal session created: {session_id}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to create session: {str(e)}")
            return None

    async def get_session(self, session_id: str) -> Optional[TerminalSession]:
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                if datetime.utcnow() > session.expires_at:
                    await self.terminate_session(session_id, "expired")
                    return None
                return session
            
            if not self.database:
                return None
            
            async with self.database.get_session() as session_db:
                result = await session_db.execute("""
                    SELECT session_id, user_id, session_type, status, permissions, host, port,
                           working_directory, environment_vars, created_at, last_activity, expires_at,
                           max_idle_minutes, command_history, output_buffer, metadata
                    FROM terminal_sessions
                    WHERE session_id = :session_id
                """, {"session_id": session_id})
                
                row = result.fetchone()
                if not row:
                    return None
                
                session = TerminalSession(
                    session_id=row.session_id,
                    user_id=row.user_id,
                    session_type=SessionType(row.session_type),
                    status=SessionStatus(row.status),
                    permissions=[SessionPermission(p) for p in row.permissions],
                    host=row.host,
                    port=row.port,
                    working_directory=row.working_directory,
                    environment_vars=row.environment_vars or {},
                    created_at=row.created_at,
                    last_activity=row.last_activity,
                    expires_at=row.expires_at,
                    max_idle_minutes=row.max_idle_minutes,
                    command_history=row.command_history or [],
                    output_buffer=row.output_buffer or "",
                    metadata=row.metadata or {}
                )
                
                if session.status in [SessionStatus.ACTIVE, SessionStatus.IDLE] and datetime.utcnow() <= session.expires_at:
                    self.active_sessions[session_id] = session
                
                return session
                
        except Exception as e:
            self.logger.error(f"Failed to get session: {str(e)}")
            return None

    async def update_session_activity(self, session_id: str) -> bool:
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            session.last_activity = datetime.utcnow()
            
            if session.status == SessionStatus.IDLE:
                session.status = SessionStatus.ACTIVE
            
            if not self.database:
                return False
            
            async with self.database.get_session() as session_db:
                await session_db.execute("""
                    UPDATE terminal_sessions 
                    SET last_activity = :last_activity, status = :status
                    WHERE session_id = :session_id
                """, {
                    "session_id": session_id,
                    "last_activity": session.last_activity,
                    "status": session.status.value
                })
                await session_db.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update session activity: {str(e)}")
            return False

    async def execute_command(
        self,
        session_id: str,
        command: str,
        user_id: str
    ) -> Optional[str]:
        try:
            session = await self.get_session(session_id)
            if not session:
                return None
            
            if session.user_id != user_id:
                self.logger.warning(f"User {user_id} attempted to execute command in session {session_id} owned by {session.user_id}")
                return None
            
            if SessionPermission.EXECUTE not in session.permissions:
                self.logger.warning(f"User {user_id} does not have execute permission in session {session_id}")
                return None
            
            await self.update_session_activity(session_id)
            
            command_id = str(uuid.uuid4())
            start_time = datetime.utcnow()
            
            session_command = SessionCommand(
                command_id=command_id,
                session_id=session_id,
                command=command,
                executed_at=start_time,
                exit_code=None,
                duration_seconds=None,
                output="",
                error="",
                metadata={}
            )
            
            session.command_history.append(command)
            if len(session.command_history) > 1000:
                session.command_history = session.command_history[-1000:]
            
            await self._log_session_event(session_id, "command_executed", f"Command executed: {command}")
            
            if not self.database:
                return None
            
            async with self.database.get_session() as session_db:
                await session_db.execute("""
                    INSERT INTO session_commands (
                        command_id, session_id, command, executed_at, metadata
                    ) VALUES (
                        :command_id, :session_id, :command, :executed_at, :metadata
                    )
                """, {
                    "command_id": command_id,
                    "session_id": session_id,
                    "command": command,
                    "executed_at": start_time,
                    "metadata": session_command.metadata
                })
                
                await session_db.execute("""
                    UPDATE terminal_sessions 
                    SET command_history = :command_history, last_activity = :last_activity
                    WHERE session_id = :session_id
                """, {
                    "session_id": session_id,
                    "command_history": session.command_history,
                    "last_activity": datetime.utcnow()
                })
                
                await session_db.commit()
            
            return command_id
            
        except Exception as e:
            self.logger.error(f"Failed to execute command: {str(e)}")
            return None

    async def update_command_result(
        self,
        command_id: str,
        exit_code: int,
        output: str,
        error: str,
        duration_seconds: int
    ) -> bool:
        try:
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE session_commands 
                    SET exit_code = :exit_code, output = :output, error = :error, duration_seconds = :duration_seconds
                    WHERE command_id = :command_id
                """, {
                    "command_id": command_id,
                    "exit_code": exit_code,
                    "output": output,
                    "error": error,
                    "duration_seconds": duration_seconds
                })
                await session.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update command result: {str(e)}")
            return False

    async def suspend_session(self, session_id: str, reason: str = "suspended") -> bool:
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            session.status = SessionStatus.SUSPENDED
            
            if not self.database:
                return False
            
            async with self.database.get_session() as session_db:
                await session_db.execute("""
                    UPDATE terminal_sessions 
                    SET status = :status
                    WHERE session_id = :session_id
                """, {
                    "session_id": session_id,
                    "status": session.status.value
                })
                await session_db.commit()
            
            await self._log_session_event(session_id, "session_suspended", f"Session suspended: {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to suspend session: {str(e)}")
            return False

    async def resume_session(self, session_id: str) -> bool:
        try:
            if not self.database:
                return False
            
            async with self.database.get_session() as session_db:
                result = await session_db.execute("""
                    SELECT session_id, user_id, session_type, status, permissions, host, port,
                           working_directory, environment_vars, created_at, last_activity, expires_at,
                           max_idle_minutes, command_history, output_buffer, metadata
                    FROM terminal_sessions
                    WHERE session_id = :session_id AND status = 'suspended'
                """, {"session_id": session_id})
                
                row = result.fetchone()
                if not row:
                    return False
                
                if datetime.utcnow() > row.expires_at:
                    await self.terminate_session(session_id, "expired")
                    return False
                
                await session_db.execute("""
                    UPDATE terminal_sessions 
                    SET status = :status, last_activity = :last_activity
                    WHERE session_id = :session_id
                """, {
                    "session_id": session_id,
                    "status": SessionStatus.ACTIVE.value,
                    "last_activity": datetime.utcnow()
                })
                await session_db.commit()
                
                session = TerminalSession(
                    session_id=row.session_id,
                    user_id=row.user_id,
                    session_type=SessionType(row.session_type),
                    status=SessionStatus.ACTIVE,
                    permissions=[SessionPermission(p) for p in row.permissions],
                    host=row.host,
                    port=row.port,
                    working_directory=row.working_directory,
                    environment_vars=row.environment_vars or {},
                    created_at=row.created_at,
                    last_activity=datetime.utcnow(),
                    expires_at=row.expires_at,
                    max_idle_minutes=row.max_idle_minutes,
                    command_history=row.command_history or [],
                    output_buffer=row.output_buffer or "",
                    metadata=row.metadata or {}
                )
                
                self.active_sessions[session_id] = session
                
                await self._log_session_event(session_id, "session_resumed", "Session resumed")
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to resume session: {str(e)}")
            return False

    async def terminate_session(self, session_id: str, reason: str = "terminated") -> bool:
        try:
            session = None
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                del self.active_sessions[session_id]
            
            if not self.database:
                return False
            
            async with self.database.get_session() as session_db:
                await session_db.execute("""
                    UPDATE terminal_sessions 
                    SET status = :status
                    WHERE session_id = :session_id
                """, {
                    "session_id": session_id,
                    "status": SessionStatus.TERMINATED.value
                })
                await session_db.commit()
            
            if session:
                if session.user_id in self.user_sessions:
                    self.user_sessions[session.user_id].discard(session_id)
                    if not self.user_sessions[session.user_id]:
                        del self.user_sessions[session.user_id]
                
                await self._log_session_event(session_id, "session_terminated", f"Session terminated: {reason}")
            
            self.logger.info(f"Session terminated: {session_id} - {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to terminate session: {str(e)}")
            return False

    async def _log_session_event(
        self,
        session_id: str,
        event_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        try:
            if not self.database:
                return
            
            event_id = str(uuid.uuid4())
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO session_events (
                        event_id, session_id, event_type, description, metadata
                    ) VALUES (
                        :event_id, :session_id, :event_type, :description, :metadata
                    )
                """, {
                    "event_id": event_id,
                    "session_id": session_id,
                    "event_type": event_type,
                    "description": description,
                    "metadata": metadata or {}
                })
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log session event: {str(e)}")

    async def get_user_sessions(self, user_id: str) -> List[TerminalSession]:
        try:
            sessions = []
            if user_id in self.user_sessions:
                for session_id in self.user_sessions[user_id]:
                    session = await self.get_session(session_id)
                    if session:
                        sessions.append(session)
            return sessions
        except Exception as e:
            self.logger.error(f"Failed to get user sessions: {str(e)}")
            return []

    async def get_session_commands(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionCommand]:
        if not self.database:
            return []
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT command_id, session_id, command, executed_at, exit_code,
                       duration_seconds, output, error, metadata
                FROM session_commands
                WHERE session_id = :session_id
                ORDER BY executed_at DESC
                LIMIT :limit OFFSET :offset
            """, {"session_id": session_id, "limit": limit, "offset": offset})
            
            commands = []
            for row in result:
                command = SessionCommand(
                    command_id=row.command_id,
                    session_id=row.session_id,
                    command=row.command,
                    executed_at=row.executed_at,
                    exit_code=row.exit_code,
                    duration_seconds=row.duration_seconds,
                    output=row.output or "",
                    error=row.error or "",
                    metadata=row.metadata or {}
                )
                commands.append(command)
            
            return commands

    async def get_session_events(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionEvent]:
        if not self.database:
            return []
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT event_id, session_id, event_type, description, timestamp, metadata
                FROM session_events
                WHERE session_id = :session_id
                ORDER BY timestamp DESC
                LIMIT :limit OFFSET :offset
            """, {"session_id": session_id, "limit": limit, "offset": offset})
            
            events = []
            for row in result:
                event = SessionEvent(
                    event_id=row.event_id,
                    session_id=row.session_id,
                    event_type=row.event_type,
                    description=row.description,
                    timestamp=row.timestamp,
                    metadata=row.metadata or {}
                )
                events.append(event)
            
            return events

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
                    COUNT(CASE WHEN status = 'idle' THEN 1 END) as idle_sessions,
                    COUNT(CASE WHEN status = 'suspended' THEN 1 END) as suspended_sessions,
                    COUNT(CASE WHEN status = 'terminated' THEN 1 END) as terminated_sessions,
                    COUNT(CASE WHEN session_type = 'terminal' THEN 1 END) as terminal_sessions,
                    COUNT(CASE WHEN session_type = 'ssh' THEN 1 END) as ssh_sessions,
                    COUNT(CASE WHEN session_type = 'web_console' THEN 1 END) as web_console_sessions,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(EXTRACT(EPOCH FROM (last_activity - created_at))/3600) as avg_session_duration_hours
                FROM terminal_sessions
                WHERE created_at BETWEEN :start_date AND :end_date
            """, {"start_date": start_date, "end_date": end_date})
            
            row = result.fetchone()
            if not row:
                return {}
            
            return {
                "total_sessions": row.total_sessions,
                "active_sessions": row.active_sessions,
                "idle_sessions": row.idle_sessions,
                "suspended_sessions": row.suspended_sessions,
                "terminated_sessions": row.terminated_sessions,
                "terminal_sessions": row.terminal_sessions,
                "ssh_sessions": row.ssh_sessions,
                "web_console_sessions": row.web_console_sessions,
                "unique_users": row.unique_users,
                "avg_session_duration_hours": float(row.avg_session_duration_hours) if row.avg_session_duration_hours else 0.0
            }

_terminal_session_manager: Optional[TerminalSessionManager] = None

async def get_terminal_session_manager() -> TerminalSessionManager:
    global _terminal_session_manager
    if _terminal_session_manager is None:
        _terminal_session_manager = TerminalSessionManager()
        await _terminal_session_manager.initialize()
    return _terminal_session_manager

async def init_terminal_session_manager() -> TerminalSessionManager:
    return await get_terminal_session_manager()

# Alias for backward compatibility
SessionManager = TerminalSessionManager