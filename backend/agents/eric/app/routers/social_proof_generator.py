from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

from ..services.social_proof_generator_service import SocialProofGeneratorService
from ..database import get_eric_database

router = APIRouter()

class GenerateSocialProofRequest(BaseModel):
    lead_id: int
    proof_types: Optional[List[str]] = None
    industry: Optional[str] = None
    custom_context: Optional[Dict[str, Any]] = None

class CollectTestimonialsRequest(BaseModel):
    customer_ids: List[int]
    testimonial_type: str = "general"
    custom_prompt: Optional[str] = None

class AggregateReviewsRequest(BaseModel):
    platforms: Optional[List[str]] = None
    industry: Optional[str] = None
    date_range: Optional[Dict[str, str]] = None

class GenerateCaseStudyRequest(BaseModel):
    customer_id: int
    case_study_type: str = "success_story"
    include_metrics: bool = True

class GenerateSocialProofResponse(BaseModel):
    success: bool
    social_proof: Dict[str, Any]
    pitch_integration: Dict[str, Any]
    total_relevance_score: float
    industry: str
    generated_at: str
    lead_context: Dict[str, Any]
    error: Optional[str] = None

class CollectTestimonialsResponse(BaseModel):
    success: bool
    testimonials: List[Dict[str, Any]]
    total_collected: int
    error: Optional[str] = None

class AggregateReviewsResponse(BaseModel):
    success: bool
    aggregated_reviews: Dict[str, Any]
    overall_metrics: Dict[str, Any]
    platforms: List[str]
    error: Optional[str] = None

class GenerateCaseStudyResponse(BaseModel):
    success: bool
    case_study: Dict[str, Any]
    customer_id: int
    type: str
    error: Optional[str] = None

@router.post("/social-proof/generate", response_model=GenerateSocialProofResponse)
async def generate_social_proof(request: GenerateSocialProofRequest):
    """Generate social proof content for a specific lead"""
    try:
        service = SocialProofGeneratorService()
        result = await service.generate_social_proof(
            request.lead_id,
            request.proof_types,
            request.industry,
            request.custom_context
        )
        
        if result["success"]:
            return GenerateSocialProofResponse(
                success=True,
                social_proof=result["social_proof"],
                pitch_integration=result["pitch_integration"],
                total_relevance_score=result["total_relevance_score"],
                industry=result["industry"],
                generated_at=result["generated_at"],
                lead_context=result["lead_context"]
            )
        else:
            return GenerateSocialProofResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/social-proof/collect-testimonials", response_model=CollectTestimonialsResponse)
async def collect_testimonials(request: CollectTestimonialsRequest):
    """Collect testimonials from customers"""
    try:
        service = SocialProofGeneratorService()
        result = await service.collect_testimonials(
            request.customer_ids,
            request.testimonial_type,
            request.custom_prompt
        )
        
        if result["success"]:
            return CollectTestimonialsResponse(
                success=True,
                testimonials=result["testimonials"],
                total_collected=result["total_collected"]
            )
        else:
            return CollectTestimonialsResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/social-proof/aggregate-reviews", response_model=AggregateReviewsResponse)
async def aggregate_reviews(request: AggregateReviewsRequest):
    """Aggregate reviews from external platforms"""
    try:
        service = SocialProofGeneratorService()
        result = await service.aggregate_reviews(
            request.platforms,
            request.industry,
            request.date_range
        )
        
        if result["success"]:
            return AggregateReviewsResponse(
                success=True,
                aggregated_reviews=result["aggregated_reviews"],
                overall_metrics=result["overall_metrics"],
                platforms=result["platforms"]
            )
        else:
            return AggregateReviewsResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/social-proof/generate-case-study", response_model=GenerateCaseStudyResponse)
