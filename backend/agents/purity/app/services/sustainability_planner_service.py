from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import PurityBusinessIdea, PuritySustainabilityPlan, PurityBusinessModel
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class SustainabilityPlannerService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def develop_sustainability_strategy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        industry_type: str,
        sustainability_goals: List[str],
        budget_allocation: float,
        timeline_years: int
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(PurityBusinessIdea).where(PurityBusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"sustainability_strategy:{business_idea_id}:{industry_type}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_sustainability_strategy_prompt(
                business_idea, industry_type, sustainability_goals, budget_allocation, timeline_years
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with sustainability planning. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            strategy_data = json.loads(ai_response)
            
            sustainability_strategy = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "industry_type": industry_type,
                "sustainability_goals": sustainability_goals,
                "budget_allocation": budget_allocation,
                "timeline_years": timeline_years,
                "sustainability_pillars": strategy_data.get("sustainability_pillars", {}),
                "implementation_plan": strategy_data.get("implementation_plan", {}),
                "eco_friendly_practices": strategy_data.get("eco_friendly_practices", []),
                "sustainability_metrics": strategy_data.get("sustainability_metrics", {}),
                "roi_projections": strategy_data.get("roi_projections", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(strategy_data), expire=3600)
            await self.event_bus.publish("purity.sustainability_strategy_developed", {
                "business_idea_id": business_idea_id,
                "industry_type": industry_type,
                "sustainability_goals": sustainability_goals,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return sustainability_strategy
            
        except Exception as e:
            raise e
    
    async def recommend_eco_friendly_practices(
        self,
        db: AsyncSession,
        business_idea_id: int,
        business_operations: List[str],
        environmental_impact_areas: List[str],
        implementation_budget: float
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(PurityBusinessIdea).where(PurityBusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_eco_friendly_practices_prompt(
                business_idea, business_operations, environmental_impact_areas, implementation_budget
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with sustainability planning. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            practices_data = json.loads(ai_response)
            
            eco_friendly_practices = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "business_operations": business_operations,
                "environmental_impact_areas": environmental_impact_areas,
                "implementation_budget": implementation_budget,
                "recommended_practices": practices_data.get("recommended_practices", []),
                "implementation_priorities": practices_data.get("implementation_priorities", []),
                "cost_benefit_analysis": practices_data.get("cost_benefit_analysis", {}),
                "environmental_impact": practices_data.get("environmental_impact", {}),
                "branding_opportunities": practices_data.get("branding_opportunities", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.eco_friendly_practices_recommended", {
                "business_idea_id": business_idea_id,
                "practice_count": len(practices_data.get("recommended_practices", [])),
                "implementation_budget": implementation_budget,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return eco_friendly_practices
            
        except Exception as e:
            raise e
    
    async def create_sustainability_report(
        self,
        db: AsyncSession,
        business_idea_id: int,
        reporting_period: str,
        sustainability_metrics: Dict[str, Any],
        stakeholder_requirements: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(PurityBusinessIdea).where(PurityBusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_sustainability_report_prompt(
                business_idea, reporting_period, sustainability_metrics, stakeholder_requirements
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with sustainability planning. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            report_data = json.loads(ai_response)
            
            sustainability_report = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "reporting_period": reporting_period,
                "sustainability_metrics": sustainability_metrics,
                "stakeholder_requirements": stakeholder_requirements,
                "executive_summary": report_data.get("executive_summary", ""),
                "environmental_performance": report_data.get("environmental_performance", {}),
                "social_impact": report_data.get("social_impact", {}),
                "governance_metrics": report_data.get("governance_metrics", {}),
                "sustainability_goals": report_data.get("sustainability_goals", {}),
                "future_commitments": report_data.get("future_commitments", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.sustainability_report_created", {
                "business_idea_id": business_idea_id,
                "reporting_period": reporting_period,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return sustainability_report
            
        except Exception as e:
            raise e
    
    def _create_sustainability_strategy_prompt(
        self,
        business_idea: PurityBusinessIdea,
        industry_type: str,
        sustainability_goals: List[str],
        budget_allocation: float,
        timeline_years: int
    ) -> str:
        return f"""
        Develop sustainability strategy for:
        - Business Idea: {business_idea.description}
        - Industry Type: {industry_type}
        - Sustainability Goals: {', '.join(sustainability_goals)}
        - Budget Allocation: ${budget_allocation:,.2f}
        - Timeline: {timeline_years} years
        
        Provide comprehensive sustainability strategy including:
        1. Sustainability pillars
        2. Implementation plan
        3. Eco-friendly practices
        4. Sustainability metrics
        5. ROI projections
        
        Return the response as a JSON object with the following structure:
        {{
            "sustainability_pillars": {{
                "environmental": {{
                    "focus_areas": ["Area 1", "Area 2"],
                    "objectives": ["Objective 1", "Objective 2"],
                    "targets": "Environmental targets"
                }},
                "social": {{
                    "focus_areas": ["Area 1", "Area 2"],
                    "objectives": ["Objective 1", "Objective 2"],
                    "targets": "Social targets"
                }},
                "governance": {{
                    "focus_areas": ["Area 1", "Area 2"],
                    "objectives": ["Objective 1", "Objective 2"],
                    "targets": "Governance targets"
                }}
            }},
            "implementation_plan": {{
                "phase_1": {{
                    "duration": "6 months",
                    "activities": ["Activity 1", "Activity 2"],
                    "budget": "Phase 1 budget",
                    "expected_outcomes": ["Outcome 1", "Outcome 2"]
                }},
                "phase_2": {{
                    "duration": "12 months",
                    "activities": ["Activity 1", "Activity 2"],
                    "budget": "Phase 2 budget",
                    "expected_outcomes": ["Outcome 1", "Outcome 2"]
                }}
            }},
            "eco_friendly_practices": [
                "Practice 1: Energy efficiency optimization",
                "Practice 2: Waste reduction and recycling",
                "Practice 3: Sustainable sourcing",
                "Practice 4: Carbon footprint reduction",
                "Practice 5: Water conservation"
            ],
            "sustainability_metrics": {{
                "environmental_metrics": ["Metric 1", "Metric 2"],
                "social_metrics": ["Metric 1", "Metric 2"],
                "governance_metrics": ["Metric 1", "Metric 2"],
                "reporting_frequency": "Reporting frequency"
            }},
            "roi_projections": {{
                "cost_savings": "Projected cost savings",
                "brand_value": "Brand value enhancement",
                "customer_loyalty": "Customer loyalty impact",
                "employee_engagement": "Employee engagement impact",
                "regulatory_compliance": "Regulatory compliance benefits"
            }}
        }}
        """
    
    def _create_eco_friendly_practices_prompt(
        self,
        business_idea: PurityBusinessIdea,
        business_operations: List[str],
        environmental_impact_areas: List[str],
        implementation_budget: float
    ) -> str:
        return f"""
        Recommend eco-friendly practices for:
        - Business Idea: {business_idea.description}
        - Business Operations: {', '.join(business_operations)}
        - Environmental Impact Areas: {', '.join(environmental_impact_areas)}
        - Implementation Budget: ${implementation_budget:,.2f}
        
        Provide comprehensive eco-friendly practice recommendations including:
        1. Recommended practices
        2. Implementation priorities
        3. Cost-benefit analysis
        4. Environmental impact
        5. Branding opportunities
        
        Return the response as a JSON object with the following structure:
        {{
            "recommended_practices": [
                {{
                    "practice_name": "Practice name",
                    "description": "Practice description",
                    "implementation_cost": "Implementation cost",
                    "environmental_benefit": "Environmental benefit",
                    "business_benefit": "Business benefit",
                    "implementation_difficulty": "Easy/Medium/Hard"
                }}
            ],
            "implementation_priorities": [
                {{
                    "priority_level": "High/Medium/Low",
                    "practice_name": "Practice name",
                    "rationale": "Priority rationale",
                    "timeline": "Implementation timeline",
                    "dependencies": ["Dependency 1", "Dependency 2"]
                }}
            ],
            "cost_benefit_analysis": {{
                "total_implementation_cost": "Total cost",
                "annual_savings": "Annual savings",
                "payback_period": "Payback period",
                "long_term_benefits": ["Benefit 1", "Benefit 2"],
                "risk_assessment": "Risk assessment"
            }},
            "environmental_impact": {{
                "carbon_reduction": "Carbon reduction potential",
                "waste_reduction": "Waste reduction potential",
                "energy_savings": "Energy savings potential",
                "water_conservation": "Water conservation potential",
                "biodiversity_impact": "Biodiversity impact"
            }},
            "branding_opportunities": [
                "Opportunity 1: Green certification",
                "Opportunity 2: Sustainability marketing",
                "Opportunity 3: Customer education",
                "Opportunity 4: Industry leadership",
                "Opportunity 5: Partnership opportunities"
            ]
        }}
        """
    
    def _create_sustainability_report_prompt(
        self,
        business_idea: PurityBusinessIdea,
        reporting_period: str,
        sustainability_metrics: Dict[str, Any],
        stakeholder_requirements: List[str]
    ) -> str:
        return f"""
        Create sustainability report for:
        - Business Idea: {business_idea.description}
        - Reporting Period: {reporting_period}
        - Sustainability Metrics: {sustainability_metrics}
        - Stakeholder Requirements: {', '.join(stakeholder_requirements)}
        
        Provide comprehensive sustainability report including:
        1. Executive summary
        2. Environmental performance
        3. Social impact
        4. Governance metrics
        5. Sustainability goals
        6. Future commitments
        
        Return the response as a JSON object with the following structure:
        {{
            "executive_summary": "Comprehensive executive summary of sustainability performance and achievements",
            "environmental_performance": {{
                "carbon_footprint": "Carbon footprint data",
                "energy_consumption": "Energy consumption metrics",
                "waste_management": "Waste management performance",
                "water_usage": "Water usage metrics",
                "biodiversity_impact": "Biodiversity impact assessment"
            }},
            "social_impact": {{
                "employee_wellbeing": "Employee wellbeing metrics",
                "community_engagement": "Community engagement activities",
                "supply_chain_responsibility": "Supply chain responsibility",
                "diversity_inclusion": "Diversity and inclusion metrics",
                "health_safety": "Health and safety performance"
            }},
            "governance_metrics": {{
                "ethical_leadership": "Ethical leadership practices",
                "transparency": "Transparency measures",
                "stakeholder_engagement": "Stakeholder engagement",
                "compliance": "Compliance performance",
                "risk_management": "Risk management practices"
            }},
            "sustainability_goals": {{
                "achieved_goals": ["Goal 1", "Goal 2"],
                "in_progress_goals": ["Goal 1", "Goal 2"],
                "future_goals": ["Goal 1", "Goal 2"],
                "goal_performance": "Overall goal performance"
            }},
            "future_commitments": [
                "Commitment 1: Carbon neutrality by 2030",
                "Commitment 2: 100% renewable energy",
                "Commitment 3: Zero waste operations",
                "Commitment 4: Sustainable supply chain",
                "Commitment 5: Enhanced stakeholder engagement"
            ]
        }}
        """
