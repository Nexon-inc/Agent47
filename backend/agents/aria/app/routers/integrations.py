from fastapi import APIRouter, Depends
from core.authentication.auth_manager import get_current_user
from core.database.models import User
from ..integrations.buffer_client import BufferClient


router = APIRouter(prefix="/aria/integrations", tags=["aria:integrations"])


@router.get("/buffer/profiles")
async def buffer_profiles(current_user: User = Depends(get_current_user)):
    client = BufferClient()
    return await client.list_profiles()


