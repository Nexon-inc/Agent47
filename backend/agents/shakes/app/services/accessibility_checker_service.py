from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.utils.database_utils import DatabaseUtils
from backend.core.utils.cache_utils import CacheUtils
from backend.core.utils.event_bus_utils import EventBusUtils
from backend.core.utils.integration_utils import IntegrationUtils
from backend.core.config import settings
from ..database import get_shakes_database

class AccessibilityCheckerService:
    """Service for checking content accessibility and WCAG compliance"""
    
    def __init__(self):
        self.nlp_utils = NLPUtils()
        self.db_utils = DatabaseUtils()
        self.cache_utils = CacheUtils()
        self.event_bus = EventBusUtils()
        self.integration_utils = IntegrationUtils()
        self.model_config = {"model": "grok-llm", "temperature": 0.3, "max_tokens": 1500}
        
    async def initialize(self):
        """Initialize service dependencies"""
        await self.nlp_utils.initialize()
        await self.db_utils.initialize()
        await self.cache_utils.initialize()
        await self.event_bus.initialize()
        await self.integration_utils.initialize()
    
    async def check_accessibility(self, content_piece_id: int, 
                                accessibility_standards: List[str],
                                check_categories: List[str]) -> Dict[str, Any]:
        """Check content accessibility compliance"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                content_piece = await session.get("content_pieces", content_piece_id)
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                accessibility_checks = await self._perform_accessibility_checks(
                    content_piece, accessibility_standards, check_categories
                )
                
                compliance_report = await self._generate_compliance_report(
                    accessibility_checks, accessibility_standards
                )
                
                improvement_recommendations = await self._generate_improvement_recommendations(
                    accessibility_checks, compliance_report
                )
                
                accessibility_score = await self._calculate_accessibility_score(
                    compliance_report
                )
                
                await self._save_accessibility_report(
                    content_piece_id, accessibility_checks, compliance_report, session
                )
                
                await self.event_bus.publish_event("accessibility_checked", {
                    "content_piece_id": content_piece_id,
                    "accessibility_score": accessibility_score,
                    "compliance_level": compliance_report.get("compliance_level")
                })
                
                return {
                    "success": True,
                    "accessibility_checks": accessibility_checks,
                    "compliance_report": compliance_report,
                    "accessibility_score": accessibility_score,
                    "improvement_recommendations": improvement_recommendations,
                    "wcag_compliance": await self._assess_wcag_compliance(accessibility_checks)
                }
                
        except Exception as e:
            return {"success": False, "error": f"Accessibility check failed: {str(e)}"}
    
    async def fix_accessibility_issues(self, content_piece_id: int, 
                                     issue_categories: List[str],
                                     fix_priorities: List[str]) -> Dict[str, Any]:
        """Fix accessibility issues in content"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                content_piece = await session.get("content_pieces", content_piece_id)
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                accessibility_issues = await self._identify_accessibility_issues(
                    content_piece, issue_categories
                )
                
                fixed_content = await self._apply_accessibility_fixes(
                    content_piece, accessibility_issues, fix_priorities
                )
                
                fix_verification = await self._verify_accessibility_fixes(
                    fixed_content, accessibility_issues
                )
                
                updated_content = await self._update_content_piece(
                    content_piece_id, fixed_content, session
                )
                
                await self.event_bus.publish_event("accessibility_issues_fixed", {
                    "content_piece_id": content_piece_id,
                    "issues_fixed": len(accessibility_issues),
                    "fix_verification": fix_verification
                })
                
                return {
                    "success": True,
                    "fixed_content": updated_content,
                    "accessibility_issues": accessibility_issues,
                    "fix_verification": fix_verification,
                    "improvement_summary": await self._generate_improvement_summary(
                        content_piece, updated_content
                    )
                }
                
        except Exception as e:
            return {"success": False, "error": f"Accessibility fix failed: {str(e)}"}
    
    async def generate_alt_text(self, content_piece_id: int, 
                              image_elements: List[Dict[str, Any]],
                              alt_text_style: str) -> Dict[str, Any]:
        """Generate alt text for images and visual elements"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                content_piece = await session.get("content_pieces", content_piece_id)
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                alt_text_generations = []
                for image_element in image_elements:
                    alt_text = await self._generate_alt_text_for_image(
                        image_element, content_piece, alt_text_style
                    )
                    
                    alt_text_generations.append({
                        "image_id": image_element.get("id"),
                        "alt_text": alt_text,
                        "context": image_element.get("context"),
                        "accessibility_score": await self._assess_alt_text_quality(alt_text)
                    })
                
                await self._save_alt_text_generations(
                    content_piece_id, alt_text_generations, session
                )
                
                await self.event_bus.publish_event("alt_text_generated", {
                    "content_piece_id": content_piece_id,
                    "alt_text_count": len(alt_text_generations)
                })
                
                return {
                    "success": True,
                    "alt_text_generations": alt_text_generations,
                    "accessibility_improvements": await self._calculate_accessibility_improvements(
                        alt_text_generations
                    ),
                    "seo_benefits": await self._assess_seo_benefits(alt_text_generations)
                }
                
        except Exception as e:
            return {"success": False, "error": f"Alt text generation failed: {str(e)}"}
    
    async def validate_color_contrast(self, content_piece_id: int,
                                    color_elements: List[Dict[str, Any]],
                                    contrast_standards: List[str]) -> Dict[str, Any]:
        """Validate color contrast for accessibility"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                content_piece = await session.get("content_pieces", content_piece_id)
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                contrast_analysis = []
                for color_element in color_elements:
                    contrast_ratio = await self._calculate_contrast_ratio(
                        color_element.get("foreground_color"),
                        color_element.get("background_color")
                    )
                    
                    compliance_status = await self._check_contrast_compliance(
                        contrast_ratio, contrast_standards
                    )
                    
                    contrast_analysis.append({
                        "element_id": color_element.get("id"),
                        "foreground_color": color_element.get("foreground_color"),
                        "background_color": color_element.get("background_color"),
                        "contrast_ratio": contrast_ratio,
                        "compliance_status": compliance_status,
                        "recommendations": await self._generate_contrast_recommendations(
                            contrast_ratio, compliance_status
                        )
                    })
                
                overall_compliance = await self._assess_overall_contrast_compliance(
                    contrast_analysis
                )
                
                await self.event_bus.publish_event("color_contrast_validated", {
                    "content_piece_id": content_piece_id,
                    "overall_compliance": overall_compliance,
                    "elements_checked": len(contrast_analysis)
                })
                
                return {
                    "success": True,
                    "contrast_analysis": contrast_analysis,
                    "overall_compliance": overall_compliance,
                    "improvement_suggestions": await self._generate_contrast_improvements(
                        contrast_analysis
                    ),
                    "wcag_compliance": await self._assess_wcag_contrast_compliance(
                        contrast_analysis
                    )
                }
                
        except Exception as e:
            return {"success": False, "error": f"Color contrast validation failed: {str(e)}"}
    
    async def _perform_accessibility_checks(self, content_piece: Dict[str, Any],
                                          accessibility_standards: List[str],
                                          check_categories: List[str]) -> Dict[str, Any]:
        """Perform comprehensive accessibility checks"""
        checks = {}
        
        if "text_accessibility" in check_categories:
            checks["text_accessibility"] = await self._check_text_accessibility(content_piece)
        
        if "visual_accessibility" in check_categories:
            checks["visual_accessibility"] = await self._check_visual_accessibility(content_piece)
        
        if "navigation_accessibility" in check_categories:
            checks["navigation_accessibility"] = await self._check_navigation_accessibility(content_piece)
        
        if "interactive_accessibility" in check_categories:
            checks["interactive_accessibility"] = await self._check_interactive_accessibility(content_piece)
        
        if "media_accessibility" in check_categories:
            checks["media_accessibility"] = await self._check_media_accessibility(content_piece)
        
        return checks
    
    async def _check_text_accessibility(self, content_piece: Dict[str, Any]) -> Dict[str, Any]:
        """Check text accessibility features"""
        return {
            "readability_score": await self._assess_readability(content_piece),
            "font_size_compliance": await self._check_font_size_compliance(content_piece),
            "line_spacing_compliance": await self._check_line_spacing_compliance(content_piece),
            "text_contrast_compliance": await self._check_text_contrast_compliance(content_piece),
            "language_identification": await self._check_language_identification(content_piece)
        }
    
    async def _check_visual_accessibility(self, content_piece: Dict[str, Any]) -> Dict[str, Any]:
        """Check visual accessibility features"""
        return {
            "alt_text_presence": await self._check_alt_text_presence(content_piece),
            "alt_text_quality": await self._check_alt_text_quality(content_piece),
            "color_dependency": await self._check_color_dependency(content_piece),
            "visual_hierarchy": await self._check_visual_hierarchy(content_piece),
            "focus_indicators": await self._check_focus_indicators(content_piece)
        }
    
    async def _check_navigation_accessibility(self, content_piece: Dict[str, Any]) -> Dict[str, Any]:
        """Check navigation accessibility features"""
        return {
            "heading_structure": await self._check_heading_structure(content_piece),
            "link_descriptions": await self._check_link_descriptions(content_piece),
            "keyboard_navigation": await self._check_keyboard_navigation(content_piece),
            "skip_links": await self._check_skip_links(content_piece),
            "landmark_roles": await self._check_landmark_roles(content_piece)
        }
    
    async def _check_interactive_accessibility(self, content_piece: Dict[str, Any]) -> Dict[str, Any]:
        """Check interactive accessibility features"""
        return {
            "form_labels": await self._check_form_labels(content_piece),
            "button_descriptions": await self._check_button_descriptions(content_piece),
            "error_handling": await self._check_error_handling(content_piece),
            "focus_management": await self._check_focus_management(content_piece),
            "interactive_feedback": await self._check_interactive_feedback(content_piece)
        }
    
    async def _check_media_accessibility(self, content_piece: Dict[str, Any]) -> Dict[str, Any]:
        """Check media accessibility features"""
        return {
            "video_captions": await self._check_video_captions(content_piece),
            "audio_transcripts": await self._check_audio_transcripts(content_piece),
            "media_controls": await self._check_media_controls(content_piece),
            "autoplay_compliance": await self._check_autoplay_compliance(content_piece),
            "media_descriptions": await self._check_media_descriptions(content_piece)
        }
    
    async def _generate_compliance_report(self, accessibility_checks: Dict[str, Any],
                                        accessibility_standards: List[str]) -> Dict[str, Any]:
        """Generate accessibility compliance report"""
        return {
            "compliance_level": await self._determine_compliance_level(accessibility_checks),
            "wcag_aa_compliance": await self._assess_wcag_aa_compliance(accessibility_checks),
            "wcag_aaa_compliance": await self._assess_wcag_aaa_compliance(accessibility_checks),
            "section_508_compliance": await self._assess_section_508_compliance(accessibility_checks),
            "compliance_details": await self._generate_compliance_details(accessibility_checks),
            "critical_issues": await self._identify_critical_issues(accessibility_checks),
            "minor_issues": await self._identify_minor_issues(accessibility_checks)
        }
    
    async def _calculate_accessibility_score(self, compliance_report: Dict[str, Any]) -> float:
        """Calculate overall accessibility score"""
        base_score = 100.0
        
        critical_issues = compliance_report.get("critical_issues", [])
        minor_issues = compliance_report.get("minor_issues", [])
        
        critical_penalty = len(critical_issues) * 20
        minor_penalty = len(minor_issues) * 5
        
        final_score = max(0, base_score - critical_penalty - minor_penalty)
        
        return round(final_score, 2)
    
    async def _generate_improvement_recommendations(self, accessibility_checks: Dict[str, Any],
                                                  compliance_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate improvement recommendations"""
        recommendations = []
        
        critical_issues = compliance_report.get("critical_issues", [])
        for issue in critical_issues:
            recommendations.append({
                "priority": "critical",
                "issue": issue,
                "recommendation": await self._get_issue_recommendation(issue),
                "impact": "high"
            })
        
        minor_issues = compliance_report.get("minor_issues", [])
        for issue in minor_issues:
            recommendations.append({
                "priority": "minor",
                "issue": issue,
                "recommendation": await self._get_issue_recommendation(issue),
                "impact": "medium"
            })
        
        return recommendations
