"""
Groq Tier Enforcement Utilities

Helper functions for agent services to easily integrate tier-based usage enforcement.
"""

from typing import Optional, Dict
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..authentication.auth_manager import get_current_user
from ..database.models import User, UserTier
from ..database.connection import get_db


async def get_user_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> tuple[int, Optional[UserTier]]:
    """Get user context (user_id and tier) for tier enforcement
    
    Usage in FastAPI routes:
        @router.post("/endpoint")
        async def my_endpoint(
            user_context: tuple[int, Optional[UserTier]] = Depends(get_user_context)
        ):
            user_id, user_tier = user_context
            # Use user_id and user_tier with AI Service Manager
    """
    return current_user.id, current_user.tier


async def check_tier_limit_before_request(
    user_id: int,
    user_tier: Optional[UserTier],
    service_type: str,
    estimated_tokens: int = 0,
    estimated_duration_seconds: float = 0.0
) -> tuple[bool, Optional[str], Optional[Dict]]:
    """Check tier limit before making an API request
    
    This is a convenience function that can be called before using AI services.
    
    Args:
        user_id: User ID
        user_tier: User's subscription tier
        service_type: "llm", "tts", or "stt"
        estimated_tokens: Estimated tokens (for LLM)
        estimated_duration_seconds: Estimated duration (for TTS/STT)
    
    Returns:
        Tuple of (allowed, error_message, usage_stats)
    """
    try:
        from .groq_tier_enforcement import get_groq_tier_enforcement, ServiceType as TierServiceType
        
        tier_enforcement = await get_groq_tier_enforcement()
        
        # Map service type string to enum
        service_type_map = {
            "llm": TierServiceType.LLM,
            "tts": TierServiceType.TTS,
            "stt": TierServiceType.STT
        }
        
        tier_service_type = service_type_map.get(service_type.lower())
        if not tier_service_type:
            return True, None, None  # Unknown service type, allow
        
        allowed, error_msg, usage_stats = await tier_enforcement.check_tier_limit(
            user_id=user_id,
            user_tier=user_tier,
            service_type=tier_service_type,
            tokens=estimated_tokens,
            duration_seconds=estimated_duration_seconds
        )
        
        return allowed, error_msg, usage_stats
        
    except Exception:
        # If tier enforcement fails, allow the request (fail open)
        return True, None, None


def raise_if_tier_limit_exceeded(
    allowed: bool,
    error_msg: Optional[str],
    status_code: int = 429
) -> None:
    """Raise HTTPException if tier limit is exceeded
    
    Usage:
        allowed, error_msg, _ = await check_tier_limit_before_request(...)
        raise_if_tier_limit_exceeded(allowed, error_msg)
    """
    if not allowed and error_msg:
        raise HTTPException(
            status_code=status_code,
            detail=error_msg
        )
