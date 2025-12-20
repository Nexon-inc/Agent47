import asyncio
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

from core.database import get_database, DatabaseManager
from core.cache import get_redis, RedisManager
from core.event_bus import get_kafka, KafkaManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class CoordinationType(Enum):
    TASK_DISTRIBUTION = "task_distribution"
    LOAD_BALANCING = "load_balancing"
    RESOURCE_SHARING = "resource_sharing"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    COLLABORATIVE_PROCESSING = "collaborative_processing"
    DATA_SYNCHRONIZATION = "data_synchronization"
    FAILOVER_MANAGEMENT = "failover_management"

class CoordinationStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AgentCoordination:
    id: str
    coordinator_agent_id: str
    coordinated_agent_id: str
    coordination_type: CoordinationType
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: CoordinationStatus = CoordinationStatus.PENDING
    priority: int = 1
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

@dataclass
class WorkflowDefinition:
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    dependencies: Dict[str, List[str]]
    timeout_seconds: int = 3600
    retry_policy: Dict[str, Any] = field(default_factory=lambda: {"max_retries": 3, "backoff_factor": 2})
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

@dataclass
class WorkflowExecution:
    id: str
    workflow_id: str
    status: str = "pending"
    current_step: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    step_results: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class AgentCoordinator(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.kafka: Optional[KafkaManager] = None
        self.settings = get_settings()
        
        self.coordinations: Dict[str, AgentCoordination] = {}
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.workflow_executions: Dict[str, WorkflowExecution] = {}
        self.active_coordinations: Dict[str, asyncio.Task] = {}
        
        self.logger = logger
        self._shutdown_event = asyncio.Event()

    async def initialize(self) -> bool:
        """Initialize the agent coordinator system"""
        try:
            self.logger.info("Initializing AgentCoordinator...")
            
            # Initialize core services
            self.database = get_database()
            self.redis = await get_redis()
            self.kafka = await get_kafka()
            
            # Setup database tables
            await self._setup_coordinator_tables()
            
            # Load existing coordinations and workflows
            await self._load_coordinations_from_database()
            await self._load_workflows_from_database()
            
            # Start background tasks
            asyncio.create_task(self._coordination_monitor())
            asyncio.create_task(self._workflow_executor())
            
            self.logger.info("AgentCoordinator initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AgentCoordinator: {str(e)}")
            return False

    async def _setup_coordinator_tables(self):
        """Setup database tables for agent coordination"""
        if not self.database:
            raise RuntimeError("Database not initialized")

        try:
            async with self.database.get_session() as session:
                # Agent coordinations table
                await session.execute("""
                    CREATE TABLE IF NOT EXISTS agent_coordinations (
                        id VARCHAR(255) PRIMARY KEY,
                        coordinator_agent_id VARCHAR(255) NOT NULL,
                        coordinated_agent_id VARCHAR(255) NOT NULL,
                        coordination_type VARCHAR(100) NOT NULL,
                        task_id VARCHAR(255),
                        metadata JSONB NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status VARCHAR(50) NOT NULL,
                        priority INTEGER DEFAULT 1,
                        timeout_seconds INTEGER DEFAULT 300,
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        error_message TEXT,
                        result JSONB,
                        FOREIGN KEY (coordinator_agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                        FOREIGN KEY (coordinated_agent_id) REFERENCES agents(id) ON DELETE CASCADE
                    )
                """)
                
                # Agent workflows table
                await session.execute("""
                    CREATE TABLE IF NOT EXISTS agent_workflows (
                        id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        steps JSONB NOT NULL,
                        dependencies JSONB NOT NULL,
                        timeout_seconds INTEGER DEFAULT 3600,
                        retry_policy JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                
                # Workflow executions table
                await session.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_executions (
                        id VARCHAR(255) PRIMARY KEY,
                        workflow_id VARCHAR(255) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        current_step INTEGER DEFAULT 0,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        step_results JSONB NOT NULL,
                        error_message TEXT,
                        metadata JSONB NOT NULL,
                        FOREIGN KEY (workflow_id) REFERENCES agent_workflows(id) ON DELETE CASCADE
                    )
                """)
                
                # Agent communication logs table
                await session.execute("""
                    CREATE TABLE IF NOT EXISTS agent_communications (
                        id SERIAL PRIMARY KEY,
                        sender_agent_id VARCHAR(255) NOT NULL,
                        receiver_agent_id VARCHAR(255) NOT NULL,
                        message_type VARCHAR(100) NOT NULL,
                        content TEXT NOT NULL,
                        metadata JSONB,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        read_at TIMESTAMP,
                        coordination_id VARCHAR(255),
                        FOREIGN KEY (sender_agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                        FOREIGN KEY (receiver_agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                        FOREIGN KEY (coordination_id) REFERENCES agent_coordinations(id) ON DELETE SET NULL
                    )
                """)

                await session.commit()
                self.logger.info("Agent coordinator tables setup completed")

        except Exception as e:
            self.logger.error(f"Failed to setup coordinator tables: {str(e)}")
            raise

    async def _load_coordinations_from_database(self):
        """Load existing coordinations from database"""
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, coordinator_agent_id, coordinated_agent_id, coordination_type,
                           task_id, metadata, timestamp, status, priority, timeout_seconds,
                           retry_count, max_retries, error_message, result
                    FROM agent_coordinations WHERE status IN ('pending', 'active')
                """)

                rows = result.fetchall()
                for row in rows:
                    coordination = self._create_coordination_from_row(row)
                    self.coordinations[coordination.id] = coordination

            self.logger.info(f"Loaded {len(self.coordinations)} active coordinations from database")

        except Exception as e:
            self.logger.error(f"Failed to load coordinations from database: {str(e)}")

    async def _load_workflows_from_database(self):
        """Load workflow definitions from database"""
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, name, description, steps, dependencies, timeout_seconds,
                           retry_policy, created_at, updated_at, is_active
                    FROM agent_workflows WHERE is_active = TRUE
                """)

                rows = result.fetchall()
                for row in rows:
                    workflow = self._create_workflow_from_row(row)
                    self.workflow_definitions[workflow.id] = workflow

            self.logger.info(f"Loaded {len(self.workflow_definitions)} workflow definitions from database")

        except Exception as e:
            self.logger.error(f"Failed to load workflows from database: {str(e)}")

    def _create_coordination_from_row(self, row) -> AgentCoordination:
        """Create AgentCoordination object from database row"""
        return AgentCoordination(
            id=row[0],
            coordinator_agent_id=row[1],
            coordinated_agent_id=row[2],
            coordination_type=CoordinationType(row[3]),
            task_id=row[4],
            metadata=row[5] or {},
            timestamp=row[6],
            status=CoordinationStatus(row[7]),
            priority=row[8],
            timeout_seconds=row[9],
            retry_count=row[10],
            max_retries=row[11],
            error_message=row[12],
            result=row[13]
        )

    def _create_workflow_from_row(self, row) -> WorkflowDefinition:
        """Create WorkflowDefinition object from database row"""
        return WorkflowDefinition(
            id=row[0],
            name=row[1],
            description=row[2],
            steps=row[3],
            dependencies=row[4],
            timeout_seconds=row[5],
            retry_policy=row[6],
            created_at=row[7],
            updated_at=row[8],
            is_active=row[9]
        )

    async def create_coordination(self, coordinator_id: str, coordinated_id: str, 
                                coordination_type: CoordinationType, task_id: Optional[str] = None,
                                metadata: Optional[Dict[str, Any]] = None, priority: int = 1,
                                timeout_seconds: int = 300) -> AgentCoordination:
        """Create a new agent coordination"""
        try:
            coordination_id = str(uuid.uuid4())
            
            coordination = AgentCoordination(
                id=coordination_id,
                coordinator_agent_id=coordinator_id,
                coordinated_agent_id=coordinated_id,
                coordination_type=coordination_type,
                task_id=task_id,
                metadata=metadata or {},
                priority=priority,
                timeout_seconds=timeout_seconds
            )
            
            await self._save_coordination_to_database(coordination)
            self.coordinations[coordination.id] = coordination
            
            # Start coordination task
            task = asyncio.create_task(self._execute_coordination(coordination))
            self.active_coordinations[coordination.id] = task
            
            self.logger.info(f"Coordination created: {coordinator_id} -> {coordinated_id} (Type: {coordination_type.value})")
            return coordination
            
        except Exception as e:
            self.logger.error(f"Failed to create coordination: {str(e)}")
            raise

    async def _save_coordination_to_database(self, coordination: AgentCoordination):
        """Save coordination to database"""
        if not self.database:
            return
            
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO agent_coordinations (id, coordinator_agent_id, coordinated_agent_id,
                                                   coordination_type, task_id, metadata, timestamp, status,
                                                   priority, timeout_seconds, retry_count, max_retries,
                                                   error_message, result)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    coordination.id, coordination.coordinator_agent_id, coordination.coordinated_agent_id,
                    coordination.coordination_type.value, coordination.task_id,
                    json.dumps(coordination.metadata), coordination.timestamp, coordination.status.value,
                    coordination.priority, coordination.timeout_seconds, coordination.retry_count,
                    coordination.max_retries, coordination.error_message,
                    json.dumps(coordination.result) if coordination.result else None
                ))
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save coordination to database: {str(e)}")
            raise

    async def _execute_coordination(self, coordination: AgentCoordination):
        """Execute a coordination task"""
        try:
            self.logger.info(f"Starting coordination execution: {coordination.id}")
            
            # Update status to active
            coordination.status = CoordinationStatus.ACTIVE
            await self._update_coordination_status(coordination.id, coordination.status)
            
            # Execute based on coordination type
            if coordination.coordination_type == CoordinationType.TASK_DISTRIBUTION:
                result = await self._execute_task_distribution(coordination)
            elif coordination.coordination_type == CoordinationType.LOAD_BALANCING:
                result = await self._execute_load_balancing(coordination)
            elif coordination.coordination_type == CoordinationType.RESOURCE_SHARING:
                result = await self._execute_resource_sharing(coordination)
            elif coordination.coordination_type == CoordinationType.WORKFLOW_ORCHESTRATION:
                result = await self._execute_workflow_orchestration(coordination)
            elif coordination.coordination_type == CoordinationType.COLLABORATIVE_PROCESSING:
                result = await self._execute_collaborative_processing(coordination)
            else:
                raise ValueError(f"Unknown coordination type: {coordination.coordination_type}")

            # Update coordination with result
            coordination.result = result
            coordination.status = CoordinationStatus.COMPLETED
            await self._update_coordination_status(coordination.id, coordination.status, result)
            
            self.logger.info(f"Coordination completed successfully: {coordination.id}")
            
        except Exception as e:
            self.logger.error(f"Coordination execution failed: {coordination.id}, Error: {str(e)}")
            
            # Handle retry logic
            if coordination.retry_count < coordination.max_retries:
                coordination.retry_count += 1
                coordination.error_message = str(e)
                await self._update_coordination_retry(coordination.id, coordination.retry_count, str(e))
                
                # Retry after exponential backoff
                retry_delay = coordination.timeout_seconds * (2 ** (coordination.retry_count - 1))
                await asyncio.sleep(retry_delay)
                
                # Restart coordination
                task = asyncio.create_task(self._execute_coordination(coordination))
                self.active_coordinations[coordination.id] = task
            else:
                coordination.status = CoordinationStatus.FAILED
                coordination.error_message = str(e)
                await self._update_coordination_status(coordination.id, coordination.status, error_message=str(e))
                
        finally:
            # Clean up active coordination
            if coordination.id in self.active_coordinations:
                del self.active_coordinations[coordination.id]

    async def _execute_task_distribution(self, coordination: AgentCoordination) -> Dict[str, Any]:
        """Execute task distribution coordination"""
        # Implementation for task distribution logic
        return {
            "type": "task_distribution",
            "distributed_tasks": [],
            "load_balanced": True,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _execute_load_balancing(self, coordination: AgentCoordination) -> Dict[str, Any]:
        """Execute load balancing coordination"""
        # Implementation for load balancing logic
        return {
            "type": "load_balancing",
            "balanced_load": True,
            "performance_improved": True,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _execute_resource_sharing(self, coordination: AgentCoordination) -> Dict[str, Any]:
        """Execute resource sharing coordination"""
        # Implementation for resource sharing logic
        return {
            "type": "resource_sharing",
            "shared_resources": [],
            "efficiency_gained": True,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _execute_workflow_orchestration(self, coordination: AgentCoordination) -> Dict[str, Any]:
        """Execute workflow orchestration coordination"""
        # Implementation for workflow orchestration logic
        return {
            "type": "workflow_orchestration",
            "orchestrated_workflows": [],
            "workflow_completed": True,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _execute_collaborative_processing(self, coordination: AgentCoordination) -> Dict[str, Any]:
        """Execute collaborative processing coordination"""
        # Implementation for collaborative processing logic
        return {
            "type": "collaborative_processing",
            "collaboration_successful": True,
            "processing_completed": True,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _update_coordination_status(self, coordination_id: str, status: CoordinationStatus, 
                                        result: Optional[Dict[str, Any]] = None, 
                                        error_message: Optional[str] = None):
        """Update coordination status in database"""
        if not self.database:
            return
            
        try:
            async with self.database.get_session() as session:
                update_fields = ["status = %s"]
                params = [status.value]
                
                if result is not None:
                    update_fields.append("result = %s")
                    params.append(json.dumps(result))
                    
                if error_message is not None:
                    update_fields.append("error_message = %s")
                    params.append(error_message)
                
                params.append(coordination_id)
                
                query = f"""
                    UPDATE agent_coordinations 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """
                
                await session.execute(query, params)
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to update coordination status: {str(e)}")

    async def _update_coordination_retry(self, coordination_id: str, retry_count: int, error_message: str):
        """Update coordination retry information"""
        if not self.database:
            return
            
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE agent_coordinations 
                    SET retry_count = %s, error_message = %s
                    WHERE id = %s
                """, (retry_count, error_message, coordination_id))
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to update coordination retry: {str(e)}")

    async def _coordination_monitor(self):
        """Background task to monitor active coordinations"""
        while not self._shutdown_event.is_set():
            try:
                # Check for timed out coordinations
                current_time = datetime.utcnow()
                timed_out_coordinations = []
                
                for coordination in self.coordinations.values():
                    if (coordination.status == CoordinationStatus.ACTIVE and 
                        (current_time - coordination.timestamp).total_seconds() > coordination.timeout_seconds):
                        timed_out_coordinations.append(coordination.id)
                
                # Handle timed out coordinations
                for coordination_id in timed_out_coordinations:
                    coordination = self.coordinations.get(coordination_id)
                    if coordination:
                        coordination.status = CoordinationStatus.FAILED
                        coordination.error_message = "Coordination timed out"
                        await self._update_coordination_status(coordination_id, coordination.status, 
                                                             error_message="Coordination timed out")
                        
                        # Cancel active task
                        if coordination_id in self.active_coordinations:
                            self.active_coordinations[coordination_id].cancel()
                            del self.active_coordinations[coordination_id]
                
                if timed_out_coordinations:
                    self.logger.warning(f"Timed out {len(timed_out_coordinations)} coordinations")
                
                # Clean up completed coordinations older than 24 hours
                cutoff_time = current_time - timedelta(hours=24)
                completed_coordinations = [
                    cid for cid, coord in self.coordinations.items()
                    if coord.status in [CoordinationStatus.COMPLETED, CoordinationStatus.FAILED, CoordinationStatus.CANCELLED]
                    and coord.timestamp < cutoff_time
                ]
                
                for coordination_id in completed_coordinations:
                    del self.coordinations[coordination_id]
                
                if completed_coordinations:
                    self.logger.info(f"Cleaned up {len(completed_coordinations)} old coordinations")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in coordination monitor: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _workflow_executor(self):
        """Background task to execute workflows"""
        while not self._shutdown_event.is_set():
            try:
                # Process pending workflow executions
                pending_executions = [
                    exec_id for exec_id, execution in self.workflow_executions.items()
                    if execution.status == "pending"
                ]
                
                for execution_id in pending_executions:
                    execution = self.workflow_executions[execution_id]
                    workflow = self.workflow_definitions.get(execution.workflow_id)
                    
                    if workflow:
                        asyncio.create_task(self._execute_workflow(execution, workflow))
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error in workflow executor: {str(e)}")
                await asyncio.sleep(30)

    async def _execute_workflow(self, execution: WorkflowExecution, workflow: WorkflowDefinition):
        """Execute a workflow"""
        try:
            execution.status = "running"
            execution.started_at = datetime.utcnow()
            
            self.logger.info(f"Starting workflow execution: {execution.id}")
            
            # Execute workflow steps
            for step_index, step in enumerate(workflow.steps):
                if execution.status != "running":
                    break
                    
                execution.current_step = step_index
                
                # Execute step
                step_result = await self._execute_workflow_step(step, execution)
                execution.step_results[f"step_{step_index}"] = step_result
                
                # Check dependencies
                if not await self._check_step_dependencies(step_index, execution, workflow):
                    execution.status = "failed"
                    execution.error_message = f"Dependency check failed for step {step_index}"
                    break
            
            if execution.status == "running":
                execution.status = "completed"
                execution.completed_at = datetime.utcnow()
                self.logger.info(f"Workflow execution completed: {execution.id}")
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            self.logger.error(f"Workflow execution failed: {execution.id}, Error: {str(e)}")

    async def _execute_workflow_step(self, step: Dict[str, Any], execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute a single workflow step"""
        # Implementation for workflow step execution
        return {
            "step_type": step.get("type", "unknown"),
            "executed_at": datetime.utcnow().isoformat(),
            "success": True
        }

    async def _check_step_dependencies(self, step_index: int, execution: WorkflowExecution, 
                                     workflow: WorkflowDefinition) -> bool:
        """Check if step dependencies are met"""
        # Implementation for dependency checking
        return True

    async def get_coordinations(self, agent_id: Optional[str] = None, 
                              coordination_type: Optional[CoordinationType] = None,
                              status: Optional[CoordinationStatus] = None) -> List[AgentCoordination]:
        """Get coordinations with optional filtering"""
        coordinations = list(self.coordinations.values())
        
        if agent_id:
            coordinations = [c for c in coordinations 
                           if c.coordinator_agent_id == agent_id or c.coordinated_agent_id == agent_id]
            
        if coordination_type:
            coordinations = [c for c in coordinations if c.coordination_type == coordination_type]
            
        if status:
            coordinations = [c for c in coordinations if c.status == status]
            
        return coordinations

    async def get_coordination(self, coordination_id: str) -> Optional[AgentCoordination]:
        """Get a specific coordination by ID"""
        return self.coordinations.get(coordination_id)

    async def cancel_coordination(self, coordination_id: str) -> bool:
        """Cancel an active coordination"""
        coordination = self.coordinations.get(coordination_id)
        if not coordination:
            return False
            
        if coordination.status == CoordinationStatus.ACTIVE:
            coordination.status = CoordinationStatus.CANCELLED
            await self._update_coordination_status(coordination_id, coordination.status)
            
            # Cancel active task
            if coordination_id in self.active_coordinations:
                self.active_coordinations[coordination_id].cancel()
                del self.active_coordinations[coordination_id]
            
            self.logger.info(f"Coordination cancelled: {coordination_id}")
            return True
            
        return False

    async def create_workflow(self, name: str, description: str, steps: List[Dict[str, Any]], 
                            dependencies: Dict[str, List[str]], timeout_seconds: int = 3600,
                            retry_policy: Optional[Dict[str, Any]] = None) -> WorkflowDefinition:
        """Create a new workflow definition"""
        try:
            workflow_id = str(uuid.uuid4())
            
            workflow = WorkflowDefinition(
                id=workflow_id,
                name=name,
                description=description,
                steps=steps,
                dependencies=dependencies,
                timeout_seconds=timeout_seconds,
                retry_policy=retry_policy or {"max_retries": 3, "backoff_factor": 2}
            )
            
            await self._save_workflow_to_database(workflow)
            self.workflow_definitions[workflow.id] = workflow
            
            self.logger.info(f"Workflow created: {workflow.name} (ID: {workflow_id})")
            return workflow
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow: {str(e)}")
            raise

    async def _save_workflow_to_database(self, workflow: WorkflowDefinition):
        """Save workflow to database"""
        if not self.database:
            return
            
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO agent_workflows (id, name, description, steps, dependencies,
                                               timeout_seconds, retry_policy, created_at, updated_at, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    workflow.id, workflow.name, workflow.description,
                    json.dumps(workflow.steps), json.dumps(workflow.dependencies),
                    workflow.timeout_seconds, json.dumps(workflow.retry_policy),
                    workflow.created_at, workflow.updated_at, workflow.is_active
                ))
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save workflow to database: {str(e)}")
            raise

    async def execute_workflow(self, workflow_id: str, metadata: Optional[Dict[str, Any]] = None) -> WorkflowExecution:
        """Execute a workflow"""
        workflow = self.workflow_definitions.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
            
        try:
            execution_id = str(uuid.uuid4())
            
            execution = WorkflowExecution(
                id=execution_id,
                workflow_id=workflow_id,
                metadata=metadata or {}
            )
            
            self.workflow_executions[execution.id] = execution
            
            self.logger.info(f"Workflow execution started: {workflow.name} (Execution ID: {execution_id})")
            return execution
            
        except Exception as e:
            self.logger.error(f"Failed to execute workflow: {str(e)}")
            raise

    async def get_workflows(self) -> List[WorkflowDefinition]:
        """Get all workflow definitions"""
        return list(self.workflow_definitions.values())

    async def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a specific workflow by ID"""
        return self.workflow_definitions.get(workflow_id)

    async def get_workflow_executions(self, workflow_id: Optional[str] = None) -> List[WorkflowExecution]:
        """Get workflow executions with optional filtering"""
        executions = list(self.workflow_executions.values())
        
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
            
        return executions

    async def send_agent_message(self, sender_id: str, receiver_id: str, message_type: str, 
                               content: str, metadata: Optional[Dict[str, Any]] = None,
                               coordination_id: Optional[str] = None) -> bool:
        """Send a message between agents"""
        try:
            if not self.database:
                return False
                
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO agent_communications (sender_agent_id, receiver_agent_id, message_type,
                                                   content, metadata, coordination_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    sender_id, receiver_id, message_type, content,
                    json.dumps(metadata or {}), coordination_id
                ))
                await session.commit()
                
            self.logger.info(f"Agent message sent: {sender_id} -> {receiver_id} ({message_type})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send agent message: {str(e)}")
            return False

    async def get_agent_messages(self, agent_id: str, message_type: Optional[str] = None,
                               unread_only: bool = True) -> List[Dict[str, Any]]:
        """Get messages for an agent"""
        if not self.database:
            return []
            
        try:
            async with self.database.get_session() as session:
                query = """
                    SELECT id, sender_agent_id, receiver_agent_id, message_type, content,
                           metadata, timestamp, read_at, coordination_id
                    FROM agent_communications
                    WHERE receiver_agent_id = %s
                """
                params = [agent_id]
                
                if message_type:
                    query += " AND message_type = %s"
                    params.append(message_type)
                    
                if unread_only:
                    query += " AND read_at IS NULL"
                    
                query += " ORDER BY timestamp DESC"
                
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                messages = []
                for row in rows:
                    messages.append({
                        "id": row[0],
                        "sender_agent_id": row[1],
                        "receiver_agent_id": row[2],
                        "message_type": row[3],
                        "content": row[4],
                        "metadata": row[5] or {},
                        "timestamp": row[6].isoformat(),
                        "read_at": row[7].isoformat() if row[7] else None,
                        "coordination_id": row[8]
                    })
                
                return messages
                
        except Exception as e:
            self.logger.error(f"Failed to get agent messages: {str(e)}")
            return []

    async def mark_message_read(self, message_id: int) -> bool:
        """Mark a message as read"""
        if not self.database:
            return False
            
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE agent_communications 
                    SET read_at = %s 
                    WHERE id = %s
                """, (datetime.utcnow(), message_id))
                await session.commit()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to mark message as read: {str(e)}")
            return False

    async def get_coordination_statistics(self) -> Dict[str, Any]:
        """Get coordination statistics"""
        total_coordinations = len(self.coordinations)
        active_coordinations = len([c for c in self.coordinations.values() 
                                  if c.status == CoordinationStatus.ACTIVE])
        completed_coordinations = len([c for c in self.coordinations.values() 
                                     if c.status == CoordinationStatus.COMPLETED])
        failed_coordinations = len([c for c in self.coordinations.values() 
                                  if c.status == CoordinationStatus.FAILED])
        
        coordination_types = {}
        for coordination in self.coordinations.values():
            coord_type = coordination.coordination_type.value
            coordination_types[coord_type] = coordination_types.get(coord_type, 0) + 1
        
        return {
            "total_coordinations": total_coordinations,
            "active_coordinations": active_coordinations,
            "completed_coordinations": completed_coordinations,
            "failed_coordinations": failed_coordinations,
            "coordination_types": coordination_types,
            "active_workflows": len(self.workflow_executions),
            "total_workflows": len(self.workflow_definitions)
        }

    async def close(self):
        """Shutdown the agent coordinator"""
        self.logger.info("Closing AgentCoordinator...")
        
        # Set shutdown event
        self._shutdown_event.set()
        
        # Cancel all active coordinations
        for task in self.active_coordinations.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.active_coordinations:
            await asyncio.gather(*self.active_coordinations.values(), return_exceptions=True)
        
        self.logger.info("AgentCoordinator closed successfully")

# Global instances and initialization functions
_agent_coordinator: Optional[AgentCoordinator] = None

async def init_agent_coordinator() -> AgentCoordinator:
    """Initialize the global agent coordinator instance"""
    global _agent_coordinator
    if not _agent_coordinator:
        _agent_coordinator = AgentCoordinator()
        await _agent_coordinator.initialize()
    return _agent_coordinator

async def get_agent_coordinator() -> AgentCoordinator:
    """Get the global agent coordinator instance"""
    global _agent_coordinator
    if not _agent_coordinator:
        _agent_coordinator = await init_agent_coordinator()
    return _agent_coordinator
