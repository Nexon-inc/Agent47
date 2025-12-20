import asyncio
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from core.database import get_database
from core.cache import get_redis
from core.logs import get_logger
from core.config import get_settings


class PerformanceMetric(Enum):
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IO = "network_io"


class PerformanceLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class PerformanceData:
    id: str
    metric_type: PerformanceMetric
    value: float
    unit: str
    level: PerformanceLevel
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PerformanceAlert:
    id: str
    metric_type: PerformanceMetric
    threshold: float
    current_value: float
    severity: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PerformanceSnapshot:
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    disk_io: Dict[str, float]
    process_count: int
    thread_count: int
    handle_count: int
    database_connections: int
    redis_connections: int
    kafka_lag: float
    chroma_operations: int
    response_time_avg: float
    throughput: float
    error_rate: float
    concurrent_users: int


class PerformanceMonitor:
    def __init__(self):
        self.config = get_settings()
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()
        
        # Performance thresholds
        self.thresholds = {
            PerformanceMetric.CPU_USAGE: {"warning": 70, "critical": 90},
            PerformanceMetric.MEMORY_USAGE: {"warning": 80, "critical": 95},
            PerformanceMetric.DISK_USAGE: {"warning": 85, "critical": 95}
        }
    
    async def collect_performance_metrics(self) -> List[PerformanceData]:
        """Collect current performance metrics"""
        try:
            metrics = []
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_level = self._determine_performance_level(cpu_percent, PerformanceMetric.CPU_USAGE)
            metrics.append(PerformanceData(
                id=f"cpu_{datetime.utcnow().timestamp()}",
                metric_type=PerformanceMetric.CPU_USAGE,
                value=cpu_percent,
                unit="%",
                level=cpu_level
            ))
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_level = self._determine_performance_level(memory.percent, PerformanceMetric.MEMORY_USAGE)
            metrics.append(PerformanceData(
                id=f"memory_{datetime.utcnow().timestamp()}",
                metric_type=PerformanceMetric.MEMORY_USAGE,
                value=memory.percent,
                unit="%",
                level=memory_level
            ))
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_level = self._determine_performance_level(disk.percent, PerformanceMetric.DISK_USAGE)
            metrics.append(PerformanceData(
                id=f"disk_{datetime.utcnow().timestamp()}",
                metric_type=PerformanceMetric.DISK_USAGE,
                value=disk.percent,
                unit="%",
                level=disk_level
            ))
            
            # Store metrics
            await self._store_performance_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect performance metrics: {e}")
            return []
    
    def _determine_performance_level(self, value: float, metric_type: PerformanceMetric) -> PerformanceLevel:
        """Determine performance level based on value and thresholds"""
        thresholds = self.thresholds.get(metric_type, {})
        warning_threshold = thresholds.get("warning", 80)
        critical_threshold = thresholds.get("critical", 95)
        
        if value >= critical_threshold:
            return PerformanceLevel.CRITICAL
        elif value >= warning_threshold:
            return PerformanceLevel.POOR
        elif value >= warning_threshold * 0.7:
            return PerformanceLevel.FAIR
        elif value >= warning_threshold * 0.5:
            return PerformanceLevel.GOOD
        else:
            return PerformanceLevel.EXCELLENT
    
    async def _store_performance_metrics(self, metrics: List[PerformanceData]):
        """Store performance metrics in database"""
        try:
            for metric in metrics:
                await self.db.execute(
                    """
                    INSERT INTO performance_metrics 
                    (id, metric_type, value, unit, level, timestamp)
                    VALUES (:id, :metric_type, :value, :unit, :level, :timestamp)
                    """,
                    {
                        "id": metric.id,
                        "metric_type": metric.metric_type.value,
                        "value": metric.value,
                        "unit": metric.unit,
                        "level": metric.level.value,
                        "timestamp": metric.timestamp
                    }
                )
        except Exception as e:
            self.logger.error(f"Failed to store performance metrics: {e}")
    
    async def _check_performance_alerts(self, metrics: List[PerformanceData]):
        """Check for performance alerts"""
        try:
            alerts = []
            
            for metric in metrics:
                thresholds = self.thresholds.get(metric.metric_type, {})
                warning_threshold = thresholds.get("warning")
                critical_threshold = thresholds.get("critical")
                
                if critical_threshold and metric.value >= critical_threshold:
                    alerts.append(PerformanceAlert(
                        id=f"alert_{metric.id}",
                        metric_type=metric.metric_type,
                        threshold=critical_threshold,
                        current_value=metric.value,
                        severity="critical",
                        message=f"Critical {metric.metric_type.value}: {metric.value}{metric.unit}"
                    ))
                elif warning_threshold and metric.value >= warning_threshold:
                    alerts.append(PerformanceAlert(
                        id=f"alert_{metric.id}",
                        metric_type=metric.metric_type,
                        threshold=warning_threshold,
                        current_value=metric.value,
                        severity="warning",
                        message=f"Warning {metric.metric_type.value}: {metric.value}{metric.unit}"
                    ))
            
            # Store and send alerts
            for alert in alerts:
                await self._store_performance_alert(alert)
                await self._send_performance_alert(alert)
                            
        except Exception as e:
            self.logger.error(f"Failed to check performance alerts: {e}")
    
    async def _store_performance_alert(self, alert: PerformanceAlert):
        """Store performance alert"""
        try:
            await self.db.execute(
                """
                INSERT INTO performance_alerts 
                (id, metric_type, threshold, current_value, severity, message, timestamp)
                VALUES (:id, :metric_type, :threshold, :current_value, :severity, :message, :timestamp)
                """,
                {
                    "id": alert.id,
                    "metric_type": alert.metric_type.value,
                    "threshold": alert.threshold,
                    "current_value": alert.current_value,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to store performance alert: {e}")

    async def _send_performance_alert(self, alert: PerformanceAlert):
        """Send performance alert"""
        try:
            alert_data = {
                "type": "performance_alert",
                "metric_type": alert.metric_type.value,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat()
            }
            
            await self.redis.publish("admin:performance_alerts", alert_data)
            
        except Exception as e:
            self.logger.error(f"Failed to send performance alert: {e}")
    
    async def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            metrics = await self.db.fetch_all(
                """
                SELECT metric_type, value, level, timestamp 
                FROM performance_metrics 
                WHERE timestamp >= :since
                ORDER BY timestamp DESC
                """,
                {"since": since}
            )
            
            summary = {
                "cpu_usage": {"current": 0, "average": 0, "max": 0},
                "memory_usage": {"current": 0, "average": 0, "max": 0},
                "disk_usage": {"current": 0, "average": 0, "max": 0}
            }
            
            # Group metrics by type
            metrics_by_type = {}
            for row in metrics:
                metric_type = row["metric_type"]
                if metric_type not in metrics_by_type:
                    metrics_by_type[metric_type] = []
                metrics_by_type[metric_type].append(row)
            
            # Calculate summaries
            for metric_type, metric_list in metrics_by_type.items():
                if metric_list:
                    values = [m["value"] for m in metric_list]
                    summary[metric_type] = {
                        "current": values[0],
                        "average": sum(values) / len(values),
                        "max": max(values)
                    }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get performance summary: {e}")
            return {}
    
    async def get_performance_history(self, metric_type: PerformanceMetric, 
                                    hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance history for a specific metric"""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            rows = await self.db.fetch_all(
                """
                SELECT value, level, timestamp 
                FROM performance_metrics 
                WHERE metric_type = :metric_type AND timestamp >= :since
                    ORDER BY timestamp ASC
                """,
                {
                    "metric_type": metric_type.value,
                    "since": since
                }
            )
            
            history = []
            for row in rows:
                history.append({
                    "value": row["value"],
                    "level": row["level"],
                    "timestamp": row["timestamp"].isoformat()
                })
            
            return history
                
        except Exception as e:
            self.logger.error(f"Failed to get performance history: {e}")
            return []

# Singleton instance
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

def init_performance_monitor():
    """Initialize performance monitoring system"""
    global _performance_monitor
    _performance_monitor = PerformanceMonitor()
    return _performance_monitor
