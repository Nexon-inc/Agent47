from typing import Dict, Any, Optional
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.database.connection import get_supabase
from ..models import EngagementEvent


class EngagementService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None

    async def _get_ai_service_manager(self):
        """Get AI service manager"""
        if not self.ai_service_manager:
            self.ai_service_manager = await get_ai_service_manager()
        return self.ai_service_manager

    async def auto_reply(self, user_id: int, platform: str, text: str, sentiment_hint: str = "auto") -> Dict[str, Any]:
        """Generate automatic replies using AI service manager"""
        try:
            ai_manager = await self._get_ai_service_manager()
            
            # Sentiment classification via AI
            sentiment = sentiment_hint
            if sentiment == "auto":
                sentiment_messages = [
                    {"role": "system", "content": "You are a sentiment analysis expert. Return only one word: positive, neutral, or negative."},
                    {"role": "user", "content": f"Analyze the sentiment of this text: {text}"}
                ]
                
                sentiment_result = await ai_manager.generate_text(
                    messages=sentiment_messages,
                    max_tokens=10,
                    temperature=0.1
                )
                
                if sentiment_result.success:
                    sentiment = sentiment_result.text_content.strip().lower()
                    if sentiment not in ["positive", "neutral", "negative"]:
                        sentiment = "neutral"
                else:
                    sentiment = "neutral"
            
            # Generate reply using AI
            reply_messages = [
                {
                    "role": "system", 
                    "content": f"""You are a professional social media manager creating brand-safe, friendly replies.

Guidelines:
- Sentiment context: {sentiment}
- Keep replies under 240 characters
- Be brand-safe and professional
- Match the sentiment appropriately
- Be helpful and engaging"""
                },
                {
                    "role": "user", 
                    "content": f"Compose a reply to this message: {text}"
                }
            ]
            
            reply_result = await ai_manager.generate_text(
                messages=reply_messages,
                max_tokens=100,
                temperature=0.7
            )
            
            reply_text = reply_result.text_content if reply_result.success else ""
            
            # Save engagement event
            db = await get_supabase()
            async with db.get_session() as session:
                evt = EngagementEvent(
                    user_id=user_id, 
                    platform=platform, 
                    source="auto", 
                    post_ref="", 
                    actor_handle="", 
                    event_type="reply", 
                    text=reply_text, 
                    sentiment=sentiment, 
                    metadata={
                        "ai_model_used": reply_result.service_used,
                        "fallback_used": reply_result.fallback_used,
                        "response_time_ms": reply_result.response_time_ms
                    }
                )
                session.add(evt)
                await session.commit()
            
            return {
                "success": True,
                "sentiment": sentiment, 
                "reply": reply_text,
                "ai_model_used": reply_result.service_used,
                "fallback_used": reply_result.fallback_used
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Auto-reply generation failed: {str(e)}",
                "sentiment": "neutral",
                "reply": ""
            }


