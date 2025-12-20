from fastapi import APIRouter, Depends, UploadFile, File
from core.authentication.auth_manager import get_current_user
from core.database.models import User
from ..services.speech_service import SpeechService


router = APIRouter(prefix="/aria/speech", tags=["aria:speech"])


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    svc = SpeechService()
    content = await file.read()
    return await svc.transcribe(file.filename, content)


