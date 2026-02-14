from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.aria_chat_service import AriaChatService
from core.authentication.auth_manager import get_current_user
from core.database.connection import get_database as get_core_db
from core.database.models import UserSelectedAgent
from sqlalchemy import select
from ..models import AriaBrandProfile
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/aria-chat", tags=["Aria Chat Interface"])

aria_chat_service = AriaChatService()


from pydantic import BaseModel

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/message")
async def process_chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Process a chat message from the user and get Aria's response"""
    try:
        # Enforce per-agent pause/automation guard for Aria
        core_db = get_core_db()  # get_database() is synchronous, no await needed
        async with core_db.get_session() as core_session:
            res = await core_session.execute(
                select(UserSelectedAgent).where(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == "aria",
                )
            )
            row = res.scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=403, detail="Agent Aria is not selected")
            if row.status == "paused":
                raise HTTPException(status_code=403, detail="Agent Aria is paused")

        result = await aria_chat_service.process_chat_message(
            user_id=current_user.id,
            message=request.message,
            session_id=request.session_id,
            db=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Result was not successful but no exception raised
            error_msg = result.get('error', "AI Service returned failure")
            logger.error(f"Aria Chat Service returned failure: {error_msg}")
            raise HTTPException(
                status_code=500, 
                detail=error_msg
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message for Aria: {str(e)}", exc_info=True)
        # Return the actual error message for transparency during debugging
        raise HTTPException(
            status_code=500, 
            detail=str(e)
        )


@router.get("/suggestions/{user_id}")
async def get_chat_suggestions(user_id: int):
    """Get personalized chat suggestions for the user"""
    try:
        suggestions = await aria_chat_service.get_chat_suggestions(user_id)
        return {
            "success": True,
            "user_id": user_id,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat suggestions: {str(e)}")


@router.post("/session/end")
async def end_chat_session(session_id: str):
    """End a chat session and clean up"""
    try:
        result = await aria_chat_service.end_chat_session(session_id)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "session_duration": result["session_duration"],
                "total_messages": result["total_messages"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end chat session: {str(e)}")


@router.get("/history/{user_id}")
async def get_chat_history(
    user_id: int,
    session_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100)
):
    """Get chat history for a user or specific session"""
    try:
        result = await aria_chat_service.get_chat_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")


@router.get("/status")
async def get_chat_service_status():
    """Get the current status of the Aria chat service"""
    try:
        active_sessions = len(aria_chat_service.active_sessions)
        
        return {
            "success": True,
            "service_status": "active",
            "active_sessions": active_sessions,
            "features_available": [
                "Account analysis",
                "Content creation",
                "Post scheduling",
                "Performance analytics",
                "Trend monitoring",
                "Ad management",
                "Geo-targeted campaigns",
                "Voice interaction",
                "NLP processing"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service status: {str(e)}")


@router.post("/demo")
async def demo_chat_interaction():
    """Demonstrate Aria's chat capabilities with example interactions"""
    try:
        demo_conversations = [
            {
                "user_message": "Hello Aria!",
                "aria_response": "Hello! I'm Aria, your AI-powered social media management assistant. I'm here to help you manage your social media presence effectively.",
                "intent": "greeting",
                "suggested_actions": ["Analyze my accounts", "Create content", "Check analytics", "View trends"]
            },
            {
                "user_message": "Can you analyze my social media accounts?",
                "aria_response": "I'll analyze your connected social media accounts and provide detailed insights and recommendations for improvement. Let me scan your accounts to understand your current performance and identify opportunities for growth.",
                "intent": "account_management",
                "suggested_actions": ["Full account scan", "Platform-specific insights", "Health score details", "Improvement recommendations"]
            },
            {
                "user_message": "Help me create content for Instagram",
                "aria_response": "I can help you create engaging content with AI-generated captions, hashtags, and even generate images. What type of content would you like to create?",
                "intent": "content_creation",
                "suggested_actions": ["Generate captions", "Create hashtags", "Generate images", "Content remix"]
            },
            {
                "user_message": "What's trending in my industry?",
                "aria_response": "I'll monitor trending topics, hashtags, and conversations relevant to your brand and suggest content ideas. Let me keep you updated on the latest trends and help you create timely, relevant content that resonates with your audience.",
                "intent": "trends",
                "suggested_actions": ["Trending topics", "Popular hashtags", "Competitor analysis", "Content suggestions"]
            },
            {
                "user_message": "Create a campaign targeting Kenya and Nigeria",
                "aria_response": "I can help you create location-specific campaigns targeting specific regions, including African countries and cities like Kenya, Nairobi, and many more. Let's create geo-targeted campaigns! I can help you design campaigns for specific regions, including popular African locations and global markets.",
                "intent": "geo_campaigns",
                "suggested_actions": ["African markets", "Global regions", "Local targeting", "Cultural insights"]
            }
        ]
        
        return {
            "success": True,
            "demo_title": "Aria Chat Interface Demo",
            "description": "This demonstrates how users can interact with Aria through natural language chat",
            "conversations": demo_conversations,
            "features_demonstrated": [
                "Natural language processing",
                "Intent detection",
                "Contextual responses",
                "Actionable suggestions",
                "Multi-language support",
                "Platform-specific insights"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate demo: {str(e)}")


@router.get("/help")
async def get_chat_help():
    """Get comprehensive help information for using Aria's chat interface"""
    try:
        help_info = {
            "chat_interface": {
                "title": "Aria Chat Interface Help",
                "description": "Learn how to interact with Aria through natural language chat",
                "features": {
                    "natural_language": "Speak naturally - no need to learn specific commands",
                    "intent_recognition": "Aria understands what you want to do",
                    "contextual_responses": "Responses are tailored to your specific needs",
                    "actionable_suggestions": "Get specific next steps and recommendations"
                }
            },
            "common_interactions": {
                "account_management": [
                    "Analyze my accounts",
                    "How are my Instagram and LinkedIn performing?",
                    "What's my account health score?",
                    "Give me recommendations for improvement"
                ],
                "content_creation": [
                    "Create a caption about sustainable business",
                    "Generate hashtags for tech startup",
                    "Create an image for my product launch",
                    "Help me remix content for different platforms"
                ],
                "scheduling": [
                    "What are the best posting times?",
                    "Schedule a post for tomorrow",
                    "Create a weekly content calendar",
                    "Optimize schedule for multiple timezones"
                ],
                "analytics": [
                    "Show me my performance metrics",
                    "How is my engagement doing?",
                    "What's my audience like?",
                    "Show me growth trends"
                ],
                "trends": [
                    "What's trending in my industry?",
                    "Show me popular hashtags",
                    "What are my competitors doing?",
                    "Give me content ideas based on trends"
                ],
                "advertising": [
                    "Help me create Instagram ads",
                    "Set up LinkedIn advertising",
                    "Create a campaign for my target audience",
                    "Optimize my ad performance"
                ],
                "geo_campaigns": [
                    "Create a campaign for Kenya",
                    "Target African markets",
                    "Show me insights for Lagos",
                    "Create global region campaigns"
                ]
            },
            "tips_for_better_interactions": [
                "Be specific about what you want to accomplish",
                "Mention specific platforms when relevant",
                "Ask follow-up questions for deeper insights",
                "Use the suggested actions for quick navigation",
                "Let Aria know your business goals and target audience"
            ],
            "voice_interaction": {
                "available": True,
                "description": "You can also interact with Aria using voice commands",
                "supported_languages": ["English", "Multiple African languages", "Global languages"],
                "voice_features": [
                    "Voice-to-post creation",
                    "Voice commands for account management",
                    "Voice navigation through features",
                    "Accessibility support"
                ]
            }
        }
        
        return {
            "success": True,
            "help": help_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get help information: {str(e)}")
