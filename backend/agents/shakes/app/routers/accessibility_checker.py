from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..services.accessibility_checker_service import AccessibilityCheckerService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/accessibility-checker", tags=["Accessibility Checker"])

# Pydantic Models
class CheckAccessibilityRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    accessibility_standards: List[str] = Field(..., description="Accessibility standards")
    check_categories: List[str] = Field(..., description="Check categories")

class FixAccessibilityIssuesRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    issue_categories: List[str] = Field(..., description="Issue categories")
    fix_priorities: List[str] = Field(..., description="Fix priorities")

class GenerateAltTextRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    image_elements: List[Dict[str, Any]] = Field(..., description="Image elements")
    alt_text_style: str = Field(..., description="Alt text style")

class ValidateColorContrastRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    color_elements: List[Dict[str, Any]] = Field(..., description="Color elements")
    contrast_standards: List[str] = Field(..., description="Contrast standards")

# Dependency
async def get_accessibility_checker_service() -> AccessibilityCheckerService:
    """Get accessibility checker service instance"""
    service = AccessibilityCheckerService()
    await service.initialize()
    return service

# Endpoints
@router.post("/check", response_model=Dict[str, Any], status_code=200)
async def check_accessibility(
    request: CheckAccessibilityRequest,
    service: AccessibilityCheckerService = Depends(get_accessibility_checker_service)
):
    """Check content accessibility compliance"""
    try:
        result = await service.check_accessibility(
            content_piece_id=request.content_piece_id,
            accessibility_standards=request.accessibility_standards,
            check_categories=request.check_categories
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to check accessibility")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Accessibility check failed: {str(e)}"
        )

@router.post("/fix-issues", response_model=Dict[str, Any], status_code=200)
async def fix_accessibility_issues(
    request: FixAccessibilityIssuesRequest,
    service: AccessibilityCheckerService = Depends(get_accessibility_checker_service)
):
    """Fix accessibility issues in content"""
    try:
        result = await service.fix_accessibility_issues(
            content_piece_id=request.content_piece_id,
            issue_categories=request.issue_categories,
            fix_priorities=request.fix_priorities
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to fix accessibility issues")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Accessibility fix failed: {str(e)}"
        )

@router.post("/generate-alt-text", response_model=Dict[str, Any], status_code=201)
async def generate_alt_text(
    request: GenerateAltTextRequest,
    service: AccessibilityCheckerService = Depends(get_accessibility_checker_service)
):
    """Generate alt text for images and visual elements"""
    try:
        result = await service.generate_alt_text(
            content_piece_id=request.content_piece_id,
            image_elements=request.image_elements,
            alt_text_style=request.alt_text_style
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate alt text")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Alt text generation failed: {str(e)}"
        )

@router.post("/validate-color-contrast", response_model=Dict[str, Any], status_code=200)
async def validate_color_contrast(
    request: ValidateColorContrastRequest,
    service: AccessibilityCheckerService = Depends(get_accessibility_checker_service)
):
    """Validate color contrast for accessibility"""
    try:
        result = await service.validate_color_contrast(
            content_piece_id=request.content_piece_id,
            color_elements=request.color_elements,
            contrast_standards=request.contrast_standards
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to validate color contrast")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Color contrast validation failed: {str(e)}"
        )

@router.get("/accessibility-standards")
async def get_accessibility_standards():
    """Get available accessibility standards for checking"""
    return {
        "accessibility_standards": [
            {
                "id": "wcag_2_1_aa",
                "name": "WCAG 2.1 AA",
                "description": "Web Content Accessibility Guidelines 2.1 Level AA",
                "level": "AA",
                "compliance_requirements": [
                    "color_contrast_ratio_4_5_1",
                    "text_resize_200_percent",
                    "keyboard_navigation",
                    "focus_indicators",
                    "alt_text_for_images",
                    "heading_structure"
                ],
                "legal_requirement": "ADA_compliant"
            },
            {
                "id": "wcag_2_1_aaa",
                "name": "WCAG 2.1 AAA",
                "description": "Web Content Accessibility Guidelines 2.1 Level AAA",
                "level": "AAA",
                "compliance_requirements": [
                    "color_contrast_ratio_7_1",
                    "text_resize_200_percent",
                    "no_autoplay_audio",
                    "sign_language_interpretation",
                    "extended_audio_description",
                    "low_background_audio"
                ],
                "legal_requirement": "enhanced_accessibility"
            },
            {
                "id": "section_508",
                "name": "Section 508",
                "description": "Section 508 of the Rehabilitation Act",
                "level": "Federal",
                "compliance_requirements": [
                    "accessible_technology",
                    "electronic_documents",
                    "web_content",
                    "software_applications",
                    "multimedia_presentations",
                    "telecommunications"
                ],
                "legal_requirement": "federal_requirement"
            },
            {
                "id": "ada",
                "name": "ADA",
                "description": "Americans with Disabilities Act",
                "level": "Legal",
                "compliance_requirements": [
                    "equal_access",
                    "reasonable_accommodations",
                    "auxiliary_aids",
                    "effective_communication",
                    "program_accessibility",
                    "nondiscrimination"
                ],
                "legal_requirement": "civil_rights_law"
            }
        ]
    }

