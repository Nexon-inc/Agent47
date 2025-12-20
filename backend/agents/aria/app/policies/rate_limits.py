from typing import Optional
from datetime import timedelta
from core.cache.redis_manager import get_redis


class RateLimiter:
    def __init__(self, feature: str, max_per_minute: int):
        self.feature = feature
        self.max_per_minute = max_per_minute
        self.redis = None

    async def initialize(self):
        self.redis = await get_redis()

    async def allow(self, tenant_id: str, key: Optional[str] = None) -> bool:
        rk = f"rl:{tenant_id}:{self.feature}:{key or 'global'}"
        current = await self.redis.increment(rk)
        if current == 1:
            await self.redis.expire(rk, timedelta(minutes=1))
        return current <= self.max_per_minute


