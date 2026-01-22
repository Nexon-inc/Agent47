from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import PurityBusinessIdea, PurityFinancialForecast, PurityBusinessModel, PurityMarketResearch
from ..services.financial_planning_service import FinancialPlanningService

router = APIRouter(prefix="/financial-planning", tags=["Financial Planning"])

class FinancialForecastRequest(BaseModel):
    business_idea_id: int
    forecast_period_months: int = Field(12, ge=1, le=60)
    initial_investment: float = Field(..., ge=0)
    monthly_operating_costs: float = Field(..., ge=0)
    expected_monthly_revenue: float = Field(..., ge=0)
    growth_rate_percentage: float = Field(5.0, ge=0, le=100)
    include_sensitivity_analysis: bool = True

class FinancialForecastResponse(BaseModel):
    id: int
    business_idea_id: int
    forecast_period_months: int
    initial_investment: float
    monthly_operating_costs: float
    expected_monthly_revenue: float
    growth_rate_percentage: float
    projected_revenue: List[float]
    projected_costs: List[float]
    projected_profit: List[float]
    projected_cash_flow: List[float]
    roi_percentage: float
    payback_period_months: float
    sensitivity_analysis: Optional[dict]
    created_at: datetime
    updated_at: datetime

class BreakEvenRequest(BaseModel):
    business_idea_id: int
    fixed_costs: float = Field(..., ge=0)
    variable_cost_per_unit: float = Field(..., ge=0)
    selling_price_per_unit: float = Field(..., ge=0)
    target_profit: float = Field(0, ge=0)

class BreakEvenResponse(BaseModel):
    id: int
    business_idea_id: int
    break_even_units: float
    break_even_revenue: float
    break_even_months: float
    margin_of_safety: float
    contribution_margin: float
    target_profit_units: float
    target_profit_revenue: float
    insights: str
    created_at: datetime

class BusinessValuationRequest(BaseModel):
    business_idea_id: int
    current_revenue: float = Field(..., ge=0)
    current_profit: float = Field(..., ge=0)
    growth_rate: float = Field(..., ge=0)
    industry_multiplier: float = Field(2.5, ge=0.5, le=10.0)
    discount_rate: float = Field(0.15, ge=0.05, le=0.30)
    assets_value: float = Field(0, ge=0)

class BusinessValuationResponse(BaseModel):
    id: int
    business_idea_id: int
    dcf_valuation: float
    multiples_valuation: float
    asset_based_valuation: float
    weighted_average_valuation: float
    valuation_range: dict
    key_factors: List[str]
    risk_assessment: str
    created_at: datetime

class TaxPlanningRequest(BaseModel):
    business_idea_id: int
    business_location: str
    business_type: str
    expected_annual_revenue: float = Field(..., ge=0)
    expected_annual_expenses: float = Field(..., ge=0)
    employee_count: int = Field(0, ge=0)
    has_international_operations: bool = False

class TaxPlanningResponse(BaseModel):
    id: int
    business_idea_id: int
    business_location: str
    business_type: str
    tax_obligations: List[dict]
    tax_optimization_strategies: List[str]
    required_registrations: List[str]
    compliance_checklist: List[str]
    estimated_tax_liability: float
    tax_savings_opportunities: List[str]
    created_at: datetime

