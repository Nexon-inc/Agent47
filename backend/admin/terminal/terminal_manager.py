import asyncio
import subprocess
import os
import sys
from typing import Dict, Any, List, Optional

# Unix-specific imports (not available on Windows)
if sys.platform != 'win32':
    import pty
    import termios
    import fcntl
    import struct
    import signal
else:
    # Windows-compatible stubs (not used in this code)
    pty = None
    termios = None
    fcntl = None
    struct = None
    signal = None
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text

from backend.core.database import get_database, DatabaseManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class TerminalStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"

class CommandStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class TerminalSession:
    session_id: str
    user_id: str
    status: TerminalStatus
    created_at: datetime
    last_activity: datetime
    working_directory: str
    environment: Dict[str, str]
    metadata: Dict[str, Any]

@dataclass
class Command:
    command_id: str
    session_id: str
    command: str
    status: CommandStatus
    output: str
    error: str
    exit_code: int
    start_time: datetime
    end_time: Optional[datetime]
    execution_time: float

class TerminalManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.active_sessions = {}
        self.command_history = {}
        self.allowed_commands = self._load_allowed_commands()
        self.blocked_commands = self._load_blocked_commands()

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing TerminalManager...")
            self.database = get_database()
            await self._setup_terminal_tables()
            await self._load_session_history()
            self.logger.info("TerminalManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize TerminalManager: {str(e)}")
            return False

    async def _setup_terminal_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS terminal_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    user_id VARCHAR(255) NOT NULL,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    working_directory TEXT,
                    environment JSONB,
                    metadata JSONB
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS terminal_commands (
                    id SERIAL PRIMARY KEY,
                    command_id VARCHAR(255) UNIQUE NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    command TEXT NOT NULL,
                    status VARCHAR(20) DEFAULT 'running',
                    output TEXT,
                    error TEXT,
                    exit_code INTEGER,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    execution_time FLOAT,
                    metadata JSONB
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS terminal_logs (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    details JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_terminal_sessions_user_id 
                ON terminal_sessions(user_id)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_terminal_commands_session_id 
                ON terminal_commands(session_id)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_terminal_commands_start_time 
                ON terminal_commands(start_time)
            """))
            
            await session.commit()

    def _load_allowed_commands(self) -> List[str]:
        return [
            "ls", "pwd", "cd", "cat", "head", "tail", "grep", "find", "ps", "top", "htop",
            "df", "du", "free", "uptime", "who", "w", "last", "history", "echo", "date",
            "cal", "uname", "hostname", "ip", "netstat", "ss", "ping", "curl", "wget",
            "tar", "gzip", "gunzip", "zip", "unzip", "mkdir", "rmdir", "cp", "mv", "rm",
            "chmod", "chown", "touch", "ln", "which", "whereis", "locate", "updatedb",
            "systemctl", "service", "journalctl", "logrotate", "crontab", "at",
            "useradd", "userdel", "usermod", "groupadd", "groupdel", "passwd",
            "apt", "apt-get", "dpkg", "yum", "dnf", "rpm", "brew", "pip", "npm",
            "git", "svn", "docker", "kubectl", "helm", "terraform", "ansible"
        ]

    def _load_blocked_commands(self) -> List[str]:
        return [
            "rm -rf /", "rm -rf /*", "dd if=/dev/zero", "mkfs", "fdisk", "parted",
            "shutdown", "reboot", "halt", "poweroff", "init 0", "init 6",
            "sudo", "su", "passwd root", "chmod 777", "chmod -R 777",
            "wget http://", "curl http://", "nc", "netcat", "telnet",
            "ssh-keygen", "ssh-copy-id", "scp", "rsync",
            "crontab -r", "atrm", "killall", "pkill", "kill -9",
            "iptables", "firewall-cmd", "ufw", "nft",
            "mount", "umount", "fstab", "grub", "lilo"
        ]

    async def _load_session_history(self):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT session_id, user_id, status, created_at, last_activity, 
                           working_directory, environment, metadata
                    FROM terminal_sessions 
                    WHERE status = 'active'
                """))
                
                for row in result.fetchall():
                    terminal_session = TerminalSession(
                        session_id=row[0],
                        user_id=row[1],
                        status=TerminalStatus(row[2]),
                        created_at=row[3],
                        last_activity=row[4],
                        working_directory=row[5] or "/",
                        environment=row[6] or {},
                        metadata=row[7] or {}
                    )
                    self.active_sessions[row[0]] = terminal_session
        except Exception as e:
            self.logger.error(f"Failed to load session history: {str(e)}")

    async def create_session(self, user_id: str, working_directory: str = None) -> Dict[str, Any]:
        if not self.database:
            return {"error": "Database not initialized"}
        
        session_id = f"term_{user_id}_{int(datetime.utcnow().timestamp())}"
        
        try:
            working_dir = working_directory or os.getcwd()
            
            terminal_session = TerminalSession(
                session_id=session_id,
                user_id=user_id,
                status=TerminalStatus.ACTIVE,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                working_directory=working_dir,
                environment=dict(os.environ),
                metadata={"created_by": user_id}
            )
            
            await self._save_session(terminal_session)
            self.active_sessions[session_id] = terminal_session
            
            await self._log_session_action(session_id, "created", {"user_id": user_id})
            
            return {
                "success": True,
                "session_id": session_id,
                "working_directory": working_dir,
                "message": "Terminal session created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create terminal session: {str(e)}")
            return {"error": str(e)}

    async def _save_session(self, session: TerminalSession):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session_db:
                await session_db.execute(text("""
                    INSERT INTO terminal_sessions (
                        session_id, user_id, status, created_at, last_activity,
                        working_directory, environment, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        last_activity = EXCLUDED.last_activity,
                        working_directory = EXCLUDED.working_directory,
                        environment = EXCLUDED.environment,
                        metadata = EXCLUDED.metadata
                """), (
                    session.session_id,
                    session.user_id,
                    session.status.value,
                    session.created_at,
                    session.last_activity,
                    session.working_directory,
                    session.environment,
                    session.metadata
                ))
                await session_db.commit()
        except Exception as e:
            self.logger.error(f"Failed to save session: {str(e)}")

    async def execute_command(self, session_id: str, command: str, timeout: int = 30) -> Dict[str, Any]:
        if session_id not in self.active_sessions:
            return {"error": "Session not found or inactive"}
        
        if not self._is_command_allowed(command):
            return {"error": "Command not allowed"}
        
        if self._is_command_blocked(command):
            return {"error": "Command is blocked for security reasons"}
        
        command_id = f"cmd_{session_id}_{int(datetime.utcnow().timestamp())}"
        
        try:
            start_time = datetime.utcnow()
            
            cmd_obj = Command(
                command_id=command_id,
                session_id=session_id,
                command=command,
                status=CommandStatus.RUNNING,
                output="",
                error="",
                exit_code=0,
                start_time=start_time,
                end_time=None,
                execution_time=0.0
            )
            
            await self._save_command(cmd_obj)
            
            result = await self._run_command(command, timeout)
            
            cmd_obj.status = CommandStatus.COMPLETED if result["success"] else CommandStatus.FAILED
            cmd_obj.output = result.get("output", "")
            cmd_obj.error = result.get("error", "")
            cmd_obj.exit_code = result.get("exit_code", 1)
            cmd_obj.end_time = datetime.utcnow()
            cmd_obj.execution_time = (cmd_obj.end_time - start_time).total_seconds()
            
            await self._update_command(cmd_obj)
            
            session = self.active_sessions[session_id]
            session.last_activity = datetime.utcnow()
            await self._save_session(session)
            
            await self._log_session_action(session_id, "command_executed", {
                "command": command,
                "success": result["success"],
                "execution_time": cmd_obj.execution_time
            })
            
            return {
                "success": True,
                "command_id": command_id,
                "output": cmd_obj.output,
                "error": cmd_obj.error,
                "exit_code": cmd_obj.exit_code,
                "execution_time": cmd_obj.execution_time
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute command: {str(e)}")
            return {"error": str(e)}

    async def _run_command(self, command: str, timeout: int) -> Dict[str, Any]:
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                
                return {
                    "success": process.returncode == 0,
                    "output": stdout.decode('utf-8', errors='ignore'),
                    "error": stderr.decode('utf-8', errors='ignore'),
                    "exit_code": process.returncode
                }
                
            except asyncio.TimeoutError:
                process.terminate()
                await process.wait()
                
                return {
                    "success": False,
                    "output": "",
                    "error": f"Command timed out after {timeout} seconds",
                    "exit_code": -1
                }
                
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "exit_code": -1
            }

    def _is_command_allowed(self, command: str) -> bool:
        command_parts = command.strip().split()
        if not command_parts:
            return False
        
        base_command = command_parts[0].lower()
        return base_command in self.allowed_commands

    def _is_command_blocked(self, command: str) -> bool:
        command_lower = command.lower()
        for blocked_cmd in self.blocked_commands:
            if blocked_cmd in command_lower:
                return True
        return False

    async def _save_command(self, command: Command):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO terminal_commands (
                        command_id, session_id, command, status, output, error,
                        exit_code, start_time, end_time, execution_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """), (
                    command.command_id,
                    command.session_id,
                    command.command,
                    command.status.value,
                    command.output,
                    command.error,
                    command.exit_code,
                    command.start_time,
                    command.end_time,
                    command.execution_time
                ))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to save command: {str(e)}")

    async def _update_command(self, command: Command):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    UPDATE terminal_commands 
                    SET status = %s, output = %s, error = %s, exit_code = %s,
                        end_time = %s, execution_time = %s
                    WHERE command_id = %s
                """), (
                    command.status.value,
                    command.output,
                    command.error,
                    command.exit_code,
                    command.end_time,
                    command.execution_time,
                    command.command_id
                ))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to update command: {str(e)}")

    async def _log_session_action(self, session_id: str, action: str, details: Dict[str, Any]):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO terminal_logs (session_id, action, details)
                    VALUES (%s, %s, %s)
                """), (session_id, action, details))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to log session action: {str(e)}")

    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "working_directory": session.working_directory,
            "environment": session.environment,
            "metadata": session.metadata
        }

    async def get_command_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT command_id, command, status, output, error, exit_code,
                           start_time, end_time, execution_time
                    FROM terminal_commands 
                    WHERE session_id = %s
                    ORDER BY start_time DESC 
                    LIMIT %s
                """), (session_id, limit))
                
                commands = []
                for row in result.fetchall():
                    commands.append({
                        "command_id": row[0],
                        "command": row[1],
                        "status": row[2],
                        "output": row[3][:500] + "..." if len(row[3]) > 500 else row[3],
                        "error": row[4],
                        "exit_code": row[5],
                        "start_time": row[6].isoformat(),
                        "end_time": row[7].isoformat() if row[7] else None,
                        "execution_time": row[8]
                    })
                
                return commands
        except Exception as e:
            self.logger.error(f"Failed to get command history: {str(e)}")
            return []

    async def close_session(self, session_id: str) -> bool:
        if session_id not in self.active_sessions:
            return False
        
        try:
            session = self.active_sessions[session_id]
            session.status = TerminalStatus.TERMINATED
            
            await self._save_session(session)
            await self._log_session_action(session_id, "closed", {"closed_by": session.user_id})
            
            del self.active_sessions[session_id]
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to close session: {str(e)}")
            return False

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        for session in self.active_sessions.values():
            sessions.append({
                "session_id": session.session_id,
                "user_id": session.user_id,
                "status": session.status.value,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "working_directory": session.working_directory
            })
        return sessions

    async def cleanup_inactive_sessions(self, hours: int = 24):
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        sessions_to_close = []
        for session_id, session in self.active_sessions.items():
            if session.last_activity < cutoff_time:
                sessions_to_close.append(session_id)
        
        for session_id in sessions_to_close:
            await self.close_session(session_id)

    async def shutdown(self):
        self.logger.info("Shutting down TerminalManager...")
        
        for session_id in list(self.active_sessions.keys()):
            await self.close_session(session_id)
        
        self.logger.info("TerminalManager shutdown complete")
