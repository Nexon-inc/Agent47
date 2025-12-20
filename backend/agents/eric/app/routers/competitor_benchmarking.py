from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from datetime import datetime

from ..services.competitor_benchmarking_service import CompetitorBenchmarkingService, CompetitorProfile, BenchmarkingMetrics, CompetitiveAnalysis
from ..database import get_eric_database
from core.cache.redis_manager import RedisManager

router = APIRouter(prefix="/competitor-benchmarking", tags=["Competitor Benchmarking"])
competitor_service = CompetitorBenchmarkingService()
redis_manager = RedisManager()

logger = logging.getLogger(__name__)

# Request/Response Models
class CompetitorProfileCreate(BaseModel):
    name: str
    industry: str
    website: str
    social_media: Dict[str, str] = {}
    key_metrics: Dict[str, float]
    pricing_strategy: str
    target_market: List[str] = []
    strengths: List[str] = []
    weaknesses: List[str] = []
    opportunities: List[str] = []
    threats: List[str] = []

class CompetitorProfileUpdate(BaseModel):
    name: str = None
    industry: str = None
    website: str = None
    social_media: Dict[str, str] = None
    key_metrics: Dict[str, float] = None
    pricing_strategy: str = None
    target_market: List[str] = None
    strengths: List[str] = None
    weaknesses: List[str] = None
    opportunities: List[str] = None
    threats: List[str] = None

class BenchmarkingRequest(BaseModel):
    industry: str
    your_metrics: Dict[str, float]

class CompetitiveAnalysisRequest(BaseModel):
    competitor_id: int

class MonitoringRequest(BaseModel):
    competitor_id: int

# Competitor Profile Endpoints
@router.post("/competitors", response_model=CompetitorProfile, summary="Create Competitor Profile")
async def create_competitor_profile(competitor_data: CompetitorProfileCreate):
    """Create a new competitor profile for benchmarking"""
    try:
        competitor_profile = CompetitorProfile(**competitor_data.dict())
        created_profile = await competitor_service.create_competitor_profile(competitor_profile)
        return created_profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create competitor profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/competitors", response_model=List[CompetitorProfile], summary="Get All Competitor Profiles")
async def get_competitor_profiles(industry: str = None):
    """Get all competitor profiles, optionally filtered by industry"""
    try:
        profiles = await competitor_service.get_competitor_profiles(industry)
        return profiles
    except Exception as e:
        logger.error(f"Failed to get competitor profiles: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/competitors/{competitor_id}", response_model=CompetitorProfile, summary="Get Competitor Profile")
