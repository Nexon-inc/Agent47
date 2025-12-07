from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, BackgroundTasks
import json
import asyncio
from enum import Enum
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from ..models import (
    TicketGroup, BulkAction, ResolutionTemplate, TicketCluster,
    ResolutionBatch, SupportTicket, SupportAgent, CustomerInteraction
)
from ..schemas.multi_ticket_resolution import (
    CreateTicketGroupRequest, UpdateTicketGroupRequest,
    CreateResolutionTemplateRequest, UpdateResolutionTemplateRequest,
    BulkActionRequest, TicketGroupResponse, ResolutionTemplateResponse,
    BulkActionResponse, TicketClusterResponse, ResolutionBatchResponse
)
from ..database import get_clara_database
from ..core.config import settings
from ..core.integrations import IntegrationManager
from ..core.analytics import AnalyticsManager
from ..core.nlp import NLPUtils


class BulkActionType(str, Enum):
    UPDATE_STATUS = "update_status"
    ASSIGN_AGENT = "assign_agent"
    ADD_TAGS = "add_tags"
    UPDATE_PRIORITY = "update_priority"
    SEND_RESPONSE = "send_response"
    ESCALATE = "escalate"


class TicketGroupStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    CLOSED = "closed"


class MultiTicketResolutionService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        # NLPUtils removed - not used in this service
        
    async def create_ticket_group(
        self, 
        db: Session, 
        request: CreateTicketGroupRequest
    ) -> TicketGroupResponse:
        """Create a new ticket group"""
        try:
            # Verify tickets exist
            for ticket_id in request.ticket_ids:
                ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
                if not ticket:
                    raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
            
            group = TicketGroup(
                name=request.name,
                description=request.description,
                ticket_ids=request.ticket_ids,
                category=request.category,
                priority=request.priority,
                assigned_agent_id=request.assigned_agent_id,
                status=TicketGroupStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(group)
            db.commit()
            db.refresh(group)
            
            # Update tickets to reference the group
            for ticket_id in request.ticket_ids:
                ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
                if ticket:
                    ticket.group_id = group.id
                    ticket.updated_at = datetime.utcnow()
            
            db.commit()
            
            return TicketGroupResponse(
                id=group.id,
                name=group.name,
                description=group.description,
                ticket_ids=group.ticket_ids,
                category=group.category,
                priority=group.priority,
                assigned_agent_id=group.assigned_agent_id,
                status=group.status,
                created_at=group.created_at,
                updated_at=group.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create ticket group: {str(e)}")
    
    async def get_ticket_group(
        self, 
        db: Session, 
        group_id: int
    ) -> TicketGroupResponse:
        """Get ticket group by ID"""
        group = db.query(TicketGroup).filter(TicketGroup.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Ticket group not found")
        
        return TicketGroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            ticket_ids=group.ticket_ids,
            category=group.category,
            priority=group.priority,
            assigned_agent_id=group.assigned_agent_id,
            status=group.status,
            created_at=group.created_at,
            updated_at=group.updated_at
        )
    
    async def list_ticket_groups(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[TicketGroupResponse]:
        """List ticket groups"""
        query = db.query(TicketGroup)
        
        if status:
            query = query.filter(TicketGroup.status == status)
        if category:
            query = query.filter(TicketGroup.category == category)
        
        groups = query.offset(skip).limit(limit).all()
        
        return [
            TicketGroupResponse(
                id=group.id,
                name=group.name,
                description=group.description,
                ticket_ids=group.ticket_ids,
                category=group.category,
                priority=group.priority,
                assigned_agent_id=group.assigned_agent_id,
                status=group.status,
                created_at=group.created_at,
                updated_at=group.updated_at
            ) for group in groups
        ]
    
    async def update_ticket_group(
        self, 
        db: Session, 
        group_id: int, 
        request: UpdateTicketGroupRequest
    ) -> TicketGroupResponse:
        """Update ticket group"""
        group = db.query(TicketGroup).filter(TicketGroup.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Ticket group not found")
        
        try:
            if request.name is not None:
                group.name = request.name
            if request.description is not None:
                group.description = request.description
            if request.category is not None:
                group.category = request.category
            if request.priority is not None:
                group.priority = request.priority
            if request.assigned_agent_id is not None:
                group.assigned_agent_id = request.assigned_agent_id
            if request.status is not None:
                group.status = request.status
            
            group.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(group)
            
            return TicketGroupResponse(
                id=group.id,
                name=group.name,
                description=group.description,
                ticket_ids=group.ticket_ids,
                category=group.category,
                priority=group.priority,
                assigned_agent_id=group.assigned_agent_id,
                status=group.status,
                created_at=group.created_at,
                updated_at=group.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update ticket group: {str(e)}")
    
    async def delete_ticket_group(
        self, 
        db: Session, 
        group_id: int
    ) -> Dict[str, str]:
        """Delete ticket group"""
        group = db.query(TicketGroup).filter(TicketGroup.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Ticket group not found")
        
        try:
            # Remove group reference from tickets
            for ticket_id in group.ticket_ids:
                ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
                if ticket:
                    ticket.group_id = None
                    ticket.updated_at = datetime.utcnow()
            
            db.delete(group)
            db.commit()
            return {"message": "Ticket group deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete ticket group: {str(e)}")
    
    async def create_resolution_template(
        self, 
        db: Session, 
        request: CreateResolutionTemplateRequest
    ) -> ResolutionTemplateResponse:
        """Create a new resolution template"""
        try:
            template = ResolutionTemplate(
                name=request.name,
                description=request.description,
                content=request.content,
                variables=request.variables,
                category=request.category,
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(template)
            db.commit()
            db.refresh(template)
            
            return ResolutionTemplateResponse(
                id=template.id,
                name=template.name,
                description=template.description,
                content=template.content,
                variables=template.variables,
                category=template.category,
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create resolution template: {str(e)}")
    
    async def get_resolution_template(
        self, 
        db: Session, 
        template_id: int
    ) -> ResolutionTemplateResponse:
        """Get resolution template by ID"""
        template = db.query(ResolutionTemplate).filter(ResolutionTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Resolution template not found")
        
        return ResolutionTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            content=template.content,
            variables=template.variables,
            category=template.category,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    
    async def list_resolution_templates(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[ResolutionTemplateResponse]:
        """List resolution templates"""
        query = db.query(ResolutionTemplate)
        
        if category:
            query = query.filter(ResolutionTemplate.category == category)
        if is_active is not None:
            query = query.filter(ResolutionTemplate.is_active == is_active)
        
        templates = query.offset(skip).limit(limit).all()
        
        return [
            ResolutionTemplateResponse(
                id=template.id,
                name=template.name,
                description=template.description,
                content=template.content,
                variables=template.variables,
                category=template.category,
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at
            ) for template in templates
        ]
    
    async def update_resolution_template(
        self, 
        db: Session, 
        template_id: int, 
        request: UpdateResolutionTemplateRequest
    ) -> ResolutionTemplateResponse:
        """Update resolution template"""
        template = db.query(ResolutionTemplate).filter(ResolutionTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Resolution template not found")
        
        try:
            if request.name is not None:
                template.name = request.name
            if request.description is not None:
                template.description = request.description
            if request.content is not None:
                template.content = request.content
            if request.variables is not None:
                template.variables = request.variables
            if request.category is not None:
                template.category = request.category
            if request.is_active is not None:
                template.is_active = request.is_active
            
            template.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(template)
            
            return ResolutionTemplateResponse(
                id=template.id,
                name=template.name,
                description=template.description,
                content=template.content,
                variables=template.variables,
                category=template.category,
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update resolution template: {str(e)}")
    
    async def delete_resolution_template(
        self, 
        db: Session, 
        template_id: int
    ) -> Dict[str, str]:
        """Delete resolution template"""
        template = db.query(ResolutionTemplate).filter(ResolutionTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Resolution template not found")
        
        try:
            db.delete(template)
            db.commit()
            return {"message": "Resolution template deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete resolution template: {str(e)}")
    
    async def execute_bulk_action(
        self, 
        db: Session, 
        request: BulkActionRequest
    ) -> BulkActionResponse:
        """Execute a bulk action on multiple tickets"""
        try:
            # Verify tickets exist
            tickets = []
            for ticket_id in request.ticket_ids:
                ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
                if not ticket:
                    raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
                tickets.append(ticket)
            
            # Create bulk action record
            bulk_action = BulkAction(
                action_type=request.action_type,
                ticket_ids=request.ticket_ids,
                parameters=request.parameters,
                executed_by=request.executed_by,
                status="in_progress",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(bulk_action)
            db.commit()
            db.refresh(bulk_action)
            
            # Execute the action
            success_count = 0
            failed_count = 0
            errors = []
            
            for ticket in tickets:
                try:
                    await self._execute_single_action(ticket, request.action_type, request.parameters, db)
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Ticket {ticket.id}: {str(e)}")
            
            # Update bulk action status
            bulk_action.status = "completed" if failed_count == 0 else "completed_with_errors"
            bulk_action.results = {
                "success_count": success_count,
                "failed_count": failed_count,
                "errors": errors
            }
            bulk_action.updated_at = datetime.utcnow()
            
            db.commit()
            
            return BulkActionResponse(
                id=bulk_action.id,
                action_type=bulk_action.action_type,
                ticket_ids=bulk_action.ticket_ids,
                parameters=bulk_action.parameters,
                executed_by=bulk_action.executed_by,
                status=bulk_action.status,
                results=bulk_action.results,
                created_at=bulk_action.created_at,
                updated_at=bulk_action.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to execute bulk action: {str(e)}")
    
    async def get_bulk_action(
        self, 
        db: Session, 
        action_id: int
    ) -> BulkActionResponse:
        """Get bulk action by ID"""
        action = db.query(BulkAction).filter(BulkAction.id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail="Bulk action not found")
        
        return BulkActionResponse(
            id=action.id,
            action_type=action.action_type,
            ticket_ids=action.ticket_ids,
            parameters=action.parameters,
            executed_by=action.executed_by,
            status=action.status,
            results=action.results,
            created_at=action.created_at,
            updated_at=action.updated_at
        )
    
    async def list_bulk_actions(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        action_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[BulkActionResponse]:
        """List bulk actions"""
        query = db.query(BulkAction)
        
        if action_type:
            query = query.filter(BulkAction.action_type == action_type)
        if status:
            query = query.filter(BulkAction.status == status)
        
        actions = query.order_by(desc(BulkAction.created_at)).offset(skip).limit(limit).all()
        
        return [
            BulkActionResponse(
                id=action.id,
                action_type=action.action_type,
                ticket_ids=action.ticket_ids,
                parameters=action.parameters,
                executed_by=action.executed_by,
                status=action.status,
                results=action.results,
                created_at=action.created_at,
                updated_at=action.updated_at
            ) for action in actions
        ]
    
    async def cluster_tickets(
        self, 
        db: Session, 
        ticket_ids: List[int],
        similarity_threshold: float = 0.8
    ) -> List[TicketClusterResponse]:
        """Cluster similar tickets together"""
        try:
            # Get tickets
            tickets = []
            for ticket_id in ticket_ids:
                ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
                if not ticket:
                    raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
                tickets.append(ticket)
            
            if len(tickets) < 2:
                return []
            
            # Extract text features
            texts = []
            for ticket in tickets:
                text = f"{ticket.title} {ticket.description} {ticket.category}"
                texts.append(text)
            
            # Vectorize text
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            vectors = vectorizer.fit_transform(texts).toarray()
            
            # Cluster using DBSCAN
            clustering = DBSCAN(eps=1-similarity_threshold, min_samples=2)
            cluster_labels = clustering.fit_predict(vectors)
            
            # Group tickets by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label == -1:  # Noise points
                    continue
                
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(tickets[i])
            
            # Create cluster records
            cluster_responses = []
            for label, cluster_tickets in clusters.items():
                if len(cluster_tickets) < 2:
                    continue
                
                # Create cluster record
                cluster = TicketCluster(
                    ticket_ids=[t.id for t in cluster_tickets],
                    similarity_score=similarity_threshold,
                    common_category=cluster_tickets[0].category,
                    created_at=datetime.utcnow()
                )
                
                db.add(cluster)
                cluster_responses.append(TicketClusterResponse(
                    id=cluster.id,
                    ticket_ids=cluster.ticket_ids,
                    similarity_score=cluster.similarity_score,
                    common_category=cluster.common_category,
                    created_at=cluster.created_at
                ))
            
            db.commit()
            return cluster_responses
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to cluster tickets: {str(e)}")
    
    async def create_resolution_batch(
        self, 
        db: Session, 
        ticket_ids: List[int],
        template_id: int,
        variables: Dict[str, Any]
    ) -> ResolutionBatchResponse:
        """Create a resolution batch for multiple tickets"""
        try:
            # Verify template exists
            template = db.query(ResolutionTemplate).filter(ResolutionTemplate.id == template_id).first()
            if not template:
                raise HTTPException(status_code=404, detail="Resolution template not found")
            
            # Verify tickets exist
            tickets = []
            for ticket_id in ticket_ids:
                ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
                if not ticket:
                    raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
                tickets.append(ticket)
            
            # Create resolution batch
            batch = ResolutionBatch(
                ticket_ids=ticket_ids,
                template_id=template_id,
                variables=variables,
                status="pending",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(batch)
            db.commit()
            db.refresh(batch)
            
            # Apply resolution to tickets
            success_count = 0
            failed_count = 0
            
            for ticket in tickets:
                try:
                    # Render template with variables
                    resolution_content = self._render_template(template.content, variables, ticket)
                    
                    # Update ticket
                    ticket.resolution = resolution_content
                    ticket.status = "resolved"
                    ticket.resolved_at = datetime.utcnow()
                    ticket.updated_at = datetime.utcnow()
                    
                    success_count += 1
                except Exception as e:
                    failed_count += 1
            
            # Update batch status
            batch.status = "completed" if failed_count == 0 else "completed_with_errors"
            batch.results = {
                "success_count": success_count,
                "failed_count": failed_count
            }
            batch.updated_at = datetime.utcnow()
            
            db.commit()
            
            return ResolutionBatchResponse(
                id=batch.id,
                ticket_ids=batch.ticket_ids,
                template_id=batch.template_id,
                variables=batch.variables,
                status=batch.status,
                results=batch.results,
                created_at=batch.created_at,
                updated_at=batch.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create resolution batch: {str(e)}")
    
    async def get_resolution_batch(
        self, 
        db: Session, 
        batch_id: int
    ) -> ResolutionBatchResponse:
        """Get resolution batch by ID"""
        batch = db.query(ResolutionBatch).filter(ResolutionBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Resolution batch not found")
        
        return ResolutionBatchResponse(
            id=batch.id,
            ticket_ids=batch.ticket_ids,
            template_id=batch.template_id,
            variables=batch.variables,
            status=batch.status,
            results=batch.results,
            created_at=batch.created_at,
            updated_at=batch.updated_at
        )
    
    async def list_resolution_batches(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[ResolutionBatchResponse]:
        """List resolution batches"""
        query = db.query(ResolutionBatch)
        
        if status:
            query = query.filter(ResolutionBatch.status == status)
        
        batches = query.order_by(desc(ResolutionBatch.created_at)).offset(skip).limit(limit).all()
        
        return [
            ResolutionBatchResponse(
                id=batch.id,
                ticket_ids=batch.ticket_ids,
                template_id=batch.template_id,
                variables=batch.variables,
                status=batch.status,
                results=batch.results,
                created_at=batch.created_at,
                updated_at=batch.updated_at
            ) for batch in batches
        ]
    
    async def smart_grouping(
        self, 
        db: Session, 
        criteria: Dict[str, Any]
    ) -> List[TicketGroupResponse]:
        """Automatically group tickets based on smart criteria"""
        try:
            # Build query based on criteria
            query = db.query(SupportTicket).filter(SupportTicket.group_id.is_(None))
            
            if criteria.get("category"):
                query = query.filter(SupportTicket.category == criteria["category"])
            
            if criteria.get("priority"):
                query = query.filter(SupportTicket.priority == criteria["priority"])
            
            if criteria.get("status"):
                query = query.filter(SupportTicket.status == criteria["status"])
            
            if criteria.get("assigned_agent_id"):
                query = query.filter(SupportTicket.assigned_agent_id == criteria["assigned_agent_id"])
            
            # Get tickets
            tickets = query.all()
            
            if len(tickets) < 2:
                return []
            
            # Group by similarity
            groups = self._group_tickets_by_similarity(tickets, criteria.get("similarity_threshold", 0.7))
            
            # Create ticket groups
            group_responses = []
            for group_tickets in groups:
                if len(group_tickets) < 2:
                    continue
                
                # Create group
                group = TicketGroup(
                    name=f"Auto Group - {group_tickets[0].category} - {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    description=f"Automatically grouped {len(group_tickets)} similar tickets",
                    ticket_ids=[t.id for t in group_tickets],
                    category=group_tickets[0].category,
                    priority=group_tickets[0].priority,
                    assigned_agent_id=group_tickets[0].assigned_agent_id,
                    status=TicketGroupStatus.ACTIVE,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(group)
                group_responses.append(TicketGroupResponse(
                    id=group.id,
                    name=group.name,
                    description=group.description,
                    ticket_ids=group.ticket_ids,
                    category=group.category,
                    priority=group.priority,
                    assigned_agent_id=group.assigned_agent_id,
                    status=group.status,
                    created_at=group.created_at,
                    updated_at=group.updated_at
                ))
            
            db.commit()
            return group_responses
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to perform smart grouping: {str(e)}")
    
    async def resolution_recommendations(
        self, 
        db: Session, 
        ticket_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """Get resolution recommendations for tickets"""
        try:
            recommendations = []
            
            for ticket_id in ticket_ids:
                ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
                if not ticket:
                    continue
                
                # Find similar resolved tickets
                similar_tickets = db.query(SupportTicket).filter(
                    and_(
                        SupportTicket.category == ticket.category,
                        SupportTicket.status == "resolved",
                        SupportTicket.id != ticket_id
                    )
                ).limit(5).all()
                
                if similar_tickets:
                    # Get most common resolution
                    resolutions = [t.resolution for t in similar_tickets if t.resolution]
                    if resolutions:
                        common_resolution = max(set(resolutions), key=resolutions.count)
                        
                        recommendations.append({
                            "ticket_id": ticket_id,
                            "recommended_resolution": common_resolution,
                            "similar_tickets_count": len(similar_tickets),
                            "confidence_score": len([r for r in resolutions if r == common_resolution]) / len(resolutions)
                        })
                
                # Get relevant templates
                templates = db.query(ResolutionTemplate).filter(
                    and_(
                        ResolutionTemplate.category == ticket.category,
                        ResolutionTemplate.is_active == True
                    )
                ).limit(3).all()
                
                if templates:
                    recommendations.append({
                        "ticket_id": ticket_id,
                        "recommended_templates": [
                            {
                                "id": t.id,
                                "name": t.name,
                                "description": t.description
                            } for t in templates
                        ]
                    })
            
            return recommendations
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get resolution recommendations: {str(e)}")
    
    async def efficiency_analytics(
        self, 
        db: Session, 
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get efficiency analytics for multi-ticket resolution"""
        try:
            # Get data in date range
            groups = db.query(TicketGroup).filter(
                and_(
                    TicketGroup.created_at >= start_date,
                    TicketGroup.created_at <= end_date
                )
            ).all()
            
            bulk_actions = db.query(BulkAction).filter(
                and_(
                    BulkAction.created_at >= start_date,
                    BulkAction.created_at <= end_date
                )
            ).all()
            
            resolution_batches = db.query(ResolutionBatch).filter(
                and_(
                    ResolutionBatch.created_at >= start_date,
                    ResolutionBatch.created_at <= end_date
                )
            ).all()
            
            # Calculate metrics
            total_groups = len(groups)
            total_bulk_actions = len(bulk_actions)
            total_resolution_batches = len(resolution_batches)
            
            # Group efficiency
            total_tickets_in_groups = sum(len(g.ticket_ids) for g in groups)
            avg_group_size = total_tickets_in_groups / total_groups if total_groups > 0 else 0
            
            # Bulk action efficiency
            successful_actions = [a for a in bulk_actions if a.status == "completed"]
            action_success_rate = len(successful_actions) / total_bulk_actions if total_bulk_actions > 0 else 0
            
            # Resolution batch efficiency
            successful_batches = [b for b in resolution_batches if b.status == "completed"]
            batch_success_rate = len(successful_batches) / total_resolution_batches if total_resolution_batches > 0 else 0
            
            # Time savings estimation
            estimated_time_saved = total_bulk_actions * 5 + total_resolution_batches * 10  # minutes per action/batch
            
            return {
                "period_start": start_date,
                "period_end": end_date,
                "total_groups": total_groups,
                "total_bulk_actions": total_bulk_actions,
                "total_resolution_batches": total_resolution_batches,
                "total_tickets_processed": total_tickets_in_groups,
                "avg_group_size": avg_group_size,
                "action_success_rate": action_success_rate,
                "batch_success_rate": batch_success_rate,
                "estimated_time_saved_minutes": estimated_time_saved,
                "efficiency_score": (action_success_rate + batch_success_rate) / 2
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get efficiency analytics: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of multi-ticket resolution system"""
        try:
            db = next(get_db())
            group_count = db.query(TicketGroup).count()
            template_count = db.query(ResolutionTemplate).count()
            action_count = db.query(BulkAction).count()
            batch_count = db.query(ResolutionBatch).count()
            
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "groups_count": group_count,
                    "templates_count": template_count,
                    "actions_count": action_count,
                    "batches_count": batch_count
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def _execute_single_action(
        self, 
        ticket: SupportTicket, 
        action_type: str, 
        parameters: Dict[str, Any], 
        db: Session
    ):
        """Execute a single action on a ticket"""
        try:
            if action_type == BulkActionType.UPDATE_STATUS:
                ticket.status = parameters.get("status", ticket.status)
            elif action_type == BulkActionType.ASSIGN_AGENT:
                ticket.assigned_agent_id = parameters.get("agent_id")
            elif action_type == BulkActionType.ADD_TAGS:
                current_tags = ticket.tags or []
                new_tags = parameters.get("tags", [])
                ticket.tags = list(set(current_tags + new_tags))
            elif action_type == BulkActionType.UPDATE_PRIORITY:
                ticket.priority = parameters.get("priority", ticket.priority)
            elif action_type == BulkActionType.SEND_RESPONSE:
                response_content = parameters.get("response_content")
                if response_content:
                    # Create interaction record
                    interaction = CustomerInteraction(
                        customer_id=ticket.customer_id,
                        agent_id=parameters.get("agent_id"),
                        interaction_type="response",
                        content=response_content,
                        created_at=datetime.utcnow()
                    )
                    db.add(interaction)
            elif action_type == BulkActionType.ESCALATE:
                ticket.priority = "high"
                ticket.status = "escalated"
            
            ticket.updated_at = datetime.utcnow()
            
        except Exception as e:
            raise Exception(f"Failed to execute action {action_type}: {str(e)}")
    
    def _render_template(
        self, 
        template_content: str, 
        variables: Dict[str, Any], 
        ticket: SupportTicket
    ) -> str:
        """Render template with variables and ticket data"""
        try:
            content = template_content
            
            # Add ticket-specific variables
            ticket_variables = {
                "ticket_id": ticket.id,
                "customer_name": ticket.customer_name,
                "category": ticket.category,
                "priority": ticket.priority,
                "created_date": ticket.created_at.strftime("%Y-%m-%d"),
                "description": ticket.description
            }
            
            # Merge variables
            all_variables = {**variables, **ticket_variables}
            
            # Replace placeholders
            for key, value in all_variables.items():
                placeholder = f"{{{{{key}}}}}"
                content = content.replace(placeholder, str(value))
            
            return content
            
        except Exception:
            return template_content
    
    def _group_tickets_by_similarity(
        self, 
        tickets: List[SupportTicket], 
        similarity_threshold: float
    ) -> List[List[SupportTicket]]:
        """Group tickets by similarity"""
        if len(tickets) < 2:
            return []
        
        # Extract text features
        texts = []
        for ticket in tickets:
            text = f"{ticket.title} {ticket.description} {ticket.category}"
            texts.append(text)
        
        # Vectorize text
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        vectors = vectorizer.fit_transform(texts).toarray()
        
        # Cluster using DBSCAN
        clustering = DBSCAN(eps=1-similarity_threshold, min_samples=2)
        cluster_labels = clustering.fit_predict(vectors)
        
        # Group tickets by cluster
        clusters = {}
        for i, label in enumerate(cluster_labels):
            if label == -1:  # Noise points
                continue
            
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(tickets[i])
        
        return list(clusters.values())
