from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, BusinessModel, CustomerAvatar
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class CustomerRetentionService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def analyze_customer_churn(
        self,
        db: AsyncSession,
        business_idea_id: int,
        customer_data: Dict[str, Any],
        churn_indicators: List[str],
        retention_period: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"churn_analysis:{business_idea_id}:{retention_period}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_churn_analysis_prompt(
                business_idea, customer_data, churn_indicators, retention_period
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with customer retention. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            churn_data = json.loads(ai_response)
            
            churn_analysis = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "customer_data": customer_data,
                "churn_indicators": churn_indicators,
                "retention_period": retention_period,
                "churn_rate": churn_data.get("churn_rate", 0.0),
                "risk_segments": churn_data.get("risk_segments", []),
                "churn_reasons": churn_data.get("churn_reasons", []),
                "retention_opportunities": churn_data.get("retention_opportunities", []),
                "intervention_strategies": churn_data.get("intervention_strategies", []),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(churn_data), expire=3600)
            await self.event_bus.publish("purity.churn_analysis_completed", {
                "business_idea_id": business_idea_id,
                "churn_rate": churn_analysis["churn_rate"],
                "retention_period": retention_period,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return churn_analysis
            
        except Exception as e:
            raise e
    
    async def create_loyalty_program(
        self,
        db: AsyncSession,
        business_idea_id: int,
        program_type: str,
        target_customers: str,
        reward_structure: Dict[str, Any],
        program_duration: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_loyalty_program_prompt(
                business_idea, program_type, target_customers, reward_structure, program_duration
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with customer retention. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            loyalty_data = json.loads(ai_response)
            
            loyalty_program = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "program_type": program_type,
                "target_customers": target_customers,
                "reward_structure": reward_structure,
                "program_duration": program_duration,
                "program_structure": loyalty_data.get("program_structure", {}),
                "reward_tiers": loyalty_data.get("reward_tiers", []),
                "engagement_tactics": loyalty_data.get("engagement_tactics", []),
                "redemption_options": loyalty_data.get("redemption_options", []),
                "success_metrics": loyalty_data.get("success_metrics", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.loyalty_program_created", {
                "business_idea_id": business_idea_id,
                "program_type": program_type,
                "target_customers": target_customers,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return loyalty_program
            
        except Exception as e:
            raise e
    
    async def develop_retention_strategy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        current_retention_rate: float,
        target_retention_rate: float,
        customer_segments: List[str],
        retention_goals: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_retention_strategy_prompt(
                business_idea, current_retention_rate, target_retention_rate, customer_segments, retention_goals
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with customer retention. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            strategy_data = json.loads(ai_response)
            
            retention_strategy = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "current_retention_rate": current_retention_rate,
                "target_retention_rate": target_retention_rate,
                "customer_segments": customer_segments,
                "retention_goals": retention_goals,
                "strategy_components": strategy_data.get("strategy_components", []),
                "implementation_plan": strategy_data.get("implementation_plan", {}),
                "success_metrics": strategy_data.get("success_metrics", {}),
                "risk_mitigation": strategy_data.get("risk_mitigation", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.retention_strategy_developed", {
                "business_idea_id": business_idea_id,
                "current_retention_rate": current_retention_rate,
                "target_retention_rate": target_retention_rate,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return retention_strategy
            
        except Exception as e:
            raise e
    
    async def create_customer_engagement_plan(
        self,
        db: AsyncSession,
        business_idea_id: int,
        engagement_channels: List[str],
        engagement_frequency: str,
        content_types: List[str],
        personalization_level: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_engagement_plan_prompt(
                business_idea, engagement_channels, engagement_frequency, content_types, personalization_level
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with customer retention. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            engagement_data = json.loads(ai_response)
            
            engagement_plan = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "engagement_channels": engagement_channels,
                "engagement_frequency": engagement_frequency,
                "content_types": content_types,
                "personalization_level": personalization_level,
                "engagement_calendar": engagement_data.get("engagement_calendar", {}),
                "content_strategy": engagement_data.get("content_strategy", {}),
                "personalization_tactics": engagement_data.get("personalization_tactics", []),
                "engagement_metrics": engagement_data.get("engagement_metrics", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.engagement_plan_created", {
                "business_idea_id": business_idea_id,
                "engagement_channels": engagement_channels,
                "engagement_frequency": engagement_frequency,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return engagement_plan
            
        except Exception as e:
            raise e
    
    def _create_churn_analysis_prompt(
        self,
        business_idea: BusinessIdea,
        customer_data: Dict[str, Any],
        churn_indicators: List[str],
        retention_period: str
    ) -> str:
        return f"""
        Analyze customer churn for:
        - Business Idea: {business_idea.description}
        - Customer Data: {customer_data}
        - Churn Indicators: {', '.join(churn_indicators)}
        - Retention Period: {retention_period}
        
        Provide comprehensive churn analysis including:
        1. Churn rate calculation
        2. Risk segments identification
        3. Churn reasons analysis
        4. Retention opportunities
        5. Intervention strategies
        
        Return the response as a JSON object with the following structure:
        {{
            "churn_rate": 15.5,
            "risk_segments": [
                {{
                    "segment_name": "High-risk segment",
                    "risk_factors": ["Factor 1", "Factor 2"],
                    "intervention_priority": "High"
                }}
            ],
            "churn_reasons": [
                "Reason 1: Poor customer service",
                "Reason 2: High pricing",
                "Reason 3: Lack of features"
            ],
            "retention_opportunities": [
                "Opportunity 1: Improve onboarding",
                "Opportunity 2: Enhance customer support",
                "Opportunity 3: Add value features"
            ],
            "intervention_strategies": [
                "Strategy 1: Proactive outreach",
                "Strategy 2: Personalized offers",
                "Strategy 3: Feature education"
            ]
        }}
        """
    
    def _create_loyalty_program_prompt(
        self,
        business_idea: BusinessIdea,
        program_type: str,
        target_customers: str,
        reward_structure: Dict[str, Any],
        program_duration: str
    ) -> str:
        return f"""
        Create loyalty program for:
        - Business Idea: {business_idea.description}
        - Program Type: {program_type}
        - Target Customers: {target_customers}
        - Reward Structure: {reward_structure}
        - Program Duration: {program_duration}
        
        Develop comprehensive loyalty program including:
        1. Program structure
        2. Reward tiers
        3. Engagement tactics
        4. Redemption options
        5. Success metrics
        
        Return the response as a JSON object with the following structure:
        {{
            "program_structure": {{
                "tier_system": "Tier system description",
                "point_system": "Point system details",
                "qualification_criteria": "Qualification criteria"
            }},
            "reward_tiers": [
                {{
                    "tier_name": "Bronze",
                    "requirements": "Requirements",
                    "benefits": ["Benefit 1", "Benefit 2"],
                    "rewards": ["Reward 1", "Reward 2"]
                }}
            ],
            "engagement_tactics": [
                "Tactic 1: Gamification elements",
                "Tactic 2: Exclusive content",
                "Tactic 3: Early access"
            ],
            "redemption_options": [
                "Option 1: Discounts",
                "Option 2: Free products",
                "Option 3: Premium features"
            ],
            "success_metrics": {{
                "enrollment_rate": "Target enrollment rate",
                "engagement_rate": "Target engagement rate",
                "retention_impact": "Expected retention impact"
            }}
        }}
        """
    
    def _create_retention_strategy_prompt(
        self,
        business_idea: BusinessIdea,
        current_retention_rate: float,
        target_retention_rate: float,
        customer_segments: List[str],
        retention_goals: List[str]
    ) -> str:
        return f"""
        Develop retention strategy for:
        - Business Idea: {business_idea.description}
        - Current Retention Rate: {current_retention_rate}%
        - Target Retention Rate: {target_retention_rate}%
        - Customer Segments: {', '.join(customer_segments)}
        - Retention Goals: {', '.join(retention_goals)}
        
        Create comprehensive retention strategy including:
        1. Strategy components
        2. Implementation plan
        3. Success metrics
        4. Risk mitigation
        
        Return the response as a JSON object with the following structure:
        {{
            "strategy_components": [
                "Component 1: Customer onboarding optimization",
                "Component 2: Proactive support system",
                "Component 3: Value-added services"
            ],
            "implementation_plan": {{
                "phase_1": {{
                    "duration": "3 months",
                    "activities": ["Activity 1", "Activity 2"],
                    "success_criteria": "Success criteria"
                }},
                "phase_2": {{
                    "duration": "6 months",
                    "activities": ["Activity 1", "Activity 2"],
                    "success_criteria": "Success criteria"
                }}
            }},
            "success_metrics": {{
                "retention_rate_target": "Target retention rate",
                "customer_lifetime_value": "Expected CLV increase",
                "churn_reduction": "Expected churn reduction"
            }},
            "risk_mitigation": [
                "Risk 1: Implementation delays",
                "Risk 2: Customer resistance",
                "Risk 3: Resource constraints"
            ]
        }}
        """
    
    def _create_engagement_plan_prompt(
        self,
        business_idea: BusinessIdea,
        engagement_channels: List[str],
        engagement_frequency: str,
        content_types: List[str],
        personalization_level: str
    ) -> str:
        return f"""
        Create customer engagement plan for:
        - Business Idea: {business_idea.description}
        - Engagement Channels: {', '.join(engagement_channels)}
        - Engagement Frequency: {engagement_frequency}
        - Content Types: {', '.join(content_types)}
        - Personalization Level: {personalization_level}
        
        Develop comprehensive engagement plan including:
        1. Engagement calendar
        2. Content strategy
        3. Personalization tactics
        4. Engagement metrics
        
        Return the response as a JSON object with the following structure:
        {{
            "engagement_calendar": {{
                "weekly_schedule": {{
                    "monday": ["Activity 1", "Activity 2"],
                    "wednesday": ["Activity 1", "Activity 2"],
                    "friday": ["Activity 1", "Activity 2"]
                }},
                "monthly_themes": ["Theme 1", "Theme 2", "Theme 3"]
            }},
            "content_strategy": {{
                "content_pillars": ["Pillar 1", "Pillar 2"],
                "content_mix": "Content mix breakdown",
                "content_calendar": "Content calendar"
            }},
            "personalization_tactics": [
                "Tactic 1: Behavioral targeting",
                "Tactic 2: Preference-based content",
                "Tactic 3: Lifecycle stage targeting"
            ],
            "engagement_metrics": {{
                "open_rate": "Target open rate",
                "click_rate": "Target click rate",
                "response_rate": "Target response rate",
                "retention_impact": "Expected retention impact"
            }}
        }}
        """
