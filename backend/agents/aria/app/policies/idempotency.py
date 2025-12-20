from datetime import timedelta
from core.cache.redis_manager import get_redis


class Idempotency:
    def __init__(self, prefix: str, ttl_minutes: int = 2880):
        self.prefix = prefix
        self.ttl = timedelta(minutes=ttl_minutes)
        self.redis = None

    async def initialize(self):
        self.redis = await get_redis()

    async def check_and_set(self, key: str) -> bool:
        rk = f"idem:{self.prefix}:{key}"
        exists = await self.redis.exists(rk)
        if exists:
            return False
        await self.redis.set(rk, 1, expire=self.ttl)
        return True


