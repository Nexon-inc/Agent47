from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import BusinessIdea, BusinessModel, CustomerAvatar
from ..services.sales_funnel_service import SalesFunnelService

router = APIRouter(prefix="/sales-funnel", tags=["Sales Funnel"])

class SalesFunnelRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    target_audience: str = Field(..., description="Target audience")
    funnel_type: str = Field(..., description="Funnel type (awareness, consideration, decision)")
    conversion_goals: List[str] = Field(..., description="Conversion goals")
    budget_range: str = Field(..., description="Budget range")

class LeadNurturingRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    lead_stage: str = Field(..., description="Lead stage (awareness, consideration, decision)")
    sequence_length: int = Field(7, ge=3, le=21, description="Number of emails in sequence")
    nurture_goals: List[str] = Field(..., description="Nurturing goals")
    personalization_level: str = Field(..., description="Personalization level")

class ConversionOptimizationRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    current_conversion_rate: float = Field(..., ge=0, le=100, description="Current conversion rate")
    funnel_stages: List[str] = Field(..., description="Funnel stages to optimize")
    optimization_goals: List[str] = Field(..., description="Optimization goals")

class FunnelAnalyticsRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    funnel_metrics: Dict[str, Any] = Field(..., description="Funnel metrics data")
    tracking_period: str = Field(..., description="Tracking period")

