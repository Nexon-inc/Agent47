"""
Phone Calling Service
Makes voice calls using Twilio with agent voices
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
import base64

from ..config import settings
from ..voice import get_voice_io_service
from ..ai.agent_voice_mapping import AgentVoiceMapping
from ..database import get_database as get_db_manager
from ..database.models import User

logger = logging.getLogger(__name__)

class PhoneCallingService:
    """Service for making phone calls with agent voices"""
    
    def __init__(self):
        self.twilio_account_sid = settings.twilio.twilio_account_sid
        self.twilio_auth_token = settings.twilio.twilio_auth_token
        self.twilio_phone_number = settings.twilio.twilio_phone_number
        self.twilio_enabled = settings.twilio.twilio_enabled
        self.voice_io_service = None
        self.voice_mapping = AgentVoiceMapping()
        self._initialized = False
    
    async def initialize(self):
        """Initialize phone calling service"""
        if not self.twilio_enabled:
            logger.warning("Twilio is disabled in settings")
            return
        
        if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_phone_number]):
            logger.warning("Twilio credentials not fully configured")
            return
        
        self.voice_io_service = await get_voice_io_service()
        self._initialized = True
        logger.info("Phone calling service initialized")
    
    async def make_agent_call(
        self,
        phone_number: str,
        agent_key: str,
        message: str,
        user_id: Optional[int] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make a phone call with agent voice
        
        Args:
            phone_number: Phone number to call (E.164 format)
            agent_key: Agent identifier (aria, clara, eric, etc.)
            message: Message for agent to speak
            user_id: User ID making the call
            language: Language code
            
        Returns:
            Dict with success, call_sid, and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.twilio_enabled:
            return {
                "success": False,
                "error": "Twilio calling is disabled"
            }
        
        try:
            # Generate agent voice audio
            if not self.voice_io_service:
                self.voice_io_service = await get_voice_io_service()
            
            synthesis_result = await self.voice_io_service.synthesize_speech(
                text=message,
                agent_key=agent_key,
                language=language or "en",
                user_id=user_id
            )
            
            if not synthesis_result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to generate agent voice: {synthesis_result.get('error')}"
                }
            
            audio_data = synthesis_result.get("audio_data")
            
            # Upload audio to Twilio (or use TwiML for text-to-speech)
            # For now, we'll use TwiML Say verb with agent voice
            # In production, upload audio to Twilio Media and use Play verb
            
            # Create TwiML response
            twiml = self._create_twiml_response(message, agent_key)
            
            # Make call via Twilio API
            call_result = await self._make_twilio_call(
                to_phone=phone_number,
                twiml=twiml
            )
            
            if call_result.get("success"):
                # Store call record in database
                await self._store_call_record(
                    call_sid=call_result.get("call_sid"),
                    phone_number=phone_number,
                    agent_key=agent_key,
                    message=message,
                    user_id=user_id
                )
            
            return call_result
            
        except Exception as e:
            logger.error(f"Failed to make agent call: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_twiml_response(self, message: str, agent_key: str) -> str:
        """Create TwiML response for call"""
        # Get agent voice configuration
        voice_config = self.voice_mapping.get_agent_voice(agent_key)
        
        # TwiML with Say verb (Twilio will use TTS)
        # Note: Twilio has its own voices, but we can use SSML for better control
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">{message}</Say>
</Response>"""
        
        return twiml
    
    async def _make_twilio_call(
        self,
        to_phone: str,
        twiml: str
    ) -> Dict[str, Any]:
        """Make call via Twilio API"""
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Calls.json"
            
            # Use TwiML Bin URL or direct TwiML
            # For simplicity, we'll use a TwiML Bin or webhook URL
            # In production, set up a webhook endpoint that returns TwiML
            
            data = {
                "From": self.twilio_phone_number,
                "To": to_phone,
                "Url": f"{settings.base_url}/api/v1/phone/twiml",  # Webhook URL
                "Method": "POST"
            }
            
            auth = (self.twilio_account_sid, self.twilio_auth_token)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=data, auth=auth)
                response.raise_for_status()
                result = response.json()
                
                return {
                    "success": True,
                    "call_sid": result.get("sid"),
                    "status": result.get("status"),
                    "to": result.get("to"),
                    "from": result.get("from"),
                    "metadata": {
                        "created_at": result.get("date_created"),
                        "direction": result.get("direction")
                    }
                }
                
        except Exception as e:
            logger.error(f"Twilio call failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _store_call_record(
        self,
        call_sid: str,
        phone_number: str,
        agent_key: str,
        message: str,
        user_id: Optional[int]
    ):
        """Store call record in database"""
        try:
            db = await get_db_manager()
            async with db.get_session() as session:
                from sqlalchemy import text
                await session.execute(
                    text("""
                        INSERT INTO phone_calls (
                            call_sid, phone_number, agent_key, message, user_id, 
                            status, created_at
                        ) VALUES (
                            :call_sid, :phone_number, :agent_key, :message, :user_id,
                            'initiated', NOW()
                        )
                    """),
                    {
                        "call_sid": call_sid,
                        "phone_number": phone_number,
                        "agent_key": agent_key,
                        "message": message,
                        "user_id": user_id
                    }
                )
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to store call record: {e}")

# Singleton instance
_phone_calling_service: Optional[PhoneCallingService] = None

async def get_phone_calling_service() -> PhoneCallingService:
    """Get or create phone calling service instance"""
    global _phone_calling_service
    if not _phone_calling_service:
        _phone_calling_service = PhoneCallingService()
        await _phone_calling_service.initialize()
    return _phone_calling_service

