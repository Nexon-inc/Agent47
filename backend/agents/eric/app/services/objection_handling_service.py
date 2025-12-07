from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging
from pydantic import BaseModel

from backend.core.cache.redis_manager import RedisManager
from backend.core.messaging.kafka_manager import KafkaManager
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.platforms.platform_manager import PlatformManager
from backend.core.ai import get_ai_service_manager
from ..database import get_eric_database
from ..models import (
    Lead, LeadInteraction, Deal, SalesActivity, Objection,
    SalesCampaign, EmailSequence, SalesTeam, SalesRep, SalesAnalytics
)

logger = logging.getLogger(__name__)

class ObjectionType(BaseModel):
    id: Optional[int] = None
    name: str
    category: str  # price, timing, authority, need, competition, etc.
    description: str
    common_phrases: List[str] = []
    severity_level: str  # low, medium, high, critical
    success_rate: float = 0.0
    created_at: Optional[datetime] = None

class ObjectionResponse(BaseModel):
    id: Optional[int] = None
    objection_type_id: int
    response_text: str
    response_type: str  # question, statement, story, data, testimonial
    tone: str  # empathetic, confident, professional, casual
    effectiveness_score: float = 0.0
    usage_count: int = 0
    success_rate: float = 0.0
    created_at: Optional[datetime] = None

class ObjectionHandlingSession(BaseModel):
    id: Optional[int] = None
    lead_id: int
    sales_rep_id: int
    conversation_id: str
    objection_detected: str
    objection_type: str
    suggested_responses: List[ObjectionResponse] = []
    selected_response: Optional[ObjectionResponse] = None
    customer_reaction: str = ""
    outcome: str = ""  # resolved, escalated, lost
    confidence_score: float = 0.0
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class ObjectionAnalysis(BaseModel):
    objection_text: str
    detected_type: str
    confidence_score: float
    severity_level: str
    suggested_responses: List[ObjectionResponse] = []
    recommended_approach: str
    follow_up_questions: List[str] = []
    escalation_needed: bool = False

