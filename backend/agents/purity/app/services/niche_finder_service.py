from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, NicheOpportunity, PurityMarketResearch
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class NicheFinderService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def find_profitable_niches(
        self,
        db: AsyncSession,
        industry: str,
        budget_range: str,
        skills: List[str],
        interests: List[str],
        market_size_preference: str
    ) -> Dict[str, Any]:
        try:
            cache_key = f"profitable_niches:{industry}:{budget_range}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_niche_finding_prompt(
                industry, budget_range, skills, interests, market_size_preference
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps find business niches. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            niche_data = json.loads(ai_response)
            
            profitable_niches = {
                "id": f"{industry}_{budget_range}",
                "industry": industry,
                "budget_range": budget_range,
                "skills": skills,
                "interests": interests,
                "market_size_preference": market_size_preference,
                "niche_opportunities": niche_data.get("niche_opportunities", []),
                "market_analysis": niche_data.get("market_analysis", {}),
                "competition_level": niche_data.get("competition_level", {}),
                "profitability_indicators": niche_data.get("profitability_indicators", []),
                "entry_strategies": niche_data.get("entry_strategies", []),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(niche_data), expire=3600)
            await self.event_bus.publish("purity.profitable_niches_found", {
                "industry": industry,
                "budget_range": budget_range,
                "niche_count": len(niche_data.get("niche_opportunities", [])),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return profitable_niches
            
        except Exception as e:
            raise e
    
    async def analyze_niche_competition(
        self,
        db: AsyncSession,
        niche_name: str,
        geographic_market: str,
        analysis_depth: str
    ) -> Dict[str, Any]:
        try:
            prompt = self._create_competition_analysis_prompt(
                niche_name, geographic_market, analysis_depth
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps find business niches. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            competition_data = json.loads(ai_response)
            
            competition_analysis = {
                "id": f"{niche_name}_{geographic_market}",
                "niche_name": niche_name,
                "geographic_market": geographic_market,
                "analysis_depth": analysis_depth,
                "competitor_landscape": competition_data.get("competitor_landscape", {}),
                "market_share_analysis": competition_data.get("market_share_analysis", {}),
                "competitive_advantages": competition_data.get("competitive_advantages", []),
                "market_gaps": competition_data.get("market_gaps", []),
                "entry_barriers": competition_data.get("entry_barriers", []),
                "differentiation_opportunities": competition_data.get("differentiation_opportunities", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.niche_competition_analyzed", {
                "niche_name": niche_name,
                "geographic_market": geographic_market,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return competition_analysis
            
        except Exception as e:
            raise e
    
    async def identify_market_gaps(
        self,
        db: AsyncSession,
        target_market: str,
        customer_pain_points: List[str],
        existing_solutions: List[str]
    ) -> Dict[str, Any]:
        try:
            prompt = self._create_market_gaps_prompt(
                target_market, customer_pain_points, existing_solutions
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps find business niches. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            gaps_data = json.loads(ai_response)
            
            market_gaps = {
                "id": f"gaps_{target_market}",
                "target_market": target_market,
                "customer_pain_points": customer_pain_points,
                "existing_solutions": existing_solutions,
                "identified_gaps": gaps_data.get("identified_gaps", []),
                "opportunity_sizing": gaps_data.get("opportunity_sizing", {}),
                "solution_ideas": gaps_data.get("solution_ideas", []),
                "implementation_difficulty": gaps_data.get("implementation_difficulty", {}),
                "market_timing": gaps_data.get("market_timing", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.market_gaps_identified", {
                "target_market": target_market,
                "gaps_count": len(gaps_data.get("identified_gaps", [])),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return market_gaps
            
        except Exception as e:
            raise e
    
    async def validate_niche_opportunity(
        self,
        db: AsyncSession,
        niche_name: str,
        target_audience: str,
        business_model: str,
        validation_criteria: List[str]
    ) -> Dict[str, Any]:
        try:
            prompt = self._create_niche_validation_prompt(
                niche_name, target_audience, business_model, validation_criteria
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps find business niches. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            validation_data = json.loads(ai_response)
            
            niche_validation = {
                "id": f"validation_{niche_name}",
                "niche_name": niche_name,
                "target_audience": target_audience,
                "business_model": business_model,
                "validation_criteria": validation_criteria,
                "validation_score": validation_data.get("validation_score", 0.0),
                "market_viability": validation_data.get("market_viability", {}),
                "competitive_analysis": validation_data.get("competitive_analysis", {}),
                "financial_feasibility": validation_data.get("financial_feasibility", {}),
                "risk_assessment": validation_data.get("risk_assessment", []),
                "recommendations": validation_data.get("recommendations", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.niche_opportunity_validated", {
                "niche_name": niche_name,
                "validation_score": niche_validation["validation_score"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return niche_validation
            
        except Exception as e:
            raise e
    
    def _create_niche_finding_prompt(
        self,
        industry: str,
        budget_range: str,
        skills: List[str],
        interests: List[str],
        market_size_preference: str
    ) -> str:
        return f"""
        Find profitable niches for:
        - Industry: {industry}
        - Budget Range: {budget_range}
        - Skills: {', '.join(skills)}
        - Interests: {', '.join(interests)}
        - Market Size Preference: {market_size_preference}
        
        Identify profitable niche opportunities including:
        1. Niche opportunities
        2. Market analysis
        3. Competition level
        4. Profitability indicators
        5. Entry strategies
        
        Return the response as a JSON object with the following structure:
        {{
            "niche_opportunities": [
                {{
                    "niche_name": "Niche name",
                    "description": "Niche description",
                    "target_audience": "Target audience",
                    "market_size": "Market size estimate",
                    "competition_level": "Low/Medium/High",
                    "profitability_potential": "High/Medium/Low",
                    "entry_cost": "Entry cost estimate",
                    "required_skills": ["Skill 1", "Skill 2"]
                }}
            ],
            "market_analysis": {{
                "trend_analysis": "Market trend analysis",
                "growth_potential": "Growth potential assessment",
                "seasonal_factors": "Seasonal considerations"
            }},
            "competition_level": {{
                "low_competition_niches": ["Niche 1", "Niche 2"],
                "medium_competition_niches": ["Niche 3", "Niche 4"],
                "high_competition_niches": ["Niche 5", "Niche 6"]
            }},
            "profitability_indicators": [
                "Indicator 1: High customer lifetime value",
                "Indicator 2: Low customer acquisition cost",
                "Indicator 3: Strong repeat purchase behavior"
            ],
            "entry_strategies": [
                "Strategy 1: Focus on underserved segment",
                "Strategy 2: Leverage unique skills",
                "Strategy 3: Build strong brand differentiation"
            ]
        }}
        """
    
    def _create_competition_analysis_prompt(
        self,
        niche_name: str,
        geographic_market: str,
        analysis_depth: str
    ) -> str:
        return f"""
        Analyze niche competition for:
        - Niche Name: {niche_name}
        - Geographic Market: {geographic_market}
        - Analysis Depth: {analysis_depth}
        
        Provide comprehensive competition analysis including:
        1. Competitor landscape
        2. Market share analysis
        3. Competitive advantages
        4. Market gaps
        5. Entry barriers
        6. Differentiation opportunities
        
        Return the response as a JSON object with the following structure:
        {{
            "competitor_landscape": {{
                "major_competitors": [
                    {{
                        "name": "Competitor name",
                        "market_share": "Market share percentage",
                        "strengths": ["Strength 1", "Strength 2"],
                        "weaknesses": ["Weakness 1", "Weakness 2"]
                    }}
                ],
                "niche_players": ["Player 1", "Player 2"],
                "emerging_competitors": ["Emerging 1", "Emerging 2"]
            }},
            "market_share_analysis": {{
                "market_leader": "Market leader name",
                "leader_share": "Leader market share",
                "fragmentation_level": "High/Medium/Low",
                "consolidation_trends": "Consolidation trends"
            }},
            "competitive_advantages": [
                "Advantage 1: Unique value proposition",
                "Advantage 2: Cost leadership",
                "Advantage 3: Technology advantage"
            ],
            "market_gaps": [
                "Gap 1: Underserved customer segment",
                "Gap 2: Geographic coverage gap",
                "Gap 3: Product feature gap"
            ],
            "entry_barriers": [
                "Barrier 1: High capital requirements",
                "Barrier 2: Regulatory compliance",
                "Barrier 3: Brand loyalty"
            ],
            "differentiation_opportunities": [
                "Opportunity 1: Superior customer service",
                "Opportunity 2: Innovative technology",
                "Opportunity 3: Niche specialization"
            ]
        }}
        """
    
    def _create_market_gaps_prompt(
        self,
        target_market: str,
        customer_pain_points: List[str],
        existing_solutions: List[str]
    ) -> str:
        return f"""
        Identify market gaps for:
        - Target Market: {target_market}
        - Customer Pain Points: {', '.join(customer_pain_points)}
        - Existing Solutions: {', '.join(existing_solutions)}
        
        Analyze market gaps including:
        1. Identified gaps
        2. Opportunity sizing
        3. Solution ideas
        4. Implementation difficulty
        5. Market timing
        
        Return the response as a JSON object with the following structure:
        {{
            "identified_gaps": [
                {{
                    "gap_name": "Gap name",
                    "description": "Gap description",
                    "customer_impact": "Impact on customers",
                    "market_size": "Market size estimate",
                    "urgency_level": "High/Medium/Low"
                }}
            ],
            "opportunity_sizing": {{
                "total_addressable_market": "TAM estimate",
                "serviceable_addressable_market": "SAM estimate",
                "serviceable_obtainable_market": "SOM estimate"
            }},
            "solution_ideas": [
                {{
                    "solution_name": "Solution name",
                    "description": "Solution description",
                    "unique_value": "Unique value proposition",
                    "implementation_complexity": "High/Medium/Low"
                }}
            ],
            "implementation_difficulty": {{
                "technical_complexity": "Technical difficulty",
                "resource_requirements": "Resource needs",
                "timeline_estimate": "Implementation timeline"
            }},
            "market_timing": {{
                "market_readiness": "Market readiness assessment",
                "optimal_entry_timing": "Optimal entry timing",
                "trend_alignment": "Trend alignment analysis"
            }}
        }}
        """
    
    def _create_niche_validation_prompt(
        self,
        niche_name: str,
        target_audience: str,
        business_model: str,
        validation_criteria: List[str]
    ) -> str:
        return f"""
        Validate niche opportunity for:
        - Niche Name: {niche_name}
        - Target Audience: {target_audience}
        - Business Model: {business_model}
        - Validation Criteria: {', '.join(validation_criteria)}
        
        Provide comprehensive validation including:
        1. Validation score
        2. Market viability
        3. Competitive analysis
        4. Financial feasibility
        5. Risk assessment
        6. Recommendations
        
        Return the response as a JSON object with the following structure:
        {{
            "validation_score": 85.5,
            "market_viability": {{
                "market_size": "Market size assessment",
                "growth_potential": "Growth potential",
                "customer_demand": "Customer demand analysis"
            }},
            "competitive_analysis": {{
                "competition_level": "Competition assessment",
                "competitive_advantages": ["Advantage 1", "Advantage 2"],
                "differentiation_potential": "Differentiation potential"
            }},
            "financial_feasibility": {{
                "startup_costs": "Startup cost estimate",
                "revenue_potential": "Revenue potential",
                "profitability_timeline": "Profitability timeline"
            }},
            "risk_assessment": [
                "Risk 1: Market saturation risk",
                "Risk 2: Regulatory risk",
                "Risk 3: Technology risk"
            ],
            "recommendations": [
                "Recommendation 1: Focus on specific segment",
                "Recommendation 2: Develop unique value proposition",
                "Recommendation 3: Build strong partnerships"
            ]
        }}
        """
