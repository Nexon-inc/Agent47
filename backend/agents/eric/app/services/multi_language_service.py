from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging
from pydantic import BaseModel

from core.cache.redis_manager import RedisManager
from core.messaging.kafka_manager import KafkaManager
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
from core.ai import get_ai_service_manager
from ..database import get_eric_database
from ..models import (
    EricLead, EricLeadInteraction, EricDeal, EricSalesActivity, EricObjection,
    EricSalesCampaign, EricEmailSequence, EricSalesTeam, EricSalesRep, EricSalesAnalytics
)

logger = logging.getLogger(__name__)

class LanguageConfig(BaseModel):
    language_code: str
    language_name: str
    region: str
    currency: str
    timezone: str
    date_format: str
    number_format: str
    cultural_notes: List[str] = []
    business_etiquette: Dict[str, str] = {}
    is_active: bool = True

class TranslationRequest(BaseModel):
    text: str
    source_language: str
    target_language: str
    context: str = "sales"
    tone: str = "professional"
    cultural_adaptation: bool = True

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence_score: float
    cultural_adaptations: List[str] = []
    alternative_translations: List[str] = []
    created_at: datetime

class LocalizedContent(BaseModel):
    content_id: str
    language_code: str
    content_type: str  # email, pitch, proposal, etc.
    title: str
    body: str
    subject_line: str = ""
    call_to_action: str = ""
    cultural_notes: List[str] = []
    created_at: datetime
    updated_at: datetime

class CulturalInsight(BaseModel):
    country: str
    language: str
    business_culture: Dict[str, str]
    communication_style: Dict[str, str]
    negotiation_tactics: List[str]
    common_greetings: List[str]
    taboos: List[str]
    success_indicators: List[str]

