import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc

from core.ai import get_ai_service_manager, AIServiceManager
from core.cache.redis_manager import init_redis
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
# NLPUtils removed - not used
from ..models import EricLead, EricLeadInteraction, CommunicationChannel, EricEmailSequence
from ..database import get_eric_database

logger = logging.getLogger(__name__)

class SalesOutreachService:
    """Service for sales outreach and communication"""
    
    def __init__(self):
        self.nlp_utils = None
        self.redis_client = None
        self.integration_manager = None
        self.platform_manager = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize sales outreach service"""
        if self._initialized:
            return
        
        try:
            # NLPUtils removed - not used in this service
            self.redis_client = await init_redis()
            self.integration_manager = IntegrationManager()
            await self.integration_manager.initialize()
            self.platform_manager = PlatformManager()
            await self.platform_manager.initialize()
            self._initialized = True
            logger.info("Eric sales outreach service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize sales outreach service: {e}")
            raise
    
    async def send_personalized_email(
        self,
        lead_id: int,
        email_template: str,
        personalization_data: Dict[str, Any],
        sender_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send personalized email to lead"""
        try:
            await self.initialize()
            
            db = next(get_db())
            lead = db.query(EricLead).filter(EricLead.id == lead_id).first()
            
            if not lead:
                return {
                    "success": False,
                    "error": "EricLead not found"
                }
            
            # Generate personalized content
            personalized_content = await self._generate_personalized_content(
                email_template,
                lead,
                personalization_data
            )
            
            # Prepare email data
            email_data = {
                "to_email": lead.email,
                "to_name": f"{lead.first_name} {lead.last_name}",
                "subject": personalized_content["subject"],
                "body": personalized_content["body"],
                "sender_name": sender_config.get("sender_name", "Sales Team"),
                "sender_email": sender_config.get("sender_email"),
                "reply_to": sender_config.get("reply_to"),
                "tracking_enabled": sender_config.get("tracking_enabled", True)
            }
            
            # Send email via integration manager
            result = await self.integration_manager.call_integration_api(
                integration_type="email",
                endpoint="send",
                method="POST",
                data=email_data,
                config=sender_config
            )
            
            if result.get("success"):
                # Record interaction
                interaction = EricLeadInteraction(
                    lead_id=lead_id,
                    interaction_type="email_sent",
                    channel=CommunicationChannel.EMAIL,
                    content=personalized_content["body"],
                    outcome="sent",
                    metadata={
                        "email_id": result.get("email_id"),
                        "subject": personalized_content["subject"],
                        "personalization_data": personalization_data
                    }
                )
                db.add(interaction)
                db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send personalized email: {e}")
            return {
                "success": False,
                "error": f"Failed to send personalized email: {str(e)}"
            }
    
    async def send_sms_outreach(
        self,
        lead_id: int,
        sms_template: str,
        personalization_data: Dict[str, Any],
        sender_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send SMS outreach to lead"""
        try:
            await self.initialize()
            
            db = next(get_db())
            lead = db.query(EricLead).filter(EricLead.id == lead_id).first()
            
            if not lead or not lead.phone:
                return {
                    "success": False,
                    "error": "EricLead not found or no phone number"
                }
            
            # Generate personalized SMS content
            personalized_content = await self._generate_personalized_content(
                sms_template,
                lead,
                personalization_data
            )
            
            # Prepare SMS data
            sms_data = {
                "to_phone": lead.phone,
                "message": personalized_content["body"],
                "sender_id": sender_config.get("sender_id"),
                "tracking_enabled": sender_config.get("tracking_enabled", True)
            }
            
            # Send SMS via integration manager
            result = await self.integration_manager.call_integration_api(
                integration_type="sms",
                endpoint="send",
                method="POST",
                data=sms_data,
                config=sender_config
            )
            
            if result.get("success"):
                # Record interaction
                interaction = EricLeadInteraction(
                    lead_id=lead_id,
                    interaction_type="sms_sent",
                    channel=CommunicationChannel.SMS,
                    content=personalized_content["body"],
                    outcome="sent",
                    metadata={
                        "sms_id": result.get("sms_id"),
                        "personalization_data": personalization_data
                    }
                )
                db.add(interaction)
                db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send SMS outreach: {e}")
            return {
                "success": False,
                "error": f"Failed to send SMS outreach: {str(e)}"
            }
    
    async def send_linkedin_message(
        self,
        lead_id: int,
        message_template: str,
        personalization_data: Dict[str, Any],
        sender_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send LinkedIn message to lead"""
        try:
            await self.initialize()
            
            db = next(get_db())
            lead = db.query(EricLead).filter(EricLead.id == lead_id).first()
            
            if not lead:
                return {
                    "success": False,
                    "error": "EricLead not found"
                }
            
            # Get LinkedIn profile from social profiles
            social_profiles = lead.social_profiles or {}
            linkedin_profile = social_profiles.get("linkedin")
            
            if not linkedin_profile:
                return {
                    "success": False,
                    "error": "No LinkedIn profile found for lead"
                }
            
            # Generate personalized message
            personalized_content = await self._generate_personalized_content(
                message_template,
                lead,
                personalization_data
            )
            
            # Prepare LinkedIn message data
            linkedin_data = {
                "profile_url": linkedin_profile,
                "message": personalized_content["body"],
                "sender_profile": sender_config.get("sender_profile"),
                "connection_request": sender_config.get("connection_request", False)
            }
            
            # Send LinkedIn message via platform manager
            result = await self.platform_manager.send_linkedin_message(
                profile_url=linkedin_profile,
                message=personalized_content["body"],
                config=sender_config
            )
            
            if result.get("success"):
                # Record interaction
                interaction = EricLeadInteraction(
                    lead_id=lead_id,
                    interaction_type="linkedin_message_sent",
                    channel=CommunicationChannel.LINKEDIN,
                    content=personalized_content["body"],
                    outcome="sent",
                    metadata={
                        "linkedin_profile": linkedin_profile,
                        "personalization_data": personalization_data
                    }
                )
                db.add(interaction)
                db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send LinkedIn message: {e}")
            return {
                "success": False,
                "error": f"Failed to send LinkedIn message: {str(e)}"
            }
    
    async def create_follow_up_sequence(
        self,
        lead_id: int,
        sequence_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create automated follow-up sequence for lead"""
        try:
            await self.initialize()
            
            db = next(get_db())
            lead = db.query(EricLead).filter(EricLead.id == lead_id).first()
            
            if not lead:
                return {
                    "success": False,
                    "error": "EricLead not found"
                }
            
            # Create email sequence
            sequence = EricEmailSequence(
                campaign_id=sequence_config.get("campaign_id"),
                sequence_name=sequence_config.get("sequence_name", "Follow-up Sequence"),
                subject_line=sequence_config.get("subject_line"),
                email_content=sequence_config.get("email_content"),
                delay_days=sequence_config.get("delay_days", 1),
                sequence_order=sequence_config.get("sequence_order", 1),
                active=True
            )
            db.add(sequence)
            db.commit()
            
            # Schedule follow-up emails
            scheduled_emails = []
            for i, email_config in enumerate(sequence_config.get("emails", [])):
                delay_days = email_config.get("delay_days", (i + 1) * 2)
                scheduled_date = datetime.now() + timedelta(days=delay_days)
                
                scheduled_email = {
                    "lead_id": lead_id,
                    "sequence_id": sequence.id,
                    "email_config": email_config,
                    "scheduled_date": scheduled_date.isoformat(),
                    "status": "scheduled"
                }
                scheduled_emails.append(scheduled_email)
            
            # Store scheduled emails in Redis for processing
            await self.redis_client.hset(
                f"follow_up_sequence:{sequence.id}",
                mapping={
                    "lead_id": lead_id,
                    "scheduled_emails": json.dumps(scheduled_emails),
                    "status": "active"
                }
            )
            
            return {
                "success": True,
                "sequence_id": sequence.id,
                "scheduled_emails": len(scheduled_emails),
                "next_email_date": scheduled_emails[0]["scheduled_date"] if scheduled_emails else None
            }
            
        except Exception as e:
            logger.error(f"Failed to create follow-up sequence: {e}")
            return {
                "success": False,
                "error": f"Failed to create follow-up sequence: {str(e)}"
            }
    
    async def get_outreach_analytics(
        self,
        brand_id: int,
        date_range: str = "30d"
    ) -> Dict[str, Any]:
        """Get outreach analytics and performance metrics"""
        try:
            await self.initialize()
            
            # Calculate date range
            end_date = datetime.now()
            if date_range == "7d":
                start_date = end_date - timedelta(days=7)
            elif date_range == "30d":
                start_date = end_date - timedelta(days=30)
            elif date_range == "90d":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)
            
            db = next(get_db())
            
            # Get interactions in date range
            interactions = db.query(EricLeadInteraction).join(EricLead).filter(
                and_(
                    EricLead.brand_id == brand_id,
                    EricLeadInteraction.created_at >= start_date,
                    EricLeadInteraction.created_at <= end_date
                )
            ).all()
            
            # Calculate analytics
            total_interactions = len(interactions)
            email_interactions = len([i for i in interactions if i.channel == CommunicationChannel.EMAIL])
            sms_interactions = len([i for i in interactions if i.channel == CommunicationChannel.SMS])
            linkedin_interactions = len([i for i in interactions if i.channel == CommunicationChannel.LINKEDIN])
            
            # Calculate response rates
            responses = [i for i in interactions if i.outcome in ["replied", "responded", "engaged"]]
            response_rate = (len(responses) / total_interactions * 100) if total_interactions > 0 else 0
            
            # Calculate channel performance
            channel_performance = {}
            for channel in [CommunicationChannel.EMAIL, CommunicationChannel.SMS, CommunicationChannel.LINKEDIN]:
                channel_interactions = [i for i in interactions if i.channel == channel]
                channel_responses = [i for i in channel_interactions if i.outcome in ["replied", "responded", "engaged"]]
                channel_response_rate = (len(channel_responses) / len(channel_interactions) * 100) if channel_interactions else 0
                
                channel_performance[channel.value] = {
                    "total_sent": len(channel_interactions),
                    "responses": len(channel_responses),
                    "response_rate": round(channel_response_rate, 2)
                }
            
            analytics = {
                "date_range": date_range,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_interactions": total_interactions,
                "response_rate": round(response_rate, 2),
                "channel_breakdown": {
                    "email": email_interactions,
                    "sms": sms_interactions,
                    "linkedin": linkedin_interactions
                },
                "channel_performance": channel_performance,
                "top_performing_channels": sorted(
                    channel_performance.items(),
                    key=lambda x: x[1]["response_rate"],
                    reverse=True
                )[:3]
            }
            
            return {
                "success": True,
                "analytics": analytics
            }
            
        except Exception as e:
            logger.error(f"Failed to get outreach analytics: {e}")
            return {
                "success": False,
                "error": f"Failed to get outreach analytics: {str(e)}"
            }
    
    async def _generate_personalized_content(
        self,
        template: str,
        lead: EricLead,
        personalization_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate personalized content using NLP"""
        try:
            # Prepare personalization context
            context = {
                "lead_first_name": lead.first_name,
                "lead_last_name": lead.last_name,
                "lead_company": lead.company or "your company",
                "lead_job_title": lead.job_title or "your role",
                "lead_industry": lead.industry or "your industry",
                "lead_location": lead.location or "your location",
                **personalization_data
            }
            
            # Generate personalized content using NLP
            prompt = f"""
            Personalize this template for a sales outreach:
            
            Template: {template}
            
            EricLead Information:
            - Name: {lead.first_name} {lead.last_name}
            - Company: {lead.company}
            - Job Title: {lead.job_title}
            - Industry: {lead.industry}
            - Location: {lead.location}
            
            Personalization Data: {personalization_data}
            
            Generate a personalized version that feels natural and relevant to this specific lead.
            """
            
            # Use AI Service Manager instead of NLPUtils (consistent with Aria)
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant helping personalize sales outreach messages."},
                {"role": "user", "content": prompt}
            ]
            ai_response = await ai_manager.generate_text(
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            personalized_content = ai_response.text_content if ai_response.success else ""
            
            # Extract subject and body if template contains both
            if "Subject:" in personalized_content and "Body:" in personalized_content:
                parts = personalized_content.split("Body:")
                subject = parts[0].replace("Subject:", "").strip()
                body = parts[1].strip()
            else:
                subject = "Personalized message from our team"
                body = personalized_content
            
            return {
                "subject": subject,
                "body": body
            }
            
        except Exception as e:
            logger.error(f"Failed to generate personalized content: {e}")
            return {
                "subject": "Personalized message from our team",
                "body": template
            }
