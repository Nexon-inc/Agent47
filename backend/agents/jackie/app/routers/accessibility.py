from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from pydantic import BaseModel, Field

from ..database import get_db
from ..services.accessibility_service import AccessibilityService

router = APIRouter(prefix="/accessibility", tags=["Accessibility Optimization"])

class AccessibilityRequest(BaseModel):
    content_type: str
    content: str
    target_audience: Optional[List[str]] = Field(default_factory=list)
    accessibility_level: str = "WCAG_AA"
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AccessibilityResponse(BaseModel):
    id: str
    original_content: str
    optimized_content: str
    alt_text: Optional[str]
    accessibility_score: float
    compliance_level: str
    recommendations: List[str]
    created_at: datetime

@router.post("/optimize-content", response_model=AccessibilityResponse)
async def optimize_content_accessibility(
    request: AccessibilityRequest,
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.optimize_content_accessibility(
            request.content_type,
            request.content,
            request.target_audience,
            request.accessibility_level,
            request.context
        )
        return AccessibilityResponse(
            id=result["id"],
            original_content=result["original_content"],
            optimized_content=result["optimized_content"],
            alt_text=result["alt_text"],
            accessibility_score=result["accessibility_score"],
            compliance_level=result["compliance_level"],
            recommendations=result["recommendations"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-alt-text")
async def generate_alt_text(
    image_url: str,
    context: Optional[str] = None,
    alt_text_style: str = "descriptive",
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.generate_alt_text(image_url, context, alt_text_style)
        return {
            "alt_text": result["alt_text"],
            "confidence_score": result["confidence_score"],
            "suggestions": result["suggestions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-generate-alt-text")
async def batch_generate_alt_text(
    images: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        results = service.batch_generate_alt_text(images)
        return {
            "processed_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-compliance")
async def check_accessibility_compliance(
    content: str,
    content_type: str,
    compliance_standards: List[str],
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.check_accessibility_compliance(content, content_type, compliance_standards)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fix-issues")
async def fix_accessibility_issues(
    content: str,
    issues: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.fix_accessibility_issues(content, issues)
        return {
            "fixed_content": result["fixed_content"],
            "fixed_issues": result["fixed_issues"],
            "remaining_issues": result["remaining_issues"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-forms")
async def optimize_form_accessibility(
    form_structure: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.optimize_form_accessibility(form_structure)
        return {
            "optimized_form": result["optimized_form"],
            "accessibility_improvements": result["accessibility_improvements"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-navigation")
async def optimize_navigation_accessibility(
    navigation_structure: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.optimize_navigation_accessibility(navigation_structure)
        return {
            "optimized_navigation": result["optimized_navigation"],
            "keyboard_navigation": result["keyboard_navigation"],
            "screen_reader_optimizations": result["screen_reader_optimizations"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-media")
async def optimize_media_accessibility(
    media_url: str,
    media_type: str,
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.optimize_media_accessibility(media_url, media_type)
        return {
            "optimized_media": result["optimized_media"],
            "captions": result["captions"],
            "transcripts": result["transcripts"],
            "descriptions": result["descriptions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-captions")
async def generate_media_captions(
    media_url: str,
    language: str = "en",
    caption_style: str = "standard",
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.generate_media_captions(media_url, language, caption_style)
        return {
            "captions": result["captions"],
            "timing": result["timing"],
            "format": result["format"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-transcripts")
async def generate_media_transcripts(
    media_url: str,
    language: str = "en",
    transcript_type: str = "full",
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.generate_media_transcripts(media_url, language, transcript_type)
        return {
            "transcript": result["transcript"],
            "timestamps": result["timestamps"],
            "speaker_identification": result["speaker_identification"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-color-contrast")
async def optimize_color_contrast(
    color_palette: List[str],
    target_contrast_ratio: float = 4.5,
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.optimize_color_contrast(color_palette, target_contrast_ratio)
        return {
            "optimized_colors": result["optimized_colors"],
            "contrast_ratios": result["contrast_ratios"],
            "recommendations": result["recommendations"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-typography")
async def optimize_typography_accessibility(
    typography_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.optimize_typography_accessibility(typography_config)
        return {
            "optimized_typography": result["optimized_typography"],
            "readability_score": result["readability_score"],
            "font_recommendations": result["font_recommendations"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-interactions")
async def optimize_interaction_accessibility(
    interaction_elements: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.optimize_interaction_accessibility(interaction_elements)
        return {
            "optimized_interactions": result["optimized_interactions"],
            "keyboard_shortcuts": result["keyboard_shortcuts"],
            "focus_management": result["focus_management"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-aria-labels")
async def generate_aria_labels(
    elements: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.generate_aria_labels(elements)
        return {
            "aria_labels": result["aria_labels"],
            "aria_descriptions": result["aria_descriptions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-semantic-structure")
async def optimize_semantic_structure(
    html_content: str,
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.optimize_semantic_structure(html_content)
        return {
            "optimized_html": result["optimized_html"],
            "semantic_improvements": result["semantic_improvements"],
            "heading_structure": result["heading_structure"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-screen-reader")
async def test_screen_reader_compatibility(
    content: str,
    screen_reader_type: str = "nvda",
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.test_screen_reader_compatibility(content, screen_reader_type)
        return {
            "compatibility_score": result["compatibility_score"],
            "issues": result["issues"],
            "recommendations": result["recommendations"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-keyboard-navigation")
async def test_keyboard_navigation(
    navigation_structure: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.test_keyboard_navigation(navigation_structure)
        return {
            "navigation_score": result["navigation_score"],
            "tab_order": result["tab_order"],
            "issues": result["issues"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-accessibility-report")
async def generate_accessibility_report(
    content_url: str,
    report_type: str = "comprehensive",
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.generate_accessibility_report(content_url, report_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/standards/{standard}/requirements")
async def get_accessibility_requirements(
    standard: str,
    level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        requirements = service.get_accessibility_requirements(standard, level)
        return {"requirements": requirements}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-wcag")
async def validate_wcag_compliance(
    content: str,
    wcag_level: str = "AA",
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.validate_wcag_compliance(content, wcag_level)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-mobile-accessibility")
async def optimize_mobile_accessibility(
    mobile_content: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.optimize_mobile_accessibility(mobile_content)
        return {
            "optimized_mobile": result["optimized_mobile"],
            "touch_targets": result["touch_targets"],
            "gesture_alternatives": result["gesture_alternatives"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-accessibility-guidelines")
async def generate_accessibility_guidelines(
    project_type: str,
    target_audience: List[str],
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.generate_accessibility_guidelines(project_type, target_audience)
        return {
            "guidelines": result["guidelines"],
            "checklist": result["checklist"],
            "best_practices": result["best_practices"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-email-accessibility")
async def optimize_email_accessibility(
    email_content: str,
    email_client: str = "outlook",
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.optimize_email_accessibility(email_content, email_client)
        return {
            "optimized_email": result["optimized_email"],
            "client_specific_optimizations": result["client_specific_optimizations"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-social-media")
async def optimize_social_media_accessibility(
    platform: str,
    content: str,
    media_urls: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.optimize_social_media_accessibility(platform, content, media_urls)
        return {
            "optimized_content": result["optimized_content"],
            "platform_specific_optimizations": result["platform_specific_optimizations"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/accessibility")
async def get_accessibility_analytics(
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        analytics = service.get_accessibility_analytics(timeframe)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-optimize")
async def batch_optimize_accessibility(
    content_batch: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        results = service.batch_optimize_accessibility(content_batch)
        return {
            "processed_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-pdf")
async def optimize_pdf_accessibility(
    pdf_url: str,
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.optimize_pdf_accessibility(pdf_url)
        return {
            "optimized_pdf": result["optimized_pdf"],
            "accessibility_improvements": result["accessibility_improvements"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-presentation")
async def optimize_presentation_accessibility(
    presentation_content: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = AccessibilityService(db)
    try:
        result = service.optimize_presentation_accessibility(presentation_content)
        return {
            "optimized_presentation": result["optimized_presentation"],
            "slide_descriptions": result["slide_descriptions"],
            "narrative_script": result["narrative_script"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
