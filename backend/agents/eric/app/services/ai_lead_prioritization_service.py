from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload

from ..database import get_eric_database
# NLPUtils removed - not used
from core.integrations.integration_manager import IntegrationManager
from core.analytics.analytics_manager import AnalyticsManager
from core.event_bus.kafka_manager import EventBus as KafkaManager
from core.cache.redis_manager import RedisManager
from ..models import Lead, LeadInteraction, Deal, SalesActivity, SalesRep, CustomerProfile
from ..models import LeadSource

logger = logging.getLogger(__name__)

class AILeadPrioritizationService:
    """Service for AI-powered lead prioritization and scoring"""
    
    def __init__(self):
        # NLPUtils removed - not used
        self.ai_service_manager = None
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        self.kafka_manager = KafkaManager()
        self.redis_manager = RedisManager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize AI lead prioritization service"""
        if self._initialized:
            return
        
        try:
            from core.ai import get_ai_service_manager
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.analytics_manager.initialize()
            await self.kafka_manager.initialize()
            await self.redis_manager.initialize()
            self._initialized = True
            logger.info("AI lead prioritization service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI lead prioritization service: {e}")
            raise
        
        # Define intent signals and their weights
        self.intent_signals = {
            "website_visit": {
                "weight": 10,
                "decay_rate": 0.1,  # per day
                "max_score": 100
            },
            "email_open": {
                "weight": 15,
                "decay_rate": 0.15,
                "max_score": 100
            },
            "email_click": {
                "weight": 25,
                "decay_rate": 0.2,
                "max_score": 100
            },
            "form_submission": {
                "weight": 50,
                "decay_rate": 0.05,
                "max_score": 100
            },
            "demo_request": {
                "weight": 75,
                "decay_rate": 0.02,
                "max_score": 100
            },
            "pricing_page_visit": {
                "weight": 30,
                "decay_rate": 0.12,
                "max_score": 100
            },
            "social_media_engagement": {
                "weight": 20,
                "decay_rate": 0.18,
                "max_score": 100
            },
            "phone_call": {
                "weight": 60,
                "decay_rate": 0.08,
                "max_score": 100
            },
            "chat_interaction": {
                "weight": 35,
                "decay_rate": 0.14,
                "max_score": 100
            }
        }
        
        # Define lead characteristics scoring
        self.lead_characteristics = {
            "company_size": {
                "startup": 20,
                "small": 30,
                "medium": 40,
                "large": 50,
                "enterprise": 60
            },
            "budget_range": {
                "low": 20,
                "medium": 40,
                "high": 60,
                "enterprise": 80
            },
            "timeline": {
                "immediate": 50,
                "this_quarter": 40,
                "this_year": 30,
                "future": 20
            },
            "decision_maker": {
                "yes": 40,
                "no": 10,
                "unknown": 20
            }
        }
    
    async def prioritize_leads(
        self,
        lead_ids: Optional[List[int]] = None,
        rep_id: Optional[int] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Prioritize leads based on AI analysis of intent signals and characteristics"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Get leads to prioritize
                leads = await self._get_leads_for_prioritization(session, lead_ids, rep_id, limit)
                
                prioritized_leads = []
                for lead in leads:
                    # Calculate intent score
                    intent_score = await self._calculate_intent_score(session, lead.id)
                    
                    # Calculate characteristic score
                    characteristic_score = await self._calculate_characteristic_score(lead)
                    
                    # Calculate engagement score
                    engagement_score = await self._calculate_engagement_score(session, lead.id)
                    
                    # Calculate urgency score
                    urgency_score = await self._calculate_urgency_score(lead)
                    
                    # Calculate total priority score
                    total_score = (
                        intent_score * 0.4 +
                        characteristic_score * 0.3 +
                        engagement_score * 0.2 +
                        urgency_score * 0.1
                    )
                    
                    # Determine priority level
                    priority_level = self._determine_priority_level(total_score)
                    
                    # Get next best action
                    next_action = await self._determine_next_action(session, lead, total_score)
                    
                    prioritized_leads.append({
                        "lead_id": lead.id,
                        "name": lead.name,
                        "company": lead.company,
                        "total_score": round(total_score, 2),
                        "priority_level": priority_level,
                        "intent_score": round(intent_score, 2),
                        "characteristic_score": round(characteristic_score, 2),
                        "engagement_score": round(engagement_score, 2),
                        "urgency_score": round(urgency_score, 2),
                        "next_action": next_action,
                        "last_activity": lead.updated_at.isoformat() if lead.updated_at else None
                    })
                
                # Sort by total score (highest first)
                prioritized_leads.sort(key=lambda x: x["total_score"], reverse=True)
                
                # Store prioritization results
                await self._store_prioritization_results(session, prioritized_leads)
                
                # Track analytics
                await self.analytics_manager.log_event(
                    "leads_prioritized",
                    {
                        "total_leads": len(prioritized_leads),
                        "rep_id": rep_id,
                        "average_score": sum(l["total_score"] for l in prioritized_leads) / len(prioritized_leads) if prioritized_leads else 0
                    }
                )
                
                return {
                    "success": True,
                    "prioritized_leads": prioritized_leads,
                    "total_leads": len(prioritized_leads),
                    "prioritization_date": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error prioritizing leads: {e}")
            return {"success": False, "error": str(e)}
    
    async def track_intent_signal(
        self,
        lead_id: int,
        signal_type: str,
        signal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track an intent signal for a lead"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Validate signal type
                if signal_type not in self.intent_signals:
                    return {"success": False, "error": f"Invalid signal type: {signal_type}"}
                
                # Create lead interaction record
                interaction = LeadInteraction(
                    lead_id=lead_id,
                    interaction_type=signal_type,
                    interaction_data=signal_data,
                    timestamp=datetime.utcnow()
                )
                
                session.add(interaction)
                await session.commit()
                
                # Update lead's last activity
                await self._update_lead_activity(session, lead_id)
                
                # Trigger real-time prioritization update
                await self._trigger_prioritization_update(lead_id)
                
                # Track analytics
                await self.analytics_manager.log_event(
                    "intent_signal_tracked",
                    {
                        "lead_id": lead_id,
                        "signal_type": signal_type,
                        "signal_weight": self.intent_signals[signal_type]["weight"]
                    }
                )
                
                return {
                    "success": True,
                    "signal_tracked": True,
                    "lead_id": lead_id,
                    "signal_type": signal_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error tracking intent signal: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_lead_priority_details(
        self,
        lead_id: int
    ) -> Dict[str, Any]:
        """Get detailed priority analysis for a specific lead"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Get lead information
                lead = await self._get_lead_with_context(session, lead_id)
                if not lead:
                    return {"success": False, "error": "Lead not found"}
                
                # Calculate all scores
                intent_score = await self._calculate_intent_score(session, lead_id)
                characteristic_score = await self._calculate_characteristic_score(lead)
                engagement_score = await self._calculate_engagement_score(session, lead_id)
                urgency_score = await self._calculate_urgency_score(lead)
                
                total_score = (
                    intent_score * 0.4 +
                    characteristic_score * 0.3 +
                    engagement_score * 0.2 +
                    urgency_score * 0.1
                )
                
                # Get recent intent signals
                recent_signals = await self._get_recent_intent_signals(session, lead_id)
                
                # Get engagement history
                engagement_history = await self._get_engagement_history(session, lead_id)
                
                # Get comparison with similar leads
                similar_leads_comparison = await self._compare_with_similar_leads(session, lead)
                
                return {
                    "success": True,
                    "lead_id": lead_id,
                    "lead_info": {
                        "name": lead.name,
                        "company": lead.company,
                        "industry": lead.industry,
                        "stage": lead.stage,
                        "source": lead.source
                    },
                    "priority_analysis": {
                        "total_score": round(total_score, 2),
                        "priority_level": self._determine_priority_level(total_score),
                        "intent_score": round(intent_score, 2),
                        "characteristic_score": round(characteristic_score, 2),
                        "engagement_score": round(engagement_score, 2),
                        "urgency_score": round(urgency_score, 2)
                    },
                    "recent_intent_signals": recent_signals,
                    "engagement_history": engagement_history,
                    "similar_leads_comparison": similar_leads_comparison,
                    "recommendations": await self._generate_priority_recommendations(
                        lead, total_score, recent_signals
                    )
                }
                
        except Exception as e:
            logger.error(f"Error getting lead priority details: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_prioritization_weights(
        self,
        new_weights: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update the weights for intent signals and characteristics"""
        try:
            # Validate new weights
            for signal_type, weights in new_weights.items():
                if signal_type in self.intent_signals:
                    if "weight" in weights:
                        self.intent_signals[signal_type]["weight"] = weights["weight"]
                    if "decay_rate" in weights:
                        self.intent_signals[signal_type]["decay_rate"] = weights["decay_rate"]
                    if "max_score" in weights:
                        self.intent_signals[signal_type]["max_score"] = weights["max_score"]
                elif signal_type in self.lead_characteristics:
                    for category, score in weights.items():
                        if category in self.lead_characteristics[signal_type]:
                            self.lead_characteristics[signal_type][category] = score
            
            # Store updated weights in cache
            await self.redis_manager.set(
                "prioritization_weights",
                json.dumps({
                    "intent_signals": self.intent_signals,
                    "lead_characteristics": self.lead_characteristics
                }),
                expire=86400
            )
            
            # Track analytics
            await self.analytics_manager.log_event(
                "prioritization_weights_updated",
                {"updated_weights": new_weights}
            )
            
            return {
                "success": True,
                "weights_updated": True,
                "current_weights": {
                    "intent_signals": self.intent_signals,
                    "lead_characteristics": self.lead_characteristics
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating prioritization weights: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_prioritization_insights(
        self,
        rep_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get insights about lead prioritization performance"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Get prioritization history
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Query prioritization activities
                query = select(SalesActivity).where(
                    and_(
                        SalesActivity.activity_type == "lead_prioritization",
                        SalesActivity.created_at >= start_date
                    )
                )
                
                if rep_id:
                    query = query.where(SalesActivity.rep_id == rep_id)
                
                activities = await session.execute(query)
                activities = activities.scalars().all()
                
                # Analyze insights
                total_prioritizations = len(activities)
                average_scores = []
                conversion_rates = []
                
                for activity in activities:
                    metadata = activity.metadata or {}
                    if "total_score" in metadata:
                        average_scores.append(metadata["total_score"])
                    
                    # Check if lead was converted
                    lead_converted = await self._check_lead_conversion(session, activity.lead_id)
                    conversion_rates.append(1 if lead_converted else 0)
                
                insights = {
                    "total_prioritizations": total_prioritizations,
                    "average_priority_score": sum(average_scores) / len(average_scores) if average_scores else 0,
                    "conversion_rate": (sum(conversion_rates) / len(conversion_rates)) * 100 if conversion_rates else 0,
                    "top_intent_signals": await self._get_top_intent_signals(session, start_date),
                    "priority_distribution": await self._get_priority_distribution(activities),
                    "recommendations": await self._generate_insight_recommendations(
                        total_prioritizations, average_scores, conversion_rates
                    )
                }
                
                return {
                    "success": True,
                    "insights": insights,
                    "analysis_period": f"Last {days} days"
                }
                
        except Exception as e:
            logger.error(f"Error getting prioritization insights: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_leads_for_prioritization(
        self,
        session: AsyncSession,
        lead_ids: Optional[List[int]],
        rep_id: Optional[int],
        limit: int
    ) -> List[Lead]:
        """Get leads for prioritization with filters"""
        query = select(Lead)
        
        if lead_ids:
            query = query.where(Lead.id.in_(lead_ids))
        
        if rep_id:
            query = query.where(Lead.assigned_rep_id == rep_id)
        
        # Only include active leads
        query = query.where(Lead.status.in_(["new", "contacted", "qualified", "proposal"]))
        
        query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def _calculate_intent_score(
        self,
        session: AsyncSession,
        lead_id: int
    ) -> float:
        """Calculate intent score based on recent signals"""
        try:
            # Get recent interactions
            start_date = datetime.utcnow() - timedelta(days=30)
            query = select(LeadInteraction).where(
                and_(
                    LeadInteraction.lead_id == lead_id,
                    LeadInteraction.timestamp >= start_date
                )
            )
            
            interactions = await session.execute(query)
            interactions = interactions.scalars().all()
            
            total_score = 0
            for interaction in interactions:
                signal_type = interaction.interaction_type
                if signal_type in self.intent_signals:
                    signal_config = self.intent_signals[signal_type]
                    
                    # Calculate time decay
                    days_ago = (datetime.utcnow() - interaction.timestamp).days
                    decay_factor = max(0, 1 - (signal_config["decay_rate"] * days_ago))
                    
                    # Calculate signal score
                    signal_score = signal_config["weight"] * decay_factor
                    signal_score = min(signal_score, signal_config["max_score"])
                    
                    total_score += signal_score
            
            return min(total_score, 100)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Error calculating intent score: {e}")
            return 0
    
    async def _calculate_characteristic_score(self, lead: Lead) -> float:
        """Calculate score based on lead characteristics"""
        try:
            score = 0
            
            # Company size score
            if lead.company_size in self.lead_characteristics["company_size"]:
                score += self.lead_characteristics["company_size"][lead.company_size]
            
            # Budget score
            if lead.budget:
                if lead.budget < 10000:
                    budget_category = "low"
                elif lead.budget < 50000:
                    budget_category = "medium"
                elif lead.budget < 200000:
                    budget_category = "high"
                else:
                    budget_category = "enterprise"
                
                score += self.lead_characteristics["budget_range"][budget_category]
            
            # Timeline score
            if lead.timeline:
                if lead.timeline == "immediate":
                    timeline_category = "immediate"
                elif lead.timeline in ["this_quarter", "q1", "q2", "q3", "q4"]:
                    timeline_category = "this_quarter"
                elif lead.timeline == "this_year":
                    timeline_category = "this_year"
                else:
                    timeline_category = "future"
                
                score += self.lead_characteristics["timeline"][timeline_category]
            
            # Decision maker score
            if lead.is_decision_maker:
                score += self.lead_characteristics["decision_maker"]["yes"]
            else:
                score += self.lead_characteristics["decision_maker"]["unknown"]
            
            return min(score, 100)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Error calculating characteristic score: {e}")
            return 0
    
    async def _calculate_engagement_score(
        self,
        session: AsyncSession,
        lead_id: int
    ) -> float:
        """Calculate engagement score based on interaction frequency and quality"""
        try:
            # Get recent interactions
            start_date = datetime.utcnow() - timedelta(days=60)
            query = select(LeadInteraction).where(
                and_(
                    LeadInteraction.lead_id == lead_id,
                    LeadInteraction.timestamp >= start_date
                )
            )
            
            interactions = await session.execute(query)
            interactions = interactions.scalars().all()
            
            if not interactions:
                return 0
            
            # Calculate engagement metrics
            total_interactions = len(interactions)
            unique_days = len(set(i.timestamp.date() for i in interactions))
            avg_interactions_per_day = total_interactions / unique_days if unique_days > 0 else 0
            
            # Calculate engagement score
            engagement_score = min(avg_interactions_per_day * 20, 100)  # Scale factor
            
            return engagement_score
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0
    
    async def _calculate_urgency_score(self, lead: Lead) -> float:
        """Calculate urgency score based on timeline and other factors"""
        try:
            urgency_score = 0
        
            # Timeline urgency
            if lead.timeline == "immediate":
                urgency_score += 50
            elif lead.timeline in ["this_quarter", "q1", "q2", "q3", "q4"]:
                urgency_score += 30
            elif lead.timeline == "this_year":
                urgency_score += 20
            else:
                urgency_score += 10
            
            # Budget urgency (higher budget = higher urgency)
            if lead.budget and lead.budget > 100000:
                urgency_score += 30
            elif lead.budget and lead.budget > 50000:
                urgency_score += 20
            elif lead.budget and lead.budget > 10000:
                urgency_score += 10
            
            # Stage urgency
            if lead.stage in ["proposal", "negotiation"]:
                urgency_score += 20
            elif lead.stage == "qualified":
                urgency_score += 15
            elif lead.stage == "contacted":
                urgency_score += 10
            
            return min(urgency_score, 100)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Error calculating urgency score: {e}")
            return 0
    
    def _determine_priority_level(self, total_score: float) -> str:
        """Determine priority level based on total score"""
        if total_score >= 80:
            return "critical"
        elif total_score >= 60:
            return "high"
        elif total_score >= 40:
            return "medium"
        elif total_score >= 20:
            return "low"
        else:
            return "very_low"
    
    async def _determine_next_action(
        self,
        session: AsyncSession,
        lead: Lead,
        total_score: float
    ) -> Dict[str, Any]:
        """Determine the next best action for a lead"""
        try:
            if total_score >= 80:
                return {
                    "action": "immediate_call",
                    "priority": "urgent",
                    "reason": "High intent signals and engagement"
                }
            elif total_score >= 60:
                return {
                    "action": "schedule_demo",
                    "priority": "high",
                    "reason": "Strong interest indicators"
                }
            elif total_score >= 40:
                return {
                    "action": "send_personalized_email",
                    "priority": "medium",
                    "reason": "Moderate engagement level"
                }
            elif total_score >= 20:
                return {
                    "action": "nurture_sequence",
                    "priority": "low",
                    "reason": "Low engagement, needs nurturing"
                }
            else:
                return {
                    "action": "re-engage_campaign",
                    "priority": "very_low",
                    "reason": "Very low engagement, needs re-engagement"
                }
                
        except Exception as e:
            logger.error(f"Error determining next action: {e}")
            return {
                "action": "follow_up",
                "priority": "medium",
                "reason": "Default action"
            }
    
    async def _store_prioritization_results(
        self,
        session: AsyncSession,
        prioritized_leads: List[Dict[str, Any]]
    ) -> None:
        """Store prioritization results in the database"""
        try:
            for lead_data in prioritized_leads:
                activity = SalesActivity(
                    activity_type="lead_prioritization",
                    lead_id=lead_data["lead_id"],
                    metadata={
                        "total_score": lead_data["total_score"],
                        "priority_level": lead_data["priority_level"],
                        "intent_score": lead_data["intent_score"],
                        "characteristic_score": lead_data["characteristic_score"],
                        "engagement_score": lead_data["engagement_score"],
                        "urgency_score": lead_data["urgency_score"],
                        "next_action": lead_data["next_action"]
                    }
                )
                
                session.add(activity)
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error storing prioritization results: {e}")
    
    async def _update_lead_activity(
        self,
        session: AsyncSession,
        lead_id: int
    ) -> None:
        """Update lead's last activity timestamp"""
        try:
            query = select(Lead).where(Lead.id == lead_id)
            lead = await session.execute(query)
            lead = lead.scalar_one_or_none()
            
            if lead:
                lead.updated_at = datetime.utcnow()
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error updating lead activity: {e}")
    
    async def _trigger_prioritization_update(self, lead_id: int) -> None:
        """Trigger real-time prioritization update"""
        try:
            await self.kafka_manager.publish_event(
                "lead_prioritization_update",
                {"lead_id": lead_id, "timestamp": datetime.utcnow().isoformat()}
            )
            
        except Exception as e:
            logger.error(f"Error triggering prioritization update: {e}")
    
    async def _get_lead_with_context(
        self,
        session: AsyncSession,
        lead_id: int
    ) -> Optional[Lead]:
        """Get lead with full context"""
        query = select(Lead).where(Lead.id == lead_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_recent_intent_signals(
        self,
        session: AsyncSession,
        lead_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get recent intent signals for a lead"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = select(LeadInteraction).where(
                and_(
                    LeadInteraction.lead_id == lead_id,
                    LeadInteraction.timestamp >= start_date
                )
            ).order_by(desc(LeadInteraction.timestamp))
            
            interactions = await session.execute(query)
            interactions = interactions.scalars().all()
            
            signals = []
            for interaction in interactions:
                signals.append({
                    "type": interaction.interaction_type,
                    "timestamp": interaction.timestamp.isoformat(),
                    "data": interaction.interaction_data,
                    "weight": self.intent_signals.get(interaction.interaction_type, {}).get("weight", 0)
                })
            
            return signals
            
        except Exception as e:
            logger.error(f"Error getting recent intent signals: {e}")
            return []
    
    async def _get_engagement_history(
        self,
        session: AsyncSession,
        lead_id: int,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """Get engagement history for a lead"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = select(LeadInteraction).where(
                and_(
                    LeadInteraction.lead_id == lead_id,
                    LeadInteraction.timestamp >= start_date
                )
            ).order_by(desc(LeadInteraction.timestamp))
            
            interactions = await session.execute(query)
            interactions = interactions.scalars().all()
            
            history = []
            for interaction in interactions:
                history.append({
                    "type": interaction.interaction_type,
                    "timestamp": interaction.timestamp.isoformat(),
                    "data": interaction.interaction_data
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting engagement history: {e}")
            return []
    
    async def _compare_with_similar_leads(
        self,
        session: AsyncSession,
        lead: Lead
    ) -> Dict[str, Any]:
        """Compare lead with similar leads"""
        try:
            # Find similar leads based on industry and company size
            query = select(Lead).where(
                and_(
                    Lead.industry == lead.industry,
                    Lead.company_size == lead.company_size,
                    Lead.id != lead.id
                )
            ).limit(10)
            
            similar_leads = await session.execute(query)
            similar_leads = similar_leads.scalars().all()
            
            if not similar_leads:
                return {"similar_leads_count": 0, "average_score": 0}
            
            # Calculate average scores for similar leads
            total_score = 0
            for similar_lead in similar_leads:
                intent_score = await self._calculate_intent_score(session, similar_lead.id)
                characteristic_score = await self._calculate_characteristic_score(similar_lead)
                engagement_score = await self._calculate_engagement_score(session, similar_lead.id)
                urgency_score = await self._calculate_urgency_score(similar_lead)
                
                similar_total = (
                    intent_score * 0.4 +
                    characteristic_score * 0.3 +
                    engagement_score * 0.2 +
                    urgency_score * 0.1
                )
                total_score += similar_total
            
            average_score = total_score / len(similar_leads)
            
            return {
                "similar_leads_count": len(similar_leads),
                "average_score": round(average_score, 2)
            }
            
        except Exception as e:
            logger.error(f"Error comparing with similar leads: {e}")
            return {"similar_leads_count": 0, "average_score": 0}
    
    async def _generate_priority_recommendations(
        self,
        lead: Lead,
        total_score: float,
        recent_signals: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for improving lead priority"""
        try:
            recommendations = []
            
            if total_score < 40:
                recommendations.append("Increase engagement through targeted outreach")
                recommendations.append("Focus on high-value intent signals (demo requests, pricing page visits)")
                recommendations.append("Consider lead nurturing campaigns")
            
            if not recent_signals:
                recommendations.append("Re-engage the lead with fresh content")
                recommendations.append("Try different communication channels")
            
            if lead.stage == "new":
                recommendations.append("Move lead to contacted stage with personalized outreach")
            
            if lead.budget and lead.budget < 10000:
                recommendations.append("Focus on value proposition and ROI demonstration")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating priority recommendations: {e}")
            return ["Focus on building engagement"]
    
    async def _check_lead_conversion(
        self,
        session: AsyncSession,
        lead_id: int
    ) -> bool:
        """Check if a lead was converted to a deal"""
        try:
            query = select(Deal).where(Deal.lead_id == lead_id)
            deals = await session.execute(query)
            deals = deals.scalars().all()
            
            return len(deals) > 0
            
        except Exception as e:
            logger.error(f"Error checking lead conversion: {e}")
            return False
    
    async def _get_top_intent_signals(
        self,
        session: AsyncSession,
        start_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get top intent signals in the given period"""
        try:
            query = select(
                LeadInteraction.interaction_type,
                func.count(LeadInteraction.id).label("count")
            ).where(
                LeadInteraction.timestamp >= start_date
            ).group_by(
                LeadInteraction.interaction_type
            ).order_by(
                desc(func.count(LeadInteraction.id))
            ).limit(5)
            
            result = await session.execute(query)
            signals = result.all()
            
            return [
                {
                    "signal_type": signal.interaction_type,
                    "count": signal.count,
                    "weight": self.intent_signals.get(signal.interaction_type, {}).get("weight", 0)
                }
                for signal in signals
            ]
            
        except Exception as e:
            logger.error(f"Error getting top intent signals: {e}")
            return []
    
    async def _get_priority_distribution(
        self,
        activities: List[SalesActivity]
    ) -> Dict[str, int]:
        """Get distribution of priority levels"""
        try:
            distribution = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "very_low": 0
            }
            
            for activity in activities:
                metadata = activity.metadata or {}
                priority_level = metadata.get("priority_level", "medium")
                if priority_level in distribution:
                    distribution[priority_level] += 1
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error getting priority distribution: {e}")
            return {}
    
    async def _generate_insight_recommendations(
        self,
        total_prioritizations: int,
        average_scores: List[float],
        conversion_rates: List[float]
    ) -> List[str]:
        """Generate recommendations based on prioritization insights"""
        try:
            recommendations = []
            
            if total_prioritizations < 10:
                recommendations.append("Increase lead prioritization frequency for better insights")
            
            if average_scores and sum(average_scores) / len(average_scores) < 50:
                recommendations.append("Review and adjust intent signal weights")
                recommendations.append("Focus on improving lead qualification criteria")
            
            if conversion_rates and sum(conversion_rates) / len(conversion_rates) < 0.1:
                recommendations.append("Improve lead nurturing processes")
                recommendations.append("Review sales follow-up procedures")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating insight recommendations: {e}")
            return ["Continue monitoring and optimizing prioritization"]
