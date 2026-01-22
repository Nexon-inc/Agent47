from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..services.local_market_insights_service import (
    LocalMarketInsightsService, RegionalInsight, MarketTrend
)
from ..database import get_db
from core.authentication.auth import get_current_user

router = APIRouter(prefix="/local-market-insights", tags=["Local Market Insights"])

# Initialize service
market_insights_service = LocalMarketInsightsService()


class EmergingMarketsRequest(BaseModel):
    target_regions: List[str]


@router.get("/insights/{region}")
async def get_regional_market_insights(
    region: str,
    industry: Optional[str] = Query(None, description="Industry filter"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> RegionalInsight:
    """Get comprehensive market insights for a specific region"""
    try:
        insights = await market_insights_service.get_regional_market_insights(
            db=db,
            region=region,
            industry=industry
        )
        return insights
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market insights: {str(e)}")


@router.get("/trends/{region}")
async def get_market_trends(
    region: str,
    industry: Optional[str] = Query(None, description="Industry filter"),
    trend_type: Optional[str] = Query(None, description="Trend type filter"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[MarketTrend]:
    """Get market trends for a specific region and industry"""
    try:
        trends = await market_insights_service.get_market_trends(
            db=db,
            region=region,
            industry=industry,
            trend_type=trend_type
        )
        return trends
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market trends: {str(e)}")


@router.get("/strategy-recommendations/{sales_rep_id}")
async def get_sales_strategy_recommendations(
    sales_rep_id: int,
    region: str = Query(..., description="Target region"),
    industry: Optional[str] = Query(None, description="Industry filter"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get personalized sales strategy recommendations based on local market insights"""
    try:
        recommendations = await market_insights_service.get_sales_strategy_recommendations(
            db=db,
            sales_rep_id=sales_rep_id,
            region=region,
            industry=industry
        )
        return recommendations
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get strategy recommendations: {str(e)}")


@router.get("/benchmarks/{region}")
async def get_regional_performance_benchmarks(
    region: str,
    industry: Optional[str] = Query(None, description="Industry filter"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get performance benchmarks for a specific region"""
    try:
        benchmarks = await market_insights_service.get_regional_performance_benchmarks(
            db=db,
            region=region,
            industry=industry
        )
        return benchmarks
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance benchmarks: {str(e)}")


@router.post("/emerging-markets")
async def get_emerging_markets_analysis(
    request: EmergingMarketsRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Analyze emerging markets and identify expansion opportunities"""
    try:
        analysis = await market_insights_service.get_emerging_markets_analysis(
            db=db,
            target_regions=request.target_regions
        )
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze emerging markets: {str(e)}")


@router.get("/regions/available")
async def get_available_regions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get list of available regions for analysis"""
    try:
        # Get unique regions from sales reps
        regions = db.query(EricSalesRep.region).distinct().all()
        region_list = [region[0] for region in regions if region[0]]
        
        return {
            "available_regions": region_list,
            "total_regions": len(region_list),
            "description": "Regions where sales reps are active"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available regions: {str(e)}")


@router.get("/industries/available")
async def get_available_industries(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get list of available industries for analysis"""
    try:
        # Get unique industries from customer profiles
        industries = db.query(CustomerProfile.industry).distinct().all()
        industry_list = [industry[0] for industry in industries if industry[0]]
        
        return {
            "available_industries": industry_list,
            "total_industries": len(industry_list),
            "description": "Industries of existing customers"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available industries: {str(e)}")


@router.get("/comparison/{region1}/{region2}")
async def compare_regions(
    region1: str,
    region2: str,
    industry: Optional[str] = Query(None, description="Industry filter"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Compare market insights between two regions"""
    try:
        # Get insights for both regions
        insights1 = await market_insights_service.get_regional_market_insights(db, region1, industry)
        insights2 = await market_insights_service.get_regional_market_insights(db, region2, industry)
        
        # Get performance benchmarks for both regions
        benchmarks1 = await market_insights_service.get_regional_performance_benchmarks(db, region1, industry)
        benchmarks2 = await market_insights_service.get_regional_performance_benchmarks(db, region2, industry)
        
        # Compare key metrics
        comparison = {
            "region1": {
                "name": region1,
                "insights": insights1.dict(),
                "performance": benchmarks1["regional_metrics"]
            },
            "region2": {
                "name": region2,
                "insights": insights2.dict(),
                "performance": benchmarks2["regional_metrics"]
            },
            "comparison": {
                "market_size_difference": insights1.market_size - insights2.market_size,
                "growth_rate_difference": insights1.growth_rate - insights2.growth_rate,
                "competition_level": {
                    "region1": insights1.competition_level,
                    "region2": insights2.competition_level
                },
                "market_maturity": {
                    "region1": insights1.market_maturity,
                    "region2": insights2.market_maturity
                },
                "conversion_rate_difference": benchmarks1["regional_metrics"]["conversion_rate"] - benchmarks2["regional_metrics"]["conversion_rate"],
                "avg_deal_size_difference": benchmarks1["regional_metrics"]["avg_deal_size"] - benchmarks2["regional_metrics"]["avg_deal_size"]
            },
            "recommendations": {
                "better_performing_region": region1 if benchmarks1["regional_metrics"]["conversion_rate"] > benchmarks2["regional_metrics"]["conversion_rate"] else region2,
                "higher_growth_region": region1 if insights1.growth_rate > insights2.growth_rate else region2,
                "lower_competition_region": region1 if insights1.competition_level == "low" and insights2.competition_level != "low" else region2 if insights2.competition_level == "low" and insights1.competition_level != "low" else "similar"
            }
        }
        
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare regions: {str(e)}")


@router.get("/trends/analysis/{region}")
async def get_trend_analysis(
    region: str,
    industry: Optional[str] = Query(None, description="Industry filter"),
    time_period: str = Query("6m", description="Time period: 3m, 6m, 12m"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed trend analysis for a region"""
    try:
        # Get market trends
        trends = await market_insights_service.get_market_trends(db, region, industry)
        
        # Get market insights
        insights = await market_insights_service.get_regional_market_insights(db, region, industry)
        
        # Analyze trend patterns
        trend_analysis = {
            "region": region,
            "industry": industry,
            "time_period": time_period,
            "total_trends": len(trends),
            "trend_categories": {
                "economic": len([t for t in trends if t.trend_type == "economic"]),
                "technology": len([t for t in trends if t.trend_type == "technology"]),
                "competitive": len([t for t in trends if t.trend_type == "competitive"]),
                "sales": len([t for t in trends if t.trend_type == "sales"])
            },
            "high_impact_trends": [t.dict() for t in trends if t.impact_score > 7.0],
            "trend_summary": {
                "positive_trends": len([t for t in trends if t.impact_score > 6.0]),
                "neutral_trends": len([t for t in trends if 4.0 <= t.impact_score <= 6.0]),
                "negative_trends": len([t for t in trends if t.impact_score < 4.0])
            },
            "market_insights": insights.dict(),
            "recommendations": insights.recommended_strategies
        }
        
        return trend_analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trend analysis: {str(e)}")


@router.get("/opportunities/{region}")
async def get_market_opportunities(
    region: str,
    industry: Optional[str] = Query(None, description="Industry filter"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed market opportunities for a region"""
    try:
        # Get market insights
        insights = await market_insights_service.get_regional_market_insights(db, region, industry)
        
        # Get market trends
        trends = await market_insights_service.get_market_trends(db, region, industry)
        
        # Analyze opportunities
        opportunities_analysis = {
            "region": region,
            "industry": industry,
            "market_overview": {
                "market_size": insights.market_size,
                "growth_rate": insights.growth_rate,
                "competition_level": insights.competition_level,
                "market_maturity": insights.market_maturity
            },
            "key_opportunities": insights.key_opportunities,
            "challenges": insights.challenges,
            "recommended_strategies": insights.recommended_strategies,
            "trend_opportunities": [
                {
                    "trend": trend.description,
                    "opportunity": f"Leverage {trend.trend_type} trend for market advantage",
                    "impact_score": trend.impact_score,
                    "confidence": trend.confidence_level
                }
                for trend in trends if trend.impact_score > 6.0
            ],
            "market_potential": {
                "score": min(insights.growth_rate / 10 + (1 if insights.competition_level == "low" else 0.5), 10),
                "rating": "high" if insights.growth_rate > 10 and insights.competition_level == "low" else "medium" if insights.growth_rate > 5 else "low"
            }
        }
        
        return opportunities_analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market opportunities: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for the local market insights service"""
    try:
        health_status = await market_insights_service.health_check()
        return health_status
    except Exception as e:
        return {
            "service": "local_market_insights",
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
