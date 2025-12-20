import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload
import json
import openai
from core.config import settings
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import EventBus
from core.cache.redis_manager import init_redis
from ..database import get_purity_database
from ..models import (
    BusinessIdea, FinancialForecast, BusinessModel, PurityMarketResearch,
    RevenueModel
)

logger = logging.getLogger(__name__)

class FinancialPlanningService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = EventBus()
        self.redis_client = None
        self._initialized = False
        self._financial_assumptions = {
            "default_margin": 0.3,
            "growth_rate": 0.15,
            "discount_rate": 0.1,
            "tax_rate": 0.25,
            "inflation_rate": 0.02,
            "working_capital_ratio": 0.2
        }
    
    async def initialize(self):
        """Initialize financial planning service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.event_bus.initialize()
            self.redis_client = await init_redis()
            self._initialized = True
            logger.info("Financial planning service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize financial planning service: {e}")
            raise
    
    async def generate_financial_forecast(
        self,
        idea_id: int,
        forecast_period: int = 36,
        assumptions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive financial forecasts"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_purity_database()
            async with db.get_session() as session:
                # Get idea and related data
                idea_query = select(BusinessIdea).where(BusinessIdea.id == idea_id)
                idea_result = await session.execute(idea_query)
                idea = idea_result.scalar_one_or_none()
                
                if not idea:
                    return {"success": False, "error": "Idea not found"}
                
                # Get business model and market research
                business_model_query = select(BusinessModel).where(BusinessModel.idea_id == idea_id)
                business_model_result = await session.execute(business_model_query)
                business_model = business_model_result.scalar_one_or_none()
                
                market_research_query = select(PurityMarketResearch).where(PurityMarketResearch.idea_id == idea_id)
                market_research_result = await session.execute(market_research_query)
                market_research = market_research_result.scalar_one_or_none()
                
                # Generate financial forecast using AI
                forecast_data = await self._generate_forecast_with_ai(
                    idea, business_model, market_research, forecast_period, assumptions
                )
                
                # Save financial forecast
                financial_forecast = FinancialForecast(
                    idea_id=idea_id,
                    forecast_period=forecast_period,
                    revenue_projections=forecast_data["revenue_projections"],
                    cost_projections=forecast_data["cost_projections"],
                    profit_projections=forecast_data["profit_projections"],
                    cash_flow_projections=forecast_data["cash_flow_projections"],
                    break_even_analysis=forecast_data["break_even_analysis"],
                    funding_requirements=forecast_data["funding_requirements"],
                    roi_projections=forecast_data["roi_projections"],
                    sensitivity_analysis=forecast_data["sensitivity_analysis"],
                    assumptions=forecast_data["assumptions"]
                )
                
                session.add(financial_forecast)
                await session.commit()
                
                # Publish forecast completion event
                await self.event_bus.publish(
                    "financial.forecast.completed",
                    {
                        "idea_id": idea_id,
                        "forecast_period": forecast_period,
                        "total_revenue": forecast_data["total_revenue"],
                        "break_even_month": forecast_data["break_even_analysis"]["break_even_month"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return {
                    "success": True,
                    "financial_forecast": financial_forecast,
                    "forecast_data": forecast_data
                }
                
        except Exception as e:
            logger.error(f"Failed to generate financial forecast: {e}")
            return {"success": False, "error": str(e)}
    
    async def calculate_break_even_analysis(
        self,
        idea_id: int,
        detailed_analysis: bool = True
    ) -> Dict[str, Any]:
        """Calculate detailed break-even analysis"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_purity_database()
            async with db.get_session() as session:
                # Get idea and financial data
                idea_query = select(BusinessIdea).where(BusinessIdea.id == idea_id)
                idea_result = await session.execute(idea_query)
                idea = idea_result.scalar_one_or_none()
                
                if not idea:
                    return {"success": False, "error": "Idea not found"}
                
                # Get existing financial forecast
                forecast_query = select(FinancialForecast).where(FinancialForecast.idea_id == idea_id)
                forecast_result = await session.execute(forecast_query)
                forecast = forecast_result.scalar_one_or_none()
                
                if not forecast:
                    return {"success": False, "error": "Financial forecast not found. Generate forecast first."}
                
                # Perform break-even analysis
                break_even_data = await self._perform_break_even_analysis(idea, forecast, detailed_analysis)
                
                # Update forecast with new break-even data
                forecast.break_even_analysis = break_even_data
                await session.commit()
                
                return {
                    "success": True,
                    "break_even_analysis": break_even_data
                }
                
        except Exception as e:
            logger.error(f"Failed to calculate break-even analysis: {e}")
            return {"success": False, "error": str(e)}
    
    async def estimate_business_valuation(
        self,
        idea_id: int,
        valuation_method: str = "dcf",
        exit_year: int = 5
    ) -> Dict[str, Any]:
        """Estimate business valuation using multiple methods"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_purity_database()
            async with db.get_session() as session:
                # Get idea and financial data
                idea_query = select(BusinessIdea).where(BusinessIdea.id == idea_id)
                idea_result = await session.execute(idea_query)
                idea = idea_result.scalar_one_or_none()
                
                if not idea:
                    return {"success": False, "error": "Idea not found"}
                
                # Get financial forecast
                forecast_query = select(FinancialForecast).where(FinancialForecast.idea_id == idea_id)
                forecast_result = await session.execute(forecast_query)
                forecast = forecast_result.scalar_one_or_none()
                
                if not forecast:
                    return {"success": False, "error": "Financial forecast not found. Generate forecast first."}
                
                # Perform valuation analysis
                valuation_data = await self._perform_valuation_analysis(
                    idea, forecast, valuation_method, exit_year
                )
                
                return {
                    "success": True,
                    "valuation_data": valuation_data
                }
                
        except Exception as e:
            logger.error(f"Failed to estimate business valuation: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_tax_planning_strategy(
        self,
        idea_id: int,
        business_location: str,
        business_structure: str = "llc"
    ) -> Dict[str, Any]:
        """Create tax planning strategy"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_purity_database()
            async with db.get_session() as session:
                # Get idea details
                idea_query = select(BusinessIdea).where(BusinessIdea.id == idea_id)
                idea_result = await session.execute(idea_query)
                idea = idea_result.scalar_one_or_none()
                
                if not idea:
                    return {"success": False, "error": "Idea not found"}
                
                # Generate tax planning strategy
                tax_strategy = await self._generate_tax_strategy(idea, business_location, business_structure)
                
                return {
                    "success": True,
                    "tax_strategy": tax_strategy
                }
                
        except Exception as e:
            logger.error(f"Failed to create tax planning strategy: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_forecast_with_ai(
        self,
        idea: BusinessIdea,
        business_model: Optional[BusinessModel],
        market_research: Optional[PurityMarketResearch],
        forecast_period: int,
        assumptions: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate financial forecast using AI"""
        try:
            # Merge assumptions
            final_assumptions = {**self._financial_assumptions}
            if assumptions:
                final_assumptions.update(assumptions)
            
            prompt = f"""
            Generate a comprehensive financial forecast for this business idea:
            
            Business: {idea.title}
            Industry: {idea.industry.value}
            Target Market: {idea.target_market}
            Revenue Potential: ${idea.revenue_potential:,.0f}
            Startup Cost: ${idea.startup_cost:,.0f}
            Forecast Period: {forecast_period} months
            
            Business Model: {json.dumps(business_model.__dict__ if business_model else {}, indent=2)}
            Market Research: {json.dumps(market_research.__dict__ if market_research else {}, indent=2)}
            
            Financial Assumptions: {json.dumps(final_assumptions, indent=2)}
            
            Generate:
            1. Monthly Revenue Projections (array of {forecast_period} values)
            2. Monthly Cost Projections (array of {forecast_period} values)
            3. Monthly Profit Projections (array of {forecast_period} values)
            4. Monthly Cash Flow Projections (array of {forecast_period} values)
            5. Break-even Analysis (break_even_month, break_even_revenue, break_even_customers)
            6. Funding Requirements (total_funding_needed, funding_rounds)
            7. ROI Projections (roi_percentage, payback_period)
            8. Sensitivity Analysis (best_case, worst_case, base_case)
            9. Key Assumptions Used
            
            Format as JSON.
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self._ai_config["financial_forecasting"]["model"],
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst and CFO with deep knowledge of startup financial modeling and forecasting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self._ai_config["financial_forecasting"]["temperature"],
                max_tokens=self._ai_config["financial_forecasting"]["max_tokens"]
            )
            
            content = response.choices[0].message.content
            forecast_data = json.loads(content)
            
            # Calculate total revenue
            total_revenue = sum(forecast_data.get("revenue_projections", []))
            forecast_data["total_revenue"] = total_revenue
            
            return forecast_data
            
        except Exception as e:
            logger.error(f"Failed to generate forecast with AI: {e}")
            return self._generate_default_forecast(forecast_period)
    
    async def _perform_break_even_analysis(
        self,
        idea: BusinessIdea,
        forecast: FinancialForecast,
        detailed_analysis: bool
    ) -> Dict[str, Any]:
        """Perform detailed break-even analysis"""
        try:
            revenue_projections = forecast.revenue_projections or []
            cost_projections = forecast.cost_projections or []
            
            if not revenue_projections or not cost_projections:
                return {"error": "Insufficient financial data"}
            
            # Find break-even point
            break_even_month = None
            cumulative_profit = 0
            
            for month in range(len(revenue_projections)):
                monthly_profit = revenue_projections[month] - cost_projections[month]
                cumulative_profit += monthly_profit
                
                if cumulative_profit >= 0 and break_even_month is None:
                    break_even_month = month + 1
            
            # Calculate break-even metrics
            if break_even_month:
                break_even_revenue = revenue_projections[break_even_month - 1]
                break_even_costs = cost_projections[break_even_month - 1]
                
                # Estimate break-even customers (assuming average revenue per customer)
                avg_revenue_per_customer = idea.revenue_potential / 1000  # Rough estimate
                break_even_customers = break_even_revenue / avg_revenue_per_customer if avg_revenue_per_customer > 0 else 0
            else:
                break_even_revenue = 0
                break_even_costs = 0
                break_even_customers = 0
            
            break_even_data = {
                "break_even_month": break_even_month,
                "break_even_revenue": break_even_revenue,
                "break_even_costs": break_even_costs,
                "break_even_customers": break_even_customers,
                "cumulative_profit_at_break_even": cumulative_profit if break_even_month else None,
                "analysis_date": datetime.utcnow().isoformat()
            }
            
            if detailed_analysis:
                # Add detailed analysis using AI
                detailed_analysis = await self._generate_break_even_insights(idea, break_even_data)
                break_even_data["detailed_analysis"] = detailed_analysis
            
            return break_even_data
            
        except Exception as e:
            logger.error(f"Failed to perform break-even analysis: {e}")
            return {"error": str(e)}
    
    async def _perform_valuation_analysis(
        self,
        idea: BusinessIdea,
        forecast: FinancialForecast,
        valuation_method: str,
        exit_year: int
    ) -> Dict[str, Any]:
        """Perform business valuation analysis"""
        try:
            # Get financial projections
            revenue_projections = forecast.revenue_projections or []
            profit_projections = forecast.profit_projections or []
            
            if not revenue_projections or not profit_projections:
                return {"error": "Insufficient financial data"}
            
            # Calculate key metrics
            total_revenue = sum(revenue_projections)
            total_profit = sum(profit_projections)
            avg_annual_profit = total_profit / (len(profit_projections) / 12) if profit_projections else 0
            
            # Perform different valuation methods
            valuations = {}
            
            # DCF Valuation
            if valuation_method in ["dcf", "all"]:
                dcf_value = await self._calculate_dcf_valuation(forecast, exit_year)
                valuations["dcf"] = dcf_value
            
            # Multiple-based Valuation
            if valuation_method in ["multiple", "all"]:
                multiple_value = await self._calculate_multiple_valuation(idea, avg_annual_profit)
                valuations["multiple"] = multiple_value
            
            # Asset-based Valuation
            if valuation_method in ["asset", "all"]:
                asset_value = await self._calculate_asset_valuation(idea, forecast)
                valuations["asset"] = asset_value
            
            # Generate valuation insights using AI
            valuation_insights = await self._generate_valuation_insights(idea, valuations, forecast)
            
            return {
                "valuation_methods": valuations,
                "key_metrics": {
                    "total_revenue": total_revenue,
                    "total_profit": total_profit,
                    "avg_annual_profit": avg_annual_profit,
                    "exit_year": exit_year
                },
                "insights": valuation_insights,
                "valuation_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to perform valuation analysis: {e}")
            return {"error": str(e)}
    
    async def _generate_tax_strategy(
        self,
        idea: BusinessIdea,
        business_location: str,
        business_structure: str
    ) -> Dict[str, Any]:
        """Generate tax planning strategy using AI"""
        try:
            prompt = f"""
            Create a comprehensive tax planning strategy for this business:
            
            Business: {idea.title}
            Industry: {idea.industry.value}
            Location: {business_location}
            Business Structure: {business_structure}
            Revenue Potential: ${idea.revenue_potential:,.0f}
            
            Provide:
            1. Tax Obligations
            2. Deductions and Credits
            3. Tax Optimization Strategies
            4. Compliance Requirements
            5. Tax Calendar
            6. Estimated Tax Burden
            7. Recommendations
            
            Format as JSON.
            """
            
            response = await openai.ChatCompletion.acreate(
                model="grok-llm",
                messages=[
                    {"role": "system", "content": "You are an expert tax advisor and CPA with deep knowledge of business taxation and tax optimization strategies."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Failed to generate tax strategy: {e}")
            return {"error": str(e)}
    
    async def _generate_break_even_insights(
        self,
        idea: BusinessIdea,
        break_even_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights for break-even analysis"""
        try:
            prompt = f"""
            Provide insights and recommendations for this break-even analysis:
            
            Business: {idea.title}
            Break-even Month: {break_even_data.get('break_even_month')}
            Break-even Revenue: ${break_even_data.get('break_even_revenue', 0):,.0f}
            Break-even Customers: {break_even_data.get('break_even_customers', 0):.0f}
            
            Provide:
            1. Analysis of Break-even Timeline
            2. Risk Factors
            3. Optimization Strategies
            4. Cash Flow Management
            5. Recommendations
            
            Format as JSON.
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self._ai_config["break_even_analysis"]["model"],
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst specializing in break-even analysis and cash flow management."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self._ai_config["break_even_analysis"]["temperature"],
                max_tokens=self._ai_config["break_even_analysis"]["max_tokens"]
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Failed to generate break-even insights: {e}")
            return {"error": str(e)}
    
    async def _calculate_dcf_valuation(
        self,
        forecast: FinancialForecast,
        exit_year: int
    ) -> Dict[str, Any]:
        """Calculate Discounted Cash Flow valuation"""
        try:
            cash_flow_projections = forecast.cash_flow_projections or []
            
            if not cash_flow_projections:
                return {"value": 0, "error": "No cash flow data"}
            
            # Calculate present value of cash flows
            discount_rate = self._financial_assumptions["discount_rate"]
            present_value = 0
            
            for month, cash_flow in enumerate(cash_flow_projections):
                if month < exit_year * 12:  # Only consider cash flows up to exit year
                    present_value += cash_flow / ((1 + discount_rate) ** (month / 12))
            
            # Add terminal value (simplified)
            terminal_value = cash_flow_projections[-1] * (1 + self._financial_assumptions["growth_rate"]) / (discount_rate - self._financial_assumptions["growth_rate"])
            terminal_value_pv = terminal_value / ((1 + discount_rate) ** exit_year)
            
            total_value = present_value + terminal_value_pv
            
            return {
                "value": total_value,
                "present_value_cash_flows": present_value,
                "terminal_value": terminal_value_pv,
                "discount_rate": discount_rate,
                "exit_year": exit_year
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate DCF valuation: {e}")
            return {"value": 0, "error": str(e)}
    
    async def _calculate_multiple_valuation(
        self,
        idea: BusinessIdea,
        avg_annual_profit: float
    ) -> Dict[str, Any]:
        """Calculate multiple-based valuation"""
        try:
            # Industry-specific multiples (simplified)
            industry_multiples = {
                "technology": 15,
                "healthcare": 12,
                "finance": 10,
                "education": 8,
                "retail": 6,
                "manufacturing": 8,
                "services": 10,
                "entertainment": 12,
                "food_beverage": 8,
                "real_estate": 10,
                "transportation": 8,
                "energy": 12,
                "other": 10
            }
            
            multiple = industry_multiples.get(idea.industry.value, 10)
            valuation = avg_annual_profit * multiple
            
            return {
                "value": valuation,
                "multiple": multiple,
                "avg_annual_profit": avg_annual_profit,
                "industry": idea.industry.value
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate multiple valuation: {e}")
            return {"value": 0, "error": str(e)}
    
    async def _calculate_asset_valuation(
        self,
        idea: BusinessIdea,
        forecast: FinancialForecast
    ) -> Dict[str, Any]:
        """Calculate asset-based valuation"""
        try:
            # Simplified asset valuation
            startup_cost = idea.startup_cost or 0
            accumulated_profits = sum(forecast.profit_projections or [])
            
            # Add intangible assets (brand value, IP, etc.)
            intangible_assets = startup_cost * 0.3  # 30% of startup cost as intangible
            
            total_assets = startup_cost + accumulated_profits + intangible_assets
            
            return {
                "value": total_assets,
                "tangible_assets": startup_cost,
                "accumulated_profits": accumulated_profits,
                "intangible_assets": intangible_assets
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate asset valuation: {e}")
            return {"value": 0, "error": str(e)}
    
    async def _generate_valuation_insights(
        self,
        idea: BusinessIdea,
        valuations: Dict[str, Any],
        forecast: FinancialForecast
    ) -> Dict[str, Any]:
        """Generate valuation insights using AI"""
        try:
            prompt = f"""
            Provide insights and analysis for this business valuation:
            
            Business: {idea.title}
            Industry: {idea.industry.value}
            Valuations: {json.dumps(valuations, indent=2)}
            
            Provide:
            1. Valuation Analysis
            2. Key Drivers
            3. Risk Factors
            4. Growth Opportunities
            5. Recommendations
            
            Format as JSON.
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self._ai_config["valuation"]["model"],
                messages=[
                    {"role": "system", "content": "You are an expert business valuator and investment analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self._ai_config["valuation"]["temperature"],
                max_tokens=self._ai_config["valuation"]["max_tokens"]
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Failed to generate valuation insights: {e}")
            return {"error": str(e)}
    
    def _generate_default_forecast(self, forecast_period: int) -> Dict[str, Any]:
        """Generate default forecast when AI fails"""
        try:
            # Generate simple linear growth forecast
            revenue_projections = []
            cost_projections = []
            profit_projections = []
            cash_flow_projections = []
            
            base_revenue = 10000  # $10K starting revenue
            base_costs = 8000     # $8K starting costs
            growth_rate = 0.1     # 10% monthly growth
            
            for month in range(forecast_period):
                revenue = base_revenue * (1 + growth_rate) ** month
                costs = base_costs * (1 + growth_rate * 0.8) ** month  # Costs grow slower
                profit = revenue - costs
                cash_flow = profit - (base_costs * 0.2)  # Assume 20% of costs are non-cash
                
                revenue_projections.append(revenue)
                cost_projections.append(costs)
                profit_projections.append(profit)
                cash_flow_projections.append(cash_flow)
            
            return {
                "revenue_projections": revenue_projections,
                "cost_projections": cost_projections,
                "profit_projections": profit_projections,
                "cash_flow_projections": cash_flow_projections,
                "break_even_analysis": {
                    "break_even_month": 6,
                    "break_even_revenue": 15000,
                    "break_even_customers": 150
                },
                "funding_requirements": {
                    "total_funding_needed": 50000,
                    "funding_rounds": [{"amount": 25000, "month": 0}, {"amount": 25000, "month": 12}]
                },
                "roi_projections": {
                    "roi_percentage": 150,
                    "payback_period": 18
                },
                "sensitivity_analysis": {
                    "best_case": {"revenue_multiplier": 1.5, "cost_multiplier": 0.8},
                    "worst_case": {"revenue_multiplier": 0.7, "cost_multiplier": 1.2},
                    "base_case": {"revenue_multiplier": 1.0, "cost_multiplier": 1.0}
                },
                "assumptions": self._financial_assumptions,
                "total_revenue": sum(revenue_projections)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate default forecast: {e}")
            return {
                "revenue_projections": [],
                "cost_projections": [],
                "profit_projections": [],
                "cash_flow_projections": [],
                "break_even_analysis": {},
                "funding_requirements": {},
                "roi_projections": {},
                "sensitivity_analysis": {},
                "assumptions": {},
                "total_revenue": 0
            }
