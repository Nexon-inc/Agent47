import asyncio
import os
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from core.database import get_database, DatabaseManager
from core.cache import get_redis, RedisManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings
from .terminal_manager import get_terminal_manager, TerminalManager
from .error_monitor import get_error_monitor, ErrorMonitor

logger = get_logger(__name__)

class CodeOperation(Enum):
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    EXECUTE_COMMAND = "execute_command"
    ANALYZE_CODE = "analyze_code"
    DEBUG_ERROR = "debug_error"
    DEPLOY_CODE = "deploy_code"
    ROLLBACK_CODE = "rollback_code"

class CodeHealthStatus(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class CodeHealthMetrics:
    total_files: int
    error_count: int
    warning_count: int
    test_coverage: float
    complexity_score: float
    maintainability_index: float
    last_updated: datetime
    health_status: CodeHealthStatus

@dataclass
class CodeOperation:
    id: str
    operation_type: str
    target_file: str
    operation_data: Dict[str, Any]
    timestamp: datetime
    user_id: str
    status: str
    result: Optional[str] = None
    error_message: Optional[str] = None

class CodeManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.terminal_manager: Optional[TerminalManager] = None
        self.error_monitor: Optional[ErrorMonitor] = None
        self.settings = get_settings()
        
        self.active_operations: Dict[str, CodeOperation] = {}
        self.code_health_cache: Dict[str, CodeHealthMetrics] = {}
        self.logger = logger

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing CodeManager...")
            
            self.database = get_database()
            self.redis = await get_redis()
            self.terminal_manager = await get_terminal_manager()
            self.error_monitor = await get_error_monitor()
            
            await self._setup_code_manager_tables()
            await self._load_active_operations()
            
            self.logger.info("CodeManager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize CodeManager: {str(e)}")
            return False

    async def _setup_code_manager_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS code_operations (
                    id VARCHAR(255) PRIMARY KEY,
                    operation_type VARCHAR(100) NOT NULL,
                    target_file VARCHAR(500) NOT NULL,
                    operation_data JSONB NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    result TEXT,
                    error_message TEXT
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS code_health_snapshots (
                    id SERIAL PRIMARY KEY,
                    snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_files INTEGER NOT NULL,
                    error_count INTEGER NOT NULL,
                    warning_count INTEGER NOT NULL,
                    test_coverage DECIMAL(5,2),
                    complexity_score DECIMAL(5,2),
                    maintainability_index DECIMAL(5,2),
                    health_status VARCHAR(50) NOT NULL,
                    metadata JSONB
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS code_deployments (
                    id SERIAL PRIMARY KEY,
                    deployment_id VARCHAR(255) UNIQUE NOT NULL,
                    version VARCHAR(100) NOT NULL,
                    description TEXT,
                    deployed_by VARCHAR(255) NOT NULL,
                    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50) NOT NULL,
                    rollback_version VARCHAR(100),
                    metadata JSONB
                )
            """)
            
            await session.commit()

    async def _load_active_operations(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT id, operation_type, target_file, operation_data, timestamp, user_id, status, result, error_message
                FROM code_operations WHERE status IN ('pending', 'in_progress')
            """)
            
            rows = result.fetchall()
            for row in result.fetchall():
                operation = CodeOperation(
                    id=row[0],
                    operation_type=row[1],
                    target_file=row[2],
                    operation_data=row[3],
                    timestamp=row[4],
                    user_id=row[5],
                    status=row[6],
                    result=row[7],
                    error_message=row[8]
                )
                self.active_operations[operation.id] = operation

    async def read_file(self, file_path: str, user_id: str, session_id: str = None) -> Dict[str, Any]:
        try:
            # Validate file path
            if not self._is_file_path_safe(file_path):
                raise ValueError("File path not allowed for security reasons")
            
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Analyze file content
            file_analysis = await self._analyze_file_content(file_path, content)
            
            # Log operation
            await self._log_code_operation(
                "read_file", file_path, {"file_size": len(content)}, user_id, "completed"
            )
            
            return {
                "file_path": file_path,
                "content": content,
                "file_size": len(content),
                "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                "analysis": file_analysis
            }
            
        except Exception as e:
            await self._log_code_operation(
                "read_file", file_path, {"error": str(e)}, user_id, "failed", str(e)
            )
            raise

    async def write_file(self, file_path: str, content: str, user_id: str, backup: bool = True) -> Dict[str, Any]:
        try:
            # Validate file path
            if not self._is_file_path_safe(file_path):
                raise ValueError("File path not allowed for security reasons")
            
            # Create backup if requested
            backup_path = None
            if backup and os.path.exists(file_path):
                backup_path = await self._create_file_backup(file_path)
            
            # Write file content
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            # Analyze updated file
            file_analysis = await self._analyze_file_content(file_path, content)
            
            # Log operation
            await self._log_code_operation(
                "write_file", file_path, {
                    "file_size": len(content),
                    "backup_created": backup_path is not None,
                    "backup_path": backup_path
                }, user_id, "completed"
            )
            
            return {
                "file_path": file_path,
                "file_size": len(content),
                "backup_created": backup_path is not None,
                "backup_path": backup_path,
                "analysis": file_analysis
            }
            
        except Exception as e:
            await self._log_code_operation(
                "write_file", file_path, {"error": str(e)}, user_id, "failed", str(e)
            )
            raise

    async def execute_terminal_command(self, command: str, user_id: str, session_id: str = None, 
                                     timeout_seconds: int = 300) -> Dict[str, Any]:
        try:
            if not self.terminal_manager:
                raise RuntimeError("Terminal manager not initialized")
            
            # Create terminal session if not provided
            if not session_id:
                from .terminal_manager import TerminalPermission
                session = await self.terminal_manager.create_terminal_session(
                    user_id, [TerminalPermission.BASIC_EXECUTION]
                )
                session_id = session.session_id
            
            # Execute command
            result = await self.terminal_manager.execute_command(
                session_id, command, timeout_seconds
            )
            
            # Log operation
            await self._log_code_operation(
                "execute_command", "terminal", {
                    "command": command,
                    "exit_code": result.exit_code,
                    "execution_time": result.execution_time
                }, user_id, "completed"
            )
            
            return {
                "command": command,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": result.execution_time,
                "status": result.status.value
            }
            
        except Exception as e:
            await self._log_code_operation(
                "execute_command", "terminal", {"error": str(e)}, user_id, "failed", str(e)
            )
            raise

    async def analyze_code_health(self, directory_path: str = None) -> CodeHealthMetrics:
        try:
            if not directory_path:
                directory_path = os.getcwd()
            
            # Check if analysis is cached and recent
            cache_key = f"code_health:{directory_path}"
            if self.redis:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    cached_metrics = json.loads(cached_data)
                    last_updated = datetime.fromisoformat(cached_metrics["last_updated"])
                    if datetime.utcnow() - last_updated < timedelta(minutes=30):
                        return CodeHealthMetrics(**cached_metrics)
            
            # Perform code health analysis
            metrics = await self._perform_code_health_analysis(directory_path)
            
            # Cache results
            if self.redis:
                cache_data = {
                    "total_files": metrics.total_files,
                    "error_count": metrics.error_count,
                    "warning_count": metrics.warning_count,
                    "test_coverage": metrics.test_coverage,
                    "complexity_score": metrics.complexity_score,
                    "maintainability_index": metrics.maintainability_index,
                    "last_updated": metrics.last_updated.isoformat(),
                    "health_status": metrics.health_status.value
                }
                await self.redis.set(cache_key, json.dumps(cache_data), expire=1800)  # 30 minutes
            
            # Store snapshot in database
            await self._store_code_health_snapshot(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to analyze code health: {str(e)}")
            raise

    async def _perform_code_health_analysis(self, directory_path: str) -> CodeHealthMetrics:
        try:
            total_files = 0
            error_count = 0
            warning_count = 0
            test_coverage = 0.0
            complexity_score = 0.0
            maintainability_index = 0.0
            
            # Count files and analyze code
            for root, dirs, files in os.walk(directory_path):
                # Skip hidden directories and common exclusions
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.git']]
                
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c')):
                        total_files += 1
                        file_path = os.path.join(root, file)
                        
                        # Analyze individual file
                        file_metrics = await self._analyze_file_health(file_path)
                        error_count += file_metrics.get("errors", 0)
                        warning_count += file_metrics.get("warnings", 0)
                        complexity_score += file_metrics.get("complexity", 0)
                        maintainability_index += file_metrics.get("maintainability", 0)
            
            # Calculate averages
            if total_files > 0:
                complexity_score /= total_files
                maintainability_index /= total_files
            
            # Determine health status
            health_status = self._calculate_health_status(
                error_count, warning_count, complexity_score, maintainability_index
            )
            
            return CodeHealthMetrics(
                total_files=total_files,
                error_count=error_count,
                warning_count=warning_count,
                test_coverage=test_coverage,
                complexity_score=complexity_score,
                maintainability_index=maintainability_index,
                last_updated=datetime.utcnow(),
                health_status=health_status
            )
            
        except Exception as e:
            self.logger.error(f"Error in code health analysis: {str(e)}")
            # Return default metrics on error
            return CodeHealthMetrics(
                total_files=0,
                error_count=1,
                warning_count=0,
                test_coverage=0.0,
                complexity_score=0.0,
                maintainability_index=0.0,
                last_updated=datetime.utcnow(),
                health_status=CodeHealthStatus.CRITICAL
            )

    async def _analyze_file_health(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            lines = content.split('\n')
            metrics = {
                "errors": 0,
                "warnings": 0,
                "complexity": 0,
                "maintainability": 0
            }
            
            # Simple complexity analysis
            for line in lines:
                line = line.strip()
                if line.startswith(('if ', 'for ', 'while ', 'except ', 'with ')):
                    metrics["complexity"] += 1
                if line.startswith('#'):
                    metrics["maintainability"] += 1
            
            # Normalize scores
            metrics["complexity"] = min(10.0, metrics["complexity"] / max(len(lines), 1) * 100)
            metrics["maintainability"] = min(100.0, metrics["maintainability"] / max(len(lines), 1) * 100)
            
            return metrics
            
        except Exception:
            return {"errors": 0, "warnings": 0, "complexity": 0, "maintainability": 0}

    def _calculate_health_status(self, error_count: int, warning_count: int, 
                                complexity_score: float, maintainability_index: float) -> CodeHealthStatus:
        if error_count > 100 or complexity_score > 80:
            return CodeHealthStatus.CRITICAL
        elif error_count > 50 or complexity_score > 60:
            return CodeHealthStatus.POOR
        elif error_count > 20 or complexity_score > 40:
            return CodeHealthStatus.FAIR
        elif error_count > 5 or complexity_score > 20:
            return CodeHealthStatus.GOOD
        else:
            return CodeHealthStatus.EXCELLENT

    async def _analyze_file_content(self, file_path: str, content: str) -> Dict[str, Any]:
        try:
            analysis = {
                "file_type": os.path.splitext(file_path)[1],
                "line_count": len(content.split('\n')),
                "character_count": len(content),
                "has_errors": False,
                "suggestions": []
            }
            
            # Basic content analysis
            if content.strip() == "":
                analysis["suggestions"].append("File is empty")
            
            if len(content.split('\n')) > 1000:
                analysis["suggestions"].append("File is very long - consider breaking it down")
            
            if content.count('\t') > 0:
                analysis["suggestions"].append("File contains tabs - consider using spaces for consistency")
            
            return analysis
            
        except Exception:
            return {"file_type": "unknown", "line_count": 0, "character_count": 0, "has_errors": True, "suggestions": []}

    async def _create_file_backup(self, file_path: str) -> str:
        try:
            backup_dir = os.path.join(os.path.dirname(file_path), ".backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            filename = os.path.basename(file_path)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{filename}.backup_{timestamp}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Copy file
            with open(file_path, 'r', encoding='utf-8') as source:
                with open(backup_path, 'w', encoding='utf-8') as backup:
                    backup.write(source.read())
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {str(e)}")
            return None

    def _is_file_path_safe(self, file_path: str) -> bool:
        try:
            abs_path = os.path.abspath(file_path)
            
            # Check for restricted directories
            restricted_dirs = [
                "/etc", "/var/log", "/proc", "/sys", "/dev",
                "C:\\Windows\\System32", "C:\\Windows\\SysWOW64"
            ]
            
            for restricted in restricted_dirs:
                if abs_path.startswith(restricted):
                    return False
            
            # Check for allowed file extensions
            allowed_extensions = [
                '.py', '.js', '.ts', '.html', '.css', '.json', '.yml', '.yaml',
                '.md', '.txt', '.log', '.conf', '.ini', '.env', '.sh', '.bat'
            ]
            
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in allowed_extensions:
                return False
            
            return True
            
        except Exception:
            return False

    async def _log_code_operation(self, operation_type: str, target_file: str, 
                                 operation_data: Dict[str, Any], user_id: str, 
                                 status: str, error_message: str = None):
        try:
            operation_id = f"op_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id}"
            
            operation = CodeOperation(
                id=operation_id,
                operation_type=operation_type,
                target_file=target_file,
                operation_data=operation_data,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                status=status,
                result=operation_data.get("result"),
                error_message=error_message
            )
            
            await self._save_code_operation(operation)
            self.active_operations[operation_id] = operation
            
        except Exception as e:
            self.logger.error(f"Failed to log code operation: {str(e)}")

    async def _save_code_operation(self, operation: CodeOperation):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute("""
                INSERT INTO code_operations (id, operation_type, target_file, operation_data,
                                           timestamp, user_id, status, result, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                operation.id, operation.operation_type, operation.target_file,
                json.dumps(operation.operation_data), operation.timestamp,
                operation.user_id, operation.status, operation.result, operation.error_message
            ))
            await session.commit()

    async def _store_code_health_snapshot(self, metrics: CodeHealthMetrics):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO code_health_snapshots (total_files, error_count, warning_count,
                                                     test_coverage, complexity_score, maintainability_index,
                                                     health_status, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    metrics.total_files, metrics.error_count, metrics.warning_count,
                    metrics.test_coverage, metrics.complexity_score, metrics.maintainability_index,
                    metrics.health_status.value, json.dumps({"timestamp": metrics.last_updated.isoformat()})
                ))
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to store code health snapshot: {str(e)}")

    async def get_code_health_history(self, days: int = 7) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT snapshot_time, total_files, error_count, warning_count,
                           test_coverage, complexity_score, maintainability_index, health_status
                    FROM code_health_snapshots 
                    WHERE snapshot_time >= %s 
                    ORDER BY snapshot_time DESC
                """, (cutoff_time,))
                
                history = []
                for row in result.fetchall():
                    history.append({
                        "timestamp": row[0].isoformat(),
                        "total_files": row[1],
                        "error_count": row[2],
                        "warning_count": row[3],
                        "test_coverage": float(row[4]) if row[4] else 0.0,
                        "complexity_score": float(row[5]) if row[5] else 0.0,
                        "maintainability_index": float(row[6]) if row[6] else 0.0,
                        "health_status": row[7]
                    })
                
                return history
                
        except Exception as e:
            self.logger.error(f"Failed to get code health history: {str(e)}")
            return []

    async def close(self):
        self.logger.info("Closing CodeManager...")
        if self.database:
            await self.database.close()

# Global instances and initialization functions
_code_manager: Optional[CodeManager] = None

async def init_code_manager() -> CodeManager:
    global _code_manager
    if not _code_manager:
        _code_manager = CodeManager()
        await _code_manager.initialize()
    return _code_manager

async def get_code_manager() -> CodeManager:
    global _code_manager
    if not _code_manager:
        _code_manager = await init_code_manager()
    return _code_manager
