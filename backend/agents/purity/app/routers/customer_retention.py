from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import PurityBusinessIdea, PurityBusinessModel, PurityCustomerAvatar
from ..services.customer_retention_service import CustomerRetentionService

router = APIRouter(prefix="/customer-retention", tags=["Customer Retention"])

class ChurnAnalysisRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    customer_data: Dict[str, Any] = Field(..., description="Customer data")
    churn_indicators: List[str] = Field(..., description="Churn indicators")
    retention_period: str = Field(..., description="Retention period")

class LoyaltyProgramRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    program_type: str = Field(..., description="Loyalty program type")
    target_customers: str = Field(..., description="Target customers")
    reward_structure: Dict[str, Any] = Field(..., description="Reward structure")
    program_duration: str = Field(..., description="Program duration")

class RetentionStrategyRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    current_retention_rate: float = Field(..., ge=0, le=100, description="Current retention rate")
    target_retention_rate: float = Field(..., ge=0, le=100, description="Target retention rate")
    customer_segments: List[str] = Field(..., description="Customer segments")
    retention_goals: List[str] = Field(..., description="Retention goals")

class EngagementPlanRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    engagement_channels: List[str] = Field(..., description="Engagement channels")
    engagement_frequency: str = Field(..., description="Engagement frequency")
    content_types: List[str] = Field(..., description="Content types")
    personalization_level: str = Field(..., description="Personalization level")

