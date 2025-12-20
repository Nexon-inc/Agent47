from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, BusinessModel
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class BusinessIdeaGeneratorService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def generate_business_ideas(
        self,
        db: AsyncSession,
        skills: List[str],
        passions: List[str],
        available_capital: float,
        industry_preferences: List[str],
        risk_tolerance: str
    ) -> Dict[str, Any]:
        try:
            cache_key = f"business_ideas:{skills}:{passions}:{available_capital}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_idea_generation_prompt(
                skills, passions, available_capital, industry_preferences, risk_tolerance
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates business ideas. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            ideas_data = json.loads(ai_response)
            
            business_ideas = {
                "id": f"ideas_{skills}_{passions}_{available_capital}",
                "skills": skills,
                "passions": passions,
                "available_capital": available_capital,
                "industry_preferences": industry_preferences,
                "risk_tolerance": risk_tolerance,
                "generated_ideas": ideas_data.get("generated_ideas", []),
                "market_trends": ideas_data.get("market_trends", {}),
                "opportunity_analysis": ideas_data.get("opportunity_analysis", {}),
                "implementation_roadmap": ideas_data.get("implementation_roadmap", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(ideas_data), expire=3600)
            await self.event_bus.publish("purity.business_ideas_generated", {
                "skills": skills,
                "passions": passions,
                "available_capital": available_capital,
                "idea_count": len(ideas_data.get("generated_ideas", [])),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return business_ideas
            
        except Exception as e:
            raise e
    
    async def analyze_idea_viability(
        self,
        db: AsyncSession,
        business_idea: str,
        target_market: str,
        competition_level: str,
        market_size: str
    ) -> Dict[str, Any]:
        try:
            prompt = self._create_viability_analysis_prompt(
                business_idea, target_market, competition_level, market_size
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that analyzes business viability. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            viability_data = json.loads(ai_response)
            
            idea_viability = {
                "id": f"viability_{business_idea}_{target_market}",
                "business_idea": business_idea,
                "target_market": target_market,
                "competition_level": competition_level,
                "market_size": market_size,
                "viability_score": viability_data.get("viability_score", 0.0),
                "market_analysis": viability_data.get("market_analysis", {}),
                "competitive_landscape": viability_data.get("competitive_landscape", {}),
                "risk_assessment": viability_data.get("risk_assessment", {}),
                "success_factors": viability_data.get("success_factors", []),
                "recommendations": viability_data.get("recommendations", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.idea_viability_analyzed", {
                "business_idea": business_idea,
                "target_market": target_market,
                "viability_score": idea_viability["viability_score"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return idea_viability
            
        except Exception as e:
            raise e
    
    async def create_idea_roadmap(
        self,
        db: AsyncSession,
        business_idea: str,
        timeline_months: int,
        budget_allocation: Dict[str, float],
        milestones: List[str]
    ) -> Dict[str, Any]:
        try:
            prompt = self._create_roadmap_prompt(
                business_idea, timeline_months, budget_allocation, milestones
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates business roadmaps. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            roadmap_data = json.loads(ai_response)
            
            idea_roadmap = {
                "id": f"roadmap_{business_idea}_{timeline_months}",
                "business_idea": business_idea,
                "timeline_months": timeline_months,
                "budget_allocation": budget_allocation,
                "milestones": milestones,
                "development_phases": roadmap_data.get("development_phases", {}),
                "resource_requirements": roadmap_data.get("resource_requirements", {}),
                "timeline_breakdown": roadmap_data.get("timeline_breakdown", {}),
                "success_metrics": roadmap_data.get("success_metrics", {}),
                "risk_mitigation": roadmap_data.get("risk_mitigation", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.idea_roadmap_created", {
                "business_idea": business_idea,
                "timeline_months": timeline_months,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return idea_roadmap
            
        except Exception as e:
            raise e
    
    def _create_idea_generation_prompt(
        self,
        skills: List[str],
        passions: List[str],
        available_capital: float,
        industry_preferences: List[str],
        risk_tolerance: str
    ) -> str:
        return f"""
        Generate business ideas for:
        - Skills: {', '.join(skills)}
        - Passions: {', '.join(passions)}
        - Available Capital: ${available_capital:,.2f}
        - Industry Preferences: {', '.join(industry_preferences)}
        - Risk Tolerance: {risk_tolerance}
        
        Provide comprehensive business idea generation including:
        1. Generated ideas
        2. Market trends
        3. Opportunity analysis
        4. Implementation roadmap
        
        Return the response as a JSON object with the following structure:
        {{
            "generated_ideas": [
                {{
                    "idea_name": "Business idea name",
                    "description": "Detailed idea description",
                    "target_market": "Target market description",
                    "required_capital": "Required capital amount",
                    "time_to_market": "Time to market estimate",
                    "profit_potential": "Profit potential assessment",
                    "skill_alignment": "Skill alignment score",
                    "passion_alignment": "Passion alignment score",
                    "risk_level": "Risk level assessment",
                    "competitive_advantage": "Competitive advantage description"
                }}
            ],
            "market_trends": {{
                "emerging_trends": ["Trend 1", "Trend 2"],
                "growth_industries": ["Industry 1", "Industry 2"],
                "consumer_behavior": "Consumer behavior analysis",
                "technology_impact": "Technology impact assessment",
                "regulatory_changes": "Regulatory changes affecting opportunities"
            }},
            "opportunity_analysis": {{
                "market_gaps": ["Gap 1", "Gap 2"],
                "underserved_segments": ["Segment 1", "Segment 2"],
                "emerging_needs": ["Need 1", "Need 2"],
                "disruption_opportunities": ["Opportunity 1", "Opportunity 2"],
                "scalability_potential": "Scalability potential analysis"
            }},
            "implementation_roadmap": {{
                "phase_1": {{
                    "duration": "3 months",
                    "activities": ["Activity 1", "Activity 2"],
                    "budget": "Phase 1 budget",
                    "deliverables": ["Deliverable 1", "Deliverable 2"]
                }},
                "phase_2": {{
                    "duration": "6 months",
                    "activities": ["Activity 1", "Activity 2"],
                    "budget": "Phase 2 budget",
                    "deliverables": ["Deliverable 1", "Deliverable 2"]
                }}
            }}
        }}
        """
    
    def _create_viability_analysis_prompt(
        self,
        business_idea: str,
        target_market: str,
        competition_level: str,
        market_size: str
    ) -> str:
        return f"""
        Analyze idea viability for:
        - Business Idea: {business_idea}
        - Target Market: {target_market}
        - Competition Level: {competition_level}
        - Market Size: {market_size}
        
        Provide comprehensive viability analysis including:
        1. Viability score
        2. Market analysis
        3. Competitive landscape
        4. Risk assessment
        5. Success factors
        6. Recommendations
        
        Return the response as a JSON object with the following structure:
        {{
            "viability_score": 85.5,
            "market_analysis": {{
                "market_size": "Market size assessment",
                "growth_potential": "Growth potential analysis",
                "market_maturity": "Market maturity level",
                "customer_demand": "Customer demand assessment",
                "market_barriers": "Market entry barriers"
            }},
            "competitive_landscape": {{
                "competitor_count": "Number of competitors",
                "competitive_intensity": "Competitive intensity level",
                "market_share_opportunity": "Market share opportunity",
                "differentiation_potential": "Differentiation potential",
                "competitive_advantages": ["Advantage 1", "Advantage 2"]
            }},
            "risk_assessment": {{
                "market_risks": ["Risk 1", "Risk 2"],
                "competitive_risks": ["Risk 1", "Risk 2"],
                "operational_risks": ["Risk 1", "Risk 2"],
                "financial_risks": ["Risk 1", "Risk 2"],
                "regulatory_risks": ["Risk 1", "Risk 2"]
            }},
            "success_factors": [
                "Factor 1: Strong value proposition",
                "Factor 2: Market timing",
                "Factor 3: Execution capability",
                "Factor 4: Resource availability",
                "Factor 5: Competitive positioning"
            ],
            "recommendations": [
                "Recommendation 1: Conduct detailed market research",
                "Recommendation 2: Develop unique value proposition",
                "Recommendation 3: Build competitive advantages",
                "Recommendation 4: Secure necessary resources",
                "Recommendation 5: Create risk mitigation plan"
            ]
        }}
        """
    
    def _create_roadmap_prompt(
        self,
        business_idea: str,
        timeline_months: int,
        budget_allocation: Dict[str, float],
        milestones: List[str]
    ) -> str:
        return f"""
        Create idea roadmap for:
        - Business Idea: {business_idea}
        - Timeline: {timeline_months} months
        - Budget Allocation: {budget_allocation}
        - Milestones: {', '.join(milestones)}
        
        Provide comprehensive roadmap including:
        1. Development phases
        2. Resource requirements
        3. Timeline breakdown
        4. Success metrics
        5. Risk mitigation
        
        Return the response as a JSON object with the following structure:
        {{
            "development_phases": {{
                "phase_1": {{
                    "name": "Research and Planning",
                    "duration": "2 months",
                    "objectives": ["Objective 1", "Objective 2"],
                    "activities": ["Activity 1", "Activity 2"],
                    "budget": "Phase 1 budget"
                }},
                "phase_2": {{
                    "name": "Development and Testing",
                    "duration": "4 months",
                    "objectives": ["Objective 1", "Objective 2"],
                    "activities": ["Activity 1", "Activity 2"],
                    "budget": "Phase 2 budget"
                }},
                "phase_3": {{
                    "name": "Launch and Growth",
                    "duration": "6 months",
                    "objectives": ["Objective 1", "Objective 2"],
                    "activities": ["Activity 1", "Activity 2"],
                    "budget": "Phase 3 budget"
                }}
            }},
            "resource_requirements": {{
                "human_resources": ["Resource 1", "Resource 2"],
                "financial_resources": "Financial resource requirements",
                "technical_resources": ["Resource 1", "Resource 2"],
                "partnerships": ["Partnership 1", "Partnership 2"],
                "infrastructure": "Infrastructure requirements"
            }},
            "timeline_breakdown": {{
                "month_1_2": {{
                    "activities": ["Activity 1", "Activity 2"],
                    "deliverables": ["Deliverable 1", "Deliverable 2"],
                    "milestones": ["Milestone 1", "Milestone 2"]
                }},
                "month_3_6": {{
                    "activities": ["Activity 1", "Activity 2"],
                    "deliverables": ["Deliverable 1", "Deliverable 2"],
                    "milestones": ["Milestone 1", "Milestone 2"]
                }},
                "month_7_12": {{
                    "activities": ["Activity 1", "Activity 2"],
                    "deliverables": ["Deliverable 1", "Deliverable 2"],
                    "milestones": ["Milestone 1", "Milestone 2"]
                }}
            }},
            "success_metrics": {{
                "financial_metrics": ["Metric 1", "Metric 2"],
                "operational_metrics": ["Metric 1", "Metric 2"],
                "customer_metrics": ["Metric 1", "Metric 2"],
                "growth_metrics": ["Metric 1", "Metric 2"],
                "quality_metrics": ["Metric 1", "Metric 2"]
            }},
            "risk_mitigation": [
                "Risk 1: Timeline delays - Mitigation strategy",
                "Risk 2: Budget overruns - Mitigation strategy",
                "Risk 3: Technical challenges - Mitigation strategy",
                "Risk 4: Market changes - Mitigation strategy",
                "Risk 5: Resource constraints - Mitigation strategy"
            ]
        }}
        """
