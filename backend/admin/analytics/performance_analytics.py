import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from core.database import get_database
from core.cache import get_redis
from core.logs import get_logger
from .analytics_manager import TimeRange


class PerfMetric(Enum):
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"


@dataclass
class PerfSummary:
    metric: PerfMetric
    average: float
    p95: float
    max_value: float
    min_value: float
    trend: str
    change_percentage: float


class PerformanceAnalytics:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()

    async def initialize(self):
        return True

    async def get_summary(self, time_range: TimeRange = TimeRange.DAY) -> Dict[str, Any]:
        start_time = self._get_start_time(time_range)
        end_time = datetime.utcnow()
        summaries: List[PerfSummary] = []
        for metric in [
            PerfMetric.RESPONSE_TIME,
            PerfMetric.THROUGHPUT,
            PerfMetric.ERROR_RATE,
        ]:
            summary = await self._summarize_metric(metric, start_time, end_time)
            if summary:
                summaries.append(summary)
        resource_summaries: List[PerfSummary] = []
        for metric in [PerfMetric.CPU_USAGE, PerfMetric.MEMORY_USAGE]:
            rs = await self._summarize_resource_metric(metric, start_time, end_time)
            if rs:
                resource_summaries.append(rs)
        return {
            "period": {"start": start_time.isoformat(), "end": end_time.isoformat()},
            "api_metrics": [s.__dict__ for s in summaries],
            "resource_metrics": [s.__dict__ for s in resource_summaries],
        }

    async def _summarize_metric(self, metric: PerfMetric, start: datetime, end: datetime) -> Optional[PerfSummary]:
        name_map = {
            PerfMetric.RESPONSE_TIME: "%response_time%",
            PerfMetric.THROUGHPUT: "%throughput%",
            PerfMetric.ERROR_RATE: "%error_rate%",
        }
        try:
            async with self.db.get_session() as session:
                result = await session.execute(
                    """
                    SELECT AVG(metric_value) avg_v,
                           PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY metric_value) p95_v,
                           MAX(metric_value) max_v,
                           MIN(metric_value) min_v
                    FROM analytics_metrics
                    WHERE metric_name LIKE %s AND timestamp BETWEEN %s AND %s
                    """,
                    (name_map[metric], start, end),
                )
                row = result.fetchone()
                if not row:
                    return None
                prev_start = start - (end - start)
                prev_end = start
                result2 = await session.execute(
                    """
                    SELECT AVG(metric_value) avg_v
                    FROM analytics_metrics
                    WHERE metric_name LIKE %s AND timestamp BETWEEN %s AND %s
                    """,
                    (name_map[metric], prev_start, prev_end),
                )
                prev_avg = float(result2.scalar() or 0.0)
                avg_v = float(row.avg_v or 0.0)
                change = ((avg_v - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0.0
                trend = "increasing" if change > 3 else ("decreasing" if change < -3 else "stable")
                return PerfSummary(metric=metric, average=avg_v, p95=float(row.p95_v or 0.0), max_value=float(row.max_v or 0.0), min_value=float(row.min_v or 0.0), trend=trend, change_percentage=change)
        except Exception as e:
            self.logger.error(f"Failed to summarize metric {metric.value}: {e}")
            return None

    async def _summarize_resource_metric(self, metric: PerfMetric, start: datetime, end: datetime) -> Optional[PerfSummary]:
        column = "cpu_usage" if metric == PerfMetric.CPU_USAGE else "memory_usage"
        try:
            async with self.db.get_session() as session:
                result = await session.execute(
                    f"""
                    SELECT AVG({column}) avg_v,
                           PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {column}) p95_v,
                           MAX({column}) max_v,
                           MIN({column}) min_v
                    FROM performance_snapshots
                    WHERE timestamp BETWEEN %s AND %s
                    """,
                    (start, end),
                )
                row = result.fetchone()
                if not row:
                    return None
                prev_start = start - (end - start)
                prev_end = start
                result2 = await session.execute(
                    f"""
                    SELECT AVG({column}) avg_v
                    FROM performance_snapshots
                    WHERE timestamp BETWEEN %s AND %s
                    """,
                    (prev_start, prev_end),
                )
                prev_avg = float(result2.scalar() or 0.0)
                avg_v = float(row.avg_v or 0.0)
                change = ((avg_v - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0.0
                trend = "increasing" if change > 3 else ("decreasing" if change < -3 else "stable")
                return PerfSummary(metric=metric, average=avg_v, p95=float(row.p95_v or 0.0), max_value=float(row.max_v or 0.0), min_value=float(row.min_v or 0.0), trend=trend, change_percentage=change)
        except Exception as e:
            self.logger.error(f"Failed to summarize resource metric {metric.value}: {e}")
            return None

    def _get_start_time(self, tr: TimeRange) -> datetime:
        now = datetime.utcnow()
        if tr == TimeRange.HOUR:
            return now - timedelta(hours=1)
        if tr == TimeRange.DAY:
            return now - timedelta(days=1)
        if tr == TimeRange.WEEK:
            return now - timedelta(weeks=1)
        if tr == TimeRange.MONTH:
            return now - timedelta(days=30)
        if tr == TimeRange.QUARTER:
            return now - timedelta(days=90)
        return now - timedelta(days=365)


_performance_analytics: Optional[PerformanceAnalytics] = None


async def get_performance_analytics() -> PerformanceAnalytics:
    global _performance_analytics
    if _performance_analytics is None:
        _performance_analytics = PerformanceAnalytics()
        await _performance_analytics.initialize()
    return _performance_analytics


async def init_performance_analytics() -> PerformanceAnalytics:
    analytics = PerformanceAnalytics()
    await analytics.initialize()
    return analytics
