import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from backend.core.database import get_database
from backend.core.cache import get_redis
from backend.core.logs import get_logger
from backend.core.config import get_config
from backend.core.event_bus import get_kafka


class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_USER = "waiting_for_user"
    WAITING_FOR_AGENT = "waiting_for_agent"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TicketCategory(Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    ACCOUNT = "account"
    INTEGRATION = "integration"
    GENERAL = "general"


class SupportChannel(Enum):
    EMAIL = "email"
    CHAT = "chat"
    PHONE = "phone"
    TICKET = "ticket"
    SOCIAL_MEDIA = "social_media"


@dataclass
class SupportTicket:
    id: str
    user_id: str
    user_email: str
    subject: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    channel: SupportChannel
    assigned_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolution_time: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    internal_notes: str = ""


@dataclass
class TicketResponse:
    id: str
    ticket_id: str
    responder_id: str
    responder_type: str  # "user", "agent", "admin"
    message: str
    is_internal: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    attachments: List[str] = field(default_factory=list)


@dataclass
class SupportAgent:
    id: str
    name: str
    email: str
    specialization: List[str]
    current_tickets: int
    max_tickets: int
    availability: bool
    performance_score: float
    last_activity: datetime


@dataclass
class SupportMetrics:
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    average_resolution_time: float
    customer_satisfaction_score: float
    first_response_time: float
    agent_utilization: float


class UserSupport:
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()
        self.kafka = get_kafka()
        self.support_agents: Dict[str, SupportAgent] = {}
        self.active_tickets: Dict[str, SupportTicket] = {}

    async def initialize(self):
        """Initialize the user support system"""
        try:
            await self._setup_support_tables()
            await self._load_support_agents()
            await self._load_active_tickets()
            self.logger.info("UserSupport initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize UserSupport: {e}")
            raise

    async def _setup_support_tables(self):
        """Create support system tables"""
        async with self.db.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id VARCHAR(100) PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    user_email VARCHAR(255) NOT NULL,
                    subject VARCHAR(500) NOT NULL,
                    description TEXT NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    priority VARCHAR(20) NOT NULL,
                    status VARCHAR(30) NOT NULL,
                    channel VARCHAR(30) NOT NULL,
                    assigned_agent VARCHAR(100),
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    resolved_at TIMESTAMP,
                    resolution_time DOUBLE PRECISION,
                    tags JSONB DEFAULT '[]',
                    attachments JSONB DEFAULT '[]',
                    internal_notes TEXT DEFAULT '',
                    created_at_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS ticket_responses (
                    id VARCHAR(100) PRIMARY KEY,
                    ticket_id VARCHAR(100) NOT NULL,
                    responder_id VARCHAR(100) NOT NULL,
                    responder_type VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    is_internal BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP NOT NULL,
                    attachments JSONB DEFAULT '[]',
                    created_at_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS support_agents (
                    id VARCHAR(100) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    specialization JSONB NOT NULL,
                    current_tickets INTEGER DEFAULT 0,
                    max_tickets INTEGER DEFAULT 10,
                    availability BOOLEAN DEFAULT TRUE,
                    performance_score DOUBLE PRECISION DEFAULT 0.0,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS support_metrics (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    total_tickets INTEGER NOT NULL,
                    open_tickets INTEGER NOT NULL,
                    resolved_tickets INTEGER NOT NULL,
                    average_resolution_time DOUBLE PRECISION NOT NULL,
                    customer_satisfaction_score DOUBLE PRECISION NOT NULL,
                    first_response_time DOUBLE PRECISION NOT NULL,
                    agent_utilization DOUBLE PRECISION NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.commit()

    async def _load_support_agents(self):
        """Load support agents from database"""
        try:
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT * FROM support_agents WHERE availability = TRUE
                """)
                
                rows = result.fetchall()
                for row in rows:
                    agent = SupportAgent(
                        id=row.id,
                        name=row.name,
                        email=row.email,
                        specialization=row.specialization,
                        current_tickets=row.current_tickets,
                        max_tickets=row.max_tickets,
                        availability=row.availability,
                        performance_score=row.performance_score,
                        last_activity=row.last_activity
                    )
                    self.support_agents[agent.id] = agent
                
                self.logger.info(f"Loaded {len(self.support_agents)} support agents")
                
        except Exception as e:
            self.logger.error(f"Error loading support agents: {e}")

    async def _load_active_tickets(self):
        """Load active tickets from database"""
        try:
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT * FROM support_tickets 
                    WHERE status NOT IN ('resolved', 'closed', 'cancelled')
                    ORDER BY priority DESC, created_at ASC
                """)
                
                rows = result.fetchall()
                for row in rows:
                    ticket = SupportTicket(
                        id=row.id,
                        user_id=row.user_id,
                        user_email=row.user_email,
                        subject=row.subject,
                        description=row.description,
                        category=TicketCategory(row.category),
                        priority=TicketPriority(row.priority),
                        status=TicketStatus(row.status),
                        channel=SupportChannel(row.channel),
                        assigned_agent=row.assigned_agent,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                        resolved_at=row.resolved_at,
                        resolution_time=row.resolution_time,
                        tags=row.tags or [],
                        attachments=row.attachments or [],
                        internal_notes=row.internal_notes or ""
                    )
                    self.active_tickets[ticket.id] = ticket
                
                self.logger.info(f"Loaded {len(self.active_tickets)} active tickets")
                
        except Exception as e:
            self.logger.error(f"Error loading active tickets: {e}")

    async def create_support_ticket(self, user_id: str, user_email: str, subject: str, 
                                  description: str, category: TicketCategory, 
                                  priority: TicketPriority, channel: SupportChannel,
                                  tags: Optional[List[str]] = None) -> SupportTicket:
        """Create a new support ticket"""
        try:
            ticket_id = f"ticket_{uuid.uuid4().hex[:8]}"
            
            # Auto-assign priority based on category and keywords
            auto_priority = self._auto_assign_priority(category, description, subject)
            if auto_priority.value > priority.value:
                priority = auto_priority
            
            ticket = SupportTicket(
                id=ticket_id,
                user_id=user_id,
                user_email=user_email,
                subject=subject,
                description=description,
                category=category,
                priority=priority,
                status=TicketStatus.OPEN,
                channel=channel,
                tags=tags or []
            )
            
            # Auto-assign agent if possible
            assigned_agent = await self._auto_assign_agent(ticket)
            if assigned_agent:
                ticket.assigned_agent = assigned_agent
                ticket.status = TicketStatus.IN_PROGRESS
            
            # Save to database
            await self._save_ticket_to_database(ticket)
            
            # Add to active tickets
            self.active_tickets[ticket.id] = ticket
            
            # Update agent workload
            if ticket.assigned_agent:
                await self._update_agent_workload(ticket.assigned_agent, 1)
            
            # Publish ticket creation event
            await self._publish_ticket_event("ticket_created", ticket)
            
            # Send notification
            await self._send_ticket_notification(ticket, "created")
            
            # Broadcast ticket creation via WebSocket (to admins)
            try:
                from backend.core.realtime.websocket_router import broadcast_alert
                await broadcast_alert({
                    "id": ticket_id,
                    "source": "support",
                    "severity": priority.value,
                    "title": f"New Support Ticket: {subject}",
                    "message": f"Ticket created by {user_email}: {description[:100]}",
                    "status": ticket.status.value,
                    "created_at": ticket.created_at.isoformat() if ticket.created_at else datetime.utcnow().isoformat(),
                    "metadata": {
                        "ticket_id": ticket_id,
                        "user_id": user_id,
                        "user_email": user_email,
                        "category": category.value,
                        "priority": priority.value,
                        "assigned_agent": ticket.assigned_agent
                    }
                })
            except Exception as e:
                self.logger.warning(f"Failed to broadcast ticket creation: {e}")
            
            self.logger.info(f"Created support ticket {ticket_id} for user {user_email}")
            
            return ticket
            
        except Exception as e:
            self.logger.error(f"Error creating support ticket: {e}")
            raise

    def _auto_assign_priority(self, category: TicketCategory, description: str, 
                             subject: str) -> TicketPriority:
        """Auto-assign priority based on category and content"""
        try:
            # Critical keywords
            critical_keywords = ["urgent", "critical", "down", "broken", "error", "crash", "security"]
            high_keywords = ["important", "blocking", "issue", "problem", "bug", "fail"]
            
            content = f"{subject} {description}".lower()
            
            # Check for critical keywords
            if any(keyword in content for keyword in critical_keywords):
                return TicketPriority.CRITICAL
            
            # Check for high priority keywords
            if any(keyword in content for keyword in high_keywords):
                return TicketPriority.HIGH
            
            # Category-based priority
            category_priorities = {
                TicketCategory.BILLING: TicketPriority.MEDIUM,
                TicketCategory.TECHNICAL: TicketPriority.HIGH,
                TicketCategory.BUG_REPORT: TicketPriority.HIGH,
                TicketCategory.FEATURE_REQUEST: TicketPriority.LOW,
                TicketCategory.ACCOUNT: TicketPriority.MEDIUM,
                TicketCategory.INTEGRATION: TicketPriority.MEDIUM,
                TicketCategory.GENERAL: TicketPriority.LOW
            }
            
            return category_priorities.get(category, TicketPriority.MEDIUM)
            
        except Exception as e:
            self.logger.warning(f"Could not auto-assign priority: {e}")
            return TicketPriority.MEDIUM

    async def _auto_assign_agent(self, ticket: SupportTicket) -> Optional[str]:
        """Auto-assign the best available agent for a ticket"""
        try:
            available_agents = [
                agent for agent in self.support_agents.values()
                if agent.availability and agent.current_tickets < agent.max_tickets
            ]
            
            if not available_agents:
                return None
            
            # Score agents based on specialization, workload, and performance
            agent_scores = []
            for agent in available_agents:
                score = 0
                
                # Specialization match (40% weight)
                if ticket.category.value in agent.specialization:
                    score += 40
                elif any(spec in ticket.category.value for spec in agent.specialization):
                    score += 20
                
                # Workload balance (30% weight)
                workload_ratio = agent.current_tickets / agent.max_tickets
                score += 30 * (1 - workload_ratio)
                
                # Performance score (30% weight)
                score += 30 * (agent.performance_score / 100)
                
                agent_scores.append((agent.id, score))
            
            # Return agent with highest score
            if agent_scores:
                best_agent_id = max(agent_scores, key=lambda x: x[1])[0]
                return best_agent_id
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Could not auto-assign agent: {e}")
            return None

    async def _save_ticket_to_database(self, ticket: SupportTicket):
        """Save ticket to database"""
        try:
            async with self.db.get_session() as session:
                await session.execute("""
                    INSERT INTO support_tickets (
                        id, user_id, user_email, subject, description, category, priority,
                        status, channel, assigned_agent, created_at, updated_at, tags, attachments
                    ) VALUES (
                        :id, :user_id, :user_email, :subject, :description, :category, :priority,
                        :status, :channel, :assigned_agent, :created_at, :updated_at, :tags, :attachments
                    )
                """, {
                    "id": ticket.id,
                    "user_id": ticket.user_id,
                    "user_email": ticket.user_email,
                    "subject": ticket.subject,
                    "description": ticket.description,
                    "category": ticket.category.value,
                    "priority": ticket.priority.value,
                    "status": ticket.status.value,
                    "channel": ticket.channel.value,
                    "assigned_agent": ticket.assigned_agent,
                    "created_at": ticket.created_at,
                    "updated_at": ticket.updated_at,
                    "tags": ticket.tags,
                    "attachments": ticket.attachments
                })
                await session.commit()
        except Exception as e:
            self.logger.error(f"Error saving ticket to database: {e}")
            raise

    async def _update_agent_workload(self, agent_id: str, change: int):
        """Update agent's current ticket count"""
        try:
            if agent_id in self.support_agents:
                self.support_agents[agent_id].current_tickets += change
                
                # Update in database
                async with self.db.get_session() as session:
                    await session.execute("""
                        UPDATE support_agents 
                        SET current_tickets = current_tickets + :change
                        WHERE id = :agent_id
                    """, {
                        "change": change,
                        "agent_id": agent_id
                    })
                    await session.commit()
                    
        except Exception as e:
            self.logger.warning(f"Could not update agent workload: {e}")

    async def _publish_ticket_event(self, event_type: str, ticket: SupportTicket):
        """Publish ticket event to Kafka"""
        try:
            event_data = {
                "event_type": event_type,
                "ticket_id": ticket.id,
                "user_id": ticket.user_id,
                "user_email": ticket.user_email,
                "priority": ticket.priority.value,
                "category": ticket.category.value,
                "status": ticket.status.value,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.kafka.publish_event("support_tickets", event_data)
            
        except Exception as e:
            self.logger.warning(f"Could not publish ticket event: {e}")

    async def _send_ticket_notification(self, ticket: SupportTicket, action: str):
        """Send ticket notification"""
        try:
            notification_data = {
                "type": f"ticket_{action}",
                "ticket_id": ticket.id,
                "user_email": ticket.user_email,
                "subject": ticket.subject,
                "priority": ticket.priority.value,
                "category": ticket.category.value,
                "assigned_agent": ticket.assigned_agent,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in Redis for notification service
            await self.redis.set(
                f"notifications:support:{ticket.id}",
                notification_data,
                expire=3600
            )
            
        except Exception as e:
            self.logger.warning(f"Could not send ticket notification: {e}")

    async def update_ticket_status(self, ticket_id: str, new_status: TicketStatus, 
                                 agent_id: Optional[str] = None, 
                                 internal_notes: Optional[str] = None) -> bool:
        """Update ticket status"""
        try:
            if ticket_id not in self.active_tickets:
                raise ValueError(f"Ticket {ticket_id} not found")
            
            ticket = self.active_tickets[ticket_id]
            old_status = ticket.status
            old_agent = ticket.assigned_agent
            
            # Update ticket
            ticket.status = new_status
            ticket.updated_at = datetime.utcnow()
            
            if agent_id and agent_id != ticket.assigned_agent:
                # Update agent assignment
                if old_agent:
                    await self._update_agent_workload(old_agent, -1)
                ticket.assigned_agent = agent_id
                await self._update_agent_workload(agent_id, 1)
            
            if internal_notes:
                ticket.internal_notes = internal_notes
            
            # Handle status-specific actions
            if new_status == TicketStatus.RESOLVED:
                ticket.resolved_at = datetime.utcnow()
                if ticket.created_at and ticket.resolved_at:
                    ticket.resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds()
                
                # Remove from active tickets
                del self.active_tickets[ticket_id]
                
                # Update agent workload
                if ticket.assigned_agent:
                    await self._update_agent_workload(ticket.assigned_agent, -1)
            
            # Update in database
            await self._update_ticket_in_database(ticket)
            
            # Publish status change event
            await self._publish_ticket_event("ticket_status_changed", ticket)
            
            # Send notification
            await self._send_ticket_notification(ticket, "status_updated")
            
            self.logger.info(f"Updated ticket {ticket_id} status from {old_status.value} to {new_status.value}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating ticket status: {e}")
            return False

    async def _update_ticket_in_database(self, ticket: SupportTicket):
        """Update ticket in database"""
        try:
            async with self.db.get_session() as session:
                await session.execute("""
                    UPDATE support_tickets 
                    SET status = :status, updated_at = :updated_at, assigned_agent = :assigned_agent,
                        resolved_at = :resolved_at, resolution_time = :resolution_time,
                        internal_notes = :internal_notes
                    WHERE id = :id
                """, {
                    "status": ticket.status.value,
                    "updated_at": ticket.updated_at,
                    "assigned_agent": ticket.assigned_agent,
                    "resolved_at": ticket.resolved_at,
                    "resolution_time": ticket.resolution_time,
                    "internal_notes": ticket.internal_notes,
                    "id": ticket.id
                })
                await session.commit()
        except Exception as e:
            self.logger.error(f"Error updating ticket in database: {e}")
            raise

    async def add_ticket_response(self, ticket_id: str, responder_id: str, 
                                responder_type: str, message: str, 
                                is_internal: bool = False, 
                                attachments: Optional[List[str]] = None) -> TicketResponse:
        """Add a response to a ticket"""
        try:
            if ticket_id not in self.active_tickets:
                raise ValueError(f"Ticket {ticket_id} not found")
            
            response_id = f"response_{uuid.uuid4().hex[:8]}"
            
            response = TicketResponse(
                id=response_id,
                ticket_id=ticket_id,
                responder_id=responder_id,
                responder_type=responder_type,
                message=message,
                is_internal=is_internal,
                attachments=attachments or []
            )
            
            # Save to database
            await self._save_response_to_database(response)
            
            # Update ticket timestamp
            ticket = self.active_tickets[ticket_id]
            ticket.updated_at = datetime.utcnow()
            await self._update_ticket_in_database(ticket)
            
            # Publish response event
            await self._publish_ticket_event("ticket_response_added", ticket)
            
            self.logger.info(f"Added response to ticket {ticket_id}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error adding ticket response: {e}")
            raise

    async def _save_response_to_database(self, response: TicketResponse):
        """Save response to database"""
        try:
            async with self.db.get_session() as session:
                await session.execute("""
                    INSERT INTO ticket_responses (
                        id, ticket_id, responder_id, responder_type, message, 
                        is_internal, created_at, attachments
                    ) VALUES (
                        :id, :ticket_id, :responder_id, :responder_type, :message,
                        :is_internal, :created_at, :attachments
                    )
                """, {
                    "id": response.id,
                    "ticket_id": response.ticket_id,
                    "responder_id": response.responder_id,
                    "responder_type": response.responder_type,
                    "message": response.message,
                    "is_internal": response.is_internal,
                    "created_at": response.created_at,
                    "attachments": response.attachments
                })
                await session.commit()
        except Exception as e:
            self.logger.error(f"Error saving response to database: {e}")
            raise

    async def get_ticket(self, ticket_id: str) -> Optional[SupportTicket]:
        """Get a specific ticket"""
        try:
            # Check active tickets first
            if ticket_id in self.active_tickets:
                return self.active_tickets[ticket_id]
            
            # Check database for resolved/closed tickets
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT * FROM support_tickets WHERE id = :ticket_id
                """, {"ticket_id": ticket_id})
                
                row = result.fetchone()
                if row:
                    return SupportTicket(
                        id=row.id,
                        user_id=row.user_id,
                        user_email=row.user_email,
                        subject=row.subject,
                        description=row.description,
                        category=TicketCategory(row.category),
                        priority=TicketPriority(row.priority),
                        status=TicketStatus(row.status),
                        channel=SupportChannel(row.channel),
                        assigned_agent=row.assigned_agent,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                        resolved_at=row.resolved_at,
                        resolution_time=row.resolution_time,
                        tags=row.tags or [],
                        attachments=row.attachments or [],
                        internal_notes=row.internal_notes or ""
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting ticket {ticket_id}: {e}")
            return None

    async def get_ticket_responses(self, ticket_id: str) -> List[TicketResponse]:
        """Get all responses for a ticket"""
        try:
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT * FROM ticket_responses 
                    WHERE ticket_id = :ticket_id
                    ORDER BY created_at ASC
                """, {"ticket_id": ticket_id})
                
                rows = result.fetchall()
                responses = []
                for row in rows:
                    response = TicketResponse(
                        id=row.id,
                        ticket_id=row.ticket_id,
                        responder_id=row.responder_id,
                        responder_type=row.responder_type,
                        message=row.message,
                        is_internal=row.is_internal,
                        created_at=row.created_at,
                        attachments=row.attachments or []
                    )
                    responses.append(response)
                
                return responses
                
        except Exception as e:
            self.logger.error(f"Error getting ticket responses: {e}")
            return []

    async def search_tickets(self, filters: Dict[str, Any]) -> List[SupportTicket]:
        """Search tickets based on filters"""
        try:
            async with self.db.get_session() as session:
                # Build query based on filters
                query = "SELECT * FROM support_tickets WHERE 1=1"
                params = {}
                
                if "user_id" in filters:
                    query += " AND user_id = :user_id"
                    params["user_id"] = filters["user_id"]
                
                if "status" in filters:
                    query += " AND status = :status"
                    params["status"] = filters["status"]
                
                if "priority" in filters:
                    query += " AND priority = :priority"
                    params["priority"] = filters["priority"]
                
                if "category" in filters:
                    query += " AND category = :category"
                    params["category"] = filters["category"]
                
                if "assigned_agent" in filters:
                    query += " AND assigned_agent = :assigned_agent"
                    params["assigned_agent"] = filters["assigned_agent"]
                
                if "date_from" in filters:
                    query += " AND created_at >= :date_from"
                    params["date_from"] = filters["date_from"]
                
                if "date_to" in filters:
                    query += " AND created_at <= :date_to"
                    params["date_to"] = filters["date_to"]
                
                query += " ORDER BY priority DESC, created_at DESC"
                
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                tickets = []
                for row in rows:
                    ticket = SupportTicket(
                        id=row.id,
                        user_id=row.user_id,
                        user_email=row.user_email,
                        subject=row.subject,
                        description=row.description,
                        category=TicketCategory(row.category),
                        priority=TicketPriority(row.priority),
                        status=TicketStatus(row.status),
                        channel=SupportChannel(row.channel),
                        assigned_agent=row.assigned_agent,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                        resolved_at=row.resolved_at,
                        resolution_time=row.resolution_time,
                        tags=row.tags or [],
                        attachments=row.attachments or [],
                        internal_notes=row.internal_notes or ""
                    )
                    tickets.append(ticket)
                
                return tickets
                
        except Exception as e:
            self.logger.error(f"Error searching tickets: {e}")
            return []

    async def get_support_metrics(self, date: Optional[datetime] = None) -> SupportMetrics:
        """Get support system metrics"""
        try:
            if date is None:
                date = datetime.utcnow().date()
            
            async with self.db.get_session() as session:
                # Get metrics for the specified date
                result = await session.execute("""
                    SELECT * FROM support_metrics WHERE date = :date
                """, {"date": date})
                
                row = result.fetchone()
                if row:
                    return SupportMetrics(
                        total_tickets=row.total_tickets,
                        open_tickets=row.open_tickets,
                        resolved_tickets=row.resolved_tickets,
                        average_resolution_time=row.average_resolution_time,
                        customer_satisfaction_score=row.customer_satisfaction_score,
                        first_response_time=row.first_response_time,
                        agent_utilization=row.agent_utilization
                    )
                
                # Calculate metrics if not found
                return await self._calculate_support_metrics(session, date)
                
        except Exception as e:
            self.logger.error(f"Error getting support metrics: {e}")
            return SupportMetrics(0, 0, 0, 0.0, 0.0, 0.0, 0.0)

    async def _calculate_support_metrics(self, session, date: datetime.date) -> SupportMetrics:
        """Calculate support metrics for a specific date"""
        try:
            # Get ticket counts
            ticket_result = await session.execute("""
                SELECT 
                    COUNT(*) as total_tickets,
                    COUNT(CASE WHEN status NOT IN ('resolved', 'closed', 'cancelled') THEN 1 END) as open_tickets,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_tickets
                FROM support_tickets
                WHERE DATE(created_at) = :date
            """, {"date": date})
            
            ticket_row = ticket_result.fetchone()
            total_tickets = ticket_row.total_tickets or 0
            open_tickets = ticket_row.open_tickets or 0
            resolved_tickets = ticket_row.resolved_tickets or 0
            
            # Get average resolution time
            resolution_result = await session.execute("""
                SELECT AVG(resolution_time) as avg_resolution_time
                FROM support_tickets
                WHERE DATE(created_at) = :date AND resolution_time IS NOT NULL
            """, {"date": date})
            
            resolution_row = resolution_result.fetchone()
            average_resolution_time = resolution_row.avg_resolution_time or 0.0
            
            # Get first response time (simplified calculation)
            first_response_result = await session.execute("""
                SELECT AVG(EXTRACT(EPOCH FROM (tr.created_at - st.created_at))) as avg_first_response
                FROM support_tickets st
                JOIN ticket_responses tr ON st.id = tr.ticket_id
                WHERE DATE(st.created_at) = :date AND tr.responder_type = 'agent'
            """, {"date": date})
            
            first_response_row = first_response_result.fetchone()
            first_response_time = first_response_row.avg_first_response or 0.0
            
            # Calculate agent utilization
            agent_utilization = 0.0
            if self.support_agents:
                total_capacity = sum(agent.max_tickets for agent in self.support_agents.values())
                total_current = sum(agent.current_tickets for agent in self.support_agents.values())
                if total_capacity > 0:
                    agent_utilization = (total_current / total_capacity) * 100
            
            # Calculate customer satisfaction based on support metrics
            # Factors: resolution time, first response time, resolution rate
            customer_satisfaction_score = 50.0  # Base score
            
            if total_tickets > 0:
                # Resolution rate factor (0-30 points)
                resolution_rate = (resolved_tickets / total_tickets) * 100
                resolution_score = min(30.0, (resolution_rate / 100) * 30)
                customer_satisfaction_score += resolution_score
                
                # First response time factor (0-20 points)
                # Faster response = higher score
                if first_response_time > 0:
                    # Target: < 1 hour = 20 points, < 4 hours = 15 points, < 24 hours = 10 points
                    if first_response_time < 3600:  # < 1 hour
                        response_score = 20.0
                    elif first_response_time < 14400:  # < 4 hours
                        response_score = 15.0
                    elif first_response_time < 86400:  # < 24 hours
                        response_score = 10.0
                    else:
                        response_score = 5.0
                    customer_satisfaction_score += response_score
                
                # Resolution time factor (0-20 points)
                # Faster resolution = higher score
                if average_resolution_time > 0:
                    # Target: < 24 hours = 20 points, < 48 hours = 15 points, < 7 days = 10 points
                    resolution_hours = average_resolution_time / 3600
                    if resolution_hours < 24:
                        resolution_time_score = 20.0
                    elif resolution_hours < 48:
                        resolution_time_score = 15.0
                    elif resolution_hours < 168:  # 7 days
                        resolution_time_score = 10.0
                    else:
                        resolution_time_score = 5.0
                    customer_satisfaction_score += resolution_time_score
                
                # Agent utilization factor (0-10 points)
                # Optimal utilization (60-80%) = higher score
                if 60 <= agent_utilization <= 80:
                    utilization_score = 10.0
                elif 40 <= agent_utilization < 60 or 80 < agent_utilization <= 90:
                    utilization_score = 7.0
                else:
                    utilization_score = 5.0
                customer_satisfaction_score += utilization_score
            
            # Ensure score is between 0 and 100
            customer_satisfaction_score = min(100.0, max(0.0, customer_satisfaction_score))
            
            metrics = SupportMetrics(
                total_tickets=total_tickets,
                open_tickets=open_tickets,
                resolved_tickets=resolved_tickets,
                average_resolution_time=average_resolution_time,
                customer_satisfaction_score=customer_satisfaction_score,
                first_response_time=first_response_time,
                agent_utilization=agent_utilization
            )
            
            # Save metrics for future use
            await self._save_support_metrics(session, date, metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating support metrics: {e}")
            return SupportMetrics(0, 0, 0, 0.0, 0.0, 0.0, 0.0)

    async def _save_support_metrics(self, session, date: datetime.date, metrics: SupportMetrics):
        """Save support metrics to database"""
        try:
            await session.execute("""
                INSERT INTO support_metrics (
                    date, total_tickets, open_tickets, resolved_tickets,
                    average_resolution_time, customer_satisfaction_score,
                    first_response_time, agent_utilization
                ) VALUES (
                    :date, :total_tickets, :open_tickets, :resolved_tickets,
                    :average_resolution_time, :customer_satisfaction_score,
                    :first_response_time, :agent_utilization
                )
            """, {
                "date": date,
                "total_tickets": metrics.total_tickets,
                "open_tickets": metrics.open_tickets,
                "resolved_tickets": metrics.resolved_tickets,
                "average_resolution_time": metrics.average_resolution_time,
                "customer_satisfaction_score": metrics.customer_satisfaction_score,
                "first_response_time": metrics.first_response_time,
                "agent_utilization": metrics.agent_utilization
            })
            await session.commit()
        except Exception as e:
            self.logger.warning(f"Could not save support metrics: {e}")

    async def close(self):
        """Clean up resources"""
        self.logger.info("UserSupport closed")


# Singleton instances
_user_support = None


async def get_user_support() -> UserSupport:
    """Get the UserSupport singleton instance"""
    global _user_support
    if _user_support is None:
        _user_support = UserSupport()
        await _user_support.initialize()
    return _user_support


async def init_user_support() -> UserSupport:
    """Initialize and return a new UserSupport instance"""
    support = UserSupport()
    await support.initialize()
    return support
