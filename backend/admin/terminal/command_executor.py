import asyncio
import subprocess
import shlex
import os
import signal
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text
import psutil

from backend.core.database import get_database, DatabaseManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class CommandStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class CommandType(Enum):
    SHELL = "shell"
    PYTHON = "python"
    SQL = "sql"
    SYSTEM = "system"
    CUSTOM = "custom"

class ExecutionEnvironment(Enum):
    LOCAL = "local"
    DOCKER = "docker"
    SSH = "ssh"
    KUBERNETES = "kubernetes"

@dataclass
class CommandExecution:
    execution_id: str
    command: str
    command_type: CommandType
    environment: ExecutionEnvironment
    status: CommandStatus
    user_id: str
    working_directory: str
    environment_vars: Dict[str, str]
    timeout_seconds: int
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    exit_code: Optional[int]
    stdout: str
    stderr: str
    metadata: Dict[str, Any]

@dataclass
class CommandTemplate:
    template_id: str
    name: str
    description: str
    command_template: str
    command_type: CommandType
    environment: ExecutionEnvironment
    parameters: List[str]
    timeout_seconds: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

class CommandExecutor(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.active_executions: Dict[str, CommandExecution] = {}
        self.command_templates: Dict[str, CommandTemplate] = {}
        self.execution_history: List[CommandExecution] = []
        self.max_concurrent_executions = 10
        self.default_timeout_seconds = 300
        self.allowed_commands: List[str] = []
        self.blocked_commands: List[str] = []
        self.safe_directories: List[str] = []

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing CommandExecutor...")
            self.database = get_database()
            await self._setup_command_tables()
            await self._load_command_templates()
            await self._load_security_config()
            await self._start_cleanup_task()
            self.logger.info("CommandExecutor initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize CommandExecutor: {str(e)}")
            return False

    async def _setup_command_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS command_executions (
                    id SERIAL PRIMARY KEY,
                    execution_id VARCHAR(255) UNIQUE NOT NULL,
                    command TEXT NOT NULL,
                    command_type VARCHAR(20) NOT NULL,
                    environment VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    user_id VARCHAR(255) NOT NULL,
                    working_directory VARCHAR(500) NOT NULL,
                    environment_vars JSONB DEFAULT '{}'::jsonb,
                    timeout_seconds INTEGER DEFAULT 300,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    duration_seconds INTEGER,
                    exit_code INTEGER,
                    stdout TEXT,
                    stderr TEXT,
                    metadata JSONB DEFAULT '{}'::jsonb
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS command_templates (
                    id SERIAL PRIMARY KEY,
                    template_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    command_template TEXT NOT NULL,
                    command_type VARCHAR(20) NOT NULL,
                    environment VARCHAR(20) NOT NULL,
                    parameters JSONB DEFAULT '[]'::jsonb,
                    timeout_seconds INTEGER DEFAULT 300,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS command_security_rules (
                    id SERIAL PRIMARY KEY,
                    rule_id VARCHAR(255) UNIQUE NOT NULL,
                    rule_type VARCHAR(20) NOT NULL,
                    pattern VARCHAR(500) NOT NULL,
                    action VARCHAR(20) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_command_executions_status 
                ON command_executions(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_command_executions_user_id 
                ON command_executions(user_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_command_executions_started_at 
                ON command_executions(started_at);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_command_templates_is_active 
                ON command_templates(is_active);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_command_security_rules_is_active 
                ON command_security_rules(is_active);
            """)
            
            await session.commit()

    async def _load_command_templates(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT template_id, name, description, command_template, command_type,
                       environment, parameters, timeout_seconds, is_active, created_at, updated_at
                FROM command_templates
                WHERE is_active = TRUE
            """)
            
            for row in result:
                template = CommandTemplate(
                    template_id=row.template_id,
                    name=row.name,
                    description=row.description or "",
                    command_template=row.command_template,
                    command_type=CommandType(row.command_type),
                    environment=ExecutionEnvironment(row.environment),
                    parameters=row.parameters or [],
                    timeout_seconds=row.timeout_seconds,
                    is_active=row.is_active,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                self.command_templates[template.template_id] = template

    async def _load_security_config(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT rule_type, pattern, action
                FROM command_security_rules
                WHERE is_active = TRUE
            """)
            
            for row in result:
                if row.rule_type == "allowed":
                    self.allowed_commands.append(row.pattern)
                elif row.rule_type == "blocked":
                    self.blocked_commands.append(row.pattern)
                elif row.rule_type == "safe_directory":
                    self.safe_directories.append(row.pattern)

    async def _start_cleanup_task(self):
        asyncio.create_task(self._cleanup_old_executions())

    async def _cleanup_old_executions(self):
        while True:
            try:
                await self._cleanup_old_executions_internal()
                await asyncio.sleep(3600)
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {str(e)}")
                await asyncio.sleep(3600)

    async def _cleanup_old_executions_internal(self):
        if not self.database:
            return
        
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                DELETE FROM command_executions 
                WHERE started_at < :cutoff_date AND status IN ('completed', 'failed', 'timeout', 'cancelled')
            """, {"cutoff_date": cutoff_date})
            
            deleted_count = result.rowcount
            await session.commit()
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old command executions")

    async def execute_command(
        self,
        command: str,
        command_type: CommandType,
        environment: ExecutionEnvironment,
        user_id: str,
        working_directory: str = "/tmp",
        environment_vars: Optional[Dict[str, str]] = None,
        timeout_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        try:
            if len(self.active_executions) >= self.max_concurrent_executions:
                self.logger.warning("Maximum concurrent executions reached")
                return None
            
            if not await self._validate_command(command, working_directory):
                self.logger.warning(f"Command validation failed: {command}")
                return None
            
            execution_id = f"CMD_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(command) % 10000}"
            
            execution = CommandExecution(
                execution_id=execution_id,
                command=command,
                command_type=command_type,
                environment=environment,
                status=CommandStatus.PENDING,
                user_id=user_id,
                working_directory=working_directory,
                environment_vars=environment_vars or {},
                timeout_seconds=timeout_seconds or self.default_timeout_seconds,
                started_at=datetime.utcnow(),
                completed_at=None,
                duration_seconds=None,
                exit_code=None,
                stdout="",
                stderr="",
                metadata=metadata or {}
            )
            
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO command_executions (
                        execution_id, command, command_type, environment, status, user_id,
                        working_directory, environment_vars, timeout_seconds, metadata
                    ) VALUES (
                        :execution_id, :command, :command_type, :environment, :status, :user_id,
                        :working_directory, :environment_vars, :timeout_seconds, :metadata
                    )
                """, {
                    "execution_id": execution.execution_id,
                    "command": execution.command,
                    "command_type": execution.command_type.value,
                    "environment": execution.environment.value,
                    "status": execution.status.value,
                    "user_id": execution.user_id,
                    "working_directory": execution.working_directory,
                    "environment_vars": execution.environment_vars,
                    "timeout_seconds": execution.timeout_seconds,
                    "metadata": execution.metadata
                })
                await session.commit()
            
            self.active_executions[execution_id] = execution
            asyncio.create_task(self._execute_command_async(execution))
            
            self.logger.info(f"Command execution started: {execution_id}")
            return execution_id
            
        except Exception as e:
            self.logger.error(f"Failed to execute command: {str(e)}")
            return None

    async def _validate_command(self, command: str, working_directory: str) -> bool:
        try:
            if self.blocked_commands:
                for blocked_pattern in self.blocked_commands:
                    if blocked_pattern in command.lower():
                        return False
            
            if self.allowed_commands:
                command_allowed = False
                for allowed_pattern in self.allowed_commands:
                    if allowed_pattern in command.lower():
                        command_allowed = True
                        break
                if not command_allowed:
                    return False
            
            if self.safe_directories:
                directory_safe = False
                for safe_dir in self.safe_directories:
                    if working_directory.startswith(safe_dir):
                        directory_safe = True
                        break
                if not directory_safe:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Command validation error: {str(e)}")
            return False

    async def _execute_command_async(self, execution: CommandExecution):
        try:
            execution.status = CommandStatus.RUNNING
            
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE command_executions 
                    SET status = :status
                    WHERE execution_id = :execution_id
                """, {
                    "execution_id": execution.execution_id,
                    "status": execution.status.value
                })
                await session.commit()
            
            if execution.environment == ExecutionEnvironment.LOCAL:
                await self._execute_local_command(execution)
            elif execution.environment == ExecutionEnvironment.DOCKER:
                await self._execute_docker_command(execution)
            elif execution.environment == ExecutionEnvironment.SSH:
                await self._execute_ssh_command(execution)
            elif execution.environment == ExecutionEnvironment.KUBERNETES:
                await self._execute_kubernetes_command(execution)
            
        except Exception as e:
            self.logger.error(f"Command execution failed: {str(e)}")
            await self._mark_execution_failed(execution.execution_id, str(e))

    async def _execute_local_command(self, execution: CommandExecution):
        try:
            if execution.command_type == CommandType.SHELL:
                process = await asyncio.create_subprocess_shell(
                    execution.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=execution.working_directory,
                    env={**os.environ, **execution.environment_vars}
                )
            elif execution.command_type == CommandType.PYTHON:
                process = await asyncio.create_subprocess_exec(
                    "python", "-c", execution.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=execution.working_directory,
                    env={**os.environ, **execution.environment_vars}
                )
            elif execution.command_type == CommandType.SQL:
                process = await asyncio.create_subprocess_exec(
                    "psql", "-c", execution.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=execution.working_directory,
                    env={**os.environ, **execution.environment_vars}
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *shlex.split(execution.command),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=execution.working_directory,
                    env={**os.environ, **execution.environment_vars}
                )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=execution.timeout_seconds
                )
                
                execution.status = CommandStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                execution.duration_seconds = int((execution.completed_at - execution.started_at).total_seconds())
                execution.exit_code = process.returncode
                execution.stdout = stdout.decode('utf-8', errors='replace')
                execution.stderr = stderr.decode('utf-8', errors='replace')
                
            except asyncio.TimeoutError:
                process.kill()
                execution.status = CommandStatus.TIMEOUT
                execution.completed_at = datetime.utcnow()
                execution.duration_seconds = execution.timeout_seconds
                execution.exit_code = -1
                execution.stderr = f"Command timed out after {execution.timeout_seconds} seconds"
            
            await self._save_execution_result(execution)
            
        except Exception as e:
            self.logger.error(f"Local command execution failed: {str(e)}")
            await self._mark_execution_failed(execution.execution_id, str(e))

    async def _execute_docker_command(self, execution: CommandExecution):
        try:
            docker_command = f"docker exec -it {execution.metadata.get('container_id', 'default')} {execution.command}"
            
            process = await asyncio.create_subprocess_shell(
                docker_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=execution.working_directory,
                env={**os.environ, **execution.environment_vars}
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=execution.timeout_seconds
                )
                
                execution.status = CommandStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                execution.duration_seconds = int((execution.completed_at - execution.started_at).total_seconds())
                execution.exit_code = process.returncode
                execution.stdout = stdout.decode('utf-8', errors='replace')
                execution.stderr = stderr.decode('utf-8', errors='replace')
                
            except asyncio.TimeoutError:
                process.kill()
                execution.status = CommandStatus.TIMEOUT
                execution.completed_at = datetime.utcnow()
                execution.duration_seconds = execution.timeout_seconds
                execution.exit_code = -1
                execution.stderr = f"Docker command timed out after {execution.timeout_seconds} seconds"
            
            await self._save_execution_result(execution)
            
        except Exception as e:
            self.logger.error(f"Docker command execution failed: {str(e)}")
            await self._mark_execution_failed(execution.execution_id, str(e))

    async def _execute_ssh_command(self, execution: CommandExecution):
        try:
            ssh_host = execution.metadata.get('ssh_host', 'localhost')
            ssh_user = execution.metadata.get('ssh_user', 'root')
            ssh_key = execution.metadata.get('ssh_key', '')
            
            ssh_command = f"ssh -o StrictHostKeyChecking=no {ssh_user}@{ssh_host} '{execution.command}'"
            
            process = await asyncio.create_subprocess_shell(
                ssh_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=execution.working_directory,
                env={**os.environ, **execution.environment_vars}
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=execution.timeout_seconds
                )
                
                execution.status = CommandStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                execution.duration_seconds = int((execution.completed_at - execution.started_at).total_seconds())
                execution.exit_code = process.returncode
                execution.stdout = stdout.decode('utf-8', errors='replace')
                execution.stderr = stderr.decode('utf-8', errors='replace')
                
            except asyncio.TimeoutError:
                process.kill()
                execution.status = CommandStatus.TIMEOUT
                execution.completed_at = datetime.utcnow()
                execution.duration_seconds = execution.timeout_seconds
                execution.exit_code = -1
                execution.stderr = f"SSH command timed out after {execution.timeout_seconds} seconds"
            
            await self._save_execution_result(execution)
            
        except Exception as e:
            self.logger.error(f"SSH command execution failed: {str(e)}")
            await self._mark_execution_failed(execution.execution_id, str(e))

    async def _execute_kubernetes_command(self, execution: CommandExecution):
        try:
            pod_name = execution.metadata.get('pod_name', 'default-pod')
            namespace = execution.metadata.get('namespace', 'default')
            
            kubectl_command = f"kubectl exec {pod_name} -n {namespace} -- {execution.command}"
            
            process = await asyncio.create_subprocess_shell(
                kubectl_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=execution.working_directory,
                env={**os.environ, **execution.environment_vars}
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=execution.timeout_seconds
                )
                
                execution.status = CommandStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                execution.duration_seconds = int((execution.completed_at - execution.started_at).total_seconds())
                execution.exit_code = process.returncode
                execution.stdout = stdout.decode('utf-8', errors='replace')
                execution.stderr = stderr.decode('utf-8', errors='replace')
                
            except asyncio.TimeoutError:
                process.kill()
                execution.status = CommandStatus.TIMEOUT
                execution.completed_at = datetime.utcnow()
                execution.duration_seconds = execution.timeout_seconds
                execution.exit_code = -1
                execution.stderr = f"Kubernetes command timed out after {execution.timeout_seconds} seconds"
            
            await self._save_execution_result(execution)
            
        except Exception as e:
            self.logger.error(f"Kubernetes command execution failed: {str(e)}")
            await self._mark_execution_failed(execution.execution_id, str(e))

    async def _save_execution_result(self, execution: CommandExecution):
        try:
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE command_executions 
                    SET status = :status, completed_at = :completed_at, duration_seconds = :duration_seconds,
                        exit_code = :exit_code, stdout = :stdout, stderr = :stderr
                    WHERE execution_id = :execution_id
                """, {
                    "execution_id": execution.execution_id,
                    "status": execution.status.value,
                    "completed_at": execution.completed_at,
                    "duration_seconds": execution.duration_seconds,
                    "exit_code": execution.exit_code,
                    "stdout": execution.stdout,
                    "stderr": execution.stderr
                })
                await session.commit()
            
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]
            
            self.execution_history.append(execution)
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-1000:]
            
            self.logger.info(f"Command execution completed: {execution.execution_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save execution result: {str(e)}")

    async def _mark_execution_failed(self, execution_id: str, error_message: str):
        try:
            if execution_id in self.active_executions:
                execution = self.active_executions[execution_id]
                execution.status = CommandStatus.FAILED
                execution.completed_at = datetime.utcnow()
                execution.duration_seconds = int((execution.completed_at - execution.started_at).total_seconds())
                execution.exit_code = -1
                execution.stderr = error_message
                
                await self._save_execution_result(execution)
            
        except Exception as e:
            self.logger.error(f"Failed to mark execution as failed: {str(e)}")

    async def cancel_execution(self, execution_id: str) -> bool:
        try:
            if execution_id not in self.active_executions:
                return False
            
            execution = self.active_executions[execution_id]
            execution.status = CommandStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = int((execution.completed_at - execution.started_at).total_seconds())
            execution.exit_code = -1
            execution.stderr = "Command cancelled by user"
            
            await self._save_execution_result(execution)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel execution: {str(e)}")
            return False

    async def get_execution(self, execution_id: str) -> Optional[CommandExecution]:
        try:
            if execution_id in self.active_executions:
                return self.active_executions[execution_id]
            
            if not self.database:
                return None
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT execution_id, command, command_type, environment, status, user_id,
                           working_directory, environment_vars, timeout_seconds, started_at,
                           completed_at, duration_seconds, exit_code, stdout, stderr, metadata
                    FROM command_executions
                    WHERE execution_id = :execution_id
                """, {"execution_id": execution_id})
                
                row = result.fetchone()
                if not row:
                    return None
                
                execution = CommandExecution(
                    execution_id=row.execution_id,
                    command=row.command,
                    command_type=CommandType(row.command_type),
                    environment=ExecutionEnvironment(row.environment),
                    status=CommandStatus(row.status),
                    user_id=row.user_id,
                    working_directory=row.working_directory,
                    environment_vars=row.environment_vars or {},
                    timeout_seconds=row.timeout_seconds,
                    started_at=row.started_at,
                    completed_at=row.completed_at,
                    duration_seconds=row.duration_seconds,
                    exit_code=row.exit_code,
                    stdout=row.stdout or "",
                    stderr=row.stderr or "",
                    metadata=row.metadata or {}
                )
                
                return execution
                
        except Exception as e:
            self.logger.error(f"Failed to get execution: {str(e)}")
            return None

    async def get_executions(
        self,
        user_id: Optional[str] = None,
        status: Optional[CommandStatus] = None,
        command_type: Optional[CommandType] = None,
        environment: Optional[ExecutionEnvironment] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CommandExecution]:
        if not self.database:
            return []
        
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if user_id:
            conditions.append("user_id = :user_id")
            params["user_id"] = user_id
        
        if status:
            conditions.append("status = :status")
            params["status"] = status.value
        
        if command_type:
            conditions.append("command_type = :command_type")
            params["command_type"] = command_type.value
        
        if environment:
            conditions.append("environment = :environment")
            params["environment"] = environment.value
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT execution_id, command, command_type, environment, status, user_id,
                       working_directory, environment_vars, timeout_seconds, started_at,
                       completed_at, duration_seconds, exit_code, stdout, stderr, metadata
                FROM command_executions
                {where_clause}
                ORDER BY started_at DESC
                LIMIT :limit OFFSET :offset
            """, params)
            
            executions = []
            for row in result:
                execution = CommandExecution(
                    execution_id=row.execution_id,
                    command=row.command,
                    command_type=CommandType(row.command_type),
                    environment=ExecutionEnvironment(row.environment),
                    status=CommandStatus(row.status),
                    user_id=row.user_id,
                    working_directory=row.working_directory,
                    environment_vars=row.environment_vars or {},
                    timeout_seconds=row.timeout_seconds,
                    started_at=row.started_at,
                    completed_at=row.completed_at,
                    duration_seconds=row.duration_seconds,
                    exit_code=row.exit_code,
                    stdout=row.stdout or "",
                    stderr=row.stderr or "",
                    metadata=row.metadata or {}
                )
                executions.append(execution)
            
            return executions

    async def create_command_template(
        self,
        template_id: str,
        name: str,
        description: str,
        command_template: str,
        command_type: CommandType,
        environment: ExecutionEnvironment,
        parameters: Optional[List[str]] = None,
        timeout_seconds: int = 300
    ) -> bool:
        try:
            if not self.database:
                return False
            
            template = CommandTemplate(
                template_id=template_id,
                name=name,
                description=description,
                command_template=command_template,
                command_type=command_type,
                environment=environment,
                parameters=parameters or [],
                timeout_seconds=timeout_seconds,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO command_templates (
                        template_id, name, description, command_template, command_type,
                        environment, parameters, timeout_seconds
                    ) VALUES (
                        :template_id, :name, :description, :command_template, :command_type,
                        :environment, :parameters, :timeout_seconds
                    )
                """, {
                    "template_id": template.template_id,
                    "name": template.name,
                    "description": template.description,
                    "command_template": template.command_template,
                    "command_type": template.command_type.value,
                    "environment": template.environment.value,
                    "parameters": template.parameters,
                    "timeout_seconds": template.timeout_seconds
                })
                await session.commit()
            
            self.command_templates[template_id] = template
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create command template: {str(e)}")
            return False

    async def execute_template(
        self,
        template_id: str,
        user_id: str,
        parameters: Optional[Dict[str, str]] = None,
        working_directory: str = "/tmp",
        environment_vars: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        try:
            if template_id not in self.command_templates:
                return None
            
            template = self.command_templates[template_id]
            command = template.command_template
            
            if parameters:
                for param_name, param_value in parameters.items():
                    command = command.replace(f"{{{param_name}}}", param_value)
            
            return await self.execute_command(
                command=command,
                command_type=template.command_type,
                environment=template.environment,
                user_id=user_id,
                working_directory=working_directory,
                environment_vars=environment_vars,
                timeout_seconds=template.timeout_seconds,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Failed to execute template: {str(e)}")
            return None

    async def get_command_stats(
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
                    COUNT(*) as total_executions,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions,
                    COUNT(CASE WHEN status = 'timeout' THEN 1 END) as timeout_executions,
                    COUNT(CASE WHEN command_type = 'shell' THEN 1 END) as shell_commands,
                    COUNT(CASE WHEN command_type = 'python' THEN 1 END) as python_commands,
                    COUNT(CASE WHEN command_type = 'sql' THEN 1 END) as sql_commands,
                    COUNT(CASE WHEN environment = 'local' THEN 1 END) as local_executions,
                    COUNT(CASE WHEN environment = 'docker' THEN 1 END) as docker_executions,
                    AVG(duration_seconds) as avg_duration_seconds,
                    AVG(exit_code) as avg_exit_code
                FROM command_executions
                WHERE started_at BETWEEN :start_date AND :end_date
            """, {"start_date": start_date, "end_date": end_date})
            
            row = result.fetchone()
            if not row:
                return {}
            
            return {
                "total_executions": row.total_executions,
                "successful_executions": row.successful_executions,
                "failed_executions": row.failed_executions,
                "timeout_executions": row.timeout_executions,
                "shell_commands": row.shell_commands,
                "python_commands": row.python_commands,
                "sql_commands": row.sql_commands,
                "local_executions": row.local_executions,
                "docker_executions": row.docker_executions,
                "avg_duration_seconds": float(row.avg_duration_seconds) if row.avg_duration_seconds else 0.0,
                "avg_exit_code": float(row.avg_exit_code) if row.avg_exit_code else 0.0,
                "success_rate": (row.successful_executions / row.total_executions * 100) if row.total_executions > 0 else 0
            }

_command_executor: Optional[CommandExecutor] = None

async def get_command_executor() -> CommandExecutor:
    global _command_executor
    if _command_executor is None:
        _command_executor = CommandExecutor()
        await _command_executor.initialize()
    return _command_executor

async def init_command_executor() -> CommandExecutor:
    return await get_command_executor()
