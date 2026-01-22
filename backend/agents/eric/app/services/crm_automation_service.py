import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc

from core.ai import get_ai_service_manager, AIServiceManager
from core.cache.redis_manager import init_redis
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
# NLPUtils removed - not used
from ..models import EricLead, EricDeal, EricSalesActivity, LeadStatus, SalesStage
from ..database import get_eric_database

logger = logging.getLogger(__name__)

class CRMAutomationService:
    """Service for CRM automation and integration"""
    
    def __init__(self):
        self.nlp_utils = None
        self.redis_client = None
        self.integration_manager = None
        self.platform_manager = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize CRM automation service"""
        if self._initialized:
            return
        
        try:
            # NLPUtils removed - not used in this service
            self.redis_client = await init_redis()
            self.integration_manager = IntegrationManager()
            await self.integration_manager.initialize()
            self.platform_manager = PlatformManager()
            await self.platform_manager.initialize()
            self._initialized = True
            logger.info("Eric CRM automation service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CRM automation service: {e}")
            raise
    
    async def sync_lead_to_crm(
        self,
        lead_id: int,
        crm_platform: str,
        crm_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync lead data to external CRM"""
        try:
            await self.initialize()
            
            db = next(get_db())
            lead = db.query(EricLead).filter(EricLead.id == lead_id).first()
            
            if not lead:
                return {
                    "success": False,
                    "error": "EricLead not found"
                }
            
            # Prepare lead data for CRM
            lead_data = {
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "email": lead.email,
                "phone": lead.phone,
                "company": lead.company,
                "job_title": lead.job_title,
                "industry": lead.industry,
                "lead_source": lead.lead_source.value,
                "lead_score": lead.lead_score,
                "status": lead.lead_status.value,
                "budget": lead.budget,
                "timeline": lead.timeline,
                "pain_points": lead.pain_points,
                "requirements": lead.requirements,
                "location": lead.location,
                "timezone": lead.timezone,
                "language": lead.language,
                "created_at": lead.created_at.isoformat(),
                "updated_at": lead.updated_at.isoformat()
            }
            
            # Sync to CRM based on platform
            if crm_platform.lower() == "salesforce":
                result = await self._sync_to_salesforce(lead_data, crm_config)
            elif crm_platform.lower() == "hubspot":
                result = await self._sync_to_hubspot(lead_data, crm_config)
            elif crm_platform.lower() == "pipedrive":
                result = await self._sync_to_pipedrive(lead_data, crm_config)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported CRM platform: {crm_platform}"
                }
            
            if result["success"]:
                # Update lead with CRM reference
                lead.engagement_history = lead.engagement_history or {}
                lead.engagement_history.update({
                    "crm_sync": {
                        "platform": crm_platform,
                        "crm_id": result.get("crm_id"),
                        "synced_at": datetime.now().isoformat(),
                        "status": "success"
                    }
                })
                db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to sync lead to CRM: {e}")
            return {
                "success": False,
                "error": f"Failed to sync lead to CRM: {str(e)}"
            }
    
    async def sync_deal_to_crm(
        self,
        deal_id: int,
        crm_platform: str,
        crm_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync deal data to external CRM"""
        try:
            await self.initialize()
            
            db = next(get_db())
            deal = db.query(EricDeal).filter(EricDeal.id == deal_id).first()
            
            if not deal:
                return {
                    "success": False,
                    "error": "EricDeal not found"
                }
            
            # Get associated lead
            lead = db.query(EricLead).filter(EricLead.id == deal.lead_id).first()
            
            # Prepare deal data for CRM
            deal_data = {
                "deal_name": deal.deal_name,
                "deal_value": deal.deal_value,
                "currency": deal.currency,
                "sales_stage": deal.sales_stage.value,
                "probability": deal.probability,
                "expected_close_date": deal.expected_close_date.isoformat() if deal.expected_close_date else None,
                "actual_close_date": deal.actual_close_date.isoformat() if deal.actual_close_date else None,
                "win_reason": deal.win_reason,
                "loss_reason": deal.loss_reason,
                "sales_rep_id": deal.sales_rep_id,
                "team_id": deal.team_id,
                "pipeline_id": deal.pipeline_id,
                "tags": deal.tags,
                "notes": deal.notes,
                "created_at": deal.created_at.isoformat(),
                "updated_at": deal.updated_at.isoformat(),
                "lead": {
                    "first_name": lead.first_name if lead else None,
                    "last_name": lead.last_name if lead else None,
                    "email": lead.email if lead else None,
                    "company": lead.company if lead else None,
                    "job_title": lead.job_title if lead else None
                }
            }
            
            # Sync to CRM based on platform
            if crm_platform.lower() == "salesforce":
                result = await self._sync_deal_to_salesforce(deal_data, crm_config)
            elif crm_platform.lower() == "hubspot":
                result = await self._sync_deal_to_hubspot(deal_data, crm_config)
            elif crm_platform.lower() == "pipedrive":
                result = await self._sync_deal_to_pipedrive(deal_data, crm_config)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported CRM platform: {crm_platform}"
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to sync deal to CRM: {e}")
            return {
                "success": False,
                "error": f"Failed to sync deal to CRM: {str(e)}"
            }
    
    async def update_crm_records(
        self,
        brand_id: int,
        crm_platform: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update multiple CRM records"""
        try:
            await self.initialize()
            
            db = next(get_db())
            
            # Get leads and deals for the brand
            leads = db.query(EricLead).filter(EricLead.brand_id == brand_id).all()
            deals = db.query(EricDeal).filter(EricDeal.brand_id == brand_id).all()
            
            updated_records = []
            failed_records = []
            
            # Update leads
            for lead in leads:
                try:
                    result = await self.sync_lead_to_crm(lead.id, crm_platform, update_data.get("crm_config", {}))
                    if result["success"]:
                        updated_records.append({
                            "type": "lead",
                            "id": lead.id,
                            "crm_id": result.get("crm_id")
                        })
                    else:
                        failed_records.append({
                            "type": "lead",
                            "id": lead.id,
                            "error": result.get("error")
                        })
                except Exception as e:
                    failed_records.append({
                        "type": "lead",
                        "id": lead.id,
                        "error": str(e)
                    })
            
            # Update deals
            for deal in deals:
                try:
                    result = await self.sync_deal_to_crm(deal.id, crm_platform, update_data.get("crm_config", {}))
                    if result["success"]:
                        updated_records.append({
                            "type": "deal",
                            "id": deal.id,
                            "crm_id": result.get("crm_id")
                        })
                    else:
                        failed_records.append({
                            "type": "deal",
                            "id": deal.id,
                            "error": result.get("error")
                        })
                except Exception as e:
                    failed_records.append({
                        "type": "deal",
                        "id": deal.id,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "updated_records": updated_records,
                "failed_records": failed_records,
                "total_updated": len(updated_records),
                "total_failed": len(failed_records)
            }
            
        except Exception as e:
            logger.error(f"Failed to update CRM records: {e}")
            return {
                "success": False,
                "error": f"Failed to update CRM records: {str(e)}"
            }
    
    async def get_crm_analytics(
        self,
        brand_id: int,
        crm_platform: str,
        date_range: str = "30d"
    ) -> Dict[str, Any]:
        """Get CRM analytics and insights"""
        try:
            await self.initialize()
            
            # Calculate date range
            end_date = datetime.now()
            if date_range == "7d":
                start_date = end_date - timedelta(days=7)
            elif date_range == "30d":
                start_date = end_date - timedelta(days=30)
            elif date_range == "90d":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)
            
            db = next(get_db())
            
            # Get leads created in date range
            leads = db.query(EricLead).filter(
                and_(
                    EricLead.brand_id == brand_id,
                    EricLead.created_at >= start_date,
                    EricLead.created_at <= end_date
                )
            ).all()
            
            # Get deals created in date range
            deals = db.query(EricDeal).filter(
                and_(
                    EricDeal.brand_id == brand_id,
                    EricDeal.created_at >= start_date,
                    EricDeal.created_at <= end_date
                )
            ).all()
            
            # Calculate analytics
            total_leads = len(leads)
            qualified_leads = len([l for l in leads if l.lead_status == LeadStatus.QUALIFIED])
            converted_leads = len([l for l in leads if l.lead_status in [LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST]])
            
            total_deals = len(deals)
            won_deals = len([d for d in deals if d.sales_stage == SalesStage.CLOSED and d.win_reason])
            total_revenue = sum([d.deal_value for d in deals if d.sales_stage == SalesStage.CLOSED and d.win_reason])
            
            # Calculate conversion rates
            lead_to_qualified_rate = (qualified_leads / total_leads * 100) if total_leads > 0 else 0
            qualified_to_deal_rate = (total_deals / qualified_leads * 100) if qualified_leads > 0 else 0
            deal_to_won_rate = (won_deals / total_deals * 100) if total_deals > 0 else 0
            
            analytics = {
                "date_range": date_range,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "leads": {
                    "total": total_leads,
                    "qualified": qualified_leads,
                    "converted": converted_leads,
                    "lead_to_qualified_rate": round(lead_to_qualified_rate, 2),
                    "qualified_to_deal_rate": round(qualified_to_deal_rate, 2)
                },
                "deals": {
                    "total": total_deals,
                    "won": won_deals,
                    "total_revenue": total_revenue,
                    "deal_to_won_rate": round(deal_to_won_rate, 2),
                    "average_deal_value": round(total_revenue / won_deals, 2) if won_deals > 0 else 0
                },
                "pipeline": {
                    "prospecting": len([d for d in deals if d.sales_stage == SalesStage.PROSPECTING]),
                    "qualification": len([d for d in deals if d.sales_stage == SalesStage.QUALIFICATION]),
                    "proposal": len([d for d in deals if d.sales_stage == SalesStage.PROPOSAL]),
                    "negotiation": len([d for d in deals if d.sales_stage == SalesStage.NEGOTIATION]),
                    "closing": len([d for d in deals if d.sales_stage == SalesStage.CLOSING])
                }
            }
            
            return {
                "success": True,
                "crm_platform": crm_platform,
                "analytics": analytics
            }
            
        except Exception as e:
            logger.error(f"Failed to get CRM analytics: {e}")
            return {
                "success": False,
                "error": f"Failed to get CRM analytics: {str(e)}"
            }
    
    async def _sync_to_salesforce(
        self,
        lead_data: Dict[str, Any],
        crm_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync lead to Salesforce"""
        try:
            # Use integration manager to call Salesforce API
            result = await self.integration_manager.call_integration_api(
                integration_type="salesforce",
                endpoint="leads",
                method="POST",
                data=lead_data,
                config=crm_config
            )
            
            return {
                "success": True,
                "crm_id": result.get("id"),
                "platform": "salesforce"
            }
            
        except Exception as e:
            logger.error(f"Failed to sync to Salesforce: {e}")
            return {
                "success": False,
                "error": f"Failed to sync to Salesforce: {str(e)}"
            }
    
    async def _sync_to_hubspot(
        self,
        lead_data: Dict[str, Any],
        crm_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync lead to HubSpot"""
        try:
            # Use integration manager to call HubSpot API
            result = await self.integration_manager.call_integration_api(
                integration_type="hubspot",
                endpoint="contacts",
                method="POST",
                data=lead_data,
                config=crm_config
            )
            
            return {
                "success": True,
                "crm_id": result.get("id"),
                "platform": "hubspot"
            }
            
        except Exception as e:
            logger.error(f"Failed to sync to HubSpot: {e}")
            return {
                "success": False,
                "error": f"Failed to sync to HubSpot: {str(e)}"
            }
    
    async def _sync_to_pipedrive(
        self,
        lead_data: Dict[str, Any],
        crm_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync lead to Pipedrive"""
        try:
            # Use integration manager to call Pipedrive API
            result = await self.integration_manager.call_integration_api(
                integration_type="pipedrive",
                endpoint="persons",
                method="POST",
                data=lead_data,
                config=crm_config
            )
            
            return {
                "success": True,
                "crm_id": result.get("id"),
                "platform": "pipedrive"
            }
            
        except Exception as e:
            logger.error(f"Failed to sync to Pipedrive: {e}")
            return {
                "success": False,
                "error": f"Failed to sync to Pipedrive: {str(e)}"
            }
    
    async def _sync_deal_to_salesforce(
        self,
        deal_data: Dict[str, Any],
        crm_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync deal to Salesforce"""
        try:
            # Use integration manager to call Salesforce API
            result = await self.integration_manager.call_integration_api(
                integration_type="salesforce",
                endpoint="opportunities",
                method="POST",
                data=deal_data,
                config=crm_config
            )
            
            return {
                "success": True,
                "crm_id": result.get("id"),
                "platform": "salesforce"
            }
            
        except Exception as e:
            logger.error(f"Failed to sync deal to Salesforce: {e}")
            return {
                "success": False,
                "error": f"Failed to sync deal to Salesforce: {str(e)}"
            }
    
    async def _sync_deal_to_hubspot(
        self,
        deal_data: Dict[str, Any],
        crm_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync deal to HubSpot"""
        try:
            # Use integration manager to call HubSpot API
            result = await self.integration_manager.call_integration_api(
                integration_type="hubspot",
                endpoint="deals",
                method="POST",
                data=deal_data,
                config=crm_config
            )
            
            return {
                "success": True,
                "crm_id": result.get("id"),
                "platform": "hubspot"
            }
            
        except Exception as e:
            logger.error(f"Failed to sync deal to HubSpot: {e}")
            return {
                "success": False,
                "error": f"Failed to sync deal to HubSpot: {str(e)}"
            }
    
    async def _sync_deal_to_pipedrive(
        self,
        deal_data: Dict[str, Any],
        crm_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync deal to Pipedrive"""
        try:
            # Use integration manager to call Pipedrive API
            result = await self.integration_manager.call_integration_api(
                integration_type="pipedrive",
                endpoint="deals",
                method="POST",
                data=deal_data,
                config=crm_config
            )
            
            return {
                "success": True,
                "crm_id": result.get("id"),
                "platform": "pipedrive"
            }
            
        except Exception as e:
            logger.error(f"Failed to sync deal to Pipedrive: {e}")
            return {
                "success": False,
                "error": f"Failed to sync deal to Pipedrive: {str(e)}"
            }
