import asyncio
import subprocess
import os
import signal
import tempfile
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio.subprocess
import platform

from backend.core.database import get_database, DatabaseManager
from backend.core.cache import get_redis, RedisManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class TerminalPermission(Enum):
    READ_ONLY = "read_only"
    BASIC_EXECUTION = "basic_execution"
    FULL_ACCESS = "full_access"
    SYSTEM_ACCESS = "system_access"

class CommandType(Enum):
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    SYSTEM_INFO = "system_info"
    PROCESS_MANAGEMENT = "process_management"
    NETWORK_DIAGNOSTICS = "network_diagnostics"
    CODE_ANALYSIS = "code_analysis"
    CUSTOM_SCRIPT = "custom_script"

class CommandStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"

@dataclass
class TerminalSession:
    session_id: str
    user_id: str
    permissions: List[TerminalPermission]
    created_at: datetime
    last_activity: datetime
    is_active: bool
    current_directory: str
    environment_vars: Dict[str, str]
    command_history: List[str]
    max_commands: int = 100
    timeout_minutes: int = 30

@dataclass
class TerminalCommand:
    id: str
    session_id: str
    command: str
    command_type: CommandType
    status: CommandStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = None
    risk_level: str = "low"

class TerminalManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.settings = get_settings()
        
        self.active_sessions: Dict[str, TerminalSession] = {}
        self.running_processes: Dict[str, asyncio.subprocess.Process] = {}
        self.command_handlers: Dict[CommandType, Callable] = {}
        self.logger = logger
        
        self._setup_command_handlers()
        self._setup_security_rules()

    def _setup_command_handlers(self):
        self.command_handlers = {
            CommandType.FILE_READ: self._handle_file_read,
            CommandType.FILE_WRITE: self._handle_file_write,
            CommandType.SYSTEM_INFO: self._handle_system_info,
            CommandType.PROCESS_MANAGEMENT: self._handle_process_management,
            CommandType.NETWORK_DIAGNOSTICS: self._handle_network_diagnostics,
            CommandType.CODE_ANALYSIS: self._handle_code_analysis,
            CommandType.CUSTOM_SCRIPT: self._handle_custom_script
        }

    def _setup_security_rules(self):
        self.blocked_commands = [
            "rm -rf /",
            "dd if=/dev/zero",
            "mkfs",
            "fdisk",
            "format",
            "del C:\\",
            "format C:",
            "shutdown",
            "reboot",
            "halt",
            "poweroff"
        ]
        
        self.restricted_directories = [
            "/etc",
            "/var/log",
            "/proc",
            "/sys",
            "/dev",
            "C:\\Windows\\System32",
            "C:\\Windows\\SysWOW64"
        ]
        
        self.allowed_extensions = [
            ".py", ".js", ".ts", ".html", ".css", ".json", ".yml", ".yaml",
            ".md", ".txt", ".log", ".conf", ".ini", ".env", ".sh", ".bat"
        ]

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing TerminalManager...")
            
            self.database = get_database()
            self.redis = await get_redis()
            
            await self._setup_terminal_tables()
            await self._cleanup_expired_sessions()
            
            self.logger.info("TerminalManager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TerminalManager: {str(e)}")
            return False

    async def _setup_terminal_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS terminal_sessions (
                    session_id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    permissions JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    current_directory TEXT NOT NULL,
                    environment_vars JSONB NOT NULL,
                    command_history JSONB NOT NULL,
                    max_commands INTEGER DEFAULT 100,
                    timeout_minutes INTEGER DEFAULT 30
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS terminal_commands (
                    id VARCHAR(255) PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    command TEXT NOT NULL,
                    command_type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    exit_code INTEGER,
                    stdout TEXT,
                    stderr TEXT,
                    execution_time DECIMAL(10,3),
                    metadata JSONB,
                    risk_level VARCHAR(20) DEFAULT 'low',
                    FOREIGN KEY (session_id) REFERENCES terminal_sessions(session_id) ON DELETE CASCADE
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS terminal_activities (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    activity_type VARCHAR(100) NOT NULL,
                    description TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB,
                    FOREIGN KEY (session_id) REFERENCES terminal_sessions(session_id) ON DELETE CASCADE
                )
            """)
            
            await session.commit()

    async def create_terminal_session(self, user_id: str, permissions: List[TerminalPermission], 
                                    current_directory: str = None, timeout_minutes: int = 30) -> TerminalSession:
        try:
            session_id = str(uuid.uuid4())
            
            if not current_directory:
                current_directory = os.getcwd()
            
            # Ensure current directory is safe
            if not self._is_directory_safe(current_directory):
                current_directory = os.path.expanduser("~")
            
            session = TerminalSession(
                session_id=session_id,
                user_id=user_id,
                permissions=permissions,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                is_active=True,
                current_directory=current_directory,
                environment_vars=dict(os.environ),
                command_history=[],
                timeout_minutes=timeout_minutes
            )
            
            await self._save_session_to_database(session)
            self.active_sessions[session_id] = session
            
            await self._log_terminal_activity(session_id, "SESSION_CREATED", f"Terminal session created for user {user_id}")
            
            self.logger.info(f"Terminal session {session_id} created for user {user_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to create terminal session: {str(e)}")
            raise

    def _is_directory_safe(self, directory: str) -> bool:
        try:
            abs_path = os.path.abspath(directory)
            for restricted in self.restricted_directories:
                if abs_path.startswith(restricted):
                    return False
            return True
        except Exception:
            return False

    async def _save_session_to_database(self, session: TerminalSession):
        if not self.database:
            return
        
        async with self.database.get_session() as session_db:
            await session_db.execute("""
                INSERT INTO terminal_sessions (session_id, user_id, permissions, created_at, last_activity,
                                             is_active, current_directory, environment_vars, command_history,
                                             max_commands, timeout_minutes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                session.session_id, session.user_id, json.dumps([p.value for p in session.permissions]),
                session.created_at, session.last_activity, session.is_active, session.current_directory,
                json.dumps(session.environment_vars), json.dumps(session.command_history),
                session.max_commands, session.timeout_minutes
            ))
            await session_db.commit()

    async def execute_command(self, session_id: str, command: str, timeout_seconds: int = 300) -> TerminalCommand:
        session = self.active_sessions.get(session_id)
        if not session or not session.is_active:
            raise ValueError("Invalid or inactive session")
        
        # Check session timeout
        if datetime.utcnow() - session.last_activity > timedelta(minutes=session.timeout_minutes):
            await self._deactivate_session(session_id)
            raise ValueError("Session expired")
        
        # Security validation
        if not self._is_command_safe(command, session.permissions):
            raise ValueError("Command blocked for security reasons")
        
        # Create command record
        command_id = str(uuid.uuid4())
        command_type = self._classify_command(command)
        risk_level = self._assess_command_risk(command)
        
        terminal_command = TerminalCommand(
            id=command_id,
            session_id=session_id,
            command=command,
            command_type=command_type,
            status=CommandStatus.PENDING,
            started_at=datetime.utcnow(),
            metadata={"risk_level": risk_level}
        )
        
        # Update session activity
        session.last_activity = datetime.utcnow()
        session.command_history.append(command)
        if len(session.command_history) > session.max_commands:
            session.command_history.pop(0)
        
        await self._save_command_to_database(terminal_command)
        await self._update_session_activity(session_id)
        
        # Execute command
        try:
            await self._execute_command_async(terminal_command, timeout_seconds)
        except Exception as e:
            terminal_command.status = CommandStatus.FAILED
            terminal_command.stderr = str(e)
            await self._update_command_status(terminal_command)
        
        return terminal_command

    def _is_command_safe(self, command: str, permissions: List[TerminalPermission]) -> bool:
        # Check for blocked commands
        command_lower = command.lower().strip()
        for blocked in self.blocked_commands:
            if blocked in command_lower:
                return False
        
        # Check permissions
        if TerminalPermission.SYSTEM_ACCESS.value in [p.value for p in permissions]:
            return True
        
        if TerminalPermission.FULL_ACCESS.value in [p.value for p in permissions]:
            return not any(blocked in command_lower for blocked in self.blocked_commands)
        
        if TerminalPermission.BASIC_EXECUTION.value in [p.value for p in permissions]:
            # Only allow safe commands
            safe_commands = ["ls", "cat", "head", "tail", "grep", "find", "pwd", "whoami", "date"]
            return any(safe in command_lower for safe in safe_commands)
        
        # READ_ONLY - no execution allowed
        return False

    def _classify_command(self, command: str) -> CommandType:
        command_lower = command.lower().strip()
        
        if any(cmd in command_lower for cmd in ["cat", "head", "tail", "less", "more"]):
            return CommandType.FILE_READ
        elif any(cmd in command_lower for cmd in ["echo", "touch", "mkdir", "cp", "mv"]):
            return CommandType.FILE_WRITE
        elif any(cmd in command_lower for cmd in ["ps", "top", "htop", "kill"]):
            return CommandType.PROCESS_MANAGEMENT
        elif any(cmd in command_lower for cmd in ["ping", "netstat", "ifconfig", "ip"]):
            return CommandType.NETWORK_DIAGNOSTICS
        elif any(cmd in command_lower for cmd in ["uname", "cat /proc/version", "systeminfo"]):
            return CommandType.SYSTEM_INFO
        elif any(cmd in command_lower for cmd in ["python", "node", "gcc", "make"]):
            return CommandType.CODE_ANALYSIS
        else:
            return CommandType.CUSTOM_SCRIPT

    def _assess_command_risk(self, command: str) -> str:
        command_lower = command.lower().strip()
        
        # High risk commands
        high_risk = ["rm", "del", "format", "fdisk", "mkfs", "dd", "shutdown", "reboot"]
        if any(risk in command_lower for risk in high_risk):
            return "high"
        
        # Medium risk commands
        medium_risk = ["chmod", "chown", "sudo", "su", "passwd", "useradd", "userdel"]
        if any(risk in command_lower for risk in medium_risk):
            return "medium"
        
        # Low risk commands
        low_risk = ["ls", "cat", "pwd", "whoami", "date", "echo", "grep"]
        if any(risk in command_lower for risk in low_risk):
            return "low"
        
        return "medium"

    async def _execute_command_async(self, terminal_command: TerminalCommand, timeout_seconds: int):
        terminal_command.status = CommandStatus.EXECUTING
        await self._update_command_status(terminal_command)
        
        try:
            # Create process
            if platform.system() == "Windows":
                process = await asyncio.create_subprocess_exec(
                    "cmd", "/c", terminal_command.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.active_sessions[terminal_command.session_id].current_directory
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    "bash", "-c", terminal_command.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.active_sessions[terminal_command.session_id].current_directory
                )
            
            self.running_processes[terminal_command.id] = process
            
            # Execute with timeout
            start_time = datetime.utcnow()
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update command result
            terminal_command.status = CommandStatus.COMPLETED
            terminal_command.completed_at = datetime.utcnow()
            terminal_command.exit_code = process.returncode
            terminal_command.stdout = stdout.decode('utf-8', errors='ignore') if stdout else ""
            terminal_command.stderr = stderr.decode('utf-8', errors='ignore') if stderr else ""
            terminal_command.execution_time = execution_time
            
            # Remove from running processes
            if terminal_command.id in self.running_processes:
                del self.running_processes[terminal_command.id]
            
            await self._update_command_status(terminal_command)
            
            # Log successful execution
            await self._log_terminal_activity(
                terminal_command.session_id,
                "COMMAND_EXECUTED",
                f"Command executed successfully: {terminal_command.command[:50]}...",
                {"command_id": terminal_command.id, "execution_time": execution_time}
            )
            
        except asyncio.TimeoutError:
            terminal_command.status = CommandStatus.TIMEOUT
            terminal_command.stderr = "Command execution timed out"
            await self._update_command_status(terminal_command)
            
            # Kill process if still running
            if terminal_command.id in self.running_processes:
                process = self.running_processes[terminal_command.id]
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5)
                except:
                    process.kill()
                del self.running_processes[terminal_command.id]
            
        except Exception as e:
            terminal_command.status = CommandStatus.FAILED
            terminal_command.stderr = str(e)
            await self._update_command_status(terminal_command)

    async def _save_command_to_database(self, command: TerminalCommand):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute("""
                INSERT INTO terminal_commands (id, session_id, command, command_type, status, started_at,
                                             completed_at, exit_code, stdout, stderr, execution_time,
                                             metadata, risk_level)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                command.id, command.session_id, command.command, command.command_type.value,
                command.status.value, command.started_at, command.completed_at, command.exit_code,
                command.stdout, command.stderr, command.execution_time,
                json.dumps(command.metadata or {}), command.risk_level
            ))
            await session.commit()

    async def _update_command_status(self, command: TerminalCommand):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute("""
                UPDATE terminal_commands 
                SET status = %s, completed_at = %s, exit_code = %s, stdout = %s, stderr = %s,
                    execution_time = %s, metadata = %s
                WHERE id = %s
            """, (
                command.status.value, command.completed_at, command.exit_code,
                command.stdout, command.stderr, command.execution_time,
                json.dumps(command.metadata or {}), command.id
            ))
            await session.commit()

    async def _update_session_activity(self, session_id: str):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute("""
                UPDATE terminal_sessions 
                SET last_activity = %s, command_history = %s
                WHERE session_id = %s
            """, (
                datetime.utcnow(),
                json.dumps(self.active_sessions[session_id].command_history),
                session_id
            ))
            await session.commit()

    async def get_session_info(self, session_id: str) -> Optional[TerminalSession]:
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        if not self.database:
            return None
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT session_id, user_id, permissions, created_at, last_activity, is_active,
                       current_directory, environment_vars, command_history, max_commands, timeout_minutes
                FROM terminal_sessions WHERE session_id = %s
            """, (session_id,))
            
            row = result.fetchone()
            if row:
                return TerminalSession(
                    session_id=row[0],
                    user_id=row[1],
                    permissions=[TerminalPermission(p) for p in row[2]],
                    created_at=row[3],
                    last_activity=row[4],
                    is_active=row[5],
                    current_directory=row[6],
                    environment_vars=row[7],
                    command_history=row[8],
                    max_commands=row[9],
                    timeout_minutes=row[10]
                )
        
        return None

    async def get_command_history(self, session_id: str, limit: int = 50) -> List[TerminalCommand]:
        if not self.database:
            return []
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT id, session_id, command, command_type, status, started_at, completed_at,
                       exit_code, stdout, stderr, execution_time, metadata, risk_level
                FROM terminal_commands 
                WHERE session_id = %s 
                ORDER BY started_at DESC 
                LIMIT %s
            """, (session_id, limit))
            
            commands = []
            for row in result.fetchall():
                command = TerminalCommand(
                    id=row[0],
                    session_id=row[1],
                    command=row[2],
                    command_type=CommandType(row[3]),
                    status=CommandStatus(row[4]),
                    started_at=row[5],
                    completed_at=row[6],
                    exit_code=row[7],
                    stdout=row[8],
                    stderr=row[9],
                    execution_time=float(row[10]) if row[10] else None,
                    metadata=row[11] if row[11] else {},
                    risk_level=row[12]
                )
                commands.append(command)
            
            return commands

    async def change_directory(self, session_id: str, new_directory: str) -> bool:
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        try:
            # Validate new directory
            if not self._is_directory_safe(new_directory):
                return False
            
            # Check if directory exists and is accessible
            if not os.path.exists(new_directory) or not os.access(new_directory, os.R_OK):
                return False
            
            old_directory = session.current_directory
            session.current_directory = os.path.abspath(new_directory)
            
            # Update database
            if self.database:
                async with self.database.get_session() as session_db:
                    await session_db.execute("""
                        UPDATE terminal_sessions 
                        SET current_directory = %s, last_activity = %s
                        WHERE session_id = %s
                    """, (session.current_directory, datetime.utcnow(), session_id))
                    await session_db.commit()
            
            await self._log_terminal_activity(
                session_id,
                "DIRECTORY_CHANGED",
                f"Directory changed from {old_directory} to {session.current_directory}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to change directory: {str(e)}")
            return False

    async def _deactivate_session(self, session_id: str):
        if session_id in self.active_sessions:
            self.active_sessions[session_id].is_active = False
        
        if self.database:
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE terminal_sessions 
                    SET is_active = FALSE 
                    WHERE session_id = %s
                """, (session_id,))
                await session.commit()

    async def _log_terminal_activity(self, session_id: str, activity_type: str, description: str, metadata: Dict[str, Any] = None):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO terminal_activities (session_id, activity_type, description, metadata)
                    VALUES (%s, %s, %s, %s)
                """, (session_id, activity_type, description, json.dumps(metadata or {})))
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log terminal activity: {str(e)}")

    async def cleanup_expired_sessions(self):
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if current_time - session.last_activity > timedelta(minutes=session.timeout_minutes):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self._deactivate_session(session_id)
            self.logger.info(f"Terminal session {session_id} expired and deactivated")

    async def close(self):
        self.logger.info("Closing TerminalManager...")
        
        # Kill all running processes
        for command_id, process in self.running_processes.items():
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5)
            except:
                process.kill()
        
        if self.database:
            await self.database.close()

# Global instances and initialization functions
_terminal_manager: Optional[TerminalManager] = None

async def init_terminal_manager() -> TerminalManager:
    global _terminal_manager
    if not _terminal_manager:
        _terminal_manager = TerminalManager()
        await _terminal_manager.initialize()
    return _terminal_manager

async def get_terminal_manager() -> TerminalManager:
    global _terminal_manager
    if not _terminal_manager:
        _terminal_manager = await init_terminal_manager()
    return _terminal_manager
