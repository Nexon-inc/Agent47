from fastapi import Depends, HTTPException, status
from core.authentication.auth_manager import get_current_user
from core.database.models import User, UserTier
from .services.tier_rbac_service import TierRBAC


async def require_posting_allowed(current_user: User = Depends(get_current_user)) -> User:
    try:
        await TierRBAC().assert_can_post(current_user.tier.value)
        await TierRBAC().assert_tokens(current_user.id)
        return current_user
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


async def require_team_allowed(current_user: User = Depends(get_current_user)) -> User:
    try:
        await TierRBAC().assert_team_features(current_user.tier.value)
        return current_user
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


