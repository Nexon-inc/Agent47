from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..services.deal_closing_assistance_service import (
    DealClosingAssistanceService,
    DealClosingRequest,
    DealClosingStrategyRequest,
    DealClosingTemplateRequest,
    DealClosingActivityRequest
)

router = APIRouter(prefix="/deal-closing", tags=["Deal Closing Assistance"])
deal_closing_service = DealClosingAssistanceService()

# Request models
class DealAnalysisRequest(BaseModel):
    deal_id: str
    brand_id: str

class ProposalGenerationRequest(BaseModel):
    deal_id: str
    brand_id: str
    proposal_type: str = "standard"

class ClosingSequenceRequest(BaseModel):
    deal_id: str
    brand_id: str
    sequence_type: str = "standard"

class ObjectionHandlingRequest(BaseModel):
    deal_id: str
    brand_id: str
    objection_type: str
    objection_details: str

class ClosingActivityRequest(BaseModel):
    deal_id: str
    brand_id: str
    activity_type: str
    activity_data: Dict[str, Any]

class ProgressTrackingRequest(BaseModel):
    deal_id: str
    brand_id: str

class DealFinalizationRequest(BaseModel):
    deal_id: str
    brand_id: str
    closing_method: str
    closing_terms: Dict[str, Any]

# Response models
class DealAnalysisResponse(BaseModel):
    deal_id: str
    analysis: Dict[str, Any]
    strategy: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    recommended_actions: List[Dict[str, Any]]

class ProposalResponse(BaseModel):
    deal_id: str
    proposal_type: str
    generated_at: datetime
    valid_until: datetime
    content: Dict[str, Any]
    pricing: List[Dict[str, Any]]
    terms: Dict[str, Any]
    next_steps: List[Dict[str, Any]]

class ClosingSequenceResponse(BaseModel):
    deal_id: str
    sequence_type: str
    created_at: datetime
    status: str
    steps: List[Dict[str, Any]]
    scheduled_activities: List[Dict[str, Any]]
    expected_completion: datetime

class ObjectionResponse(BaseModel):
    deal_id: str
    objection_type: str
    objection_analysis: Dict[str, Any]
    response_strategy: Dict[str, Any]
    response: str
    next_actions: List[Dict[str, Any]]

class ActivityExecutionResponse(BaseModel):
    deal_id: str
    activity_type: str
    execution_result: Dict[str, Any]
    timestamp: datetime
    next_recommended_action: Dict[str, Any]

class ProgressReportResponse(BaseModel):
    deal_id: str
    current_stage: str
    progress_percentage: int
    time_elapsed: str
    time_remaining: str
    activities_completed: int
    activities_pending: int
    milestones: List[str]
    bottlenecks: List[str]
    recommendations: List[Dict[str, Any]]

class DealFinalizationResponse(BaseModel):
    deal_id: str
    closing_method: str
    closing_status: str
    closing_result: Dict[str, Any]
    closed_at: datetime
    post_closing_activities: List[Dict[str, Any]]

@router.post("/analyze", response_model=DealAnalysisResponse)
async def analyze_deal_for_closing(request: DealAnalysisRequest):
    """Analyze a deal to determine optimal closing strategy"""
    try:
        result = await deal_closing_service.analyze_deal_for_closing(
            deal_id=request.deal_id,
            brand_id=request.brand_id
        )
        return DealAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze deal: {str(e)}")

@router.post("/generate-proposal", response_model=ProposalResponse)
async def generate_closing_proposal(request: ProposalGenerationRequest):
    """Generate a personalized closing proposal"""
    try:
        result = await deal_closing_service.generate_closing_proposal(
            deal_id=request.deal_id,
            brand_id=request.brand_id,
            proposal_type=request.proposal_type
        )
        return ProposalResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate proposal: {str(e)}")

@router.post("/create-sequence", response_model=ClosingSequenceResponse)
async def create_closing_sequence(request: ClosingSequenceRequest):
    """Create an automated closing sequence"""
    try:
        result = await deal_closing_service.create_closing_sequence(
            deal_id=request.deal_id,
            brand_id=request.brand_id,
            sequence_type=request.sequence_type
        )
        return ClosingSequenceResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create closing sequence: {str(e)}")

@router.post("/handle-objections", response_model=ObjectionResponse)
async def handle_objections_and_concerns(request: ObjectionHandlingRequest):
    """Handle customer objections and concerns during closing"""
    try:
        result = await deal_closing_service.handle_objections_and_concerns(
            deal_id=request.deal_id,
            brand_id=request.brand_id,
            objection_type=request.objection_type,
            objection_details=request.objection_details
        )
        return ObjectionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to handle objections: {str(e)}")

@router.post("/execute-activity", response_model=ActivityExecutionResponse)
async def execute_closing_activities(request: ClosingActivityRequest):
    """Execute specific closing activities"""
    try:
        result = await deal_closing_service.execute_closing_activities(
            deal_id=request.deal_id,
            brand_id=request.brand_id,
            activity_type=request.activity_type,
            activity_data=request.activity_data
        )
        return ActivityExecutionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute closing activity: {str(e)}")

@router.post("/track-progress", response_model=ProgressReportResponse)
async def track_closing_progress(request: ProgressTrackingRequest):
    """Track the progress of deal closing activities"""
    try:
        result = await deal_closing_service.track_closing_progress(
            deal_id=request.deal_id,
            brand_id=request.brand_id
        )
        return ProgressReportResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track closing progress: {str(e)}")

