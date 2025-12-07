from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import BusinessIdea, BrandIdentity, BusinessModel
from ..services.copywriting_assistant_service import CopywritingAssistantService

router = APIRouter(prefix="/copywriting", tags=["Copywriting Assistant"])

class LandingPageRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    target_audience: str = Field(..., description="Target audience")
    value_proposition: str = Field(..., description="Value proposition")
    call_to_action: str = Field(..., description="Call to action")
    page_sections: List[str] = Field(..., description="Page sections to include")

class AdCopyRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    ad_platform: str = Field(..., description="Ad platform (Google, Facebook, etc.)")
    ad_type: str = Field(..., description="Ad type (search, display, video, etc.)")
    target_audience: str = Field(..., description="Target audience")
    ad_objective: str = Field(..., description="Ad objective")
    budget_range: str = Field(..., description="Budget range")

class ProductDescriptionRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    product_name: str = Field(..., description="Product name")
    product_features: List[str] = Field(..., description="Product features")
    target_audience: str = Field(..., description="Target audience")
    tone: str = Field(..., description="Tone of voice")
    length_preference: str = Field(..., description="Length preference")

class EmailCopyRequest(BaseModel):
    business_idea_id: int = Field(..., description="Business idea ID")
    email_type: str = Field(..., description="Email type (welcome, nurture, sales, etc.)")
    target_audience: str = Field(..., description="Target audience")
    email_purpose: str = Field(..., description="Email purpose")
    tone: str = Field(..., description="Tone of voice")
    include_offer: bool = Field(False, description="Include special offer")

