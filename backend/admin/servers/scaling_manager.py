import asyncio
import subprocess
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text

from core.database import get_database, DatabaseManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class ScalingAction(Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    SCALE_OUT = "scale_out"
    SCALE_IN = "scale_in"
    NO_ACTION = "no_action"

class ScalingTrigger(Enum):
    CPU_THRESHOLD = "cpu_threshold"
    MEMORY_THRESHOLD = "memory_threshold"
    REQUEST_RATE = "request_rate"
    RESPONSE_TIME = "response_time"
    QUEUE_LENGTH = "queue_length"
    CUSTOM_METRIC = "custom_metric"
    MANUAL = "manual"
    SCHEDULED = "scheduled"

class ScalingStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ResourceType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    INSTANCES = "instances"
    REPLICAS = "replicas"
    NODES = "nodes"

@dataclass
class ScalingRule:
    rule_id: str
    name: str
    description: str
    trigger: ScalingTrigger
    resource_type: ResourceType
    threshold_value: float
    scaling_action: ScalingAction
    scaling_factor: float
    min_instances: int
    max_instances: int
    cooldown_minutes: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class ScalingEvent:
    event_id: str
    rule_id: str
    action: ScalingAction
    resource_type: ResourceType
    current_value: float
    target_value: float
    status: ScalingStatus
    triggered_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class ResourceMetrics:
    resource_id: str
    resource_type: ResourceType
    current_value: float
    target_value: float
    min_value: float
    max_value: float
    utilization_percent: float
    timestamp: datetime

class ScalingManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.scaling_rules: Dict[str, ScalingRule] = {}
        self.active_scaling_events: Dict[str, ScalingEvent] = {}
        self.resource_metrics: Dict[str, ResourceMetrics] = {}
        self.cooldown_timers: Dict[str, datetime] = {}
        self.monitoring_interval_seconds = 30
        self.scaling_timeout_minutes = 10
        self.max_concurrent_scaling_events = 3

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing ScalingManager...")
            self.database = get_database()
            await self._setup_scaling_tables()
            await self._load_scaling_rules()
            await self._start_scaling_monitor()
            self.logger.info("ScalingManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize ScalingManager: {str(e)}")
            return False

    async def _setup_scaling_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS scaling_rules (
                    id SERIAL PRIMARY KEY,
                    rule_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    trigger VARCHAR(50) NOT NULL,
                    resource_type VARCHAR(50) NOT NULL,
                    threshold_value FLOAT NOT NULL,
                    scaling_action VARCHAR(20) NOT NULL,
                    scaling_factor FLOAT NOT NULL,
                    min_instances INTEGER NOT NULL,
                    max_instances INTEGER NOT NULL,
                    cooldown_minutes INTEGER DEFAULT 5,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS scaling_events (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(255) UNIQUE NOT NULL,
                    rule_id VARCHAR(255) NOT NULL,
                    action VARCHAR(20) NOT NULL,
                    resource_type VARCHAR(50) NOT NULL,
                    current_value FLOAT NOT NULL,
                    target_value FLOAT NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    metadata JSONB,
                    FOREIGN KEY (rule_id) REFERENCES scaling_rules(rule_id)
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS resource_metrics (
                    id SERIAL PRIMARY KEY,
                    resource_id VARCHAR(255) NOT NULL,
                    resource_type VARCHAR(50) NOT NULL,
                    current_value FLOAT NOT NULL,
                    target_value FLOAT NOT NULL,
                    min_value FLOAT NOT NULL,
                    max_value FLOAT NOT NULL,
                    utilization_percent FLOAT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_scaling_rules_trigger 
                ON scaling_rules(trigger);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_scaling_rules_is_active 
                ON scaling_rules(is_active);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_scaling_events_rule_id 
                ON scaling_events(rule_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_scaling_events_status 
                ON scaling_events(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_scaling_events_triggered_at 
                ON scaling_events(triggered_at);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_resource_metrics_resource_id 
                ON resource_metrics(resource_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_resource_metrics_timestamp 
                ON resource_metrics(timestamp);
            """)
            
            await session.commit()

    async def _load_scaling_rules(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT rule_id, name, description, trigger, resource_type, threshold_value,
                       scaling_action, scaling_factor, min_instances, max_instances,
                       cooldown_minutes, is_active, created_at, updated_at
                FROM scaling_rules
                WHERE is_active = TRUE
            """)
            
            for row in result:
                rule = ScalingRule(
                    rule_id=row.rule_id,
                    name=row.name,
                    description=row.description,
                    trigger=ScalingTrigger(row.trigger),
                    resource_type=ResourceType(row.resource_type),
                    threshold_value=row.threshold_value,
                    scaling_action=ScalingAction(row.scaling_action),
                    scaling_factor=row.scaling_factor,
                    min_instances=row.min_instances,
                    max_instances=row.max_instances,
                    cooldown_minutes=row.cooldown_minutes,
                    is_active=row.is_active,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                self.scaling_rules[rule.rule_id] = rule

    async def _start_scaling_monitor(self):
        asyncio.create_task(self._scaling_monitor_loop())

    async def _scaling_monitor_loop(self):
        while True:
            try:
                await self._evaluate_scaling_rules()
                await asyncio.sleep(self.monitoring_interval_seconds)
            except Exception as e:
                self.logger.error(f"Error in scaling monitor: {str(e)}")
                await asyncio.sleep(60)

    async def create_scaling_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        trigger: ScalingTrigger,
        resource_type: ResourceType,
        threshold_value: float,
        scaling_action: ScalingAction,
        scaling_factor: float,
        min_instances: int,
        max_instances: int,
        cooldown_minutes: int = 5
    ) -> bool:
        try:
            if not self.database:
                return False
            
            rule = ScalingRule(
                rule_id=rule_id,
                name=name,
                description=description,
                trigger=trigger,
                resource_type=resource_type,
                threshold_value=threshold_value,
                scaling_action=scaling_action,
                scaling_factor=scaling_factor,
                min_instances=min_instances,
                max_instances=max_instances,
                cooldown_minutes=cooldown_minutes,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO scaling_rules (
                        rule_id, name, description, trigger, resource_type, threshold_value,
                        scaling_action, scaling_factor, min_instances, max_instances, cooldown_minutes
                    ) VALUES (
                        :rule_id, :name, :description, :trigger, :resource_type, :threshold_value,
                        :scaling_action, :scaling_factor, :min_instances, :max_instances, :cooldown_minutes
                    )
                """, {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "description": rule.description,
                    "trigger": rule.trigger.value,
                    "resource_type": rule.resource_type.value,
                    "threshold_value": rule.threshold_value,
                    "scaling_action": rule.scaling_action.value,
                    "scaling_factor": rule.scaling_factor,
                    "min_instances": rule.min_instances,
                    "max_instances": rule.max_instances,
                    "cooldown_minutes": rule.cooldown_minutes
                })
                await session.commit()
            
            self.scaling_rules[rule_id] = rule
            self.logger.info(f"Scaling rule created: {rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create scaling rule: {str(e)}")
            return False

    async def update_scaling_rule(
        self,
        rule_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        threshold_value: Optional[float] = None,
        scaling_factor: Optional[float] = None,
        min_instances: Optional[int] = None,
        max_instances: Optional[int] = None,
        cooldown_minutes: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        try:
            if rule_id not in self.scaling_rules:
                return False
            
            if not self.database:
                return False
            
            rule = self.scaling_rules[rule_id]
            
            if name is not None:
                rule.name = name
            if description is not None:
                rule.description = description
            if threshold_value is not None:
                rule.threshold_value = threshold_value
            if scaling_factor is not None:
                rule.scaling_factor = scaling_factor
            if min_instances is not None:
                rule.min_instances = min_instances
            if max_instances is not None:
                rule.max_instances = max_instances
            if cooldown_minutes is not None:
                rule.cooldown_minutes = cooldown_minutes
            if is_active is not None:
                rule.is_active = is_active
            
            rule.updated_at = datetime.utcnow()
            
            async with self.database.get_session() as session:
                update_fields = ["updated_at = :updated_at"]
                params = {"rule_id": rule_id, "updated_at": rule.updated_at}
                
                if name is not None:
                    update_fields.append("name = :name")
                    params["name"] = name
                if description is not None:
                    update_fields.append("description = :description")
                    params["description"] = description
                if threshold_value is not None:
                    update_fields.append("threshold_value = :threshold_value")
                    params["threshold_value"] = threshold_value
                if scaling_factor is not None:
                    update_fields.append("scaling_factor = :scaling_factor")
                    params["scaling_factor"] = scaling_factor
                if min_instances is not None:
                    update_fields.append("min_instances = :min_instances")
                    params["min_instances"] = min_instances
                if max_instances is not None:
                    update_fields.append("max_instances = :max_instances")
                    params["max_instances"] = max_instances
                if cooldown_minutes is not None:
                    update_fields.append("cooldown_minutes = :cooldown_minutes")
                    params["cooldown_minutes"] = cooldown_minutes
                if is_active is not None:
                    update_fields.append("is_active = :is_active")
                    params["is_active"] = is_active
                
                await session.execute(f"""
                    UPDATE scaling_rules 
                    SET {', '.join(update_fields)}
                    WHERE rule_id = :rule_id
                """, params)
                await session.commit()
            
            if not rule.is_active and rule_id in self.scaling_rules:
                del self.scaling_rules[rule_id]
            elif rule.is_active:
                self.scaling_rules[rule_id] = rule
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update scaling rule: {str(e)}")
            return False

    async def delete_scaling_rule(self, rule_id: str) -> bool:
        try:
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    DELETE FROM scaling_rules WHERE rule_id = :rule_id
                """, {"rule_id": rule_id})
                await session.commit()
            
            if rule_id in self.scaling_rules:
                del self.scaling_rules[rule_id]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete scaling rule: {str(e)}")
            return False

    async def _evaluate_scaling_rules(self):
        for rule_id, rule in self.scaling_rules.items():
            try:
                if not rule.is_active:
                    continue
                
                if rule_id in self.cooldown_timers:
                    if datetime.utcnow() < self.cooldown_timers[rule_id]:
                        continue
                    else:
                        del self.cooldown_timers[rule_id]
                
                if len(self.active_scaling_events) >= self.max_concurrent_scaling_events:
                    continue
                
                current_value = await self._get_current_metric_value(rule.trigger, rule.resource_type)
                if current_value is None:
                    continue
                
                should_scale = await self._should_trigger_scaling(rule, current_value)
                if should_scale:
                    await self._trigger_scaling_event(rule, current_value)
                    
            except Exception as e:
                self.logger.error(f"Error evaluating scaling rule {rule_id}: {str(e)}")

    async def _get_current_metric_value(self, trigger: ScalingTrigger, resource_type: ResourceType) -> Optional[float]:
        try:
            if trigger == ScalingTrigger.CPU_THRESHOLD:
                return await self._get_cpu_utilization()
            elif trigger == ScalingTrigger.MEMORY_THRESHOLD:
                return await self._get_memory_utilization()
            elif trigger == ScalingTrigger.REQUEST_RATE:
                return await self._get_request_rate()
            elif trigger == ScalingTrigger.RESPONSE_TIME:
                return await self._get_response_time()
            elif trigger == ScalingTrigger.QUEUE_LENGTH:
                return await self._get_queue_length()
            elif trigger == ScalingTrigger.CUSTOM_METRIC:
                return await self._get_custom_metric(resource_type)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get metric value: {str(e)}")
            return None

    async def _get_cpu_utilization(self) -> Optional[float]:
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            self.logger.error(f"Failed to get CPU utilization: {str(e)}")
            return None

    async def _get_memory_utilization(self) -> Optional[float]:
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.percent
        except Exception as e:
            self.logger.error(f"Failed to get memory utilization: {str(e)}")
            return None

    async def _get_request_rate(self) -> Optional[float]:
        try:
            if not self.database:
                return None
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT COUNT(*) as request_count
                    FROM request_logs
                    WHERE timestamp >= :start_time
                """, {"start_time": datetime.utcnow() - timedelta(minutes=1)})
                
                row = result.fetchone()
                return float(row.request_count) if row else 0.0
                
        except Exception as e:
            self.logger.error(f"Failed to get request rate: {str(e)}")
            return None

    async def _get_response_time(self) -> Optional[float]:
        try:
            if not self.database:
                return None
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT AVG(response_time) as avg_response_time
                    FROM request_logs
                    WHERE timestamp >= :start_time
                """, {"start_time": datetime.utcnow() - timedelta(minutes=5)})
                
                row = result.fetchone()
                return float(row.avg_response_time) if row and row.avg_response_time else 0.0
                
        except Exception as e:
            self.logger.error(f"Failed to get response time: {str(e)}")
            return None

    async def _get_queue_length(self) -> Optional[float]:
        try:
            if not self.database:
                return None
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT COUNT(*) as queue_length
                    FROM task_queue
                    WHERE status = 'pending'
                """)
                
                row = result.fetchone()
                return float(row.queue_length) if row else 0.0
                
        except Exception as e:
            self.logger.error(f"Failed to get queue length: {str(e)}")
            return None

    async def _get_custom_metric(self, resource_type: ResourceType) -> Optional[float]:
        try:
            resource_id = f"{resource_type.value}_metric"
            if resource_id in self.resource_metrics:
                return self.resource_metrics[resource_id].current_value
            return None
        except Exception as e:
            self.logger.error(f"Failed to get custom metric: {str(e)}")
            return None

    async def _should_trigger_scaling(self, rule: ScalingRule, current_value: float) -> bool:
        try:
            if rule.scaling_action in [ScalingAction.SCALE_UP, ScalingAction.SCALE_OUT]:
                return current_value >= rule.threshold_value
            elif rule.scaling_action in [ScalingAction.SCALE_DOWN, ScalingAction.SCALE_IN]:
                return current_value <= rule.threshold_value
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate scaling condition: {str(e)}")
            return False

    async def _trigger_scaling_event(self, rule: ScalingRule, current_value: float):
        try:
            event_id = f"scale_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(rule.rule_id) % 10000}"
            
            current_instances = await self._get_current_instance_count(rule.resource_type)
            target_instances = await self._calculate_target_instances(rule, current_instances)
            
            if target_instances == current_instances:
                return
            
            event = ScalingEvent(
                event_id=event_id,
                rule_id=rule.rule_id,
                action=rule.scaling_action,
                resource_type=rule.resource_type,
                current_value=current_value,
                target_value=target_instances,
                status=ScalingStatus.PENDING,
                triggered_at=datetime.utcnow(),
                completed_at=None,
                error_message=None,
                metadata={"current_instances": current_instances, "target_instances": target_instances}
            )
            
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO scaling_events (
                        event_id, rule_id, action, resource_type, current_value,
                        target_value, status, metadata
                    ) VALUES (
                        :event_id, :rule_id, :action, :resource_type, :current_value,
                        :target_value, :status, :metadata
                    )
                """, {
                    "event_id": event.event_id,
                    "rule_id": event.rule_id,
                    "action": event.action.value,
                    "resource_type": event.resource_type.value,
                    "current_value": event.current_value,
                    "target_value": event.target_value,
                    "status": event.status.value,
                    "metadata": event.metadata
                })
                await session.commit()
            
            self.active_scaling_events[event_id] = event
            self.cooldown_timers[rule.rule_id] = datetime.utcnow() + timedelta(minutes=rule.cooldown_minutes)
            
            asyncio.create_task(self._execute_scaling_event(event))
            
        except Exception as e:
            self.logger.error(f"Failed to trigger scaling event: {str(e)}")

    async def _get_current_instance_count(self, resource_type: ResourceType) -> int:
        try:
            if resource_type == ResourceType.INSTANCES:
                return await self._get_application_instances()
            elif resource_type == ResourceType.REPLICAS:
                return await self._get_replica_count()
            elif resource_type == ResourceType.NODES:
                return await self._get_node_count()
            else:
                return 1
        except Exception as e:
            self.logger.error(f"Failed to get current instance count: {str(e)}")
            return 1

    async def _get_application_instances(self) -> int:
        try:
            result = subprocess.run(
                ["kubectl", "get", "deployment", "app", "-o", "jsonpath={.spec.replicas}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return int(result.stdout) if result.returncode == 0 else 1
        except Exception as e:
            self.logger.error(f"Failed to get application instances: {str(e)}")
            return 1

    async def _get_replica_count(self) -> int:
        try:
            result = subprocess.run(
                ["kubectl", "get", "replicaset", "-o", "jsonpath={.items[*].spec.replicas}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                replicas = result.stdout.split()
                return sum(int(r) for r in replicas if r.isdigit())
            return 1
        except Exception as e:
            self.logger.error(f"Failed to get replica count: {str(e)}")
            return 1

    async def _get_node_count(self) -> int:
        try:
            result = subprocess.run(
                ["kubectl", "get", "nodes", "--no-headers"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return len(result.stdout.strip().split('\n'))
            return 1
        except Exception as e:
            self.logger.error(f"Failed to get node count: {str(e)}")
            return 1

    async def _calculate_target_instances(self, rule: ScalingRule, current_instances: int) -> int:
        try:
            if rule.scaling_action in [ScalingAction.SCALE_UP, ScalingAction.SCALE_OUT]:
                target = int(current_instances * rule.scaling_factor)
            elif rule.scaling_action in [ScalingAction.SCALE_DOWN, ScalingAction.SCALE_IN]:
                target = int(current_instances / rule.scaling_factor)
            else:
                target = current_instances
            
            return max(rule.min_instances, min(rule.max_instances, target))
            
        except Exception as e:
            self.logger.error(f"Failed to calculate target instances: {str(e)}")
            return current_instances

    async def _execute_scaling_event(self, event: ScalingEvent):
        try:
            event.status = ScalingStatus.IN_PROGRESS
            
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE scaling_events 
                    SET status = :status
                    WHERE event_id = :event_id
                """, {
                    "event_id": event.event_id,
                    "status": event.status.value
                })
                await session.commit()
            
            success = await self._perform_scaling_action(event)
            
            if success:
                event.status = ScalingStatus.COMPLETED
                event.completed_at = datetime.utcnow()
            else:
                event.status = ScalingStatus.FAILED
                event.error_message = "Scaling action failed"
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE scaling_events 
                    SET status = :status, completed_at = :completed_at, error_message = :error_message
                    WHERE event_id = :event_id
                """, {
                    "event_id": event.event_id,
                    "status": event.status.value,
                    "completed_at": event.completed_at,
                    "error_message": event.error_message
                })
                await session.commit()
            
            if event.event_id in self.active_scaling_events:
                del self.active_scaling_events[event.event_id]
            
            self.logger.info(f"Scaling event completed: {event.event_id} - {event.status.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to execute scaling event: {str(e)}")
            await self._mark_scaling_event_failed(event.event_id, str(e))

    async def _perform_scaling_action(self, event: ScalingEvent) -> bool:
        try:
            if event.resource_type == ResourceType.INSTANCES:
                return await self._scale_application_instances(event)
            elif event.resource_type == ResourceType.REPLICAS:
                return await self._scale_replicas(event)
            elif event.resource_type == ResourceType.NODES:
                return await self._scale_nodes(event)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to perform scaling action: {str(e)}")
            return False

    async def _scale_application_instances(self, event: ScalingEvent) -> bool:
        try:
            result = subprocess.run(
                ["kubectl", "scale", "deployment", "app", f"--replicas={int(event.target_value)}"],
                capture_output=True,
                text=True,
                timeout=self.scaling_timeout_minutes * 60
            )
            
            if result.returncode == 0:
                self.logger.info(f"Scaled application instances to {int(event.target_value)}")
                return True
            else:
                self.logger.error(f"Failed to scale application instances: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Scaling operation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to scale application instances: {str(e)}")
            return False

    async def _scale_replicas(self, event: ScalingEvent) -> bool:
        try:
            result = subprocess.run(
                ["kubectl", "scale", "replicaset", "app", f"--replicas={int(event.target_value)}"],
                capture_output=True,
                text=True,
                timeout=self.scaling_timeout_minutes * 60
            )
            
            if result.returncode == 0:
                self.logger.info(f"Scaled replicas to {int(event.target_value)}")
                return True
            else:
                self.logger.error(f"Failed to scale replicas: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Scaling operation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to scale replicas: {str(e)}")
            return False

    async def _scale_nodes(self, event: ScalingEvent) -> bool:
        try:
            if event.action == ScalingAction.SCALE_OUT:
                result = subprocess.run(
                    ["kubectl", "create", "node", f"node-{int(event.target_value)}"],
                    capture_output=True,
                    text=True,
                    timeout=self.scaling_timeout_minutes * 60
                )
            else:
                result = subprocess.run(
                    ["kubectl", "delete", "node", f"node-{int(event.target_value)}"],
                    capture_output=True,
                    text=True,
                    timeout=self.scaling_timeout_minutes * 60
                )
            
            if result.returncode == 0:
                self.logger.info(f"Scaled nodes to {int(event.target_value)}")
                return True
            else:
                self.logger.error(f"Failed to scale nodes: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Scaling operation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to scale nodes: {str(e)}")
            return False

    async def _mark_scaling_event_failed(self, event_id: str, error_message: str):
        try:
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE scaling_events 
                    SET status = :status, completed_at = :completed_at, error_message = :error_message
                    WHERE event_id = :event_id
                """, {
                    "event_id": event_id,
                    "status": ScalingStatus.FAILED.value,
                    "completed_at": datetime.utcnow(),
                    "error_message": error_message
                })
                await session.commit()
            
            if event_id in self.active_scaling_events:
                del self.active_scaling_events[event_id]
                
        except Exception as e:
            self.logger.error(f"Failed to mark scaling event as failed: {str(e)}")

    async def get_scaling_rules(
        self,
        is_active: Optional[bool] = None,
        trigger: Optional[ScalingTrigger] = None,
        resource_type: Optional[ResourceType] = None
    ) -> List[ScalingRule]:
        if not self.database:
            return []
        
        conditions = []
        params = {}
        
        if is_active is not None:
            conditions.append("is_active = :is_active")
            params["is_active"] = is_active
        
        if trigger:
            conditions.append("trigger = :trigger")
            params["trigger"] = trigger.value
        
        if resource_type:
            conditions.append("resource_type = :resource_type")
            params["resource_type"] = resource_type.value
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT rule_id, name, description, trigger, resource_type, threshold_value,
                       scaling_action, scaling_factor, min_instances, max_instances,
                       cooldown_minutes, is_active, created_at, updated_at
                FROM scaling_rules
                {where_clause}
                ORDER BY created_at DESC
            """, params)
            
            rules = []
            for row in result:
                rule = ScalingRule(
                    rule_id=row.rule_id,
                    name=row.name,
                    description=row.description,
                    trigger=ScalingTrigger(row.trigger),
                    resource_type=ResourceType(row.resource_type),
                    threshold_value=row.threshold_value,
                    scaling_action=ScalingAction(row.scaling_action),
                    scaling_factor=row.scaling_factor,
                    min_instances=row.min_instances,
                    max_instances=row.max_instances,
                    cooldown_minutes=row.cooldown_minutes,
                    is_active=row.is_active,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                rules.append(rule)
            
            return rules

    async def get_scaling_events(
        self,
        rule_id: Optional[str] = None,
        status: Optional[ScalingStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ScalingEvent]:
        if not self.database:
            return []
        
        conditions = []
        params = {"limit": limit}
        
        if rule_id:
            conditions.append("rule_id = :rule_id")
            params["rule_id"] = rule_id
        
        if status:
            conditions.append("status = :status")
            params["status"] = status.value
        
        if start_date:
            conditions.append("triggered_at >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            conditions.append("triggered_at <= :end_date")
            params["end_date"] = end_date
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT event_id, rule_id, action, resource_type, current_value, target_value,
                       status, triggered_at, completed_at, error_message, metadata
                FROM scaling_events
                {where_clause}
                ORDER BY triggered_at DESC
                LIMIT :limit
            """, params)
            
            events = []
            for row in result:
                event = ScalingEvent(
                    event_id=row.event_id,
                    rule_id=row.rule_id,
                    action=ScalingAction(row.action),
                    resource_type=ResourceType(row.resource_type),
                    current_value=row.current_value,
                    target_value=row.target_value,
                    status=ScalingStatus(row.status),
                    triggered_at=row.triggered_at,
                    completed_at=row.completed_at,
                    error_message=row.error_message,
                    metadata=row.metadata or {}
                )
                events.append(event)
            
            return events

    async def get_scaling_stats(
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
                    COUNT(*) as total_events,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_events,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_events,
                    COUNT(CASE WHEN action = 'scale_up' THEN 1 END) as scale_up_events,
                    COUNT(CASE WHEN action = 'scale_down' THEN 1 END) as scale_down_events,
                    COUNT(CASE WHEN action = 'scale_out' THEN 1 END) as scale_out_events,
                    COUNT(CASE WHEN action = 'scale_in' THEN 1 END) as scale_in_events,
                    AVG(EXTRACT(EPOCH FROM (completed_at - triggered_at))/60) as avg_duration_minutes
                FROM scaling_events
                WHERE triggered_at BETWEEN :start_date AND :end_date
                AND completed_at IS NOT NULL
            """, {"start_date": start_date, "end_date": end_date})
            
            row = result.fetchone()
            if not row:
                return {}
            
            return {
                "total_events": row.total_events,
                "successful_events": row.successful_events,
                "failed_events": row.failed_events,
                "scale_up_events": row.scale_up_events,
                "scale_down_events": row.scale_down_events,
                "scale_out_events": row.scale_out_events,
                "scale_in_events": row.scale_in_events,
                "avg_duration_minutes": float(row.avg_duration_minutes) if row.avg_duration_minutes else 0.0,
                "success_rate": (row.successful_events / row.total_events * 100) if row.total_events > 0 else 0
            }

    async def update_resource_metrics(
        self,
        resource_id: str,
        resource_type: ResourceType,
        current_value: float,
        target_value: float,
        min_value: float,
        max_value: float
    ):
        try:
            utilization_percent = ((current_value - min_value) / (max_value - min_value)) * 100 if max_value > min_value else 0
            
            metrics = ResourceMetrics(
                resource_id=resource_id,
                resource_type=resource_type,
                current_value=current_value,
                target_value=target_value,
                min_value=min_value,
                max_value=max_value,
                utilization_percent=utilization_percent,
                timestamp=datetime.utcnow()
            )
            
            self.resource_metrics[resource_id] = metrics
            
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO resource_metrics (
                        resource_id, resource_type, current_value, target_value,
                        min_value, max_value, utilization_percent
                    ) VALUES (
                        :resource_id, :resource_type, :current_value, :target_value,
                        :min_value, :max_value, :utilization_percent
                    )
                """, {
                    "resource_id": metrics.resource_id,
                    "resource_type": metrics.resource_type.value,
                    "current_value": metrics.current_value,
                    "target_value": metrics.target_value,
                    "min_value": metrics.min_value,
                    "max_value": metrics.max_value,
                    "utilization_percent": metrics.utilization_percent
                })
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to update resource metrics: {str(e)}")

_scaling_manager: Optional[ScalingManager] = None

async def get_scaling_manager() -> ScalingManager:
    global _scaling_manager
    if _scaling_manager is None:
        _scaling_manager = ScalingManager()
        await _scaling_manager.initialize()
    return _scaling_manager

async def init_scaling_manager() -> ScalingManager:
    return await get_scaling_manager()
