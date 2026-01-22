from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import AriaScheduledPost


class SchedulesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, scheduled_post_id: int) -> Optional[AriaScheduledPost]:
        result = await self.session.execute(
            select(AriaScheduledPost).where(AriaScheduledPost.id == scheduled_post_id)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency(self, idempotency_key: str) -> Optional[AriaScheduledPost]:
        result = await self.session.execute(
            select(AriaScheduledPost).where(AriaScheduledPost.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    async def create(self, data: Dict[str, Any]) -> AriaScheduledPost:
        scheduled = AriaScheduledPost(**data)
        self.session.add(scheduled)
        await self.session.flush()
        return scheduled

    async def list_for_user(self, user_id: int, time_from: Optional[str] = None, time_to: Optional[str] = None, status: Optional[str] = None) -> List[AriaScheduledPost]:
        query = select(AriaScheduledPost).where(AriaScheduledPost.user_id == user_id)
        if time_from:
            query = query.where(AriaScheduledPost.scheduled_at >= time_from)
        if time_to:
            query = query.where(AriaScheduledPost.scheduled_at <= time_to)
        if status:
            query = query.where(AriaScheduledPost.status == status)
        result = await self.session.execute(query.order_by(AriaScheduledPost.scheduled_at.asc()))
        return result.scalars().all()

    async def update(self, scheduled_post_id: int, updates: Dict[str, Any]) -> Optional[AriaScheduledPost]:
        scheduled = await self.get_by_id(scheduled_post_id)
        if not scheduled:
            return None
        for k, v in updates.items():
            setattr(scheduled, k, v)
        await self.session.flush()
        return scheduled


