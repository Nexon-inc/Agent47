from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.authentication.auth_manager import get_current_user
from backend.core.database.connection import get_database as get_core_db
from backend.core.database.models import UserSelectedAgent
from sqlalchemy import select
from backend.core.database.models import User
from ..database import get_db
from ..models import Lead, Deal, LeadInteraction, LeadStatus, DealStatus, CommunicationChannel
from ..services.lead_generation_service import LeadGenerationService
from ..services.sales_forecasting_service import SalesForecastingService
from ..services.performance_analytics_service import PerformanceAnalyticsService

router = APIRouter(prefix="/eric", tags=["Eric Dashboard"])

@router.get("/leads")
async def get_leads(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50
):
    """Get sales leads for the user/organization"""
    try:
        # Query leads
        query = "SELECT * FROM leads WHERE brand_id = :user_id"
        params = {"user_id": current_user.id}
        
        if status:
            query += " AND lead_status = :status"
            params["status"] = status
            
        if source:
            query += " AND lead_source = :source"
            params["source"] = source
            
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        leads = await db.execute(query, params)
        leads_data = leads.fetchall()
        
        # Format the response
        formatted_leads = []
        for lead in leads_data:
            formatted_leads.append({
                "id": lead.id,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "email": lead.email,
                "phone": lead.phone,
                "company": lead.company,
                "job_title": lead.job_title,
                "industry": lead.industry,
                "lead_source": lead.lead_source.value,
                "lead_status": lead.lead_status.value,
                "lead_score": lead.lead_score,
                "budget": lead.budget,
                "timeline": lead.timeline,
                "location": lead.location,
                "created_at": lead.created_at.isoformat(),
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None
            })
        
        return formatted_leads
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch leads: {str(e)}")

@router.get("/deals")
async def get_deals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    limit: int = 50
):
    """Get sales deals for the user/organization"""
    try:
        # Query deals
        query = "SELECT * FROM deals WHERE brand_id = :user_id"
        params = {"user_id": current_user.id}
        
        if status:
            query += " AND deal_status = :status"
            params["status"] = status
            
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        deals = await db.execute(query, params)
        deals_data = deals.fetchall()
        
        # Format the response
        formatted_deals = []
        for deal in deals_data:
            formatted_deals.append({
                "id": deal.id,
                "deal_name": deal.deal_name,
                "lead_id": deal.lead_id,
                "deal_value": deal.deal_value,
                "deal_status": deal.deal_status.value,
                "sales_stage": deal.sales_stage.value,
                "probability": deal.probability,
                "expected_close_date": deal.expected_close_date.isoformat() if deal.expected_close_date else None,
                "created_at": deal.created_at.isoformat(),
                "updated_at": deal.updated_at.isoformat() if deal.updated_at else None
            })
        
        return formatted_deals
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch deals: {str(e)}")

