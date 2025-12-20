import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from pydantic import BaseModel

from ..database import get_eric_database
from ..models import (
    DealClosing, DealClosingStage, DealClosingStrategy,
    DealClosingTemplate, DealClosingActivity
)
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager
from ..models import CustomerProfile
from ..models import Deal, SalesStage

logger = logging.getLogger(__name__)

class DealClosingRequest(BaseModel):
    deal_id: str
    brand_id: str
    customer_id: str
    deal_value: float
    deal_stage: str
    customer_concerns: Optional[List[str]] = []
    preferred_closing_method: Optional[str] = "email"
    urgency_level: Optional[str] = "medium"

class DealClosingStrategyRequest(BaseModel):
    deal_id: str
    brand_id: str
    strategy_type: str
    customer_profile: Dict[str, Any]
    deal_context: Dict[str, Any]

class DealClosingTemplateRequest(BaseModel):
    brand_id: str
    template_name: str
    template_type: str
    content: Dict[str, Any]
    conditions: Optional[Dict[str, Any]] = {}

class DealClosingActivityRequest(BaseModel):
    deal_id: str
    brand_id: str
    activity_type: str
    activity_data: Dict[str, Any]
    scheduled_time: Optional[datetime] = None

class DealClosingAssistanceService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self.kafka_manager = KafkaManager()
        self.redis_manager = RedisManager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize deal closing assistance service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            await self.kafka_manager.initialize()
            await self.redis_manager.initialize()
            self._initialized = True
            logger.info("Deal closing assistance service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize deal closing assistance service: {e}")
            raise

    async def analyze_deal_for_closing(self, deal_id: str, brand_id: str) -> Dict[str, Any]:
        """Analyze a deal to determine optimal closing strategy"""
        try:
            async with get_eric_database() as db:
                # Get deal information
                deal_query = select(DealClosing).where(
                    and_(DealClosing.deal_id == deal_id, DealClosing.brand_id == brand_id)
                )
                deal_result = await db.execute(deal_query)
                deal = deal_result.scalar_one_or_none()
                
                if not deal:
                    raise ValueError(f"Deal {deal_id} not found")
                
                # Analyze customer behavior and preferences
                customer_analysis = await self._analyze_customer_behavior(deal.customer_id, brand_id)
                
                # Determine optimal closing approach
                closing_approach = await self._determine_closing_approach(deal, customer_analysis)
                
                # Generate personalized closing strategy
                strategy = await self._generate_closing_strategy(deal, closing_approach)
                
                # Create closing timeline
                timeline = await self._create_closing_timeline(deal, strategy)
                
                return {
                    "deal_id": deal_id,
                    "analysis": {
                        "customer_profile": customer_analysis,
                        "closing_approach": closing_approach,
                        "risk_factors": await self._identify_risk_factors(deal),
                        "opportunity_signals": await self._identify_opportunity_signals(deal)
                    },
                    "strategy": strategy,
                    "timeline": timeline,
                    "recommended_actions": await self._get_recommended_actions(deal, strategy)
                }
                
        except Exception as e:
            logger.error(f"Error analyzing deal for closing: {e}")
            raise

    async def generate_closing_proposal(self, deal_id: str, brand_id: str, 
                                      proposal_type: str = "standard") -> Dict[str, Any]:
        """Generate a personalized closing proposal"""
        try:
            async with get_eric_database() as db:
                # Get deal details
                deal_query = select(DealClosing).where(
                    and_(DealClosing.deal_id == deal_id, DealClosing.brand_id == brand_id)
                )
                deal_result = await db.execute(deal_query)
                deal = deal_result.scalar_one_or_none()
                
                if not deal:
                    raise ValueError(f"Deal {deal_id} not found")
                
                # Get customer profile
                customer_profile = await self._get_customer_profile(deal.customer_id, brand_id)
                
                # Generate proposal content using AI
                proposal_content = await self._generate_proposal_content(
                    deal, customer_profile, proposal_type
                )
                
                # Create proposal structure
                proposal = {
                    "deal_id": deal_id,
                    "proposal_type": proposal_type,
                    "generated_at": datetime.utcnow(),
                    "valid_until": datetime.utcnow() + timedelta(days=30),
                    "content": proposal_content,
                    "pricing": await self._generate_pricing_options(deal),
                    "terms": await self._generate_terms_and_conditions(deal),
                    "next_steps": await self._generate_next_steps(deal)
                }
                
                # Save proposal to database
                await self._save_proposal(deal_id, brand_id, proposal)
                
                return proposal
                
        except Exception as e:
            logger.error(f"Error generating closing proposal: {e}")
            raise

    async def create_closing_sequence(self, deal_id: str, brand_id: str, 
                                    sequence_type: str = "standard") -> Dict[str, Any]:
        """Create an automated closing sequence"""
        try:
            async with get_eric_database() as db:
                # Get deal information
                deal_query = select(DealClosing).where(
                    and_(DealClosing.deal_id == deal_id, DealClosing.brand_id == brand_id)
                )
                deal_result = await db.execute(deal_query)
                deal = deal_result.scalar_one_or_none()
                
                if not deal:
                    raise ValueError(f"Deal {deal_id} not found")
                
                # Create sequence steps
                sequence_steps = await self._create_sequence_steps(deal, sequence_type)
                
                # Schedule sequence activities
                scheduled_activities = await self._schedule_sequence_activities(
                    deal_id, brand_id, sequence_steps
                )
                
                # Create sequence tracking
                sequence = {
                    "deal_id": deal_id,
                    "sequence_type": sequence_type,
                    "created_at": datetime.utcnow(),
                    "status": "active",
                    "steps": sequence_steps,
                    "scheduled_activities": scheduled_activities,
                    "expected_completion": await self._calculate_expected_completion(sequence_steps)
                }
                
                # Save sequence to database
                await self._save_closing_sequence(deal_id, brand_id, sequence)
                
                return sequence
                
        except Exception as e:
            logger.error(f"Error creating closing sequence: {e}")
            raise

    async def handle_objections_and_concerns(self, deal_id: str, brand_id: str, 
                                           objection_type: str, objection_details: str) -> Dict[str, Any]:
        """Handle customer objections and concerns during closing"""
        try:
            async with get_eric_database() as db:
                # Get deal information
                deal_query = select(DealClosing).where(
                    and_(DealClosing.deal_id == deal_id, DealClosing.brand_id == brand_id)
                )
                deal_result = await db.execute(deal_query)
                deal = deal_result.scalar_one_or_none()
                
                if not deal:
                    raise ValueError(f"Deal {deal_id} not found")
                
                # Use AI Service Manager for sentiment and intent analysis
                ai_manager = await get_ai_service_manager()
                prompt = f"Analyze the sentiment and intent of this objection: {objection_details}. Respond with JSON: {{\"sentiment\": \"positive/negative/neutral\", \"sentiment_score\": 0.0-1.0, \"intent\": \"...\", \"intent_confidence\": 0.0-1.0}}"
                messages = [{"role": "system", "content": "You are an AI assistant that analyzes objections for sentiment and intent. Respond in JSON format."}, {"role": "user", "content": prompt}]
                analysis_response = await ai_manager.generate_text(messages=messages, max_tokens=300, temperature=0.3)
                try:
                    import json
                    objection_analysis = json.loads(analysis_response.text_content) if analysis_response.success else {"sentiment": "neutral", "sentiment_score": 0.5, "intent": "general", "intent_confidence": 0.5}
                except:
                    objection_analysis = {"sentiment": "neutral", "sentiment_score": 0.5, "intent": "general", "intent_confidence": 0.5}
                
                # Generate response strategy
                response_strategy = await self._generate_objection_response_strategy(
                    objection_type, objection_analysis, deal
                )
                
                # Create personalized response
                response = await self._create_objection_response(
                    objection_details, response_strategy, deal
                )
                
                # Update deal status
                await self._update_deal_objection_status(deal_id, brand_id, objection_type, response_strategy)
                
                return {
                    "deal_id": deal_id,
                    "objection_type": objection_type,
                    "objection_analysis": objection_analysis,
                    "response_strategy": response_strategy,
                    "response": response,
                    "next_actions": await self._get_objection_follow_up_actions(deal, objection_type)
                }
                
        except Exception as e:
            logger.error(f"Error handling objections: {e}")
            raise

    async def execute_closing_activities(self, deal_id: str, brand_id: str, 
                                       activity_type: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific closing activities"""
        try:
            async with get_eric_database() as db:
                # Validate activity
                if not await self._validate_closing_activity(activity_type, activity_data):
                    raise ValueError(f"Invalid closing activity: {activity_type}")
                
                # Execute activity based on type
                if activity_type == "send_proposal":
                    result = await self._send_closing_proposal(deal_id, brand_id, activity_data)
                elif activity_type == "schedule_demo":
                    result = await self._schedule_closing_demo(deal_id, brand_id, activity_data)
                elif activity_type == "send_contract":
                    result = await self._send_closing_contract(deal_id, brand_id, activity_data)
                elif activity_type == "follow_up_call":
                    result = await self._execute_follow_up_call(deal_id, brand_id, activity_data)
                elif activity_type == "negotiate_terms":
                    result = await self._negotiate_closing_terms(deal_id, brand_id, activity_data)
                else:
                    raise ValueError(f"Unsupported activity type: {activity_type}")
                
                # Log activity
                await self._log_closing_activity(deal_id, brand_id, activity_type, activity_data, result)
                
                # Update deal progress
                await self._update_deal_progress(deal_id, brand_id, activity_type, result)
                
                return {
                    "deal_id": deal_id,
                    "activity_type": activity_type,
                    "execution_result": result,
                    "timestamp": datetime.utcnow(),
                    "next_recommended_action": await self._get_next_recommended_action(deal_id, brand_id)
                }
                
        except Exception as e:
            logger.error(f"Error executing closing activity: {e}")
            raise

    async def track_closing_progress(self, deal_id: str, brand_id: str) -> Dict[str, Any]:
        """Track the progress of deal closing activities"""
        try:
            async with get_eric_database() as db:
                # Get deal information
                deal_query = select(DealClosing).where(
                    and_(DealClosing.deal_id == deal_id, DealClosing.brand_id == brand_id)
                )
                deal_result = await db.execute(deal_query)
                deal = deal_result.scalar_one_or_none()
                
                if not deal:
                    raise ValueError(f"Deal {deal_id} not found")
                
                # Get all activities for this deal
                activities_query = select(DealClosingActivity).where(
                    and_(DealClosingActivity.deal_id == deal_id, DealClosingActivity.brand_id == brand_id)
                ).order_by(DealClosingActivity.created_at)
                
                activities_result = await db.execute(activities_query)
                activities = activities_result.scalars().all()
                
                # Calculate progress metrics
                progress_metrics = await self._calculate_closing_progress(deal, activities)
                
                # Get current stage information
                current_stage = await self._get_current_closing_stage(deal, activities)
                
                # Generate progress report
                progress_report = {
                    "deal_id": deal_id,
                    "current_stage": current_stage,
                    "progress_percentage": progress_metrics["overall_progress"],
                    "time_elapsed": progress_metrics["time_elapsed"],
                    "time_remaining": progress_metrics["time_remaining"],
                    "activities_completed": progress_metrics["activities_completed"],
                    "activities_pending": progress_metrics["activities_pending"],
                    "milestones": progress_metrics["milestones"],
                    "bottlenecks": await self._identify_closing_bottlenecks(deal, activities),
                    "recommendations": await self._get_progress_recommendations(deal, progress_metrics)
                }
                
                return progress_report
                
        except Exception as e:
            logger.error(f"Error tracking closing progress: {e}")
            raise

    async def finalize_deal(self, deal_id: str, brand_id: str, 
                           closing_method: str, closing_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize a deal with specified closing method and terms"""
        try:
            async with get_eric_database() as db:
                # Get deal information
                deal_query = select(DealClosing).where(
                    and_(DealClosing.deal_id == deal_id, DealClosing.brand_id == brand_id)
                )
                deal_result = await db.execute(deal_query)
                deal = deal_result.scalar_one_or_none()
                
                if not deal:
                    raise ValueError(f"Deal {deal_id} not found")
                
                # Validate closing terms
                if not await self._validate_closing_terms(closing_terms):
                    raise ValueError("Invalid closing terms")
                
                # Execute closing based on method
                if closing_method == "contract_signature":
                    closing_result = await self._execute_contract_closing(deal, closing_terms)
                elif closing_method == "payment_processing":
                    closing_result = await self._execute_payment_closing(deal, closing_terms)
                elif closing_method == "handshake_agreement":
                    closing_result = await self._execute_handshake_closing(deal, closing_terms)
                else:
                    raise ValueError(f"Unsupported closing method: {closing_method}")
                
                # Update deal status
                await self._update_deal_to_closed(deal_id, brand_id, closing_method, closing_result)
                
                # Trigger post-closing activities
                await self._trigger_post_closing_activities(deal_id, brand_id, closing_result)
                
                # Send notifications
                await self._send_closing_notifications(deal_id, brand_id, closing_result)
                
                return {
                    "deal_id": deal_id,
                    "closing_method": closing_method,
                    "closing_status": "completed",
                    "closing_result": closing_result,
                    "closed_at": datetime.utcnow(),
                    "post_closing_activities": await self._get_post_closing_activities(deal_id, brand_id)
                }
                
        except Exception as e:
            logger.error(f"Error finalizing deal: {e}")
            raise

    # Helper methods
    async def _analyze_customer_behavior(self, customer_id: str, brand_id: str) -> Dict[str, Any]:
        """Analyze customer behavior for closing strategy"""
        try:
            async with get_eric_database() as db:
                # Get customer's interaction history
                interactions = await db.execute(
                    select(SalesActivity).where(
                        and_(
                            SalesActivity.customer_id == customer_id,
                            SalesActivity.brand_id == brand_id,
                            SalesActivity.created_at >= datetime.utcnow() - timedelta(days=90)
                        )
                    )
                )
                activity_list = interactions.scalars().all()
                
                # Get customer's deal history
                deals = await db.execute(
                    select(Deal).where(
                        and_(
                            Deal.customer_id == customer_id,
                            Deal.brand_id == brand_id
                        )
                    )
                )
                deal_list = deals.scalars().all()
                
                # Analyze communication preferences
                email_count = sum(1 for activity in activity_list if activity.activity_type == "email_sent")
                call_count = sum(1 for activity in activity_list if activity.activity_type == "call_made")
                meeting_count = sum(1 for activity in activity_list if activity.activity_type == "meeting_scheduled")
                
                total_interactions = len(activity_list)
                if total_interactions > 0:
                    communication_preference = "email" if email_count > call_count else "phone" if call_count > meeting_count else "meeting"
                else:
                    communication_preference = "email"  # Default
                
                # Analyze decision making style based on deal history
                avg_deal_cycle = 0
                if len(deal_list) > 1:
                    deal_dates = sorted([deal.created_at for deal in deal_list])
                    cycle_times = [(deal_dates[i+1] - deal_dates[i]).days for i in range(len(deal_dates)-1)]
                    avg_deal_cycle = sum(cycle_times) / len(cycle_times)
                
                decision_making_style = "analytical" if avg_deal_cycle > 30 else "quick" if avg_deal_cycle < 7 else "balanced"
                
                # Determine urgency level based on recent activity
                recent_activities = [a for a in activity_list if a.created_at >= datetime.utcnow() - timedelta(days=7)]
                urgency_level = "high" if len(recent_activities) > 5 else "medium" if len(recent_activities) > 2 else "low"
                
                # Analyze price sensitivity from deal values
                if deal_list:
                    avg_deal_value = sum(deal.value for deal in deal_list) / len(deal_list)
                    price_sensitivity = "low" if avg_deal_value > 100000 else "moderate" if avg_deal_value > 25000 else "high"
                else:
                    price_sensitivity = "moderate"
                
                # Determine risk tolerance based on engagement patterns
                risk_tolerance = "low" if len(activity_list) < 5 else "moderate" if len(activity_list) < 15 else "high"
                
                return {
                    "communication_preference": communication_preference,
                    "decision_making_style": decision_making_style,
                    "urgency_level": urgency_level,
                    "price_sensitivity": price_sensitivity,
                    "risk_tolerance": risk_tolerance,
                    "total_interactions": total_interactions,
                    "avg_deal_cycle_days": avg_deal_cycle,
                    "total_deals": len(deal_list)
                }
                
        except Exception as e:
            logger.error(f"Error analyzing customer behavior: {e}")
            # Return default values if analysis fails
            return {
                "communication_preference": "email",
                "decision_making_style": "analytical",
                "urgency_level": "medium",
                "price_sensitivity": "moderate",
                "risk_tolerance": "low"
            }

    async def _determine_closing_approach(self, deal: DealClosing, customer_analysis: Dict[str, Any]) -> str:
        """Determine optimal closing approach based on deal and customer analysis"""
        try:
            # Analyze deal characteristics
            deal_value = deal.deal_value or 0
            deal_stage = deal.deal_stage or "prospecting"
            
            # Get customer behavior patterns
            communication_preference = customer_analysis.get("communication_preference", "email")
            decision_making_style = customer_analysis.get("decision_making_style", "analytical")
            urgency_level = customer_analysis.get("urgency_level", "medium")
            price_sensitivity = customer_analysis.get("price_sensitivity", "moderate")
            risk_tolerance = customer_analysis.get("risk_tolerance", "low")
            
            # Determine approach based on deal value and customer profile
            if deal_value > 100000:
                if decision_making_style == "analytical":
                    return "consultative"
                elif urgency_level == "high":
                    return "accelerated"
                else:
                    return "relationship_based"
            elif deal_value > 25000:
                if price_sensitivity == "high":
                    return "value_focused"
                elif communication_preference == "phone":
                    return "direct"
                else:
                    return "consultative"
            else:
                if urgency_level == "high":
                    return "quick_close"
                elif risk_tolerance == "low":
                    return "risk_mitigation"
                else:
                    return "standard"
                    
        except Exception as e:
            logger.error(f"Error determining closing approach: {e}")
            return "consultative"  # Default fallback

    async def _generate_closing_strategy(self, deal: DealClosing, approach: str) -> Dict[str, Any]:
        """Generate personalized closing strategy"""
        try:
            async with get_eric_database() as db:
                # Get deal details
                deal_value = deal.deal_value or 0
                deal_stage = deal.deal_stage or "prospecting"
                
                # Get customer profile for personalization
                customer_profile = await self._get_customer_profile(deal.customer_id, deal.brand_id)
                
                # Determine timeline based on deal value and urgency
                if deal_value > 100000:
                    timeline = "4-6 weeks"
                elif deal_value > 25000:
                    timeline = "2-3 weeks"
                else:
                    timeline = "1-2 weeks"
                
                # Generate key messages based on approach
                if approach == "consultative":
                    key_messages = [
                        "Value proposition and ROI demonstration",
                        "Customized solution alignment",
                        "Long-term partnership benefits"
                    ]
                elif approach == "value_focused":
                    key_messages = [
                        "Cost-benefit analysis",
                        "Competitive advantage",
                        "Quick implementation benefits"
                    ]
                elif approach == "accelerated":
                    key_messages = [
                        "Limited time opportunity",
                        "Immediate value delivery",
                        "Expedited implementation"
                    ]
                else:
                    key_messages = [
                        "Standard value proposition",
                        "Feature benefits",
                        "Customer success stories"
                    ]
                
                # Generate objection handling strategies
                objection_handling = []
                if deal_value > 50000:
                    objection_handling.extend(["Budget justification", "ROI demonstration"])
                if customer_profile.get("price_sensitivity") == "high":
                    objection_handling.append("Payment terms flexibility")
                if deal_stage == "negotiation":
                    objection_handling.extend(["Timeline concerns", "Feature requirements"])
                
                # Add common objections
                objection_handling.extend(["Competition comparison", "Implementation timeline"])
                
                return {
                    "approach": approach,
                    "timeline": timeline,
                    "key_messages": key_messages,
                    "objection_handling": objection_handling,
                    "personalization_level": "high" if deal_value > 50000 else "medium",
                    "risk_factors": await self._identify_risk_factors(deal),
                    "success_indicators": ["Positive engagement", "Decision maker involvement", "Budget confirmation"]
                }
                
        except Exception as e:
            logger.error(f"Error generating closing strategy: {e}")
            return {
                "approach": approach,
                "timeline": "2 weeks",
                "key_messages": ["Value proposition", "ROI demonstration"],
                "objection_handling": ["Price concerns", "Timeline concerns"]
            }

    async def _create_closing_timeline(self, deal: DealClosing, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create detailed closing timeline"""
        # Implementation for creating closing timeline
        return [
            {"day": 1, "activity": "Send proposal", "status": "scheduled"},
            {"day": 3, "activity": "Follow-up call", "status": "pending"},
            {"day": 7, "activity": "Demo session", "status": "pending"}
        ]

    async def _get_recommended_actions(self, deal: DealClosing, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommended actions for deal closing"""
        try:
            async with get_eric_database() as db:
                # Get deal details
                deal_value = deal.deal_value or 0
                deal_stage = deal.deal_stage or "prospecting"
                approach = strategy.get("approach", "standard")
                
                # Get customer profile
                customer_profile = await self._get_customer_profile(deal.customer_id, deal.brand_id)
                
                recommended_actions = []
                
                # High-value deal actions
                if deal_value > 100000:
                    recommended_actions.extend([
                        {
                            "action": "Schedule executive presentation",
                            "priority": "high",
                            "timing": "within_48_hours",
                            "description": "Present to C-level stakeholders for high-value deal"
                        },
                        {
                            "action": "Prepare detailed ROI analysis",
                            "priority": "high",
                            "timing": "within_24_hours",
                            "description": "Demonstrate clear financial benefits"
                        }
                    ])
                
                # Stage-specific actions
                if deal_stage == "prospecting":
                    recommended_actions.extend([
                        {
                            "action": "Send personalized proposal",
                            "priority": "high",
                            "timing": "immediate",
                            "description": "Initial proposal to move deal forward"
                        },
                        {
                            "action": "Schedule discovery call",
                            "priority": "medium",
                            "timing": "within_3_days",
                            "description": "Understand customer needs better"
                        }
                    ])
                elif deal_stage == "negotiation":
                    recommended_actions.extend([
                        {
                            "action": "Prepare contract draft",
                            "priority": "high",
                            "timing": "within_24_hours",
                            "description": "Have contract ready for review"
                        },
                        {
                            "action": "Schedule negotiation call",
                            "priority": "high",
                            "timing": "within_48_hours",
                            "description": "Address any remaining concerns"
                        }
                    ])
                elif deal_stage == "closing":
                    recommended_actions.extend([
                        {
                            "action": "Final contract review",
                            "priority": "critical",
                            "timing": "immediate",
                            "description": "Ensure all terms are agreed"
                        },
                        {
                            "action": "Schedule contract signing",
                            "priority": "critical",
                            "timing": "within_24_hours",
                            "description": "Close the deal"
                        }
                    ])
                
                # Approach-specific actions
                if approach == "consultative":
                    recommended_actions.append({
                        "action": "Schedule technical demo",
                        "priority": "medium",
                        "timing": "within_1_week",
                        "description": "Show technical capabilities"
                    })
                elif approach == "accelerated":
                    recommended_actions.append({
                        "action": "Send limited-time offer",
                        "priority": "high",
                        "timing": "immediate",
                        "description": "Create urgency for quick decision"
                    })
                
                # Customer-specific actions
                if customer_profile.get("communication_preference") == "phone":
                    recommended_actions.append({
                        "action": "Schedule follow-up call",
                        "priority": "medium",
                        "timing": "within_2_days",
                        "description": "Phone follow-up preferred by customer"
                    })
                
                # Add standard actions
                recommended_actions.extend([
                    {
                        "action": "Update CRM with latest activity",
                        "priority": "low",
                        "timing": "immediate",
                        "description": "Keep records current"
                    },
                    {
                        "action": "Prepare next steps summary",
                        "priority": "medium",
                        "timing": "within_24_hours",
                        "description": "Document agreed next steps"
                    }
                ])
                
                return recommended_actions
                
        except Exception as e:
            logger.error(f"Error getting recommended actions: {e}")
            return [
                {"action": "Send personalized proposal", "priority": "high", "timing": "immediate"},
                {"action": "Schedule demo call", "priority": "medium", "timing": "within_3_days"}
            ]

    async def _get_customer_profile(self, customer_id: str, brand_id: str) -> Dict[str, Any]:
        """Get customer profile for proposal generation"""
        try:
            async with get_eric_database() as db:
                # Get customer profile from database
                customer_query = select(CustomerProfile).where(
                    and_(
                        CustomerProfile.customer_id == customer_id,
                        CustomerProfile.brand_id == brand_id
                    )
                )
                customer_result = await db.execute(customer_query)
                customer = customer_result.scalar_one_or_none()
                
                if not customer:
                    # Return default profile if not found
                    return {
                        "name": "Unknown Customer",
                        "company": "Unknown Company",
                        "role": "Unknown",
                        "budget_range": "Unknown",
                        "decision_authority": "Unknown"
                    }
                
                # Get customer's deal history for additional insights
                deals_query = select(Deal).where(
                    and_(
                        Deal.customer_id == customer_id,
                        Deal.brand_id == brand_id
                    )
                )
                deals_result = await db.execute(deals_query)
                deal_list = deals_result.scalars().all()
                
                # Calculate additional metrics
                total_deals = len(deal_list)
                won_deals = [d for d in deal_list if d.sales_stage == SalesStage.CLOSED]
                win_rate = (len(won_deals) / total_deals * 100) if total_deals > 0 else 0
                
                avg_deal_size = 0
                if deal_list:
                    avg_deal_size = sum(d.deal_value for d in deal_list) / len(deal_list)
                
                # Determine decision authority based on role and deal history
                job_title = customer.job_title or "Unknown"
                decision_authority = "high"
                if any(word in job_title.lower() for word in ["ceo", "cto", "cfo", "vp", "director"]):
                    decision_authority = "high"
                elif any(word in job_title.lower() for word in ["manager", "lead", "head"]):
                    decision_authority = "medium"
                else:
                    decision_authority = "low"
                
                # Determine budget range based on lifetime value
                lifetime_value = customer.lifetime_value or 0
                if lifetime_value > 100000:
                    budget_range = "$100K+"
                elif lifetime_value > 50000:
                    budget_range = "$50K-$100K"
                elif lifetime_value > 10000:
                    budget_range = "$10K-$50K"
                else:
                    budget_range = "$1K-$10K"
                
                return {
                    "name": f"{customer.first_name or ''} {customer.last_name or ''}".strip(),
                    "company": customer.company or "Unknown Company",
                    "role": customer.job_title or "Unknown",
                    "budget_range": budget_range,
                    "decision_authority": decision_authority,
                    "industry": customer.industry or "Unknown",
                    "company_size": customer.company_size or "Unknown",
                    "location": customer.location or "Unknown",
                    "lifetime_value": round(lifetime_value, 2),
                    "total_deals": total_deals,
                    "win_rate": round(win_rate, 2),
                    "avg_deal_size": round(avg_deal_size, 2),
                    "preferred_communication": customer.preferred_communication or "email",
                    "pain_points": customer.pain_points or [],
                    "requirements": customer.requirements or []
                }
                
        except Exception as e:
            logger.error(f"Error getting customer profile: {e}")
            return {
                "name": "John Doe",
                "company": "TechCorp",
                "role": "CTO",
                "budget_range": "$50K-$100K",
                "decision_authority": "high"
            }

    async def _generate_proposal_content(self, deal: DealClosing, customer_profile: Dict[str, Any], 
                                       proposal_type: str) -> Dict[str, Any]:
        """Generate proposal content using AI"""
        # Implementation for generating proposal content
        return {
            "executive_summary": "AI-generated executive summary",
            "solution_overview": "AI-generated solution overview",
            "pricing": "AI-generated pricing structure",
            "timeline": "AI-generated implementation timeline"
        }

    async def _generate_pricing_options(self, deal: DealClosing) -> List[Dict[str, Any]]:
        """Generate pricing options for the deal"""
        # Implementation for generating pricing options
        return [
            {"option": "Basic", "price": 50000, "features": ["Core features"]},
            {"option": "Premium", "price": 75000, "features": ["Core + Advanced features"]}
        ]

    async def _generate_terms_and_conditions(self, deal: DealClosing) -> Dict[str, Any]:
        """Generate terms and conditions for the deal"""
        # Implementation for generating terms and conditions
        return {
            "payment_terms": "Net 30",
            "delivery_timeline": "6 weeks",
            "warranty": "1 year",
            "support": "24/7"
        }

    async def _generate_next_steps(self, deal: DealClosing) -> List[Dict[str, Any]]:
        """Generate next steps for the deal"""
        # Implementation for generating next steps
        return [
            {"step": "Review proposal", "timeline": "3 days"},
            {"step": "Schedule demo", "timeline": "1 week"},
            {"step": "Contract signing", "timeline": "2 weeks"}
        ]

    async def _save_proposal(self, deal_id: str, brand_id: str, proposal: Dict[str, Any]):
        """Save proposal to database"""
        # Implementation for saving proposal
        pass

    async def _create_sequence_steps(self, deal: DealClosing, sequence_type: str) -> List[Dict[str, Any]]:
        """Create sequence steps for closing"""
        # Implementation for creating sequence steps
        return [
            {"step": 1, "action": "Send proposal", "delay": "0 days"},
            {"step": 2, "action": "Follow-up email", "delay": "2 days"},
            {"step": 3, "action": "Phone call", "delay": "5 days"}
        ]

    async def _schedule_sequence_activities(self, deal_id: str, brand_id: str, 
                                          sequence_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Schedule sequence activities"""
        # Implementation for scheduling sequence activities
        return [
            {"activity_id": "act_001", "scheduled_time": datetime.utcnow() + timedelta(days=2)},
            {"activity_id": "act_002", "scheduled_time": datetime.utcnow() + timedelta(days=5)}
        ]

    async def _calculate_expected_completion(self, sequence_steps: List[Dict[str, Any]]) -> datetime:
        """Calculate expected completion time for sequence"""
        # Implementation for calculating expected completion
        return datetime.utcnow() + timedelta(days=14)

    async def _save_closing_sequence(self, deal_id: str, brand_id: str, sequence: Dict[str, Any]):
        """Save closing sequence to database"""
        try:
            async with get_eric_database() as db:
                # Create closing sequence record
                closing_sequence = ClosingSequence(
                    deal_id=deal_id,
                    brand_id=brand_id,
                    sequence_type=sequence.get("type", "standard"),
                    steps=sequence.get("steps", []),
                    status="active",
                    created_at=datetime.utcnow(),
                    expected_completion=sequence.get("expected_completion")
                )
                
                db.add(closing_sequence)
                await db.commit()
                
                # Store in Redis for quick access
                await self.redis_manager.set(
                    f"closing_sequence:{deal_id}",
                    json.dumps(sequence),
                    expire=86400  # 24 hours
                )
                
                logger.info(f"Saved closing sequence for deal {deal_id}")
                
        except Exception as e:
            logger.error(f"Failed to save closing sequence for deal {deal_id}: {e}")
            raise

    async def _generate_objection_response_strategy(self, objection_type: str, 
                                                  objection_analysis: Dict[str, Any], 
                                                  deal: DealClosing) -> Dict[str, Any]:
        """Generate response strategy for objections"""
        # Implementation for generating objection response strategy
        return {
            "approach": "empathetic",
            "key_points": ["Address concern", "Provide solution", "Reinforce value"],
            "timing": "immediate"
        }

    async def _create_objection_response(self, objection_details: str, 
                                       response_strategy: Dict[str, Any], 
                                       deal: DealClosing) -> str:
        """Create personalized objection response"""
        # Implementation for creating objection response
        return "AI-generated personalized response addressing the objection"

    async def _update_deal_objection_status(self, deal_id: str, brand_id: str, 
        objection_type: str, response_strategy: Dict[str, Any]):
        """Update deal objection status"""
        try:
            async with get_eric_database() as db:
                # Update deal with objection information
                await db.execute(
                    update(DealClosing).where(
                        and_(
                            DealClosing.deal_id == deal_id,
                            DealClosing.brand_id == brand_id
                        )
                    ).values(
                        objection_type=objection_type,
                        objection_status="addressed",
                        response_strategy=response_strategy,
                        last_objection_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                )

                # Create objection tracking record
                objection_record = DealClosingActivity(
                    deal_id=deal_id,
                    brand_id=brand_id,
                    activity_type="objection_handled",
                    activity_data={
                        "objection_type": objection_type,
                        "response_strategy": response_strategy,
                        "handled_at": datetime.utcnow().isoformat()
                    },
                    created_at=datetime.utcnow()
                )

                db.add(objection_record)
                await db.commit()

                logger.info(f"Updated objection status for deal {deal_id}")

        except Exception as e:
            logger.error(f"Failed to update deal objection status: {e}")
            raise

    async def _get_objection_follow_up_actions(self, deal: DealClosing, objection_type: str) -> List[Dict[str, Any]]:
        """Get follow-up actions for objections"""
        # Implementation for getting objection follow-up actions
        return [
            {"action": "Schedule follow-up call", "timing": "within_24_hours"},
            {"action": "Send additional materials", "timing": "immediate"}
        ]

    async def _validate_closing_activity(self, activity_type: str, activity_data: Dict[str, Any]) -> bool:
        """Validate closing activity"""
        # Implementation for validating closing activity
        return True

    async def _send_closing_proposal(self, deal_id: str, brand_id: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send closing proposal"""
        # Implementation for sending closing proposal
        return {"status": "sent", "delivery_confirmation": "confirmed"}

    async def _schedule_closing_demo(self, deal_id: str, brand_id: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule closing demo"""
        # Implementation for scheduling closing demo
        return {"status": "scheduled", "demo_time": datetime.utcnow() + timedelta(days=3)}

    async def _send_closing_contract(self, deal_id: str, brand_id: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send closing contract"""
        # Implementation for sending closing contract
        return {"status": "sent", "contract_id": "contract_123"}

    async def _execute_follow_up_call(self, deal_id: str, brand_id: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute follow-up call"""
        # Implementation for executing follow-up call
        return {"status": "completed", "call_duration": "15 minutes"}

    async def _negotiate_closing_terms(self, deal_id: str, brand_id: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Negotiate closing terms"""
        # Implementation for negotiating closing terms
        return {"status": "negotiated", "agreed_terms": activity_data.get("terms")}

    async def _log_closing_activity(self, deal_id: str, brand_id: str, activity_type: str, 
                                  activity_data: Dict[str, Any], result: Dict[str, Any]):
        """Log closing activity"""
        # Implementation for logging closing activity
        pass

    async def _update_deal_progress(self, deal_id: str, brand_id: str, activity_type: str, result: Dict[str, Any]):
        """Update deal progress"""
        # Implementation for updating deal progress
        pass

    async def _get_next_recommended_action(self, deal_id: str, brand_id: str) -> Dict[str, Any]:
        """Get next recommended action"""
        # Implementation for getting next recommended action
        return {"action": "Schedule demo", "priority": "high", "timing": "within_3_days"}

    async def _calculate_closing_progress(self, deal: DealClosing, activities: List[DealClosingActivity]) -> Dict[str, Any]:
        """Calculate closing progress metrics"""
        # Implementation for calculating closing progress
        return {
            "overall_progress": 75,
            "time_elapsed": "10 days",
            "time_remaining": "4 days",
            "activities_completed": 6,
            "activities_pending": 2,
            "milestones": ["Proposal sent", "Demo scheduled", "Contract prepared"]
        }

    async def _get_current_closing_stage(self, deal: DealClosing, activities: List[DealClosingActivity]) -> str:
        """Get current closing stage"""
        # Implementation for getting current closing stage
        return "negotiation"

    async def _identify_closing_bottlenecks(self, deal: DealClosing, activities: List[DealClosingActivity]) -> List[str]:
        """Identify closing bottlenecks"""
        # Implementation for identifying closing bottlenecks
        return ["Customer review time", "Legal approval"]

    async def _get_progress_recommendations(self, deal: DealClosing, progress_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get progress recommendations"""
        # Implementation for getting progress recommendations
        return [
            {"recommendation": "Follow up on proposal", "priority": "high"},
            {"recommendation": "Prepare contract", "priority": "medium"}
        ]

    async def _validate_closing_terms(self, closing_terms: Dict[str, Any]) -> bool:
        """Validate closing terms"""
        # Implementation for validating closing terms
        return True

    async def _execute_contract_closing(self, deal: DealClosing, closing_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Execute contract-based closing"""
        # Implementation for executing contract closing
        return {"contract_signed": True, "payment_processed": True}

    async def _execute_payment_closing(self, deal: DealClosing, closing_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Execute payment-based closing"""
        # Implementation for executing payment closing
        return {"payment_processed": True, "amount": closing_terms.get("amount")}

    async def _execute_handshake_closing(self, deal: DealClosing, closing_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Execute handshake agreement closing"""
        # Implementation for executing handshake closing
        return {"agreement_confirmed": True, "next_steps": closing_terms.get("next_steps")}

    async def _update_deal_to_closed(self, deal_id: str, brand_id: str, closing_method: str, closing_result: Dict[str, Any]):
        """Update deal status to closed"""
        # Implementation for updating deal to closed
        pass

    async def _trigger_post_closing_activities(self, deal_id: str, brand_id: str, closing_result: Dict[str, Any]):
        """Trigger post-closing activities"""
        # Implementation for triggering post-closing activities
        pass

    async def _send_closing_notifications(self, deal_id: str, brand_id: str, closing_result: Dict[str, Any]):
        """Send closing notifications"""
        # Implementation for sending closing notifications
        pass

    async def _get_post_closing_activities(self, deal_id: str, brand_id: str) -> List[Dict[str, Any]]:
        """Get post-closing activities"""
        # Implementation for getting post-closing activities
        return [
            {"activity": "Onboarding setup", "timeline": "1 week"},
            {"activity": "Success metrics tracking", "timeline": "ongoing"}
        ]

    async def _identify_risk_factors(self, deal: DealClosing) -> List[str]:
        """Identify risk factors for deal closing"""
        # Implementation for identifying risk factors
        return ["Budget constraints", "Timeline pressure", "Competition"]

    async def _identify_opportunity_signals(self, deal: DealClosing) -> List[str]:
        """Identify opportunity signals for deal closing"""
        # Implementation for identifying opportunity signals
        return ["High engagement", "Positive feedback", "Decision maker involvement"]
