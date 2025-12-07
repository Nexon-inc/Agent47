import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta, date
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from ..event_bus.kafka_manager import EventBus, get_kafka
from ..ai import get_ai_service_manager, AIServiceManager
from ..cache.redis_manager import init_redis
from collections import defaultdict

logger = logging.getLogger(__name__)

class MetricType(Enum):
    ENGAGEMENT = "engagement"
    RESPONSE_TIME = "response_time"
    ROI = "roi"
    USAGE = "usage"
    TASK_COMPLETION = "task_completion"
    SUCCESS_RATE = "success_rate"
    USER_SATISFACTION = "user_satisfaction"

class TimePeriod(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

@dataclass
class AnalyticsMetric:
    id: str
    user_id: int
    agent_id: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = None
    period: TimePeriod = TimePeriod.DAY

@dataclass
class AnalyticsSummary:
    total_tasks: int
    completed_tasks: int
    success_rate: float
    average_response_time: float
    total_engagement: float
    roi_percentage: float
    user_satisfaction: float
    period_start: datetime
    period_end: datetime
    agent_breakdown: Dict[str, Dict[str, Any]]

@dataclass
class ChartDataPoint:
    date: str
    value: float
    agent_id: Optional[str] = None
    metadata: Dict[str, Any] = None

class AnalyticsService:
    """Service for analytics and performance tracking"""
    
    def __init__(self):
        self.event_bus: Optional[EventBus] = None
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.redis_client = None
        self._initialized = False
        self.metrics: Dict[str, AnalyticsMetric] = {}
        self.agent_colors = {
            "aria": "#FF6B1A",
            "clara": "#FF1493", 
            "jackie": "#9370DB",
            "shakes": "#3CB371",
            "eric": "#FFD700",
            "joe": "#3B82F6",
            "purity": "#6366F1"
        }
    
    async def initialize(self):
        """Initialize analytics service"""
        if self._initialized:
            return
        
        try:
            kafka_manager = await get_kafka()
            self.event_bus = kafka_manager.event_bus
            self.ai_service_manager = await get_ai_service_manager()
            self.redis_client = await init_redis()
            
            # Subscribe to analytics events
            await self._setup_event_handlers()
            
            self._initialized = True
            logger.info("Analytics service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize analytics service: {e}")
            raise
    
    async def _setup_event_handlers(self):
        """Setup event handlers for analytics events"""
        self.event_bus.register_handler("task.completed", self._handle_task_completed)
        self.event_bus.register_handler("task.failed", self._handle_task_failed)
        self.event_bus.register_handler("agent.response", self._handle_agent_response)
        self.event_bus.register_handler("user.feedback", self._handle_user_feedback)
        
        # Subscribe to topics
        await self.event_bus.subscribe_to_topic("task.completed")
        await self.event_bus.subscribe_to_topic("task.failed")
        await self.event_bus.subscribe_to_topic("agent.response")
        await self.event_bus.subscribe_to_topic("user.feedback")
    
    async def record_metric(
        self,
        user_id: int,
        agent_id: str,
        metric_type: MetricType,
        value: float,
        metadata: Dict[str, Any] = None
    ) -> AnalyticsMetric:
        """Record a new analytics metric"""
        if not self._initialized:
            await self.initialize()
        
        metric_id = f"metric_{user_id}_{agent_id}_{datetime.utcnow().timestamp()}"
        
        metric = AnalyticsMetric(
            id=metric_id,
            user_id=user_id,
            agent_id=agent_id,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            period=TimePeriod.DAY
        )
        
        self.metrics[metric_id] = metric
        
        # Publish metric event
        await self.event_bus.publish_event("analytics.metric_recorded", {
            "metric": asdict(metric),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Analytics metric recorded: {metric_type.value} = {value} for agent {agent_id}")
        return metric
    
    async def get_user_analytics(
        self,
        user_id: int,
        period_days: int = 30,
        agent_id: Optional[str] = None,
        metric_type: Optional[MetricType] = None
    ) -> AnalyticsSummary:
        """Get comprehensive analytics for a user"""
        if not self._initialized:
            await self.initialize()
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Filter metrics by user and date range
        user_metrics = [
            metric for metric in self.metrics.values()
            if metric.user_id == user_id and start_date <= metric.timestamp <= end_date
        ]
        
        # Apply additional filters
        if agent_id:
            user_metrics = [m for m in user_metrics if m.agent_id == agent_id]
        if metric_type:
            user_metrics = [m for m in user_metrics if m.metric_type == metric_type]
        
        # Calculate summary statistics
        total_tasks = len([m for m in user_metrics if m.metric_type == MetricType.TASK_COMPLETION])
        completed_tasks = len([m for m in user_metrics if m.metric_type == MetricType.TASK_COMPLETION and m.value > 0])
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        response_times = [m.value for m in user_metrics if m.metric_type == MetricType.RESPONSE_TIME]
        average_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        engagement_values = [m.value for m in user_metrics if m.metric_type == MetricType.ENGAGEMENT]
        total_engagement = sum(engagement_values)
        
        roi_values = [m.value for m in user_metrics if m.metric_type == MetricType.ROI]
        roi_percentage = sum(roi_values) / len(roi_values) if roi_values else 0
        
        satisfaction_values = [m.value for m in user_metrics if m.metric_type == MetricType.USER_SATISFACTION]
        user_satisfaction = sum(satisfaction_values) / len(satisfaction_values) if satisfaction_values else 0
        
        # Calculate agent breakdown
        agent_breakdown = defaultdict(lambda: {
            "tasks_completed": 0,
            "success_rate": 0,
            "avg_response_time": 0,
            "engagement": 0,
            "roi": 0
        })
        
        for metric in user_metrics:
            agent_data = agent_breakdown[metric.agent_id]
            
            if metric.metric_type == MetricType.TASK_COMPLETION:
                agent_data["tasks_completed"] += 1
            elif metric.metric_type == MetricType.RESPONSE_TIME:
                agent_data["avg_response_time"] = metric.value
            elif metric.metric_type == MetricType.ENGAGEMENT:
                agent_data["engagement"] += metric.value
            elif metric.metric_type == MetricType.ROI:
                agent_data["roi"] = metric.value
        
        # Calculate success rates per agent
        for agent_id, data in agent_breakdown.items():
            agent_tasks = [m for m in user_metrics if m.agent_id == agent_id and m.metric_type == MetricType.TASK_COMPLETION]
            completed_agent_tasks = [m for m in agent_tasks if m.value > 0]
            data["success_rate"] = (len(completed_agent_tasks) / len(agent_tasks) * 100) if agent_tasks else 0
        
        return AnalyticsSummary(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            success_rate=success_rate,
            average_response_time=average_response_time,
            total_engagement=total_engagement,
            roi_percentage=roi_percentage,
            user_satisfaction=user_satisfaction,
            period_start=start_date,
            period_end=end_date,
            agent_breakdown=dict(agent_breakdown)
        )
    
    async def get_chart_data(
        self,
        user_id: int,
        metric_type: MetricType,
        period_days: int = 30,
        agent_id: Optional[str] = None,
        group_by: TimePeriod = TimePeriod.DAY
    ) -> List[ChartDataPoint]:
        """Get chart data for a specific metric"""
        if not self._initialized:
            await self.initialize()
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Filter metrics
        user_metrics = [
            metric for metric in self.metrics.values()
            if (metric.user_id == user_id and 
                metric.metric_type == metric_type and
                start_date <= metric.timestamp <= end_date)
        ]
        
        if agent_id:
            user_metrics = [m for m in user_metrics if m.agent_id == agent_id]
        
        # Group by time period
        grouped_data = defaultdict(list)
        
        for metric in user_metrics:
            if group_by == TimePeriod.DAY:
                key = metric.timestamp.date().isoformat()
            elif group_by == TimePeriod.WEEK:
                week_start = metric.timestamp.date() - timedelta(days=metric.timestamp.weekday())
                key = week_start.isoformat()
            elif group_by == TimePeriod.MONTH:
                key = metric.timestamp.strftime("%Y-%m")
            else:
                key = metric.timestamp.date().isoformat()
            
            grouped_data[key].append(metric)
        
        # Create chart data points
        chart_data = []
        for date_key, metrics in grouped_data.items():
            if agent_id:
                # Single agent data
                avg_value = sum(m.value for m in metrics) / len(metrics)
                chart_data.append(ChartDataPoint(
                    date=date_key,
                    value=avg_value,
                    agent_id=agent_id
                ))
            else:
                # Multiple agents data
                agent_values = defaultdict(list)
                for metric in metrics:
                    agent_values[metric.agent_id].append(metric.value)
                
                for agent_id, values in agent_values.items():
                    avg_value = sum(values) / len(values)
                    chart_data.append(ChartDataPoint(
                        date=date_key,
                        value=avg_value,
                        agent_id=agent_id,
                        metadata={"color": self.agent_colors.get(agent_id, "#6B7280")}
                    ))
        
        # Sort by date
        chart_data.sort(key=lambda x: x.date)
        return chart_data
    
    async def get_usage_distribution(
        self,
        user_id: int,
        period_days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get usage distribution across agents"""
        if not self._initialized:
            await self.initialize()
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Get task completion metrics
        task_metrics = [
            metric for metric in self.metrics.values()
            if (metric.user_id == user_id and 
                metric.metric_type == MetricType.TASK_COMPLETION and
                start_date <= metric.timestamp <= end_date)
        ]
        
        # Count tasks per agent
        agent_counts = defaultdict(int)
        for metric in task_metrics:
            agent_counts[metric.agent_id] += 1
        
        # Create distribution data
        total_tasks = sum(agent_counts.values())
        distribution = []
        
        for agent_id, count in agent_counts.items():
            percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
            distribution.append({
                "name": agent_id.title(),
                "value": count,
                "percentage": percentage,
                "color": self.agent_colors.get(agent_id, "#6B7280")
            })
        
        return distribution
    
    async def get_detailed_data(
        self,
        user_id: int,
        period_days: int = 30,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get detailed analytics data for tables"""
        if not self._initialized:
            await self.initialize()
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Get all metrics for the user
        user_metrics = [
            metric for metric in self.metrics.values()
            if metric.user_id == user_id and start_date <= metric.timestamp <= end_date
        ]
        
        if agent_id:
            user_metrics = [m for m in user_metrics if m.agent_id == agent_id]
        
        # Group by task (assuming tasks have unique identifiers in metadata)
        task_groups = defaultdict(list)
        for metric in user_metrics:
            task_id = metric.metadata.get("task_id", f"task_{metric.id}")
            task_groups[task_id].append(metric)
        
        # Create detailed records
        detailed_data = []
        for task_id, metrics in list(task_groups.items())[:limit]:
            # Get task info from first metric
            first_metric = metrics[0]
            task_title = first_metric.metadata.get("task_title", f"Task {task_id}")
            
            # Calculate metrics
            engagement = next((m.value for m in metrics if m.metric_type == MetricType.ENGAGEMENT), 0)
            response_time = next((m.value for m in metrics if m.metric_type == MetricType.RESPONSE_TIME), 0)
            roi = next((m.value for m in metrics if m.metric_type == MetricType.ROI), 0)
            satisfaction = next((m.value for m in metrics if m.metric_type == MetricType.USER_SATISFACTION), 0)
            
            detailed_data.append({
                "id": task_id,
                "task": task_title,
                "agent": first_metric.agent_id.title(),
                "engagement": f"{engagement:.1f}%",
                "response_time": f"{response_time:.0f}ms",
                "roi": f"{roi:.1f}%",
                "satisfaction": f"{satisfaction:.1f}/5",
                "date": first_metric.timestamp.strftime("%Y-%m-%d %H:%M"),
                "status": "completed" if any(m.metric_type == MetricType.TASK_COMPLETION and m.value > 0 for m in metrics) else "failed"
            })
        
        # Sort by date (newest first)
        detailed_data.sort(key=lambda x: x["date"], reverse=True)
        return detailed_data
    
    async def generate_mock_data(self, user_id: int, days: int = 30):
        """Generate mock analytics data for demonstration"""
        import random
        
        agents = ["aria", "clara", "jackie", "shakes", "eric", "joe", "purity"]
        metric_types = [MetricType.ENGAGEMENT, MetricType.RESPONSE_TIME, MetricType.ROI, MetricType.TASK_COMPLETION, MetricType.USER_SATISFACTION]
        
        for day in range(days):
            date = datetime.utcnow() - timedelta(days=day)
            
            for agent in agents:
                # Generate 3-8 metrics per agent per day
                num_metrics = random.randint(3, 8)
                
                for _ in range(num_metrics):
                    metric_type = random.choice(metric_types)
                    
                    if metric_type == MetricType.ENGAGEMENT:
                        value = random.uniform(60, 95)
                    elif metric_type == MetricType.RESPONSE_TIME:
                        value = random.uniform(500, 3000)
                    elif metric_type == MetricType.ROI:
                        value = random.uniform(15, 85)
                    elif metric_type == MetricType.TASK_COMPLETION:
                        value = random.choice([0, 1])  # 0 = failed, 1 = completed
                    elif metric_type == MetricType.USER_SATISFACTION:
                        value = random.uniform(3.5, 5.0)
                    else:
                        value = random.uniform(0, 100)
                    
                    await self.record_metric(
                        user_id=user_id,
                        agent_id=agent,
                        metric_type=metric_type,
                        value=value,
                        metadata={
                            "task_id": f"task_{agent}_{day}_{random.randint(1, 10)}",
                            "task_title": f"{agent.title()} Task {random.randint(1, 10)}",
                            "generated": True
                        }
                    )
    
    async def _handle_task_completed(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle task completion events"""
        try:
            task_data = event_data.get("data", {})
            user_id = task_data.get("user_id")
            agent_id = task_data.get("agent_id")
            
            if user_id and agent_id:
                await self.record_metric(
                    user_id=user_id,
                    agent_id=agent_id,
                    metric_type=MetricType.TASK_COMPLETION,
                    value=1.0,
                    metadata=task_data
                )
        except Exception as e:
            logger.error(f"Error handling task completion: {e}")
    
    async def _handle_task_failed(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle task failure events"""
        try:
            task_data = event_data.get("data", {})
            user_id = task_data.get("user_id")
            agent_id = task_data.get("agent_id")
            
            if user_id and agent_id:
                await self.record_metric(
                    user_id=user_id,
                    agent_id=agent_id,
                    metric_type=MetricType.TASK_COMPLETION,
                    value=0.0,
                    metadata=task_data
                )
        except Exception as e:
            logger.error(f"Error handling task failure: {e}")
    
    async def _handle_agent_response(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle agent response events"""
        try:
            response_data = event_data.get("data", {})
            user_id = response_data.get("user_id")
            agent_id = response_data.get("agent_id")
            response_time = response_data.get("response_time", 0)
            
            if user_id and agent_id and response_time:
                await self.record_metric(
                    user_id=user_id,
                    agent_id=agent_id,
                    metric_type=MetricType.RESPONSE_TIME,
                    value=response_time,
                    metadata=response_data
                )
        except Exception as e:
            logger.error(f"Error handling agent response: {e}")
    
    async def _handle_user_feedback(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle user feedback events"""
        try:
            feedback_data = event_data.get("data", {})
            user_id = feedback_data.get("user_id")
            agent_id = feedback_data.get("agent_id")
            satisfaction = feedback_data.get("satisfaction", 0)
            engagement = feedback_data.get("engagement", 0)
            
            if user_id and agent_id:
                if satisfaction > 0:
                    await self.record_metric(
                        user_id=user_id,
                        agent_id=agent_id,
                        metric_type=MetricType.USER_SATISFACTION,
                        value=satisfaction,
                        metadata=feedback_data
                    )
                
                if engagement > 0:
                    await self.record_metric(
                        user_id=user_id,
                        agent_id=agent_id,
                        metric_type=MetricType.ENGAGEMENT,
                        value=engagement,
                        metadata=feedback_data
                    )
        except Exception as e:
            logger.error(f"Error handling user feedback: {e}")

# Global analytics service instance
analytics_service = AnalyticsService()

async def get_analytics_service() -> AnalyticsService:
    return analytics_service

async def init_analytics():
    await analytics_service.initialize()

async def close_analytics():
    # Cleanup if needed
    pass
