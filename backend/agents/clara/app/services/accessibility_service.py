import logging
import json
from typing import Dict, Any, Optional, List
from backend.core.ai import get_ai_service_manager, AIServiceManager
from ..database import get_clara_database

logger = logging.getLogger(__name__)

class AccessibilityService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize accessibility service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            self._initialized = True
            logger.info("Accessibility service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize accessibility service: {e}")
            raise
    
    async def enhance_response_accessibility(
        self,
        response_text: str,
        accessibility_features: List[str] = None
    ) -> Dict[str, Any]:
        """Enhance response text for accessibility"""
        if not self._initialized:
            await self.initialize()
        
        try:
            if not accessibility_features:
                accessibility_features = ["screen_reader", "high_contrast", "plain_language"]
            
            enhanced_response = response_text
            
            # Add screen reader enhancements
            if "screen_reader" in accessibility_features:
                enhanced_response = await self._add_screen_reader_enhancements(enhanced_response)
            
            # Add high contrast indicators
            if "high_contrast" in accessibility_features:
                enhanced_response = await self._add_high_contrast_indicators(enhanced_response)
            
            # Simplify language for better comprehension
            if "plain_language" in accessibility_features:
                enhanced_response = await self._simplify_language(enhanced_response)
            
            return {
                "success": True,
                "original_response": response_text,
                "enhanced_response": enhanced_response,
                "accessibility_features_applied": accessibility_features,
                "accessibility_score": await self._calculate_accessibility_score(enhanced_response)
            }
            
        except Exception as e:
            logger.error(f"Failed to enhance response accessibility: {e}")
            return {"success": False, "error": str(e)}
    
    async def _add_screen_reader_enhancements(self, text: str) -> str:
        """Add screen reader friendly enhancements"""
        try:
            # Add semantic markers for screen readers
            enhanced_text = text
            
            # Mark headings
            enhanced_text = enhanced_text.replace("**", " [Heading] ")
            
            # Mark lists
            if "- " in enhanced_text or "* " in enhanced_text:
                enhanced_text = enhanced_text.replace("- ", "[List item] - ")
                enhanced_text = enhanced_text.replace("* ", "[List item] * ")
            
            # Mark important information
            enhanced_text = enhanced_text.replace("Important:", "[Important] ")
            enhanced_text = enhanced_text.replace("Note:", "[Note] ")
            enhanced_text = enhanced_text.replace("Warning:", "[Warning] ")
            
            # Mark actions
            enhanced_text = enhanced_text.replace("Click here", "[Action] Click here")
            enhanced_text = enhanced_text.replace("Submit", "[Action] Submit")
            enhanced_text = enhanced_text.replace("Continue", "[Action] Continue")
            
            return enhanced_text
            
        except Exception as e:
            logger.error(f"Failed to add screen reader enhancements: {e}")
            return text
    
    async def _add_high_contrast_indicators(self, text: str) -> str:
        """Add high contrast indicators"""
        try:
            enhanced_text = text
            
            # Add visual indicators for important elements
            enhanced_text = enhanced_text.replace("Error:", "⚠️ [Error] ")
            enhanced_text = enhanced_text.replace("Success:", "✅ [Success] ")
            enhanced_text = enhanced_text.replace("Info:", "ℹ️ [Info] ")
            
            return enhanced_text
            
        except Exception as e:
            logger.error(f"Failed to add high contrast indicators: {e}")
            return text
    
    async def _simplify_language(self, text: str) -> str:
        """Simplify language for better comprehension"""
        try:
            # Use NLP to simplify complex sentences
            simplification_prompt = f"""Simplify this text to make it easier to understand. Use:
- Shorter sentences
- Simple words
- Clear structure
- Active voice

Text: {text}

Simplified version:"""
            
            # Use AI Service Manager instead of NLPUtils
            from backend.core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that simplifies content for accessibility."},
                {"role": "user", "content": simplification_prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
            if ai_response.success:
                return ai_response.text_content.strip()
            else:
                return text
                
        except Exception as e:
            logger.error(f"Failed to simplify language: {e}")
            return text
    
    async def _calculate_accessibility_score(self, text: str) -> float:
        """Calculate accessibility score for text"""
        try:
            score = 100.0
            
            # Check sentence length
            sentences = text.split('.')
            long_sentences = [s for s in sentences if len(s.split()) > 20]
            if long_sentences:
                score -= len(long_sentences) * 5
            
            # Check for complex words
            complex_words = ["nevertheless", "consequently", "furthermore", "notwithstanding"]
            found_complex = sum(1 for word in complex_words if word.lower() in text.lower())
            score -= found_complex * 3
            
            # Check for accessibility markers
            accessibility_markers = ["[Heading]", "[List item]", "[Important]", "[Action]"]
            found_markers = sum(1 for marker in accessibility_markers if marker in text)
            score += found_markers * 2
            
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.error(f"Failed to calculate accessibility score: {e}")
            return 70.0  # Default score
