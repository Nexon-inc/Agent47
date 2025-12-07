from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..services.email_marketing_service import EmailMarketingService
from ..database import get_jackie_database

router = APIRouter()

class CreateEmailCampaignRequest(BaseModel):
    user_id: int
    campaign_name: str
    subject_line: str
    email_content: str
    recipient_list: List[str]
    sender_email: str
    sender_name: str
    scheduled_time: Optional[str] = None

class EmailTemplateRequest(BaseModel):
    user_id: int
    template_name: str
    subject_line: str
    email_content: str
    template_type: str

async def get_email_marketing_service() -> EmailMarketingService:
    service = EmailMarketingService()
    await service.initialize()
    return service

@router.post("/campaigns/create", response_model=Dict[str, Any])
async def create_email_campaign(
    request: CreateEmailCampaignRequest,
    service: EmailMarketingService = Depends(get_email_marketing_service)
):
    try:
        result = await service.create_email_campaign(
            user_id=request.user_id,
            campaign_name=request.campaign_name,
            subject_line=request.subject_line,
            email_content=request.email_content,
            recipient_list=request.recipient_list,
            sender_email=request.sender_email,
            sender_name=request.sender_name,
            scheduled_time=request.scheduled_time
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates/create", response_model=Dict[str, Any])
async def create_email_template(
    request: EmailTemplateRequest,
    service: EmailMarketingService = Depends(get_email_marketing_service)
):
    try:
        result = await service.create_email_template(
            user_id=request.user_id,
            template_name=request.template_name,
            subject_line=request.subject_line,
            email_content=request.email_content,
            template_type=request.template_type
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/{campaign_id}/analytics", response_model=Dict[str, Any])
async def get_email_analytics(
    campaign_id: int,
    service: EmailMarketingService = Depends(get_email_marketing_service)
):
    try:
        result = await service.get_email_analytics(campaign_id)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/campaigns/{campaign_id}/send", response_model=Dict[str, Any])
async def send_email_campaign(
    campaign_id: int,
    service: EmailMarketingService = Depends(get_email_marketing_service)
):
    try:
        result = await service.send_email_campaign(campaign_id)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates", response_model=Dict[str, Any])
async def get_email_templates(
    user_id: int = Query(...),
    service: EmailMarketingService = Depends(get_email_marketing_service)
):
    try:
        result = await service.get_email_templates(user_id)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/automation/create", response_model=Dict[str, Any])
async def create_email_automation(
    user_id: int = Body(...),
    automation_name: str = Body(...),
    trigger_conditions: Dict[str, Any] = Body(...),
    email_template_id: int = Body(...),
    service: EmailMarketingService = Depends(get_email_marketing_service)
):
    try:
        result = await service.create_email_automation(
            user_id=user_id,
            automation_name=automation_name,
            trigger_conditions=trigger_conditions,
            email_template_id=email_template_id
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
