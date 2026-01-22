import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import JackieChatbotConversation, JackieEmpathyResponse, JackieContextSession, JackieConversationFlow

class HumanChatbotService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def generate_empathetic_response(self, user_message: str, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        response_id = str(uuid.uuid4())
        response_result = self.nlp_processor.generate_empathetic_response(f"User Message: {user_message}")
        
        response = JackieEmpathyResponse(
            id=response_id, user_message=user_message, conversation_context=json.dumps(conversation_context),
            response_content=json.dumps(response_result), created_at=datetime.utcnow()
        )
        self.db.add(response)
        self.db.commit()
        
        return {"response_id": response_id, "response_content": response_result}
    
    def create_conversation_session(self, user_id: str, session_type: str = "marketing_support") -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        
        session = JackieContextSession(
            id=session_id, user_id=user_id, session_type=session_type,
            status="active", created_at=datetime.utcnow()
        )
        self.db.add(session)
        self.db.commit()
        
        return {"session_id": session_id, "session_type": session_type}
    
    def get_chatbot_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        conversations_count = self.db.query(JackieChatbotConversation).filter(JackieChatbotConversation.created_at >= cutoff_date).count()
        empathetic_responses = self.db.query(JackieEmpathyResponse).filter(JackieEmpathyResponse.created_at >= cutoff_date).count()
        active_sessions = self.db.query(JackieContextSession).filter(JackieContextSession.created_at >= cutoff_date, JackieContextSession.status == "active").count()
        
        return {
            "timeframe": timeframe, "conversations_count": conversations_count,
            "empathetic_responses": empathetic_responses, "active_sessions": active_sessions
        }
