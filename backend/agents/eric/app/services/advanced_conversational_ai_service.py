from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging
from pydantic import BaseModel

from core.cache.redis_manager import RedisManager
from core.messaging.kafka_manager import KafkaManager
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
from core.ai import get_ai_service_manager
from ..database import get_eric_database
from ..models import (
    Lead, LeadInteraction, Deal, SalesActivity, Objection,
    SalesCampaign, EmailSequence, SalesTeam, SalesRep
)

logger = logging.getLogger(__name__)

class ConversationContext(BaseModel):
    conversation_id: str
    user_id: int
    lead_id: Optional[int] = None
    deal_id: Optional[int] = None
    industry: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = []
    current_topic: Optional[str] = None
    user_intent: Optional[str] = None
    confidence_score: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class IndustryQuery(BaseModel):
    id: Optional[int] = None
    industry: str
    query_type: str
    question: str
    answer: str
    confidence_score: float
    sources: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ConversationResponse(BaseModel):
    response: str
    confidence_score: float
    suggested_actions: List[Dict[str, Any]] = []
    follow_up_questions: List[str] = []
    industry_context: Optional[Dict[str, Any]] = None
    next_best_action: Optional[str] = None

class AdvancedConversationalAIService:
    def __init__(self):
        self.ai_service_manager = None
        self.redis_manager = RedisManager()
        self.kafka_manager = KafkaManager()
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self._initialized = False
        # Using AI Service Manager for intent detection and text generation
    
    async def initialize(self):
        """Initialize advanced conversational AI service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.redis_manager.initialize()
            await self.kafka_manager.initialize()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            self._initialized = True
            logger.info("Advanced conversational AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize advanced conversational AI service: {e}")
            raise
        
        # Industry-specific knowledge bases
        self.industry_knowledge = {
            "technology": {
                "topics": ["software", "hardware", "cloud", "AI", "cybersecurity"],
                "common_questions": [
                    "What's the ROI of implementing this solution?",
                    "How does this integrate with existing systems?",
                    "What's the implementation timeline?",
                    "What support is available?"
                ]
            },
            "healthcare": {
                "topics": ["HIPAA", "patient care", "medical devices", "compliance"],
                "common_questions": [
                    "Is this HIPAA compliant?",
                    "How does this improve patient outcomes?",
                    "What certifications do you have?",
                    "How do you handle data security?"
                ]
            },
            "finance": {
                "topics": ["compliance", "risk management", "regulations", "audit"],
                "common_questions": [
                    "What compliance certifications do you have?",
                    "How do you handle regulatory changes?",
                    "What's your audit trail?",
                    "How do you ensure data security?"
                ]
            },
            "manufacturing": {
                "topics": ["automation", "quality control", "supply chain", "efficiency"],
                "common_questions": [
                    "How does this improve efficiency?",
                    "What's the implementation cost?",
                    "How do you handle quality control?",
                    "What training is required?"
                ]
            }
        }
    
    async def process_conversation(self, user_message: str, context: ConversationContext) -> ConversationResponse:
        """Process user message and generate contextual response"""
        async with get_eric_database() as session:
            try:
                # Update conversation context
                context.conversation_history.append({
                    "role": "user",
                    "message": user_message,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Analyze user intent
                intent_analysis = await self._analyze_user_intent(user_message, context)
                context.user_intent = intent_analysis["intent"]
                context.confidence_score = intent_analysis["confidence"]
                
                # Get industry-specific context
                industry_context = await self._get_industry_context(context.industry, session)
                
                # Generate response based on intent and context
                response = await self._generate_contextual_response(
                    user_message, 
                    intent_analysis, 
                    industry_context, 
                    context
                )
                
                # Update conversation history
                context.conversation_history.append({
                    "role": "assistant",
                    "message": response.response,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Cache conversation context
                await self.redis_manager.set_cache(
                    f"conversation_context_{context.conversation_id}",
                    context.dict(),
                    expire=3600  # 1 hour
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "advanced_conversational_ai.conversation_processed",
                    {
                        "conversation_id": context.conversation_id,
                        "user_id": context.user_id,
                        "intent": intent_analysis["intent"],
                        "confidence": intent_analysis["confidence"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Processed conversation for user {context.user_id}")
                return response
                
            except Exception as e:
                logger.error(f"Failed to process conversation: {e}")
                raise
    
    async def handle_industry_specific_query(self, query: str, industry: str, user_id: int) -> IndustryQuery:
        """Handle industry-specific queries with detailed responses"""
        async with get_eric_database() as session:
            try:
                # Analyze query type
                query_type = await self._classify_query_type(query, industry)
                
                # Generate industry-specific answer
                answer = await self._generate_industry_answer(query, industry, query_type)
                
                # Get relevant sources
                sources = await self._get_relevant_sources(query, industry)
                
                # Calculate confidence score
                confidence_score = await self._calculate_query_confidence(query, industry, answer)
                
                # Create industry query record
                industry_query = IndustryQuery(
                    industry=industry,
                    query_type=query_type,
                    question=query,
                    answer=answer,
                    confidence_score=confidence_score,
                    sources=sources,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                # Store in database (simplified for demo)
                industry_query.id = 1  # Simulate ID generation
                
                # Cache query
                await self.redis_manager.set_cache(
                    f"industry_query_{industry_query.id}",
                    industry_query.dict(),
                    expire=86400  # 24 hours
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "advanced_conversational_ai.industry_query_handled",
                    {
                        "query_id": industry_query.id,
                        "industry": industry,
                        "query_type": query_type,
                        "confidence": confidence_score,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Handled industry-specific query for {industry}")
                return industry_query
                
            except Exception as e:
                logger.error(f"Failed to handle industry-specific query: {e}")
                raise
    
    async def get_conversation_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get conversation context from cache"""
        try:
            cached_context = await self.redis_manager.get_cache(f"conversation_context_{conversation_id}")
            if cached_context:
                return ConversationContext(**cached_context)
            return None
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return None
    
    async def update_conversation_context(self, context: ConversationContext) -> bool:
        """Update conversation context in cache"""
        try:
            context.updated_at = datetime.utcnow()
            await self.redis_manager.set_cache(
                f"conversation_context_{context.conversation_id}",
                context.dict(),
                expire=3600  # 1 hour
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update conversation context: {e}")
            return False
    
    async def get_industry_knowledge_base(self, industry: str) -> Dict[str, Any]:
        """Get industry-specific knowledge base"""
        try:
            # Try cache first
            cached_knowledge = await self.redis_manager.get_cache(f"industry_knowledge_{industry}")
            if cached_knowledge:
                return cached_knowledge
            
            # Get from database or default knowledge
            knowledge = self.industry_knowledge.get(industry, {
                "topics": ["general"],
                "common_questions": [
                    "What are your pricing options?",
                    "How does this work?",
                    "What are the benefits?",
                    "How do I get started?"
                ]
            })
            
            # Cache knowledge
            await self.redis_manager.set_cache(
                f"industry_knowledge_{industry}",
                knowledge,
                expire=86400  # 24 hours
            )
            
            return knowledge
            
        except Exception as e:
            logger.error(f"Failed to get industry knowledge base: {e}")
            return {}
    
    async def analyze_conversation_sentiment(self, conversation_id: str) -> Dict[str, Any]:
        """Analyze sentiment and emotions in a conversation"""
        try:
            async with get_eric_database() as db:
                # Get conversation interactions
                interactions_query = select(LeadInteraction).where(
                    LeadInteraction.conversation_id == conversation_id
                ).order_by(LeadInteraction.created_at)
                
                interactions_result = await db.execute(interactions_query)
                interactions = interactions_result.scalars().all()
                
                if not interactions:
                    return {
                        "conversation_id": conversation_id,
                        "overall_sentiment": "neutral",
                        "sentiment_score": 0,
                        "emotions": [],
                        "key_phrases": [],
                        "sentiment_trend": "stable"
                    }
                
                # Analyze sentiment scores
                sentiment_scores = [i.sentiment_score for i in interactions if i.sentiment_score]
                if sentiment_scores:
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                    
                    # Determine overall sentiment
                    if avg_sentiment > 0.3:
                        overall_sentiment = "positive"
                    elif avg_sentiment < -0.3:
                        overall_sentiment = "negative"
                    else:
                        overall_sentiment = "neutral"
                    
                    # Analyze sentiment trend
                    if len(sentiment_scores) > 1:
                        first_half = sentiment_scores[:len(sentiment_scores)//2]
                        second_half = sentiment_scores[len(sentiment_scores)//2:]
                        
                        first_avg = sum(first_half) / len(first_half)
                        second_avg = sum(second_half) / len(second_half)
                        
                        if second_avg > first_avg + 0.2:
                            sentiment_trend = "improving"
                        elif second_avg < first_avg - 0.2:
                            sentiment_trend = "declining"
                        else:
                            sentiment_trend = "stable"
                    else:
                        sentiment_trend = "stable"
                else:
                    avg_sentiment = 0
                    overall_sentiment = "neutral"
                    sentiment_trend = "stable"
                
                # Extract key phrases and emotions (simplified analysis)
                key_phrases = []
                emotions = []
                
                for interaction in interactions:
                    if interaction.content:
                        content_lower = interaction.content.lower()
                        
                        # Simple emotion detection
                        if any(word in content_lower for word in ["happy", "excited", "great", "amazing"]):
                            emotions.append("positive")
                        elif any(word in content_lower for word in ["frustrated", "angry", "disappointed"]):
                            emotions.append("negative")
                        elif any(word in content_lower for word in ["concerned", "worried", "unsure"]):
                            emotions.append("concerned")
                        
                        # Extract potential key phrases (simplified)
                        words = content_lower.split()
                        if len(words) >= 3:
                            # Look for phrases with business keywords
                            business_keywords = ["price", "cost", "budget", "timeline", "features", "solution"]
                            for i in range(len(words) - 2):
                                phrase = " ".join(words[i:i+3])
                                if any(keyword in phrase for keyword in business_keywords):
                                    key_phrases.append(phrase)
                
                # Remove duplicates and limit results
                emotions = list(set(emotions))[:5]
                key_phrases = list(set(key_phrases))[:10]
                
                return {
                    "conversation_id": conversation_id,
                    "overall_sentiment": overall_sentiment,
                    "sentiment_score": round(avg_sentiment, 3),
                    "emotions": emotions,
                    "key_phrases": key_phrases,
                    "sentiment_trend": sentiment_trend,
                    "total_interactions": len(interactions),
                    "analysis_date": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error analyzing conversation sentiment: {e}")
            return {
                "conversation_id": conversation_id,
                "overall_sentiment": "neutral",
                "sentiment_score": 0,
                "emotions": [],
                "key_phrases": [],
                "sentiment_trend": "stable"
            }
    
    async def get_conversation_insights(self, conversation_id: str) -> Dict[str, Any]:
        """Get insights from conversation analysis"""
        try:
            # Get conversation context
            context = await self.get_conversation_context(conversation_id)
            if not context:
                raise ValueError("Conversation context not found")
            
            # Analyze sentiment
            sentiment_analysis = await self.analyze_conversation_sentiment(conversation_id)
            
            # Get user behavior patterns
            behavior_patterns = await self._analyze_user_behavior(context)
            
            # Get conversation effectiveness
            effectiveness = await self._calculate_conversation_effectiveness(context)
            
            insights = {
                "conversation_id": conversation_id,
                "user_id": context.user_id,
                "sentiment_analysis": sentiment_analysis,
                "behavior_patterns": behavior_patterns,
                "effectiveness": effectiveness,
                "key_topics": await self._extract_key_topics(context.conversation_history),
                "recommendations": await self._generate_conversation_recommendations(context, sentiment_analysis),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get conversation insights: {e}")
            raise
    
    # Helper methods (simplified implementations)
    async def _analyze_user_intent(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Analyze user intent from message"""
        try:
            # Use AI Service Manager for intent detection
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that detects user intent from messages. Respond with JSON: {\"intent\": \"...\", \"confidence\": 0.0-1.0, \"entities\": []}"}, {"role": "user", "content": f"Analyze the intent of this message: {message}"}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.3)
            if ai_response.success:
                import json
                try:
                    intent_result = json.loads(ai_response.text_content)
                except:
                    intent_result = {"intent": "general", "confidence": 0.7, "entities": []}
            else:
                intent_result = {"intent": "general", "confidence": 0.5, "entities": []}
            return intent_result
        except Exception as e:
            logger.error(f"Failed to analyze user intent: {e}")
            return {
                "intent": "general_inquiry",
                "confidence": 0.5,
                "entities": [],
                "sentiment": "neutral"
            }
    
    async def _get_industry_context(self, industry: str, session: AsyncSession) -> Dict[str, Any]:
        """Get industry-specific context and knowledge"""
        try:
            if not industry:
                return {}
            
            knowledge_base = await self.get_industry_knowledge_base(industry)
            
            return {
                "knowledge_base": knowledge_base,
                "industry_trends": await self._get_industry_trends(industry),
                "best_practices": await self._get_industry_best_practices(industry)
            }
        except Exception as e:
            logger.error(f"Failed to get industry context: {e}")
            return {}
    
    async def _generate_contextual_response(
        self, 
        message: str, 
        intent_analysis: Dict[str, Any], 
        industry_context: Dict[str, Any], 
        context: ConversationContext
    ) -> ConversationResponse:
        """Generate contextual response based on intent and industry context"""
        try:
            intent = intent_analysis.get("intent", "general_inquiry")
            confidence = intent_analysis.get("confidence", 0.5)
            
            # Generate base response using NLP
            # Use AI Service Manager instead of NLPUtils
            from core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": f"You are an AI sales assistant. Detected intent: {intent}"},
                {"role": "user", "content": message}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
            base_response = ai_response.text_content if ai_response.success else ""
            
            # Enhance with industry context
            enhanced_response = await self._enhance_response_with_industry_context(
                base_response, industry_context, intent
            )
            
            # Generate suggested actions
            suggested_actions = await self._generate_suggested_actions(intent, context, industry_context)
            
            # Generate follow-up questions
            follow_up_questions = await self._generate_follow_up_questions(intent, context, industry_context)
            
            # Determine next best action
            next_best_action = await self._determine_next_best_action(intent, context, confidence)
            
            return ConversationResponse(
                response=enhanced_response,
                confidence_score=confidence,
                suggested_actions=suggested_actions,
                follow_up_questions=follow_up_questions,
                industry_context=industry_context,
                next_best_action=next_best_action
            )
            
        except Exception as e:
            logger.error(f"Failed to generate contextual response: {e}")
            return ConversationResponse(
                response="I apologize, but I'm having trouble processing your request. Could you please rephrase?",
                confidence_score=0.0,
                suggested_actions=[],
                follow_up_questions=["Could you provide more details about your question?"],
                industry_context=None,
                next_best_action="clarify_request"
            )
    
    async def _classify_query_type(self, query: str, industry: str) -> str:
        """Classify the type of industry-specific query"""
        try:
            query_lower = query.lower()
            
            query_types = {
                "pricing": ["cost", "price", "pricing", "budget", "expensive", "cheap", "afford"],
                "technical": ["how", "what", "when", "where", "why", "technical", "implementation", "setup"],
                "compliance": ["compliance", "regulations", "legal", "certification", "audit", "security"],
                "support": ["support", "help", "assistance", "maintenance", "service", "training"],
                "comparison": ["compare", "difference", "better", "worse", "alternative", "competitor"],
                "timeline": ["when", "timeline", "schedule", "deadline", "duration", "time"]
            }
            
            for query_type, keywords in query_types.items():
                if any(keyword in query_lower for keyword in keywords):
                    return query_type
            
            return "general"
            
        except Exception as e:
            logger.error(f"Failed to classify query type: {e}")
            return "general"
    
    async def _generate_industry_answer(self, query: str, industry: str, query_type: str) -> str:
        """Generate industry-specific answer"""
        try:
            if query_type == "pricing":
                return f"Based on {industry} industry standards, our pricing is competitive and includes comprehensive support. We offer flexible payment plans and volume discounts for enterprise clients."
            elif query_type == "technical":
                return f"For {industry} implementations, we provide detailed technical documentation, API access, and integration support. Our solution is designed to work with existing {industry} workflows."
            elif query_type == "compliance":
                return f"We maintain full compliance with {industry} regulations and standards. Our platform undergoes regular audits and we provide compliance documentation upon request."
            elif query_type == "support":
                return f"We offer 24/7 support specifically tailored for {industry} clients, including dedicated account managers and industry-specific training programs."
            else:
                return f"I understand your question about {industry}. Let me connect you with our {industry} specialist who can provide detailed information tailored to your specific needs."
            
        except Exception as e:
            logger.error(f"Failed to generate industry answer: {e}")
            return "I apologize, but I need more information to provide a specific answer. Could you please provide more details?"
    
    async def _get_relevant_sources(self, query: str, industry: str) -> List[str]:
        """Get relevant sources for the query"""
        try:
            sources = [
                f"{industry.capitalize()} Industry Best Practices Guide",
                f"{industry.capitalize()} Compliance Documentation",
                f"{industry.capitalize()} Case Studies",
                "Product Documentation",
                "Customer Success Stories"
            ]
            
            return sources[:3]  # Return top 3 sources
            
        except Exception as e:
            logger.error(f"Failed to get relevant sources: {e}")
            return []
    
    async def _calculate_query_confidence(self, query: str, industry: str, answer: str) -> float:
        """Calculate confidence score for the query response"""
        try:
            base_confidence = 0.7
            
            if len(query.split()) > 10:
                base_confidence -= 0.1
            
            if industry in self.industry_knowledge:
                base_confidence += 0.1
            
            if len(answer.split()) > 20:
                base_confidence += 0.1
            
            return min(base_confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate query confidence: {e}")
            return 0.5
    
    async def _enhance_response_with_industry_context(
        self, 
        base_response: str, 
        industry_context: Dict[str, Any], 
        intent: str
    ) -> str:
        """Enhance response with industry-specific context"""
        try:
            if not industry_context:
                return base_response
            
            knowledge_base = industry_context.get("knowledge_base", {})
            common_questions = knowledge_base.get("common_questions", [])
            
            if intent == "pricing_inquiry" and common_questions:
                enhanced_response = f"{base_response} This is a common question in your industry. "
                enhanced_response += "Many of our clients in similar situations find our pricing structure very competitive."
            
            elif intent == "technical_inquiry":
                enhanced_response = f"{base_response} Our solution is specifically designed for your industry's technical requirements. "
                enhanced_response += "We provide industry-standard integrations and compliance features."
            
            else:
                enhanced_response = base_response
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Failed to enhance response with industry context: {e}")
            return base_response
    
    async def _generate_suggested_actions(
        self, 
        intent: str, 
        context: ConversationContext, 
        industry_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate suggested actions based on intent and context"""
        try:
            actions = []
            
            if intent == "pricing_inquiry":
                actions.append({
                    "action": "schedule_demo",
                    "description": "Schedule a personalized demo",
                    "priority": "high"
                })
                actions.append({
                    "action": "get_quote",
                    "description": "Get a detailed quote",
                    "priority": "medium"
                })
            
            elif intent == "technical_inquiry":
                actions.append({
                    "action": "technical_demo",
                    "description": "Schedule a technical deep-dive",
                    "priority": "high"
                })
                actions.append({
                    "action": "documentation",
                    "description": "Access technical documentation",
                    "priority": "medium"
                })
            
            elif intent == "general_inquiry":
                actions.append({
                    "action": "learn_more",
                    "description": "Learn more about our solution",
                    "priority": "medium"
                })
                actions.append({
                    "action": "contact_sales",
                    "description": "Contact sales representative",
                    "priority": "low"
                })
            
            return actions
            
        except Exception as e:
            logger.error(f"Failed to generate suggested actions: {e}")
            return []
    
    async def _generate_follow_up_questions(
        self, 
        intent: str, 
        context: ConversationContext, 
        industry_context: Dict[str, Any]
    ) -> List[str]:
        """Generate follow-up questions based on intent and context"""
        try:
            questions = []
            
            if intent == "pricing_inquiry":
                questions.extend([
                    "What's your budget range?",
                    "How many users will need access?",
                    "Do you need any custom features?"
                ])
            
            elif intent == "technical_inquiry":
                questions.extend([
                    "What systems do you currently use?",
                    "How many integrations do you need?",
                    "What's your timeline for implementation?"
                ])
            
            elif intent == "general_inquiry":
                questions.extend([
                    "What specific challenges are you facing?",
                    "How did you hear about us?",
                    "What's your timeline for making a decision?"
                ])
            
            return questions[:3]  # Return top 3 questions
            
        except Exception as e:
            logger.error(f"Failed to generate follow-up questions: {e}")
            return []
    
    async def _determine_next_best_action(
        self, 
        intent: str, 
        context: ConversationContext, 
        confidence: float
    ) -> str:
        """Determine the next best action based on intent and confidence"""
        try:
            if confidence < 0.5:
                return "clarify_request"
            
            if intent == "pricing_inquiry":
                return "schedule_demo"
            elif intent == "technical_inquiry":
                return "technical_demo"
            elif intent == "general_inquiry":
                return "provide_information"
            else:
                return "continue_conversation"
            
        except Exception as e:
            logger.error(f"Failed to determine next best action: {e}")
            return "continue_conversation"
    
    async def _analyze_user_behavior(self, context: ConversationContext) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        try:
            if not context.conversation_history:
                return {}
            
            user_messages = [msg for msg in context.conversation_history if msg["role"] == "user"]
            
            return {
                "message_count": len(user_messages),
                "average_message_length": sum(len(msg["message"]) for msg in user_messages) / len(user_messages) if user_messages else 0,
                "response_time": "immediate",  # Simplified
                "engagement_level": "high" if len(user_messages) > 5 else "medium",
                "topic_consistency": "consistent"  # Simplified
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze user behavior: {e}")
            return {}
    
    async def _calculate_conversation_effectiveness(self, context: ConversationContext) -> Dict[str, Any]:
        """Calculate conversation effectiveness metrics"""
        try:
            if not context.conversation_history:
                return {"score": 0.0, "factors": []}
            
            factors = []
            score = 0.5  # Base score
            
            if len(context.conversation_history) > 10:
                score += 0.2
                factors.append("extended_conversation")
            
            user_messages = [msg for msg in context.conversation_history if msg["role"] == "user"]
            if len(user_messages) > 5:
                score += 0.2
                factors.append("high_engagement")
            
            if context.user_intent and context.confidence_score > 0.7:
                score += 0.1
                factors.append("clear_intent")
            
            return {
                "score": min(score, 1.0),
                "factors": factors,
                "recommendations": await self._get_effectiveness_recommendations(score, factors)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate conversation effectiveness: {e}")
            return {"score": 0.0, "factors": []}
    
    async def _extract_key_topics(self, conversation_history: List[Dict[str, Any]]) -> List[str]:
        """Extract key topics from conversation"""
        try:
            all_messages = " ".join([msg["message"] for msg in conversation_history])
            # Use AI Service Manager for keyword extraction
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that extracts key topics from text. Return a comma-separated list of the top 5 most important topics."}, {"role": "user", "content": f"Extract the top 5 key topics from this conversation: {all_messages}"}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
            if ai_response.success:
                topics = [t.strip() for t in ai_response.text_content.split(",")][:5]
            else:
                topics = []
            return topics
            
        except Exception as e:
            logger.error(f"Failed to extract key topics: {e}")
            return []
    
    async def _generate_conversation_recommendations(
        self, 
        context: ConversationContext, 
        sentiment_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for improving conversation"""
        try:
            recommendations = []
            
            if sentiment_analysis.get("overall_sentiment") == "negative":
                recommendations.append("Address user concerns more directly")
                recommendations.append("Provide more detailed explanations")
            
            if sentiment_analysis.get("engagement_score", 0) < 0.5:
                recommendations.append("Ask more engaging questions")
                recommendations.append("Provide more interactive responses")
            
            if len(context.conversation_history) < 5:
                recommendations.append("Encourage more detailed responses")
                recommendations.append("Ask follow-up questions")
            
            return recommendations[:3]  # Return top 3 recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate conversation recommendations: {e}")
            return []
    
    async def _get_effectiveness_recommendations(self, score: float, factors: List[str]) -> List[str]:
        """Get recommendations for improving effectiveness"""
        try:
            recommendations = []
            
            if score < 0.5:
                recommendations.append("Improve initial engagement")
                recommendations.append("Ask more specific questions")
            
            if "extended_conversation" not in factors:
                recommendations.append("Encourage longer conversations")
            
            if "high_engagement" not in factors:
                recommendations.append("Increase user interaction")
            
            return recommendations[:3]  # Return top 3 recommendations
            
        except Exception as e:
            logger.error(f"Failed to get effectiveness recommendations: {e}")
            return []
    
    async def _get_industry_trends(self, industry: str) -> List[str]:
        """Get industry trends (simplified)"""
        try:
            trends = {
                "technology": ["AI adoption", "Cloud migration", "Cybersecurity focus"],
                "healthcare": ["Digital transformation", "Telemedicine", "Data privacy"],
                "finance": ["Regulatory compliance", "Digital banking", "Risk management"],
                "manufacturing": ["Automation", "IoT integration", "Supply chain optimization"]
            }
            
            return trends.get(industry, ["Digital transformation", "Cost optimization", "Efficiency improvement"])
            
        except Exception as e:
            logger.error(f"Failed to get industry trends: {e}")
            return []
    
    async def _get_industry_best_practices(self, industry: str) -> List[str]:
        """Get industry best practices (simplified)"""
        try:
            practices = {
                "technology": ["Agile development", "DevOps practices", "Security-first approach"],
                "healthcare": ["Patient-centered care", "Data security", "Compliance adherence"],
                "finance": ["Risk assessment", "Regulatory compliance", "Customer protection"],
                "manufacturing": ["Quality control", "Lean manufacturing", "Continuous improvement"]
            }
            
            return practices.get(industry, ["Best practices", "Industry standards", "Quality assurance"])
            
        except Exception as e:
            logger.error(f"Failed to get industry best practices: {e}")
            return []
