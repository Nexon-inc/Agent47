from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..services.sales_outreach_service import SalesOutreachService
from ..database import get_db

router = APIRouter(prefix="/sales-outreach", tags=["Sales Outreach"])
sales_outreach_service = SalesOutreachService()

class EmailOutreachRequest(BaseModel):
    lead_id: int
    email_template: str
    personalization_data: Dict[str, Any]
    sender_config: Dict[str, Any]

class SMSOutreachRequest(BaseModel):
    lead_id: int
    sms_template: str
    personalization_data: Dict[str, Any]
    sender_config: Dict[str, Any]

class LinkedInOutreachRequest(BaseModel):
    lead_id: int
    message_template: str
    personalization_data: Dict[str, Any]
    sender_config: Dict[str, Any]

class FollowUpSequenceRequest(BaseModel):
    lead_id: int
    sequence_config: Dict[str, Any]

class OutreachAnalyticsRequest(BaseModel):
    brand_id: int
    date_range: str = "30d"

@router.post("/send-email")
async def send_personalized_email(request: EmailOutreachRequest):
    """Send personalized email to lead"""
    try:
        result = await sales_outreach_service.send_personalized_email(
            lead_id=request.lead_id,
            email_template=request.email_template,
            personalization_data=request.personalization_data,
            sender_config=request.sender_config
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send personalized email: {str(e)}")

@router.post("/send-sms")
async def send_sms_outreach(request: SMSOutreachRequest):
    """Send SMS outreach to lead"""
    try:
        result = await sales_outreach_service.send_sms_outreach(
            lead_id=request.lead_id,
            sms_template=request.sms_template,
            personalization_data=request.personalization_data,
            sender_config=request.sender_config
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send SMS outreach: {str(e)}")

@router.post("/send-linkedin")
async def send_linkedin_message(request: LinkedInOutreachRequest):
    """Send LinkedIn message to lead"""
    try:
        result = await sales_outreach_service.send_linkedin_message(
            lead_id=request.lead_id,
            message_template=request.message_template,
            personalization_data=request.personalization_data,
            sender_config=request.sender_config
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send LinkedIn message: {str(e)}")

@router.post("/create-follow-up-sequence")
async def create_follow_up_sequence(request: FollowUpSequenceRequest):
    """Create automated follow-up sequence for lead"""
    try:
        result = await sales_outreach_service.create_follow_up_sequence(
            lead_id=request.lead_id,
            sequence_config=request.sequence_config
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create follow-up sequence: {str(e)}")

@router.post("/analytics")
async def get_outreach_analytics(request: OutreachAnalyticsRequest):
    """Get outreach analytics and performance metrics"""
    try:
        result = await sales_outreach_service.get_outreach_analytics(
            brand_id=request.brand_id,
            date_range=request.date_range
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get outreach analytics: {str(e)}")

@router.get("/templates")
async def get_outreach_templates():
    """Get available outreach templates"""
    return {
        "email_templates": [
            {
                "id": "cold_outreach",
                "name": "Cold Outreach",
                "subject": "Quick question about {company}",
                "description": "Professional cold outreach template"
            },
            {
                "id": "follow_up",
                "name": "Follow Up",
                "subject": "Following up on our conversation",
                "description": "Gentle follow-up template"
            },
            {
                "id": "value_proposition",
                "name": "Value Proposition",
                "subject": "How we help {industry} companies",
                "description": "Value-focused outreach template"
            }
        ],
        "sms_templates": [
            {
                "id": "quick_touch",
                "name": "Quick Touch",
                "message": "Hi {first_name}, quick question about {company} - do you have 2 minutes?",
                "description": "Short and direct SMS template"
            },
            {
                "id": "meeting_reminder",
                "name": "Meeting Reminder",
                "message": "Hi {first_name}, looking forward to our call tomorrow at {time}",
                "description": "Meeting reminder template"
            }
        ],
        "linkedin_templates": [
            {
                "id": "connection_request",
                "name": "Connection Request",
                "message": "Hi {first_name}, I noticed we both work in {industry}. Would love to connect!",
                "description": "Professional connection request"
            },
            {
                "id": "value_share",
                "name": "Value Share",
                "message": "Hi {first_name}, I came across this article and thought of {company}. Hope it's helpful!",
                "description": "Value-sharing template"
            }
        ]
    }

@router.get("/health")
async def health_check():
    """Health check for sales outreach service"""
    return {
        "status": "healthy",
        "service": "sales_outreach",
        "timestamp": datetime.now().isoformat()
    }
