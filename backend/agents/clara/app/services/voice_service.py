import uuid
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.storage.s3_manager import storage_manager
from ..database import get_clara_database
from ..models import (
    SupportTicket, CustomerInteraction, TicketCategory, SupportChannel,
    SentimentType, InteractionType, TicketAttachment
)

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.storage_manager = storage_manager
        self._initialized = False
    
    async def initialize(self):
        """Initialize voice service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            # Storage manager is already initialized
            self._initialized = True
            logger.info("Clara voice service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize voice service: {e}")
            raise
    
    async def process_voice_message(
        self,
        customer_id: int,
        audio_file_path: str,
        channel: SupportChannel = SupportChannel.PHONE,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process voice message and create support ticket"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Transcribe audio to text
            transcription_result = await self._transcribe_audio(audio_file_path)
            if not transcription_result["success"]:
                return {"success": False, "error": "Failed to transcribe audio"}
            
            transcribed_text = transcription_result["text"]
            confidence = transcription_result["confidence"]
            
            # Analyze sentiment and intent
            sentiment_result = await self._analyze_voice_sentiment(transcribed_text)
            intent_result = await self._analyze_voice_intent(transcribed_text)
            
            # Determine ticket category and priority
            category = await self._determine_voice_category(transcribed_text, intent_result)
            priority = await self._determine_voice_priority(transcribed_text, sentiment_result, category)
            
            # Create support ticket
            from .support_service import SupportService
            support_service = SupportService()
            await support_service.initialize()
            
            ticket_result = await support_service.create_ticket(
                customer_id=customer_id,
                channel=channel,
                category=category,
                subject=f"Voice Support Request - {category.value.title()}",
                description=transcribed_text,
                priority=priority,
                tags=["voice", "transcribed"],
                metadata={
                    "voice_processing": {
                        "audio_file_path": audio_file_path,
                        "transcription_confidence": confidence,
                        "sentiment_analysis": sentiment_result,
                        "intent_analysis": intent_result,
                        "original_metadata": metadata or {}
                    }
                }
            )
            
            if not ticket_result["success"]:
                return ticket_result
            
            # Upload audio file to S3
            s3_result = await self._upload_voice_file(
                audio_file_path=audio_file_path,
                ticket_id=ticket_result["ticket"]["id"],
                customer_id=customer_id
            )
            
            # Create voice interaction record
            await self._create_voice_interaction(
                ticket_id=ticket_result["ticket"]["id"],
                customer_id=customer_id,
                transcribed_text=transcribed_text,
                audio_file_path=audio_file_path,
                s3_url=s3_result.get("s3_url") if s3_result["success"] else None,
                confidence=confidence,
                sentiment=sentiment_result["sentiment_type"],
                metadata=metadata
            )
            
            return {
                "success": True,
                "ticket": ticket_result["ticket"],
                "transcription": {
                    "text": transcribed_text,
                    "confidence": confidence
                },
                "analysis": {
                    "sentiment": sentiment_result,
                    "intent": intent_result,
                    "category": category.value,
                    "priority": priority.value
                },
                "audio_storage": s3_result
            }
            
        except Exception as e:
            logger.error(f"Failed to process voice message: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_voice_response(
        self,
        message: str,
        response_type: str = "support_response",
        language: str = "en",
        voice_style: str = "professional"
    ) -> Dict[str, Any]:
        """Generate voice response text and optionally convert to speech"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Generate appropriate response based on type
            if response_type == "support_response":
                response = await self._generate_support_voice_response(message, language, voice_style)
            elif response_type == "confirmation":
                response = await self._generate_confirmation_voice_response(message, language, voice_style)
            elif response_type == "escalation":
                response = await self._generate_escalation_voice_response(message, language, voice_style)
            else:
                response = await self._generate_general_voice_response(message, language, voice_style)
            
            if not response["success"]:
                return response
            
            # Convert text to speech if requested
            speech_result = await self._text_to_speech(
                text=response["response"],
                language=language,
                voice_style=voice_style
            )
            
            return {
                "success": True,
                "text_response": response["response"],
                "speech_audio": speech_result.get("audio_data") if speech_result["success"] else None,
                "speech_metadata": speech_result.get("metadata") if speech_result["success"] else None
            }
            
        except Exception as e:
            logger.error(f"Failed to generate voice response: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_ivr_interaction(
        self,
        customer_id: int,
        phone_number: str,
        menu_selection: str,
        spoken_input: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle IVR (Interactive Voice Response) interactions"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Process IVR menu selection
            ivr_result = await self._process_ivr_menu(menu_selection, spoken_input)
            
            if ivr_result["requires_human"]:
                # Create support ticket for human intervention
                from .support_service import SupportService
                support_service = SupportService()
                await support_service.initialize()
                
                ticket_result = await support_service.create_ticket(
                    customer_id=customer_id,
                    channel=SupportChannel.IVR,
                    category=ivr_result["category"],
                    subject=f"IVR Escalation - {ivr_result['menu_option']}",
                    description=f"IVR Menu Selection: {menu_selection}\nSpoken Input: {spoken_input or 'None'}\nReason: {ivr_result['escalation_reason']}",
                    priority=ivr_result["priority"],
                    tags=["ivr", "escalation"],
                    metadata={
                        "ivr_interaction": {
                            "phone_number": phone_number,
                            "menu_selection": menu_selection,
                            "spoken_input": spoken_input,
                            "escalation_reason": ivr_result["escalation_reason"],
                            "original_metadata": metadata or {}
                        }
                    }
                )
                
                return {
                    "success": True,
                    "action": "escalate_to_human",
                    "ticket": ticket_result["ticket"],
                    "message": ivr_result["escalation_message"],
                    "estimated_wait_time": ivr_result["estimated_wait_time"]
                }
            else:
                # Handle automated IVR response
                response = await self._generate_ivr_response(
                    menu_selection=menu_selection,
                    spoken_input=spoken_input,
                    customer_id=customer_id
                )
                
                return {
                    "success": True,
                    "action": "automated_response",
                    "response": response["response"],
                    "next_menu_options": response["next_menu_options"],
                    "estimated_resolution_time": response["estimated_resolution_time"]
                }
                
        except Exception as e:
            logger.error(f"Failed to handle IVR interaction: {e}")
            return {"success": False, "error": str(e)}
    
    async def _transcribe_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio file to text using Groq STT via AI Service Manager"""
        try:
            from backend.core.ai import get_ai_service_manager
            
            ai_manager = await get_ai_service_manager()
            
            # Use AI Service Manager's transcribe_audio_file method
            result = await ai_manager.transcribe_audio_file(
                audio_file_path=audio_file_path
            )
            
            if not result.get("success"):
                return result
            
            # Format response to match expected structure
            return {
                "success": True,
                "text": result.get("text", ""),
                "confidence": result.get("confidence", 0.0),
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", []),
                "metadata": result.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_voice_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of transcribed voice text"""
        try:
            sentiment_prompt = f"""Analyze the sentiment of this transcribed voice message and respond with a JSON object containing:
1. sentiment_type (positive, neutral, negative, frustrated, satisfied, urgent)
2. sentiment_score (float between -1.0 and 1.0)
3. urgency_level (1-5, where 5 is most urgent)
4. emotional_tone (calm, agitated, confused, confident, etc.)

Voice Message: {text}"""
            
            messages = [
                {"role": "system", "content": sentiment_prompt},
                {"role": "user", "content": text}
            ]
            
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=100,
                temperature=0.3
            )
            
            if response.success:
                try:
                    sentiment_data = json.loads(response.text_content)
                    return {
                        "success": True,
                        "sentiment_type": SentimentType(sentiment_data["sentiment_type"]),
                        "sentiment_score": sentiment_data["sentiment_score"],
                        "urgency_level": sentiment_data["urgency_level"],
                        "emotional_tone": sentiment_data["emotional_tone"]
                    }
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass
            
            # Fallback sentiment analysis
            text_lower = text.lower()
            negative_words = ["error", "broken", "failed", "issue", "problem", "urgent", "critical", "angry", "frustrated"]
            positive_words = ["thank", "great", "good", "excellent", "working", "solved", "happy", "satisfied"]
            urgent_words = ["urgent", "critical", "emergency", "immediately", "now", "asap"]
            
            negative_count = sum(1 for word in negative_words if word in text_lower)
            positive_count = sum(1 for word in positive_words if word in text_lower)
            urgent_count = sum(1 for word in urgent_words if word in text_lower)
            
            if urgent_count > 0:
                sentiment_type = SentimentType.FRUSTRATED
                urgency_level = 5
            elif negative_count > positive_count:
                sentiment_type = SentimentType.NEGATIVE
                urgency_level = 4
            elif positive_count > negative_count:
                sentiment_type = SentimentType.POSITIVE
                urgency_level = 2
            else:
                sentiment_type = SentimentType.NEUTRAL
                urgency_level = 3
            
            return {
                "success": True,
                "sentiment_type": sentiment_type,
                "sentiment_score": -0.5 if sentiment_type == SentimentType.NEGATIVE else 0.5 if sentiment_type == SentimentType.POSITIVE else 0.0,
                "urgency_level": urgency_level,
                "emotional_tone": "agitated" if urgent_count > 0 else "neutral"
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze voice sentiment: {e}")
            return {
                "success": True,
                "sentiment_type": SentimentType.NEUTRAL,
                "sentiment_score": 0.0,
                "urgency_level": 3,
                "emotional_tone": "neutral"
            }
    
    async def _analyze_voice_intent(self, text: str) -> Dict[str, Any]:
        """Analyze intent of transcribed voice text"""
        try:
            intent_prompt = f"""Analyze this transcribed voice message and determine the customer's intent. Respond with a JSON object containing:
1. primary_intent (what they want to accomplish)
2. secondary_intent (additional goals if any)
3. category (technical, billing, general, account, order, etc.)
4. complexity (simple, moderate, complex, high)
5. requires_immediate_action (boolean)
6. suggested_response_type (automated, human_agent, specialist)

Voice Message: {text}"""
            
            messages = [
                {"role": "system", "content": intent_prompt},
                {"role": "user", "content": text}
            ]
            
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=150,
                temperature=0.3
            )
            
            if response.success:
                try:
                    intent_data = json.loads(response.text_content)
                    return {
                        "success": True,
                        "primary_intent": intent_data["primary_intent"],
                        "secondary_intent": intent_data.get("secondary_intent"),
                        "category": intent_data["category"],
                        "complexity": intent_data["complexity"],
                        "requires_immediate_action": intent_data["requires_immediate_action"],
                        "suggested_response_type": intent_data["suggested_response_type"]
                    }
                except (json.JSONDecodeError, KeyError):
                    pass
            
            # Fallback intent analysis
            text_lower = text.lower()
            
            if any(word in text_lower for word in ["error", "broken", "not working", "issue", "problem"]):
                primary_intent = "technical_support"
                category = "technical"
                complexity = "moderate"
            elif any(word in text_lower for word in ["bill", "payment", "charge", "refund", "money"]):
                primary_intent = "billing_inquiry"
                category = "billing"
                complexity = "simple"
            elif any(word in text_lower for word in ["account", "login", "password", "access"]):
                primary_intent = "account_help"
                category = "account_issue"
                complexity = "simple"
            elif any(word in text_lower for word in ["order", "track", "delivery", "shipping"]):
                primary_intent = "order_tracking"
                category = "order_tracking"
                complexity = "simple"
            else:
                primary_intent = "general_inquiry"
                category = "general"
                complexity = "simple"
            
            return {
                "success": True,
                "primary_intent": primary_intent,
                "secondary_intent": None,
                "category": category,
                "complexity": complexity,
                "requires_immediate_action": "urgent" in text_lower or "critical" in text_lower,
                "suggested_response_type": "human_agent" if complexity == "complex" else "automated"
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze voice intent: {e}")
            return {
                "success": True,
                "primary_intent": "general_inquiry",
                "secondary_intent": None,
                "category": "general",
                "complexity": "simple",
                "requires_immediate_action": False,
                "suggested_response_type": "automated"
            }
    
    async def _determine_voice_category(
        self,
        text: str,
        intent_result: Dict[str, Any]
    ) -> TicketCategory:
        """Determine ticket category from voice input"""
        try:
            category_mapping = {
                "technical": TicketCategory.TECHNICAL,
                "billing": TicketCategory.BILLING,
                "account": TicketCategory.ACCOUNT_ISSUE,
                "order": TicketCategory.ORDER_TRACKING,
                "product": TicketCategory.PRODUCT_SUPPORT,
                "bug": TicketCategory.BUG_REPORT,
                "feature": TicketCategory.FEATURE_REQUEST,
                "security": TicketCategory.SECURITY,
                "integration": TicketCategory.INTEGRATION
            }
            
            return category_mapping.get(intent_result["category"], TicketCategory.GENERAL)
            
        except Exception as e:
            logger.error(f"Failed to determine voice category: {e}")
            return TicketCategory.GENERAL
    
    async def _determine_voice_priority(
        self,
        text: str,
        sentiment_result: Dict[str, Any],
        category: TicketCategory
    ) -> str:
        """Determine ticket priority from voice input"""
        try:
            # Base priority on urgency level and category
            urgency_level = sentiment_result.get("urgency_level", 3)
            
            if urgency_level >= 5 or category in [TicketCategory.SECURITY, TicketCategory.BUG_REPORT]:
                return "critical"
            elif urgency_level >= 4 or category in [TicketCategory.TECHNICAL, TicketCategory.ACCOUNT_ISSUE]:
                return "high"
            elif urgency_level >= 3 or category in [TicketCategory.BILLING, TicketCategory.ORDER_TRACKING]:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            logger.error(f"Failed to determine voice priority: {e}")
            return "medium"
    
    async def _upload_voice_file(
        self,
        audio_file_path: str,
        ticket_id: int,
        customer_id: int
    ) -> Dict[str, Any]:
        """Upload voice file to Supabase Storage"""
        try:
            # Generate storage key
            file_extension = audio_file_path.split(".")[-1]
            storage_key = f"voice_support/{customer_id}/{ticket_id}/{uuid.uuid4().hex}.{file_extension}"
            
            # Upload to Supabase Storage
            with open(audio_file_path, "rb") as audio_file:
                file_data = audio_file.read()
                storage_url = self.storage_manager.put_bytes(
                    file_data,
                    f"audio/{file_extension}",
                    storage_key
                )
            
            return {
                "success": True,
                "s3_url": storage_url,  # Keep s3_url for backward compatibility
                "s3_key": storage_key,  # Keep s3_key for backward compatibility
                "file_size": len(file_data)
            }
                
        except Exception as e:
            logger.error(f"Failed to upload voice file: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_voice_interaction(
        self,
        ticket_id: int,
        customer_id: int,
        transcribed_text: str,
        audio_file_path: str,
        s3_url: Optional[str],
        confidence: float,
        sentiment: SentimentType,
        metadata: Optional[Dict[str, Any]]
    ):
        """Create voice interaction record"""
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Create interaction record
                interaction = CustomerInteraction(
                    ticket_id=ticket_id,
                    interaction_type=InteractionType.CUSTOMER_MESSAGE,
                    channel=SupportChannel.PHONE,
                    message=transcribed_text,
                    sentiment=sentiment,
                    is_automated=False,
                    metadata={
                        "voice_interaction": {
                            "audio_file_path": audio_file_path,
                            "s3_url": s3_url,
                            "transcription_confidence": confidence,
                            "original_metadata": metadata or {}
                        }
                    }
                )
                session.add(interaction)
                
                # Create attachment record if S3 upload was successful
                if s3_url:
                    attachment = TicketAttachment(
                        ticket_id=ticket_id,
                        filename=f"voice_message_{uuid.uuid4().hex[:8]}.wav",
                        file_path=s3_url,
                        file_size=0,  # Will be updated if available
                        mime_type="audio/wav",
                        description="Voice message recording",
                        uploaded_by=customer_id
                    )
                    session.add(attachment)
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to create voice interaction: {e}")
    
    async def _process_ivr_menu(
        self,
        menu_selection: str,
        spoken_input: Optional[str]
    ) -> Dict[str, Any]:
        """Process IVR menu selection and determine action"""
        try:
            # Simple IVR logic - can be expanded
            if menu_selection == "1" or (spoken_input and "technical" in spoken_input.lower()):
                return {
                    "requires_human": False,
                    "category": "technical",
                    "menu_option": "Technical Support",
                    "escalation_reason": None,
                    "priority": "medium",
                    "estimated_wait_time": None
                }
            elif menu_selection == "2" or (spoken_input and "billing" in spoken_input.lower()):
                return {
                    "requires_human": False,
                    "category": "billing",
                    "menu_option": "Billing Support",
                    "escalation_reason": None,
                    "priority": "medium",
                    "estimated_wait_time": None
                }
            elif menu_selection == "3" or (spoken_input and "speak" in spoken_input.lower()):
                return {
                    "requires_human": True,
                    "category": "general",
                    "menu_option": "Speak to Representative",
                    "escalation_reason": "Customer requested human assistance",
                    "priority": "medium",
                    "estimated_wait_time": "5-10 minutes"
                }
            else:
                return {
                    "requires_human": True,
                    "category": "general",
                    "menu_option": "General Inquiry",
                    "escalation_reason": "Unclear menu selection",
                    "priority": "low",
                    "estimated_wait_time": "10-15 minutes"
                }
                
        except Exception as e:
            logger.error(f"Failed to process IVR menu: {e}")
            return {
                "requires_human": True,
                "category": "general",
                "menu_option": "Error",
                "escalation_reason": "IVR processing error",
                "priority": "medium",
                "estimated_wait_time": "5-10 minutes"
            }
    
    async def _generate_ivr_response(
        self,
        menu_selection: str,
        spoken_input: Optional[str],
        customer_id: int
    ) -> Dict[str, Any]:
        """Generate IVR response"""
        try:
            if menu_selection == "1":
                response = "Thank you for selecting technical support. I can help you with most technical issues. Please describe your problem, and I'll either solve it or connect you with a specialist."
                next_menu_options = ["Continue with automated help", "Speak to human agent"]
                estimated_time = "2-5 minutes"
            elif menu_selection == "2":
                response = "Thank you for selecting billing support. I can help you with payment questions, refunds, and billing issues. Please provide your account details or describe your billing concern."
                next_menu_options = ["Continue with automated help", "Speak to human agent"]
                estimated_time = "3-7 minutes"
            else:
                response = "I understand you need assistance. Let me help you with your inquiry. Please describe what you need help with."
                next_menu_options = ["Continue with automated help", "Speak to human agent"]
                estimated_time = "5-10 minutes"
            
            return {
                "success": True,
                "response": response,
                "next_menu_options": next_menu_options,
                "estimated_resolution_time": estimated_time
            }
            
        except Exception as e:
            logger.error(f"Failed to generate IVR response: {e}")
            return {
                "success": True,
                "response": "I apologize, but I'm experiencing some technical difficulties. Let me connect you with our support team.",
                "next_menu_options": ["Speak to human agent"],
                "estimated_resolution_time": "5-10 minutes"
            }
    
    async def _text_to_speech(
        self,
        text: str,
        language: str = "en",
        voice_style: str = "professional"
    ) -> Dict[str, Any]:
        """Convert text to speech using Groq TTS via AI Service Manager"""
        try:
            from backend.core.ai import get_ai_service_manager
            
            ai_manager = await get_ai_service_manager()
            
            # Use AI Service Manager's text_to_speech method
            result = await ai_manager.text_to_speech(
                text=text,
                language=language,
                voice_style=voice_style
            )
            
            if not result.get("success"):
                return result
            
            # Save to temporary file for compatibility
            import tempfile
            import os
            
            audio_data = result.get("audio_data")
            if not audio_data:
                return {
                    "success": False,
                    "error": "No audio data returned from TTS service"
                }
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Merge metadata
            metadata = result.get("metadata", {})
            metadata.update({
                "voice_style": voice_style,
                "text_length": len(text)
            })
            
            return {
                "success": True,
                "audio_data": audio_data,
                "temp_file_path": temp_file_path,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to convert text to speech: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_support_voice_response(
        self,
        message: str,
        language: str,
        voice_style: str
    ) -> Dict[str, Any]:
        """Generate support voice response"""
        try:
            response_prompt = f"""Generate a helpful, professional voice response for a customer support scenario. The response should be:
- Conversational and natural for voice
- Concise but informative
- Professional yet warm
- Easy to understand when spoken

Customer Message: {message}
Language: {language}
Voice Style: {voice_style}

Generate a natural voice response:"""
            
            messages = [
                {"role": "system", "content": response_prompt},
                {"role": "user", "content": text}
            ]
            
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            if response.success:
                return {"success": True, "response": response.text_content}
            else:
                return response
                
        except Exception as e:
            logger.error(f"Failed to generate support voice response: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_confirmation_voice_response(
        self,
        message: str,
        language: str,
        voice_style: str
    ) -> Dict[str, Any]:
        """Generate confirmation voice response"""
        try:
            response_prompt = f"""Generate a confirmation voice response that:
- Confirms understanding of the customer's request
- Provides clear next steps
- Reassures the customer
- Is natural for voice communication

Customer Request: {message}
Language: {language}
Voice Style: {voice_style}

Generate a confirmation response:"""
            
            messages = [
                {"role": "system", "content": response_prompt},
                {"role": "user", "content": text}
            ]
            
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            if response.success:
                return {"success": True, "response": response.text_content}
            else:
                return response
                
        except Exception as e:
            logger.error(f"Failed to generate confirmation voice response: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_escalation_voice_response(
        self,
        message: str,
        language: str,
        voice_style: str
    ) -> Dict[str, Any]:
        """Generate escalation voice response"""
        try:
            response_prompt = f"""Generate a voice response for escalating a customer request to a human agent. The response should:
- Acknowledge the customer's need
- Explain why escalation is necessary
- Provide estimated wait time
- Reassure the customer
- Be natural for voice communication

Customer Request: {message}
Language: {language}
Voice Style: {voice_style}

Generate an escalation response:"""
            
            messages = [
                {"role": "system", "content": response_prompt},
                {"role": "user", "content": text}
            ]
            
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            if response.success:
                return {"success": True, "response": response.text_content}
            else:
                return response
                
        except Exception as e:
            logger.error(f"Failed to generate escalation voice response: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_general_voice_response(
        self,
        message: str,
        language: str,
        voice_style: str
    ) -> Dict[str, Any]:
        """Generate general voice response"""
        try:
            response_prompt = f"""Generate a general helpful voice response for a customer. The response should be:
- Helpful and informative
- Natural for voice communication
- Professional and friendly
- Easy to understand when spoken

Customer Message: {message}
Language: {language}
Voice Style: {voice_style}

Generate a helpful response:"""
            
            messages = [
                {"role": "system", "content": response_prompt},
                {"role": "user", "content": text}
            ]
            
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            if response.success:
                return {"success": True, "response": response.text_content}
            else:
                return response
                
        except Exception as e:
            logger.error(f"Failed to generate general voice response: {e}")
            return {"success": False, "error": str(e)}


# Backwards-compatible alias: some modules import ClaraVoiceService
# while the concrete class is named VoiceService. Expose the alias after
# the class definition so imports like `from ...voice_service import ClaraVoiceService`
# succeed without changing multiple files across the codebase.
ClaraVoiceService = VoiceService