@router.post("/generate")
async def generate_sales_funnel(
    request: SalesFunnelRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Generate a comprehensive sales funnel"""
    try:
        service = SalesFunnelService()
        result = await service.generate_sales_funnel(
            db=db,
            business_idea_id=request.business_idea_id,
            target_audience=request.target_audience,
            funnel_type=request.funnel_type,
            conversion_goals=request.conversion_goals,
            budget_range=request.budget_range
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Sales funnel generated for {request.funnel_type} funnel"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate sales funnel: {str(e)}"
        )

@router.post("/lead-nurturing")
async def create_lead_nurturing_sequence(
    request: LeadNurturingRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create a lead nurturing email sequence"""
    try:
        service = SalesFunnelService()
        result = await service.create_lead_nurturing_sequence(
            db=db,
            business_idea_id=request.business_idea_id,
            lead_stage=request.lead_stage,
            sequence_length=request.sequence_length,
            nurture_goals=request.nurture_goals,
            personalization_level=request.personalization_level
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Lead nurturing sequence created with {request.sequence_length} emails"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lead nurturing sequence: {str(e)}"
        )

@router.post("/optimize-conversion")
async def optimize_conversion_funnel(
    request: ConversionOptimizationRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Optimize conversion funnel performance"""
    try:
        service = SalesFunnelService()
        result = await service.optimize_conversion_funnel(
            db=db,
            business_idea_id=request.business_idea_id,
            current_conversion_rate=request.current_conversion_rate,
            funnel_stages=request.funnel_stages,
            optimization_goals=request.optimization_goals
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Conversion optimization completed for {request.current_conversion_rate}% current rate"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize conversion funnel: {str(e)}"
        )

@router.post("/analytics")
async def create_funnel_analytics(
    request: FunnelAnalyticsRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create comprehensive funnel analytics"""
    try:
        service = SalesFunnelService()
        result = await service.create_funnel_analytics(
            db=db,
            business_idea_id=request.business_idea_id,
            funnel_metrics=request.funnel_metrics,
            tracking_period=request.tracking_period
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Funnel analytics created for {request.tracking_period} period"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create funnel analytics: {str(e)}"
        )

@router.get("/funnel-types")
async def get_funnel_types(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get different types of sales funnels and their characteristics"""
    try:
        funnel_types = {
            "awareness_funnel": {
                "name": "Awareness Funnel",
                "description": "Designed to attract and educate potential customers",
                "stages": [
                    "Traffic Generation",
                    "Lead Capture",
                    "Education & Nurturing",
                    "Lead Qualification",
                    "Conversion"
                ],
                "best_for": "New markets, complex products, long sales cycles",
                "key_metrics": [
                    "Traffic volume",
                    "Lead capture rate",
                    "Engagement rate",
                    "Time to conversion"
                ]
            },
            "consideration_funnel": {
                "name": "Consideration Funnel",
                "description": "Focused on helping prospects evaluate options",
                "stages": [
                    "Problem Recognition",
                    "Solution Research",
                    "Feature Comparison",
                    "Value Assessment",
                    "Decision Making"
                ],
                "best_for": "Competitive markets, feature-rich products",
                "key_metrics": [
                    "Research engagement",
                    "Feature comparison time",
                    "Competitive analysis",
                    "Decision timeline"
                ]
            },
            "decision_funnel": {
                "name": "Decision Funnel",
                "description": "Optimized for final purchase decisions",
                "stages": [
                    "Final Evaluation",
                    "Risk Assessment",
                    "Purchase Decision",
                    "Checkout Process",
                    "Post-Purchase"
                ],
                "best_for": "E-commerce, direct response, impulse purchases",
                "key_metrics": [
                    "Cart abandonment rate",
                    "Checkout completion",
                    "Purchase frequency",
                    "Customer lifetime value"
                ]
            },
            "retention_funnel": {
                "name": "Retention Funnel",
                "description": "Focused on customer retention and upselling",
                "stages": [
                    "Onboarding",
                    "Value Delivery",
                    "Engagement",
                    "Upselling",
                    "Advocacy"
                ],
                "best_for": "Subscription businesses, SaaS, service companies",
                "key_metrics": [
                    "Onboarding completion",
                    "Feature adoption",
                    "Retention rate",
                    "Net promoter score"
                ]
            }
        }
        return {
            "status": "success",
            "data": funnel_types,
            "message": "Funnel types retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve funnel types: {str(e)}"
        )

@router.get("/conversion-optimization-tactics")
async def get_conversion_optimization_tactics(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get proven conversion optimization tactics"""
    try:
        optimization_tactics = {
            "psychological_triggers": {
                "name": "Psychological Triggers",
                "tactics": [
                    {
                        "name": "Social Proof",
                        "description": "Show that others are using/buying your product",
                        "examples": ["Customer testimonials", "User reviews", "Case studies"],
                        "implementation": "Add testimonials, reviews, and social proof elements"
                    },
                    {
                        "name": "Scarcity",
                        "description": "Create urgency with limited availability",
                        "examples": ["Limited time offers", "Stock alerts", "Countdown timers"],
                        "implementation": "Use countdown timers and limited availability messaging"
                    },
                    {
                        "name": "Authority",
                        "description": "Establish credibility and expertise",
                        "examples": ["Expert endorsements", "Industry awards", "Media mentions"],
                        "implementation": "Display credentials, awards, and expert testimonials"
                    }
                ]
            },
            "user_experience": {
                "name": "User Experience Optimization",
                "tactics": [
                    {
                        "name": "Simplify Forms",
                        "description": "Reduce form fields and friction",
                        "examples": ["Progressive forms", "Auto-fill options", "Single-page checkout"],
                        "implementation": "Remove unnecessary fields and use smart defaults"
                    },
                    {
                        "name": "Clear CTAs",
                        "description": "Make call-to-action buttons prominent and clear",
                        "examples": ["High contrast colors", "Action-oriented text", "Strategic placement"],
                        "implementation": "Use contrasting colors and action verbs"
                    },
                    {
                        "name": "Mobile Optimization",
                        "description": "Ensure seamless mobile experience",
                        "examples": ["Responsive design", "Touch-friendly buttons", "Fast loading"],
                        "implementation": "Test on mobile devices and optimize for speed"
                    }
                ]
            },
            "content_optimization": {
                "name": "Content Optimization",
                "tactics": [
                    {
                        "name": "Value-First Content",
                        "description": "Provide immediate value before asking for anything",
                        "examples": ["Free resources", "Educational content", "Tools and calculators"],
                        "implementation": "Create valuable content that addresses customer needs"
                    },
                    {
                        "name": "Personalization",
                        "description": "Tailor content to individual preferences",
                        "examples": ["Dynamic content", "Behavioral targeting", "Segmented messaging"],
                        "implementation": "Use customer data to personalize experiences"
                    },
                    {
                        "name": "Trust Building",
                        "description": "Build trust through transparency and guarantees",
                        "examples": ["Money-back guarantees", "Free trials", "Transparent pricing"],
                        "implementation": "Offer guarantees and be transparent about pricing"
                    }
                ]
            }
        }
        return {
            "status": "success",
            "data": optimization_tactics,
            "message": "Conversion optimization tactics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversion optimization tactics: {str(e)}"
        )

@router.get("/funnel-metrics")
async def get_funnel_metrics(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get key funnel metrics and KPIs"""
    try:
        funnel_metrics = {
            "awareness_metrics": {
                "name": "Awareness Stage Metrics",
                "metrics": [
                    {
                        "name": "Traffic Volume",
                        "description": "Number of visitors to your funnel",
                        "calculation": "Total unique visitors",
                        "benchmark": "Industry dependent"
                    },
                    {
                        "name": "Traffic Sources",
                        "description": "Where your traffic is coming from",
                        "calculation": "Traffic source breakdown",
                        "benchmark": "Organic: 40-60%, Paid: 20-40%"
                    },
                    {
                        "name": "Bounce Rate",
                        "description": "Percentage of visitors who leave without interaction",
                        "calculation": "Bounces / Total visits",
                        "benchmark": "< 40%"
                    }
                ]
            },
            "consideration_metrics": {
                "name": "Consideration Stage Metrics",
                "metrics": [
                    {
                        "name": "Engagement Rate",
                        "description": "How engaged visitors are with your content",
                        "calculation": "Engaged sessions / Total sessions",
                        "benchmark": "> 60%"
                    },
                    {
                        "name": "Time on Page",
                        "description": "Average time spent on funnel pages",
                        "calculation": "Total time / Total sessions",
                        "benchmark": "> 2 minutes"
                    },
                    {
                        "name": "Page Views per Session",
                        "description": "Number of pages viewed per session",
                        "calculation": "Total page views / Total sessions",
                        "benchmark": "> 3 pages"
                    }
                ]
            },
            "conversion_metrics": {
                "name": "Conversion Stage Metrics",
                "metrics": [
                    {
                        "name": "Conversion Rate",
                        "description": "Percentage of visitors who convert",
                        "calculation": "Conversions / Total visitors",
                        "benchmark": "2-5% (industry dependent)"
                    },
                    {
                        "name": "Cost per Conversion",
                        "description": "Cost to acquire each conversion",
                        "calculation": "Total ad spend / Total conversions",
                        "benchmark": "Industry dependent"
                    },
                    {
                        "name": "Conversion Value",
                        "description": "Average value of each conversion",
                        "calculation": "Total revenue / Total conversions",
                        "benchmark": "Industry dependent"
                    }
                ]
            },
            "retention_metrics": {
                "name": "Retention Stage Metrics",
                "metrics": [
                    {
                        "name": "Customer Retention Rate",
                        "description": "Percentage of customers who remain active",
                        "calculation": "Retained customers / Total customers",
                        "benchmark": "> 80%"
                    },
                    {
                        "name": "Customer Lifetime Value",
                        "description": "Total value a customer brings over time",
                        "calculation": "Average order value × Purchase frequency × Customer lifespan",
                        "benchmark": "Industry dependent"
                    },
                    {
                        "name": "Churn Rate",
                        "description": "Percentage of customers who stop using your product",
                        "calculation": "Churned customers / Total customers",
                        "benchmark": "< 5% monthly"
                    }
                ]
            }
        }
        return {
            "status": "success",
            "data": funnel_metrics,
            "message": "Funnel metrics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve funnel metrics: {str(e)}"
        )
