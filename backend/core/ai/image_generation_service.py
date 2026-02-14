"""
Image Generation Service

This module provides image generation capabilities using Google Gemini models.
Tier-based model selection:
- Pro tier: Gemini 3 Pro Image Preview (4K resolution, professional quality)
- Starter tier: Gemini 2.5 Flash Image (1024px, fast generation)
- Free tier: Image generation disabled
"""

import asyncio
import aiohttp
import logging
import base64
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..config import settings
from ..logs import get_logger
from ..database.models import UserTier

logger = get_logger(__name__)

class ImageGenerationStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    DISABLED = "disabled"
    RATE_LIMITED = "rate_limited"
    DAILY_LIMIT_EXCEEDED = "daily_limit_exceeded"

@dataclass
class ImageGenerationRequest:
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 1024
    height: int = 1024
    num_images: int = 1
    steps: int = 20
    guidance_scale: float = 7.5
    seed: Optional[int] = None
    style: Optional[str] = None

@dataclass
class ImageGenerationResponse:
    success: bool
    images: Optional[List[str]] = None  # Base64 encoded images or URLs
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status: ImageGenerationStatus = ImageGenerationStatus.FAILED
    response_time_ms: Optional[int] = None
    daily_requests: Optional[int] = None
    daily_limit: Optional[int] = None

