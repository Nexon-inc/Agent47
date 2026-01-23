from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from core.authentication.auth_manager import get_current_user
from core.database.connection import get_database as get_core_db
from core.database.models import UserSelectedAgent
from sqlalchemy import select
from core.database.models import User
from ..database import get_db
from ..models import ClaraSupportTicket, ClaraCustomerInteraction, ClaraCustomerFeedback, TicketStatus, TicketPriority, SupportChannel
from ..services.support_service import SupportService
from ..services.analytics_service import AnalyticsService
from ..services.chatbot_service import ChatbotService

router = APIRouter(prefix="/clara", tags=["Clara Dashboard"])

@router.get("/tickets")
async def get_support_tickets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50
):
    """Get support tickets for the user/organization"""
    try:
        # Query support tickets
        query = "SELECT * FROM support_tickets WHERE customer_id = :user_id"
        params = {"user_id": current_user.id}
        
        if status:
            query += " AND status = :status"
            params["status"] = status
            
        if priority:
            query += " AND priority = :priority"
            params["priority"] = priority
            
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        tickets = await db.execute(query, params)
        tickets_data = tickets.fetchall()
        
        # Format the response
        formatted_tickets = []
        for ticket in tickets_data:
            formatted_tickets.append({
                "id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "subject": ticket.subject,
                "description": ticket.description,
                "status": ticket.status.value,
                "priority": ticket.priority.value,
                "category": ticket.category.value,
                "channel": ticket.channel.value,
                "satisfaction_score": ticket.satisfaction_score,
                "sentiment_score": ticket.sentiment_score,
                "first_response_time": ticket.first_response_time,
                "actual_resolution_time": ticket.actual_resolution_time,
                "created_at": ticket.created_at.isoformat(),
                "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
                "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None
            })
        
        return formatted_tickets
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch support tickets: {str(e)}")

