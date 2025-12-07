from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import ScheduledPost


class SchedulesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, scheduled_post_id: int) -> Optional[ScheduledPost]:
        result = await self.session.execute(
            select(ScheduledPost).where(ScheduledPost.id == scheduled_post_id)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency(self, idempotency_key: str) -> Optional[ScheduledPost]:
        result = await self.session.execute(
            select(ScheduledPost).where(ScheduledPost.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    async def create(self, data: Dict[str, Any]) -> ScheduledPost:
        scheduled = ScheduledPost(**data)
        self.session.add(scheduled)
        await self.session.flush()
        return scheduled

    async def list_for_user(self, user_id: int, time_from: Optional[str] = None, time_to: Optional[str] = None, status: Optional[str] = None) -> List[ScheduledPost]:
        query = select(ScheduledPost).where(ScheduledPost.user_id == user_id)
        if time_from:
            query = query.where(ScheduledPost.scheduled_at >= time_from)
        if time_to:
            query = query.where(ScheduledPost.scheduled_at <= time_to)
        if status:
            query = query.where(ScheduledPost.status == status)
        result = await self.session.execute(query.order_by(ScheduledPost.scheduled_at.asc()))
        return result.scalars().all()

    async def update(self, scheduled_post_id: int, updates: Dict[str, Any]) -> Optional[ScheduledPost]:
        scheduled = await self.get_by_id(scheduled_post_id)
        if not scheduled:
            return None
        for k, v in updates.items():
            setattr(scheduled, k, v)
        await self.session.flush()
        return scheduled


