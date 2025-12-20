"""
Unified Voice Input/Output Service
Connects all existing voice services (Groq STT/TTS, agent voice mapping)
Provides unified API for voice conversations with agents
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..ai import get_ai_service_manager, AIServiceManager
from ..ai.agent_voice_mapping import AgentVoiceMapping
from ..config import settings
from ..database.models import User

logger = logging.getLogger(__name__)

class VoiceIOService:
    """Unified voice input/output service for agent conversations"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.voice_mapping = AgentVoiceMapping()
        self._initialized = False
    
    async def initialize(self):
        """Initialize voice I/O service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            self._initialized = True
            logger.info("Voice I/O service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize voice I/O service: {e}")
            raise
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: Optional[str] = None,
        language: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text using Groq STT
        
        Args:
            audio_data: Audio file data as bytes
            audio_format: Audio format (mp3, wav, ogg, flac, m4a)
            language: Language code (auto-detected if not provided)
            user_id: User ID for tier enforcement
            
        Returns:
            Dict with success, text, confidence, language, and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.ai_service_manager or not self.ai_service_manager.groq_stt_client:
            return {
                "success": False,
                "error": "STT service not available"
            }
        
        # Get user tier if user_id provided
        user_tier = None
        if user_id:
            try:
                db = await get_db_manager()
                async with db.get_session() as session:
                    from sqlalchemy import select
                    from ..database.models import User, UserTier
                    result = await session.execute(
                        select(User).where(User.id == user_id)
                    )
                    user = result.scalar_one_or_none()
                    if user:
                        user_tier = user.tier
            except Exception as e:
                logger.warning(f"Failed to get user tier: {e}")
        
        # Use AI service manager's transcribe method
        result = await self.ai_service_manager.transcribe_audio(
            audio_data=audio_data,
            audio_format=audio_format,
            language=language,
            user_id=user_id,
            user_tier=user_tier
        )
        
        return result
    
    async def synthesize_speech(
        self,
        text: str,
        agent_key: str,
        language: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Convert text to speech using agent-specific voice
        
        Args:
            text: Text to convert to speech
            agent_key: Agent identifier (aria, clara, eric, etc.)
            language: Language code (auto-detected if not provided)
            user_id: User ID for tier enforcement
            
        Returns:
            Dict with success, audio_data (bytes), and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.ai_service_manager or not self.ai_service_manager.groq_tts_client:
            return {
                "success": False,
                "error": "TTS service not available"
            }
        
        # Get agent voice configuration
        voice_config = self.voice_mapping.get_agent_voice(agent_key)
        agent_voice = voice_config["voice"]
        
        # Auto-detect language if not provided
        if not language:
            # Try to detect from user preferences
            if user_id:
                try:
                    db = await get_db_manager()
                    async with db.get_session() as session:
                        from sqlalchemy import select
                        from ..database.models import User
                        result = await session.execute(
                            select(User).where(User.id == user_id)
                        )
                        user = result.scalar_one_or_none()
                        if user and user.preferences:
                            language = user.preferences.get("language", "en")
                except Exception as e:
                    logger.warning(f"Failed to get user language preference: {e}")
            
            if not language:
                language = "en"  # Default to English
        
        # Get user tier if user_id provided
        user_tier = None
        if user_id:
            try:
                db = await get_db_manager()
                async with db.get_session() as session:
                    from sqlalchemy import select
                    from ..database.models import User, UserTier
                    result = await session.execute(
                        select(User).where(User.id == user_id)
                    )
                    user = result.scalar_one_or_none()
                    if user:
                        user_tier = user.tier
            except Exception as e:
                logger.warning(f"Failed to get user tier: {e}")
        
        # Use AI service manager's text_to_speech with agent voice
        result = await self.ai_service_manager.text_to_speech(
            text=text,
            voice=agent_voice,
            language=language,
            speed=settings.groq.voice_output_speed,
            pitch=settings.groq.voice_output_pitch,
            voice_style=voice_config.get("style"),
            user_id=user_id,
            user_tier=user_tier
        )
        
        if result.get("success"):
            # Add agent voice metadata
            metadata = result.get("metadata", {})
            metadata.update({
                "agent_key": agent_key,
                "agent_voice": agent_voice,
                "agent_gender": voice_config.get("gender"),
                "agent_style": voice_config.get("style")
            })
            result["metadata"] = metadata
        
        return result
    
    async def voice_conversation(
        self,
        audio_data: bytes,
        agent_key: str,
        user_id: int,
        audio_format: Optional[str] = None,
        language: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete voice conversation: transcribe -> process -> synthesize
        
        Args:
            audio_data: User's audio input
            agent_key: Agent to converse with
            user_id: User ID
            audio_format: Audio format
            language: Language code
            context: Conversation context
            
        Returns:
            Dict with transcription, agent response text, and audio
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Step 1: Transcribe user's audio
            transcription_result = await self.transcribe_audio(
                audio_data=audio_data,
                audio_format=audio_format,
                language=language,
                user_id=user_id
            )
            
            if not transcription_result.get("success"):
                return {
                    "success": False,
                    "error": f"Transcription failed: {transcription_result.get('error')}"
                }
            
            user_text = transcription_result.get("text", "")
            detected_language = transcription_result.get("language", language or "en")
            
            # Step 2: Process with agent (route to appropriate agent service)
            agent_response = await self._process_agent_request(
                agent_key=agent_key,
                user_id=user_id,
                user_message=user_text,
                context=context or {}
            )
            
            if not agent_response.get("success"):
                return {
                    "success": False,
                    "error": f"Agent processing failed: {agent_response.get('error')}",
                    "transcription": {
                        "text": user_text,
                        "language": detected_language
                    }
                }
            
            agent_text = agent_response.get("response", "")
            
            # Step 3: Synthesize agent's response
            synthesis_result = await self.synthesize_speech(
                text=agent_text,
                agent_key=agent_key,
                language=detected_language,
                user_id=user_id
            )
            
            if not synthesis_result.get("success"):
                return {
                    "success": False,
                    "error": f"Speech synthesis failed: {synthesis_result.get('error')}",
                    "transcription": {
                        "text": user_text,
                        "language": detected_language
                    },
                    "agent_response": {
                        "text": agent_text
                    }
                }
            
            return {
                "success": True,
                "transcription": {
                    "text": user_text,
                    "language": detected_language,
                    "confidence": transcription_result.get("confidence", 0.0)
                },
                "agent_response": {
                    "text": agent_text,
                    "audio_data": synthesis_result.get("audio_data"),
                    "audio_metadata": synthesis_result.get("metadata", {})
                },
                "conversation_id": agent_response.get("conversation_id")
            }
            
        except Exception as e:
            logger.error(f"Voice conversation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_agent_request(
        self,
        agent_key: str,
        user_id: int,
        user_message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route request to appropriate agent service"""
        try:
            # Route to agent-specific chat service
            if agent_key == "clara":
                from agents.clara.app.services.clara_chat_service import ClaraChatService
                service = ClaraChatService()
                await service.initialize()
                result = await service.process_chat_message(
                    user_id=user_id,
                    message=user_message,
                    context=context
                )
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "conversation_id": result.get("conversation_id")
                }
            
            elif agent_key == "eric":
                from agents.eric.app.services.eric_chat_service import EricChatService
                service = EricChatService()
                await service.initialize()
                result = await service.process_chat_message(
                    user_id=user_id,
                    message=user_message,
                    session_id=context.get("session_id")
                )
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "conversation_id": result.get("session_id")
                }
            
            elif agent_key == "aria":
                from agents.aria.app.services.aria_chat_service import AriaChatService
                service = AriaChatService()
                await service.initialize()
                result = await service.process_message(
                    user_id=user_id,
                    message=user_message,
                    context=context
                )
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "conversation_id": result.get("conversation_id")
                }
            
            elif agent_key == "jackie":
                from agents.jackie.app.services.jackie_chat_service import JackieChatService
                service = JackieChatService()
                await service.initialize()
                result = await service.process_message(
                    user_id=user_id,
                    message=user_message,
                    context=context
                )
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "conversation_id": result.get("conversation_id")
                }
            
            elif agent_key == "joe":
                from agents.joe.app.services.joe_chat_service import JoeChatService
                service = JoeChatService()
                await service.initialize()
                result = await service.process_message(
                    user_id=user_id,
                    message=user_message,
                    context=context
                )
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "conversation_id": result.get("conversation_id")
                }
            
            elif agent_key == "purity":
                from agents.purity.app.services.purity_chat_service import PurityChatService
                service = PurityChatService()
                await service.initialize()
                result = await service.process_message(
                    user_id=user_id,
                    message=user_message,
                    context=context
                )
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "conversation_id": result.get("conversation_id")
                }
            
            elif agent_key == "shakes":
                from agents.shakes.app.services.shakes_chat_service import ShakesChatService
                service = ShakesChatService()
                await service.initialize()
                result = await service.process_message(
                    user_id=user_id,
                    message=user_message,
                    context=context
                )
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "conversation_id": result.get("conversation_id")
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown agent: {agent_key}"
                }
                
        except Exception as e:
            logger.error(f"Failed to process agent request for {agent_key}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Singleton instance
_voice_io_service: Optional[VoiceIOService] = None

async def get_voice_io_service() -> VoiceIOService:
    """Get or create voice I/O service instance"""
    global _voice_io_service
    if not _voice_io_service:
        _voice_io_service = VoiceIOService()
        await _voice_io_service.initialize()
    return _voice_io_service