class ObjectionHandlingService:
    def __init__(self):
        self.ai_service_manager = None
        self.redis_manager = RedisManager()
        self.kafka_manager = KafkaManager()
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self._initialized = False
        # Using AI Service Manager for sentiment analysis and intent detection
    
    async def initialize(self):
        """Initialize objection handling service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.redis_manager.initialize()
            await self.kafka_manager.initialize()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            self._initialized = True
            logger.info("Objection handling service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize objection handling service: {e}")
            raise
        
        # Pre-defined objection types and responses
        self.objection_types = {
            "price": {
                "name": "Price Objection",
                "category": "financial",
                "description": "Customer thinks the price is too high",
                "common_phrases": [
                    "it's too expensive",
                    "we can't afford it",
                    "it's over our budget",
                    "the price is too high",
                    "we need a better deal",
                    "can you lower the price"
                ],
                "severity_level": "high",
                "success_rate": 0.75
            },
            "timing": {
                "name": "Timing Objection",
                "category": "decision",
                "description": "Customer wants to delay the decision",
                "common_phrases": [
                    "we need more time",
                    "let's wait until next quarter",
                    "we're not ready to decide",
                    "we need to think about it",
                    "can we postpone this",
                    "we'll get back to you"
                ],
                "severity_level": "medium",
                "success_rate": 0.65
            },
            "authority": {
                "name": "Authority Objection",
                "category": "decision",
                "description": "Customer doesn't have decision-making authority",
                "common_phrases": [
                    "I need to check with my boss",
                    "I don't have the authority",
                    "I need approval",
                    "let me run this by the team",
                    "I need to discuss this",
                    "I can't make this decision"
                ],
                "severity_level": "medium",
                "success_rate": 0.70
            },
            "need": {
                "name": "Need Objection",
                "category": "value",
                "description": "Customer doesn't see the need for the solution",
                "common_phrases": [
                    "we don't need this",
                    "we're doing fine without it",
                    "it's not a priority",
                    "we don't have this problem",
                    "we're not interested",
                    "it's not relevant to us"
                ],
                "severity_level": "high",
                "success_rate": 0.60
            },
            "competition": {
                "name": "Competition Objection",
                "category": "comparison",
                "description": "Customer is considering competitors",
                "common_phrases": [
                    "we're looking at other options",
                    "your competitor offers this",
                    "we're evaluating alternatives",
                    "someone else has a better deal",
                    "we're comparing solutions",
                    "your competitor is cheaper"
                ],
                "severity_level": "high",
                "success_rate": 0.55
            },
            "trust": {
                "name": "Trust Objection",
                "category": "relationship",
                "description": "Customer doesn't trust the company or solution",
                "common_phrases": [
                    "I don't know your company",
                    "we've never heard of you",
                    "how do we know you're reliable",
                    "we need references",
                    "we're concerned about security",
                    "we need to verify your claims"
                ],
                "severity_level": "critical",
                "success_rate": 0.80
            }
        }
        
        # Pre-defined responses for each objection type
        self.objection_responses = {
            "price": [
                {
                    "response_text": "I understand price is important. Let me show you the ROI you'll get from this investment. Based on what you've told me, you could save $X per month, which means this pays for itself in Y months. What specific budget constraints are you working with?",
                    "response_type": "question",
                    "tone": "empathetic",
                    "effectiveness_score": 0.85
                },
                {
                    "response_text": "You're absolutely right to be concerned about cost. Let me break down the value you're getting: [specific benefits]. When you compare this to the cost of [current problem], you're actually saving money. What would make this investment worthwhile for you?",
                    "response_type": "statement",
                    "tone": "confident",
                    "effectiveness_score": 0.80
                },
                {
                    "response_text": "I appreciate you being upfront about budget concerns. We have flexible payment options and can work within your budget. What's your ideal price range, and I'll show you what we can deliver within that?",
                    "response_type": "question",
                    "tone": "professional",
                    "effectiveness_score": 0.75
                }
            ],
            "timing": [
                {
                    "response_text": "I understand you want to be thorough in your decision. What specific concerns do you have that are making you want to wait? Sometimes waiting can actually cost more in terms of [specific costs/risks].",
                    "response_type": "question",
                    "tone": "empathetic",
                    "effectiveness_score": 0.80
                },
                {
                    "response_text": "That's a fair point. Let me ask - what would need to happen for you to feel comfortable moving forward now? Sometimes the best time to start is when you have a clear understanding of the problem and solution.",
                    "response_type": "question",
                    "tone": "professional",
                    "effectiveness_score": 0.75
                },
                {
                    "response_text": "I respect that you want to think this through. What if we started with a small pilot or trial? That way you can see the results without making a big commitment, and we can address any concerns as they come up.",
                    "response_type": "statement",
                    "tone": "casual",
                    "effectiveness_score": 0.70
                }
            ],
            "authority": [
                {
                    "response_text": "That makes perfect sense. What information would be most helpful for your [boss/team] to make this decision? I can prepare a summary of our discussion and the key benefits we've identified.",
                    "response_type": "question",
                    "tone": "professional",
                    "effectiveness_score": 0.85
                },
                {
                    "response_text": "I understand you need to get approval. Would it be helpful if I joined the meeting with your [boss/team] to answer any questions they might have? I can also provide case studies and references.",
                    "response_type": "question",
                    "tone": "confident",
                    "effectiveness_score": 0.80
                },
                {
                    "response_text": "That's a smart approach. What concerns do you think your [boss/team] will have, and how can I help address them? I want to make sure you have everything you need to get approval.",
                    "response_type": "question",
                    "tone": "empathetic",
                    "effectiveness_score": 0.75
                }
            ],
            "need": [
                {
                    "response_text": "I appreciate your honesty. Let me ask - what would need to happen for you to see this as a priority? Sometimes the need isn't obvious until we look at the hidden costs of [current situation].",
                    "response_type": "question",
                    "tone": "empathetic",
                    "effectiveness_score": 0.75
                },
                {
                    "response_text": "That's interesting. Most of our customers thought the same thing initially. What changed their mind was seeing how much time and money they were losing by [specific problem]. What's your biggest challenge right now?",
                    "response_type": "statement",
                    "tone": "confident",
                    "effectiveness_score": 0.70
                },
                {
                    "response_text": "I understand. Let me share a quick story about a client who was in your exact situation. They thought they didn't need our solution, but after implementing it, they saved [specific metrics]. What's your biggest pain point?",
                    "response_type": "story",
                    "tone": "casual",
                    "effectiveness_score": 0.65
                }
            ],
            "competition": [
                {
                    "response_text": "I'm glad you're doing your research. What specific features or benefits are you looking for? I'd be happy to show you how we compare and what makes us different.",
                    "response_type": "question",
                    "tone": "confident",
                    "effectiveness_score": 0.80
                },
                {
                    "response_text": "That's a fair comparison. What's most important to you - price, features, support, or something else? I want to make sure we're comparing apples to apples.",
                    "response_type": "question",
                    "tone": "professional",
                    "effectiveness_score": 0.75
                },
                {
                    "response_text": "I appreciate you being upfront about looking at alternatives. What specific concerns do you have about our solution? I'd love to address them directly.",
                    "response_type": "question",
                    "tone": "empathetic",
                    "effectiveness_score": 0.70
                }
            ],
            "trust": [
                {
                    "response_text": "That's a completely valid concern. We've been in business for [X] years and have helped [Y] companies like yours. Would it be helpful to speak with some of our current customers?",
                    "response_type": "statement",
                    "tone": "empathetic",
                    "effectiveness_score": 0.90
                },
                {
                    "response_text": "I understand you want to be sure about our reliability. What specific concerns do you have? I can provide references, case studies, and security certifications.",
                    "response_type": "question",
                    "tone": "professional",
                    "effectiveness_score": 0.85
                },
                {
                    "response_text": "Your trust is important to us. Let me share some of our customer success stories and security measures. What would make you feel more comfortable about working with us?",
                    "response_type": "statement",
                    "tone": "confident",
                    "effectiveness_score": 0.80
                }
            ]
        }
    
    async def analyze_objection(self, objection_text: str, lead_id: int = None, context: Dict[str, Any] = None) -> ObjectionAnalysis:
        """Analyze an objection and suggest responses"""
        async with get_eric_database() as session:
            try:
                # Use AI Service Manager for sentiment and intent analysis
                ai_manager = await get_ai_service_manager()
                sentiment_prompt = f"Analyze the sentiment of this objection: {objection_text}. Respond with JSON: {{\"sentiment\": \"positive/negative/neutral\", \"score\": 0.0-1.0}}"
                messages = [{"role": "system", "content": "You are an AI assistant that analyzes sentiment. Respond in JSON format."}, {"role": "user", "content": sentiment_prompt}]
                sentiment_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
                try:
                    import json
                    sentiment = json.loads(sentiment_response.text_content) if sentiment_response.success else {"sentiment": "neutral", "score": 0.5}
                except:
                    sentiment = {"sentiment": "neutral", "score": 0.5}
                
                intent_prompt = f"Extract the intent from this objection: {objection_text}. Respond with JSON: {{\"intent\": \"...\", \"confidence\": 0.0-1.0}}"
                messages = [{"role": "system", "content": "You are an AI assistant that extracts intent. Respond in JSON format."}, {"role": "user", "content": intent_prompt}]
                intent_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
                try:
                    intent = json.loads(intent_response.text_content) if intent_response.success else {"intent": "general", "confidence": 0.5}
                except:
                    intent = {"intent": "general", "confidence": 0.5}
                
                # Detect objection type
                detected_type = self._detect_objection_type(objection_text)
                confidence_score = self._calculate_confidence_score(objection_text, detected_type)
                
                # Get severity level
                severity_level = self.objection_types.get(detected_type, {}).get("severity_level", "medium")
                
                # Get suggested responses
                suggested_responses = await self._get_suggested_responses(detected_type, context)
                
                # Generate recommended approach
                recommended_approach = self._generate_recommended_approach(detected_type, severity_level, sentiment)
                
                # Generate follow-up questions
                follow_up_questions = self._generate_follow_up_questions(detected_type, objection_text)
                
                # Determine if escalation is needed
                escalation_needed = self._determine_escalation_needed(severity_level, confidence_score, sentiment)
                
                analysis = ObjectionAnalysis(
                    objection_text=objection_text,
                    detected_type=detected_type,
                    confidence_score=confidence_score,
                    severity_level=severity_level,
                    suggested_responses=suggested_responses,
                    recommended_approach=recommended_approach,
                    follow_up_questions=follow_up_questions,
                    escalation_needed=escalation_needed
                )
                
                # Cache analysis
                await self.redis_manager.set_cache(
                    f"objection_analysis_{hash(objection_text)}",
                    analysis.dict(),
                    expire=3600  # 1 hour
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "objection_handling.objection_analyzed",
                    {
                        "lead_id": lead_id,
                        "objection_type": detected_type,
                        "severity_level": severity_level,
                        "confidence_score": confidence_score,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Analyzed objection: {detected_type} with confidence {confidence_score}")
                return analysis
                
            except Exception as e:
                logger.error(f"Failed to analyze objection: {e}")
                raise
    
    async def create_objection_handling_session(self, lead_id: int, sales_rep_id: int, objection_text: str, conversation_id: str) -> ObjectionHandlingSession:
        """Create a new objection handling session"""
        async with get_eric_database() as session:
            try:
                # Analyze the objection
                analysis = await self.analyze_objection(objection_text, lead_id)
                
                # Create session
                handling_session = ObjectionHandlingSession(
                    lead_id=lead_id,
                    sales_rep_id=sales_rep_id,
                    conversation_id=conversation_id,
                    objection_detected=objection_text,
                    objection_type=analysis.detected_type,
                    suggested_responses=analysis.suggested_responses,
                    confidence_score=analysis.confidence_score,
                    created_at=datetime.utcnow()
                )
                
                # Store in database (simplified for demo)
                handling_session.id = 1  # Simulate ID generation
                
                # Cache session
                await self.redis_manager.set_cache(
                    f"objection_session_{handling_session.id}",
                    handling_session.dict(),
                    expire=86400  # 24 hours
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "objection_handling.session_created",
                    {
                        "session_id": handling_session.id,
                        "lead_id": lead_id,
                        "objection_type": analysis.detected_type,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Created objection handling session for lead {lead_id}")
                return handling_session
                
            except Exception as e:
                logger.error(f"Failed to create objection handling session: {e}")
                raise
    
    async def select_response(self, session_id: int, response_id: int) -> bool:
        """Select a response for an objection handling session"""
        try:
            # Get session
            cached_session = await self.redis_manager.get_cache(f"objection_session_{session_id}")
            if not cached_session:
                raise ValueError("Objection handling session not found")
            
            session = ObjectionHandlingSession(**cached_session)
            
            # Find the selected response
            selected_response = next(
                (r for r in session.suggested_responses if r.id == response_id),
                None
            )
            
            if not selected_response:
                raise ValueError("Response not found")
            
            # Update session
            session.selected_response = selected_response
            
            # Update cache
            await self.redis_manager.set_cache(
                f"objection_session_{session_id}",
                session.dict(),
                expire=86400  # 24 hours
            )
            
            # Publish event
            await self.kafka_manager.publish_event(
                "objection_handling.response_selected",
                {
                    "session_id": session_id,
                    "response_id": response_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Selected response {response_id} for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to select response: {e}")
            raise
    
    async def record_outcome(self, session_id: int, customer_reaction: str, outcome: str) -> bool:
        """Record the outcome of an objection handling session"""
        try:
            # Get session
            cached_session = await self.redis_manager.get_cache(f"objection_session_{session_id}")
            if not cached_session:
                raise ValueError("Objection handling session not found")
            
            session = ObjectionHandlingSession(**cached_session)
            
            # Update session
            session.customer_reaction = customer_reaction
            session.outcome = outcome
            session.resolved_at = datetime.utcnow()
            
            # Update cache
            await self.redis_manager.set_cache(
                f"objection_session_{session_id}",
                session.dict(),
                expire=86400  # 24 hours
            )
            
            # Update response effectiveness
            if session.selected_response:
                await self._update_response_effectiveness(session.selected_response.id, outcome)
            
            # Publish event
            await self.kafka_manager.publish_event(
                "objection_handling.outcome_recorded",
                {
                    "session_id": session_id,
                    "outcome": outcome,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Recorded outcome '{outcome}' for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record outcome: {e}")
            raise
    
    async def get_objection_types(self) -> List[ObjectionType]:
        """Get all objection types"""
        try:
            objection_types = []
            for key, data in self.objection_types.items():
                objection_type = ObjectionType(
                    id=len(objection_types) + 1,
                    name=data["name"],
                    category=data["category"],
                    description=data["description"],
                    common_phrases=data["common_phrases"],
                    severity_level=data["severity_level"],
                    success_rate=data["success_rate"],
                    created_at=datetime.utcnow()
                )
                objection_types.append(objection_type)
            
            return objection_types
            
        except Exception as e:
            logger.error(f"Failed to get objection types: {e}")
            raise
    
    async def get_responses_for_objection_type(self, objection_type: str) -> List[ObjectionResponse]:
        """Get responses for a specific objection type"""
        try:
            responses_data = self.objection_responses.get(objection_type, [])
            responses = []
            
            for i, data in enumerate(responses_data):
                response = ObjectionResponse(
                    id=i + 1,
                    objection_type_id=1,  # Simplified for demo
                    response_text=data["response_text"],
                    response_type=data["response_type"],
                    tone=data["tone"],
                    effectiveness_score=data["effectiveness_score"],
                    usage_count=0,
                    success_rate=0.0,
                    created_at=datetime.utcnow()
                )
                responses.append(response)
            
            return responses
            
        except Exception as e:
            logger.error(f"Failed to get responses for objection type: {e}")
            raise
    
    async def get_objection_handling_analytics(self, lead_id: int = None, sales_rep_id: int = None, date_range: str = "30d") -> Dict[str, Any]:
        """Get analytics for objection handling"""
        async with get_eric_database() as session:
            try:
                # Calculate date range
                end_date = datetime.utcnow()
                if date_range == "7d":
                    start_date = end_date - timedelta(days=7)
                elif date_range == "30d":
                    start_date = end_date - timedelta(days=30)
                elif date_range == "90d":
                    start_date = end_date - timedelta(days=90)
                else:
                    start_date = end_date - timedelta(days=30)
                
                # Query objection handling activities
                query = select(SalesActivity).where(
                    and_(
                        SalesActivity.activity_type == "objection_handling",
                        SalesActivity.created_at >= start_date,
                        SalesActivity.created_at <= end_date
                    )
                )
                
                if lead_id:
                    query = query.where(SalesActivity.lead_id == lead_id)
                if sales_rep_id:
                    query = query.where(SalesActivity.sales_rep_id == sales_rep_id)
                
                activities = await session.execute(query)
                activities = activities.scalars().all()
                
                # Calculate analytics
                total_objections = len(activities)
                resolved_objections = len([a for a in activities if a.metadata.get("resolved", False)])
                resolution_rate = resolved_objections / total_objections if total_objections > 0 else 0
                
                # Calculate average resolution time
                resolution_times = []
                for activity in activities:
                    if activity.metadata.get("resolved") and activity.metadata.get("resolution_time"):
                        resolution_times.append(activity.metadata["resolution_time"])
                
                average_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 15
                
                # Calculate objection type distribution
                objection_types = {}
                for activity in activities:
                    objection_type = activity.metadata.get("objection_type", "unknown")
                    objection_types[objection_type] = objection_types.get(objection_type, 0) + 1
                
                # Calculate response effectiveness
                response_effectiveness = {}
                response_types = ["questions", "statements", "stories", "testimonials"]
                for response_type in response_types:
                    type_activities = [a for a in activities if a.metadata.get("response_type") == response_type]
                    if type_activities:
                        successful = len([a for a in type_activities if a.metadata.get("resolved", False)])
                        effectiveness = successful / len(type_activities)
                        response_effectiveness[response_type] = effectiveness
                    else:
                        response_effectiveness[response_type] = 0.7  # Default
                
                # Get top performing responses
                top_performing_responses = []
                for activity in activities:
                    if activity.metadata.get("resolved") and activity.metadata.get("response_text"):
                        top_performing_responses.append({
                            "response_text": activity.metadata["response_text"][:100] + "...",
                            "success_rate": 1.0 if activity.metadata.get("resolved") else 0.0,
                            "usage_count": 1
                        })
                
                # Limit to top 5
                top_performing_responses = top_performing_responses[:5]
                
                # Calculate escalation rate
                escalated = len([a for a in activities if a.metadata.get("escalated", False)])
                escalation_rate = escalated / total_objections if total_objections > 0 else 0
                
                # Calculate customer satisfaction (simplified)
                satisfaction_scores = [a.metadata.get("satisfaction", 4.0) for a in activities if a.metadata.get("satisfaction")]
                customer_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 4.2
                
                analytics = {
                    "total_objections": total_objections,
                    "resolved_objections": resolved_objections,
                    "resolution_rate": resolution_rate,
                    "average_resolution_time": average_resolution_time,
                    "objection_type_distribution": objection_types,
                    "response_effectiveness": response_effectiveness,
                    "top_performing_responses": top_performing_responses,
                    "escalation_rate": escalation_rate,
                    "customer_satisfaction": customer_satisfaction
                }
                
                return analytics
            
            except Exception as e:
                logger.error(f"Failed to get objection handling analytics: {e}")
                raise
    
    def _detect_objection_type(self, objection_text: str) -> str:
        """Detect the type of objection from text"""
        objection_text_lower = objection_text.lower()
        
        # Check each objection type
        for objection_type, data in self.objection_types.items():
            for phrase in data["common_phrases"]:
                if phrase in objection_text_lower:
                    return objection_type
        
        # If no exact match, use NLP for classification
        # For demo purposes, return a default type
        return "price"
    
    def _calculate_confidence_score(self, objection_text: str, detected_type: str) -> float:
        """Calculate confidence score for objection detection"""
        objection_text_lower = objection_text.lower()
        matching_phrases = 0
        
        if detected_type in self.objection_types:
            for phrase in self.objection_types[detected_type]["common_phrases"]:
                if phrase in objection_text_lower:
                    matching_phrases += 1
        
        # Calculate confidence based on phrase matches
        total_phrases = len(self.objection_types.get(detected_type, {}).get("common_phrases", []))
        if total_phrases > 0:
            confidence = matching_phrases / total_phrases
        else:
            confidence = 0.5  # Default confidence
        
        return min(confidence, 1.0)
    
    async def _get_suggested_responses(self, objection_type: str, context: Dict[str, Any] = None) -> List[ObjectionResponse]:
        """Get suggested responses for an objection type"""
        try:
            responses_data = self.objection_responses.get(objection_type, [])
            responses = []
            
            for i, data in enumerate(responses_data):
                response = ObjectionResponse(
                    id=i + 1,
                    objection_type_id=1,  # Simplified for demo
                    response_text=data["response_text"],
                    response_type=data["response_type"],
                    tone=data["tone"],
                    effectiveness_score=data["effectiveness_score"],
                    usage_count=0,
                    success_rate=0.0,
                    created_at=datetime.utcnow()
                )
                responses.append(response)
            
            # Sort by effectiveness score
            responses.sort(key=lambda x: x.effectiveness_score, reverse=True)
            
            return responses[:3]  # Return top 3 responses
            
        except Exception as e:
            logger.error(f"Failed to get suggested responses: {e}")
            return []
    
    def _generate_recommended_approach(self, objection_type: str, severity_level: str, sentiment: str) -> str:
        """Generate recommended approach for handling objection"""
        approaches = {
            "price": {
                "low": "Focus on value proposition and ROI",
                "medium": "Address budget concerns with flexible options",
                "high": "Provide detailed cost-benefit analysis",
                "critical": "Immediate escalation to senior sales rep"
            },
            "timing": {
                "low": "Gentle follow-up and education",
                "medium": "Create urgency with limited-time offers",
                "high": "Address specific concerns and provide timeline",
                "critical": "Escalate to sales manager for urgency"
            },
            "authority": {
                "low": "Provide materials for decision maker",
                "medium": "Offer to join meeting with decision maker",
                "high": "Prepare comprehensive presentation",
                "critical": "Involve senior sales rep in decision maker meeting"
            },
            "need": {
                "low": "Educational approach with case studies",
                "medium": "Problem identification and solution mapping",
                "high": "Detailed needs analysis and ROI calculation",
                "critical": "Escalate to solutions consultant"
            },
            "competition": {
                "low": "Highlight differentiators",
                "medium": "Provide competitive analysis",
                "high": "Address specific competitor concerns",
                "critical": "Escalate to competitive specialist"
            },
            "trust": {
                "low": "Share testimonials and references",
                "medium": "Provide security documentation and certifications",
                "high": "Offer trial or pilot program",
                "critical": "Escalate to customer success team"
            }
        }
        
        return approaches.get(objection_type, {}).get(severity_level, "Address concerns directly and professionally")
    
    def _generate_follow_up_questions(self, objection_type: str, objection_text: str) -> List[str]:
        """Generate follow-up questions based on objection type"""
        questions = {
            "price": [
                "What's your budget range for this type of solution?",
                "What would make this investment worthwhile for you?",
                "How do you currently measure ROI on similar investments?"
            ],
            "timing": [
                "What specific concerns do you have about moving forward now?",
                "What would need to happen for you to feel comfortable starting?",
                "What's the cost of waiting to implement this solution?"
            ],
            "authority": [
                "What information would be most helpful for your decision maker?",
                "What concerns do you think they'll have?",
                "Would it be helpful if I joined the meeting with them?"
            ],
            "need": [
                "What's your biggest challenge right now?",
                "What would success look like for you?",
                "What happens if you don't solve this problem?"
            ],
            "competition": [
                "What specific features are you looking for?",
                "What's most important to you in a solution?",
                "What concerns do you have about our solution?"
            ],
            "trust": [
                "What would make you feel more comfortable about working with us?",
                "What specific concerns do you have about our reliability?",
                "Would speaking with our current customers help?"
            ]
        }
        
        return questions.get(objection_type, ["What specific concerns do you have?"])
    
    def _determine_escalation_needed(self, severity_level: str, confidence_score: float, sentiment: str) -> bool:
        """Determine if escalation is needed"""
        # Escalate for critical severity or very negative sentiment
        if severity_level == "critical":
            return True
        
        # Escalate for high severity with low confidence
        if severity_level == "high" and confidence_score < 0.7:
            return True
        
        # Escalate for very negative sentiment
        if sentiment == "very_negative":
            return True
        
        return False
    
    async def _update_response_effectiveness(self, response_id: int, outcome: str) -> bool:
        """Update the effectiveness score of a response"""
        async with get_eric_database() as session:
            try:
                # Update the response effectiveness in the database
                response = await session.execute(
                    select(ObjectionResponse).where(ObjectionResponse.id == response_id)
                )
                response = response.scalar_one_or_none()
                
                if response:
                    # Update usage count
                    response.usage_count += 1
                    
                    # Update success rate
                    if outcome == "success":
                        response.success_rate = ((response.success_rate * (response.usage_count - 1)) + 1) / response.usage_count
                    else:
                        response.success_rate = (response.success_rate * (response.usage_count - 1)) / response.usage_count
                    
                    # Update effectiveness score based on success rate
                    response.effectiveness_score = response.success_rate
                    
                    await session.commit()
                    logger.info(f"Updated response {response_id} effectiveness based on outcome: {outcome}")
                    return True
                else:
                    logger.warning(f"Response {response_id} not found for effectiveness update")
                    return False
                
            except Exception as e:
                logger.error(f"Failed to update response effectiveness: {e}")
                return False
