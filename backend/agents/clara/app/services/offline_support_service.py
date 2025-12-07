import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_, desc
from sqlalchemy.orm import selectinload
from backend.core.ai import get_ai_service_manager, AIServiceManager
from ..database import get_clara_database
from ..models import (
    SupportTicket, CustomerInteraction, ChatSession, CustomerProfile,
    TicketCategory, SupportChannel, SentimentType
)

logger = logging.getLogger(__name__)

class OfflineSupportService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize offline support service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            self._initialized = True
            logger.info("Offline support service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize offline support service: {e}")
            raise
    
    async def queue_offline_response(
        self,
        customer_id: int,
        message: str,
        channel: SupportChannel,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Queue a response for when customer comes back online"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Create offline interaction record
                interaction = CustomerInteraction(
                    customer_id=customer_id,
                    interaction_type="offline_response",
                    channel=channel,
                    message=message,
                    metadata={
                        "offline": True,
                        "queued_at": datetime.utcnow().isoformat(),
                        "priority": priority,
                        "status": "queued",
                        **(metadata or {})
                    }
                )
                session.add(interaction)
                await session.flush()
                
                # Update customer profile to indicate offline response is queued
                profile = await session.execute(
                    select(CustomerProfile).where(CustomerProfile.user_id == customer_id)
                )
                profile = profile.scalar_one_or_none()
                
                if profile:
                    if not hasattr(profile, 'offline_responses_queued'):
                        # This would need to be added to the model
                        pass
                    else:
                        profile.offline_responses_queued += 1
                        profile.last_offline_response = datetime.utcnow()
                    
                    session.add(profile)
                
                await session.commit()
                
                return {
                    "success": True,
                    "interaction_id": interaction.id,
                    "message": "Response queued for offline customer",
                    "queued_at": interaction.created_at.isoformat(),
                    "priority": priority,
                    "estimated_delivery": "When customer comes back online"
                }
                
        except Exception as e:
            logger.error(f"Failed to queue offline response: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_queued_responses(
        self,
        customer_id: int,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get queued responses for a customer"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get queued offline responses
                queued_responses = await session.execute(
                    select(CustomerInteraction).where(
                        and_(
                            CustomerInteraction.customer_id == customer_id,
                            CustomerInteraction.interaction_type == "offline_response",
                            CustomerInteraction.metadata.contains({"status": "queued"})
                        )
                    ).order_by(
                        CustomerInteraction.metadata["priority"].desc(),
                        CustomerInteraction.created_at.asc()
                    ).limit(limit)
                )
                queued_responses = queued_responses.scalars().all()
                
                # Format responses
                responses = []
                for response in queued_responses:
                    responses.append({
                        "id": response.id,
                        "message": response.message,
                        "channel": response.channel.value,
                        "queued_at": response.created_at.isoformat(),
                        "priority": response.metadata.get("priority", "normal"),
                        "metadata": response.metadata
                    })
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "queued_responses": responses,
                    "total_queued": len(responses),
                    "message": f"Found {len(responses)} queued responses"
                }
                
        except Exception as e:
            logger.error(f"Failed to get queued responses: {e}")
            return {"success": False, "error": str(e)}
    
    async def deliver_queued_responses(
        self,
        customer_id: int,
        delivery_channel: SupportChannel
    ) -> Dict[str, Any]:
        """Deliver all queued responses to a customer"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get all queued responses
                queued_responses = await session.execute(
                    select(CustomerInteraction).where(
                        and_(
                            CustomerInteraction.customer_id == customer_id,
                            CustomerInteraction.interaction_type == "offline_response",
                            CustomerInteraction.metadata.contains({"status": "queued"})
                        )
                    ).order_by(
                        CustomerInteraction.metadata["priority"].desc(),
                        CustomerInteraction.created_at.asc()
                    )
                )
                queued_responses = queued_responses.scalars().all()
                
                if not queued_responses:
                    return {
                        "success": True,
                        "message": "No queued responses to deliver",
                        "delivered_count": 0
                    }
                
                # Deliver responses
                delivered_count = 0
                for response in queued_responses:
                    delivery_result = await self._deliver_single_response(
                        response, delivery_channel, session
                    )
                    
                    if delivery_result["success"]:
                        # Mark as delivered
                        response.metadata["status"] = "delivered"
                        response.metadata["delivered_at"] = datetime.utcnow().isoformat()
                        response.metadata["delivery_channel"] = delivery_channel.value
                        
                        session.add(response)
                        delivered_count += 1
                
                await session.commit()
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "delivered_count": delivered_count,
                    "total_queued": len(queued_responses),
                    "delivery_channel": delivery_channel.value,
                    "message": f"Successfully delivered {delivered_count} queued responses"
                }
                
        except Exception as e:
            logger.error(f"Failed to deliver queued responses: {e}")
            return {"success": False, "error": str(e)}
    
    async def _deliver_single_response(
        self,
        response: CustomerInteraction,
        delivery_channel: SupportChannel,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Deliver a single queued response"""
        try:
            # Integrate with the actual delivery system
            # Update interaction metadata
            response.metadata["delivery_attempts"] = response.metadata.get("delivery_attempts", 0) + 1
            response.metadata["last_delivery_attempt"] = datetime.utcnow().isoformat()
            
            # Attempt actual delivery based on channel
            delivery_success = False
            delivery_error = None
            
            try:
                if response.channel == SupportChannel.EMAIL:
                    # Send email notification
                    delivery_success = await self._send_email_notification(response)
                elif response.channel == SupportChannel.SMS:
                    # Send SMS notification
                    delivery_success = await self._send_sms_notification(response)
                elif response.channel == SupportChannel.PUSH:
                    # Send push notification
                    delivery_success = await self._send_push_notification(response)
                else:
                    # Default to email for unknown channels
                    delivery_success = await self._send_email_notification(response)
                    
            except Exception as delivery_exception:
                delivery_error = str(delivery_exception)
                logger.error(f"Delivery failed: {delivery_error}")
            
            if delivery_success:
                return {"success": True, "delivered": True}
            else:
                return {"success": False, "delivered": False, "error": delivery_error or "Delivery failed"}
                
        except Exception as e:
            logger.error(f"Failed to deliver single response: {e}")
            return {"success": False, "delivered": False, "error": str(e)}
    
    async def create_offline_ticket(
        self,
        customer_id: int,
        subject: str,
        description: str,
        category: TicketCategory,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a support ticket for offline customer"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Create offline ticket
                from ..services.support_service import SupportService
                support_service = SupportService()
                await support_service.initialize()
                
                ticket_result = await support_service.create_ticket(
                    customer_id=customer_id,
                    channel=SupportChannel.WEB_FORM,
                    category=category,
                    subject=f"[OFFLINE] {subject}",
                    description=f"{description}\n\n[Note: This ticket was created while customer was offline]",
                    priority=priority,
                    metadata={
                        "offline_created": True,
                        "created_while_offline": True,
                        "offline_priority": priority,
                        **(metadata or {})
                    }
                )
                
                if ticket_result["success"]:
                    # Queue notification for when customer comes back online
                    notification_message = f"Your support ticket '{subject}' has been created and is being reviewed by our team."
                    await self.queue_offline_response(
                        customer_id=customer_id,
                        message=notification_message,
                        channel=SupportChannel.EMAIL,  # Default to email for offline notifications
                        priority="high",
                        metadata={"ticket_id": ticket_result["ticket"]["id"], "type": "ticket_created"}
                    )
                    
                    return {
                        "success": True,
                        "ticket": ticket_result["ticket"],
                        "message": "Offline ticket created successfully",
                        "notification_queued": True
                    }
                else:
                    return ticket_result
                
        except Exception as e:
            logger.error(f"Failed to create offline ticket: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_offline_support_summary(
        self,
        customer_id: int
    ) -> Dict[str, Any]:
        """Get summary of offline support activities"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get offline interactions
                offline_interactions = await session.execute(
                    select(CustomerInteraction).where(
                        and_(
                            CustomerInteraction.customer_id == customer_id,
                            CustomerInteraction.metadata.contains({"offline": True})
                        )
                    ).order_by(CustomerInteraction.created_at.desc())
                )
                offline_interactions = offline_interactions.scalars().all()
                
                # Get offline tickets
                offline_tickets = await session.execute(
                    select(SupportTicket).where(
                        and_(
                            SupportTicket.customer_id == customer_id,
                            SupportTicket.metadata.contains({"offline_created": True})
                        )
                    ).order_by(SupportTicket.created_at.desc())
                )
                offline_tickets = offline_tickets.scalars().all()
                
                # Calculate statistics
                total_offline_interactions = len(offline_interactions)
                queued_responses = len([i for i in offline_interactions if i.metadata.get("status") == "queued"])
                delivered_responses = len([i for i in offline_interactions if i.metadata.get("status") == "delivered"])
                offline_tickets_count = len(offline_tickets)
                
                # Get recent offline activity
                recent_offline_activity = []
                for interaction in offline_interactions[:5]:  # Last 5 interactions
                    recent_offline_activity.append({
                        "id": interaction.id,
                        "type": interaction.interaction_type,
                        "message": interaction.message[:100] + "..." if len(interaction.message) > 100 else interaction.message,
                        "created_at": interaction.created_at.isoformat(),
                        "status": interaction.metadata.get("status", "unknown"),
                        "priority": interaction.metadata.get("priority", "normal")
                    })
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "offline_support_summary": {
                        "total_offline_interactions": total_offline_interactions,
                        "queued_responses": queued_responses,
                        "delivered_responses": delivered_responses,
                        "offline_tickets_created": offline_tickets_count,
                        "delivery_rate": round((delivered_responses / max(total_offline_interactions, 1)) * 100, 1)
                    },
                    "recent_offline_activity": recent_offline_activity,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get offline support summary: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_low_connectivity(
        self,
        customer_id: int,
        connectivity_level: str = "low",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle low connectivity scenarios"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Determine appropriate response based on connectivity level
            if connectivity_level == "very_low":
                # Minimal response, queue everything else
                response = "We're experiencing connectivity issues. Your request has been saved and will be processed when connection improves."
                should_queue = True
                priority = "high"
            elif connectivity_level == "low":
                # Basic response, queue non-essential items
                response = "Connection is slow. We'll process your request as quickly as possible."
                should_queue = True
                priority = "normal"
            else:
                # Normal response
                response = "We're here to help!"
                should_queue = False
                priority = "normal"
            
            # Queue response if needed
            if should_queue:
                queue_result = await self.queue_offline_response(
                    customer_id=customer_id,
                    message=response,
                    channel=SupportChannel.CHAT,
                    priority=priority,
                    metadata={
                        "connectivity_issue": True,
                        "connectivity_level": connectivity_level,
                        **(metadata or {})
                    }
                )
                
                return {
                    "success": True,
                    "response": response,
                    "queued": True,
                    "queue_result": queue_result,
                    "connectivity_level": connectivity_level
                }
            else:
                return {
                    "success": True,
                    "response": response,
                    "queued": False,
                    "connectivity_level": connectivity_level
                }
                
        except Exception as e:
            logger.error(f"Failed to handle low connectivity: {e}")
            return {"success": False, "error": str(e)}
