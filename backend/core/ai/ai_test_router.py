"""
AI Service Test Router

This module provides test endpoints for the new AI service integration.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
import logging

from ..authentication.auth_router import get_current_active_user
from ..database.models import User
from .ai_service_manager import get_ai_service_manager, UnifiedAIRequest
from .llm_service_pool import LLMRequest
from .image_generation_service import ImageGenerationRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Services"])

@router.get("/status")
async def get_ai_service_status(current_user: User = Depends(get_current_active_user)):
    """Get AI service status and health"""
    try:
        ai_manager = await get_ai_service_manager()
        status = await ai_manager.get_service_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get AI service status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_ai_service_metrics(current_user: User = Depends(get_current_active_user)):
    """Get AI service metrics"""
    try:
        ai_manager = await get_ai_service_manager()
        metrics = await ai_manager.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get AI service metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/text")
async def test_text_generation(
    prompt: str,
    max_tokens: Optional[int] = 500,
    temperature: Optional[float] = 0.7,
    current_user: User = Depends(get_current_active_user)
):
    """Test text generation with the new AI service"""
    try:
        ai_manager = await get_ai_service_manager()
        
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ]
        
        response = await ai_manager.generate_text(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return {
            "success": response.success,
            "content": response.text_content,
            "service_used": response.service_used,
            "fallback_used": response.fallback_used,
            "response_time_ms": response.response_time_ms,
            "error": response.error
        }
        
    except Exception as e:
        logger.error(f"Text generation test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/image")
async def test_image_generation(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    current_user: User = Depends(get_current_active_user)
):
    """Test image generation with the new AI service"""
    try:
        ai_manager = await get_ai_service_manager()
        
        response = await ai_manager.generate_image(
            prompt=prompt,
            width=width,
            height=height
        )
        
        return {
            "success": response.success,
            "images": response.images,
            "service_used": response.service_used,
            "response_time_ms": response.response_time_ms,
            "error": response.error
        }
        
    except Exception as e:
        logger.error(f"Image generation test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/combined")
async def test_combined_generation(
    text_prompt: str,
    image_prompt: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Test combined text and image generation"""
    try:
        ai_manager = await get_ai_service_manager()
        
        request = UnifiedAIRequest(
            text_prompt=text_prompt,
            image_prompt=image_prompt
        )
        
        results = await ai_manager.generate_combined(request)
        
        return {
            "success": True,
            "results": {
                "text": {
                    "success": results.get("text", {}).success if "text" in results else False,
                    "content": results.get("text", {}).text_content if "text" in results else None,
                    "service_used": results.get("text", {}).service_used if "text" in results else None,
                    "fallback_used": results.get("text", {}).fallback_used if "text" in results else False,
                    "error": results.get("text", {}).error if "text" in results else None
                },
                "image": {
                    "success": results.get("image", {}).success if "image" in results else False,
                    "images": results.get("image", {}).images if "image" in results else None,
                    "service_used": results.get("image", {}).service_used if "image" in results else None,
                    "error": results.get("image", {}).error if "image" in results else None
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Combined generation test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check for AI services"""
    try:
        ai_manager = await get_ai_service_manager()
        health = await ai_manager.health_check()
        return health
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e)
        }
