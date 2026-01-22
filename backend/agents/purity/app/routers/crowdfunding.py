from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import PurityBusinessIdea, PurityCrowdfundingCampaign, PurityBusinessModel
from ..services.crowdfunding_service import CrowdfundingService

router = APIRouter(prefix="/crowdfunding", tags=["Crowdfunding"])

class CrowdfundingCampaignRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    campaign_type: str = Field(..., description="Campaign type (reward, equity, donation)")
    funding_goal: float = Field(..., ge=0, description="Funding goal amount")
    campaign_duration: int = Field(30, ge=7, le=60, description="Campaign duration in days")
    reward_tiers: List[Dict[str, Any]] = Field(..., description="Reward tiers")
    campaign_description: str = Field(..., description="Campaign description")

class FundingStrategyRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    campaign_id: int = Field(..., description="Campaign ID")
    target_audience: str = Field(..., description="Target audience")
    marketing_channels: List[str] = Field(..., description="Marketing channels")
    budget_allocation: Dict[str, float] = Field(..., description="Budget allocation")

class MarketingPlanRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    campaign_id: int = Field(..., description="Campaign ID")
    marketing_strategy: str = Field(..., description="Marketing strategy")
    content_plan: Dict[str, Any] = Field(..., description="Content plan")
    social_media_strategy: Dict[str, Any] = Field(..., description="Social media strategy")

class CampaignPerformanceRequest(BaseModel):
    campaign_id: int = Field(..., description="Campaign ID")
    performance_metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    tracking_period: str = Field(..., description="Tracking period")

