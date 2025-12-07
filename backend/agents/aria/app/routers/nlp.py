from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.core.ai import get_ai_service_manager, AIServiceManager


router = APIRouter(prefix="/aria/nlp", tags=["aria:nlp"])


class NLPCommand(BaseModel):
    user_id: int
    text: str
    context: Optional[Dict[str, Any]] = None


@router.post("/command")
async def nlp_command(payload: NLPCommand):
    """Process NLP commands using the unified AI service manager"""
    try:
        ai_manager: AIServiceManager = await get_ai_service_manager()
        
        # Build context for Aria-specific NLP processing
        context = {
            "user_id": payload.user_id,
            "agent": "aria",
            "capabilities": [
                "social_media_management",
                "content_creation", 
                "scheduling",
                "analytics",
                "trend_monitoring",
                "ad_management"
            ],
            **(payload.context or {})
        }
        
        # Create system prompt for Aria-specific NLP processing
        system_prompt = f"""You are Aria, an AI-powered social media management assistant. Process the user's request and provide helpful responses.

User Context: {context}

Available Aria capabilities:
- Social media account management and analysis
- Content creation (captions, hashtags, images)
- Post scheduling and optimization
- Analytics and performance insights
- Trend monitoring and analysis
- Advertising campaign management
- Geo-targeted campaigns
- Multi-platform posting

Respond with helpful, actionable advice related to social media management."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": payload.text}
        ]
        
        result = await ai_manager.generate_text(
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        if result.success:
            return {
                "success": True,
                "response": result.text_content,
                "model_used": result.service_used,
                "fallback_used": result.fallback_used,
                "response_time_ms": result.response_time_ms
            }
        else:
            raise HTTPException(status_code=503, detail=f"AI service unavailable: {result.error}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process NLP command: {str(e)}")


