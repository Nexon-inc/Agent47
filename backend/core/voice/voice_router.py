"""
Voice I/O Router
Handles voice input/output for agent conversations
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Optional, Dict, Any
import logging
from pydantic import BaseModel

from ..authentication.auth_manager import get_current_active_user
from ..database.models import User
from .voice_service import get_voice_io_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

class TranscribeRequest(BaseModel):
    language: Optional[str] = None

class SynthesizeRequest(BaseModel):
    text: str
    agent_key: str
    language: Optional[str] = None

class ConversationRequest(BaseModel):
    agent_key: str
    language: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

@router.post("/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Transcribe audio to text"""
    try:
        audio_data = await audio_file.read()
        
        voice_service = await get_voice_io_service()
        result = await voice_service.transcribe_audio(
            audio_data=audio_data,
            audio_format=audio_file.filename.split('.')[-1] if audio_file.filename else None,
            language=language,
            user_id=current_user.id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Transcription failed")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )

@router.post("/synthesize")
async def synthesize_speech(
    request: SynthesizeRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Convert text to speech with agent voice"""
    try:
        voice_service = await get_voice_io_service()
        result = await voice_service.synthesize_speech(
            text=request.text,
            agent_key=request.agent_key,
            language=request.language,
            user_id=current_user.id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Speech synthesis failed")
            )
        
        # Return audio as base64 or file download
        audio_data = result.get("audio_data")
        if audio_data:
            import base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            result["audio_base64"] = audio_base64
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis failed: {str(e)}"
        )

@router.post("/conversation")
async def voice_conversation(
    audio_file: UploadFile = File(...),
    agent_key: str = None,
    language: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Complete voice conversation: transcribe -> process -> synthesize"""
    try:
        if not agent_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="agent_key is required"
            )
        
        audio_data = await audio_file.read()
        
        voice_service = await get_voice_io_service()
        result = await voice_service.voice_conversation(
            audio_data=audio_data,
            agent_key=agent_key,
            user_id=current_user.id,
            audio_format=audio_file.filename.split('.')[-1] if audio_file.filename else None,
            language=language
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Voice conversation failed")
            )
        
        # Return audio as base64
        audio_data = result.get("agent_response", {}).get("audio_data")
        if audio_data:
            import base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            result["agent_response"]["audio_base64"] = audio_base64
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice conversation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice conversation failed: {str(e)}"
        )

