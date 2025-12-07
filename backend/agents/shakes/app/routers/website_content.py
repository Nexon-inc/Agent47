from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from ..services.website_content_service import WebsiteContentService

router = APIRouter(prefix="/website-content", tags=["Website Content"])


# Pydantic Models
class CreateLandingPageRequest(BaseModel):
    user_id: int = Field(..., description="User ID creating the landing page")
    page_title: str = Field(..., description="Title of the landing page")
    business_type: str = Field(..., description="Type of business or industry")
    target_audience: str = Field(..., description="Target audience description")
    primary_goal: str = Field(..., description="Primary goal of the landing page")
    key_benefits: List[str] = Field(..., description="Key benefits to highlight")
    call_to_action: str = Field(..., description="Desired call-to-action")
    tone: str = Field(..., description="Tone of the content")
    page_type: str = Field(default="conversion", description="Type of landing page")


class CreateWebsitePageRequest(BaseModel):
    user_id: int = Field(..., description="User ID creating the website page")
    page_title: str = Field(..., description="Title of the website page")
    page_type: str = Field(..., description="Type of website page")
    business_type: str = Field(..., description="Type of business or industry")
    target_audience: str = Field(..., description="Target audience description")
    page_purpose: str = Field(..., description="Purpose of the page")
    content_sections: List[str] = Field(..., description="List of content sections")
    tone: str = Field(..., description="Tone of the content")
    seo_keywords: List[str] = Field(default_factory=list)


class CreateWebsiteStructureRequest(BaseModel):
    user_id: int = Field(..., description="User ID creating the website structure")
    business_name: str = Field(..., description="Name of the business")
    business_type: str = Field(..., description="Type of business or industry")
    target_audience: str = Field(..., description="Target audience description")
    business_goals: List[str] = Field(..., description="List of business goals")
    tone: str = Field(..., description="Tone of the content")
    industry: str = Field(..., description="Industry or business sector")


class LandingPageResponse(BaseModel):
    success: bool
    project_id: int
    content_piece_id: int
    page_title: str
    page_structure: str
    hero_content: str
    features_content: str
    social_proof_content: str
    cta_content: str
    complete_page: str
    word_count: int
    reading_time: int
    timestamp: str


class WebsitePageResponse(BaseModel):
    success: bool
    project_id: int
    content_piece_id: int
    page_title: str
    page_structure: str
    page_content: Dict[str, str]
    meta_content: str
    complete_page: str
    word_count: int
    reading_time: int
    timestamp: str


class WebsiteStructureResponse(BaseModel):
    success: bool
    project_id: int
    content_piece_id: int
    business_name: str
    website_structure: str
    navigation_structure: str
    content_strategy: str
    word_count: int
    timestamp: str


# Dependency
async def get_website_content_service() -> WebsiteContentService:
    service = WebsiteContentService()
    await service.initialize()
    return service


# Endpoints
@router.post("/landing-page", response_model=LandingPageResponse, status_code=status.HTTP_201_CREATED)
async def create_landing_page(
    request: CreateLandingPageRequest,
    service: WebsiteContentService = Depends(get_website_content_service),
):
    try:
        result = await service.create_landing_page(
            user_id=request.user_id,
            page_title=request.page_title,
            business_type=request.business_type,
            target_audience=request.target_audience,
            primary_goal=request.primary_goal,
            key_benefits=request.key_benefits,
            call_to_action=request.call_to_action,
            tone=request.tone,
            page_type=request.page_type,
        )

        if not result.get("success"):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error", "Failed to create landing page"))

        return LandingPageResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Landing page creation failed: {str(e)}")


@router.post("/website-page", response_model=WebsitePageResponse, status_code=status.HTTP_201_CREATED)
async def create_website_page(
    request: CreateWebsitePageRequest,
    service: WebsiteContentService = Depends(get_website_content_service),
):
    try:
        result = await service.create_website_page(
            user_id=request.user_id,
            page_title=request.page_title,
            page_type=request.page_type,
            business_type=request.business_type,
            target_audience=request.target_audience,
            page_purpose=request.page_purpose,
            content_sections=request.content_sections,
            tone=request.tone,
            seo_keywords=request.seo_keywords,
        )

        if not result.get("success"):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error", "Failed to create website page"))

        return WebsitePageResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Website page creation failed: {str(e)}")


@router.post("/website-structure", response_model=WebsiteStructureResponse, status_code=status.HTTP_201_CREATED)
async def create_website_structure(
    request: CreateWebsiteStructureRequest,
    service: WebsiteContentService = Depends(get_website_content_service),
):
    try:
        result = await service.create_website_structure(
            user_id=request.user_id,
            business_name=request.business_name,
            business_type=request.business_type,
            target_audience=request.target_audience,
            business_goals=request.business_goals,
            tone=request.tone,
            industry=request.industry,
        )

        if not result.get("success"):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error", "Failed to create website structure"))

        return WebsiteStructureResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Website structure creation failed: {str(e)}")


@router.get("/landing-page-types")
async def get_landing_page_types():
    return {
        "landing_page_types": [
            {
                "id": "conversion",
                "name": "Conversion Landing Page",
                "description": "Focused on converting visitors to customers",
                "best_for": ["product_launches", "service_signups", "lead_generation"],
                "key_sections": ["hero", "features", "social_proof", "cta"],
                "conversion_focus": "high",
            },
            {
                "id": "lead_generation",
                "name": "Lead Generation Landing Page",
                "description": "Designed to capture lead information",
                "best_for": ["newsletter_signups", "whitepaper_downloads", "consultation_booking"],
                "key_sections": ["hero", "value_proposition", "lead_form", "cta"],
                "conversion_focus": "medium",
            },
        ]
    }


@router.get("/website-page-types")
async def get_website_page_types():
    return {
        "website_page_types": [
            {"id": "home", "name": "Home Page", "description": "Main landing page for the website"},
            {"id": "about", "name": "About Page", "description": "Company information and story"},
        ]
    }


@router.get("/content-sections")
async def get_content_sections():
    return {
        "content_sections": [
            {"id": "hero", "name": "Hero Section", "description": "Main headline and value proposition"},
            {"id": "about", "name": "About Section", "description": "Company or service introduction"},
        ]
    }


@router.get("/best-practices")
async def get_website_best_practices():
    return {
        "landing_page_best_practices": {
            "structure": [
                "Clear value proposition above the fold",
                "Single focus and goal per page",
            ]
        },
        "website_best_practices": {
            "navigation": ["Clear and intuitive menu structure", "Consistent navigation across pages"]
        },
    }
