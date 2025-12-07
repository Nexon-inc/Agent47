from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from ..database import get_shakes_database
from ..services.ad_copywriting_service import AdCopywritingService

router = APIRouter(prefix="/ad-copywriting", tags=["Ad Copywriting"])

# Pydantic Models
class CreateAdCopyRequest(BaseModel):
    user_id: int = Field(..., description="User ID creating the ad copy")
    platform: str = Field(..., description="Advertising platform (google_ads, facebook_ads, instagram_ads, linkedin_ads, twitter_ads)")
    ad_type: str = Field(..., description="Type of ad (search, display, social, video)")
    product_service: str = Field(..., description="Product or service being advertised")
    target_audience: str = Field(..., description="Target audience description")
    ad_objective: str = Field(..., description="Primary objective of the ad")
    budget_range: str = Field(..., description="Budget range for the ad")
    call_to_action: str = Field(..., description="Desired call-to-action")
    tone: str = Field(default="professional", description="Tone of the ad copy")

class CreateAdCampaignRequest(BaseModel):
    user_id: int = Field(..., description="User ID creating the campaign")
    platform: str = Field(..., description="Advertising platform")
    campaign_name: str = Field(..., description="Name of the campaign")
    product_service: str = Field(..., description="Product or service being advertised")
    target_audience: str = Field(..., description="Target audience description")
    ad_objective: str = Field(..., description="Primary objective of the campaign")
    budget_range: str = Field(..., description="Budget range for the campaign")
    campaign_duration: int = Field(..., description="Duration of campaign in days")
    ad_types: List[str] = Field(..., description="List of ad types to create")

class OptimizeAdCopyRequest(BaseModel):
    optimization_type: str = Field(..., description="Type of optimization (improve_headlines, enhance_persuasion, optimize_cta, a_b_testing)")
    optimization_params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for optimization")

class AdCopyResponse(BaseModel):
    success: bool
    project_id: int
    content_piece_id: int
    ad_copy: str
    variations: List[str]
    performance_prediction: str
    platform_optimizations: Dict[str, Any]
    copywriting_tips: List[str]
    timestamp: str

class AdCampaignResponse(BaseModel):
    success: bool
    project_id: int
    campaign_strategy: str
    campaign_ads: List[Dict[str, Any]]
    platform: str
    ad_types: List[str]
    timestamp: str

class OptimizationResponse(BaseModel):
    success: bool
    optimized_copy: str
    word_count: int
    optimization_type: str
    timestamp: str

# Dependency
async def get_ad_copywriting_service() -> AdCopywritingService:
    """Get ad copywriting service instance"""
    service = AdCopywritingService()
    await service.initialize()
    return service

# Endpoints
@router.post("/create", response_model=AdCopyResponse, status_code=status.HTTP_201_CREATED)
async def create_ad_copy(
    request: CreateAdCopyRequest,
    service: AdCopywritingService = Depends(get_ad_copywriting_service)
):
    """Create AI-powered ad copy for specified platform and ad type"""
    try:
        result = await service.create_ad_copy(
            user_id=request.user_id,
            platform=request.platform,
            ad_type=request.ad_type,
            product_service=request.product_service,
            target_audience=request.target_audience,
            ad_objective=request.ad_objective,
            budget_range=request.budget_range,
            call_to_action=request.call_to_action,
            tone=request.tone
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to create ad copy")
            )
        
        return AdCopyResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ad copy creation failed: {str(e)}"
        )

@router.post("/campaign", response_model=AdCampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_ad_campaign(
    request: CreateAdCampaignRequest,
    service: AdCopywritingService = Depends(get_ad_copywriting_service)
):
    """Create comprehensive ad campaign with multiple ad types"""
    try:
        result = await service.create_ad_campaign(
            user_id=request.user_id,
            platform=request.platform,
            campaign_name=request.campaign_name,
            product_service=request.product_service,
            target_audience=request.target_audience,
            ad_objective=request.ad_objective,
            budget_range=request.budget_range,
            campaign_duration=request.campaign_duration,
            ad_types=request.ad_types
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to create ad campaign")
            )
        
        return AdCampaignResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ad campaign creation failed: {str(e)}"
        )

