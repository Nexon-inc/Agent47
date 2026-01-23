from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json

from ..database import get_db
from ..services.multi_ticket_resolution_service import MultiTicketResolutionService
from ..models import ClaraTicketGroup, ClaraBulkAction, ClaraResolutionTemplate, ClaraTicketCluster, ClaraResolutionBatch
from ..core.integration_manager import IntegrationManager
from ..core.event_bus import EventBus

router = APIRouter()

# Pydantic models for request/response
class CreateTicketGroupRequest(BaseModel):
    group_name: str = Field(..., description="Group name")
    group_type: str = Field(..., description="Group type (similar_issues, bulk_resolution, escalation)")
    ticket_ids: List[int] = Field(..., description="List of ticket IDs to group")
    criteria: Dict[str, Any] = Field(..., description="Grouping criteria")
    priority: str = Field("medium", description="Group priority")
    assigned_agent: Optional[str] = Field(None, description="Assigned agent ID")

class UpdateTicketGroupRequest(BaseModel):
    group_name: Optional[str] = Field(None, description="Group name")
    group_type: Optional[str] = Field(None, description="Group type")
    priority: Optional[str] = Field(None, description="Group priority")
    assigned_agent: Optional[str] = Field(None, description="Assigned agent ID")
    status: Optional[str] = Field(None, description="Group status")

class CreateResolutionTemplateRequest(BaseModel):
    template_name: str = Field(..., description="Template name")
    template_type: str = Field(..., description="Template type (bulk_response, escalation, resolution)")
    content: str = Field(..., description="Template content")
    variables: List[str] = Field([], description="Template variables")
    applicable_issues: List[str] = Field(..., description="Applicable issue types")
    is_active: bool = Field(True, description="Template active status")

class UpdateResolutionTemplateRequest(BaseModel):
    template_name: Optional[str] = Field(None, description="Template name")
    template_type: Optional[str] = Field(None, description="Template type")
    content: Optional[str] = Field(None, description="Template content")
    variables: Optional[List[str]] = Field(None, description="Template variables")
    applicable_issues: Optional[List[str]] = Field(None, description="Applicable issue types")
    is_active: Optional[bool] = Field(None, description="Template active status")

class BulkActionRequest(BaseModel):
    action_type: str = Field(..., description="Action type (update_status, assign_agent, send_response, escalate)")
    ticket_ids: List[int] = Field(..., description="List of ticket IDs")
    action_data: Dict[str, Any] = Field(..., description="Action data")
    template_id: Optional[int] = Field(None, description="Template ID to use")
    execute_immediately: bool = Field(False, description="Execute immediately or schedule")

class TicketGroupResponse(BaseModel):
    id: int
    group_name: str
    group_type: str
    ticket_count: int
    criteria: Dict[str, Any]
    priority: str
    status: str
    assigned_agent: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ResolutionTemplateResponse(BaseModel):
    id: int
    template_name: str
    template_type: str
    content: str
    variables: List[str]
    applicable_issues: List[str]
    is_active: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BulkActionResponse(BaseModel):
    id: int
    action_type: str
    ticket_count: int
    action_data: Dict[str, Any]
    status: str
    completed_count: int
    failed_count: int
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class TicketClusterResponse(BaseModel):
    id: int
    cluster_name: str
    similarity_score: float
    ticket_ids: List[int]
    common_issues: List[str]
    suggested_resolution: str
    created_at: datetime

    class Config:
        from_attributes = True

class ResolutionBatchResponse(BaseModel):
    id: int
    batch_name: str
    batch_type: str
    ticket_count: int
    resolution_template_id: int
    status: str
    progress: float
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

# Dependency
async def get_multi_ticket_resolution_service(db: AsyncSession = Depends(get_db)) -> MultiTicketResolutionService:
    integration_manager = IntegrationManager()
    event_bus = EventBus()
    return MultiTicketResolutionService(db, integration_manager, event_bus)

