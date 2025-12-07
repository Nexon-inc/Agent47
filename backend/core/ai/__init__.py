"""
AI Services Module

This module provides centralized AI services including LLM text generation
and image generation with Grok LLM as primary and OpenAI as fallback.
"""

from .llm_service_pool import (
    LLMServicePool,
    LLMRequest,
    LLMResponse,
    LLMServiceStatus,
    LLMServiceMetrics,
    get_llm_service_pool,
    init_llm_service_pool
)

from .image_generation_service import (
    ImageGenerationService,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageGenerationStatus,
    # ChutesImageGenerationClient removed
    get_image_generation_service,
    init_image_generation_service
)

from .ai_service_manager import (
    AIServiceManager,
    UnifiedAIRequest,
    UnifiedAIResponse,
    get_ai_service_manager,
    init_ai_service_manager
)

__all__ = [
    # LLM Service Pool
    "LLMServicePool",
    "LLMRequest", 
    "LLMResponse",
    "LLMServiceStatus",
    "LLMServiceMetrics",
    "get_llm_service_pool",
    "init_llm_service_pool",
    
    # Image Generation Service
    "ImageGenerationService",
    "ImageGenerationRequest",
    "ImageGenerationResponse", 
    "ImageGenerationStatus",
    # "ChutesImageGenerationClient" removed
    "get_image_generation_service",
    "init_image_generation_service",
    
    # AI Service Manager
    "AIServiceManager",
    "UnifiedAIRequest",
    "UnifiedAIResponse",
    "get_ai_service_manager",
    "init_ai_service_manager"
]