@router.get("/check-categories")
async def get_check_categories():
    """Get available check categories for accessibility"""
    return {
        "check_categories": [
            {
                "id": "text_accessibility",
                "name": "Text Accessibility",
                "description": "Text and typography accessibility checks",
                "checks": [
                    "font_size_compliance",
                    "line_spacing_compliance",
                    "text_contrast_compliance",
                    "readability_score",
                    "language_identification"
                ],
                "importance": "high"
            },
            {
                "id": "visual_accessibility",
                "name": "Visual Accessibility",
                "description": "Visual elements and imagery accessibility",
                "checks": [
                    "alt_text_presence",
                    "alt_text_quality",
                    "color_dependency",
                    "visual_hierarchy",
                    "focus_indicators"
                ],
                "importance": "high"
            },
            {
                "id": "navigation_accessibility",
                "name": "Navigation Accessibility",
                "description": "Navigation and structure accessibility",
                "checks": [
                    "heading_structure",
                    "link_descriptions",
                    "keyboard_navigation",
                    "skip_links",
                    "landmark_roles"
                ],
                "importance": "high"
            },
            {
                "id": "interactive_accessibility",
                "name": "Interactive Accessibility",
                "description": "Interactive elements accessibility",
                "checks": [
                    "form_labels",
                    "button_descriptions",
                    "error_handling",
                    "focus_management",
                    "interactive_feedback"
                ],
                "importance": "medium"
            },
            {
                "id": "media_accessibility",
                "name": "Media Accessibility",
                "description": "Media content accessibility",
                "checks": [
                    "video_captions",
                    "audio_transcripts",
                    "media_controls",
                    "autoplay_compliance",
                    "media_descriptions"
                ],
                "importance": "medium"
            }
        ]
    }

@router.get("/alt-text-styles")
async def get_alt_text_styles():
    """Get available alt text styles for generation"""
    return {
        "alt_text_styles": [
            {
                "id": "descriptive",
                "name": "Descriptive",
                "description": "Detailed description of visual content",
                "characteristics": ["detailed", "comprehensive", "contextual", "informative"],
                "best_for": ["complex_images", "charts", "diagrams", "artwork"],
                "length": "long"
            },
            {
                "id": "concise",
                "name": "Concise",
                "description": "Brief, essential description",
                "characteristics": ["brief", "essential", "focused", "direct"],
                "best_for": ["simple_images", "icons", "decorative_images", "thumbnails"],
                "length": "short"
            },
            {
                "id": "functional",
                "name": "Functional",
                "description": "Focus on function and purpose",
                "characteristics": ["purpose_focused", "action_oriented", "functional", "practical"],
                "best_for": ["buttons", "links", "interactive_elements", "navigation"],
                "length": "medium"
            },
            {
                "id": "emotional",
                "name": "Emotional",
                "description": "Captures emotional context and mood",
                "characteristics": ["emotional", "mood_capturing", "atmospheric", "expressive"],
                "best_for": ["lifestyle_images", "portraits", "scenic_views", "artistic_content"],
                "length": "medium"
            },
            {
                "id": "technical",
                "name": "Technical",
                "description": "Technical and precise description",
                "characteristics": ["technical", "precise", "detailed", "accurate"],
                "best_for": ["technical_diagrams", "screenshots", "data_visualizations", "scientific_content"],
                "length": "long"
            }
        ]
    }

@router.get("/contrast-standards")
async def get_contrast_standards():
    """Get available color contrast standards"""
    return {
        "contrast_standards": [
            {
                "id": "wcag_aa",
                "name": "WCAG AA",
                "description": "WCAG 2.1 Level AA contrast requirements",
                "normal_text": "4.5:1",
                "large_text": "3:1",
                "ui_components": "3:1",
                "graphical_objects": "3:1",
                "compliance_level": "AA"
            },
            {
                "id": "wcag_aaa",
                "name": "WCAG AAA",
                "description": "WCAG 2.1 Level AAA contrast requirements",
                "normal_text": "7:1",
                "large_text": "4.5:1",
                "ui_components": "4.5:1",
                "graphical_objects": "4.5:1",
                "compliance_level": "AAA"
            },
            {
                "id": "section_508",
                "name": "Section 508",
                "description": "Section 508 contrast requirements",
                "normal_text": "4.5:1",
                "large_text": "3:1",
                "ui_components": "3:1",
                "graphical_objects": "3:1",
                "compliance_level": "Federal"
            },
            {
                "id": "enhanced",
                "name": "Enhanced",
                "description": "Enhanced contrast for better accessibility",
                "normal_text": "7:1",
                "large_text": "4.5:1",
                "ui_components": "4.5:1",
                "graphical_objects": "4.5:1",
                "compliance_level": "Enhanced"
            }
        ]
    }

@router.get("/fix-priorities")
async def get_fix_priorities():
    """Get available fix priorities for accessibility issues"""
    return {
        "fix_priorities": [
            {
                "id": "critical",
                "name": "Critical",
                "description": "Critical accessibility issues that must be fixed",
                "examples": ["missing_alt_text", "no_keyboard_navigation", "insufficient_contrast"],
                "impact": "high",
                "urgency": "immediate"
            },
            {
                "id": "high",
                "name": "High",
                "description": "High priority accessibility issues",
                "examples": ["poor_heading_structure", "missing_form_labels", "autoplay_media"],
                "impact": "high",
                "urgency": "within_24_hours"
            },
            {
                "id": "medium",
                "name": "Medium",
                "description": "Medium priority accessibility issues",
                "examples": ["inconsistent_focus_indicators", "missing_skip_links", "poor_color_choices"],
                "impact": "medium",
                "urgency": "within_week"
            },
            {
                "id": "low",
                "name": "Low",
                "description": "Low priority accessibility improvements",
                "examples": ["minor_contrast_improvements", "enhanced_descriptions", "additional_metadata"],
                "impact": "low",
                "urgency": "within_month"
            }
        ]
    }
