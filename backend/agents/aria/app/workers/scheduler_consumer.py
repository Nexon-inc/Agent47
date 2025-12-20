import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy import select, and_
from core.database.connection import get_supabase
from core.event_bus.kafka_manager import get_kafka
from ..models import ScheduledPost, PostStatus
from ..config import aria_settings


class SchedulerConsumer:
    def __init__(self):
        self.kafka = None

    async def initialize(self):
        self.kafka = await get_kafka()
        await self.kafka.subscribe_to_topic(aria_settings.kafka_topics_scheduling_created)
        self.kafka.register_handler(aria_settings.kafka_topics_scheduling_created, self._handle_created)

    async def _handle_created(self, event: Dict[str, Any], key: str, topic: str):
        data = event.get("data", {})
        scheduled_post_id = data.get("scheduled_post_id")
        if not scheduled_post_id:
            return
        # Polling approach to wait until time window due; alternatively a scheduler service would push events
        await self._emit_due_when_ready(int(scheduled_post_id))

    async def _emit_due_when_ready(self, scheduled_post_id: int):
        db = await get_supabase()
        while True:
            async with db.get_session() as session:
                result = await session.execute(select(ScheduledPost).where(ScheduledPost.id == scheduled_post_id))
                post: ScheduledPost = result.scalar_one_or_none()
                if not post or post.status != PostStatus.scheduled:
                    return
                if post.scheduled_at and post.scheduled_at <= datetime.utcnow():
                    await self.kafka.publish_event(
                        aria_settings.kafka_topics_scheduling_due,
                        {"scheduled_post_id": post.id, "user_id": post.user_id},
                        key=str(post.user_id),
                    )
                    return
            await asyncio.sleep(5)


scheduler_consumer = SchedulerConsumer()


