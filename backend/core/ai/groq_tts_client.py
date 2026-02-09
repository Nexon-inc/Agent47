"""
Groq TTS Client

This module provides a production-ready Groq API client for Text-to-Speech (TTS).
Groq TTS supports playai-tts (English) and playai-tts-arabic (Arabic) models.
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from ..config import settings
from ..logs import get_logger
from .groq_rate_limiter import get_groq_rate_limiter, ServiceType

logger = get_logger(__name__)


# Groq TTS Voice Options
# English voices (19 voices)
ENGLISH_VOICES = [
    "alloy", "echo", "fable", "onyx", "nova", "shimmer",
    "adam", "antoni", "arnold", "bella", "domi", "elli",
    "josh", "rachel", "sam", "thomas", "charlie", "emily", "gigi"
]

# Arabic voices (4 voices)
ARABIC_VOICES = [
    "arabic-male-1", "arabic-male-2", "arabic-female-1", "arabic-female-2"
]

# Voice mapping for common styles
VOICE_STYLE_MAPPING = {
    "professional": "alloy",
    "friendly": "echo",
    "calm": "fable",
    "energetic": "onyx",
    "warm": "nova",
    "male": "adam",
    "female": "bella",
    "neutral": "alloy"
}


class GroqTTSClient:
    """Production-ready Groq TTS client for Agent47"""
    
    def __init__(self):
        self.api_key = settings.groq.groq_api_key
        self.api_base_url = settings.groq.groq_api_base_url
        self.tts_model = settings.groq.groq_tts_model
        self.rate_limit_per_minute = settings.groq.groq_tts_rate_limit_per_minute
        self.rate_limit_per_day = settings.groq.groq_tts_rate_limit_per_day
        self.timeout = settings.groq.groq_request_timeout
        self.max_retries = settings.groq.groq_max_retries
        self.retry_delay = settings.groq.groq_retry_delay
        
        self.session: Optional[aiohttp.ClientSession] = None
        self._health_status = "unknown"
        self._last_health_check = 0
        self._concurrent_requests = 0
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._daily_requests = 0
        self._last_daily_reset = datetime.utcnow().date()
        self._requests_per_minute = []
        self._rate_limiter = None
        
    async def initialize(self):
        """Initialize HTTP session and verify Groq API connection"""
        try:
            if not self.api_key:
                raise ValueError("Groq API key not configured. Set GROQ_API_KEY in environment variables.")
            
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Agent47-Groq-TTS-Client/1.0"
                }
            )
            
            # Test connection with a simple health check
            health_result = await self.health_check()
            if health_result["healthy"]:
                self._health_status = "healthy"
                # Initialize rate limiter (optional, falls back to client-side if unavailable)
                try:
                    self._rate_limiter = await get_groq_rate_limiter()
                except Exception as e:
                    logger.warning(f"Rate limiter not available, using client-side rate limiting: {e}")
                    self._rate_limiter = None
                logger.info("Groq TTS client initialized successfully")
                return True
            else:
                raise Exception(f"Groq TTS API health check failed: {health_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Groq TTS client: {e}")
            self._health_status = "unhealthy"
            raise
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Groq API health with caching"""
        current_time = time.time()
        
        # Cache health check results for 30 seconds
        if current_time - self._last_health_check < 30:
            return {
                "healthy": self._health_status == "healthy",
                "status": self._health_status,
                "cached": True
            }
        
        try:
            if not self.session:
                return {"healthy": False, "error": "Session not initialized"}
            
            if not self.api_key:
                return {"healthy": False, "error": "API key not configured"}
            
            # Use models endpoint as health check (lightweight)
            health_endpoint = f"{self.api_base_url}/models"
            
            async with self.session.get(health_endpoint, timeout=5) as response:
                if response.status == 200:
                    self._health_status = "healthy"
                    self._last_health_check = current_time
                    return {"healthy": True, "status": "healthy"}
                elif response.status == 401:
                    self._health_status = "unauthorized"
                    return {"healthy": False, "error": "Invalid API key"}
                elif response.status == 429:
                    self._health_status = "rate_limited"
                    return {"healthy": False, "error": "Rate limit exceeded"}
                else:
                    self._health_status = "unhealthy"
                    return {"healthy": False, "error": f"HTTP {response.status}"}
                    
        except asyncio.TimeoutError:
            self._health_status = "timeout"
            return {"healthy": False, "error": "Health check timeout"}
        except Exception as e:
            self._health_status = "error"
            return {"healthy": False, "error": str(e)}
    
