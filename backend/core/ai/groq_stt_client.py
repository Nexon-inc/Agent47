"""
Groq STT Client

This module provides a production-ready Groq API client for Speech-to-Text (STT).
Groq STT uses whisper-large-v3-turbo model for multilingual transcription.
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import base64

from ..config import settings
from ..logs import get_logger
from .groq_rate_limiter import get_groq_rate_limiter, ServiceType

logger = get_logger(__name__)


class GroqSTTClient:
    """Production-ready Groq STT client for Agent47"""
    
    def __init__(self):
        self.api_key = settings.groq.groq_api_key
        self.api_base_url = settings.groq.groq_api_base_url
        self.stt_model = settings.groq.groq_stt_model
        self.rate_limit_per_minute = settings.groq.groq_stt_rate_limit_per_minute
        self.rate_limit_per_day = settings.groq.groq_stt_rate_limit_per_day
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
                    "User-Agent": "Agent47-Groq-STT-Client/1.0"
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
                logger.info("Groq STT client initialized successfully")
                return True
            else:
                raise Exception(f"Groq STT API health check failed: {health_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Groq STT client: {e}")
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
    
    async def _check_rate_limits(self) -> Tuple[bool, Optional[str]]:
        """Check if rate limits are exceeded"""
        # Use centralized rate limiter if available
        if self._rate_limiter:
            try:
                allowed, error_msg, usage_stats = await self._rate_limiter.check_rate_limit(
                    ServiceType.STT, user_id=None
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
    
    def _detect_audio_format(self, audio_data: bytes, audio_format: Optional[str] = None) -> str:
        """Detect audio format from data or use provided format"""
        if audio_format:
            return audio_format.lower()
        
        # Detect format from magic bytes
        if audio_data.startswith(b'\xff\xfb') or audio_data.startswith(b'ID3'):
            return "mp3"
        elif audio_data.startswith(b'RIFF') and b'WAVE' in audio_data[:12]:
            return "wav"
        elif audio_data.startswith(b'OggS'):
            return "ogg"
        elif audio_data.startswith(b'fLaC'):
            return "flac"
        elif audio_data.startswith(b'\x00\x00\x00\x20ftyp'):
            return "m4a"
        else:
            return "mp3"  # Default to mp3
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe audio to text using Groq STT API
        
        Args:
            audio_data: Audio file data as bytes
            audio_format: Audio format (mp3, wav, ogg, flac, m4a). Auto-detected if not provided.
            language: Language code (optional, auto-detected if not provided)
        
        Returns:
            Dict with success, text, confidence, language, and segments
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
                "error": f"Groq STT API is unhealthy: {health_check.get('error', 'Unknown error')}",
                "health_status": self._health_status
            }
        
        # Detect audio format if not provided
        detected_format = self._detect_audio_format(audio_data, audio_format)
        
        self._concurrent_requests += 1
        self._total_requests += 1
        
        try:
            endpoint = f"{self.api_base_url}/audio/transcriptions"
            
            # Prepare multipart form data
            data = aiohttp.FormData()
            data.add_field('model', self.stt_model)
            data.add_field('file', audio_data, filename=f'audio.{detected_format}', content_type=f'audio/{detected_format}')
            data.add_field('response_format', 'verbose_json')
            
            if language:
                data.add_field('language', language)
            
            # Make request with retries
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    start_time = time.time()
                    
                    async with self.session.post(
                        endpoint,
                        data=data,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            response_time = int((time.time() - start_time) * 1000)
                            
                            # Extract transcription data
                            text = result.get("text", "")
                            detected_language = result.get("language", language or "unknown")
                            duration = result.get("duration", 0)
                            segments = result.get("segments", [])
                            
                            # Calculate confidence from segments if available
                            confidence = 0.0
                            if segments:
                                segment_confidences = [seg.get("no_speech_prob", 0) for seg in segments]
                                if segment_confidences:
                                    # Convert no_speech_prob to confidence (inverse)
                                    avg_no_speech = sum(segment_confidences) / len(segment_confidences)
                                    confidence = max(0.0, min(1.0, 1.0 - avg_no_speech))
                            
                            # Update metrics
                            self._successful_requests += 1
                            self._daily_requests += 1
                            self._requests_per_minute.append(time.time())
                            
                            # Record usage in centralized rate limiter
                            if self._rate_limiter:
                                try:
                                    await self._rate_limiter.record_usage(
                                        ServiceType.STT, user_id=None, tokens=0
                                    )
                                except Exception as e:
                                    logger.warning(f"Failed to record usage in rate limiter: {e}")
                            
                            return {
                                "success": True,
                                "text": text,
                                "confidence": confidence,
                                "language": detected_language,
                                "duration": duration,
                                "segments": segments,
                                "metadata": {
                                    "model": self.stt_model,
                                    "audio_format": detected_format,
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
            logger.error(f"Groq STT transcription error: {e}")
            self._failed_requests += 1
            return {
                "success": False,
                "error": str(e)
            }
            
        finally:
            self._concurrent_requests -= 1
    
    async def transcribe_audio_file(
        self,
        audio_file_path: str,
        audio_format: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe audio file to text
        
        Convenience method that reads audio file and calls transcribe_audio
        """
        try:
            with open(audio_file_path, "rb") as f:
                audio_data = f.read()
            
            return await self.transcribe_audio(
                audio_data=audio_data,
                audio_format=audio_format,
                language=language
            )
        except Exception as e:
            logger.error(f"Failed to read audio file: {e}")
            return {
                "success": False,
                "error": f"Failed to read audio file: {str(e)}"
            }
    
    def _reset_daily_counter_if_needed(self):
        """Reset daily request counter if a new day has started"""
        today = datetime.utcnow().date()
        if today > self._last_daily_reset:
            self._daily_requests = 0
            self._last_daily_reset = today
            logger.info(f"Reset Groq STT daily request counter (new day: {today})")
    
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

