import asyncio
import psutil
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, NamedTuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from core.database import get_database
from core.cache import get_redis
from core.logs import get_logger
from core.config import get_config


class ResourceType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    PROCESS = "process"
    FILE_SYSTEM = "file_system"
    DATABASE = "database"
    CACHE = "cache"
    STORAGE = "storage"


class ResourceStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ResourceUsage:
    resource_type: ResourceType
    current_usage: float
    total_capacity: float
    usage_percentage: float
    unit: str
    status: ResourceStatus
    timestamp: datetime
    details: Dict = field(default_factory=dict)


@dataclass
class ResourceThreshold:
    resource_type: ResourceType
    warning_threshold: float
    critical_threshold: float
    emergency_threshold: float
    unit: str


@dataclass
class ResourceAlert:
    id: str
    timestamp: datetime
    resource_type: ResourceType
    current_usage: float
    threshold: float
    alert_level: str
    message: str
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


@dataclass
class SystemResources:
    timestamp: datetime
    cpu: Dict[str, float]
    memory: Dict[str, float]
    disk: Dict[str, float]
    network: Dict[str, float]
    processes: Dict[str, int]
    file_systems: List[Dict[str, any]]
    database_connections: int
    cache_usage: Dict[str, float]
    storage_usage: Dict[str, float]


