import asyncio
import psutil
import platform
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from core.database import get_database, DatabaseManager
from core.cache import get_redis, RedisManager
from core.storage import get_chroma, ChromaDBManager
from core.event_bus import get_kafka, KafkaManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class SystemStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"

class MaintenanceMode(Enum):
    NONE = "none"
    SCHEDULED = "scheduled"
    EMERGENCY = "emergency"

@dataclass
class SystemMetrics:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int
    response_time: float
    error_rate: float
    timestamp: datetime

@dataclass
class MaintenanceWindow:
    start_time: datetime
    end_time: datetime
    reason: str
    affected_services: List[str]
    notification_sent: bool = False

class SystemManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.chroma: Optional[ChromaDBManager] = None
        self.kafka: Optional[KafkaManager] = None
        self.settings = get_settings()

        self.system_status = SystemStatus.HEALTHY
        self.maintenance_mode = MaintenanceMode.NONE
        self.maintenance_windows: List[MaintenanceWindow] = []
        self.system_metrics: Dict[str, SystemMetrics] = {}
        self.health_checks: Dict[str, bool] = {}
        self.logger = logger

        self._setup_health_checks()

    def _setup_health_checks(self):
        self.health_checks = {
            "database": True,
            "redis": True,
            "chroma": True,
            "kafka": True,
            "api": True,
            "agents": True
        }

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing SystemManager...")

            self.database = get_database()
            self.redis = await get_redis()
            self.chroma = await get_chroma()
            self.kafka = await get_kafka()

            await self._setup_system_tables()
            await self._load_maintenance_windows()
            await self._perform_initial_health_check()

            self.logger.info("SystemManager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize SystemManager: {str(e)}")
            return False

    async def _setup_system_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")

        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id SERIAL PRIMARY KEY,
                    service_name VARCHAR(100) NOT NULL,
                    cpu_usage DECIMAL(5,2),
                    memory_usage DECIMAL(5,2),
                    disk_usage DECIMAL(5,2),
                    network_io JSONB,
                    active_connections INTEGER,
                    response_time DECIMAL(10,3),
                    error_rate DECIMAL(5,2),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_windows (
                    id SERIAL PRIMARY KEY,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    reason TEXT NOT NULL,
                    affected_services JSONB NOT NULL,
                    notification_sent BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(255) NOT NULL
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(100) NOT NULL,
                    severity VARCHAR(50) NOT NULL,
                    description TEXT NOT NULL,
                    affected_services JSONB,
                    metadata JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    resolved_by VARCHAR(255)
                )
            """)

            await session.commit()

    async def _load_maintenance_windows(self):
        if not self.database:
            return

        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT start_time, end_time, reason, affected_services, notification_sent
                FROM maintenance_windows
                WHERE end_time > %s
                ORDER BY start_time ASC
            """, (datetime.utcnow(),))

            rows = result.fetchall()
            for row in rows:
                maintenance_window = MaintenanceWindow(
                    start_time=row[0],
                    end_time=row[1],
                    reason=row[2],
                    affected_services=row[3] or [],
                    notification_sent=row[4]
                )
                self.maintenance_windows.append(maintenance_window)

    async def _perform_initial_health_check(self):
        try:
            await self._check_database_health()
            await self._check_redis_health()
            await self._check_chroma_health()
            await self._check_kafka_health()
            await self._check_system_resources()
            await self._update_system_status()
        except Exception as e:
            self.logger.error(f"Initial health check failed: {str(e)}")

    async def _check_database_health(self):
        try:
            if self.database:
                health = await self.database.health_check()
                self.health_checks["database"] = health.get("status") == "healthy"
            else:
                self.health_checks["database"] = False
        except Exception as e:
            self.health_checks["database"] = False
            self.logger.error(f"Database health check failed: {str(e)}")

    async def _check_redis_health(self):
        try:
            if self.redis:
                health = await self.redis.health_check()
                self.health_checks["redis"] = health.get("status") == "healthy"
            else:
                self.health_checks["redis"] = False
        except Exception as e:
            self.health_checks["redis"] = False
            self.logger.error(f"Redis health check failed: {str(e)}")

    async def _check_chroma_health(self):
        try:
            if self.chroma:
                health = await self.chroma.health_check()
                self.health_checks["chroma"] = health.get("status") == "healthy"
            else:
                self.health_checks["chroma"] = False
        except Exception as e:
            self.health_checks["chroma"] = False
            self.logger.error(f"ChromaDB health check failed: {str(e)}")

    async def _check_kafka_health(self):
        try:
            if self.kafka:
                health = await self.kafka.health_check()
                self.health_checks["kafka"] = health.get("status") == "healthy"
            else:
                self.health_checks["kafka"] = False
        except Exception as e:
            self.health_checks["kafka"] = False
            self.logger.error(f"Kafka health check failed: {str(e)}")

    async def _check_system_resources(self):
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()

            metrics = SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_io={
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                active_connections=len(psutil.net_connections()),
                response_time=0.0,  # Will be updated by performance monitoring
                error_rate=0.0,     # Will be updated by error monitoring
                timestamp=datetime.utcnow()
            )

            self.system_metrics["system"] = metrics
            await self._save_system_metrics("system", metrics)

        except Exception as e:
            self.logger.error(f"System resources check failed: {str(e)}")

    async def _update_system_status(self):
        healthy_services = sum(self.health_checks.values())
        total_services = len(self.health_checks)

        if healthy_services == total_services:
            self.system_status = SystemStatus.HEALTHY
        elif healthy_services >= total_services * 0.8:
            self.system_status = SystemStatus.DEGRADED
        else:
            self.system_status = SystemStatus.CRITICAL

        # Check if in maintenance mode
        current_time = datetime.utcnow()
        for window in self.maintenance_windows:
            if window.start_time <= current_time <= window.end_time:
                self.maintenance_mode = MaintenanceMode.SCHEDULED
                break
        else:
            self.maintenance_mode = MaintenanceMode.NONE

    async def _save_system_metrics(self, service_name: str, metrics: SystemMetrics):
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO system_metrics (service_name, cpu_usage, memory_usage, disk_usage,
                                              network_io, active_connections, response_time, error_rate, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    service_name, metrics.cpu_usage, metrics.memory_usage, metrics.disk_usage,
                    json.dumps(metrics.network_io), metrics.active_connections,
                    metrics.response_time, metrics.error_rate, metrics.timestamp
                ))
                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to save system metrics: {str(e)}")

    async def get_system_status(self) -> Dict[str, Any]:
        await self._update_system_status()
        
        return {
            "status": self.system_status.value,
            "maintenance_mode": self.maintenance_mode.value,
            "health_checks": self.health_checks,
            "timestamp": datetime.utcnow().isoformat(),
            "maintenance_windows": [
                {
                    "start_time": window.start_time.isoformat(),
                    "end_time": window.end_time.isoformat(),
                    "reason": window.reason,
                    "affected_services": window.affected_services
                }
                for window in self.maintenance_windows
            ]
        }

    async def get_system_metrics(self, service_name: str = None, hours: int = 24) -> Dict[str, Any]:
        if not self.database:
            return {}

        try:
            query = """
                SELECT service_name, cpu_usage, memory_usage, disk_usage, network_io,
                       active_connections, response_time, error_rate, timestamp
                FROM system_metrics
                WHERE timestamp >= %s
            """
            params = [datetime.utcnow() - timedelta(hours=hours)]

            if service_name:
                query += " AND service_name = %s"
                params.append(service_name)

            query += " ORDER BY timestamp DESC"

            async with self.database.get_session() as session:
                result = await session.execute(query, params)
                rows = result.fetchall()

                metrics = []
                for row in rows:
                    metrics.append({
                        "service_name": row[0],
                        "cpu_usage": float(row[1]) if row[1] else 0.0,
                        "memory_usage": float(row[2]) if row[2] else 0.0,
                        "disk_usage": float(row[3]) if row[3] else 0.0,
                        "network_io": row[4] if row[4] else {},
                        "active_connections": row[5] if row[5] else 0,
                        "response_time": float(row[6]) if row[6] else 0.0,
                        "error_rate": float(row[7]) if row[7] else 0.0,
                        "timestamp": row[8].isoformat()
                    })

                return {
                    "metrics": metrics,
                    "summary": self._calculate_metrics_summary(metrics)
                }

        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {str(e)}")
            return {}

    def _calculate_metrics_summary(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not metrics:
            return {}

        summary = {
            "total_records": len(metrics),
            "avg_cpu_usage": 0.0,
            "avg_memory_usage": 0.0,
            "avg_disk_usage": 0.0,
            "avg_response_time": 0.0,
            "avg_error_rate": 0.0,
            "peak_cpu_usage": 0.0,
            "peak_memory_usage": 0.0
        }

        cpu_values = [m["cpu_usage"] for m in metrics if m["cpu_usage"] is not None]
        memory_values = [m["memory_usage"] for m in metrics if m["memory_usage"] is not None]
        disk_values = [m["disk_usage"] for m in metrics if m["disk_usage"] is not None]
        response_values = [m["response_time"] for m in metrics if m["response_time"] is not None]
        error_values = [m["error_rate"] for m in metrics if m["error_rate"] is not None]

        if cpu_values:
            summary["avg_cpu_usage"] = sum(cpu_values) / len(cpu_values)
            summary["peak_cpu_usage"] = max(cpu_values)

        if memory_values:
            summary["avg_memory_usage"] = sum(memory_values) / len(memory_values)
            summary["peak_memory_usage"] = max(memory_values)

        if disk_values:
            summary["avg_disk_usage"] = sum(disk_values) / len(disk_values)

        if response_values:
            summary["avg_response_time"] = sum(response_values) / len(response_values)

        if error_values:
            summary["avg_error_rate"] = sum(error_values) / len(error_values)

        return summary

    async def schedule_maintenance(self, start_time: datetime, end_time: datetime, reason: str,
                                 affected_services: List[str], created_by: str) -> bool:
        try:
            maintenance_window = MaintenanceWindow(
                start_time=start_time,
                end_time=end_time,
                reason=reason,
                affected_services=affected_services
            )

            if not self.database:
                self.maintenance_windows.append(maintenance_window)
                return True

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO maintenance_windows (start_time, end_time, reason, affected_services, created_by)
                    VALUES (%s, %s, %s, %s, %s)
                """, (start_time, end_time, reason, json.dumps(affected_services), created_by))
                await session.commit()

            self.maintenance_windows.append(maintenance_window)
            await self._log_system_event("MAINTENANCE_SCHEDULED", "info", reason, affected_services)

            self.logger.info(f"Maintenance scheduled from {start_time} to {end_time}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to schedule maintenance: {str(e)}")
            return False

    async def cancel_maintenance(self, start_time: datetime, end_time: datetime, cancelled_by: str) -> bool:
        try:
            if not self.database:
                self.maintenance_windows = [
                    w for w in self.maintenance_windows
                    if not (w.start_time == start_time and w.end_time == end_time)
                ]
                return True

            async with self.database.get_session() as session:
                await session.execute("""
                    DELETE FROM maintenance_windows
                    WHERE start_time = %s AND end_time = %s
                """, (start_time, end_time))
                await session.commit()

            self.maintenance_windows = [
                w for w in self.maintenance_windows
                if not (w.start_time == start_time and w.end_time == end_time)
            ]

            await self._log_system_event("MAINTENANCE_CANCELLED", "info", 
                                       f"Maintenance cancelled by {cancelled_by}", [])

            self.logger.info(f"Maintenance cancelled for {start_time} to {end_time}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to cancel maintenance: {str(e)}")
            return False

    async def _log_system_event(self, event_type: str, severity: str, description: str,
                               affected_services: List[str], metadata: Dict[str, Any] = None):
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO system_events (event_type, severity, description, affected_services, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (event_type, severity, description, json.dumps(affected_services), json.dumps(metadata or {})))
                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to log system event: {str(e)}")

    async def get_system_events(self, hours: int = 24, severity: str = None) -> List[Dict[str, Any]]:
        if not self.database:
            return []

        try:
            query = """
                SELECT event_type, severity, description, affected_services, metadata, timestamp, resolved_at, resolved_by
                FROM system_events
                WHERE timestamp >= %s
            """
            params = [datetime.utcnow() - timedelta(hours=hours)]

            if severity:
                query += " AND severity = %s"
                params.append(severity)

            query += " ORDER BY timestamp DESC"

            async with self.database.get_session() as session:
                result = await session.execute(query, params)
                rows = result.fetchall()

                events = []
                for row in rows:
                    events.append({
                        "event_type": row[0],
                        "severity": row[1],
                        "description": row[2],
                        "affected_services": row[3] if row[3] else [],
                        "metadata": row[4] if row[4] else {},
                        "timestamp": row[5].isoformat(),
                        "resolved_at": row[6].isoformat() if row[6] else None,
                        "resolved_by": row[7]
                    })

                return events

        except Exception as e:
            self.logger.error(f"Failed to get system events: {str(e)}")
            return []

    async def resolve_system_event(self, event_type: str, description: str, resolved_by: str) -> bool:
        if not self.database:
            return False

        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE system_events
                    SET resolved_at = %s, resolved_by = %s
                    WHERE event_type = %s AND description = %s AND resolved_at IS NULL
                """, (datetime.utcnow(), resolved_by, event_type, description))
                await session.commit()

            self.logger.info(f"System event resolved: {event_type} - {description}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to resolve system event: {str(e)}")
            return False

    async def get_system_info(self) -> Dict[str, Any]:
        try:
            system_info = {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.architecture()[0],
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "hostname": platform.node(),
                "uptime": self._get_system_uptime(),
                "disk_partitions": self._get_disk_partitions(),
                "network_interfaces": self._get_network_interfaces(),
                "timestamp": datetime.utcnow().isoformat()
            }

            return system_info

        except Exception as e:
            self.logger.error(f"Failed to get system info: {str(e)}")
            return {}

    def _get_system_uptime(self) -> str:
        try:
            uptime_seconds = psutil.boot_time()
            uptime = datetime.utcnow() - datetime.fromtimestamp(uptime_seconds)
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{days} days, {hours} hours, {minutes} minutes"
        except:
            return "Unknown"

    def _get_disk_partitions(self) -> List[Dict[str, Any]]:
        try:
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "filesystem": partition.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent
                    })
                except:
                    continue
            return partitions
        except:
            return []

    def _get_network_interfaces(self) -> List[Dict[str, Any]]:
        try:
            interfaces = []
            for interface, addresses in psutil.net_if_addrs().items():
                interface_info = {
                    "name": interface,
                    "addresses": []
                }
                for addr in addresses:
                    interface_info["addresses"].append({
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast
                    })
                interfaces.append(interface_info)
            return interfaces
        except:
            return []

    async def close(self):
        self.logger.info("Closing SystemManager...")
        if self.database:
            await self.database.close()

# Global instances and initialization functions
_system_manager: Optional[SystemManager] = None

async def init_system_manager() -> SystemManager:
    global _system_manager
    if not _system_manager:
        _system_manager = SystemManager()
        await _system_manager.initialize()
    return _system_manager

async def get_system_manager() -> SystemManager:
    global _system_manager
    if not _system_manager:
        _system_manager = await init_system_manager()
    return _system_manager
