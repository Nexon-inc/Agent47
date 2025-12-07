from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..services.content_localization_service import ContentLocalizationService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/content-localization", tags=["Content Localization"])

# Pydantic Models
class LocalizeContentRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    target_languages: List[str] = Field(..., description="Target languages")
    localization_options: Dict[str, Any] = Field(default={}, description="Localization options")
    cultural_adaptations: Dict[str, Any] = Field(default={}, description="Cultural adaptations")

class AdaptContentRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    target_regions: List[str] = Field(..., description="Target regions")
    adaptation_type: str = Field(..., description="Adaptation type")
    cultural_context: Dict[str, Any] = Field(default={}, description="Cultural context")

class ValidateLocalizationRequest(BaseModel):
    localized_content_id: int = Field(..., description="Localized content ID")
    validation_criteria: List[str] = Field(..., description="Validation criteria")
    quality_standards: Dict[str, Any] = Field(default={}, description="Quality standards")

class OptimizeLocalizationRequest(BaseModel):
    localized_content_id: int = Field(..., description="Localized content ID")
    optimization_goals: List[str] = Field(..., description="Optimization goals")
    performance_metrics: Dict[str, Any] = Field(default={}, description="Performance metrics")

# Dependency
async def get_content_localization_service() -> ContentLocalizationService:
    """Get content localization service instance"""
    service = ContentLocalizationService()
    await service.initialize()
    return service

# Endpoints
@router.post("/localize", response_model=Dict[str, Any], status_code=201)
async def localize_content(
    request: LocalizeContentRequest,
    service: ContentLocalizationService = Depends(get_content_localization_service)
):
    """Localize content for multiple languages and regions"""
    try:
        result = await service.localize_content(
            content_piece_id=request.content_piece_id,
            target_languages=request.target_languages,
            localization_options=request.localization_options,
            cultural_adaptations=request.cultural_adaptations
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to localize content")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content localization failed: {str(e)}"
        )

@router.post("/adapt", response_model=Dict[str, Any], status_code=200)
async def adapt_content(
    request: AdaptContentRequest,
    service: ContentLocalizationService = Depends(get_content_localization_service)
):
    """Adapt content for specific regions and cultural contexts"""
    try:
        result = await service.adapt_content(
            content_piece_id=request.content_piece_id,
            target_regions=request.target_regions,
            adaptation_type=request.adaptation_type,
            cultural_context=request.cultural_context
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to adapt content")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content adaptation failed: {str(e)}"
        )

@router.post("/validate", response_model=Dict[str, Any], status_code=200)
async def validate_localization(
    request: ValidateLocalizationRequest,
    service: ContentLocalizationService = Depends(get_content_localization_service)
):
    """Validate localized content quality and accuracy"""
    try:
        result = await service.validate_localization(
            localized_content_id=request.localized_content_id,
            validation_criteria=request.validation_criteria,
            quality_standards=request.quality_standards
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to validate localization")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Localization validation failed: {str(e)}"
        )

@router.post("/optimize", response_model=Dict[str, Any], status_code=200)
async def optimize_localization(
    request: OptimizeLocalizationRequest,
    service: ContentLocalizationService = Depends(get_content_localization_service)
):
    """Optimize localized content for better performance"""
    try:
        result = await service.optimize_localization(
            localized_content_id=request.localized_content_id,
            optimization_goals=request.optimization_goals,
            performance_metrics=request.performance_metrics
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to optimize localization")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Localization optimization failed: {str(e)}"
        )

