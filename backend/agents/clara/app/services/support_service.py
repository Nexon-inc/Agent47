import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_clara_database
from ..models import (
    SupportTicket, CustomerInteraction, TicketEscalation, CustomerFeedback,
    SupportAgent, SupportWorkflow, TicketPriority,
    TicketStatus, TicketCategory, SupportChannel, SentimentType,
    InteractionType, ChatSession, ChatMessage
)
from core.database.models import UserProfile

logger = logging.getLogger(__name__)

class SupportService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
    
    async def initialize(self):
        """Initialize support service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Support service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize support service: {e}")
            raise
    
    async def create_ticket(
        self,
        customer_id: int,
        channel: SupportChannel,
        category: TicketCategory,
        subject: str,
        description: str,
        priority: Optional[TicketPriority] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_url: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new support ticket"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Generate ticket number
                ticket_number = f"TKT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
                
                # Auto-assign priority if not specified
                if not priority:
                    priority = await self._auto_assign_priority(description, category)
                
                # Create ticket
                ticket = SupportTicket(
                    ticket_number=ticket_number,
                    customer_id=customer_id,
                    channel=channel,
                    category=category,
                    priority=priority,
                    status=TicketStatus.OPEN,
                    subject=subject,
                    description=description,
                    tags=tags or [],
                    metadata=metadata or {},
                    source_url=source_url,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                session.add(ticket)
                await session.flush()
                
                # Auto-assign agent if possible
                assigned_agent = await self._auto_assign_agent(ticket, session)
                if assigned_agent:
                    ticket.assigned_agent_id = assigned_agent.id
                
                # Create initial interaction
                interaction = CustomerInteraction(
                    ticket_id=ticket.id,
                    interaction_type=InteractionType.CUSTOMER_MESSAGE,
                    channel=channel,
                    message=description,
                    sentiment=SentimentType.NEUTRAL,
                    is_automated=False
                )
                session.add(interaction)
                
                # Analyze sentiment
                sentiment_result = await self._analyze_sentiment(description)
                if sentiment_result["success"]:
                    ticket.sentiment_score = sentiment_result["sentiment_score"]
                    interaction.sentiment = sentiment_result["sentiment_type"]
                
                await session.commit()
                
                # Publish ticket created event
                await self.event_bus.publish_event(
                    topic="clara_ticket_created",
                    event_data={
                        "ticket_id": ticket.id,
                        "ticket_number": ticket.ticket_number,
                        "customer_id": customer_id,
                        "priority": priority.value,
                        "category": category.value,
                        "channel": channel.value
                    }
                )
                
                # Update customer profile
                await self._update_customer_profile(customer_id, session)
                
                return {
                    "success": True,
                    "ticket": {
                        "id": ticket.id,
                        "ticket_number": ticket.ticket_number,
                        "status": ticket.status.value,
                        "priority": ticket.priority.value,
                        "assigned_agent_id": ticket.assigned_agent_id,
                        "estimated_resolution_time": await self._estimate_resolution_time(ticket)
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to create ticket: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_ticket_status(
        self,
        ticket_id: int,
        status: TicketStatus,
        agent_id: int,
        notes: Optional[str] = None,
        resolution_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update ticket status"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                ticket = await session.execute(
                    select(SupportTicket).where(SupportTicket.id == ticket_id)
                )
                ticket = ticket.scalar_one_or_none()
                
                if not ticket:
                    return {"success": False, "error": "Ticket not found"}
                
                old_status = ticket.status
                ticket.status = status
                ticket.updated_at = datetime.utcnow()
                
                # Handle status-specific logic
                if status == TicketStatus.RESOLVED:
                    ticket.resolved_at = datetime.utcnow()
                    if resolution_time:
                        ticket.actual_resolution_time = resolution_time
                elif status == TicketStatus.CLOSED:
                    ticket.closed_at = datetime.utcnow()
                
                # Create status update interaction
                interaction = CustomerInteraction(
                    ticket_id=ticket_id,
                    interaction_type=InteractionType.SYSTEM_NOTIFICATION,
                    channel=ticket.channel,
                    message=f"Ticket status updated from {old_status.value} to {status.value}",
                    response=notes,
                    agent_id=agent_id,
                    is_automated=False
                )
                session.add(interaction)
                
                await session.commit()
                
                # Publish status update event
                await self.event_bus.publish_event(
                    topic="clara_ticket_status_updated",
                    event_data={
                        "ticket_id": ticket_id,
                        "old_status": old_status.value,
                        "new_status": status.value,
                        "agent_id": agent_id
                    }
                )
                
                return {"success": True, "ticket_id": ticket_id, "status": status.value}
                
        except Exception as e:
            logger.error(f"Failed to update ticket status: {e}")
            return {"success": False, "error": str(e)}
    
    async def assign_ticket(
        self,
        ticket_id: int,
        agent_id: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Assign ticket to an agent"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Check if agent exists and is available
                agent = await session.execute(
                    select(SupportAgent).where(SupportAgent.user_id == agent_id)
                )
                agent = agent.scalar_one_or_none()
                
                if not agent:
                    return {"success": False, "error": "Agent not found"}
                
                if agent.availability_status != "available":
                    return {"success": False, "error": "Agent is not available"}
                
                if agent.current_ticket_count >= agent.max_concurrent_tickets:
                    return {"success": False, "error": "Agent has reached maximum ticket limit"}
                
                # Update ticket assignment
                ticket = await session.execute(
                    select(SupportTicket).where(SupportTicket.id == ticket_id)
                )
                ticket = ticket.scalar_one_or_none()
                
                if not ticket:
                    return {"success": False, "error": "Ticket not found"}
                
                old_agent_id = ticket.assigned_agent_id
                ticket.assigned_agent_id = agent_id
                ticket.status = TicketStatus.IN_PROGRESS
                ticket.updated_at = datetime.utcnow()
                
                # Update agent ticket count
                if old_agent_id:
                    old_agent = await session.execute(
                        select(SupportAgent).where(SupportAgent.user_id == old_agent_id)
                    )
                    old_agent = old_agent.scalar_one_or_none()
                    if old_agent:
                        old_agent.current_ticket_count = max(0, old_agent.current_ticket_count - 1)
                
                agent.current_ticket_count += 1
                
                # Create assignment interaction
                interaction = CustomerInteraction(
                    ticket_id=ticket_id,
                    interaction_type=InteractionType.SYSTEM_NOTIFICATION,
                    channel=ticket.channel,
                    message=f"Ticket assigned to agent {agent.agent_code}",
                    response=reason,
                    agent_id=agent_id,
                    is_automated=False
                )
                session.add(interaction)
                
                await session.commit()
                
                # Publish assignment event
                await self.event_bus.publish_event(
                    topic="clara_ticket_assigned",
                    event_data={
                        "ticket_id": ticket_id,
                        "agent_id": agent_id,
                        "old_agent_id": old_agent_id
                    }
                )
                
                return {"success": True, "ticket_id": ticket_id, "agent_id": agent_id}
                
        except Exception as e:
            logger.error(f"Failed to assign ticket: {e}")
            return {"success": False, "error": str(e)}
    
    async def escalate_ticket(
        self,
        ticket_id: int,
        escalated_from_agent_id: int,
        escalated_to_agent_id: int,
        reason: str,
        priority_increase: bool = False,
        sla_extension: Optional[int] = None
    ) -> Dict[str, Any]:
        """Escalate ticket to another agent"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Create escalation record
                escalation = TicketEscalation(
                    ticket_id=ticket_id,
                    escalated_from_agent_id=escalated_from_agent_id,
                    escalated_to_agent_id=escalated_to_agent_id,
                    reason=reason,
                    priority_increase=priority_increase,
                    sla_extension=sla_extension
                )
                session.add(escalation)
                
                # Update ticket
                ticket = await session.execute(
                    select(SupportTicket).where(SupportTicket.id == ticket_id)
                )
                ticket = ticket.scalar_one_or_none()
                
                if not ticket:
                    return {"success": False, "error": "Ticket not found"}
                
                ticket.status = TicketStatus.ESCALATED
                ticket.assigned_agent_id = escalated_to_agent_id
                ticket.updated_at = datetime.utcnow()
                
                if priority_increase:
                    current_priority = ticket.priority
                    if current_priority == TicketPriority.LOW:
                        ticket.priority = TicketPriority.MEDIUM
                    elif current_priority == TicketPriority.MEDIUM:
                        ticket.priority = TicketPriority.HIGH
                    elif current_priority == TicketPriority.HIGH:
                        ticket.priority = TicketPriority.URGENT
                    elif current_priority == TicketPriority.URGENT:
                        ticket.priority = TicketPriority.CRITICAL
                
                # Create escalation interaction
                interaction = CustomerInteraction(
                    ticket_id=ticket_id,
                    interaction_type=InteractionType.ESCALATION,
                    channel=ticket.channel,
                    message=f"Ticket escalated to agent {escalated_to_agent_id}",
                    response=reason,
                    agent_id=escalated_from_agent_id,
                    is_automated=False
                )
                session.add(interaction)
                
                await session.commit()
                
                # Publish escalation event
                await self.event_bus.publish_event(
                    topic="clara_ticket_escalated",
                    event_data={
                        "ticket_id": ticket_id,
                        "from_agent_id": escalated_from_agent_id,
                        "to_agent_id": escalated_to_agent_id,
                        "reason": reason,
                        "priority_increase": priority_increase
                    }
                )
                
                return {"success": True, "ticket_id": ticket_id, "escalation_id": escalation.id}
                
        except Exception as e:
            logger.error(f"Failed to escalate ticket: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_ticket_details(self, ticket_id: int) -> Dict[str, Any]:
        """Get detailed ticket information"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                ticket = await session.execute(
                    select(SupportTicket)
                    .options(
                        selectinload(SupportTicket.customer),
                        selectinload(SupportTicket.assigned_agent),
                        selectinload(SupportTicket.interactions),
                        selectinload(SupportTicket.attachments),
                        selectinload(SupportTicket.escalations),
                        selectinload(SupportTicket.feedback)
                    )
                    .where(SupportTicket.id == ticket_id)
                )
                ticket = ticket.scalar_one_or_none()
                
                if not ticket:
                    return {"success": False, "error": "Ticket not found"}
                
                return {
                    "success": True,
                    "ticket": {
                        "id": ticket.id,
                        "ticket_number": ticket.ticket_number,
                        "customer_id": ticket.customer_id,
                        "assigned_agent_id": ticket.assigned_agent_id,
                        "channel": ticket.channel.value,
                        "priority": ticket.priority.value,
                        "status": ticket.status.value,
                        "category": ticket.category.value,
                        "subject": ticket.subject,
                        "description": ticket.description,
                        "sentiment_score": ticket.sentiment_score,
                        "satisfaction_score": ticket.satisfaction_score,
                        "tags": ticket.tags,
                        "metadata": ticket.metadata,
                        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
                        "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
                        "customer": {
                            "id": ticket.customer.id,
                            "email": ticket.customer.email,
                            "full_name": ticket.customer.full_name
                        } if ticket.customer else None,
                        "assigned_agent": {
                            "id": ticket.assigned_agent.id,
                            "email": ticket.assigned_agent.email,
                            "full_name": ticket.assigned_agent.full_name
                        } if ticket.assigned_agent else None,
                        "interactions_count": len(ticket.interactions),
                        "attachments_count": len(ticket.attachments),
                        "escalations_count": len(ticket.escalations)
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get ticket details: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_tickets(
        self,
        customer_id: Optional[int] = None,
        agent_id: Optional[int] = None,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        category: Optional[TicketCategory] = None,
        channel: Optional[SupportChannel] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search tickets with filters"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                query = select(SupportTicket)
                
                # Apply filters
                if customer_id:
                    query = query.where(SupportTicket.customer_id == customer_id)
                if agent_id:
                    query = query.where(SupportTicket.assigned_agent_id == agent_id)
                if status:
                    query = query.where(SupportTicket.status == status)
                if priority:
                    query = query.where(SupportTicket.priority == priority)
                if category:
                    query = query.where(SupportTicket.category == category)
                if channel:
                    query = query.where(SupportTicket.channel == channel)
                
                # Get total count
                count_query = select(func.count()).select_from(query.subquery())
                total_count = await session.execute(count_query)
                total_count = total_count.scalar()
                
                # Apply pagination and ordering
                query = query.order_by(SupportTicket.created_at.desc()).limit(limit).offset(offset)
                
                tickets = await session.execute(query)
                tickets = tickets.scalars().all()
                
                return {
                    "success": True,
                    "tickets": [
                        {
                            "id": ticket.id,
                            "ticket_number": ticket.ticket_number,
                            "customer_id": ticket.customer_id,
                            "assigned_agent_id": ticket.assigned_agent_id,
                            "channel": ticket.channel.value,
                            "priority": ticket.priority.value,
                            "status": ticket.status.value,
                            "category": ticket.category.value,
                            "subject": ticket.subject,
                            "sentiment_score": ticket.sentiment_score,
                            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None
                        }
                        for ticket in tickets
                    ],
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset
                }
                
        except Exception as e:
            logger.error(f"Failed to search tickets: {e}")
            return {"success": False, "error": str(e)}
    
    async def _auto_assign_priority(self, description: str, category: TicketCategory) -> TicketPriority:
        """Auto-assign ticket priority based on content and category"""
        try:
            # Use NLP to analyze urgency
            urgency_prompt = f"Analyze this support request and determine urgency level (1-5, where 5 is most urgent):\n\nCategory: {category.value}\nDescription: {description}\n\nRespond with only a number 1-5."
            
            messages = [
                {"role": "system", "content": urgency_prompt},
                {"role": "user", "content": f"Category: {category.value}\nDescription: {description}"}
            ]
            
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=10,
                temperature=0.1
            )
            
            if response.success:
                try:
                    urgency_level = int(response.text_content.strip())
                    if urgency_level == 5:
                        return TicketPriority.CRITICAL
                    elif urgency_level == 4:
                        return TicketPriority.URGENT
                    elif urgency_level == 3:
                        return TicketPriority.HIGH
                    elif urgency_level == 2:
                        return TicketPriority.MEDIUM
                    else:
                        return TicketPriority.LOW
                except ValueError:
                    pass
            
            # Fallback priority assignment
            if category in [TicketCategory.SECURITY, TicketCategory.BUG_REPORT]:
                return TicketPriority.HIGH
            elif category in [TicketCategory.BILLING, TicketCategory.ACCOUNT_ISSUE]:
                return TicketPriority.MEDIUM
            else:
                return TicketPriority.LOW
                
        except Exception as e:
            logger.error(f"Failed to auto-assign priority: {e}")
            return TicketPriority.MEDIUM
    
    async def _auto_assign_agent(self, ticket: SupportTicket, session: AsyncSession) -> Optional[SupportAgent]:
        """Auto-assign ticket to available agent"""
        try:
            # Find available agents with matching skills
            query = select(SupportAgent).where(
                and_(
                    SupportAgent.availability_status == "available",
                    SupportAgent.current_ticket_count < SupportAgent.max_concurrent_tickets,
                    SupportAgent.skills.contains([ticket.category.value])
                )
            ).order_by(SupportAgent.current_ticket_count.asc(), SupportAgent.performance_score.desc())
            
            agent = await session.execute(query)
            agent = agent.scalar_one_or_none()
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to auto-assign agent: {e}")
            return None
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze text sentiment using NLP"""
        try:
            sentiment_prompt = f"Analyze the sentiment of this text and respond with a JSON object containing 'sentiment_type' (positive, neutral, negative, frustrated, satisfied) and 'sentiment_score' (float between -1.0 and 1.0):\n\nText: {text}"
            
            messages = [
                {"role": "system", "content": sentiment_prompt},
                {"role": "user", "content": text}
            ]
            
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=100,
                temperature=0.3
            )
            
            if response.success:
                try:
                    import json
                    sentiment_data = json.loads(response.text_content)
                    return {
                        "success": True,
                        "sentiment_type": SentimentType(sentiment_data["sentiment_type"]),
                        "sentiment_score": sentiment_data["sentiment_score"]
                    }
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass
            
            # Fallback sentiment analysis
            negative_words = ["error", "broken", "failed", "issue", "problem", "urgent", "critical"]
            positive_words = ["thank", "great", "good", "excellent", "working", "solved"]
            
            text_lower = text.lower()
            negative_count = sum(1 for word in negative_words if word in text_lower)
            positive_count = sum(1 for word in positive_words if word in text_lower)
            
            if negative_count > positive_count:
                return {
                    "success": True,
                    "sentiment_type": SentimentType.NEGATIVE,
                    "sentiment_score": -0.5
                }
            elif positive_count > negative_count:
                return {
                    "success": True,
                    "sentiment_type": SentimentType.POSITIVE,
                    "sentiment_score": 0.5
                }
            else:
                return {
                    "success": True,
                    "sentiment_type": SentimentType.NEUTRAL,
                    "sentiment_score": 0.0
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e}")
            return {
                "success": True,
                "sentiment_type": SentimentType.NEUTRAL,
                "sentiment_score": 0.0
            }
    
    async def _estimate_resolution_time(self, ticket: SupportTicket) -> int:
        """Estimate ticket resolution time in minutes"""
        try:
            # Base resolution times by category and priority
            base_times = {
                TicketCategory.TECHNICAL: 120,  # 2 hours
                TicketCategory.BILLING: 60,     # 1 hour
                TicketCategory.GENERAL: 90,     # 1.5 hours
                TicketCategory.FEATURE_REQUEST: 480,  # 8 hours
                TicketCategory.BUG_REPORT: 240,  # 4 hours
                TicketCategory.ACCOUNT_ISSUE: 60,  # 1 hour
                TicketCategory.ORDER_TRACKING: 30,  # 30 minutes
                TicketCategory.PRODUCT_SUPPORT: 90,  # 1.5 hours
                TicketCategory.INTEGRATION: 180,  # 3 hours
                TicketCategory.SECURITY: 360   # 6 hours
            }
            
            priority_multipliers = {
                TicketPriority.LOW: 0.5,
                TicketPriority.MEDIUM: 1.0,
                TicketPriority.HIGH: 1.5,
                TicketPriority.URGENT: 2.0,
                TicketPriority.CRITICAL: 3.0
            }
            
            base_time = base_times.get(ticket.category, 90)
            multiplier = priority_multipliers.get(ticket.priority, 1.0)
            
            return int(base_time * multiplier)
            
        except Exception as e:
            logger.error(f"Failed to estimate resolution time: {e}")
            return 120  # Default 2 hours
    
    async def _update_customer_profile(self, customer_id: int, session: AsyncSession):
        """Update customer support profile"""
        try:
            # Get or create customer profile
            profile = await session.execute(
                select(CustomerProfile).where(CustomerProfile.user_id == customer_id)
            )
            profile = profile.scalar_one_or_none()
            
            if not profile:
                profile = CustomerProfile(user_id=customer_id)
                session.add(profile)
            
            # Update support history
            profile.total_support_tickets += 1
            profile.last_support_contact = datetime.utcnow()
            
            # Update loyalty level based on ticket count
            if profile.total_support_tickets >= 20:
                profile.loyalty_level = "vip"
            elif profile.total_support_tickets >= 10:
                profile.loyalty_level = "loyal"
            elif profile.total_support_tickets >= 3:
                profile.loyalty_level = "returning"
            
            await session.flush()
            
        except Exception as e:
            logger.error(f"Failed to update customer profile: {e}")
