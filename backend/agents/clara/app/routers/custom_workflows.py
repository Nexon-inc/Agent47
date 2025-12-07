from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
from ..services.custom_workflows_service import CustomWorkflowsService
from ..models import SupportChannel, TicketPriority, TicketStatus, TicketCategory

router = APIRouter()

# Pydantic models for request/response
class CreateWorkflowRequest(BaseModel):
    name: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    steps: List[Dict[str, Any]]
    auto_assign: bool = False
    auto_assign_agent_id: Optional[int] = None
    sla_target: Optional[int] = None
    escalation_rules: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, Any]] = None
    is_active: bool = True

class UpdateWorkflowRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    steps: Optional[List[Dict[str, Any]]] = None
    auto_assign: Optional[bool] = None
    auto_assign_agent_id: Optional[int] = None
    sla_target: Optional[int] = None
    escalation_rules: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ExecuteWorkflowRequest(BaseModel):
    context: Optional[Dict[str, Any]] = None

async def get_workflows_service() -> CustomWorkflowsService:
    """Dependency to get custom workflows service"""
    service = CustomWorkflowsService()
    await service.initialize()
    return service

@router.post("/workflows", response_model=Dict[str, Any])
async def create_workflow(
    request: CreateWorkflowRequest,
    created_by: Optional[int] = Query(None),
    workflows_service: CustomWorkflowsService = Depends(get_workflows_service)
):
    """Create a new custom workflow"""
    try:
        result = await workflows_service.create_workflow(
            name=request.name,
            description=request.description,
            category=request.category,
            priority=request.priority,
            steps=request.steps,
            auto_assign=request.auto_assign,
            auto_assign_agent_id=request.auto_assign_agent_id,
            sla_target=request.sla_target,
            escalation_rules=request.escalation_rules,
            conditions=request.conditions,
            is_active=request.is_active,
            created_by=created_by
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow(
    workflow_id: int,
    include_inactive: bool = Query(False),
    workflows_service: CustomWorkflowsService = Depends(get_workflows_service)
):
    """Get a specific workflow by ID"""
    try:
        result = await workflows_service.get_workflow(
            workflow_id=workflow_id,
            include_inactive=include_inactive
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows", response_model=Dict[str, Any])
async def search_workflows(
    category: Optional[TicketCategory] = Query(None),
    priority: Optional[TicketPriority] = Query(None),
    is_active: Optional[bool] = Query(None),
    search_term: Optional[str] = Query(None),
    workflows_service: CustomWorkflowsService = Depends(get_workflows_service)
):
    """Search workflows with filters"""
    try:
        result = await workflows_service.search_workflows(
            category=category,
            priority=priority,
            is_active=is_active,
            search_term=search_term
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def update_workflow(
    workflow_id: int,
    request: UpdateWorkflowRequest,
    workflows_service: CustomWorkflowsService = Depends(get_workflows_service)
):
    """Update an existing workflow"""
    try:
        updates = request.dict(exclude_unset=True)
        
        result = await workflows_service.update_workflow(
            workflow_id=workflow_id,
            updates=updates
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def delete_workflow(
    workflow_id: int,
    workflows_service: CustomWorkflowsService = Depends(get_workflows_service)
):
    """Delete a workflow"""
    try:
        result = await workflows_service.delete_workflow(workflow_id=workflow_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/{workflow_id}/execute/{ticket_id}", response_model=Dict[str, Any])
async def execute_workflow(
    workflow_id: int,
    ticket_id: int,
    request: ExecuteWorkflowRequest,
    workflows_service: CustomWorkflowsService = Depends(get_workflows_service)
):
    """Execute a workflow for a specific ticket"""
    try:
        result = await workflows_service.execute_workflow(
            workflow_id=workflow_id,
            ticket_id=ticket_id,
            context=request.context
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/matching/{ticket_id}", response_model=Dict[str, Any])
async def get_matching_workflows(
    ticket_id: int,
    context: Optional[str] = Query(None, description="Optional JSON-encoded context"),
    workflows_service: CustomWorkflowsService = Depends(get_workflows_service)
):
    """Get workflows that match a ticket's criteria

    The `context` query parameter must be a JSON-encoded string (e.g. `?context={"key": "value"}`).
    FastAPI does not allow complex types like Dict in Query parameters, so we accept a string and
    parse it here.
    """
    try:
        parsed_context: Optional[Dict[str, Any]] = None
        if context:
            import json
            try:
                parsed_context = json.loads(context)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid JSON for 'context' query parameter")

        result = await workflows_service.get_matching_workflows(
            ticket_id=ticket_id,
            context=parsed_context
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions", response_model=Dict[str, Any])
async def get_workflow_execution_history(
    workflow_id: Optional[int] = Query(None),
    ticket_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    workflows_service: CustomWorkflowsService = Depends(get_workflows_service)
):
    """Get workflow execution history"""
    try:
        result = await workflows_service.get_workflow_execution_history(
            workflow_id=workflow_id,
            ticket_id=ticket_id,
            limit=limit
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/step-types", response_model=Dict[str, Any])
async def get_available_step_types():
    """Get available workflow step types"""
    try:
        step_types = [
            {
                "type": "assign_agent",
                "name": "Assign Agent",
                "description": "Assign ticket to a specific agent or find agent by criteria",
                "parameters": ["agent_id", "agent_criteria"]
            },
            {
                "type": "update_status",
                "name": "Update Status",
                "description": "Update ticket status",
                "parameters": ["status"]
            },
            {
                "type": "update_priority",
                "name": "Update Priority",
                "description": "Update ticket priority",
                "parameters": ["priority"]
            },
            {
                "type": "add_tag",
                "name": "Add Tag",
                "description": "Add tags to ticket",
                "parameters": ["tags"]
            },
            {
                "type": "send_notification",
                "name": "Send Notification",
                "description": "Send notification via various channels",
                "parameters": ["notification_type", "channels"]
            },
            {
                "type": "create_follow_up",
                "name": "Create Follow-up",
                "description": "Create a follow-up ticket",
                "parameters": ["follow_up_days"]
            },
            {
                "type": "escalate_ticket",
                "name": "Escalate Ticket",
                "description": "Escalate ticket to another agent or team",
                "parameters": ["reason", "escalated_to_agent_id"]
            },
            {
                "type": "update_sla",
                "name": "Update SLA",
                "description": "Update ticket SLA target",
                "parameters": ["sla_minutes"]
            },
            {
                "type": "add_note",
                "name": "Add Note",
                "description": "Add internal note to ticket",
                "parameters": ["note", "author"]
            },
            {
                "type": "trigger_webhook",
                "name": "Trigger Webhook",
                "description": "Trigger external webhook",
                "parameters": ["webhook_url", "data"]
            },
            {
                "type": "send_email",
                "name": "Send Email",
                "description": "Send email notification",
                "parameters": ["template_id", "email_content", "recipients"]
            }
        ]
        
        return {
            "success": True,
            "step_types": step_types,
            "count": len(step_types)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=Dict[str, Any])
async def check_workflows_health(
    workflows_service: CustomWorkflowsService = Depends(get_workflows_service)
):
    """Check health status of workflows service"""
    try:
        return {
            "success": True,
            "service": "custom_workflows",
            "status": "healthy",
            "workflows_count": len(workflows_service._workflow_cache),
            "execution_history_count": len(workflows_service._workflow_execution_history),
            "message": "Custom workflows service is operational"
        }
    except Exception as e:
        return {
            "success": False,
            "service": "custom_workflows",
            "status": "error",
            "error": str(e)
        }
