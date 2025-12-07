from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.competitor_benchmarking_service import CompetitorBenchmarkingService

router = APIRouter(prefix="/competitor-benchmarking", tags=["Competitor Benchmarking"])

class BenchmarkRequest(BaseModel):
    industry: str = Field(..., description="Industry to benchmark")
    competitors: List[str] = Field(..., description="Competitors to benchmark against")
    metrics: List[str] = Field(default=[], description="Metrics to compare")

# Dependency
async def get_competitor_benchmarking_service() -> CompetitorBenchmarkingService:
    service = CompetitorBenchmarkingService()
    await service.initialize()
    return service

@router.post("/benchmark")
async def benchmark_competitors(
    request: BenchmarkRequest,
    service: CompetitorBenchmarkingService = Depends(get_competitor_benchmarking_service)
):
    """Benchmark against competitors in the industry"""
    try:
        result = await service.benchmark_competitors(
            user_id=1,  # TODO: Get from authentication
            industry=request.industry,
            competitors=request.competitors,
            metrics=request.metrics
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["benchmark_data"],
                "message": f"Benchmarked {len(request.competitors)} competitors in {request.industry}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Competitor benchmarking failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to benchmark competitors: {str(e)}"
        )

@router.get("/industry-benchmarks/{industry}")
async def get_industry_benchmarks(
    industry: str,
    service: CompetitorBenchmarkingService = Depends(get_competitor_benchmarking_service)
):
    """Get industry benchmark standards"""
    try:
        result = await service.get_industry_benchmarks(
            user_id=1,  # TODO: Get from authentication
            industry=industry
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["benchmarks"],
                "message": f"Retrieved industry benchmarks for {industry}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get industry benchmarks: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get industry benchmarks: {str(e)}"
        )

@router.get("/metrics")
async def get_benchmark_metrics(service: CompetitorBenchmarkingService = Depends(get_competitor_benchmarking_service)):
    """Get available benchmark metrics"""
    metrics = [
        {
            "id": "traffic",
            "name": "Website Traffic",
            "description": "Monthly website visitors",
            "unit": "visitors",
            "category": "Digital"
        },
        {
            "id": "engagement",
            "name": "Engagement Rate",
            "description": "User engagement percentage",
            "unit": "percentage",
            "category": "Digital"
        },
        {
            "id": "revenue",
            "name": "Revenue",
            "description": "Annual revenue",
            "unit": "currency",
            "category": "Financial"
        },
        {
            "id": "market_share",
            "name": "Market Share",
            "description": "Percentage of market captured",
            "unit": "percentage",
            "category": "Market"
        },
        {
            "id": "growth_rate",
            "name": "Growth Rate",
            "description": "Year-over-year growth",
            "unit": "percentage",
            "category": "Growth"
        }
    ]
    
    return {
        "status": "success",
        "data": metrics,
        "message": f"Retrieved {len(metrics)} benchmark metrics"
    }
