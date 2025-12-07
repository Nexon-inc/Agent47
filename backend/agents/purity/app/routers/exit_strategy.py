from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import BusinessIdea, ExitStrategy, BusinessModel
from ..services.exit_strategy_service import ExitStrategyService

router = APIRouter(prefix="/exit-strategy", tags=["Exit Strategy"])

class ExitStrategyRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    exit_timeline: str = Field(..., description="Desired exit timeline")
    exit_valuation: float = Field(..., ge=0, description="Target exit valuation")
    exit_type: str = Field(..., description="Preferred exit type")
    industry_landscape: Dict[str, Any] = Field(..., description="Industry landscape data")

class ExitOptionsRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    company_stage: str = Field(..., description="Current company stage")
    market_conditions: str = Field(..., description="Current market conditions")
    financial_performance: Dict[str, Any] = Field(..., description="Financial performance data")

class ExitPlanRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    exit_strategy_id: int = Field(..., description="Exit strategy ID")
    preparation_timeline: str = Field(..., description="Preparation timeline")
    key_milestones: List[str] = Field(..., description="Key milestones to achieve")

@router.post("/create")
async def create_exit_strategy(
    request: ExitStrategyRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create a comprehensive exit strategy"""
    try:
        service = ExitStrategyService()
        result = await service.create_exit_strategy(
            db=db,
            business_idea_id=request.business_idea_id,
            exit_timeline=request.exit_timeline,
            exit_valuation=request.exit_valuation,
            exit_type=request.exit_type,
            industry_landscape=request.industry_landscape
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Exit strategy created for {request.exit_type} exit with ${request.exit_valuation:,.2f} valuation"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create exit strategy: {str(e)}"
        )

@router.post("/analyze-options")
async def analyze_exit_options(
    request: ExitOptionsRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Analyze different exit options and their feasibility"""
    try:
        service = ExitStrategyService()
        result = await service.analyze_exit_options(
            db=db,
            business_idea_id=request.business_idea_id,
            company_stage=request.company_stage,
            market_conditions=request.market_conditions,
            financial_performance=request.financial_performance
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Exit options analyzed for {request.company_stage} stage company"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze exit options: {str(e)}"
        )

@router.post("/develop-plan")
async def develop_exit_plan(
    request: ExitPlanRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Develop a detailed exit execution plan"""
    try:
        service = ExitStrategyService()
        result = await service.develop_exit_plan(
            db=db,
            business_idea_id=request.business_idea_id,
            exit_strategy_id=request.exit_strategy_id,
            preparation_timeline=request.preparation_timeline,
            key_milestones=request.key_milestones
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Exit plan developed with {len(request.key_milestones)} key milestones"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to develop exit plan: {str(e)}"
        )

@router.get("/exit-types")
async def get_exit_types(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get different types of exit strategies and their characteristics"""
    try:
        exit_types = {
            "acquisition": {
                "name": "Strategic Acquisition",
                "description": "Selling to a larger company in the same or related industry",
                "typical_valuation": "3-10x revenue or 15-25x EBITDA",
                "timeline": "6-18 months",
                "advantages": [
                    "Higher valuations possible",
                    "Strategic synergies",
                    "Faster execution",
                    "Access to resources"
                ],
                "disadvantages": [
                    "Cultural integration challenges",
                    "Loss of control",
                    "Complex negotiations",
                    "Regulatory approvals"
                ],
                "best_for": "Companies with strong market position and strategic value"
            },
            "ipo": {
                "name": "Initial Public Offering",
                "description": "Going public through stock market listing",
                "typical_valuation": "10-20x revenue or 20-40x EBITDA",
                "timeline": "12-24 months",
                "advantages": [
                    "Highest potential valuation",
                    "Liquidity for shareholders",
                    "Access to capital markets",
                    "Enhanced brand recognition"
                ],
                "disadvantages": [
                    "Complex regulatory requirements",
                    "High costs and fees",
                    "Public scrutiny",
                    "Quarterly reporting obligations"
                ],
                "best_for": "Large, profitable companies with strong growth"
            },
            "management_buyout": {
                "name": "Management Buyout (MBO)",
                "description": "Selling to existing management team",
                "typical_valuation": "3-7x EBITDA",
                "timeline": "3-12 months",
                "advantages": [
                    "Preserves company culture",
                    "Faster execution",
                    "Lower transaction costs",
                    "Management continuity"
                ],
                "disadvantages": [
                    "Lower valuations",
                    "Limited capital for growth",
                    "Management debt burden",
                    "Conflict of interest"
                ],
                "best_for": "Stable companies with strong management teams"
            },
            "private_equity": {
                "name": "Private Equity Sale",
                "description": "Selling to a private equity firm",
                "typical_valuation": "5-12x EBITDA",
                "timeline": "6-15 months",
                "advantages": [
                    "Good valuations",
                    "Operational expertise",
                    "Growth capital",
                    "Flexible deal structures"
                ],
                "disadvantages": [
                    "High debt levels",
                    "Pressure for growth",
                    "Management changes",
                    "Exit timeline pressure"
                ],
                "best_for": "Profitable companies with growth potential"
            },
            "merger": {
                "name": "Merger of Equals",
                "description": "Combining with a similar-sized company",
                "typical_valuation": "Market-based multiples",
                "timeline": "9-18 months",
                "advantages": [
                    "Synergy opportunities",
                    "Shared resources",
                    "Market expansion",
                    "Risk diversification"
                ],
                "disadvantages": [
                    "Complex integration",
                    "Cultural challenges",
                    "Regulatory hurdles",
                    "Leadership conflicts"
                ],
                "best_for": "Companies seeking scale and market expansion"
            }
        }
        return {
            "status": "success",
            "data": exit_types,
            "message": "Exit types retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve exit types: {str(e)}"
        )

@router.get("/valuation-methods")
async def get_valuation_methods(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get different business valuation methods and their applications"""
    try:
        valuation_methods = {
            "discounted_cash_flow": {
                "name": "Discounted Cash Flow (DCF)",
                "description": "Valuing based on future cash flow projections",
                "best_for": "Companies with predictable cash flows",
                "key_factors": [
                    "Revenue growth projections",
                    "Profit margin assumptions",
                    "Discount rate selection",
                    "Terminal value calculation"
                ],
                "advantages": [
                    "Forward-looking approach",
                    "Considers time value of money",
                    "Flexible for different scenarios"
                ],
                "limitations": [
                    "Sensitive to assumptions",
                    "Requires detailed projections",
                    "May not reflect market sentiment"
                ]
            },
            "comparable_company": {
                "name": "Comparable Company Analysis",
                "description": "Valuing based on similar public companies",
                "best_for": "Companies in established industries",
                "key_factors": [
                    "Industry peer selection",
                    "Financial metric multiples",
                    "Growth rate comparisons",
                    "Risk profile adjustments"
                ],
                "advantages": [
                    "Market-based approach",
                    "Easy to understand",
                    "Reflects current market conditions"
                ],
                "limitations": [
                    "Limited comparable companies",
                    "Market volatility impact",
                    "May not reflect unique value"
                ]
            },
            "precedent_transactions": {
                "name": "Precedent Transactions",
                "description": "Valuing based on recent M&A transactions",
                "best_for": "Companies in active M&A markets",
                "key_factors": [
                    "Recent transaction data",
                    "Industry-specific multiples",
                    "Transaction size relevance",
                    "Market timing considerations"
                ],
                "advantages": [
                    "Real transaction data",
                    "Industry-specific insights",
                    "Control premium included"
                ],
                "limitations": [
                    "Limited transaction data",
                    "Market timing impact",
                    "May not reflect current conditions"
                ]
            },
            "asset_based": {
                "name": "Asset-Based Valuation",
                "description": "Valuing based on company assets",
                "best_for": "Asset-heavy businesses",
                "key_factors": [
                    "Tangible asset values",
                    "Intangible asset assessment",
                    "Liability adjustments",
                    "Asset condition evaluation"
                ],
                "advantages": [
                    "Tangible basis",
                    "Conservative approach",
                    "Clear methodology"
                ],
                "limitations": [
                    "May undervalue growth potential",
                    "Doesn't consider future earnings",
                    "Asset value fluctuations"
                ]
            },
            "revenue_multiple": {
                "name": "Revenue Multiple",
                "description": "Valuing based on revenue multiples",
                "best_for": "High-growth, pre-profit companies",
                "key_factors": [
                    "Revenue growth rate",
                    "Industry benchmarks",
                    "Profit margin potential",
                    "Market conditions"
                ],
                "advantages": [
                    "Simple to calculate",
                    "Good for growth companies",
                    "Less sensitive to accounting"
                ],
                "limitations": [
                    "Ignores profitability",
                    "May not reflect true value",
                    "Growth assumptions critical"
                ]
            }
        }
        return {
            "status": "success",
            "data": valuation_methods,
            "message": "Valuation methods retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve valuation methods: {str(e)}"
        )

@router.get("/exit-checklist")
async def get_exit_checklist(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get comprehensive exit preparation checklist"""
    try:
        exit_checklist = {
            "financial_preparation": {
                "title": "Financial Preparation",
                "items": [
                    "Clean, audited financial statements",
                    "Detailed financial projections",
                    "Working capital optimization",
                    "Debt restructuring if needed",
                    "Tax planning and optimization",
                    "Financial due diligence preparation"
                ],
                "timeline": "6-12 months before exit"
            },
            "operational_preparation": {
                "title": "Operational Preparation",
                "items": [
                    "Streamlined operations",
                    "Key employee retention plans",
                    "Customer concentration reduction",
                    "Supplier relationship optimization",
                    "Technology infrastructure review",
                    "Process documentation"
                ],
                "timeline": "12-18 months before exit"
            },
            "legal_preparation": {
                "title": "Legal Preparation",
                "items": [
                    "Corporate structure review",
                    "Intellectual property protection",
                    "Contract review and optimization",
                    "Regulatory compliance audit",
                    "Employment agreement review",
                    "Legal due diligence preparation"
                ],
                "timeline": "6-12 months before exit"
            },
            "market_preparation": {
                "title": "Market Preparation",
                "items": [
                    "Market position analysis",
                    "Competitive landscape review",
                    "Growth strategy development",
                    "Customer relationship strengthening",
                    "Brand value enhancement",
                    "Market expansion planning"
                ],
                "timeline": "12-24 months before exit"
            },
            "team_preparation": {
                "title": "Team Preparation",
                "items": [
                    "Key management retention",
                    "Succession planning",
                    "Employee incentive programs",
                    "Organizational structure optimization",
                    "Culture preservation planning",
                    "Communication strategy"
                ],
                "timeline": "12-18 months before exit"
            },
            "transaction_preparation": {
                "title": "Transaction Preparation",
                "items": [
                    "Investment banker selection",
                    "Valuation analysis",
                    "Deal structure planning",
                    "Due diligence team preparation",
                    "Negotiation strategy development",
                    "Timeline planning"
                ],
                "timeline": "6-12 months before exit"
            }
        }
        return {
            "status": "success",
            "data": exit_checklist,
            "message": "Exit checklist retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve exit checklist: {str(e)}"
        )