@router.post("/{content_piece_id}/optimize", response_model=OptimizationResponse)
async def optimize_ad_copy(
    content_piece_id: int,
    request: OptimizeAdCopyRequest,
    service: AdCopywritingService = Depends(get_ad_copywriting_service)
):
    """Optimize existing ad copy for better performance"""
    try:
        result = await service.optimize_ad_copy(
            content_piece_id=content_piece_id,
            optimization_type=request.optimization_type,
            optimization_params=request.optimization_params
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to optimize ad copy")
            )
        
        return OptimizationResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ad copy optimization failed: {str(e)}"
        )

@router.get("/platforms")
async def get_ad_platforms():
    """Get list of supported advertising platforms"""
    return {
        "platforms": [
            {
                "id": "google_ads",
                "name": "Google Ads",
                "description": "Search and display advertising on Google network",
                "ad_types": ["search", "display", "shopping", "video"],
                "character_limits": {
                    "headlines": 30,
                    "descriptions": 90
                }
            },
            {
                "id": "facebook_ads",
                "name": "Facebook Ads",
                "description": "Social media advertising on Facebook and Instagram",
                "ad_types": ["feed", "stories", "reels", "carousel"],
                "character_limits": {
                    "primary_text": 125,
                    "headlines": 40
                }
            },
            {
                "id": "instagram_ads",
                "name": "Instagram Ads",
                "description": "Visual advertising on Instagram platform",
                "ad_types": ["feed", "stories", "reels", "explore"],
                "character_limits": {
                    "caption": 125,
                    "hashtags": "5-15 recommended"
                }
            },
            {
                "id": "linkedin_ads",
                "name": "LinkedIn Ads",
                "description": "Professional B2B advertising on LinkedIn",
                "ad_types": ["sponsored_content", "message_ads", "dynamic_ads"],
                "character_limits": {
                    "headlines": 70,
                    "descriptions": 150
                }
            },
            {
                "id": "twitter_ads",
                "name": "Twitter Ads",
                "description": "Real-time advertising on Twitter platform",
                "ad_types": ["promoted_tweets", "promoted_accounts", "promoted_trends"],
                "character_limits": {
                    "tweet": 280,
                    "hashtags": "1-3 recommended"
                }
            }
        ]
    }

@router.get("/ad-types")
async def get_ad_types():
    """Get list of supported ad types"""
    return {
        "ad_types": [
            {
                "id": "search",
                "name": "Search Ads",
                "description": "Text-based ads shown in search results",
                "best_for": ["lead_generation", "sales", "website_traffic"],
                "platforms": ["google_ads", "bing_ads"]
            },
            {
                "id": "display",
                "name": "Display Ads",
                "description": "Visual banner ads across websites",
                "best_for": ["brand_awareness", "remarketing", "visual_products"],
                "platforms": ["google_ads", "facebook_ads", "linkedin_ads"]
            },
            {
                "id": "social",
                "name": "Social Media Ads",
                "description": "Native ads within social media feeds",
                "best_for": ["engagement", "community_building", "brand_loyalty"],
                "platforms": ["facebook_ads", "instagram_ads", "twitter_ads", "linkedin_ads"]
            },
            {
                "id": "video",
                "name": "Video Ads",
                "description": "Video content for various platforms",
                "best_for": ["storytelling", "product_demos", "brand_emotion"],
                "platforms": ["google_ads", "facebook_ads", "instagram_ads", "youtube_ads"]
            },
            {
                "id": "shopping",
                "name": "Shopping Ads",
                "description": "Product-focused ads with images and prices",
                "best_for": ["ecommerce", "product_sales", "retail"],
                "platforms": ["google_ads", "facebook_ads", "instagram_ads"]
            }
        ]
    }

