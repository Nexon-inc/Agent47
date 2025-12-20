import asyncio
import subprocess
import json
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from sqlalchemy import text

from core.database import get_database, DatabaseManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class DeploymentStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"

class DeploymentType(Enum):
    APPLICATION = "application"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    CONFIGURATION = "configuration"
    SECURITY = "security"

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

@dataclass
class Deployment:
    deployment_id: str
    name: str
    description: str
    deployment_type: DeploymentType
    environment: Environment
    status: DeploymentStatus
    version: str
    target_servers: List[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: str
    metadata: Dict[str, Any]

@dataclass
class DeploymentStep:
    step_id: str
    deployment_id: str
    step_name: str
    step_type: str
    status: DeploymentStatus
    order: int
    command: str
    timeout_seconds: int
    retry_count: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    output: Optional[str]
    error_message: Optional[str]

class DeploymentManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.active_deployments: Dict[str, Deployment] = {}
        self.deployment_templates: Dict[str, Dict[str, Any]] = {}
        self.max_concurrent_deployments = 5
        self.default_timeout_minutes = 30
        self.rollback_enabled = True

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing DeploymentManager...")
            self.database = get_database()
            await self._setup_deployment_tables()
            await self._load_deployment_templates()
            self.logger.info("DeploymentManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize DeploymentManager: {str(e)}")
            return False

    async def _setup_deployment_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS deployments (
                    id SERIAL PRIMARY KEY,
                    deployment_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    deployment_type VARCHAR(50) NOT NULL,
                    environment VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    version VARCHAR(100) NOT NULL,
                    target_servers JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_by VARCHAR(255) NOT NULL,
                    metadata JSONB
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS deployment_steps (
                    id SERIAL PRIMARY KEY,
                    step_id VARCHAR(255) UNIQUE NOT NULL,
                    deployment_id VARCHAR(255) NOT NULL,
                    step_name VARCHAR(255) NOT NULL,
                    step_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    step_order INTEGER NOT NULL,
                    command TEXT NOT NULL,
                    timeout_seconds INTEGER DEFAULT 300,
                    retry_count INTEGER DEFAULT 0,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    output TEXT,
                    error_message TEXT,
                    FOREIGN KEY (deployment_id) REFERENCES deployments(deployment_id)
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS deployment_templates (
                    id SERIAL PRIMARY KEY,
                    template_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    deployment_type VARCHAR(50) NOT NULL,
                    environment VARCHAR(20) NOT NULL,
                    steps JSONB NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_deployments_status 
                ON deployments(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_deployments_environment 
                ON deployments(environment);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_deployments_created_at 
                ON deployments(created_at);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_deployment_steps_deployment_id 
                ON deployment_steps(deployment_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_deployment_steps_status 
                ON deployment_steps(status);
            """)
            
            await session.commit()

    async def _load_deployment_templates(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT template_id, name, description, deployment_type, environment, steps
                FROM deployment_templates
                WHERE is_active = TRUE
            """)
            
            for row in result:
                self.deployment_templates[row.template_id] = {
                    "name": row.name,
                    "description": row.description,
                    "deployment_type": row.deployment_type,
                    "environment": row.environment,
                    "steps": row.steps
                }

    async def create_deployment(
        self,
        name: str,
        description: str,
        deployment_type: DeploymentType,
        environment: Environment,
        version: str,
        target_servers: List[str],
        template_id: Optional[str] = None,
        custom_steps: Optional[List[Dict[str, Any]]] = None,
        created_by: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        try:
            if len(self.active_deployments) >= self.max_concurrent_deployments:
                self.logger.warning("Maximum concurrent deployments reached")
                return None
            
            deployment_id = f"deploy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(name) % 10000}"
            
            deployment = Deployment(
                deployment_id=deployment_id,
                name=name,
                description=description,
                deployment_type=deployment_type,
                environment=environment,
                status=DeploymentStatus.PENDING,
                version=version,
                target_servers=target_servers,
                created_at=datetime.utcnow(),
                started_at=None,
                completed_at=None,
                created_by=created_by,
                metadata=metadata or {}
            )
            
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO deployments (
                        deployment_id, name, description, deployment_type, environment,
                        status, version, target_servers, created_by, metadata
                    ) VALUES (
                        :deployment_id, :name, :description, :deployment_type, :environment,
                        :status, :version, :target_servers, :created_by, :metadata
                    )
                """, {
                    "deployment_id": deployment.deployment_id,
                    "name": deployment.name,
                    "description": deployment.description,
                    "deployment_type": deployment.deployment_type.value,
                    "environment": deployment.environment.value,
                    "status": deployment.status.value,
                    "version": deployment.version,
                    "target_servers": deployment.target_servers,
                    "created_by": deployment.created_by,
                    "metadata": deployment.metadata
                })
                
                steps = []
                if template_id and template_id in self.deployment_templates:
                    steps = self.deployment_templates[template_id]["steps"]
                elif custom_steps:
                    steps = custom_steps
                else:
                    steps = self._get_default_steps(deployment_type, environment)
                
                for i, step_config in enumerate(steps):
                    step_id = f"step_{deployment_id}_{i+1}"
                    await session.execute("""
                        INSERT INTO deployment_steps (
                            step_id, deployment_id, step_name, step_type, status,
                            step_order, command, timeout_seconds
                        ) VALUES (
                            :step_id, :deployment_id, :step_name, :step_type, :status,
                            :step_order, :command, :timeout_seconds
                        )
                    """, {
                        "step_id": step_id,
                        "deployment_id": deployment_id,
                        "step_name": step_config.get("name", f"Step {i+1}"),
                        "step_type": step_config.get("type", "command"),
                        "status": DeploymentStatus.PENDING.value,
                        "step_order": i + 1,
                        "command": step_config.get("command", ""),
                        "timeout_seconds": step_config.get("timeout_seconds", 300)
                    })
                
                await session.commit()
            
            self.active_deployments[deployment_id] = deployment
            self.logger.info(f"Deployment created: {deployment_id}")
            return deployment_id
            
        except Exception as e:
            self.logger.error(f"Failed to create deployment: {str(e)}")
            return None

    def _get_default_steps(self, deployment_type: DeploymentType, environment: Environment) -> List[Dict[str, Any]]:
        if deployment_type == DeploymentType.APPLICATION:
            return [
                {
                    "name": "Backup Current Version",
                    "type": "backup",
                    "command": "backup_application.sh",
                    "timeout_seconds": 600
                },
                {
                    "name": "Download New Version",
                    "type": "download",
                    "command": "download_version.sh",
                    "timeout_seconds": 300
                },
                {
                    "name": "Deploy Application",
                    "type": "deploy",
                    "command": "deploy_application.sh",
                    "timeout_seconds": 900
                },
                {
                    "name": "Health Check",
                    "type": "health_check",
                    "command": "health_check.sh",
                    "timeout_seconds": 120
                }
            ]
        elif deployment_type == DeploymentType.DATABASE:
            return [
                {
                    "name": "Database Backup",
                    "type": "backup",
                    "command": "backup_database.sh",
                    "timeout_seconds": 1800
                },
                {
                    "name": "Run Migrations",
                    "type": "migration",
                    "command": "run_migrations.sh",
                    "timeout_seconds": 600
                },
                {
                    "name": "Verify Schema",
                    "type": "verification",
                    "command": "verify_schema.sh",
                    "timeout_seconds": 300
                }
            ]
        elif deployment_type == DeploymentType.INFRASTRUCTURE:
            return [
                {
                    "name": "Validate Infrastructure",
                    "type": "validation",
                    "command": "validate_infrastructure.sh",
                    "timeout_seconds": 300
                },
                {
                    "name": "Deploy Infrastructure",
                    "type": "deploy",
                    "command": "deploy_infrastructure.sh",
                    "timeout_seconds": 1800
                },
                {
                    "name": "Verify Deployment",
                    "type": "verification",
                    "command": "verify_deployment.sh",
                    "timeout_seconds": 600
                }
            ]
        else:
            return [
                {
                    "name": "Execute Command",
                    "type": "command",
                    "command": "execute.sh",
                    "timeout_seconds": 300
                }
            ]

    async def start_deployment(self, deployment_id: str) -> bool:
        try:
            if deployment_id not in self.active_deployments:
                return False
            
            deployment = self.active_deployments[deployment_id]
            if deployment.status != DeploymentStatus.PENDING:
                return False
            
            deployment.status = DeploymentStatus.IN_PROGRESS
            deployment.started_at = datetime.utcnow()
            
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE deployments 
                    SET status = :status, started_at = :started_at
                    WHERE deployment_id = :deployment_id
                """, {
                    "deployment_id": deployment_id,
                    "status": deployment.status.value,
                    "started_at": deployment.started_at
                })
                await session.commit()
            
            asyncio.create_task(self._execute_deployment(deployment_id))
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start deployment: {str(e)}")
            return False

    async def _execute_deployment(self, deployment_id: str):
        try:
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT step_id, step_name, step_type, command, timeout_seconds
                    FROM deployment_steps
                    WHERE deployment_id = :deployment_id
                    ORDER BY step_order
                """, {"deployment_id": deployment_id})
                
                steps = result.fetchall()
            
            for step_row in steps:
                step_id = step_row.step_id
                step_name = step_row.step_name
                step_type = step_row.step_type
                command = step_row.command
                timeout_seconds = step_row.timeout_seconds
                
                await self._execute_step(deployment_id, step_id, step_name, step_type, command, timeout_seconds)
                
                if deployment_id in self.active_deployments:
                    deployment = self.active_deployments[deployment_id]
                    if deployment.status == DeploymentStatus.FAILED:
                        if self.rollback_enabled:
                            await self._rollback_deployment(deployment_id)
                        break
            
            if deployment_id in self.active_deployments:
                deployment = self.active_deployments[deployment_id]
                if deployment.status == DeploymentStatus.IN_PROGRESS:
                    deployment.status = DeploymentStatus.SUCCESS
                    deployment.completed_at = datetime.utcnow()
                    
                    async with self.database.get_session() as session:
                        await session.execute("""
                            UPDATE deployments 
                            SET status = :status, completed_at = :completed_at
                            WHERE deployment_id = :deployment_id
                        """, {
                            "deployment_id": deployment_id,
                            "status": deployment.status.value,
                            "completed_at": deployment.completed_at
                        })
                        await session.commit()
                    
                    self.logger.info(f"Deployment completed successfully: {deployment_id}")
                    del self.active_deployments[deployment_id]
            
        except Exception as e:
            self.logger.error(f"Deployment execution failed: {str(e)}")
            await self._mark_deployment_failed(deployment_id, str(e))

    async def _execute_step(
        self,
        deployment_id: str,
        step_id: str,
        step_name: str,
        step_type: str,
        command: str,
        timeout_seconds: int
    ):
        try:
            await self._update_step_status(step_id, DeploymentStatus.IN_PROGRESS)
            
            if step_type == "command":
                result = await self._execute_command(command, timeout_seconds)
            elif step_type == "script":
                result = await self._execute_script(command, timeout_seconds)
            elif step_type == "api_call":
                result = await self._execute_api_call(command, timeout_seconds)
            else:
                result = {"success": False, "output": "", "error": f"Unknown step type: {step_type}"}
            
            if result["success"]:
                await self._update_step_status(step_id, DeploymentStatus.SUCCESS, result["output"])
            else:
                await self._update_step_status(step_id, DeploymentStatus.FAILED, None, result["error"])
                await self._mark_deployment_failed(deployment_id, result["error"])
            
        except Exception as e:
            self.logger.error(f"Step execution failed: {str(e)}")
            await self._update_step_status(step_id, DeploymentStatus.FAILED, None, str(e))
            await self._mark_deployment_failed(deployment_id, str(e))

    async def _execute_command(self, command: str, timeout_seconds: int) -> Dict[str, Any]:
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds
            )
            
            output = stdout.decode('utf-8') if stdout else ""
            error = stderr.decode('utf-8') if stderr else ""
            
            return {
                "success": process.returncode == 0,
                "output": output,
                "error": error
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "output": "",
                "error": f"Command timed out after {timeout_seconds} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }

    async def _execute_script(self, script_path: str, timeout_seconds: int) -> Dict[str, Any]:
        try:
            if not Path(script_path).exists():
                return {
                    "success": False,
                    "output": "",
                    "error": f"Script not found: {script_path}"
                }
            
            process = await asyncio.create_subprocess_exec(
                "bash", script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds
            )
            
            output = stdout.decode('utf-8') if stdout else ""
            error = stderr.decode('utf-8') if stderr else ""
            
            return {
                "success": process.returncode == 0,
                "output": output,
                "error": error
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "output": "",
                "error": f"Script timed out after {timeout_seconds} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }

    async def _execute_api_call(self, api_config: str, timeout_seconds: int) -> Dict[str, Any]:
        try:
            import requests
            
            config = json.loads(api_config)
            method = config.get("method", "GET").upper()
            url = config.get("url", "")
            headers = config.get("headers", {})
            data = config.get("data", {})
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout_seconds)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=timeout_seconds)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=timeout_seconds)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=timeout_seconds)
            else:
                return {
                    "success": False,
                    "output": "",
                    "error": f"Unsupported HTTP method: {method}"
                }
            
            return {
                "success": response.status_code < 400,
                "output": response.text,
                "error": "" if response.status_code < 400 else f"HTTP {response.status_code}: {response.text}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }

    async def _update_step_status(
        self,
        step_id: str,
        status: DeploymentStatus,
        output: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        if not self.database:
            return
        
        update_fields = ["status = :status"]
        params = {"step_id": step_id, "status": status.value}
        
        if status == DeploymentStatus.IN_PROGRESS:
            update_fields.append("started_at = :started_at")
            params["started_at"] = datetime.utcnow()
        elif status in [DeploymentStatus.SUCCESS, DeploymentStatus.FAILED]:
            update_fields.append("completed_at = :completed_at")
            params["completed_at"] = datetime.utcnow()
        
        if output is not None:
            update_fields.append("output = :output")
            params["output"] = output
        
        if error_message is not None:
            update_fields.append("error_message = :error_message")
            params["error_message"] = error_message
        
        async with self.database.get_session() as session:
            await session.execute(f"""
                UPDATE deployment_steps 
                SET {', '.join(update_fields)}
                WHERE step_id = :step_id
            """, params)
            await session.commit()

    async def _mark_deployment_failed(self, deployment_id: str, error_message: str):
        if deployment_id in self.active_deployments:
            deployment = self.active_deployments[deployment_id]
            deployment.status = DeploymentStatus.FAILED
            deployment.completed_at = datetime.utcnow()
        
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute("""
                UPDATE deployments 
                SET status = :status, completed_at = :completed_at
                WHERE deployment_id = :deployment_id
            """, {
                "deployment_id": deployment_id,
                "status": DeploymentStatus.FAILED.value,
                "completed_at": datetime.utcnow()
            })
            await session.commit()

    async def _rollback_deployment(self, deployment_id: str):
        try:
            if deployment_id not in self.active_deployments:
                return
            
            deployment = self.active_deployments[deployment_id]
            deployment.status = DeploymentStatus.ROLLED_BACK
            deployment.completed_at = datetime.utcnow()
            
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE deployments 
                    SET status = :status, completed_at = :completed_at
                    WHERE deployment_id = :deployment_id
                """, {
                    "deployment_id": deployment_id,
                    "status": deployment.status.value,
                    "completed_at": deployment.completed_at
                })
                await session.commit()
            
            self.logger.info(f"Deployment rolled back: {deployment_id}")
            del self.active_deployments[deployment_id]
            
        except Exception as e:
            self.logger.error(f"Failed to rollback deployment: {str(e)}")

    async def cancel_deployment(self, deployment_id: str) -> bool:
        try:
            if deployment_id not in self.active_deployments:
                return False
            
            deployment = self.active_deployments[deployment_id]
            deployment.status = DeploymentStatus.CANCELLED
            deployment.completed_at = datetime.utcnow()
            
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE deployments 
                    SET status = :status, completed_at = :completed_at
                    WHERE deployment_id = :deployment_id
                """, {
                    "deployment_id": deployment_id,
                    "status": deployment.status.value,
                    "completed_at": deployment.completed_at
                })
                await session.commit()
            
            del self.active_deployments[deployment_id]
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel deployment: {str(e)}")
            return False

    async def get_deployments(
        self,
        status: Optional[DeploymentStatus] = None,
        environment: Optional[Environment] = None,
        deployment_type: Optional[DeploymentType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Deployment]:
        if not self.database:
            return []
        
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if status:
            conditions.append("status = :status")
            params["status"] = status.value
        
        if environment:
            conditions.append("environment = :environment")
            params["environment"] = environment.value
        
        if deployment_type:
            conditions.append("deployment_type = :deployment_type")
            params["deployment_type"] = deployment_type.value
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT deployment_id, name, description, deployment_type, environment,
                       status, version, target_servers, created_at, started_at, completed_at,
                       created_by, metadata
                FROM deployments
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """, params)
            
            deployments = []
            for row in result:
                deployment = Deployment(
                    deployment_id=row.deployment_id,
                    name=row.name,
                    description=row.description,
                    deployment_type=DeploymentType(row.deployment_type),
                    environment=Environment(row.environment),
                    status=DeploymentStatus(row.status),
                    version=row.version,
                    target_servers=row.target_servers,
                    created_at=row.created_at,
                    started_at=row.started_at,
                    completed_at=row.completed_at,
                    created_by=row.created_by,
                    metadata=row.metadata or {}
                )
                deployments.append(deployment)
            
            return deployments

    async def get_deployment_steps(self, deployment_id: str) -> List[DeploymentStep]:
        if not self.database:
            return []
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT step_id, deployment_id, step_name, step_type, status, step_order,
                       command, timeout_seconds, retry_count, started_at, completed_at,
                       output, error_message
                FROM deployment_steps
                WHERE deployment_id = :deployment_id
                ORDER BY step_order
            """, {"deployment_id": deployment_id})
            
            steps = []
            for row in result:
                step = DeploymentStep(
                    step_id=row.step_id,
                    deployment_id=row.deployment_id,
                    step_name=row.step_name,
                    step_type=row.step_type,
                    status=DeploymentStatus(row.status),
                    order=row.step_order,
                    command=row.command,
                    timeout_seconds=row.timeout_seconds,
                    retry_count=row.retry_count,
                    started_at=row.started_at,
                    completed_at=row.completed_at,
                    output=row.output,
                    error_message=row.error_message
                )
                steps.append(step)
            
            return steps

    async def get_deployment_stats(
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
                    COUNT(*) as total_deployments,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_deployments,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_deployments,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_deployments,
                    COUNT(CASE WHEN deployment_type = 'application' THEN 1 END) as application_deployments,
                    COUNT(CASE WHEN deployment_type = 'database' THEN 1 END) as database_deployments,
                    COUNT(CASE WHEN deployment_type = 'infrastructure' THEN 1 END) as infrastructure_deployments,
                    COUNT(CASE WHEN environment = 'production' THEN 1 END) as production_deployments,
                    COUNT(CASE WHEN environment = 'staging' THEN 1 END) as staging_deployments,
                    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))/60) as avg_duration_minutes
                FROM deployments
                WHERE created_at BETWEEN :start_date AND :end_date
                AND completed_at IS NOT NULL
            """, {"start_date": start_date, "end_date": end_date})
            
            row = result.fetchone()
            if not row:
                return {}
            
            return {
                "total_deployments": row.total_deployments,
                "successful_deployments": row.successful_deployments,
                "failed_deployments": row.failed_deployments,
                "in_progress_deployments": row.in_progress_deployments,
                "application_deployments": row.application_deployments,
                "database_deployments": row.database_deployments,
                "infrastructure_deployments": row.infrastructure_deployments,
                "production_deployments": row.production_deployments,
                "staging_deployments": row.staging_deployments,
                "avg_duration_minutes": float(row.avg_duration_minutes) if row.avg_duration_minutes else 0.0,
                "success_rate": (row.successful_deployments / row.total_deployments * 100) if row.total_deployments > 0 else 0
            }

    async def create_deployment_template(
        self,
        template_id: str,
        name: str,
        description: str,
        deployment_type: DeploymentType,
        environment: Environment,
        steps: List[Dict[str, Any]]
    ) -> bool:
        try:
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO deployment_templates (
                        template_id, name, description, deployment_type, environment, steps
                    ) VALUES (
                        :template_id, :name, :description, :deployment_type, :environment, :steps
                    )
                """, {
                    "template_id": template_id,
                    "name": name,
                    "description": description,
                    "deployment_type": deployment_type.value,
                    "environment": environment.value,
                    "steps": steps
                })
                await session.commit()
            
            await self._load_deployment_templates()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create deployment template: {str(e)}")
            return False

_deployment_manager: Optional[DeploymentManager] = None

async def get_deployment_manager() -> DeploymentManager:
    global _deployment_manager
    if _deployment_manager is None:
        _deployment_manager = DeploymentManager()
        await _deployment_manager.initialize()
    return _deployment_manager

async def init_deployment_manager() -> DeploymentManager:
    return await get_deployment_manager()
