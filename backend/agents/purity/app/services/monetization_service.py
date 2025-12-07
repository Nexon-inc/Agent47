from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, MonetizationStrategy, BusinessModel, CustomerAvatar
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.event_bus.kafka_manager import KafkaManager
from backend.core.cache.redis_manager import RedisManager

class MonetizationService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def create_monetization_strategy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        target_audience: str,
        business_model: str,
        revenue_goals: List[str],
        pricing_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"monetization_strategy:{business_idea_id}:{business_model}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_monetization_strategy_prompt(
                business_idea, target_audience, business_model, revenue_goals, pricing_preferences
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with business monetization. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            strategy_data = json.loads(ai_response)
            
            monetization_strategy = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "target_audience": target_audience,
                "business_model": business_model,
                "revenue_goals": revenue_goals,
                "pricing_preferences": pricing_preferences,
                "revenue_models": strategy_data.get("revenue_models", []),
                "pricing_strategy": strategy_data.get("pricing_strategy", {}),
                "monetization_channels": strategy_data.get("monetization_channels", []),
                "revenue_projections": strategy_data.get("revenue_projections", {}),
                "implementation_plan": strategy_data.get("implementation_plan", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(strategy_data), expire=3600)
            await self.event_bus.publish("purity.monetization_strategy_created", {
                "business_idea_id": business_idea_id,
                "business_model": business_model,
                "revenue_goals": revenue_goals,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return monetization_strategy
            
        except Exception as e:
            raise e
    
    async def optimize_pricing_strategy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        current_pricing: Dict[str, Any],
        market_analysis: Dict[str, Any],
        customer_feedback: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_pricing_optimization_prompt(
                business_idea, current_pricing, market_analysis, customer_feedback
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with business monetization. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            optimization_data = json.loads(ai_response)
            
            pricing_optimization = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "current_pricing": current_pricing,
                "market_analysis": market_analysis,
                "customer_feedback": customer_feedback,
                "optimized_pricing": optimization_data.get("optimized_pricing", {}),
                "pricing_tiers": optimization_data.get("pricing_tiers", []),
                "pricing_psychology": optimization_data.get("pricing_psychology", {}),
                "competitive_analysis": optimization_data.get("competitive_analysis", {}),
                "revenue_impact": optimization_data.get("revenue_impact", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.pricing_strategy_optimized", {
                "business_idea_id": business_idea_id,
                "revenue_impact": optimization_data.get("revenue_impact", {}),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return pricing_optimization
            
        except Exception as e:
            raise e
    
    async def analyze_revenue_models(
        self,
        db: AsyncSession,
        business_idea_id: int,
        business_type: str,
        target_market: str,
        scalability_requirements: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_revenue_model_analysis_prompt(
                business_idea, business_type, target_market, scalability_requirements
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with business monetization. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            analysis_data = json.loads(ai_response)
            
            revenue_model_analysis = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "business_type": business_type,
                "target_market": target_market,
                "scalability_requirements": scalability_requirements,
                "recommended_models": analysis_data.get("recommended_models", []),
                "model_comparison": analysis_data.get("model_comparison", {}),
                "implementation_complexity": analysis_data.get("implementation_complexity", {}),
                "scalability_analysis": analysis_data.get("scalability_analysis", {}),
                "risk_assessment": analysis_data.get("risk_assessment", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.revenue_models_analyzed", {
                "business_idea_id": business_idea_id,
                "business_type": business_type,
                "recommended_models_count": len(analysis_data.get("recommended_models", [])),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return revenue_model_analysis
            
        except Exception as e:
            raise e
    
    async def create_subscription_model(
        self,
        db: AsyncSession,
        business_idea_id: int,
        subscription_type: str,
        pricing_tiers: List[str],
        billing_cycle: str,
        value_proposition: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_subscription_model_prompt(
                business_idea, subscription_type, pricing_tiers, billing_cycle, value_proposition
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with business monetization. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            subscription_data = json.loads(ai_response)
            
            subscription_model = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "subscription_type": subscription_type,
                "pricing_tiers": pricing_tiers,
                "billing_cycle": billing_cycle,
                "value_proposition": value_proposition,
                "tier_structure": subscription_data.get("tier_structure", []),
                "pricing_strategy": subscription_data.get("pricing_strategy", {}),
                "retention_tactics": subscription_data.get("retention_tactics", []),
                "upgrade_paths": subscription_data.get("upgrade_paths", []),
                "churn_prevention": subscription_data.get("churn_prevention", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.subscription_model_created", {
                "business_idea_id": business_idea_id,
                "subscription_type": subscription_type,
                "pricing_tiers_count": len(pricing_tiers),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return subscription_model
            
        except Exception as e:
            raise e
    
    def _create_monetization_strategy_prompt(
        self,
        business_idea: BusinessIdea,
        target_audience: str,
        business_model: str,
        revenue_goals: List[str],
        pricing_preferences: Dict[str, Any]
    ) -> str:
        return f"""
        Create monetization strategy for:
        - Business Idea: {business_idea.description}
        - Target Audience: {target_audience}
        - Business Model: {business_model}
        - Revenue Goals: {', '.join(revenue_goals)}
        - Pricing Preferences: {pricing_preferences}
        
        Develop comprehensive monetization strategy including:
        1. Revenue models
        2. Pricing strategy
        3. Monetization channels
        4. Revenue projections
        5. Implementation plan
        
        Return the response as a JSON object with the following structure:
        {{
            "revenue_models": [
                {{
                    "model_name": "Model name",
                    "description": "Model description",
                    "pros": ["Pro 1", "Pro 2"],
                    "cons": ["Con 1", "Con 2"],
                    "implementation_complexity": "High/Medium/Low",
                    "revenue_potential": "Revenue potential estimate"
                }}
            ],
            "pricing_strategy": {{
                "pricing_model": "Pricing model type",
                "price_points": ["Point 1", "Point 2"],
                "pricing_psychology": "Pricing psychology factors",
                "competitive_positioning": "Competitive positioning"
            }},
            "monetization_channels": [
                {{
                    "channel_name": "Channel name",
                    "revenue_potential": "Revenue potential",
                    "implementation_cost": "Implementation cost",
                    "timeline": "Implementation timeline"
                }}
            ],
            "revenue_projections": {{
                "year_1": 100000,
                "year_2": 250000,
                "year_3": 500000,
                "growth_rate": 150.0
            }},
            "implementation_plan": {{
                "phase_1": {{
                    "duration": "3 months",
                    "activities": ["Activity 1", "Activity 2"],
                    "milestones": ["Milestone 1", "Milestone 2"]
                }},
                "phase_2": {{
                    "duration": "6 months",
                    "activities": ["Activity 1", "Activity 2"],
                    "milestones": ["Milestone 1", "Milestone 2"]
                }}
            }}
        }}
        """
    
    def _create_pricing_optimization_prompt(
        self,
        business_idea: BusinessIdea,
        current_pricing: Dict[str, Any],
        market_analysis: Dict[str, Any],
        customer_feedback: List[str]
    ) -> str:
        return f"""
        Optimize pricing strategy for:
        - Business Idea: {business_idea.description}
        - Current Pricing: {current_pricing}
        - Market Analysis: {market_analysis}
        - Customer Feedback: {', '.join(customer_feedback)}
        
        Provide comprehensive pricing optimization including:
        1. Optimized pricing
        2. Pricing tiers
        3. Pricing psychology
        4. Competitive analysis
        5. Revenue impact
        
        Return the response as a JSON object with the following structure:
        {{
            "optimized_pricing": {{
                "base_price": 99.0,
                "premium_price": 199.0,
                "enterprise_price": 499.0,
                "pricing_justification": "Pricing justification"
            }},
            "pricing_tiers": [
                {{
                    "tier_name": "Basic",
                    "price": 99.0,
                    "features": ["Feature 1", "Feature 2"],
                    "target_audience": "Target audience"
                }}
            ],
            "pricing_psychology": {{
                "anchoring": "Anchoring strategy",
                "decoy_pricing": "Decoy pricing approach",
                "bundling": "Bundling strategy"
            }},
            "competitive_analysis": {{
                "competitor_pricing": "Competitor pricing analysis",
                "price_positioning": "Price positioning strategy",
                "differentiation": "Price differentiation approach"
            }},
            "revenue_impact": {{
                "projected_increase": "Projected revenue increase",
                "conversion_impact": "Expected conversion impact",
                "customer_lifetime_value": "Expected CLV impact"
            }}
        }}
        """
    
    def _create_revenue_model_analysis_prompt(
        self,
        business_idea: BusinessIdea,
        business_type: str,
        target_market: str,
        scalability_requirements: List[str]
    ) -> str:
        return f"""
        Analyze revenue models for:
        - Business Idea: {business_idea.description}
        - Business Type: {business_type}
        - Target Market: {target_market}
        - Scalability Requirements: {', '.join(scalability_requirements)}
        
        Provide comprehensive revenue model analysis including:
        1. Recommended models
        2. Model comparison
        3. Implementation complexity
        4. Scalability analysis
        5. Risk assessment
        
        Return the response as a JSON object with the following structure:
        {{
            "recommended_models": [
                {{
                    "model_name": "Model name",
                    "description": "Model description",
                    "suitability_score": 85.5,
                    "revenue_potential": "Revenue potential",
                    "scalability": "Scalability assessment"
                }}
            ],
            "model_comparison": {{
                "subscription_vs_one_time": "Comparison analysis",
                "freemium_vs_premium": "Comparison analysis",
                "marketplace_vs_direct": "Comparison analysis"
            }},
            "implementation_complexity": {{
                "technical_requirements": "Technical requirements",
                "operational_requirements": "Operational requirements",
                "timeline": "Implementation timeline"
            }},
            "scalability_analysis": {{
                "growth_potential": "Growth potential assessment",
                "resource_requirements": "Resource requirements",
                "bottlenecks": "Potential bottlenecks"
            }},
            "risk_assessment": [
                "Risk 1: Market adoption risk",
                "Risk 2: Competition risk",
                "Risk 3: Technology risk"
            ]
        }}
        """
    
    def _create_subscription_model_prompt(
        self,
        business_idea: BusinessIdea,
        subscription_type: str,
        pricing_tiers: List[str],
        billing_cycle: str,
        value_proposition: str
    ) -> str:
        return f"""
        Create subscription model for:
        - Business Idea: {business_idea.description}
        - Subscription Type: {subscription_type}
        - Pricing Tiers: {', '.join(pricing_tiers)}
        - Billing Cycle: {billing_cycle}
        - Value Proposition: {value_proposition}
        
        Develop comprehensive subscription model including:
        1. Tier structure
        2. Pricing strategy
        3. Retention tactics
        4. Upgrade paths
        5. Churn prevention
        
        Return the response as a JSON object with the following structure:
        {{
            "tier_structure": [
                {{
                    "tier_name": "Tier name",
                    "price": 99.0,
                    "billing_cycle": "Monthly/Annual",
                    "features": ["Feature 1", "Feature 2"],
                    "target_audience": "Target audience"
                }}
            ],
            "pricing_strategy": {{
                "introductory_pricing": "Introductory pricing strategy",
                "annual_discount": "Annual discount strategy",
                "volume_discounts": "Volume discount strategy"
            }},
            "retention_tactics": [
                "Tactic 1: Value demonstration",
                "Tactic 2: Exclusive content",
                "Tactic 3: Community access"
            ],
            "upgrade_paths": [
                {{
                    "from_tier": "Current tier",
                    "to_tier": "Upgrade tier",
                    "trigger": "Upgrade trigger",
                    "incentive": "Upgrade incentive"
                }}
            ],
            "churn_prevention": {{
                "early_warning_signals": ["Signal 1", "Signal 2"],
                "intervention_strategies": ["Strategy 1", "Strategy 2"],
                "win_back_campaigns": ["Campaign 1", "Campaign 2"]
            }}
        }}
        """
