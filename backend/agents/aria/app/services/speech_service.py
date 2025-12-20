from typing import Dict, Any
from core.ai import get_ai_service_manager, AIServiceManager


class SpeechService:
    def __init__(self):
        self.ai_service_manager: AIServiceManager = None

    async def _get_ai_service_manager(self):
        """Get AI service manager"""
        if not self.ai_service_manager:
            self.ai_service_manager = await get_ai_service_manager()
        return self.ai_service_manager

    async def transcribe(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Transcribe audio using Groq STT via AI Service Manager"""
        try:
            ai_manager = await self._get_ai_service_manager()
            
            # Detect audio format from filename
            audio_format = None
            if filename.lower().endswith('.mp3'):
                audio_format = "mp3"
            elif filename.lower().endswith('.wav'):
                audio_format = "wav"
            elif filename.lower().endswith('.m4a'):
                audio_format = "m4a"
            elif filename.lower().endswith('.ogg'):
                audio_format = "ogg"
            else:
                # Try to detect from content
                if content.startswith(b'\xff\xfb') or content.startswith(b'ID3'):
                    audio_format = "mp3"
                elif content.startswith(b'RIFF') and b'WAVE' in content[:12]:
                    audio_format = "wav"
            
            # Use Groq STT via AI Service Manager
            result = await ai_manager.transcribe_audio(
                audio_data=content,
                audio_format=audio_format,
                language=None  # Auto-detect language
            )
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Transcription failed"),
                    "text": ""
                }
            
            return {
                "success": True,
                "text": result.get("text", ""),
                "confidence": result.get("confidence", 0.0),
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", []),
                "model": "whisper-large-v3-turbo"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Transcription error: {str(e)}",
                "text": ""
            }