@router.get("/analytics/summary")
async def get_sales_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get sales analytics summary"""
    try:
        # Get analytics for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Query lead statistics
        leads_query = """
        SELECT 
            COUNT(*) as total_leads,
            COUNT(CASE WHEN lead_status = 'qualified' THEN 1 END) as qualified_leads,
            COUNT(CASE WHEN lead_status = 'closed_won' THEN 1 END) as won_leads,
            COUNT(CASE WHEN lead_status = 'closed_lost' THEN 1 END) as lost_leads,
            AVG(lead_score) as avg_lead_score
        FROM leads 
        WHERE brand_id = :user_id AND created_at >= :start_date
        """
        
        leads_stats = await db.execute(leads_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        leads_data = leads_stats.fetchone()
        
        # Query deal statistics
        deals_query = """
        SELECT 
            COUNT(*) as total_deals,
            COUNT(CASE WHEN deal_status = 'closed_won' THEN 1 END) as won_deals,
            COUNT(CASE WHEN deal_status = 'closed_lost' THEN 1 END) as lost_deals,
            SUM(CASE WHEN deal_status = 'closed_won' THEN deal_value ELSE 0 END) as total_revenue,
            AVG(CASE WHEN deal_status = 'closed_won' THEN deal_value ELSE NULL END) as avg_deal_value
        FROM deals 
        WHERE brand_id = :user_id AND created_at >= :start_date
        """
        
        deals_stats = await db.execute(deals_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        deals_data = deals_stats.fetchone()
        
        # Get lead source breakdown
        source_query = """
        SELECT lead_source, COUNT(*) as count
        FROM leads 
        WHERE brand_id = :user_id AND created_at >= :start_date
        GROUP BY lead_source
        """
        
        sources = await db.execute(source_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        source_data = sources.fetchall()
        
        source_breakdown = {row.lead_source.value: row.count for row in source_data}
        
        # Calculate conversion rates
        lead_to_deal_rate = 0
        if leads_data.total_leads > 0:
            lead_to_deal_rate = (deals_data.total_deals / leads_data.total_leads) * 100
        
        deal_close_rate = 0
        if deals_data.total_deals > 0:
            deal_close_rate = (deals_data.won_deals / deals_data.total_deals) * 100
        
        return {
            "total_leads": leads_data.total_leads or 0,
            "qualified_leads": leads_data.qualified_leads or 0,
            "won_leads": leads_data.won_leads or 0,
            "lost_leads": leads_data.lost_leads or 0,
            "avg_lead_score": round(leads_data.avg_lead_score or 0, 1),
            "total_deals": deals_data.total_deals or 0,
            "won_deals": deals_data.won_deals or 0,
            "lost_deals": deals_data.lost_deals or 0,
            "total_revenue": deals_data.total_revenue or 0,
            "avg_deal_value": round(deals_data.avg_deal_value or 0, 2),
            "lead_to_deal_rate": round(lead_to_deal_rate, 1),
            "deal_close_rate": round(deal_close_rate, 1),
            "source_breakdown": source_breakdown,
            "period": "last_30_days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")

@router.get("/forecast")
async def get_sales_forecast(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    period: str = "30_days"
):
    """Get sales forecast"""
    try:
        forecasting_service = SalesForecastingService()
        
        # Get forecast data
        forecast_data = await forecasting_service.generate_forecast(
            user_id=current_user.id,
            period=period,
            db=db
        )
        
        return {
            "period": period,
            "forecasted_revenue": forecast_data.get("forecasted_revenue", 0),
            "forecasted_deals": forecast_data.get("forecasted_deals", 0),
            "confidence_score": forecast_data.get("confidence_score", 0),
            "trend": forecast_data.get("trend", "stable"),
            "key_factors": forecast_data.get("key_factors", []),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate forecast: {str(e)}")

@router.get("/performance")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Eric's performance metrics"""
    try:
        analytics_service = PerformanceAnalyticsService()
        
        # Get performance data for the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        performance_data = await analytics_service.get_performance_metrics(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            db=db
        )
        
        return {
            "leads_generated": performance_data.get("leads_generated", 0),
            "deals_created": performance_data.get("deals_created", 0),
            "emails_sent": performance_data.get("emails_sent", 0),
            "conversations_handled": performance_data.get("conversations_handled", 0),
            "conversion_rate": performance_data.get("conversion_rate", 0),
            "response_time": performance_data.get("response_time", 0),
            "period": "last_7_days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance metrics: {str(e)}")

@router.post("/chatbot/message")
async def send_chatbot_message(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message to Eric's sales chatbot"""
    try:
        # Enforce per-agent pause/automation guard
        core_db = await get_core_db()
        async with core_db.get_session() as core_session:
            res = await core_session.execute(
                select(UserSelectedAgent).where(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == "eric",
                )
            )
            row = res.scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=403, detail="Agent Eric is not selected")
            if row.status == "paused":
                raise HTTPException(status_code=403, detail="Agent Eric is paused")
        from ..services.conversational_ai_service import ConversationalAIService
        
        conversational_ai = ConversationalAIService()
        await conversational_ai.initialize()
        
        message = request.get("message", "")
        context = request.get("context", {})
        
        # Process the message through Eric's conversational AI
        response = await conversational_ai.process_message(
            user_id=current_user.id,
            message=message,
            context=context,
            db=db
        )
        
        return {
            "success": True,
            "response": response.get("response", "I'm here to help with your sales needs! How can I assist you today?"),
            "suggestions": response.get("suggestions", []),
            "lead_created": response.get("lead_created", False),
            "lead_id": response.get("lead_id"),
            "next_actions": response.get("next_actions", []),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.get("/health")
async def eric_health_check():
    """Health check for Eric services"""
    return {
        "status": "healthy",
        "agent": "Eric",
        "version": "1.0.0",
        "services": [
            "lead_generation",
            "sales_outreach",
            "conversational_ai",
            "sales_forecasting",
            "deal_closing",
            "performance_analytics",
            "crm_automation",
            "predictive_analytics"
        ],
        "timestamp": datetime.now().isoformat()
    }
