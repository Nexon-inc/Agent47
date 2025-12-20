import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload
import httpx
from core.config import settings
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_clara_database
from ..models import (
    SupportTicket, CustomerInteraction, CustomerProfile,
    TicketPriority, TicketStatus, TicketCategory, SupportChannel
)

logger = logging.getLogger(__name__)

class CRMIntegrationService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self._crm_clients = {}
    
    async def initialize(self):
        """Initialize CRM integration service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            await self._initialize_crm_clients()
            self._initialized = True
            logger.info("CRM integration service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CRM integration service: {e}")
            raise
    
    async def _initialize_crm_clients(self):
        """Initialize CRM API clients"""
        db = await get_clara_database()
        async with db.get_session() as session:
            # Get active CRM integrations
            integrations = await self.integration_manager.get_integrations_by_type("crm")
            
            for integration in integrations:
                if integration.name == "zendesk":
                    self._crm_clients["zendesk"] = ZendeskClient(integration)
                elif integration.name == "freshdesk":
                    self._crm_clients["freshdesk"] = FreshdeskClient(integration)
                elif integration.name == "hubspot":
                    self._crm_clients["hubspot"] = HubSpotClient(integration)
                elif integration.name == "salesforce":
                    self._crm_clients["salesforce"] = SalesforceClient(integration)
    
    async def sync_ticket_to_crm(
        self,
        ticket_id: int,
        crm_platform: str,
        crm_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Sync a support ticket to external CRM"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get ticket details
                ticket_query = select(SupportTicket).where(SupportTicket.id == ticket_id)
                ticket_result = await session.execute(ticket_query)
                ticket = ticket_result.scalar_one_or_none()
                
                if not ticket:
                    raise ValueError(f"Ticket {ticket_id} not found")
                
                # Get CRM client
                crm_client = self._crm_clients.get(crm_platform)
                if not crm_client:
                    raise ValueError(f"CRM platform {crm_platform} not configured")
                
                # Prepare ticket data for CRM
                crm_ticket_data = await self._prepare_ticket_for_crm(ticket, crm_platform)
                
                # Sync to CRM
                crm_response = await crm_client.create_ticket(crm_ticket_data)
                
                # Update ticket with CRM reference
                ticket.crm_case_id = crm_response.get("id")
                ticket.metadata = {
                    **ticket.metadata,
                    "crm_sync": {
                        "platform": crm_platform,
                        "crm_id": crm_response.get("id"),
                        "synced_at": datetime.utcnow().isoformat(),
                        "status": "synced"
                    }
                }
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish(
                    "clara.crm.ticket_synced",
                    {
                        "ticket_id": ticket_id,
                        "crm_platform": crm_platform,
                        "crm_id": crm_response.get("id"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return {
                    "success": True,
                    "ticket_id": ticket_id,
                    "crm_platform": crm_platform,
                    "crm_id": crm_response.get("id"),
                    "message": f"Ticket synced to {crm_platform} successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to sync ticket {ticket_id} to {crm_platform}: {e}")
            return {
                "success": False,
                "ticket_id": ticket_id,
                "crm_platform": crm_platform,
                "error": str(e)
            }
    
    async def sync_customer_to_crm(
        self,
        customer_id: int,
        crm_platform: str,
        crm_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Sync customer profile to external CRM"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get customer profile
                profile_query = select(CustomerProfile).where(CustomerProfile.user_id == customer_id)
                profile_result = await session.execute(profile_query)
                profile = profile_result.scalar_one_or_none()
                
                if not profile:
                    raise ValueError(f"Customer profile {customer_id} not found")
                
                # Get CRM client
                crm_client = self._crm_clients.get(crm_platform)
                if not crm_client:
                    raise ValueError(f"CRM platform {crm_platform} not configured")
                
                # Prepare customer data for CRM
                crm_customer_data = await self._prepare_customer_for_crm(profile, crm_platform)
                
                # Sync to CRM
                crm_response = await crm_client.create_contact(crm_customer_data)
                
                # Update profile with CRM reference
                profile.metadata = {
                    **profile.metadata,
                    "crm_sync": {
                        "platform": crm_platform,
                        "crm_id": crm_response.get("id"),
                        "synced_at": datetime.utcnow().isoformat(),
                        "status": "synced"
                    }
                }
                
                await session.commit()
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "crm_platform": crm_platform,
                    "crm_id": crm_response.get("id"),
                    "message": f"Customer synced to {crm_platform} successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to sync customer {customer_id} to {crm_platform}: {e}")
            return {
                "success": False,
                "customer_id": customer_id,
                "crm_platform": crm_platform,
                "error": str(e)
            }
    
    async def get_crm_ticket_status(
        self,
        ticket_id: int,
        crm_platform: str
    ) -> Dict[str, Any]:
        """Get ticket status from external CRM"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get ticket
                ticket_query = select(SupportTicket).where(SupportTicket.id == ticket_id)
                ticket_result = await session.execute(ticket_query)
                ticket = ticket_result.scalar_one_or_none()
                
                if not ticket or not ticket.crm_case_id:
                    raise ValueError(f"Ticket {ticket_id} not synced to {crm_platform}")
                
                # Get CRM client
                crm_client = self._crm_clients.get(crm_platform)
                if not crm_client:
                    raise ValueError(f"CRM platform {crm_platform} not configured")
                
                # Get status from CRM
                crm_status = await crm_client.get_ticket_status(ticket.crm_case_id)
                
                return {
                    "success": True,
                    "ticket_id": ticket_id,
                    "crm_platform": crm_platform,
                    "crm_id": ticket.crm_case_id,
                    "status": crm_status
                }
                
        except Exception as e:
            logger.error(f"Failed to get CRM status for ticket {ticket_id}: {e}")
            return {
                "success": False,
                "ticket_id": ticket_id,
                "crm_platform": crm_platform,
                "error": str(e)
            }
    
    async def update_crm_ticket(
        self,
        ticket_id: int,
        crm_platform: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update ticket in external CRM"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get ticket
                ticket_query = select(SupportTicket).where(SupportTicket.id == ticket_id)
                ticket_result = await session.execute(ticket_query)
                ticket = ticket_result.scalar_one_or_none()
                
                if not ticket or not ticket.crm_case_id:
                    raise ValueError(f"Ticket {ticket_id} not synced to {crm_platform}")
                
                # Get CRM client
                crm_client = self._crm_clients.get(crm_platform)
                if not crm_client:
                    raise ValueError(f"CRM platform {crm_platform} not configured")
                
                # Update in CRM
                crm_response = await crm_client.update_ticket(ticket.crm_case_id, update_data)
                
                return {
                    "success": True,
                    "ticket_id": ticket_id,
                    "crm_platform": crm_platform,
                    "crm_id": ticket.crm_case_id,
                    "message": f"Ticket updated in {crm_platform} successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to update CRM ticket {ticket_id}: {e}")
            return {
                "success": False,
                "ticket_id": ticket_id,
                "crm_platform": crm_platform,
                "error": str(e)
            }
    
    async def get_crm_analytics(
        self,
        crm_platform: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics data from external CRM"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get CRM client
            crm_client = self._crm_clients.get(crm_platform)
            if not crm_client:
                raise ValueError(f"CRM platform {crm_platform} not configured")
            
            # Get analytics from CRM
            analytics = await crm_client.get_analytics(date_from, date_to)
            
            return {
                "success": True,
                "crm_platform": crm_platform,
                "analytics": analytics
            }
            
        except Exception as e:
            logger.error(f"Failed to get CRM analytics for {crm_platform}: {e}")
            return {
                "success": False,
                "crm_platform": crm_platform,
                "error": str(e)
            }
    
    async def _prepare_ticket_for_crm(
        self,
        ticket: SupportTicket,
        crm_platform: str
    ) -> Dict[str, Any]:
        """Prepare ticket data for CRM sync"""
        base_data = {
            "subject": ticket.subject,
            "description": ticket.description,
            "priority": ticket.priority.value,
            "status": ticket.status.value,
            "category": ticket.category.value,
            "channel": ticket.channel.value,
            "created_at": ticket.created_at.isoformat(),
            "tags": ticket.tags or [],
            "metadata": ticket.metadata or {}
        }
        
        # Platform-specific formatting
        if crm_platform == "zendesk":
            return {
                "ticket": {
                    "subject": base_data["subject"],
                    "description": base_data["description"],
                    "priority": base_data["priority"],
                    "status": base_data["status"],
                    "tags": base_data["tags"],
                    "custom_fields": base_data["metadata"]
                }
            }
        elif crm_platform == "freshdesk":
            return {
                "subject": base_data["subject"],
                "description": base_data["description"],
                "priority": base_data["priority"],
                "status": base_data["status"],
                "tags": base_data["tags"],
                "custom_fields": base_data["metadata"]
            }
        elif crm_platform == "hubspot":
            return {
                "properties": {
                    "hs_ticket_priority": base_data["priority"],
                    "hs_ticket_category": base_data["category"],
                    "hs_ticket_subject": base_data["subject"],
                    "hs_ticket_description": base_data["description"],
                    "hs_ticket_status": base_data["status"]
                }
            }
        elif crm_platform == "salesforce":
            return {
                "Subject": base_data["subject"],
                "Description": base_data["description"],
                "Priority": base_data["priority"],
                "Status": base_data["status"],
                "Type": base_data["category"]
            }
        
        return base_data
    
    async def _prepare_customer_for_crm(
        self,
        profile: CustomerProfile,
        crm_platform: str
    ) -> Dict[str, Any]:
        """Prepare customer data for CRM sync"""
        base_data = {
            "support_tier": profile.support_tier,
            "preferred_channel": profile.preferred_channel.value,
            "language_preference": profile.language_preference,
            "timezone": profile.timezone,
            "trust_score": profile.trust_score,
            "loyalty_level": profile.loyalty_level,
            "total_support_tickets": profile.total_support_tickets,
            "resolved_tickets": profile.resolved_tickets,
            "average_satisfaction": profile.average_satisfaction
        }
        
        # Platform-specific formatting
        if crm_platform == "zendesk":
            return {
                "user": {
                    "name": f"Customer {profile.user_id}",
                    "tags": [profile.support_tier, profile.loyalty_level],
                    "user_fields": base_data
                }
            }
        elif crm_platform == "hubspot":
            return {
                "properties": {
                    "support_tier": base_data["support_tier"],
                    "preferred_channel": base_data["preferred_channel"],
                    "language": base_data["language_preference"],
                    "timezone": base_data["timezone"],
                    "trust_score": base_data["trust_score"],
                    "loyalty_level": base_data["loyalty_level"]
                }
            }
        
        return base_data


class ZendeskClient:
    def __init__(self, integration):
        self.integration = integration
        self.base_url = integration.base_url
        self.api_key = integration.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tickets.json",
                headers=self.headers,
                json=ticket_data
            )
            response.raise_for_status()
            return response.json()["ticket"]
    
    async def get_ticket_status(self, ticket_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tickets/{ticket_id}.json",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()["ticket"]
    
    async def update_ticket(self, ticket_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/tickets/{ticket_id}.json",
                headers=self.headers,
                json={"ticket": update_data}
            )
            response.raise_for_status()
            return response.json()["ticket"]
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/users.json",
                headers=self.headers,
                json=contact_data
            )
            response.raise_for_status()
            return response.json()["user"]
    
    async def get_analytics(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/incremental/tickets.json",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()


class FreshdeskClient:
    def __init__(self, integration):
        self.integration = integration
        self.base_url = integration.base_url
        self.api_key = integration.api_key
        self.headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tickets",
                headers=self.headers,
                json=ticket_data
            )
            response.raise_for_status()
            return response.json()
    
    async def get_ticket_status(self, ticket_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tickets/{ticket_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def update_ticket(self, ticket_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/tickets/{ticket_id}",
                headers=self.headers,
                json=update_data
            )
            response.raise_for_status()
            return response.json()
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/contacts",
                headers=self.headers,
                json=contact_data
            )
            response.raise_for_status()
            return response.json()
    
    async def get_analytics(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/reports",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()


class HubSpotClient:
    def __init__(self, integration):
        self.integration = integration
        self.base_url = integration.base_url
        self.api_key = integration.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/crm/v3/objects/tickets",
                headers=self.headers,
                json=ticket_data
            )
            response.raise_for_status()
            return response.json()
    
    async def get_ticket_status(self, ticket_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/crm/v3/objects/tickets/{ticket_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def update_ticket(self, ticket_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/crm/v3/objects/tickets/{ticket_id}",
                headers=self.headers,
                json=ticket_data
            )
            response.raise_for_status()
            return response.json()
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/crm/v3/objects/contacts",
                headers=self.headers,
                json=contact_data
            )
            response.raise_for_status()
            return response.json()
    
    async def get_analytics(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/analytics/v2/reports",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()


class SalesforceClient:
    def __init__(self, integration):
        self.integration = integration
        self.base_url = integration.base_url
        self.api_key = integration.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/services/data/v52.0/sobjects/Case",
                headers=self.headers,
                json=ticket_data
            )
            response.raise_for_status()
            return response.json()
    
    async def get_ticket_status(self, ticket_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/services/data/v52.0/sobjects/Case/{ticket_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def update_ticket(self, ticket_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/services/data/v52.0/sobjects/Case/{ticket_id}",
                headers=self.headers,
                json=update_data
            )
            response.raise_for_status()
            return response.json()
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/services/data/v52.0/sobjects/Contact",
                headers=self.headers,
                json=contact_data
            )
            response.raise_for_status()
            return response.json()
    
    async def get_analytics(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/services/data/v52.0/analytics/reports",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
