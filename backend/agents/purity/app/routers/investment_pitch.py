from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import BusinessIdea, InvestmentPitch, BusinessModel, FinancialForecast
from ..services.investment_pitch_service import InvestmentPitchService

router = APIRouter(prefix="/investment-pitch", tags=["Investment Pitch"])

class InvestmentPitchRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    funding_amount: float = Field(..., ge=0, description="Funding amount needed")
    equity_offered: float = Field(..., ge=0, le=100, description="Equity percentage offered")
    use_of_funds: List[str] = Field(..., description="How funds will be used")
    investor_type: str = Field(..., description="Type of investor (angel, VC, etc.)")
    pitch_deck_format: str = Field("slides", description="Pitch deck format")

class PitchDeckRequest(BaseModel):
    investment_pitch_id: int = Field(..., description="Investment pitch ID")
    slide_count: int = Field(15, ge=5, le=30, description="Number of slides")
    include_financials: bool = Field(True, description="Include financial slides")
    include_market_data: bool = Field(True, description="Include market data slides")

class FinancialProjectionsRequest(BaseModel):
    investment_pitch_id: int = Field(..., description="Investment pitch ID")
    projection_years: int = Field(5, ge=3, le=10, description="Number of years to project")
    include_scenarios: bool = Field(True, description="Include scenario analysis")

class InvestorMaterialsRequest(BaseModel):
    investment_pitch_id: int = Field(..., description="Investment pitch ID")
    material_types: List[str] = Field(..., description="Types of materials to generate")

