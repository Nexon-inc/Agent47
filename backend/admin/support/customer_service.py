import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text

from backend.core.database import get_database, DatabaseManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class ServiceChannel(Enum):
    EMAIL = "email"
    PHONE = "phone"
    CHAT = "chat"
    TICKET = "ticket"
    SOCIAL = "social"
    WEB = "web"

class ServiceStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    BREAK = "break"
    TRAINING = "training"

class InteractionType(Enum):
    INQUIRY = "inquiry"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    TECHNICAL_SUPPORT = "technical_support"
    BILLING = "billing"
    ACCOUNT = "account"
    SALES = "sales"
    GENERAL = "general"

class InteractionStatus(Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    TRANSFERRED = "transferred"
    ABANDONED = "abandoned"

@dataclass
class CustomerServiceAgent:
    agent_id: str
    name: str
    email: str
    status: ServiceStatus
    channels: List[ServiceChannel]
    skills: List[str]
    max_concurrent_interactions: int
    current_interactions: int
    total_interactions: int
    average_rating: float
    last_active: datetime
    metadata: Dict[str, Any]

@dataclass
class CustomerInteraction:
    interaction_id: str
    customer_id: str
    customer_name: str
    customer_email: str
    agent_id: Optional[str]
    channel: ServiceChannel
    interaction_type: InteractionType
    status: InteractionStatus
    subject: str
    description: str
    priority: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    resolution: Optional[str]
    customer_satisfaction: Optional[int]
    tags: List[str]
    metadata: Dict[str, Any]

@dataclass
class ServiceQueue:
    queue_id: str
    name: str
    description: str
    channel: ServiceChannel
    interaction_type: InteractionType
    priority: str
    max_wait_time_minutes: int
    current_wait_time_minutes: int
    queue_length: int
    average_handle_time_minutes: int
    is_active: bool
    metadata: Dict[str, Any]

@dataclass
class ServiceMetrics:
    total_interactions: int
    active_interactions: int
    resolved_interactions: int
    average_resolution_time_minutes: float
    customer_satisfaction_score: float
    first_contact_resolution_rate: float
    agent_utilization_rate: float
    queue_wait_time_minutes: float

class CustomerService(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.agents: Dict[str, CustomerServiceAgent] = {}
        self.active_interactions: Dict[str, CustomerInteraction] = {}
        self.service_queues: Dict[str, ServiceQueue] = {}
        self.routing_rules: List[Dict[str, Any]] = []
        self.escalation_rules: List[Dict[str, Any]] = []
        self.sla_rules: Dict[str, Dict[str, Any]] = {}
        self.auto_response_templates: Dict[str, str] = {}

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing CustomerService...")
            self.database = get_database()
            await self._setup_customer_service_tables()
            await self._load_agents()
            await self._load_service_queues()
            await self._load_configuration()
            await self._start_background_tasks()
            self.logger.info("CustomerService initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize CustomerService: {str(e)}")
            return False

    async def _setup_customer_service_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS customer_service_agents (
                    id SERIAL PRIMARY KEY,
                    agent_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    channels JSONB DEFAULT '[]'::jsonb,
                    skills JSONB DEFAULT '[]'::jsonb,
                    max_concurrent_interactions INTEGER DEFAULT 5,
                    current_interactions INTEGER DEFAULT 0,
                    total_interactions INTEGER DEFAULT 0,
                    average_rating FLOAT DEFAULT 0.0,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS customer_interactions (
                    id SERIAL PRIMARY KEY,
                    interaction_id VARCHAR(255) UNIQUE NOT NULL,
                    customer_id VARCHAR(255) NOT NULL,
                    customer_name VARCHAR(255) NOT NULL,
                    customer_email VARCHAR(255) NOT NULL,
                    agent_id VARCHAR(255),
                    channel VARCHAR(20) NOT NULL,
                    interaction_type VARCHAR(30) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    subject VARCHAR(500) NOT NULL,
                    description TEXT NOT NULL,
                    priority VARCHAR(20) NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    duration_seconds INTEGER,
                    resolution TEXT,
                    customer_satisfaction INTEGER CHECK (customer_satisfaction >= 1 AND customer_satisfaction <= 5),
                    tags JSONB DEFAULT '[]'::jsonb,
                    metadata JSONB DEFAULT '{}'::jsonb
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS service_queues (
                    id SERIAL PRIMARY KEY,
                    queue_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    channel VARCHAR(20) NOT NULL,
                    interaction_type VARCHAR(30) NOT NULL,
                    priority VARCHAR(20) NOT NULL,
                    max_wait_time_minutes INTEGER DEFAULT 30,
                    current_wait_time_minutes INTEGER DEFAULT 0,
                    queue_length INTEGER DEFAULT 0,
                    average_handle_time_minutes INTEGER DEFAULT 15,
                    is_active BOOLEAN DEFAULT TRUE,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS interaction_messages (
                    id SERIAL PRIMARY KEY,
                    message_id VARCHAR(255) UNIQUE NOT NULL,
                    interaction_id VARCHAR(255) NOT NULL,
                    sender_id VARCHAR(255) NOT NULL,
                    sender_type VARCHAR(20) NOT NULL,
                    message_type VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    FOREIGN KEY (interaction_id) REFERENCES customer_interactions(interaction_id)
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS service_escalations (
                    id SERIAL PRIMARY KEY,
                    escalation_id VARCHAR(255) UNIQUE NOT NULL,
                    interaction_id VARCHAR(255) NOT NULL,
                    escalated_from VARCHAR(255) NOT NULL,
                    escalated_to VARCHAR(255) NOT NULL,
                    reason TEXT NOT NULL,
                    escalated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    FOREIGN KEY (interaction_id) REFERENCES customer_interactions(interaction_id)
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_customer_service_agents_status 
                ON customer_service_agents(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_customer_interactions_status 
                ON customer_interactions(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_customer_interactions_agent_id 
                ON customer_interactions(agent_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_customer_interactions_customer_id 
                ON customer_interactions(customer_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_customer_interactions_channel 
                ON customer_interactions(channel);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_customer_interactions_started_at 
                ON customer_interactions(started_at);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_interaction_messages_interaction_id 
                ON interaction_messages(interaction_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_interaction_messages_timestamp 
                ON interaction_messages(timestamp);
            """)
            
            await session.commit()

    async def _load_agents(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT agent_id, name, email, status, channels, skills, max_concurrent_interactions,
                       current_interactions, total_interactions, average_rating, last_active, metadata
                FROM customer_service_agents
            """)
            
            for row in result:
                agent = CustomerServiceAgent(
                    agent_id=row.agent_id,
                    name=row.name,
                    email=row.email,
                    status=ServiceStatus(row.status),
                    channels=[ServiceChannel(ch) for ch in row.channels],
                    skills=row.skills or [],
                    max_concurrent_interactions=row.max_concurrent_interactions,
                    current_interactions=row.current_interactions,
                    total_interactions=row.total_interactions,
                    average_rating=row.average_rating,
                    last_active=row.last_active,
                    metadata=row.metadata or {}
                )
                self.agents[agent.agent_id] = agent

    async def _load_service_queues(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT queue_id, name, description, channel, interaction_type, priority,
                       max_wait_time_minutes, current_wait_time_minutes, queue_length,
                       average_handle_time_minutes, is_active, metadata
                FROM service_queues
                WHERE is_active = TRUE
            """)
            
            for row in result:
                queue = ServiceQueue(
                    queue_id=row.queue_id,
                    name=row.name,
                    description=row.description or "",
                    channel=ServiceChannel(row.channel),
                    interaction_type=InteractionType(row.interaction_type),
                    priority=row.priority,
                    max_wait_time_minutes=row.max_wait_time_minutes,
                    current_wait_time_minutes=row.current_wait_time_minutes,
                    queue_length=row.queue_length,
                    average_handle_time_minutes=row.average_handle_time_minutes,
                    is_active=row.is_active,
                    metadata=row.metadata or {}
                )
                self.service_queues[queue.queue_id] = queue

    async def _load_configuration(self):
        self.routing_rules = [
            {
                "channel": ServiceChannel.EMAIL,
                "interaction_type": InteractionType.TECHNICAL_SUPPORT,
                "priority": "high",
                "assign_to": "technical_team",
                "sla_minutes": 60
            },
            {
                "channel": ServiceChannel.PHONE,
                "interaction_type": InteractionType.BILLING,
                "priority": "high",
                "assign_to": "billing_team",
                "sla_minutes": 30
            },
            {
                "channel": ServiceChannel.CHAT,
                "interaction_type": InteractionType.GENERAL,
                "priority": "normal",
                "assign_to": "general_team",
                "sla_minutes": 15
            }
        ]
        
        self.escalation_rules = [
            {
                "condition": "wait_time_exceeded",
                "threshold_minutes": 30,
                "action": "escalate_to_supervisor"
            },
            {
                "condition": "customer_dissatisfaction",
                "threshold_rating": 2,
                "action": "escalate_to_manager"
            }
        ]
        
        self.sla_rules = {
            "critical": {"response_minutes": 5, "resolution_minutes": 60},
            "high": {"response_minutes": 15, "resolution_minutes": 240},
            "normal": {"response_minutes": 30, "resolution_minutes": 480},
            "low": {"response_minutes": 60, "resolution_minutes": 1440}
        }

    async def _start_background_tasks(self):
        asyncio.create_task(self._queue_monitor())
        asyncio.create_task(self._sla_monitor())
        asyncio.create_task(self._escalation_monitor())

    async def _queue_monitor(self):
        while True:
            try:
                await self._process_queues()
                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"Error in queue monitor: {str(e)}")
                await asyncio.sleep(60)

    async def _sla_monitor(self):
        while True:
            try:
                await self._check_sla_violations()
                await asyncio.sleep(300)
            except Exception as e:
                self.logger.error(f"Error in SLA monitor: {str(e)}")
                await asyncio.sleep(300)

    async def _escalation_monitor(self):
        while True:
            try:
                await self._check_escalations()
                await asyncio.sleep(600)
            except Exception as e:
                self.logger.error(f"Error in escalation monitor: {str(e)}")
                await asyncio.sleep(600)

    async def create_interaction(
        self,
        customer_id: str,
        customer_name: str,
        customer_email: str,
        channel: ServiceChannel,
        interaction_type: InteractionType,
        subject: str,
        description: str,
        priority: str = "normal",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        try:
            interaction_id = f"INT_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(customer_id) % 10000}"
            
            interaction = CustomerInteraction(
                interaction_id=interaction_id,
                customer_id=customer_id,
                customer_name=customer_name,
                customer_email=customer_email,
                agent_id=None,
                channel=channel,
                interaction_type=interaction_type,
                status=InteractionStatus.ACTIVE,
                subject=subject,
                description=description,
                priority=priority,
                started_at=datetime.utcnow(),
                ended_at=None,
                duration_seconds=None,
                resolution=None,
                customer_satisfaction=None,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO customer_interactions (
                        interaction_id, customer_id, customer_name, customer_email, channel,
                        interaction_type, status, subject, description, priority, tags, metadata
                    ) VALUES (
                        :interaction_id, :customer_id, :customer_name, :customer_email, :channel,
                        :interaction_type, :status, :subject, :description, :priority, :tags, :metadata
                    )
                """, {
                    "interaction_id": interaction.interaction_id,
                    "customer_id": interaction.customer_id,
                    "customer_name": interaction.customer_name,
                    "customer_email": interaction.customer_email,
                    "channel": interaction.channel.value,
                    "interaction_type": interaction.interaction_type.value,
                    "status": interaction.status.value,
                    "subject": interaction.subject,
                    "description": interaction.description,
                    "priority": interaction.priority,
                    "tags": interaction.tags,
                    "metadata": interaction.metadata
                })
                await session.commit()
            
            await self._route_interaction(interaction)
            self.active_interactions[interaction_id] = interaction
            
            self.logger.info(f"Customer interaction created: {interaction_id}")
            return interaction_id
            
        except Exception as e:
            self.logger.error(f"Failed to create interaction: {str(e)}")
            return None

    async def _route_interaction(self, interaction: CustomerInteraction):
        try:
            best_agent = await self._find_best_agent(interaction)
            if best_agent:
                await self._assign_interaction(interaction, best_agent.agent_id)
            else:
                await self._queue_interaction(interaction)
                
        except Exception as e:
            self.logger.error(f"Failed to route interaction: {str(e)}")

    async def _find_best_agent(self, interaction: CustomerInteraction) -> Optional[CustomerServiceAgent]:
        try:
            available_agents = [
                agent for agent in self.agents.values()
                if (agent.status == ServiceStatus.AVAILABLE and
                    interaction.channel in agent.channels and
                    agent.current_interactions < agent.max_concurrent_interactions)
            ]
            
            if not available_agents:
                return None
            
            best_agent = None
            best_score = -1
            
            for agent in available_agents:
                score = 0
                
                if interaction.interaction_type.value in agent.skills:
                    score += 10
                
                if agent.average_rating > 4.0:
                    score += 5
                
                if agent.current_interactions == 0:
                    score += 3
                
                if score > best_score:
                    best_score = score
                    best_agent = agent
            
            return best_agent
            
        except Exception as e:
            self.logger.error(f"Failed to find best agent: {str(e)}")
            return None

    async def _assign_interaction(self, interaction: CustomerInteraction, agent_id: str):
        try:
            interaction.agent_id = agent_id
            interaction.status = InteractionStatus.ACTIVE
            
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE customer_interactions 
                    SET agent_id = :agent_id, status = :status
                    WHERE interaction_id = :interaction_id
                """, {
                    "interaction_id": interaction.interaction_id,
                    "agent_id": agent_id,
                    "status": interaction.status.value
                })
                
                await session.execute("""
                    UPDATE customer_service_agents 
                    SET current_interactions = current_interactions + 1, last_active = :last_active
                    WHERE agent_id = :agent_id
                """, {
                    "agent_id": agent_id,
                    "last_active": datetime.utcnow()
                })
                
                await session.commit()
            
            if agent_id in self.agents:
                self.agents[agent_id].current_interactions += 1
                self.agents[agent_id].last_active = datetime.utcnow()
            
            self.logger.info(f"Interaction {interaction.interaction_id} assigned to agent {agent_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to assign interaction: {str(e)}")

    async def _queue_interaction(self, interaction: CustomerInteraction):
        try:
            queue_id = f"queue_{interaction.channel.value}_{interaction.interaction_type.value}"
            
            if queue_id in self.service_queues:
                queue = self.service_queues[queue_id]
                queue.queue_length += 1
                
                if not self.database:
                    return
                
                async with self.database.get_session() as session:
                    await session.execute("""
                        UPDATE service_queues 
                        SET queue_length = queue_length + 1
                        WHERE queue_id = :queue_id
                    """, {"queue_id": queue_id})
                    await session.commit()
                
                self.logger.info(f"Interaction {interaction.interaction_id} queued in {queue_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to queue interaction: {str(e)}")

    async def _process_queues(self):
        try:
            for queue_id, queue in self.service_queues.items():
                if queue.queue_length > 0:
                    await self._process_queue(queue_id)
                    
        except Exception as e:
            self.logger.error(f"Failed to process queues: {str(e)}")

    async def _process_queue(self, queue_id: str):
        try:
            if queue_id not in self.service_queues:
                return
            
            queue = self.service_queues[queue_id]
            
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT interaction_id, customer_id, customer_name, customer_email, channel,
                           interaction_type, status, subject, description, priority, tags, metadata
                    FROM customer_interactions
                    WHERE agent_id IS NULL AND channel = :channel AND interaction_type = :interaction_type
                    ORDER BY started_at ASC
                    LIMIT 1
                """, {
                    "channel": queue.channel.value,
                    "interaction_type": queue.interaction_type.value
                })
                
                row = result.fetchone()
                if not row:
                    return
                
                interaction = CustomerInteraction(
                    interaction_id=row.interaction_id,
                    customer_id=row.customer_id,
                    customer_name=row.customer_name,
                    customer_email=row.customer_email,
                    agent_id=None,
                    channel=ServiceChannel(row.channel),
                    interaction_type=InteractionType(row.interaction_type),
                    status=InteractionStatus(row.status),
                    subject=row.subject,
                    description=row.description,
                    priority=row.priority,
                    started_at=datetime.utcnow(),
                    ended_at=None,
                    duration_seconds=None,
                    resolution=None,
                    customer_satisfaction=None,
                    tags=row.tags or [],
                    metadata=row.metadata or {}
                )
                
                best_agent = await self._find_best_agent(interaction)
                if best_agent:
                    await self._assign_interaction(interaction, best_agent.agent_id)
                    queue.queue_length -= 1
                    
                    await session.execute("""
                        UPDATE service_queues 
                        SET queue_length = queue_length - 1
                        WHERE queue_id = :queue_id
                    """, {"queue_id": queue_id})
                    await session.commit()
                    
        except Exception as e:
            self.logger.error(f"Failed to process queue: {str(e)}")

    async def end_interaction(
        self,
        interaction_id: str,
        resolution: str,
        customer_satisfaction: Optional[int] = None,
        ended_by: str = "system"
    ) -> bool:
        try:
            if interaction_id not in self.active_interactions:
                return False
            
            interaction = self.active_interactions[interaction_id]
            interaction.status = InteractionStatus.RESOLVED
            interaction.ended_at = datetime.utcnow()
            interaction.duration_seconds = int((interaction.ended_at - interaction.started_at).total_seconds())
            interaction.resolution = resolution
            interaction.customer_satisfaction = customer_satisfaction
            
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE customer_interactions 
                    SET status = :status, ended_at = :ended_at, duration_seconds = :duration_seconds,
                        resolution = :resolution, customer_satisfaction = :customer_satisfaction
                    WHERE interaction_id = :interaction_id
                """, {
                    "interaction_id": interaction_id,
                    "status": interaction.status.value,
                    "ended_at": interaction.ended_at,
                    "duration_seconds": interaction.duration_seconds,
                    "resolution": resolution,
                    "customer_satisfaction": customer_satisfaction
                })
                
                if interaction.agent_id:
                    await session.execute("""
                        UPDATE customer_service_agents 
                        SET current_interactions = current_interactions - 1, total_interactions = total_interactions + 1
                        WHERE agent_id = :agent_id
                    """, {"agent_id": interaction.agent_id})
                
                await session.commit()
            
            if interaction.agent_id and interaction.agent_id in self.agents:
                self.agents[interaction.agent_id].current_interactions -= 1
                self.agents[interaction.agent_id].total_interactions += 1
            
            del self.active_interactions[interaction_id]
            self.logger.info(f"Interaction ended: {interaction_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to end interaction: {str(e)}")
            return False

    async def add_interaction_message(
        self,
        interaction_id: str,
        sender_id: str,
        sender_type: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        try:
            message_id = f"MSG_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(interaction_id) % 10000}"
            
            if not self.database:
                return None
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO interaction_messages (
                        message_id, interaction_id, sender_id, sender_type, message_type, content, metadata
                    ) VALUES (
                        :message_id, :interaction_id, :sender_id, :sender_type, :message_type, :content, :metadata
                    )
                """, {
                    "message_id": message_id,
                    "interaction_id": interaction_id,
                    "sender_id": sender_id,
                    "sender_type": sender_type,
                    "message_type": message_type,
                    "content": content,
                    "metadata": metadata or {}
                })
                await session.commit()
            
            return message_id
            
        except Exception as e:
            self.logger.error(f"Failed to add interaction message: {str(e)}")
            return None

    async def _check_sla_violations(self):
        try:
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT interaction_id, priority, started_at, agent_id
                    FROM customer_interactions
                    WHERE status = 'active' AND agent_id IS NOT NULL
                """)
                
                for row in result:
                    sla_rule = self.sla_rules.get(row.priority)
                    if sla_rule:
                        response_threshold = datetime.utcnow() - timedelta(minutes=sla_rule["response_minutes"])
                        if row.started_at < response_threshold:
                            await self._handle_sla_violation(row.interaction_id, "response_time")
                    
        except Exception as e:
            self.logger.error(f"Failed to check SLA violations: {str(e)}")

    async def _check_escalations(self):
        try:
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT interaction_id, started_at, customer_satisfaction
                    FROM customer_interactions
                    WHERE status = 'active'
                """)
                
                for row in result:
                    if row.customer_satisfaction and row.customer_satisfaction <= 2:
                        await self._escalate_interaction(row.interaction_id, "customer_dissatisfaction")
                    
        except Exception as e:
            self.logger.error(f"Failed to check escalations: {str(e)}")

    async def _handle_sla_violation(self, interaction_id: str, violation_type: str):
        try:
            await self._escalate_interaction(interaction_id, f"SLA violation: {violation_type}")
            self.logger.warning(f"SLA violation detected for interaction {interaction_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle SLA violation: {str(e)}")

    async def _escalate_interaction(self, interaction_id: str, reason: str):
        try:
            if not self.database:
                return
            
            escalation_id = f"ESC_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(interaction_id) % 10000}"
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO service_escalations (
                        escalation_id, interaction_id, escalated_from, escalated_to, reason
                    ) VALUES (
                        :escalation_id, :interaction_id, :escalated_from, :escalated_to, :reason
                    )
                """, {
                    "escalation_id": escalation_id,
                    "interaction_id": interaction_id,
                    "escalated_from": "system",
                    "escalated_to": "supervisor",
                    "reason": reason
                })
                await session.commit()
            
            self.logger.warning(f"Interaction escalated: {interaction_id} - {reason}")
            
        except Exception as e:
            self.logger.error(f"Failed to escalate interaction: {str(e)}")

    async def get_interactions(
        self,
        status: Optional[InteractionStatus] = None,
        agent_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        channel: Optional[ServiceChannel] = None,
        interaction_type: Optional[InteractionType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CustomerInteraction]:
        if not self.database:
            return []
        
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if status:
            conditions.append("status = :status")
            params["status"] = status.value
        
        if agent_id:
            conditions.append("agent_id = :agent_id")
            params["agent_id"] = agent_id
        
        if customer_id:
            conditions.append("customer_id = :customer_id")
            params["customer_id"] = customer_id
        
        if channel:
            conditions.append("channel = :channel")
            params["channel"] = channel.value
        
        if interaction_type:
            conditions.append("interaction_type = :interaction_type")
            params["interaction_type"] = interaction_type.value
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT interaction_id, customer_id, customer_name, customer_email, agent_id,
                       channel, interaction_type, status, subject, description, priority,
                       started_at, ended_at, duration_seconds, resolution, customer_satisfaction,
                       tags, metadata
                FROM customer_interactions
                {where_clause}
                ORDER BY started_at DESC
                LIMIT :limit OFFSET :offset
            """, params)
            
            interactions = []
            for row in result:
                interaction = CustomerInteraction(
                    interaction_id=row.interaction_id,
                    customer_id=row.customer_id,
                    customer_name=row.customer_name,
                    customer_email=row.customer_email,
                    agent_id=row.agent_id,
                    channel=ServiceChannel(row.channel),
                    interaction_type=InteractionType(row.interaction_type),
                    status=InteractionStatus(row.status),
                    subject=row.subject,
                    description=row.description,
                    priority=row.priority,
                    started_at=row.started_at,
                    ended_at=row.ended_at,
                    duration_seconds=row.duration_seconds,
                    resolution=row.resolution,
                    customer_satisfaction=row.customer_satisfaction,
                    tags=row.tags or [],
                    metadata=row.metadata or {}
                )
                interactions.append(interaction)
            
            return interactions

    async def get_service_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ServiceMetrics:
        if not self.database:
            return ServiceMetrics(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT 
                    COUNT(*) as total_interactions,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_interactions,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_interactions,
                    AVG(duration_seconds/60.0) as avg_resolution_time_minutes,
                    AVG(customer_satisfaction) as customer_satisfaction_score,
                    COUNT(CASE WHEN status = 'resolved' AND duration_seconds < 300 THEN 1 END) as first_contact_resolved
                FROM customer_interactions
                WHERE started_at BETWEEN :start_date AND :end_date
            """, {"start_date": start_date, "end_date": end_date})
            
            row = result.fetchone()
            if not row:
                return ServiceMetrics(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)
            
            total_agents = len(self.agents)
            active_agents = len([a for a in self.agents.values() if a.status == ServiceStatus.AVAILABLE])
            agent_utilization = (active_agents / total_agents * 100) if total_agents > 0 else 0.0
            
            return ServiceMetrics(
                total_interactions=row.total_interactions,
                active_interactions=row.active_interactions,
                resolved_interactions=row.resolved_interactions,
                average_resolution_time_minutes=float(row.avg_resolution_time_minutes) if row.avg_resolution_time_minutes else 0.0,
                customer_satisfaction_score=float(row.customer_satisfaction_score) if row.customer_satisfaction_score else 0.0,
                first_contact_resolution_rate=(row.first_contact_resolved / row.total_interactions * 100) if row.total_interactions > 0 else 0.0,
                agent_utilization_rate=agent_utilization,
                queue_wait_time_minutes=0.0
            )

_customer_service: Optional[CustomerService] = None

async def get_customer_service() -> CustomerService:
    global _customer_service
    if _customer_service is None:
        _customer_service = CustomerService()
        await _customer_service.initialize()
    return _customer_service

async def init_customer_service() -> CustomerService:
    return await get_customer_service()
