import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    from backend.core.integrations.integration_manager import IntegrationManager
except Exception:
    IntegrationManager = None


class IntegrationUtils:
    """Small wrapper providing initialize and call helpers for integrations.

    Falls back to a no-op logger if the real IntegrationManager isn't available
    at import time to avoid import-time failures during startup.
    """

    def __init__(self):
        self._manager = IntegrationManager() if IntegrationManager is not None else None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        if self._manager is not None:
            await self._manager.initialize()
        self._initialized = True

    async def call_integration(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self._manager is not None:
            return await self._manager.call(name, payload)
        logger.info(f"(IntegrationUtils fallback) call_integration: {name} -> {payload}")
        return {"success": False, "message": "integration manager not available"}


def get_integration_utils() -> IntegrationUtils:
    return IntegrationUtils()