@router.get("/supported-languages")
async def get_supported_languages():
    """Get supported languages for localization"""
    return {
        "supported_languages": [
            {
                "id": "en",
                "name": "English",
                "native_name": "English",
                "region": "Global",
                "complexity": "low",
                "localization_effort": "minimal"
            },
            {
                "id": "es",
                "name": "Spanish",
                "native_name": "Español",
                "region": "Latin America, Spain",
                "complexity": "medium",
                "localization_effort": "moderate"
            },
            {
                "id": "fr",
                "name": "French",
                "native_name": "Français",
                "region": "France, Canada, Africa",
                "complexity": "medium",
                "localization_effort": "moderate"
            },
            {
                "id": "de",
                "name": "German",
                "native_name": "Deutsch",
                "region": "Germany, Austria, Switzerland",
                "complexity": "high",
                "localization_effort": "high"
            },
            {
                "id": "zh",
                "name": "Chinese",
                "native_name": "中文",
                "region": "China, Taiwan, Singapore",
                "complexity": "very_high",
                "localization_effort": "very_high"
            },
            {
                "id": "ja",
                "name": "Japanese",
                "native_name": "日本語",
                "region": "Japan",
                "complexity": "very_high",
                "localization_effort": "very_high"
            },
            {
                "id": "ko",
                "name": "Korean",
                "native_name": "한국어",
                "region": "South Korea",
                "complexity": "high",
                "localization_effort": "high"
            },
            {
                "id": "pt",
                "name": "Portuguese",
                "native_name": "Português",
                "region": "Brazil, Portugal",
                "complexity": "medium",
                "localization_effort": "moderate"
            },
            {
                "id": "it",
                "name": "Italian",
                "native_name": "Italiano",
                "region": "Italy",
                "complexity": "medium",
                "localization_effort": "moderate"
            },
            {
                "id": "ru",
                "name": "Russian",
                "native_name": "Русский",
                "region": "Russia, Eastern Europe",
                "complexity": "high",
                "localization_effort": "high"
            }
        ]
    }

@router.get("/cultural-adaptations")
async def get_cultural_adaptations():
    """Get available cultural adaptations for localization"""
    return {
        "cultural_adaptations": [
            {
                "id": "date_format",
                "name": "Date Format",
                "description": "Adapt date formats to regional preferences",
                "examples": ["MM/DD/YYYY (US)", "DD/MM/YYYY (EU)", "YYYY/MM/DD (Asia)"],
                "importance": "high"
            },
            {
                "id": "currency",
                "name": "Currency",
                "description": "Convert and format currency for local markets",
                "examples": ["USD ($)", "EUR (€)", "JPY (¥)", "GBP (£)"],
                "importance": "high"
            },
            {
                "id": "measurements",
                "name": "Measurements",
                "description": "Convert units of measurement",
                "examples": ["Imperial (US)", "Metric (EU)", "Traditional (Asia)"],
                "importance": "medium"
            },
            {
                "id": "color_preferences",
                "name": "Color Preferences",
                "description": "Adapt colors to cultural meanings",
                "examples": ["Red (luck in China, danger in US)", "White (purity in US, mourning in Asia)"],
                "importance": "medium"
            },
            {
                "id": "imagery",
                "name": "Imagery",
                "description": "Adapt images to cultural contexts",
                "examples": ["Local landmarks", "Cultural symbols", "Regional aesthetics"],
                "importance": "high"
            },
            {
                "id": "tone_style",
                "name": "Tone and Style",
                "description": "Adapt communication style to cultural norms",
                "examples": ["Formal vs informal", "Direct vs indirect", "Humor styles"],
                "importance": "high"
            }
        ]
    }