@router.post("/forecast", response_model=FinancialForecastResponse)
async def generate_financial_forecast(
    request: FinancialForecastRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = FinancialPlanningService()
        forecast = await service.generate_financial_forecast(
            db=db,
            business_idea_id=request.business_idea_id,
            forecast_period_months=request.forecast_period_months,
            initial_investment=request.initial_investment,
            monthly_operating_costs=request.monthly_operating_costs,
            expected_monthly_revenue=request.expected_monthly_revenue,
            growth_rate_percentage=request.growth_rate_percentage,
            include_sensitivity_analysis=request.include_sensitivity_analysis
        )
        return FinancialForecastResponse(
            id=forecast.id,
            business_idea_id=forecast.business_idea_id,
            forecast_period_months=forecast.forecast_period_months,
            initial_investment=forecast.initial_investment,
            monthly_operating_costs=forecast.monthly_operating_costs,
            expected_monthly_revenue=forecast.expected_monthly_revenue,
            growth_rate_percentage=forecast.growth_rate_percentage,
            projected_revenue=json.loads(forecast.projected_revenue),
            projected_costs=json.loads(forecast.projected_costs),
            projected_profit=json.loads(forecast.projected_profit),
            projected_cash_flow=json.loads(forecast.projected_cash_flow),
            roi_percentage=forecast.roi_percentage,
            payback_period_months=forecast.payback_period_months,
            sensitivity_analysis=json.loads(forecast.sensitivity_analysis) if forecast.sensitivity_analysis else None,
            created_at=forecast.created_at,
            updated_at=forecast.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/break-even", response_model=BreakEvenResponse)
async def calculate_break_even_analysis(
    request: BreakEvenRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = FinancialPlanningService()
        break_even = await service.calculate_break_even_analysis(
            db=db,
            business_idea_id=request.business_idea_id,
            fixed_costs=request.fixed_costs,
            variable_cost_per_unit=request.variable_cost_per_unit,
            selling_price_per_unit=request.selling_price_per_unit,
            target_profit=request.target_profit
        )
        return BreakEvenResponse(
            id=break_even.id,
            business_idea_id=break_even.business_idea_id,
            break_even_units=break_even.break_even_units,
            break_even_revenue=break_even.break_even_revenue,
            break_even_months=break_even.break_even_months,
            margin_of_safety=break_even.margin_of_safety,
            contribution_margin=break_even.contribution_margin,
            target_profit_units=break_even.target_profit_units,
            target_profit_revenue=break_even.target_profit_revenue,
            insights=break_even.insights,
            created_at=break_even.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/valuation", response_model=BusinessValuationResponse)
async def estimate_business_valuation(
    request: BusinessValuationRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = FinancialPlanningService()
        valuation = await service.estimate_business_valuation(
            db=db,
            business_idea_id=request.business_idea_id,
            current_revenue=request.current_revenue,
            current_profit=request.current_profit,
            growth_rate=request.growth_rate,
            industry_multiplier=request.industry_multiplier,
            discount_rate=request.discount_rate,
            assets_value=request.assets_value
        )
        return BusinessValuationResponse(
            id=valuation.id,
            business_idea_id=valuation.business_idea_id,
            dcf_valuation=valuation.dcf_valuation,
            multiples_valuation=valuation.multiples_valuation,
            asset_based_valuation=valuation.asset_based_valuation,
            weighted_average_valuation=valuation.weighted_average_valuation,
            valuation_range=json.loads(valuation.valuation_range),
            key_factors=json.loads(valuation.key_factors),
            risk_assessment=valuation.risk_assessment,
            created_at=valuation.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/tax-planning", response_model=TaxPlanningResponse)
async def create_tax_planning_strategy(
    request: TaxPlanningRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = FinancialPlanningService()
        tax_plan = await service.create_tax_planning_strategy(
            db=db,
            business_idea_id=request.business_idea_id,
            business_location=request.business_location,
            business_type=request.business_type,
            expected_annual_revenue=request.expected_annual_revenue,
            expected_annual_expenses=request.expected_annual_expenses,
            employee_count=request.employee_count,
            has_international_operations=request.has_international_operations
        )
        return TaxPlanningResponse(
            id=tax_plan.id,
            business_idea_id=tax_plan.business_idea_id,
            business_location=tax_plan.business_location,
            business_type=tax_plan.business_type,
            tax_obligations=json.loads(tax_plan.tax_obligations),
            tax_optimization_strategies=json.loads(tax_plan.tax_optimization_strategies),
            required_registrations=json.loads(tax_plan.required_registrations),
            compliance_checklist=json.loads(tax_plan.compliance_checklist),
            estimated_tax_liability=tax_plan.estimated_tax_liability,
            tax_savings_opportunities=json.loads(tax_plan.tax_savings_opportunities),
            created_at=tax_plan.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/forecast/{forecast_id}", response_model=FinancialForecastResponse)
async def get_financial_forecast(
    forecast_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityFinancialForecast).where(PurityFinancialForecast.id == forecast_id))
        forecast = result.scalar_one_or_none()
        if not forecast:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial forecast not found")
        return FinancialForecastResponse(
            id=forecast.id,
            business_idea_id=forecast.business_idea_id,
            forecast_period_months=forecast.forecast_period_months,
            initial_investment=forecast.initial_investment,
            monthly_operating_costs=forecast.monthly_operating_costs,
            expected_monthly_revenue=forecast.expected_monthly_revenue,
            growth_rate_percentage=forecast.growth_rate_percentage,
            projected_revenue=json.loads(forecast.projected_revenue),
            projected_costs=json.loads(forecast.projected_costs),
            projected_profit=json.loads(forecast.projected_profit),
            projected_cash_flow=json.loads(forecast.projected_cash_flow),
            roi_percentage=forecast.roi_percentage,
            payback_period_months=forecast.payback_period_months,
            sensitivity_analysis=json.loads(forecast.sensitivity_analysis) if forecast.sensitivity_analysis else None,
            created_at=forecast.created_at,
            updated_at=forecast.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/forecast/business/{business_idea_id}", response_model=List[FinancialForecastResponse])
async def get_business_forecasts(
    business_idea_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityFinancialForecast).where(PurityFinancialForecast.business_idea_id == business_idea_id))
        forecasts = result.scalars().all()
        return [
            FinancialForecastResponse(
                id=forecast.id,
                business_idea_id=forecast.business_idea_id,
                forecast_period_months=forecast.forecast_period_months,
                initial_investment=forecast.initial_investment,
                monthly_operating_costs=forecast.monthly_operating_costs,
                expected_monthly_revenue=forecast.expected_monthly_revenue,
                growth_rate_percentage=forecast.growth_rate_percentage,
                projected_revenue=json.loads(forecast.projected_revenue),
                projected_costs=json.loads(forecast.projected_costs),
                projected_profit=json.loads(forecast.projected_profit),
                projected_cash_flow=json.loads(forecast.projected_cash_flow),
                roi_percentage=forecast.roi_percentage,
                payback_period_months=forecast.payback_period_months,
                sensitivity_analysis=json.loads(forecast.sensitivity_analysis) if forecast.sensitivity_analysis else None,
                created_at=forecast.created_at,
                updated_at=forecast.updated_at
            )
            for forecast in forecasts
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/forecast/{forecast_id}")
async def delete_financial_forecast(
    forecast_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityFinancialForecast).where(PurityFinancialForecast.id == forecast_id))
        forecast = result.scalar_one_or_none()
        if not forecast:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial forecast not found")
        await db.delete(forecast)
        await db.commit()
        return {"message": "Financial forecast deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
