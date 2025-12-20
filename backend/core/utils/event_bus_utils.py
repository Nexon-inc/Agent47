import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    from core.event_bus.kafka_manager import EventBus
except Exception:
    EventBus = None


class EventBusUtils:
    """Small wrapper to provide initialize/publish helpers around the EventBus
    implementation. If the real EventBus is not available at import time, the
    wrapper falls back to a no-op implementation to avoid import-time failures.
    """

    def __init__(self):
        self._bus = EventBus() if EventBus is not None else None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        if self._bus is not None:
            await self._bus.initialize()
        self._initialized = True

    async def publish(self, topic: str, message: Dict[str, Any]) -> None:
        if self._bus is not None:
            await self._bus.publish(topic, message)
        else:
            # Fallback: log the event
            logger.info(f"(EventBus fallback) publish: {topic} -> {message}")


def get_event_bus_utils() -> EventBusUtils:
    return EventBusUtils()
