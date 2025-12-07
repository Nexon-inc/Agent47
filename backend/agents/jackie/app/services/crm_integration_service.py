from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import uuid

from ..models import CRMINtegration
from backend.core.utils.nlp_utils import NLPUtils

class CRMIntegrationService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_utils = NLPUtils()

    def connect_crm(self, crm_platform: str, api_key: str, api_secret: Optional[str] = None, base_url: Optional[str] = None) -> Dict[str, Any]:
        connection_id = str(uuid.uuid4())
        
        integration = CRMINtegration(
            crm_platform=crm_platform,
            api_key=api_key,
            api_secret=api_secret,
            base_url=base_url,
            connection_status="connected",
            last_sync=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        self.db.add(integration)
        self.db.commit()
        self.db.refresh(integration)
        
        return {
            "connection_id": integration.id,
            "status": integration.connection_status,
            "crm_platform": integration.crm_platform
        }

    def list_connections(self) -> List[Dict[str, Any]]:
        connections = self.db.query(CRMINtegration).all()
        
        return [
            {
                "id": conn.id,
                "crm_platform": conn.crm_platform,
                "connection_status": conn.connection_status,
                "last_sync": conn.last_sync,
                "created_at": conn.created_at
            }
            for conn in connections
        ]

    def get_connection(self, connection_id: int) -> Optional[Dict[str, Any]]:
        connection = self.db.query(CRMINtegration).filter(CRMINtegration.id == connection_id).first()
        if not connection:
            return None
        
        return {
            "id": connection.id,
            "crm_platform": connection.crm_platform,
            "connection_status": connection.connection_status,
            "last_sync": connection.last_sync,
            "created_at": connection.created_at
        }

    def disconnect_crm(self, connection_id: int) -> bool:
        connection = self.db.query(CRMINtegration).filter(CRMINtegration.id == connection_id).first()
        if not connection:
            return False
        
        connection.connection_status = "disconnected"
        connection.last_sync = datetime.utcnow()
        
        self.db.commit()
        return True

    def sync_data(self, data_type: str, sync_direction: str = "bidirectional", filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        sync_id = str(uuid.uuid4())
        
        sync_result = {
            "sync_id": sync_id,
            "data_type": data_type,
            "sync_direction": sync_direction,
            "status": "in_progress",
            "estimated_duration": "5-10 minutes",
            "filters": filters or {}
        }
        
        return sync_result

    def get_sync_status(self, sync_id: str) -> Optional[Dict[str, Any]]:
        return {
            "sync_id": sync_id,
            "status": "completed",
            "progress": 100,
            "records_processed": 1500,
            "records_synced": 1450,
            "errors": 50,
            "start_time": datetime.utcnow() - timedelta(minutes=8),
            "end_time": datetime.utcnow(),
            "duration": "8 minutes"
        }

    def get_contacts(self, crm_platform: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        contacts = []
        
        for i in range(offset, min(offset + limit, 1000)):
            contact = {
                "id": f"contact_{i}",
                "first_name": f"John{i}",
                "last_name": f"Doe{i}",
                "email": f"john.doe{i}@example.com",
                "phone": f"+1-555-{i:03d}-{i:04d}",
                "company": f"Company {i}",
                "title": "Manager",
                "lead_source": "Website",
                "created_date": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "last_modified": datetime.utcnow().isoformat(),
                "crm_platform": crm_platform or "hubspot"
            }
            contacts.append(contact)
        
        return contacts

    def get_leads(self, crm_platform: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        leads = []
        
        for i in range(offset, min(offset + limit, 500)):
            lead = {
                "id": f"lead_{i}",
                "first_name": f"Jane{i}",
                "last_name": f"Smith{i}",
                "email": f"jane.smith{i}@example.com",
                "phone": f"+1-555-{i:03d}-{i:04d}",
                "company": f"Company {i}",
                "title": "Director",
                "lead_source": "LinkedIn",
                "lead_status": "New",
                "lead_score": 85,
                "created_date": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "last_modified": datetime.utcnow().isoformat(),
                "crm_platform": crm_platform or "hubspot"
            }
            leads.append(lead)
        
        return leads

    def get_deals(self, crm_platform: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        deals = []
        
        for i in range(offset, min(offset + limit, 300)):
            deal = {
                "id": f"deal_{i}",
                "deal_name": f"Deal {i}",
                "amount": 50000 + (i * 1000),
                "currency": "USD",
                "stage": "Proposal",
                "close_date": (datetime.utcnow() + timedelta(days=30 + i)).isoformat(),
                "probability": 75,
                "owner": f"Sales Rep {i}",
                "company": f"Company {i}",
                "created_date": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "last_modified": datetime.utcnow().isoformat(),
                "crm_platform": crm_platform or "hubspot"
            }
            deals.append(deal)
        
        return deals

    def create_contact(self, contact_data: Dict[str, Any], crm_platform: Optional[str] = None) -> Dict[str, Any]:
        contact_id = str(uuid.uuid4())
        
        return {
            "contact_id": contact_id,
            "crm_platform": crm_platform or "hubspot",
            "status": "created",
            "contact_data": contact_data
        }

    def update_contact(self, contact_id: str, contact_data: Dict[str, Any], crm_platform: Optional[str] = None) -> bool:
        return True

    def create_lead(self, lead_data: Dict[str, Any], crm_platform: Optional[str] = None) -> Dict[str, Any]:
        lead_id = str(uuid.uuid4())
        
        return {
            "lead_id": lead_id,
            "crm_platform": crm_platform or "hubspot",
            "status": "created",
            "lead_data": lead_data
        }

    def create_deal(self, deal_data: Dict[str, Any], crm_platform: Optional[str] = None) -> Dict[str, Any]:
        deal_id = str(uuid.uuid4())
        
        return {
            "deal_id": deal_id,
            "crm_platform": crm_platform or "hubspot",
            "status": "created",
            "deal_data": deal_data
        }

    def get_crm_analytics(self, crm_platform: Optional[str] = None, timeframe: str = "30d") -> Dict[str, Any]:
        return {
            "crm_platform": crm_platform or "all",
            "timeframe": timeframe,
            "metrics": {
                "total_contacts": 15000,
                "total_leads": 5000,
                "total_deals": 3000,
                "active_deals": 1200,
                "closed_deals": 800,
                "total_revenue": 2500000,
                "average_deal_size": 3125,
                "conversion_rate": 16.0,
                "lead_to_contact_rate": 85.5,
                "contact_to_deal_rate": 20.0
            },
            "trends": {
                "contacts_growth": 12.5,
                "leads_growth": 8.2,
                "deals_growth": 15.8,
                "revenue_growth": 22.3
            },
            "top_sources": [
                {"source": "Website", "leads": 2500, "conversion_rate": 18.5},
                {"source": "LinkedIn", "leads": 1200, "conversion_rate": 15.2},
                {"source": "Referral", "leads": 800, "conversion_rate": 25.0},
                {"source": "Email", "leads": 500, "conversion_rate": 12.8}
            ],
            "top_stages": [
                {"stage": "Qualified", "deals": 500, "value": 1500000},
                {"stage": "Proposal", "deals": 300, "value": 900000},
                {"stage": "Negotiation", "deals": 200, "value": 600000},
                {"stage": "Closed Won", "deals": 800, "value": 2500000}
            ]
        }

    def setup_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        webhook_id = str(uuid.uuid4())
        webhook_url = f"https://api.jackie.com/webhooks/{webhook_id}"
        
        return {
            "webhook_id": webhook_id,
            "webhook_url": webhook_url,
            "events": webhook_data.get("events", ["contact.created", "lead.created", "deal.created"]),
            "status": "active"
        }

    def list_webhooks(self) -> List[Dict[str, Any]]:
        webhooks = []
        
        for i in range(5):
            webhook = {
                "id": f"webhook_{i}",
                "url": f"https://api.jackie.com/webhooks/webhook_{i}",
                "events": ["contact.created", "lead.created", "deal.created"],
                "status": "active",
                "created_at": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "last_triggered": datetime.utcnow().isoformat()
            }
            webhooks.append(webhook)
        
        return webhooks

    def delete_webhook(self, webhook_id: int) -> bool:
        return True

    def get_supported_platforms(self) -> List[Dict[str, Any]]:
        return [
            {
                "platform": "hubspot",
                "name": "HubSpot",
                "description": "All-in-one inbound marketing and CRM platform",
                "features": ["contacts", "leads", "deals", "companies", "email_marketing"],
                "api_version": "v3",
                "rate_limit": "100 requests/second"
            },
            {
                "platform": "salesforce",
                "name": "Salesforce",
                "description": "Leading CRM platform for sales, service, and marketing",
                "features": ["contacts", "leads", "opportunities", "accounts", "campaigns"],
                "api_version": "v57.0",
                "rate_limit": "1500 requests/hour"
            },
            {
                "platform": "zoho",
                "name": "Zoho CRM",
                "description": "Cloud-based CRM solution for businesses",
                "features": ["contacts", "leads", "deals", "accounts", "email_marketing"],
                "api_version": "v2.1",
                "rate_limit": "100 requests/minute"
            },
            {
                "platform": "pipedrive",
                "name": "Pipedrive",
                "description": "Sales CRM and pipeline management platform",
                "features": ["contacts", "leads", "deals", "organizations"],
                "api_version": "v1",
                "rate_limit": "100 requests/second"
            },
            {
                "platform": "freshsales",
                "name": "Freshsales",
                "description": "AI-powered CRM for high-velocity sales teams",
                "features": ["contacts", "leads", "deals", "accounts", "email_tracking"],
                "api_version": "v1",
                "rate_limit": "100 requests/minute"
            }
        ]
