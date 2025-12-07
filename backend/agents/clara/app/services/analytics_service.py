from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, BackgroundTasks
import json
import asyncio
from enum import Enum

from ..models import SupportAnalytics, SupportTicket, CustomerInteraction, SupportAgent
from ..database import get_clara_database
from backend.core.config import settings
from backend.core.integrations import IntegrationManager
from backend.core.analytics import AnalyticsManager
# NLPUtils removed - not used


class AnalyticsService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        # NLPUtils removed - not used in this service
        
    async def get_support_analytics(
        self, 
        db: Session, 
        start_date: datetime,
        end_date: datetime,
        agent_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive support analytics"""
        try:
            # Build base queries
            tickets_query = db.query(SupportTicket).filter(
                and_(
                    SupportTicket.created_at >= start_date,
                    SupportTicket.created_at <= end_date
                )
            )
            
            interactions_query = db.query(CustomerInteraction).filter(
                and_(
                    CustomerInteraction.created_at >= start_date,
                    CustomerInteraction.created_at <= end_date
                )
            )
            
            if agent_id:
                tickets_query = tickets_query.filter(SupportTicket.assigned_agent_id == agent_id)
                interactions_query = interactions_query.filter(CustomerInteraction.agent_id == agent_id)
            
            tickets = tickets_query.all()
            interactions = interactions_query.all()
            
            # Calculate key metrics
            total_tickets = len(tickets)
            resolved_tickets = len([t for t in tickets if t.status == "resolved"])
            avg_resolution_time = self._calculate_avg_resolution_time(tickets)
            customer_satisfaction = self._calculate_customer_satisfaction(interactions)
            
            # Ticket status breakdown
            status_breakdown = {}
            for ticket in tickets:
                status = ticket.status
                if status not in status_breakdown:
                    status_breakdown[status] = 0
                status_breakdown[status] += 1
            
            # Priority breakdown
            priority_breakdown = {}
            for ticket in tickets:
                priority = ticket.priority
                if priority not in priority_breakdown:
                    priority_breakdown[priority] = 0
                priority_breakdown[priority] += 1
            
            # Channel breakdown
            channel_breakdown = {}
            for interaction in interactions:
                channel = interaction.channel
                if channel not in channel_breakdown:
                    channel_breakdown[channel] = 0
                channel_breakdown[channel] += 1
            
            return {
                "period_start": start_date,
                "period_end": end_date,
                "total_tickets": total_tickets,
                "resolved_tickets": resolved_tickets,
                "resolution_rate": resolved_tickets / total_tickets if total_tickets > 0 else 0,
                "avg_resolution_time_hours": avg_resolution_time,
                "customer_satisfaction_score": customer_satisfaction,
                "status_breakdown": status_breakdown,
                "priority_breakdown": priority_breakdown,
                "channel_breakdown": channel_breakdown
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get support analytics: {str(e)}")
    
    async def get_agent_performance(
        self, 
        db: Session, 
        start_date: datetime,
        end_date: datetime,
        agent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get agent performance analytics"""
        try:
            # Get all agents if no specific agent_id
            if agent_id:
                agents = [db.query(SupportAgent).filter(SupportAgent.id == agent_id).first()]
            else:
                agents = db.query(SupportAgent).all()
            
            performance_data = []
            
            for agent in agents:
                if not agent:
                    continue
                
                # Get agent's tickets
                tickets = db.query(SupportTicket).filter(
                    and_(
                        SupportTicket.assigned_agent_id == agent.id,
                        SupportTicket.created_at >= start_date,
                        SupportTicket.created_at <= end_date
                    )
                ).all()
                
                # Get agent's interactions
                interactions = db.query(CustomerInteraction).filter(
                    and_(
                        CustomerInteraction.agent_id == agent.id,
                        CustomerInteraction.created_at >= start_date,
                        CustomerInteraction.created_at <= end_date
                    )
                ).all()
                
                # Calculate metrics
                total_tickets = len(tickets)
                resolved_tickets = len([t for t in tickets if t.status == "resolved"])
                avg_resolution_time = self._calculate_avg_resolution_time(tickets)
                customer_satisfaction = self._calculate_customer_satisfaction(interactions)
                
                performance_data.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "total_tickets": total_tickets,
                    "resolved_tickets": resolved_tickets,
                    "resolution_rate": resolved_tickets / total_tickets if total_tickets > 0 else 0,
                    "avg_resolution_time_hours": avg_resolution_time,
                    "customer_satisfaction_score": customer_satisfaction,
                    "total_interactions": len(interactions)
                })
            
            return performance_data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get agent performance: {str(e)}")
    
    async def get_trend_analytics(
        self, 
        db: Session, 
        days: int = 30,
        metric: str = "tickets"
    ) -> List[Dict[str, Any]]:
        """Get trend analytics over time"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            trend_data = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                if metric == "tickets":
                    count = db.query(SupportTicket).filter(
                        and_(
                            SupportTicket.created_at >= current_date,
                            SupportTicket.created_at < next_date
                        )
                    ).count()
                elif metric == "interactions":
                    count = db.query(CustomerInteraction).filter(
                        and_(
                            CustomerInteraction.created_at >= current_date,
                            CustomerInteraction.created_at < next_date
                        )
                    ).count()
                else:
                    count = 0
                
                trend_data.append({
                    "date": current_date.date().isoformat(),
                    "count": count
                })
                
                current_date = next_date
            
            return trend_data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get trend analytics: {str(e)}")
    
    async def log_analytics_event(
        self, 
        db: Session, 
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Log analytics event"""
        try:
            analytics = SupportAnalytics(
                event_type=event_type,
                event_data=event_data,
                created_at=datetime.utcnow()
            )
            
            db.add(analytics)
            db.commit()
            
            return {"message": "Analytics event logged successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to log analytics event: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of analytics system"""
        try:
            db = next(get_db())
            analytics_count = db.query(SupportAnalytics).count()
            tickets_count = db.query(SupportTicket).count()
            interactions_count = db.query(CustomerInteraction).count()
            
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "analytics_events_count": analytics_count,
                    "tickets_count": tickets_count,
                    "interactions_count": interactions_count
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    def _calculate_avg_resolution_time(self, tickets: List[SupportTicket]) -> float:
        """Calculate average resolution time in hours"""
        resolved_tickets = [t for t in tickets if t.status == "resolved" and t.resolved_at]
        
        if not resolved_tickets:
            return 0.0
        
        total_hours = 0
        for ticket in resolved_tickets:
            resolution_time = ticket.resolved_at - ticket.created_at
            total_hours += resolution_time.total_seconds() / 3600
        
        return total_hours / len(resolved_tickets)
    
    def _calculate_customer_satisfaction(self, interactions: List[CustomerInteraction]) -> float:
        """Calculate customer satisfaction score"""
        satisfaction_interactions = [i for i in interactions if i.satisfaction_score is not None]
        
        if not satisfaction_interactions:
            return 0.0
        
        total_score = sum(i.satisfaction_score for i in satisfaction_interactions)
        return total_score / len(satisfaction_interactions)
