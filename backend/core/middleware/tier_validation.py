from fastapi import HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from ..database import get_database
from ..database.models import User, UserTier
from ..authentication.auth_manager import get_current_active_user

logger = logging.getLogger(__name__)

class TierValidationError(HTTPException):
    def __init__(self, detail: str = "Tier selection required"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

async def require_tier_selection(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Middleware to ensure user has selected a tier before accessing protected resources.
    Raises TierValidationError if no tier is selected.
    """
    if current_user.tier is None:
        logger.warning(f"User {current_user.id} attempted to access protected resource without tier selection")
        raise TierValidationError("You must select a subscription tier before accessing this feature")
    
    return current_user

async def require_minimum_tier(required_tier: UserTier, current_user: User = Depends(get_current_active_user)) -> User:
    """
    Middleware to ensure user has at least the required tier level.
    """
    if current_user.tier is None:
        raise TierValidationError("You must select a subscription tier before accessing this feature")
    
    tier_hierarchy = {
        UserTier.FREE: 0,
        UserTier.STARTER: 1,
        UserTier.PRO: 2
    }
    
    user_tier_level = tier_hierarchy.get(current_user.tier, 0)
    required_tier_level = tier_hierarchy.get(required_tier, 0)
    
    if user_tier_level < required_tier_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This feature requires {required_tier.value} tier or higher. Your current tier: {current_user.tier.value if current_user.tier else 'None'}"
        )
    
    return current_user

async def require_pro_tier(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Middleware specifically for PRO tier features.
    """
    return await require_minimum_tier(UserTier.PRO, current_user)

async def require_starter_tier(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Middleware specifically for STARTER tier features.
    """
    return await require_minimum_tier(UserTier.STARTER, current_user)

def create_tier_redirect_response(redirect_url: str = "/pricing") -> RedirectResponse:
    """
    Creates a redirect response to tier selection page.
    """
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