@router.get("/analytics/summary")
async def get_support_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get support analytics summary"""
    try:
        analytics_service = AnalyticsService()
        
        # Get analytics for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Query ticket statistics
        stats_query = """
        SELECT 
            COUNT(*) as total_tickets,
            COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_tickets,
            COUNT(CASE WHEN status = 'open' THEN 1 END) as open_tickets,
            COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_tickets,
            AVG(first_response_time) as avg_first_response_time,
            AVG(actual_resolution_time) as avg_resolution_time,
            AVG(satisfaction_score) as avg_satisfaction_score,
            AVG(sentiment_score) as avg_sentiment_score
        FROM support_tickets 
        WHERE customer_id = :user_id AND created_at >= :start_date
        """
        
        stats = await db.execute(stats_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        stats_data = stats.fetchone()
        
        # Get channel breakdown
        channel_query = """
        SELECT channel, COUNT(*) as count
        FROM support_tickets 
        WHERE customer_id = :user_id AND created_at >= :start_date
        GROUP BY channel
        """
        
        channels = await db.execute(channel_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        channel_data = channels.fetchall()
        
        channel_breakdown = {row.channel.value: row.count for row in channel_data}
        
        # Get priority breakdown
        priority_query = """
        SELECT priority, COUNT(*) as count
        FROM support_tickets 
        WHERE customer_id = :user_id AND created_at >= :start_date
        GROUP BY priority
        """
        
        priorities = await db.execute(priority_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        priority_data = priorities.fetchall()
        
        priority_breakdown = {row.priority.value: row.count for row in priority_data}
        
        return {
            "total_tickets": stats_data.total_tickets or 0,
            "resolved_tickets": stats_data.resolved_tickets or 0,
            "open_tickets": stats_data.open_tickets or 0,
            "in_progress_tickets": stats_data.in_progress_tickets or 0,
            "avg_first_response_time": round(stats_data.avg_first_response_time or 0, 1),
            "avg_resolution_time": round(stats_data.avg_resolution_time or 0, 1),
            "avg_satisfaction_score": round(stats_data.avg_satisfaction_score or 0, 1),
            "avg_sentiment_score": round(stats_data.avg_sentiment_score or 0, 1),
            "channel_breakdown": channel_breakdown,
            "priority_breakdown": priority_breakdown,
            "resolution_rate": round((stats_data.resolved_tickets or 0) / max(stats_data.total_tickets or 1, 1) * 100, 1),
            "period": "last_30_days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")

@router.get("/chatbot/conversations")
async def get_chatbot_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20
):
    """Get recent chatbot conversations"""
    try:
        # Query recent interactions
        interactions_query = """
        SELECT ci.*, st.ticket_number, st.subject
        FROM customer_interactions ci
        LEFT JOIN support_tickets st ON ci.ticket_id = st.id
        WHERE ci.customer_id = :user_id
        ORDER BY ci.timestamp DESC
        LIMIT :limit
        """
        
        interactions = await db.execute(interactions_query, {
            "user_id": current_user.id,
            "limit": limit
        })
        interactions_data = interactions.fetchall()
        
        # Format the response
        formatted_conversations = []
        for interaction in interactions_data:
            formatted_conversations.append({
                "id": interaction.id,
                "ticket_number": interaction.ticket_number,
                "subject": interaction.subject,
                "message": interaction.message,
                "response": interaction.response,
                "interaction_type": interaction.interaction_type.value,
                "sentiment": interaction.sentiment.value if interaction.sentiment else None,
                "satisfaction_rating": interaction.satisfaction_rating,
                "timestamp": interaction.timestamp.isoformat(),
                "response_time": interaction.response_time
            })
        
        return formatted_conversations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {str(e)}")

@router.post("/chatbot/message")
async def send_chatbot_message(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message to Clara's chatbot"""
    try:
        # Enforce per-agent pause/automation guard
        core_db = get_core_db()
        async with core_db.get_session() as core_session:
            res = await core_session.execute(
                select(UserSelectedAgent).where(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == "clara",
                )
            )
            row = res.scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=403, detail="Agent Clara is not selected")
            if row.status == "paused":
                raise HTTPException(status_code=403, detail="Agent Clara is paused")
            # Allow manual chat regardless of automation flag; if you want to block without automation, uncomment below
            # if not row.automation_enabled:
            #     raise HTTPException(status_code=403, detail="Automation is disabled for Clara")

        chatbot_service = ChatbotService()
        await chatbot_service.initialize()
        
        message = request.get("message", "")
        context = request.get("context", {})
        
        # Process the message through Clara's chatbot
        response = await chatbot_service.process_message(
            user_id=current_user.id,
            message=message,
            context=context,
            db=db
        )
        
        return {
            "success": True,
            "response": response.get("response", "I'm here to help! How can I assist you today?"),
            "suggestions": response.get("suggestions", []),
            "escalation_needed": response.get("escalation_needed", False),
            "ticket_created": response.get("ticket_created", False),
            "ticket_id": response.get("ticket_id"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.get("/knowledge-base")
async def get_knowledge_base(
    current_user: User = Depends(get_current_user),
    search: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20
):
    """Get knowledge base articles"""
    try:
        # Mock knowledge base data
        knowledge_articles = [
            {
                "id": 1,
                "title": "How to reset your password",
                "content": "To reset your password, go to the login page and click 'Forgot Password'...",
                "category": "Account",
                "tags": ["password", "security", "login"],
                "helpfulness_score": 4.5,
                "views": 1250
            },
            {
                "id": 2,
                "title": "Billing and subscription questions",
                "content": "For billing questions, you can view your invoices in the account section...",
                "category": "Billing",
                "tags": ["billing", "subscription", "payment"],
                "helpfulness_score": 4.2,
                "views": 890
            },
            {
                "id": 3,
                "title": "Troubleshooting common issues",
                "content": "If you're experiencing issues, try these common solutions...",
                "category": "Technical",
                "tags": ["troubleshooting", "technical", "issues"],
                "helpfulness_score": 4.7,
                "views": 2100
            }
        ]
        
        # Filter by search term if provided
        if search:
            knowledge_articles = [
                article for article in knowledge_articles
                if search.lower() in article["title"].lower() or search.lower() in article["content"].lower()
            ]
        
        # Filter by category if provided
        if category:
            knowledge_articles = [
                article for article in knowledge_articles
                if article["category"].lower() == category.lower()
            ]
        
        return knowledge_articles[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch knowledge base: {str(e)}")

@router.get("/performance-metrics")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Clara's performance metrics"""
    try:
        # Get performance metrics for the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Query performance data
        performance_query = """
        SELECT 
            COUNT(*) as total_interactions,
            COUNT(CASE WHEN satisfaction_rating >= 4 THEN 1 END) as satisfied_interactions,
            AVG(response_time) as avg_response_time,
            COUNT(CASE WHEN escalation_needed = true THEN 1 END) as escalations,
            COUNT(CASE WHEN resolution_achieved = true THEN 1 END) as resolutions
        FROM customer_interactions 
        WHERE customer_id = :user_id AND timestamp >= :start_date
        """
        
        performance = await db.execute(performance_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        performance_data = performance.fetchone()
        
        satisfaction_rate = 0
        if performance_data.total_interactions > 0:
            satisfaction_rate = (performance_data.satisfied_interactions / performance_data.total_interactions) * 100
        
        resolution_rate = 0
        if performance_data.total_interactions > 0:
            resolution_rate = (performance_data.resolutions / performance_data.total_interactions) * 100
        
        return {
            "total_interactions": performance_data.total_interactions or 0,
            "satisfaction_rate": round(satisfaction_rate, 1),
            "avg_response_time": round(performance_data.avg_response_time or 0, 1),
            "escalation_rate": round((performance_data.escalations or 0) / max(performance_data.total_interactions or 1, 1) * 100, 1),
            "resolution_rate": round(resolution_rate, 1),
            "period": "last_7_days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance metrics: {str(e)}")

@router.get("/health")
async def clara_health_check():
    """Health check for Clara services"""
    return {
        "status": "healthy",
        "agent": "Clara",
        "version": "1.0.0",
        "services": [
            "24_7_customer_support",
            "ai_chatbot",
            "voice_support",
            "ticket_management",
            "knowledge_base",
            "sentiment_analysis",
            "predictive_analytics",
            "multilingual_support",
            "crm_integration",
            "social_media_support"
        ],
        "timestamp": datetime.now().isoformat()
    }
