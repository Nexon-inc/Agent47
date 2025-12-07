from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.content_templates_service import ContentTemplatesService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/content-templates", tags=["Content Templates"])

# Pydantic Models
class CreateTemplateRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    template_name: str = Field(..., description="Template name")
    template_type: str = Field(..., description="Template type")
    template_category: str = Field(..., description="Template category")
    template_description: str = Field(..., description="Template description")
    template_structure: Dict[str, Any] = Field(..., description="Template structure")
    target_audience: str = Field(..., description="Target audience")
    industry: str = Field(..., description="Industry")
    use_cases: List[str] = Field(..., description="Use cases")

class CreateTemplateResponse(BaseModel):
    success: bool
    template_id: int
    template_name: str
    template_type: str
    template_category: str
    template_content: str
    template_structure: Dict[str, Any]
    usage_instructions: str
    target_audience: str
    industry: str
    use_cases: List[str]
    timestamp: str

class UseTemplateRequest(BaseModel):
    template_id: int = Field(..., description="Template ID")
    user_id: int = Field(..., description="User ID")
    template_variables: Dict[str, Any] = Field(..., description="Template variables")
    customization_requests: List[str] = Field(default=[], description="Customization requests")

class CustomizeTemplateRequest(BaseModel):
    template_id: int = Field(..., description="Template ID to customize")
    customization_requests: List[str] = Field(..., description="Customization requests")
    new_template_name: str = Field(default=None, description="New template name")

# Dependency
async def get_content_templates_service() -> ContentTemplatesService:
    """Get content templates service instance"""
    service = ContentTemplatesService()
    await service.initialize()
    return service

# Endpoints
@router.post("/create", response_model=CreateTemplateResponse, status_code=201)
async def create_template(
    request: CreateTemplateRequest,
    service: ContentTemplatesService = Depends(get_content_templates_service)
):
    """Create new content template"""
    try:
        result = await service.create_template(
            user_id=request.user_id,
            template_name=request.template_name,
            template_type=request.template_type,
            template_category=request.template_category,
            template_description=request.template_description,
            template_structure=request.template_structure,
            target_audience=request.target_audience,
            industry=request.industry,
            use_cases=request.use_cases
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to create template")
            )
        
        return CreateTemplateResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Template creation failed: {str(e)}"
        )

@router.post("/use", response_model=Dict[str, Any], status_code=201)
async def use_template(
    request: UseTemplateRequest,
    service: ContentTemplatesService = Depends(get_content_templates_service)
):
    """Use template to generate content"""
    try:
        result = await service.use_template(
            template_id=request.template_id,
            user_id=request.user_id,
            template_variables=request.template_variables,
            customization_requests=request.customization_requests
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to use template")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Template usage failed: {str(e)}"
        )

@router.post("/customize", response_model=Dict[str, Any], status_code=201)
async def customize_template(
    request: CustomizeTemplateRequest,
    service: ContentTemplatesService = Depends(get_content_templates_service)
):
    """Customize existing template"""
    try:
        result = await service.customize_template(
            template_id=request.template_id,
            customization_requests=request.customization_requests,
            new_template_name=request.new_template_name
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to customize template")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Template customization failed: {str(e)}"
        )

@router.get("/by-category", response_model=Dict[str, Any], status_code=200)
async def get_templates_by_category(
    category: str = Query(..., description="Template category"),
    template_type: str = Query(None, description="Template type filter"),
    industry: str = Query(None, description="Industry filter"),
    service: ContentTemplatesService = Depends(get_content_templates_service)
):
    """Get templates by category and filters"""
    try:
        result = await service.get_templates_by_category(
            category=category,
            template_type=template_type,
            industry=industry
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get templates")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Template retrieval failed: {str(e)}"
        )

@router.get("/template-categories")
async def get_template_categories():
    """Get available template categories"""
    return {
        "template_categories": [
            {
                "id": "marketing",
                "name": "Marketing",
                "description": "Templates for marketing and promotional content",
                "template_types": ["email_campaigns", "social_media", "ad_copy", "landing_pages"],
                "use_cases": ["product_launches", "promotions", "brand_awareness", "lead_generation"]
            },
            {
                "id": "content_marketing",
                "name": "Content Marketing",
                "description": "Templates for content marketing and thought leadership",
                "template_types": ["blog_posts", "articles", "whitepapers", "case_studies"],
                "use_cases": ["seo_content", "thought_leadership", "audience_education", "brand_authority"]
            },
            {
                "id": "social_media",
                "name": "Social Media",
                "description": "Templates for social media content and engagement",
                "template_types": ["posts", "stories", "captions", "hashtag_campaigns"],
                "use_cases": ["community_building", "engagement", "brand_awareness", "social_selling"]
            },
            {
                "id": "email_marketing",
                "name": "Email Marketing",
                "description": "Templates for email campaigns and newsletters",
                "template_types": ["newsletters", "promotional_emails", "welcome_series", "nurture_sequences"],
                "use_cases": ["customer_nurturing", "product_updates", "promotions", "onboarding"]
            },
            {
                "id": "sales",
                "name": "Sales",
                "description": "Templates for sales and conversion content",
                "template_types": ["proposals", "presentations", "follow_up_emails", "case_studies"],
                "use_cases": ["lead_conversion", "proposal_writing", "follow_up_sequences", "client_communication"]
            },
            {
                "id": "customer_service",
                "name": "Customer Service",
                "description": "Templates for customer service and support",
                "template_types": ["response_templates", "faq_content", "support_guides", "apology_letters"],
                "use_cases": ["customer_support", "issue_resolution", "customer_education", "relationship_management"]
            }
        ]
    }

