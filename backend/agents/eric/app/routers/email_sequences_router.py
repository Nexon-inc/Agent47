from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..services.email_sequences_service import EmailSequencesService

router = APIRouter(prefix="/email-sequences", tags=["Email Sequences"])
email_sequences_service = EmailSequencesService()

# Request models
class EmailSequenceRequest(BaseModel):
    brand_id: str
    sequence_data: Dict[str, Any]

class FollowUpWorkflowRequest(BaseModel):
    brand_id: str
    workflow_data: Dict[str, Any]

class EmailSendRequest(BaseModel):
    sequence_id: str
    lead_id: str
    send_data: Dict[str, Any]

class EmailPerformanceRequest(BaseModel):
    sequence_id: str
    time_period: str = "30d"

class EmailTimingRequest(BaseModel):
    brand_id: str
    lead_data: Dict[str, Any]

class DynamicSequenceRequest(BaseModel):
    brand_id: str
    dynamic_rules: Dict[str, Any]

# Response models
class EmailSequenceResponse(BaseModel):
    sequence_id: str
    brand_id: str
    sequence_name: str
    sequence_type: str
    sequence_steps: List[Dict[str, Any]]
    automation_triggers: List[Dict[str, Any]]
    status: str
    created_at: datetime

class FollowUpWorkflowResponse(BaseModel):
    workflow_id: str
    brand_id: str
    workflow_name: str
    workflow_type: str
    workflow_rules: List[Dict[str, Any]]
    automation_config: Dict[str, Any]
    status: str
    created_at: datetime

class EmailSendResponse(BaseModel):
    scheduled_email_id: str
    sequence_id: str
    lead_id: str
    personalized_content: Dict[str, Any]
    scheduled_time: datetime
    status: str
    created_at: datetime

class EmailPerformanceResponse(BaseModel):
    sequence_id: str
    time_period: str
    email_metrics: Dict[str, Any]
    performance_analysis: Dict[str, Any]
    insights: List[str]
    recommendations: List[Dict[str, Any]]

class EmailTimingResponse(BaseModel):
    brand_id: str
    lead_id: Optional[str]
    behavior_patterns: Dict[str, Any]
    optimal_timing: List[str]
    timing_recommendations: List[Dict[str, Any]]

class DynamicSequenceResponse(BaseModel):
    dynamic_sequence_id: str
    brand_id: str
    dynamic_rules: Dict[str, Any]
    dynamic_sequence: List[Dict[str, Any]]
    conditional_logic: Dict[str, Any]
    status: str
    created_at: datetime

@router.post("/create-sequence", response_model=EmailSequenceResponse)
async def create_email_sequence(request: EmailSequenceRequest):
    """Create a new email sequence"""
    try:
        result = await email_sequences_service.create_email_sequence(
            brand_id=request.brand_id,
            sequence_data=request.sequence_data
        )
        return EmailSequenceResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create email sequence: {str(e)}")

@router.post("/manage-workflows", response_model=FollowUpWorkflowResponse)
async def manage_follow_up_workflows(request: FollowUpWorkflowRequest):
    """Manage follow-up workflows"""
    try:
        result = await email_sequences_service.manage_follow_up_workflows(
            brand_id=request.brand_id,
            workflow_data=request.workflow_data
        )
        return FollowUpWorkflowResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to manage follow-up workflows: {str(e)}")

@router.post("/schedule-email", response_model=EmailSendResponse)
async def schedule_email_send(request: EmailSendRequest):
    """Schedule an email to be sent"""
    try:
        result = await email_sequences_service.schedule_email_send(
            sequence_id=request.sequence_id,
            lead_id=request.lead_id,
            send_data=request.send_data
        )
        return EmailSendResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule email send: {str(e)}")

@router.post("/track-performance", response_model=EmailPerformanceResponse)
async def track_email_performance(request: EmailPerformanceRequest):
    """Track email sequence performance"""
    try:
        result = await email_sequences_service.track_email_performance(
            sequence_id=request.sequence_id,
            time_period=request.time_period
        )
        return EmailPerformanceResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track email performance: {str(e)}")