@router.post("/analyze-churn")
async def analyze_customer_churn(
    request: ChurnAnalysisRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Analyze customer churn patterns and identify risk factors"""
    try:
        service = CustomerRetentionService()
        result = await service.analyze_customer_churn(
            db=db,
            business_idea_id=request.business_idea_id,
            customer_data=request.customer_data,
            churn_indicators=request.churn_indicators,
            retention_period=request.retention_period
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Churn analysis completed with {result.get('churn_rate', 0)}% churn rate"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze customer churn: {str(e)}"
        )

@router.post("/loyalty-program")
async def create_loyalty_program(
    request: LoyaltyProgramRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create a comprehensive loyalty program"""
    try:
        service = CustomerRetentionService()
        result = await service.create_loyalty_program(
            db=db,
            business_idea_id=request.business_idea_id,
            program_type=request.program_type,
            target_customers=request.target_customers,
            reward_structure=request.reward_structure,
            program_duration=request.program_duration
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Loyalty program created for {request.program_type} type"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create loyalty program: {str(e)}"
        )

@router.post("/retention-strategy")
async def develop_retention_strategy(
    request: RetentionStrategyRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Develop a comprehensive customer retention strategy"""
    try:
        service = CustomerRetentionService()
        result = await service.develop_retention_strategy(
            db=db,
            business_idea_id=request.business_idea_id,
            current_retention_rate=request.current_retention_rate,
            target_retention_rate=request.target_retention_rate,
            customer_segments=request.customer_segments,
            retention_goals=request.retention_goals
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Retention strategy developed to improve from {request.current_retention_rate}% to {request.target_retention_rate}%"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to develop retention strategy: {str(e)}"
        )

@router.post("/engagement-plan")
async def create_customer_engagement_plan(
    request: EngagementPlanRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create a customer engagement plan"""
    try:
        service = CustomerRetentionService()
        result = await service.create_customer_engagement_plan(
            db=db,
            business_idea_id=request.business_idea_id,
            engagement_channels=request.engagement_channels,
            engagement_frequency=request.engagement_frequency,
            content_types=request.content_types,
            personalization_level=request.personalization_level
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Customer engagement plan created for {len(request.engagement_channels)} channels"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create customer engagement plan: {str(e)}"
        )

@router.get("/retention-metrics")
async def get_retention_metrics(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get customer retention metrics and KPIs"""
    try:
        retention_metrics = {
            "churn_metrics": {
                "name": "Churn Metrics",
                "metrics": [
                    {
                        "name": "Customer Churn Rate",
                        "description": "Percentage of customers who stop using your product",
                        "calculation": "Churned customers / Total customers",
                        "benchmark": "< 5% monthly"
                    },
                    {
                        "name": "Revenue Churn Rate",
                        "description": "Percentage of revenue lost from churned customers",
                        "calculation": "Revenue from churned customers / Total revenue",
                        "benchmark": "< 3% monthly"
                    },
                    {
                        "name": "Net Revenue Retention",
                        "description": "Revenue retention including expansions",
                        "calculation": "(Starting revenue - churn + expansion) / Starting revenue",
                        "benchmark": "> 100%"
                    }
                ]
            },
            "engagement_metrics": {
                "name": "Engagement Metrics",
                "metrics": [
                    {
                        "name": "Customer Engagement Score",
                        "description": "Overall engagement level of customers",
                        "calculation": "Weighted average of engagement activities",
                        "benchmark": "> 70%"
                    },
                    {
                        "name": "Feature Adoption Rate",
                        "description": "Percentage of customers using key features",
                        "calculation": "Customers using features / Total customers",
                        "benchmark": "> 60%"
                    },
                    {
                        "name": "Time to Value",
                        "description": "Time for customers to realize value",
                        "calculation": "Average time to first success",
                        "benchmark": "< 7 days"
                    }
                ]
            },
            "loyalty_metrics": {
                "name": "Loyalty Metrics",
                "metrics": [
                    {
                        "name": "Customer Lifetime Value",
                        "description": "Total value a customer brings over time",
                        "calculation": "Average order value × Purchase frequency × Customer lifespan",
                        "benchmark": "Industry dependent"
                    },
                    {
                        "name": "Repeat Purchase Rate",
                        "description": "Percentage of customers who make repeat purchases",
                        "calculation": "Repeat customers / Total customers",
                        "benchmark": "> 40%"
                    },
                    {
                        "name": "Net Promoter Score",
                        "description": "Customer satisfaction and loyalty measure",
                        "calculation": "Promoters - Detractors",
                        "benchmark": "> 50"
                    }
                ]
            }
        }
        return {
            "status": "success",
            "data": retention_metrics,
            "message": "Retention metrics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve retention metrics: {str(e)}"
        )

@router.get("/loyalty-program-types")
async def get_loyalty_program_types(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get different types of loyalty programs and their characteristics"""
    try:
        loyalty_programs = {
            "points_based": {
                "name": "Points-Based Program",
                "description": "Customers earn points for purchases and activities",
                "structure": {
                    "earning": "Points per dollar spent",
                    "redemption": "Points for rewards/discounts",
                    "tiers": "Bronze, Silver, Gold levels"
                },
                "advantages": [
                    "Flexible reward options",
                    "Easy to understand",
                    "Scalable program"
                ],
                "best_for": "Retail, e-commerce, restaurants"
            },
            "tier_based": {
                "name": "Tier-Based Program",
                "description": "Customers progress through levels based on spending",
                "structure": {
                    "tiers": "Bronze, Silver, Gold, Platinum",
                    "benefits": "Increasing perks per tier",
                    "requirements": "Spending thresholds"
                },
                "advantages": [
                    "Clear progression path",
                    "Exclusive benefits",
                    "Status recognition"
                ],
                "best_for": "Hotels, airlines, premium brands"
            },
            "subscription_based": {
                "name": "Subscription-Based Program",
                "description": "Monthly/annual fee for exclusive benefits",
                "structure": {
                    "membership_fee": "Monthly or annual payment",
                    "benefits": "Exclusive discounts, early access",
                    "cancellation": "Flexible cancellation"
                },
                "advantages": [
                    "Predictable revenue",
                    "High engagement",
                    "Exclusive community"
                ],
                "best_for": "Amazon Prime, Costco, subscription services"
            },
            "gamified": {
                "name": "Gamified Program",
                "description": "Game-like elements to increase engagement",
                "structure": {
                    "challenges": "Daily/weekly tasks",
                    "achievements": "Badges and milestones",
                    "leaderboards": "Competition elements"
                },
                "advantages": [
                    "High engagement",
                    "Fun user experience",
                    "Social sharing"
                ],
                "best_for": "Mobile apps, gaming, fitness"
            },
            "referral_based": {
                "name": "Referral-Based Program",
                "description": "Rewards for bringing new customers",
                "structure": {
                    "referral_rewards": "Points/cash for successful referrals",
                    "friend_benefits": "Discounts for new customers",
                    "tracking": "Referral link system"
                },
                "advantages": [
                    "Viral growth",
                    "Low customer acquisition cost",
                    "Trust-based marketing"
                ],
                "best_for": "SaaS, services, subscription businesses"
            }
        }
        return {
            "status": "success",
            "data": loyalty_programs,
            "message": "Loyalty program types retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve loyalty program types: {str(e)}"
        )

@router.get("/retention-strategies")
async def get_retention_strategies(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get proven customer retention strategies"""
    try:
        retention_strategies = {
            "onboarding_optimization": {
                "name": "Onboarding Optimization",
                "description": "Improve customer onboarding to increase retention",
                "strategies": [
                    {
                        "name": "Welcome Series",
                        "description": "Multi-email welcome sequence",
                        "implementation": "Create 5-7 email welcome series",
                        "timeline": "First 30 days"
                    },
                    {
                        "name": "Quick Wins",
                        "description": "Help customers achieve early success",
                        "implementation": "Identify and guide to quick wins",
                        "timeline": "First 7 days"
                    },
                    {
                        "name": "Feature Education",
                        "description": "Teach customers to use key features",
                        "implementation": "Interactive tutorials and guides",
                        "timeline": "First 14 days"
                    }
                ]
            },
            "proactive_support": {
                "name": "Proactive Support",
                "description": "Anticipate and solve customer issues before they arise",
                "strategies": [
                    {
                        "name": "Predictive Analytics",
                        "description": "Identify at-risk customers",
                        "implementation": "Monitor usage patterns and behavior",
                        "timeline": "Ongoing"
                    },
                    {
                        "name": "Preventive Communication",
                        "description": "Reach out before problems occur",
                        "implementation": "Regular check-ins and tips",
                        "timeline": "Weekly/Monthly"
                    },
                    {
                        "name": "Self-Service Resources",
                        "description": "Provide comprehensive help resources",
                        "implementation": "Knowledge base, FAQs, tutorials",
                        "timeline": "Continuous"
                    }
                ]
            },
            "value_enhancement": {
                "name": "Value Enhancement",
                "description": "Continuously increase the value customers receive",
                "strategies": [
                    {
                        "name": "Feature Updates",
                        "description": "Regular product improvements",
                        "implementation": "Quarterly feature releases",
                        "timeline": "Quarterly"
                    },
                    {
                        "name": "Personalization",
                        "description": "Tailor experience to individual needs",
                        "implementation": "AI-driven personalization",
                        "timeline": "Ongoing"
                    },
                    {
                        "name": "Exclusive Content",
                        "description": "Provide premium content and resources",
                        "implementation": "Webinars, guides, industry insights",
                        "timeline": "Monthly"
                    }
                ]
            },
            "community_building": {
                "name": "Community Building",
                "description": "Create a sense of belonging and community",
                "strategies": [
                    {
                        "name": "User Groups",
                        "description": "Facilitate customer connections",
                        "implementation": "Online forums, local meetups",
                        "timeline": "Monthly"
                    },
                    {
                        "name": "Customer Events",
                        "description": "Host exclusive customer events",
                        "implementation": "Webinars, conferences, workshops",
                        "timeline": "Quarterly"
                    },
                    {
                        "name": "User-Generated Content",
                        "description": "Encourage customer content creation",
                        "implementation": "Reviews, testimonials, case studies",
                        "timeline": "Ongoing"
                    }
                ]
            }
        }
        return {
            "status": "success",
            "data": retention_strategies,
            "message": "Retention strategies retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve retention strategies: {str(e)}"
        )

@router.get("/engagement-channels")
async def get_engagement_channels(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get customer engagement channels and best practices"""
    try:
        engagement_channels = {
            "email_marketing": {
                "name": "Email Marketing",
                "description": "Direct communication through email",
                "best_practices": [
                    "Personalize subject lines and content",
                    "Segment your audience",
                    "Test different send times",
                    "Provide valuable content"
                ],
                "frequency": "Weekly to monthly",
                "tools": ["Mailchimp", "ConvertKit", "ActiveCampaign"]
            },
            "social_media": {
                "name": "Social Media",
                "description": "Engage customers on social platforms",
                "best_practices": [
                    "Post consistently",
                    "Engage with comments and messages",
                    "Share user-generated content",
                    "Use platform-specific features"
                ],
                "frequency": "Daily to weekly",
                "tools": ["Hootsuite", "Buffer", "Sprout Social"]
            },
            "push_notifications": {
                "name": "Push Notifications",
                "description": "Real-time mobile notifications",
                "best_practices": [
                    "Send at optimal times",
                    "Personalize messages",
                    "Don't over-send",
                    "Provide clear value"
                ],
                "frequency": "As needed",
                "tools": ["OneSignal", "Pushwoosh", "Airship"]
            },
            "in_app_messaging": {
                "name": "In-App Messaging",
                "description": "Messages within your application",
                "best_practices": [
                    "Contextual messaging",
                    "Non-intrusive design",
                    "Clear call-to-action",
                    "A/B test messages"
                ],
                "frequency": "As needed",
                "tools": ["Intercom", "Drift", "Crisp"]
            },
            "sms_messaging": {
                "name": "SMS Messaging",
                "description": "Text message communication",
                "best_practices": [
                    "Get explicit consent",
                    "Keep messages short",
                    "Include opt-out option",
                    "Send at appropriate times"
                ],
                "frequency": "Monthly to quarterly",
                "tools": ["Twilio", "MessageBird", "SendGrid"]
            },
            "webinars_events": {
                "name": "Webinars & Events",
                "description": "Live educational and networking events",
                "best_practices": [
                    "Provide valuable content",
                    "Interactive elements",
                    "Follow up with attendees",
                    "Record and share content"
                ],
                "frequency": "Monthly to quarterly",
                "tools": ["Zoom", "GoToWebinar", "Webex"]
            }
        }
        return {
            "status": "success",
            "data": engagement_channels,
            "message": "Engagement channels retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve engagement channels: {str(e)}"
        )