@router.get("/optimization-types")
async def get_optimization_types():
    """Get list of available optimization types"""
    return {
        "optimization_types": [
            {
                "id": "improve_headlines",
                "name": "Headline Improvement",
                "description": "Enhance headlines for better click-through rates",
                "parameters": {
                    "focus": ["engagement", "clarity", "urgency"],
                    "style": ["benefit-focused", "question-based", "number-based"]
                }
            },
            {
                "id": "enhance_persuasion",
                "name": "Persuasion Enhancement",
                "description": "Strengthen persuasive elements in ad copy",
                "parameters": {
                    "technique": ["benefit-focused", "social_proof", "urgency", "scarcity"],
                    "emotion": ["desire", "fear", "excitement", "trust"]
                }
            },
            {
                "id": "optimize_cta",
                "name": "Call-to-Action Optimization",
                "description": "Improve call-to-action for better conversions",
                "parameters": {
                    "cta_style": ["action-oriented", "benefit-focused", "urgency-based"],
                    "urgency": ["low", "moderate", "high"]
                }
            },
            {
                "id": "a_b_testing",
                "name": "A/B Testing Variants",
                "description": "Create multiple variants for testing",
                "parameters": {
                    "variant_count": [2, 3, 4, 5],
                    "testing_focus": ["headlines", "descriptions", "cta", "tone"]
                }
            }
        ]
    }

@router.get("/best-practices/{platform}")
async def get_platform_best_practices(platform: str):
    """Get platform-specific best practices for ad copywriting"""
    best_practices = {
        "google_ads": {
            "headlines": [
                "Include primary keyword in first headline",
                "Use benefit-focused language",
                "Keep under 30 characters",
                "Test different headline combinations"
            ],
            "descriptions": [
                "Use all 90 characters effectively",
                "Include clear call-to-action",
                "Highlight unique value proposition",
                "Use emotional triggers"
            ],
            "extensions": [
                "Utilize sitelink extensions",
                "Add callout extensions",
                "Use structured snippets",
                "Include call extensions"
            ]
        },
        "facebook_ads": {
            "primary_text": [
                "Hook in first sentence",
                "Tell a compelling story",
                "Use emotional language",
                "Include social proof"
            ],
            "headlines": [
                "Keep under 40 characters",
                "Use questions and curiosity",
                "Include benefit statements",
                "Test different approaches"
            ],
            "visual_optimization": [
                "Minimize text overlay",
                "Use high-quality images",
                "Ensure mobile optimization",
                "Test different creative elements"
            ]
        },
        "instagram_ads": {
            "captions": [
                "Hook in first line",
                "Use Instagram-specific language",
                "Include relevant hashtags",
                "End with clear CTA"
            ],
            "hashtag_strategy": [
                "Use 5-15 relevant hashtags",
                "Mix popular and niche hashtags",
                "Research trending hashtags",
                "Create branded hashtags"
            ],
            "visual_content": [
                "Ensure high-quality visuals",
                "Use consistent aesthetic",
                "Optimize for mobile viewing",
                "Test different content formats"
            ]
        },
        "linkedin_ads": {
            "professional_tone": [
                "Use industry terminology",
                "Focus on business outcomes",
                "Maintain professional language",
                "Include statistics and data"
            ],
            "content_strategy": [
                "Emphasize ROI and benefits",
                "Use social proof and testimonials",
                "Include clear professional CTA",
                "Target decision-makers"
            ],
            "audience_targeting": [
                "Use job title targeting",
                "Target by company size",
                "Focus on industry-specific terms",
                "Leverage LinkedIn groups"
            ]
        },
        "twitter_ads": {
            "character_optimization": [
                "Use all available characters",
                "Include relevant hashtags",
                "Keep message concise",
                "Use Twitter-specific features"
            ],
            "engagement_focus": [
                "Encourage retweets and replies",
                "Use trending topics",
                "Include clear call-to-action",
                "Respond to mentions quickly"
            ],
            "timing_strategy": [
                "Post during peak hours",
                "Use Twitter analytics",
                "Engage with trending conversations",
                "Maintain consistent posting"
            ]
        }
    }
    
    if platform.lower() not in best_practices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Best practices not available for platform: {platform}"
        )
    
    return {
        "platform": platform,
        "best_practices": best_practices[platform.lower()]
    }
