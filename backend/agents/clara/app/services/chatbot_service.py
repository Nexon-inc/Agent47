import uuid
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.cache.redis_manager import init_redis
from ..database import get_clara_database
from ..models import (
    ChatSession, ChatMessage, KnowledgeBase, SupportTicket,
    CustomerInteraction, TicketCategory, SupportChannel,
    SentimentType, InteractionType
)

logger = logging.getLogger(__name__)

class ChatbotService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.redis_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize chatbot service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            self.redis_client = await init_redis()
            self._initialized = True
            logger.info("Clara chatbot service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize chatbot service: {e}")
            raise
    
    async def start_chat_session(
        self,
        customer_id: int,
        channel: SupportChannel = SupportChannel.CHAT,
        initial_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Start a new chat session"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Generate session ID
                session_id = f"CHAT-{uuid.uuid4().hex[:16]}"
                
                # Create chat session
                chat_session = ChatSession(
                    session_id=session_id,
                    customer_id=customer_id,
                    channel=channel,
                    status="active",
                    start_time=datetime.utcnow(),
                    metadata=metadata or {}
                )
                session.add(chat_session)
                await session.flush()
                
                # Add initial message if provided
                if initial_message:
                    await self.add_message(
                        session_id=chat_session.id,
                        sender_type="customer",
                        sender_id=customer_id,
                        message=initial_message,
                        session=session
                    )
                    
                    # Generate automated response
                    response = await self.generate_response(
                        message=initial_message,
                        customer_id=customer_id,
                        session_id=chat_session.id,
                        session=session
                    )
                    
                    if response["success"]:
                        await self.add_message(
                            session_id=chat_session.id,
                            sender_type="system",
                            sender_id=None,
                            message=response["response"],
                            session=session
                        )
                        chat_session.auto_responses_count += 1
                
                await session.commit()
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "chat_session_id": chat_session.id,
                    "status": "active"
                }
                
        except Exception as e:
            logger.error(f"Failed to start chat session: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_message(
        self,
        session_id: int,
        sender_type: str,
        sender_id: Optional[int],
        message: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Add a message to chat session"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            use_external_session = session is not None
            
            if not use_external_session:
                session = await db.get_session()
            
            # Create chat message
            chat_message = ChatMessage(
                session_id=session_id,
                sender_type=sender_type,
                sender_id=sender_id,
                message=message,
                message_type=message_type,
                metadata=metadata or {},
                timestamp=datetime.utcnow()
            )
            session.add(chat_message)
            
            # Update session message count
            await session.execute(
                select(ChatSession).where(ChatSession.id == session_id)
            )
            chat_session = session.execute(
                select(ChatSession).where(ChatSession.id == session_id)
            ).scalar_one_or_none()
            
            if chat_session:
                chat_session.messages_count += 1
                chat_session.updated_at = datetime.utcnow()
            
            if not use_external_session:
                await session.commit()
                await session.close()
            
            return {"success": True, "message_id": chat_message.id}
            
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_response(
        self,
        message: str,
        customer_id: int,
        session_id: int,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Generate intelligent response using AI and knowledge base"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Analyze user intent
            intent_result = await self._analyze_intent(message)
            if not intent_result["success"]:
                return {"success": False, "error": "Failed to analyze intent"}
            
            intent = intent_result["intent"]
            
            # Check if we need human handoff
            if intent["confidence"] < 0.7 or intent["complexity"] == "high":
                return await self._handle_complex_request(message, customer_id, session_id, session)
            
            # Search knowledge base for relevant information
            kb_result = await self._search_knowledge_base(message, intent)
            
            # Generate contextual response
            response = await self._generate_contextual_response(
                message=message,
                intent=intent,
                knowledge_base_result=kb_result,
                customer_id=customer_id
            )
            
            if response["success"]:
                # Update session metrics
                if not session:
                    db = await get_clara_database()
                    async with db.get_session() as db_session:
                        await self._update_session_metrics(session_id, db_session)
                else:
                    await self._update_session_metrics(session_id, session)
                
                return {
                    "success": True,
                    "response": response["response"],
                    "intent": intent,
                    "knowledge_used": kb_result["success"] if kb_result else False,
                    "automated": True
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return {"success": False, "error": str(e)}
    
    async def end_chat_session(
        self,
        session_id: int,
        customer_satisfaction: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """End a chat session"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get chat session
                chat_session = await session.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                )
                chat_session = chat_session.scalar_one_or_none()
                
                if not chat_session:
                    return {"success": False, "error": "Chat session not found"}
                
                # Update session
                chat_session.status = "closed"
                chat_session.end_time = datetime.utcnow()
                chat_session.duration = int((chat_session.end_time - chat_session.start_time).total_seconds())
                
                if customer_satisfaction:
                    chat_session.customer_satisfaction = customer_satisfaction
                
                # Add closing message
                closing_message = "Thank you for chatting with Clara! Your session has ended."
                if reason:
                    closing_message += f" Reason: {reason}"
                
                await self.add_message(
                    session_id=chat_session.id,
                    sender_type="system",
                    sender_id=None,
                    message=closing_message,
                    session=session
                )
                
                await session.commit()
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "duration": chat_session.duration,
                    "messages_count": chat_session.messages_count
                }
                
        except Exception as e:
            logger.error(f"Failed to end chat session: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_chat_history(
        self,
        customer_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get customer chat history"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get chat sessions
                sessions_query = select(ChatSession).where(
                    ChatSession.customer_id == customer_id
                ).order_by(ChatSession.start_time.desc()).limit(limit).offset(offset)
                
                chat_sessions = await session.execute(sessions_query)
                chat_sessions = chat_sessions.scalars().all()
                
                # Get total count
                total_count = await session.execute(
                    select(func.count(ChatSession.id)).where(ChatSession.customer_id == customer_id)
                )
                total_count = total_count.scalar()
                
                sessions_data = []
                for chat_session in chat_sessions:
                    # Get messages for this session
                    messages_query = select(ChatMessage).where(
                        ChatMessage.session_id == chat_session.id
                    ).order_by(ChatMessage.timestamp.asc()).limit(10)  # Last 10 messages
                    
                    messages = await session.execute(messages_query)
                    messages = messages.scalars().all()
                    
                    sessions_data.append({
                        "session_id": chat_session.session_id,
                        "status": chat_session.status,
                        "start_time": chat_session.start_time.isoformat() if chat_session.start_time else None,
                        "end_time": chat_session.end_time.isoformat() if chat_session.end_time else None,
                        "duration": chat_session.duration,
                        "messages_count": chat_session.messages_count,
                        "customer_satisfaction": chat_session.customer_satisfaction,
                        "messages": [
                            {
                                "id": msg.id,
                                "sender_type": msg.sender_type,
                                "message": msg.message,
                                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                            }
                            for msg in messages
                        ]
                    })
                
                return {
                    "success": True,
                    "sessions": sessions_data,
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset
                }
                
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user intent using NLP"""
        try:
            intent_prompt = f"""Analyze this customer message and determine:
1. Intent (what they want to accomplish)
2. Category (technical, billing, general, etc.)
3. Urgency level (1-5, where 5 is most urgent)
4. Complexity (simple, moderate, complex, high)
5. Sentiment (positive, neutral, negative, frustrated)
6. Confidence score (0.0-1.0)

Respond with a JSON object containing these fields.

Message: {message}"""
            
            messages = [
                {"role": "system", "content": intent_prompt},
                {"role": "user", "content": message}
            ]
            
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=200,
                temperature=0.3
            )
            
            if response.success:
                try:
                    intent_data = json.loads(response.text_content)
                    return {
                        "success": True,
                        "intent": {
                            "intent": intent_data.get("intent", "general_inquiry"),
                            "category": intent_data.get("category", "general"),
                            "urgency": intent_data.get("urgency", 3),
                            "complexity": intent_data.get("complexity", "moderate"),
                            "sentiment": intent_data.get("sentiment", "neutral"),
                            "confidence": intent_data.get("confidence", 0.7)
                        }
                    }
                except (json.JSONDecodeError, KeyError):
                    pass
            
            # Fallback intent analysis
            message_lower = message.lower()
            
            # Simple keyword-based intent detection
            if any(word in message_lower for word in ["error", "broken", "not working", "issue"]):
                intent = "technical_support"
                category = "technical"
                urgency = 4
                complexity = "moderate"
            elif any(word in message_lower for word in ["bill", "payment", "charge", "refund"]):
                intent = "billing_inquiry"
                category = "billing"
                urgency = 3
                complexity = "simple"
            elif any(word in message_lower for word in ["how to", "guide", "tutorial", "help"]):
                intent = "how_to_help"
                category = "general"
                urgency = 2
                complexity = "simple"
            else:
                intent = "general_inquiry"
                category = "general"
                urgency = 2
                complexity = "simple"
            
            return {
                "success": True,
                "intent": {
                    "intent": intent,
                    "category": category,
                    "urgency": urgency,
                    "complexity": complexity,
                    "sentiment": "neutral",
                    "confidence": 0.6
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze intent: {e}")
            return {
                "success": True,
                "intent": {
                    "intent": "general_inquiry",
                    "category": "general",
                    "urgency": 2,
                    "complexity": "simple",
                    "sentiment": "neutral",
                    "confidence": 0.5
                }
            }
    
    async def _search_knowledge_base(
        self,
        message: str,
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search knowledge base for relevant information"""
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Search by category and keywords
                query = select(KnowledgeBase).where(
                    and_(
                        KnowledgeBase.is_public == True,
                        or_(
                            KnowledgeBase.category == intent["category"],
                            KnowledgeBase.tags.contains([intent["category"]]),
                            KnowledgeBase.keywords.contains([intent["category"]])
                        )
                    )
                ).order_by(KnowledgeBase.success_rate.desc(), KnowledgeBase.usage_count.desc())
                
                results = await session.execute(query)
                results = results.scalars().all()
                
                if results:
                    # Find best match using semantic similarity
                    best_match = None
                    best_score = 0.0
                    
                    for kb_item in results[:5]:  # Check top 5 results
                        similarity = await self._calculate_semantic_similarity(message, kb_item.question)
                        if similarity > best_score:
                            best_score = similarity
                            best_match = kb_item
                    
                    if best_match and best_score > 0.7:
                        return {
                            "success": True,
                            "knowledge_item": {
                                "id": best_match.id,
                                "title": best_match.title,
                                "question": best_match.question,
                                "answer": best_match.answer,
                                "category": best_match.category,
                                "similarity_score": best_score
                            }
                        }
                
                return {"success": False, "message": "No relevant knowledge base items found"}
                
        except Exception as e:
            logger.error(f"Failed to search knowledge base: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_contextual_response(
        self,
        message: str,
        intent: Dict[str, Any],
        knowledge_base_result: Dict[str, Any],
        customer_id: int
    ) -> Dict[str, Any]:
        """Generate contextual response using AI"""
        try:
            # Build context-aware prompt
            context = f"""You are Clara, an AI customer support assistant. Generate a helpful, empathetic response.

Customer Message: {message}
Intent: {intent['intent']}
Category: {intent['category']}
Urgency: {intent['urgency']}/5
Complexity: {intent['complexity']}

{f"Knowledge Base Answer: {knowledge_base_result['knowledge_item']['answer']}" if knowledge_base_result.get('success') else "No specific knowledge base match found."}

Guidelines:
- Be helpful, professional, and empathetic
- Keep responses concise but informative
- If you have knowledge base information, use it
- If the issue seems complex, suggest creating a support ticket
- Always offer to help further if needed

Generate a natural, helpful response:"""

            messages = [
                {"role": "system", "content": context},
                {"role": "user", "content": message}
            ]
            
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            if response.success:
                return {
                    "success": True,
                    "response": response.text_content
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"Failed to generate contextual response: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_complex_request(
        self,
        message: str,
        customer_id: int,
        session_id: int,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Handle complex requests that need human intervention"""
        try:
            # Create support ticket
            from .support_service import SupportService
            support_service = SupportService()
            await support_service.initialize()
            
            # Determine category
            category_mapping = {
                "technical": "technical",
                "billing": "billing",
                "account": "account_issue",
                "general": "general"
            }
            
            category = category_mapping.get("general", "general")
            
            ticket_result = await support_service.create_ticket(
                customer_id=customer_id,
                channel=SupportChannel.CHAT,
                category=category,
                subject="Complex chat request requiring human support",
                description=f"Original message: {message}\n\nThis request was escalated from chat due to complexity.",
                priority="medium",
                metadata={"chat_session_id": session_id, "escalated_from_chat": True}
            )
            
            if ticket_result["success"]:
                response = f"I understand your request requires more detailed assistance. I've created a support ticket (#{ticket_result['ticket']['ticket_number']}) and assigned it to our support team. They'll get back to you shortly with a comprehensive solution. Is there anything else I can help you with in the meantime?"
                
                return {
                    "success": True,
                    "response": response,
                    "ticket_created": True,
                    "ticket_number": ticket_result['ticket']['ticket_number'],
                    "automated": False
                }
            else:
                return {
                    "success": True,
                    "response": "I understand your request is complex and I want to ensure you get the best possible help. Let me connect you with our support team. Please hold while I transfer you.",
                    "ticket_created": False,
                    "automated": False
                }
                
        except Exception as e:
            logger.error(f"Failed to handle complex request: {e}")
            return {
                "success": True,
                "response": "I apologize, but I'm experiencing some technical difficulties. Let me connect you with our support team right away.",
                "automated": False
            }
    
    async def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        try:
            # Simple cosine similarity using word overlap
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            if len(union) == 0:
                return 0.0
            
            return len(intersection) / len(union)
            
        except Exception as e:
            logger.error(f"Failed to calculate semantic similarity: {e}")
            return 0.0
    
    async def _update_session_metrics(self, session_id: int, session: AsyncSession):
        """Update chat session metrics"""
        try:
            # Update message count and other metrics
            chat_session = await session.execute(
                select(ChatSession).where(ChatSession.id == session_id)
            )
            chat_session = chat_session.scalar_one_or_none()
            
            if chat_session:
                chat_session.updated_at = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Failed to update session metrics: {e}")


# Backwards compatibility: some modules expect the class to be named ClaraChatbotService
ClaraChatbotService = ChatbotService
