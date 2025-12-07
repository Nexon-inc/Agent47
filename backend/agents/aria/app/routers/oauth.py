from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.core.authentication.auth_manager import get_current_user
from backend.core.database.models import User
from ..services.oauth_service import OAuthService


router = APIRouter(prefix="/aria/oauth", tags=["aria:oauth"])


class CodePayload(BaseModel):
    code: str


@router.post("/linkedin")
async def linkedin_auth(payload: CodePayload, current_user: User = Depends(get_current_user)):
    svc = OAuthService()
    return await svc.exchange_code_linkedin(current_user.id, payload.code)


@router.post("/facebook")
async def facebook_auth(payload: CodePayload, current_user: User = Depends(get_current_user)):
    svc = OAuthService()
    return await svc.exchange_code_facebook(current_user.id, payload.code)


