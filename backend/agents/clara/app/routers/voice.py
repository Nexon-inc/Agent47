from fastapi import APIRouter, HTTPException, Depends, Query, Body, UploadFile, File
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..services.voice_service import ClaraVoiceService
from ..models import SupportChannel
from ..database import get_clara_database

router = APIRouter()

# Pydantic models for request/response
class ProcessVoiceMessageRequest(BaseModel):
    customer_id: int
    channel: SupportChannel = SupportChannel.PHONE
    metadata: Optional[Dict[str, Any]] = None

class GenerateVoiceResponseRequest(BaseModel):
    message: str
    response_type: str = "support_response"
    language: str = "en"
    voice_style: str = "professional"

class IVRInteractionRequest(BaseModel):
    customer_id: int
    phone_number: str
    menu_selection: str
    spoken_input: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# Dependency
async def get_voice_service() -> ClaraVoiceService:
    service = ClaraVoiceService()
    await service.initialize()
    return service

@router.post("/process", response_model=Dict[str, Any])
async def process_voice_message(
    customer_id: int = Body(...),
    channel: SupportChannel = Body(SupportChannel.PHONE),
    metadata: Optional[Dict[str, Any]] = Body(None),
    audio_file: UploadFile = File(...),
    service: ClaraVoiceService = Depends(get_voice_service)
):
    """Process voice message and create support ticket"""
    try:
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            result = await service.process_voice_message(
                customer_id=customer_id,
                audio_file_path=temp_file_path,
                channel=channel,
                metadata=metadata
            )
            
            if result["success"]:
                return result
            else:
                raise HTTPException(status_code=400, detail=result["error"])
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-response", response_model=Dict[str, Any])
async def generate_voice_response(
    request: GenerateVoiceResponseRequest,
    service: ClaraVoiceService = Depends(get_voice_service)
):
    """Generate voice response text and optionally convert to speech"""
    try:
        result = await service.generate_voice_response(
            message=request.message,
            response_type=request.response_type,
            language=request.language,
            voice_style=request.voice_style
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ivr/interact", response_model=Dict[str, Any])
async def handle_ivr_interaction(
    request: IVRInteractionRequest,
    service: ClaraVoiceService = Depends(get_voice_service)
):
    """Handle IVR (Interactive Voice Response) interactions"""
    try:
        result = await service.handle_ivr_interaction(
            customer_id=request.customer_id,
            phone_number=request.phone_number,
            menu_selection=request.menu_selection,
            spoken_input=request.spoken_input,
            metadata=request.metadata
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ivr/menu", response_model=Dict[str, Any])
async def get_ivr_menu_options():
    """Get available IVR menu options"""
    try:
        return {
            "success": True,
            "menu_options": [
                {
                    "option": "1",
                    "description": "Technical Support",
                    "action": "route_to_technical"
                },
                {
                    "option": "2",
                    "description": "Billing Support",
                    "action": "route_to_billing"
                },
                {
                    "option": "3",
                    "description": "Speak to Representative",
                    "action": "escalate_to_human"
                },
                {
                    "option": "4",
                    "description": "Order Tracking",
                    "action": "route_to_orders"
                },
                {
                    "option": "5",
                    "description": "General Inquiry",
                    "action": "route_to_general"
                }
            ],
            "welcome_message": "Welcome to Clara Customer Support. Please select an option from the menu.",
            "timeout_message": "No selection detected. Please try again or stay on the line to speak with a representative."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/voice", response_model=Dict[str, Any])
async def get_voice_support_stats(
    service: ClaraVoiceService = Depends(get_voice_service)
):
    """Get voice support statistics"""
    try:
        # This would be implemented in the analytics service
        return {
            "success": True,
            "stats": {
                "total_voice_messages": 0,
                "successful_transcriptions": 0,
                "average_transcription_confidence": 0,
                "voice_tickets_created": 0,
                "ivr_interactions": 0,
                "human_escalations": 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/languages/supported", response_model=Dict[str, Any])
async def get_supported_languages():
    """Get supported languages for voice support"""
    try:
        return {
            "success": True,
            "languages": [
                {"code": "en", "name": "English", "default": True},
                {"code": "es", "name": "Spanish", "default": False},
                {"code": "fr", "name": "French", "default": False},
                {"code": "de", "name": "German", "default": False},
                {"code": "it", "name": "Italian", "default": False},
                {"code": "pt", "name": "Portuguese", "default": False},
                {"code": "ru", "name": "Russian", "default": False},
                {"code": "zh", "name": "Chinese", "default": False},
                {"code": "ja", "name": "Japanese", "default": False},
                {"code": "ko", "name": "Korean", "default": False}
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice-styles", response_model=Dict[str, Any])
async def get_available_voice_styles():
    """Get available voice styles for text-to-speech"""
    try:
        return {
            "success": True,
            "voice_styles": [
                {"id": "professional", "name": "Professional", "description": "Formal and business-like"},
                {"id": "friendly", "name": "Friendly", "description": "Warm and approachable"},
                {"id": "calm", "name": "Calm", "description": "Relaxed and soothing"},
                {"id": "energetic", "name": "Energetic", "description": "Dynamic and enthusiastic"},
                {"id": "warm", "name": "Warm", "description": "Gentle and caring"}
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
