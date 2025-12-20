from fastapi import APIRouter, Header, HTTPException, Request
import hmac
import hashlib
from core.config import settings
from ..models import WebhookEvent
from core.database.connection import get_supabase
from core.event_bus.kafka_manager import get_kafka
from ..config import aria_settings


router = APIRouter(prefix="/aria/webhooks", tags=["aria:webhooks"])


def _verify_signature(platform: str, payload: bytes, signature: str) -> bool:
    secret = settings.webhooks.shared_secrets.get(platform)
    if not secret or not signature:
        return False
    mac = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature)


@router.post("/{platform}")
async def ingest(platform: str, request: Request, x_signature: str = Header(None)):
    body = await request.body()
    if not _verify_signature(platform, body, x_signature):
        raise HTTPException(status_code=401, detail="invalid_signature")
    db = await get_supabase()
    kafka = await get_kafka()
    async with db.get_session() as session:
        evt = WebhookEvent(
            source=platform,
            signature=x_signature,
            payload=await request.json(),
            processed=False,
        )
        session.add(evt)
        await session.commit()
        await kafka.publish_event(aria_settings.kafka_topics_published_success, {"webhook_event_id": evt.id, "platform": platform}, key=platform)
        return {"accepted": True, "event_id": evt.id}