@router.post("/finalize", response_model=DealFinalizationResponse)
async def finalize_deal(request: DealFinalizationRequest):
    """Finalize a deal with specified closing method and terms"""
    try:
        result = await deal_closing_service.finalize_deal(
            deal_id=request.deal_id,
            brand_id=request.brand_id,
            closing_method=request.closing_method,
            closing_terms=request.closing_terms
        )
        return DealFinalizationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to finalize deal: {str(e)}")

@router.get("/strategies/{brand_id}")
async def get_closing_strategies(brand_id: str):
    """Get available closing strategies for a brand"""
    try:
        # This would typically fetch from database
        strategies = [
            {
                "strategy_id": "consultative",
                "name": "Consultative Closing",
                "description": "Build trust through understanding and education",
                "best_for": ["Complex solutions", "Long sales cycles", "High-value deals"],
                "success_rate": 0.85
            },
            {
                "strategy_id": "assumptive",
                "name": "Assumptive Closing",
                "description": "Assume the sale and focus on details",
                "best_for": ["Simple products", "Short sales cycles", "Qualified leads"],
                "success_rate": 0.78
            },
            {
                "strategy_id": "urgency",
                "name": "Urgency Closing",
                "description": "Create urgency through limited time offers",
                "best_for": ["Seasonal products", "Limited inventory", "Price-sensitive customers"],
                "success_rate": 0.72
            }
        ]
        return {"brand_id": brand_id, "strategies": strategies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get closing strategies: {str(e)}")

@router.get("/templates/{brand_id}")
async def get_closing_templates(brand_id: str):
    """Get available closing templates for a brand"""
    try:
        templates = [
            {
                "template_id": "proposal_standard",
                "name": "Standard Proposal Template",
                "type": "proposal",
                "description": "Professional proposal template for standard deals",
                "content_sections": ["Executive Summary", "Solution Overview", "Pricing", "Timeline"]
            },
            {
                "template_id": "contract_standard",
                "name": "Standard Contract Template",
                "type": "contract",
                "description": "Standard contract template with common terms",
                "content_sections": ["Terms and Conditions", "Payment Terms", "Delivery Timeline", "Warranty"]
            },
            {
                "template_id": "follow_up_sequence",
                "name": "Follow-up Sequence Template",
                "type": "sequence",
                "description": "Automated follow-up sequence for deal closing",
                "content_sections": ["Initial Follow-up", "Value Reinforcement", "Final Push"]
            }
        ]
        return {"brand_id": brand_id, "templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get closing templates: {str(e)}")

@router.get("/activities/{deal_id}")
async def get_deal_activities(deal_id: str):
    """Get all activities for a specific deal"""
    try:
        # This would typically fetch from database
        activities = [
            {
                "activity_id": "act_001",
                "deal_id": deal_id,
                "activity_type": "proposal_sent",
                "timestamp": "2024-01-15T10:00:00Z",
                "status": "completed",
                "details": "Proposal sent to customer"
            },
            {
                "activity_id": "act_002",
                "deal_id": deal_id,
                "activity_type": "follow_up_call",
                "timestamp": "2024-01-17T14:30:00Z",
                "status": "scheduled",
                "details": "Follow-up call scheduled for next week"
            }
        ]
        return {"deal_id": deal_id, "activities": activities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deal activities: {str(e)}")

@router.get("/metrics/{brand_id}")
async def get_closing_metrics(brand_id: str):
    """Get closing performance metrics for a brand"""
    try:
        metrics = {
            "brand_id": brand_id,
            "overall_metrics": {
                "total_deals": 150,
                "closed_deals": 89,
                "closing_rate": 0.59,
                "average_closing_time": "18 days",
                "average_deal_value": 75000
            },
            "performance_by_strategy": {
                "consultative": {"success_rate": 0.85, "avg_time": "22 days"},
                "assumptive": {"success_rate": 0.78, "avg_time": "12 days"},
                "urgency": {"success_rate": 0.72, "avg_time": "8 days"}
            },
            "bottlenecks": [
                {"issue": "Customer review time", "frequency": 0.45},
                {"issue": "Legal approval", "frequency": 0.32},
                {"issue": "Budget approval", "frequency": 0.28}
            ]
        }
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get closing metrics: {str(e)}")

@router.post("/validate-terms")
async def validate_closing_terms(terms: Dict[str, Any]):
    """Validate closing terms before finalization"""
    try:
        # This would typically validate against business rules
        validation_result = {
            "is_valid": True,
            "issues": [],
            "recommendations": [
                "Consider adding payment terms",
                "Include delivery timeline"
            ]
        }
        return validation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate terms: {str(e)}")

@router.get("/objection-types")
async def get_objection_types():
    """Get common objection types and handling strategies"""
    try:
        objection_types = [
            {
                "type": "price",
                "name": "Price Concerns",
                "description": "Customer concerned about cost",
                "common_responses": [
                    "Focus on ROI and value",
                    "Offer payment plans",
                    "Compare with alternatives"
                ]
            },
            {
                "type": "timeline",
                "name": "Timeline Concerns",
                "description": "Customer concerned about implementation time",
                "common_responses": [
                    "Show implementation roadmap",
                    "Offer phased approach",
                    "Highlight quick wins"
                ]
            },
            {
                "type": "competition",
                "name": "Competition Comparison",
                "description": "Customer comparing with competitors",
                "common_responses": [
                    "Highlight unique value propositions",
                    "Show competitive advantages",
                    "Provide case studies"
                ]
            }
        ]
        return {"objection_types": objection_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get objection types: {str(e)}")