# Ticket Group Management
@router.post("/groups", response_model=TicketGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket_group(
    request: CreateTicketGroupRequest,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Create a new ticket group"""
    try:
        group = await service.create_ticket_group(
            group_name=request.group_name,
            group_type=request.group_type,
            ticket_ids=request.ticket_ids,
            criteria=request.criteria,
            priority=request.priority,
            assigned_agent=request.assigned_agent
        )
        return TicketGroupResponse.from_orm(group)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/groups", response_model=List[TicketGroupResponse])
async def get_ticket_groups(
    group_type: Optional[str] = None,
    status: Optional[str] = None,
    assigned_agent: Optional[str] = None,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Get ticket groups with optional filtering"""
    try:
        groups = await service.get_ticket_groups(
            group_type=group_type,
            status=status,
            assigned_agent=assigned_agent
        )
        return [TicketGroupResponse.from_orm(group) for group in groups]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/groups/{group_id}", response_model=TicketGroupResponse)
async def get_ticket_group(
    group_id: int,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Get a specific ticket group by ID"""
    try:
        group = await service.get_ticket_group(group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket group not found")
        return TicketGroupResponse.from_orm(group)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/groups/{group_id}", response_model=TicketGroupResponse)
async def update_ticket_group(
    group_id: int,
    request: UpdateTicketGroupRequest,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Update a ticket group"""
    try:
        group = await service.update_ticket_group(
            group_id=group_id,
            group_name=request.group_name,
            group_type=request.group_type,
            priority=request.priority,
            assigned_agent=request.assigned_agent,
            status=request.status
        )
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket group not found")
        return TicketGroupResponse.from_orm(group)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket_group(
    group_id: int,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Delete a ticket group"""
    try:
        success = await service.delete_ticket_group(group_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket group not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Resolution Template Management
@router.post("/templates", response_model=ResolutionTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_resolution_template(
    request: CreateResolutionTemplateRequest,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Create a new resolution template"""
    try:
        template = await service.create_resolution_template(
            template_name=request.template_name,
            template_type=request.template_type,
            content=request.content,
            variables=request.variables,
            applicable_issues=request.applicable_issues,
            is_active=request.is_active
        )
        return ResolutionTemplateResponse.from_orm(template)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/templates", response_model=List[ResolutionTemplateResponse])
async def get_resolution_templates(
    template_type: Optional[str] = None,
    applicable_issue: Optional[str] = None,
    active_only: bool = True,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Get resolution templates with optional filtering"""
    try:
        templates = await service.get_resolution_templates(
            template_type=template_type,
            applicable_issue=applicable_issue,
            active_only=active_only
        )
        return [ResolutionTemplateResponse.from_orm(template) for template in templates]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/templates/{template_id}", response_model=ResolutionTemplateResponse)
async def get_resolution_template(
    template_id: int,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Get a specific resolution template by ID"""
    try:
        template = await service.get_resolution_template(template_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resolution template not found")
        return ResolutionTemplateResponse.from_orm(template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/templates/{template_id}", response_model=ResolutionTemplateResponse)
async def update_resolution_template(
    template_id: int,
    request: UpdateResolutionTemplateRequest,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Update a resolution template"""
    try:
        template = await service.update_resolution_template(
            template_id=template_id,
            template_name=request.template_name,
            template_type=request.template_type,
            content=request.content,
            variables=request.variables,
            applicable_issues=request.applicable_issues,
            is_active=request.is_active
        )
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resolution template not found")
        return ResolutionTemplateResponse.from_orm(template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resolution_template(
    template_id: int,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Delete a resolution template"""
    try:
        success = await service.delete_resolution_template(template_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resolution template not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Bulk Actions
@router.post("/bulk-actions", response_model=BulkActionResponse, status_code=status.HTTP_201_CREATED)
async def execute_bulk_action(
    request: BulkActionRequest,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Execute a bulk action on multiple tickets"""
    try:
        action = await service.execute_bulk_action(
            action_type=request.action_type,
            ticket_ids=request.ticket_ids,
            action_data=request.action_data,
            template_id=request.template_id,
            execute_immediately=request.execute_immediately
        )
        return BulkActionResponse.from_orm(action)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/bulk-actions", response_model=List[BulkActionResponse])
async def get_bulk_actions(
    action_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Get bulk actions with optional filtering"""
    try:
        actions = await service.get_bulk_actions(
            action_type=action_type,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        return [BulkActionResponse.from_orm(action) for action in actions]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/bulk-actions/{action_id}", response_model=BulkActionResponse)
async def get_bulk_action(
    action_id: int,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Get a specific bulk action by ID"""
    try:
        action = await service.get_bulk_action(action_id)
        if not action:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bulk action not found")
        return BulkActionResponse.from_orm(action)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Ticket Clustering and Similarity
@router.post("/cluster-tickets")
async def cluster_similar_tickets(
    similarity_threshold: float = 0.8,
    max_cluster_size: int = 50,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Cluster similar tickets together"""
    try:
        clusters = await service.cluster_similar_tickets(
            similarity_threshold=similarity_threshold,
            max_cluster_size=max_cluster_size
        )
        return clusters
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/clusters", response_model=List[TicketClusterResponse])
async def get_ticket_clusters(
    min_similarity: float = 0.5,
    min_cluster_size: int = 2,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Get ticket clusters"""
    try:
        clusters = await service.get_ticket_clusters(
            min_similarity=min_similarity,
            min_cluster_size=min_cluster_size
        )
        return [TicketClusterResponse.from_orm(cluster) for cluster in clusters]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/clusters/{cluster_id}", response_model=TicketClusterResponse)
async def get_ticket_cluster(
    cluster_id: int,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Get a specific ticket cluster by ID"""
    try:
        cluster = await service.get_ticket_cluster(cluster_id)
        if not cluster:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket cluster not found")
        return TicketClusterResponse.from_orm(cluster)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Resolution Batches
@router.post("/resolution-batches", response_model=ResolutionBatchResponse, status_code=status.HTTP_201_CREATED)
async def create_resolution_batch(
    batch_name: str,
    ticket_ids: List[int],
    template_id: int,
    batch_type: str = "bulk_resolution",
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Create a resolution batch for multiple tickets"""
    try:
        batch = await service.create_resolution_batch(
            batch_name=batch_name,
            ticket_ids=ticket_ids,
            template_id=template_id,
            batch_type=batch_type
        )
        return ResolutionBatchResponse.from_orm(batch)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/resolution-batches", response_model=List[ResolutionBatchResponse])
async def get_resolution_batches(
    batch_type: Optional[str] = None,
    status: Optional[str] = None,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Get resolution batches with optional filtering"""
    try:
        batches = await service.get_resolution_batches(
            batch_type=batch_type,
            status=status
        )
        return [ResolutionBatchResponse.from_orm(batch) for batch in batches]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/resolution-batches/{batch_id}", response_model=ResolutionBatchResponse)
async def get_resolution_batch(
    batch_id: int,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Get a specific resolution batch by ID"""
    try:
        batch = await service.get_resolution_batch(batch_id)
        if not batch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resolution batch not found")
        return ResolutionBatchResponse.from_orm(batch)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/resolution-batches/{batch_id}/execute")
async def execute_resolution_batch(
    batch_id: int,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Execute a resolution batch"""
    try:
        result = await service.execute_resolution_batch(batch_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Smart Grouping and Recommendations
@router.post("/smart-grouping")
async def suggest_smart_groups(
    ticket_ids: List[int],
    grouping_criteria: Optional[Dict[str, Any]] = None,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Suggest smart groupings for tickets"""
    try:
        suggestions = await service.suggest_smart_groups(
            ticket_ids=ticket_ids,
            grouping_criteria=grouping_criteria
        )
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/recommend-resolutions")
async def recommend_resolutions(
    ticket_ids: List[int],
    include_templates: bool = True,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Recommend resolutions for multiple tickets"""
    try:
        recommendations = await service.recommend_resolutions(
            ticket_ids=ticket_ids,
            include_templates=include_templates
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Efficiency Analytics
@router.get("/analytics/efficiency")
async def get_resolution_efficiency(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    agent_id: Optional[str] = None,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Get resolution efficiency analytics"""
    try:
        efficiency_metrics = await service.get_resolution_efficiency(
            start_date=start_date,
            end_date=end_date,
            agent_id=agent_id
        )
        return efficiency_metrics
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/analytics/bulk-actions")
async def get_bulk_action_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    action_type: Optional[str] = None,
    service: MultiTicketResolutionService = Depends(get_multi_ticket_resolution_service)
):
    """Get bulk action analytics"""
    try:
        analytics = await service.get_bulk_action_analytics(
            start_date=start_date,
            end_date=end_date,
            action_type=action_type
        )
        return analytics
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Health Check
@router.get("/health")
async def health_check():
    """Health check endpoint for Multi-Ticket Resolution"""
    return {
        "status": "healthy",
        "service": "Multi-Ticket Resolution",
        "features": [
            "ticket_group_management",
            "resolution_template_management",
            "bulk_actions",
            "ticket_clustering",
            "resolution_batches",
            "smart_grouping",
            "resolution_recommendations",
            "efficiency_analytics"
        ],
        "message": "Multi-Ticket Resolution service is running and ready!"
    }
