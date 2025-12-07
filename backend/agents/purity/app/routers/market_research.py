from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from ..services.market_research_service import MarketResearchService
from ..models import BusinessIdea, PurityMarketResearch, PurityCompetitorAnalysis, NicheOpportunity, IndustryType
from ..database import get_purity_database

router = APIRouter()

# Pydantic models for request/response
class MarketResearchRequest(BaseModel):
    research_scope: Optional[Dict[str, Any]] = None

class CompetitorAnalysisRequest(BaseModel):
    competitor_names: Optional[List[str]] = None

class NicheFinderRequest(BaseModel):
    niche_criteria: Optional[Dict[str, Any]] = None

class MarketTrendsRequest(BaseModel):
    time_period: str = "12_months"

class MarketResearchResponse(BaseModel):
    id: int
    idea_id: int
    market_size: Optional[float]
    market_growth_rate: Optional[float]
    target_market_size: Optional[float]
    market_trends: List[str]
    competitor_analysis: List[Dict[str, Any]]
    customer_pain_points: List[str]
    market_opportunities: List[str]
    market_risks: List[str]
    regulatory_environment: Optional[str]
    technology_trends: List[str]
    social_trends: List[str]
    economic_factors: List[str]
    research_sources: List[str]
    confidence_score: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class CompetitorAnalysisResponse(BaseModel):
    id: int
    idea_id: int
    competitor_name: str
    competitor_url: Optional[str]
    market_position: Optional[str]
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    pricing_strategy: Optional[str]
    marketing_strategy: Optional[str]
    technology_stack: List[str]
    customer_base: Optional[str]
    revenue_estimate: Optional[float]
    competitive_advantage: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class NicheOpportunityResponse(BaseModel):
    id: int
    idea_id: int
    niche_name: str
    niche_description: Optional[str]
    market_size: Optional[float]
    competition_level: Optional[str]
    entry_barriers: List[str]
    growth_potential: Optional[float]
    profitability_score: Optional[float]
    customer_pain_points: List[str]
    monetization_opportunities: List[str]
    marketing_channels: List[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

@router.post("/research", response_model=Dict[str, Any])
async def conduct_market_research(
    idea_id: int,
    request: MarketResearchRequest
):
    """Conduct comprehensive market research for a business idea"""
    try:
        service = MarketResearchService()
        await service.initialize()
        
        result = await service.conduct_market_research(
            idea_id=idea_id,
            research_scope=request.research_scope
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "market_research": {
                "id": result["market_research"].id,
                "idea_id": result["market_research"].idea_id,
                "market_size": result["market_research"].market_size,
                "market_growth_rate": result["market_research"].market_growth_rate,
                "target_market_size": result["market_research"].target_market_size,
                "market_trends": result["market_research"].market_trends,
                "competitor_analysis": result["market_research"].competitor_analysis,
                "customer_pain_points": result["market_research"].customer_pain_points,
                "market_opportunities": result["market_research"].market_opportunities,
                "market_risks": result["market_research"].market_risks,
                "regulatory_environment": result["market_research"].regulatory_environment,
                "technology_trends": result["market_research"].technology_trends,
                "social_trends": result["market_research"].social_trends,
                "economic_factors": result["market_research"].economic_factors,
                "research_sources": result["market_research"].research_sources,
                "confidence_score": result["market_research"].confidence_score,
                "created_at": result["market_research"].created_at.isoformat(),
                "updated_at": result["market_research"].updated_at.isoformat() if result["market_research"].updated_at else None
            },
            "research_report": result["research_report"],
            "market_metrics": result["market_metrics"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to conduct market research: {str(e)}")

@router.post("/competitors", response_model=Dict[str, Any])
async def analyze_competitors(
    idea_id: int,
    request: CompetitorAnalysisRequest
):
    """Analyze competitors in detail"""
    try:
        service = MarketResearchService()
        await service.initialize()
        
        result = await service.analyze_competitors(
            idea_id=idea_id,
            competitor_names=request.competitor_names
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "competitor_analyses": [
                {
                    "id": analysis.id,
                    "idea_id": analysis.idea_id,
                    "competitor_name": analysis.competitor_name,
                    "competitor_url": analysis.competitor_url,
                    "market_position": analysis.market_position,
                    "strengths": analysis.strengths,
                    "weaknesses": analysis.weaknesses,
                    "opportunities": analysis.opportunities,
                    "threats": analysis.threats,
                    "pricing_strategy": analysis.pricing_strategy,
                    "marketing_strategy": analysis.marketing_strategy,
                    "technology_stack": analysis.technology_stack,
                    "customer_base": analysis.customer_base,
                    "revenue_estimate": analysis.revenue_estimate,
                    "competitive_advantage": analysis.competitive_advantage,
                    "created_at": analysis.created_at.isoformat(),
                    "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None
                }
                for analysis in result["competitor_analyses"]
            ],
            "total_competitors": result["total_competitors"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze competitors: {str(e)}")

@router.post("/niches", response_model=Dict[str, Any])
async def find_niche_opportunities(
    idea_id: int,
    request: NicheFinderRequest
):
    """Find profitable niche opportunities"""
    try:
        service = MarketResearchService()
        await service.initialize()
        
        result = await service.find_niche_opportunities(
            idea_id=idea_id,
            niche_criteria=request.niche_criteria
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "niche_opportunities": [
                {
                    "id": niche.id,
                    "idea_id": niche.idea_id,
                    "niche_name": niche.niche_name,
                    "niche_description": niche.niche_description,
                    "market_size": niche.market_size,
                    "competition_level": niche.competition_level,
                    "entry_barriers": niche.entry_barriers,
                    "growth_potential": niche.growth_potential,
                    "profitability_score": niche.profitability_score,
                    "customer_pain_points": niche.customer_pain_points,
                    "monetization_opportunities": niche.monetization_opportunities,
                    "marketing_channels": niche.marketing_channels,
                    "created_at": niche.created_at.isoformat(),
                    "updated_at": niche.updated_at.isoformat() if niche.updated_at else None
                }
                for niche in result["niche_opportunities"]
            ],
            "total_niches": result["total_niches"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find niche opportunities: {str(e)}")

@router.get("/trends/{industry}", response_model=Dict[str, Any])
async def get_market_trends(
    industry: IndustryType,
    time_period: str = Query("12_months", description="Time period for trends")
):
    """Get market trends for a specific industry"""
    try:
        service = MarketResearchService()
        await service.initialize()
        
        result = await service.get_market_trends(
            industry=industry,
            time_period=time_period
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market trends: {str(e)}")

@router.get("/research", response_model=List[MarketResearchResponse])
async def get_market_research(
    idea_id: Optional[int] = Query(None, description="Filter by idea ID"),
    limit: int = Query(10, description="Number of research records to return"),
    offset: int = Query(0, description="Number of research records to skip")
):
    """Get market research records with optional filtering"""
    try:
        db = await get_purity_database()
        async with db.get_session() as session:
            from sqlalchemy import select
            
            query = select(PurityMarketResearch)
            
            if idea_id:
                query = query.where(PurityMarketResearch.idea_id == idea_id)
            
            query = query.order_by(PurityMarketResearch.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            result = await session.execute(query)
            research_records = result.scalars().all()
            
            return [
                MarketResearchResponse(
                    id=research.id,
                    idea_id=research.idea_id,
                    market_size=research.market_size,
                    market_growth_rate=research.market_growth_rate,
                    target_market_size=research.target_market_size,
                    market_trends=research.market_trends,
                    competitor_analysis=research.competitor_analysis,
                    customer_pain_points=research.customer_pain_points,
                    market_opportunities=research.market_opportunities,
                    market_risks=research.market_risks,
                    regulatory_environment=research.regulatory_environment,
                    technology_trends=research.technology_trends,
                    social_trends=research.social_trends,
                    economic_factors=research.economic_factors,
                    research_sources=research.research_sources,
                    confidence_score=research.confidence_score,
                    created_at=research.created_at,
                    updated_at=research.updated_at
                )
                for research in research_records
            ]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market research: {str(e)}")

@router.get("/research/{research_id}", response_model=MarketResearchResponse)
async def get_market_research_by_id(research_id: int):
    """Get a specific market research record by ID"""
    try:
        db = await get_purity_database()
        async with db.get_session() as session:
            from sqlalchemy import select
            
            query = select(PurityMarketResearch).where(PurityMarketResearch.id == research_id)
            result = await session.execute(query)
            research = result.scalar_one_or_none()
            
            if not research:
                raise HTTPException(status_code=404, detail="Market research not found")
            
            return MarketResearchResponse(
                id=research.id,
                idea_id=research.idea_id,
                market_size=research.market_size,
                market_growth_rate=research.market_growth_rate,
                target_market_size=research.target_market_size,
                market_trends=research.market_trends,
                competitor_analysis=research.competitor_analysis,
                customer_pain_points=research.customer_pain_points,
                market_opportunities=research.market_opportunities,
                market_risks=research.market_risks,
                regulatory_environment=research.regulatory_environment,
                technology_trends=research.technology_trends,
                social_trends=research.social_trends,
                economic_factors=research.economic_factors,
                research_sources=research.research_sources,
                confidence_score=research.confidence_score,
                created_at=research.created_at,
                updated_at=research.updated_at
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market research: {str(e)}")

@router.get("/competitors", response_model=List[CompetitorAnalysisResponse])
async def get_competitor_analyses(
    idea_id: Optional[int] = Query(None, description="Filter by idea ID"),
    limit: int = Query(10, description="Number of competitor analyses to return"),
    offset: int = Query(0, description="Number of competitor analyses to skip")
):
    """Get competitor analyses with optional filtering"""
    try:
        db = await get_purity_database()
        async with db.get_session() as session:
            from sqlalchemy import select
            
            query = select(PurityCompetitorAnalysis)
            
            if idea_id:
                query = query.where(PurityCompetitorAnalysis.idea_id == idea_id)
            
            query = query.order_by(PurityCompetitorAnalysis.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            result = await session.execute(query)
            competitor_analyses = result.scalars().all()
            
            return [
                CompetitorAnalysisResponse(
                    id=analysis.id,
                    idea_id=analysis.idea_id,
                    competitor_name=analysis.competitor_name,
                    competitor_url=analysis.competitor_url,
                    market_position=analysis.market_position,
                    strengths=analysis.strengths,
                    weaknesses=analysis.weaknesses,
                    opportunities=analysis.opportunities,
                    threats=analysis.threats,
                    pricing_strategy=analysis.pricing_strategy,
                    marketing_strategy=analysis.marketing_strategy,
                    technology_stack=analysis.technology_stack,
                    customer_base=analysis.customer_base,
                    revenue_estimate=analysis.revenue_estimate,
                    competitive_advantage=analysis.competitive_advantage,
                    created_at=analysis.created_at,
                    updated_at=analysis.updated_at
                )
                for analysis in competitor_analyses
            ]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get competitor analyses: {str(e)}")

@router.get("/competitors/{analysis_id}", response_model=CompetitorAnalysisResponse)
async def get_competitor_analysis_by_id(analysis_id: int):
    """Get a specific competitor analysis by ID"""
    try:
        db = await get_purity_database()
        async with db.get_session() as session:
            from sqlalchemy import select
            
            query = select(PurityCompetitorAnalysis).where(PurityCompetitorAnalysis.id == analysis_id)
            result = await session.execute(query)
            analysis = result.scalar_one_or_none()
            
            if not analysis:
                raise HTTPException(status_code=404, detail="Competitor analysis not found")
            
            return CompetitorAnalysisResponse(
                id=analysis.id,
                idea_id=analysis.idea_id,
                competitor_name=analysis.competitor_name,
                competitor_url=analysis.competitor_url,
                market_position=analysis.market_position,
                strengths=analysis.strengths,
                weaknesses=analysis.weaknesses,
                opportunities=analysis.opportunities,
                threats=analysis.threats,
                pricing_strategy=analysis.pricing_strategy,
                marketing_strategy=analysis.marketing_strategy,
                technology_stack=analysis.technology_stack,
                customer_base=analysis.customer_base,
                revenue_estimate=analysis.revenue_estimate,
                competitive_advantage=analysis.competitive_advantage,
                created_at=analysis.created_at,
                updated_at=analysis.updated_at
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get competitor analysis: {str(e)}")

@router.get("/niches", response_model=List[NicheOpportunityResponse])
async def get_niche_opportunities(
    idea_id: Optional[int] = Query(None, description="Filter by idea ID"),
    limit: int = Query(10, description="Number of niche opportunities to return"),
    offset: int = Query(0, description="Number of niche opportunities to skip")
):
    """Get niche opportunities with optional filtering"""
    try:
        db = await get_purity_database()
        async with db.get_session() as session:
            from sqlalchemy import select
            
            query = select(NicheOpportunity)
            
            if idea_id:
                query = query.where(NicheOpportunity.idea_id == idea_id)
            
            query = query.order_by(NicheOpportunity.profitability_score.desc())
            query = query.offset(offset).limit(limit)
            
            result = await session.execute(query)
            niche_opportunities = result.scalars().all()
            
            return [
                NicheOpportunityResponse(
                    id=niche.id,
                    idea_id=niche.idea_id,
                    niche_name=niche.niche_name,
                    niche_description=niche.niche_description,
                    market_size=niche.market_size,
                    competition_level=niche.competition_level,
                    entry_barriers=niche.entry_barriers,
                    growth_potential=niche.growth_potential,
                    profitability_score=niche.profitability_score,
                    customer_pain_points=niche.customer_pain_points,
                    monetization_opportunities=niche.monetization_opportunities,
                    marketing_channels=niche.marketing_channels,
                    created_at=niche.created_at,
                    updated_at=niche.updated_at
                )
                for niche in niche_opportunities
            ]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get niche opportunities: {str(e)}")

@router.get("/niches/{niche_id}", response_model=NicheOpportunityResponse)
async def get_niche_opportunity_by_id(niche_id: int):
    """Get a specific niche opportunity by ID"""
    try:
        db = await get_purity_database()
        async with db.get_session() as session:
            from sqlalchemy import select
            
            query = select(NicheOpportunity).where(NicheOpportunity.id == niche_id)
            result = await session.execute(query)
            niche = result.scalar_one_or_none()
            
            if not niche:
                raise HTTPException(status_code=404, detail="Niche opportunity not found")
            
            return NicheOpportunityResponse(
                id=niche.id,
                idea_id=niche.idea_id,
                niche_name=niche.niche_name,
                niche_description=niche.niche_description,
                market_size=niche.market_size,
                competition_level=niche.competition_level,
                entry_barriers=niche.entry_barriers,
                growth_potential=niche.growth_potential,
                profitability_score=niche.profitability_score,
                customer_pain_points=niche.customer_pain_points,
                monetization_opportunities=niche.monetization_opportunities,
                marketing_channels=niche.marketing_channels,
                created_at=niche.created_at,
                updated_at=niche.updated_at
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get niche opportunity: {str(e)}")

@router.get("/summary/{idea_id}", response_model=Dict[str, Any])
async def get_market_research_summary(idea_id: int):
    """Get a comprehensive summary of market research for a business idea"""
    try:
        db = await get_purity_database()
        async with db.get_session() as session:
            from sqlalchemy import select, func
            from sqlalchemy.orm import selectinload
            
            # Get idea with market research
            idea_query = select(BusinessIdea).options(
                selectinload(BusinessIdea.market_research)
            ).where(BusinessIdea.id == idea_id)
            
            idea_result = await session.execute(idea_query)
            idea = idea_result.scalar_one_or_none()
            
            if not idea:
                raise HTTPException(status_code=404, detail="Business idea not found")
            
            # Get competitor analyses count
            competitor_count_query = select(func.count(PurityCompetitorAnalysis.id)).where(PurityCompetitorAnalysis.idea_id == idea_id)
            competitor_count_result = await session.execute(competitor_count_query)
            competitor_count = competitor_count_result.scalar()
            
            # Get niche opportunities count
            niche_count_query = select(func.count(NicheOpportunity.id)).where(NicheOpportunity.idea_id == idea_id)
            niche_count_result = await session.execute(niche_count_query)
            niche_count = niche_count_result.scalar()
            
            # Calculate research completion percentage
            total_research_components = 3  # market research, competitors, niches
            completed_components = 0
            
            if idea.market_research:
                completed_components += 1
            if competitor_count > 0:
                completed_components += 1
            if niche_count > 0:
                completed_components += 1
            
            completion_percentage = (completed_components / total_research_components) * 100
            
            return {
                "success": True,
                "idea_id": idea_id,
                "idea_title": idea.title,
                "market_research_count": len(idea.market_research),
                "competitor_analyses_count": competitor_count,
                "niche_opportunities_count": niche_count,
                "completion_percentage": completion_percentage,
                "summary": {
                    "total_research_components": total_research_components,
                    "completed_components": completed_components,
                    "next_steps": _get_market_research_next_steps(idea.market_research, competitor_count, niche_count)
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market research summary: {str(e)}")

def _get_market_research_next_steps(market_research: List[PurityMarketResearch], competitor_count: int, niche_count: int) -> List[str]:
    """Get recommended next steps based on current market research data"""
    next_steps = []
    
    if not market_research:
        next_steps.append("Conduct comprehensive market research")
    if competitor_count == 0:
        next_steps.append("Analyze competitors")
    if niche_count == 0:
        next_steps.append("Find niche opportunities")
    
    if not next_steps:
        next_steps.append("Proceed to financial planning")
        next_steps.append("Develop brand strategy")
        next_steps.append("Create launch plan")
    
    return next_steps
