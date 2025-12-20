from typing import Dict, Any, List, Optional
from datetime import datetime
from core.database.connection import get_supabase
from core.platforms.platform_manager import get_platform_manager
from ..integrations.buffer_client import BufferClient
from ..models import ScheduledPost, PublishedPost, PlatformEnum, PostStatus


class PublisherService:
    def __init__(self):
        self.platforms = None

    async def initialize(self):
        self.platforms = await get_platform_manager()
        self.buffer = BufferClient()

    async def process_due_post(self, scheduled_post_id: int) -> Dict[str, Any]:
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(ScheduledPost).where(ScheduledPost.id == scheduled_post_id))
            post: Optional[ScheduledPost] = result.scalar_one_or_none()
            if not post:
                return {"success": False, "error": "scheduled_post_not_found"}

            if post.status == PostStatus.scheduled:
                post.status = PostStatus.publishing
                await session.flush()

            text = self._compose_text(post.caption, post.hashtags)
            media_urls = self._collect_media_urls(post.media_refs)
            results: List[Dict[str, Any]] = []

            # Buffer fan-out if profile IDs provided
            if post.buffer_profile_ids:
                b = await self.buffer.create_update(post.buffer_profile_ids, text, media_urls, None)
                results.append({"platform": "buffer", **b})

            for p in post.platform_targets:
                platform_name = str(p).lower()
                res = await self.platforms.post_to_platform(
                    user_id=post.user_id,
                    platform_name=platform_name,
                    content=text,
                    media_urls=media_urls,
                    scheduled_time=None,
                )
                try:
                    pe = PlatformEnum(platform_name)
                except Exception:
                    pe = PlatformEnum.twitter
                pub = PublishedPost(
                    scheduled_post_id=post.id,
                    platform=pe,
                    platform_post_id=res.get("post_id"),
                    published_at=datetime.utcnow(),
                    status="published" if res.get("success") else "failed",
                    permalink=(res.get("response", {}) or {}).get("permalink") if isinstance(res.get("response"), dict) else None,
                    error=res.get("error"),
                )
                session.add(pub)
                results.append({"platform": platform_name, **res})

            post.status = PostStatus.published if any(r.get("success") for r in results) else PostStatus.failed
            await session.commit()
            return {"success": True, "results": results, "status": post.status.value}

    def _compose_text(self, caption: Optional[str], hashtags: Optional[List[str]]) -> str:
        base = caption or ""
        if hashtags:
            tags = " ".join([h if h.startswith("#") else f"#{h}" for h in hashtags])
            return f"{base}\n\n{tags}" if base else tags
        return base

    def _collect_media_urls(self, media_refs: Optional[List[Dict[str, Any]]]) -> Optional[List[str]]:
        if not media_refs:
            return None
        urls: List[str] = []
        for m in media_refs:
            url = m.get("url") or m.get("s3_url") or m.get("cdn_url")
            if url:
                urls.append(url)
        return urls or None


