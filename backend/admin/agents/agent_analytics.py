import asyncio
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from core.database import get_database
from core.cache import get_redis
from core.logs import get_logger
from core.config import get_settings


class AnalyticsTimeframe(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class MetricType(Enum):
    PERFORMANCE = "performance"
    EFFICIENCY = "efficiency"
    RELIABILITY = "reliability"
    UTILIZATION = "utilization"
    COST = "cost"
    QUALITY = "quality"


@dataclass
class AgentMetrics:
    agent_id: str
    agent_name: str
    timeframe: AnalyticsTimeframe
    start_date: datetime
    end_date: datetime
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    average_execution_time: float
    average_response_time: float
    cpu_usage_avg: float
    memory_usage_avg: float
    availability_percentage: float
    efficiency_score: float
    cost_per_task: float
    quality_score: float


@dataclass
class AgentTrend:
    agent_id: str
    agent_name: str
    metric: str
    trend_direction: str
    trend_strength: float
    change_percentage: float
    period_start: datetime
    period_end: datetime
    data_points: List[Tuple[datetime, float]]


@dataclass
class AgentComparison:
    metric: str
    agents: List[str]
    values: List[float]
    rankings: List[int]
    best_performer: str
    worst_performer: str
    average_value: float
    standard_deviation: float


@dataclass
class AgentInsight:
    agent_id: str
    agent_name: str
    insight_type: str
    insight_message: str
    confidence: float
    recommendation: str
    impact_score: float
    timestamp: datetime


class AgentAnalytics:
    def __init__(self):
        self.config = get_settings()
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()
        self.cache_ttl = 3600  # 1 hour cache

    async def initialize(self):
        """Initialize the agent analytics system"""
        try:
            self.logger.info("AgentAnalytics initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize AgentAnalytics: {e}")
            raise

    async def get_agent_metrics(self, agent_id: str, timeframe: AnalyticsTimeframe, 
                               start_date: Optional[datetime] = None) -> AgentMetrics:
        """Get comprehensive metrics for a specific agent over a time period"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            if start_date is None:
                start_date = self._calculate_start_date(end_date, timeframe)
            
            # Check cache first
            cache_key = f"agent_metrics:{agent_id}:{timeframe.value}:{start_date.date()}"
            cached_metrics = await self.redis.get(cache_key)
            if cached_metrics:
                return AgentMetrics(**cached_metrics)
            
            # Get metrics from database
            metrics = await self._calculate_agent_metrics(agent_id, start_date, end_date)
            
            # Cache the results
            await self.redis.set(cache_key, metrics.__dict__, expire=self.cache_ttl)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting agent metrics: {e}")
            raise

    def _calculate_start_date(self, end_date: datetime, timeframe: AnalyticsTimeframe) -> datetime:
        """Calculate start date based on timeframe"""
        if timeframe == AnalyticsTimeframe.HOUR:
            return end_date - timedelta(hours=1)
        elif timeframe == AnalyticsTimeframe.DAY:
            return end_date - timedelta(days=1)
        elif timeframe == AnalyticsTimeframe.WEEK:
            return end_date - timedelta(weeks=1)
        elif timeframe == AnalyticsTimeframe.MONTH:
            return end_date - timedelta(days=30)
        elif timeframe == AnalyticsTimeframe.QUARTER:
            return end_date - timedelta(days=90)
        elif timeframe == AnalyticsTimeframe.YEAR:
            return end_date - timedelta(days=365)
        else:
            return end_date - timedelta(days=1)

    async def _calculate_agent_metrics(self, agent_id: str, start_date: datetime, 
                                     end_date: datetime) -> AgentMetrics:
        """Calculate comprehensive metrics for an agent"""
        try:
            async with self.db.get_session() as session:
                # Get task metrics
                task_result = await session.execute("""
                    SELECT 
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
                        AVG(execution_time) as avg_execution_time
                    FROM agent_tasks
                    WHERE agent_id = :agent_id 
                    AND started_at >= :start_date 
                    AND started_at <= :end_date
                """, {
                    "agent_id": agent_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                task_row = task_result.fetchone()
                total_tasks = task_row.total_tasks or 0
                completed_tasks = task_row.completed_tasks or 0
                failed_tasks = task_row.failed_tasks or 0
                avg_execution_time = task_row.avg_execution_time or 0.0
                
                success_rate = (completed_tasks / max(total_tasks, 1)) * 100
                
                # Get performance metrics
                perf_result = await session.execute("""
                    SELECT 
                        AVG(cpu_usage) as avg_cpu,
                        AVG(memory_usage) as avg_memory,
                        AVG(response_time) as avg_response_time,
                        AVG(availability) as avg_availability,
                        AVG(efficiency_score) as avg_efficiency
                    FROM agent_performance
                    WHERE agent_id = :agent_id 
                    AND timestamp >= :start_date 
                    AND timestamp <= :end_date
                """, {
                    "agent_id": agent_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                perf_row = perf_result.fetchone()
                avg_cpu = perf_row.avg_cpu or 0.0
                avg_memory = perf_row.avg_memory or 0.0
                avg_response_time = perf_row.avg_response_time or 0.0
                avg_availability = perf_row.avg_availability or 0.0
                avg_efficiency = perf_row.avg_efficiency or 0.0
                
                # Get agent name
                name_result = await session.execute("""
                    SELECT agent_name FROM agent_tasks 
                    WHERE agent_id = :agent_id LIMIT 1
                """, {"agent_id": agent_id})
                
                name_row = name_result.fetchone()
                agent_name = name_row.agent_name if name_row else "Unknown"
                
                # Calculate derived metrics
                cost_per_task = self._calculate_cost_per_task(agent_id, total_tasks, avg_execution_time)
                quality_score = self._calculate_quality_score(success_rate, avg_response_time, avg_execution_time)
                
                metrics = AgentMetrics(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    timeframe=AnalyticsTimeframe.DAY,  # Default, will be updated
                    start_date=start_date,
                    end_date=end_date,
                    total_tasks=total_tasks,
                    completed_tasks=completed_tasks,
                    failed_tasks=failed_tasks,
                    success_rate=success_rate,
                    average_execution_time=avg_execution_time,
                    average_response_time=avg_response_time,
                    cpu_usage_avg=avg_cpu,
                    memory_usage_avg=avg_memory,
                    availability_percentage=avg_availability,
                    efficiency_score=avg_efficiency,
                    cost_per_task=cost_per_task,
                    quality_score=quality_score
                )
                
                return metrics
                
        except Exception as e:
            self.logger.error(f"Error calculating agent metrics: {e}")
            raise

    def _calculate_cost_per_task(self, agent_id: str, total_tasks: int, avg_execution_time: float) -> float:
        """Calculate cost per task based on agent type and execution time"""
        try:
            # Base costs per agent type (would come from configuration)
            base_costs = {
                "aria": 0.05,      # Social media management
                "clara": 0.03,     # Customer support
                "eric": 0.08,      # Sales
                "joe": 0.04,       # Research
                "jackie": 0.06,    # Marketing
                "shakes": 0.07,    # Content creation
                "purity": 0.10     # Business and finance
            }
            
            # Extract agent type from agent_id
            agent_type = agent_id.lower().split('_')[0] if '_' in agent_id else agent_id.lower()
            base_cost = base_costs.get(agent_type, 0.05)
            
            # Time-based cost adjustment
            time_factor = max(0.5, min(2.0, avg_execution_time / 60.0))  # Normalize to 1 minute
            
            return base_cost * time_factor
            
        except Exception as e:
            self.logger.warning(f"Could not calculate cost per task: {e}")
            return 0.05

    def _calculate_quality_score(self, success_rate: float, avg_response_time: float, 
                                avg_execution_time: float) -> float:
        """Calculate quality score based on multiple factors"""
        try:
            # Success rate component (40% weight)
            success_score = success_rate
            
            # Response time component (30% weight)
            response_score = max(0, 100 - (avg_response_time / 100))
            
            # Execution time component (30% weight)
            execution_score = max(0, 100 - (avg_execution_time / 60))
            
            # Weighted average
            quality_score = (success_score * 0.4 + response_score * 0.3 + execution_score * 0.3)
            
            return min(100.0, max(0.0, quality_score))
            
        except Exception as e:
            self.logger.warning(f"Could not calculate quality score: {e}")
            return 0.0

    async def get_agent_trends(self, agent_id: str, metric: str, 
                               timeframe: AnalyticsTimeframe) -> AgentTrend:
        """Get trend analysis for a specific agent metric"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, timeframe)
            
            # Get historical data points
            data_points = await self._get_metric_data_points(agent_id, metric, start_date, end_date)
            
            if not data_points:
                return None
            
            # Calculate trend
            trend_direction, trend_strength, change_percentage = self._calculate_trend(data_points)
            
            # Get agent name
            agent_name = await self._get_agent_name(agent_id)
            
            trend = AgentTrend(
                agent_id=agent_id,
                agent_name=agent_name,
                metric=metric,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                change_percentage=change_percentage,
                period_start=start_date,
                period_end=end_date,
                data_points=data_points
            )
            
            return trend
            
        except Exception as e:
            self.logger.error(f"Error getting agent trends: {e}")
            return None

    async def _get_metric_data_points(self, agent_id: str, metric: str, 
                                    start_date: datetime, end_date: datetime) -> List[Tuple[datetime, float]]:
        """Get data points for a specific metric over time"""
        try:
            async with self.db.get_session() as session:
                if metric in ["cpu_usage", "memory_usage", "response_time", "efficiency_score"]:
                    result = await session.execute("""
                        SELECT timestamp, {} as value
                        FROM agent_performance
                        WHERE agent_id = :agent_id 
                        AND timestamp >= :start_date 
                        AND timestamp <= :end_date
                        ORDER BY timestamp ASC
                    """.format(metric), {
                        "agent_id": agent_id,
                        "start_date": start_date,
                        "end_date": end_date
                    })
                else:
                    # For task-based metrics
                    result = await session.execute("""
                        SELECT started_at as timestamp, 
                               CASE 
                                   WHEN :metric = 'success_rate' THEN 
                                       CASE WHEN status = 'completed' THEN 100.0 ELSE 0.0 END
                                   WHEN :metric = 'execution_time' THEN execution_time
                                   ELSE 0.0
                               END as value
                        FROM agent_tasks
                        WHERE agent_id = :agent_id 
                        AND started_at >= :start_date 
                        AND started_at <= :end_date
                        ORDER BY started_at ASC
                    """, {
                        "agent_id": agent_id,
                        "metric": metric,
                        "start_date": start_date,
                        "end_date": end_date
                    })
                
                rows = result.fetchall()
                return [(row.timestamp, row.value) for row in rows if row.value is not None]
                
        except Exception as e:
            self.logger.error(f"Error getting metric data points: {e}")
            return []

    def _calculate_trend(self, data_points: List[Tuple[datetime, float]]) -> Tuple[str, float, float]:
        """Calculate trend direction, strength, and change percentage"""
        try:
            if len(data_points) < 2:
                return "stable", 0.0, 0.0
            
            values = [point[1] for point in data_points]
            
            # Calculate linear regression slope
            n = len(values)
            x_values = list(range(n))
            
            # Calculate means
            x_mean = statistics.mean(x_values)
            y_mean = statistics.mean(values)
            
            # Calculate slope
            numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
            denominator = sum((x - x_mean) ** 2 for x in x_values)
            
            if denominator == 0:
                slope = 0
            else:
                slope = numerator / denominator
            
            # Determine trend direction
            if slope > 0.01:
                trend_direction = "increasing"
            elif slope < -0.01:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
            
            # Calculate trend strength (R-squared)
            if len(values) > 2:
                y_pred = [y_mean + slope * (x - x_mean) for x in x_values]
                ss_res = sum((y - y_pred) ** 2 for y, y_pred in zip(values, y_pred))
                ss_tot = sum((y - y_mean) ** 2 for y in values)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                trend_strength = r_squared
            else:
                trend_strength = 0.0
            
            # Calculate change percentage
            if values[0] != 0:
                change_percentage = ((values[-1] - values[0]) / values[0]) * 100
            else:
                change_percentage = 0.0
            
            return trend_direction, trend_strength, change_percentage
            
        except Exception as e:
            self.logger.warning(f"Could not calculate trend: {e}")
            return "stable", 0.0, 0.0

    async def _get_agent_name(self, agent_id: str) -> str:
        """Get agent name from agent_id"""
        try:
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT agent_name FROM agent_tasks 
                    WHERE agent_id = :agent_id LIMIT 1
                """, {"agent_id": agent_id})
                
                row = result.fetchone()
                return row.agent_name if row else "Unknown"
                
        except Exception as e:
            self.logger.warning(f"Could not get agent name: {e}")
            return "Unknown"

    async def compare_agents(self, metric: str, agent_ids: List[str], 
                           timeframe: AnalyticsTimeframe) -> AgentComparison:
        """Compare multiple agents on a specific metric"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, timeframe)
            
            agent_values = []
            agent_names = []
            
            for agent_id in agent_ids:
                metrics = await self.get_agent_metrics(agent_id, timeframe, start_date)
                agent_names.append(metrics.agent_name)
                
                # Extract the specific metric value
                if metric == "success_rate":
                    value = metrics.success_rate
                elif metric == "efficiency_score":
                    value = metrics.efficiency_score
                elif metric == "quality_score":
                    value = metrics.quality_score
                elif metric == "cost_per_task":
                    value = metrics.cost_per_task
                elif metric == "average_execution_time":
                    value = metrics.average_execution_time
                elif metric == "average_response_time":
                    value = metrics.average_response_time
                else:
                    value = 0.0
                
                agent_values.append(value)
            
            # Calculate rankings
            sorted_pairs = sorted(zip(agent_names, agent_values), key=lambda x: x[1], reverse=True)
            rankings = [sorted_pairs.index((name, value)) + 1 for name, value in zip(agent_names, agent_values)]
            
            # Find best and worst performers
            best_performer = sorted_pairs[0][0] if sorted_pairs else "None"
            worst_performer = sorted_pairs[-1][0] if sorted_pairs else "None"
            
            # Calculate statistics
            average_value = statistics.mean(agent_values) if agent_values else 0.0
            standard_deviation = statistics.stdev(agent_values) if len(agent_values) > 1 else 0.0
            
            comparison = AgentComparison(
                metric=metric,
                agents=agent_names,
                values=agent_values,
                rankings=rankings,
                best_performer=best_performer,
                worst_performer=worst_performer,
                average_value=average_value,
                standard_deviation=standard_deviation
            )
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing agents: {e}")
            return None

    async def generate_agent_insights(self, agent_id: str) -> List[AgentInsight]:
        """Generate insights and recommendations for an agent"""
        try:
            insights = []
            
            # Get current metrics
            metrics = await self.get_agent_metrics(agent_id, AnalyticsTimeframe.DAY)
            
            # Analyze success rate
            if metrics.success_rate < 80:
                insights.append(AgentInsight(
                    agent_id=agent_id,
                    agent_name=metrics.agent_name,
                    insight_type="performance_issue",
                    insight_message=f"Success rate is {metrics.success_rate:.1f}%, below the 80% threshold",
                    confidence=0.85,
                    recommendation="Review recent failed tasks and implement error handling improvements",
                    impact_score=0.7,
                    timestamp=datetime.utcnow()
                ))
            
            # Analyze response time
            if metrics.average_response_time > 2000:
                insights.append(AgentInsight(
                    agent_id=agent_id,
                    agent_name=metrics.agent_name,
                    insight_type="performance_issue",
                    insight_message=f"Average response time is {metrics.average_response_time:.1f}ms, above the 2000ms threshold",
                    confidence=0.80,
                    recommendation="Optimize agent processing logic and consider resource scaling",
                    impact_score=0.6,
                    timestamp=datetime.utcnow()
                ))
            
            # Analyze efficiency
            if metrics.efficiency_score < 70:
                insights.append(AgentInsight(
                    agent_id=agent_id,
                    agent_name=metrics.agent_name,
                    insight_type="efficiency_issue",
                    insight_message=f"Efficiency score is {metrics.efficiency_score:.1f}, below the 70% threshold",
                    confidence=0.75,
                    recommendation="Review agent configuration and optimize resource usage",
                    impact_score=0.5,
                    timestamp=datetime.utcnow()
                ))
            
            # Analyze cost efficiency
            if metrics.cost_per_task > 0.10:
                insights.append(AgentInsight(
                    agent_id=agent_id,
                    agent_name=metrics.agent_name,
                    insight_type="cost_issue",
                    insight_message=f"Cost per task is ${metrics.cost_per_task:.3f}, above the $0.10 threshold",
                    confidence=0.70,
                    recommendation="Optimize task execution and reduce processing time",
                    impact_score=0.4,
                    timestamp=datetime.utcnow()
                ))
            
            # Get trend insights
            trends = await self._get_trend_insights(agent_id)
            insights.extend(trends)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating agent insights: {e}")
            return []

    async def _get_trend_insights(self, agent_id: str) -> List[AgentInsight]:
        """Get insights based on trend analysis"""
        try:
            insights = []
            
            # Analyze success rate trend
            success_trend = await self.get_agent_trends(agent_id, "success_rate", AnalyticsTimeframe.WEEK)
            if success_trend and success_trend.trend_direction == "decreasing" and success_trend.trend_strength > 0.5:
                insights.append(AgentInsight(
                    agent_id=agent_id,
                    agent_name=success_trend.agent_name,
                    insight_type="trend_warning",
                    insight_message=f"Success rate is decreasing by {abs(success_trend.change_percentage):.1f}% over the past week",
                    confidence=0.75,
                    recommendation="Investigate root causes and implement corrective measures",
                    impact_score=0.6,
                    timestamp=datetime.utcnow()
                ))
            
            # Analyze response time trend
            response_trend = await self.get_agent_trends(agent_id, "response_time", AnalyticsTimeframe.WEEK)
            if response_trend and response_trend.trend_direction == "increasing" and response_trend.trend_strength > 0.5:
                insights.append(AgentInsight(
                    agent_id=agent_id,
                    agent_name=response_trend.agent_name,
                    insight_type="trend_warning",
                    insight_message=f"Response time is increasing by {response_trend.change_percentage:.1f}% over the past week",
                    confidence=0.70,
                    recommendation="Monitor system resources and optimize processing logic",
                    impact_score=0.5,
                    timestamp=datetime.utcnow()
                ))
            
            return insights
            
        except Exception as e:
            self.logger.warning(f"Could not get trend insights: {e}")
            return []

    async def get_system_wide_analytics(self, timeframe: AnalyticsTimeframe) -> Dict[str, Any]:
        """Get system-wide analytics across all agents"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, timeframe)
            
            async with self.db.get_session() as session:
                # Get overall system metrics
                result = await session.execute("""
                    SELECT 
                        COUNT(DISTINCT agent_id) as total_agents,
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
                        AVG(execution_time) as avg_execution_time
                    FROM agent_tasks
                    WHERE started_at >= :start_date AND started_at <= :end_date
                """, {
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                row = result.fetchone()
                total_agents = row.total_agents or 0
                total_tasks = row.total_tasks or 0
                completed_tasks = row.completed_tasks or 0
                failed_tasks = row.failed_tasks or 0
                avg_execution_time = row.avg_execution_time or 0.0
                
                # Get performance metrics
                perf_result = await session.execute("""
                    SELECT 
                        AVG(cpu_usage) as avg_cpu,
                        AVG(memory_usage) as avg_memory,
                        AVG(response_time) as avg_response_time,
                        AVG(efficiency_score) as avg_efficiency
                    FROM agent_performance
                    WHERE timestamp >= :start_date AND timestamp <= :end_date
                """, {
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                perf_row = perf_result.fetchone()
                avg_cpu = perf_row.avg_cpu or 0.0
                avg_memory = perf_row.avg_memory or 0.0
                avg_response_time = perf_row.avg_response_time or 0.0
                avg_efficiency = perf_row.avg_efficiency or 0.0
                
                # Calculate derived metrics
                overall_success_rate = (completed_tasks / max(total_tasks, 1)) * 100
                system_health_score = self._calculate_system_health_score(
                    overall_success_rate, avg_cpu, avg_memory, avg_response_time
                )
                
                analytics = {
                    "timeframe": timeframe.value,
                    "period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "overview": {
                        "total_agents": total_agents,
                        "total_tasks": total_tasks,
                        "completed_tasks": completed_tasks,
                        "failed_tasks": failed_tasks,
                        "success_rate": overall_success_rate
                    },
                    "performance": {
                        "average_execution_time": avg_execution_time,
                        "average_response_time": avg_response_time,
                        "average_cpu_usage": avg_cpu,
                        "average_memory_usage": avg_memory,
                        "average_efficiency": avg_efficiency
                    },
                    "system_health": {
                        "overall_score": system_health_score,
                        "status": self._get_system_health_status(system_health_score)
                    }
                }
                
                return analytics
                
        except Exception as e:
            self.logger.error(f"Error getting system-wide analytics: {e}")
            return {}

    def _calculate_system_health_score(self, success_rate: float, avg_cpu: float, 
                                     avg_memory: float, avg_response_time: float) -> float:
        """Calculate overall system health score"""
        try:
            # Success rate component (40% weight)
            success_score = success_rate
            
            # Resource usage component (30% weight)
            resource_score = 100 - ((avg_cpu + avg_memory) / 2)
            
            # Response time component (30% weight)
            response_score = max(0, 100 - (avg_response_time / 100))
            
            # Weighted average
            health_score = (success_score * 0.4 + resource_score * 0.3 + response_score * 0.3)
            
            return min(100.0, max(0.0, health_score))
            
        except Exception as e:
            self.logger.warning(f"Could not calculate system health score: {e}")
            return 0.0

    def _get_system_health_status(self, health_score: float) -> str:
        """Get system health status based on score"""
        if health_score >= 90:
            return "excellent"
        elif health_score >= 80:
            return "good"
        elif health_score >= 70:
            return "fair"
        elif health_score >= 60:
            return "poor"
        else:
            return "critical"

    async def close(self):
        """Clean up resources"""
        self.logger.info("AgentAnalytics closed")


# Singleton instances
_agent_analytics = None


async def get_agent_analytics() -> AgentAnalytics:
    """Get the AgentAnalytics singleton instance"""
    global _agent_analytics
    if _agent_analytics is None:
        _agent_analytics = AgentAnalytics()
        await _agent_analytics.initialize()
    return _agent_analytics


async def init_agent_analytics() -> AgentAnalytics:
    """Initialize and return a new AgentAnalytics instance"""
    analytics = AgentAnalytics()
    await analytics.initialize()
    return analytics
