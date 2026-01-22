from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import PurityBusinessIdea, PurityOpportunityValidation, PurityBusinessModel
from ..services.opportunity_validation_service import OpportunityValidationService

router = APIRouter(prefix="/opportunity-validation", tags=["Opportunity Validation"])

class ValidationRequest(BaseModel):
    business_idea: str = Field(..., description="Business idea description")
    target_market: str = Field(..., description="Target market")
    market_data: Dict[str, Any] = Field(..., description="Market data")
    seo_trends: Dict[str, Any] = Field(..., description="SEO trends data")
    competitor_analysis: Dict[str, Any] = Field(..., description="Competitor analysis data")

class MarketAnalysisRequest(BaseModel):
    market_segment: str = Field(..., description="Market segment")
    geographic_region: str = Field(..., description="Geographic region")
    time_period: str = Field(..., description="Time period for analysis")
    data_sources: List[str] = Field(..., description="Data sources to analyze")

class SEOAnalysisRequest(BaseModel):
    keywords: List[str] = Field(..., description="Keywords to analyze")
    industry: str = Field(..., description="Industry")
    search_volume_data: Dict[str, Any] = Field(..., description="Search volume data")
    competition_level: str = Field(..., description="Competition level")

class CompetitorAnalysisRequest(BaseModel):
    competitors: List[str] = Field(..., description="List of competitors")
    analysis_depth: str = Field(..., description="Analysis depth")
    competitive_metrics: Dict[str, Any] = Field(..., description="Competitive metrics")
    market_position: str = Field(..., description="Market position")

@router.post("/validate")
async def validate_business_opportunity(
    request: ValidationRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Validate a business opportunity using market data, SEO trends, and competitor analysis"""
    try:
        service = OpportunityValidationService()
        result = await service.validate_business_opportunity(
            db=db,
            business_idea=request.business_idea,
            target_market=request.target_market,
            market_data=request.market_data,
            seo_trends=request.seo_trends,
            competitor_analysis=request.competitor_analysis
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Opportunity validation completed with score: {result.get('validation_score', 0)}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate business opportunity: {str(e)}"
        )

@router.post("/market-analysis")
async def analyze_market_data(
    request: MarketAnalysisRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Analyze market data for a specific segment and region"""
    try:
        service = OpportunityValidationService()
        result = await service.analyze_market_data(
            db=db,
            market_segment=request.market_segment,
            geographic_region=request.geographic_region,
            time_period=request.time_period,
            data_sources=request.data_sources
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Market analysis completed for {request.market_segment} in {request.geographic_region}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze market data: {str(e)}"
        )

@router.post("/seo-analysis")
async def analyze_seo_trends(
    request: SEOAnalysisRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Analyze SEO trends for specific keywords and industry"""
    try:
        service = OpportunityValidationService()
        result = await service.analyze_seo_trends(
            db=db,
            keywords=request.keywords,
            industry=request.industry,
            search_volume_data=request.search_volume_data,
            competition_level=request.competition_level
        )
        return {
            "status": "success",
            "data": result,
            "message": f"SEO analysis completed for {len(request.keywords)} keywords in {request.industry}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze SEO trends: {str(e)}"
        )

@router.post("/competitor-analysis")
async def conduct_competitor_analysis(
    request: CompetitorAnalysisRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Conduct comprehensive competitor analysis"""
    try:
        service = OpportunityValidationService()
        result = await service.conduct_competitor_analysis(
            db=db,
            competitors=request.competitors,
            analysis_depth=request.analysis_depth,
            competitive_metrics=request.competitive_metrics,
            market_position=request.market_position
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Competitor analysis completed for {len(request.competitors)} competitors"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to conduct competitor analysis: {str(e)}"
        )

@router.get("/validation-metrics")
async def get_validation_metrics(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get validation metrics and scoring criteria"""
    try:
        metrics = {
            "market_viability_weights": {
                "market_size": 0.25,
                "growth_potential": 0.20,
                "customer_demand": 0.20,
                "market_barriers": 0.15,
                "market_maturity": 0.20
            },
            "competitive_analysis_weights": {
                "competitor_count": 0.15,
                "competitive_intensity": 0.25,
                "market_share_opportunity": 0.30,
                "differentiation_potential": 0.20,
                "competitive_advantages": 0.10
            },
            "seo_opportunity_weights": {
                "keyword_opportunities": 0.30,
                "search_volume": 0.25,
                "competition_level": 0.20,
                "content_gaps": 0.15,
                "ranking_potential": 0.10
            },
            "scoring_criteria": {
                "excellent": "90-100",
                "good": "75-89",
                "fair": "60-74",
                "poor": "Below 60"
            }
        }
        return {
            "status": "success",
            "data": metrics,
            "message": "Validation metrics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve validation metrics: {str(e)}"
        )

@router.get("/market-trends")
async def get_market_trends(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get current market trends and insights"""
    try:
        trends = {
            "emerging_markets": [
                "Artificial Intelligence Services",
                "Sustainable Products",
                "Digital Health Solutions",
                "Remote Work Tools",
                "E-commerce Platforms"
            ],
            "declining_markets": [
                "Traditional Retail",
                "Print Media",
                "Fossil Fuel Energy",
                "Traditional Banking",
                "Conventional Agriculture"
            ],
            "market_opportunities": [
                "Aging population services",
                "Mental health solutions",
                "Local business digitization",
                "Personalized education",
                "Sustainable consumer products"
            ],
            "risk_factors": [
                "Economic uncertainty",
                "Regulatory changes",
                "Technology disruption",
                "Supply chain issues",
                "Climate change impact"
            ]
        }
        return {
            "status": "success",
            "data": trends,
            "message": "Market trends retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve market trends: {str(e)}"
        )
