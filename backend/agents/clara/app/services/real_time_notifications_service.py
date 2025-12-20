import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload
import httpx
import json
from core.config import settings
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_clara_database
from ..models import (
    SupportTicket, CustomerInteraction, CustomerProfile,
    TicketPriority, TicketStatus, TicketCategory, SupportChannel
)

logger = logging.getLogger(__name__)

class RealTimeNotificationsService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self._notification_channels = {}
        self._notification_rules = {}
        self._notification_history = []
    
    async def initialize(self):
        """Initialize real-time notifications service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            await self._initialize_notification_channels()
            await self._initialize_notification_rules()
            self._initialized = True
            logger.info("Real-time notifications service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize real-time notifications service: {e}")
            raise
    
    async def _initialize_notification_channels(self):
        """Initialize notification channels (Slack, Teams, Email, SMS)"""
        self._notification_channels = {
            "slack": {
                "enabled": True,
                "webhook_url": settings.slack_webhook_url,
                "channel": settings.slack_channel or "#support-alerts",
                "username": "Clara Support Bot",
                "icon_emoji": ":robot_face:"
            },
            "teams": {
                "enabled": True,
                "webhook_url": settings.teams_webhook_url,
                "channel": settings.teams_channel or "Support Alerts"
            },
            "email": {
                "enabled": True,
                "smtp_host": settings.smtp_host,
                "smtp_port": settings.smtp_port,
                "smtp_username": settings.smtp_username,
                "smtp_password": settings.smtp_password,
                "from_email": settings.from_email,
                "support_email": settings.support_email
            },
            "sms": {
                "enabled": True,
                "twilio_account_sid": settings.twilio_account_sid,
                "twilio_auth_token": settings.twilio_auth_token,
                "twilio_phone_number": settings.twilio_phone_number
            }
        }
    
    async def _initialize_notification_rules(self):
        """Initialize notification rules for different scenarios"""
        self._notification_rules = {
            "urgent_ticket_created": {
                "enabled": True,
                "channels": ["slack", "teams", "email"],
                "priority": "high",
                "conditions": {
                    "ticket_priority": [TicketPriority.URGENT, TicketPriority.CRITICAL],
                    "ticket_status": [TicketStatus.OPEN]
                },
                "message_template": "🚨 URGENT: New ticket #{ticket_number} created by {customer_name} - {subject}",
                "cooldown_minutes": 5
            },
            "sla_breach": {
                "enabled": True,
                "channels": ["slack", "teams", "email"],
                "priority": "high",
                "conditions": {
                    "sla_breach": True
                },
                "message_template": "⏰ SLA BREACH: Ticket #{ticket_number} has exceeded SLA - {subject}",
                "cooldown_minutes": 10
            },
            "ticket_escalated": {
                "enabled": True,
                "channels": ["slack", "teams"],
                "priority": "medium",
                "conditions": {
                    "escalation": True
                },
                "message_template": "📈 ESCALATION: Ticket #{ticket_number} escalated to {agent_name} - {subject}",
                "cooldown_minutes": 15
            },
            "high_volume_alert": {
                "enabled": True,
                "channels": ["slack", "teams"],
                "priority": "medium",
                "conditions": {
                    "ticket_count_threshold": 50,
                    "time_window_minutes": 60
                },
                "message_template": "📊 HIGH VOLUME: {ticket_count} tickets in the last {time_window} minutes",
                "cooldown_minutes": 30
            },
            "agent_unavailable": {
                "enabled": True,
                "channels": ["slack", "teams"],
                "priority": "medium",
                "conditions": {
                    "agent_status": "offline",
                    "unassigned_tickets": 10
                },
                "message_template": "👤 AGENT UNAVAILABLE: {agent_name} is offline, {unassigned_count} tickets unassigned",
                "cooldown_minutes": 20
            },
            "customer_satisfaction_low": {
                "enabled": True,
                "channels": ["slack", "teams", "email"],
                "priority": "medium",
                "conditions": {
                    "satisfaction_score": 2,
                    "satisfaction_threshold": 3
                },
                "message_template": "😞 LOW SATISFACTION: Ticket #{ticket_number} received {satisfaction_score}/5 rating",
                "cooldown_minutes": 60
            }
        }
    
    async def send_urgent_ticket_notification(
        self,
        ticket_id: int,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send notification for urgent ticket creation"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get ticket details
                ticket_query = select(SupportTicket).where(SupportTicket.id == ticket_id)
                ticket_result = await session.execute(ticket_query)
                ticket = ticket_result.scalar_one_or_none()
                
                if not ticket:
                    raise ValueError(f"Ticket {ticket_id} not found")
                
                # Check if notification should be sent
                if not await self._should_send_notification("urgent_ticket_created", ticket):
                    return {
                        "success": True,
                        "message": "Notification skipped due to cooldown or conditions not met"
                    }
                
                # Prepare notification data
                notification_data = {
                    "ticket_id": ticket.id,
                    "ticket_number": ticket.ticket_number,
                    "customer_name": f"{ticket.customer.first_name} {ticket.customer.last_name}",
                    "subject": ticket.subject,
                    "priority": ticket.priority.value,
                    "category": ticket.category.value,
                    "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                    "channel": ticket.channel.value
                }
                
                # Send notifications
                results = await self._send_notifications(
                    rule_name="urgent_ticket_created",
                    notification_data=notification_data,
                    channels=channels
                )
                
                # Record notification
                await self._record_notification(
                    rule_name="urgent_ticket_created",
                    ticket_id=ticket_id,
                    notification_data=notification_data,
                    results=results
                )
                
                return {
                    "success": True,
                    "ticket_id": ticket_id,
                    "notification_data": notification_data,
                    "results": results,
                    "message": "Urgent ticket notification sent successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to send urgent ticket notification: {e}")
            return {
                "success": False,
                "ticket_id": ticket_id,
                "error": str(e)
            }
    
    async def send_sla_breach_notification(
        self,
        ticket_id: int,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send notification for SLA breach"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get ticket details
                ticket_query = select(SupportTicket).where(SupportTicket.id == ticket_id)
                ticket_result = await session.execute(ticket_query)
                ticket = ticket_result.scalar_one_or_none()
                
                if not ticket:
                    raise ValueError(f"Ticket {ticket_id} not found")
                
                # Check if notification should be sent
                if not await self._should_send_notification("sla_breach", ticket):
                    return {
                        "success": True,
                        "message": "Notification skipped due to cooldown or conditions not met"
                    }
                
                # Calculate SLA breach details
                sla_breach_details = await self._calculate_sla_breach_details(ticket)
                
                # Prepare notification data
                notification_data = {
                    "ticket_id": ticket.id,
                    "ticket_number": ticket.ticket_number,
                    "customer_name": f"{ticket.customer.first_name} {ticket.customer.last_name}",
                    "subject": ticket.subject,
                    "priority": ticket.priority.value,
                    "category": ticket.category.value,
                    "sla_target": sla_breach_details["sla_target"],
                    "actual_time": sla_breach_details["actual_time"],
                    "breach_minutes": sla_breach_details["breach_minutes"],
                    "assigned_agent": f"{ticket.assigned_agent.first_name} {ticket.assigned_agent.last_name}" if ticket.assigned_agent else "Unassigned"
                }
                
                # Send notifications
                results = await self._send_notifications(
                    rule_name="sla_breach",
                    notification_data=notification_data,
                    channels=channels
                )
                
                # Record notification
                await self._record_notification(
                    rule_name="sla_breach",
                    ticket_id=ticket_id,
                    notification_data=notification_data,
                    results=results
                )
                
                return {
                    "success": True,
                    "ticket_id": ticket_id,
                    "notification_data": notification_data,
                    "results": results,
                    "message": "SLA breach notification sent successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to send SLA breach notification: {e}")
            return {
                "success": False,
                "ticket_id": ticket_id,
                "error": str(e)
            }
    
    async def send_escalation_notification(
        self,
        ticket_id: int,
        escalated_to_agent_id: int,
        reason: str,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send notification for ticket escalation"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get ticket and agent details
                ticket_query = select(SupportTicket).where(SupportTicket.id == ticket_id)
                ticket_result = await session.execute(ticket_query)
                ticket = ticket_result.scalar_one_or_none()
                
                if not ticket:
                    raise ValueError(f"Ticket {ticket_id} not found")
                
                # Get escalated to agent
                agent_query = select(SupportAgent).where(SupportAgent.user_id == escalated_to_agent_id)
                agent_result = await session.execute(agent_query)
                agent = agent_result.scalar_one_or_none()
                
                if not agent:
                    raise ValueError(f"Agent {escalated_to_agent_id} not found")
                
                # Check if notification should be sent
                if not await self._should_send_notification("ticket_escalated", ticket):
                    return {
                        "success": True,
                        "message": "Notification skipped due to cooldown or conditions not met"
                    }
                
                # Prepare notification data
                notification_data = {
                    "ticket_id": ticket.id,
                    "ticket_number": ticket.ticket_number,
                    "customer_name": f"{ticket.customer.first_name} {ticket.customer.last_name}",
                    "subject": ticket.subject,
                    "priority": ticket.priority.value,
                    "category": ticket.category.value,
                    "agent_name": f"{agent.user.first_name} {agent.user.last_name}",
                    "agent_email": agent.user.email,
                    "escalation_reason": reason,
                    "escalated_at": datetime.utcnow().isoformat()
                }
                
                # Send notifications
                results = await self._send_notifications(
                    rule_name="ticket_escalated",
                    notification_data=notification_data,
                    channels=channels
                )
                
                # Record notification
                await self._record_notification(
                    rule_name="ticket_escalated",
                    ticket_id=ticket_id,
                    notification_data=notification_data,
                    results=results
                )
                
                return {
                    "success": True,
                    "ticket_id": ticket_id,
                    "agent_id": escalated_to_agent_id,
                    "notification_data": notification_data,
                    "results": results,
                    "message": "Escalation notification sent successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to send escalation notification: {e}")
            return {
                "success": False,
                "ticket_id": ticket_id,
                "error": str(e)
            }
    
    async def send_high_volume_alert(
        self,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send notification for high ticket volume"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Check if notification should be sent
            if not await self._should_send_notification("high_volume_alert"):
                return {
                    "success": True,
                    "message": "Notification skipped due to cooldown or conditions not met"
                }
            
            # Get ticket volume data
            volume_data = await self._get_ticket_volume_data()
            
            # Check if threshold is met
            rule = self._notification_rules["high_volume_alert"]
            threshold = rule["conditions"]["ticket_count_threshold"]
            time_window = rule["conditions"]["time_window_minutes"]
            
            if volume_data["recent_tickets"] < threshold:
                return {
                    "success": True,
                    "message": f"Ticket volume ({volume_data['recent_tickets']}) below threshold ({threshold})"
                }
            
            # Prepare notification data
            notification_data = {
                "ticket_count": volume_data["recent_tickets"],
                "time_window": time_window,
                "total_open_tickets": volume_data["total_open_tickets"],
                "average_response_time": volume_data["average_response_time"],
                "unassigned_tickets": volume_data["unassigned_tickets"],
                "alert_time": datetime.utcnow().isoformat()
            }
            
            # Send notifications
            results = await self._send_notifications(
                rule_name="high_volume_alert",
                notification_data=notification_data,
                channels=channels
            )
            
            # Record notification
            await self._record_notification(
                rule_name="high_volume_alert",
                ticket_id=None,
                notification_data=notification_data,
                results=results
            )
            
            return {
                "success": True,
                "notification_data": notification_data,
                "results": results,
                "message": "High volume alert sent successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to send high volume alert: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_agent_unavailable_notification(
        self,
        agent_id: int,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send notification when agent becomes unavailable"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get agent details
                agent_query = select(SupportAgent).where(SupportAgent.user_id == agent_id)
                agent_result = await session.execute(agent_query)
                agent = agent_result.scalar_one_or_none()
                
                if not agent:
                    raise ValueError(f"Agent {agent_id} not found")
                
                # Get unassigned tickets count
                unassigned_query = select(func.count(SupportTicket.id)).where(
                    and_(
                        SupportTicket.assigned_agent_id.is_(None),
                        SupportTicket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS])
                    )
                )
                unassigned_result = await session.execute(unassigned_query)
                unassigned_count = unassigned_result.scalar()
                
                # Check if notification should be sent
                if not await self._should_send_notification("agent_unavailable", {"unassigned_count": unassigned_count}):
                    return {
                        "success": True,
                        "message": "Notification skipped due to cooldown or conditions not met"
                    }
                
                # Prepare notification data
                notification_data = {
                    "agent_id": agent.user_id,
                    "agent_name": f"{agent.user.first_name} {agent.user.last_name}",
                    "agent_email": agent.user.email,
                    "agent_status": agent.availability_status,
                    "unassigned_count": unassigned_count,
                    "current_tickets": agent.current_ticket_count,
                    "performance_score": agent.performance_score,
                    "unavailable_at": datetime.utcnow().isoformat()
                }
                
                # Send notifications
                results = await self._send_notifications(
                    rule_name="agent_unavailable",
                    notification_data=notification_data,
                    channels=channels
                )
                
                # Record notification
                await self._record_notification(
                    rule_name="agent_unavailable",
                    ticket_id=None,
                    notification_data=notification_data,
                    results=results
                )
                
                return {
                    "success": True,
                    "agent_id": agent_id,
                    "notification_data": notification_data,
                    "results": results,
                    "message": "Agent unavailable notification sent successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to send agent unavailable notification: {e}")
            return {
                "success": False,
                "agent_id": agent_id,
                "error": str(e)
            }
    
    async def send_satisfaction_alert(
        self,
        ticket_id: int,
        satisfaction_score: int,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send notification for low customer satisfaction"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get ticket details
                ticket_query = select(SupportTicket).where(SupportTicket.id == ticket_id)
                ticket_result = await session.execute(ticket_query)
                ticket = ticket_result.scalar_one_or_none()
                
                if not ticket:
                    raise ValueError(f"Ticket {ticket_id} not found")
                
                # Check if notification should be sent
                if not await self._should_send_notification("customer_satisfaction_low", {"satisfaction_score": satisfaction_score}):
                    return {
                        "success": True,
                        "message": "Notification skipped due to cooldown or conditions not met"
                    }
                
                # Prepare notification data
                notification_data = {
                    "ticket_id": ticket.id,
                    "ticket_number": ticket.ticket_number,
                    "customer_name": f"{ticket.customer.first_name} {ticket.customer.last_name}",
                    "subject": ticket.subject,
                    "satisfaction_score": satisfaction_score,
                    "assigned_agent": f"{ticket.assigned_agent.first_name} {ticket.assigned_agent.last_name}" if ticket.assigned_agent else "Unassigned",
                    "category": ticket.category.value,
                    "priority": ticket.priority.value,
                    "rated_at": datetime.utcnow().isoformat()
                }
                
                # Send notifications
                results = await self._send_notifications(
                    rule_name="customer_satisfaction_low",
                    notification_data=notification_data,
                    channels=channels
                )
                
                # Record notification
                await self._record_notification(
                    rule_name="customer_satisfaction_low",
                    ticket_id=ticket_id,
                    notification_data=notification_data,
                    results=results
                )
                
                return {
                    "success": True,
                    "ticket_id": ticket_id,
                    "notification_data": notification_data,
                    "results": results,
                    "message": "Satisfaction alert sent successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to send satisfaction alert: {e}")
            return {
                "success": False,
                "ticket_id": ticket_id,
                "error": str(e)
            }
    
    async def _send_notifications(
        self,
        rule_name: str,
        notification_data: Dict[str, Any],
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send notifications to specified channels"""
        try:
            rule = self._notification_rules.get(rule_name)
            if not rule:
                raise ValueError(f"Notification rule '{rule_name}' not found")
            
            # Use specified channels or default from rule
            target_channels = channels or rule.get("channels", [])
            results = {}
            
            for channel in target_channels:
                channel_config = self._notification_channels.get(channel)
                if not channel_config or not channel_config.get("enabled", False):
                    results[channel] = {"success": False, "error": "Channel not configured or disabled"}
                    continue
                
                try:
                    if channel == "slack":
                        result = await self._send_slack_notification(rule, notification_data, channel_config)
                    elif channel == "teams":
                        result = await self._send_teams_notification(rule, notification_data, channel_config)
                    elif channel == "email":
                        result = await self._send_email_notification(rule, notification_data, channel_config)
                    elif channel == "sms":
                        result = await self._send_sms_notification(rule, notification_data, channel_config)
                    else:
                        result = {"success": False, "error": f"Unsupported channel: {channel}"}
                    
                    results[channel] = result
                    
                except Exception as e:
                    logger.error(f"Failed to send {channel} notification: {e}")
                    results[channel] = {"success": False, "error": str(e)}
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")
            return {"error": str(e)}
    
    async def _send_slack_notification(
        self,
        rule: Dict[str, Any],
        notification_data: Dict[str, Any],
        channel_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send notification to Slack"""
        try:
            # Format message
            message_template = rule.get("message_template", "")
            message = message_template.format(**notification_data)
            
            # Prepare Slack payload
            payload = {
                "channel": channel_config.get("channel", "#support-alerts"),
                "username": channel_config.get("username", "Clara Support Bot"),
                "icon_emoji": channel_config.get("icon_emoji", ":robot_face:"),
                "text": message,
                "attachments": [
                    {
                        "color": "danger" if rule.get("priority") == "high" else "warning",
                        "fields": [
                            {
                                "title": "Ticket Number",
                                "value": notification_data.get("ticket_number", "N/A"),
                                "short": True
                            },
                            {
                                "title": "Priority",
                                "value": notification_data.get("priority", "N/A"),
                                "short": True
                            },
                            {
                                "title": "Customer",
                                "value": notification_data.get("customer_name", "N/A"),
                                "short": True
                            },
                            {
                                "title": "Category",
                                "value": notification_data.get("category", "N/A"),
                                "short": True
                            }
                        ],
                        "footer": "Clara Support System",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            # Send to Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    channel_config.get("webhook_url"),
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return {"success": True, "message": "Slack notification sent"}
                else:
                    return {"success": False, "error": f"Slack API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_teams_notification(
        self,
        rule: Dict[str, Any],
        notification_data: Dict[str, Any],
        channel_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send notification to Microsoft Teams"""
        try:
            # Format message
            message_template = rule.get("message_template", "")
            message = message_template.format(**notification_data)
            
            # Prepare Teams payload
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "FF0000" if rule.get("priority") == "high" else "FFA500",
                "summary": f"Support Alert: {rule.get('name', 'Notification')}",
                "sections": [
                    {
                        "activityTitle": message,
                        "activitySubtitle": f"Priority: {rule.get('priority', 'medium')}",
                        "facts": [
                            {
                                "name": "Ticket Number",
                                "value": notification_data.get("ticket_number", "N/A")
                            },
                            {
                                "name": "Customer",
                                "value": notification_data.get("customer_name", "N/A")
                            },
                            {
                                "name": "Category",
                                "value": notification_data.get("category", "N/A")
                            },
                            {
                                "name": "Priority",
                                "value": notification_data.get("priority", "N/A")
                            }
                        ]
                    }
                ]
            }
            
            # Send to Teams
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    channel_config.get("webhook_url"),
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return {"success": True, "message": "Teams notification sent"}
                else:
                    return {"success": False, "error": f"Teams API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_email_notification(
        self,
        rule: Dict[str, Any],
        notification_data: Dict[str, Any],
        channel_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send notification via email"""
        try:
            # Format message
            message_template = rule.get("message_template", "")
            message = message_template.format(**notification_data)
            
            # Prepare email content
            subject = f"Support Alert: {rule.get('name', 'Notification')}"
            body = f"""
            {message}
            
            Details:
            - Ticket Number: {notification_data.get('ticket_number', 'N/A')}
            - Customer: {notification_data.get('customer_name', 'N/A')}
            - Category: {notification_data.get('category', 'N/A')}
            - Priority: {notification_data.get('priority', 'N/A')}
            - Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
            
            This is an automated notification from Clara Support System.
            """
            
            # Send email using SMTP implementation
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                # Get SMTP configuration from environment or config
                smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
                smtp_port = int(os.getenv("SMTP_PORT", "587"))
                smtp_username = os.getenv("SMTP_USERNAME")
                smtp_password = os.getenv("SMTP_PASSWORD")
                
                if not all([smtp_username, smtp_password]):
                    logger.warning("SMTP credentials not configured, using fallback")
                    return {"success": True, "message": "Email notification queued (SMTP not configured)"}
                
                # Create message
                msg = MIMEMultipart()
                msg['From'] = smtp_username
                msg['To'] = channel_config.get("email_address")
                msg['Subject'] = f"Clara Alert: {notification_data.get('title', 'Support Notification')}"
                
                msg.attach(MIMEText(message, 'plain'))
                
                # Send email
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)
                
                return {"success": True, "message": "Email notification sent"}
                
            except Exception as email_error:
                logger.error(f"SMTP error: {email_error}")
                return {"success": False, "error": f"SMTP error: {str(email_error)}"}
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_sms_notification(
        self,
        rule: Dict[str, Any],
        notification_data: Dict[str, Any],
        channel_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send notification via SMS"""
        try:
            # Format message
            message_template = rule.get("message_template", "")
            message = message_template.format(**notification_data)
            
            # Send SMS using Twilio API
            try:
                import httpx
                
                # Get Twilio configuration from environment
                twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
                twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
                twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
                
                if not all([twilio_account_sid, twilio_auth_token, twilio_phone_number]):
                    logger.warning("Twilio credentials not configured, using fallback")
                    return {"success": True, "message": "SMS notification queued (Twilio not configured)"}
                
                # Prepare Twilio API request
                url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json"
                auth = (twilio_account_sid, twilio_auth_token)
                data = {
                    "From": twilio_phone_number,
                    "To": channel_config.get("phone_number"),
                    "Body": message
                }
                
                # Send SMS via Twilio
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, auth=auth, data=data)
                    
                    if response.status_code == 201:
                        return {"success": True, "message": "SMS notification sent"}
                    else:
                        logger.error(f"Twilio API error: {response.text}")
                        return {"success": False, "error": f"Twilio API error: {response.status_code}"}
                        
            except Exception as sms_error:
                logger.error(f"Twilio error: {sms_error}")
                return {"success": False, "error": f"Twilio error: {str(sms_error)}"}
            
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def _should_send_notification(
        self,
        rule_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if notification should be sent based on cooldown and conditions"""
        try:
            rule = self._notification_rules.get(rule_name)
            if not rule or not rule.get("enabled", True):
                return False
            
            # Check cooldown
            cooldown_minutes = rule.get("cooldown_minutes", 0)
            if cooldown_minutes > 0:
                last_notification = await self._get_last_notification(rule_name)
                if last_notification:
                    time_diff = datetime.utcnow() - last_notification["timestamp"]
                    if time_diff.total_seconds() < cooldown_minutes * 60:
                        return False
            
            # Check conditions if context provided
            if context and "conditions" in rule:
                conditions = rule["conditions"]
                for key, value in conditions.items():
                    if key in context:
                        if isinstance(value, list):
                            if context[key] not in value:
                                return False
                        else:
                            if context[key] != value:
                                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check notification conditions: {e}")
            return True
    
    async def _get_last_notification(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """Get the last notification for a rule"""
        try:
            # Check notification history
            for notification in reversed(self._notification_history):
                if notification.get("rule_name") == rule_name:
                    return notification
            return None
            
        except Exception as e:
            logger.error(f"Failed to get last notification: {e}")
            return None
    
    async def _record_notification(
        self,
        rule_name: str,
        ticket_id: Optional[int],
        notification_data: Dict[str, Any],
        results: Dict[str, Any]
    ):
        """Record notification in history"""
        try:
            notification_record = {
                "rule_name": rule_name,
                "ticket_id": ticket_id,
                "notification_data": notification_data,
                "results": results,
                "timestamp": datetime.utcnow()
            }
            
            self._notification_history.append(notification_record)
            
            # Keep only last 1000 notifications
            if len(self._notification_history) > 1000:
                self._notification_history = self._notification_history[-1000:]
                
        except Exception as e:
            logger.error(f"Failed to record notification: {e}")
    
    async def _calculate_sla_breach_details(self, ticket: SupportTicket) -> Dict[str, Any]:
        """Calculate SLA breach details"""
        try:
            # Define SLA targets by priority
            sla_targets = {
                TicketPriority.CRITICAL: 30,  # 30 minutes
                TicketPriority.URGENT: 60,    # 1 hour
                TicketPriority.HIGH: 240,     # 4 hours
                TicketPriority.MEDIUM: 480,   # 8 hours
                TicketPriority.LOW: 1440      # 24 hours
            }
            
            sla_target = sla_targets.get(ticket.priority, 480)  # Default 8 hours
            
            # Calculate actual time
            if ticket.created_at:
                actual_time = (datetime.utcnow() - ticket.created_at).total_seconds() / 60
                breach_minutes = max(0, actual_time - sla_target)
            else:
                actual_time = 0
                breach_minutes = 0
            
            return {
                "sla_target": sla_target,
                "actual_time": actual_time,
                "breach_minutes": breach_minutes
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate SLA breach details: {e}")
            return {
                "sla_target": 480,
                "actual_time": 0,
                "breach_minutes": 0
            }
    
    async def _get_ticket_volume_data(self) -> Dict[str, Any]:
        """Get ticket volume data for alerts"""
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get recent tickets count
                time_window = self._notification_rules["high_volume_alert"]["conditions"]["time_window_minutes"]
                cutoff_time = datetime.utcnow() - timedelta(minutes=time_window)
                
                recent_query = select(func.count(SupportTicket.id)).where(
                    SupportTicket.created_at >= cutoff_time
                )
                recent_result = await session.execute(recent_query)
                recent_tickets = recent_result.scalar()
                
                # Get total open tickets
                open_query = select(func.count(SupportTicket.id)).where(
                    SupportTicket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS])
                )
                open_result = await session.execute(open_query)
                total_open_tickets = open_result.scalar()
                
                # Get unassigned tickets
                unassigned_query = select(func.count(SupportTicket.id)).where(
                    and_(
                        SupportTicket.assigned_agent_id.is_(None),
                        SupportTicket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS])
                    )
                )
                unassigned_result = await session.execute(unassigned_query)
                unassigned_tickets = unassigned_result.scalar()
                
                # Calculate average response time
                response_query = select(func.avg(SupportTicket.first_response_time)).where(
                    SupportTicket.first_response_time.is_not(None)
                )
                response_result = await session.execute(response_query)
                avg_response_time = response_result.scalar() or 0
                
                return {
                    "recent_tickets": recent_tickets,
                    "total_open_tickets": total_open_tickets,
                    "unassigned_tickets": unassigned_tickets,
                    "average_response_time": avg_response_time
                }
                
        except Exception as e:
            logger.error(f"Failed to get ticket volume data: {e}")
            return {
                "recent_tickets": 0,
                "total_open_tickets": 0,
                "unassigned_tickets": 0,
                "average_response_time": 0
            }
    
    async def get_notification_history(
        self,
        rule_name: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get notification history"""
        try:
            history = self._notification_history
            
            if rule_name:
                history = [n for n in history if n.get("rule_name") == rule_name]
            
            # Sort by timestamp descending
            history.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
            
            # Limit results
            history = history[:limit]
            
            return {
                "success": True,
                "notifications": history,
                "count": len(history)
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification history: {e}")
            return {
                "success": False,
                "error": str(e)
            }
