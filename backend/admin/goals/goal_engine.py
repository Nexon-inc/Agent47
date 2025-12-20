import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

from core.database import get_database, DatabaseManager
from core.cache import get_redis, RedisManager
from core.event_bus import get_kafka, KafkaManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings
from core.utils.nlp_utils import get_nlp_utils, NLPUtils

logger = get_logger(__name__)

class AgentCapability(Enum):
    SOCIAL_MEDIA_MANAGEMENT = "social_media_management"
    CONTENT_CREATION = "content_creation"
    CUSTOMER_SUPPORT = "customer_support"
    SALES_AND_MARKETING = "sales_and_marketing"
    DATA_ANALYSIS = "data_analysis"
    AUTOMATION = "automation"
    RESEARCH = "research"
    COMMUNICATION = "communication"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AgentTask:
    id: str
    goal_id: str
    agent_name: str
    task_type: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    assigned_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: int = 0  # minutes
    actual_duration: Optional[int] = None
    progress: float = 0.0
    metadata: Dict[str, Any] = None
    result: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class GoalExecutionPlan:
    goal_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    estimated_completion_time: datetime
    current_phase: str
    agent_workload: Dict[str, int]
    critical_path: List[str]
    risk_factors: List[str]
    optimization_suggestions: List[str]

