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
from ..models import Lead, Deal, LeadInteraction, LeadStatus, SalesStage, Objection, SalesActivity
from ..database import get_eric_database

logger = logging.getLogger(__name__)

class DealClosingService:
    """Service for deal closing assistance and optimization"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.redis_client = None
        self.chroma_manager = None
        self.integration_manager = None
        self.platform_manager = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize deal closing service"""
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
            logger.info("Eric deal closing service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize deal closing service: {e}")
            raise
    
    async def generate_closing_recommendations(
        self,
        deal_id: int,
        closing_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized closing recommendations for a deal"""
        try:
            await self.initialize()
            
            db = next(get_db())
            deal = db.query(Deal).filter(Deal.id == deal_id).first()
            
            if not deal:
                return {
                    "success": False,
                    "error": "Deal not found"
                }
            
            # Get associated lead
            lead = db.query(Lead).filter(Lead.id == deal.lead_id).first()
            
            # Analyze deal context
            deal_analysis = await self._analyze_deal_context(deal, lead, db)
            
            # Generate closing strategies
            closing_strategies = await self._generate_closing_strategies(deal, lead, deal_analysis)
            
            # Generate personalized offers
            personalized_offers = await self._generate_personalized_offers(deal, lead, deal_analysis)
            
            # Generate objection handling
            objection_handling = await self._generate_objection_handling(deal, lead, deal_analysis)
            
            # Generate closing timeline
            closing_timeline = await self._generate_closing_timeline(deal, deal_analysis)
            
            return {
                "success": True,
                "deal_id": deal_id,
                "deal_analysis": deal_analysis,
                "closing_strategies": closing_strategies,
                "personalized_offers": personalized_offers,
                "objection_handling": objection_handling,
                "closing_timeline": closing_timeline,
                "recommendations": await self._generate_closing_recommendations_summary(deal, closing_strategies, personalized_offers)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate closing recommendations: {e}")
            return {
                "success": False,
                "error": f"Failed to generate closing recommendations: {str(e)}"
            }
    
    async def optimize_deal_value(
        self,
        deal_id: int,
        optimization_goals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize deal value and terms"""
        try:
            await self.initialize()
            
            db = next(get_db())
            deal = db.query(Deal).filter(Deal.id == deal_id).first()
            
            if not deal:
                return {
                    "success": False,
                    "error": "Deal not found"
                }
            
            # Analyze current deal value
            current_value_analysis = await self._analyze_current_deal_value(deal, db)
            
            # Generate value optimization strategies
            value_optimization = await self._generate_value_optimization_strategies(deal, optimization_goals)
            
            # Generate upsell opportunities
            upsell_opportunities = await self._identify_upsell_opportunities(deal, db)
            
            # Generate cross-sell opportunities
            cross_sell_opportunities = await self._identify_cross_sell_opportunities(deal, db)
            
            # Generate pricing optimization
            pricing_optimization = await self._optimize_pricing_strategy(deal, optimization_goals)
            
            return {
                "success": True,
                "deal_id": deal_id,
                "current_value_analysis": current_value_analysis,
                "value_optimization": value_optimization,
                "upsell_opportunities": upsell_opportunities,
                "cross_sell_opportunities": cross_sell_opportunities,
                "pricing_optimization": pricing_optimization,
                "total_potential_value": await self._calculate_total_potential_value(deal, upsell_opportunities, cross_sell_opportunities)
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize deal value: {e}")
            return {
                "success": False,
                "error": f"Failed to optimize deal value: {str(e)}"
            }
    
    async def handle_deal_objections(
        self,
        deal_id: int,
        objection_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle and respond to deal objections"""
        try:
            await self.initialize()
            
            db = next(get_db())
            deal = db.query(Deal).filter(Deal.id == deal_id).first()
            
            if not deal:
                return {
                    "success": False,
                    "error": "Deal not found"
                }
            
            # Record objection
            objection = Objection(
                deal_id=deal_id,
                objection_type=objection_data.get("objection_type"),
                objection_text=objection_data.get("objection_text"),
                severity=objection_data.get("severity", "medium"),
                source=objection_data.get("source", "customer"),
                created_at=datetime.now()
            )
            db.add(objection)
            db.commit()
            
            # Generate objection response
            objection_response = await self._generate_objection_response(deal, objection_data)
            
            # Generate follow-up strategy
            follow_up_strategy = await self._generate_follow_up_strategy(deal, objection_data)
            
            # Update deal status
            if objection_data.get("severity") == "high":
                deal.sales_stage = SalesStage.NEGOTIATION
                deal.probability = max(deal.probability - 10, 0)
            else:
                deal.probability = max(deal.probability - 5, 0)
            
            db.commit()
            
            return {
                "success": True,
                "objection_id": objection.id,
                "objection_response": objection_response,
                "follow_up_strategy": follow_up_strategy,
                "updated_deal_probability": deal.probability,
                "recommendations": await self._generate_objection_recommendations(deal, objection_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to handle deal objections: {e}")
            return {
                "success": False,
                "error": f"Failed to handle deal objections: {str(e)}"
            }
    
    async def create_closing_playbook(
        self,
        deal_id: int,
        playbook_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a personalized closing playbook"""
        try:
            await self.initialize()
            
            db = next(get_db())
            deal = db.query(Deal).filter(Deal.id == deal_id).first()
            
            if not deal:
                return {
                    "success": False,
                    "error": "Deal not found"
                }
            
            # Generate playbook sections
            playbook = {
                "deal_summary": await self._generate_deal_summary(deal, db),
                "customer_profile": await self._generate_customer_profile(deal, db),
                "value_proposition": await self._generate_value_proposition(deal, playbook_config),
                "closing_scripts": await self._generate_closing_scripts(deal, playbook_config),
                "objection_handlers": await self._generate_objection_handlers(deal, db),
                "negotiation_tactics": await self._generate_negotiation_tactics(deal, playbook_config),
                "timeline": await self._generate_closing_timeline(deal, {}),
                "success_metrics": await self._define_success_metrics(deal, playbook_config)
            }
            
            return {
                "success": True,
                "deal_id": deal_id,
                "playbook": playbook,
                "playbook_id": f"playbook_{deal_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create closing playbook: {e}")
            return {
                "success": False,
                "error": f"Failed to create closing playbook: {str(e)}"
            }
    
    async def track_closing_progress(
        self,
        deal_id: int,
        progress_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track and analyze closing progress"""
        try:
            await self.initialize()
            
            db = next(get_db())
            deal = db.query(Deal).filter(Deal.id == deal_id).first()
            
            if not deal:
                return {
                    "success": False,
                    "error": "Deal not found"
                }
            
            # Update deal progress
            if progress_data.get("milestone_completed"):
                deal.probability = min(deal.probability + 10, 100)
            
            if progress_data.get("objection_resolved"):
                deal.probability = min(deal.probability + 5, 100)
            
            # Update expected close date if provided
            if progress_data.get("expected_close_date"):
                deal.expected_close_date = datetime.fromisoformat(progress_data["expected_close_date"])
            
            db.commit()
            
            # Analyze progress
            progress_analysis = await self._analyze_closing_progress(deal, progress_data, db)
            
            # Generate next steps
            next_steps = await self._generate_next_steps(deal, progress_analysis)
            
            return {
                "success": True,
                "deal_id": deal_id,
                "updated_probability": deal.probability,
                "progress_analysis": progress_analysis,
                "next_steps": next_steps,
                "recommendations": await self._generate_progress_recommendations(deal, progress_analysis)
            }
            
        except Exception as e:
            logger.error(f"Failed to track closing progress: {e}")
            return {
                "success": False,
                "error": f"Failed to track closing progress: {str(e)}"
            }
    
    async def _analyze_deal_context(
        self,
        deal: Deal,
        lead: Lead,
        db: Session
    ) -> Dict[str, Any]:
        """Analyze deal context and factors"""
        try:
            # Get deal interactions
            interactions = db.query(LeadInteraction).filter(
                LeadInteraction.lead_id == deal.lead_id
            ).all()
            
            # Analyze deal factors
            deal_factors = {
                "deal_value": deal.deal_value,
                "probability": deal.probability,
                "sales_stage": deal.sales_stage.value,
                "days_in_pipeline": (datetime.now() - deal.created_at).days,
                "interaction_count": len(interactions),
                "last_activity_days": 0
            }
            
            if interactions:
                last_interaction = max(interactions, key=lambda x: x.created_at)
                deal_factors["last_activity_days"] = (datetime.now() - last_interaction.created_at).days
            
            # Analyze customer factors
            customer_factors = {
                "lead_score": lead.lead_score,
                "company_size": lead.company,
                "industry": lead.industry,
                "budget": lead.budget,
                "timeline": lead.timeline,
                "pain_points": lead.pain_points
            }
            
            # Calculate urgency score
            urgency_score = 0
            if deal_factors["days_in_pipeline"] > 30:
                urgency_score += 30
            if deal_factors["last_activity_days"] > 7:
                urgency_score += 20
            if lead.timeline in ["immediate", "this month"]:
                urgency_score += 25
            if deal.probability > 70:
                urgency_score += 25
            
            return {
                "deal_factors": deal_factors,
                "customer_factors": customer_factors,
                "urgency_score": min(urgency_score, 100),
                "risk_factors": await self._identify_risk_factors(deal, lead, deal_factors)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze deal context: {e}")
            return {}
    
    async def _generate_closing_strategies(
        self,
        deal: Deal,
        lead: Lead,
        deal_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate closing strategies based on deal analysis"""
        try:
            strategies = []
            
            # Urgency-based strategies
            urgency_score = deal_analysis.get("urgency_score", 0)
            if urgency_score > 70:
                strategies.append({
                    "type": "urgency",
                    "title": "High Urgency - Immediate Action Required",
                    "description": "Deal shows high urgency signals. Focus on quick closing with limited-time offers.",
                    "tactics": [
                        "Present limited-time pricing",
                        "Schedule immediate decision meeting",
                        "Offer expedited implementation"
                    ],
                    "priority": "high"
                })
            
            # Value-based strategies
            if deal.deal_value > 10000:
                strategies.append({
                    "type": "value",
                    "title": "High-Value Deal - Executive Engagement",
                    "description": "High-value deal requiring executive-level engagement and custom solutions.",
                    "tactics": [
                        "Engage executive sponsors",
                        "Create custom ROI analysis",
                        "Offer executive briefing"
                    ],
                    "priority": "high"
                })
            
            # Relationship-based strategies
            if lead.lead_score > 0.7:
                strategies.append({
                    "type": "relationship",
                    "title": "Strong Relationship - Trust-Based Closing",
                    "description": "Strong relationship with customer. Focus on trust and partnership.",
                    "tactics": [
                        "Leverage existing relationship",
                        "Provide customer references",
                        "Offer partnership opportunities"
                    ],
                    "priority": "medium"
                })
            
            # Risk mitigation strategies
            risk_factors = deal_analysis.get("risk_factors", [])
            if risk_factors:
                strategies.append({
                    "type": "risk_mitigation",
                    "title": "Risk Mitigation - Address Concerns",
                    "description": "Address identified risk factors to improve closing probability.",
                    "tactics": [
                        "Address specific objections",
                        "Provide additional assurances",
                        "Offer trial or pilot program"
                    ],
                    "priority": "high"
                })
            
            return strategies
            
        except Exception as e:
            logger.error(f"Failed to generate closing strategies: {e}")
            return []
    
    async def _generate_personalized_offers(
        self,
        deal: Deal,
        lead: Lead,
        deal_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate personalized offers for the deal"""
        try:
            offers = []
            
            # Base offer optimization
            base_offer = {
                "type": "base_optimization",
                "title": "Optimized Base Offer",
                "description": "Enhanced base offer with improved terms",
                "original_value": deal.deal_value,
                "optimized_value": deal.deal_value * 1.1,
                "discount_percentage": 10,
                "validity_days": 14,
                "terms": [
                    "Extended payment terms",
                    "Enhanced support package",
                    "Training included"
                ]
            }
            offers.append(base_offer)
            
            # Volume-based offers
            if deal.deal_value > 5000:
                volume_offer = {
                    "type": "volume_discount",
                    "title": "Volume Discount Package",
                    "description": "Additional volume discount for larger commitment",
                    "original_value": deal.deal_value,
                    "discounted_value": deal.deal_value * 0.85,
                    "discount_percentage": 15,
                    "validity_days": 7,
                    "terms": [
                        "Minimum 12-month commitment",
                        "Additional user licenses",
                        "Premium support tier"
                    ]
                }
                offers.append(volume_offer)
            
            # Early adoption offers
            if lead.timeline in ["immediate", "this month"]:
                early_offer = {
                    "type": "early_adoption",
                    "title": "Early Adoption Incentive",
                    "description": "Special pricing for early adoption",
                    "original_value": deal.deal_value,
                    "discounted_value": deal.deal_value * 0.9,
                    "discount_percentage": 10,
                    "validity_days": 5,
                    "terms": [
                        "Pilot program access",
                        "Dedicated success manager",
                        "Custom onboarding"
                    ]
                }
                offers.append(early_offer)
            
            # Risk-free offers
            if deal.probability < 60:
                risk_free_offer = {
                    "type": "risk_free",
                    "title": "Risk-Free Trial",
                    "description": "Risk-free trial with money-back guarantee",
                    "original_value": deal.deal_value,
                    "trial_value": deal.deal_value * 0.3,
                    "trial_period": "30 days",
                    "validity_days": 10,
                    "terms": [
                        "30-day money-back guarantee",
                        "Full feature access",
                        "No setup fees"
                    ]
                }
                offers.append(risk_free_offer)
            
            return offers
            
        except Exception as e:
            logger.error(f"Failed to generate personalized offers: {e}")
            return []
    
    async def _generate_objection_handling(
        self,
        deal: Deal,
        lead: Lead,
        deal_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate objection handling strategies"""
        try:
            objection_handlers = {
                "price_objections": [
                    {
                        "objection": "Too expensive",
                        "response": "Let me show you the ROI calculation. Our solution typically pays for itself within 6 months.",
                        "evidence": "ROI analysis, case studies, cost comparison"
                    },
                    {
                        "objection": "Budget constraints",
                        "response": "I understand budget concerns. Let's explore flexible payment options and phased implementation.",
                        "evidence": "Payment plans, implementation phases, value demonstration"
                    }
                ],
                "timeline_objections": [
                    {
                        "objection": "Need more time to decide",
                        "response": "I understand the need for careful consideration. Let's set up a timeline that works for you.",
                        "evidence": "Implementation timeline, pilot program, gradual rollout"
                    }
                ],
                "feature_objections": [
                    {
                        "objection": "Missing features",
                        "response": "Let me address your specific needs. We can customize the solution or integrate with existing tools.",
                        "evidence": "Customization options, integrations, roadmap"
                    }
                ],
                "trust_objections": [
                    {
                        "objection": "Not sure about the company",
                        "response": "I'd be happy to provide customer references and case studies from your industry.",
                        "evidence": "Customer testimonials, case studies, company credentials"
                    }
                ]
            }
            
            return objection_handlers
            
        except Exception as e:
            logger.error(f"Failed to generate objection handling: {e}")
            return {}
    
    async def _generate_closing_timeline(
        self,
        deal: Deal,
        deal_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate closing timeline and milestones"""
        try:
            urgency_score = deal_analysis.get("urgency_score", 0)
            
            if urgency_score > 70:
                timeline_days = 7
            elif urgency_score > 40:
                timeline_days = 14
            else:
                timeline_days = 30
            
            timeline = {
                "total_days": timeline_days,
                "milestones": [
                    {
                        "day": 1,
                        "milestone": "Initial closing discussion",
                        "action": "Present final proposal and address immediate concerns"
                    },
                    {
                        "day": 3,
                        "milestone": "Follow-up meeting",
                        "action": "Address objections and provide additional information"
                    },
                    {
                        "day": 7,
                        "milestone": "Decision meeting",
                        "action": "Final presentation and decision request"
                    },
                    {
                        "day": timeline_days,
                        "milestone": "Close deal",
                        "action": "Contract signing and implementation planning"
                    }
                ],
                "critical_path": [
                    "Address all objections within 48 hours",
                    "Provide ROI analysis within 3 days",
                    "Schedule decision meeting within 7 days"
                ]
            }
            
            return timeline
            
        except Exception as e:
            logger.error(f"Failed to generate closing timeline: {e}")
            return {}
    
    async def _analyze_current_deal_value(
        self,
        deal: Deal,
        db: Session
    ) -> Dict[str, Any]:
        """Analyze current deal value and components"""
        try:
            # Get deal components
            deal_components = {
                "base_value": deal.deal_value,
                "currency": deal.currency,
                "probability": deal.probability,
                "expected_value": deal.deal_value * (deal.probability / 100),
                "days_in_pipeline": (datetime.now() - deal.created_at).days
            }
            
            # Analyze value trends
            value_trends = {
                "value_change": 0,  # Would track historical changes
                "probability_change": 0,  # Would track probability changes
                "trend_direction": "stable"
            }
            
            return {
                "current_value": deal_components,
                "value_trends": value_trends,
                "optimization_potential": await self._calculate_optimization_potential(deal)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze current deal value: {e}")
            return {}
    
    async def _generate_value_optimization_strategies(
        self,
        deal: Deal,
        optimization_goals: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate value optimization strategies"""
        try:
            strategies = []
            
            # Upselling strategies
            if optimization_goals.get("increase_value"):
                strategies.append({
                    "type": "upsell",
                    "title": "Premium Features Upsell",
                    "description": "Add premium features to increase deal value",
                    "potential_increase": deal.deal_value * 0.3,
                    "implementation": "Immediate",
                    "risk": "Low"
                })
            
            # Cross-selling strategies
            if optimization_goals.get("expand_scope"):
                strategies.append({
                    "type": "cross_sell",
                    "title": "Additional Services",
                    "description": "Add complementary services to the deal",
                    "potential_increase": deal.deal_value * 0.2,
                    "implementation": "Immediate",
                    "risk": "Low"
                })
            
            # Pricing optimization
            if optimization_goals.get("optimize_pricing"):
                strategies.append({
                    "type": "pricing",
                    "title": "Value-Based Pricing",
                    "description": "Adjust pricing based on value delivered",
                    "potential_increase": deal.deal_value * 0.15,
                    "implementation": "Immediate",
                    "risk": "Medium"
                })
            
            return strategies
            
        except Exception as e:
            logger.error(f"Failed to generate value optimization strategies: {e}")
            return []
    
    async def _identify_upsell_opportunities(
        self,
        deal: Deal,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Identify upsell opportunities"""
        try:
            upsell_opportunities = []
            
            # Premium features
            upsell_opportunities.append({
                "type": "premium_features",
                "title": "Advanced Analytics Package",
                "description": "Add advanced analytics and reporting capabilities",
                "value": deal.deal_value * 0.25,
                "probability": 0.6,
                "effort": "Low"
            })
            
            # Enterprise features
            if deal.deal_value > 5000:
                upsell_opportunities.append({
                    "type": "enterprise_features",
                    "title": "Enterprise Security Package",
                    "description": "Add enterprise-grade security and compliance features",
                    "value": deal.deal_value * 0.3,
                    "probability": 0.5,
                    "effort": "Medium"
                })
            
            # Training and support
            upsell_opportunities.append({
                "type": "services",
                "title": "Premium Support and Training",
                "description": "Add premium support and comprehensive training",
                "value": deal.deal_value * 0.15,
                "probability": 0.7,
                "effort": "Low"
            })
            
            return upsell_opportunities
            
        except Exception as e:
            logger.error(f"Failed to identify upsell opportunities: {e}")
            return []
    
    async def _identify_cross_sell_opportunities(
        self,
        deal: Deal,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Identify cross-sell opportunities"""
        try:
            cross_sell_opportunities = []
            
            # Complementary products
            cross_sell_opportunities.append({
                "type": "complementary_product",
                "title": "Integration Services",
                "description": "Add integration services for existing systems",
                "value": deal.deal_value * 0.2,
                "probability": 0.6,
                "effort": "Medium"
            })
            
            # Consulting services
            cross_sell_opportunities.append({
                "type": "consulting",
                "title": "Implementation Consulting",
                "description": "Add implementation consulting and project management",
                "value": deal.deal_value * 0.3,
                "probability": 0.5,
                "effort": "High"
            })
            
            return cross_sell_opportunities
            
        except Exception as e:
            logger.error(f"Failed to identify cross-sell opportunities: {e}")
            return []
    
    async def _optimize_pricing_strategy(
        self,
        deal: Deal,
        optimization_goals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize pricing strategy"""
        try:
            pricing_strategies = {
                "current_pricing": {
                    "base_price": deal.deal_value,
                    "currency": deal.currency,
                    "pricing_model": "one_time"
                },
                "optimization_options": [
                    {
                        "strategy": "value_based_pricing",
                        "description": "Price based on value delivered",
                        "potential_increase": 15,
                        "implementation": "Immediate"
                    },
                    {
                        "strategy": "tiered_pricing",
                        "description": "Offer multiple pricing tiers",
                        "potential_increase": 20,
                        "implementation": "Immediate"
                    },
                    {
                        "strategy": "subscription_model",
                        "description": "Convert to subscription pricing",
                        "potential_increase": 25,
                        "implementation": "Medium"
                    }
                ],
                "recommendations": [
                    "Implement value-based pricing for immediate impact",
                    "Consider subscription model for long-term value",
                    "Offer tiered pricing for different customer segments"
                ]
            }
            
            return pricing_strategies
            
        except Exception as e:
            logger.error(f"Failed to optimize pricing strategy: {e}")
            return {}
    
    async def _generate_objection_response(
        self,
        deal: Deal,
        objection_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate response to specific objection"""
        try:
            objection_type = objection_data.get("objection_type")
            objection_text = objection_data.get("objection_text", "")
            
            # Generate AI-powered response
            response_prompt = f"""
            Generate a professional response to this sales objection:
            
            Objection Type: {objection_type}
            Objection Text: {objection_text}
            Deal Value: ${deal.deal_value:,.2f}
            
            Provide a response that:
            1. Acknowledges the concern
            2. Addresses the specific objection
            3. Provides value-based solution
            4. Includes next steps
            """
            
            # Use AI Service Manager instead of NLPUtils
            from core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI sales assistant that helps with deal closing strategies."},
                {"role": "user", "content": response_prompt}
            ]
            ai_response_obj = await ai_manager.generate_text(
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            ai_response = ai_response_obj.text_content if ai_response_obj.success else ""
            
            return {
                "response": ai_response,
                "objection_type": objection_type,
                "addressing_points": [
                    "Acknowledge customer concern",
                    "Provide specific solution",
                    "Offer value demonstration",
                    "Suggest next steps"
                ],
                "follow_up_actions": [
                    "Schedule follow-up meeting",
                    "Provide additional materials",
                    "Offer trial or demo",
                    "Connect with technical team"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate objection response: {e}")
            return {
                "response": "Thank you for sharing your concern. I'd be happy to address this specifically and provide you with the information you need to make an informed decision.",
                "objection_type": objection_data.get("objection_type"),
                "addressing_points": [],
                "follow_up_actions": []
            }
    
    async def _identify_risk_factors(
        self,
        deal: Deal,
        lead: Lead,
        deal_factors: Dict[str, Any]
    ) -> List[str]:
        """Identify risk factors for the deal"""
        try:
            risk_factors = []
            
            # Time-based risks
            if deal_factors.get("days_in_pipeline", 0) > 60:
                risk_factors.append("Deal aging - may lose momentum")
            
            if deal_factors.get("last_activity_days", 0) > 14:
                risk_factors.append("No recent activity - customer may be disengaged")
            
            # Value-based risks
            if deal.deal_value > 50000 and deal.probability < 50:
                risk_factors.append("High-value deal with low probability")
            
            # Customer-based risks
            if lead.lead_score < 0.4:
                risk_factors.append("Low lead score - may not be qualified")
            
            if not lead.budget or lead.budget < deal.deal_value:
                risk_factors.append("Budget constraints - may not afford solution")
            
            return risk_factors
            
        except Exception as e:
            logger.error(f"Failed to identify risk factors: {e}")
            return []
    
    async def _calculate_optimization_potential(
        self,
        deal: Deal
    ) -> Dict[str, Any]:
        """Calculate optimization potential for the deal"""
        try:
            potential = {
                "upsell_potential": deal.deal_value * 0.3,
                "cross_sell_potential": deal.deal_value * 0.2,
                "pricing_optimization": deal.deal_value * 0.15,
                "total_potential": deal.deal_value * 0.65
            }
            
            return potential
            
        except Exception as e:
            logger.error(f"Failed to calculate optimization potential: {e}")
            return {}
    
    async def _calculate_total_potential_value(
        self,
        deal: Deal,
        upsell_opportunities: List[Dict[str, Any]],
        cross_sell_opportunities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate total potential value including upsells and cross-sells"""
        try:
            upsell_value = sum([opp["value"] for opp in upsell_opportunities])
            cross_sell_value = sum([opp["value"] for opp in cross_sell_opportunities])
            
            total_potential = deal.deal_value + upsell_value + cross_sell_value
            
            return {
                "current_value": deal.deal_value,
                "upsell_potential": upsell_value,
                "cross_sell_potential": cross_sell_value,
                "total_potential": total_potential,
                "growth_percentage": ((total_potential - deal.deal_value) / deal.deal_value) * 100
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate total potential value: {e}")
            return {}
    
    # Additional helper methods for playbook generation
    async def _generate_deal_summary(self, deal: Deal, db: Session) -> Dict[str, Any]:
        """Generate deal summary for playbook"""
        return {
            "deal_id": deal.id,
            "deal_name": deal.deal_name,
            "value": deal.deal_value,
            "stage": deal.sales_stage.value,
            "probability": deal.probability,
            "expected_close": deal.expected_close_date.isoformat() if deal.expected_close_date else None
        }
    
    async def _generate_customer_profile(self, deal: Deal, db: Session) -> Dict[str, Any]:
        """Generate customer profile for playbook"""
        lead = db.query(Lead).filter(Lead.id == deal.lead_id).first()
        return {
            "name": f"{lead.first_name} {lead.last_name}",
            "company": lead.company,
            "industry": lead.industry,
            "role": lead.job_title,
            "pain_points": lead.pain_points,
            "budget": lead.budget,
            "timeline": lead.timeline
        }
    
    async def _generate_value_proposition(self, deal: Deal, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate value proposition for playbook"""
        return {
            "primary_value": "Increased efficiency and cost savings",
            "secondary_value": "Improved customer experience",
            "roi_estimate": f"{(deal.deal_value * 3):,.0f}",
            "payback_period": "6 months"
        }
    
    async def _generate_closing_scripts(self, deal: Deal, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate closing scripts for playbook"""
        return [
            {
                "type": "opening",
                "script": "Thank you for your time today. I'm excited to present our final proposal that addresses all your requirements."
            },
            {
                "type": "value_demonstration",
                "script": "Based on your needs, our solution will deliver [specific value] and help you achieve [specific goals]."
            },
            {
                "type": "closing",
                "script": "Given the value we've discussed and the timeline you mentioned, I'd like to move forward with the agreement."
            }
        ]
    
    async def _generate_objection_handlers(self, deal: Deal, db: Session) -> List[Dict[str, Any]]:
        """Generate objection handlers for playbook"""
        return [
            {
                "objection": "Price concern",
                "response": "I understand budget is important. Let me show you how this investment pays for itself.",
                "evidence": "ROI calculator, case studies"
            },
            {
                "objection": "Timeline concern",
                "response": "I appreciate the need for careful consideration. Let's create a timeline that works for you.",
                "evidence": "Implementation plan, pilot program"
            }
        ]
    
    async def _generate_negotiation_tactics(self, deal: Deal, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate negotiation tactics for playbook"""
        return [
            {
                "tactic": "Value-based negotiation",
                "description": "Focus on value delivered rather than price",
                "implementation": "Present ROI analysis and case studies"
            },
            {
                "tactic": "Concession strategy",
                "description": "Plan concessions in advance",
                "implementation": "Identify what can be offered and what cannot"
            }
        ]
    
    async def _define_success_metrics(self, deal: Deal, config: Dict[str, Any]) -> Dict[str, Any]:
        """Define success metrics for playbook"""
        return {
            "primary_metric": "Deal closed at target value",
            "secondary_metrics": [
                "Close within timeline",
                "Maintain relationship quality",
                "Secure future opportunities"
            ],
            "target_value": deal.deal_value,
            "target_timeline": "30 days"
        }
    
    # Additional helper methods for progress tracking
    async def _analyze_closing_progress(self, deal: Deal, progress_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Analyze closing progress"""
        return {
            "current_stage": deal.sales_stage.value,
            "probability_change": 0,
            "milestones_completed": progress_data.get("milestones_completed", []),
            "next_milestone": "Final decision meeting",
            "days_to_close": (deal.expected_close_date - datetime.now()).days if deal.expected_close_date else None
        }
    
    async def _generate_next_steps(self, deal: Deal, progress_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate next steps based on progress"""
        return [
            {
                "step": "Schedule final decision meeting",
                "timeline": "Within 3 days",
                "priority": "High"
            },
            {
                "step": "Prepare final proposal",
                "timeline": "Before decision meeting",
                "priority": "High"
            },
            {
                "step": "Address any remaining objections",
                "timeline": "Immediate",
                "priority": "Medium"
            }
        ]
    
    # Additional helper methods for recommendations
    async def _generate_closing_recommendations_summary(self, deal: Deal, strategies: List[Dict[str, Any]], offers: List[Dict[str, Any]]) -> List[str]:
        """Generate summary of closing recommendations"""
        recommendations = []
        
        if strategies:
            recommendations.append(f"Focus on {strategies[0]['type']} strategy for highest impact")
        
        if offers:
            recommendations.append(f"Present {offers[0]['type']} offer to increase deal value")
        
        recommendations.append("Schedule follow-up meeting within 48 hours")
        recommendations.append("Prepare ROI analysis for next meeting")
        
        return recommendations
    
    async def _generate_objection_recommendations(self, deal: Deal, objection_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations for objection handling"""
        return [
            "Address objection within 24 hours",
            "Provide additional supporting materials",
            "Schedule technical discussion if needed",
            "Offer trial or pilot program"
        ]
    
    async def _generate_progress_recommendations(self, deal: Deal, progress_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on progress"""
        recommendations = []
        
        if progress_analysis.get("probability_change", 0) < 0:
            recommendations.append("Address recent setbacks immediately")
        
        if progress_analysis.get("days_to_close", 0) < 7:
            recommendations.append("Accelerate closing activities")
        
        recommendations.append("Maintain regular communication with customer")
        recommendations.append("Prepare for final decision meeting")
        
        return recommendations

    async def _analyze_deal_health(self, deal_id: str, brand_id: str) -> Dict[str, Any]:
        """Analyze the health and status of a deal"""
        try:
            async with get_eric_database() as db:
                # Get deal information
                deal_query = select(Deal).where(
                    and_(
                        Deal.id == deal_id,
                        Deal.brand_id == brand_id
                    )
                )
                deal_result = await db.execute(deal_query)
                deal = deal_result.scalar_one_or_none()
                
                if not deal:
                    return {
                        "deal_id": deal_id,
                        "health_score": 0,
                        "status": "not_found",
                        "risk_factors": ["Deal not found"],
                        "recommendations": ["Verify deal exists"]
                    }
                
                # Get deal activities
                activities_query = select(SalesActivity).where(
                    SalesActivity.deal_id == deal_id
                ).order_by(SalesActivity.created_at.desc())
                
                activities_result = await db.execute(activities_query)
                activities = activities_result.scalars().all()
                
                # Calculate health metrics
                total_activities = len(activities)
                recent_activities = [a for a in activities if a.created_at >= datetime.utcnow() - timedelta(days=7)]
                recent_activity_count = len(recent_activities)
                
                # Calculate days since last activity
                days_since_last_activity = 0
                if activities:
                    last_activity = max(a.created_at for a in activities)
                    days_since_last_activity = (datetime.utcnow() - last_activity).days
                
                # Calculate deal age
                deal_age_days = 0
                if deal.created_at:
                    deal_age_days = (datetime.utcnow() - deal.created_at).days
                
                # Calculate health score (0-100)
                health_score = 100
                
                # Deduct points for inactivity
                if days_since_last_activity > 14:
                    health_score -= 30
                elif days_since_last_activity > 7:
                    health_score -= 15
                
                # Deduct points for long deal cycles
                if deal_age_days > 90:
                    health_score -= 20
                elif deal_age_days > 60:
                    health_score -= 10
                
                # Add points for recent activity
                if recent_activity_count > 3:
                    health_score += 10
                elif recent_activity_count > 0:
                    health_score += 5
                
                # Ensure score is within bounds
                health_score = max(0, min(100, health_score))
                
                # Determine health status
                if health_score >= 80:
                    status = "excellent"
                elif health_score >= 60:
                    status = "good"
                elif health_score >= 40:
                    status = "fair"
                else:
                    status = "poor"
                
                # Identify risk factors
                risk_factors = []
                if days_since_last_activity > 14:
                    risk_factors.append("No recent activity")
                if deal_age_days > 90:
                    risk_factors.append("Long deal cycle")
                if deal.probability < 0.3:
                    risk_factors.append("Low probability")
                if deal.expected_close_date and deal.expected_close_date < datetime.utcnow():
                    risk_factors.append("Past expected close date")
                
                # Generate recommendations
                recommendations = []
                if days_since_last_activity > 7:
                    recommendations.append("Schedule follow-up activity")
                if deal.probability < 0.5:
                    recommendations.append("Increase deal probability through engagement")
                if not deal.expected_close_date:
                    recommendations.append("Set expected close date")
                
                return {
                    "deal_id": deal_id,
                    "deal_name": deal.deal_name,
                    "health_score": health_score,
                    "status": status,
                    "deal_value": deal.deal_value,
                    "probability": deal.probability,
                    "sales_stage": deal.sales_stage.value if deal.sales_stage else None,
                    "total_activities": total_activities,
                    "recent_activities": recent_activity_count,
                    "days_since_last_activity": days_since_last_activity,
                    "deal_age_days": deal_age_days,
                    "risk_factors": risk_factors,
                    "recommendations": recommendations,
                    "last_activity_date": last_activity if activities else None,
                    "analysis_date": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error analyzing deal health: {e}")
            return {
                "deal_id": deal_id,
                "health_score": 0,
                "status": "error",
                "risk_factors": ["Analysis error"],
                "recommendations": ["Contact support"]
            }
