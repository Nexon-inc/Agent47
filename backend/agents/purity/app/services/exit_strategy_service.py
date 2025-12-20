from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, ExitStrategy, BusinessModel, FinancialForecast
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class ExitStrategyService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def create_exit_strategy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        exit_type: str,
        target_timeline_years: int,
        current_valuation: float,
        growth_rate: float,
        industry_multiplier: float
    ) -> ExitStrategy:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"exit_strategy:{business_idea_id}:{exit_type}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_exit_strategy_prompt(
                business_idea, exit_type, target_timeline_years, current_valuation,
                growth_rate, industry_multiplier
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with exit strategies. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            strategy_data = json.loads(ai_response)
            
            exit_strategy = ExitStrategy(
                business_idea_id=business_idea_id,
                exit_type=exit_type,
                target_timeline_years=target_timeline_years,
                current_valuation=current_valuation,
                growth_rate=growth_rate,
                industry_multiplier=industry_multiplier,
                exit_valuation=json.dumps(strategy_data.get("exit_valuation", {})),
                exit_timeline=json.dumps(strategy_data.get("exit_timeline", [])),
                preparation_requirements=json.dumps(strategy_data.get("preparation_requirements", [])),
                potential_buyers=json.dumps(strategy_data.get("potential_buyers", [])),
                risk_factors=json.dumps(strategy_data.get("risk_factors", [])),
                success_probability=strategy_data.get("success_probability", 0.0)
            )
            
            db.add(exit_strategy)
            await db.commit()
            await db.refresh(exit_strategy)
            
            await self.redis_manager.set(cache_key, json.dumps(strategy_data), expire=3600)
            await self.event_bus.publish("purity.exit_strategy_created", {
                "business_idea_id": business_idea_id,
                "exit_type": exit_type,
                "target_timeline_years": target_timeline_years,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return exit_strategy
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def estimate_exit_valuation(
        self,
        db: AsyncSession,
        exit_strategy_id: int,
        valuation_methods: List[str],
        market_conditions: str
    ) -> Dict[str, Any]:
        try:
            strategy_result = await db.execute(
                select(ExitStrategy).where(ExitStrategy.id == exit_strategy_id)
            )
            exit_strategy = strategy_result.scalar_one_or_none()
            if not exit_strategy:
                raise ValueError("Exit strategy not found")
            
            prompt = self._create_valuation_estimation_prompt(
                exit_strategy, valuation_methods, market_conditions
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with exit strategies. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            valuation_data = json.loads(ai_response)
            
            valuation_estimate = {
                "id": exit_strategy_id,
                "exit_strategy_id": exit_strategy_id,
                "valuation_methods": valuation_methods,
                "market_conditions": market_conditions,
                "dcf_valuation": valuation_data.get("dcf_valuation", 0.0),
                "comparable_valuation": valuation_data.get("comparable_valuation", 0.0),
                "asset_based_valuation": valuation_data.get("asset_based_valuation", 0.0),
                "weighted_average_valuation": valuation_data.get("weighted_average_valuation", 0.0),
                "valuation_range": valuation_data.get("valuation_range", {}),
                "key_drivers": valuation_data.get("key_drivers", []),
                "sensitivity_analysis": valuation_data.get("sensitivity_analysis", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.exit_valuation_estimated", {
                "exit_strategy_id": exit_strategy_id,
                "weighted_average_valuation": valuation_estimate["weighted_average_valuation"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return valuation_estimate
            
        except Exception as e:
            raise e
    
    async def create_exit_timeline(
        self,
        db: AsyncSession,
        exit_strategy_id: int,
        target_exit_date: datetime,
        preparation_activities: List[str]
    ) -> Dict[str, Any]:
        try:
            strategy_result = await db.execute(
                select(ExitStrategy).where(ExitStrategy.id == exit_strategy_id)
            )
            exit_strategy = strategy_result.scalar_one_or_none()
            if not exit_strategy:
                raise ValueError("Exit strategy not found")
            
            prompt = self._create_exit_timeline_prompt(
                exit_strategy, target_exit_date, preparation_activities
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with exit strategies. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            timeline_data = json.loads(ai_response)
            
            exit_timeline = {
                "id": exit_strategy_id,
                "exit_strategy_id": exit_strategy_id,
                "target_exit_date": target_exit_date,
                "preparation_activities": preparation_activities,
                "detailed_timeline": timeline_data.get("detailed_timeline", []),
                "milestone_dates": timeline_data.get("milestone_dates", {}),
                "resource_requirements": timeline_data.get("resource_requirements", {}),
                "risk_mitigation_plan": timeline_data.get("risk_mitigation_plan", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.exit_timeline_created", {
                "exit_strategy_id": exit_strategy_id,
                "target_exit_date": target_exit_date.isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return exit_timeline
            
        except Exception as e:
            raise e
    
    async def identify_potential_buyers(
        self,
        db: AsyncSession,
        exit_strategy_id: int,
        buyer_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            strategy_result = await db.execute(
                select(ExitStrategy).where(ExitStrategy.id == exit_strategy_id)
            )
            exit_strategy = strategy_result.scalar_one_or_none()
            if not exit_strategy:
                raise ValueError("Exit strategy not found")
            
            prompt = self._create_buyer_identification_prompt(
                exit_strategy, buyer_criteria
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with exit strategies. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            buyers_data = json.loads(ai_response)
            
            potential_buyers = {
                "id": exit_strategy_id,
                "exit_strategy_id": exit_strategy_id,
                "buyer_criteria": buyer_criteria,
                "strategic_buyers": buyers_data.get("strategic_buyers", []),
                "financial_buyers": buyers_data.get("financial_buyers", []),
                "buyer_profiles": buyers_data.get("buyer_profiles", []),
                "contact_strategies": buyers_data.get("contact_strategies", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.potential_buyers_identified", {
                "exit_strategy_id": exit_strategy_id,
                "buyer_count": len(buyers_data.get("strategic_buyers", []) + buyers_data.get("financial_buyers", [])),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return potential_buyers
            
        except Exception as e:
            raise e
    
    def _create_exit_strategy_prompt(
        self,
        business_idea: BusinessIdea,
        exit_type: str,
        target_timeline_years: int,
        current_valuation: float,
        growth_rate: float,
        industry_multiplier: float
    ) -> str:
        return f"""
        Create a comprehensive exit strategy for:
        - Business Idea: {business_idea.description}
        - Exit Type: {exit_type}
        - Target Timeline: {target_timeline_years} years
        - Current Valuation: ${current_valuation:,.2f}
        - Growth Rate: {growth_rate}%
        - Industry Multiplier: {industry_multiplier}x
        
        Develop a complete exit strategy including:
        1. Exit valuation projections
        2. Exit timeline
        3. Preparation requirements
        4. Potential buyers
        5. Risk factors
        6. Success probability
        
        Return the response as a JSON object with the following structure:
        {{
            "exit_valuation": {{
                "year_1": 1000000,
                "year_2": 1500000,
                "year_3": 2250000,
                "target_exit_value": 3000000
            }},
            "exit_timeline": [
                {{
                    "year": 1,
                    "activities": ["Activity 1", "Activity 2"],
                    "milestones": ["Milestone 1"],
                    "preparation_phase": "Preparation phase description"
                }}
            ],
            "preparation_requirements": [
                "Requirement 1: Financial preparation",
                "Requirement 2: Legal preparation",
                "Requirement 3: Operational preparation"
            ],
            "potential_buyers": [
                {{
                    "type": "Strategic Buyer",
                    "name": "Potential Buyer Name",
                    "motivation": "Buyer motivation",
                    "valuation_multiplier": 3.5
                }}
            ],
            "risk_factors": [
                "Risk 1: Market conditions",
                "Risk 2: Competition",
                "Risk 3: Regulatory changes"
            ],
            "success_probability": 75.5
        }}
        """
    
    def _create_valuation_estimation_prompt(
        self,
        exit_strategy: ExitStrategy,
        valuation_methods: List[str],
        market_conditions: str
    ) -> str:
        return f"""
        Estimate exit valuation for:
        - Exit Type: {exit_strategy.exit_type}
        - Current Valuation: ${exit_strategy.current_valuation:,.2f}
        - Growth Rate: {exit_strategy.growth_rate}%
        - Industry Multiplier: {exit_strategy.industry_multiplier}x
        - Valuation Methods: {', '.join(valuation_methods)}
        - Market Conditions: {market_conditions}
        
        Calculate comprehensive valuation including:
        1. DCF valuation
        2. Comparable company valuation
        3. Asset-based valuation
        4. Weighted average valuation
        5. Valuation range
        6. Key drivers
        7. Sensitivity analysis
        
        Return the response as a JSON object with the following structure:
        {{
            "dcf_valuation": 2500000.0,
            "comparable_valuation": 2800000.0,
            "asset_based_valuation": 2000000.0,
            "weighted_average_valuation": 2600000.0,
            "valuation_range": {{
                "low": 2000000.0,
                "high": 3200000.0,
                "most_likely": 2600000.0
            }},
            "key_drivers": [
                "Driver 1: Revenue growth",
                "Driver 2: Profit margins",
                "Driver 3: Market position"
            ],
            "sensitivity_analysis": {{
                "growth_rate_impact": "High growth rate impact",
                "multiple_impact": "Multiple impact analysis",
                "market_condition_impact": "Market condition impact"
            }}
        }}
        """
    
    def _create_exit_timeline_prompt(
        self,
        exit_strategy: ExitStrategy,
        target_exit_date: datetime,
        preparation_activities: List[str]
    ) -> str:
        return f"""
        Create exit timeline for:
        - Exit Type: {exit_strategy.exit_type}
        - Target Exit Date: {target_exit_date.strftime('%Y-%m-%d')}
        - Preparation Activities: {', '.join(preparation_activities)}
        - Current Valuation: ${exit_strategy.current_valuation:,.2f}
        
        Develop comprehensive exit timeline including:
        1. Detailed timeline breakdown
        2. Milestone dates
        3. Resource requirements
        4. Risk mitigation plan
        
        Return the response as a JSON object with the following structure:
        {{
            "detailed_timeline": [
                {{
                    "phase": "Phase Name",
                    "duration": "Duration",
                    "activities": ["Activity 1", "Activity 2"],
                    "milestones": ["Milestone 1"],
                    "resources": ["Resource 1", "Resource 2"]
                }}
            ],
            "milestone_dates": {{
                "preparation_start": "2024-01-01",
                "valuation_complete": "2024-06-01",
                "buyer_identification": "2024-09-01",
                "exit_execution": "2024-12-01"
            }},
            "resource_requirements": {{
                "team_requirements": ["Role 1", "Role 2"],
                "external_consultants": ["Consultant 1", "Consultant 2"],
                "budget_requirements": "Budget breakdown"
            }},
            "risk_mitigation_plan": {{
                "identified_risks": ["Risk 1", "Risk 2"],
                "mitigation_strategies": ["Strategy 1", "Strategy 2"],
                "contingency_plans": ["Plan 1", "Plan 2"]
            }}
        }}
        """
    
    def _create_buyer_identification_prompt(
        self,
        exit_strategy: ExitStrategy,
        buyer_criteria: Dict[str, Any]
    ) -> str:
        return f"""
        Identify potential buyers for:
        - Exit Type: {exit_strategy.exit_type}
        - Current Valuation: ${exit_strategy.current_valuation:,.2f}
        - Industry Multiplier: {exit_strategy.industry_multiplier}x
        - Buyer Criteria: {buyer_criteria}
        
        Identify comprehensive buyer list including:
        1. Strategic buyers
        2. Financial buyers
        3. Buyer profiles
        4. Contact strategies
        
        Return the response as a JSON object with the following structure:
        {{
            "strategic_buyers": [
                {{
                    "name": "Strategic Buyer Name",
                    "industry": "Buyer Industry",
                    "motivation": "Strategic motivation",
                    "valuation_multiplier": 3.5,
                    "contact_info": "Contact information"
                }}
            ],
            "financial_buyers": [
                {{
                    "name": "Financial Buyer Name",
                    "type": "PE/VC/Other",
                    "investment_criteria": "Investment criteria",
                    "valuation_multiplier": 2.8,
                    "contact_info": "Contact information"
                }}
            ],
            "buyer_profiles": [
                {{
                    "profile_type": "Profile Type",
                    "characteristics": ["Characteristic 1", "Characteristic 2"],
                    "preferences": ["Preference 1", "Preference 2"]
                }}
            ],
            "contact_strategies": [
                {{
                    "buyer_type": "Buyer Type",
                    "approach": "Contact approach",
                    "timing": "Contact timing",
                    "messaging": "Key messaging points"
                }}
            ]
        }}
        """