@router.post("/create")
async def create_investment_pitch(
    request: InvestmentPitchRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create a comprehensive investment pitch"""
    try:
        service = InvestmentPitchService()
        result = await service.create_investment_pitch(
            db=db,
            business_idea_id=request.business_idea_id,
            funding_amount=request.funding_amount,
            equity_offered=request.equity_offered,
            use_of_funds=request.use_of_funds,
            investor_type=request.investor_type,
            pitch_deck_format=request.pitch_deck_format
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Investment pitch created successfully for ${request.funding_amount:,.2f} funding"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create investment pitch: {str(e)}"
        )

@router.post("/pitch-deck")
async def generate_pitch_deck(
    request: PitchDeckRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Generate a detailed pitch deck"""
    try:
        service = InvestmentPitchService()
        result = await service.generate_pitch_deck(
            db=db,
            investment_pitch_id=request.investment_pitch_id,
            slide_count=request.slide_count,
            include_financials=request.include_financials,
            include_market_data=request.include_market_data
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Pitch deck generated with {request.slide_count} slides"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate pitch deck: {str(e)}"
        )

@router.post("/financial-projections")
async def create_financial_projections(
    request: FinancialProjectionsRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create detailed financial projections"""
    try:
        service = InvestmentPitchService()
        result = await service.create_financial_projections(
            db=db,
            investment_pitch_id=request.investment_pitch_id,
            projection_years=request.projection_years,
            include_scenarios=request.include_scenarios
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Financial projections created for {request.projection_years} years"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create financial projections: {str(e)}"
        )

@router.post("/investor-materials")
async def generate_investor_materials(
    request: InvestorMaterialsRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Generate comprehensive investor materials"""
    try:
        service = InvestmentPitchService()
        result = await service.generate_investor_materials(
            db=db,
            investment_pitch_id=request.investment_pitch_id,
            material_types=request.material_types
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Investor materials generated for {len(request.material_types)} types"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate investor materials: {str(e)}"
        )

@router.get("/pitch-templates")
async def get_pitch_templates(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get available pitch deck templates"""
    try:
        templates = {
            "startup_pitch": {
                "name": "Startup Pitch Deck",
                "slides": [
                    "Problem Statement",
                    "Solution Overview",
                    "Market Opportunity",
                    "Business Model",
                    "Go-to-Market Strategy",
                    "Competitive Analysis",
                    "Financial Projections",
                    "Team",
                    "Funding Ask",
                    "Appendix"
                ],
                "target_audience": "Angel investors, early-stage VCs",
                "estimated_duration": "10-15 minutes"
            },
            "growth_pitch": {
                "name": "Growth Stage Pitch Deck",
                "slides": [
                    "Executive Summary",
                    "Company Overview",
                    "Market Analysis",
                    "Product/Service",
                    "Traction & Metrics",
                    "Business Model",
                    "Growth Strategy",
                    "Financials",
                    "Team",
                    "Funding Use",
                    "Exit Strategy"
                ],
                "target_audience": "Series A+ VCs, growth investors",
                "estimated_duration": "20-30 minutes"
            },
            "enterprise_pitch": {
                "name": "Enterprise Pitch Deck",
                "slides": [
                    "Executive Summary",
                    "Market Problem",
                    "Solution",
                    "Market Size",
                    "Business Model",
                    "Competitive Advantage",
                    "Go-to-Market",
                    "Financial Projections",
                    "Risk Assessment",
                    "Team",
                    "Investment Opportunity"
                ],
                "target_audience": "Enterprise VCs, strategic investors",
                "estimated_duration": "25-35 minutes"
            }
        }
        return {
            "status": "success",
            "data": templates,
            "message": "Pitch templates retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pitch templates: {str(e)}"
        )

@router.get("/investor-types")
async def get_investor_types(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get different types of investors and their preferences"""
    try:
        investor_types = {
            "angel_investors": {
                "name": "Angel Investors",
                "investment_range": "$25K - $500K",
                "equity_expectation": "5-20%",
                "focus_areas": ["Early-stage startups", "Innovative ideas", "Strong teams"],
                "decision_factors": ["Team quality", "Market opportunity", "Innovation"],
                "typical_timeline": "2-4 weeks"
            },
            "seed_vcs": {
                "name": "Seed VCs",
                "investment_range": "$500K - $2M",
                "equity_expectation": "10-25%",
                "focus_areas": ["Product-market fit", "Traction", "Scalable models"],
                "decision_factors": ["Traction metrics", "Market size", "Team execution"],
                "typical_timeline": "4-8 weeks"
            },
            "series_a_vcs": {
                "name": "Series A VCs",
                "investment_range": "$2M - $15M",
                "equity_expectation": "15-30%",
                "focus_areas": ["Proven business model", "Strong growth", "Market leadership"],
                "decision_factors": ["Revenue growth", "Unit economics", "Market position"],
                "typical_timeline": "8-12 weeks"
            },
            "growth_vcs": {
                "name": "Growth VCs",
                "investment_range": "$10M - $100M",
                "equity_expectation": "10-25%",
                "focus_areas": ["Scaling companies", "Market expansion", "Operational excellence"],
                "decision_factors": ["Scalability", "Market dominance", "Team capability"],
                "typical_timeline": "6-10 weeks"
            },
            "strategic_investors": {
                "name": "Strategic Investors",
                "investment_range": "$5M - $50M",
                "equity_expectation": "10-30%",
                "focus_areas": ["Strategic fit", "Technology integration", "Market access"],
                "decision_factors": ["Strategic value", "Technology advantage", "Market access"],
                "typical_timeline": "12-16 weeks"
            }
        }
        return {
            "status": "success",
            "data": investor_types,
            "message": "Investor types retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve investor types: {str(e)}"
        )

@router.get("/pitch-best-practices")
async def get_pitch_best_practices(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get best practices for creating effective investment pitches"""
    try:
        best_practices = {
            "storytelling": {
                "title": "Compelling Storytelling",
                "description": "Tell a compelling story that connects emotionally",
                "tips": [
                    "Start with the problem you're solving",
                    "Show the human impact",
                    "Create a clear narrative arc",
                    "Use concrete examples and data"
                ]
            },
            "market_opportunity": {
                "title": "Market Opportunity",
                "description": "Clearly demonstrate market size and opportunity",
                "tips": [
                    "Use TAM, SAM, SOM framework",
                    "Show market growth trends",
                    "Identify market drivers",
                    "Quantify the opportunity"
                ]
            },
            "traction_metrics": {
                "title": "Traction & Metrics",
                "description": "Show concrete evidence of progress and growth",
                "tips": [
                    "Focus on key performance indicators",
                    "Show month-over-month growth",
                    "Include customer testimonials",
                    "Demonstrate product-market fit"
                ]
            },
            "financial_projections": {
                "title": "Financial Projections",
                "description": "Present realistic and well-supported financials",
                "tips": [
                    "Use conservative assumptions",
                    "Show multiple scenarios",
                    "Explain key drivers",
                    "Include unit economics"
                ]
            },
            "team_presentation": {
                "title": "Team Presentation",
                "description": "Highlight team strengths and relevant experience",
                "tips": [
                    "Focus on relevant experience",
                    "Show complementary skills",
                    "Include advisor/board members",
                    "Demonstrate commitment"
                ]
            },
            "competitive_advantage": {
                "title": "Competitive Advantage",
                "description": "Clearly articulate your unique advantages",
                "tips": [
                    "Identify key differentiators",
                    "Show competitive moats",
                    "Explain sustainable advantages",
                    "Address competitive threats"
                ]
            }
        }
        return {
            "status": "success",
            "data": best_practices,
            "message": "Pitch best practices retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pitch best practices: {str(e)}"
        )
