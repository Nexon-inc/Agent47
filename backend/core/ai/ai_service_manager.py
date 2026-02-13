"""
AI Service Manager

This module provides a unified interface for all AI services including
LLM text generation and image generation with automatic failover.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass

from ..config import settings
from ..logs import get_logger
from .llm_service_pool import LLMServicePool, LLMRequest, LLMResponse, get_llm_service_pool
from .image_generation_service import ImageGenerationService, ImageGenerationRequest, ImageGenerationResponse, get_image_generation_service
from .groq_tts_client import GroqTTSClient
from .groq_stt_client import GroqSTTClient
from .groq_tier_enforcement import get_groq_tier_enforcement, ServiceType as TierServiceType
from ..database.models import UserTier

logger = get_logger(__name__)

@dataclass
class UnifiedAIRequest:
    """Unified request for AI services"""
    text_prompt: Optional[str] = None
    image_prompt: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stream: bool = False
    
    # Image generation parameters
    image_width: int = 1024
    image_height: int = 1024
    num_images: int = 1
    image_steps: int = 20
    guidance_scale: float = 7.5
    image_seed: Optional[int] = None
    negative_prompt: Optional[str] = None
    style: Optional[str] = None

@dataclass
class UnifiedAIResponse:
    """Unified response from AI services"""
    success: bool
    text_content: Optional[str] = None
    images: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    service_used: Optional[str] = None
    fallback_used: bool = False
    image_generation_disabled: bool = False
    response_time_ms: Optional[int] = None

class AIServiceManager:
    """Unified AI service manager with automatic failover"""
    
    def __init__(self):
        self.llm_service_pool: Optional[LLMServicePool] = None
        self.image_generation_service: Optional[ImageGenerationService] = None
        self.groq_tts_client: Optional[GroqTTSClient] = None
        self.groq_stt_client: Optional[GroqSTTClient] = None
        self._tier_enforcement = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize all AI services"""
        try:
            logger.info("Initializing AI Service Manager...")
            
            # Initialize LLM service pool
            self.llm_service_pool = await get_llm_service_pool()
            
            # Initialize image generation service
            self.image_generation_service = await get_image_generation_service()
            
            # Voice services (TTS/STT) will be lazily initialized on first use 
            # to reduce startup latency.
            
            # Initialize tier enforcement
            
            # Initialize tier enforcement
            try:
                self._tier_enforcement = await get_groq_tier_enforcement()
                logger.info("Groq tier enforcement initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize tier enforcement: {e}. Tier limits will not be enforced.")
                self._tier_enforcement = None
            
            # Sync image generation status with LLM service pool
            await self._sync_services()
            
            self._initialized = True
            logger.info("AI Service Manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Service Manager: {e}")
            return False
    
    async def close(self):
        """Close all AI services"""
        if self.llm_service_pool:
            await self.llm_service_pool.close()
        if self.image_generation_service:
            await self.image_generation_service.close()
        if self.groq_tts_client:
            await self.groq_tts_client.close()
        if self.groq_stt_client:
            await self.groq_stt_client.close()
        self._initialized = False
    
    async def _sync_services(self):
        """Sync image generation service with LLM service pool status"""
        if self.llm_service_pool and self.image_generation_service:
            llm_status = self.llm_service_pool.get_service_status()
            image_enabled = llm_status.get("image_generation_enabled", True)
            self.image_generation_service.set_enabled(image_enabled)
    
    async def generate_text(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stream: bool = False,
        user_id: Optional[int] = None,
        user_tier: Optional[UserTier] = None,
        **kwargs
    ) -> UnifiedAIResponse:
        """Generate text using the best available LLM service"""
        if not self._initialized:
            return UnifiedAIResponse(
                success=False,
                error="AI Service Manager not initialized"
            )
        
        # Check tier limits if user_id is provided
        if user_id is not None and self._tier_enforcement:
            try:
                # Estimate tokens (rough estimate: 4 chars per token)
                estimated_tokens = sum(len(msg.get("content", "")) for msg in messages) // 4
                if max_tokens:
                    estimated_tokens += max_tokens
                
                allowed, error_msg, usage_stats = await self._tier_enforcement.check_tier_limit(
                    user_id=user_id,
                    user_tier=user_tier,
                    service_type=TierServiceType.LLM,
                    tokens=estimated_tokens
                )
                
                if not allowed:
                    return UnifiedAIResponse(
                        success=False,
                        error=error_msg or "Tier limit exceeded",
                        metadata=usage_stats
                    )
            except Exception as e:
                logger.warning(f"Tier limit check failed: {e}. Proceeding without tier enforcement.")
        
        # Create LLM request with universal pass-through params
        llm_request = LLMRequest(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stream=stream,
            require_image_generation=False,
            extra_params=kwargs
        )
        
        # Generate text
        llm_response = await self.llm_service_pool.generate_text(llm_request)
        
        # Record usage if successful and user_id is provided
        if llm_response.success and user_id is not None and self._tier_enforcement:
            try:
                tokens_used = llm_response.usage.get("total_tokens", 0) if llm_response.usage else 0
                await self._tier_enforcement.record_usage(
                    user_id=user_id,
                    user_tier=user_tier,
                    service_type=TierServiceType.LLM,
                    tokens=tokens_used
                )
            except Exception as e:
                logger.warning(f"Failed to record usage: {e}")
        
        # Sync services after potential failover
        await self._sync_services()
        
        return UnifiedAIResponse(
            success=llm_response.success,
            text_content=llm_response.content,
            metadata=llm_response.usage,
            error=llm_response.error,
            service_used=llm_response.service_used,
            fallback_used=llm_response.fallback_used,
            image_generation_disabled=llm_response.image_generation_disabled,
            response_time_ms=llm_response.response_time_ms
        )
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
        steps: int = 20,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        style: Optional[str] = None,
        user_id: Optional[int] = None,
        user_tier: Optional[UserTier] = None
    ) -> UnifiedAIResponse:
        """Generate image using Google Gemini with tier-based model selection
        
        Args:
            prompt: Image generation prompt
            negative_prompt: Negative prompt (optional)
            width: Image width (default: 1024)
            height: Image height (default: 1024)
            num_images: Number of images to generate (default: 1)
            steps: Generation steps (not used for Gemini, kept for compatibility)
            guidance_scale: Guidance scale (not used for Gemini, kept for compatibility)
            seed: Random seed (optional)
            style: Style preset (optional)
            user_id: User ID for tier lookup (optional)
            user_tier: User tier (FREE, STARTER, PRO) - if not provided, will be looked up
        """
        if not self._initialized:
            return UnifiedAIResponse(
                success=False,
                error="AI Service Manager not initialized"
            )
        
        # If user_tier not provided but user_id is, we could look it up
        # For now, we'll require user_tier to be passed explicitly
        if user_tier is None:
            # Default to FREE tier if not specified (will be rejected)
            user_tier = UserTier.FREE
        
        # Create image generation request
        image_request = ImageGenerationRequest(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_images=num_images,
            steps=steps,
            guidance_scale=guidance_scale,
            seed=seed,
            style=style
        )
        
        # Generate image with tier-based model selection
        image_response = await self.image_generation_service.generate_image(
            image_request, 
            user_tier=user_tier
        )
        
        return UnifiedAIResponse(
            success=image_response.success,
            images=image_response.images,
            metadata=image_response.metadata,
            error=image_response.error,
            service_used="google_gemini",
            response_time_ms=image_response.response_time_ms
        )
    
    async def generate_combined(
        self,
        request: UnifiedAIRequest
    ) -> Dict[str, UnifiedAIResponse]:
        """Generate both text and image content"""
        results = {}
        
        # Generate text if requested
        if request.text_prompt or request.messages:
            if request.messages:
                messages = request.messages
            else:
                messages = [{"role": "user", "content": request.text_prompt}]
            
            text_response = await self.generate_text(
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
                stream=request.stream
            )
            results["text"] = text_response
        
        # Generate image if requested
        if request.image_prompt:
            image_response = await self.generate_image(
                prompt=request.image_prompt,
                negative_prompt=request.negative_prompt,
                width=request.image_width,
                height=request.image_height,
                num_images=request.num_images,
                steps=request.image_steps,
                guidance_scale=request.guidance_scale,
                seed=request.image_seed,
                style=request.style
            )
            results["image"] = image_response
        
        return results
    
    async def text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        language: str = "en",
        speed: float = 1.0,
        pitch: float = 1.0,
        voice_style: Optional[str] = None,
        user_id: Optional[int] = None,
        user_tier: Optional[UserTier] = None
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
        if not self._initialized:
            return {
                "success": False,
                "error": "AI Service Manager not initialized"
            }
        
        if not self.groq_tts_client:
            try:
                logger.info("Lazily initializing Groq TTS client...")
                self.groq_tts_client = GroqTTSClient()
                await self.groq_tts_client.initialize()
            except Exception as e:
                logger.error(f"Failed to lazily initialize Groq TTS client: {e}")
                return {
                    "success": False,
                    "error": "Groq TTS client initialization failed"
                }
        
        # Check tier limits if user_id is provided
        if user_id is not None and self._tier_enforcement:
            try:
                # Estimate duration (rough: ~150 words per minute, average 5 chars per word)
                estimated_words = len(text) / 5
                estimated_duration = (estimated_words / 150) * 60  # seconds
                
                allowed, error_msg, usage_stats = await self._tier_enforcement.check_tier_limit(
                    user_id=user_id,
                    user_tier=user_tier,
                    service_type=TierServiceType.TTS,
                    duration_seconds=estimated_duration
                )
                
                if not allowed:
                    return {
                        "success": False,
                        "error": error_msg or "Tier limit exceeded",
                        "usage_stats": usage_stats
                    }
            except Exception as e:
                logger.warning(f"Tier limit check failed: {e}. Proceeding without tier enforcement.")
        
        try:
            result = await self.groq_tts_client.text_to_speech(
                text=text,
                voice=voice,
                language=language,
                speed=speed,
                pitch=pitch,
                voice_style=voice_style
            )
            
            # Record usage if successful and user_id is provided
            if result.get("success") and user_id is not None and self._tier_enforcement:
                try:
                    # Get actual duration from metadata if available
                    metadata = result.get("metadata", {})
                    duration = metadata.get("duration_seconds", 0.0)
                    if not duration:
                        # Estimate from audio size (rough: ~1KB per second for MP3)
                        audio_size = metadata.get("audio_size_bytes", 0)
                        duration = audio_size / 1024.0
                    
                    await self._tier_enforcement.record_usage(
                        user_id=user_id,
                        user_tier=user_tier,
                        service_type=TierServiceType.TTS,
                        duration_seconds=duration
                    )
                except Exception as e:
                    logger.warning(f"Failed to record TTS usage: {e}")
            
            return result
        except Exception as e:
            logger.error(f"TTS generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: Optional[str] = None,
        language: Optional[str] = None,
        user_id: Optional[int] = None,
        user_tier: Optional[UserTier] = None
    ) -> Dict[str, Any]:
        """Transcribe audio to text using Groq STT API
        
        Args:
            audio_data: Audio file data as bytes
            audio_format: Audio format (mp3, wav, ogg, flac, m4a). Auto-detected if not provided.
            language: Language code (optional, auto-detected if not provided)
        
        Returns:
            Dict with success, text, confidence, language, segments, and metadata
        """
        if not self._initialized:
            return {
                "success": False,
                "error": "AI Service Manager not initialized"
            }
        
        if not self.groq_stt_client:
            try:
                logger.info("Lazily initializing Groq STT client...")
                self.groq_stt_client = GroqSTTClient()
                await self.groq_stt_client.initialize()
            except Exception as e:
                logger.error(f"Failed to lazily initialize Groq STT client: {e}")
                return {
                    "success": False,
                    "error": "Groq STT client initialization failed"
                }
        
        # Check tier limits if user_id is provided
        if user_id is not None and self._tier_enforcement:
            try:
                # Estimate duration from audio size (rough: ~1KB per second for MP3, ~10KB per second for WAV)
                if audio_format == "wav":
                    estimated_duration = len(audio_data) / 10240.0
                else:
                    estimated_duration = len(audio_data) / 1024.0
                
                allowed, error_msg, usage_stats = await self._tier_enforcement.check_tier_limit(
                    user_id=user_id,
                    user_tier=user_tier,
                    service_type=TierServiceType.STT,
                    duration_seconds=estimated_duration
                )
                
                if not allowed:
                    return {
                        "success": False,
                        "error": error_msg or "Tier limit exceeded",
                        "usage_stats": usage_stats
                    }
            except Exception as e:
                logger.warning(f"Tier limit check failed: {e}. Proceeding without tier enforcement.")
        
        try:
            result = await self.groq_stt_client.transcribe_audio(
                audio_data=audio_data,
                audio_format=audio_format,
                language=language
            )
            
            # Record usage if successful and user_id is provided
            if result.get("success") and user_id is not None and self._tier_enforcement:
                try:
                    # Get actual duration from metadata if available
                    metadata = result.get("metadata", {})
                    duration = metadata.get("duration", 0.0)
                    if not duration:
                        # Estimate from audio size
                        audio_size = metadata.get("audio_size_bytes", len(audio_data))
                        if audio_format == "wav":
                            duration = audio_size / 10240.0
                        else:
                            duration = audio_size / 1024.0
                    
                    await self._tier_enforcement.record_usage(
                        user_id=user_id,
                        user_tier=user_tier,
                        service_type=TierServiceType.STT,
                        duration_seconds=duration
                    )
                except Exception as e:
                    logger.warning(f"Failed to record STT usage: {e}")
            
            return result
        except Exception as e:
            logger.error(f"STT transcription error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def transcribe_audio_file(
        self,
        audio_file_path: str,
        audio_format: Optional[str] = None,
        language: Optional[str] = None,
        user_id: Optional[int] = None,
        user_tier: Optional[UserTier] = None
    ) -> Dict[str, Any]:
        """Transcribe audio file to text
        
        Convenience method that reads audio file and calls transcribe_audio
        """
        if not self._initialized:
            return {
                "success": False,
                "error": "AI Service Manager not initialized"
            }
        
        if not self.groq_stt_client:
            return {
                "success": False,
                "error": "Groq STT client not initialized"
            }
        
        try:
            # Read file size for tier limit estimation
            import os
            file_size = os.path.getsize(audio_file_path)
            
            # Check tier limits if user_id is provided
            if user_id is not None and self._tier_enforcement:
                try:
                    # Estimate duration from file size
                    if audio_format == "wav":
                        estimated_duration = file_size / 10240.0
                    else:
                        estimated_duration = file_size / 1024.0
                    
                    allowed, error_msg, usage_stats = await self._tier_enforcement.check_tier_limit(
                        user_id=user_id,
                        user_tier=user_tier,
                        service_type=TierServiceType.STT,
                        duration_seconds=estimated_duration
                    )
                    
                    if not allowed:
                        return {
                            "success": False,
                            "error": error_msg or "Tier limit exceeded",
                            "usage_stats": usage_stats
                        }
                except Exception as e:
                    logger.warning(f"Tier limit check failed: {e}. Proceeding without tier enforcement.")
            
            result = await self.groq_stt_client.transcribe_audio_file(
                audio_file_path=audio_file_path,
                audio_format=audio_format,
                language=language
            )
            
            # Record usage if successful and user_id is provided
            if result.get("success") and user_id is not None and self._tier_enforcement:
                try:
                    # Get actual duration from metadata if available
                    metadata = result.get("metadata", {})
                    duration = metadata.get("duration", 0.0)
                    if not duration:
                        # Use file size estimate
                        if audio_format == "wav":
                            duration = file_size / 10240.0
                        else:
                            duration = file_size / 1024.0
                    
                    await self._tier_enforcement.record_usage(
                        user_id=user_id,
                        user_tier=user_tier,
                        service_type=TierServiceType.STT,
                        duration_seconds=duration
                    )
                except Exception as e:
                    logger.warning(f"Failed to record STT usage: {e}")
            
            return result
        except Exception as e:
            logger.error(f"STT file transcription error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        if not self._initialized:
            return {
                "initialized": False,
                "error": "AI Service Manager not initialized"
            }
        
        llm_status = self.llm_service_pool.get_service_status() if self.llm_service_pool else {}
        image_status = self.image_generation_service.get_service_status() if self.image_generation_service else {}
        tts_status = self.groq_tts_client.get_metrics() if self.groq_tts_client else {}
        stt_status = self.groq_stt_client.get_metrics() if self.groq_stt_client else {}
        
        return {
            "initialized": self._initialized,
            "llm_service": llm_status,
            "image_generation_service": image_status,
            "tts_service": {
                "initialized": self.groq_tts_client is not None,
                "health_status": tts_status.get("health_status", "unknown"),
                "metrics": tts_status
            },
            "stt_service": {
                "initialized": self.groq_stt_client is not None,
                "health_status": stt_status.get("health_status", "unknown"),
                "metrics": stt_status
            },
            "overall_status": "healthy" if llm_status.get("initialized", False) else "unhealthy"
        }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics for all services"""
        if not self._initialized:
            return {"error": "AI Service Manager not initialized"}
        
        llm_metrics = self.llm_service_pool.get_metrics() if self.llm_service_pool else {}
        image_metrics = self.image_generation_service.get_service_status() if self.image_generation_service else {}
        tts_metrics = self.groq_tts_client.get_metrics() if self.groq_tts_client else {}
        stt_metrics = self.groq_stt_client.get_metrics() if self.groq_stt_client else {}
        
        return {
            "llm_service": llm_metrics,
            "image_generation_service": image_metrics,
            "tts_service": tts_metrics,
            "stt_service": stt_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        if not self._initialized:
            return {
                "healthy": False,
                "error": "AI Service Manager not initialized"
            }
        
        try:
            # Check LLM service health
            llm_status = self.llm_service_pool.get_service_status()
            llm_healthy = llm_status.get("initialized", False)
            
            # Check image generation service health
            image_status = self.image_generation_service.get_service_status()
            image_healthy = image_status.get("initialized", False)
            
            # Check TTS service health
            tts_healthy = False
            tts_status = {}
            if self.groq_tts_client:
                tts_health = await self.groq_tts_client.health_check()
                tts_healthy = tts_health.get("healthy", False)
                tts_status = self.groq_tts_client.get_metrics()
            
            # Check STT service health
            stt_healthy = False
            stt_status = {}
            if self.groq_stt_client:
                stt_health = await self.groq_stt_client.health_check()
                stt_healthy = stt_health.get("healthy", False)
                stt_status = self.groq_stt_client.get_metrics()
            
            overall_healthy = llm_healthy and image_healthy
            
            return {
                "healthy": overall_healthy,
                "llm_service_healthy": llm_healthy,
                "image_generation_healthy": image_healthy,
                "tts_service_healthy": tts_healthy,
                "stt_service_healthy": stt_healthy,
                "services": {
                    "llm": llm_status,
                    "image_generation": image_status,
                    "tts": tts_status,
                    "stt": stt_status
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def get_usage_stats(
        self,
        user_id: int,
        user_tier: Optional[UserTier] = None
    ) -> Dict[str, Any]:
        """Get comprehensive usage statistics for a user
        
        Args:
            user_id: User ID
            user_tier: User's subscription tier (optional, will be fetched if not provided)
        
        Returns:
            Dict with usage statistics and limits
        """
        if not self._initialized:
            return {
                "error": "AI Service Manager not initialized"
            }
        
        if not self._tier_enforcement:
            return {
                "error": "Tier enforcement not initialized"
            }
        
        try:
            stats = await self._tier_enforcement.get_usage_stats(user_id, user_tier)
            return stats
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {
                "error": str(e)
            }

# Global instance
_ai_service_manager: Optional[AIServiceManager] = None

async def get_ai_service_manager() -> AIServiceManager:
    """Get the global AI service manager instance"""
    global _ai_service_manager
    if not _ai_service_manager:
        _ai_service_manager = AIServiceManager()
        await _ai_service_manager.initialize()
    return _ai_service_manager

async def init_ai_service_manager() -> AIServiceManager:
    """Initialize the global AI service manager instance"""
    global _ai_service_manager
    _ai_service_manager = AIServiceManager()
    await _ai_service_manager.initialize()
    return _ai_service_manager
