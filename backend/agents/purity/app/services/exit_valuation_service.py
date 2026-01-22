from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import PurityBusinessIdea, PurityExitValuation, PurityBusinessModel
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class ExitValuationService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def estimate_business_valuation(
        self,
        db: AsyncSession,
        business_idea_id: int,
        current_revenue: float,
        growth_rate: float,
        profit_margins: float,
        market_conditions: Dict[str, Any],
        valuation_methods: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(PurityBusinessIdea).where(PurityBusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"business_valuation:{business_idea_id}:{current_revenue}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_valuation_estimate_prompt(
                business_idea, current_revenue, growth_rate, profit_margins, market_conditions, valuation_methods
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with business valuation. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            valuation_data = json.loads(ai_response)
            
            business_valuation = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "current_revenue": current_revenue,
                "growth_rate": growth_rate,
                "profit_margins": profit_margins,
                "market_conditions": market_conditions,
                "valuation_methods": valuation_methods,
                "valuation_results": valuation_data.get("valuation_results", {}),
                "valuation_factors": valuation_data.get("valuation_factors", {}),
                "comparative_analysis": valuation_data.get("comparative_analysis", {}),
                "risk_assessment": valuation_data.get("risk_assessment", {}),
                "valuation_range": valuation_data.get("valuation_range", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(valuation_data), expire=3600)
            await self.event_bus.publish("purity.business_valuation_estimated", {
                "business_idea_id": business_idea_id,
                "current_revenue": current_revenue,
                "valuation_range": valuation_data.get("valuation_range", {}),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return business_valuation
            
        except Exception as e:
            raise e
    
    async def plan_exit_strategy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        exit_timeline: str,
        exit_type: str,
        target_buyers: List[str],
        exit_goals: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(PurityBusinessIdea).where(PurityBusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_exit_strategy_prompt(
                business_idea, exit_timeline, exit_type, target_buyers, exit_goals
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with business valuation. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            strategy_data = json.loads(ai_response)
            
            exit_strategy = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "exit_timeline": exit_timeline,
                "exit_type": exit_type,
                "target_buyers": target_buyers,
                "exit_goals": exit_goals,
                "exit_roadmap": strategy_data.get("exit_roadmap", {}),
                "preparation_activities": strategy_data.get("preparation_activities", []),
                "valuation_optimization": strategy_data.get("valuation_optimization", {}),
                "deal_structure": strategy_data.get("deal_structure", {}),
                "risk_mitigation": strategy_data.get("risk_mitigation", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.exit_strategy_planned", {
                "business_idea_id": business_idea_id,
                "exit_timeline": exit_timeline,
                "exit_type": exit_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return exit_strategy
            
        except Exception as e:
            raise e
    
    async def analyze_exit_scenarios(
        self,
        db: AsyncSession,
        business_idea_id: int,
        exit_scenarios: List[str],
        market_conditions: Dict[str, Any],
        timing_factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(PurityBusinessIdea).where(PurityBusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_exit_scenarios_prompt(
                business_idea, exit_scenarios, market_conditions, timing_factors
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with business valuation. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            scenarios_data = json.loads(ai_response)
            
            exit_scenarios_analysis = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "exit_scenarios": exit_scenarios,
                "market_conditions": market_conditions,
                "timing_factors": timing_factors,
                "scenario_analysis": scenarios_data.get("scenario_analysis", {}),
                "valuation_impact": scenarios_data.get("valuation_impact", {}),
                "timing_recommendations": scenarios_data.get("timing_recommendations", {}),
                "market_opportunities": scenarios_data.get("market_opportunities", []),
                "optimal_exit_timing": scenarios_data.get("optimal_exit_timing", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.exit_scenarios_analyzed", {
                "business_idea_id": business_idea_id,
                "exit_scenarios": exit_scenarios,
                "optimal_timing": scenarios_data.get("optimal_exit_timing", {}),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return exit_scenarios_analysis
            
        except Exception as e:
            raise e
    
    def _create_valuation_estimate_prompt(
        self,
        business_idea: PurityBusinessIdea,
        current_revenue: float,
        growth_rate: float,
        profit_margins: float,
        market_conditions: Dict[str, Any],
        valuation_methods: List[str]
    ) -> str:
        return f"""
        Estimate business valuation for:
        - Business Idea: {business_idea.description}
        - Current Revenue: ${current_revenue:,.2f}
        - Growth Rate: {growth_rate}%
        - Profit Margins: {profit_margins}%
        - Market Conditions: {market_conditions}
        - Valuation Methods: {', '.join(valuation_methods)}
        
        Provide comprehensive business valuation including:
        1. Valuation results
        2. Valuation factors
        3. Comparative analysis
        4. Risk assessment
        5. Valuation range
        
        Return the response as a JSON object with the following structure:
        {{
            "valuation_results": {{
                "discounted_cash_flow": 2500000.0,
                "comparable_company_analysis": 2800000.0,
                "precedent_transactions": 2200000.0,
                "asset_based_valuation": 1800000.0,
                "weighted_average": 2325000.0
            }},
            "valuation_factors": {{
                "financial_performance": "Financial performance assessment",
                "market_position": "Market position analysis",
                "growth_potential": "Growth potential evaluation",
                "competitive_advantages": "Competitive advantages",
                "risk_factors": "Risk factors affecting valuation"
            }},
            "comparative_analysis": {{
                "industry_multiples": "Industry multiple analysis",
                "peer_comparison": "Peer company comparison",
                "market_trends": "Market trend analysis",
                "valuation_premiums": "Valuation premium factors",
                "discount_factors": "Discount factors applied"
            }},
            "risk_assessment": {{
                "market_risks": ["Risk 1", "Risk 2"],
                "operational_risks": ["Risk 1", "Risk 2"],
                "financial_risks": ["Risk 1", "Risk 2"],
                "regulatory_risks": ["Risk 1", "Risk 2"],
                "risk_adjustments": "Risk adjustments to valuation"
            }},
            "valuation_range": {{
                "low_end": 2000000.0,
                "mid_range": 2325000.0,
                "high_end": 2800000.0,
                "confidence_level": "High/Medium/Low",
                "valuation_notes": "Valuation range notes"
            }}
        }}
        """
    
    def _create_exit_strategy_prompt(
        self,
        business_idea: PurityBusinessIdea,
        exit_timeline: str,
        exit_type: str,
        target_buyers: List[str],
        exit_goals: List[str]
    ) -> str:
        return f"""
        Plan exit strategy for:
        - Business Idea: {business_idea.description}
        - Exit Timeline: {exit_timeline}
        - Exit Type: {exit_type}
        - Target Buyers: {', '.join(target_buyers)}
        - Exit Goals: {', '.join(exit_goals)}
        
        Provide comprehensive exit strategy including:
        1. Exit roadmap
        2. Preparation activities
        3. Valuation optimization
        4. Deal structure
        5. Risk mitigation
        
        Return the response as a JSON object with the following structure:
        {{
            "exit_roadmap": {{
                "phase_1": {{
                    "duration": "6 months",
                    "activities": ["Activity 1", "Activity 2"],
                    "objectives": ["Objective 1", "Objective 2"],
                    "success_metrics": ["Metric 1", "Metric 2"]
                }},
                "phase_2": {{
                    "duration": "12 months",
                    "activities": ["Activity 1", "Activity 2"],
                    "objectives": ["Objective 1", "Objective 2"],
                    "success_metrics": ["Metric 1", "Metric 2"]
                }}
            }},
            "preparation_activities": [
                "Activity 1: Financial statement preparation",
                "Activity 2: Legal documentation review",
                "Activity 3: Operational improvements",
                "Activity 4: Market positioning enhancement",
                "Activity 5: Management team development"
            ],
            "valuation_optimization": {{
                "financial_optimization": "Financial optimization strategies",
                "operational_improvements": "Operational improvement opportunities",
                "market_positioning": "Market positioning strategies",
                "growth_acceleration": "Growth acceleration tactics",
                "risk_reduction": "Risk reduction measures"
            }},
            "deal_structure": {{
                "deal_type": "Deal structure type",
                "payment_terms": "Payment terms structure",
                "earn_out_provisions": "Earn-out provisions",
                "retention_agreements": "Retention agreements",
                "transition_period": "Transition period planning"
            }},
            "risk_mitigation": [
                "Risk 1: Market timing risk mitigation",
                "Risk 2: Valuation risk mitigation",
                "Risk 3: Deal execution risk mitigation",
                "Risk 4: Post-transaction risk mitigation",
                "Risk 5: Regulatory risk mitigation"
            ]
        }}
        """
    
    def _create_exit_scenarios_prompt(
        self,
        business_idea: PurityBusinessIdea,
        exit_scenarios: List[str],
        market_conditions: Dict[str, Any],
        timing_factors: Dict[str, Any]
    ) -> str:
        return f"""
        Analyze exit scenarios for:
        - Business Idea: {business_idea.description}
        - Exit Scenarios: {', '.join(exit_scenarios)}
        - Market Conditions: {market_conditions}
        - Timing Factors: {timing_factors}
        
        Provide comprehensive exit scenario analysis including:
        1. Scenario analysis
        2. Valuation impact
        3. Timing recommendations
        4. Market opportunities
        5. Optimal exit timing
        
        Return the response as a JSON object with the following structure:
        {{
            "scenario_analysis": {{
                "scenario_1": {{
                    "description": "Scenario description",
                    "probability": "Probability assessment",
                    "valuation_impact": "Valuation impact",
                    "timeline": "Expected timeline",
                    "risks": ["Risk 1", "Risk 2"]
                }},
                "scenario_2": {{
                    "description": "Scenario description",
                    "probability": "Probability assessment",
                    "valuation_impact": "Valuation impact",
                    "timeline": "Expected timeline",
                    "risks": ["Risk 1", "Risk 2"]
                }}
            }},
            "valuation_impact": {{
                "bull_market_scenario": "Bull market valuation impact",
                "bear_market_scenario": "Bear market valuation impact",
                "stable_market_scenario": "Stable market valuation impact",
                "volatile_market_scenario": "Volatile market valuation impact"
            }},
            "timing_recommendations": {{
                "optimal_timing": "Optimal exit timing",
                "market_cycles": "Market cycle considerations",
                "seasonal_factors": "Seasonal timing factors",
                "competitive_landscape": "Competitive landscape timing",
                "regulatory_environment": "Regulatory timing considerations"
            }},
            "market_opportunities": [
                "Opportunity 1: Strategic buyer interest",
                "Opportunity 2: Market consolidation",
                "Opportunity 3: Industry growth phase",
                "Opportunity 4: Technology disruption",
                "Opportunity 5: Regulatory changes"
            ],
            "optimal_exit_timing": {{
                "recommended_timing": "Recommended exit timing",
                "rationale": "Timing rationale",
                "preparation_period": "Required preparation period",
                "market_conditions": "Expected market conditions",
                "valuation_expectations": "Expected valuation range"
            }}
        }}
        """
