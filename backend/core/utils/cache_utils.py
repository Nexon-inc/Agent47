import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from backend.core.cache.redis_manager import RedisManager
except Exception:
    RedisManager = None


class CacheUtils:
    """Small wrapper that prefers RedisManager when available, otherwise
    falls back to an in-memory dict. This avoids import-time failures while
    providing realistic caching behavior.
    """

    def __init__(self):
        self._redis = RedisManager() if RedisManager is not None else None
        self._store = {} if self._redis is None else None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        if self._redis:
            await self._redis.initialize()
        self._initialized = True

    async def get(self, key: str) -> Optional[Any]:
        if self._redis:
            return await self._redis.get(key)
        return self._store.get(key)

    async def set(self, key: str, value: Any, expire: int = None) -> None:
        if self._redis:
            await self._redis.set(key, value, expire=expire)
        else:
            self._store[key] = value

    async def delete(self, key: str) -> None:
        if self._redis:
            await self._redis.delete(key)
        else:
            self._store.pop(key, None)


def get_cache_utils() -> CacheUtils:
    return CacheUtils()
