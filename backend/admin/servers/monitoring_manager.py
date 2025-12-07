import asyncio
import psutil
import requests
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text

from backend.core.database import get_database, DatabaseManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class MonitoringStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    OFFLINE = "offline"

class MetricType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    APPLICATION = "application"
    DATABASE = "database"
    CUSTOM = "custom"

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class ServerMetric:
    metric_id: str
    server_id: str
    metric_type: MetricType
    name: str
    value: float
    unit: str
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class ServerInfo:
    server_id: str
    name: str
    hostname: str
    ip_address: str
    status: MonitoringStatus
    last_seen: datetime
    os_type: str
    os_version: str
    cpu_cores: int
    total_memory: int
    total_disk: int
    metadata: Dict[str, Any]

@dataclass
class MonitoringAlert:
    alert_id: str
    server_id: str
    metric_name: str
    alert_level: AlertLevel
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime
    acknowledged: bool
    resolved: bool

class ServerMonitoringManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.monitored_servers: Dict[str, ServerInfo] = {}
        self.metric_cache: Dict[str, List[ServerMetric]] = {}
        self.active_alerts: Dict[str, MonitoringAlert] = {}
        self.monitoring_interval_seconds = 60
        self.alert_cooldown_minutes = 15
        self.metric_retention_hours = 24
        self.health_check_timeout_seconds = 30

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing ServerMonitoringManager...")
            self.database = get_database()
            await self._setup_monitoring_tables()
            await self._load_monitored_servers()
            await self._start_monitoring_tasks()
            self.logger.info("ServerMonitoringManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize ServerMonitoringManager: {str(e)}")
            return False

    async def _setup_monitoring_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS monitored_servers (
                    id SERIAL PRIMARY KEY,
                    server_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    hostname VARCHAR(255) NOT NULL,
                    ip_address INET NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    os_type VARCHAR(50),
                    os_version VARCHAR(100),
                    cpu_cores INTEGER,
                    total_memory BIGINT,
                    total_disk BIGINT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS server_metrics (
                    id SERIAL PRIMARY KEY,
                    metric_id VARCHAR(255) UNIQUE NOT NULL,
                    server_id VARCHAR(255) NOT NULL,
                    metric_type VARCHAR(50) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    value FLOAT NOT NULL,
                    unit VARCHAR(20) NOT NULL,
                    threshold_warning FLOAT,
                    threshold_critical FLOAT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB,
                    FOREIGN KEY (server_id) REFERENCES monitored_servers(server_id)
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_alerts (
                    id SERIAL PRIMARY KEY,
                    alert_id VARCHAR(255) UNIQUE NOT NULL,
                    server_id VARCHAR(255) NOT NULL,
                    metric_name VARCHAR(255) NOT NULL,
                    alert_level VARCHAR(20) NOT NULL,
                    current_value FLOAT NOT NULL,
                    threshold_value FLOAT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES monitored_servers(server_id)
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_monitored_servers_status 
                ON monitored_servers(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_monitored_servers_last_seen 
                ON monitored_servers(last_seen);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_server_metrics_server_id 
                ON server_metrics(server_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_server_metrics_timestamp 
                ON server_metrics(timestamp);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_server_metrics_metric_type 
                ON server_metrics(metric_type);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_server_id 
                ON monitoring_alerts(server_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_timestamp 
                ON monitoring_alerts(timestamp);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_acknowledged 
                ON monitoring_alerts(acknowledged);
            """)
            
            await session.commit()

    async def _load_monitored_servers(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT server_id, name, hostname, ip_address, status, last_seen,
                       os_type, os_version, cpu_cores, total_memory, total_disk, metadata
                FROM monitored_servers
            """)
            
            for row in result:
                server_info = ServerInfo(
                    server_id=row.server_id,
                    name=row.name,
                    hostname=row.hostname,
                    ip_address=row.ip_address,
                    status=MonitoringStatus(row.status),
                    last_seen=row.last_seen,
                    os_type=row.os_type or "",
                    os_version=row.os_version or "",
                    cpu_cores=row.cpu_cores or 0,
                    total_memory=row.total_memory or 0,
                    total_disk=row.total_disk or 0,
                    metadata=row.metadata or {}
                )
                self.monitored_servers[server_info.server_id] = server_info

    async def _start_monitoring_tasks(self):
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._cleanup_old_metrics())
        asyncio.create_task(self._check_server_health())

    async def _monitoring_loop(self):
        while True:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.monitoring_interval_seconds)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(60)

    async def _cleanup_old_metrics(self):
        while True:
            try:
                await self._cleanup_old_metrics_internal()
                await asyncio.sleep(3600)
            except Exception as e:
                self.logger.error(f"Error in metrics cleanup: {str(e)}")
                await asyncio.sleep(3600)

    async def _check_server_health(self):
        while True:
            try:
                await self._check_server_health_internal()
                await asyncio.sleep(300)
            except Exception as e:
                self.logger.error(f"Error in health check: {str(e)}")
                await asyncio.sleep(300)

    async def add_server(
        self,
        server_id: str,
        name: str,
        hostname: str,
        ip_address: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        try:
            if not self.database:
                return False
            
            server_info = ServerInfo(
                server_id=server_id,
                name=name,
                hostname=hostname,
                ip_address=ip_address,
                status=MonitoringStatus.UNKNOWN,
                last_seen=datetime.utcnow(),
                os_type="",
                os_version="",
                cpu_cores=0,
                total_memory=0,
                total_disk=0,
                metadata=metadata or {}
            )
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO monitored_servers (
                        server_id, name, hostname, ip_address, status, metadata
                    ) VALUES (
                        :server_id, :name, :hostname, :ip_address, :status, :metadata
                    )
                """, {
                    "server_id": server_info.server_id,
                    "name": server_info.name,
                    "hostname": server_info.hostname,
                    "ip_address": server_info.ip_address,
                    "status": server_info.status.value,
                    "metadata": server_info.metadata
                })
                await session.commit()
            
            self.monitored_servers[server_id] = server_info
            self.logger.info(f"Server added to monitoring: {server_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add server: {str(e)}")
            return False

    async def remove_server(self, server_id: str) -> bool:
        try:
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    DELETE FROM monitored_servers WHERE server_id = :server_id
                """, {"server_id": server_id})
                await session.commit()
            
            if server_id in self.monitored_servers:
                del self.monitored_servers[server_id]
            
            if server_id in self.metric_cache:
                del self.metric_cache[server_id]
            
            self.logger.info(f"Server removed from monitoring: {server_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove server: {str(e)}")
            return False

    async def _collect_metrics(self):
        for server_id, server_info in self.monitored_servers.items():
            try:
                if server_info.status == MonitoringStatus.OFFLINE:
                    continue
                
                metrics = await self._collect_server_metrics(server_id, server_info)
                if metrics:
                    await self._store_metrics(metrics)
                    await self._check_metric_thresholds(metrics)
                    await self._update_server_status(server_id, MonitoringStatus.HEALTHY)
                else:
                    await self._update_server_status(server_id, MonitoringStatus.OFFLINE)
                    
            except Exception as e:
                self.logger.error(f"Failed to collect metrics for server {server_id}: {str(e)}")
                await self._update_server_status(server_id, MonitoringStatus.CRITICAL)

    async def _collect_server_metrics(self, server_id: str, server_info: ServerInfo) -> List[ServerMetric]:
        metrics = []
        
        try:
            if server_info.ip_address == "127.0.0.1" or server_info.hostname == "localhost":
                metrics.extend(await self._collect_local_metrics(server_id))
            else:
                metrics.extend(await self._collect_remote_metrics(server_id, server_info))
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics for server {server_id}: {str(e)}")
            return []

    async def _collect_local_metrics(self, server_id: str) -> List[ServerMetric]:
        metrics = []
        timestamp = datetime.utcnow()
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            metrics.append(ServerMetric(
                metric_id=f"cpu_{server_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                server_id=server_id,
                metric_type=MetricType.CPU,
                name="cpu_usage",
                value=cpu_percent,
                unit="percent",
                threshold_warning=80.0,
                threshold_critical=95.0,
                timestamp=timestamp,
                metadata={}
            ))
            
            metrics.append(ServerMetric(
                metric_id=f"memory_{server_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                server_id=server_id,
                metric_type=MetricType.MEMORY,
                name="memory_usage",
                value=memory.percent,
                unit="percent",
                threshold_warning=85.0,
                threshold_critical=95.0,
                timestamp=timestamp,
                metadata={"total": memory.total, "available": memory.available}
            ))
            
            metrics.append(ServerMetric(
                metric_id=f"disk_{server_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                server_id=server_id,
                metric_type=MetricType.DISK,
                name="disk_usage",
                value=(disk.used / disk.total) * 100,
                unit="percent",
                threshold_warning=85.0,
                threshold_critical=95.0,
                timestamp=timestamp,
                metadata={"total": disk.total, "used": disk.used, "free": disk.free}
            ))
            
            metrics.append(ServerMetric(
                metric_id=f"network_in_{server_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                server_id=server_id,
                metric_type=MetricType.NETWORK,
                name="network_bytes_in",
                value=network.bytes_recv,
                unit="bytes",
                threshold_warning=0.0,
                threshold_critical=0.0,
                timestamp=timestamp,
                metadata={}
            ))
            
            metrics.append(ServerMetric(
                metric_id=f"network_out_{server_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                server_id=server_id,
                metric_type=MetricType.NETWORK,
                name="network_bytes_out",
                value=network.bytes_sent,
                unit="bytes",
                threshold_warning=0.0,
                threshold_critical=0.0,
                timestamp=timestamp,
                metadata={}
            ))
            
        except Exception as e:
            self.logger.error(f"Failed to collect local metrics: {str(e)}")
        
        return metrics

    async def _collect_remote_metrics(self, server_id: str, server_info: ServerInfo) -> List[ServerMetric]:
        metrics = []
        timestamp = datetime.utcnow()
        
        try:
            health_url = f"http://{server_info.ip_address}:8080/health"
            response = requests.get(health_url, timeout=self.health_check_timeout_seconds)
            
            if response.status_code == 200:
                health_data = response.json()
                
                if "metrics" in health_data:
                    for metric_data in health_data["metrics"]:
                        metrics.append(ServerMetric(
                            metric_id=f"{metric_data['name']}_{server_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                            server_id=server_id,
                            metric_type=MetricType(metric_data.get("type", "custom")),
                            name=metric_data["name"],
                            value=float(metric_data["value"]),
                            unit=metric_data.get("unit", ""),
                            threshold_warning=float(metric_data.get("threshold_warning", 0.0)),
                            threshold_critical=float(metric_data.get("threshold_critical", 0.0)),
                            timestamp=timestamp,
                            metadata=metric_data.get("metadata", {})
                        ))
            else:
                self.logger.warning(f"Health check failed for server {server_id}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Failed to collect remote metrics for server {server_id}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error collecting remote metrics for server {server_id}: {str(e)}")
        
        return metrics

    async def _store_metrics(self, metrics: List[ServerMetric]):
        if not self.database or not metrics:
            return
        
        try:
            async with self.database.get_session() as session:
                for metric in metrics:
                    await session.execute("""
                        INSERT INTO server_metrics (
                            metric_id, server_id, metric_type, name, value, unit,
                            threshold_warning, threshold_critical, metadata
                        ) VALUES (
                            :metric_id, :server_id, :metric_type, :name, :value, :unit,
                            :threshold_warning, :threshold_critical, :metadata
                        )
                    """, {
                        "metric_id": metric.metric_id,
                        "server_id": metric.server_id,
                        "metric_type": metric.metric_type.value,
                        "name": metric.name,
                        "value": metric.value,
                        "unit": metric.unit,
                        "threshold_warning": metric.threshold_warning,
                        "threshold_critical": metric.threshold_critical,
                        "metadata": metric.metadata
                    })
                
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to store metrics: {str(e)}")

    async def _check_metric_thresholds(self, metrics: List[ServerMetric]):
        for metric in metrics:
            try:
                if metric.threshold_critical > 0 and metric.value >= metric.threshold_critical:
                    await self._create_alert(metric, AlertLevel.CRITICAL)
                elif metric.threshold_warning > 0 and metric.value >= metric.threshold_warning:
                    await self._create_alert(metric, AlertLevel.WARNING)
                    
            except Exception as e:
                self.logger.error(f"Failed to check thresholds for metric {metric.metric_id}: {str(e)}")

    async def _create_alert(self, metric: ServerMetric, alert_level: AlertLevel):
        try:
            alert_id = f"alert_{metric.server_id}_{metric.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            if alert_id in self.active_alerts:
                return
            
            threshold_value = metric.threshold_critical if alert_level == AlertLevel.CRITICAL else metric.threshold_warning
            
            alert = MonitoringAlert(
                alert_id=alert_id,
                server_id=metric.server_id,
                metric_name=metric.name,
                alert_level=alert_level,
                current_value=metric.value,
                threshold_value=threshold_value,
                message=f"{metric.name} is {metric.value}{metric.unit}, exceeding {alert_level.value} threshold of {threshold_value}{metric.unit}",
                timestamp=datetime.utcnow(),
                acknowledged=False,
                resolved=False
            )
            
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO monitoring_alerts (
                        alert_id, server_id, metric_name, alert_level, current_value,
                        threshold_value, message, timestamp
                    ) VALUES (
                        :alert_id, :server_id, :metric_name, :alert_level, :current_value,
                        :threshold_value, :message, :timestamp
                    )
                """, {
                    "alert_id": alert.alert_id,
                    "server_id": alert.server_id,
                    "metric_name": alert.metric_name,
                    "alert_level": alert.alert_level.value,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "message": alert.message,
                    "timestamp": alert.timestamp
                })
                await session.commit()
            
            self.active_alerts[alert_id] = alert
            self.logger.warning(f"Monitoring alert created: {alert.message}")
            
        except Exception as e:
            self.logger.error(f"Failed to create alert: {str(e)}")

    async def _update_server_status(self, server_id: str, status: MonitoringStatus):
        try:
            if server_id in self.monitored_servers:
                self.monitored_servers[server_id].status = status
                self.monitored_servers[server_id].last_seen = datetime.utcnow()
            
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE monitored_servers 
                    SET status = :status, last_seen = :last_seen, updated_at = :updated_at
                    WHERE server_id = :server_id
                """, {
                    "server_id": server_id,
                    "status": status.value,
                    "last_seen": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to update server status: {str(e)}")

    async def _check_server_health_internal(self):
        for server_id, server_info in self.monitored_servers.items():
            try:
                if server_info.ip_address == "127.0.0.1" or server_info.hostname == "localhost":
                    continue
                
                health_url = f"http://{server_info.ip_address}:8080/health"
                response = requests.get(health_url, timeout=self.health_check_timeout_seconds)
                
                if response.status_code == 200:
                    await self._update_server_status(server_id, MonitoringStatus.HEALTHY)
                else:
                    await self._update_server_status(server_id, MonitoringStatus.WARNING)
                    
            except requests.exceptions.RequestException:
                await self._update_server_status(server_id, MonitoringStatus.OFFLINE)
            except Exception as e:
                self.logger.error(f"Health check failed for server {server_id}: {str(e)}")

    async def _cleanup_old_metrics_internal(self):
        if not self.database:
            return
        
        cutoff_time = datetime.utcnow() - timedelta(hours=self.metric_retention_hours)
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                DELETE FROM server_metrics 
                WHERE timestamp < :cutoff_time
            """, {"cutoff_time": cutoff_time})
            
            deleted_count = result.rowcount
            await session.commit()
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old metrics")

    async def get_server_metrics(
        self,
        server_id: str,
        metric_type: Optional[MetricType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[ServerMetric]:
        if not self.database:
            return []
        
        conditions = ["server_id = :server_id"]
        params = {"server_id": server_id, "limit": limit}
        
        if metric_type:
            conditions.append("metric_type = :metric_type")
            params["metric_type"] = metric_type.value
        
        if start_date:
            conditions.append("timestamp >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            conditions.append("timestamp <= :end_date")
            params["end_date"] = end_date
        
        where_clause = "WHERE " + " AND ".join(conditions)
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT metric_id, server_id, metric_type, name, value, unit,
                       threshold_warning, threshold_critical, timestamp, metadata
                FROM server_metrics
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT :limit
            """, params)
            
            metrics = []
            for row in result:
                metric = ServerMetric(
                    metric_id=row.metric_id,
                    server_id=row.server_id,
                    metric_type=MetricType(row.metric_type),
                    name=row.name,
                    value=row.value,
                    unit=row.unit,
                    threshold_warning=row.threshold_warning,
                    threshold_critical=row.threshold_critical,
                    timestamp=row.timestamp,
                    metadata=row.metadata or {}
                )
                metrics.append(metric)
            
            return metrics

    async def get_monitoring_alerts(
        self,
        server_id: Optional[str] = None,
        alert_level: Optional[AlertLevel] = None,
        acknowledged: Optional[bool] = None,
        resolved: Optional[bool] = None,
        limit: int = 100
    ) -> List[MonitoringAlert]:
        if not self.database:
            return []
        
        conditions = []
        params = {"limit": limit}
        
        if server_id:
            conditions.append("server_id = :server_id")
            params["server_id"] = server_id
        
        if alert_level:
            conditions.append("alert_level = :alert_level")
            params["alert_level"] = alert_level.value
        
        if acknowledged is not None:
            conditions.append("acknowledged = :acknowledged")
            params["acknowledged"] = acknowledged
        
        if resolved is not None:
            conditions.append("resolved = :resolved")
            params["resolved"] = resolved
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT alert_id, server_id, metric_name, alert_level, current_value,
                       threshold_value, message, timestamp, acknowledged, resolved, resolved_at
                FROM monitoring_alerts
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT :limit
            """, params)
            
            alerts = []
            for row in result:
                alert = MonitoringAlert(
                    alert_id=row.alert_id,
                    server_id=row.server_id,
                    metric_name=row.metric_name,
                    alert_level=AlertLevel(row.alert_level),
                    current_value=row.current_value,
                    threshold_value=row.threshold_value,
                    message=row.message,
                    timestamp=row.timestamp,
                    acknowledged=row.acknowledged,
                    resolved=row.resolved
                )
                alerts.append(alert)
            
            return alerts

    async def acknowledge_alert(self, alert_id: str) -> bool:
        try:
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE monitoring_alerts 
                    SET acknowledged = TRUE
                    WHERE alert_id = :alert_id
                """, {"alert_id": alert_id})
                await session.commit()
            
            if alert_id in self.active_alerts:
                self.active_alerts[alert_id].acknowledged = True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert: {str(e)}")
            return False

    async def resolve_alert(self, alert_id: str) -> bool:
        try:
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE monitoring_alerts 
                    SET resolved = TRUE, resolved_at = :resolved_at
                    WHERE alert_id = :alert_id
                """, {
                    "alert_id": alert_id,
                    "resolved_at": datetime.utcnow()
                })
                await session.commit()
            
            if alert_id in self.active_alerts:
                self.active_alerts[alert_id].resolved = True
                del self.active_alerts[alert_id]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to resolve alert: {str(e)}")
            return False

    async def get_monitoring_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if not self.database:
            return {}
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT 
                    COUNT(DISTINCT server_id) as total_servers,
                    COUNT(CASE WHEN status = 'healthy' THEN 1 END) as healthy_servers,
                    COUNT(CASE WHEN status = 'warning' THEN 1 END) as warning_servers,
                    COUNT(CASE WHEN status = 'critical' THEN 1 END) as critical_servers,
                    COUNT(CASE WHEN status = 'offline' THEN 1 END) as offline_servers
                FROM monitored_servers
            """)
            
            server_stats = result.fetchone()
            
            result = await session.execute("""
                SELECT 
                    COUNT(*) as total_alerts,
                    COUNT(CASE WHEN alert_level = 'critical' THEN 1 END) as critical_alerts,
                    COUNT(CASE WHEN alert_level = 'warning' THEN 1 END) as warning_alerts,
                    COUNT(CASE WHEN acknowledged = TRUE THEN 1 END) as acknowledged_alerts,
                    COUNT(CASE WHEN resolved = TRUE THEN 1 END) as resolved_alerts
                FROM monitoring_alerts
                WHERE timestamp BETWEEN :start_date AND :end_date
            """, {"start_date": start_date, "end_date": end_date})
            
            alert_stats = result.fetchone()
            
            return {
                "total_servers": server_stats.total_servers,
                "healthy_servers": server_stats.healthy_servers,
                "warning_servers": server_stats.warning_servers,
                "critical_servers": server_stats.critical_servers,
                "offline_servers": server_stats.offline_servers,
                "total_alerts": alert_stats.total_alerts,
                "critical_alerts": alert_stats.critical_alerts,
                "warning_alerts": alert_stats.warning_alerts,
                "acknowledged_alerts": alert_stats.acknowledged_alerts,
                "resolved_alerts": alert_stats.resolved_alerts,
                "alert_resolution_rate": (alert_stats.resolved_alerts / alert_stats.total_alerts * 100) if alert_stats.total_alerts > 0 else 0
            }

_monitoring_manager: Optional[ServerMonitoringManager] = None

async def get_monitoring_manager() -> ServerMonitoringManager:
    global _monitoring_manager
    if _monitoring_manager is None:
        _monitoring_manager = ServerMonitoringManager()
        await _monitoring_manager.initialize()
    return _monitoring_manager

async def init_monitoring_manager() -> ServerMonitoringManager:
    return await get_monitoring_manager()
