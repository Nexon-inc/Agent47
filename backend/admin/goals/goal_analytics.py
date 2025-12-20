import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from core.database import get_database, DatabaseManager
from core.cache import get_redis, RedisManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class AnalyticsTimeframe(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

class MetricType(Enum):
    COUNT = "count"
    PERCENTAGE = "percentage"
    RATE = "rate"
    DURATION = "duration"
    SCORE = "score"

@dataclass
class GoalPerformanceMetrics:
    goal_id: str
    timeframe: AnalyticsTimeframe
    start_date: datetime
    end_date: datetime
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    avg_completion_time: float
    agent_performance: Dict[str, Dict[str, Any]]
    trend_data: List[Dict[str, Any]]
    insights: List[str]

@dataclass
class AgentEffectivenessMetrics:
    agent_name: str
    timeframe: AnalyticsTimeframe
    total_tasks_assigned: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    avg_task_duration: float
    task_complexity_distribution: Dict[str, int]
    goal_contribution: Dict[str, float]
    performance_score: float

class GoalAnalytics(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.settings = get_settings()
        
        self.analytics_cache: Dict[str, Any] = {}
        self.logger = logger

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing GoalAnalytics...")
            
            self.database = get_database()
            self.redis = await get_redis()
            
            self.logger.info("GoalAnalytics initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GoalAnalytics: {str(e)}")
            return False

    async def get_goal_performance_metrics(self, goal_id: str, timeframe: AnalyticsTimeframe = AnalyticsTimeframe.WEEK) -> GoalPerformanceMetrics:
        try:
            # Check cache first
            cache_key = f"goal_performance:{goal_id}:{timeframe.value}"
            if self.redis:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    cached_metrics = json.loads(cached_data)
                    return GoalPerformanceMetrics(**cached_metrics)
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, timeframe)
            
            # Get goal data
            goal_data = await self._get_goal_data(goal_id)
            if not goal_data:
                raise ValueError(f"Goal {goal_id} not found")
            
            # Get task performance data
            task_metrics = await self._get_task_performance_metrics(goal_id, start_date, end_date)
            
            # Calculate agent performance
            agent_performance = await self._calculate_agent_performance(goal_id, start_date, end_date)
            
            # Generate trend data
            trend_data = await self._generate_trend_data(goal_id, start_date, end_date, timeframe)
            
            # Generate insights
            insights = await self._generate_goal_insights(goal_id, task_metrics, agent_performance)
            
            # Create metrics object
            metrics = GoalPerformanceMetrics(
                goal_id=goal_id,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                total_tasks=task_metrics["total_tasks"],
                completed_tasks=task_metrics["completed_tasks"],
                failed_tasks=task_metrics["failed_tasks"],
                success_rate=task_metrics["success_rate"],
                avg_completion_time=task_metrics["avg_completion_time"],
                agent_performance=agent_performance,
                trend_data=trend_data,
                insights=insights
            )
            
            # Cache results
            if self.redis:
                cache_data = {
                    "goal_id": metrics.goal_id,
                    "timeframe": metrics.timeframe.value,
                    "start_date": metrics.start_date.isoformat(),
                    "end_date": metrics.end_date.isoformat(),
                    "total_tasks": metrics.total_tasks,
                    "completed_tasks": metrics.completed_tasks,
                    "failed_tasks": metrics.failed_tasks,
                    "success_rate": metrics.success_rate,
                    "avg_completion_time": metrics.avg_completion_time,
                    "agent_performance": metrics.agent_performance,
                    "trend_data": metrics.trend_data,
                    "insights": metrics.insights
                }
                await self.redis.set(cache_key, json.dumps(cache_data), expire=1800)  # 30 minutes
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get goal performance metrics: {str(e)}")
            raise

    def _calculate_start_date(self, end_date: datetime, timeframe: AnalyticsTimeframe) -> datetime:
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
            return end_date - timedelta(days=7)

    async def _get_goal_data(self, goal_id: str) -> Optional[Dict[str, Any]]:
        if not self.database:
            return None
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT id, name, description, goal_type, status, priority, start_date, end_date,
                       metrics, assigned_agents, created_by, created_at, updated_at, tags, budget, actual_cost
                FROM goals WHERE id = %s
            """, (goal_id,))
            
            row = result.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "goal_type": row[3],
                    "status": row[4],
                    "priority": row[5],
                    "start_date": row[6],
                    "end_date": row[7],
                    "metrics": row[8],
                    "assigned_agents": row[9],
                    "created_by": row[10],
                    "created_at": row[11],
                    "updated_at": row[12],
                    "tags": row[13],
                    "budget": float(row[14]) if row[14] else 0.0,
                    "actual_cost": float(row[15]) if row[15] else 0.0
                }
        
        return None

    async def _get_task_performance_metrics(self, goal_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        if not self.database:
            return {"total_tasks": 0, "completed_tasks": 0, "failed_tasks": 0, "success_rate": 0.0, "avg_completion_time": 0.0}
        
        async with self.database.get_session() as session:
            # Get total tasks
            result = await session.execute("""
                SELECT COUNT(*) FROM agent_tasks 
                WHERE goal_id = %s AND assigned_at BETWEEN %s AND %s
            """, (goal_id, start_date, end_date))
            total_tasks = result.scalar()
            
            # Get completed tasks
            result = await session.execute("""
                SELECT COUNT(*) FROM agent_tasks 
                WHERE goal_id = %s AND status = 'completed' AND completed_at BETWEEN %s AND %s
            """, (goal_id, start_date, end_date))
            completed_tasks = result.scalar()
            
            # Get failed tasks
            result = await session.execute("""
                SELECT COUNT(*) FROM agent_tasks 
                WHERE goal_id = %s AND status = 'failed' AND completed_at BETWEEN %s AND %s
            """, (goal_id, start_date, end_date))
            failed_tasks = result.scalar()
            
            # Calculate success rate
            success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
            
            # Calculate average completion time
            result = await session.execute("""
                SELECT AVG(EXTRACT(EPOCH FROM (completed_at - started_at))/60) 
                FROM agent_tasks 
                WHERE goal_id = %s AND status = 'completed' AND completed_at BETWEEN %s AND %s
            """, (goal_id, start_date, end_date))
            avg_completion_time = float(result.scalar() or 0)
            
            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": success_rate,
                "avg_completion_time": avg_completion_time
            }

    async def _calculate_agent_performance(self, goal_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Dict[str, Any]]:
        if not self.database:
            return {}
        
        async with self.database.get_session() as session:
            # Get agent performance data
            result = await session.execute("""
                SELECT agent_name, 
                       COUNT(*) as total_tasks,
                       COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                       COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
                       AVG(EXTRACT(EPOCH FROM (completed_at - started_at))/60) as avg_duration
                FROM agent_tasks 
                WHERE goal_id = %s AND assigned_at BETWEEN %s AND %s
                GROUP BY agent_name
            """, (goal_id, start_date, end_date))
            
            agent_performance = {}
            for row in result.fetchall():
                agent_name = row[0]
                total_tasks = row[1]
                completed_tasks = row[2]
                failed_tasks = row[3]
                avg_duration = float(row[4] or 0)
                
                success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
                
                agent_performance[agent_name] = {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "failed_tasks": failed_tasks,
                    "success_rate": success_rate,
                    "avg_duration": avg_duration,
                    "efficiency_score": self._calculate_efficiency_score(success_rate, avg_duration)
                }
            
            return agent_performance

    def _calculate_efficiency_score(self, success_rate: float, avg_duration: float) -> float:
        # Simple efficiency scoring based on success rate and duration
        # Higher success rate and lower duration = higher efficiency
        success_score = min(100.0, success_rate)
        duration_score = max(0.0, 100.0 - (avg_duration / 60.0 * 10))  # Penalize long durations
        
        return (success_score * 0.7 + duration_score * 0.3)

    async def _generate_trend_data(self, goal_id: str, start_date: datetime, end_date: datetime, timeframe: AnalyticsTimeframe) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            # Generate time buckets based on timeframe
            if timeframe == AnalyticsTimeframe.HOUR:
                time_format = "YYYY-MM-DD HH24:00"
                interval = "1 hour"
            elif timeframe == AnalyticsTimeframe.DAY:
                time_format = "YYYY-MM-DD"
                interval = "1 day"
            elif timeframe == AnalyticsTimeframe.WEEK:
                time_format = "YYYY-WW"
                interval = "1 week"
            else:
                time_format = "YYYY-MM-DD"
                interval = "1 day"
            
            async with self.database.get_session() as session:
                result = await session.execute(f"""
                    SELECT 
                        TO_CHAR(assigned_at, %s) as time_bucket,
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks
                    FROM agent_tasks 
                    WHERE goal_id = %s AND assigned_at BETWEEN %s AND %s
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """, (time_format, goal_id, start_date, end_date))
                
                trend_data = []
                for row in result.fetchall():
                    time_bucket = row[0]
                    total_tasks = row[1]
                    completed_tasks = row[2]
                    failed_tasks = row[3]
                    
                    success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
                    
                    trend_data.append({
                        "time_bucket": time_bucket,
                        "total_tasks": total_tasks,
                        "completed_tasks": completed_tasks,
                        "failed_tasks": failed_tasks,
                        "success_rate": success_rate
                    })
                
                return trend_data
                
        except Exception as e:
            self.logger.error(f"Failed to generate trend data: {str(e)}")
            return []

    async def _generate_goal_insights(self, goal_id: str, task_metrics: Dict[str, Any], agent_performance: Dict[str, Dict[str, Any]]) -> List[str]:
        insights = []
        
        # Task completion insights
        if task_metrics["success_rate"] < 80:
            insights.append(f"Low success rate ({task_metrics['success_rate']:.1f}%) - consider reviewing task assignments and agent capabilities")
        
        if task_metrics["failed_tasks"] > task_metrics["total_tasks"] * 0.2:
            insights.append(f"High failure rate ({task_metrics['failed_tasks']} out of {task_metrics['total_tasks']} tasks) - investigate root causes")
        
        # Agent performance insights
        if agent_performance:
            best_agent = max(agent_performance.items(), key=lambda x: x[1]["efficiency_score"])
            worst_agent = min(agent_performance.items(), key=lambda x: x[1]["efficiency_score"])
            
            if best_agent[1]["efficiency_score"] > 80:
                insights.append(f"Agent {best_agent[0]} is performing excellently - consider assigning more critical tasks")
            
            if worst_agent[1]["efficiency_score"] < 50:
                insights.append(f"Agent {worst_agent[0]} is struggling - consider additional training or task reassignment")
            
            # Workload balance
            agent_workloads = [agent_data["total_tasks"] for agent_data in agent_performance.values()]
            if max(agent_workloads) - min(agent_workloads) > 3:
                insights.append("Workload is imbalanced across agents - consider redistributing tasks")
        
        # Time-based insights
        if task_metrics["avg_completion_time"] > 120:  # More than 2 hours
            insights.append("Tasks are taking longer than expected - review task complexity and agent assignments")
        
        return insights

    async def get_agent_effectiveness_metrics(self, agent_name: str, timeframe: AnalyticsTimeframe = AnalyticsTimeframe.WEEK) -> AgentEffectivenessMetrics:
        try:
            # Check cache first
            cache_key = f"agent_effectiveness:{agent_name}:{timeframe.value}"
            if self.redis:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    cached_metrics = json.loads(cached_data)
                    return AgentEffectivenessMetrics(**cached_metrics)
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, timeframe)
            
            # Get agent performance data
            agent_data = await self._get_agent_performance_data(agent_name, start_date, end_date)
            
            # Calculate task complexity distribution
            complexity_distribution = await self._get_task_complexity_distribution(agent_name, start_date, end_date)
            
            # Calculate goal contribution
            goal_contribution = await self._get_goal_contribution(agent_name, start_date, end_date)
            
            # Calculate performance score
            performance_score = self._calculate_agent_performance_score(agent_data)
            
            # Create metrics object
            metrics = AgentEffectivenessMetrics(
                agent_name=agent_name,
                timeframe=timeframe,
                total_tasks_assigned=agent_data["total_tasks"],
                completed_tasks=agent_data["completed_tasks"],
                failed_tasks=agent_data["failed_tasks"],
                success_rate=agent_data["success_rate"],
                avg_task_duration=agent_data["avg_duration"],
                task_complexity_distribution=complexity_distribution,
                goal_contribution=goal_contribution,
                performance_score=performance_score
            )
            
            # Cache results
            if self.redis:
                cache_data = {
                    "agent_name": metrics.agent_name,
                    "timeframe": metrics.timeframe.value,
                    "total_tasks_assigned": metrics.total_tasks_assigned,
                    "completed_tasks": metrics.completed_tasks,
                    "failed_tasks": metrics.failed_tasks,
                    "success_rate": metrics.success_rate,
                    "avg_task_duration": metrics.avg_task_duration,
                    "task_complexity_distribution": metrics.task_complexity_distribution,
                    "goal_contribution": metrics.goal_contribution,
                    "performance_score": metrics.performance_score
                }
                await self.redis.set(cache_key, json.dumps(cache_data), expire=1800)  # 30 minutes
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get agent effectiveness metrics: {str(e)}")
            raise

    async def _get_agent_performance_data(self, agent_name: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        if not self.database:
            return {"total_tasks": 0, "completed_tasks": 0, "failed_tasks": 0, "success_rate": 0.0, "avg_duration": 0.0}
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT 
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
                    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))/60) as avg_duration
                FROM agent_tasks 
                WHERE agent_name = %s AND assigned_at BETWEEN %s AND %s
            """, (agent_name, start_date, end_date))
            
            row = result.fetchone()
            if row:
                total_tasks = row[0]
                completed_tasks = row[1]
                failed_tasks = row[2]
                avg_duration = float(row[3] or 0)
                
                success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
                
                return {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "failed_tasks": failed_tasks,
                    "success_rate": success_rate,
                    "avg_duration": avg_duration
                }
        
        return {"total_tasks": 0, "completed_tasks": 0, "failed_tasks": 0, "success_rate": 0.0, "avg_duration": 0.0}

    async def _get_task_complexity_distribution(self, agent_name: str, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        if not self.database:
            return {}
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT priority, COUNT(*) 
                FROM agent_tasks 
                WHERE agent_name = %s AND assigned_at BETWEEN %s AND %s
                GROUP BY priority
            """, (agent_name, start_date, end_date))
            
            return dict(result.fetchall())

    async def _get_goal_contribution(self, agent_name: str, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        if not self.database:
            return {}
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT g.name, COUNT(at.id) * 100.0 / (
                    SELECT COUNT(*) FROM agent_tasks at2 
                    WHERE at2.goal_id = g.id AND at2.assigned_at BETWEEN %s AND %s
                ) as contribution_percentage
                FROM agent_tasks at
                JOIN goals g ON at.goal_id = g.id
                WHERE at.agent_name = %s AND at.assigned_at BETWEEN %s AND %s
                GROUP BY g.id, g.name
            """, (start_date, end_date, agent_name, start_date, end_date))
            
            return {row[0]: float(row[1] or 0) for row in result.fetchall()}

    def _calculate_agent_performance_score(self, agent_data: Dict[str, Any]) -> float:
        # Calculate performance score based on multiple factors
        success_rate = agent_data["success_rate"]
        avg_duration = agent_data["avg_duration"]
        total_tasks = agent_data["total_tasks"]
        
        # Base score from success rate
        base_score = success_rate
        
        # Duration penalty (tasks should be completed efficiently)
        duration_penalty = min(20.0, avg_duration / 60.0 * 5)  # Max 20 point penalty
        
        # Volume bonus (agents handling more tasks get bonus)
        volume_bonus = min(10.0, total_tasks * 0.5)  # Max 10 point bonus
        
        final_score = base_score - duration_penalty + volume_bonus
        return max(0.0, min(100.0, final_score))

    async def get_system_wide_analytics(self, timeframe: AnalyticsTimeframe = AnalyticsTimeframe.WEEK) -> Dict[str, Any]:
        try:
            # Check cache first
            cache_key = f"system_analytics:{timeframe.value}"
            if self.redis:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, timeframe)
            
            # Get system-wide metrics
            total_goals = await self._get_total_goals(start_date, end_date)
            total_tasks = await self._get_total_tasks(start_date, end_date)
            agent_performance = await self._get_system_agent_performance(start_date, end_date)
            goal_success_rates = await self._get_goal_success_rates(start_date, end_date)
            
            analytics = {
                "timeframe": timeframe.value,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_goals": total_goals,
                "total_tasks": total_tasks,
                "agent_performance": agent_performance,
                "goal_success_rates": goal_success_rates,
                "system_health_score": self._calculate_system_health_score(agent_performance, goal_success_rates),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache results
            if self.redis:
                await self.redis.set(cache_key, json.dumps(analytics), expire=1800)  # 30 minutes
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to get system-wide analytics: {str(e)}")
            raise

    async def _get_total_goals(self, start_date: datetime, end_date: datetime) -> int:
        if not self.database:
            return 0
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT COUNT(*) FROM goals 
                WHERE created_at BETWEEN %s AND %s
            """, (start_date, end_date))
            
            return result.scalar() or 0

    async def _get_total_tasks(self, start_date: datetime, end_date: datetime) -> int:
        if not self.database:
            return 0
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT COUNT(*) FROM agent_tasks 
                WHERE assigned_at BETWEEN %s AND %s
            """, (start_date, end_date))
            
            return result.scalar() or 0

    async def _get_system_agent_performance(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        if not self.database:
            return {}
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT 
                    agent_name,
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))/60) as avg_duration
                FROM agent_tasks 
                WHERE assigned_at BETWEEN %s AND %s
                GROUP BY agent_name
            """, (start_date, end_date))
            
            agent_performance = {}
            for row in result.fetchall():
                agent_name = row[0]
                total_tasks = row[1]
                completed_tasks = row[2]
                avg_duration = float(row[3] or 0)
                
                success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
                
                agent_performance[agent_name] = {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "success_rate": success_rate,
                    "avg_duration": avg_duration
                }
            
            return agent_performance

    async def _get_goal_success_rates(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        if not self.database:
            return {}
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT g.name, 
                       COUNT(at.id) as total_tasks,
                       COUNT(CASE WHEN at.status = 'completed' THEN 1 END) as completed_tasks
                FROM goals g
                LEFT JOIN agent_tasks at ON g.id = at.goal_id AND at.assigned_at BETWEEN %s AND %s
                WHERE g.created_at BETWEEN %s AND %s
                GROUP BY g.id, g.name
            """, (start_date, end_date, start_date, end_date))
            
            goal_success_rates = {}
            for row in result.fetchall():
                goal_name = row[0]
                total_tasks = row[1]
                completed_tasks = row[2]
                
                success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
                goal_success_rates[goal_name] = success_rate
            
            return goal_success_rates

    def _calculate_system_health_score(self, agent_performance: Dict[str, Any], goal_success_rates: Dict[str, float]) -> float:
        if not agent_performance or not goal_success_rates:
            return 0.0
        
        # Calculate average agent success rate
        agent_success_rates = [data["success_rate"] for data in agent_performance.values()]
        avg_agent_success = sum(agent_success_rates) / len(agent_success_rates) if agent_success_rates else 0.0
        
        # Calculate average goal success rate
        goal_success_values = list(goal_success_rates.values())
        avg_goal_success = sum(goal_success_values) / len(goal_success_values) if goal_success_values else 0.0
        
        # Weighted system health score
        system_health = (avg_agent_success * 0.6) + (avg_goal_success * 0.4)
        
        return round(system_health, 2)

    async def close(self):
        self.logger.info("Closing GoalAnalytics...")
        if self.database:
            await self.database.close()

# Global instances and initialization functions
_goal_analytics: Optional[GoalAnalytics] = None

async def init_goal_analytics() -> GoalAnalytics:
    global _goal_analytics
    if not _goal_analytics:
        _goal_analytics = GoalAnalytics()
        await _goal_analytics.initialize()
    return _goal_analytics

async def get_goal_analytics() -> GoalAnalytics:
    global _goal_analytics
    if not _goal_analytics:
        _goal_analytics = await init_goal_analytics()
    return _goal_analytics
