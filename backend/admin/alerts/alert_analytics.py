import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text
import statistics

from core.database import get_database, DatabaseManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class AnalyticsPeriod(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

class TrendDirection(Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"

@dataclass
class AlertMetrics:
    total_alerts: int
    active_alerts: int
    resolved_alerts: int
    critical_alerts: int
    warning_alerts: int
    info_alerts: int
    average_resolution_time_minutes: float
    escalation_rate: float
    false_positive_rate: float
    alert_volume_trend: TrendDirection
    resolution_trend: TrendDirection

@dataclass
class AlertTrend:
    period: str
    alert_count: int
    resolution_count: int
    escalation_count: int
    average_resolution_time: float
    trend_direction: TrendDirection

@dataclass
class AlertPattern:
    pattern_id: str
    name: str
    description: str
    frequency: int
    severity_distribution: Dict[str, int]
    source_distribution: Dict[str, int]
    time_patterns: Dict[str, Any]
    confidence_score: float
    recommendations: List[str]

@dataclass
class AlertCorrelation:
    correlation_id: str
    alert_ids: List[str]
    correlation_type: str
    confidence_score: float
    pattern_description: str
    suggested_action: str

class AlertAnalytics(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.cache_duration_minutes = 15
        self.cached_metrics: Dict[str, Tuple[AlertMetrics, datetime]] = {}
        self.cached_trends: Dict[str, Tuple[List[AlertTrend], datetime]] = {}
        self.pattern_detection_enabled = True
        self.correlation_analysis_enabled = True

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing AlertAnalytics...")
            self.database = get_database()
            await self._setup_analytics_tables()
            await self._start_analytics_processor()
            self.logger.info("AlertAnalytics initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize AlertAnalytics: {str(e)}")
            return False

    async def _setup_analytics_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS alert_analytics_cache (
                    id SERIAL PRIMARY KEY,
                    cache_key VARCHAR(255) UNIQUE NOT NULL,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS alert_patterns (
                    id SERIAL PRIMARY KEY,
                    pattern_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    frequency INTEGER NOT NULL,
                    severity_distribution JSONB,
                    source_distribution JSONB,
                    time_patterns JSONB,
                    confidence_score FLOAT,
                    recommendations JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS alert_correlations (
                    id SERIAL PRIMARY KEY,
                    correlation_id VARCHAR(255) UNIQUE NOT NULL,
                    alert_ids JSONB NOT NULL,
                    correlation_type VARCHAR(100) NOT NULL,
                    confidence_score FLOAT NOT NULL,
                    pattern_description TEXT,
                    suggested_action TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_alert_analytics_cache_expires 
                ON alert_analytics_cache(expires_at);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_alert_patterns_confidence 
                ON alert_patterns(confidence_score);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_alert_correlations_confidence 
                ON alert_correlations(confidence_score);
            """)
            
            await session.commit()

    async def _start_analytics_processor(self):
        asyncio.create_task(self._process_analytics())

    async def _process_analytics(self):
        while True:
            try:
                if self.pattern_detection_enabled:
                    await self._detect_alert_patterns()
                
                if self.correlation_analysis_enabled:
                    await self._analyze_alert_correlations()
                
                await self._cleanup_expired_cache()
                await asyncio.sleep(300)
            except Exception as e:
                self.logger.error(f"Error in analytics processor: {str(e)}")
                await asyncio.sleep(600)

    async def get_alert_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        use_cache: bool = True
    ) -> AlertMetrics:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        cache_key = f"metrics_{start_date.isoformat()}_{end_date.isoformat()}"
        
        if use_cache and cache_key in self.cached_metrics:
            metrics, cached_at = self.cached_metrics[cache_key]
            if datetime.utcnow() - cached_at < timedelta(minutes=self.cache_duration_minutes):
                return metrics
        
        if not self.database:
            return AlertMetrics(0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, TrendDirection.STABLE, TrendDirection.STABLE)
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT 
                    COUNT(*) as total_alerts,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_alerts,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_alerts,
                    COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_alerts,
                    COUNT(CASE WHEN severity = 'warning' THEN 1 END) as warning_alerts,
                    COUNT(CASE WHEN severity = 'info' THEN 1 END) as info_alerts
                FROM alerts
                WHERE created_at BETWEEN :start_date AND :end_date
            """, {"start_date": start_date, "end_date": end_date})
            
            row = result.fetchone()
            if not row:
                return AlertMetrics(0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, TrendDirection.STABLE, TrendDirection.STABLE)
            
            resolution_time_result = await session.execute("""
                SELECT AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/60) as avg_resolution_time
                FROM alerts
                WHERE status = 'resolved' 
                AND created_at BETWEEN :start_date AND :end_date
                AND resolved_at IS NOT NULL
            """, {"start_date": start_date, "end_date": end_date})
            
            resolution_time_row = resolution_time_result.fetchone()
            avg_resolution_time = resolution_time_row.avg_resolution_time or 0.0
            
            escalation_result = await session.execute("""
                SELECT COUNT(*) as escalation_count
                FROM escalation_events
                WHERE triggered_at BETWEEN :start_date AND :end_date
            """, {"start_date": start_date, "end_date": end_date})
            
            escalation_row = escalation_result.fetchone()
            escalation_count = escalation_row.escalation_count or 0
            escalation_rate = (escalation_count / row.total_alerts * 100) if row.total_alerts > 0 else 0.0
            
            false_positive_result = await session.execute("""
                SELECT COUNT(*) as false_positive_count
                FROM alerts
                WHERE status = 'resolved' 
                AND created_at BETWEEN :start_date AND :end_date
                AND metadata->>'false_positive' = 'true'
            """, {"start_date": start_date, "end_date": end_date})
            
            false_positive_row = false_positive_result.fetchone()
            false_positive_count = false_positive_row.false_positive_count or 0
            false_positive_rate = (false_positive_count / row.resolved_alerts * 100) if row.resolved_alerts > 0 else 0.0
            
            alert_volume_trend = await self._calculate_volume_trend(start_date, end_date)
            resolution_trend = await self._calculate_resolution_trend(start_date, end_date)
            
            metrics = AlertMetrics(
                total_alerts=row.total_alerts,
                active_alerts=row.active_alerts,
                resolved_alerts=row.resolved_alerts,
                critical_alerts=row.critical_alerts,
                warning_alerts=row.warning_alerts,
                info_alerts=row.info_alerts,
                average_resolution_time_minutes=avg_resolution_time,
                escalation_rate=escalation_rate,
                false_positive_rate=false_positive_rate,
                alert_volume_trend=alert_volume_trend,
                resolution_trend=resolution_trend
            )
            
            if use_cache:
                self.cached_metrics[cache_key] = (metrics, datetime.utcnow())
            
            return metrics

    async def _calculate_volume_trend(self, start_date: datetime, end_date: datetime) -> TrendDirection:
        if not self.database:
            return TrendDirection.STABLE
        
        period_days = (end_date - start_date).days
        if period_days < 7:
            return TrendDirection.STABLE
        
        mid_point = start_date + timedelta(days=period_days // 2)
        
        async with self.database.get_session() as session:
            first_half_result = await session.execute("""
                SELECT COUNT(*) as count
                FROM alerts
                WHERE created_at BETWEEN :start_date AND :mid_point
            """, {"start_date": start_date, "mid_point": mid_point})
            
            second_half_result = await session.execute("""
                SELECT COUNT(*) as count
                FROM alerts
                WHERE created_at BETWEEN :mid_point AND :end_date
            """, {"mid_point": mid_point, "end_date": end_date})
            
            first_half_count = first_half_result.fetchone().count
            second_half_count = second_half_result.fetchone().count
            
            if first_half_count == 0:
                return TrendDirection.INCREASING if second_half_count > 0 else TrendDirection.STABLE
            
            change_ratio = (second_half_count - first_half_count) / first_half_count
            
            if change_ratio > 0.2:
                return TrendDirection.INCREASING
            elif change_ratio < -0.2:
                return TrendDirection.DECREASING
            else:
                return TrendDirection.STABLE

    async def _calculate_resolution_trend(self, start_date: datetime, end_date: datetime) -> TrendDirection:
        if not self.database:
            return TrendDirection.STABLE
        
        period_days = (end_date - start_date).days
        if period_days < 7:
            return TrendDirection.STABLE
        
        mid_point = start_date + timedelta(days=period_days // 2)
        
        async with self.database.get_session() as session:
            first_half_result = await session.execute("""
                SELECT AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/60) as avg_time
                FROM alerts
                WHERE status = 'resolved' 
                AND created_at BETWEEN :start_date AND :mid_point
                AND resolved_at IS NOT NULL
            """, {"start_date": start_date, "mid_point": mid_point})
            
            second_half_result = await session.execute("""
                SELECT AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/60) as avg_time
                FROM alerts
                WHERE status = 'resolved' 
                AND created_at BETWEEN :mid_point AND :end_date
                AND resolved_at IS NOT NULL
            """, {"mid_point": mid_point, "end_date": end_date})
            
            first_half_time = first_half_result.fetchone().avg_time or 0
            second_half_time = second_half_result.fetchone().avg_time or 0
            
            if first_half_time == 0:
                return TrendDirection.STABLE
            
            change_ratio = (second_half_time - first_half_time) / first_half_time
            
            if change_ratio > 0.2:
                return TrendDirection.INCREASING
            elif change_ratio < -0.2:
                return TrendDirection.DECREASING
            else:
                return TrendDirection.STABLE

    async def get_alert_trends(
        self,
        period: AnalyticsPeriod = AnalyticsPeriod.DAY,
        days: int = 30,
        use_cache: bool = True
    ) -> List[AlertTrend]:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        cache_key = f"trends_{period.value}_{days}"
        
        if use_cache and cache_key in self.cached_trends:
            trends, cached_at = self.cached_trends[cache_key]
            if datetime.utcnow() - cached_at < timedelta(minutes=self.cache_duration_minutes):
                return trends
        
        if not self.database:
            return []
        
        trends = []
        
        if period == AnalyticsPeriod.HOUR:
            interval = "1 hour"
            format_str = "YYYY-MM-DD HH24:00"
        elif period == AnalyticsPeriod.DAY:
            interval = "1 day"
            format_str = "YYYY-MM-DD"
        elif period == AnalyticsPeriod.WEEK:
            interval = "1 week"
            format_str = "YYYY-'W'WW"
        elif period == AnalyticsPeriod.MONTH:
            interval = "1 month"
            format_str = "YYYY-MM"
        else:
            interval = "1 day"
            format_str = "YYYY-MM-DD"
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT 
                    TO_CHAR(created_at, '{format_str}') as period,
                    COUNT(*) as alert_count,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolution_count
                FROM alerts
                WHERE created_at BETWEEN :start_date AND :end_date
                GROUP BY TO_CHAR(created_at, '{format_str}')
                ORDER BY period
            """, {"start_date": start_date, "end_date": end_date})
            
            escalation_result = await session.execute(f"""
                SELECT 
                    TO_CHAR(triggered_at, '{format_str}') as period,
                    COUNT(*) as escalation_count
                FROM escalation_events
                WHERE triggered_at BETWEEN :start_date AND :end_date
                GROUP BY TO_CHAR(triggered_at, '{format_str}')
                ORDER BY period
            """, {"start_date": start_date, "end_date": end_date})
            
            resolution_time_result = await session.execute(f"""
                SELECT 
                    TO_CHAR(created_at, '{format_str}') as period,
                    AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/60) as avg_resolution_time
                FROM alerts
                WHERE status = 'resolved' 
                AND created_at BETWEEN :start_date AND :end_date
                AND resolved_at IS NOT NULL
                GROUP BY TO_CHAR(created_at, '{format_str}')
                ORDER BY period
            """, {"start_date": start_date, "end_date": end_date})
            
            alert_data = {row.period: row for row in result}
            escalation_data = {row.period: row.escalation_count for row in escalation_result}
            resolution_time_data = {row.period: row.avg_resolution_time for row in resolution_time_result}
            
            for period_str in sorted(alert_data.keys()):
                alert_row = alert_data[period_str]
                escalation_count = escalation_data.get(period_str, 0)
                avg_resolution_time = resolution_time_data.get(period_str, 0.0) or 0.0
                
                trend_direction = await self._calculate_period_trend_direction(
                    period_str, alert_row.alert_count, start_date, end_date
                )
                
                trend = AlertTrend(
                    period=period_str,
                    alert_count=alert_row.alert_count,
                    resolution_count=alert_row.resolution_count,
                    escalation_count=escalation_count,
                    average_resolution_time=avg_resolution_time,
                    trend_direction=trend_direction
                )
                trends.append(trend)
        
        if use_cache:
            self.cached_trends[cache_key] = (trends, datetime.utcnow())
        
        return trends

    async def _calculate_period_trend_direction(
        self, 
        period_str: str, 
        current_count: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> TrendDirection:
        if not self.database:
            return TrendDirection.STABLE
        
        try:
            period_date = datetime.strptime(period_str, "%Y-%m-%d")
            previous_period = period_date - timedelta(days=1)
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT COUNT(*) as count
                    FROM alerts
                    WHERE DATE(created_at) = :previous_period
                """, {"previous_period": previous_period.date()})
                
                previous_count = result.fetchone().count
                
                if previous_count == 0:
                    return TrendDirection.INCREASING if current_count > 0 else TrendDirection.STABLE
                
                change_ratio = (current_count - previous_count) / previous_count
                
                if change_ratio > 0.2:
                    return TrendDirection.INCREASING
                elif change_ratio < -0.2:
                    return TrendDirection.DECREASING
                else:
                    return TrendDirection.STABLE
                    
        except Exception as e:
            self.logger.error(f"Failed to calculate trend direction: {str(e)}")
            return TrendDirection.STABLE

    async def _detect_alert_patterns(self):
        if not self.database:
            return
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT 
                        source,
                        severity,
                        EXTRACT(HOUR FROM created_at) as hour_of_day,
                        EXTRACT(DOW FROM created_at) as day_of_week,
                        COUNT(*) as frequency
                    FROM alerts
                    WHERE created_at BETWEEN :start_date AND :end_date
                    GROUP BY source, severity, EXTRACT(HOUR FROM created_at), EXTRACT(DOW FROM created_at)
                    HAVING COUNT(*) >= 5
                    ORDER BY frequency DESC
                """, {"start_date": start_date, "end_date": end_date})
                
                patterns = {}
                for row in result:
                    pattern_key = f"{row.source}_{row.severity}_{row.hour_of_day}_{row.day_of_week}"
                    
                    if pattern_key not in patterns:
                        patterns[pattern_key] = {
                            "source": row.source,
                            "severity": row.severity,
                            "hour_of_day": int(row.hour_of_day),
                            "day_of_week": int(row.day_of_week),
                            "frequency": 0,
                            "alert_ids": []
                        }
                    
                    patterns[pattern_key]["frequency"] += row.frequency
                
                for pattern_key, pattern_data in patterns.items():
                    if pattern_data["frequency"] >= 10:
                        await self._save_alert_pattern(pattern_data)
                        
        except Exception as e:
            self.logger.error(f"Failed to detect alert patterns: {str(e)}")

    async def _save_alert_pattern(self, pattern_data: Dict[str, Any]):
        if not self.database:
            return
        
        try:
            pattern_id = f"pattern_{hash(str(pattern_data)) % 100000}"
            
            recommendations = []
            if pattern_data["frequency"] > 50:
                recommendations.append("High frequency pattern detected - consider automated resolution")
            if pattern_data["severity"] == "critical":
                recommendations.append("Critical severity pattern - implement immediate alerting")
            if pattern_data["hour_of_day"] in [2, 3, 4]:
                recommendations.append("Night-time pattern - consider on-call rotation")
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO alert_patterns (
                        pattern_id, name, description, frequency, severity_distribution,
                        source_distribution, time_patterns, confidence_score, recommendations
                    ) VALUES (
                        :pattern_id, :name, :description, :frequency, :severity_distribution,
                        :source_distribution, :time_patterns, :confidence_score, :recommendations
                    )
                    ON CONFLICT (pattern_id) DO UPDATE SET
                        frequency = EXCLUDED.frequency,
                        confidence_score = EXCLUDED.confidence_score,
                        updated_at = CURRENT_TIMESTAMP
                """, {
                    "pattern_id": pattern_id,
                    "name": f"Pattern: {pattern_data['source']} {pattern_data['severity']}",
                    "description": f"Recurring {pattern_data['severity']} alerts from {pattern_data['source']}",
                    "frequency": pattern_data["frequency"],
                    "severity_distribution": {pattern_data["severity"]: pattern_data["frequency"]},
                    "source_distribution": {pattern_data["source"]: pattern_data["frequency"]},
                    "time_patterns": {
                        "hour_of_day": pattern_data["hour_of_day"],
                        "day_of_week": pattern_data["day_of_week"]
                    },
                    "confidence_score": min(pattern_data["frequency"] / 100.0, 1.0),
                    "recommendations": recommendations
                })
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save alert pattern: {str(e)}")

    async def _analyze_alert_correlations(self):
        if not self.database:
            return
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(hours=24)
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT 
                        a1.alert_id as alert1,
                        a2.alert_id as alert2,
                        a1.source as source1,
                        a2.source as source2,
                        a1.severity as severity1,
                        a2.severity as severity2,
                        ABS(EXTRACT(EPOCH FROM (a1.created_at - a2.created_at))) as time_diff_seconds
                    FROM alerts a1
                    JOIN alerts a2 ON a1.alert_id != a2.alert_id
                    WHERE a1.created_at BETWEEN :start_date AND :end_date
                    AND a2.created_at BETWEEN :start_date AND :end_date
                    AND ABS(EXTRACT(EPOCH FROM (a1.created_at - a2.created_at))) <= 300
                    AND a1.source != a2.source
                """, {"start_date": start_date, "end_date": end_date})
                
                correlations = {}
                for row in result:
                    correlation_key = f"{row.source1}_{row.source2}"
                    
                    if correlation_key not in correlations:
                        correlations[correlation_key] = {
                            "alert_pairs": [],
                            "count": 0,
                            "avg_time_diff": 0
                        }
                    
                    correlations[correlation_key]["alert_pairs"].append([row.alert1, row.alert2])
                    correlations[correlation_key]["count"] += 1
                    correlations[correlation_key]["avg_time_diff"] += row.time_diff_seconds
                
                for correlation_key, correlation_data in correlations.items():
                    if correlation_data["count"] >= 3:
                        correlation_data["avg_time_diff"] /= correlation_data["count"]
                        await self._save_alert_correlation(correlation_key, correlation_data)
                        
        except Exception as e:
            self.logger.error(f"Failed to analyze alert correlations: {str(e)}")

    async def _save_alert_correlation(self, correlation_key: str, correlation_data: Dict[str, Any]):
        if not self.database:
            return
        
        try:
            correlation_id = f"correlation_{hash(correlation_key) % 100000}"
            sources = correlation_key.split("_")
            
            confidence_score = min(correlation_data["count"] / 10.0, 1.0)
            
            suggested_action = "Monitor for cascading failures"
            if correlation_data["avg_time_diff"] < 60:
                suggested_action = "Investigate potential system-wide issue"
            elif confidence_score > 0.7:
                suggested_action = "Implement automated correlation handling"
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO alert_correlations (
                        correlation_id, alert_ids, correlation_type, confidence_score,
                        pattern_description, suggested_action
                    ) VALUES (
                        :correlation_id, :alert_ids, :correlation_type, :confidence_score,
                        :pattern_description, :suggested_action
                    )
                    ON CONFLICT (correlation_id) DO UPDATE SET
                        confidence_score = EXCLUDED.confidence_score,
                        suggested_action = EXCLUDED.suggested_action
                """, {
                    "correlation_id": correlation_id,
                    "alert_ids": [pair for pair in correlation_data["alert_pairs"][:10]],
                    "correlation_type": "temporal",
                    "confidence_score": confidence_score,
                    "pattern_description": f"Alerts from {sources[0]} and {sources[1]} occur within {correlation_data['avg_time_diff']:.0f} seconds",
                    "suggested_action": suggested_action
                })
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save alert correlation: {str(e)}")

    async def get_alert_patterns(
        self,
        min_confidence: float = 0.5,
        limit: int = 50
    ) -> List[AlertPattern]:
        if not self.database:
            return []
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT pattern_id, name, description, frequency, severity_distribution,
                       source_distribution, time_patterns, confidence_score, recommendations
                FROM alert_patterns
                WHERE confidence_score >= :min_confidence
                ORDER BY confidence_score DESC, frequency DESC
                LIMIT :limit
            """, {"min_confidence": min_confidence, "limit": limit})
            
            patterns = []
            for row in result:
                pattern = AlertPattern(
                    pattern_id=row.pattern_id,
                    name=row.name,
                    description=row.description,
                    frequency=row.frequency,
                    severity_distribution=row.severity_distribution or {},
                    source_distribution=row.source_distribution or {},
                    time_patterns=row.time_patterns or {},
                    confidence_score=row.confidence_score,
                    recommendations=row.recommendations or []
                )
                patterns.append(pattern)
            
            return patterns

    async def get_alert_correlations(
        self,
        min_confidence: float = 0.5,
        limit: int = 50
    ) -> List[AlertCorrelation]:
        if not self.database:
            return []
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT correlation_id, alert_ids, correlation_type, confidence_score,
                       pattern_description, suggested_action
                FROM alert_correlations
                WHERE confidence_score >= :min_confidence
                ORDER BY confidence_score DESC
                LIMIT :limit
            """, {"min_confidence": min_confidence, "limit": limit})
            
            correlations = []
            for row in result:
                correlation = AlertCorrelation(
                    correlation_id=row.correlation_id,
                    alert_ids=row.alert_ids or [],
                    correlation_type=row.correlation_type,
                    confidence_score=row.confidence_score,
                    pattern_description=row.pattern_description,
                    suggested_action=row.suggested_action
                )
                correlations.append(correlation)
            
            return correlations

    async def get_alert_insights(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        metrics = await self.get_alert_metrics(start_date, end_date)
        trends = await self.get_alert_trends(AnalyticsPeriod.DAY, 30)
        patterns = await self.get_alert_patterns(min_confidence=0.6, limit=10)
        correlations = await self.get_alert_correlations(min_confidence=0.6, limit=10)
        
        insights = {
            "summary": {
                "total_alerts": metrics.total_alerts,
                "resolution_rate": (metrics.resolved_alerts / metrics.total_alerts * 100) if metrics.total_alerts > 0 else 0,
                "escalation_rate": metrics.escalation_rate,
                "false_positive_rate": metrics.false_positive_rate,
                "avg_resolution_time_hours": metrics.average_resolution_time_minutes / 60
            },
            "trends": {
                "volume_trend": metrics.alert_volume_trend.value,
                "resolution_trend": metrics.resolution_trend.value,
                "recent_trends": trends[-7:] if trends else []
            },
            "patterns": {
                "count": len(patterns),
                "top_patterns": patterns[:5] if patterns else []
            },
            "correlations": {
                "count": len(correlations),
                "top_correlations": correlations[:5] if correlations else []
            },
            "recommendations": await self._generate_recommendations(metrics, patterns, correlations)
        }
        
        return insights

    async def _generate_recommendations(
        self,
        metrics: AlertMetrics,
        patterns: List[AlertPattern],
        correlations: List[AlertCorrelation]
    ) -> List[str]:
        recommendations = []
        
        if metrics.escalation_rate > 20:
            recommendations.append("High escalation rate detected - review alert thresholds and response procedures")
        
        if metrics.false_positive_rate > 15:
            recommendations.append("High false positive rate - refine alert conditions and filters")
        
        if metrics.average_resolution_time_minutes > 120:
            recommendations.append("Long resolution times - consider automated remediation for common issues")
        
        if metrics.alert_volume_trend == TrendDirection.INCREASING:
            recommendations.append("Increasing alert volume - investigate root causes and implement preventive measures")
        
        if len(patterns) > 5:
            recommendations.append("Multiple alert patterns detected - implement pattern-based automation")
        
        if len(correlations) > 3:
            recommendations.append("Alert correlations found - set up correlation-based alerting")
        
        if metrics.critical_alerts > metrics.total_alerts * 0.3:
            recommendations.append("High critical alert ratio - review severity classifications")
        
        return recommendations

    async def _cleanup_expired_cache(self):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    DELETE FROM alert_analytics_cache 
                    WHERE expires_at < CURRENT_TIMESTAMP
                """)
                await session.commit()
                
            expired_keys = []
            for cache_key, (_, cached_at) in self.cached_metrics.items():
                if datetime.utcnow() - cached_at > timedelta(minutes=self.cache_duration_minutes):
                    expired_keys.append(cache_key)
            
            for key in expired_keys:
                del self.cached_metrics[key]
            
            expired_trend_keys = []
            for cache_key, (_, cached_at) in self.cached_trends.items():
                if datetime.utcnow() - cached_at > timedelta(minutes=self.cache_duration_minutes):
                    expired_trend_keys.append(cache_key)
            
            for key in expired_trend_keys:
                del self.cached_trends[key]
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired cache: {str(e)}")

    async def export_analytics_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        metrics = await self.get_alert_metrics(start_date, end_date, use_cache=False)
        trends = await self.get_alert_trends(AnalyticsPeriod.DAY, 30, use_cache=False)
        patterns = await self.get_alert_patterns(min_confidence=0.3, limit=100)
        correlations = await self.get_alert_correlations(min_confidence=0.3, limit=100)
        insights = await self.get_alert_insights(start_date, end_date)
        
        export_data = {
            "export_info": {
                "generated_at": datetime.utcnow().isoformat(),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "format": format
            },
            "metrics": {
                "total_alerts": metrics.total_alerts,
                "active_alerts": metrics.active_alerts,
                "resolved_alerts": metrics.resolved_alerts,
                "critical_alerts": metrics.critical_alerts,
                "warning_alerts": metrics.warning_alerts,
                "info_alerts": metrics.info_alerts,
                "average_resolution_time_minutes": metrics.average_resolution_time_minutes,
                "escalation_rate": metrics.escalation_rate,
                "false_positive_rate": metrics.false_positive_rate,
                "alert_volume_trend": metrics.alert_volume_trend.value,
                "resolution_trend": metrics.resolution_trend.value
            },
            "trends": [
                {
                    "period": trend.period,
                    "alert_count": trend.alert_count,
                    "resolution_count": trend.resolution_count,
                    "escalation_count": trend.escalation_count,
                    "average_resolution_time": trend.average_resolution_time,
                    "trend_direction": trend.trend_direction.value
                }
                for trend in trends
            ],
            "patterns": [
                {
                    "pattern_id": pattern.pattern_id,
                    "name": pattern.name,
                    "description": pattern.description,
                    "frequency": pattern.frequency,
                    "severity_distribution": pattern.severity_distribution,
                    "source_distribution": pattern.source_distribution,
                    "time_patterns": pattern.time_patterns,
                    "confidence_score": pattern.confidence_score,
                    "recommendations": pattern.recommendations
                }
                for pattern in patterns
            ],
            "correlations": [
                {
                    "correlation_id": correlation.correlation_id,
                    "alert_ids": correlation.alert_ids,
                    "correlation_type": correlation.correlation_type,
                    "confidence_score": correlation.confidence_score,
                    "pattern_description": correlation.pattern_description,
                    "suggested_action": correlation.suggested_action
                }
                for correlation in correlations
            ],
            "insights": insights
        }
        
        return export_data

_alert_analytics: Optional[AlertAnalytics] = None

async def get_alert_analytics() -> AlertAnalytics:
    global _alert_analytics
    if _alert_analytics is None:
        _alert_analytics = AlertAnalytics()
        await _alert_analytics.initialize()
    return _alert_analytics

async def init_alert_analytics() -> AlertAnalytics:
    return await get_alert_analytics()