@router.get("/validation-criteria")
async def get_validation_criteria():
    """Get available validation criteria for localized content"""
    return {
        "validation_criteria": [
            {
                "id": "linguistic_accuracy",
                "name": "Linguistic Accuracy",
                "description": "Accuracy of translation and language usage",
                "checks": ["grammar", "spelling", "syntax", "terminology"],
                "importance": "critical"
            },
            {
                "id": "cultural_appropriateness",
                "name": "Cultural Appropriateness",
                "description": "Cultural sensitivity and appropriateness",
                "checks": ["cultural_references", "sensitivity", "local_norms", "taboos"],
                "importance": "critical"
            },
            {
                "id": "brand_consistency",
                "name": "Brand Consistency",
                "description": "Consistency with brand voice and values",
                "checks": ["brand_voice", "messaging", "tone", "values_alignment"],
                "importance": "high"
            },
            {
                "id": "technical_accuracy",
                "name": "Technical Accuracy",
                "description": "Technical and functional accuracy",
                "checks": ["functionality", "links", "formatting", "compatibility"],
                "importance": "high"
            },
            {
                "id": "legal_compliance",
                "name": "Legal Compliance",
                "description": "Compliance with local laws and regulations",
                "checks": ["privacy_laws", "advertising_regulations", "disclaimers", "terms"],
                "importance": "critical"
            },
            {
                "id": "seo_optimization",
                "name": "SEO Optimization",
                "description": "Search engine optimization for local markets",
                "checks": ["keywords", "meta_tags", "local_seo", "search_terms"],
                "importance": "medium"
            }
        ]
    }

@router.get("/optimization-goals")
async def get_optimization_goals():
    """Get available optimization goals for localized content"""
    return {
        "optimization_goals": [
            {
                "id": "engagement",
                "name": "Increase Engagement",
                "description": "Optimize for higher engagement in target markets",
                "target_metrics": ["engagement_rate", "time_spent", "interaction_rate"],
                "strategies": ["cultural_relevance", "local_trends", "audience_preferences"]
            },
            {
                "id": "conversion",
                "name": "Improve Conversion",
                "description": "Optimize for better conversion rates in local markets",
                "target_metrics": ["conversion_rate", "sales", "lead_generation"],
                "strategies": ["local_payment_methods", "cultural_trust_signals", "localized_ctas"]
            },
            {
                "id": "brand_awareness",
                "name": "Build Brand Awareness",
                "description": "Increase brand awareness in new markets",
                "target_metrics": ["brand_recognition", "market_penetration", "share_of_voice"],
                "strategies": ["local_influencers", "cultural_partnerships", "localized_campaigns"]
            },
            {
                "id": "user_experience",
                "name": "Enhance User Experience",
                "description": "Improve user experience for local audiences",
                "target_metrics": ["user_satisfaction", "usability", "accessibility"],
                "strategies": ["local_ux_patterns", "cultural_navigation", "localized_interface"]
            }
        ]
    }

@router.get("/localization-templates")
async def get_localization_templates():
    """Get available templates for common localization scenarios"""
    return {
        "localization_templates": [
            {
                "id": "ecommerce_global",
                "name": "E-commerce Global",
                "description": "Template for global e-commerce localization",
                "features": ["product_descriptions", "pricing", "shipping_info", "payment_methods"],
                "languages": ["en", "es", "fr", "de", "zh", "ja"],
                "use_cases": ["online_stores", "marketplace_sellers", "global_brands"]
            },
            {
                "id": "marketing_campaign",
                "name": "Marketing Campaign",
                "description": "Template for marketing campaign localization",
                "features": ["ad_copy", "landing_pages", "email_sequences", "social_media"],
                "languages": ["en", "es", "fr", "de", "pt", "it"],
                "use_cases": ["digital_marketing", "advertising_campaigns", "brand_promotion"]
            },
            {
                "id": "software_application",
                "name": "Software Application",
                "description": "Template for software application localization",
                "features": ["ui_text", "help_documentation", "error_messages", "user_guides"],
                "languages": ["en", "es", "fr", "de", "zh", "ja", "ko"],
                "use_cases": ["mobile_apps", "web_applications", "desktop_software"]
            },
            {
                "id": "content_marketing",
                "name": "Content Marketing",
                "description": "Template for content marketing localization",
                "features": ["blog_posts", "articles", "whitepapers", "case_studies"],
                "languages": ["en", "es", "fr", "de", "pt", "it", "ru"],
                "use_cases": ["content_marketing", "seo_content", "thought_leadership"]
            }
        ]
    }