@router.post("/optimize-timing", response_model=EmailTimingResponse)
async def optimize_email_timing(request: EmailTimingRequest):
    """Optimize email send timing based on lead behavior"""
    try:
        result = await email_sequences_service.optimize_email_timing(
            brand_id=request.brand_id,
            lead_data=request.lead_data
        )
        return EmailTimingResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to optimize email timing: {str(e)}")

@router.post("/create-dynamic-sequence", response_model=DynamicSequenceResponse)
async def create_dynamic_sequences(request: DynamicSequenceRequest):
    """Create dynamic email sequences based on lead behavior"""
    try:
        result = await email_sequences_service.create_dynamic_sequences(
            brand_id=request.brand_id,
            dynamic_rules=request.dynamic_rules
        )
        return DynamicSequenceResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dynamic sequence: {str(e)}")

@router.get("/sequences/{brand_id}")
async def get_email_sequences(brand_id: str):
    """Get all email sequences for a brand"""
    try:
        sequences = [
            {
                "sequence_id": "seq_001",
                "sequence_name": "Welcome Sequence",
                "sequence_type": "welcome",
                "status": "active",
                "created_at": "2024-01-15T10:00:00Z"
            },
            {
                "sequence_id": "seq_002",
                "sequence_name": "Nurture Sequence",
                "sequence_type": "nurture",
                "status": "active",
                "created_at": "2024-01-14T15:30:00Z"
            }
        ]
        return {"brand_id": brand_id, "sequences": sequences}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get email sequences: {str(e)}")

