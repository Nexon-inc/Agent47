import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.ai import get_ai_service_manager, AIServiceManager
from core.cache.redis_manager import init_redis

logger = logging.getLogger(__name__)

class GeoLocalizationService:
    """Service for geo-targeting and multi-language localization support"""
    
    def __init__(self):
        self.nlp_utils = None
        self.redis_client = None
        self._initialized = False
        
        # Core language support
        self.language_regions = {
            "en": {"name": "English", "regions": ["US", "UK", "CA", "AU", "KE", "NG", "ZA"], "rtl": False},
            "es": {"name": "Spanish", "regions": ["ES", "MX", "AR", "CO", "PE"], "rtl": False},
            "fr": {"name": "French", "regions": ["FR", "CA", "BE", "SN", "CI"], "rtl": False},
            "de": {"name": "German", "regions": ["DE", "AT", "CH"], "rtl": False},
            "sw": {"name": "Swahili", "regions": ["KE", "TZ", "UG", "RW"], "rtl": False},
            "yo": {"name": "Yoruba", "regions": ["NG", "BJ", "TG"], "rtl": False},
            "ha": {"name": "Hausa", "regions": ["NG", "NE", "TD"], "rtl": False},
            "zu": {"name": "Zulu", "regions": ["ZA", "ZW"], "rtl": False}
        }
    
    async def initialize(self):
        """Initialize geo-localization service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager: Optional[AIServiceManager] = None
            self.ai_service_manager = await get_ai_service_manager()
            self.redis_client = await init_redis()
            self._initialized = True
            logger.info("Clara geo-localization service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize geo-localization service: {e}")
            raise
    
    async def detect_customer_location(
        self,
        ip_address: Optional[str] = None,
        timezone: Optional[str] = None,
        language: Optional[str] = None,
        coordinates: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Detect customer location and preferred language with Google Maps integration"""
        try:
            await self.initialize()
            
            detected_info = {
                "country": "Unknown",
                "region": "Unknown",
                "timezone": timezone or "UTC",
                "language": language or "en",
                "confidence": "low"
            }
            
            # Use Google Maps reverse geocoding if coordinates provided
            if coordinates:
                from core.services.google_maps_service import get_google_maps_service
                maps_service = await get_google_maps_service()
                
                # Use Google Maps Geocoding API for reverse geocoding
                try:
                    import httpx
                    url = "https://maps.googleapis.com/maps/api/geocode/json"
                    params = {
                        "latlng": f"{coordinates.get('lat')},{coordinates.get('lng')}",
                        "key": maps_service.api_key
                    }
                    
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(url, params=params)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("status") == "OK" and data.get("results"):
                                result = data["results"][0]
                                for component in result.get("address_components", []):
                                    if "country" in component.get("types", []):
                                        detected_info["country"] = component.get("long_name")
                                    if "administrative_area_level_1" in component.get("types", []):
                                        detected_info["region"] = component.get("long_name")
                                detected_info["confidence"] = "high"
                                detected_info["formatted_address"] = result.get("formatted_address")
                except Exception as e:
                    logger.warning(f"Google Maps reverse geocoding failed: {e}")
            
            # Use provided language if available
            if language and language in self.language_regions:
                detected_info["language"] = language
                if detected_info["confidence"] == "low":
                    detected_info["confidence"] = "medium"
                
                # Infer region from language
                if language in ["sw", "yo", "ha", "zu"]:
                    if detected_info["region"] == "Unknown":
                        detected_info["region"] = "Africa"
                    detected_info["confidence"] = "high"
            
            # Use timezone to refine location
            if timezone:
                detected_info["timezone"] = timezone
                if "Africa" in timezone and detected_info["region"] == "Unknown":
                    detected_info["region"] = "Africa"
                    if detected_info["confidence"] != "high":
                        detected_info["confidence"] = "medium"
            
            return {
                "success": True,
                "location": detected_info
            }
            
        except Exception as e:
            logger.error(f"Failed to detect customer location: {e}")
            return {
                "success": False,
                "error": f"Failed to detect customer location: {str(e)}"
            }
    
    async def get_localized_response(
        self,
        message: str,
        target_language: str,
        formality_level: str = "casual"
    ) -> Dict[str, Any]:
        """Get localized response in the target language"""
        try:
            await self.initialize()
            
            if target_language not in self.language_regions:
                return {
                    "success": False,
                    "error": f"Unsupported language: {target_language}"
                }
            
            lang_info = self.language_regions[target_language]
            
            # Generate localized response using NLP
            localized_prompt = f"""
            Translate and localize this message to {lang_info['name']} ({target_language}):
            "{message}"
            
            Consider cultural context and provide a natural, localized response.
            """
            
            # Use AI Service Manager instead of NLPUtils
            from core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that localizes content for different regions and cultures."},
                {"role": "user", "content": localized_prompt}
            ]
            ai_response = await ai_manager.generate_text(
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            localized_response = ai_response.text_content if ai_response.success else response
            
            return {
                "success": True,
                "localized_message": localized_response,
                "target_language": target_language,
                "language_name": lang_info["name"],
                "rtl": lang_info["rtl"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get localized response: {e}")
            return {
                "success": False,
                "error": f"Failed to get localized response: {str(e)}"
            }
    
    async def get_supported_languages(self) -> Dict[str, Any]:
        """Get list of supported languages"""
        try:
            await self.initialize()
            
            languages = []
            for code, info in self.language_regions.items():
                languages.append({
                    "code": code,
                    "name": info["name"],
                    "regions": info["regions"],
                    "rtl": info["rtl"]
                })
            
            return {
                "success": True,
                "languages": languages,
                "total_languages": len(languages)
            }
            
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return {
                "success": False,
                "error": f"Failed to get supported languages: {str(e)}"
            }
    
    async def get_regional_support_info(
        self,
        region: str
    ) -> Dict[str, Any]:
        """Get regional support information"""
        try:
            await self.initialize()
            
            # Basic regional support data
            regional_info = {
                "africa": {
                    "business_hours": "8:00-17:00",
                    "timezone": "Africa/Nairobi",
                    "languages": ["en", "sw", "yo", "ha", "zu"],
                    "cultural_notes": "Respectful communication, relationship-focused"
                },
                "europe": {
                    "business_hours": "9:00-18:00",
                    "timezone": "Europe/London",
                    "languages": ["en", "de", "fr", "it"],
                    "cultural_notes": "Professional, time-conscious"
                },
                "asia": {
                    "business_hours": "9:00-18:00",
                    "timezone": "Asia/Tokyo",
                    "languages": ["en", "zh", "ja", "ko"],
                    "cultural_notes": "Formal, hierarchical communication"
                }
            }
            
            if region.lower() in regional_info:
                return {
                    "success": True,
                    "region": region,
                    "info": regional_info[region.lower()]
                }
            else:
                return {
                    "success": False,
                    "error": f"Region not found: {region}"
                }
                
        except Exception as e:
            logger.error(f"Failed to get regional support info: {e}")
            return {
                "success": False,
                "error": f"Failed to get regional support info: {str(e)}"
            }