async def get_competitor_profile(competitor_id: int):
    """Get a specific competitor profile by ID"""
    try:
        profiles = await competitor_service.get_competitor_profiles()
        profile = next((p for p in profiles if p.id == competitor_id), None)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Competitor profile not found")
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get competitor profile {competitor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/competitors/{competitor_id}", response_model=CompetitorProfile, summary="Update Competitor Profile")
async def update_competitor_profile(competitor_id: int, updates: CompetitorProfileUpdate):
    """Update an existing competitor profile"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid updates provided")
        
        updated_profile = await competitor_service.update_competitor_profile(competitor_id, update_data)
        return updated_profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update competitor profile {competitor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/competitors/{competitor_id}", summary="Delete Competitor Profile")
async def delete_competitor_profile(competitor_id: int):
    """Delete a competitor profile"""
    try:
        success = await competitor_service.delete_competitor_profile(competitor_id)
        
        if success:
            return {"message": "Competitor profile deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Competitor profile not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete competitor profile {competitor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Benchmarking Endpoints
@router.post("/benchmarking", response_model=List[BenchmarkingMetrics], summary="Calculate Benchmarking Metrics")
async def calculate_benchmarking_metrics(request: BenchmarkingRequest):
    """Calculate benchmarking metrics comparing your performance to industry and competitors"""
    try:
        metrics = await competitor_service.calculate_benchmarking_metrics(
            request.industry,
            request.your_metrics
        )
        return metrics
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to calculate benchmarking metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/competitive-analysis", response_model=CompetitiveAnalysis, summary="Perform Competitive Analysis")
async def perform_competitive_analysis(request: CompetitiveAnalysisRequest):
    """Perform comprehensive competitive analysis for a specific competitor"""
    try:
        analysis = await competitor_service.perform_competitive_analysis(request.competitor_id)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to perform competitive analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/intelligence-report/{industry}", summary="Get Competitive Intelligence Report")
async def get_competitive_intelligence_report(industry: str):
    """Generate comprehensive competitive intelligence report"""
    try:
        report = await competitor_service.get_competitive_intelligence_report(industry)
        return report
    except Exception as e:
        logger.error(f"Failed to generate competitive intelligence report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Monitoring Endpoints
@router.post("/monitoring", summary="Monitor Competitor Activity")
async def monitor_competitor_activity(request: MonitoringRequest):
    """Monitor real-time competitor activity and changes"""
    try:
        activity_report = await competitor_service.monitor_competitor_activity(request.competitor_id)
        return activity_report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to monitor competitor activity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Analytics Endpoints
@router.get("/analytics/industry/{industry}", summary="Get Industry Analytics")
async def get_industry_analytics(industry: str):
    """Get industry-specific competitive analytics"""
    try:
        # Get competitor profiles for industry
        competitors = await competitor_service.get_competitor_profiles(industry)
        
        # Calculate industry statistics
        total_competitors = len(competitors)
        avg_deal_size = sum(c.key_metrics.get("deal_size", 0) for c in competitors) / total_competitors if competitors else 0
        avg_conversion_rate = sum(c.key_metrics.get("conversion_rate", 0) for c in competitors) / total_competitors if competitors else 0
        
        # Analyze market positions
        positions = {}
        for competitor in competitors:
            position = "market_leader" if competitor.key_metrics.get("deal_size", 0) > 50000 else "strong_contender" if competitor.key_metrics.get("deal_size", 0) > 25000 else "mid_market_player"
            positions[position] = positions.get(position, 0) + 1
        
        return {
            "industry": industry,
            "total_competitors": total_competitors,
            "average_metrics": {
                "deal_size": avg_deal_size,
                "conversion_rate": avg_conversion_rate
            },
            "market_positions": positions,
            "competitive_landscape": "highly_competitive" if total_competitors > 10 else "moderately_competitive" if total_competitors > 5 else "less_competitive"
        }
    except Exception as e:
        logger.error(f"Failed to get industry analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/threats", summary="Get Competitive Threats")
async def get_competitive_threats(industry: str = None):
    """Get analysis of competitive threats"""
    try:
        competitors = await competitor_service.get_competitor_profiles(industry)
        
        threats = []
        for competitor in competitors:
            threat_level = "high" if competitor.key_metrics.get("deal_size", 0) > 40000 else "medium" if competitor.key_metrics.get("deal_size", 0) > 25000 else "low"
            
            if threat_level in ["high", "medium"]:
                threats.append({
                    "competitor_name": competitor.name,
                    "threat_level": threat_level,
                    "key_factors": [
                        "Large deal sizes" if competitor.key_metrics.get("deal_size", 0) > 40000 else None,
                        "High conversion rate" if competitor.key_metrics.get("conversion_rate", 0) > 3.0 else None,
                        "Premium positioning" if competitor.pricing_strategy == "premium" else None
                    ],
                    "recommended_action": "Monitor closely" if threat_level == "medium" else "Develop counter-strategy"
                })
        
        return {
            "total_threats": len(threats),
            "high_threats": len([t for t in threats if t["threat_level"] == "high"]),
            "medium_threats": len([t for t in threats if t["threat_level"] == "medium"]),
            "threats": threats
        }
    except Exception as e:
        logger.error(f"Failed to get competitive threats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Utility Endpoints
@router.get("/industries", summary="Get Supported Industries")
async def get_supported_industries():
    """Get list of supported industries for benchmarking"""
    try:
        industries = [
            "technology",
            "healthcare",
            "finance",
            "manufacturing",
            "retail",
            "education",
            "real_estate",
            "consulting"
        ]
        
        return {
            "industries": industries,
            "total_count": len(industries)
        }
    except Exception as e:
        logger.error(f"Failed to get supported industries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/metrics", summary="Get Supported Metrics")
async def get_supported_metrics():
    """Get list of supported metrics for benchmarking"""
    try:
        metrics = [
            "conversion_rate",
            "response_time",
            "deal_size",
            "sales_cycle",
            "customer_acquisition_cost",
            "lifetime_value",
            "churn_rate",
            "win_rate",
            "average_deal_size",
            "lead_quality_score"
        ]
        
        return {
            "metrics": metrics,
            "total_count": len(metrics),
            "description": "Key performance indicators used for competitive benchmarking"
        }
    except Exception as e:
        logger.error(f"Failed to get supported metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/pricing-strategies", summary="Get Pricing Strategies")
async def get_pricing_strategies():
    """Get list of pricing strategies for competitor analysis"""
    try:
        strategies = [
            "premium",
            "competitive",
            "economy",
            "freemium",
            "subscription",
            "usage_based",
            "tiered",
            "dynamic"
        ]
        
        return {
            "strategies": strategies,
            "total_count": len(strategies)
        }
    except Exception as e:
        logger.error(f"Failed to get pricing strategies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health Check Endpoint
@router.get("/health", summary="Competitor Benchmarking Health Check")
async def health_check():
    """Check the health of the competitor benchmarking service"""
    try:
        # Test basic functionality
        test_competitors = await competitor_service.get_competitor_profiles()
        
        return {
            "status": "healthy",
            "service": "Competitor Benchmarking",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "Competitor Profile Management",
                "Benchmarking Metrics Calculation",
                "Competitive Analysis",
                "Intelligence Reporting",
                "Activity Monitoring",
                "Threat Assessment"
            ],
            "competitors_loaded": len(test_competitors)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")
