import asyncio
from typing import Dict, Any
from backend.core.event_bus.kafka_manager import get_kafka
from ..config import aria_settings
from ..services.publisher_service import PublisherService


class PublisherConsumer:
    def __init__(self):
        self.kafka = None
        self.service = PublisherService()

    async def initialize(self):
        self.kafka = await get_kafka()
        await self.service.initialize()
        await self.kafka.subscribe_to_topic(aria_settings.kafka_topics_scheduling_due)
        self.kafka.register_handler(aria_settings.kafka_topics_scheduling_due, self._handle_due_event)

    async def _handle_due_event(self, event: Dict[str, Any], key: str, topic: str):
        data = event.get("data", {})
        scheduled_post_id = data.get("scheduled_post_id")
        if scheduled_post_id:
            await self.service.process_due_post(int(scheduled_post_id))


publisher_consumer = PublisherConsumer()