class GoalEngine(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.kafka: Optional[KafkaManager] = None
        self.nlp: Optional[NLPUtils] = None
        self.settings = get_settings()
        
        self.active_executions: Dict[str, GoalExecutionPlan] = {}
        self.agent_capabilities: Dict[str, List[AgentCapability]] = {}
        self.task_queue: List[AgentTask] = []
        self.logger = logger
        
        self._setup_agent_capabilities()

    def _setup_agent_capabilities(self):
        self.agent_capabilities = {
            "Aria": [AgentCapability.RESEARCH, AgentCapability.DATA_ANALYSIS, AgentCapability.AUTOMATION],
            "Clara": [AgentCapability.SOCIAL_MEDIA_MANAGEMENT, AgentCapability.CONTENT_CREATION, AgentCapability.COMMUNICATION],
            "Eric": [AgentCapability.SALES_AND_MARKETING, AgentCapability.CONTENT_CREATION, AgentCapability.COMMUNICATION],
            "Joe": [AgentCapability.SALES_AND_MARKETING, AgentCapability.DATA_ANALYSIS, AgentCapability.AUTOMATION],
            "Jackie": [AgentCapability.CUSTOMER_SUPPORT, AgentCapability.COMMUNICATION, AgentCapability.AUTOMATION],
            "Shakes": [AgentCapability.COMMUNICATION, AgentCapability.CONTENT_CREATION, AgentCapability.RESEARCH],
            "Purity": [AgentCapability.DATA_ANALYSIS, AgentCapability.RESEARCH, AgentCapability.AUTOMATION]
        }

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing GoalEngine...")
            
            self.database = get_database()
            self.redis = await get_redis()
            self.kafka = await get_kafka()
            self.nlp = await get_nlp_utils()
            
            await self._setup_goal_engine_tables()
            await self._load_active_executions()
            
            self.logger.info("GoalEngine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GoalEngine: {str(e)}")
            return False

    async def _setup_goal_engine_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS goal_executions (
                    id SERIAL PRIMARY KEY,
                    goal_id VARCHAR(255) NOT NULL,
                    total_tasks INTEGER NOT NULL,
                    completed_tasks INTEGER DEFAULT 0,
                    failed_tasks INTEGER DEFAULT 0,
                    estimated_completion_time TIMESTAMP,
                    current_phase VARCHAR(100),
                    agent_workload JSONB,
                    critical_path JSONB,
                    risk_factors JSONB,
                    optimization_suggestions JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'active'
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS agent_tasks (
                    id VARCHAR(255) PRIMARY KEY,
                    goal_id VARCHAR(255) NOT NULL,
                    agent_name VARCHAR(100) NOT NULL,
                    task_type VARCHAR(100) NOT NULL,
                    description TEXT NOT NULL,
                    priority VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    assigned_at TIMESTAMP NOT NULL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    estimated_duration INTEGER DEFAULT 0,
                    actual_duration INTEGER,
                    progress DECIMAL(5,2) DEFAULT 0.0,
                    metadata JSONB,
                    result TEXT,
                    error_message TEXT,
                    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    id SERIAL PRIMARY KEY,
                    task_id VARCHAR(255) NOT NULL,
                    depends_on_task_id VARCHAR(255) NOT NULL,
                    dependency_type VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES agent_tasks(id) ON DELETE CASCADE,
                    FOREIGN KEY (depends_on_task_id) REFERENCES agent_tasks(id) ON DELETE CASCADE
                )
            """)
            
            await session.commit()

    async def _load_active_executions(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT goal_id, total_tasks, completed_tasks, failed_tasks, estimated_completion_time,
                       current_phase, agent_workload, critical_path, risk_factors, optimization_suggestions
                FROM goal_executions WHERE status = 'active'
            """)
            
            rows = result.fetchall()
            for row in rows:
                execution_plan = GoalExecutionPlan(
                    goal_id=row[0],
                    total_tasks=row[1],
                    completed_tasks=row[2],
                    failed_tasks=row[3],
                    estimated_completion_time=row[4],
                    current_phase=row[5],
                    agent_workload=row[6] or {},
                    critical_path=row[7] or [],
                    risk_factors=row[8] or [],
                    optimization_suggestions=row[9] or []
                )
                self.active_executions[row[0]] = execution_plan

    async def create_execution_plan(self, goal_id: str, goal_data: Dict[str, Any]) -> GoalExecutionPlan:
        try:
            execution_plan = await self._generate_execution_plan(goal_id, goal_data)
            
            if not self.database:
                return execution_plan
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO goal_executions (goal_id, total_tasks, completed_tasks, failed_tasks,
                                               estimated_completion_time, current_phase, agent_workload,
                                               critical_path, risk_factors, optimization_suggestions)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    goal_id, execution_plan.total_tasks, execution_plan.completed_tasks,
                    execution_plan.failed_tasks, execution_plan.estimated_completion_time,
                    execution_plan.current_phase, json.dumps(execution_plan.agent_workload),
                    json.dumps(execution_plan.critical_path), json.dumps(execution_plan.risk_factors),
                    json.dumps(execution_plan.optimization_suggestions)
                ))
                await session.commit()
            
            self.active_executions[goal_id] = execution_plan
            await self._create_agent_tasks(goal_id, execution_plan)
            
            self.logger.info(f"Execution plan created for goal {goal_id}")
            return execution_plan
            
        except Exception as e:
            self.logger.error(f"Failed to create execution plan: {str(e)}")
            raise

    async def _generate_execution_plan(self, goal_id: str, goal_data: Dict[str, Any]) -> GoalExecutionPlan:
        goal_type = goal_data.get("goal_type")
        assigned_agents = goal_data.get("assigned_agents", [])
        start_date = datetime.fromisoformat(goal_data["start_date"])
        end_date = datetime.fromisoformat(goal_data["end_date"])
        
        # Analyze goal requirements and generate tasks
        tasks = await self._analyze_goal_requirements(goal_type, assigned_agents, start_date, end_date)
        
        # Calculate workload distribution
        agent_workload = {}
        for agent in assigned_agents:
            agent_tasks = [task for task in tasks if task.agent_name == agent]
            agent_workload[agent] = len(agent_tasks)
        
        # Identify critical path
        critical_path = await self._identify_critical_path(tasks)
        
        # Assess risks
        risk_factors = await self._assess_risks(goal_type, assigned_agents, start_date, end_date)
        
        # Generate optimization suggestions
        optimization_suggestions = await self._generate_optimization_suggestions(tasks, agent_workload, risk_factors)
        
        # Estimate completion time
        estimated_completion_time = await self._estimate_completion_time(tasks, critical_path, start_date, end_date)
        
        return GoalExecutionPlan(
            goal_id=goal_id,
            total_tasks=len(tasks),
            completed_tasks=0,
            failed_tasks=0,
            estimated_completion_time=estimated_completion_time,
            current_phase="planning",
            agent_workload=agent_workload,
            critical_path=critical_path,
            risk_factors=risk_factors,
            optimization_suggestions=optimization_suggestions
        )

    async def _analyze_goal_requirements(self, goal_type: str, assigned_agents: List[str], start_date: datetime, end_date: datetime) -> List[AgentTask]:
        tasks = []
        task_id_counter = 1
        
        if goal_type == "user_acquisition":
            # Phase 1: Market Research and Planning
            tasks.append(AgentTask(
                id=f"task_{task_id_counter}",
                goal_id="",  # Will be set later
                agent_name="Purity",
                task_type="market_research",
                description="Conduct market research to identify target audience and optimal acquisition channels",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                assigned_at=start_date,
                estimated_duration=120,
                metadata={"phase": "planning", "dependencies": []}
            ))
            task_id_counter += 1
            
            # Phase 2: Content Creation and Social Media
            tasks.append(AgentTask(
                id=f"task_{task_id_counter}",
                goal_id="",
                agent_name="Clara",
                task_type="content_creation",
                description="Create engaging social media content to attract target users",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                assigned_at=start_date + timedelta(hours=2),
                estimated_duration=180,
                metadata={"phase": "execution", "dependencies": ["task_1"]}
            ))
            task_id_counter += 1
            
            # Phase 3: Marketing Campaigns
            tasks.append(AgentTask(
                id=f"task_{task_id_counter}",
                goal_id="",
                agent_name="Eric",
                task_type="marketing_campaign",
                description="Execute targeted marketing campaigns across multiple channels",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                assigned_at=start_date + timedelta(hours=5),
                estimated_duration=240,
                metadata={"phase": "execution", "dependencies": ["task_1", "task_2"]}
            ))
            task_id_counter += 1
            
            # Phase 4: Sales and Conversion
            tasks.append(AgentTask(
                id=f"task_{task_id_counter}",
                goal_id="",
                agent_name="Joe",
                task_type="sales_optimization",
                description="Optimize conversion funnels and sales processes",
                priority=TaskPriority.CRITICAL,
                status=TaskStatus.PENDING,
                assigned_at=start_date + timedelta(hours=9),
                estimated_duration=300,
                metadata={"phase": "execution", "dependencies": ["task_3"]}
            ))
            
        elif goal_type == "customer_satisfaction":
            # Phase 1: Support System Analysis
            tasks.append(AgentTask(
                id=f"task_{task_id_counter}",
                goal_id="",
                agent_name="Purity",
                task_type="support_analysis",
                description="Analyze current support system performance and identify bottlenecks",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                assigned_at=start_date,
                estimated_duration=90,
                metadata={"phase": "analysis", "dependencies": []}
            ))
            task_id_counter += 1
            
            # Phase 2: Support Process Optimization
            tasks.append(AgentTask(
                id=f"task_{task_id_counter}",
                goal_id="",
                agent_name="Jackie",
                task_type="process_optimization",
                description="Optimize support processes and response workflows",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                assigned_at=start_date + timedelta(hours=1.5),
                estimated_duration=120,
                metadata={"phase": "optimization", "dependencies": ["task_1"]}
            ))
            task_id_counter += 1
            
            # Phase 3: Communication Enhancement
            tasks.append(AgentTask(
                id=f"task_{task_id_counter}",
                goal_id="",
                agent_name="Shakes",
                task_type="communication_enhancement",
                description="Enhance communication templates and response quality",
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                assigned_at=start_date + timedelta(hours=3.5),
                estimated_duration=150,
                metadata={"phase": "enhancement", "dependencies": ["task_2"]}
            ))
            
        elif goal_type == "revenue_generation":
            # Phase 1: Revenue Analysis
            tasks.append(AgentTask(
                id=f"task_{task_id_counter}",
                goal_id="",
                agent_name="Purity",
                task_type="revenue_analysis",
                description="Analyze current revenue streams and identify growth opportunities",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                assigned_at=start_date,
                estimated_duration=120,
                metadata={"phase": "analysis", "dependencies": []}
            ))
            task_id_counter += 1
            
            # Phase 2: Sales Strategy Development
            tasks.append(AgentTask(
                id=f"task_{task_id_counter}",
                goal_id="",
                agent_name="Eric",
                task_type="sales_strategy",
                description="Develop comprehensive sales strategy and target market analysis",
                priority=TaskPriority.CRITICAL,
                status=TaskStatus.PENDING,
                assigned_at=start_date + timedelta(hours=2),
                estimated_duration=180,
                metadata={"phase": "strategy", "dependencies": ["task_1"]}
            ))
            task_id_counter += 1
            
            # Phase 3: Conversion Optimization
            tasks.append(AgentTask(
                id=f"task_{task_id_counter}",
                goal_id="",
                agent_name="Joe",
                task_type="conversion_optimization",
                description="Optimize conversion funnels and implement A/B testing",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                assigned_at=start_date + timedelta(hours=5),
                estimated_duration=240,
                metadata={"phase": "optimization", "dependencies": ["task_2"]}
            ))
            task_id_counter += 1
            
            # Phase 4: Customer Retention
            tasks.append(AgentTask(
                id=f"task_{task_id_counter}",
                goal_id="",
                agent_name="Clara",
                task_type="customer_retention",
                description="Implement customer retention strategies and loyalty programs",
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                assigned_at=start_date + timedelta(hours=9),
                estimated_duration=180,
                metadata={"phase": "retention", "dependencies": ["task_3"]}
            ))
        
        return tasks

    async def _identify_critical_path(self, tasks: List[AgentTask]) -> List[str]:
        if not tasks:
            return []
        
        # Simple critical path identification based on dependencies and duration
        critical_tasks = []
        for task in tasks:
            if not task.metadata.get("dependencies"):
                critical_tasks.append(task.id)
            else:
                # Check if this task is on the critical path
                max_dependency_time = 0
                for dep_id in task.metadata["dependencies"]:
                    dep_task = next((t for t in tasks if t.id == dep_id), None)
                    if dep_task:
                        max_dependency_time = max(max_dependency_time, dep_task.estimated_duration)
                
                if max_dependency_time + task.estimated_duration > 0:
                    critical_tasks.append(task.id)
        
        return critical_tasks

    async def _assess_risks(self, goal_type: str, assigned_agents: List[str], start_date: datetime, end_date: datetime) -> List[str]:
        risks = []
        
        # Time-based risks
        total_days = (end_date - start_date).days
        if total_days < 7:
            risks.append("Aggressive timeline may impact quality")
        elif total_days > 30:
            risks.append("Extended timeline may lead to scope creep")
        
        # Resource risks
        if len(assigned_agents) < 2:
            risks.append("Limited agent availability may cause bottlenecks")
        elif len(assigned_agents) > 5:
            risks.append("Too many agents may lead to coordination challenges")
        
        # Goal-specific risks
        if goal_type == "user_acquisition":
            risks.append("Market competition may affect acquisition rates")
            risks.append("Seasonal factors may impact user behavior")
        elif goal_type == "customer_satisfaction":
            risks.append("Support quality may vary during high-volume periods")
        elif goal_type == "revenue_generation":
            risks.append("Economic factors may affect customer spending")
            risks.append("Market saturation may limit growth potential")
        
        return risks

    async def _generate_optimization_suggestions(self, tasks: List[AgentTask], agent_workload: Dict[str, int], risk_factors: List[str]) -> List[str]:
        suggestions = []
        
        # Workload optimization
        max_workload = max(agent_workload.values()) if agent_workload else 0
        min_workload = min(agent_workload.values()) if agent_workload else 0
        
        if max_workload - min_workload > 2:
            suggestions.append("Redistribute tasks to balance agent workload")
        
        # Task optimization
        total_estimated_time = sum(task.estimated_duration for task in tasks)
        if total_estimated_time > 480:  # More than 8 hours
            suggestions.append("Consider parallel task execution to reduce timeline")
        
        # Risk mitigation
        if "Aggressive timeline" in risk_factors:
            suggestions.append("Implement parallel processing and reduce task dependencies")
        if "Limited agent availability" in risk_factors:
            suggestions.append("Prioritize critical path tasks and automate non-essential processes")
        
        return suggestions

    async def _estimate_completion_time(self, tasks: List[AgentTask], critical_path: List[str], start_date: datetime, end_date: datetime) -> datetime:
        if not tasks:
            return end_date
        
        # Calculate critical path duration
        critical_duration = 0
        for task_id in critical_path:
            task = next((t for t in tasks if t.id == task_id), None)
            if task:
                critical_duration += task.estimated_duration
        
        # Convert minutes to hours and add buffer
        critical_hours = (critical_duration / 60) * 1.2  # 20% buffer
        
        estimated_completion = start_date + timedelta(hours=critical_hours)
        
        # Ensure it doesn't exceed the goal deadline
        return min(estimated_completion, end_date)

    async def _create_agent_tasks(self, goal_id: str, execution_plan: GoalExecutionPlan):
        if not self.database:
            return
        
        # Get tasks for this goal
        tasks = await self._get_tasks_for_goal(goal_id)
        
        for task in tasks:
            task.goal_id = goal_id
            await self._save_task_to_database(task)

    async def _get_tasks_for_goal(self, goal_id: str) -> List[AgentTask]:
        # This would typically come from the execution plan generation
        # For now, return empty list as tasks are created during plan generation
        return []

    async def _save_task_to_database(self, task: AgentTask):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute("""
                INSERT INTO agent_tasks (id, goal_id, agent_name, task_type, description, priority,
                                       status, assigned_at, started_at, completed_at, estimated_duration,
                                       actual_duration, progress, metadata, result, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                task.id, task.goal_id, task.agent_name, task.task_type, task.description,
                task.priority.value, task.status.value, task.assigned_at, task.started_at,
                task.completed_at, task.estimated_duration, task.actual_duration,
                task.progress, json.dumps(task.metadata or {}), task.result, task.error_message
            ))
            await session.commit()

    async def get_execution_plan(self, goal_id: str) -> Optional[GoalExecutionPlan]:
        if goal_id in self.active_executions:
            return self.active_executions[goal_id]
        
        if not self.database:
            return None
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT goal_id, total_tasks, completed_tasks, failed_tasks, estimated_completion_time,
                       current_phase, agent_workload, critical_path, risk_factors, optimization_suggestions
                FROM goal_executions WHERE goal_id = %s
            """, (goal_id,))
            
            row = result.fetchone()
            if row:
                return GoalExecutionPlan(
                    goal_id=row[0],
                    total_tasks=row[1],
                    completed_tasks=row[2],
                    failed_tasks=row[3],
                    estimated_completion_time=row[4],
                    current_phase=row[5],
                    agent_workload=row[6] or {},
                    critical_path=row[7] or [],
                    risk_factors=row[8] or [],
                    optimization_suggestions=row[9] or []
                )
        
        return None

    async def update_task_status(self, task_id: str, new_status: TaskStatus, progress: float = None, result: str = None, error_message: str = None) -> bool:
        if not self.database:
            return False
        
        try:
            async with self.database.get_session() as session:
                update_fields = ["status = %s"]
                params = [new_status.value, task_id]
                
                if progress is not None:
                    update_fields.append("progress = %s")
                    params.insert(-1, progress)
                
                if new_status == TaskStatus.IN_PROGRESS:
                    update_fields.append("started_at = %s")
                    params.insert(-1, datetime.utcnow())
                elif new_status == TaskStatus.COMPLETED:
                    update_fields.append("completed_at = %s")
                    params.insert(-1, datetime.utcnow())
                    if result:
                        update_fields.append("result = %s")
                        params.insert(-1, result)
                
                if error_message:
                    update_fields.append("error_message = %s")
                    params.insert(-1, error_message)
                
                query = f"UPDATE agent_tasks SET {', '.join(update_fields)} WHERE id = %s"
                await session.execute(query, params)
                await session.commit()
                
                # Update execution plan if needed
                await self._update_execution_plan_progress(task_id, new_status)
                
                self.logger.info(f"Task {task_id} status updated to {new_status.value}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update task status: {str(e)}")
            return False

    async def _update_execution_plan_progress(self, task_id: str, new_status: TaskStatus):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                # Get task details
                result = await session.execute("""
                    SELECT goal_id FROM agent_tasks WHERE id = %s
                """, (task_id,))
                row = result.fetchone()
                if not row:
                    return
                
                goal_id = row[0]
                
                # Update execution plan
                if new_status == TaskStatus.COMPLETED:
                    await session.execute("""
                        UPDATE goal_executions 
                        SET completed_tasks = completed_tasks + 1, updated_at = %s
                        WHERE goal_id = %s
                    """, (datetime.utcnow(), goal_id))
                elif new_status == TaskStatus.FAILED:
                    await session.execute("""
                        UPDATE goal_executions 
                        SET failed_tasks = failed_tasks + 1, updated_at = %s
                        WHERE goal_id = %s
                    """, (datetime.utcnow(), goal_id))
                
                await session.commit()
                
                # Update local cache
                if goal_id in self.active_executions:
                    if new_status == TaskStatus.COMPLETED:
                        self.active_executions[goal_id].completed_tasks += 1
                    elif new_status == TaskStatus.FAILED:
                        self.active_executions[goal_id].failed_tasks += 1
                
        except Exception as e:
            self.logger.error(f"Failed to update execution plan progress: {str(e)}")

    async def get_agent_tasks(self, agent_name: str, status: Optional[TaskStatus] = None) -> List[AgentTask]:
        if not self.database:
            return []
        
        query = "SELECT * FROM agent_tasks WHERE agent_name = %s"
        params = [agent_name]
        
        if status:
            query += " AND status = %s"
            params.append(status.value)
        
        query += " ORDER BY assigned_at ASC"
        
        async with self.database.get_session() as session:
            result = await session.execute(query, params)
            rows = result.fetchall()
            
            tasks = []
            for row in result.fetchall():
                task = AgentTask(
                    id=row[0],
                    goal_id=row[1],
                    agent_name=row[2],
                    task_type=row[3],
                    description=row[4],
                    priority=TaskPriority(row[5]),
                    status=TaskStatus(row[6]),
                    assigned_at=row[7],
                    started_at=row[8],
                    completed_at=row[9],
                    estimated_duration=row[10],
                    actual_duration=row[11],
                    progress=float(row[12]) if row[12] else 0.0,
                    metadata=row[13] if row[13] else {},
                    result=row[14],
                    error_message=row[15]
                )
                tasks.append(task)
            
            return tasks

    async def optimize_execution_plan(self, goal_id: str) -> List[str]:
        execution_plan = await self.get_execution_plan(goal_id)
        if not execution_plan:
            return []
        
        optimizations = []
        
        # Check for workload imbalances
        if execution_plan.agent_workload:
            max_workload = max(execution_plan.agent_workload.values())
            min_workload = min(execution_plan.agent_workload.values())
            
            if max_workload - min_workload > 2:
                optimizations.append("Redistribute tasks to balance agent workload")
        
        # Check for timeline risks
        if execution_plan.estimated_completion_time:
            time_remaining = (execution_plan.estimated_completion_time - datetime.utcnow()).total_seconds() / 3600
            if time_remaining < 24:  # Less than 24 hours
                optimizations.append("Critical timeline - consider task prioritization and parallel execution")
        
        # Check for failure rates
        if execution_plan.total_tasks > 0:
            failure_rate = execution_plan.failed_tasks / execution_plan.total_tasks
            if failure_rate > 0.2:  # More than 20% failure rate
                optimizations.append("High failure rate - review task assignments and agent capabilities")
        
        return optimizations

    async def close(self):
        self.logger.info("Closing GoalEngine...")
        if self.database:
            await self.database.close()

# Global instances and initialization functions
_goal_engine: Optional[GoalEngine] = None

async def init_goal_engine() -> GoalEngine:
    global _goal_engine
    if not _goal_engine:
        _goal_engine = GoalEngine()
        await _goal_engine.initialize()
    return _goal_engine

async def get_goal_engine() -> GoalEngine:
    global _goal_engine
    if not _goal_engine:
        _goal_engine = await init_goal_engine()
    return _goal_engine
