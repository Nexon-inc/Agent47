from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ..database import get_clara_database
from ..models import SupportAnalytics, SupportTicket, CustomerInteraction, ChatSession
from sqlalchemy import select, func, cast, Date, and_
from datetime import datetime, timedelta

router = APIRouter()

# Pydantic models for request/response
class AnalyticsDateRange(BaseModel):
    start_date: str
    end_date: str

class AnalyticsFilter(BaseModel):
    customer_id: Optional[int] = None
    agent_id: Optional[int] = None
    category: Optional[str] = None
    channel: Optional[str] = None

@router.get("/overview", response_model=Dict[str, Any])
async def get_support_overview():
    """Get overall support analytics overview"""
    try:
        db = await get_clara_database()
        async with db.get_session() as db_session:
            
            # Get current date and 30 days ago
            now = datetime.utcnow()
            thirty_days_ago = now - timedelta(days=30)
            
            # Total tickets
            total_tickets = await db_session.execute(select(func.count(SupportTicket.id)))
            total_tickets = total_tickets.scalar()
            
            # Open tickets
            open_tickets = await db_session.execute(
                select(func.count(SupportTicket.id))
                .where(SupportTicket.status.in_(["open", "in_progress", "waiting_customer", "waiting_agent"]))
            )
            open_tickets = open_tickets.scalar()
            
            # Resolved tickets in last 30 days
            resolved_tickets = await db_session.execute(
                select(func.count(SupportTicket.id))
                .where(
                    and_(
                        SupportTicket.status == "resolved",
                        SupportTicket.resolved_at >= thirty_days_ago
                    )
                )
            )
            resolved_tickets = resolved_tickets.scalar()
            
            # Active chat sessions
            active_chats = await db_session.execute(
                select(func.count(ChatSession.id))
                .where(ChatSession.status == "active")
            )
            active_chats = active_chats.scalar()
            
            return {
                "success": True,
                "overview": {
                    "total_tickets": total_tickets,
                    "open_tickets": open_tickets,
                    "resolved_tickets_30_days": resolved_tickets,
                    "active_chat_sessions": active_chats,
                    "resolution_rate_30_days": round((resolved_tickets / max(total_tickets, 1)) * 100, 2)
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/trends", response_model=Dict[str, Any])
async def get_ticket_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get ticket trends over time"""
    try:
        db = await get_clara_database()
        async with db.get_session() as db_session:
            
            # Generate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get daily ticket counts
            daily_tickets = await db_session.execute(
                select(
                    cast(SupportTicket.created_at, Date).label("date"),
                    func.count(SupportTicket.id).label("count")
                )
                .where(SupportTicket.created_at >= start_date)
                .group_by(cast(SupportTicket.created_at, Date))
                .order_by(cast(SupportTicket.created_at, Date))
            )
            daily_tickets = daily_tickets.all()
            
            # Get daily resolved tickets
            daily_resolved = await db_session.execute(
                select(
                    cast(SupportTicket.resolved_at, Date).label("date"),
                    func.count(SupportTicket.id).label("count")
                )
                .where(
                    and_(
                        SupportTicket.resolved_at >= start_date,
                        SupportTicket.status == "resolved"
                    )
                )
                .group_by(cast(SupportTicket.resolved_at, Date))
                .order_by(cast(SupportTicket.resolved_at, Date))
            )
            daily_resolved = daily_resolved.all()
            
            return {
                "success": True,
                "trends": {
                    "period_days": days,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "daily_created": [
                        {
                            "date": str(item.date),
                            "count": item.count
                        }
                        for item in daily_tickets
                    ],
                    "daily_resolved": [
                        {
                            "date": str(item.date),
                            "count": item.count
                        }
                        for item in daily_resolved
                    ]
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/category-distribution", response_model=Dict[str, Any])
async def get_ticket_category_distribution():
    """Get ticket distribution by category"""
    try:
        db = await get_clara_database()
        async with db.get_session() as db_session:
            
            # Get tickets by category
            category_distribution = await db_session.execute(
                select(
                    SupportTicket.category,
                    func.count(SupportTicket.id).label("count")
                )
                .group_by(SupportTicket.category)
                .order_by(func.count(SupportTicket.id).desc())
            )
            category_distribution = category_distribution.all()
            
            return {
                "success": True,
                "category_distribution": [
                    {
                        "category": item.category.value,
                        "count": item.count,
                        "percentage": 0  # Will be calculated in frontend
                    }
                    for item in category_distribution
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/priority-distribution", response_model=Dict[str, Any])
async def get_ticket_priority_distribution():
    """Get ticket distribution by priority"""
    try:
        db = await get_clara_database()
        async with db.get_session() as db_session:
            
            # Get tickets by priority
            priority_distribution = await db_session.execute(
                select(
                    SupportTicket.priority,
                    func.count(SupportTicket.id).label("count")
                )
                .group_by(SupportTicket.priority)
                .order_by(func.count(SupportTicket.id).desc())
            )
            priority_distribution = priority_distribution.all()
            
            return {
                "success": True,
                "priority_distribution": [
                    {
                        "priority": item.priority.value,
                        "count": item.count,
                        "percentage": 0  # Will be calculated in frontend
                    }
                    for item in priority_distribution
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/channel-distribution", response_model=Dict[str, Any])
async def get_ticket_channel_distribution():
    """Get ticket distribution by support channel"""
    try:
        db = await get_clara_database()
        async with db.get_session() as db_session:
            
            # Get tickets by channel
            channel_distribution = await db_session.execute(
                select(
                    SupportTicket.channel,
                    func.count(SupportTicket.id).label("count")
                )
                .group_by(SupportTicket.channel)
                .order_by(func.count(SupportTicket.id).desc())
            )
            channel_distribution = channel_distribution.all()
            
            return {
                "success": True,
                "channel_distribution": [
                    {
                        "channel": item.channel.value,
                        "count": item.count,
                        "percentage": 0  # Will be calculated in frontend
                    }
                    for item in channel_distribution
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/response-times", response_model=Dict[str, Any])
async def get_response_time_analytics():
    """Get response time analytics"""
    try:
        db = await get_clara_database()
        async with db.get_session() as db_session:
            
            # Get average first response time
            avg_first_response = await db_session.execute(
                select(func.avg(SupportTicket.first_response_time))
                .where(SupportTicket.first_response_time.isnot(None))
            )
            avg_first_response = avg_first_response.scalar() or 0
            
            # Get average resolution time
            avg_resolution = await db_session.execute(
                select(func.avg(SupportTicket.actual_resolution_time))
                .where(SupportTicket.actual_resolution_time.isnot(None))
            )
            avg_resolution = avg_resolution.scalar() or 0
            
            # Get SLA compliance rate
            total_with_sla = await db_session.execute(
                select(func.count(SupportTicket.id))
                .where(SupportTicket.sla_breach.isnot(None))
            )
            total_with_sla = total_with_sla.scalar()
            
            sla_breaches = await db_session.execute(
                select(func.count(SupportTicket.id))
                .where(SupportTicket.sla_breach == True)
            )
            sla_breaches = sla_breaches.scalar()
            
            sla_compliance_rate = 0
            if total_with_sla > 0:
                sla_compliance_rate = round(((total_with_sla - sla_breaches) / total_with_sla) * 100, 2)
            
            return {
                "success": True,
                "response_times": {
                    "average_first_response_time_minutes": round(avg_first_response, 2),
                    "average_resolution_time_minutes": round(avg_resolution, 2),
                    "sla_compliance_rate_percentage": sla_compliance_rate,
                    "total_sla_tickets": total_with_sla,
                    "sla_breaches": sla_breaches
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/customer-satisfaction", response_model=Dict[str, Any])
async def get_customer_satisfaction_analytics():
    """Get customer satisfaction analytics"""
    try:
        db = await get_clara_database()
        async with db.get_session() as db_session:
            
            # Get average satisfaction score
            avg_satisfaction = await db_session.execute(
                select(func.avg(SupportTicket.satisfaction_score))
                .where(SupportTicket.satisfaction_score.isnot(None))
            )
            avg_satisfaction = avg_satisfaction.scalar() or 0
            
            # Get satisfaction distribution
            satisfaction_distribution = await db_session.execute(
                select(
                    SupportTicket.satisfaction_score,
                    func.count(SupportTicket.id).label("count")
                )
                .where(SupportTicket.satisfaction_score.isnot(None))
                .group_by(SupportTicket.satisfaction_score)
                .order_by(SupportTicket.satisfaction_score)
            )
            satisfaction_distribution = satisfaction_distribution.all()
            
            # Get total rated tickets
            total_rated = await db_session.execute(
                select(func.count(SupportTicket.id))
                .where(SupportTicket.satisfaction_score.isnot(None))
            )
            total_rated = total_rated.scalar()
            
            return {
                "success": True,
                "customer_satisfaction": {
                    "average_satisfaction_score": round(avg_satisfaction, 2),
                    "total_rated_tickets": total_rated,
                    "satisfaction_distribution": [
                        {
                            "score": item.satisfaction_score,
                            "count": item.count,
                            "percentage": round((item.count / max(total_rated, 1)) * 100, 2)
                        }
                        for item in satisfaction_distribution
                    ]
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/analytics", response_model=Dict[str, Any])
async def get_chat_analytics():
    """Get chat analytics"""
    try:
        db = await get_clara_database()
        async with db.get_session() as db_session:
            
            # Get current date and 30 days ago
            now = datetime.utcnow()
            thirty_days_ago = now - timedelta(days=30)
            
            # Total chat sessions
            total_sessions = await db_session.execute(select(func.count(ChatSession.id)))
            total_sessions = total_sessions.scalar()
            
            # Active sessions
            active_sessions = await db_session.execute(
                select(func.count(ChatSession.id))
                .where(ChatSession.status == "active")
            )
            active_sessions = active_sessions.scalar()
            
            # Sessions in last 30 days
            recent_sessions = await db_session.execute(
                select(func.count(ChatSession.id))
                .where(ChatSession.start_time >= thirty_days_ago)
            )
            recent_sessions = recent_sessions.scalar()
            
            # Average session duration
            avg_duration = await db_session.execute(
                select(func.avg(ChatSession.duration))
                .where(ChatSession.duration.isnot(None))
            )
            avg_duration = avg_duration.scalar() or 0
            
            # Average messages per session
            avg_messages = await db_session.execute(
                select(func.avg(ChatSession.messages_count))
                .where(ChatSession.messages_count > 0)
            )
            avg_messages = avg_messages.scalar() or 0
            
            return {
                "success": True,
                "chat_analytics": {
                    "total_sessions": total_sessions,
                    "active_sessions": active_sessions,
                    "recent_sessions_30_days": recent_sessions,
                    "average_session_duration_seconds": round(avg_duration, 2),
                    "average_messages_per_session": round(avg_messages, 2)
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/performance", response_model=Dict[str, Any])
async def get_agent_performance_analytics():
    """Get agent performance analytics"""
    try:
        db = await get_clara_database()
        async with db.get_session() as db_session:
            from sqlalchemy import select, func
            from ..models import SupportAgent
            
            # Get agent performance data
            agent_performance = await db_session.execute(
                select(
                    SupportAgent.user_id,
                    SupportAgent.agent_code,
                    SupportAgent.total_tickets_resolved,
                    SupportAgent.total_tickets_escalated,
                    SupportAgent.performance_score,
                    SupportAgent.customer_satisfaction_avg,
                    SupportAgent.response_time_avg
                )
                .order_by(SupportAgent.performance_score.desc())
            )
            agent_performance = agent_performance.all()
            
            return {
                "success": True,
                "agent_performance": [
                    {
                        "user_id": item.user_id,
                        "agent_code": item.agent_code,
                        "tickets_resolved": item.total_tickets_resolved,
                        "tickets_escalated": item.total_tickets_escalated,
                        "performance_score": round(item.performance_score, 2),
                        "customer_satisfaction_avg": round(item.customer_satisfaction_avg or 0, 2),
                        "response_time_avg_minutes": round(item.response_time_avg or 0, 2)
                    }
                    for item in agent_performance
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/daily", response_model=Dict[str, Any])
async def get_daily_report(
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    """Get daily support report"""
    try:
        db = await get_clara_database()
        async with db.get_session() as db_session:
            
            # Parse date
            try:
                report_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
            
            # Get tickets created on this date
            tickets_created = await db_session.execute(
                select(func.count(SupportTicket.id))
                .where(cast(SupportTicket.created_at, Date) == report_date)
            )
            tickets_created = tickets_created.scalar()
            
            # Get tickets resolved on this date
            tickets_resolved = await db_session.execute(
                select(func.count(SupportTicket.id))
                .where(
                    and_(
                        cast(SupportTicket.resolved_at, Date) == report_date,
                        SupportTicket.status == "resolved"
                    )
                )
            )
            tickets_resolved = tickets_resolved.scalar()
            
            # Get chat sessions started on this date
            chats_started = await db_session.execute(
                select(func.count(ChatSession.id))
                .where(cast(ChatSession.start_time, Date) == report_date)
            )
            chats_started = chats_started.scalar()
            
            return {
                "success": True,
                "daily_report": {
                    "date": date,
                    "tickets_created": tickets_created,
                    "tickets_resolved": tickets_resolved,
                    "chats_started": chats_started,
                    "resolution_rate": round((tickets_resolved / max(tickets_created, 1)) * 100, 2)
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
