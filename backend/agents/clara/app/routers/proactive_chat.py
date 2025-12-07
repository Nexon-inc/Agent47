from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ..services.proactive_chat_service import ProactiveChatService

router = APIRouter()

# Pydantic models for request/response
class BehaviorAnalysisRequest(BaseModel):
    customer_id: int
    analysis_period_days: int = 30

class ProactiveChatInitiationRequest(BaseModel):
    customer_id: int
    trigger_type: str
    custom_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ProactiveChatDecisionRequest(BaseModel):
    customer_id: int
    trigger_type: Optional[str] = None

class ProactiveChatInsightsRequest(BaseModel):
    customer_id: int
    period_days: int = 30

# Dependency
async def get_proactive_chat_service() -> ProactiveChatService:
    service = ProactiveChatService()
    await service.initialize()
    return service

@router.post("/behavior/analyze", response_model=Dict[str, Any])
async def analyze_customer_behavior(
    request: BehaviorAnalysisRequest,
    service: ProactiveChatService = Depends(get_proactive_chat_service)
):
    """Analyze customer behavior for proactive engagement opportunities"""
    try:
        result = await service.analyze_customer_behavior(
            customer_id=request.customer_id,
            analysis_period_days=request.analysis_period_days
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/should-initiate", response_model=Dict[str, Any])
async def should_initiate_proactive_chat(
    request: ProactiveChatDecisionRequest,
    service: ProactiveChatService = Depends(get_proactive_chat_service)
):
    """Determine if proactive chat should be initiated"""
    try:
        result = await service.should_initiate_proactive_chat(
            customer_id=request.customer_id,
            trigger_type=request.trigger_type
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/initiate", response_model=Dict[str, Any])
async def initiate_proactive_chat(
    request: ProactiveChatInitiationRequest,
    service: ProactiveChatService = Depends(get_proactive_chat_service)
):
    """Initiate a proactive chat session"""
    try:
        result = await service.initiate_proactive_chat(
            customer_id=request.customer_id,
            trigger_type=request.trigger_type,
            custom_message=request.custom_message,
            metadata=request.metadata
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/insights/customer", response_model=Dict[str, Any])
async def get_proactive_chat_insights(
    request: ProactiveChatInsightsRequest,
    service: ProactiveChatService = Depends(get_proactive_chat_service)
):
    """Get insights about proactive chat effectiveness"""
    try:
        result = await service.get_proactive_chat_insights(
            customer_id=request.customer_id,
            period_days=request.period_days
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/triggers/available", response_model=Dict[str, Any])
async def get_available_proactive_triggers(
    service: ProactiveChatService = Depends(get_proactive_chat_service)
):
    """Get list of available proactive chat triggers"""
    try:
        triggers = {
            "success": True,
            "available_triggers": [
                {
                    "type": "inactive_customer",
                    "description": "Customer has been inactive for extended period",
                    "priority": "medium",
                    "recommended_message": "We noticed you haven't been around lately. Is there anything we can help you with?"
                },
                {
                    "type": "declining_satisfaction",
                    "description": "Customer satisfaction is declining",
                    "priority": "high",
                    "recommended_message": "We want to ensure you're having a great experience. How can we improve our service?"
                },
                {
                    "type": "technical_difficulties",
                    "description": "Customer experiencing frequent technical issues",
                    "priority": "high",
                    "recommended_message": "We see you've had some technical challenges. Let us help you get everything working smoothly!"
                },
                {
                    "type": "urgent_support_needs",
                    "description": "Customer has urgent support needs",
                    "priority": "critical",
                    "recommended_message": "We understand you need immediate assistance. Let's get this resolved right away!"
                },
                {
                    "type": "new_customer_onboarding",
                    "description": "New customer who might need onboarding help",
                    "priority": "medium",
                    "recommended_message": "Welcome! We're here to help you get started. Do you have any questions?"
                },
                {
                    "type": "premium_customer_engagement",
                    "description": "Premium customer with low engagement",
                    "priority": "medium",
                    "recommended_message": "As a premium customer, we want to ensure you're getting the most value. How can we help?"
                }
            ],
            "trigger_categories": {
                "high_priority": ["declining_satisfaction", "technical_difficulties", "urgent_support_needs"],
                "medium_priority": ["inactive_customer", "new_customer_onboarding", "premium_customer_engagement"],
                "low_priority": []
            }
        }
        
        return triggers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_proactive_chat_overview(
    service: ProactiveChatService = Depends(get_proactive_chat_service)
):
    """Get overview of proactive chat system"""
    try:
        overview = {
            "success": True,
            "proactive_chat_overview": {
                "system_status": "active",
                "total_customers_monitored": 0,
                "active_triggers": 0,
                "proactive_chats_initiated": 0,
                "engagement_rate": 0.0,
                "average_response_time": 0,
                "top_trigger_types": [],
                "performance_metrics": {
                    "daily_initiations": 0,
                    "weekly_initiations": 0,
                    "monthly_initiations": 0,
                    "success_rate": 0.0
                }
            },
            "last_updated": "2024-01-01T00:00:00Z"
        }
        
        return overview
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/settings", response_model=Dict[str, Any])
async def get_proactive_chat_configuration(
    service: ProactiveChatService = Depends(get_proactive_chat_service)
):
    """Get proactive chat configuration settings"""
    try:
        config = {
            "success": True,
            "proactive_chat_config": {
                "enabled": True,
                "max_daily_initiations_per_customer": 3,
                "minimum_interval_between_contacts": 24,  # hours
                "business_hours_only": False,
                "timezone": "UTC",
                "auto_escalation_threshold": 3,  # failed attempts
                "smart_timing": True,
                "personalization_enabled": True,
                "a_b_testing_enabled": False,
                "compliance_features": {
                    "gdpr_compliant": True,
                    "opt_out_respected": True,
                    "frequency_capping": True
                }
            }
        }
        
        return config
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
