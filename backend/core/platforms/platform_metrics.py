import time
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import asyncio
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics that can be tracked."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"

@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: datetime
    value: Union[int, float]
    labels: Dict[str, str]
    metric_type: MetricType

@dataclass
class MetricSummary:
    """Summary statistics for a metric."""
    count: int
    sum: float
    min: float
    max: float
    avg: float
    p50: float
    p95: float
    p99: float

class PlatformMetrics:
    """Manages platform performance and usage metrics."""
    
    def __init__(self, retention_days: int = 30, max_points_per_metric: int = 10000):
        self.retention_days = retention_days
        self.max_points_per_metric = max_points_per_metric
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points_per_metric))
        self.metric_types: Dict[str, MetricType] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start the background cleanup task."""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(3600)  # Run every hour
                    self._cleanup_old_metrics()
                except Exception as e:
                    logger.error(f"Error in metrics cleanup: {e}")
        
        try:
            self._cleanup_task = asyncio.create_task(cleanup_loop())
        except RuntimeError:
            # Event loop not running, skip cleanup task
            pass
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        cutoff_time = datetime.utcnow() - timedelta(days=self.retention_days)
        
        for metric_name, points in self.metrics.items():
            # Remove old points
            while points and points[0].timestamp < cutoff_time:
                points.popleft()
    
    def record_counter(
        self, 
        metric_name: str, 
        value: int = 1, 
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Record a counter metric.
        
        Args:
            metric_name: Name of the metric
            value: Value to increment by (default 1)
            labels: Optional labels for the metric
        """
        try:
            labels = labels or {}
            point = MetricPoint(
                timestamp=datetime.utcnow(),
                value=value,
                labels=labels,
                metric_type=MetricType.COUNTER
            )
            
            self.metrics[metric_name].append(point)
            self.metric_types[metric_name] = MetricType.COUNTER
            
            logger.debug(f"Recorded counter metric: {metric_name} = {value}")
            
        except Exception as e:
            logger.error(f"Failed to record counter metric: {e}")
    
    def record_gauge(
        self, 
        metric_name: str, 
        value: float, 
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Record a gauge metric.
        
        Args:
            metric_name: Name of the metric
            value: Current value
            labels: Optional labels for the metric
        """
        try:
            labels = labels or {}
            point = MetricPoint(
                timestamp=datetime.utcnow(),
                value=value,
                labels=labels,
                metric_type=MetricType.GAUGE
            )
            
            self.metrics[metric_name].append(point)
            self.metric_types[metric_name] = MetricType.GAUGE
            
            logger.debug(f"Recorded gauge metric: {metric_name} = {value}")
            
        except Exception as e:
            logger.error(f"Failed to record gauge metric: {e}")
    
    def record_histogram(
        self, 
        metric_name: str, 
        value: float, 
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Record a histogram metric.
        
        Args:
            metric_name: Name of the metric
            value: Value to record
            labels: Optional labels for the metric
        """
        try:
            labels = labels or {}
            point = MetricPoint(
                timestamp=datetime.utcnow(),
                value=value,
                labels=labels,
                metric_type=MetricType.HISTOGRAM
            )
            
            self.metrics[metric_name].append(point)
            self.metric_types[metric_name] = MetricType.HISTOGRAM
            
            logger.debug(f"Recorded histogram metric: {metric_name} = {value}")
            
        except Exception as e:
            logger.error(f"Failed to record histogram metric: {e}")
    
    def record_timer(
        self, 
        metric_name: str, 
        duration_seconds: float, 
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Record a timer metric.
        
        Args:
            metric_name: Name of the metric
            duration_seconds: Duration in seconds
            labels: Optional labels for the metric
        """
        try:
            labels = labels or {}
            point = MetricPoint(
                timestamp=datetime.utcnow(),
                value=duration_seconds,
                labels=labels,
                metric_type=MetricType.TIMER
            )
            
            self.metrics[metric_name].append(point)
            self.metric_types[metric_name] = MetricType.TIMER
            
            logger.debug(f"Recorded timer metric: {metric_name} = {duration_seconds}s")
            
        except Exception as e:
            logger.error(f"Failed to record timer metric: {e}")
    
    def record_rate(
        self, 
        metric_name: str, 
        value: float, 
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Record a rate metric (events per second).
        
        Args:
            metric_name: Name of the metric
            value: Rate value
            labels: Optional labels for the metric
        """
        try:
            labels = labels or {}
            point = MetricPoint(
                timestamp=datetime.utcnow(),
                value=value,
                labels=labels,
                metric_type=MetricType.RATE
            )
            
            self.metrics[metric_name].append(point)
            self.metric_types[metric_name] = MetricType.RATE
            
            logger.debug(f"Recorded rate metric: {metric_name} = {value}")
            
        except Exception as e:
            logger.error(f"Failed to record rate metric: {e}")
    
    def get_metric_summary(
        self, 
        metric_name: str, 
        time_range_minutes: int = 60,
        labels_filter: Optional[Dict[str, str]] = None
    ) -> Optional[MetricSummary]:
        """
        Get summary statistics for a metric.
        
        Args:
            metric_name: Name of the metric
            time_range_minutes: Time range in minutes to analyze
            labels_filter: Optional filter for specific labels
            
        Returns:
            MetricSummary or None if no data
        """
        try:
            if metric_name not in self.metrics:
                return None
            
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_range_minutes)
            points = self.metrics[metric_name]
            
            # Filter by time and labels
            filtered_points = []
            for point in points:
                if point.timestamp >= cutoff_time:
                    if labels_filter is None or all(
                        point.labels.get(k) == v for k, v in labels_filter.items()
                    ):
                        filtered_points.append(point.value)
            
            if not filtered_points:
                return None
            
            # Calculate statistics
            values = sorted(filtered_points)
            count = len(values)
            total = sum(values)
            
            return MetricSummary(
                count=count,
                sum=total,
                min=values[0],
                max=values[-1],
                avg=total / count,
                p50=self._percentile(values, 50),
                p95=self._percentile(values, 95),
                p99=self._percentile(values, 99)
            )
            
        except Exception as e:
            logger.error(f"Failed to get metric summary: {e}")
            return None
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0
        
        index = int((percentile / 100) * (len(values) - 1))
        return values[index]
    
    def get_metric_trend(
        self, 
        metric_name: str, 
        time_range_minutes: int = 60,
        interval_minutes: int = 5,
        labels_filter: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get metric trend data over time.
        
        Args:
            metric_name: Name of the metric
            time_range_minutes: Total time range in minutes
            interval_minutes: Interval between data points
            labels_filter: Optional filter for specific labels
            
        Returns:
            List of trend data points
        """
        try:
            if metric_name not in self.metrics:
                return []
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_range_minutes)
            points = self.metrics[metric_name]
            
            # Group points by interval
            intervals = {}
            interval_seconds = interval_minutes * 60
            
            for point in points:
                if start_time <= point.timestamp <= end_time:
                    if labels_filter is None or all(
                        point.labels.get(k) == v for k, v in labels_filter.items()
                    ):
                        interval_start = point.timestamp.replace(
                            second=point.timestamp.second - (point.timestamp.second % interval_seconds),
                            microsecond=0
                        )
                        
                        if interval_start not in intervals:
                            intervals[interval_start] = []
                        intervals[interval_start].append(point.value)
            
            # Calculate summary for each interval
            trend_data = []
            for interval_start, values in sorted(intervals.items()):
                if values:
                    trend_data.append({
                        "timestamp": interval_start.isoformat(),
                        "count": len(values),
                        "sum": sum(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values)
                    })
            
            return trend_data
            
        except Exception as e:
            logger.error(f"Failed to get metric trend: {e}")
            return []
    
    def get_platform_metrics(self, platform_name: str) -> Dict[str, Any]:
        """
        Get comprehensive metrics for a specific platform.
        
        Args:
            platform_name: Name of the platform
            
        Returns:
            Dictionary with platform metrics
        """
        try:
            platform_metrics = {}
            
            # Filter metrics by platform name
            for metric_name, points in self.metrics.items():
                if any(f"platform={platform_name}" in str(point.labels) for point in points):
                    summary = self.get_metric_summary(metric_name, time_range_minutes=60)
                    if summary:
                        platform_metrics[metric_name] = asdict(summary)
            
            return {
                "platform": platform_name,
                "metrics": platform_metrics,
                "total_metrics": len(platform_metrics),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get platform metrics: {e}")
            return {}
    
    def get_all_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of all metrics.
        
        Returns:
            Dictionary with overall metrics summary
        """
        try:
            summary = {
                "total_metrics": len(self.metrics),
                "metric_types": {},
                "top_metrics": [],
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Count by metric type
            for metric_name, metric_type in self.metric_types.items():
                metric_type_name = metric_type.value
                if metric_type_name not in summary["metric_types"]:
                    summary["metric_types"][metric_type_name] = 0
                summary["metric_types"][metric_type_name] += 1
            
            # Get top metrics by data point count
            metric_counts = [(name, len(points)) for name, points in self.metrics.items()]
            metric_counts.sort(key=lambda x: x[1], reverse=True)
            
            summary["top_metrics"] = [
                {"name": name, "data_points": count} 
                for name, count in metric_counts[:10]
            ]
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get all metrics summary: {e}")
            return {}
    
    def clear_metrics(self, metric_name: Optional[str] = None):
        """
        Clear metrics data.
        
        Args:
            metric_name: Specific metric to clear, or None to clear all
        """
        try:
            if metric_name:
                if metric_name in self.metrics:
                    self.metrics[metric_name].clear()
                    logger.info(f"Cleared metrics for: {metric_name}")
            else:
                self.metrics.clear()
                self.metric_types.clear()
                logger.info("Cleared all metrics")
                
        except Exception as e:
            logger.error(f"Failed to clear metrics: {e}")
    
    def export_metrics(self, format: str = "json") -> str:
        """
        Export metrics data.
        
        Args:
            format: Export format (json, csv)
            
        Returns:
            Exported data as string
        """
        try:
            if format.lower() == "json":
                export_data = {
                    "exported_at": datetime.utcnow().isoformat(),
                    "metrics": {}
                }
                
                for metric_name, points in self.metrics.items():
                    export_data["metrics"][metric_name] = {
                        "type": self.metric_types.get(metric_name, "unknown").value,
                        "points": [
                            {
                                "timestamp": point.timestamp.isoformat(),
                                "value": point.value,
                                "labels": point.labels
                            }
                            for point in points
                        ]
                    }
                
                return json.dumps(export_data, indent=2)
            
            elif format.lower() == "csv":
                csv_lines = ["metric_name,timestamp,value,labels,type"]
                
                for metric_name, points in self.metrics.items():
                    metric_type = self.metric_types.get(metric_name, "unknown").value
                    for point in points:
                        labels_str = json.dumps(point.labels)
                        csv_lines.append(
                            f"{metric_name},{point.timestamp.isoformat()},{point.value},{labels_str},{metric_type}"
                        )
                
                return "\n".join(csv_lines)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return ""

# Global instance
platform_metrics = PlatformMetrics()

def get_platform_metrics() -> PlatformMetrics:
    """Get the global platform metrics instance."""
    return platform_metrics