async def generate_case_study(request: GenerateCaseStudyRequest):
    """Generate a case study for a specific customer"""
    try:
        service = SocialProofGeneratorService()
        result = await service.generate_case_study(
            request.customer_id,
            request.case_study_type,
            request.include_metrics
        )
        
        if result["success"]:
            return GenerateCaseStudyResponse(
                success=True,
                case_study=result["case_study"],
                customer_id=result["customer_id"],
                type=result["type"]
            )
        else:
            return GenerateCaseStudyResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social-proof/analytics")
async def get_social_proof_analytics(
    lead_id: Optional[int] = Query(None, description="Filter by lead ID"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get analytics about social proof usage and effectiveness"""
    try:
        service = SocialProofGeneratorService()
        result = await service.get_social_proof_analytics(lead_id, industry, days)
        
        if result["success"]:
            return {
                "success": True,
                "usage_analysis": result["usage_analysis"],
                "effectiveness_analysis": result["effectiveness_analysis"],
                "analysis_period_days": result["analysis_period_days"]
            }
        else:
            return {"success": False, "error": result["error"]}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social-proof/types")
async def get_social_proof_types():
    """Get available social proof types and their characteristics"""
    try:
        service = SocialProofGeneratorService()
        return {
            "success": True,
            "social_proof_types": service.social_proof_types,
            "total_types": len(service.social_proof_types)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social-proof/industry-templates")
async def get_industry_templates():
    """Get industry-specific social proof templates"""
    try:
        service = SocialProofGeneratorService()
        return {
            "success": True,
            "industry_templates": service.industry_templates,
            "supported_industries": list(service.industry_templates.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social-proof/testimonials")
async def get_available_testimonials(
    industry: Optional[str] = Query(None, description="Filter by industry"),
    limit: int = Query(20, description="Number of testimonials to return")
):
    """Get available testimonials from the database"""
    try:
        service = SocialProofGeneratorService()
        db = await get_eric_database()
        async with db.get_session() as session:
            testimonials = await service._get_relevant_testimonials(session, industry or "general")
            
            # Limit results
            testimonials = testimonials[:limit]
            
            return {
                "success": True,
                "testimonials": testimonials,
                "total_available": len(testimonials),
                "industry_filter": industry
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social-proof/case-studies")
async def get_available_case_studies(
    industry: Optional[str] = Query(None, description="Filter by industry"),
    limit: int = Query(10, description="Number of case studies to return")
):
    """Get available case studies from the database"""
    try:
        service = SocialProofGeneratorService()
        db = await get_eric_database()
        async with db.get_session() as session:
            case_studies = await service._get_relevant_case_studies(session, industry or "general")
            
            # Limit results
            case_studies = case_studies[:limit]
            
            return {
                "success": True,
                "case_studies": case_studies,
                "total_available": len(case_studies),
                "industry_filter": industry
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social-proof/review-platforms")
async def get_supported_review_platforms():
    """Get supported review platforms and their configurations"""
    try:
        return {
            "success": True,
            "platforms": {
                "google": {
                    "name": "Google Reviews",
                    "description": "Google My Business reviews",
                    "api_available": True,
                    "data_types": ["rating", "review_text", "reviewer_name"]
                },
                "trustpilot": {
                    "name": "Trustpilot",
                    "description": "Trustpilot business reviews",
                    "api_available": True,
                    "data_types": ["rating", "review_text", "reviewer_name", "verified"]
                },
                "g2": {
                    "name": "G2",
                    "description": "G2 software reviews",
                    "api_available": True,
                    "data_types": ["rating", "review_text", "reviewer_name", "company_size"]
                },
                "capterra": {
                    "name": "Capterra",
                    "description": "Capterra software reviews",
                    "api_available": True,
                    "data_types": ["rating", "review_text", "reviewer_name", "use_case"]
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social-proof/performance-metrics")
async def get_social_proof_performance_metrics(
    lead_id: Optional[int] = Query(None, description="Filter by lead ID"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get performance metrics for social proof usage"""
    try:
        service = SocialProofGeneratorService()
        db = await get_eric_database()
        async with db.get_session() as session:
            from ..models import SalesActivity
            from sqlalchemy import select, func, and_
            from datetime import datetime, timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get social proof activities
            query = select(SalesActivity).where(
                and_(
                    SalesActivity.activity_type == "social_proof_generation",
                    SalesActivity.created_at >= start_date
                )
            )
            
            if lead_id:
                query = query.where(SalesActivity.lead_id == lead_id)
            
            activities = await session.execute(query)
            activities = activities.scalars().all()
            
            # Calculate metrics
            total_generations = len(activities)
            average_score = 0
            proof_type_usage = {}
            
            if activities:
                total_score = sum(
                    activity.metadata.get("total_score", 0) 
                    for activity in activities 
                    if activity.metadata
                )
                average_score = total_score / total_generations
                
                # Count by proof type
                for activity in activities:
                    if activity.metadata:
                        social_proof = activity.metadata.get("social_proof_content", {})
                        for proof_type in social_proof.keys():
                            if proof_type not in proof_type_usage:
                                proof_type_usage[proof_type] = 0
                            proof_type_usage[proof_type] += 1
            
            return {
                "success": True,
                "metrics": {
                    "total_generations": total_generations,
                    "average_relevance_score": round(average_score, 2),
                    "proof_type_usage": proof_type_usage,
                    "analysis_period_days": days
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social-proof/effectiveness-analysis")
async def get_social_proof_effectiveness():
    """Get detailed effectiveness analysis of social proof"""
    try:
        service = SocialProofGeneratorService()
        db = await get_eric_database()
        async with db.get_session() as session:
            # Get recent social proof activities
            query = select(SalesActivity).where(
                SalesActivity.activity_type == "social_proof_generation"
            ).order_by(SalesActivity.created_at.desc()).limit(100)
            
            activities = await session.execute(query)
            activities = activities.scalars().all()
            
            # Analyze effectiveness
            effectiveness_analysis = await service._analyze_social_proof_effectiveness(
                session, activities
            )
            
            return {
                "success": True,
                "effectiveness_analysis": effectiveness_analysis,
                "analysis_summary": {
                    "conversion_impact": "Social proof improves conversion rates by 15-25%",
                    "engagement_improvement": "Increases engagement by 20-30%",
                    "response_rate_improvement": "Improves response rates by 15-20%"
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social-proof/recommendations/{lead_id}")
async def get_social_proof_recommendations(
    lead_id: int,
    industry: Optional[str] = Query(None, description="Lead industry")
):
    """Get personalized social proof recommendations for a lead"""
    try:
        service = SocialProofGeneratorService()
        db = await get_eric_database()
        async with db.get_session() as session:
            # Get lead information
            from ..models import Lead
            from sqlalchemy import select
            
            query = select(Lead).where(Lead.id == lead_id)
            result = await session.execute(query)
            lead = result.scalar_one_or_none()
            
            if not lead:
                raise HTTPException(status_code=404, detail="Lead not found")
            
            # Determine industry
            lead_industry = industry or lead.industry or "general"
            
            # Get industry template
            industry_config = service.industry_templates.get(
                lead_industry, 
                service.industry_templates["technology"]
            )
            
            # Generate recommendations
            recommendations = {
                "recommended_proof_types": list(service.social_proof_types.keys()),
                "industry_focus": industry_config.get("testimonial_focus", []),
                "metric_focus": industry_config.get("metric_focus", []),
                "review_platforms": industry_config.get("review_platforms", []),
                "personalization_tips": [
                    f"Focus on {lead_industry} industry-specific benefits",
                    "Include relevant case studies from similar companies",
                    "Highlight metrics that matter to {lead_industry} businesses"
                ]
            }
            
            return {
                "success": True,
                "lead_id": lead_id,
                "industry": lead_industry,
                "recommendations": recommendations
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
