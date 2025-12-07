from typing import Dict, Any, List
from datetime import datetime
from backend.core.database.connection import get_supabase
from backend.core.config import settings
import httpx
from ..models import Approval, ScheduledPost, ApprovalStatus


class ApprovalService:
    async def request_approval(self, user_id: int, scheduled_post_id: int, reviewers: List[str]) -> Dict[str, Any]:
        db = await get_supabase()
        async with db.get_session() as session:
            ap = Approval(user_id=user_id, scheduled_post_id=scheduled_post_id, reviewers=reviewers, status=ApprovalStatus.pending)
            session.add(ap)
            await session.commit()
        await self._notify(reviewers, f"Approval requested for scheduled post {scheduled_post_id}")
        return {"approval_id": ap.id, "status": ap.status.value}

    async def decide(self, approval_id: int, decision: str, comment: str = "") -> Dict[str, Any]:
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            res = await session.execute(select(Approval).where(Approval.id == approval_id))
            ap: Approval = res.scalar_one_or_none()
            if not ap:
                return {"success": False, "error": "approval_not_found"}
            ap.status = ApprovalStatus.approved if decision == "approve" else ApprovalStatus.rejected
            ap.comments = (ap.comments or []) + ([{"text": comment, "at": datetime.utcnow().isoformat()}] if comment else [])
            ap.decided_at = datetime.utcnow()
            await session.commit()
            return {"success": True, "status": ap.status.value}

    async def _notify(self, reviewers: List[str], message: str):
        # Slack notification if configured
        if settings.slack.bot_token:
            async with httpx.AsyncClient() as client:
                for channel in reviewers:
                    await client.post(
                        f"{settings.slack.base_url}/chat.postMessage",
                        headers={"Authorization": f"Bearer {settings.slack.bot_token}"},
                        json={"channel": channel, "text": message},
                        timeout=10.0,
                    )


