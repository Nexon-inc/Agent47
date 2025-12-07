from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class MultiTicketResolutionRequest(BaseModel):
    ticket_ids: List[int]
    strategy: Optional[str] = "sequential"

class MultiTicketResolutionResponse(BaseModel):
    resolved_ticket_ids: List[int]
    failed_ticket_ids: List[int]


class CreateTicketGroupRequest(BaseModel):
    name: str
    description: Optional[str] = None
    ticket_ids: List[int]
    category: Optional[str] = None
    priority: Optional[str] = None
    assigned_agent_id: Optional[int] = None


class UpdateTicketGroupRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ticket_ids: Optional[List[int]] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    assigned_agent_id: Optional[int] = None


class CreateResolutionTemplateRequest(BaseModel):
    name: str
    content: str


class UpdateResolutionTemplateRequest(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None


class BulkActionRequest(BaseModel):
    action_type: str
    payload: Dict[str, Any]


class TicketGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    ticket_ids: List[int]
    category: Optional[str] = None
    priority: Optional[str] = None
    assigned_agent_id: Optional[int] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ResolutionTemplateResponse(BaseModel):
    id: int
    name: str
    content: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BulkActionResponse(BaseModel):
    id: int
    action_type: str
    status: str
    result: Optional[Dict[str, Any]] = None


class TicketClusterResponse(BaseModel):
    id: int
    ticket_ids: List[int]
    centroid: Optional[List[float]] = None


class ResolutionBatchResponse(BaseModel):
    id: int
    batch_size: int
    resolved_count: int
    failed_count: int
    created_at: Optional[datetime] = None