@router.post("/create-campaign")
async def create_crowdfunding_campaign(
    request: CrowdfundingCampaignRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create a comprehensive crowdfunding campaign"""
    try:
        service = CrowdfundingService()
        result = await service.create_crowdfunding_campaign(
            db=db,
            business_idea_id=request.business_idea_id,
            campaign_type=request.campaign_type,
            funding_goal=request.funding_goal,
            campaign_duration=request.campaign_duration,
            reward_tiers=request.reward_tiers,
            campaign_description=request.campaign_description
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Crowdfunding campaign created with ${request.funding_goal:,.2f} goal"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create crowdfunding campaign: {str(e)}"
        )

@router.post("/funding-strategy")
async def develop_funding_strategy(
    request: FundingStrategyRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Develop a comprehensive funding strategy"""
    try:
        service = CrowdfundingService()
        result = await service.develop_funding_strategy(
            db=db,
            business_idea_id=request.business_idea_id,
            campaign_id=request.campaign_id,
            target_audience=request.target_audience,
            marketing_channels=request.marketing_channels,
            budget_allocation=request.budget_allocation
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Funding strategy developed for {request.target_audience} audience"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to develop funding strategy: {str(e)}"
        )

@router.post("/marketing-plan")
async def create_marketing_plan(
    request: MarketingPlanRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create a comprehensive marketing plan"""
    try:
        service = CrowdfundingService()
        result = await service.create_marketing_plan(
            db=db,
            business_idea_id=request.business_idea_id,
            campaign_id=request.campaign_id,
            marketing_strategy=request.marketing_strategy,
            content_plan=request.content_plan,
            social_media_strategy=request.social_media_strategy
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Marketing plan created for {request.marketing_strategy} strategy"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create marketing plan: {str(e)}"
        )

@router.post("/campaign-performance")
async def manage_campaign_performance(
    request: CampaignPerformanceRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Manage and analyze campaign performance"""
    try:
        service = CrowdfundingService()
        result = await service.manage_campaign_performance(
            db=db,
            campaign_id=request.campaign_id,
            performance_metrics=request.performance_metrics,
            tracking_period=request.tracking_period
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Campaign performance analyzed for {request.tracking_period} period"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to manage campaign performance: {str(e)}"
        )

@router.get("/crowdfunding-platforms")
async def get_crowdfunding_platforms(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get different crowdfunding platforms and their characteristics"""
    try:
        platforms = {
            "kickstarter": {
                "name": "Kickstarter",
                "description": "Reward-based crowdfunding for creative projects",
                "campaign_types": ["Reward-based"],
                "funding_model": "All-or-nothing",
                "fees": "5% platform fee + 3-5% payment processing",
                "best_for": [
                    "Creative projects",
                    "Product launches",
                    "Art and design",
                    "Technology innovations"
                ],
                "requirements": [
                    "US, UK, Canada, Australia, New Zealand",
                    "Creative project focus",
                    "All-or-nothing funding"
                ],
                "success_rate": "37%",
                "average_pledge": "$25"
            },
            "indiegogo": {
                "name": "Indiegogo",
                "description": "Flexible crowdfunding for various project types",
                "campaign_types": ["Reward-based", "Equity", "Donation"],
                "funding_model": "Flexible or fixed",
                "fees": "5% platform fee + 3-5% payment processing",
                "best_for": [
                    "Technology products",
                    "Social causes",
                    "Innovative ideas",
                    "International projects"
                ],
                "requirements": [
                    "Global availability",
                    "Flexible funding options",
                    "Multiple campaign types"
                ],
                "success_rate": "34%",
                "average_pledge": "$88"
            },
            "go_fund_me": {
                "name": "GoFundMe",
                "description": "Personal fundraising and donation-based crowdfunding",
                "campaign_types": ["Donation-based"],
                "funding_model": "Keep what you raise",
                "fees": "2.9% payment processing + $0.30 per donation",
                "best_for": [
                    "Personal causes",
                    "Medical expenses",
                    "Emergency funds",
                    "Charitable causes"
                ],
                "requirements": [
                    "Personal or charitable cause",
                    "Keep what you raise model",
                    "No project requirements"
                ],
                "success_rate": "12%",
                "average_pledge": "$66"
            },
            "seed_invest": {
                "name": "SeedInvest",
                "description": "Equity crowdfunding for startups and businesses",
                "campaign_types": ["Equity-based"],
                "funding_model": "Equity investment",
                "fees": "7.5% placement fee + 2% escrow fee",
                "best_for": [
                    "Startups",
                    "Business expansion",
                    "Equity investment",
                    "Accredited investors"
                ],
                "requirements": [
                    "Accredited investors",
                    "Business focus",
                    "Equity offering"
                ],
                "success_rate": "15%",
                "average_investment": "$2,000"
            },
            "startengine": {
                "name": "StartEngine",
                "description": "Equity crowdfunding platform for startups",
                "campaign_types": ["Equity-based"],
                "funding_model": "Equity investment",
                "fees": "7% placement fee + 2% escrow fee",
                "best_for": [
                    "Startups",
                    "Growth companies",
                    "Equity investment",
                    "Regulation A+ offerings"
                ],
                "requirements": [
                    "Regulation A+ or Regulation D",
                    "Business focus",
                    "Equity offering"
                ],
                "success_rate": "20%",
                "average_investment": "$1,500"
            }
        }
        return {
            "status": "success",
            "data": platforms,
            "message": "Crowdfunding platforms retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve crowdfunding platforms: {str(e)}"
        )

@router.get("/campaign-best-practices")
async def get_campaign_best_practices(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get best practices for successful crowdfunding campaigns"""
    try:
        best_practices = {
            "campaign_planning": {
                "name": "Campaign Planning",
                "practices": [
                    {
                        "name": "Set Realistic Goals",
                        "description": "Set achievable funding goals based on your network and market",
                        "tips": [
                            "Calculate your network size and potential reach",
                            "Research similar successful campaigns",
                            "Set a minimum viable funding goal",
                            "Plan stretch goals for additional funding"
                        ]
                    },
                    {
                        "name": "Create Compelling Story",
                        "description": "Tell a compelling story that connects with your audience",
                        "tips": [
                            "Start with the problem you're solving",
                            "Share your personal journey and motivation",
                            "Use emotional storytelling",
                            "Include visuals and videos"
                        ]
                    },
                    {
                        "name": "Design Attractive Rewards",
                        "description": "Create reward tiers that provide value to backers",
                        "tips": [
                            "Offer early bird discounts",
                            "Create limited edition rewards",
                            "Provide exclusive access or experiences",
                            "Include multiple price points"
                        ]
                    }
                ]
            },
            "marketing_strategy": {
                "name": "Marketing Strategy",
                "practices": [
                    {
                        "name": "Build Pre-Launch Audience",
                        "description": "Build an audience before launching your campaign",
                        "tips": [
                            "Create social media presence",
                            "Build email list",
                            "Engage with potential backers",
                            "Share behind-the-scenes content"
                        ]
                    },
                    {
                        "name": "Leverage Social Media",
                        "description": "Use social media to promote your campaign",
                        "tips": [
                            "Share campaign updates regularly",
                            "Use relevant hashtags",
                            "Engage with your audience",
                            "Create shareable content"
                        ]
                    },
                    {
                        "name": "Email Marketing",
                        "description": "Use email marketing to drive traffic and conversions",
                        "tips": [
                            "Send pre-launch emails",
                            "Update subscribers on progress",
                            "Create urgency with limited-time offers",
                            "Personalize your messages"
                        ]
                    }
                ]
            },
            "campaign_execution": {
                "name": "Campaign Execution",
                "practices": [
                    {
                        "name": "Launch Strong",
                        "description": "Start your campaign with momentum",
                        "tips": [
                            "Launch with 30% of your goal already pledged",
                            "Have your network ready to back immediately",
                            "Create buzz with launch events",
                            "Prepare press releases and media outreach"
                        ]
                    },
                    {
                        "name": "Maintain Momentum",
                        "description": "Keep the campaign momentum going throughout",
                        "tips": [
                            "Update backers regularly",
                            "Share progress and milestones",
                            "Add new rewards or stretch goals",
                            "Engage with comments and questions"
                        ]
                    },
                    {
                        "name": "End Strong",
                        "description": "Finish your campaign with a strong push",
                        "tips": [
                            "Create final countdown urgency",
                            "Offer last-minute incentives",
                            "Remind your network to back",
                            "Share final updates and thank backers"
                        ]
                    }
                ]
            },
            "post_campaign": {
                "name": "Post-Campaign Management",
                "practices": [
                    {
                        "name": "Fulfill Rewards",
                        "description": "Deliver on your promises to backers",
                        "tips": [
                            "Communicate delivery timelines",
                            "Provide regular updates on progress",
                            "Handle delays professionally",
                            "Exceed expectations when possible"
                        ]
                    },
                    {
                        "name": "Maintain Relationships",
                        "description": "Keep relationships with backers for future projects",
                        "tips": [
                            "Thank backers personally",
                            "Share project progress updates",
                            "Offer exclusive access to future projects",
                            "Build a community around your brand"
                        ]
                    },
                    {
                        "name": "Plan Next Steps",
                        "description": "Plan your business growth after the campaign",
                        "tips": [
                            "Use funds as planned",
                            "Scale your business operations",
                            "Plan for future funding rounds",
                            "Build on campaign success"
                        ]
                    }
                ]
            }
        }
        return {
            "status": "success",
            "data": best_practices,
            "message": "Campaign best practices retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve campaign best practices: {str(e)}"
        )

@router.get("/campaign-metrics")
async def get_campaign_metrics(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get key metrics for crowdfunding campaign success"""
    try:
        campaign_metrics = {
            "funding_metrics": {
                "name": "Funding Metrics",
                "metrics": [
                    {
                        "name": "Funding Goal Achievement",
                        "description": "Percentage of funding goal reached",
                        "calculation": "Total raised / Funding goal",
                        "benchmark": "100% or higher",
                        "success_factors": [
                            "Realistic goal setting",
                            "Strong pre-launch audience",
                            "Compelling campaign story"
                        ]
                    },
                    {
                        "name": "Average Pledge Amount",
                        "description": "Average amount pledged per backer",
                        "calculation": "Total raised / Number of backers",
                        "benchmark": "Platform dependent",
                        "success_factors": [
                            "Attractive reward tiers",
                            "High-value offerings",
                            "Strong value proposition"
                        ]
                    },
                    {
                        "name": "Conversion Rate",
                        "description": "Percentage of visitors who become backers",
                        "calculation": "Number of backers / Total visitors",
                        "benchmark": "2-5%",
                        "success_factors": [
                            "Compelling campaign page",
                            "Clear value proposition",
                            "Social proof and testimonials"
                        ]
                    }
                ]
            },
            "engagement_metrics": {
                "name": "Engagement Metrics",
                "metrics": [
                    {
                        "name": "Social Media Engagement",
                        "description": "Engagement on social media posts",
                        "calculation": "Likes + Shares + Comments / Followers",
                        "benchmark": "3-5%",
                        "success_factors": [
                            "Regular posting schedule",
                            "Engaging content",
                            "Community interaction"
                        ]
                    },
                    {
                        "name": "Email Open Rate",
                        "description": "Percentage of emails opened by subscribers",
                        "calculation": "Emails opened / Emails sent",
                        "benchmark": "20-30%",
                        "success_factors": [
                            "Compelling subject lines",
                            "Personalized content",
                            "Optimal send times"
                        ]
                    },
                    {
                        "name": "Website Traffic",
                        "description": "Number of visitors to campaign page",
                        "calculation": "Total unique visitors",
                        "benchmark": "Platform dependent",
                        "success_factors": [
                            "Marketing campaign effectiveness",
                            "Social media reach",
                            "Press coverage"
                        ]
                    }
                ]
            },
            "timing_metrics": {
                "name": "Timing Metrics",
                "metrics": [
                    {
                        "name": "Time to 50% Funding",
                        "description": "Time to reach 50% of funding goal",
                        "calculation": "Days to reach 50% goal",
                        "benchmark": "First 7 days",
                        "success_factors": [
                            "Strong pre-launch audience",
                            "Effective launch strategy",
                            "Network mobilization"
                        ]
                    },
                    {
                        "name": "Mid-Campaign Momentum",
                        "description": "Funding rate during middle of campaign",
                        "calculation": "Average daily funding during middle period",
                        "benchmark": "Consistent daily funding",
                        "success_factors": [
                            "Regular updates and engagement",
                            "New reward additions",
                            "Media coverage"
                        ]
                    },
                    {
                        "name": "Final Push Effectiveness",
                        "description": "Funding increase in final days",
                        "calculation": "Funding in last 3 days / Total funding",
                        "benchmark": "20-30% of total funding",
                        "success_factors": [
                            "Urgency creation",
                            "Final incentives",
                            "Network reminders"
                        ]
                    }
                ]
            }
        }
        return {
            "status": "success",
            "data": campaign_metrics,
            "message": "Campaign metrics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve campaign metrics: {str(e)}"
        )