@router.post("/landing-page")
async def generate_landing_page_copy(
    request: LandingPageRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Generate compelling landing page copy"""
    try:
        service = CopywritingAssistantService()
        result = await service.generate_landing_page_copy(
            db=db,
            business_idea_id=request.business_idea_id,
            target_audience=request.target_audience,
            value_proposition=request.value_proposition,
            call_to_action=request.call_to_action,
            page_sections=request.page_sections
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Landing page copy generated for {request.target_audience} audience"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate landing page copy: {str(e)}"
        )

@router.post("/ad-copy")
async def create_ad_copy(
    request: AdCopyRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create compelling ad copy for various platforms"""
    try:
        service = CopywritingAssistantService()
        result = await service.create_ad_copy(
            db=db,
            business_idea_id=request.business_idea_id,
            ad_platform=request.ad_platform,
            ad_type=request.ad_type,
            target_audience=request.target_audience,
            ad_objective=request.ad_objective,
            budget_range=request.budget_range
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Ad copy created for {request.ad_platform} {request.ad_type} ads"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ad copy: {str(e)}"
        )

@router.post("/product-description")
async def write_product_description(
    request: ProductDescriptionRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Write compelling product descriptions"""
    try:
        service = CopywritingAssistantService()
        result = await service.write_product_description(
            db=db,
            business_idea_id=request.business_idea_id,
            product_name=request.product_name,
            product_features=request.product_features,
            target_audience=request.target_audience,
            tone=request.tone,
            length_preference=request.length_preference
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Product description written for {request.product_name}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write product description: {str(e)}"
        )

@router.post("/email-copy")
async def create_email_copy(
    request: EmailCopyRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create compelling email copy for various purposes"""
    try:
        service = CopywritingAssistantService()
        result = await service.create_email_copy(
            db=db,
            business_idea_id=request.business_idea_id,
            email_type=request.email_type,
            target_audience=request.target_audience,
            email_purpose=request.email_purpose,
            tone=request.tone,
            include_offer=request.include_offer
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Email copy created for {request.email_type} emails"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create email copy: {str(e)}"
        )

@router.get("/copywriting-templates")
async def get_copywriting_templates(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get copywriting templates and frameworks"""
    try:
        templates = {
            "landing_page_templates": {
                "name": "Landing Page Copy Templates",
                "templates": {
                    "problem_solution": {
                        "name": "Problem-Solution Template",
                        "structure": [
                            "Headline: State the problem",
                            "Subheadline: Agitate the problem",
                            "Solution: Present your solution",
                            "Benefits: List key benefits",
                            "Proof: Social proof/testimonials",
                            "CTA: Clear call to action"
                        ],
                        "best_for": "Products solving specific problems"
                    },
                    "benefit_driven": {
                        "name": "Benefit-Driven Template",
                        "structure": [
                            "Headline: Main benefit",
                            "Subheadline: Supporting benefit",
                            "Features: Key features",
                            "Benefits: Detailed benefits",
                            "Social Proof: Customer results",
                            "CTA: Action-oriented"
                        ],
                        "best_for": "Feature-rich products"
                    },
                    "story_based": {
                        "name": "Story-Based Template",
                        "structure": [
                            "Hook: Compelling opening",
                            "Problem: The challenge",
                            "Solution: How you solved it",
                            "Results: The outcome",
                            "Offer: What you're offering",
                            "CTA: Next step"
                        ],
                        "best_for": "Personal brands and services"
                    }
                }
            },
            "ad_copy_templates": {
                "name": "Ad Copy Templates",
                "templates": {
                    "google_ads": {
                        "name": "Google Ads Template",
                        "structure": [
                            "Headline 1: Primary keyword + benefit",
                            "Headline 2: Secondary benefit",
                            "Headline 3: Call to action",
                            "Description 1: Feature + benefit",
                            "Description 2: Social proof + CTA"
                        ],
                        "character_limits": {
                            "headlines": "30 characters each",
                            "descriptions": "90 characters each"
                        }
                    },
                    "facebook_ads": {
                        "name": "Facebook Ads Template",
                        "structure": [
                            "Hook: Attention-grabbing opening",
                            "Problem: Pain point identification",
                            "Solution: Your product/service",
                            "Benefit: Key value proposition",
                            "CTA: Clear action step"
                        ],
                        "best_practices": [
                            "Use conversational tone",
                            "Include social proof",
                            "Ask questions",
                            "Use emojis strategically"
                        ]
                    }
                }
            },
            "email_templates": {
                "name": "Email Copy Templates",
                "templates": {
                    "welcome_series": {
                        "name": "Welcome Email Series",
                        "emails": [
                            {
                                "subject": "Welcome! Here's what to expect",
                                "focus": "Set expectations and introduce value"
                            },
                            {
                                "subject": "Quick tip to get you started",
                                "focus": "Provide immediate value"
                            },
                            {
                                "subject": "Your success story starts here",
                                "focus": "Share customer success stories"
                            }
                        ]
                    },
                    "nurture_sequence": {
                        "name": "Nurture Email Sequence",
                        "emails": [
                            {
                                "subject": "Common challenges in [industry]",
                                "focus": "Address pain points"
                            },
                            {
                                "subject": "How [competitor] solved this",
                                "focus": "Share case studies"
                            },
                            {
                                "subject": "Ready to see results?",
                                "focus": "Soft sell with value"
                            }
                        ]
                    }
                }
            }
        }
        return {
            "status": "success",
            "data": templates,
            "message": "Copywriting templates retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve copywriting templates: {str(e)}"
        )

@router.get("/copywriting-best-practices")
async def get_copywriting_best_practices(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get copywriting best practices and guidelines"""
    try:
        best_practices = {
            "headline_writing": {
                "title": "Headline Writing Best Practices",
                "principles": [
                    "Use power words and emotional triggers",
                    "Include specific numbers and data",
                    "Address the reader directly",
                    "Create curiosity and urgency",
                    "Test multiple variations"
                ],
                "formulas": [
                    "Number + Adjective + Keyword + Promise",
                    "How to [Achieve Goal] in [Timeframe]",
                    "[Problem]? Here's the [Solution]",
                    "The [Number] [Type] Guide to [Topic]"
                ]
            },
            "persuasion_techniques": {
                "title": "Persuasion Techniques",
                "techniques": [
                    "Social proof and testimonials",
                    "Scarcity and urgency",
                    "Authority and expertise",
                    "Reciprocity and value first",
                    "Consistency and commitment"
                ],
                "examples": [
                    "Join 10,000+ satisfied customers",
                    "Limited time offer - only 50 spots left",
                    "As featured in Forbes and TechCrunch",
                    "Free guide: 10 proven strategies",
                    "Start your transformation today"
                ]
            },
            "conversion_optimization": {
                "title": "Conversion Optimization",
                "strategies": [
                    "Clear value proposition",
                    "Strong call-to-action buttons",
                    "Reduced friction and distractions",
                    "Trust signals and guarantees",
                    "Mobile-optimized copy"
                ],
                "cta_examples": [
                    "Get Started Free",
                    "Claim Your Discount",
                    "Download Now",
                    "Book Your Call",
                    "Join the Waitlist"
                ]
            },
            "tone_and_voice": {
                "title": "Tone and Voice Guidelines",
                "tones": {
                    "professional": {
                        "description": "Formal, authoritative, trustworthy",
                        "use_for": "B2B, financial services, legal",
                        "examples": ["We deliver exceptional results", "Our proven methodology"]
                    },
                    "friendly": {
                        "description": "Warm, approachable, conversational",
                        "use_for": "Consumer products, lifestyle brands",
                        "examples": ["Hey there!", "We've got you covered"]
                    },
                    "urgent": {
                        "description": "Time-sensitive, action-oriented",
                        "use_for": "Limited offers, flash sales",
                        "examples": ["Don't miss out", "Act now before it's gone"]
                    },
                    "educational": {
                        "description": "Informative, helpful, expert",
                        "use_for": "Educational content, how-to guides",
                        "examples": ["Learn how to", "Discover the secrets"]
                    }
                }
            }
        }
        return {
            "status": "success",
            "data": best_practices,
            "message": "Copywriting best practices retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve copywriting best practices: {str(e)}"
        )

@router.get("/copywriting-tools")
async def get_copywriting_tools(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get recommended copywriting tools and resources"""
    try:
        tools = {
            "headline_analyzers": {
                "name": "Headline Analyzers",
                "tools": [
                    {
                        "name": "CoSchedule Headline Analyzer",
                        "description": "Analyzes headline quality and emotional impact",
                        "features": ["Emotional score", "Word balance", "Length analysis"]
                    },
                    {
                        "name": "Advanced Marketing Institute",
                        "description": "Tests emotional marketing value",
                        "features": ["EMV score", "Word type analysis", "Optimization tips"]
                    }
                ]
            },
            "readability_checkers": {
                "name": "Readability Checkers",
                "tools": [
                    {
                        "name": "Hemingway Editor",
                        "description": "Improves clarity and readability",
                        "features": ["Readability score", "Sentence complexity", "Word suggestions"]
                    },
                    {
                        "name": "Grammarly",
                        "description": "Grammar and style checking",
                        "features": ["Grammar correction", "Style suggestions", "Tone detection"]
                    }
                ]
            },
            "seo_tools": {
                "name": "SEO Copywriting Tools",
                "tools": [
                    {
                        "name": "Yoast SEO",
                        "description": "WordPress SEO plugin with readability analysis",
                        "features": ["Readability score", "SEO optimization", "Keyword analysis"]
                    },
                    {
                        "name": "Clearscope",
                        "description": "Content optimization platform",
                        "features": ["Content grading", "Keyword research", "Competitor analysis"]
                    }
                ]
            },
            "conversion_tools": {
                "name": "Conversion Optimization Tools",
                "tools": [
                    {
                        "name": "Hotjar",
                        "description": "User behavior analysis",
                        "features": ["Heatmaps", "Session recordings", "Conversion funnels"]
                    },
                    {
                        "name": "Optimizely",
                        "description": "A/B testing platform",
                        "features": ["Split testing", "Multivariate testing", "Personalization"]
                    }
                ]
            }
        }
        return {
            "status": "success",
            "data": tools,
            "message": "Copywriting tools retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve copywriting tools: {str(e)}"
        )