# African voices (shared from English pool for now, but with specific mapping if available)
AFRICAN_VOICES = [
    "onyx", "echo", "nova", "shimmer" # Using clearer voices for diverse accents
]

# ...

    def get_available_voices(self, language: str = "en") -> List[str]:
        """Get available voices for a given language"""
        if language.startswith("ar"):
            return ARABIC_VOICES
        elif language in ["sw", "yo", "ig", "ha", "am", "zu", "xh", "so", "af", "mg", "sn"]: # Swahili, Yoruba, Igbo, Hausa, Amharic, Zulu, Xhosa, Somali, Afrikaans, Malagasy, Shona
            return AFRICAN_VOICES
        else:
            return ENGLISH_VOICES
    
    def _select_voice(self, voice: Optional[str], language: str, voice_style: Optional[str] = None) -> str:
        """Select appropriate voice based on parameters"""
        # If voice is explicitly provided and valid, use it
        if voice:
            available_voices = self.get_available_voices(language)
            # Allow fallback to English voices if specific list doesn't have it
            if voice in available_voices or voice in ENGLISH_VOICES:
                return voice
        
        # Use voice style mapping if provided
        if voice_style:
            mapped_voice = VOICE_STYLE_MAPPING.get(voice_style.lower())
            if mapped_voice:
                return mapped_voice
        
        # Default based on language
        if language.startswith("ar"):
            return ARABIC_VOICES[0]  # Default Arabic voice
        elif language in ["sw", "yo", "ig", "ha", "am", "zu", "xh", "so", "af", "mg", "sn"]:
             return "onyx" # Default African voice (deep/clear)
        else:
            return "alloy"  # Default English voice
    
    async def _check_rate_limits(self) -> Tuple[bool, Optional[str]]:
        """Check if rate limits are exceeded"""
        # Use centralized rate limiter if available
        if self._rate_limiter:
            try:
                allowed, error_msg, usage_stats = await self._rate_limiter.check_rate_limit(
                    ServiceType.TTS, user_id=None
                )
                if not allowed:
                    return False, error_msg or "Rate limit exceeded"
            except Exception as e:
                logger.warning(f"Rate limiter check failed, using client-side: {e}")
                # Fall through to client-side rate limiting
        
        # Client-side rate limiting (fallback or primary if limiter unavailable)
        # Reset daily counter if needed
        self._reset_daily_counter_if_needed()
        
        # Check daily limit
        if self._daily_requests >= self.rate_limit_per_day:
            return False, f"Daily rate limit exceeded ({self._daily_requests}/{self.rate_limit_per_day})"
        
        # Check per-minute limit
        current_time = time.time()
        # Remove requests older than 1 minute
        self._requests_per_minute = [
            req_time for req_time in self._requests_per_minute
            if current_time - req_time < 60
        ]
        
        if len(self._requests_per_minute) >= self.rate_limit_per_minute:
            return False, f"Rate limit exceeded: {len(self._requests_per_minute)} requests in the last minute"
        
        return True, None
    
    async def text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        language: str = "en",
        speed: float = 1.0,
        pitch: float = 1.0,
        voice_style: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert text to speech using Groq TTS API
        
        Args:
            text: Text to convert to speech
            voice: Specific voice name (optional)
            language: Language code (e.g., "en", "ar")
            speed: Speech speed (0.25 to 4.0, default 1.0)
            pitch: Voice pitch (0.0 to 2.0, default 1.0)
            voice_style: Voice style hint (e.g., "professional", "friendly")
        
        Returns:
            Dict with success, audio_data (bytes), and metadata
        """
        # Check rate limits
        can_proceed, error_msg = await self._check_rate_limits()
        if not can_proceed:
            return {
                "success": False,
                "error": error_msg
            }
        
        # Check health
        health_check = await self.health_check()
        if not health_check["healthy"]:
            return {
                "success": False,
                "error": f"Groq TTS API is unhealthy: {health_check.get('error', 'Unknown error')}",
                "health_status": self._health_status
            }
        
        # Select appropriate voice
        selected_voice = self._select_voice(voice, language, voice_style)
        
        # Determine model based on language
        model = self.tts_model
        if language.startswith("ar") and "arabic" not in model:
            model = "playai-tts-arabic"
        elif not language.startswith("ar") and "arabic" in model:
            model = "playai-tts"
        
        self._concurrent_requests += 1
        self._total_requests += 1
        
        try:
            # Prepare request payload
            payload = {
                "model": model,
                "input": text,
                "voice": selected_voice,
                "response_format": "mp3",
                "speed": max(0.25, min(4.0, speed)),  # Clamp speed
            }
            
            endpoint = f"{self.api_base_url}/audio/speech"
            
            # Make request with retries
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    start_time = time.time()
                    
                    async with self.session.post(
                        endpoint,
                        json=payload,
                        timeout=self.timeout
                    ) as response:
                        
                        if response.status == 200:
                            audio_data = await response.read()
                            response_time = int((time.time() - start_time) * 1000)
                            
                            # Update metrics
                            self._successful_requests += 1
                            self._daily_requests += 1
                            self._requests_per_minute.append(time.time())
                            
                            # Record usage in centralized rate limiter
                            if self._rate_limiter:
                                try:
                                    await self._rate_limiter.record_usage(
                                        ServiceType.TTS, user_id=None, tokens=0
                                    )
                                except Exception as e:
                                    logger.warning(f"Failed to record usage in rate limiter: {e}")
                            
                            return {
                                "success": True,
                                "audio_data": audio_data,
                                "metadata": {
                                    "voice": selected_voice,
                                    "language": language,
                                    "model": model,
                                    "speed": speed,
                                    "pitch": pitch,
                                    "voice_style": voice_style,
                                    "text_length": len(text),
                                    "audio_format": "mp3",
                                    "audio_size_bytes": len(audio_data),
                                    "response_time_ms": response_time
                                }
                            }
                            
                        elif response.status == 401:
                            last_error = "Invalid API key"
                            break  # Don't retry auth errors
                            
                        elif response.status == 429:
                            # Rate limited - check retry-after header
                            retry_after = int(response.headers.get("Retry-After", self.retry_delay))
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(retry_after)
                                continue
                            last_error = f"Rate limit exceeded (HTTP 429)"
                            
                        elif response.status == 400:
                            error_data = await response.json()
                            last_error = f"Bad request: {error_data.get('error', {}).get('message', 'Unknown error')}"
                            break  # Don't retry bad requests
                            
                        else:
                            last_error = f"HTTP {response.status}"
                            
                except asyncio.TimeoutError:
                    last_error = "Request timeout"
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                        
                except Exception as e:
                    last_error = str(e)
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
            
            # All retries failed
            self._failed_requests += 1
            return {
                "success": False,
                "error": last_error or "Unknown error",
                "retries": self.max_retries
            }
            
        except Exception as e:
            logger.error(f"Groq TTS generation error: {e}")
            self._failed_requests += 1
            return {
                "success": False,
                "error": str(e)
            }
            
        finally:
            self._concurrent_requests -= 1
    
    def _reset_daily_counter_if_needed(self):
        """Reset daily request counter if a new day has started"""
        today = datetime.utcnow().date()
        if today > self._last_daily_reset:
            self._daily_requests = 0
            self._last_daily_reset = today
            logger.info(f"Reset Groq TTS daily request counter (new day: {today})")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        return {
            "health_status": self._health_status,
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "failed_requests": self._failed_requests,
            "daily_requests": self._daily_requests,
            "daily_limit": self.rate_limit_per_day,
            "concurrent_requests": self._concurrent_requests,
            "requests_last_minute": len(self._requests_per_minute),
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "last_health_check": self._last_health_check
        }

