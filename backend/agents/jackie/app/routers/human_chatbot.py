from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.human_chatbot_service import HumanChatbotService

router = APIRouter(prefix="/human-chatbot", tags=["Human-Like Chatbot Responses"])

@router.post("/empathetic-response")
def generate_empathetic_response(user_message: str, conversation_context: Dict[str, Any], 
                               db: Session = Depends(get_db)):
    service = HumanChatbotService(db)
    return service.generate_empathetic_response(user_message, conversation_context)

@router.post("/conversation-session")
def create_conversation_session(user_id: str, session_type: str = "marketing_support", 
                              db: Session = Depends(get_db)):
    service = HumanChatbotService(db)
    return service.create_conversation_session(user_id, session_type)

@router.get("/analytics")
def get_chatbot_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = HumanChatbotService(db)
    return service.get_chatbot_analytics(timeframe)
