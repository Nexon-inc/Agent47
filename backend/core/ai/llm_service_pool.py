"""
LLM Service Pool Manager

This module provides a centralized LLM service pool with automatic failover
between Ollama Llama 3 8B (primary) and OpenAI (fallback).
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from ..config import settings
from ..utils.nlp_utils import OllamaLLMClient
from .groq_client import GroqLLMClient
from ..logs import get_logger

logger = get_logger(__name__)

class LLMServiceStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    RATE_LIMITED = "rate_limited"
    DAILY_LIMIT_EXCEEDED = "daily_limit_exceeded"
    UNKNOWN = "unknown"

@dataclass
class LLMServiceMetrics:
    service_name: str
    status: LLMServiceStatus
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    daily_requests: int = 0
    daily_limit: int = 0
    last_health_check: Optional[datetime] = None
    response_time_avg: float = 0.0
    error_rate: float = 0.0

@dataclass
class LLMRequest:
    messages: List[Dict[str, str]]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stream: bool = False
    require_image_generation: bool = False

@dataclass
class LLMResponse:
    success: bool
    content: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    model_used: Optional[str] = None
    service_used: Optional[str] = None
    response_time_ms: Optional[int] = None
    error: Optional[str] = None
    fallback_used: bool = False
    image_generation_disabled: bool = False

class LLMServicePool:
    """Centralized LLM service pool with automatic failover"""
    
    def __init__(self):
        # Groq client (primary)
        self.groq_client: Optional[GroqLLMClient] = None
        # Ollama client for Llama 3 8B (fallback)
        self.ollama_client: Optional[OllamaLLMClient] = None
        self._initialized = False
        # Use configured primary LLM provider
        self._current_primary = settings.primary_llm_provider
        self._fallback_active = False
        self._image_generation_enabled = True
        self._metrics: Dict[str, LLMServiceMetrics] = {}
        self._last_health_check = datetime.utcnow()
        
        # Initialize metrics
        self._metrics["groq"] = LLMServiceMetrics(
            service_name="groq",
            status=LLMServiceStatus.UNKNOWN,
            daily_limit=settings.groq.groq_rate_limit_per_day
        )
        self._metrics["openai"] = LLMServiceMetrics(
            service_name="openai",
            status=LLMServiceStatus.UNKNOWN,
            daily_limit=1000000
        )
        self._metrics["ollama"] = LLMServiceMetrics(
            service_name="ollama",
            status=LLMServiceStatus.UNKNOWN,
            daily_limit=100000  # Ollama has no daily limit
        )
    
    async def initialize(self) -> bool:
        """Initialize the LLM service pool"""
        try:
            logger.info("Initializing LLM Service Pool...")
            
            # Initialize Groq client (primary)
            try:
                self.groq_client = GroqLLMClient()
                await self.groq_client.initialize()
                logger.info("Groq LLM client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}. Will use fallback.")
                self.groq_client = None
            
            # Initialize Ollama LLM client with Llama 3 8B (fallback)
            try:
                self.ollama_client = OllamaLLMClient()
                await self.ollama_client.initialize()
                logger.info("Ollama LLM client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama client: {e}")
                self.ollama_client = None
            
            # Perform initial health checks
            await self._perform_health_checks()
            
            # Start background health monitoring
            asyncio.create_task(self._health_monitoring_loop())
            
            self._initialized = True
            logger.info("LLM Service Pool initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM Service Pool: {e}")
            return False
    
    async def close(self):
        """Close all LLM clients"""
        if self.groq_client:
            await self.groq_client.close()
        if self.ollama_client:
            await self.ollama_client.close()
        self._initialized = False
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using the best available LLM service"""
        if not self._initialized:
            return LLMResponse(
                success=False,
                error="LLM Service Pool not initialized"
            )
        
        # Check if image generation is required and available
        if request.require_image_generation and not self._image_generation_enabled:
            return LLMResponse(
                success=False,
                error="Image generation is disabled (Grok fallback active)",
                image_generation_disabled=True
            )
        
        # Try primary service first, then fallback services
        if self._current_primary == "groq" and self._is_service_healthy("groq"):
            response = await self._try_groq_generation(request)
            if response.success:
                return response
            else:
                logger.warning(f"Groq LLM failed: {response.error}")
                # Try Ollama fallback
                if self._is_service_healthy("ollama"):
                    response = await self._try_ollama_generation(request)
                    if response.success:
                        response.fallback_used = True
                        return response
                # Try OpenAI fallback
                if self._is_service_healthy("openai"):
                    response = await self._try_openai_generation(request)
                    if response.success:
                        response.fallback_used = True
                        return response
        elif self._current_primary == "ollama" and self._is_service_healthy("ollama"):
            response = await self._try_ollama_generation(request)
            if response.success:
                return response
            else:
                logger.warning(f"Ollama LLM failed: {response.error}")
                # Try Groq fallback
                if self._is_service_healthy("groq"):
                    response = await self._try_groq_generation(request)
                    if response.success:
                        response.fallback_used = True
                        return response
                # Try OpenAI fallback
                if self._is_service_healthy("openai"):
                    response = await self._try_openai_generation(request)
                    if response.success:
                        response.fallback_used = True
                        return response
        elif self._current_primary == "grok" and self._is_service_healthy("ollama"):
            # Legacy "grok" provider name maps to Ollama
            response = await self._try_ollama_generation(request)
            if response.success:
                return response
            else:
                logger.warning(f"Ollama LLM failed: {response.error}")
                # Try Groq fallback
                if self._is_service_healthy("groq"):
                    response = await self._try_groq_generation(request)
                    if response.success:
                        response.fallback_used = True
                        return response
                # Try OpenAI fallback
                if self._is_service_healthy("openai"):
                    response = await self._try_openai_generation(request)
                    if response.success:
                        response.fallback_used = True
                        return response
        elif self._current_primary == "openai" and self._is_service_healthy("openai"):
            response = await self._try_openai_generation(request)
            if response.success:
                return response
            else:
                logger.warning(f"OpenAI failed: {response.error}")
                # Try Groq fallback
                if self._is_service_healthy("groq"):
                    response = await self._try_groq_generation(request)
                    if response.success:
                        response.fallback_used = True
                        return response
                # Try Ollama fallback
                if self._is_service_healthy("ollama"):
                    response = await self._try_ollama_generation(request)
                    if response.success:
                        response.fallback_used = True
                        return response
        
        # All services failed
        return LLMResponse(
            success=False,
            error="All LLM services are unavailable"
        )
    
    # Chutes generation method removed

    async def _try_openai_generation(self, request: LLMRequest) -> LLMResponse:
        """Try to generate text using OpenAI (first priority)"""
        try:
            import openai
            api_key = settings.openai.openai_api_key
            if not api_key:
                return LLMResponse(success=False, error="OpenAI API key not configured")

            client = openai.OpenAI(api_key=api_key, base_url=settings.openai.openai_api_base or None)

            start = datetime.utcnow()
            completion = client.chat.completions.create(
                model=settings.openai.openai_default_model,
                messages=request.messages,  # type: ignore
                max_tokens=request.max_tokens or 16000,
                temperature=request.temperature or 0.7,
                top_p=request.top_p or 0.9,
                frequency_penalty=request.frequency_penalty or 0.0,
                presence_penalty=request.presence_penalty or 0.0,
                stream=False
            )

            text = completion.choices[0].message.content if completion.choices else ""
            elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)

            # Update metrics
            self._update_service_metrics("openai", {"success": True, "response_time_ms": elapsed})

            return LLMResponse(
                success=True,
                content=text,
                usage=getattr(completion, "usage", None),
                model_used=settings.openai.openai_default_model,
                service_used="openai",
                response_time_ms=elapsed
            )
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            # Update metrics with failure
            self._update_service_metrics("openai", {"success": False, "error": str(e)})
            return LLMResponse(success=False, error=str(e))
    
    async def _try_groq_generation(self, request: LLMRequest) -> LLMResponse:
        """Try to generate text using Groq API"""
        try:
            if not self.groq_client:
                return LLMResponse(success=False, error="Groq client not initialized")
            
            result = await self.groq_client.generate_text(
                messages=request.messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p
            )
            
            # Update metrics
            self._update_service_metrics("groq", result)
            
            if result.get("success"):
                content = result.get("content") or result.get("text", "")
                return LLMResponse(
                    success=True,
                    content=content,
                    usage=result.get("usage"),
                    model_used=result.get("model", settings.groq.groq_default_model),
                    service_used="groq",
                    response_time_ms=result.get("response_time_ms")
                )
            else:
                return LLMResponse(
                    success=False,
                    error=result.get("error", "Unknown error")
                )
                
        except Exception as e:
            logger.error(f"Groq LLM generation error: {e}")
            return LLMResponse(
                success=False,
                error=str(e)
            )
    
    async def _try_ollama_generation(self, request: LLMRequest) -> LLMResponse:
        """Try to generate text using Ollama LLM"""
        try:
            if not self.ollama_client:
                return LLMResponse(success=False, error="Ollama client not initialized")
            
            result = await self.ollama_client.generate_text(
                messages=request.messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=request.stream
            )
            
            # Update metrics
            self._update_service_metrics("ollama", result)
            
            if result.get("success"):
                # Ollama returns both "text" and "content" for compatibility
                content = result.get("content") or result.get("text", "")
                return LLMResponse(
                    success=True,
                    content=content,
                    usage=result.get("usage"),
                    model_used=result.get("model", "llama3:8b"),
                    service_used="ollama",
                    response_time_ms=result.get("response_time_ms")
                )
            else:
                return LLMResponse(
                    success=False,
                    error=result.get("error", "Unknown error")
                )
                
        except Exception as e:
            logger.error(f"Ollama LLM generation error: {e}")
            return LLMResponse(
                success=False,
                error=str(e)
            )
    
    async def _activate_fallback(self):
        """Activate Grok LLM as fallback and disable image generation"""
        if not self._fallback_active:
            self._fallback_active = True
            self._image_generation_enabled = False
            logger.warning("Activated Grok LLM fallback - Image generation disabled")
    
    async def _deactivate_fallback(self):
        """Deactivate fallback and re-enable image generation"""
        if self._fallback_active:
            self._fallback_active = False
            self._image_generation_enabled = True
            logger.info("Deactivated Grok LLM fallback - Image generation re-enabled")
    
    def _is_service_healthy(self, service_name: str) -> bool:
        """Check if a service is healthy"""
        metrics = self._metrics.get(service_name)
        if not metrics:
            return False
        
        return metrics.status in [LLMServiceStatus.HEALTHY, LLMServiceStatus.RATE_LIMITED]
    
    def _update_service_metrics(self, service_name: str, result: Dict[str, Any]):
        """Update service metrics based on result"""
        metrics = self._metrics.get(service_name)
        if not metrics:
            return
        
        metrics.total_requests += 1
        
        if result["success"]:
            metrics.successful_requests += 1
            metrics.status = LLMServiceStatus.HEALTHY
        else:
            metrics.failed_requests += 1
            error = result.get("error", "")
            
            if "rate limit" in error.lower():
                metrics.status = LLMServiceStatus.RATE_LIMITED
            elif "daily limit" in error.lower():
                metrics.status = LLMServiceStatus.DAILY_LIMIT_EXCEEDED
            else:
                metrics.status = LLMServiceStatus.UNHEALTHY
        
        # Update daily requests if available (Groq returns this in success response)
        if "daily_requests" in result:
            metrics.daily_requests = result["daily_requests"]
        
        # Update response time
        if "response_time_ms" in result:
            if metrics.response_time_avg == 0:
                metrics.response_time_avg = result["response_time_ms"]
            else:
                metrics.response_time_avg = (metrics.response_time_avg + result["response_time_ms"]) / 2
        
        # Update error rate
        metrics.error_rate = (metrics.failed_requests / metrics.total_requests * 100) if metrics.total_requests > 0 else 0
    
    async def _perform_health_checks(self):
        """Perform health checks on all services"""
        try:
            # Check Groq API
            if self.groq_client:
                groq_health = await self.groq_client.health_check()
                if groq_health.get("healthy", False):
                    self._metrics["groq"].status = LLMServiceStatus.HEALTHY
                elif "rate limit" in groq_health.get("error", "").lower():
                    self._metrics["groq"].status = LLMServiceStatus.RATE_LIMITED
                else:
                    self._metrics["groq"].status = LLMServiceStatus.UNHEALTHY
                self._metrics["groq"].last_health_check = datetime.utcnow()
            else:
                self._metrics["groq"].status = LLMServiceStatus.UNHEALTHY
                self._metrics["groq"].last_health_check = datetime.utcnow()
            
            # OpenAI health is assumed healthy if API key exists
            if settings.openai.openai_api_key:
                self._metrics["openai"].status = LLMServiceStatus.HEALTHY
                self._metrics["openai"].last_health_check = datetime.utcnow()
            else:
                self._metrics["openai"].status = LLMServiceStatus.UNHEALTHY
                self._metrics["openai"].last_health_check = datetime.utcnow()
            
            # Check Ollama LLM
            if self.ollama_client:
                ollama_health = await self.ollama_client.health_check()
                self._metrics["ollama"].status = LLMServiceStatus.HEALTHY if ollama_health.get("healthy", False) else LLMServiceStatus.UNHEALTHY
                self._metrics["ollama"].last_health_check = datetime.utcnow()
            else:
                self._metrics["ollama"].status = LLMServiceStatus.UNHEALTHY
                self._metrics["ollama"].last_health_check = datetime.utcnow()
            
            self._last_health_check = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
    
    async def _health_monitoring_loop(self):
        """Background health monitoring loop"""
        while self._initialized:
            try:
                await asyncio.sleep(60)  # Default health check interval
                await self._perform_health_checks()
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "initialized": self._initialized,
            "primary_service": self._current_primary,
            "fallback_active": self._fallback_active,
            "image_generation_enabled": self._image_generation_enabled,
            "last_health_check": self._last_health_check.isoformat(),
            "services": {
                name: {
                    "status": metrics.status.value,
                    "total_requests": metrics.total_requests,
                    "successful_requests": metrics.successful_requests,
                    "failed_requests": metrics.failed_requests,
                    "daily_requests": metrics.daily_requests,
                    "daily_limit": metrics.daily_limit,
                    "error_rate": metrics.error_rate,
                    "response_time_avg": metrics.response_time_avg,
                    "last_health_check": metrics.last_health_check.isoformat() if metrics.last_health_check else None
                }
                for name, metrics in self._metrics.items()
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics for all services"""
        return self.get_service_status()

# Global instance
_llm_service_pool: Optional[LLMServicePool] = None

async def get_llm_service_pool() -> LLMServicePool:
    """Get the global LLM service pool instance"""
    global _llm_service_pool
    if not _llm_service_pool:
        _llm_service_pool = LLMServicePool()
        await _llm_service_pool.initialize()
    return _llm_service_pool

async def init_llm_service_pool() -> LLMServicePool:
    """Initialize the global LLM service pool instance"""
    global _llm_service_pool
    _llm_service_pool = LLMServicePool()
    await _llm_service_pool.initialize()
    return _llm_service_pool
