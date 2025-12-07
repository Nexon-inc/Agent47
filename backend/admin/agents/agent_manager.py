import asyncio
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from backend.core.database import get_database, DatabaseManager
from backend.core.cache import get_redis, RedisManager
from backend.core.event_bus import get_kafka, KafkaManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class AgentStatus(Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class AgentType(Enum):
    SOCIAL_MEDIA = "social_media"
    CUSTOMER_SUPPORT = "customer_support"
    SALES = "sales"
    RESEARCH = "research"
    MARKETING = "marketing"
    CONTENT_CREATION = "content_creation"
    BUSINESS_FINANCE = "business_finance"

class AgentCapability(Enum):
    NLP_PROCESSING = "nlp_processing"
    API_INTEGRATION = "api_integration"
    DATA_ANALYSIS = "data_analysis"
    AUTOMATION = "automation"
    COMMUNICATION = "communication"
    DECISION_MAKING = "decision_making"
    LEARNING = "learning"
    CREATIVE_GENERATION = "creative_generation"

@dataclass
class AgentConfig:
    max_concurrent_tasks: int = 5
    timeout_seconds: int = 300
    retry_attempts: int = 3
    memory_limit_mb: int = 512
    cpu_limit_percent: float = 25.0
    api_rate_limit: int = 100
    learning_enabled: bool = True
    auto_scaling: bool = True

@dataclass
class AgentMetrics:
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_response_time: float = 0.0
    success_rate: float = 100.0
    active_tasks: int = 0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    last_activity: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Agent:
    id: str
    name: str
    agent_type: AgentType
    status: AgentStatus
    capabilities: List[AgentCapability]
    config: AgentConfig
    metrics: AgentMetrics
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    is_active: bool = True

class AgentManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.kafka: Optional[KafkaManager] = None
        self.settings = get_settings()

        self.agents: Dict[str, Agent] = {}
        self.agent_tasks: Dict[str, List[str]] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}
        self.logger = logger

        self._shutdown_event = asyncio.Event()

        self._setup_default_agents()

    def _setup_default_agents(self):
        self.default_agents = {
            "Aria": {
                "type": AgentType.SOCIAL_MEDIA,
                "capabilities": [
                    AgentCapability.NLP_PROCESSING,
                    AgentCapability.API_INTEGRATION,
                    AgentCapability.AUTOMATION,
                    AgentCapability.COMMUNICATION
                ],
                "description": "Social media management and automation specialist",
                "config": AgentConfig(
                    max_concurrent_tasks=8,
                    timeout_seconds=600,
                    api_rate_limit=200
                )
            },
            "Clara": {
                "type": AgentType.CUSTOMER_SUPPORT,
                "capabilities": [
                    AgentCapability.NLP_PROCESSING,
                    AgentCapability.COMMUNICATION,
                    AgentCapability.DECISION_MAKING,
                    AgentCapability.LEARNING
                ],
                "description": "Customer support and relationship management expert",
                "config": AgentConfig(
                    max_concurrent_tasks=10,
                    timeout_seconds=900,
                    memory_limit_mb=1024
                )
            },
            "Eric": {
                "type": AgentType.SALES,
                "capabilities": [
                    AgentCapability.NLP_PROCESSING,
                    AgentCapability.API_INTEGRATION,
                    AgentCapability.DATA_ANALYSIS,
                    AgentCapability.COMMUNICATION
                ],
                "description": "Sales optimization and lead generation specialist",
                "config": AgentConfig(
                    max_concurrent_tasks=6,
                    timeout_seconds=450,
                    api_rate_limit=150
                )
            },
            "Joe": {
                "type": AgentType.RESEARCH,
                "capabilities": [
                    AgentCapability.NLP_PROCESSING,
                    AgentCapability.API_INTEGRATION,
                    AgentCapability.DATA_ANALYSIS,
                    AgentCapability.LEARNING
                ],
                "description": "Research and data analysis expert",
                "config": AgentConfig(
                    max_concurrent_tasks=4,
                    timeout_seconds=1200,
                    memory_limit_mb=2048
                )
            },
            "Jackie": {
                "type": AgentType.MARKETING,
                "capabilities": [
                    AgentCapability.NLP_PROCESSING,
                    AgentCapability.API_INTEGRATION,
                    AgentCapability.AUTOMATION,
                    AgentCapability.DATA_ANALYSIS
                ],
                "description": "Marketing strategy and campaign management specialist",
                "config": AgentConfig(
                    max_concurrent_tasks=7,
                    timeout_seconds=750,
                    api_rate_limit=180
                )
            },
            "Shakes": {
                "type": AgentType.CONTENT_CREATION,
                "capabilities": [
                    AgentCapability.NLP_PROCESSING,
                    AgentCapability.CREATIVE_GENERATION,
                    AgentCapability.COMMUNICATION,
                    AgentCapability.LEARNING
                ],
                "description": "Creative content generation and optimization expert",
                "config": AgentConfig(
                    max_concurrent_tasks=5,
                    timeout_seconds=600,
                    memory_limit_mb=1536
                )
            },
            "Purity": {
                "type": AgentType.BUSINESS_FINANCE,
                "capabilities": [
                    AgentCapability.DATA_ANALYSIS,
                    AgentCapability.DECISION_MAKING,
                    AgentCapability.API_INTEGRATION,
                    AgentCapability.LEARNING
                ],
                "description": "Business intelligence and financial analysis specialist",
                "config": AgentConfig(
                    max_concurrent_tasks=6,
                    timeout_seconds=900,
                    memory_limit_mb=2048
                )
            }
        }

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing AgentManager...")
            
            self.database = get_database()
            self.redis = await get_redis()
            self.kafka = await get_kafka()
            
            await self._setup_agent_tables()
            await self._load_agents_from_database()
            
            # Initialize agent coordinator for communication
            from .agent_coordinator import get_agent_coordinator
            self.agent_coordinator = await get_agent_coordinator()
            
            # Start background monitoring tasks
            asyncio.create_task(self._agent_health_monitor())
            asyncio.create_task(self._agent_communication_monitor())
            asyncio.create_task(self._agent_service_integration_monitor())
            
            self.logger.info("AgentManager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AgentManager: {str(e)}", exc_info=True)
            return False

    async def _setup_agent_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")

        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    CREATE TABLE IF NOT EXISTS agents (
                        id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        agent_type VARCHAR(100) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        capabilities JSONB NOT NULL,
                        config JSONB NOT NULL,
                        metrics JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        version VARCHAR(50) DEFAULT '1.0.0',
                        description TEXT,
                        tags JSONB DEFAULT '[]',
                        is_active BOOLEAN DEFAULT TRUE,
                        service_endpoint VARCHAR(500),
                        health_check_url VARCHAR(500),
                        last_health_check TIMESTAMP,
                        communication_protocol VARCHAR(50) DEFAULT 'http',
                        api_key VARCHAR(255),
                        webhook_url VARCHAR(500)
                    )
                """)
                
                await session.execute("""
                    CREATE TABLE IF NOT EXISTS agent_services (
                        id VARCHAR(255) PRIMARY KEY,
                        agent_id VARCHAR(255) NOT NULL,
                        service_name VARCHAR(255) NOT NULL,
                        service_type VARCHAR(100) NOT NULL,
                        endpoint VARCHAR(500) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        health_check_url VARCHAR(500),
                        last_health_check TIMESTAMP,
                        response_time_ms INTEGER,
                        error_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
                    )
                """)
                
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
                        status VARCHAR(50) DEFAULT 'sent',
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        FOREIGN KEY (sender_agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                        FOREIGN KEY (receiver_agent_id) REFERENCES agents(id) ON DELETE CASCADE
                    )
                """)
                
                await session.execute("""
                    CREATE TABLE IF NOT EXISTS agent_health_logs (
                        id SERIAL PRIMARY KEY,
                        agent_id VARCHAR(255) NOT NULL,
                        health_status VARCHAR(50) NOT NULL,
                        response_time_ms INTEGER,
                        error_message TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
                    )
                """)

                await session.commit()
                self.logger.info("Agent tables setup completed")

        except Exception as e:
            self.logger.error(f"Failed to setup agent tables: {str(e)}")
            raise

    async def _load_agents_from_database(self):
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, name, agent_type, status, capabilities, config, metrics,
                           created_at, updated_at, version, description, tags, is_active,
                           service_endpoint, health_check_url, last_health_check,
                           communication_protocol, api_key, webhook_url
                    FROM agents WHERE is_active = TRUE
                """)

                rows = result.fetchall()
                for row in rows:
                    agent = self._create_agent_from_row(row)
                    self.agents[agent.id] = agent

            self.logger.info(f"Loaded {len(self.agents)} agents from database")

        except Exception as e:
            self.logger.error(f"Failed to load agents from database: {str(e)}")

    def _create_agent_from_row(self, row) -> Agent:
        return Agent(
            id=row[0],
            name=row[1],
            agent_type=AgentType(row[2]),
            status=AgentStatus(row[3]),
            capabilities=[AgentCapability(cap) for cap in (row[4] or [])],
            config=AgentConfig(**(row[5] or {})),
            metrics=AgentMetrics(**(row[6] or {})),
            created_at=row[7],
            updated_at=row[8],
            version=row[9],
            description=row[10],
            tags=row[11] or [],
            is_active=row[12]
        )

    async def _agent_health_monitor(self):
        while not self._shutdown_event.is_set():
            try:
                for agent in self.agents.values():
                    if agent.is_active:
                        await self._check_agent_health(agent)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in agent health monitor: {str(e)}")
                await asyncio.sleep(120)

    async def _check_agent_health(self, agent: Agent):
        try:
            # Check if agent has health check URL
            if not hasattr(agent, 'health_check_url') or not agent.health_check_url:
                return
            
            import aiohttp
            import time
            
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(agent.health_check_url, timeout=10) as response:
                    response_time = int((time.time() - start_time) * 1000)
                    
                    if response.status == 200:
                        health_data = await response.json()
                        agent.metrics.avg_response_time = response_time
                        agent.status = AgentStatus.ONLINE
                        
                        # Update health metrics
                        if 'memory_usage' in health_data:
                            agent.metrics.memory_usage = health_data['memory_usage']
                        if 'cpu_usage' in health_data:
                            agent.metrics.cpu_usage = health_data['cpu_usage']
                        if 'active_tasks' in health_data:
                            agent.metrics.active_tasks = health_data['active_tasks']
                    else:
                        agent.status = AgentStatus.ERROR
                        agent.metrics.failed_tasks += 1
                    
                    # Log health check
                    await self._log_agent_health(agent.id, agent.status.value, response_time)
                    
        except Exception as e:
            self.logger.error(f"Health check failed for agent {agent.name}: {str(e)}")
            agent.status = AgentStatus.ERROR
            agent.metrics.failed_tasks += 1
            await self._log_agent_health(agent.id, "error", 0, str(e))

    async def _log_agent_health(self, agent_id: str, status: str, response_time: int, error_message: str = None):
        if not self.database:
            return
            
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO agent_health_logs (agent_id, health_status, response_time_ms, error_message)
                    VALUES (%s, %s, %s, %s)
                """, (agent_id, status, response_time, error_message))
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log agent health: {str(e)}")

    async def _agent_communication_monitor(self):
        while not self._shutdown_event.is_set():
            try:
                # Process pending communications
                await self._process_pending_communications()
                
                # Check for failed communications and retry
                await self._retry_failed_communications()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in communication monitor: {str(e)}")
                await asyncio.sleep(60)

    async def _process_pending_communications(self):
        if not self.database:
            return
            
        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, sender_agent_id, receiver_agent_id, message_type, content, metadata
                    FROM agent_communications 
                    WHERE status = 'pending' AND retry_count < max_retries
                    ORDER BY timestamp ASC
                    LIMIT 50
                """)
                
                rows = result.fetchall()
                for row in rows:
                    await self._send_agent_communication(
                        row[0], row[1], row[2], row[3], row[4], row[5] or {}
                    )
                    
        except Exception as e:
            self.logger.error(f"Failed to process pending communications: {str(e)}")

    async def _send_agent_communication(self, comm_id: int, sender_id: str, receiver_id: str, 
                                      message_type: str, content: str, metadata: dict):
        try:
            receiver_agent = self.agents.get(receiver_id)
            if not receiver_agent:
                await self._update_communication_status(comm_id, 'failed', 'Receiver agent not found')
                return
            
            # Send via agent coordinator if available
            if self.agent_coordinator:
                success = await self.agent_coordinator.send_agent_message(
                    sender_id, receiver_id, message_type, content, metadata, str(comm_id)
                )
                
                if success:
                    await self._update_communication_status(comm_id, 'sent')
                else:
                    await self._update_communication_status(comm_id, 'failed', 'Coordinator send failed')
            else:
                # Direct communication via HTTP/webhook
                success = await self._send_direct_communication(receiver_agent, message_type, content, metadata)
                
                if success:
                    await self._update_communication_status(comm_id, 'sent')
                else:
                    await self._update_communication_status(comm_id, 'failed', 'Direct send failed')
                    
        except Exception as e:
            self.logger.error(f"Failed to send communication {comm_id}: {str(e)}")
            await self._update_communication_status(comm_id, 'failed', str(e))

    async def _send_direct_communication(self, agent: Agent, message_type: str, content: str, metadata: dict) -> bool:
        try:
            if not hasattr(agent, 'webhook_url') or not agent.webhook_url:
                return False
            
            import aiohttp
            import json
            
            payload = {
                "message_type": message_type,
                "content": content,
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(agent.webhook_url, json=payload, timeout=10) as response:
                    return response.status == 200
                    
        except Exception as e:
            self.logger.error(f"Direct communication failed for agent {agent.name}: {str(e)}")
            return False

    async def _update_communication_status(self, comm_id: int, status: str, error_message: str = None):
        if not self.database:
            return
            
        try:
            async with self.database.get_session() as session:
                if error_message:
                    await session.execute("""
                        UPDATE agent_communications 
                        SET status = %s, error_message = %s, retry_count = retry_count + 1
                        WHERE id = %s
                    """, (status, error_message, comm_id))
                else:
                    await session.execute("""
                        UPDATE agent_communications 
                        SET status = %s, read_at = %s
                        WHERE id = %s
                    """, (status, datetime.utcnow(), comm_id))
                    
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to update communication status: {str(e)}")

    async def _retry_failed_communications(self):
        if not self.database:
            return
            
        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, sender_agent_id, receiver_agent_id, message_type, content, metadata
                    FROM agent_communications 
                    WHERE status = 'failed' AND retry_count < max_retries
                    AND timestamp < %s
                    ORDER BY timestamp ASC
                    LIMIT 20
                """, (datetime.utcnow() - timedelta(minutes=5),))
                
                rows = result.fetchall()
                for row in rows:
                    await self._send_agent_communication(
                        row[0], row[1], row[2], row[3], row[4], row[5] or {}
                    )
                    
        except Exception as e:
            self.logger.error(f"Failed to retry communications: {str(e)}")

    async def _agent_service_integration_monitor(self):
        while not self._shutdown_event.is_set():
            try:
                # Monitor individual agent services
                for agent in self.agents.values():
                    if agent.is_active:
                        await self._check_agent_services(agent)
                
                await asyncio.sleep(120)  # Check every 2 minutes
                
            except Exception as e:
                self.logger.error(f"Error in service integration monitor: {str(e)}")
                await asyncio.sleep(300)

    async def _check_agent_services(self, agent: Agent):
        try:
            if not hasattr(agent, 'service_endpoint') or not agent.service_endpoint:
                return
            
            import aiohttp
            import time
            
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                # Check service status
                status_url = f"{agent.service_endpoint}/status"
                async with session.get(status_url, timeout=10) as response:
                    response_time = int((time.time() - start_time) * 1000)
                    
                    if response.status == 200:
                        service_data = await response.json()
                        
                        # Update agent metrics from service data
                        if 'metrics' in service_data:
                            metrics = service_data['metrics']
                            agent.metrics.total_tasks = metrics.get('total_tasks', agent.metrics.total_tasks)
                            agent.metrics.completed_tasks = metrics.get('completed_tasks', agent.metrics.completed_tasks)
                            agent.metrics.failed_tasks = metrics.get('failed_tasks', agent.metrics.failed_tasks)
                            agent.metrics.success_rate = metrics.get('success_rate', agent.metrics.success_rate)
                            agent.metrics.active_tasks = metrics.get('active_tasks', agent.metrics.active_tasks)
                        
                        # Update agent status
                        if service_data.get('status') == 'healthy':
                            agent.status = AgentStatus.ONLINE
                        else:
                            agent.status = AgentStatus.BUSY
                    else:
                        agent.status = AgentStatus.ERROR
                        
        except Exception as e:
            self.logger.error(f"Service check failed for agent {agent.name}: {str(e)}")
            agent.status = AgentStatus.ERROR

    async def register_agent_service(self, agent_id: str, service_name: str, service_type: str, 
                                   endpoint: str, health_check_url: str = None) -> bool:
        try:
            if not self.database:
                return False
                
            service_id = str(uuid.uuid4())
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO agent_services (id, agent_id, service_name, service_type, endpoint, 
                                              status, health_check_url, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    service_id, agent_id, service_name, service_type, endpoint, 'active',
                    health_check_url, datetime.utcnow(), datetime.utcnow()
                ))
                await session.commit()
                
            self.logger.info(f"Registered service {service_name} for agent {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent service: {str(e)}")
            return False

    async def get_agent_services(self, agent_id: str) -> List[Dict[str, Any]]:
        if not self.database:
            return []
            
        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, service_name, service_type, endpoint, status, health_check_url,
                           last_health_check, response_time_ms, error_count, created_at, updated_at
                    FROM agent_services WHERE agent_id = %s
                """, (agent_id,))
                
                rows = result.fetchall()
                services = []
                for row in rows:
                    services.append({
                        "id": row[0],
                        "service_name": row[1],
                        "service_type": row[2],
                        "endpoint": row[3],
                        "status": row[4],
                        "health_check_url": row[5],
                        "last_health_check": row[6].isoformat() if row[6] else None,
                        "response_time_ms": row[7],
                        "error_count": row[8],
                        "created_at": row[9].isoformat(),
                        "updated_at": row[10].isoformat()
                    })
                
                return services
                
        except Exception as e:
            self.logger.error(f"Failed to get agent services: {str(e)}")
            return []

    async def send_agent_message(self, sender_id: str, receiver_id: str, message_type: str, 
                               content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        try:
            if not self.database:
                return False
                
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO agent_communications (sender_agent_id, receiver_agent_id, message_type,
                                                   content, metadata, timestamp, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    sender_id, receiver_id, message_type, content,
                    json.dumps(metadata or {}), datetime.utcnow(), 'pending'
                ))
                await session.commit()
                
            self.logger.info(f"Agent message queued: {sender_id} -> {receiver_id} ({message_type})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send agent message: {str(e)}")
            return False

    async def get_agent_messages(self, agent_id: str, message_type: Optional[str] = None,
                               unread_only: bool = True) -> List[Dict[str, Any]]:
        if not self.database:
            return []
            
        try:
            async with self.database.get_session() as session:
                query = """
                    SELECT id, sender_agent_id, receiver_agent_id, message_type, content,
                           metadata, timestamp, read_at, status, retry_count
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
                        "status": row[8],
                        "retry_count": row[9]
                    })
                
                return messages
                
        except Exception as e:
            self.logger.error(f"Failed to get agent messages: {str(e)}")
            return []

    async def mark_message_read(self, message_id: int) -> bool:
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

    async def get_agent_integration_status(self, agent_id: str) -> Dict[str, Any]:
        agent = self.agents.get(agent_id)
        if not agent:
            return {"error": "Agent not found"}
            
        try:
            services = await self.get_agent_services(agent_id)
            messages = await self.get_agent_messages(agent_id, unread_only=False)
            
            return {
                "agent_id": agent_id,
                "agent_name": agent.name,
                "status": agent.status.value,
                "services": services,
                "total_messages": len(messages),
                "unread_messages": len([m for m in messages if not m["read_at"]]),
                "metrics": {
                    "total_tasks": agent.metrics.total_tasks,
                    "completed_tasks": agent.metrics.completed_tasks,
                    "failed_tasks": agent.metrics.failed_tasks,
                    "success_rate": agent.metrics.success_rate,
                    "active_tasks": agent.metrics.active_tasks,
                    "avg_response_time": agent.metrics.avg_response_time,
                    "memory_usage": agent.metrics.memory_usage,
                    "cpu_usage": agent.metrics.cpu_usage
                },
                "last_activity": agent.metrics.last_activity.isoformat(),
                "capabilities": [cap.value for cap in agent.capabilities]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get agent integration status: {str(e)}")
            return {"error": str(e)}

    async def get_all_agents_integration_status(self) -> List[Dict[str, Any]]:
        statuses = []
        for agent_id in self.agents.keys():
            status = await self.get_agent_integration_status(agent_id)
            statuses.append(status)
        return statuses

    async def create_agent(self, agent_data: Dict[str, Any]) -> Agent:
        try:
            agent_id = str(uuid.uuid4())
            
            capabilities = [AgentCapability(cap) for cap in agent_data["capabilities"]]
            agent_type = AgentType(agent_data["agent_type"])
            
            config = AgentConfig(
                max_concurrent_tasks=agent_data.get("config", {}).get("max_concurrent_tasks", 5),
                timeout_seconds=agent_data.get("config", {}).get("timeout_seconds", 300),
                retry_attempts=agent_data.get("config", {}).get("retry_attempts", 3),
                memory_limit_mb=agent_data.get("config", {}).get("memory_limit_mb", 512),
                cpu_limit_percent=agent_data.get("config", {}).get("cpu_limit_percent", 25.0),
                api_rate_limit=agent_data.get("config", {}).get("api_rate_limit", 100),
                learning_enabled=agent_data.get("config", {}).get("learning_enabled", True),
                auto_scaling=agent_data.get("config", {}).get("auto_scaling", True)
            )
            
            metrics = AgentMetrics()
            
            agent = Agent(
                id=agent_id,
                name=agent_data["name"],
                agent_type=agent_type,
                status=AgentStatus.OFFLINE,
                capabilities=capabilities,
                config=config,
                metrics=metrics,
                description=agent_data.get("description", ""),
                tags=agent_data.get("tags", [])
            )
            
            await self._save_agent_to_database(agent)
            self.agents[agent.id] = agent
            
            self.logger.info(f"Agent '{agent.name}' created successfully with ID: {agent_id}")
            return agent
            
        except Exception as e:
            self.logger.error(f"Failed to create agent: {str(e)}")
            raise

    async def _save_agent_to_database(self, agent: Agent):
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO agents (id, name, agent_type, status, capabilities, config, metrics,
                                      version, description, tags)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    agent.id, agent.name, agent.agent_type.value, agent.status.value,
                    json.dumps([cap.value for cap in agent.capabilities]),
                    json.dumps(self._config_to_dict(agent.config)),
                    json.dumps(self._metrics_to_dict(agent.metrics)),
                    agent.version, agent.description, json.dumps(agent.tags)
                ))
                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to save agent to database: {str(e)}")
            raise

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        if agent_id in self.agents:
            return self.agents[agent_id]
        
        if not self.database:
            return None
            
        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, name, agent_type, status, capabilities, config, metrics,
                           created_at, updated_at, version, description, tags, is_active
                    FROM agents WHERE id = %s AND is_active = TRUE
                """, (agent_id,))
                
                row = result.fetchone()
                if row:
                    agent = self._create_agent_from_row(row)
                    self.agents[agent.id] = agent
                    return agent
                    
        except Exception as e:
            self.logger.error(f"Failed to get agent: {str(e)}")
            
        return None

    async def get_agent_by_name(self, name: str) -> Optional[Agent]:
        for agent in self.agents.values():
            if agent.name == name:
                return agent
                
        if not self.database:
            return None
            
        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, name, agent_type, status, capabilities, config, metrics,
                           created_at, updated_at, version, description, tags, is_active
                    FROM agents WHERE name = %s AND is_active = TRUE
                """, (name,))
                
                row = result.fetchone()
                if row:
                    agent = self._create_agent_from_row(row)
                    self.agents[agent.id] = agent
                    return agent
                    
        except Exception as e:
            self.logger.error(f"Failed to get agent by name: {str(e)}")
            
        return None

    async def get_all_agents(self, agent_type: Optional[AgentType] = None, status: Optional[AgentStatus] = None) -> List[Agent]:
        agents = list(self.agents.values())
        
        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]
            
        if status:
            agents = [a for a in agents if a.status == status]
            
        return agents

    async def update_agent_status(self, agent_id: str, new_status: AgentStatus) -> bool:
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
            
        old_status = agent.status
        agent.status = new_status
        agent.updated_at = datetime.utcnow()
        
        if not self.database:
            return True
            
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE agents SET status = %s, updated_at = %s WHERE id = %s
                """, (new_status.value, agent.updated_at, agent_id))
                await session.commit()
                
            self.logger.info(f"Agent {agent_id} status updated from {old_status.value} to {new_status.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update agent status: {str(e)}")
            return False

    async def update_agent_config(self, agent_id: str, config_updates: Dict[str, Any]) -> bool:
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
            
        # Update config fields
        for key, value in config_updates.items():
            if hasattr(agent.config, key):
                setattr(agent.config, key, value)
                
        agent.updated_at = datetime.utcnow()
        
        if not self.database:
            return True
            
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE agents SET config = %s, updated_at = %s WHERE id = %s
                """, (json.dumps(self._config_to_dict(agent.config)), agent.updated_at, agent_id))
                await session.commit()
                
            self.logger.info(f"Agent {agent_id} config updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update agent config: {str(e)}")
            return False

    async def update_agent_metrics(self, agent_id: str, metrics_updates: Dict[str, Any]) -> bool:
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
            
        # Update metrics fields
        for key, value in metrics_updates.items():
            if hasattr(agent.metrics, key):
                setattr(agent.metrics, key, value)
                
        agent.metrics.last_activity = datetime.utcnow()
        agent.updated_at = datetime.utcnow()
        
        if not self.database:
            return True
            
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE agents SET metrics = %s, updated_at = %s WHERE id = %s
                """, (json.dumps(self._metrics_to_dict(agent.metrics)), agent.updated_at, agent_id))
                await session.commit()
                
            self.logger.info(f"Agent {agent_id} metrics updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update agent metrics: {str(e)}")
            return False

    async def deactivate_agent(self, agent_id: str) -> bool:
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
            
        agent.is_active = False
        agent.status = AgentStatus.OFFLINE
        agent.updated_at = datetime.utcnow()
        
        if not self.database:
            if agent_id in self.agents:
                del self.agents[agent_id]
            return True
            
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE agents SET is_active = FALSE, status = %s, updated_at = %s WHERE id = %s
                """, (AgentStatus.OFFLINE.value, agent.updated_at, agent_id))
                await session.commit()
                
            if agent_id in self.agents:
                del self.agents[agent_id]
                
            self.logger.info(f"Agent {agent_id} deactivated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate agent: {str(e)}")
            return False

    async def get_agent_workload(self, agent_id: str, hours: int = 24) -> Dict[str, Any]:
        if not self.database:
            return {}
            
        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT timestamp, active_tasks, memory_usage, cpu_usage, response_time, error_count
                    FROM agent_workloads
                    WHERE agent_id = %s AND timestamp >= %s
                    ORDER BY timestamp DESC
                """, (agent_id, datetime.utcnow() - timedelta(hours=hours)))
                
                rows = result.fetchall()
                workload_data = []
                
                for row in rows:
                    workload_data.append({
                        "timestamp": row[0].isoformat(),
                        "active_tasks": row[1],
                        "memory_usage": float(row[2]) if row[2] else 0.0,
                        "cpu_usage": float(row[3]) if row[3] else 0.0,
                        "response_time": float(row[4]) if row[4] else 0.0,
                        "error_count": row[5]
                    })
                    
                return {
                    "agent_id": agent_id,
                    "workload_data": workload_data,
                    "summary": self._calculate_workload_summary(workload_data)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get agent workload: {str(e)}")
            return {}

    def _calculate_workload_summary(self, workload_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not workload_data:
            return {}
            
        summary = {
            "total_records": len(workload_data),
            "avg_active_tasks": 0.0,
            "avg_memory_usage": 0.0,
            "avg_cpu_usage": 0.0,
            "avg_response_time": 0.0,
            "total_errors": 0,
            "peak_memory_usage": 0.0,
            "peak_cpu_usage": 0.0
        }
        
        active_tasks = [w["active_tasks"] for w in workload_data]
        memory_usage = [w["memory_usage"] for w in workload_data if w["memory_usage"] is not None]
        cpu_usage = [w["cpu_usage"] for w in workload_data if w["cpu_usage"] is not None]
        response_times = [w["response_time"] for w in workload_data if w["response_time"] is not None]
        error_counts = [w["error_count"] for w in workload_data]
        
        if active_tasks:
            summary["avg_active_tasks"] = sum(active_tasks) / len(active_tasks)
            
        if memory_usage:
            summary["avg_memory_usage"] = sum(memory_usage) / len(memory_usage)
            summary["peak_memory_usage"] = max(memory_usage)
            
        if cpu_usage:
            summary["avg_cpu_usage"] = sum(cpu_usage) / len(cpu_usage)
            summary["peak_cpu_usage"] = max(cpu_usage)
            
        if response_times:
            summary["avg_response_time"] = sum(response_times) / len(response_times)
            
        summary["total_errors"] = sum(error_counts)
        
        return summary

    async def close(self):
        self.logger.info("Closing AgentManager...")
        if self.database:
            await self.database.close()

# Global instances and initialization functions
_agent_manager: Optional[AgentManager] = None

async def init_agent_manager() -> AgentManager:
    global _agent_manager
    if not _agent_manager:
        _agent_manager = AgentManager()
        await _agent_manager.initialize()
    return _agent_manager

async def get_agent_manager() -> AgentManager:
    global _agent_manager
    if not _agent_manager:
        _agent_manager = await init_agent_manager()
    return _agent_manager
