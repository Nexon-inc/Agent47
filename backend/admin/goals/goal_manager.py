import asyncio
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from core.database import get_database, DatabaseManager
from core.cache import get_redis, RedisManager
from core.event_bus import get_kafka, KafkaManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class GoalStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class GoalPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class GoalType(Enum):
    USER_ACQUISITION = "user_acquisition"
    REVENUE_GENERATION = "revenue_generation"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    MARKET_EXPANSION = "market_expansion"
    PRODUCT_DEVELOPMENT = "product_development"
    CUSTOM = "custom"

@dataclass
class GoalMetric:
    name: str
    target_value: float
    current_value: float = 0.0
    unit: str = ""
    weight: float = 1.0
    is_primary: bool = False
    
    @property
    def progress_percentage(self) -> float:
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)
    
    @property
    def is_completed(self) -> bool:
        return self.current_value >= self.target_value

@dataclass
class Goal:
    id: str
    name: str
    description: str
    goal_type: GoalType
    status: GoalStatus
    priority: GoalPriority
    start_date: datetime
    end_date: datetime
    metrics: List[GoalMetric] = field(default_factory=list)
    assigned_agents: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    budget: float = 0.0
    actual_cost: float = 0.0
    
    @property
    def overall_progress(self) -> float:
        if not self.metrics:
            return 0.0
        
        total_weight = sum(metric.weight for metric in self.metrics)
        if total_weight == 0:
            return 0.0
        
        weighted_progress = sum(
            metric.progress_percentage * metric.weight 
            for metric in self.metrics
        )
        return weighted_progress / total_weight
    
    @property
    def is_completed(self) -> bool:
        return all(metric.is_completed for metric in self.metrics)
    
    @property
    def is_overdue(self) -> bool:
        return datetime.utcnow() > self.end_date and not self.is_completed
    
    @property
    def days_remaining(self) -> int:
        remaining = self.end_date - datetime.utcnow()
        return max(0, remaining.days)
    
    @property
    def days_elapsed(self) -> int:
        elapsed = datetime.utcnow() - self.start_date
        return max(0, elapsed.days)
    
    @property
    def completion_rate(self) -> float:
        total_days = (self.end_date - self.start_date).days
        if total_days == 0:
            return 0.0
        return min(100.0, (self.days_elapsed / total_days) * 100)

class GoalManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.kafka: Optional[KafkaManager] = None
        self.settings = get_settings()
        
        self.active_goals: Dict[str, Goal] = {}
        self.goal_templates: Dict[str, Dict[str, Any]] = {}
        self.logger = logger
        
        self._setup_goal_templates()

    def _setup_goal_templates(self):
        self.goal_templates = {
            "user_acquisition_500_1week": {
                "name": "User Acquisition: 500 Users in 1 Week",
                "description": "Acquire 500 new users within 1 week, with 200 paying users and 100 pro users",
                "goal_type": GoalType.USER_ACQUISITION,
                "priority": GoalPriority.HIGH,
                "metrics": [
                    {"name": "total_users", "target_value": 500, "unit": "users", "weight": 0.4, "is_primary": True},
                    {"name": "paying_users", "target_value": 200, "unit": "users", "weight": 0.35, "is_primary": False},
                    {"name": "pro_users", "target_value": 100, "unit": "users", "weight": 0.25, "is_primary": False}
                ],
                "assigned_agents": ["Clara", "Eric", "Joe"],
                "tags": ["acquisition", "growth", "revenue"]
            },
            "customer_support_95_4hours": {
                "name": "Customer Support: 95% Resolution in 4 Hours",
                "description": "Resolve 95% of customer support tickets within 4 hours",
                "goal_type": GoalType.CUSTOMER_SATISFACTION,
                "priority": GoalPriority.MEDIUM,
                "metrics": [
                    {"name": "resolution_rate", "target_value": 95.0, "unit": "%", "weight": 0.6, "is_primary": True},
                    {"name": "avg_response_time", "target_value": 4.0, "unit": "hours", "weight": 0.4, "is_primary": False}
                ],
                "assigned_agents": ["Jackie", "Shakes"],
                "tags": ["support", "satisfaction", "efficiency"]
            },
            "revenue_50k_mrr": {
                "name": "Revenue: $50K MRR by Month End",
                "description": "Achieve $50,000 Monthly Recurring Revenue by the end of the month",
                "goal_type": GoalType.REVENUE_GENERATION,
                "priority": GoalPriority.CRITICAL,
                "metrics": [
                    {"name": "mrr", "target_value": 50000, "unit": "USD", "weight": 1.0, "is_primary": True}
                ],
                "assigned_agents": ["Eric", "Joe", "Clara"],
                "tags": ["revenue", "growth", "business"]
            }
        }

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing GoalManager...")
            
            self.database = get_database()
            self.redis = await get_redis()
            self.kafka = await get_kafka()
            
            await self._setup_goal_tables()
            await self._load_active_goals()
            
            self.logger.info("GoalManager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GoalManager: {str(e)}")
            return False

    async def _setup_goal_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(500) NOT NULL,
                    description TEXT,
                    goal_type VARCHAR(100) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    priority VARCHAR(50) NOT NULL,
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    metrics JSONB NOT NULL,
                    assigned_agents JSONB NOT NULL,
                    created_by VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags JSONB NOT NULL,
                    budget DECIMAL(15,2) DEFAULT 0.0,
                    actual_cost DECIMAL(15,2) DEFAULT 0.0
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS goal_progress (
                    id SERIAL PRIMARY KEY,
                    goal_id VARCHAR(255) NOT NULL,
                    metric_name VARCHAR(255) NOT NULL,
                    current_value DECIMAL(15,4) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by VARCHAR(255),
                    notes TEXT,
                    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS goal_activities (
                    id SERIAL PRIMARY KEY,
                    goal_id VARCHAR(255) NOT NULL,
                    activity_type VARCHAR(100) NOT NULL,
                    description TEXT,
                    performed_by VARCHAR(255),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB,
                    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
                )
            """)
            
            await session.commit()

    async def _load_active_goals(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT id, name, description, goal_type, status, priority, start_date, end_date,
                       metrics, assigned_agents, created_by, created_at, updated_at, tags, budget, actual_cost
                FROM goals WHERE status IN (%s, %s, %s)
            """, (GoalStatus.ACTIVE.value, GoalStatus.PAUSED.value, GoalStatus.DRAFT.value))
            
            rows = result.fetchall()
            for row in rows:
                goal = self._create_goal_from_row(row)
                self.active_goals[goal.id] = goal

    def _create_goal_from_row(self, row) -> Goal:
        metrics = []
        for metric_data in row[8]:  # metrics JSONB
            metric = GoalMetric(
                name=metric_data["name"],
                target_value=metric_data["target_value"],
                current_value=metric_data.get("current_value", 0.0),
                unit=metric_data.get("unit", ""),
                weight=metric_data.get("weight", 1.0),
                is_primary=metric_data.get("is_primary", False)
            )
            metrics.append(metric)
        
        return Goal(
            id=row[0],
            name=row[1],
            description=row[2],
            goal_type=GoalType(row[3]),
            status=GoalStatus(row[4]),
            priority=GoalPriority(row[5]),
            start_date=row[6],
            end_date=row[7],
            metrics=metrics,
            assigned_agents=row[9],
            created_by=row[10],
            created_at=row[11],
            updated_at=row[12],
            tags=row[13],
            budget=float(row[14]) if row[14] else 0.0,
            actual_cost=float(row[15]) if row[15] else 0.0
        )

    async def create_goal(self, goal_data: Dict[str, Any], created_by: str) -> Goal:
        try:
            goal_id = str(uuid.uuid4())
            
            # Create metrics
            metrics = []
            for metric_data in goal_data["metrics"]:
                metric = GoalMetric(
                    name=metric_data["name"],
                    target_value=metric_data["target_value"],
                    unit=metric_data.get("unit", ""),
                    weight=metric_data.get("weight", 1.0),
                    is_primary=metric_data.get("is_primary", False)
                )
                metrics.append(metric)
            
            goal = Goal(
                id=goal_id,
                name=goal_data["name"],
                description=goal_data["description"],
                goal_type=GoalType(goal_data["goal_type"]),
                status=GoalStatus.DRAFT,
                priority=GoalPriority(goal_data["priority"]),
                start_date=datetime.fromisoformat(goal_data["start_date"]),
                end_date=datetime.fromisoformat(goal_data["end_date"]),
                metrics=metrics,
                assigned_agents=goal_data.get("assigned_agents", []),
                created_by=created_by,
                tags=goal_data.get("tags", []),
                budget=goal_data.get("budget", 0.0)
            )
            
            await self._save_goal_to_database(goal)
            await self._log_goal_activity(goal.id, "CREATE", f"Goal '{goal.name}' created", created_by)
            
            self.logger.info(f"Goal '{goal.name}' created successfully with ID: {goal_id}")
            return goal
            
        except Exception as e:
            self.logger.error(f"Failed to create goal: {str(e)}")
            raise

    async def create_goal_from_template(self, template_name: str, start_date: datetime, end_date: datetime, created_by: str, customizations: Dict[str, Any] = None) -> Goal:
        if template_name not in self.goal_templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.goal_templates[template_name].copy()
        if customizations:
            template.update(customizations)
        
        template["start_date"] = start_date.isoformat()
        template["end_date"] = end_date.isoformat()
        
        return await self.create_goal(template, created_by)

    async def _save_goal_to_database(self, goal: Goal):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        metrics_data = []
        for metric in goal.metrics:
            metrics_data.append({
                "name": metric.name,
                "target_value": metric.target_value,
                "current_value": metric.current_value,
                "unit": metric.unit,
                "weight": metric.weight,
                "is_primary": metric.is_primary
            })
        
        async with self.database.get_session() as session:
            await session.execute("""
                INSERT INTO goals (id, name, description, goal_type, status, priority, start_date, end_date,
                                metrics, assigned_agents, created_by, created_at, updated_at, tags, budget, actual_cost)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                goal.id, goal.name, goal.description, goal.goal_type.value, goal.status.value, goal.priority.value,
                goal.start_date, goal.end_date, json.dumps(metrics_data), json.dumps(goal.assigned_agents),
                goal.created_by, goal.created_at, goal.updated_at, json.dumps(goal.tags), goal.budget, goal.actual_cost
            ))
            await session.commit()

    async def get_goal(self, goal_id: str) -> Optional[Goal]:
        if goal_id in self.active_goals:
            return self.active_goals[goal_id]
        
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
                return self._create_goal_from_row(row)
        
        return None

    async def get_all_goals(self, status: Optional[GoalStatus] = None, goal_type: Optional[GoalType] = None) -> List[Goal]:
        if not self.database:
            return list(self.active_goals.values())
        
        query = """
            SELECT id, name, description, goal_type, status, priority, start_date, end_date,
                   metrics, assigned_agents, created_by, created_at, updated_at, tags, budget, actual_cost
            FROM goals
        """
        params = []
        
        if status or goal_type:
            query += " WHERE "
            conditions = []
            if status:
                conditions.append("status = %s")
                params.append(status.value)
            if goal_type:
                conditions.append("goal_type = %s")
                params.append(goal_type.value)
            query += " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        async with self.database.get_session() as session:
            result = await session.execute(query, params)
            rows = result.fetchall()
            
            goals = []
            for row in rows:
                goal = self._create_goal_from_row(row)
                goals.append(goal)
            
            return goals

    async def update_goal_status(self, goal_id: str, new_status: GoalStatus, updated_by: str) -> bool:
        goal = await self.get_goal(goal_id)
        if not goal:
            return False
        
        old_status = goal.status
        goal.status = new_status
        goal.updated_at = datetime.utcnow()
        
        if not self.database:
            return False
        
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE goals SET status = %s, updated_at = %s WHERE id = %s
                """, (new_status.value, goal.updated_at, goal_id))
                await session.commit()
                
                await self._log_goal_activity(
                    goal_id, 
                    "STATUS_CHANGE", 
                    f"Goal status changed from {old_status.value} to {new_status.value}", 
                    updated_by
                )
                
                if new_status == GoalStatus.ACTIVE:
                    self.active_goals[goal_id] = goal
                elif goal_id in self.active_goals:
                    del self.active_goals[goal_id]
                
                self.logger.info(f"Goal {goal_id} status updated to {new_status.value}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update goal status: {str(e)}")
            return False

    async def update_goal_metric(self, goal_id: str, metric_name: str, new_value: float, updated_by: str, notes: str = None) -> bool:
        goal = await self.get_goal(goal_id)
        if not goal:
            return False
        
        metric = next((m for m in goal.metrics if m.name == metric_name), None)
        if not metric:
            return False
        
        old_value = metric.current_value
        metric.current_value = new_value
        
        if not self.database:
            return False
        
        try:
            async with self.database.get_session() as session:
                # Update goal metrics
                metrics_data = []
                for m in goal.metrics:
                    metrics_data.append({
                        "name": m.name,
                        "target_value": m.target_value,
                        "current_value": m.current_value,
                        "unit": m.unit,
                        "weight": m.weight,
                        "is_primary": m.is_primary
                    })
                
                await session.execute("""
                    UPDATE goals SET metrics = %s, updated_at = %s WHERE id = %s
                """, (json.dumps(metrics_data), datetime.utcnow(), goal_id))
                
                # Log progress update
                await session.execute("""
                    INSERT INTO goal_progress (goal_id, metric_name, current_value, updated_by, notes)
                    VALUES (%s, %s, %s, %s, %s)
                """, (goal_id, metric_name, new_value, updated_by, notes))
                
                await session.commit()
                
                await self._log_goal_activity(
                    goal_id,
                    "METRIC_UPDATE",
                    f"Metric '{metric_name}' updated from {old_value} to {new_value}",
                    updated_by,
                    {"metric_name": metric_name, "old_value": old_value, "new_value": new_value}
                )
                
                # Check if goal is completed
                if goal.is_completed:
                    await self.update_goal_status(goal_id, GoalStatus.COMPLETED, updated_by)
                
                self.logger.info(f"Goal {goal_id} metric '{metric_name}' updated to {new_value}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update goal metric: {str(e)}")
            return False

    async def _log_goal_activity(self, goal_id: str, activity_type: str, description: str, performed_by: str, metadata: Dict[str, Any] = None):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO goal_activities (goal_id, activity_type, description, performed_by, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (goal_id, activity_type, description, performed_by, json.dumps(metadata or {})))
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log goal activity: {str(e)}")

    async def get_goal_progress(self, goal_id: str) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT metric_name, current_value, timestamp, updated_by, notes
                FROM goal_progress 
                WHERE goal_id = %s 
                ORDER BY timestamp DESC
            """, (goal_id,))
            
            rows = result.fetchall()
            progress = []
            for row in rows:
                progress.append({
                    "metric_name": row[0],
                    "current_value": float(row[1]),
                    "timestamp": row[2],
                    "updated_by": row[3],
                    "notes": row[4]
                })
            
            return progress

    async def get_goal_activities(self, goal_id: str) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT activity_type, description, performed_by, timestamp, metadata
                FROM goal_activities 
                WHERE goal_id = %s 
                ORDER BY timestamp DESC
            """, (goal_id,))
            
            rows = result.fetchall()
            activities = []
            for row in rows:
                activities.append({
                    "activity_type": row[0],
                    "description": row[1],
                    "performed_by": row[2],
                    "timestamp": row[3],
                    "metadata": row[4] if row[4] else {}
                })
            
            return activities

    async def delete_goal(self, goal_id: str, deleted_by: str) -> bool:
        goal = await self.get_goal(goal_id)
        if not goal:
            return False
        
        if not self.database:
            return False
        
        try:
            async with self.database.get_session() as session:
                await session.execute("DELETE FROM goals WHERE id = %s", (goal_id,))
                await session.commit()
                
                if goal_id in self.active_goals:
                    del self.active_goals[goal_id]
                
                await self._log_goal_activity(
                    goal_id,
                    "DELETE",
                    f"Goal '{goal.name}' deleted",
                    deleted_by
                )
                
                self.logger.info(f"Goal {goal_id} deleted successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to delete goal: {str(e)}")
            return False

    async def get_goal_templates(self) -> Dict[str, Dict[str, Any]]:
        return self.goal_templates.copy()

    async def close(self):
        self.logger.info("Closing GoalManager...")
        if self.database:
            await self.database.close()

# Global instances and initialization functions
_goal_manager: Optional[GoalManager] = None

async def init_goal_manager() -> GoalManager:
    global _goal_manager
    if not _goal_manager:
        _goal_manager = GoalManager()
        await _goal_manager.initialize()
    return _goal_manager

async def get_goal_manager() -> GoalManager:
    global _goal_manager
    if not _goal_manager:
        _goal_manager = await init_goal_manager()
    return _goal_manager
