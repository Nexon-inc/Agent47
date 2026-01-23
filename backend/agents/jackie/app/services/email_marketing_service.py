import asyncio
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_jackie_database
from ..models import JackieEmailCampaign

logger = logging.getLogger(__name__)

class EmailMarketingService:
    def __init__(self):
        self.db = None
        self.event_bus = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return

        self.db = await get_jackie_database()
        self.event_bus = EventBus()
        await self.event_bus.initialize()
        self._initialized = True

    async def create_email_campaign(
        self,
        user_id: int,
        campaign_name: str,
        subject_line: str,
        email_content: str,
        recipient_list: List[str],
        sender_email: str,
        sender_name: str,
        scheduled_time: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            optimized_subject = await self._optimize_subject_line(subject_line)
            optimized_content = await self._optimize_email_content(email_content)
            
            async with self.db.get_session() as session:
                campaign = JackieEmailCampaign(
                    user_id=user_id,
                    campaign_name=campaign_name,
                    subject_line=optimized_subject,
                    email_content=optimized_content,
                    recipient_list=recipient_list,
                    sender_email=sender_email,
                    sender_name=sender_name,
                    scheduled_time=scheduled_time,
                    status="draft",
                    sent_count=0,
                    open_count=0,
                    click_count=0,
                    bounce_count=0
                )

                session.add(campaign)
                await session.commit()
                await session.refresh(campaign)

                await self.event_bus.publish(
                    "marketing.email_campaign.created",
                    {
                        "campaign_id": campaign.id,
                        "user_id": user_id,
                        "campaign_name": campaign_name,
                        "recipient_count": len(recipient_list)
                    }
                )

                return {
                    "success": True,
                    "email_campaign": {
                        "id": campaign.id,
                        "campaign_name": campaign.campaign_name,
                        "subject_line": campaign.subject_line,
                        "recipient_count": len(campaign.recipient_list),
                        "status": campaign.status.value,
                        "scheduled_time": campaign.scheduled_time
                    }
                }

        except Exception as e:
            logger.error(f"Failed to create email campaign: {e}")
            return {"success": False, "error": str(e)}

    async def create_email_template(
        self,
        user_id: int,
        template_name: str,
        subject_line: str,
        email_content: str,
        template_type: str
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                template = JackieEmailCampaign(
                    user_id=user_id,
                    campaign_name=template_name,
                    subject_line=subject_line,
                    email_content=email_content,
                    recipient_list=[],
                    sender_email="",
                    sender_name="",
                    status="template",
                    template_type=template_type
                )

                session.add(template)
                await session.commit()
                await session.refresh(template)

                return {
                    "success": True,
                    "email_template": {
                        "id": template.id,
                        "template_name": template.campaign_name,
                        "subject_line": template.subject_line,
                        "template_type": template.template_type
                    }
                }

        except Exception as e:
            logger.error(f"Failed to create email template: {e}")
            return {"success": False, "error": str(e)}

    async def get_email_analytics(self, campaign_id: int) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieEmailCampaign).where(JackieEmailCampaign.id == campaign_id)
                result = await session.execute(query)
                campaign = result.scalar_one_or_none()

                if not campaign:
                    return {"success": False, "error": "JackieCampaign not found"}

                analytics = await self._calculate_email_analytics(campaign)

                return {
                    "success": True,
                    "email_analytics": {
                        "campaign_id": campaign.id,
                        "campaign_name": campaign.campaign_name,
                        "sent_count": campaign.sent_count,
                        "open_count": campaign.open_count,
                        "click_count": campaign.click_count,
                        "bounce_count": campaign.bounce_count,
                        "open_rate": analytics["open_rate"],
                        "click_rate": analytics["click_rate"],
                        "bounce_rate": analytics["bounce_rate"]
                    }
                }

        except Exception as e:
            logger.error(f"Failed to get email analytics: {e}")
            return {"success": False, "error": str(e)}

    async def send_email_campaign(self, campaign_id: int) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieEmailCampaign).where(JackieEmailCampaign.id == campaign_id)
                result = await session.execute(query)
                campaign = result.scalar_one_or_none()

                if not campaign:
                    return {"success": False, "error": "JackieCampaign not found"}

                if campaign.status.value != "draft":
                    return {"success": False, "error": "JackieCampaign is not in draft status"}

                stmt = update(JackieEmailCampaign).where(JackieEmailCampaign.id == campaign_id).values(
                    status="sent",
                    sent_count=len(campaign.recipient_list)
                )
                await session.execute(stmt)
                await session.commit()

                await self.event_bus.publish(
                    "marketing.email_campaign.sent",
                    {
                        "campaign_id": campaign.id,
                        "user_id": campaign.user_id,
                        "sent_count": len(campaign.recipient_list)
                    }
                )

                return {
                    "success": True,
                    "email_sent": {
                        "campaign_id": campaign.id,
                        "sent_count": len(campaign.recipient_list),
                        "status": "sent"
                    }
                }

        except Exception as e:
            logger.error(f"Failed to send email campaign: {e}")
            return {"success": False, "error": str(e)}

    async def get_email_templates(self, user_id: int) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieEmailCampaign).where(
                    JackieEmailCampaign.user_id == user_id,
                    JackieEmailCampaign.status == "template"
                )
                result = await session.execute(query)
                templates = result.scalars().all()

                return {
                    "success": True,
                    "email_templates": [
                        {
                            "id": template.id,
                            "template_name": template.campaign_name,
                            "subject_line": template.subject_line,
                            "template_type": template.template_type
                        }
                        for template in templates
                    ]
                }

        except Exception as e:
            logger.error(f"Failed to get email templates: {e}")
            return {"success": False, "error": str(e)}

    async def create_email_automation(
        self,
        user_id: int,
        automation_name: str,
        trigger_conditions: Dict[str, Any],
        email_template_id: int
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                automation = JackieEmailCampaign(
                    user_id=user_id,
                    campaign_name=automation_name,
                    subject_line="",
                    email_content="",
                    recipient_list=[],
                    sender_email="",
                    sender_name="",
                    status="automation",
                    automation_conditions=trigger_conditions,
                    template_id=email_template_id
                )

                session.add(automation)
                await session.commit()
                await session.refresh(automation)

                await self.event_bus.publish(
                    "marketing.email_automation.created",
                    {
                        "automation_id": automation.id,
                        "user_id": user_id,
                        "automation_name": automation_name
                    }
                )

                return {
                    "success": True,
                    "email_automation": {
                        "id": automation.id,
                        "automation_name": automation.campaign_name,
                        "trigger_conditions": automation.automation_conditions,
                        "template_id": automation.template_id
                    }
                }

        except Exception as e:
            logger.error(f"Failed to create email automation: {e}")
            return {"success": False, "error": str(e)}

    async def _optimize_subject_line(self, subject_line: str) -> str:
        """Optimize email subject line using AI Service Manager"""
        ai_manager = await get_ai_service_manager()
        messages = [
            {"role": "system", "content": "You are an AI assistant that optimizes email subject lines for better open rates."},
            {"role": "user", "content": f"Optimize this email subject line for better open rates:\n\n{subject_line}"}
        ]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=100, temperature=0.7)
        return ai_response.text_content if ai_response.success else subject_line

    async def _optimize_email_content(self, email_content: str) -> str:
        """Optimize email content using AI Service Manager"""
        ai_manager = await get_ai_service_manager()
        messages = [
            {"role": "system", "content": "You are an AI assistant that optimizes email content for better engagement and conversions."},
            {"role": "user", "content": f"Optimize this email content for better engagement and conversions:\n\n{email_content}"}
        ]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
        return ai_response.text_content if ai_response.success else email_content

    async def _calculate_email_analytics(self, campaign: JackieEmailCampaign) -> Dict[str, float]:
        sent_count = campaign.sent_count or 0
        open_count = campaign.open_count or 0
        click_count = campaign.click_count or 0
        bounce_count = campaign.bounce_count or 0

        open_rate = (open_count / sent_count * 100) if sent_count > 0 else 0
        click_rate = (click_count / sent_count * 100) if sent_count > 0 else 0
        bounce_rate = (bounce_count / sent_count * 100) if sent_count > 0 else 0

        return {
            "open_rate": open_rate,
            "click_rate": click_rate,
            "bounce_rate": bounce_rate
        }
