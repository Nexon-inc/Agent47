import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

from core.database import get_database, DatabaseManager
from core.cache import get_redis, RedisManager
from core.event_bus import get_kafka, KafkaManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class AgentStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class CoordinationType(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    COLLABORATIVE = "collaborative"

@dataclass
class AgentWorkload:
    agent_name: str
    current_tasks: int
    max_capacity: int
    specialization: List[str]
    current_status: AgentStatus
    last_heartbeat: datetime
    performance_score: float
    availability_score: float

@dataclass
class AgentCoordination:
    coordination_id: str
    goal_id: str
    coordination_type: CoordinationType
    agents_involved: List[str]
    coordination_rules: Dict[str, Any]
    start_time: datetime
    expected_duration: int
    current_phase: str
    dependencies: List[str]
    communication_channels: List[str]

class AgentCoordinator(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.kafka: Optional[KafkaManager] = None
        self.settings = get_settings()
        
        self.agent_workloads: Dict[str, AgentWorkload] = {}
        self.active_coordinations: Dict[str, AgentCoordination] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        self.logger = logger
        
        self._setup_agent_capabilities()

    def _setup_agent_capabilities(self):
        self.agent_capabilities = {
            "Aria": ["research", "data_analysis", "automation", "planning"],
            "Clara": ["social_media", "content_creation", "communication", "branding"],
            "Eric": ["sales", "marketing", "content_creation", "customer_relations"],
            "Joe": ["sales", "data_analysis", "automation", "optimization"],
            "Jackie": ["customer_support", "communication", "automation", "problem_solving"],
            "Shakes": ["communication", "content_creation", "research", "presentation"],
            "Purity": ["data_analysis", "research", "automation", "quality_assurance"]
        }

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing AgentCoordinator...")
            
            self.database = get_database()
            self.redis = await get_redis()
            self.kafka = await get_kafka()
            
            await self._setup_agent_coordinator_tables()
            await self._load_agent_workloads()
            await self._start_agent_monitoring()
            
            self.logger.info("AgentCoordinator initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AgentCoordinator: {str(e)}")
            return False

    async def _setup_agent_coordinator_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS agent_workloads (
                    agent_name VARCHAR(100) PRIMARY KEY,
                    current_tasks INTEGER DEFAULT 0,
                    max_capacity INTEGER DEFAULT 10,
                    specialization JSONB NOT NULL,
                    current_status VARCHAR(50) NOT NULL,
                    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    performance_score DECIMAL(5,2) DEFAULT 100.0,
                    availability_score DECIMAL(5,2) DEFAULT 100.0
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS agent_coordinations (
                    coordination_id VARCHAR(255) PRIMARY KEY,
                    goal_id VARCHAR(255) NOT NULL,
                    coordination_type VARCHAR(50) NOT NULL,
                    agents_involved JSONB NOT NULL,
                    coordination_rules JSONB NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    expected_duration INTEGER NOT NULL,
                    current_phase VARCHAR(100) NOT NULL,
                    dependencies JSONB NOT NULL,
                    communication_channels JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS agent_communications (
                    id SERIAL PRIMARY KEY,
                    coordination_id VARCHAR(255) NOT NULL,
                    from_agent VARCHAR(100) NOT NULL,
                    to_agent VARCHAR(100) NOT NULL,
                    message_type VARCHAR(50) NOT NULL,
                    message_content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_acknowledged BOOLEAN DEFAULT FALSE,
                    metadata JSONB,
                    FOREIGN KEY (coordination_id) REFERENCES agent_coordinations(coordination_id) ON DELETE CASCADE
                )
            """)
            
            await session.commit()

    async def _load_agent_workloads(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT agent_name, current_tasks, max_capacity, specialization, current_status,
                       last_heartbeat, performance_score, availability_score
                FROM agent_workloads
            """)
            
            rows = result.fetchall()
            for row in result.fetchall():
                workload = AgentWorkload(
                    agent_name=row[0],
                    current_tasks=row[1],
                    max_capacity=row[2],
                    specialization=row[3],
                    current_status=AgentStatus(row[4]),
                    last_heartbeat=row[5],
                    performance_score=float(row[6]) if row[6] else 100.0,
                    availability_score=float(row[7]) if row[7] else 100.0
                )
                self.agent_workloads[workload.agent_name] = workload

    async def _start_agent_monitoring(self):
        # Start background monitoring tasks
        asyncio.create_task(self._monitor_agent_heartbeats())
        asyncio.create_task(self._update_agent_workloads())
        asyncio.create_task(self._cleanup_expired_coordinations())

    async def assign_agents_to_goal(self, goal_id: str, goal_type: str, required_capabilities: List[str], 
                                   coordination_type: CoordinationType = CoordinationType.COLLABORATIVE) -> List[str]:
        try:
            # Find available agents with required capabilities
            suitable_agents = await self._find_suitable_agents(required_capabilities)
            
            if not suitable_agents:
                raise ValueError(f"No suitable agents found for capabilities: {required_capabilities}")
            
            # Select optimal agent combination
            selected_agents = await self._select_optimal_agents(suitable_agents, coordination_type)
            
            # Create coordination plan
            coordination_id = await self._create_coordination_plan(
                goal_id, selected_agents, coordination_type, required_capabilities
            )
            
            # Update agent workloads
            await self._update_agent_assignments(selected_agents, goal_id)
            
            # Initialize inter-agent communication
            await self._initialize_agent_communication(coordination_id, selected_agents)
            
            self.logger.info(f"Assigned agents {selected_agents} to goal {goal_id}")
            return selected_agents
            
        except Exception as e:
            self.logger.error(f"Failed to assign agents to goal: {str(e)}")
            raise

    async def _find_suitable_agents(self, required_capabilities: List[str]) -> List[Dict[str, Any]]:
        suitable_agents = []
        
        for agent_name, capabilities in self.agent_capabilities.items():
            # Check if agent has required capabilities
            matching_capabilities = [cap for cap in required_capabilities if cap in capabilities]
            
            if matching_capabilities:
                workload = self.agent_workloads.get(agent_name)
                if workload and workload.current_status == AgentStatus.AVAILABLE:
                    capability_score = len(matching_capabilities) / len(required_capabilities)
                    availability_score = workload.availability_score / 100.0
                    performance_score = workload.performance_score / 100.0
                    
                    # Calculate overall suitability score
                    suitability_score = (capability_score * 0.4 + 
                                       availability_score * 0.3 + 
                                       performance_score * 0.3)
                    
                    suitable_agents.append({
                        "agent_name": agent_name,
                        "capabilities": capabilities,
                        "matching_capabilities": matching_capabilities,
                        "workload": workload,
                        "suitability_score": suitability_score
                    })
        
        # Sort by suitability score
        suitable_agents.sort(key=lambda x: x["suitability_score"], reverse=True)
        return suitable_agents

    async def _select_optimal_agents(self, suitable_agents: List[Dict[str, Any]], 
                                   coordination_type: CoordinationType) -> List[str]:
        if coordination_type == CoordinationType.SEQUENTIAL:
            # For sequential tasks, select the best single agent
            return [suitable_agents[0]["agent_name"]]
        
        elif coordination_type == CoordinationType.PARALLEL:
            # For parallel tasks, select multiple agents with different specializations
            selected = []
            used_capabilities = set()
            
            for agent in suitable_agents:
                if len(selected) >= 3:  # Limit to 3 agents for parallel execution
                    break
                
                # Check if agent brings new capabilities
                new_capabilities = set(agent["matching_capabilities"]) - used_capabilities
                if new_capabilities or len(selected) == 0:
                    selected.append(agent["agent_name"])
                    used_capabilities.update(agent["matching_capabilities"])
            
            return selected
        
        elif coordination_type == CoordinationType.PIPELINE:
            # For pipeline tasks, select agents that can work in sequence
            selected = []
            pipeline_capabilities = []
            
            for agent in suitable_agents:
                if len(selected) >= 4:  # Limit pipeline to 4 agents
                    break
                
                # Ensure pipeline has all required capabilities
                pipeline_capabilities.extend(agent["matching_capabilities"])
                if len(set(pipeline_capabilities)) >= len(set(agent["matching_capabilities"])):
                    selected.append(agent["agent_name"])
            
            return selected
        
        else:  # COLLABORATIVE
            # For collaborative tasks, select agents that work well together
            selected = []
            collaboration_score = 0
            
            for agent in suitable_agents[:3]:  # Limit to 3 agents for collaboration
                # Calculate collaboration potential with already selected agents
                if not selected:
                    selected.append(agent["agent_name"])
                    collaboration_score = agent["suitability_score"]
                else:
                    # Check if this agent complements the team
                    team_capabilities = set()
                    for selected_agent in selected:
                        team_capabilities.update(self.agent_capabilities[selected_agent])
                    
                    new_capabilities = set(agent["matching_capabilities"]) - team_capabilities
                    if new_capabilities or len(selected) < 2:
                        selected.append(agent["agent_name"])
                        collaboration_score += agent["suitability_score"]
            
            return selected

    async def _create_coordination_plan(self, goal_id: str, selected_agents: List[str], 
                                      coordination_type: CoordinationType, required_capabilities: List[str]) -> str:
        coordination_id = str(uuid.uuid4())
        
        # Define coordination rules based on type
        coordination_rules = self._define_coordination_rules(coordination_type, selected_agents)
        
        # Determine dependencies
        dependencies = self._determine_agent_dependencies(coordination_type, selected_agents)
        
        # Set up communication channels
        communication_channels = self._setup_communication_channels(selected_agents)
        
        coordination = AgentCoordination(
            coordination_id=coordination_id,
            goal_id=goal_id,
            coordination_type=coordination_type,
            agents_involved=selected_agents,
            coordination_rules=coordination_rules,
            start_time=datetime.utcnow(),
            expected_duration=120,  # 2 hours default
            current_phase="initialization",
            dependencies=dependencies,
            communication_channels=communication_channels
        )
        
        # Save to database
        await self._save_coordination_plan(coordination)
        self.active_coordinations[coordination_id] = coordination
        
        return coordination_id

    def _define_coordination_rules(self, coordination_type: CoordinationType, agents: List[str]) -> Dict[str, Any]:
        if coordination_type == CoordinationType.SEQUENTIAL:
            return {
                "execution_order": agents,
                "handoff_criteria": "task_completion",
                "communication_frequency": "on_handoff",
                "escalation_path": agents[0] if agents else None
            }
        
        elif coordination_type == CoordinationType.PARALLEL:
            return {
                "execution_mode": "parallel",
                "coordination_points": ["start", "midpoint", "completion"],
                "communication_frequency": "hourly",
                "conflict_resolution": "consensus"
            }
        
        elif coordination_type == CoordinationType.PIPELINE:
            return {
                "pipeline_stages": agents,
                "stage_transitions": "automatic",
                "quality_gates": "each_stage",
                "communication_frequency": "on_transition"
            }
        
        else:  # COLLABORATIVE
            return {
                "collaboration_mode": "team_based",
                "decision_making": "consensus",
                "communication_frequency": "continuous",
                "conflict_resolution": "facilitated"
            }

    def _determine_agent_dependencies(self, coordination_type: CoordinationType, agents: List[str]) -> List[str]:
        if coordination_type == CoordinationType.SEQUENTIAL:
            # Each agent depends on the previous one
            dependencies = []
            for i in range(1, len(agents)):
                dependencies.append(f"{agents[i-1]} -> {agents[i]}")
            return dependencies
        
        elif coordination_type == CoordinationType.PIPELINE:
            # Pipeline stages have sequential dependencies
            dependencies = []
            for i in range(1, len(agents)):
                dependencies.append(f"{agents[i-1]} -> {agents[i]}")
            return dependencies
        
        else:
            # Parallel and collaborative have minimal dependencies
            return []

    def _setup_communication_channels(self, agents: List[str]) -> List[str]:
        channels = []
        
        if len(agents) == 1:
            channels.append("internal")
        elif len(agents) == 2:
            channels.extend(["direct", "shared_workspace"])
        else:
            channels.extend(["team_chat", "shared_workspace", "status_updates"])
        
        return channels

    async def _save_coordination_plan(self, coordination: AgentCoordination):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute("""
                INSERT INTO agent_coordinations (coordination_id, goal_id, coordination_type, agents_involved,
                                               coordination_rules, start_time, expected_duration, current_phase,
                                               dependencies, communication_channels)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                coordination.coordination_id, coordination.goal_id, coordination.coordination_type.value,
                json.dumps(coordination.agents_involved), json.dumps(coordination.coordination_rules),
                coordination.start_time, coordination.expected_duration, coordination.current_phase,
                json.dumps(coordination.dependencies), json.dumps(coordination.communication_channels)
            ))
            await session.commit()

    async def _update_agent_assignments(self, selected_agents: List[str], goal_id: str):
        for agent_name in selected_agents:
            if agent_name in self.agent_workloads:
                workload = self.agent_workloads[agent_name]
                workload.current_tasks += 1
                
                # Update status if at capacity
                if workload.current_tasks >= workload.max_capacity:
                    workload.current_status = AgentStatus.BUSY
                
                # Update database
                await self._update_agent_workload(workload)

    async def _update_agent_workload(self, workload: AgentWorkload):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute("""
                UPDATE agent_workloads 
                SET current_tasks = %s, current_status = %s, updated_at = %s
                WHERE agent_name = %s
            """, (
                workload.current_tasks, workload.current_status.value, 
                datetime.utcnow(), workload.agent_name
            ))
            await session.commit()

    async def _initialize_agent_communication(self, coordination_id: str, agents: List[str]):
        if not self.kafka:
            return
        
        try:
            # Create communication topic for this coordination
            topic_name = f"agent_coordination_{coordination_id}"
            await self.kafka.create_topic(topic_name)
            
            # Send initialization message
            init_message = {
                "coordination_id": coordination_id,
                "agents": agents,
                "message_type": "coordination_init",
                "timestamp": datetime.utcnow().isoformat(),
                "instructions": "Begin coordination for assigned goal"
            }
            
            await self.kafka.publish_event(topic_name, init_message)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent communication: {str(e)}")

    async def send_agent_message(self, coordination_id: str, from_agent: str, to_agent: str, 
                                message_type: str, message_content: str, metadata: Dict[str, Any] = None) -> bool:
        try:
            if coordination_id not in self.active_coordinations:
                raise ValueError("Invalid coordination ID")
            
            # Save message to database
            await self._save_agent_message(coordination_id, from_agent, to_agent, message_type, message_content, metadata)
            
            # Publish to Kafka for real-time communication
            if self.kafka:
                topic_name = f"agent_coordination_{coordination_id}"
                message_data = {
                    "from_agent": from_agent,
                    "to_agent": to_agent,
                    "message_type": message_type,
                    "message_content": message_content,
                    "metadata": metadata or {},
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.kafka.publish_event(topic_name, message_data)
            
            self.logger.info(f"Message sent from {from_agent} to {to_agent} in coordination {coordination_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send agent message: {str(e)}")
            return False

    async def _save_agent_message(self, coordination_id: str, from_agent: str, to_agent: str, 
                                 message_type: str, message_content: str, metadata: Dict[str, Any] = None):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute("""
                INSERT INTO agent_communications (coordination_id, from_agent, to_agent, message_type,
                                                message_content, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                coordination_id, from_agent, to_agent, message_type, message_content,
                json.dumps(metadata or {})
            ))
            await session.commit()

    async def get_agent_workload_status(self, agent_name: str = None) -> Dict[str, Any]:
        if agent_name:
            workload = self.agent_workloads.get(agent_name)
            if workload:
                return {
                    "agent_name": workload.agent_name,
                    "current_tasks": workload.current_tasks,
                    "max_capacity": workload.max_capacity,
                    "utilization": (workload.current_tasks / workload.max_capacity) * 100,
                    "status": workload.current_status.value,
                    "performance_score": workload.performance_score,
                    "availability_score": workload.availability_score,
                    "last_heartbeat": workload.last_heartbeat.isoformat()
                }
            return {}
        
        # Return all agent workloads
        workloads = {}
        for name, workload in self.agent_workloads.items():
            workloads[name] = {
                "current_tasks": workload.current_tasks,
                "max_capacity": workload.max_capacity,
                "utilization": (workload.current_tasks / workload.max_capacity) * 100,
                "status": workload.current_status.value,
                "performance_score": workload.performance_score,
                "availability_score": workload.availability_score,
                "last_heartbeat": workload.last_heartbeat.isoformat()
            }
        
        return workloads

    async def update_agent_status(self, agent_name: str, status: AgentStatus, 
                                 performance_score: float = None, availability_score: float = None):
        if agent_name not in self.agent_workloads:
            return
        
        workload = self.agent_workloads[agent_name]
        workload.current_status = status
        workload.last_heartbeat = datetime.utcnow()
        
        if performance_score is not None:
            workload.performance_score = performance_score
        
        if availability_score is not None:
            workload.availability_score = availability_score
        
        # Update database
        await self._update_agent_status_in_db(agent_name, status, performance_score, availability_score)
        
        self.logger.info(f"Agent {agent_name} status updated to {status.value}")

    async def _update_agent_status_in_db(self, agent_name: str, status: AgentStatus, 
                                        performance_score: float = None, availability_score: float = None):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            update_fields = ["current_status = %s", "last_heartbeat = %s"]
            params = [status.value, datetime.utcnow()]
            
            if performance_score is not None:
                update_fields.append("performance_score = %s")
                params.append(performance_score)
            
            if availability_score is not None:
                update_fields.append("availability_score = %s")
                params.append(availability_score)
            
            params.append(agent_name)
            
            query = f"UPDATE agent_workloads SET {', '.join(update_fields)} WHERE agent_name = %s"
            await session.execute(query, params)
            await session.commit()

    async def _monitor_agent_heartbeats(self):
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                current_time = datetime.utcnow()
                for agent_name, workload in self.agent_workloads.items():
                    # Check if agent is responsive
                    if current_time - workload.last_heartbeat > timedelta(minutes=5):
                        if workload.current_status != AgentStatus.OFFLINE:
                            await self.update_agent_status(agent_name, AgentStatus.OFFLINE)
                            self.logger.warning(f"Agent {agent_name} marked as offline due to missed heartbeat")
                
            except Exception as e:
                self.logger.error(f"Error in agent heartbeat monitoring: {str(e)}")

    async def _update_agent_workloads(self):
        while True:
            try:
                await asyncio.sleep(300)  # Update every 5 minutes
                
                if not self.database:
                    continue
                
                # Update workload counts from database
                async with self.database.get_session() as session:
                    result = await session.execute("""
                        SELECT agent_name, COUNT(*) as current_tasks
                        FROM agent_tasks 
                        WHERE status IN ('pending', 'in_progress')
                        GROUP BY agent_name
                    """)
                    
                    for row in result.fetchall():
                        agent_name = row[0]
                        current_tasks = row[1]
                        
                        if agent_name in self.agent_workloads:
                            workload = self.agent_workloads[agent_name]
                            workload.current_tasks = current_tasks
                            
                            # Update status based on workload
                            if current_tasks == 0:
                                workload.current_status = AgentStatus.AVAILABLE
                            elif current_tasks >= workload.max_capacity:
                                workload.current_status = AgentStatus.BUSY
                            else:
                                workload.current_status = AgentStatus.AVAILABLE
                
            except Exception as e:
                self.logger.error(f"Error in workload update: {str(e)}")

    async def _cleanup_expired_coordinations(self):
        while True:
            try:
                await asyncio.sleep(3600)  # Clean up every hour
                
                current_time = datetime.utcnow()
                expired_coordinations = []
                
                for coordination_id, coordination in self.active_coordinations.items():
                    if current_time - coordination.start_time > timedelta(hours=coordination.expected_duration):
                        expired_coordinations.append(coordination_id)
                
                for coordination_id in expired_coordinations:
                    await self._cleanup_coordination(coordination_id)
                
            except Exception as e:
                self.logger.error(f"Error in coordination cleanup: {str(e)}")

    async def _cleanup_coordination(self, coordination_id: str):
        try:
            # Remove from active coordinations
            if coordination_id in self.active_coordinations:
                del self.active_coordinations[coordination_id]
            
            # Update agent workloads
            coordination = self.active_coordinations.get(coordination_id)
            if coordination:
                for agent_name in coordination.agents_involved:
                    if agent_name in self.agent_workloads:
                        workload = self.agent_workloads[agent_name]
                        workload.current_tasks = max(0, workload.current_tasks - 1)
                        
                        if workload.current_tasks < workload.max_capacity:
                            workload.current_status = AgentStatus.AVAILABLE
                        
                        await self._update_agent_workload(workload)
            
            self.logger.info(f"Cleaned up expired coordination {coordination_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup coordination {coordination_id}: {str(e)}")

    async def close(self):
        self.logger.info("Closing AgentCoordinator...")
        if self.database:
            await self.database.close()

# Global instances and initialization functions
_agent_coordinator: Optional[AgentCoordinator] = None

async def init_agent_coordinator() -> AgentCoordinator:
    global _agent_coordinator
    if not _agent_coordinator:
        _agent_coordinator = AgentCoordinator()
        await _agent_coordinator.initialize()
    return _agent_coordinator

async def get_agent_coordinator() -> AgentCoordinator:
    global _agent_coordinator
    if not _agent_coordinator:
        _agent_coordinator = await init_agent_coordinator()
    return _agent_coordinator
