from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from ..database import get_shakes_database
from ..services.email_writing_service import EmailWritingService

router = APIRouter(prefix="/email-writing", tags=["Email Writing"])

# Pydantic Models
class CreateEmailSequenceRequest(BaseModel):
    user_id: int = Field(..., description="User ID creating the email sequence")
    sequence_name: str = Field(..., description="Name of the email sequence")
    email_type: str = Field(..., description="Type of email (welcome, nurture, sales, onboarding)")
    target_audience: str = Field(..., description="Target audience description")
    business_goal: str = Field(..., description="Primary business objective")
    sequence_length: int = Field(..., description="Number of emails in sequence")
    tone: str = Field(..., description="Tone of the emails")
    industry: str = Field(..., description="Industry or business sector")
    call_to_action: str = Field(..., description="Desired call-to-action")

class CreateNewsletterRequest(BaseModel):
    user_id: int = Field(..., description="User ID creating the newsletter")
    newsletter_title: str = Field(..., description="Title of the newsletter")
    newsletter_type: str = Field(..., description="Type of newsletter (weekly, monthly, industry, company)")
    target_audience: str = Field(..., description="Target audience description")
    industry: str = Field(..., description="Industry or business sector")
    content_sections: List[str] = Field(..., description="List of content sections")
    tone: str = Field(..., description="Tone of the newsletter")
    include_analytics: bool = Field(default=True, description="Include analytics section")

class EmailSequenceResponse(BaseModel):
    success: bool
    project_id: int
    sequence_strategy: str
    email_sequence: List[Dict[str, Any]]
    email_type: str
    target_audience: str
    business_goal: str
    timestamp: str

class NewsletterResponse(BaseModel):
    success: bool
    project_id: int
    content_piece_id: int
    newsletter_title: str
    newsletter_structure: str
    newsletter_content: Dict[str, str]
    complete_newsletter: str
    word_count: int
    reading_time: int
    timestamp: str

# Dependency
async def get_email_writing_service() -> EmailWritingService:
    """Get email writing service instance"""
    service = EmailWritingService()
    await service.initialize()
    return service

# Endpoints
@router.post("/sequence", response_model=EmailSequenceResponse, status_code=status.HTTP_201_CREATED)
async def create_email_sequence(
    request: CreateEmailSequenceRequest,
    service: EmailWritingService = Depends(get_email_writing_service)
):
    """Create AI-powered email sequence with multiple emails"""
    try:
        result = await service.create_email_sequence(
            user_id=request.user_id,
            sequence_name=request.sequence_name,
            email_type=request.email_type,
            target_audience=request.target_audience,
            business_goal=request.business_goal,
            sequence_length=request.sequence_length,
            tone=request.tone,
            industry=request.industry,
            call_to_action=request.call_to_action
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to create email sequence")
            )
        
        return EmailSequenceResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email sequence creation failed: {str(e)}"
        )

@router.post("/newsletter", response_model=NewsletterResponse, status_code=status.HTTP_201_CREATED)
async def create_newsletter(
    request: CreateNewsletterRequest,
    service: EmailWritingService = Depends(get_email_writing_service)
):
    """Create comprehensive newsletter with multiple sections"""
    try:
        result = await service.create_newsletter(
            user_id=request.user_id,
            newsletter_title=request.newsletter_title,
            newsletter_type=request.newsletter_type,
            target_audience=request.target_audience,
            industry=request.industry,
            content_sections=request.content_sections,
            tone=request.tone,
            include_analytics=request.include_analytics
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to create newsletter")
            )
        
        return NewsletterResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Newsletter creation failed: {str(e)}"
        )

@router.get("/email-types")
async def get_email_types():
    """Get list of supported email types"""
    return {
        "email_types": [
            {
                "id": "welcome",
                "name": "Welcome Series",
                "description": "Onboarding emails for new subscribers or customers",
                "best_for": ["new_user_onboarding", "customer_activation", "relationship_building"],
                "typical_length": [3, 5, 7],
                "key_objectives": ["introduction", "value_delivery", "engagement"]
            },
            {
                "id": "nurture",
                "name": "Nurture Series",
                "description": "Educational content to build relationships and trust",
                "best_for": ["lead_nurturing", "thought_leadership", "brand_awareness"],
                "typical_length": [5, 10, 15],
                "key_objectives": ["education", "trust_building", "engagement"]
            },
            {
                "id": "sales",
                "name": "Sales Series",
                "description": "Conversion-focused emails to drive sales",
                "best_for": ["product_launches", "promotions", "sales_funnels"],
                "typical_length": [3, 7, 10],
                "key_objectives": ["conversion", "revenue", "action"]
            },
            {
                "id": "onboarding",
                "name": "Onboarding Series",
                "description": "Product or service setup and training emails",
                "best_for": ["software_onboarding", "service_setup", "user_training"],
                "typical_length": [5, 8, 12],
                "key_objectives": ["adoption", "training", "success"]
            },
            {
                "id": "reengagement",
                "name": "Re-engagement Series",
                "description": "Win-back campaigns for inactive users",
                "best_for": ["churn_prevention", "user_reactivation", "loyalty_building"],
                "typical_length": [3, 5, 7],
                "key_objectives": ["reactivation", "engagement", "retention"]
            }
        ]
    }

