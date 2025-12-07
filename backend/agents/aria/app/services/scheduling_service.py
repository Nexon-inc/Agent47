from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from backend.core.cache.redis_manager import get_redis
from backend.core.billing.usage_tracker import get_usage_tracker
from backend.core.database.connection import get_supabase
from backend.core.event_bus.kafka_manager import get_kafka
from ..models import ScheduledPost, PostStatus
from ..repositories.schedules_repo import SchedulesRepository
from ..config import aria_settings


class SchedulingService:
    def __init__(self):
        self.redis = None
        self.usage_tracker = None

    async def initialize(self):
        self.redis = await get_redis()
        self.usage_tracker = await get_usage_tracker()
        self.kafka = await get_kafka()

    async def create_scheduled_post(self, user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        db = await get_supabase()
        async with db.get_session() as session:
            repo = SchedulesRepository(session)
            idem_key = payload["idempotency_key"]
            existing = await repo.get_by_idempotency(idem_key)
            if existing:
                return {"id": existing.id, "status": existing.status.value, "duplicate": True}

            scheduled_at = payload["scheduled_at"]
            if isinstance(scheduled_at, str):
                scheduled_at = datetime.fromisoformat(scheduled_at)

            # Smart timing window enforcement stub: ensure at least 2 minutes in future
            if scheduled_at < datetime.utcnow() + timedelta(minutes=2):
                scheduled_at = datetime.utcnow() + timedelta(minutes=2)

            record = await repo.create({
                "idempotency_key": idem_key,
                "user_id": user_id,
                "campaign_id": payload.get("campaign_id"),
                "account_group_id": payload.get("account_group_id"),
                "platform_targets": payload["platform_targets"],
                "caption": payload.get("caption"),
                "hashtags": payload.get("hashtags", []),
                "media_refs": payload.get("media_refs", []),
                "scheduled_at": scheduled_at,
                "timezone": payload.get("timezone", "UTC"),
                "status": PostStatus.scheduled
            })

            await session.commit()
            await self.kafka.publish_event(
                aria_settings.kafka_topics_scheduling_created,
                {
                    "scheduled_post_id": record.id,
                    "user_id": user_id,
                    "scheduled_at": scheduled_at.isoformat(),
                    "platform_targets": payload["platform_targets"],
                },
                key=str(user_id),
            )
            await self.usage_tracker.track_agent_usage(user_id, "aria", "task")
            return {"id": record.id, "status": record.status.value}

    async def list_user_schedules(self, user_id: int, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        db = await get_supabase()
        async with db.get_session() as session:
            repo = SchedulesRepository(session)
            items = await repo.list_for_user(
                user_id,
                params.get("from"),
                params.get("to"),
                params.get("status")
            )
            return [
                {
                    "id": i.id,
                    "scheduled_at": i.scheduled_at.isoformat() if i.scheduled_at else None,
                    "status": i.status.value,
                    "platform_targets": i.platform_targets,
                } for i in items
            ]

    async def update_schedule(self, user_id: int, scheduled_post_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        db = await get_supabase()
        async with db.get_session() as session:
            repo = SchedulesRepository(session)
            if "scheduled_at" in updates and isinstance(updates["scheduled_at"], str):
                updates["scheduled_at"] = datetime.fromisoformat(updates["scheduled_at"])
            updated = await repo.update(scheduled_post_id, updates)
            if not updated:
                return None
            await session.commit()
            return {"id": updated.id, "status": updated.status.value}