@router.get("/workflows/{brand_id}")
async def get_follow_up_workflows(brand_id: str):
    """Get all follow-up workflows for a brand"""
    try:
        workflows = [
            {
                "workflow_id": "wf_001",
                "workflow_name": "EricLead Follow-up",
                "workflow_type": "lead_nurture",
                "status": "active",
                "created_at": "2024-01-15T10:00:00Z"
            },
            {
                "workflow_id": "wf_002",
                "workflow_name": "Customer Onboarding",
                "workflow_type": "onboarding",
                "status": "active",
                "created_at": "2024-01-14T15:30:00Z"
            }
        ]
        return {"brand_id": brand_id, "workflows": workflows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get follow-up workflows: {str(e)}")

@router.get("/templates/{brand_id}")
async def get_email_templates(brand_id: str):
    """Get email templates for a brand"""
    try:
        templates = [
            {
                "template_id": "welcome_email",
                "template_name": "Welcome Email",
                "template_type": "welcome",
                "subject": "Welcome to our platform!",
                "status": "active"
            },
            {
                "template_id": "value_proposition",
                "template_name": "Value Proposition",
                "template_type": "value_prop",
                "subject": "How we can help you succeed",
                "status": "active"
            },
            {
                "template_id": "call_to_action",
                "template_name": "Call to Action",
                "template_type": "cta",
                "subject": "Ready to get started?",
                "status": "active"
            }
        ]
        return {"brand_id": brand_id, "templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get email templates: {str(e)}")

@router.get("/analytics/{sequence_id}")
async def get_sequence_analytics(sequence_id: str, time_period: str = "30d"):
    """Get detailed analytics for a specific sequence"""
    try:
        analytics = {
            "sequence_id": sequence_id,
            "time_period": time_period,
            "metrics": {
                "total_sent": 1000,
                "total_opened": 450,
                "total_clicked": 120,
                "total_replied": 25,
                "open_rate": 0.45,
                "click_rate": 0.12,
                "reply_rate": 0.025,
                "unsubscribe_rate": 0.02
            },
            "step_performance": [
                {
                    "step": 1,
                    "sent": 1000,
                    "opened": 450,
                    "clicked": 120,
                    "replied": 25
                },
                {
                    "step": 2,
                    "sent": 975,
                    "opened": 400,
                    "clicked": 100,
                    "replied": 20
                }
            ],
            "insights": [
                "Step 1 has the highest engagement rate",
                "Reply rate decreases in subsequent steps",
                "Consider optimizing step 2 content"
            ]
        }
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sequence analytics: {str(e)}")

@router.get("/automation-triggers/{brand_id}")
async def get_automation_triggers(brand_id: str):
    """Get automation triggers for a brand"""
    try:
        triggers = [
            {
                "trigger_id": "trigger_001",
                "trigger_type": "lead_created",
                "conditions": ["new_lead", "qualified_lead"],
                "action": "start_sequence",
                "sequence_template": "welcome_sequence",
                "status": "active"
            },
            {
                "trigger_id": "trigger_002",
                "trigger_type": "lead_activity",
                "conditions": ["website_visit", "email_open"],
                "action": "continue_sequence",
                "sequence_template": "nurture_sequence",
                "status": "active"
            }
        ]
        return {"brand_id": brand_id, "triggers": triggers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get automation triggers: {str(e)}")

@router.get("/timing-insights/{brand_id}")
async def get_timing_insights(brand_id: str):
    """Get email timing insights for a brand"""
    try:
        insights = {
            "brand_id": brand_id,
            "optimal_send_times": [
                {"day": "Tuesday", "time": "9am", "open_rate": 0.52},
                {"day": "Wednesday", "time": "2pm", "open_rate": 0.48},
                {"day": "Thursday", "time": "6pm", "open_rate": 0.45}
            ],
            "avoid_times": [
                {"day": "Monday", "time": "9am", "reason": "Low engagement"},
                {"day": "Friday", "time": "5pm", "reason": "Weekend approaching"}
            ],
            "timezone_insights": [
                {"timezone": "EST", "optimal_time": "9am EST"},
                {"timezone": "PST", "optimal_time": "9am PST"}
            ]
        }
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timing insights: {str(e)}")

@router.get("/personalization-data/{lead_id}")
async def get_personalization_data(lead_id: str):
    """Get personalization data for a lead"""
    try:
        personalization_data = {
            "lead_id": lead_id,
            "lead_name": "John Doe",
            "company_name": "TechCorp",
            "industry": "Technology",
            "job_title": "CTO",
            "location": "San Francisco",
            "preferences": {
                "communication_style": "formal",
                "preferred_channels": ["email", "linkedin"],
                "timezone": "PST"
            },
            "behavior_data": {
                "website_visits": 5,
                "email_opens": 3,
                "last_activity": "2024-01-15T10:00:00Z"
            }
        }
        return personalization_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get personalization data: {str(e)}")

@router.get("/sequence-templates")
async def get_sequence_templates():
    """Get available sequence templates"""
    try:
        templates = [
            {
                "template_id": "welcome_sequence",
                "template_name": "Welcome Sequence",
                "description": "Onboard new leads with value proposition",
                "steps": 3,
                "estimated_duration": "7 days"
            },
            {
                "template_id": "nurture_sequence",
                "template_name": "EricLead Nurture Sequence",
                "description": "Nurture leads with educational content",
                "steps": 5,
                "estimated_duration": "14 days"
            },
            {
                "template_id": "re_engagement_sequence",
                "template_name": "Re-engagement Sequence",
                "description": "Re-engage inactive leads",
                "steps": 4,
                "estimated_duration": "10 days"
            }
        ]
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sequence templates: {str(e)}")

@router.get("/automation-rules/{brand_id}")
async def get_automation_rules(brand_id: str):
    """Get automation rules for a brand"""
    try:
        rules = [
            {
                "rule_id": "rule_001",
                "rule_name": "No Response After 3 Days",
                "condition": "no_response_after_3_days",
                "action": "send_follow_up_email",
                "template": "follow_up_template_1",
                "status": "active"
            },
            {
                "rule_id": "rule_002",
                "rule_name": "Email Opened But No Click",
                "condition": "email_opened_but_no_click",
                "action": "send_alternative_offer",
                "template": "alternative_offer_template",
                "status": "active"
            },
            {
                "rule_id": "rule_003",
                "rule_name": "EricLead Unsubscribed",
                "condition": "lead_unsubscribed",
                "action": "pause_sequence",
                "template": None,
                "status": "active"
            }
        ]
        return {"brand_id": brand_id, "rules": rules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get automation rules: {str(e)}")
