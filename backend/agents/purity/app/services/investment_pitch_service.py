from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, InvestmentPitch, BusinessModel, FinancialForecast
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class InvestmentPitchService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def create_investment_pitch(
        self,
        db: AsyncSession,
        business_idea_id: int,
        funding_amount: float,
        equity_offered: float,
        use_of_funds: List[str],
        investor_type: str,
        pitch_deck_format: str = "slides"
    ) -> InvestmentPitch:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"investment_pitch:{business_idea_id}:{funding_amount}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_investment_pitch_prompt(
                business_idea, funding_amount, equity_offered, use_of_funds,
                investor_type, pitch_deck_format
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates investment pitches. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            pitch_data = json.loads(ai_response)
            
            investment_pitch = InvestmentPitch(
                business_idea_id=business_idea_id,
                funding_amount=funding_amount,
                equity_offered=equity_offered,
                use_of_funds=json.dumps(use_of_funds),
                investor_type=investor_type,
                pitch_deck_content=json.dumps(pitch_data.get("pitch_deck_content", {})),
                executive_summary=pitch_data.get("executive_summary", ""),
                market_analysis=pitch_data.get("market_analysis", ""),
                competitive_advantage=pitch_data.get("competitive_advantage", ""),
                financial_projections=json.dumps(pitch_data.get("financial_projections", {})),
                investment_highlights=json.dumps(pitch_data.get("investment_highlights", [])),
                risk_assessment=pitch_data.get("risk_assessment", ""),
                exit_strategy=pitch_data.get("exit_strategy", "")
            )
            
            db.add(investment_pitch)
            await db.commit()
            await db.refresh(investment_pitch)
            
            await self.redis_manager.set(cache_key, json.dumps(pitch_data), expire=3600)
            await self.event_bus.publish("purity.investment_pitch_created", {
                "business_idea_id": business_idea_id,
                "funding_amount": funding_amount,
                "investor_type": investor_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return investment_pitch
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def generate_pitch_deck(
        self,
        db: AsyncSession,
        investment_pitch_id: int,
        slide_count: int = 15,
        include_financials: bool = True,
        include_market_data: bool = True
    ) -> Dict[str, Any]:
        try:
            pitch_result = await db.execute(
                select(InvestmentPitch).where(InvestmentPitch.id == investment_pitch_id)
            )
            investment_pitch = pitch_result.scalar_one_or_none()
            if not investment_pitch:
                raise ValueError("Investment pitch not found")
            
            prompt = self._create_pitch_deck_prompt(
                investment_pitch, slide_count, include_financials, include_market_data
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates investment pitches. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            deck_data = json.loads(ai_response)
            
            pitch_deck = {
                "id": investment_pitch_id,
                "investment_pitch_id": investment_pitch_id,
                "slide_count": slide_count,
                "slides": deck_data.get("slides", []),
                "presentation_notes": deck_data.get("presentation_notes", ""),
                "key_talking_points": deck_data.get("key_talking_points", []),
                "anticipated_questions": deck_data.get("anticipated_questions", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.pitch_deck_generated", {
                "investment_pitch_id": investment_pitch_id,
                "slide_count": slide_count,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return pitch_deck
            
        except Exception as e:
            raise e
    
    async def create_financial_projections(
        self,
        db: AsyncSession,
        investment_pitch_id: int,
        projection_years: int = 5,
        include_scenarios: bool = True
    ) -> Dict[str, Any]:
        try:
            pitch_result = await db.execute(
                select(InvestmentPitch).where(InvestmentPitch.id == investment_pitch_id)
            )
            investment_pitch = pitch_result.scalar_one_or_none()
            if not investment_pitch:
                raise ValueError("Investment pitch not found")
            
            prompt = self._create_financial_projections_prompt(
                investment_pitch, projection_years, include_scenarios
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates investment pitches. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            projections_data = json.loads(ai_response)
            
            financial_projections = {
                "id": investment_pitch_id,
                "investment_pitch_id": investment_pitch_id,
                "projection_years": projection_years,
                "revenue_projections": projections_data.get("revenue_projections", {}),
                "expense_projections": projections_data.get("expense_projections", {}),
                "profit_projections": projections_data.get("profit_projections", {}),
                "cash_flow_projections": projections_data.get("cash_flow_projections", {}),
                "scenario_analysis": projections_data.get("scenario_analysis", {}),
                "key_metrics": projections_data.get("key_metrics", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.financial_projections_created", {
                "investment_pitch_id": investment_pitch_id,
                "projection_years": projection_years,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return financial_projections
            
        except Exception as e:
            raise e
    
    async def generate_investor_materials(
        self,
        db: AsyncSession,
        investment_pitch_id: int,
        material_types: List[str]
    ) -> Dict[str, Any]:
        try:
            pitch_result = await db.execute(
                select(InvestmentPitch).where(InvestmentPitch.id == investment_pitch_id)
            )
            investment_pitch = pitch_result.scalar_one_or_none()
            if not investment_pitch:
                raise ValueError("Investment pitch not found")
            
            prompt = self._create_investor_materials_prompt(
                investment_pitch, material_types
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates investment pitches. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            materials_data = json.loads(ai_response)
            
            investor_materials = {
                "id": investment_pitch_id,
                "investment_pitch_id": investment_pitch_id,
                "material_types": material_types,
                "executive_summary": materials_data.get("executive_summary", ""),
                "business_plan": materials_data.get("business_plan", ""),
                "financial_model": materials_data.get("financial_model", {}),
                "due_diligence_package": materials_data.get("due_diligence_package", {}),
                "investor_presentation": materials_data.get("investor_presentation", ""),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.investor_materials_generated", {
                "investment_pitch_id": investment_pitch_id,
                "material_types": material_types,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return investor_materials
            
        except Exception as e:
            raise e
    
    def _create_investment_pitch_prompt(
        self,
        business_idea: BusinessIdea,
        funding_amount: float,
        equity_offered: float,
        use_of_funds: List[str],
        investor_type: str,
        pitch_deck_format: str
    ) -> str:
        return f"""
        Create a comprehensive investment pitch for:
        - Business Idea: {business_idea.description}
        - Funding Amount: ${funding_amount:,.2f}
        - Equity Offered: {equity_offered}%
        - Use of Funds: {', '.join(use_of_funds)}
        - Investor Type: {investor_type}
        - Pitch Deck Format: {pitch_deck_format}
        
        Develop a complete investment pitch including:
        1. Executive summary
        2. Market analysis
        3. Competitive advantage
        4. Financial projections
        5. Investment highlights
        6. Risk assessment
        7. Exit strategy
        8. Pitch deck content
        
        Return the response as a JSON object with the following structure:
        {{
            "executive_summary": "Compelling executive summary",
            "market_analysis": "Comprehensive market analysis",
            "competitive_advantage": "Clear competitive advantage description",
            "financial_projections": {{
                "revenue_forecast": [100000, 250000, 500000],
                "profit_margins": [15, 20, 25],
                "growth_rate": 150.0,
                "break_even": "Month 18"
            }},
            "investment_highlights": [
                "Highlight 1: Market opportunity",
                "Highlight 2: Strong team",
                "Highlight 3: Proven traction"
            ],
            "risk_assessment": "Comprehensive risk assessment",
            "exit_strategy": "Clear exit strategy",
            "pitch_deck_content": {{
                "slides": [
                    {{
                        "title": "Slide Title",
                        "content": "Slide content",
                        "key_points": ["Point 1", "Point 2"]
                    }}
                ]
            }}
        }}
        """
    
    def _create_pitch_deck_prompt(
        self,
        investment_pitch: InvestmentPitch,
        slide_count: int,
        include_financials: bool,
        include_market_data: bool
    ) -> str:
        return f"""
        Generate a detailed pitch deck for:
        - Funding Amount: ${investment_pitch.funding_amount:,.2f}
        - Equity Offered: {investment_pitch.equity_offered}%
        - Investor Type: {investment_pitch.investor_type}
        - Slide Count: {slide_count}
        - Include Financials: {include_financials}
        - Include Market Data: {include_market_data}
        
        Create a comprehensive pitch deck including:
        1. Slide content and structure
        2. Presentation notes
        3. Key talking points
        4. Anticipated questions
        
        Return the response as a JSON object with the following structure:
        {{
            "slides": [
                {{
                    "slide_number": 1,
                    "title": "Slide Title",
                    "content": "Slide content",
                    "visuals": "Visual recommendations",
                    "notes": "Presentation notes"
                }}
            ],
            "presentation_notes": "Comprehensive presentation notes",
            "key_talking_points": ["Point 1", "Point 2", "Point 3"],
            "anticipated_questions": [
                {{
                    "question": "Anticipated question",
                    "answer": "Prepared answer",
                    "category": "Question category"
                }}
            ]
        }}
        """
    
    def _create_financial_projections_prompt(
        self,
        investment_pitch: InvestmentPitch,
        projection_years: int,
        include_scenarios: bool
    ) -> str:
        return f"""
        Create financial projections for:
        - Funding Amount: ${investment_pitch.funding_amount:,.2f}
        - Use of Funds: {investment_pitch.use_of_funds}
        - Projection Years: {projection_years}
        - Include Scenarios: {include_scenarios}
        
        Develop comprehensive financial projections including:
        1. Revenue projections
        2. Expense projections
        3. Profit projections
        4. Cash flow projections
        5. Scenario analysis
        6. Key metrics
        
        Return the response as a JSON object with the following structure:
        {{
            "revenue_projections": {{
                "year_1": 100000,
                "year_2": 250000,
                "year_3": 500000,
                "growth_rate": 150.0
            }},
            "expense_projections": {{
                "year_1": 80000,
                "year_2": 180000,
                "year_3": 350000
            }},
            "profit_projections": {{
                "year_1": 20000,
                "year_2": 70000,
                "year_3": 150000
            }},
            "cash_flow_projections": {{
                "year_1": 15000,
                "year_2": 60000,
                "year_3": 140000
            }},
            "scenario_analysis": {{
                "optimistic": "Optimistic scenario",
                "realistic": "Realistic scenario",
                "pessimistic": "Pessimistic scenario"
            }},
            "key_metrics": {{
                "roi": 300.0,
                "payback_period": "24 months",
                "irr": 45.0
            }}
        }}
        """
    
    def _create_investor_materials_prompt(
        self,
        investment_pitch: InvestmentPitch,
        material_types: List[str]
    ) -> str:
        return f"""
        Generate investor materials for:
        - Funding Amount: ${investment_pitch.funding_amount:,.2f}
        - Equity Offered: {investment_pitch.equity_offered}%
        - Material Types: {', '.join(material_types)}
        
        Create comprehensive investor materials including:
        1. Executive summary
        2. Business plan
        3. Financial model
        4. Due diligence package
        5. Investor presentation
        
        Return the response as a JSON object with the following structure:
        {{
            "executive_summary": "Executive summary content",
            "business_plan": "Business plan content",
            "financial_model": {{
                "assumptions": "Financial assumptions",
                "projections": "Financial projections",
                "sensitivity_analysis": "Sensitivity analysis"
            }},
            "due_diligence_package": {{
                "legal_documents": "Legal document requirements",
                "financial_statements": "Financial statement requirements",
                "market_research": "Market research requirements"
            }},
            "investor_presentation": "Investor presentation content"
        }}
        """