@router.get("/template-types")
async def get_template_types():
    """Get available template types"""
    return {
        "template_types": [
            {
                "id": "blog_post",
                "name": "Blog Post",
                "description": "Long-form articles and blog posts",
                "structure": ["headline", "introduction", "body_sections", "conclusion", "cta"],
                "best_for": ["seo_content", "thought_leadership", "audience_education"],
                "typical_length": [800, 2000, 3000]
            },
            {
                "id": "email_newsletter",
                "name": "Email Newsletter",
                "description": "Email newsletters and updates",
                "structure": ["subject_line", "header", "content_sections", "footer", "unsubscribe"],
                "best_for": ["customer_updates", "news_updates", "content_roundups"],
                "typical_length": [300, 800, 1500]
            },
            {
                "id": "social_media_post",
                "name": "Social Media Post",
                "description": "Platform-specific social media content",
                "structure": ["hook", "content", "hashtags", "cta"],
                "best_for": ["engagement", "brand_awareness", "community_building"],
                "typical_length": [50, 280, 500]
            },
            {
                "id": "ad_copy",
                "name": "Ad Copy",
                "description": "Advertising and promotional copy",
                "structure": ["headline", "description", "cta", "disclaimer"],
                "best_for": ["conversions", "sales", "lead_generation"],
                "typical_length": [25, 100, 300]
            },
            {
                "id": "landing_page",
                "name": "Landing Page",
                "description": "Landing page content and structure",
                "structure": ["headline", "subheadline", "benefits", "testimonials", "cta"],
                "best_for": ["conversions", "lead_generation", "product_launches"],
                "typical_length": [200, 500, 1000]
            },
            {
                "id": "press_release",
                "name": "Press Release",
                "description": "Official announcements and news",
                "structure": ["headline", "dateline", "lead_paragraph", "body", "boilerplate"],
                "best_for": ["pr", "announcements", "media_relations"],
                "typical_length": [300, 600, 1000]
            }
        ]
    }

@router.get("/template-structures")
async def get_template_structures():
    """Get common template structures for different content types"""
    return {
        "template_structures": [
            {
                "content_type": "blog_post",
                "structure": {
                    "headline": "Compelling, SEO-optimized headline",
                    "introduction": "Hook, problem statement, and value proposition",
                    "body_sections": [
                        "Main point 1 with supporting evidence",
                        "Main point 2 with examples",
                        "Main point 3 with actionable insights"
                    ],
                    "conclusion": "Summary and call-to-action",
                    "cta": "Clear next steps for readers"
                },
                "placeholders": ["{topic}", "{target_audience}", "{key_points}", "{cta}"]
            },
            {
                "content_type": "email_newsletter",
                "structure": {
                    "subject_line": "Engaging subject line",
                    "preheader": "Supporting text for email preview",
                    "header": "Newsletter title and branding",
                    "content_sections": [
                        "Featured article or update",
                        "Secondary content pieces",
                        "Company news or updates"
                    ],
                    "footer": "Contact information and social links",
                    "unsubscribe": "Unsubscribe link and preferences"
                },
                "placeholders": ["{newsletter_name}", "{featured_content}", "{company_updates}"]
            },
            {
                "content_type": "social_media_post",
                "structure": {
                    "hook": "Attention-grabbing opening",
                    "content": "Main message or value",
                    "hashtags": "Relevant hashtags",
                    "cta": "Call-to-action or question"
                },
                "placeholders": ["{topic}", "{hashtags}", "{cta}", "{platform}"]
            },
            {
                "content_type": "ad_copy",
                "structure": {
                    "headline": "Compelling headline",
                    "description": "Benefit-focused description",
                    "cta": "Clear call-to-action",
                    "disclaimer": "Required disclaimers"
                },
                "placeholders": ["{product_name}", "{benefit}", "{cta}", "{offer}"]
            }
        ]
    }

@router.get("/customization-tips")
async def get_customization_tips():
    """Get tips for effective template customization"""
    return {
        "customization_tips": [
            {
                "category": "variable_usage",
                "title": "Variable Usage",
                "tips": [
                    "Use clear, descriptive variable names",
                    "Provide examples for each variable",
                    "Make variables flexible and adaptable",
                    "Include fallback values for optional variables"
                ]
            },
            {
                "category": "structure_adaptation",
                "title": "Structure Adaptation",
                "tips": [
                    "Adapt structure to your specific needs",
                    "Add or remove sections as required",
                    "Maintain logical flow and organization",
                    "Keep structure consistent across similar content"
                ]
            },
            {
                "category": "content_personalization",
                "title": "Content Personalization",
                "tips": [
                    "Personalize content for your audience",
                    "Use your brand voice and tone",
                    "Include relevant examples and case studies",
                    "Adapt language to your industry"
                ]
            },
            {
                "category": "quality_optimization",
                "title": "Quality Optimization",
                "tips": [
                    "Review and refine generated content",
                    "Ensure accuracy and relevance",
                    "Check for grammar and style consistency",
                    "Test content with your target audience"
                ]
            }
        ]
    }
