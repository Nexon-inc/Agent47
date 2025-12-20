from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import logging

from ..services.live_chat_service import LiveChatService
from core.authentication.auth_manager import AuthManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/live-chat", tags=["Live Chat"])

# Pydantic models
class ChatMessageRequest(BaseModel):
    session_id: str
    message: str
    user_data: Dict[str, Any] = {}

class SessionRequest(BaseModel):
    session_id: str
    session_data: Dict[str, Any] = {}

class InteractionRequest(BaseModel):
    session_id: str
    interaction_data: Dict[str, Any]

class EscalationRequest(BaseModel):
    session_id: str
    escalation_reason: str

class WidgetConfigRequest(BaseModel):
    brand_id: str
    widget_config: Dict[str, Any]

class AnalyticsRequest(BaseModel):
    brand_id: str
    time_period: str = "30d"

# Initialize services
live_chat_service = LiveChatService()
auth_manager = AuthManager()

@router.post("/message")
async def handle_chat_message(request: ChatMessageRequest):
    """Handle incoming chat message"""
    try:
        result = await live_chat_service.handle_chat_message(
            request.session_id,
            request.message,
            request.user_data
        )
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session")
async def manage_chat_session(request: SessionRequest):
    """Manage chat session lifecycle"""
    try:
        result = await live_chat_service.manage_chat_session(
            request.session_id,
            request.session_data
        )
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error managing chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interaction")
async def handle_real_time_interaction(request: InteractionRequest):
    """Handle real-time chat interaction"""
    try:
        result = await live_chat_service.handle_real_time_interactions(
            request.session_id,
            request.interaction_data
        )
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error handling real-time interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/escalate")
async def escalate_to_human_agent(request: EscalationRequest):
    """Escalate chat to human agent"""
    try:
        result = await live_chat_service.escalate_to_human_agent(
            request.session_id,
            request.escalation_reason
        )
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error escalating to human agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{brand_id}")
async def get_chat_analytics(brand_id: str, time_period: str = "30d"):
    """Get chat analytics and performance metrics"""
    try:
        result = await live_chat_service.track_chat_analytics(brand_id, time_period)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting chat analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/widget/configure")
async def configure_chat_widget(request: WidgetConfigRequest):
    """Configure chat widget settings"""
    try:
        result = await live_chat_service.configure_chat_widget(
            request.brand_id,
            request.widget_config
        )
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error configuring chat widget: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/widget/{brand_id}")
async def get_widget_config(brand_id: str):
    """Get current widget configuration"""
    try:
        # This would typically fetch from database
        widget_config = {
            "brand_id": brand_id,
            "position": "bottom-right",
            "theme": "light",
            "greeting_message": "Hello! How can I help you today?",
            "brand_colors": "#007bff",
            "status": "active"
        }
        return {
            "success": True,
            "data": widget_config,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting widget config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    try:
        # This would typically fetch from database
        session_info = {
            "session_id": session_id,
            "status": "active",
            "start_time": datetime.utcnow(),
            "message_count": 5,
            "current_agent": "ai_assistant"
        }
        return {
            "success": True,
            "data": session_info,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/available")
async def get_available_agents():
    """Get list of available human agents"""
    try:
        available_agents = [
            {
                "agent_id": "agent_001",
                "agent_name": "Sarah Johnson",
                "specialization": "sales",
                "availability": "online",
                "current_sessions": 2
            },
            {
                "agent_id": "agent_002",
                "agent_name": "Mike Chen",
                "specialization": "technical",
                "availability": "online",
                "current_sessions": 1
            }
        ]
        return {
            "success": True,
            "data": available_agents,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting available agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/end")
async def end_chat_session(session_id: str):
    """End a chat session"""
    try:
        # This would typically update database
        result = {
            "session_id": session_id,
            "status": "ended",
            "end_time": datetime.utcnow(),
            "total_duration": "15 minutes",
            "messages_exchanged": 8
        }
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error ending chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/{brand_id}")
async def get_chat_performance(brand_id: str):
    """Get chat performance metrics"""
    try:
        performance_metrics = {
            "brand_id": brand_id,
            "total_sessions": 500,
            "average_session_duration": 8.5,
            "ai_resolution_rate": 0.75,
            "human_escalation_rate": 0.25,
            "customer_satisfaction": 4.2,
            "response_time_avg": 2.3
        }
        return {
            "success": True,
            "data": performance_metrics,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting chat performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/transfer")
async def transfer_session(session_id: str, agent_id: str):
    """Transfer session to specific agent"""
    try:
        result = {
            "session_id": session_id,
            "agent_id": agent_id,
            "transfer_successful": True,
            "transfer_time": datetime.utcnow()
        }
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error transferring session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_response_templates():
    """Get available response templates"""
    try:
        templates = [
            {
                "template_id": "greeting",
                "name": "Welcome Greeting",
                "content": "Hello! Welcome to our chat. How can I assist you today?",
                "category": "greeting"
            },
            {
                "template_id": "product_info",
                "name": "Product Information",
                "content": "Our product offers advanced features including AI-powered automation and real-time analytics.",
                "category": "product"
            },
            {
                "template_id": "pricing_info",
                "name": "Pricing Information",
                "content": "Our pricing starts at $99/month for the Starter plan with different features for each tier.",
                "category": "pricing"
            }
        ]
        return {
            "success": True,
            "data": templates,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting response templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/notes")
async def add_session_notes(session_id: str, notes: str):
    """Add notes to chat session"""
    try:
        result = {
            "session_id": session_id,
            "notes": notes,
            "added_at": datetime.utcnow(),
            "added_by": "system"
        }
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error adding session notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get chat session history"""
    try:
        history = [
            {
                "message_id": "msg_001",
                "sender": "user",
                "content": "Hello, I'm interested in your product",
                "timestamp": datetime.utcnow()
            },
            {
                "message_id": "msg_002",
                "sender": "ai",
                "content": "Great! I'd be happy to help you learn about our product.",
                "timestamp": datetime.utcnow()
            }
        ]
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "messages": history
            },
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting session history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time chat
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message through service
            result = await live_chat_service.handle_chat_message(
                session_id,
                message_data.get("message", ""),
                message_data.get("user_data", {})
            )
            
            # Send response back to client
            await websocket.send_text(json.dumps(result))
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
