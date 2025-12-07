from typing import List
from backend.core.database.models import UserTier
from backend.core.billing.usage_tracker import get_usage_tracker


class TierRBAC:
    async def assert_can_post(self, user_tier: str):
        if user_tier == UserTier.FREE.value:
            raise PermissionError("posting_not_allowed_on_free")

    async def assert_team_features(self, user_tier: str):
        if user_tier != UserTier.PRO.value:
            raise PermissionError("team_collaboration_pro_only")

    async def assert_tokens(self, user_id: int):
        ut = await get_usage_tracker()
        limits = await ut.check_usage_limits(user_id)
        if not limits.get("within_limits", True):
            raise PermissionError("usage_limits_exceeded")


