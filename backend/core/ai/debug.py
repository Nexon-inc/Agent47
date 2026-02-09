from fastapi import APIRouter
from core.config import settings
import logging
import os

router = APIRouter(prefix="/debug", tags=["Debug"])
logger = logging.getLogger(__name__)

@router.get("/ai-config")
async def check_ai_config():
    """Debug endpoint to check AI configuration"""
    try:
        groq_key = getattr(settings.groq, 'groq_api_key', None)
        if not groq_key:
             # Try fallback to env var directly or root settings if it was moved
             groq_key = os.getenv("GROQ_API_KEY") or getattr(settings, 'GROQ_API_KEY', None)

        return {
            "groq_api_key_exists": bool(groq_key),
            "groq_api_key_length": len(groq_key) if groq_key else 0,
            "groq_api_key_prefix": groq_key[:10] + "..." if groq_key and len(groq_key) > 10 else "MISSING",
            "settings_attributes": [attr for attr in dir(settings) if not attr.startswith('_')],
            "groq_settings_object": str(getattr(settings, 'groq', 'MISSING')),
            "groq_settings": {
                "max_tokens": getattr(settings.groq, 'groq_max_tokens', 'MISSING') if hasattr(settings, 'groq') else 'NO GROQ OBJECT',
                "default_model": getattr(settings.groq, 'groq_default_model', 'MISSING') if hasattr(settings, 'groq') else 'NO GROQ OBJECT',
            }
        }
    except Exception as e:
        logger.error(f"Error checking config: {e}", exc_info=True)
        return {
            "error": str(e),
            "trace": "Check logs for full traceback"
        }
