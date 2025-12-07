from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.core.logs import get_logger
from backend.core.cache import get_redis
from backend.core.database import get_database


class IntegrationHealth:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.redis = get_redis()
        self.db = get_database()

    async def initialize(self):
        return True

    async def set_health(self, name: str, healthy: bool, message: Optional[str] = None) -> bool:
        data = {"healthy": healthy, "message": message or "", "timestamp": datetime.utcnow().isoformat()}
        await self.redis.set(f"integration:health:{name}", data, expire=600)
        return True

    async def get_health(self, name: str) -> Dict[str, Any]:
        cached = await self.redis.get(f"integration:health:{name}")
        if cached:
            return cached
        return {"healthy": False, "message": "unknown", "timestamp": None}


_integration_health: Optional[IntegrationHealth] = None


async def get_integration_health() -> IntegrationHealth:
    global _integration_health
    if _integration_health is None:
        _integration_health = IntegrationHealth()
        await _integration_health.initialize()
    return _integration_health


async def init_integration_health() -> IntegrationHealth:
    ih = IntegrationHealth()
    await ih.initialize()
    return ih