class GoogleGeminiImageClient:
    """Google Gemini Image Generation Client"""
    
    def __init__(self):
        self.api_key = settings.google_gemini_image.google_gemini_api_key
        self.api_base_url = settings.google_gemini_image.google_gemini_api_base_url
        self.pro_model = settings.google_gemini_image.google_gemini_pro_model
        self.flash_model = settings.google_gemini_image.google_gemini_flash_model
        self.timeout = settings.google_gemini_image.google_gemini_request_timeout
        self.max_retries = settings.google_gemini_image.google_gemini_max_retries
        self.retry_delay = settings.google_gemini_image.google_gemini_retry_delay
        self.session = None
        self._health_status = "unknown"
        self._last_health_check = 0
        self._concurrent_requests = 0
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
    
    async def initialize(self):
        """Initialize HTTP session and verify Google Gemini service connection"""
        try:
            if not self.api_key:
                raise Exception("Google Gemini API key not configured")
            
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Agent47-Google-Gemini-Image-Client/1.0"
                }
            )
            
            # Test connection
            health_result = await self.health_check()
            if health_result["healthy"]:
                self._health_status = "healthy"
                logger.info("Google Gemini Image Generation client initialized successfully")
                return True
            else:
                raise Exception(f"Google Gemini image service health check failed: {health_result['error']}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Google Gemini Image Generation client: {e}")
            self._health_status = "unhealthy"
            raise
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health and availability"""
        current_time = datetime.utcnow().timestamp()
        
        # Check if we need to perform health check
        if current_time - self._last_health_check < settings.google_gemini_image.google_gemini_health_check_interval:
            return {
                "healthy": self._health_status == "healthy",
                "status": self._health_status
            }
        
        try:
            if not self.session:
                await self.initialize()
            
            # Simple test request to list models endpoint
            start_time = datetime.utcnow().timestamp()
            async with self.session.get(
                f"{self.api_base_url}/models?key={self.api_key}"
            ) as response:
                response_time = int((datetime.utcnow().timestamp() - start_time) * 1000)
                
                if response.status == 200:
                    self._health_status = "healthy"
                    self._last_health_check = current_time
                    return {
                        "healthy": True,
                        "status": "healthy",
                        "response_time_ms": response_time
                    }
                else:
                    self._health_status = "unhealthy"
                    error_text = await response.text()
                    return {
                        "healthy": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "response_time_ms": response_time
                    }
                    
        except Exception as e:
            self._health_status = "unhealthy"
            self._last_health_check = current_time
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def generate_image(
        self, 
        request: ImageGenerationRequest, 
        user_tier: Optional[UserTier] = None
    ) -> ImageGenerationResponse:
        """Generate image using Google Gemini
        
        Args:
            request: Image generation request
            user_tier: User tier to determine which model to use
                - PRO: Gemini 3 Pro Image Preview (4K resolution)
                - STARTER: Gemini 2.5 Flash Image (1024px)
                - FREE: Returns error (image generation disabled)
        """
        try:
            # Check if user has access to image generation
            if user_tier == UserTier.FREE:
                return ImageGenerationResponse(
                    success=False,
                    error="Image generation is not available for Free tier users. Please upgrade to Starter or Pro tier.",
                    status=ImageGenerationStatus.DISABLED
                )
            
            # Check health
            health = await self.health_check()
            if not health["healthy"]:
                return ImageGenerationResponse(
                    success=False,
                    error=f"Service unhealthy: {health.get('error', 'Unknown error')}",
                    status=ImageGenerationStatus.FAILED
                )
            
            if not self.session:
                await self.initialize()
            
            # Select model based on tier
            if user_tier == UserTier.PRO:
                model = self.pro_model
                max_width = settings.google_gemini_image.google_gemini_max_width
                max_height = settings.google_gemini_image.google_gemini_max_height
            else:  # STARTER
                model = self.flash_model
                max_width = settings.google_gemini_image.google_gemini_flash_max_width
                max_height = settings.google_gemini_image.google_gemini_flash_max_height
            
            # Clamp dimensions to model limits
            width = min(request.width, max_width)
            height = min(request.height, max_height)
            
            # Prepare request payload for Google Gemini Image Generation API
            # Google Gemini uses generateContent API with image generation parameters
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"Generate an image: {request.prompt}"
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 8192
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            # Add image generation parameters
            # Note: Google Gemini image generation parameters may vary by model
            image_config = {
                "width": width,
                "height": height
            }
            if request.negative_prompt:
                image_config["negativePrompt"] = request.negative_prompt
            if request.seed:
                image_config["seed"] = request.seed
            if request.style:
                image_config["style"] = request.style
            
            # Add image config to generation config
            payload["generationConfig"]["imageConfig"] = image_config
            
            # Make request with retries
            for attempt in range(self.max_retries + 1):
                try:
                    start_time = datetime.utcnow().timestamp()
                    self._concurrent_requests += 1
                    self._total_requests += 1
                    
                    # Google Gemini image generation endpoint
                    # Note: The actual endpoint format may need adjustment based on Google's API documentation
                    url = f"{self.api_base_url}/models/{model}:generateContent?key={self.api_key}"
                    
                    async with self.session.post(url, json=payload) as response:
                        response_time = int((datetime.utcnow().timestamp() - start_time) * 1000)
                        
                        if response.status == 200:
                            result = await response.json()
                            self._successful_requests += 1
                            
                            # Extract images from Google Gemini response
                            images = []
                            if "candidates" in result and len(result["candidates"]) > 0:
                                candidate = result["candidates"][0]
                                if "content" in candidate and "parts" in candidate["content"]:
                                    for part in candidate["content"]["parts"]:
                                        if "inlineData" in part and "data" in part["inlineData"]:
                                            # Image is base64 encoded
                                            images.append(part["inlineData"]["data"])
                            
                            if not images:
                                return ImageGenerationResponse(
                                    success=False,
                                    error="No images generated in response",
                                    status=ImageGenerationStatus.FAILED,
                                    response_time_ms=response_time
                                )
                            
                            return ImageGenerationResponse(
                                success=True,
                                images=images,
                                metadata={
                                    "model": model,
                                    "prompt": request.prompt,
                                    "width": width,
                                    "height": height,
                                    "user_tier": user_tier.value if user_tier else None
                                },
                                status=ImageGenerationStatus.SUCCESS,
                                response_time_ms=response_time
                            )
                        elif response.status == 429:  # Rate limit
                            if attempt < self.max_retries:
                                await asyncio.sleep(self.retry_delay * (2 ** attempt))
                                continue
                            else:
                                return ImageGenerationResponse(
                                    success=False,
                                    error="Rate limit exceeded",
                                    status=ImageGenerationStatus.RATE_LIMITED,
                                    response_time_ms=response_time
                                )
                        else:
                            error_text = await response.text()
                            return ImageGenerationResponse(
                                success=False,
                                error=f"HTTP {response.status}: {error_text}",
                                status=ImageGenerationStatus.FAILED,
                                response_time_ms=response_time
                            )
                            
                except asyncio.TimeoutError:
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    else:
                        return ImageGenerationResponse(
                            success=False,
                            error="Request timeout",
                            status=ImageGenerationStatus.FAILED
                        )
                except Exception as e:
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    else:
                        return ImageGenerationResponse(
                            success=False,
                            error=str(e),
                            status=ImageGenerationStatus.FAILED
                        )
                finally:
                    self._concurrent_requests -= 1
            
            return ImageGenerationResponse(
                success=False,
                error="Max retries exceeded",
                status=ImageGenerationStatus.FAILED
            )
            
        except Exception as e:
            self._failed_requests += 1
            logger.error(f"Google Gemini image generation error: {e}")
            return ImageGenerationResponse(
                success=False,
                error=str(e),
                status=ImageGenerationStatus.FAILED
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        return {
            "health_status": self._health_status,
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "failed_requests": self._failed_requests,
            "concurrent_requests": self._concurrent_requests,
            "success_rate": (self._successful_requests / self._total_requests * 100) if self._total_requests > 0 else 0
        }

class ImageGenerationService:
    """Centralized image generation service using Google Gemini"""
    
    def __init__(self):
        self.gemini_client: Optional[GoogleGeminiImageClient] = None
        self._initialized = False
        self._enabled = True
    
    async def initialize(self) -> bool:
        """Initialize the image generation service"""
        try:
            logger.info("Initializing Image Generation Service with Google Gemini...")
            
            if not settings.google_gemini_image.google_gemini_api_key:
                logger.warning("Google Gemini API key not configured. Image generation will be disabled.")
                self._enabled = False
                self._initialized = True
                return True
            
            # Initialize Google Gemini client
            self.gemini_client = GoogleGeminiImageClient()
            await self.gemini_client.initialize()
            
            self._initialized = True
            logger.info("Image Generation Service initialized successfully with Google Gemini")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Image Generation Service: {e}")
            self._enabled = False
            self._initialized = True  # Mark as initialized but disabled
            return True  # Return True to not block startup
    
    async def close(self):
        """Close the image generation service"""
        if self.gemini_client:
            await self.gemini_client.close()
        self._initialized = False
    
    def set_enabled(self, enabled: bool):
        """Enable or disable image generation"""
        self._enabled = enabled
        logger.info(f"Image generation {'enabled' if enabled else 'disabled'}")
    
    def is_enabled(self) -> bool:
        """Check if image generation is enabled"""
        return self._enabled and self._initialized
    
    async def generate_image(
        self, 
        request: ImageGenerationRequest,
        user_tier: Optional[UserTier] = None
    ) -> ImageGenerationResponse:
        """Generate image using Google Gemini with tier-based model selection
        
        Args:
            request: Image generation request
            user_tier: User tier (FREE, STARTER, PRO) to determine model and access
        """
        if not self._enabled:
            return ImageGenerationResponse(
                success=False,
                error="Image generation is disabled",
                status=ImageGenerationStatus.DISABLED
            )
        
        if not self._initialized:
            return ImageGenerationResponse(
                success=False,
                error="Image Generation Service not initialized",
                status=ImageGenerationStatus.FAILED
            )
        
        if not self.gemini_client:
            return ImageGenerationResponse(
                success=False,
                error="Google Gemini client not initialized",
                status=ImageGenerationStatus.FAILED
            )
        
        # Generate image using Google Gemini with tier-based model selection
        return await self.gemini_client.generate_image(request, user_tier)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "initialized": self._initialized,
            "enabled": self._enabled,
            "gemini_client": self.gemini_client.get_metrics() if self.gemini_client else None
        }

# Global instance and lock for thread-safe initialization
_image_generation_service: Optional[ImageGenerationService] = None
_image_gen_lock = asyncio.Lock()

async def get_image_generation_service() -> ImageGenerationService:
    """Get the global image generation service instance with thread-safe initialization"""
    global _image_generation_service
    if not _image_generation_service:
        async with _image_gen_lock:
            if not _image_generation_service:
                _image_generation_service = ImageGenerationService()
                await _image_generation_service.initialize()
    return _image_generation_service

async def init_image_generation_service() -> ImageGenerationService:
    """Initialize the global image generation service instance with thread-safe initialization"""
    global _image_generation_service
    async with _image_gen_lock:
        if not _image_generation_service:
            _image_generation_service = ImageGenerationService()
            await _image_generation_service.initialize()
    return _image_generation_service
