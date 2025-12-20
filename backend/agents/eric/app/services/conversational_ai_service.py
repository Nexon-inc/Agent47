import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc

from core.ai import get_ai_service_manager, AIServiceManager
from core.cache.redis_manager import init_redis
from core.storage.chroma_manager import ChromaManager
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
from ..models import Lead, LeadInteraction, CommunicationChannel
from ..database import get_eric_database

logger = logging.getLogger(__name__)

class ConversationalAIService:
    """Service for conversational AI and chatbot interactions"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.redis_client = None
        self.chroma_manager = None
        self.integration_manager = None
        self.platform_manager = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize conversational AI service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            self.redis_client = await init_redis()
            self.chroma_manager = ChromaManager()
            await self.chroma_manager.initialize()
            self.integration_manager = IntegrationManager()
            await self.integration_manager.initialize()
            self.platform_manager = PlatformManager()
            await self.platform_manager.initialize()
            self._initialized = True
            logger.info("Eric conversational AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize conversational AI service: {e}")
            raise
    
    async def process_chat_message(
        self,
        lead_id: int,
        message: str,
        context: Dict[str, Any],
        channel: str = "chat"
    ) -> Dict[str, Any]:
        """Process incoming chat message and generate response"""
        try:
            await self.initialize()
            
            eric_db = await get_eric_database()
            async with eric_db.get_session() as db:
                from sqlalchemy import select
                result = await db.execute(select(Lead).where(Lead.id == lead_id))
                lead = result.scalar_one_or_none()
                
                if not lead:
                    return {
                        "success": False,
                        "error": "Lead not found"
                    }
                
                # Analyze message intent
                intent_analysis = await self._analyze_message_intent(message, context)
                
                # Generate contextual response
                response = await self._generate_contextual_response(
                    message,
                    lead,
                    intent_analysis,
                    context
                )
                
                # Record interaction
                interaction = LeadInteraction(
                    lead_id=lead_id,
                    interaction_type="chat_message",
                    channel=CommunicationChannel.CHAT,
                    content=message,
                    sentiment_score=intent_analysis.get("sentiment_score"),
                    engagement_score=intent_analysis.get("engagement_score"),
                    outcome="responded",
                    metadata={
                        "intent": intent_analysis.get("intent"),
                        "confidence": intent_analysis.get("confidence"),
                        "response": response.get("message"),
                        "channel": channel
                    }
                )
                db.add(interaction)
                await db.commit()
            
            return {
                "success": True,
                "response": response.get("message"),
                "intent": intent_analysis.get("intent"),
                "confidence": intent_analysis.get("confidence"),
                "suggested_actions": response.get("suggested_actions", []),
                "next_steps": response.get("next_steps", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to process chat message: {e}")
            return {
                "success": False,
                "error": f"Failed to process chat message: {str(e)}"
            }
    
    async def handle_voice_interaction(
        self,
        lead_id: int,
        audio_data: bytes,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle voice interaction and generate voice response"""
        try:
            await self.initialize()
            
            eric_db = await get_eric_database()
            async with eric_db.get_session() as db:
                from sqlalchemy import select
                result = await db.execute(select(Lead).where(Lead.id == lead_id))
                lead = result.scalar_one_or_none()
                
                if not lead:
                    return {
                        "success": False,
                        "error": "Lead not found"
                    }
                
                # Transcribe audio to text using Groq STT
                transcription = await self.ai_service_manager.transcribe_audio(
                    audio_data=audio_data,
                    audio_format=None,  # Auto-detect format
                    language=None  # Auto-detect language
                )
                
                if not transcription.get("success"):
                    return {
                        "success": False,
                        "error": transcription.get("error", "Failed to transcribe audio")
                    }
                
                message = transcription.get("text", "")
                
                # Process the transcribed message
                chat_response = await self.process_chat_message(lead_id, message, context, "voice")
                
                if not chat_response.get("success"):
                    return chat_response
                
                # Generate voice response using Groq TTS
                response_text = chat_response.get("response", "")
                voice_response = await self.ai_service_manager.text_to_speech(
                    text=response_text,
                    voice=None,  # Use default Groq voice
                    language="en",
                    speed=1.0,
                    pitch=1.0
                )
                
                if not voice_response.get("success"):
                    return {
                        "success": False,
                        "error": voice_response.get("error", "Failed to generate voice response")
                    }
                
                return {
                    "success": True,
                    "transcription": message,
                    "response_text": chat_response.get("response"),
                    "response_audio": voice_response.get("audio_data"),
                "intent": chat_response.get("intent"),
                "suggested_actions": chat_response.get("suggested_actions", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to handle voice interaction: {e}")
            return {
                "success": False,
                "error": f"Failed to handle voice interaction: {str(e)}"
            }
    
    async def schedule_demo(
        self,
        lead_id: int,
        demo_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Schedule a demo for the lead"""
        try:
            await self.initialize()
            
            eric_db = await get_eric_database()
            async with eric_db.get_session() as db:
                from sqlalchemy import select
                result = await db.execute(select(Lead).where(Lead.id == lead_id))
                lead = result.scalar_one_or_none()
                
                if not lead:
                    return {
                        "success": False,
                        "error": "Lead not found"
                    }
                
                # Generate demo scheduling response
                demo_response = await self._generate_demo_scheduling_response(lead, demo_preferences)
                
                # Create demo scheduling interaction
                interaction = LeadInteraction(
                    lead_id=lead_id,
                    interaction_type="demo_scheduled",
                    channel=CommunicationChannel.CHAT,
                    content=f"Demo scheduled for {demo_preferences.get('preferred_date')}",
                    outcome="demo_scheduled",
                    metadata={
                        "demo_preferences": demo_preferences,
                        "demo_response": demo_response
                    }
                )
                db.add(interaction)
                
                # Update lead status
                lead.lead_status = "qualified"
                lead.engagement_history = lead.engagement_history or {}
                lead.engagement_history.update({
                    "demo_scheduled": {
                        "date": demo_preferences.get("preferred_date"),
                        "time": demo_preferences.get("preferred_time"),
                        "duration": demo_preferences.get("duration", "30 minutes"),
                        "type": demo_preferences.get("demo_type", "product_demo")
                    }
                })
                await db.commit()
            
            return {
                "success": True,
                "demo_scheduled": True,
                "demo_date": demo_preferences.get("preferred_date"),
                "demo_time": demo_preferences.get("preferred_time"),
                "confirmation_message": demo_response,
                "next_steps": [
                    "Calendar invitation will be sent",
                    "Pre-demo questionnaire will be shared",
                    "Demo preparation materials will be provided"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule demo: {e}")
            return {
                "success": False,
                "error": f"Failed to schedule demo: {str(e)}"
            }
    
    async def answer_product_questions(
        self,
        lead_id: int,
        question: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Answer product-related questions"""
        try:
            await self.initialize()
            
            eric_db = await get_eric_database()
            async with eric_db.get_session() as db:
                from sqlalchemy import select
                result = await db.execute(select(Lead).where(Lead.id == lead_id))
                lead = result.scalar_one_or_none()
                
                if not lead:
                    return {
                        "success": False,
                        "error": "Lead not found"
                    }
                
                # Search knowledge base for relevant information
                knowledge_response = await self._search_knowledge_base(question, context)
                
                # Generate personalized answer
                answer = await self._generate_product_answer(
                    question,
                    lead,
                    knowledge_response,
                    context
                )
                
                # Record interaction
                interaction = LeadInteraction(
                    lead_id=lead_id,
                    interaction_type="product_question",
                    channel=CommunicationChannel.CHAT,
                    content=question,
                    outcome="answered",
                    metadata={
                        "question": question,
                        "answer": answer.get("response"),
                        "knowledge_sources": knowledge_response.get("sources", [])
                    }
                )
                db.add(interaction)
                await db.commit()
            
            return {
                "success": True,
                "question": question,
                "answer": answer.get("response"),
                "confidence": answer.get("confidence"),
                "related_topics": answer.get("related_topics", []),
                "suggested_resources": answer.get("suggested_resources", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to answer product question: {e}")
            return {
                "success": False,
                "error": f"Failed to answer product question: {str(e)}"
            }
    
    async def get_conversation_history(
        self,
        lead_id: int,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get conversation history for lead"""
        try:
            await self.initialize()
            
            eric_db = await get_eric_database()
            async with eric_db.get_session() as db:
                from sqlalchemy import select
                # Get recent interactions
                result = await db.execute(
                    select(LeadInteraction)
                    .where(LeadInteraction.lead_id == lead_id)
                    .order_by(desc(LeadInteraction.created_at))
                    .limit(limit)
                )
                interactions = result.scalars().all()
                
                conversation_history = []
                for interaction in interactions:
                    conversation_history.append({
                        "id": interaction.id,
                        "timestamp": interaction.created_at.isoformat(),
                        "type": interaction.interaction_type,
                        "channel": interaction.channel.value,
                        "content": interaction.content,
                        "outcome": interaction.outcome,
                        "sentiment_score": interaction.sentiment_score,
                        "engagement_score": interaction.engagement_score
                    })
            
            return {
                "success": True,
                "lead_id": lead_id,
                "conversation_history": conversation_history,
                "total_interactions": len(conversation_history)
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return {
                "success": False,
                "error": f"Failed to get conversation history: {str(e)}"
            }
    
    async def _analyze_message_intent(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze message intent and sentiment"""
        try:
            # Use NLP to analyze intent
            intent_prompt = f"""
            Analyze this sales conversation message and determine:
            1. Intent (demo_request, product_question, pricing_inquiry, objection, general_inquiry)
            2. Sentiment (positive, neutral, negative)
            3. Urgency level (low, medium, high)
            4. Engagement level (low, medium, high)
            
            Message: "{message}"
            Context: {context}
            
            Provide analysis in JSON format.
            """
            
            messages = [
                {"role": "system", "content": intent_prompt},
                {"role": "user", "content": message}
            ]
            
            intent_analysis = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=200,
                temperature=0.3
            )
            
            # Parse the analysis
            try:
                analysis_data = json.loads(intent_analysis.text_content) if intent_analysis.success else {}
            except:
                # Fallback analysis
                analysis_data = {
                    "intent": "general_inquiry",
                    "confidence": 0.7,
                    "sentiment": "neutral",
                    "sentiment_score": 0.5,
                    "urgency": "medium",
                    "engagement": "medium",
                    "engagement_score": 0.5
                }
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"Failed to analyze message intent: {e}")
            return {
                "intent": "general_inquiry",
                "confidence": 0.5,
                "sentiment": "neutral",
                "sentiment_score": 0.5,
                "urgency": "medium",
                "engagement": "medium",
                "engagement_score": 0.5
            }
    
    async def _generate_contextual_response(
        self,
        message: str,
        lead: Lead,
        intent_analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate contextual response based on intent and lead data"""
        try:
            # Prepare response context
            response_context = {
                "lead_name": f"{lead.first_name} {lead.last_name}",
                "lead_company": lead.company,
                "lead_industry": lead.industry,
                "lead_job_title": lead.job_title,
                "intent": intent_analysis.get("intent"),
                "sentiment": intent_analysis.get("sentiment"),
                "urgency": intent_analysis.get("urgency"),
                "conversation_context": context
            }
            
            # Generate response based on intent
            intent = intent_analysis.get("intent", "general_inquiry")
            
            if intent == "demo_request":
                response = await self._generate_demo_response(response_context)
            elif intent == "product_question":
                response = await self._generate_product_response(message, response_context)
            elif intent == "pricing_inquiry":
                response = await self._generate_pricing_response(response_context)
            elif intent == "objection":
                response = await self._generate_objection_response(message, response_context)
            else:
                response = await self._generate_general_response(message, response_context)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate contextual response: {e}")
            return {
                "message": "Thank you for your message. I'll connect you with our sales team to better assist you.",
                "suggested_actions": ["schedule_call", "send_information"],
                "next_steps": ["Follow up with sales team"]
            }
    
    async def _generate_demo_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate demo scheduling response"""
        response = f"""
        Hi {context['lead_name']}, I'd be happy to schedule a demo for you!
        
        I can show you how our solution can help {context['lead_company']} achieve your goals. 
        What would be the best time for a 30-minute demo?
        
        I can accommodate your schedule and tailor the demo to focus on your specific needs in the {context['lead_industry']} industry.
        """
        
        return {
            "message": response.strip(),
            "suggested_actions": ["schedule_demo", "send_case_study"],
            "next_steps": ["Confirm demo time", "Send calendar invitation"]
        }
    
    async def _generate_product_response(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate product information response"""
        response = f"""
        Great question about our product! Let me provide you with some relevant information.
        
        Based on your role as {context['lead_job_title']} at {context['lead_company']}, I think you'll find our solution particularly valuable for {context['lead_industry']} companies.
        
        Would you like me to:
        1. Send you detailed product information
        2. Schedule a personalized demo
        3. Connect you with a product specialist
        """
        
        return {
            "message": response.strip(),
            "suggested_actions": ["send_product_info", "schedule_demo", "connect_specialist"],
            "next_steps": ["Follow up with product materials"]
        }
    
    async def _generate_pricing_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pricing information response"""
        response = f"""
        I understand you're interested in our pricing. Our solutions are tailored to companies like {context['lead_company']}, and pricing depends on your specific needs and scale.
        
        To provide you with accurate pricing, I'd like to understand your requirements better. Would you be open to a brief discovery call?
        
        This will help me provide you with a customized quote that fits your budget and delivers maximum value.
        """
        
        return {
            "message": response.strip(),
            "suggested_actions": ["schedule_discovery_call", "send_pricing_guide"],
            "next_steps": ["Schedule discovery call", "Prepare customized quote"]
        }
    
    async def _generate_objection_response(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate objection handling response"""
        response = f"""
        I appreciate you sharing that concern. It's a common consideration for companies in the {context['lead_industry']} space.
        
        Let me address this by sharing how other {context['lead_industry']} companies have successfully overcome similar challenges with our solution.
        
        Would you be interested in seeing a case study or speaking with a customer in your industry?
        """
        
        return {
            "message": response.strip(),
            "suggested_actions": ["share_case_study", "customer_reference", "schedule_call"],
            "next_steps": ["Provide case study", "Arrange customer reference call"]
        }
    
    async def _generate_general_response(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate general inquiry response"""
        response = f"""
        Thank you for reaching out, {context['lead_name']}! I'm here to help you learn more about how our solution can benefit {context['lead_company']}.
        
        How can I best assist you today? I can help with:
        • Product demonstrations
        • Pricing information
        • Case studies and references
        • Technical questions
        """
        
        return {
            "message": response.strip(),
            "suggested_actions": ["schedule_demo", "send_information", "connect_specialist"],
            "next_steps": ["Understand specific needs", "Provide relevant information"]
        }
    
    async def _search_knowledge_base(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search knowledge base for relevant information"""
        try:
            # Search ChromaDB for relevant documents
            search_results = await self.chroma_manager.search(
                query=question,
                n_results=5,
                filter_metadata=context
            )
            
            return {
                "success": True,
                "sources": search_results.get("documents", []),
                "relevance_scores": search_results.get("distances", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to search knowledge base: {e}")
            return {
                "success": False,
                "sources": [],
                "relevance_scores": []
            }
    
    async def _generate_product_answer(
        self,
        question: str,
        lead: Lead,
        knowledge_response: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate product answer using knowledge base and NLP"""
        try:
            # Prepare answer context
            answer_context = {
                "question": question,
                "lead_company": lead.company,
                "lead_industry": lead.industry,
                "knowledge_sources": knowledge_response.get("sources", [])
            }
            
            # Generate answer using NLP
            answer_prompt = f"""
            Answer this product question for a potential customer:
            
            Question: {question}
            Customer Company: {lead.company}
            Customer Industry: {lead.industry}
            
            Knowledge Base Information: {knowledge_response.get('sources', [])}
            
            Provide a helpful, accurate, and personalized answer.
            """
            
            messages = [
                {"role": "system", "content": answer_prompt},
                {"role": "user", "content": question}
            ]
            
            answer = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            return {
                "response": answer.text_content if answer.success else "I'm sorry, I couldn't generate a response at this time.",
                "confidence": 0.8,
                "related_topics": ["product_features", "implementation", "support"],
                "suggested_resources": ["product_demo", "case_study", "documentation"]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate product answer: {e}")
            return {
                "response": "I'd be happy to help you with that question. Let me connect you with our product specialist for a detailed answer.",
                "confidence": 0.5,
                "related_topics": [],
                "suggested_resources": ["connect_specialist"]
            }
    
    async def _generate_demo_scheduling_response(
        self,
        lead: Lead,
        demo_preferences: Dict[str, Any]
    ) -> str:
        """Generate demo scheduling confirmation response"""
        return f"""
        Perfect! I've scheduled your demo for {demo_preferences.get('preferred_date')} at {demo_preferences.get('preferred_time')}.
        
        You'll receive a calendar invitation shortly with all the details. The demo will be {demo_preferences.get('duration', '30 minutes')} and will be tailored to {lead.company}'s specific needs in the {lead.industry} industry.
        
        I'll also send you a pre-demo questionnaire to help us prepare the most relevant demonstration for your team.
        
        Looking forward to showing you how our solution can help {lead.company} achieve your goals!
        """