class MultiLanguageService:
    def __init__(self):
        self.ai_service_manager = None
        self.redis_manager = RedisManager()
        self.kafka_manager = KafkaManager()
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self._initialized = False
        # Using AI Service Manager for translation and language detection
    
    async def initialize(self):
        """Initialize multi language service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.redis_manager.initialize()
            await self.kafka_manager.initialize()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            self._initialized = True
            logger.info("Multi language service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize multi language service: {e}")
            raise
        
        # Supported languages and configurations
        self.supported_languages = {
            "en": {
                "language_name": "English",
                "region": "Global",
                "currency": "USD",
                "timezone": "UTC",
                "date_format": "MM/DD/YYYY",
                "number_format": "1,234.56",
                "cultural_notes": ["Direct communication preferred", "Time is money"],
                "business_etiquette": {
                    "greeting": "Handshake",
                    "meeting_style": "Direct and efficient",
                    "negotiation": "Win-win approach"
                }
            },
            "es": {
                "language_name": "Spanish",
                "region": "Latin America",
                "currency": "USD",
                "timezone": "UTC-5",
                "date_format": "DD/MM/YYYY",
                "number_format": "1.234,56",
                "cultural_notes": ["Personal relationships important", "Formal titles used"],
                "business_etiquette": {
                    "greeting": "Handshake and cheek kiss",
                    "meeting_style": "Relationship building first",
                    "negotiation": "Personal connection matters"
                }
            },
            "fr": {
                "language_name": "French",
                "region": "Europe",
                "currency": "EUR",
                "timezone": "UTC+1",
                "date_format": "DD/MM/YYYY",
                "number_format": "1 234,56",
                "cultural_notes": ["Formal communication", "Respect for hierarchy"],
                "business_etiquette": {
                    "greeting": "Handshake",
                    "meeting_style": "Formal and structured",
                    "negotiation": "Logical and analytical"
                }
            },
            "de": {
                "language_name": "German",
                "region": "Europe",
                "currency": "EUR",
                "timezone": "UTC+1",
                "date_format": "DD.MM.YYYY",
                "number_format": "1.234,56",
                "cultural_notes": ["Precise and detailed", "Punctuality important"],
                "business_etiquette": {
                    "greeting": "Firm handshake",
                    "meeting_style": "Direct and efficient",
                    "negotiation": "Fact-based and thorough"
                }
            },
            "pt": {
                "language_name": "Portuguese",
                "region": "Brazil",
                "currency": "BRL",
                "timezone": "UTC-3",
                "date_format": "DD/MM/YYYY",
                "number_format": "1.234,56",
                "cultural_notes": ["Warm and friendly", "Personal relationships key"],
                "business_etiquette": {
                    "greeting": "Handshake and embrace",
                    "meeting_style": "Casual and friendly",
                    "negotiation": "Relationship-focused"
                }
            },
            "zh": {
                "language_name": "Chinese",
                "region": "Asia",
                "currency": "CNY",
                "timezone": "UTC+8",
                "date_format": "YYYY-MM-DD",
                "number_format": "1,234.56",
                "cultural_notes": ["Respect for hierarchy", "Indirect communication"],
                "business_etiquette": {
                    "greeting": "Bow or handshake",
                    "meeting_style": "Formal and respectful",
                    "negotiation": "Long-term relationship building"
                }
            },
            "ja": {
                "language_name": "Japanese",
                "region": "Asia",
                "currency": "JPY",
                "timezone": "UTC+9",
                "date_format": "YYYY-MM-DD",
                "number_format": "1,234",
                "cultural_notes": ["Group harmony important", "Indirect communication"],
                "business_etiquette": {
                    "greeting": "Bow",
                    "meeting_style": "Consensus building",
                    "negotiation": "Group decision making"
                }
            },
            "ko": {
                "language_name": "Korean",
                "region": "Asia",
                "currency": "KRW",
                "timezone": "UTC+9",
                "date_format": "YYYY-MM-DD",
                "number_format": "1,234",
                "cultural_notes": ["Respect for age and status", "Formal communication"],
                "business_etiquette": {
                    "greeting": "Bow",
                    "meeting_style": "Hierarchical and formal",
                    "negotiation": "Respect for authority"
                }
            },
            "ar": {
                "language_name": "Arabic",
                "region": "Middle East",
                "currency": "SAR",
                "timezone": "UTC+3",
                "date_format": "DD/MM/YYYY",
                "number_format": "١٬٢٣٤٫٥٦",
                "cultural_notes": ["Personal relationships crucial", "Respect for tradition"],
                "business_etiquette": {
                    "greeting": "Handshake and personal questions",
                    "meeting_style": "Relationship building first",
                    "negotiation": "Trust and personal connection"
                }
            },
            "hi": {
                "language_name": "Hindi",
                "region": "India",
                "currency": "INR",
                "timezone": "UTC+5:30",
                "date_format": "DD/MM/YYYY",
                "number_format": "1,234.56",
                "cultural_notes": ["Respect for hierarchy", "Indirect communication"],
                "business_etiquette": {
                    "greeting": "Namaste or handshake",
                    "meeting_style": "Formal and respectful",
                    "negotiation": "Relationship and trust building"
                }
            }
        }
        
        # Cultural insights for different regions
        self.cultural_insights = {
            "US": {
                "business_culture": {
                    "communication": "Direct and straightforward",
                    "decision_making": "Individual and fast",
                    "time_orientation": "Short-term and punctual"
                },
                "communication_style": {
                    "formality": "Casual in most situations",
                    "directness": "Very direct",
                    "hierarchy": "Flat organizational structure"
                },
                "negotiation_tactics": [
                    "Focus on facts and data",
                    "Win-win solutions",
                    "Time is money approach"
                ],
                "common_greetings": [
                    "Hello, how are you?",
                    "Nice to meet you",
                    "What do you do?"
                ],
                "taboos": [
                    "Personal questions too early",
                    "Being late to meetings",
                    "Not following up promptly"
                ],
                "success_indicators": [
                    "Quick decision making",
                    "Direct communication",
                    "Focus on ROI"
                ]
            },
            "UK": {
                "business_culture": {
                    "communication": "Polite and understated",
                    "decision_making": "Consensus-based",
                    "time_orientation": "Punctual but patient"
                },
                "communication_style": {
                    "formality": "Formal initially, then casual",
                    "directness": "Indirect and polite",
                    "hierarchy": "Respect for titles and positions"
                },
                "negotiation_tactics": [
                    "Understated approach",
                    "Focus on relationships",
                    "Patient negotiation style"
                ],
                "common_greetings": [
                    "Good morning/afternoon",
                    "Pleased to meet you",
                    "How do you do?"
                ],
                "taboos": [
                    "Being too direct",
                    "Not using proper titles",
                    "Rushing the relationship"
                ],
                "success_indicators": [
                    "Polite communication",
                    "Relationship building",
                    "Professional approach"
                ]
            },
            "Germany": {
                "business_culture": {
                    "communication": "Direct and precise",
                    "decision_making": "Analytical and thorough",
                    "time_orientation": "Very punctual"
                },
                "communication_style": {
                    "formality": "Formal and structured",
                    "directness": "Very direct",
                    "hierarchy": "Clear hierarchy respected"
                },
                "negotiation_tactics": [
                    "Fact-based approach",
                    "Detailed analysis",
                    "Thorough preparation"
                ],
                "common_greetings": [
                    "Guten Tag",
                    "Freut mich",
                    "Wie geht es Ihnen?"
                ],
                "taboos": [
                    "Being late",
                    "Lack of preparation",
                    "Emotional arguments"
                ],
                "success_indicators": [
                    "Thorough preparation",
                    "Fact-based presentation",
                    "Punctuality"
                ]
            }
        }
    
    async def translate_text(self, request: TranslationRequest) -> TranslationResponse:
        """Translate text with cultural adaptation"""
        async with get_eric_database() as session:
            try:
                # Use AI Service Manager for translation
                ai_manager = await get_ai_service_manager()
                translate_prompt = f"Translate the following text from {request.source_language} to {request.target_language}. Only output the translated text, nothing else:\n\n{request.text}"
                messages = [{"role": "system", "content": f"You are a professional translator. Translate text accurately while preserving meaning and tone."}, {"role": "user", "content": translate_prompt}]
                translate_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.3)
                translated_text = translate_response.text_content if translate_response.success else request.text
                
                # Apply cultural adaptation if requested
                cultural_adaptations = []
                if request.cultural_adaptation:
                    cultural_adaptations = await self._apply_cultural_adaptation(
                        translated_text,
                        request.target_language,
                        request.context
                    )
                
                # Generate alternative translations
                alternative_translations = await self._generate_alternative_translations(
                    request.text,
                    request.source_language,
                    request.target_language
                )
                
                # Calculate confidence score
                confidence_score = await self._calculate_translation_confidence(
                    request.text,
                    translated_text,
                    request.source_language,
                    request.target_language
                )
                
                response = TranslationResponse(
                    original_text=request.text,
                    translated_text=translated_text,
                    source_language=request.source_language,
                    target_language=request.target_language,
                    confidence_score=confidence_score,
                    cultural_adaptations=cultural_adaptations,
                    alternative_translations=alternative_translations,
                    created_at=datetime.utcnow()
                )
                
                # Cache translation
                await self.redis_manager.set_cache(
                    f"translation_{hash(request.text + request.target_language)}",
                    response.dict(),
                    expire=86400  # 24 hours
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "multi_language.translation_completed",
                    {
                        "source_language": request.source_language,
                        "target_language": request.target_language,
                        "confidence_score": confidence_score,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Translated text from {request.source_language} to {request.target_language}")
                return response
                
            except Exception as e:
                logger.error(f"Failed to translate text: {e}")
                raise
    
    async def create_localized_content(self, content_type: str, base_content: Dict[str, str], target_language: str) -> LocalizedContent:
        """Create localized content for a specific language"""
        try:
            # Translate content
            # Use AI Service Manager for translation
            ai_manager = await get_ai_service_manager()
            translate_prompt = f"Translate the following title from English to {target_language}. Only output the translated text:\n\n{base_content.get('title', '')}"
            messages = [{"role": "system", "content": "You are a professional translator."}, {"role": "user", "content": translate_prompt}]
            translate_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.3)
            translated_title = translate_response.text_content if translate_response.success else base_content.get("title", "")
            
            translate_prompt = f"Translate the following body text from English to {target_language}. Only output the translated text:\n\n{base_content.get('body', '')}"
            messages = [{"role": "system", "content": "You are a professional translator."}, {"role": "user", "content": translate_prompt}]
            translate_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.3)
            translated_body = translate_response.text_content if translate_response.success else base_content.get("body", "")
            
            translate_prompt = f"Translate the following subject line from English to {target_language}. Only output the translated text:\n\n{base_content.get('subject_line', '')}"
            messages = [{"role": "system", "content": "You are a professional translator."}, {"role": "user", "content": translate_prompt}]
            translate_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
            translated_subject = translate_response.text_content if translate_response.success else base_content.get("subject_line", "")
            
            translate_prompt = f"Translate the following call-to-action from English to {target_language}. Only output the translated text:\n\n{base_content.get('call_to_action', '')}"
            messages = [{"role": "system", "content": "You are a professional translator."}, {"role": "user", "content": translate_prompt}]
            translate_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
            translated_cta = translate_response.text_content if translate_response.success else base_content.get("call_to_action", "")
            
            # Apply cultural adaptations
            cultural_notes = await self._get_cultural_notes(target_language, content_type)
            
            localized_content = LocalizedContent(
                content_id=f"{content_type}_{target_language}_{datetime.utcnow().timestamp()}",
                language_code=target_language,
                content_type=content_type,
                title=translated_title,
                body=translated_body,
                subject_line=translated_subject,
                call_to_action=translated_cta,
                cultural_notes=cultural_notes,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Cache content
            await self.redis_manager.set_cache(
                f"localized_content_{localized_content.content_id}",
                localized_content.dict(),
                expire=604800  # 7 days
            )
            
            logger.info(f"Created localized content for {content_type} in {target_language}")
            return localized_content
            
        except Exception as e:
            logger.error(f"Failed to create localized content: {e}")
            raise
    
    async def get_cultural_insights(self, country: str) -> CulturalInsight:
        """Get cultural insights for a specific country"""
        try:
            if country not in self.cultural_insights:
                raise ValueError(f"Cultural insights not available for {country}")
            
            insights_data = self.cultural_insights[country]
            
            # Get language for the country
            language = self._get_primary_language(country)
            
            cultural_insight = CulturalInsight(
                country=country,
                language=language,
                business_culture=insights_data["business_culture"],
                communication_style=insights_data["communication_style"],
                negotiation_tactics=insights_data["negotiation_tactics"],
                common_greetings=insights_data["common_greetings"],
                taboos=insights_data["taboos"],
                success_indicators=insights_data["success_indicators"]
            )
            
            return cultural_insight
            
        except Exception as e:
            logger.error(f"Failed to get cultural insights: {e}")
            raise
    
    async def generate_localized_pitch(self, base_pitch: str, target_language: str, industry: str = None) -> Dict[str, str]:
        """Generate a localized sales pitch"""
        try:
            # Translate base pitch
            # Use AI Service Manager for translation
            ai_manager = await get_ai_service_manager()
            translate_prompt = f"Translate the following sales pitch from English to {target_language}. Only output the translated text:\n\n{base_pitch}"
            messages = [{"role": "system", "content": "You are a professional translator specializing in sales and marketing content."}, {"role": "user", "content": translate_prompt}]
            translate_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.3)
            translated_pitch = translate_response.text_content if translate_response.success else base_pitch
            
            # Apply cultural adaptations
            cultural_adaptations = await self._apply_cultural_adaptation(
                translated_pitch,
                target_language,
                "sales_pitch"
            )
            
            # Generate localized opening
            localized_opening = await self._generate_localized_opening(target_language, industry)
            
            # Generate localized closing
            localized_closing = await self._generate_localized_closing(target_language)
            
            localized_pitch = {
                "opening": localized_opening,
                "main_content": translated_pitch,
                "closing": localized_closing,
                "cultural_notes": cultural_adaptations,
                "language": target_language
            }
            
            logger.info(f"Generated localized pitch for {target_language}")
            return localized_pitch
            
        except Exception as e:
            logger.error(f"Failed to generate localized pitch: {e}")
            raise
    
    async def get_supported_languages(self) -> List[LanguageConfig]:
        """Get list of supported languages"""
        try:
            language_configs = []
            for code, data in self.supported_languages.items():
                config = LanguageConfig(
                    language_code=code,
                    language_name=data["language_name"],
                    region=data["region"],
                    currency=data["currency"],
                    timezone=data["timezone"],
                    date_format=data["date_format"],
                    number_format=data["number_format"],
                    cultural_notes=data["cultural_notes"],
                    business_etiquette=data["business_etiquette"],
                    is_active=data.get("is_active", True)
                )
                language_configs.append(config)
            
            return language_configs
            
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            raise
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect the language of text"""
        try:
            # Use AI Service Manager for language detection
            ai_manager = await get_ai_service_manager()
            detect_prompt = f"Detect the language of this text and respond with JSON only: {{\"language\": \"lang_code\", \"confidence\": 0.0-1.0}}\n\nText: {text}"
            messages = [{"role": "system", "content": "You are an AI assistant that detects languages. Respond only in JSON format."}, {"role": "user", "content": detect_prompt}]
            detect_response = await ai_manager.generate_text(messages=messages, max_tokens=100, temperature=0.1)
            try:
                import json
                detection_result = json.loads(detect_response.text_content) if detect_response.success else {"language": "en", "confidence": 0.5}
                detected_language = detection_result.get("language", "en")
                confidence_score = detection_result.get("confidence", 0.5)
            except:
                detected_language = "en"
                confidence_score = 0.5
            
            result = {
                "detected_language": detected_language,
                "confidence_score": confidence_score,
                "supported": detected_language in self.supported_languages,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to detect language: {e}")
            raise
    
    async def get_localization_analytics(self, date_range: str = "30d") -> Dict[str, Any]:
        """Get analytics for localization usage"""
        async with get_eric_database() as session:
            try:
                # Calculate date range
                end_date = datetime.utcnow()
                if date_range == "7d":
                    start_date = end_date - timedelta(days=7)
                elif date_range == "30d":
                    start_date = end_date - timedelta(days=30)
                elif date_range == "90d":
                    start_date = end_date - timedelta(days=90)
                else:
                    start_date = end_date - timedelta(days=30)
                
                # Query translation activities
                translation_activities = await session.execute(
                    select(EricSalesActivity).where(
                        and_(
                            EricSalesActivity.activity_type == "translation",
                            EricSalesActivity.created_at >= start_date,
                            EricSalesActivity.created_at <= end_date
                        )
                    )
                )
                translation_activities = translation_activities.scalars().all()
                
                # Calculate analytics
                total_translations = len(translation_activities)
                
                # Calculate language distribution
                language_counts = {}
                for activity in translation_activities:
                    target_language = activity.metadata.get("target_language", "unknown")
                    language_counts[target_language] = language_counts.get(target_language, 0) + 1
                
                most_translated_languages = [
                    {"language": lang, "count": count} 
                    for lang, count in sorted(language_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                ]
                
                # Calculate translation accuracy (simplified)
                translation_accuracy = {}
                for lang in language_counts.keys():
                    lang_activities = [a for a in translation_activities if a.metadata.get("target_language") == lang]
                    accuracy_scores = [a.metadata.get("accuracy", 0.9) for a in lang_activities if a.metadata.get("accuracy")]
                    avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.9
                    translation_accuracy[lang] = round(avg_accuracy, 2)
                
                # Calculate content types translated
                content_types = {}
                for activity in translation_activities:
                    content_type = activity.metadata.get("content_type", "unknown")
                    content_types[content_type] = content_types.get(content_type, 0) + 1
                
                # Calculate cultural adaptations
                cultural_adaptations_applied = len([
                    a for a in translation_activities 
                    if a.metadata.get("cultural_adaptations_applied", False)
                ])
                
                # Calculate user satisfaction
                satisfaction_scores = [
                    a.metadata.get("satisfaction", 4.0) 
                    for a in translation_activities 
                    if a.metadata.get("satisfaction")
                ]
                user_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 4.3
                
                analytics = {
                    "total_translations": total_translations,
                    "most_translated_languages": most_translated_languages,
                    "translation_accuracy": translation_accuracy,
                    "content_types_translated": content_types,
                    "cultural_adaptations_applied": cultural_adaptations_applied,
                    "user_satisfaction": round(user_satisfaction, 1)
                }
                
                return analytics
            
            except Exception as e:
                logger.error(f"Failed to get localization analytics: {e}")
                raise
    
    async def _apply_cultural_adaptation(self, text: str, target_language: str, context: str) -> List[str]:
        """Apply cultural adaptations to translated text"""
        try:
            adaptations = []
            
            # Get cultural notes for the language
            if target_language in self.supported_languages:
                cultural_notes = self.supported_languages[target_language]["cultural_notes"]
                
                # Apply context-specific adaptations
                if context == "sales_pitch":
                    if "Direct communication preferred" in cultural_notes:
                        adaptations.append("Made communication more direct")
                    if "Personal relationships important" in cultural_notes:
                        adaptations.append("Added relationship-building elements")
                
                elif context == "email":
                    if "Formal communication" in cultural_notes:
                        adaptations.append("Used formal tone and titles")
                    if "Respect for hierarchy" in cultural_notes:
                        adaptations.append("Added appropriate honorifics")
            
            return adaptations
            
        except Exception as e:
            logger.error(f"Failed to apply cultural adaptation: {e}")
            return []
    
    async def _generate_alternative_translations(self, text: str, source_language: str, target_language: str) -> List[str]:
        """Generate alternative translations using different approaches"""
        try:
            alternatives = []
            
            # Use different translation strategies for variety
            if target_language == "es":
                # Formal vs informal variations
                alternatives = [
                    f"Estimado/a, {text}",  # Formal
                    f"Hola, {text}",  # Informal
                    f"Buenos días, {text}"  # Time-based greeting
                ]
            elif target_language == "fr":
                alternatives = [
                    f"Cher/Chère, {text}",  # Formal
                    f"Bonjour, {text}",  # Standard greeting
                    f"Salut, {text}"  # Informal
                ]
            elif target_language == "de":
                alternatives = [
                    f"Sehr geehrte/r, {text}",  # Very formal
                    f"Guten Tag, {text}",  # Standard
                    f"Hallo, {text}"  # Informal
                ]
            elif target_language == "zh":
                alternatives = [
                    f"尊敬的，{text}",  # Formal
                    f"您好，{text}",  # Standard
                    f"你好，{text}"  # Informal
                ]
            elif target_language == "ja":
                alternatives = [
                    f"敬具、{text}",  # Very formal
                    f"拝啓、{text}",  # Formal
                    f"こんにちは、{text}"  # Standard
                ]
            else:
                # Generic alternatives for other languages
                alternatives = [
                    f"Dear, {text}",
                    f"Hello, {text}",
                    f"Greetings, {text}"
                ]
            
            return alternatives
            
        except Exception as e:
            logger.error(f"Failed to generate alternative translations: {e}")
            return []
    
    async def _calculate_translation_confidence(self, original_text: str, translated_text: str, source_language: str, target_language: str) -> float:
        """Calculate confidence score for translation using text analysis"""
        try:
            base_confidence = 0.85
            
            # Analyze text characteristics
            original_words = len(original_text.split())
            translated_words = len(translated_text.split())
            
            # Word count ratio (should be similar for most languages)
            word_ratio = min(translated_words / original_words, original_words / translated_words) if original_words > 0 else 0
            if word_ratio > 0.8:
                base_confidence += 0.05
            elif word_ratio < 0.5:
                base_confidence -= 0.10
            
            # Language pair complexity
            if source_language == "en" and target_language in ["es", "fr", "de"]:
                base_confidence += 0.05  # Similar language families
            elif target_language in ["zh", "ja", "ko"]:
                base_confidence -= 0.10  # More complex translation
            
            # Text length considerations
            if len(original_text) > 100:
                base_confidence += 0.02  # Longer texts often have more context
            elif len(original_text) < 20:
                base_confidence -= 0.05  # Short texts can be ambiguous
            
            # Check for common translation patterns
            if "[" in original_text and "[" in translated_text:
                base_confidence += 0.02  # Placeholders preserved
            
            return min(base_confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate translation confidence: {e}")
            return 0.5
    
    async def _get_cultural_notes(self, language_code: str, content_type: str) -> List[str]:
        """Get cultural notes for specific language and content type"""
        try:
            notes = []
            
            if language_code in self.supported_languages:
                base_notes = self.supported_languages[language_code]["cultural_notes"]
                notes.extend(base_notes)
                
                # Add content-type specific notes
                if content_type == "email":
                    notes.append("Use appropriate formalities")
                elif content_type == "pitch":
                    notes.append("Adapt to local business culture")
                elif content_type == "proposal":
                    notes.append("Consider local business practices")
            
            return notes
            
        except Exception as e:
            logger.error(f"Failed to get cultural notes: {e}")
            return []
    
    async def _generate_localized_opening(self, target_language: str, industry: str = None) -> str:
        """Generate localized opening for sales pitch"""
        try:
            openings = {
                "es": "Estimado/a [Nombre], espero que este mensaje le encuentre bien.",
                "fr": "Cher/Chère [Nom], j'espère que ce message vous trouve en bonne santé.",
                "de": "Sehr geehrte/r [Name], ich hoffe, diese Nachricht erreicht Sie gut.",
                "pt": "Prezado/a [Nome], espero que esta mensagem o/a encontre bem.",
                "zh": "尊敬的[姓名]，希望这封邮件能让您感到满意。",
                "ja": "[名前]様、このメッセージがお元気でお過ごしのところに届くことを願っております。",
                "ko": "[이름]님께, 이 메시지가 안녕하신 곳에 도착하기를 바랍니다.",
                "ar": "عزيزي/عزيزتي [الاسم]، أتمنى أن يجدك هذا الرسالة بخير.",
                "hi": "प्रिय [नाम], मुझे आशा है कि यह संदेश आपको अच्छी तरह मिलेगा।"
            }
            
            return openings.get(target_language, "Dear [Name], I hope this message finds you well.")
            
        except Exception as e:
            logger.error(f"Failed to generate localized opening: {e}")
            return "Dear [Name], I hope this message finds you well."
    
    async def _generate_localized_closing(self, target_language: str) -> str:
        """Generate localized closing for sales pitch"""
        try:
            closings = {
                "es": "Quedo a la espera de su respuesta. Saludos cordiales,",
                "fr": "J'attends votre réponse avec impatience. Cordialement,",
                "de": "Ich freue mich auf Ihre Antwort. Mit freundlichen Grüßen,",
                "pt": "Aguardo sua resposta. Atenciosamente,",
                "zh": "期待您的回复。此致敬礼，",
                "ja": "ご返信をお待ちしております。敬具、",
                "ko": "답장을 기다리겠습니다. 감사합니다,",
                "ar": "أنتظر ردك. مع أطيب التحيات،",
                "hi": "आपकी प्रतिक्रिया की प्रतीक्षा में। सादर,"
            }
            
            return closings.get(target_language, "I look forward to your response. Best regards,")
            
        except Exception as e:
            logger.error(f"Failed to generate localized closing: {e}")
            return "I look forward to your response. Best regards,"
    
    def _get_primary_language(self, country: str) -> str:
        """Get primary language for a country"""
        country_language_map = {
            "US": "en",
            "UK": "en",
            "Germany": "de",
            "France": "fr",
            "Spain": "es",
            "Brazil": "pt",
            "China": "zh",
            "Japan": "ja",
            "Korea": "ko",
            "Saudi Arabia": "ar",
            "India": "hi"
        }
        
        return country_language_map.get(country, "en")
