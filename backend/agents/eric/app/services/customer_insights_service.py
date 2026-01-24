import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from sqlalchemy import select

from core.ai import get_ai_service_manager, AIServiceManager
from core.cache.redis_manager import init_redis
from core.storage.chroma_manager import ChromaManager
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
from ..models import EricLead, EricDeal, EricLeadInteraction, LeadStatus, SalesStage, EricCustomerProfile as CustomerProfile
from ..database import get_eric_database

logger = logging.getLogger(__name__)

class CustomerInsightsService:
    """Service for customer behavior analysis and insights"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.redis_client = None
        self.chroma_manager = None
        self.integration_manager = None
        self.platform_manager = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize customer insights service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            self.redis_client = await init_redis()
            self.chroma_manager = ChromaManager()
            await self.chroma_manager.initialize()
            self.integration_manager = IntegrationManager()
            await self.integration_manager.initialize()
            self.platform_manager = PlatformManager()
            await self.platform_manager.initialize()
            self._initialized = True
            logger.info("Eric customer insights service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize customer insights service: {e}")
            raise
    
    async def analyze_customer_behavior(
        self,
        brand_id: int,
        analysis_period: str = "30d"
    ) -> Dict[str, Any]:
        """Analyze customer behavior patterns"""
        try:
            await self.initialize()
            
            db = next(get_db())
            
            # Calculate date range
            end_date = datetime.now()
            if analysis_period == "7d":
                start_date = end_date - timedelta(days=7)
            elif analysis_period == "30d":
                start_date = end_date - timedelta(days=30)
            elif analysis_period == "90d":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)
            
            # Get customer interactions
            interactions = db.query(EricLeadInteraction).join(EricLead).filter(
                and_(
                    EricLead.brand_id == brand_id,
                    EricLeadInteraction.created_at >= start_date,
                    EricLeadInteraction.created_at <= end_date
                )
            ).all()
            
            # Get leads and deals
            leads = db.query(EricLead).filter(
                and_(
                    EricLead.brand_id == brand_id,
                    EricLead.created_at >= start_date,
                    EricLead.created_at <= end_date
                )
            ).all()
            
            deals = db.query(EricDeal).filter(
                and_(
                    EricDeal.brand_id == brand_id,
                    EricDeal.created_at >= start_date,
                    EricDeal.created_at <= end_date
                )
            ).all()
            
            # Analyze behavior patterns
            behavior_analysis = await self._analyze_behavior_patterns(interactions, leads, deals)
            
            # Generate customer segments
            customer_segments = await self._generate_customer_segments(leads, interactions)
            
            # Analyze engagement patterns
            engagement_analysis = await self._analyze_engagement_patterns(interactions)
            
            # Generate insights
            insights = await self._generate_behavior_insights(behavior_analysis, customer_segments, engagement_analysis)
            
            return {
                "success": True,
                "analysis_period": analysis_period,
                "behavior_analysis": behavior_analysis,
                "customer_segments": customer_segments,
                "engagement_analysis": engagement_analysis,
                "insights": insights,
                "recommendations": await self._generate_optimization_recommendations(behavior_analysis, customer_segments)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze customer behavior: {e}")
            return {
                "success": False,
                "error": f"Failed to analyze customer behavior: {str(e)}"
            }
    
    async def analyze_lead_journey(
        self,
        brand_id: int,
        lead_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Analyze lead journey and touchpoints"""
        try:
            await self.initialize()
            
            db = next(get_db())
            
            if lead_id:
                # Analyze specific lead journey
                lead = db.query(EricLead).filter(EricLead.id == lead_id).first()
                if not lead:
                    return {
                        "success": False,
                        "error": "EricLead not found"
                    }
                
                interactions = db.query(EricLeadInteraction).filter(
                    EricLeadInteraction.lead_id == lead_id
                ).order_by(EricLeadInteraction.created_at).all()
                
                journey_analysis = await self._analyze_single_lead_journey(lead, interactions)
                
                return {
                    "success": True,
                    "lead_id": lead_id,
                    "journey_analysis": journey_analysis
                }
            else:
                # Analyze overall lead journey patterns
                leads = db.query(EricLead).filter(EricLead.brand_id == brand_id).all()
                
                journey_patterns = await self._analyze_journey_patterns(leads, db)
                
                return {
                    "success": True,
                    "journey_patterns": journey_patterns,
                    "total_leads_analyzed": len(leads)
                }
            
        except Exception as e:
            logger.error(f"Failed to analyze lead journey: {e}")
            return {
                "success": False,
                "error": f"Failed to analyze lead journey: {str(e)}"
            }
    
    async def identify_customer_preferences(
        self,
        brand_id: int,
        customer_segment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Identify customer preferences and buying patterns"""
        try:
            await self.initialize()
            
            db = next(get_db())
            
            # Get customer data
            query = db.query(EricLead).filter(EricLead.brand_id == brand_id)
            if customer_segment:
                # Filter by segment (implement segment filtering logic)
                pass
            
            customers = query.all()
            
            # Analyze preferences
            communication_preferences = await self._analyze_communication_preferences(customers, db)
            product_preferences = await self._analyze_product_preferences(customers, db)
            timing_preferences = await self._analyze_timing_preferences(customers, db)
            pricing_preferences = await self._analyze_pricing_preferences(customers, db)
            
            return {
                "success": True,
                "customer_segment": customer_segment,
                "communication_preferences": communication_preferences,
                "product_preferences": product_preferences,
                "timing_preferences": timing_preferences,
                "pricing_preferences": pricing_preferences,
                "total_customers_analyzed": len(customers)
            }
            
        except Exception as e:
            logger.error(f"Failed to identify customer preferences: {e}")
            return {
                "success": False,
                "error": f"Failed to identify customer preferences: {str(e)}"
            }
    
    async def predict_customer_churn(
        self,
        brand_id: int,
        prediction_horizon: str = "30d"
    ) -> Dict[str, Any]:
        """Predict customer churn risk"""
        try:
            await self.initialize()
            
            db = next(get_db())
            
            # Get customer data
            customers = db.query(EricLead).filter(EricLead.brand_id == brand_id).all()
            
            # Calculate churn risk factors
            churn_analysis = await self._calculate_churn_risk(customers, db)
            
            # Generate churn predictions
            churn_predictions = await self._predict_churn_probability(churn_analysis, prediction_horizon)
            
            # Generate retention recommendations
            retention_recommendations = await self._generate_retention_recommendations(churn_analysis)
            
            return {
                "success": True,
                "prediction_horizon": prediction_horizon,
                "churn_analysis": churn_analysis,
                "churn_predictions": churn_predictions,
                "retention_recommendations": retention_recommendations,
                "total_customers_analyzed": len(customers)
            }
            
        except Exception as e:
            logger.error(f"Failed to predict customer churn: {e}")
            return {
                "success": False,
                "error": f"Failed to predict customer churn: {str(e)}"
            }
    
    async def _analyze_behavior_patterns(
        self,
        interactions: List[EricLeadInteraction],
        leads: List[EricLead],
        deals: List[EricDeal]
    ) -> Dict[str, Any]:
        """Analyze customer behavior patterns"""
        try:
            # Interaction frequency analysis
            interaction_frequency = {}
            for interaction in interactions:
                interaction_type = interaction.interaction_type
                if interaction_type not in interaction_frequency:
                    interaction_frequency[interaction_type] = 0
                interaction_frequency[interaction_type] += 1
            
            # Channel preference analysis
            channel_preferences = {}
            for interaction in interactions:
                channel = interaction.channel.value
                if channel not in channel_preferences:
                    channel_preferences[channel] = 0
                channel_preferences[channel] += 1
            
            # Response time analysis
            response_times = []
            for interaction in interactions:
                if interaction.outcome in ["replied", "responded", "engaged"]:
                    # Calculate response time (simplified)
                    response_times.append(1)  # Placeholder
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Conversion pattern analysis
            conversion_patterns = {
                "total_leads": len(leads),
                "qualified_leads": len([l for l in leads if l.lead_status == LeadStatus.QUALIFIED]),
                "converted_leads": len([l for l in leads if l.lead_status in [LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST]]),
                "total_deals": len(deals),
                "won_deals": len([d for d in deals if d.sales_stage == SalesStage.CLOSED and d.win_reason])
            }
            
            return {
                "interaction_frequency": interaction_frequency,
                "channel_preferences": channel_preferences,
                "avg_response_time": avg_response_time,
                "conversion_patterns": conversion_patterns
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze behavior patterns: {e}")
            return {
                "interaction_frequency": {},
                "channel_preferences": {},
                "avg_response_time": 0,
                "conversion_patterns": {
                    "total_leads": 0,
                    "qualified_leads": 0,
                    "converted_leads": 0,
                    "total_deals": 0,
                    "won_deals": 0
                }
            }
    
    async def _generate_customer_segments(
        self,
        leads: List[EricLead],
        interactions: List[EricLeadInteraction]
    ) -> Dict[str, Any]:
        """Generate customer segments based on behavior"""
        try:
            segments = {
                "high_value": [],
                "engaged": [],
                "at_risk": [],
                "new": [],
                "inactive": []
            }
            
            for lead in leads:
                lead_interactions = [i for i in interactions if i.lead_id == lead.id]
                interaction_count = len(lead_interactions)
                
                # Segment based on behavior
                if lead.lead_score >= 0.8:
                    segments["high_value"].append({
                        "lead_id": lead.id,
                        "name": f"{lead.first_name} {lead.last_name}",
                        "company": lead.company,
                        "lead_score": lead.lead_score,
                        "interaction_count": interaction_count
                    })
                elif interaction_count >= 5:
                    segments["engaged"].append({
                        "lead_id": lead.id,
                        "name": f"{lead.first_name} {lead.last_name}",
                        "company": lead.company,
                        "interaction_count": interaction_count
                    })
                elif lead.lead_score < 0.3 and interaction_count < 2:
                    segments["at_risk"].append({
                        "lead_id": lead.id,
                        "name": f"{lead.first_name} {lead.last_name}",
                        "company": lead.company,
                        "lead_score": lead.lead_score
                    })
                elif (datetime.now() - lead.created_at).days <= 7:
                    segments["new"].append({
                        "lead_id": lead.id,
                        "name": f"{lead.first_name} {lead.last_name}",
                        "company": lead.company,
                        "created_at": lead.created_at.isoformat()
                    })
                elif (datetime.now() - lead.updated_at).days > 30:
                    segments["inactive"].append({
                        "lead_id": lead.id,
                        "name": f"{lead.first_name} {lead.last_name}",
                        "company": lead.company,
                        "last_activity": lead.updated_at.isoformat()
                    })
            
            return segments
            
        except Exception as e:
            logger.error(f"Failed to generate customer segments: {e}")
            return {
                "high_value": [],
                "engaged": [],
                "at_risk": [],
                "new": [],
                "inactive": []
            }
    
    async def _analyze_engagement_patterns(
        self,
        interactions: List[EricLeadInteraction]
    ) -> Dict[str, Any]:
        """Analyze customer engagement patterns"""
        try:
            # Time-based engagement analysis
            hourly_engagement = {}
            daily_engagement = {}
            
            for interaction in interactions:
                hour = interaction.created_at.hour
                day = interaction.created_at.strftime("%A")
                
                if hour not in hourly_engagement:
                    hourly_engagement[hour] = 0
                hourly_engagement[hour] += 1
                
                if day not in daily_engagement:
                    daily_engagement[day] = 0
                daily_engagement[day] += 1
            
            # Engagement type analysis
            engagement_types = {}
            for interaction in interactions:
                outcome = interaction.outcome
                if outcome not in engagement_types:
                    engagement_types[outcome] = 0
                engagement_types[outcome] += 1
            
            # Sentiment analysis
            positive_interactions = len([i for i in interactions if i.sentiment_score and i.sentiment_score > 0.6])
            negative_interactions = len([i for i in interactions if i.sentiment_score and i.sentiment_score < 0.4])
            neutral_interactions = len(interactions) - positive_interactions - negative_interactions
            
            return {
                "hourly_engagement": hourly_engagement,
                "daily_engagement": daily_engagement,
                "engagement_types": engagement_types,
                "sentiment_analysis": {
                    "positive": positive_interactions,
                    "negative": negative_interactions,
                    "neutral": neutral_interactions
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze engagement patterns: {e}")
            return {
                "hourly_engagement": {},
                "daily_engagement": {},
                "engagement_types": {},
                "sentiment_analysis": {
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0
                }
            }
    
    async def _analyze_single_lead_journey(
        self,
        lead: EricLead,
        interactions: List[EricLeadInteraction]
    ) -> Dict[str, Any]:
        """Analyze journey for a single lead"""
        try:
            journey_stages = []
            touchpoints = []
            
            # Create journey timeline
            for interaction in interactions:
                touchpoints.append({
                    "timestamp": interaction.created_at.isoformat(),
                    "type": interaction.interaction_type,
                    "channel": interaction.channel.value,
                    "outcome": interaction.outcome,
                    "sentiment_score": interaction.sentiment_score,
                    "content": interaction.content[:100] + "..." if len(interaction.content) > 100 else interaction.content
                })
            
            # Analyze journey progression
            if interactions:
                first_interaction = min(interactions, key=lambda x: x.created_at)
                last_interaction = max(interactions, key=lambda x: x.created_at)
                
                journey_duration = (last_interaction.created_at - first_interaction.created_at).days
                total_touchpoints = len(interactions)
                
                # Determine journey stage
                if lead.lead_status == LeadStatus.CLOSED_WON:
                    journey_stage = "converted"
                elif lead.lead_status == LeadStatus.QUALIFIED:
                    journey_stage = "qualified"
                elif lead.lead_status == LeadStatus.CONTACTED:
                    journey_stage = "contacted"
                else:
                    journey_stage = "new"
            else:
                journey_duration = 0
                total_touchpoints = 0
                journey_stage = "new"
            
            return {
                "lead_info": {
                    "id": lead.id,
                    "name": f"{lead.first_name} {lead.last_name}",
                    "company": lead.company,
                    "lead_score": lead.lead_score,
                    "lead_status": lead.lead_status.value
                },
                "journey_metrics": {
                    "duration_days": journey_duration,
                    "total_touchpoints": total_touchpoints,
                    "journey_stage": journey_stage
                },
                "touchpoints": touchpoints,
                "journey_insights": await self._generate_journey_insights(interactions, lead)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze single lead journey: {e}")
            return {
                "lead_info": {
                    "id": "unknown",
                    "name": "Unknown",
                    "company": "Unknown",
                    "lead_score": 0,
                    "lead_status": "unknown"
                },
                "journey_metrics": {
                    "duration_days": 0,
                    "total_touchpoints": 0,
                    "journey_stage": "unknown"
                },
                "touchpoints": [],
                "journey_insights": ["Unable to analyze journey"]
            }
    
    async def _analyze_journey_patterns(
        self,
        leads: List[EricLead],
        db: Session
    ) -> Dict[str, Any]:
        """Analyze overall journey patterns"""
        try:
            journey_patterns = {
                "avg_journey_duration": 0,
                "avg_touchpoints": 0,
                "conversion_by_stage": {},
                "bottlenecks": []
            }
            
            total_duration = 0
            total_touchpoints = 0
            converted_leads = 0
            
            for lead in leads:
                interactions = db.query(EricLeadInteraction).filter(
                    EricLeadInteraction.lead_id == lead.id
                ).all()
                
                if interactions:
                    first_interaction = min(interactions, key=lambda x: x.created_at)
                    last_interaction = max(interactions, key=lambda x: x.created_at)
                    
                    duration = (last_interaction.created_at - first_interaction.created_at).days
                    total_duration += duration
                    total_touchpoints += len(interactions)
                    
                    if lead.lead_status in [LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST]:
                        converted_leads += 1
            
            if converted_leads > 0:
                journey_patterns["avg_journey_duration"] = total_duration / converted_leads
                journey_patterns["avg_touchpoints"] = total_touchpoints / converted_leads
            
            return journey_patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze journey patterns: {e}")
            return {
                "avg_journey_duration": 0,
                "avg_touchpoints": 0,
                "conversion_by_stage": {},
                "bottlenecks": ["Unable to analyze journey patterns"]
            }
    
    async def _analyze_communication_preferences(
        self,
        customers: List[EricLead],
        db: Session
    ) -> Dict[str, Any]:
        """Analyze communication channel preferences"""
        try:
            channel_preferences = {}
            response_rates = {}
            
            for customer in customers:
                interactions = db.query(EricLeadInteraction).filter(
                    EricLeadInteraction.lead_id == customer.id
                ).all()
                
                for interaction in interactions:
                    channel = interaction.channel.value
                    
                    if channel not in channel_preferences:
                        channel_preferences[channel] = {"total": 0, "responses": 0}
                    
                    channel_preferences[channel]["total"] += 1
                    
                    if interaction.outcome in ["replied", "responded", "engaged"]:
                        channel_preferences[channel]["responses"] += 1
            
            # Calculate response rates
            for channel, data in channel_preferences.items():
                if data["total"] > 0:
                    response_rate = (data["responses"] / data["total"]) * 100
                    response_rates[channel] = round(response_rate, 2)
            
            return {
                "channel_preferences": channel_preferences,
                "response_rates": response_rates,
                "preferred_channels": sorted(response_rates.items(), key=lambda x: x[1], reverse=True)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze communication preferences: {e}")
            return {
                "channel_preferences": {},
                "response_rates": {},
                "preferred_channels": []
            }
    
    async def _analyze_product_preferences(
        self,
        customers: List[EricLead],
        db: Session
    ) -> Dict[str, Any]:
        """Analyze product and service preferences from customer data"""
        try:
            preferred_products = {}
            feature_interest = {}
            pricing_tier_preferences = {}
            
            # Query deals and interactions for product preferences
            for customer in customers:
                # Get deals for this customer
                deals = db.query(EricDeal).filter(EricDeal.customer_id == customer.id).all()
                
                for deal in deals:
                    if deal.product_id:
                        product_name = deal.product_id  # Assuming product_id contains product name
                        if product_name not in preferred_products:
                            preferred_products[product_name] = 0
                        preferred_products[product_name] += 1
                    
                    # Analyze pricing tier preferences
                    if deal.value:
                        if deal.value > 10000:
                            tier = "enterprise"
                        elif deal.value > 5000:
                            tier = "professional"
                        else:
                            tier = "basic"
                        
                        if tier not in pricing_tier_preferences:
                            pricing_tier_preferences[tier] = 0
                        pricing_tier_preferences[tier] += 1
                
                # Get interactions for feature interest
                interactions = db.query(EricLeadInteraction).filter(
                    EricLeadInteraction.lead_id == customer.id
                ).all()
                
                for interaction in interactions:
                    if interaction.interaction_type in ["demo_request", "feature_inquiry"]:
                        feature = interaction.interaction_type
                        if feature not in feature_interest:
                            feature_interest[feature] = 0
                        feature_interest[feature] += 1
            
            return {
                "preferred_products": preferred_products,
                "feature_interest": feature_interest,
                "pricing_tier_preferences": pricing_tier_preferences
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze product preferences: {e}")
            return {
                "preferred_products": {},
                "feature_interest": {},
                "pricing_tier_preferences": {}
            }
    
    async def _analyze_timing_preferences(
        self,
        customers: List[EricLead],
        db: Session
    ) -> Dict[str, Any]:
        """Analyze timing preferences for interactions"""
        try:
            hourly_preferences = {}
            daily_preferences = {}
            
            for customer in customers:
                interactions = db.query(EricLeadInteraction).filter(
                    EricLeadInteraction.lead_id == customer.id
                ).all()
                
                for interaction in interactions:
                    hour = interaction.created_at.hour
                    day = interaction.created_at.strftime("%A")
                    
                    if hour not in hourly_preferences:
                        hourly_preferences[hour] = 0
                    hourly_preferences[hour] += 1
                    
                    if day not in daily_preferences:
                        daily_preferences[day] = 0
                    daily_preferences[day] += 1
            
            return {
                "hourly_preferences": hourly_preferences,
                "daily_preferences": daily_preferences,
                "peak_hours": sorted(hourly_preferences.items(), key=lambda x: x[1], reverse=True)[:3],
                "peak_days": sorted(daily_preferences.items(), key=lambda x: x[1], reverse=True)[:3]
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze timing preferences: {e}")
            return {
                "hourly_preferences": {},
                "daily_preferences": {},
                "peak_hours": [],
                "peak_days": []
            }
    
    async def _analyze_pricing_preferences(
        self,
        customers: List[EricLead],
        db: Session
    ) -> Dict[str, Any]:
        """Analyze pricing preferences and sensitivity from customer data"""
        try:
            price_sensitivity = "medium"
            preferred_pricing_models = []
            budget_ranges = {}
            
            # Analyze deals for pricing preferences
            total_deals = 0
            price_negotiations = 0
            
            for customer in customers:
                deals = db.query(EricDeal).filter(EricDeal.customer_id == customer.id).all()
                
                for deal in deals:
                    total_deals += 1
                    
                    # Check for price negotiations (simplified)
                    if deal.metadata and deal.metadata.get("price_negotiated"):
                        price_negotiations += 1
                    
                    # Analyze budget ranges
                    if deal.value:
                        if deal.value <= 2000:
                            budget_range = "low"
                        elif deal.value <= 10000:
                            budget_range = "medium"
                        else:
                            budget_range = "high"
                        
                        if budget_range not in budget_ranges:
                            budget_ranges[budget_range] = 0
                        budget_ranges[budget_range] += 1
            
            # Determine price sensitivity
            if total_deals > 0:
                negotiation_rate = price_negotiations / total_deals
                if negotiation_rate > 0.7:
                    price_sensitivity = "high"
                elif negotiation_rate < 0.3:
                    price_sensitivity = "low"
                else:
                    price_sensitivity = "medium"
            
            # Determine preferred pricing models based on deal patterns
            if budget_ranges.get("high", 0) > budget_ranges.get("low", 0):
                preferred_pricing_models.append("enterprise")
            if budget_ranges.get("medium", 0) > 0:
                preferred_pricing_models.append("subscription")
            if budget_ranges.get("low", 0) > 0:
                preferred_pricing_models.append("pay_per_use")
            
            return {
                "price_sensitivity": price_sensitivity,
                "preferred_pricing_models": preferred_pricing_models,
                "budget_ranges": budget_ranges
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze pricing preferences: {e}")
            return {
                "price_sensitivity": "unknown",
                "preferred_pricing_models": [],
                "budget_ranges": {}
            }
    
    async def _calculate_churn_risk(
        self,
        customers: List[EricLead],
        db: Session
    ) -> Dict[str, Any]:
        """Calculate churn risk for customers"""
        try:
            churn_analysis = {
                "high_risk": [],
                "medium_risk": [],
                "low_risk": []
            }
            
            for customer in customers:
                interactions = db.query(EricLeadInteraction).filter(
                    EricLeadInteraction.lead_id == customer.id
                ).all()
                
                # Calculate churn risk factors
                last_interaction_days = 0
                if interactions:
                    last_interaction = max(interactions, key=lambda x: x.created_at)
                    last_interaction_days = (datetime.now() - last_interaction.created_at).days
                
                interaction_count = len(interactions)
                lead_score = customer.lead_score or 0
                
                # Determine risk level
                if last_interaction_days > 30 and interaction_count < 3:
                    churn_analysis["high_risk"].append({
                        "lead_id": customer.id,
                        "name": f"{customer.first_name} {customer.last_name}",
                        "company": customer.company,
                        "risk_factors": ["inactive", "low_engagement"]
                    })
                elif last_interaction_days > 15 or lead_score < 0.4:
                    churn_analysis["medium_risk"].append({
                        "lead_id": customer.id,
                        "name": f"{customer.first_name} {customer.last_name}",
                        "company": customer.company,
                        "risk_factors": ["recent_inactivity", "low_score"]
                    })
                else:
                    churn_analysis["low_risk"].append({
                        "lead_id": customer.id,
                        "name": f"{customer.first_name} {customer.last_name}",
                        "company": customer.company,
                        "risk_factors": ["engaged", "high_score"]
                    })
            
            return churn_analysis
            
        except Exception as e:
            logger.error(f"Failed to calculate churn risk: {e}")
            return {
                "high_risk": [],
                "medium_risk": [],
                "low_risk": []
            }
    
    async def _predict_churn_probability(
        self,
        churn_analysis: Dict[str, Any],
        prediction_horizon: str
    ) -> Dict[str, Any]:
        """Predict churn probability"""
        try:
            total_customers = sum(len(customers) for customers in churn_analysis.values())
            
            if total_customers == 0:
                return {
                    "overall_churn_rate": 0,
                    "predicted_churn": 0,
                    "confidence": 0.5
                }
            
            high_risk_count = len(churn_analysis.get("high_risk", []))
            medium_risk_count = len(churn_analysis.get("medium_risk", []))
            
            # Calculate churn probability
            high_risk_churn_prob = 0.8  # 80% chance of churn
            medium_risk_churn_prob = 0.4  # 40% chance of churn
            
            predicted_churn = (high_risk_count * high_risk_churn_prob) + (medium_risk_count * medium_risk_churn_prob)
            overall_churn_rate = (predicted_churn / total_customers) * 100
            
            return {
                "overall_churn_rate": round(overall_churn_rate, 2),
                "predicted_churn": round(predicted_churn, 0),
                "confidence": 0.7,
                "prediction_horizon": prediction_horizon
            }
            
        except Exception as e:
            logger.error(f"Failed to predict churn probability: {e}")
            return {
                "overall_churn_rate": 0,
                "predicted_churn": 0,
                "confidence": 0.5,
                "prediction_horizon": "unknown"
            }
    
    async def _generate_behavior_insights(
        self,
        behavior_analysis: Dict[str, Any],
        customer_segments: Dict[str, Any],
        engagement_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from behavior analysis"""
        try:
            insights = []
            
            # High-value customer insights
            high_value_count = len(customer_segments.get("high_value", []))
            if high_value_count > 0:
                insights.append(f"Found {high_value_count} high-value customers - prioritize personalized outreach")
            
            # Engagement insights
            if engagement_analysis.get("sentiment_analysis"):
                positive_count = engagement_analysis["sentiment_analysis"]["positive"]
                negative_count = engagement_analysis["sentiment_analysis"]["negative"]
                
                if positive_count > negative_count * 2:
                    insights.append("Strong positive sentiment - current strategies are effective")
                elif negative_count > positive_count:
                    insights.append("Negative sentiment detected - review communication approach")
            
            # Channel insights
            if behavior_analysis.get("channel_preferences"):
                top_channel = max(behavior_analysis["channel_preferences"].items(), key=lambda x: x[1])
                insights.append(f"Most preferred channel: {top_channel[0]} ({top_channel[1]} interactions)")
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate behavior insights: {e}")
            return ["Unable to generate insights"]
    
    async def _generate_journey_insights(
        self,
        interactions: List[EricLeadInteraction],
        lead: EricLead
    ) -> List[str]:
        """Generate insights for a single lead journey"""
        try:
            insights = []
            
            if not interactions:
                insights.append("No interactions recorded - initiate first contact")
                return insights
            
            # Interaction frequency
            if len(interactions) < 3:
                insights.append("Low interaction count - increase engagement frequency")
            elif len(interactions) > 10:
                insights.append("High interaction count - consider moving to next stage")
            
            # Recent activity
            last_interaction = max(interactions, key=lambda x: x.created_at)
            days_since_last = (datetime.now() - last_interaction.created_at).days
            
            if days_since_last > 7:
                insights.append(f"No activity for {days_since_last} days - re-engage")
            
            # EricLead score insights
            if lead.lead_score and lead.lead_score < 0.4:
                insights.append("Low lead score - focus on qualification")
            elif lead.lead_score and lead.lead_score > 0.8:
                insights.append("High lead score - ready for closing")
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate journey insights: {e}")
            return ["Unable to generate journey insights"]
    
    async def _generate_optimization_recommendations(
        self,
        behavior_analysis: Dict[str, Any],
        customer_segments: Dict[str, Any]
    ) -> List[str]:
        """Generate optimization recommendations"""
        try:
            recommendations = []
            
            # Segment-based recommendations
            at_risk_count = len(customer_segments.get("at_risk", []))
            if at_risk_count > 0:
                recommendations.append(f"Focus on {at_risk_count} at-risk customers with re-engagement campaigns")
            
            high_value_count = len(customer_segments.get("high_value", []))
            if high_value_count > 0:
                recommendations.append(f"Develop VIP program for {high_value_count} high-value customers")
            
            # Channel optimization
            if behavior_analysis.get("channel_preferences"):
                least_used_channel = min(behavior_analysis["channel_preferences"].items(), key=lambda x: x[1])
                recommendations.append(f"Explore {least_used_channel[0]} channel for new opportunities")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate optimization recommendations: {e}")
            return ["Unable to generate recommendations"]
    
    async def _generate_retention_recommendations(
        self,
        churn_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate customer retention recommendations"""
        try:
            recommendations = []
            
            high_risk_count = len(churn_analysis.get("high_risk", []))
            medium_risk_count = len(churn_analysis.get("medium_risk", []))
            
            if high_risk_count > 0:
                recommendations.append(f"Implement urgent re-engagement campaign for {high_risk_count} high-risk customers")
            
            if medium_risk_count > 0:
                recommendations.append(f"Develop personalized retention strategies for {medium_risk_count} medium-risk customers")
            
            if high_risk_count + medium_risk_count > 10:
                recommendations.append("Consider implementing automated retention workflows")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate retention recommendations: {e}")
            return ["Unable to generate retention recommendations"]