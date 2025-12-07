from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, PartnershipOpportunity, BusinessModel
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.event_bus.kafka_manager import KafkaManager
from backend.core.cache.redis_manager import RedisManager

class PartnershipMatchmakerService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def find_partnership_opportunities(
        self,
        db: AsyncSession,
        business_idea_id: int,
        partnership_type: str,
        required_skills: List[str],
        investment_capacity: float,
        location_preferences: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"partnership_opportunities:{business_idea_id}:{partnership_type}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_partnership_search_prompt(
                business_idea, partnership_type, required_skills, investment_capacity, location_preferences
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that matches business partnerships. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            search_data = json.loads(ai_response)
            
            partnership_opportunities = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "partnership_type": partnership_type,
                "required_skills": required_skills,
                "investment_capacity": investment_capacity,
                "location_preferences": location_preferences,
                "potential_partners": search_data.get("potential_partners", []),
                "partnership_models": search_data.get("partnership_models", []),
                "compatibility_factors": search_data.get("compatibility_factors", []),
                "partnership_benefits": search_data.get("partnership_benefits", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(search_data), expire=3600)
            await self.event_bus.publish("purity.partnership_opportunities_found", {
                "business_idea_id": business_idea_id,
                "partnership_type": partnership_type,
                "partner_count": len(search_data.get("potential_partners", [])),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return partnership_opportunities
            
        except Exception as e:
            raise e
    
    async def analyze_partner_compatibility(
        self,
        db: AsyncSession,
        business_idea_id: int,
        potential_partner: Dict[str, Any],
        partnership_goals: List[str],
        working_style_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_compatibility_analysis_prompt(
                business_idea, potential_partner, partnership_goals, working_style_preferences
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that matches business partnerships. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            compatibility_data = json.loads(ai_response)
            
            partner_compatibility = {
                "id": f"compatibility_{business_idea_id}_{potential_partner.get('id', 'unknown')}",
                "business_idea_id": business_idea_id,
                "potential_partner": potential_partner,
                "partnership_goals": partnership_goals,
                "working_style_preferences": working_style_preferences,
                "compatibility_score": compatibility_data.get("compatibility_score", 0.0),
                "skill_complementarity": compatibility_data.get("skill_complementarity", {}),
                "value_alignment": compatibility_data.get("value_alignment", {}),
                "communication_style": compatibility_data.get("communication_style", {}),
                "risk_assessment": compatibility_data.get("risk_assessment", {}),
                "recommendations": compatibility_data.get("recommendations", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.partner_compatibility_analyzed", {
                "business_idea_id": business_idea_id,
                "partner_id": potential_partner.get('id', 'unknown'),
                "compatibility_score": partner_compatibility["compatibility_score"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return partner_compatibility
            
        except Exception as e:
            raise e
    
    def _create_partnership_search_prompt(
        self,
        business_idea: BusinessIdea,
        partnership_type: str,
        required_skills: List[str],
        investment_capacity: float,
        location_preferences: List[str]
    ) -> str:
        return f"""
        Find partnership opportunities for:
        - Business Idea: {business_idea.description}
        - Partnership Type: {partnership_type}
        - Required Skills: {', '.join(required_skills)}
        - Investment Capacity: ${investment_capacity:,.2f}
        - Location Preferences: {', '.join(location_preferences)}
        
        Identify comprehensive partnership opportunities including:
        1. Potential partners
        2. Partnership models
        3. Compatibility factors
        4. Partnership benefits
        
        Return the response as a JSON object with the following structure:
        {{
            "potential_partners": [
                {{
                    "partner_id": "Partner ID",
                    "partner_name": "Partner name",
                    "skills": ["Skill 1", "Skill 2"],
                    "experience": "Experience level",
                    "investment_capacity": "Investment capacity",
                    "location": "Location",
                    "compatibility_score": 85.5,
                    "partnership_interest": "High/Medium/Low"
                }}
            ],
            "partnership_models": [
                {{
                    "model_type": "Partnership model type",
                    "description": "Model description",
                    "equity_split": "Equity split arrangement",
                    "responsibilities": ["Responsibility 1", "Responsibility 2"],
                    "benefits": ["Benefit 1", "Benefit 2"]
                }}
            ],
            "compatibility_factors": [
                "Factor 1: Skill complementarity",
                "Factor 2: Value alignment",
                "Factor 3: Communication style",
                "Factor 4: Work ethic compatibility",
                "Factor 5: Financial goals alignment"
            ],
            "partnership_benefits": {{
                "strategic_benefits": ["Benefit 1", "Benefit 2"],
                "financial_benefits": ["Benefit 1", "Benefit 2"],
                "operational_benefits": ["Benefit 1", "Benefit 2"],
                "network_benefits": ["Benefit 1", "Benefit 2"]
            }}
        }}
        """
    
    def _create_compatibility_analysis_prompt(
        self,
        business_idea: BusinessIdea,
        potential_partner: Dict[str, Any],
        partnership_goals: List[str],
        working_style_preferences: Dict[str, Any]
    ) -> str:
        return f"""
        Analyze partner compatibility for:
        - Business Idea: {business_idea.description}
        - Potential Partner: {potential_partner}
        - Partnership Goals: {', '.join(partnership_goals)}
        - Working Style Preferences: {working_style_preferences}
        
        Provide comprehensive compatibility analysis including:
        1. Compatibility score
        2. Skill complementarity
        3. Value alignment
        4. Communication style
        5. Risk assessment
        6. Recommendations
        
        Return the response as a JSON object with the following structure:
        {{
            "compatibility_score": 87.5,
            "skill_complementarity": {{
                "complementary_skills": ["Skill 1", "Skill 2"],
                "skill_gaps": ["Gap 1", "Gap 2"],
                "skill_overlap": ["Overlap 1", "Overlap 2"],
                "learning_opportunities": ["Opportunity 1", "Opportunity 2"]
            }},
            "value_alignment": {{
                "shared_values": ["Value 1", "Value 2"],
                "value_conflicts": ["Conflict 1", "Conflict 2"],
                "mission_alignment": "Mission alignment assessment",
                "culture_fit": "Cultural fit assessment"
            }},
            "communication_style": {{
                "communication_preferences": "Communication preferences",
                "conflict_resolution": "Conflict resolution style",
                "feedback_approach": "Feedback approach",
                "decision_making": "Decision-making style"
            }},
            "risk_assessment": {{
                "partnership_risks": ["Risk 1", "Risk 2"],
                "mitigation_strategies": ["Strategy 1", "Strategy 2"],
                "risk_level": "Low/Medium/High",
                "risk_factors": ["Factor 1", "Factor 2"]
            }},
            "recommendations": [
                "Recommendation 1: Establish clear communication protocols",
                "Recommendation 2: Define roles and responsibilities",
                "Recommendation 3: Create conflict resolution process",
                "Recommendation 4: Set up regular check-ins"
            ]
        }}
        """
