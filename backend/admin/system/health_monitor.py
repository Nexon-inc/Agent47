import asyncio
import psutil
import platform
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from backend.core.database import get_database, DatabaseManager
from backend.core.cache import get_redis, RedisManager
from backend.core.storage import get_chroma, ChromaDBManager
from backend.core.event_bus import get_kafka, KafkaManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"

class ServiceType(Enum):
    DATABASE = "database"
    REDIS = "redis"
    SYSTEM = "system"
    API = "api"

@dataclass
class HealthCheck:
    id: str
    service_type: ServiceType
    service_name: str
    status: HealthStatus
    response_time: float
    last_check: datetime
    details: Dict[str, Any]
    error_message: Optional[str] = None

class HealthMonitor:
    def __init__(self):
        self.config = get_settings()
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()
    
    async def perform_health_checks(self) -> List[HealthCheck]:
        """Perform all health checks"""
        try:
            checks = []
            
            # Database health check
            db_check = await self._check_database_health()
            checks.append(db_check)
            
            # Redis health check
            redis_check = await self._check_redis_health()
            checks.append(redis_check)
            
            # System health check
            system_check = await self._check_system_health()
            checks.append(system_check)
            
            # Store results
            await self._store_health_checks(checks)
            
            return checks

        except Exception as e:
            self.logger.error(f"Failed to perform health checks: {e}")
            return []
    
    async def _check_database_health(self) -> HealthCheck:
        """Check database health"""
        try:
            start_time = datetime.utcnow()
            await self.db.execute("SELECT 1")
            response_time = (datetime.utcnow() - start_time).total_seconds()
                
            status = HealthStatus.HEALTHY
            if response_time > 5.0:
                status = HealthStatus.WARNING
            if response_time > 10.0:
                status = HealthStatus.CRITICAL
            
            return HealthCheck(
                id=f"db_check_{datetime.utcnow().timestamp()}",
                service_type=ServiceType.DATABASE,
                service_name="PostgreSQL",
                status=status,
                response_time=response_time,
                last_check=datetime.utcnow(),
                details={"connection": "active"}
            )
                
        except Exception as e:
            return HealthCheck(
                id=f"db_check_{datetime.utcnow().timestamp()}",
                service_type=ServiceType.DATABASE,
                service_name="PostgreSQL",
                status=HealthStatus.CRITICAL,
                response_time=0.0,
                last_check=datetime.utcnow(),
                details={},
                error_message=str(e)
            )

    async def _check_redis_health(self) -> HealthCheck:
        """Check Redis health"""
        try:
            start_time = datetime.utcnow()
            await self.redis.ping()
            response_time = (datetime.utcnow() - start_time).total_seconds()

            status = HealthStatus.HEALTHY
            if response_time > 1.0:
                status = HealthStatus.WARNING
            if response_time > 5.0:
                status = HealthStatus.CRITICAL
            
            return HealthCheck(
                id=f"redis_check_{datetime.utcnow().timestamp()}",
                service_type=ServiceType.REDIS,
                service_name="Redis",
                status=status,
                response_time=response_time,
                last_check=datetime.utcnow(),
                details={"connection": "active"}
            )
                
        except Exception as e:
            return HealthCheck(
                id=f"redis_check_{datetime.utcnow().timestamp()}",
                service_type=ServiceType.REDIS,
                service_name="Redis",
                status=HealthStatus.CRITICAL,
                response_time=0.0,
                last_check=datetime.utcnow(),
                details={},
                error_message=str(e)
            )

    async def _check_system_health(self) -> HealthCheck:
        """Check system health"""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = HealthStatus.HEALTHY
            if cpu_usage > 80 or memory.percent > 80 or disk.percent > 80:
                status = HealthStatus.WARNING
            if cpu_usage > 95 or memory.percent > 95 or disk.percent > 95:
                status = HealthStatus.CRITICAL
            
            return HealthCheck(
                id=f"system_check_{datetime.utcnow().timestamp()}",
                service_type=ServiceType.SYSTEM,
                service_name="System",
                status=status,
                response_time=0.0,
                last_check=datetime.utcnow(),
                details={
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory.percent,
                    "disk_usage": disk.percent
                }
            )
            
        except Exception as e:
            return HealthCheck(
                id=f"system_check_{datetime.utcnow().timestamp()}",
                service_type=ServiceType.SYSTEM,
                service_name="System",
                status=HealthStatus.CRITICAL,
                response_time=0.0,
                last_check=datetime.utcnow(),
                details={},
                error_message=str(e)
            )

    async def _store_health_checks(self, checks: List[HealthCheck]):
        """Store health check results"""
        try:
            for check in checks:
                await self.db.execute(
                    """
                    INSERT INTO health_checks 
                    (id, service_type, service_name, status, response_time, last_check, details, error_message)
                    VALUES (:id, :service_type, :service_name, :status, :response_time, :last_check, :details, :error_message)
                    """,
                    {
                        "id": check.id,
                        "service_type": check.service_type.value,
                        "service_name": check.service_name,
                        "status": check.status.value,
                        "response_time": check.response_time,
                        "last_check": check.last_check,
                        "details": check.details,
                        "error_message": check.error_message
                    }
                )
        except Exception as e:
            self.logger.error(f"Failed to store health checks: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            checks = await self.db.fetch_all(
                """
                SELECT * FROM health_checks 
                WHERE last_check >= :since 
                ORDER BY last_check DESC
                """,
                {"since": datetime.utcnow() - timedelta(minutes=5)}
            )
            
            if not checks:
                return {"status": "unknown", "services": []}
            
            services = {}
            for row in checks:
                service_name = row["service_name"]
                if service_name not in services:
                    services[service_name] = {
                        "name": service_name,
                        "status": row["status"],
                        "response_time": row["response_time"],
                        "last_check": row["last_check"]
                    }
            
            status_counts = {}
            for service in services.values():
                status = service["status"]
                status_counts[status] = status_counts.get(status, 0) + 1
            
            overall_status = "healthy"
            if status_counts.get("critical", 0) > 0:
                overall_status = "critical"
            elif status_counts.get("warning", 0) > 0:
                overall_status = "warning"
            
            return {
                "status": overall_status,
                "services": list(services.values())
            }
                
        except Exception as e:
            self.logger.error(f"Failed to get health status: {e}")
            return {"status": "unknown", "services": []}

# Singleton instance
_health_monitor = None

def get_health_monitor() -> HealthMonitor:
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor

def init_health_monitor():
    """Initialize health monitoring system"""
    global _health_monitor
    _health_monitor = HealthMonitor()
    return _health_monitor
