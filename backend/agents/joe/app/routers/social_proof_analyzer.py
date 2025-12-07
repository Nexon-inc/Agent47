from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.social_proof_analyzer_service import SocialProofAnalyzerService

router = APIRouter(prefix="/social-proof-analyzer", tags=["Social Proof Analyzer"])

class CompetitorAnalysisRequest(BaseModel):
    competitor_url: str = Field(..., description="URL of competitor to analyze")
    analysis_depth: str = Field(default="comprehensive", description="Depth of analysis")

class StrategyGenerationRequest(BaseModel):
    competitor_analysis: Dict[str, Any] = Field(..., description="Competitor analysis data")
    business_goals: List[str] = Field(..., description="Business goals for social proof strategy")

# Dependency
async def get_social_proof_analyzer_service() -> SocialProofAnalyzerService:
    service = SocialProofAnalyzerService()
    await service.initialize()
    return service

@router.post("/analyze-competitor")
async def analyze_competitor_social_proof(
    request: CompetitorAnalysisRequest,
    service: SocialProofAnalyzerService = Depends(get_social_proof_analyzer_service)
):
    """Analyze competitor's social proof and credibility indicators"""
    try:
        result = await service.analyze_competitor_social_proof(
            user_id=1,  # TODO: Get from authentication
            competitor_url=request.competitor_url,
            analysis_depth=request.analysis_depth
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["analysis_data"],
                "message": "Competitor social proof analysis completed successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Social proof analysis failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze competitor social proof: {str(e)}"
        )

@router.post("/generate-strategy")
async def generate_social_proof_strategy(
    request: StrategyGenerationRequest,
    service: SocialProofAnalyzerService = Depends(get_social_proof_analyzer_service)
):
    """Generate strategy to improve social proof based on competitor analysis"""
    try:
        result = await service.generate_social_proof_strategy(
            user_id=1,  # TODO: Get from authentication
            competitor_analysis=request.competitor_analysis,
            business_goals=request.business_goals
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["strategy_data"],
                "message": "Social proof strategy generated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Strategy generation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate social proof strategy: {str(e)}"
        )

@router.get("/analysis-metrics")
async def get_analysis_metrics(service: SocialProofAnalyzerService = Depends(get_social_proof_analyzer_service)):
    """Get available social proof analysis metrics and indicators"""
    analysis_metrics = [
        {
            "metric_id": "customer_reviews",
            "name": "Customer Reviews",
            "description": "Analysis of customer review volume, ratings, and sentiment",
            "indicators": ["Total reviews", "Average rating", "Sentiment analysis", "Authenticity score"],
            "importance": "high"
        },
        {
            "metric_id": "testimonials",
            "name": "Testimonials",
            "description": "Evaluation of customer testimonials and success stories",
            "indicators": ["Total testimonials", "Photo/video content", "Industry diversity", "Credibility score"],
            "importance": "high"
        },
        {
            "metric_id": "case_studies",
            "name": "Case Studies",
            "description": "Analysis of detailed client success stories and results",
            "indicators": ["Total cases", "Detail level", "Quantified results", "Client logos", "Impact score"],
            "importance": "medium"
        },
        {
            "metric_id": "social_media",
            "name": "Social Media Presence",
            "description": "Evaluation of social media engagement and influence",
            "indicators": ["Follower count", "Engagement rate", "Content consistency", "Influencer endorsements"],
            "importance": "medium"
        },
        {
            "metric_id": "trust_signals",
            "name": "Trust Signals",
            "description": "Various credibility and trust indicators",
            "indicators": ["Certifications", "Awards", "Media mentions", "Partnerships", "Security badges"],
            "importance": "high"
        }
    ]
    
    return {
        "status": "success",
        "data": analysis_metrics,
        "message": f"Retrieved {len(analysis_metrics)} analysis metrics"
    }
