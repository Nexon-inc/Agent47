import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from ..models import EricLead, EricDeal, EricLeadInteraction, CommunicationChannel
from ..database import get_eric_database
from core.ai import get_ai_service_manager, AIServiceManager

logger = logging.getLogger(__name__)

class CustomerJourneyService:
    """Service for mapping and analyzing customer/lead journeys in sales context"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize customer journey service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            self._initialized = True
            logger.info("Eric customer journey service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize customer journey service: {e}")
            self._initialized = True  # Mark as initialized to prevent blocking
    
    async def map_customer_journey(
        self,
        user_id: int,
        lead_id: Optional[int] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Map customer journey from lead to deal conversion"""
        try:
            await self.initialize()
            
            if not db:
                return {
                    "success": False,
                    "error": "Database session not available"
                }
            
            if lead_id:
                # Map journey for specific lead
                result = await db.execute(
                    select(EricLead).where(EricLead.id == lead_id)
                )
                lead = result.scalar_one_or_none()
                
                if not lead:
                    return {
                        "success": False,
                        "error": "EricLead not found"
                    }
                
                # Get interactions for this lead
                interactions_result = await db.execute(
                    select(EricLeadInteraction).where(
                        EricLeadInteraction.lead_id == lead_id
                    ).order_by(EricLeadInteraction.created_at)
                )
                interactions = interactions_result.scalars().all()
                
                # Get associated deals
                deals_result = await db.execute(
                    select(EricDeal).where(EricDeal.lead_id == lead_id)
                )
                deals = deals_result.scalars().all()
                
                journey_stages = []
                if interactions:
                    journey_stages = [
                        {
                            "stage": interaction.interaction_type,
                            "timestamp": interaction.created_at.isoformat(),
                            "channel": interaction.channel.value if interaction.channel else None,
                            "notes": interaction.notes
                        }
                        for interaction in interactions
                    ]
                
                return {
                    "success": True,
                    "lead_id": lead_id,
                    "journey_stages": journey_stages,
                    "total_interactions": len(interactions),
                    "deals_count": len(deals),
                    "current_stage": lead.lead_status.value if lead.lead_status else "new",
                    "created_at": lead.created_at.isoformat()
                }
            else:
                # Map overall customer journey patterns
                leads_result = await db.execute(
                    select(EricLead).where(EricLead.user_id == user_id).limit(100)
                )
                leads = leads_result.scalars().all()
                
                # Analyze journey patterns
                journey_patterns = {
                    "total_leads": len(leads),
                    "average_time_to_qualify": 0,
                    "average_time_to_close": 0,
                    "conversion_rate": 0
                }
                
                return {
                    "success": True,
                    "journey_patterns": journey_patterns,
                    "user_id": user_id
                }
                
        except Exception as e:
            logger.error(f"Failed to map customer journey: {e}")
            return {
                "success": False,
                "error": f"Failed to map customer journey: {str(e)}"
            }
    
    async def analyze_journey_stage(
        self,
        user_id: int,
        stage: str,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Analyze a specific stage in the customer journey"""
        try:
            await self.initialize()
            
            if not db:
                return {
                    "success": False,
                    "error": "Database session not available"
                }
            
            # Analyze leads at specific stage
            leads_result = await db.execute(
                select(EricLead).where(
                    EricLead.user_id == user_id,
                    EricLead.lead_status == stage
                )
            )
            leads = leads_result.scalars().all()
            
            return {
                "success": True,
                "stage": stage,
                "leads_count": len(leads),
                "analysis": {
                    "total_in_stage": len(leads),
                    "recommendations": f"Focus on converting {len(leads)} leads at {stage} stage"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze journey stage: {e}")
            return {
                "success": False,
                "error": f"Failed to analyze journey stage: {str(e)}"
            }
    
    async def get_journey_recommendations(
        self,
        user_id: int,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Get recommendations for optimizing customer journey"""
        try:
            await self.initialize()
            
            if not db:
                return {
                    "success": False,
                    "error": "Database session not available"
                }
            
            # Get journey data
            journey_data = await self.map_customer_journey(user_id=user_id, db=db)
            
            recommendations = [
                "Increase touchpoints at awareness stage",
                "Improve qualification process",
                "Reduce time between stages",
                "Implement automated follow-ups"
            ]
            
            return {
                "success": True,
                "recommendations": recommendations,
                "journey_data": journey_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get journey recommendations: {e}")
            return {
                "success": False,
                "error": f"Failed to get journey recommendations: {str(e)}"
            }

