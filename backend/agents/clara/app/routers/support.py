from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..services.support_service import SupportService
from ..models import TicketPriority, TicketStatus, TicketCategory, SupportChannel
from ..database import get_clara_database

router = APIRouter()

# Pydantic models for request/response
class CreateTicketRequest(BaseModel):
    customer_id: int
    channel: SupportChannel
    category: TicketCategory
    subject: str
    description: str
    priority: Optional[TicketPriority] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    source_url: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class UpdateTicketStatusRequest(BaseModel):
    status: TicketStatus
    notes: Optional[str] = None
    resolution_time: Optional[int] = None

class AssignTicketRequest(BaseModel):
    agent_id: int
    reason: Optional[str] = None

class EscalateTicketRequest(BaseModel):
    escalated_to_agent_id: int
    reason: str
    priority_increase: bool = False
    sla_extension: Optional[int] = None

class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    customer_id: int
    assigned_agent_id: Optional[int]
    channel: str
    priority: str
    status: str
    category: str
    subject: str
    description: str
    sentiment_score: float
    satisfaction_score: Optional[int]
    tags: List[str]
    created_at: str
    updated_at: str

# Dependency
async def get_support_service() -> SupportService:
    service = SupportService()
    await service.initialize()
    return service

@router.post("/tickets", response_model=Dict[str, Any])
async def create_ticket(
    request: CreateTicketRequest,
    service: SupportService = Depends(get_support_service)
):
    """Create a new support ticket"""
    try:
        result = await service.create_ticket(
            customer_id=request.customer_id,
            channel=request.channel,
            category=request.category,
            subject=request.subject,
            description=request.description,
            priority=request.priority,
            tags=request.tags,
            metadata=request.metadata,
            source_url=request.source_url,
            ip_address=request.ip_address,
            user_agent=request.user_agent
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/{ticket_id}", response_model=Dict[str, Any])
async def get_ticket(
    ticket_id: int,
    service: SupportService = Depends(get_support_service)
):
    """Get detailed ticket information"""
    try:
        result = await service.get_ticket_details(ticket_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tickets/{ticket_id}/status", response_model=Dict[str, Any])
async def update_ticket_status(
    ticket_id: int,
    request: UpdateTicketStatusRequest,
    agent_id: int = Query(..., description="ID of the agent updating the status"),
    service: SupportService = Depends(get_support_service)
):
    """Update ticket status"""
    try:
        result = await service.update_ticket_status(
            ticket_id=ticket_id,
            status=request.status,
            agent_id=agent_id,
            notes=request.notes,
            resolution_time=request.resolution_time
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tickets/{ticket_id}/assign", response_model=Dict[str, Any])
async def assign_ticket(
    ticket_id: int,
    request: AssignTicketRequest,
    service: SupportService = Depends(get_support_service)
):
    """Assign ticket to an agent"""
    try:
        result = await service.assign_ticket(
            ticket_id=ticket_id,
            agent_id=request.agent_id,
            reason=request.reason
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tickets/{ticket_id}/escalate", response_model=Dict[str, Any])
async def escalate_ticket(
    ticket_id: int,
    request: EscalateTicketRequest,
    escalated_from_agent_id: int = Query(..., description="ID of the agent escalating the ticket"),
    service: SupportService = Depends(get_support_service)
):
    """Escalate ticket to another agent"""
    try:
        result = await service.escalate_ticket(
            ticket_id=ticket_id,
            escalated_from_agent_id=escalated_from_agent_id,
            escalated_to_agent_id=request.escalated_to_agent_id,
            reason=request.reason,
            priority_increase=request.priority_increase,
            sla_extension=request.sla_extension
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets", response_model=Dict[str, Any])
async def search_tickets(
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    agent_id: Optional[int] = Query(None, description="Filter by assigned agent ID"),
    status: Optional[TicketStatus] = Query(None, description="Filter by ticket status"),
    priority: Optional[TicketPriority] = Query(None, description="Filter by ticket priority"),
    category: Optional[TicketCategory] = Query(None, description="Filter by ticket category"),
    channel: Optional[SupportChannel] = Query(None, description="Filter by support channel"),
    limit: int = Query(50, ge=1, le=100, description="Number of tickets to return"),
    offset: int = Query(0, ge=0, description="Number of tickets to skip"),
    service: SupportService = Depends(get_support_service)
):
    """Search tickets with filters"""
    try:
        result = await service.search_tickets(
            customer_id=customer_id,
            agent_id=agent_id,
            status=status,
            priority=priority,
            category=category,
            channel=channel,
            limit=limit,
            offset=offset
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/customer/{customer_id}", response_model=Dict[str, Any])
async def get_customer_tickets(
    customer_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: SupportService = Depends(get_support_service)
):
    """Get all tickets for a specific customer"""
    try:
        result = await service.search_tickets(
            customer_id=customer_id,
            limit=limit,
            offset=offset
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/agent/{agent_id}", response_model=Dict[str, Any])
async def get_agent_tickets(
    agent_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: SupportService = Depends(get_support_service)
):
    """Get all tickets assigned to a specific agent"""
    try:
        result = await service.search_tickets(
            agent_id=agent_id,
            limit=limit,
            offset=offset
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/stats/summary", response_model=Dict[str, Any])
async def get_tickets_summary(
    service: SupportService = Depends(get_support_service)
):
    """Get summary statistics for tickets"""
    try:
        # Get statistics from analytics service
        return {
            "success": True,
            "summary": {
                "total_tickets": 0,
                "open_tickets": 0,
                "resolved_tickets": 0,
                "escalated_tickets": 0,
                "average_response_time": 0,
                "average_resolution_time": 0,
                "customer_satisfaction_avg": 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/priority/{priority}", response_model=Dict[str, Any])
async def get_tickets_by_priority(
    priority: TicketPriority,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: SupportService = Depends(get_support_service)
):
    """Get tickets by priority level"""
    try:
        result = await service.search_tickets(
            priority=priority,
            limit=limit,
            offset=offset
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/category/{category}", response_model=Dict[str, Any])
async def get_tickets_by_category(
    category: TicketCategory,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: SupportService = Depends(get_support_service)
):
    """Get tickets by category"""
    try:
        result = await service.search_tickets(
            category=category,
            limit=limit,
            offset=offset
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/channel/{channel}", response_model=Dict[str, Any])
async def get_tickets_by_channel(
    channel: SupportChannel,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: SupportService = Depends(get_support_service)
):
    """Get tickets by support channel"""
    try:
        result = await service.search_tickets(
            channel=channel,
            limit=limit,
            offset=offset
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
