from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, FranchiseOpportunity, BusinessModel
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class FranchiseScannerService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def scan_franchise_opportunities(
        self,
        db: AsyncSession,
        industry_preferences: List[str],
        budget_range: str,
        location_preferences: List[str],
        experience_level: str
    ) -> Dict[str, Any]:
        try:
            cache_key = f"franchise_opportunities:{industry_preferences}:{budget_range}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_franchise_scan_prompt(
                industry_preferences, budget_range, location_preferences, experience_level
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps analyze franchises. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            scan_data = json.loads(ai_response)
            
            franchise_opportunities = {
                "id": f"scan_{industry_preferences}_{budget_range}",
                "industry_preferences": industry_preferences,
                "budget_range": budget_range,
                "location_preferences": location_preferences,
                "experience_level": experience_level,
                "franchise_opportunities": scan_data.get("franchise_opportunities", []),
                "market_analysis": scan_data.get("market_analysis", {}),
                "investment_requirements": scan_data.get("investment_requirements", {}),
                "success_factors": scan_data.get("success_factors", []),
                "risk_assessment": scan_data.get("risk_assessment", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(scan_data), expire=3600)
            await self.event_bus.publish("purity.franchise_opportunities_scanned", {
                "industry_preferences": industry_preferences,
                "budget_range": budget_range,
                "opportunity_count": len(scan_data.get("franchise_opportunities", [])),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return franchise_opportunities
            
        except Exception as e:
            raise e
    
    async def analyze_franchise_model(
        self,
        db: AsyncSession,
        franchise_name: str,
        franchise_type: str,
        business_model: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            prompt = self._create_franchise_analysis_prompt(
                franchise_name, franchise_type, business_model, market_conditions
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps analyze franchises. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            analysis_data = json.loads(ai_response)
            
            franchise_analysis = {
                "id": f"analysis_{franchise_name}",
                "franchise_name": franchise_name,
                "franchise_type": franchise_type,
                "business_model": business_model,
                "market_conditions": market_conditions,
                "franchise_evaluation": analysis_data.get("franchise_evaluation", {}),
                "financial_analysis": analysis_data.get("financial_analysis", {}),
                "operational_requirements": analysis_data.get("operational_requirements", {}),
                "competitive_landscape": analysis_data.get("competitive_landscape", {}),
                "growth_potential": analysis_data.get("growth_potential", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.franchise_model_analyzed", {
                "franchise_name": franchise_name,
                "franchise_type": franchise_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return franchise_analysis
            
        except Exception as e:
            raise e
    
    async def evaluate_franchise_investment(
        self,
        db: AsyncSession,
        franchise_opportunity: Dict[str, Any],
        investor_profile: Dict[str, Any],
        market_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            prompt = self._create_investment_evaluation_prompt(
                franchise_opportunity, investor_profile, market_analysis
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps analyze franchises. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            evaluation_data = json.loads(ai_response)
            
            investment_evaluation = {
                "id": f"evaluation_{franchise_opportunity.get('name', 'unknown')}",
                "franchise_opportunity": franchise_opportunity,
                "investor_profile": investor_profile,
                "market_analysis": market_analysis,
                "investment_score": evaluation_data.get("investment_score", 0.0),
                "financial_projections": evaluation_data.get("financial_projections", {}),
                "risk_assessment": evaluation_data.get("risk_assessment", {}),
                "return_on_investment": evaluation_data.get("return_on_investment", {}),
                "investment_recommendation": evaluation_data.get("investment_recommendation", ""),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.franchise_investment_evaluated", {
                "franchise_name": franchise_opportunity.get('name', 'unknown'),
                "investment_score": investment_evaluation["investment_score"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return investment_evaluation
            
        except Exception as e:
            raise e
    
    async def create_franchise_guidance(
        self,
        db: AsyncSession,
        franchise_type: str,
        experience_level: str,
        budget_constraints: Dict[str, Any],
        location_preferences: List[str]
    ) -> Dict[str, Any]:
        try:
            prompt = self._create_franchise_guidance_prompt(
                franchise_type, experience_level, budget_constraints, location_preferences
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps analyze franchises. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            guidance_data = json.loads(ai_response)
            
            franchise_guidance = {
                "id": f"guidance_{franchise_type}_{experience_level}",
                "franchise_type": franchise_type,
                "experience_level": experience_level,
                "budget_constraints": budget_constraints,
                "location_preferences": location_preferences,
                "guidance_plan": guidance_data.get("guidance_plan", {}),
                "step_by_step_process": guidance_data.get("step_by_step_process", []),
                "due_diligence_checklist": guidance_data.get("due_diligence_checklist", []),
                "legal_considerations": guidance_data.get("legal_considerations", []),
                "success_tips": guidance_data.get("success_tips", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.franchise_guidance_created", {
                "franchise_type": franchise_type,
                "experience_level": experience_level,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return franchise_guidance
            
        except Exception as e:
            raise e
    
    def _create_franchise_scan_prompt(
        self,
        industry_preferences: List[str],
        budget_range: str,
        location_preferences: List[str],
        experience_level: str
    ) -> str:
        return f"""
        Scan franchise opportunities for:
        - Industry Preferences: {', '.join(industry_preferences)}
        - Budget Range: {budget_range}
        - Location Preferences: {', '.join(location_preferences)}
        - Experience Level: {experience_level}
        
        Identify comprehensive franchise opportunities including:
        1. Franchise opportunities
        2. Market analysis
        3. Investment requirements
        4. Success factors
        5. Risk assessment
        
        Return the response as a JSON object with the following structure:
        {{
            "franchise_opportunities": [
                {{
                    "franchise_name": "Franchise name",
                    "industry": "Industry category",
                    "investment_range": "Investment range",
                    "franchise_fee": "Franchise fee",
                    "royalty_fee": "Royalty fee percentage",
                    "location_availability": "Location availability",
                    "success_rate": "Success rate percentage",
                    "support_provided": ["Support 1", "Support 2"],
                    "training_program": "Training program description",
                    "market_potential": "Market potential assessment"
                }}
            ],
            "market_analysis": {{
                "industry_trends": "Industry trend analysis",
                "market_size": "Market size assessment",
                "growth_potential": "Growth potential analysis",
                "competitive_landscape": "Competitive landscape overview",
                "demographic_analysis": "Demographic analysis"
            }},
            "investment_requirements": {{
                "initial_investment": "Initial investment breakdown",
                "ongoing_costs": "Ongoing operational costs",
                "financing_options": ["Option 1", "Option 2"],
                "cash_flow_projections": "Cash flow projections",
                "break_even_analysis": "Break-even analysis"
            }},
            "success_factors": [
                "Factor 1: Location selection",
                "Factor 2: Market demand",
                "Factor 3: Operational efficiency",
                "Factor 4: Brand recognition",
                "Factor 5: Support system"
            ],
            "risk_assessment": {{
                "market_risks": ["Risk 1", "Risk 2"],
                "operational_risks": ["Risk 1", "Risk 2"],
                "financial_risks": ["Risk 1", "Risk 2"],
                "mitigation_strategies": ["Strategy 1", "Strategy 2"]
            }}
        }}
        """
    
    def _create_franchise_analysis_prompt(
        self,
        franchise_name: str,
        franchise_type: str,
        business_model: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> str:
        return f"""
        Analyze franchise model for:
        - Franchise Name: {franchise_name}
        - Franchise Type: {franchise_type}
        - Business Model: {business_model}
        - Market Conditions: {market_conditions}
        
        Provide comprehensive franchise analysis including:
        1. Franchise evaluation
        2. Financial analysis
        3. Operational requirements
        4. Competitive landscape
        5. Growth potential
        
        Return the response as a JSON object with the following structure:
        {{
            "franchise_evaluation": {{
                "brand_strength": "Brand strength assessment",
                "franchise_support": "Support system evaluation",
                "training_program": "Training program assessment",
                "operational_systems": "Operational systems evaluation",
                "franchisee_satisfaction": "Franchisee satisfaction rating"
            }},
            "financial_analysis": {{
                "initial_investment": "Initial investment breakdown",
                "operating_costs": "Operating costs analysis",
                "revenue_projections": "Revenue projections",
                "profit_margins": "Profit margin analysis",
                "return_on_investment": "ROI projections"
            }},
            "operational_requirements": {{
                "staffing_needs": "Staffing requirements",
                "equipment_requirements": "Equipment needs",
                "space_requirements": "Space requirements",
                "operational_hours": "Operating hours",
                "compliance_requirements": "Compliance requirements"
            }},
            "competitive_landscape": {{
                "direct_competitors": ["Competitor 1", "Competitor 2"],
                "competitive_advantages": ["Advantage 1", "Advantage 2"],
                "market_positioning": "Market positioning analysis",
                "differentiation_factors": ["Factor 1", "Factor 2"]
            }},
            "growth_potential": {{
                "market_expansion": "Market expansion opportunities",
                "franchise_development": "Franchise development potential",
                "scalability": "Scalability assessment",
                "long_term_viability": "Long-term viability analysis"
            }}
        }}
        """
    
    def _create_investment_evaluation_prompt(
        self,
        franchise_opportunity: Dict[str, Any],
        investor_profile: Dict[str, Any],
        market_analysis: Dict[str, Any]
    ) -> str:
        return f"""
        Evaluate franchise investment for:
        - Franchise Opportunity: {franchise_opportunity}
        - Investor Profile: {investor_profile}
        - Market Analysis: {market_analysis}
        
        Provide comprehensive investment evaluation including:
        1. Investment score
        2. Financial projections
        3. Risk assessment
        4. Return on investment
        5. Investment recommendation
        
        Return the response as a JSON object with the following structure:
        {{
            "investment_score": 85.5,
            "financial_projections": {{
                "year_1_revenue": 500000,
                "year_1_profit": 75000,
                "year_3_revenue": 800000,
                "year_3_profit": 160000,
                "payback_period": "24 months",
                "irr": 25.5
            }},
            "risk_assessment": {{
                "risk_level": "Medium",
                "key_risks": ["Risk 1", "Risk 2", "Risk 3"],
                "risk_mitigation": ["Mitigation 1", "Mitigation 2"],
                "risk_score": 65.0
            }},
            "return_on_investment": {{
                "projected_roi": 150.0,
                "roi_timeline": "5 years",
                "cash_flow_analysis": "Cash flow analysis",
                "break_even_point": "18 months"
            }},
            "investment_recommendation": "Strong recommendation to proceed with investment based on solid market potential and strong franchise support system."
        }}
        """
    
    def _create_franchise_guidance_prompt(
        self,
        franchise_type: str,
        experience_level: str,
        budget_constraints: Dict[str, Any],
        location_preferences: List[str]
    ) -> str:
        return f"""
        Create franchise guidance for:
        - Franchise Type: {franchise_type}
        - Experience Level: {experience_level}
        - Budget Constraints: {budget_constraints}
        - Location Preferences: {', '.join(location_preferences)}
        
        Provide comprehensive franchise guidance including:
        1. Guidance plan
        2. Step-by-step process
        3. Due diligence checklist
        4. Legal considerations
        5. Success tips
        
        Return the response as a JSON object with the following structure:
        {{
            "guidance_plan": {{
                "phase_1": "Research and evaluation phase",
                "phase_2": "Due diligence and selection phase",
                "phase_3": "Negotiation and agreement phase",
                "phase_4": "Setup and launch phase",
                "phase_5": "Operations and growth phase"
            }},
            "step_by_step_process": [
                "Step 1: Research franchise opportunities",
                "Step 2: Evaluate franchise options",
                "Step 3: Conduct due diligence",
                "Step 4: Review franchise agreement",
                "Step 5: Secure financing",
                "Step 6: Select location",
                "Step 7: Complete training",
                "Step 8: Launch operations"
            ],
            "due_diligence_checklist": [
                "Check 1: Review franchise disclosure document",
                "Check 2: Analyze financial statements",
                "Check 3: Speak with existing franchisees",
                "Check 4: Evaluate market conditions",
                "Check 5: Assess competition",
                "Check 6: Review legal requirements",
                "Check 7: Analyze support systems",
                "Check 8: Evaluate growth potential"
            ],
            "legal_considerations": [
                "Consideration 1: Franchise agreement terms",
                "Consideration 2: Territory rights",
                "Consideration 3: Renewal options",
                "Consideration 4: Exit strategies",
                "Consideration 5: Dispute resolution",
                "Consideration 6: Compliance requirements"
            ],
            "success_tips": [
                "Tip 1: Choose the right location",
                "Tip 2: Follow the franchise system",
                "Tip 3: Build a strong team",
                "Tip 4: Focus on customer service",
                "Tip 5: Monitor financial performance",
                "Tip 6: Stay engaged with the franchise community"
            ]
        }}
        """
