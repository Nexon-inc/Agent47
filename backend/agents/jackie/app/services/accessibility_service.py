import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from backend.core.utils.nlp_utils import NLPProcessor
from ..models import AccessibilityContent, AccessibilityAnalysis, AccessibilityReport

class AccessibilityService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        
    def optimize_content_accessibility(self, content_type: str, content: str, 
                                    target_audience: List[str], accessibility_level: str,
                                    context: Dict[str, Any]) -> Dict[str, Any]:
        optimization_id = str(uuid.uuid4())
        
        prompt = f"""
        Content Type: {content_type}
        Content: {content}
        Target Audience: {target_audience}
        Accessibility Level: {accessibility_level}
        Context: {context}
        
        Optimize this content for accessibility, ensuring it meets {accessibility_level} standards.
        Generate alt text for images, improve readability, and ensure screen reader compatibility.
        """
        
        optimization_result = self.nlp_processor.optimize_accessibility(prompt)
        
        accessibility_score = self._calculate_accessibility_score(optimization_result)
        
        content_record = AccessibilityContent(
            id=optimization_id, content_type=content_type, original_content=content,
            optimized_content=optimization_result.get("optimized_content", content),
            alt_text=optimization_result.get("alt_text"), accessibility_score=accessibility_score,
            compliance_level=accessibility_level, recommendations=json.dumps(optimization_result.get("recommendations", [])),
            created_at=datetime.utcnow()
        )
        self.db.add(content_record)
        self.db.commit()
        
        return {
            "id": optimization_id, "original_content": content,
            "optimized_content": optimization_result.get("optimized_content", content),
            "alt_text": optimization_result.get("alt_text"), "accessibility_score": accessibility_score,
            "compliance_level": accessibility_level, "recommendations": optimization_result.get("recommendations", []),
            "created_at": content_record.created_at.isoformat()
        }
    
    def generate_alt_text(self, image_url: str, context: Optional[str] = None, 
                         alt_text_style: str = "descriptive") -> Dict[str, Any]:
        prompt = f"""
        Image URL: {image_url}
        Context: {context or "No specific context provided"}
        Alt Text Style: {alt_text_style}
        
        Generate appropriate alt text for this image that is {alt_text_style} and accessible.
        """
        
        alt_text_result = self.nlp_processor.generate_alt_text(prompt)
        
        confidence_score = self._calculate_alt_text_confidence(alt_text_result.get("alt_text", ""))
        
        return {
            "alt_text": alt_text_result.get("alt_text", ""),
            "confidence_score": confidence_score,
            "suggestions": alt_text_result.get("suggestions", [])
        }
    
    def batch_generate_alt_text(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        
        for image in images:
            try:
                result = self.generate_alt_text(
                    image.get("url", ""),
                    image.get("context"),
                    image.get("style", "descriptive")
                )
                results.append({
                    "image_url": image.get("url", ""),
                    "result": result
                })
            except Exception as e:
                results.append({
                    "image_url": image.get("url", ""),
                    "error": str(e)
                })
        
        return results
    
    def check_accessibility_compliance(self, content: str, content_type: str, 
                                     compliance_standards: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Content: {content}
        Content Type: {content_type}
        Compliance Standards: {compliance_standards}
        
        Check this content against the specified accessibility compliance standards.
        """
        
        compliance_result = self.nlp_processor.check_accessibility_compliance(prompt)
        
        return {
            "content": content, "content_type": content_type,
            "compliance_standards": compliance_standards,
            "compliance_result": compliance_result
        }
    
    def fix_accessibility_issues(self, content: str, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = f"""
        Original Content: {content}
        Accessibility Issues: {issues}
        
        Fix the identified accessibility issues in the content.
        """
        
        fix_result = self.nlp_processor.fix_accessibility_issues(prompt)
        
        return {
            "fixed_content": fix_result.get("fixed_content", content),
            "fixed_issues": fix_result.get("fixed_issues", []),
            "remaining_issues": fix_result.get("remaining_issues", [])
        }
    
    def optimize_form_accessibility(self, form_structure: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Form Structure: {form_structure}
        
        Optimize this form structure for accessibility, including proper labels, ARIA attributes, and keyboard navigation.
        """
        
        optimization_result = self.nlp_processor.optimize_form_accessibility(prompt)
        
        return {
            "optimized_form": optimization_result.get("optimized_form", form_structure),
            "accessibility_improvements": optimization_result.get("improvements", [])
        }
    
    def optimize_navigation_accessibility(self, navigation_structure: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Navigation Structure: {navigation_structure}
        
        Optimize this navigation structure for accessibility, ensuring proper keyboard navigation and screen reader compatibility.
        """
        
        optimization_result = self.nlp_processor.optimize_navigation_accessibility(prompt)
        
        return {
            "optimized_navigation": optimization_result.get("optimized_navigation", navigation_structure),
            "keyboard_navigation": optimization_result.get("keyboard_navigation", {}),
            "screen_reader_optimizations": optimization_result.get("screen_reader_optimizations", [])
        }
    
    def optimize_media_accessibility(self, media_url: str, media_type: str) -> Dict[str, Any]:
        prompt = f"""
        Media URL: {media_url}
        Media Type: {media_type}
        
        Optimize this media content for accessibility, including captions, transcripts, and descriptions.
        """
        
        optimization_result = self.nlp_processor.optimize_media_accessibility(prompt)
        
        return {
            "optimized_media": optimization_result.get("optimized_media", {}),
            "captions": optimization_result.get("captions", ""),
            "transcripts": optimization_result.get("transcripts", ""),
            "descriptions": optimization_result.get("descriptions", "")
        }
    
    def generate_media_captions(self, media_url: str, language: str = "en", 
                              caption_style: str = "standard") -> Dict[str, Any]:
        prompt = f"""
        Media URL: {media_url}
        Language: {language}
        Caption Style: {caption_style}
        
        Generate captions for this media content in the specified language and style.
        """
        
        caption_result = self.nlp_processor.generate_media_captions(prompt)
        
        return {
            "captions": caption_result.get("captions", ""),
            "timing": caption_result.get("timing", []),
            "format": caption_result.get("format", "srt")
        }
    
    def generate_media_transcripts(self, media_url: str, language: str = "en", 
                                 transcript_type: str = "full") -> Dict[str, Any]:
        prompt = f"""
        Media URL: {media_url}
        Language: {language}
        Transcript Type: {transcript_type}
        
        Generate a {transcript_type} transcript for this media content.
        """
        
        transcript_result = self.nlp_processor.generate_media_transcripts(prompt)
        
        return {
            "transcript": transcript_result.get("transcript", ""),
            "timestamps": transcript_result.get("timestamps", []),
            "speaker_identification": transcript_result.get("speaker_identification", {})
        }
    
    def optimize_color_contrast(self, color_palette: List[str], 
                              target_contrast_ratio: float = 4.5) -> Dict[str, Any]:
        prompt = f"""
        Color Palette: {color_palette}
        Target Contrast Ratio: {target_contrast_ratio}
        
        Optimize these colors for better contrast ratios while maintaining visual appeal.
        """
        
        contrast_result = self.nlp_processor.optimize_color_contrast(prompt)
        
        return {
            "optimized_colors": contrast_result.get("optimized_colors", color_palette),
            "contrast_ratios": contrast_result.get("contrast_ratios", {}),
            "recommendations": contrast_result.get("recommendations", [])
        }
    
    def optimize_typography_accessibility(self, typography_config: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Typography Configuration: {typography_config}
        
        Optimize this typography configuration for accessibility and readability.
        """
        
        typography_result = self.nlp_processor.optimize_typography_accessibility(prompt)
        
        return {
            "optimized_typography": typography_result.get("optimized_typography", typography_config),
            "readability_score": typography_result.get("readability_score", 0.0),
            "font_recommendations": typography_result.get("font_recommendations", [])
        }
    
    def optimize_interaction_accessibility(self, interaction_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = f"""
        Interaction Elements: {interaction_elements}
        
        Optimize these interaction elements for accessibility, including keyboard navigation and screen reader support.
        """
        
        interaction_result = self.nlp_processor.optimize_interaction_accessibility(prompt)
        
        return {
            "optimized_interactions": interaction_result.get("optimized_interactions", interaction_elements),
            "keyboard_shortcuts": interaction_result.get("keyboard_shortcuts", {}),
            "focus_management": interaction_result.get("focus_management", {})
        }
    
    def generate_aria_labels(self, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = f"""
        Elements: {elements}
        
        Generate appropriate ARIA labels and descriptions for these elements.
        """
        
        aria_result = self.nlp_processor.generate_aria_labels(prompt)
        
        return {
            "aria_labels": aria_result.get("aria_labels", {}),
            "aria_descriptions": aria_result.get("aria_descriptions", {})
        }
    
    def optimize_semantic_structure(self, html_content: str) -> Dict[str, Any]:
        prompt = f"""
        HTML Content: {html_content}
        
        Optimize the semantic structure of this HTML content for better accessibility.
        """
        
        semantic_result = self.nlp_processor.optimize_semantic_structure(prompt)
        
        return {
            "optimized_html": semantic_result.get("optimized_html", html_content),
            "semantic_improvements": semantic_result.get("semantic_improvements", []),
            "heading_structure": semantic_result.get("heading_structure", {})
        }
    
    def test_screen_reader_compatibility(self, content: str, screen_reader_type: str = "nvda") -> Dict[str, Any]:
        prompt = f"""
        Content: {content}
        Screen Reader Type: {screen_reader_type}
        
        Test this content for compatibility with {screen_reader_type} screen reader.
        """
        
        compatibility_result = self.nlp_processor.test_screen_reader_compatibility(prompt)
        
        return {
            "compatibility_score": compatibility_result.get("compatibility_score", 0.0),
            "issues": compatibility_result.get("issues", []),
            "recommendations": compatibility_result.get("recommendations", [])
        }
    
    def test_keyboard_navigation(self, navigation_structure: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Navigation Structure: {navigation_structure}
        
        Test the keyboard navigation for this navigation structure.
        """
        
        navigation_result = self.nlp_processor.test_keyboard_navigation(prompt)
        
        return {
            "navigation_score": navigation_result.get("navigation_score", 0.0),
            "tab_order": navigation_result.get("tab_order", []),
            "issues": navigation_result.get("issues", [])
        }
    
    def generate_accessibility_report(self, content_url: str, report_type: str = "comprehensive") -> Dict[str, Any]:
        report_id = str(uuid.uuid4())
        
        prompt = f"""
        Content URL: {content_url}
        Report Type: {report_type}
        
        Generate a {report_type} accessibility report for this content.
        """
        
        report_result = self.nlp_processor.generate_accessibility_report(prompt)
        
        report_record = AccessibilityReport(
            id=report_id, content_url=content_url, report_type=report_type,
            report_data=json.dumps(report_result), created_at=datetime.utcnow()
        )
        self.db.add(report_record)
        self.db.commit()
        
        return {
            "report_id": report_id, "content_url": content_url, "report_type": report_type,
            "report_data": report_result, "created_at": report_record.created_at.isoformat()
        }
    
    def get_accessibility_requirements(self, standard: str, level: Optional[str] = None) -> List[Dict[str, Any]]:
        prompt = f"""
        Standard: {standard}
        Level: {level or "all levels"}
        
        Get the accessibility requirements for this standard and level.
        """
        
        requirements = self.nlp_processor.get_accessibility_requirements(prompt)
        
        return requirements
    
    def validate_wcag_compliance(self, content: str, wcag_level: str = "AA") -> Dict[str, Any]:
        prompt = f"""
        Content: {content}
        WCAG Level: {wcag_level}
        
        Validate this content against WCAG {wcag_level} compliance standards.
        """
        
        validation_result = self.nlp_processor.validate_wcag_compliance(prompt)
        
        return validation_result
    
    def optimize_mobile_accessibility(self, mobile_content: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Mobile Content: {mobile_content}
        
        Optimize this mobile content for accessibility, including touch targets and gesture alternatives.
        """
        
        mobile_result = self.nlp_processor.optimize_mobile_accessibility(prompt)
        
        return {
            "optimized_mobile": mobile_result.get("optimized_mobile", mobile_content),
            "touch_targets": mobile_result.get("touch_targets", {}),
            "gesture_alternatives": mobile_result.get("gesture_alternatives", [])
        }
    
    def generate_accessibility_guidelines(self, project_type: str, target_audience: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Project Type: {project_type}
        Target Audience: {target_audience}
        
        Generate accessibility guidelines for this project type and target audience.
        """
        
        guidelines_result = self.nlp_processor.generate_accessibility_guidelines(prompt)
        
        return {
            "guidelines": guidelines_result.get("guidelines", []),
            "checklist": guidelines_result.get("checklist", []),
            "best_practices": guidelines_result.get("best_practices", [])
        }
    
    def optimize_email_accessibility(self, email_content: str, email_client: str = "outlook") -> Dict[str, Any]:
        prompt = f"""
        Email Content: {email_content}
        Email Client: {email_client}
        
        Optimize this email content for accessibility in {email_client}.
        """
        
        email_result = self.nlp_processor.optimize_email_accessibility(prompt)
        
        return {
            "optimized_email": email_result.get("optimized_email", email_content),
            "client_specific_optimizations": email_result.get("client_specific_optimizations", [])
        }
    
    def optimize_social_media_accessibility(self, platform: str, content: str, 
                                          media_urls: Optional[List[str]] = None) -> Dict[str, Any]:
        prompt = f"""
        Platform: {platform}
        Content: {content}
        Media URLs: {media_urls or []}
        
        Optimize this social media content for accessibility on {platform}.
        """
        
        social_result = self.nlp_processor.optimize_social_media_accessibility(prompt)
        
        return {
            "optimized_content": social_result.get("optimized_content", content),
            "platform_specific_optimizations": social_result.get("platform_specific_optimizations", [])
        }
    
    def get_accessibility_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        total_optimizations = self.db.query(AccessibilityContent).filter(
            AccessibilityContent.created_at >= cutoff_date
        ).count()
        
        avg_score = self.db.query(AccessibilityContent).filter(
            AccessibilityContent.created_at >= cutoff_date
        ).with_entities(AccessibilityContent.accessibility_score).all()
        
        avg_score_value = sum(score[0] for score in avg_score) / len(avg_score) if avg_score else 0.0
        
        return {
            "timeframe": timeframe, "total_optimizations": total_optimizations,
            "average_accessibility_score": avg_score_value,
            "optimizations_with_scores": len(avg_score)
        }
    
    def batch_optimize_accessibility(self, content_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        
        for content_item in content_batch:
            try:
                result = self.optimize_content_accessibility(
                    content_item.get("content_type", "general"),
                    content_item.get("content", ""),
                    content_item.get("target_audience", []),
                    content_item.get("accessibility_level", "WCAG_AA"),
                    content_item.get("context", {})
                )
                results.append({
                    "content_id": content_item.get("id"),
                    "result": result
                })
            except Exception as e:
                results.append({
                    "content_id": content_item.get("id"),
                    "error": str(e)
                })
        
        return results
    
    def optimize_pdf_accessibility(self, pdf_url: str) -> Dict[str, Any]:
        prompt = f"""
        PDF URL: {pdf_url}
        
        Optimize this PDF for accessibility, including proper tagging and structure.
        """
        
        pdf_result = self.nlp_processor.optimize_pdf_accessibility(prompt)
        
        return {
            "optimized_pdf": pdf_result.get("optimized_pdf", {}),
            "accessibility_improvements": pdf_result.get("accessibility_improvements", [])
        }
    
    def optimize_presentation_accessibility(self, presentation_content: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Presentation Content: {presentation_content}
        
        Optimize this presentation for accessibility, including slide descriptions and narrative scripts.
        """
        
        presentation_result = self.nlp_processor.optimize_presentation_accessibility(prompt)
        
        return {
            "optimized_presentation": presentation_result.get("optimized_presentation", presentation_content),
            "slide_descriptions": presentation_result.get("slide_descriptions", []),
            "narrative_script": presentation_result.get("narrative_script", "")
        }
    
    def _calculate_accessibility_score(self, optimization_result: Dict[str, Any]) -> float:
        score = 0.0
        total_criteria = 0
        
        criteria = [
            "alt_text_present", "semantic_structure", "keyboard_navigation",
            "color_contrast", "readability", "screen_reader_compatibility"
        ]
        
        for criterion in criteria:
            if criterion in optimization_result:
                score += optimization_result[criterion]
                total_criteria += 1
        
        return score / total_criteria if total_criteria > 0 else 0.0
    
    def _calculate_alt_text_confidence(self, alt_text: str) -> float:
        if not alt_text:
            return 0.0
        
        confidence_factors = [
            len(alt_text) > 10,  # Minimum length
            len(alt_text) < 200,  # Maximum length
            any(word in alt_text.lower() for word in ["image", "photo", "picture", "graphic"]),
            alt_text.strip() != ""
        ]
        
        return sum(confidence_factors) / len(confidence_factors)