@router.get("/newsletter-types")
async def get_newsletter_types():
    """Get list of supported newsletter types"""
    return {
        "newsletter_types": [
            {
                "id": "weekly",
                "name": "Weekly Newsletter",
                "description": "Regular weekly updates and insights",
                "best_for": ["industry_updates", "company_news", "weekly_insights"],
                "typical_sections": ["industry_news", "company_updates", "tips_tricks", "upcoming_events"],
                "frequency": "weekly"
            },
            {
                "id": "monthly",
                "name": "Monthly Newsletter",
                "description": "Comprehensive monthly roundup and analysis",
                "best_for": ["monthly_reviews", "industry_analysis", "company_reports"],
                "typical_sections": ["monthly_highlights", "industry_trends", "company_achievements", "next_month_preview"],
                "frequency": "monthly"
            },
            {
                "id": "industry",
                "name": "Industry Newsletter",
                "description": "Industry-specific insights and trends",
                "best_for": ["thought_leadership", "industry_expertise", "professional_development"],
                "typical_sections": ["industry_news", "trend_analysis", "expert_insights", "resources"],
                "frequency": "bi-weekly"
            },
            {
                "id": "company",
                "name": "Company Newsletter",
                "description": "Internal company updates and culture",
                "best_for": ["employee_communication", "company_culture", "internal_updates"],
                "typical_sections": ["company_news", "employee_spotlight", "upcoming_events", "culture_corner"],
                "frequency": "monthly"
            },
            {
                "id": "product",
                "name": "Product Newsletter",
                "description": "Product updates and feature announcements",
                "best_for": ["product_updates", "feature_releases", "user_education"],
                "typical_sections": ["new_features", "product_tips", "user_stories", "upcoming_releases"],
                "frequency": "monthly"
            }
        ]
    }

@router.get("/content-sections")
async def get_content_sections():
    """Get list of common newsletter content sections"""
    return {
        "content_sections": [
            {
                "id": "industry_news",
                "name": "Industry News",
                "description": "Latest news and developments in the industry",
                "content_type": "news_summary",
                "typical_length": "150-300 words"
            },
            {
                "id": "company_updates",
                "name": "Company Updates",
                "description": "Internal company news and announcements",
                "content_type": "company_news",
                "typical_length": "100-250 words"
            },
            {
                "id": "tips_tricks",
                "name": "Tips & Tricks",
                "description": "Helpful advice and best practices",
                "content_type": "how_to",
                "typical_length": "200-400 words"
            },
            {
                "id": "case_studies",
                "name": "Case Studies",
                "description": "Success stories and customer examples",
                "content_type": "story",
                "typical_length": "300-600 words"
            },
            {
                "id": "upcoming_events",
                "name": "Upcoming Events",
                "description": "Events, webinars, and important dates",
                "content_type": "event_info",
                "typical_length": "100-200 words"
            },
            {
                "id": "resources",
                "name": "Resources",
                "description": "Tools, articles, and helpful resources",
                "content_type": "resource_list",
                "typical_length": "150-300 words"
            },
            {
                "id": "q_and_a",
                "name": "Q&A",
                "description": "Common questions and expert answers",
                "content_type": "faq",
                "typical_length": "200-400 words"
            },
            {
                "id": "trend_analysis",
                "name": "Trend Analysis",
                "description": "Analysis of current and emerging trends",
                "content_type": "analysis",
                "typical_length": "300-500 words"
            }
        ]
    }

@router.get("/best-practices")
async def get_email_best_practices():
    """Get email and newsletter best practices"""
    return {
        "email_best_practices": {
            "subject_lines": [
                "Keep under 50 characters",
                "Use curiosity and urgency",
                "Avoid spam trigger words",
                "Personalize when possible",
                "Test different approaches"
            ],
            "content_structure": [
                "Clear opening hook",
                "Scannable paragraphs",
                "Strong call-to-action",
                "Mobile-friendly formatting",
                "Professional signature"
            ],
            "timing": [
                "Send during business hours",
                "Test different days and times",
                "Consider time zones",
                "Avoid holidays and weekends",
                "Maintain consistent schedule"
            ],
            "personalization": [
                "Use recipient's name",
                "Segment by behavior",
                "Dynamic content blocks",
                "Personalized recommendations",
                "Customized call-to-action"
            ]
        },
        "newsletter_best_practices": {
            "design": [
                "Clean, professional layout",
                "Consistent branding",
                "Mobile-responsive design",
                "Clear content hierarchy",
                "Easy-to-scan format"
            ],
            "content": [
                "Mix of content types",
                "Engaging headlines",
                "Relevant information",
                "Actionable insights",
                "Regular publishing schedule"
            ],
            "engagement": [
                "Include social sharing",
                "Encourage feedback",
                "Interactive elements",
                "Clear navigation",
                "Subscription management"
            ]
        }
    }
