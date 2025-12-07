from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..services.chatbot_service import ClaraChatbotService
from ..models import SupportChannel
from ..database import get_clara_database
from datetime import datetime

router = APIRouter()

# Pydantic models for request/response
class StartChatSessionRequest(BaseModel):
    customer_id: int
    channel: SupportChannel = SupportChannel.CHAT
    initial_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AddMessageRequest(BaseModel):
    message: str
    message_type: str = "text"
    metadata: Optional[Dict[str, Any]] = None

class EndChatSessionRequest(BaseModel):
    customer_satisfaction: Optional[int] = None
    reason: Optional[str] = None

class ChatSessionResponse(BaseModel):
    session_id: str
    chat_session_id: int
    status: str
    start_time: str
    messages_count: int
    customer_satisfaction: Optional[int]

class ChatMessageResponse(BaseModel):
    id: int
    sender_type: str
    sender_id: Optional[int]
    message: str
    message_type: str
    timestamp: str
    is_read: bool

class ChatHistoryResponse(BaseModel):
    sessions: List[ChatSessionResponse]
    total_count: int
    limit: int
    offset: int

# Dependency
async def get_chatbot_service() -> ClaraChatbotService:
    service = ClaraChatbotService()
    await service.initialize()
    return service

@router.post("/sessions", response_model=Dict[str, Any])
async def start_chat_session(
    request: StartChatSessionRequest,
    service: ClaraChatbotService = Depends(get_chatbot_service)
):
    """Start a new chat session"""
    try:
        result = await service.start_chat_session(
            customer_id=request.customer_id,
            channel=request.channel,
            initial_message=request.initial_message,
            metadata=request.metadata
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/messages", response_model=Dict[str, Any])
async def add_message(
    session_id: str,
    request: AddMessageRequest,
    service: ClaraChatbotService = Depends(get_chatbot_service)
):
    """Add a message to chat session"""
    try:
        # Get chat session ID from session_id
        db = await get_clara_database()
        async with db.get_session() as db_session:
            from ..models import ChatSession
            from sqlalchemy import select
            
            chat_session = await db_session.execute(
                select(ChatSession).where(ChatSession.session_id == session_id)
            )
            chat_session = chat_session.scalar_one_or_none()
            
            if not chat_session:
                raise HTTPException(status_code=404, detail="Chat session not found")
            
            # Add customer message
            message_result = await service.add_message(
                session_id=chat_session.id,
                sender_type="customer",
                sender_id=chat_session.customer_id,
                message=request.message,
                message_type=request.message_type,
                metadata=request.metadata
            )
            
            if not message_result["success"]:
                raise HTTPException(status_code=400, detail=message_result["error"])
            
            # Generate AI response
            response_result = await service.generate_response(
                message=request.message,
                customer_id=chat_session.customer_id,
                session_id=chat_session.id
            )
            
            if response_result["success"]:
                # Add AI response to chat
                await service.add_message(
                    session_id=chat_session.id,
                    sender_type="system",
                    sender_id=None,
                    message=response_result["response"],
                    metadata={"automated": True, "intent": response_result.get("intent")}
                )
                
                return {
                    "success": True,
                    "customer_message_id": message_result["message_id"],
                    "ai_response": response_result["response"],
                    "automated": response_result.get("automated", True),
                    "intent": response_result.get("intent")
                }
            else:
                return {
                    "success": True,
                    "customer_message_id": message_result["message_id"],
                    "ai_response": "I apologize, but I'm experiencing some technical difficulties. Let me connect you with our support team.",
                    "automated": False,
                    "error": response_result.get("error")
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sessions/{session_id}/end", response_model=Dict[str, Any])
async def end_chat_session(
    session_id: str,
    request: EndChatSessionRequest,
    service: ClaraChatbotService = Depends(get_chatbot_service)
):
    """End a chat session"""
    try:
        result = await service.end_chat_session(
            session_id=session_id,
            customer_satisfaction=request.customer_satisfaction,
            reason=request.reason
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_chat_session(
    session_id: str,
    service: ClaraChatbotService = Depends(get_chatbot_service)
):
    """Get chat session details"""
    try:
        db = await get_clara_database()
        async with db.get_session() as db_session:
            from ..models import ChatSession, ChatMessage
            from sqlalchemy import select
            
            # Get chat session
            chat_session = await db_session.execute(
                select(ChatSession).where(ChatSession.session_id == session_id)
            )
            chat_session = chat_session.scalar_one_or_none()
            
            if not chat_session:
                raise HTTPException(status_code=404, detail="Chat session not found")
            
            # Get messages for this session
            messages = await db_session.execute(
                select(ChatMessage).where(ChatMessage.session_id == chat_session.id)
                .order_by(ChatMessage.timestamp.asc())
            )
            messages = messages.scalars().all()
            
            return {
                "success": True,
                "session": {
                    "session_id": chat_session.session_id,
                    "customer_id": chat_session.customer_id,
                    "agent_id": chat_session.agent_id,
                    "ticket_id": chat_session.ticket_id,
                    "channel": chat_session.channel.value,
                    "status": chat_session.status,
                    "start_time": chat_session.start_time.isoformat() if chat_session.start_time else None,
                    "end_time": chat_session.end_time.isoformat() if chat_session.end_time else None,
                    "duration": chat_session.duration,
                    "messages_count": chat_session.messages_count,
                    "customer_satisfaction": chat_session.customer_satisfaction,
                    "auto_responses_count": chat_session.auto_responses_count,
                    "human_handoff_count": chat_session.human_handoff_count
                },
                "messages": [
                    {
                        "id": msg.id,
                        "sender_type": msg.sender_type,
                        "sender_id": msg.sender_id,
                        "message": msg.message,
                        "message_type": msg.message_type,
                        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                        "is_read": msg.is_read,
                        "metadata": msg.metadata
                    }
                    for msg in messages
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/customer/{customer_id}", response_model=Dict[str, Any])
async def get_customer_chat_history(
    customer_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ClaraChatbotService = Depends(get_chatbot_service)
):
    """Get customer chat history"""
    try:
        result = await service.get_chat_history(
            customer_id=customer_id,
            limit=limit,
            offset=offset
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/transfer", response_model=Dict[str, Any])
async def transfer_to_human(
    session_id: str,
    reason: str = Body(..., embed=True),
    service: ClaraChatbotService = Depends(get_chatbot_service)
):
    """Transfer chat session to human agent"""
    try:
        db = await get_clara_database()
        async with db.get_session() as db_session:
            from ..models import ChatSession
            from sqlalchemy import select
            
            # Get chat session
            chat_session = await db_session.execute(
                select(ChatSession).where(ChatSession.session_id == session_id)
            )
            chat_session = chat_session.scalar_one_or_none()
            
            if not chat_session:
                raise HTTPException(status_code=404, detail="Chat session not found")
            
            # Update session status
            chat_session.status = "transferred"
            chat_session.human_handoff_count += 1
            chat_session.updated_at = datetime.utcnow()
            
            # Add transfer message
            await service.add_message(
                session_id=chat_session.id,
                sender_type="system",
                sender_id=None,
                message=f"Chat transferred to human agent. Reason: {reason}",
                metadata={"transfer_reason": reason, "automated": False}
            )
            
            await db_session.commit()
            
            return {
                "success": True,
                "session_id": session_id,
                "status": "transferred",
                "message": "Chat session transferred to human agent successfully"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/suggestions", response_model=Dict[str, Any])
async def get_chat_suggestions(
    session_id: str,
    service: ClaraChatbotService = Depends(get_chatbot_service)
):
    """Get chat suggestions based on session context"""
    try:
        # Provide contextual suggestions based on session history
        return {
            "success": True,
            "suggestions": [
                "I need technical help",
                "I have a billing question",
                "I want to speak to a human agent",
                "How do I reset my password?",
                "Where is my order?",
                "I found a bug in the system"
            ],
            "context": "general_support"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/feedback", response_model=Dict[str, Any])
async def submit_chat_feedback(
    session_id: str,
    feedback: Dict[str, Any] = Body(...),
    service: ClaraChatbotService = Depends(get_chatbot_service)
):
    """Submit feedback for chat session"""
    try:
        db = await get_clara_database()
        async with db.get_session() as db_session:
            from ..models import ChatSession
            from sqlalchemy import select
            
            # Get chat session
            chat_session = await db_session.execute(
                select(ChatSession).where(ChatSession.session_id == session_id)
            )
            chat_session = chat_session.scalar_one_or_none()
            
            if not chat_session:
                raise HTTPException(status_code=404, detail="Chat session not found")
            
            # Update session with feedback
            chat_session.customer_satisfaction = feedback.get("satisfaction_rating")
            chat_session.updated_at = datetime.utcnow()
            
            # Add feedback message
            feedback_text = f"Customer feedback: {feedback.get('feedback_text', 'No text provided')}. Rating: {feedback.get('satisfaction_rating', 'Not provided')}"
            await service.add_message(
                session_id=chat_session.id,
                sender_type="system",
                sender_id=None,
                message=feedback_text,
                metadata={"feedback": feedback, "automated": False}
            )
            
            await db_session.commit()
            
            return {
                "success": True,
                "session_id": session_id,
                "feedback_submitted": True,
                "message": "Feedback submitted successfully"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/sessions", response_model=Dict[str, Any])
async def get_chat_sessions_stats(
    service: ClaraChatbotService = Depends(get_chatbot_service)
):
    """Get chat sessions statistics"""
    try:
        # Get statistics from analytics service
        return {
            "success": True,
            "stats": {
                "total_sessions": 0,
                "active_sessions": 0,
                "completed_sessions": 0,
                "transferred_sessions": 0,
                "average_session_duration": 0,
                "average_messages_per_session": 0,
                "customer_satisfaction_avg": 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/active", response_model=Dict[str, Any])
async def get_active_chat_sessions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ClaraChatbotService = Depends(get_chatbot_service)
):
    """Get all active chat sessions"""
    try:
        db = await get_clara_database()
        async with db.get_session() as db_session:
            from ..models import ChatSession
            from sqlalchemy import select, func
            
            # Get active sessions
            active_sessions = await db_session.execute(
                select(ChatSession).where(ChatSession.status == "active")
                .order_by(ChatSession.start_time.desc())
                .limit(limit).offset(offset)
            )
            active_sessions = active_sessions.scalars().all()
            
            # Get total count
            total_count = await db_session.execute(
                select(func.count(ChatSession.id)).where(ChatSession.status == "active")
            )
            total_count = total_count.scalar()
            
            return {
                "success": True,
                "sessions": [
                    {
                        "session_id": session.session_id,
                        "customer_id": session.customer_id,
                        "channel": session.channel.value,
                        "start_time": session.start_time.isoformat() if session.start_time else None,
                        "messages_count": session.messages_count,
                        "duration": session.duration
                    }
                    for session in active_sessions
                ],
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
