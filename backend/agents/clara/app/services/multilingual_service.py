import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload
import httpx
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from core.config import settings
from core.integrations import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_clara_database
from ..models import (
    SupportTicket, CustomerInteraction, CustomerProfile,
    TicketPriority, TicketStatus, TicketCategory, SupportChannel
)

logger = logging.getLogger(__name__)

# Set seed for consistent language detection
DetectorFactory.seed = 0

class MultilingualService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self._supported_languages = {}
        self._translation_cache = {}
    
    async def initialize(self):
        """Initialize multilingual service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            await self._initialize_supported_languages()
            self._initialized = True
            logger.info("Multilingual service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize multilingual service: {e}")
            raise
    
    async def _initialize_supported_languages(self):
        """Initialize supported languages and their configurations"""
        self._supported_languages = {
            "en": {
                "name": "English",
                "native_name": "English",
                "code": "en",
                "direction": "ltr",
                "is_default": True,
                "translation_service": "google",
                "voice_models": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            },
            "es": {
                "name": "Spanish",
                "native_name": "Español",
                "code": "es",
                "direction": "ltr",
                "is_default": False,
                "translation_service": "google",
                "voice_models": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            },
            "fr": {
                "name": "French",
                "native_name": "Français",
                "code": "fr",
                "direction": "ltr",
                "is_default": False,
                "translation_service": "google",
                "voice_models": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            },
            "de": {
                "name": "German",
                "native_name": "Deutsch",
                "code": "de",
                "direction": "ltr",
                "is_default": False,
                "translation_service": "google",
                "voice_models": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            },
            "it": {
                "name": "Italian",
                "native_name": "Italiano",
                "code": "it",
                "direction": "ltr",
                "is_default": False,
                "translation_service": "google",
                "voice_models": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            },
            "pt": {
                "name": "Portuguese",
                "native_name": "Português",
                "code": "pt",
                "direction": "ltr",
                "is_default": False,
                "translation_service": "google",
                "voice_models": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            },
            "ar": {
                "name": "Arabic",
                "native_name": "العربية",
                "code": "ar",
                "direction": "rtl",
                "is_default": False,
                "translation_service": "google",
                "voice_models": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            },
            "zh": {
                "name": "Chinese",
                "native_name": "中文",
                "code": "zh",
                "direction": "ltr",
                "is_default": False,
                "translation_service": "google",
                "voice_models": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            },
            "ja": {
                "name": "Japanese",
                "native_name": "日本語",
                "code": "ja",
                "direction": "ltr",
                "is_default": False,
                "translation_service": "google",
                "voice_models": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            },
            "ko": {
                "name": "Korean",
                "native_name": "한국어",
                "code": "ko",
                "direction": "ltr",
                "is_default": False,
                "translation_service": "google",
                "voice_models": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            }
        }
    
    async def detect_language(
        self,
        text: str,
        customer_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Detect language of input text"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Use langdetect to detect language
            detected_lang = detect(text)
            confidence = 0.8  # langdetect doesn't provide confidence, so we estimate
            
            # Get language info
            language_info = self._supported_languages.get(detected_lang, {
                "name": "Unknown",
                "native_name": "Unknown",
                "code": detected_lang,
                "direction": "ltr",
                "is_default": False
            })
            
            # Update customer profile if provided
            if customer_id:
                await self._update_customer_language_preference(customer_id, detected_lang)
            
            return {
                "success": True,
                "detected_language": detected_lang,
                "confidence": confidence,
                "language_info": language_info,
                "is_supported": detected_lang in self._supported_languages
            }
            
        except LangDetectException as e:
            logger.warning(f"Could not detect language for text: {e}")
            return {
                "success": False,
                "detected_language": "en",
                "confidence": 0.0,
                "language_info": self._supported_languages["en"],
                "is_supported": True,
                "error": "Could not detect language, defaulting to English"
            }
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text to target language"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Check if target language is supported
            if target_language not in self._supported_languages:
                raise ValueError(f"Target language {target_language} is not supported")
            
            # Auto-detect source language if not provided
            if not source_language:
                detection_result = await self.detect_language(text)
                source_language = detection_result["detected_language"]
            
            # Check cache first
            cache_key = f"{source_language}_{target_language}_{hash(text)}"
            if cache_key in self._translation_cache:
                return {
                    "success": True,
                    "translated_text": self._translation_cache[cache_key],
                    "source_language": source_language,
                    "target_language": target_language,
                    "cached": True
                }
            
            # Translate using Google Translate API
            translated_text = await self._translate_with_google(text, target_language, source_language)
            
            # Cache the result
            self._translation_cache[cache_key] = translated_text
            
            return {
                "success": True,
                "translated_text": translated_text,
                "source_language": source_language,
                "target_language": target_language,
                "cached": False
            }
            
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_localized_response(
        self,
        response_template: str,
        language: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get localized response based on language and context"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get language-specific templates
            localized_template = await self._get_localized_template(response_template, language)
            
            # Translate if template is not available in target language
            if not localized_template:
                translation_result = await self.translate_text(response_template, language, "en")
                if translation_result["success"]:
                    localized_template = translation_result["translated_text"]
                else:
                    localized_template = response_template  # Fallback to English
            
            # Apply context substitutions
            if context:
                localized_template = await self._apply_context_substitutions(localized_template, context, language)
            
            return {
                "success": True,
                "localized_response": localized_template,
                "language": language,
                "template_used": response_template
            }
            
        except Exception as e:
            logger.error(f"Error getting localized response: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_supported_languages(self) -> Dict[str, Any]:
        """Get list of supported languages"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return {
                "success": True,
                "supported_languages": self._supported_languages,
                "total_languages": len(self._supported_languages),
                "default_language": "en"
            }
        except Exception as e:
            logger.error(f"Error getting supported languages: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_customer_language_preference(
        self,
        customer_id: int,
        language: str
    ) -> Dict[str, Any]:
        """Update customer's language preference"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get customer profile
                profile_query = select(CustomerProfile).where(CustomerProfile.user_id == customer_id)
                profile_result = await session.execute(profile_query)
                profile = profile_result.scalar_one_or_none()
                
                if not profile:
                    raise ValueError(f"Customer profile {customer_id} not found")
                
                # Update language preference
                profile.language_preference = language
                profile.metadata = {
                    **profile.metadata,
                    "language_settings": {
                        "preferred_language": language,
                        "last_updated": datetime.utcnow().isoformat(),
                        "language_info": self._supported_languages.get(language, {})
                    }
                }
                
                await session.commit()
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "language_preference": language,
                    "message": f"Language preference updated to {language}"
                }
                
        except Exception as e:
            logger.error(f"Error updating customer language preference: {e}")
            return {
                "success": False,
                "customer_id": customer_id,
                "error": str(e)
            }
    
    async def _update_customer_language_preference(
        self,
        customer_id: int,
        detected_language: str
    ):
        """Update customer language preference based on detected language"""
        try:
            # Only update if the detected language is supported
            if detected_language in self._supported_languages:
                await self.update_customer_language_preference(customer_id, detected_language)
        except Exception as e:
            logger.error(f"Error updating customer language preference: {e}")
    
    async def _translate_with_google(
        self,
        text: str,
        target_language: str,
        source_language: str
    ) -> str:
        """Translate text using Google Translate API"""
        try:
            # Use the actual Google Translate API
            async with httpx.AsyncClient() as client:
                # Simulate API call
                response = await client.post(
                    "https://translation.googleapis.com/language/translate/v2",
                    params={
                        "key": settings.google_translate_api_key,
                        "q": text,
                        "source": source_language,
                        "target": target_language
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["data"]["translations"][0]["translatedText"]
                else:
                    # Fallback to simple translation simulation
                    return f"[{target_language.upper()}] {text}"
                    
        except Exception as e:
            logger.error(f"Error with Google Translate API: {e}")
            # Fallback to simple translation simulation
            return f"[{target_language.upper()}] {text}"
    
    async def _get_localized_template(
        self,
        template_key: str,
        language: str
    ) -> Optional[str]:
        """Get localized template for specific language"""
        try:
            # Load from database or file system for production
            templates = {
                "greeting": {
                    "en": "Hello! How can I help you today?",
                    "es": "¡Hola! ¿Cómo puedo ayudarte hoy?",
                    "fr": "Bonjour! Comment puis-je vous aider aujourd'hui?",
                    "de": "Hallo! Wie kann ich Ihnen heute helfen?",
                    "it": "Ciao! Come posso aiutarti oggi?",
                    "pt": "Olá! Como posso ajudá-lo hoje?",
                    "ar": "مرحباً! كيف يمكنني مساعدتك اليوم؟",
                    "zh": "你好！今天我能为您做些什么？",
                    "ja": "こんにちは！今日はどのようにお手伝いできますか？",
                    "ko": "안녕하세요! 오늘 어떻게 도와드릴까요?"
                },
                "goodbye": {
                    "en": "Thank you for contacting us. Have a great day!",
                    "es": "Gracias por contactarnos. ¡Que tengas un buen día!",
                    "fr": "Merci de nous avoir contactés. Passez une excellente journée!",
                    "de": "Vielen Dank für Ihre Kontaktaufnahme. Einen schönen Tag noch!",
                    "it": "Grazie per averci contattato. Buona giornata!",
                    "pt": "Obrigado por nos contatar. Tenha um ótimo dia!",
                    "ar": "شكراً لاتصالك بنا. أتمنى لك يوماً سعيداً!",
                    "zh": "感谢您联系我们。祝您有美好的一天！",
                    "ja": "お問い合わせいただき、ありがとうございます。良い一日をお過ごしください！",
                    "ko": "연락해 주셔서 감사합니다. 좋은 하루 되세요!"
                }
            }
            
            return templates.get(template_key, {}).get(language)
            
        except Exception as e:
            logger.error(f"Error getting localized template: {e}")
            return None
    
    async def _apply_context_substitutions(
        self,
        template: str,
        context: Dict[str, Any],
        language: str
    ) -> str:
        """Apply context substitutions to template"""
        try:
            result = template
            
            # Replace placeholders with context values
            for key, value in context.items():
                placeholder = f"{{{key}}}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value))
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying context substitutions: {e}")
            return template