class ResourceMonitor:
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()
        self.monitoring = False
        self.monitoring_task = None
        self.resource_thresholds = {
            ResourceType.CPU: ResourceThreshold(
                resource_type=ResourceType.CPU,
                warning_threshold=70.0,
                critical_threshold=85.0,
                emergency_threshold=95.0,
                unit="%"
            ),
            ResourceType.MEMORY: ResourceThreshold(
                resource_type=ResourceType.MEMORY,
                warning_threshold=80.0,
                critical_threshold=90.0,
                emergency_threshold=95.0,
                unit="%"
            ),
            ResourceType.DISK: ResourceThreshold(
                resource_type=ResourceType.DISK,
                warning_threshold=85.0,
                critical_threshold=90.0,
                emergency_threshold=95.0,
                unit="%"
            ),
            ResourceType.DATABASE: ResourceThreshold(
                resource_type=ResourceType.DATABASE,
                warning_threshold=80,
                critical_threshold=90,
                emergency_threshold=95,
                unit="connections"
            ),
            ResourceType.CACHE: ResourceThreshold(
                resource_type=ResourceType.CACHE,
                warning_threshold=80.0,
                critical_threshold=90.0,
                emergency_threshold=95.0,
                unit="%"
            )
        }
        self.resource_history: List[ResourceUsage] = []
        self.active_alerts: List[ResourceAlert] = []
        self.monitoring_interval = 60  # seconds
        self.retention_days = 30
        self.monitored_paths = [
            "/tmp",
            "/var/log",
            "/var/cache",
            self.config.storage.base_path if hasattr(self.config.storage, 'base_path') else "/data"
        ]

    async def initialize(self):
        """Initialize the resource monitor and create necessary tables"""
        try:
            await self._setup_resource_tables()
            await self._load_resource_thresholds()
            await self._start_monitoring()
            self.logger.info("ResourceMonitor initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize ResourceMonitor: {e}")
            raise

    async def _setup_resource_tables(self):
        """Create resource monitoring tables"""
        async with self.db.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS resource_usage (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    resource_type VARCHAR(50) NOT NULL,
                    current_usage DOUBLE PRECISION NOT NULL,
                    total_capacity DOUBLE PRECISION NOT NULL,
                    usage_percentage DOUBLE PRECISION NOT NULL,
                    unit VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    details JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS resource_alerts (
                    id VARCHAR(50) PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    resource_type VARCHAR(50) NOT NULL,
                    current_usage DOUBLE PRECISION NOT NULL,
                    threshold DOUBLE PRECISION NOT NULL,
                    alert_level VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP,
                    resolved_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS system_resources (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    cpu JSONB NOT NULL,
                    memory JSONB NOT NULL,
                    disk JSONB NOT NULL,
                    network JSONB NOT NULL,
                    processes JSONB NOT NULL,
                    file_systems JSONB NOT NULL,
                    database_connections INTEGER NOT NULL,
                    cache_usage JSONB NOT NULL,
                    storage_usage JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.commit()

    async def _load_resource_thresholds(self):
        """Load resource thresholds from configuration or database"""
        try:
            cached_thresholds = await self.redis.get("resource:thresholds")
            if cached_thresholds:
                # Convert back to ResourceThreshold objects
                for resource_type, threshold_data in cached_thresholds.items():
                    if resource_type in self.resource_thresholds:
                        self.resource_thresholds[resource_type] = ResourceThreshold(**threshold_data)
            else:
                await self._save_resource_thresholds()
        except Exception as e:
            self.logger.warning(f"Could not load resource thresholds: {e}")

    async def _save_resource_thresholds(self):
        """Save resource thresholds to cache"""
        try:
            # Convert ResourceThreshold objects to dictionaries for serialization
            threshold_dict = {}
            for resource_type, threshold in self.resource_thresholds.items():
                threshold_dict[resource_type.value] = {
                    "resource_type": threshold.resource_type.value,
                    "warning_threshold": threshold.warning_threshold,
                    "critical_threshold": threshold.critical_threshold,
                    "emergency_threshold": threshold.emergency_threshold,
                    "unit": threshold.unit
                }
            
            await self.redis.set("resource:thresholds", threshold_dict, expire=3600)
        except Exception as e:
            self.logger.warning(f"Could not save resource thresholds: {e}")

    async def _start_monitoring(self):
        """Start the resource monitoring loop"""
        if not self.monitoring:
            self.monitoring = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.logger.info("Resource monitoring started")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                await self._collect_resource_metrics()
                await self._check_resource_thresholds()
                await self._cleanup_old_data()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"Error in resource monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def _collect_resource_metrics(self):
        """Collect current resource metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count()
            cpu_stats = psutil.cpu_stats()
            
            cpu_metrics = {
                "usage_percent": cpu_percent,
                "frequency_current": cpu_freq.current if cpu_freq else 0,
                "frequency_min": cpu_freq.min if cpu_freq else 0,
                "frequency_max": cpu_freq.max if cpu_freq else 0,
                "count": cpu_count,
                "ctx_switches": cpu_stats.ctx_switches,
                "interrupts": cpu_stats.interrupts,
                "soft_interrupts": cpu_stats.soft_interrupts,
                "syscalls": cpu_stats.syscalls
            }
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            memory_metrics = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "free": memory.free,
                "percent": memory.percent,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_free": swap.free,
                "swap_percent": swap.percent
            }
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            disk_metrics = {
                "total": disk_usage.total,
                "used": disk_usage.used,
                "free": disk_usage.free,
                "percent": disk_usage.percent,
                "read_bytes": disk_io.read_bytes,
                "write_bytes": disk_io.write_bytes,
                "read_count": disk_io.read_count,
                "write_count": disk_io.write_count
            }
            
            # Network metrics
            network_io = psutil.net_io_counters()
            network_connections = psutil.net_connections()
            
            network_metrics = {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv,
                "connections_count": len(network_connections),
                "established_connections": len([c for c in network_connections if c.status == 'ESTABLISHED'])
            }
            
            # Process metrics
            processes = psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'])
            process_metrics = {
                "total_count": len(psutil.pids()),
                "running_count": len([p for p in processes if p.info['cpu_percent'] > 0]),
                "top_cpu": sorted([p.info for p in processes], key=lambda x: x['cpu_percent'], reverse=True)[:10],
                "top_memory": sorted([p.info for p in processes], key=lambda x: x['memory_percent'], reverse=True)[:10]
            }
            
            # File system metrics
            file_systems = []
            for path in self.monitored_paths:
                try:
                    if os.path.exists(path):
                        usage = shutil.disk_usage(path)
                        file_systems.append({
                            "path": path,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": (usage.used / usage.total) * 100
                        })
                except Exception as e:
                    self.logger.warning(f"Could not get disk usage for {path}: {e}")
            
            # Database connections
            database_connections = await self._get_database_connections()
            
            # Cache usage
            cache_usage = await self._get_cache_usage()
            
            # Storage usage
            storage_usage = await self._get_storage_usage()
            
            # Create system resources snapshot
            system_resources = SystemResources(
                timestamp=datetime.utcnow(),
                cpu=cpu_metrics,
                memory=memory_metrics,
                disk=disk_metrics,
                network=network_metrics,
                processes=process_metrics,
                file_systems=file_systems,
                database_connections=database_connections,
                cache_usage=cache_usage,
                storage_usage=storage_usage
            )
            
            # Save to database
            await self._save_system_resources(system_resources)
            
            # Create resource usage records
            await self._create_resource_usage_records(system_resources)
            
            # Store in memory for quick access
            self._update_resource_history(system_resources)
            
        except Exception as e:
            self.logger.error(f"Error collecting resource metrics: {e}")

    async def _get_database_connections(self) -> int:
        """Get current database connection count"""
        try:
            async with self.db.get_session() as session:
                result = await session.execute("SELECT count(*) FROM pg_stat_activity")
                return result.scalar() or 0
        except Exception as e:
            self.logger.warning(f"Could not get database connections: {e}")
            return 0

    async def _get_cache_usage(self) -> Dict[str, float]:
        """Get current cache usage metrics"""
        try:
            info = await self.redis.execute_command("INFO", "memory")
            cache_metrics = {}
            
            for line in info.split('\n'):
                if line.startswith('used_memory:'):
                    cache_metrics["used_memory"] = int(line.split(':')[1])
                elif line.startswith('used_memory_peak:'):
                    cache_metrics["peak_memory"] = int(line.split(':')[1])
                elif line.startswith('used_memory_rss:'):
                    cache_metrics["rss_memory"] = int(line.split(':')[1])
                elif line.startswith('used_memory_lua:'):
                    cache_metrics["lua_memory"] = int(line.split(':')[1])
            
            # Calculate usage percentage if we have the data
            if "used_memory" in cache_metrics and "peak_memory" in cache_metrics:
                cache_metrics["usage_percent"] = (cache_metrics["used_memory"] / cache_metrics["peak_memory"]) * 100
            
            return cache_metrics
        except Exception as e:
            self.logger.warning(f"Could not get cache usage: {e}")
            return {"usage_percent": 0.0}

    async def _get_storage_usage(self) -> Dict[str, float]:
        """Get current storage usage metrics"""
        try:
            storage_metrics = {}
            
            # Get ChromaDB storage usage
            try:
                chroma_path = getattr(self.config.storage, 'chroma_path', '/data/chroma')
                if os.path.exists(chroma_path):
                    usage = shutil.disk_usage(chroma_path)
                    storage_metrics["chroma_total"] = usage.total
                    storage_metrics["chroma_used"] = usage.used
                    storage_metrics["chroma_free"] = usage.free
                    storage_metrics["chroma_percent"] = (usage.used / usage.total) * 100
            except Exception as e:
                self.logger.warning(f"Could not get ChromaDB storage usage: {e}")
            
            # Get general data storage usage
            try:
                data_path = getattr(self.config.storage, 'base_path', '/data')
                if os.path.exists(data_path):
                    usage = shutil.disk_usage(data_path)
                    storage_metrics["data_total"] = usage.total
                    storage_metrics["data_used"] = usage.used
                    storage_metrics["data_free"] = usage.free
                    storage_metrics["data_percent"] = (usage.used / usage.total) * 100
            except Exception as e:
                self.logger.warning(f"Could not get data storage usage: {e}")
            
            return storage_metrics
        except Exception as e:
            self.logger.warning(f"Could not get storage usage: {e}")
            return {"usage_percent": 0.0}

    async def _save_system_resources(self, resources: SystemResources):
        """Save system resources snapshot to database"""
        try:
            async with self.db.get_session() as session:
                await session.execute("""
                    INSERT INTO system_resources (
                        timestamp, cpu, memory, disk, network, processes, file_systems,
                        database_connections, cache_usage, storage_usage
                    ) VALUES (
                        :timestamp, :cpu, :memory, :disk, :network, :processes, :file_systems,
                        :database_connections, :cache_usage, :storage_usage
                    )
                """, {
                    "timestamp": resources.timestamp,
                    "cpu": resources.cpu,
                    "memory": resources.memory,
                    "disk": resources.disk,
                    "network": resources.network,
                    "processes": resources.processes,
                    "file_systems": resources.file_systems,
                    "database_connections": resources.database_connections,
                    "cache_usage": resources.cache_usage,
                    "storage_usage": resources.storage_usage
                })
                await session.commit()
        except Exception as e:
            self.logger.error(f"Error saving system resources: {e}")

    async def _create_resource_usage_records(self, resources: SystemResources):
        """Create individual resource usage records"""
        try:
            # CPU usage
            cpu_usage = ResourceUsage(
                resource_type=ResourceType.CPU,
                current_usage=sum(resources.cpu["usage_percent"]) / len(resources.cpu["usage_percent"]),
                total_capacity=100.0,
                usage_percentage=sum(resources.cpu["usage_percent"]) / len(resources.cpu["usage_percent"]),
                unit="%",
                status=self._get_resource_status(ResourceType.CPU, sum(resources.cpu["usage_percent"]) / len(resources.cpu["usage_percent"])),
                timestamp=resources.timestamp,
                details=resources.cpu
            )
            
            # Memory usage
            memory_usage = ResourceUsage(
                resource_type=ResourceType.MEMORY,
                current_usage=resources.memory["used"],
                total_capacity=resources.memory["total"],
                usage_percentage=resources.memory["percent"],
                unit="bytes",
                status=self._get_resource_status(ResourceType.MEMORY, resources.memory["percent"]),
                timestamp=resources.timestamp,
                details=resources.memory
            )
            
            # Disk usage
            disk_usage = ResourceUsage(
                resource_type=ResourceType.DISK,
                current_usage=resources.disk["used"],
                total_capacity=resources.disk["total"],
                usage_percentage=resources.disk["percent"],
                unit="bytes",
                status=self._get_resource_status(ResourceType.DISK, resources.disk["percent"]),
                timestamp=resources.timestamp,
                details=resources.disk
            )
            
            # Database connections
            db_usage = ResourceUsage(
                resource_type=ResourceType.DATABASE,
                current_usage=resources.database_connections,
                total_capacity=100,  # Assuming max 100 connections
                usage_percentage=(resources.database_connections / 100) * 100,
                unit="connections",
                status=self._get_resource_status(ResourceType.DATABASE, (resources.database_connections / 100) * 100),
                timestamp=resources.timestamp,
                details={"connections": resources.database_connections}
            )
            
            # Cache usage
            cache_usage = ResourceUsage(
                resource_type=ResourceType.CACHE,
                current_usage=resources.cache_usage.get("usage_percent", 0.0),
                total_capacity=100.0,
                usage_percentage=resources.cache_usage.get("usage_percent", 0.0),
                unit="%",
                status=self._get_resource_status(ResourceType.CACHE, resources.cache_usage.get("usage_percent", 0.0)),
                timestamp=resources.timestamp,
                details=resources.cache_usage
            )
            
            # Save to database
            await self._save_resource_usage(cpu_usage)
            await self._save_resource_usage(memory_usage)
            await self._save_resource_usage(disk_usage)
            await self._save_resource_usage(db_usage)
            await self._save_resource_usage(cache_usage)
            
        except Exception as e:
            self.logger.error(f"Error creating resource usage records: {e}")

    def _get_resource_status(self, resource_type: ResourceType, usage_percentage: float) -> ResourceStatus:
        """Determine resource status based on usage and thresholds"""
        if resource_type not in self.resource_thresholds:
            return ResourceStatus.UNKNOWN
        
        threshold = self.resource_thresholds[resource_type]
        
        if usage_percentage >= threshold.emergency_threshold:
            return ResourceStatus.CRITICAL
        elif usage_percentage >= threshold.critical_threshold:
            return ResourceStatus.CRITICAL
        elif usage_percentage >= threshold.warning_threshold:
            return ResourceStatus.WARNING
        else:
            return ResourceStatus.HEALTHY

    async def _save_resource_usage(self, usage: ResourceUsage):
        """Save resource usage to database"""
        try:
            async with self.db.get_session() as session:
                await session.execute("""
                    INSERT INTO resource_usage (
                        timestamp, resource_type, current_usage, total_capacity,
                        usage_percentage, unit, status, details
                    ) VALUES (
                        :timestamp, :resource_type, :current_usage, :total_capacity,
                        :usage_percentage, :unit, :status, :details
                    )
                """, {
                    "timestamp": usage.timestamp,
                    "resource_type": usage.resource_type.value,
                    "current_usage": usage.current_usage,
                    "total_capacity": usage.total_capacity,
                    "usage_percentage": usage.usage_percentage,
                    "unit": usage.unit,
                    "status": usage.status.value,
                    "details": usage.details
                })
                await session.commit()
        except Exception as e:
            self.logger.error(f"Error saving resource usage: {e}")

    def _update_resource_history(self, resources: SystemResources):
        """Update resource history in memory"""
        try:
            # Add to history
            self.resource_history.append(ResourceUsage(
                resource_type=ResourceType.CPU,
                current_usage=sum(resources.cpu["usage_percent"]) / len(resources.cpu["usage_percent"]),
                total_capacity=100.0,
                usage_percentage=sum(resources.cpu["usage_percent"]) / len(resources.cpu["usage_percent"]),
                unit="%",
                status=self._get_resource_status(ResourceType.CPU, sum(resources.cpu["usage_percent"]) / len(resources.cpu["usage_percent"])),
                timestamp=resources.timestamp
            ))
            
            # Keep only recent history in memory
            cutoff_time = datetime.utcnow() - timedelta(hours=2)
            self.resource_history = [
                data for data in self.resource_history 
                if data.timestamp > cutoff_time
            ]
            
        except Exception as e:
            self.logger.error(f"Error updating resource history: {e}")

    async def _check_resource_thresholds(self):
        """Check if any resources exceed alert thresholds"""
        try:
            if not self.resource_history:
                return
                
            latest_usage = {}
            for data in self.resource_history:
                if data.timestamp == max(d.timestamp for d in self.resource_history):
                    latest_usage[data.resource_type] = data
            
            for resource_type, usage in latest_usage.items():
                if resource_type in self.resource_thresholds:
                    threshold = self.resource_thresholds[resource_type]
                    
                    if usage.usage_percentage >= threshold.emergency_threshold:
                        await self._create_resource_alert(usage, threshold.emergency_threshold, "emergency")
                    elif usage.usage_percentage >= threshold.critical_threshold:
                        await self._create_resource_alert(usage, threshold.critical_threshold, "critical")
                    elif usage.usage_percentage >= threshold.warning_threshold:
                        await self._create_resource_alert(usage, threshold.warning_threshold, "warning")
                            
        except Exception as e:
            self.logger.error(f"Error checking resource thresholds: {e}")

    async def _create_resource_alert(self, usage: ResourceUsage, threshold: float, level: str):
        """Create a resource alert"""
        try:
            # Check if alert already exists
            existing_alert = next(
                (alert for alert in self.active_alerts 
                 if alert.resource_type == usage.resource_type and not alert.resolved), None
            )
            
            if existing_alert:
                return  # Alert already exists
            
            alert_id = f"resource_{usage.resource_type.value}_{int(datetime.utcnow().timestamp())}"
            message = f"{usage.resource_type.value.replace('_', ' ').title()} usage is {usage.usage_percentage:.2f}% (threshold: {threshold:.2f})"
            
            alert = ResourceAlert(
                id=alert_id,
                timestamp=datetime.utcnow(),
                resource_type=usage.resource_type,
                current_usage=usage.usage_percentage,
                threshold=threshold,
                alert_level=level,
                message=message
            )
            
            # Save to database
            async with self.db.get_session() as session:
                await session.execute("""
                    INSERT INTO resource_alerts (
                        id, timestamp, resource_type, current_usage, threshold, alert_level, message
                    ) VALUES (
                        :id, :timestamp, :resource_type, :current_usage, :threshold, :alert_level, :message
                    )
                """, {
                    "id": alert.id,
                    "timestamp": alert.timestamp,
                    "resource_type": alert.resource_type.value,
                    "current_usage": alert.current_usage,
                    "threshold": alert.threshold,
                    "alert_level": alert.alert_level,
                    "message": alert.message
                })
                await session.commit()
            
            # Add to active alerts
            self.active_alerts.append(alert)
            
            # Log alert
            self.logger.warning(f"Resource alert: {message} (Level: {level})")
            
            # Send notification
            await self._send_resource_alert_notification(alert)
            
        except Exception as e:
            self.logger.error(f"Error creating resource alert: {e}")

    async def _send_resource_alert_notification(self, alert: ResourceAlert):
        """Send resource alert notification"""
        try:
            notification_data = {
                "type": "resource_alert",
                "alert_id": alert.id,
                "resource_type": alert.resource_type.value,
                "level": alert.alert_level,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat()
            }
            
            # Store in Redis for notification service
            await self.redis.set(
                f"notifications:resource:{alert.id}",
                notification_data,
                expire=3600
            )
            
        except Exception as e:
            self.logger.warning(f"Could not send resource alert notification: {e}")

    async def _cleanup_old_data(self):
        """Clean up old resource data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            
            async with self.db.get_session() as session:
                # Clean up old resource usage
                await session.execute(
                    "DELETE FROM resource_usage WHERE timestamp < :cutoff_date",
                    {"cutoff_date": cutoff_date}
                )
                
                # Clean up old system resources
                await session.execute(
                    "DELETE FROM system_resources WHERE timestamp < :cutoff_date",
                    {"cutoff_date": cutoff_date}
                )
                
                # Clean up resolved alerts older than 7 days
                alert_cutoff = datetime.utcnow() - timedelta(days=7)
                await session.execute("""
                    DELETE FROM resource_alerts 
                    WHERE resolved = TRUE AND resolved_at < :alert_cutoff
                """, {"alert_cutoff": alert_cutoff})
                
                await session.commit()
                
        except Exception as e:
            self.logger.warning(f"Error cleaning up old resource data: {e}")

    async def get_current_resources(self) -> SystemResources:
        """Get current system resources snapshot"""
        try:
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT * FROM system_resources 
                    ORDER BY timestamp DESC LIMIT 1
                """)
                
                row = result.fetchone()
                if row:
                    return self._create_resources_from_row(row)
                
                # If no data, collect current metrics
                await self._collect_resource_metrics()
                return await self.get_current_resources()
                
        except Exception as e:
            self.logger.error(f"Error getting current resources: {e}")
            raise

    def _create_resources_from_row(self, row) -> SystemResources:
        """Create SystemResources from database row"""
        return SystemResources(
            timestamp=row.timestamp,
            cpu=row.cpu,
            memory=row.memory,
            disk=row.disk,
            network=row.network,
            processes=row.processes,
            file_systems=row.file_systems,
            database_connections=row.database_connections,
            cache_usage=row.cache_usage,
            storage_usage=row.storage_usage
        )

    async def get_resource_history(self, resource_type: ResourceType, 
                                 hours: int = 24) -> List[ResourceUsage]:
        """Get resource usage history for a specific resource type"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT * FROM resource_usage
                    WHERE resource_type = :resource_type AND timestamp >= :cutoff_time
                    ORDER BY timestamp ASC
                """, {
                    "resource_type": resource_type.value,
                    "cutoff_time": cutoff_time
                })
                
                rows = result.fetchall()
                return [
                    ResourceUsage(
                        timestamp=row.timestamp,
                        resource_type=ResourceType(row.resource_type),
                        current_usage=row.current_usage,
                        total_capacity=row.total_capacity,
                        usage_percentage=row.usage_percentage,
                        unit=row.unit,
                        status=ResourceStatus(row.status),
                        details=row.details or {}
                    )
                    for row in rows
                ]
                
        except Exception as e:
            self.logger.error(f"Error getting resource history: {e}")
            return []

    async def get_active_alerts(self) -> List[ResourceAlert]:
        """Get all active resource alerts"""
        try:
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT * FROM resource_alerts
                    WHERE resolved = FALSE
                    ORDER BY timestamp DESC
                """)
                
                rows = result.fetchall()
                alerts = []
                for row in rows:
                    alert = ResourceAlert(
                        id=row.id,
                        timestamp=row.timestamp,
                        resource_type=ResourceType(row.resource_type),
                        current_usage=row.current_usage,
                        threshold=row.threshold,
                        alert_level=row.alert_level,
                        message=row.message,
                        resolved=row.resolved,
                        resolved_at=row.resolved_at,
                        resolved_by=row.resolved_by
                    )
                    alerts.append(alert)
                
                return alerts
                
        except Exception as e:
            self.logger.error(f"Error getting active alerts: {e}")
            return []

    async def resolve_alert(self, alert_id: str, resolved_by: str):
        """Resolve a resource alert"""
        try:
            async with self.db.get_session() as session:
                await session.execute("""
                    UPDATE resource_alerts
                    SET resolved = TRUE, resolved_at = :resolved_at, resolved_by = :resolved_by
                    WHERE id = :alert_id
                """, {
                    "alert_id": alert_id,
                    "resolved_at": datetime.utcnow(),
                    "resolved_by": resolved_by
                })
                await session.commit()
            
            # Remove from active alerts
            self.active_alerts = [
                alert for alert in self.active_alerts 
                if alert.id != alert_id
            ]
            
            self.logger.info(f"Resource alert {alert_id} resolved by {resolved_by}")
            
        except Exception as e:
            self.logger.error(f"Error resolving alert {alert_id}: {e}")

    async def update_resource_thresholds(self, new_thresholds: Dict[ResourceType, ResourceThreshold]):
        """Update resource thresholds"""
        try:
            self.resource_thresholds.update(new_thresholds)
            await self._save_resource_thresholds()
            self.logger.info("Resource thresholds updated successfully")
        except Exception as e:
            self.logger.error(f"Error updating resource thresholds: {e}")

    async def get_resource_summary(self, hours: int = 24) -> Dict:
        """Get resource usage summary for the specified time period"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT 
                        resource_type,
                        AVG(usage_percentage) as avg_usage,
                        MAX(usage_percentage) as max_usage,
                        COUNT(*) as data_points
                    FROM resource_usage
                    WHERE timestamp >= :cutoff_time
                    GROUP BY resource_type
                """, {"cutoff_time": cutoff_time})
                
                rows = result.fetchall()
                summary = {}
                for row in rows:
                    summary[row.resource_type] = {
                        "average_usage": round(row.avg_usage, 2),
                        "maximum_usage": round(row.max_usage, 2),
                        "data_points": row.data_points
                    }
                
                return summary
                
        except Exception as e:
            self.logger.error(f"Error getting resource summary: {e}")
            return {}

    async def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Resource monitoring stopped")

    async def close(self):
        """Clean up resources"""
        await self.stop_monitoring()
        self.logger.info("ResourceMonitor closed")


# Singleton instances
_resource_monitor = None


async def get_resource_monitor() -> ResourceMonitor:
    """Get the ResourceMonitor singleton instance"""
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor()
        await _resource_monitor.initialize()
    return _resource_monitor


async def init_resource_monitor() -> ResourceMonitor:
    """Initialize and return a new ResourceMonitor instance"""
    monitor = ResourceMonitor()
    await monitor.initialize()
    return monitor
