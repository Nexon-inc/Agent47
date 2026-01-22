import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload
import random
from core.config import settings
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_clara_database
from ..models import (
    ClaraSupportTicket, ClaraCustomerInteraction, CustomerProfile,
    TicketPriority, TicketStatus, TicketCategory, SupportChannel
)

logger = logging.getLogger(__name__)

class CustomerLoyaltyService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
    
    async def initialize(self):
        """Initialize customer loyalty service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Customer loyalty service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize customer loyalty service: {e}")
            raise
    
    async def calculate_trust_score(
        self,
        customer_id: int
    ) -> Dict[str, Any]:
        """Calculate customer trust score and loyalty prediction"""
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
                
                # Get customer support history
                tickets_query = select(ClaraSupportTicket).where(ClaraSupportTicket.customer_id == customer_id)
                tickets_result = await session.execute(tickets_query)
                tickets = tickets_result.scalars().all()
                
                # Calculate trust score based on multiple factors
                trust_score = await self._calculate_trust_score_factors(profile, tickets)
                
                # Predict churn risk
                churn_risk = await self._predict_churn_risk(profile, tickets, trust_score)
                
                # Update customer profile
                profile.trust_score = trust_score
                profile.loyalty_level = await self._determine_loyalty_level(trust_score)
                profile.metadata = {
                    **profile.metadata,
                    "loyalty_analysis": {
                        "trust_score": trust_score,
                        "churn_risk": churn_risk,
                        "loyalty_level": profile.loyalty_level,
                        "last_updated": datetime.utcnow().isoformat(),
                        "factors": {
                            "support_frequency": len(tickets),
                            "satisfaction_avg": profile.average_satisfaction,
                            "resolution_rate": profile.resolved_tickets / profile.total_support_tickets if profile.total_support_tickets > 0 else 0,
                            "response_time_avg": await self._calculate_avg_response_time(tickets)
                        }
                    }
                }
                
                await session.commit()
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "trust_score": trust_score,
                    "churn_risk": churn_risk,
                    "loyalty_level": profile.loyalty_level,
                    "analysis": profile.metadata.get("loyalty_analysis", {})
                }
                
        except Exception as e:
            logger.error(f"Failed to calculate trust score for customer {customer_id}: {e}")
            return {
                "success": False,
                "customer_id": customer_id,
                "error": str(e)
            }
    
    async def generate_loyalty_rewards(
        self,
        customer_id: int,
        reward_type: str = "automatic"
    ) -> Dict[str, Any]:
        """Generate rewards for loyal customers"""
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
                
                # Determine reward based on loyalty level and trust score
                reward = await self._determine_reward(profile, reward_type)
                
                # Create reward record
                reward_data = {
                    "customer_id": customer_id,
                    "reward_type": reward["type"],
                    "reward_value": reward["value"],
                    "description": reward["description"],
                    "expires_at": datetime.utcnow() + timedelta(days=reward["expiry_days"]),
                    "status": "active",
                    "metadata": {
                        "loyalty_level": profile.loyalty_level,
                        "trust_score": profile.trust_score,
                        "generated_at": datetime.utcnow().isoformat()
                    }
                }
                
                # Store reward in dedicated rewards table
                profile.metadata = {
                    **profile.metadata,
                    "rewards": profile.metadata.get("rewards", []) + [reward_data]
                }
                
                await session.commit()
                
                # Publish event for notification
                await self.event_bus.publish(
                    "clara.loyalty.reward_generated",
                    {
                        "customer_id": customer_id,
                        "reward": reward_data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "reward": reward_data,
                    "message": f"Loyalty reward generated: {reward['description']}"
                }
                
        except Exception as e:
            logger.error(f"Failed to generate loyalty reward for customer {customer_id}: {e}")
            return {
                "success": False,
                "customer_id": customer_id,
                "error": str(e)
            }
    
    async def get_loyalty_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get loyalty program analytics"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get all customer profiles
                profiles_query = select(CustomerProfile)
                if date_from:
                    profiles_query = profiles_query.where(CustomerProfile.created_at >= date_from)
                if date_to:
                    profiles_query = profiles_query.where(CustomerProfile.created_at <= date_to)
                
                profiles_result = await session.execute(profiles_query)
                profiles = profiles_result.scalars().all()
                
                # Calculate loyalty metrics
                loyalty_metrics = await self._calculate_loyalty_metrics(profiles)
                
                return {
                    "success": True,
                    "analytics": loyalty_metrics,
                    "date_range": {
                        "from": date_from.isoformat() if date_from else None,
                        "to": date_to.isoformat() if date_to else None
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get loyalty analytics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _calculate_trust_score_factors(
        self,
        profile: CustomerProfile,
        tickets: List[ClaraSupportTicket]
    ) -> float:
        """Calculate trust score based on multiple factors"""
        try:
            # Base score from profile
            base_score = 0.5
            
            # Support history factor (0-0.2)
            support_factor = min(len(tickets) / 10, 0.2)  # Cap at 0.2 for 10+ tickets
            
            # Satisfaction factor (0-0.2)
            satisfaction_factor = (profile.average_satisfaction - 1) / 4 * 0.2 if profile.average_satisfaction > 0 else 0
            
            # Resolution rate factor (0-0.15)
            resolution_rate = profile.resolved_tickets / profile.total_support_tickets if profile.total_support_tickets > 0 else 0
            resolution_factor = resolution_rate * 0.15
            
            # Response time factor (0-0.15)
            avg_response_time = await self._calculate_avg_response_time(tickets)
            response_factor = max(0, (60 - avg_response_time) / 60) * 0.15  # Better score for faster response
            
            # Loyalty level bonus
            loyalty_bonus = {
                "new": 0.0,
                "returning": 0.05,
                "loyal": 0.1,
                "vip": 0.15
            }.get(profile.loyalty_level, 0.0)
            
            total_score = base_score + support_factor + satisfaction_factor + resolution_factor + response_factor + loyalty_bonus
            
            return min(total_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating trust score factors: {e}")
            return 0.5
    
    async def _predict_churn_risk(
        self,
        profile: CustomerProfile,
        tickets: List[ClaraSupportTicket],
        trust_score: float
    ) -> float:
        """Predict customer churn risk"""
        try:
            # Base churn risk
            base_risk = 0.3
            
            # Trust score reduces risk
            trust_reduction = trust_score * 0.4
            
            # Recent activity factor
            recent_tickets = [t for t in tickets if t.created_at > datetime.utcnow() - timedelta(days=30)]
            activity_factor = max(0, (5 - len(recent_tickets)) / 5) * 0.2  # Higher risk if no recent activity
            
            # Satisfaction factor
            satisfaction_factor = max(0, (3 - profile.average_satisfaction) / 2) * 0.2 if profile.average_satisfaction > 0 else 0.2
            
            # Resolution rate factor
            resolution_rate = profile.resolved_tickets / profile.total_support_tickets if profile.total_support_tickets > 0 else 0
            resolution_factor = (1 - resolution_rate) * 0.2
            
            total_risk = base_risk - trust_reduction + activity_factor + satisfaction_factor + resolution_factor
            
            return max(0.0, min(total_risk, 1.0))  # Cap between 0 and 1
            
        except Exception as e:
            logger.error(f"Error predicting churn risk: {e}")
            return 0.5
    
    async def _determine_loyalty_level(self, trust_score: float) -> str:
        """Determine loyalty level based on trust score"""
        if trust_score >= 0.8:
            return "vip"
        elif trust_score >= 0.6:
            return "loyal"
        elif trust_score >= 0.4:
            return "returning"
        else:
            return "new"
    
    async def _calculate_avg_response_time(self, tickets: List[ClaraSupportTicket]) -> float:
        """Calculate average response time for tickets"""
        try:
            response_times = []
            for ticket in tickets:
                if ticket.first_response_time:
                    response_times.append(ticket.first_response_time)
            
            return sum(response_times) / len(response_times) if response_times else 30.0  # Default 30 minutes
            
        except Exception as e:
            logger.error(f"Error calculating average response time: {e}")
            return 30.0
    
    async def _determine_reward(
        self,
        profile: CustomerProfile,
        reward_type: str
    ) -> Dict[str, Any]:
        """Determine appropriate reward for customer"""
        try:
            # Base rewards by loyalty level
            base_rewards = {
                "new": {
                    "type": "discount",
                    "value": 5,
                    "description": "5% discount on next purchase",
                    "expiry_days": 30
                },
                "returning": {
                    "type": "discount",
                    "value": 10,
                    "description": "10% discount on next purchase",
                    "expiry_days": 45
                },
                "loyal": {
                    "type": "discount",
                    "value": 15,
                    "description": "15% discount on next purchase",
                    "expiry_days": 60
                },
                "vip": {
                    "type": "discount",
                    "value": 20,
                    "description": "20% discount on next purchase",
                    "expiry_days": 90
                }
            }
            
            # Get base reward
            base_reward = base_rewards.get(profile.loyalty_level, base_rewards["new"])
            
            # Add bonus for high trust score
            if profile.trust_score >= 0.8:
                base_reward["value"] += 5
                base_reward["description"] = f"{base_reward['value']}% discount on next purchase (VIP bonus included)"
            
            # Special rewards for milestone achievements
            if profile.total_support_tickets >= 50:
                base_reward["type"] = "free_shipping"
                base_reward["value"] = 0
                base_reward["description"] = "Free shipping on next order (50+ support interactions milestone)"
            
            return base_reward
            
        except Exception as e:
            logger.error(f"Error determining reward: {e}")
            return {
                "type": "discount",
                "value": 5,
                "description": "5% discount on next purchase",
                "expiry_days": 30
            }
    
    async def _calculate_loyalty_metrics(
        self,
        profiles: List[CustomerProfile]
    ) -> Dict[str, Any]:
        """Calculate loyalty program metrics"""
        try:
            total_customers = len(profiles)
            if total_customers == 0:
                return {
                    "total_customers": 0,
                    "loyalty_distribution": {},
                    "average_trust_score": 0,
                    "average_churn_risk": 0,
                    "rewards_generated": 0
                }
            
            # Loyalty level distribution
            loyalty_distribution = {}
            trust_scores = []
            churn_risks = []
            rewards_count = 0
            
            for profile in profiles:
                # Count loyalty levels
                loyalty_distribution[profile.loyalty_level] = loyalty_distribution.get(profile.loyalty_level, 0) + 1
                
                # Collect trust scores
                trust_scores.append(profile.trust_score)
                
                # Calculate churn risk
                churn_risk = await self._predict_churn_risk(profile, [], profile.trust_score)
                churn_risks.append(churn_risk)
                
                # Count rewards
                rewards_count += len(profile.metadata.get("rewards", []))
            
            return {
                "total_customers": total_customers,
                "loyalty_distribution": loyalty_distribution,
                "average_trust_score": sum(trust_scores) / len(trust_scores),
                "average_churn_risk": sum(churn_risks) / len(churn_risks),
                "rewards_generated": rewards_count,
                "loyalty_percentages": {
                    level: (count / total_customers) * 100 
                    for level, count in loyalty_distribution.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating loyalty metrics: {e}")
            return {
                "total_customers": 0,
                "loyalty_distribution": {},
                "average_trust_score": 0,
                "average_churn_risk": 0,
                "rewards_generated": 0
            }
