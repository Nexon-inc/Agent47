from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from core.authentication.auth_manager import get_current_user
from core.database.connection import get_supabase
from core.database.models import UserSelectedAgent
from sqlalchemy import select
from core.database.models import User
from ..database import get_db
from ..models import PurityBusinessIdea, PurityBusinessModel, PurityMarketResearch, PurityCustomerAvatar, BusinessStage, ValidationStatus, IndustryType
from ..services.business_idea_generator_service import BusinessIdeaGeneratorService
from ..services.business_health_service import BusinessHealthService
from ..services.financial_planning_service import FinancialPlanningService

router = APIRouter(prefix="/purity", tags=["Purity Dashboard"])

@router.get("/business-ideas")
async def get_business_ideas(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = 50
):
    """Get business ideas for the user/organization"""
    try:
        # Query business ideas
        query = "SELECT * FROM business_ideas WHERE user_id = :user_id"
        params = {"user_id": current_user.id}
        
        if status:
            query += " AND status = :status"
            params["status"] = status
            
        if industry:
            query += " AND industry = :industry"
            params["industry"] = industry
            
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        ideas = await db.execute(query, params)
        ideas_data = ideas.fetchall()
        
        # Format the response
        formatted_ideas = []
        for idea in ideas_data:
            formatted_ideas.append({
                "id": idea.id,
                "title": idea.title,
                "description": idea.description,
                "industry": idea.industry.value,
                "target_market": idea.target_market,
                "unique_value_proposition": idea.unique_value_proposition,
                "revenue_potential": idea.revenue_potential,
                "startup_cost": idea.startup_cost,
                "time_to_market": idea.time_to_market,
                "competition_level": idea.competition_level,
                "market_size": idea.market_size,
                "validation_score": idea.validation_score,
                "status": idea.status.value,
                "tags": idea.tags or [],
                "created_at": idea.created_at.isoformat(),
                "updated_at": idea.updated_at.isoformat() if idea.updated_at else None
            })
        
        return formatted_ideas
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch business ideas: {str(e)}")

@router.get("/business-models")
async def get_business_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    idea_id: Optional[int] = None,
    limit: int = 50
):
    """Get business models for the user/organization"""
    try:
        # Query business models
        query = """
        SELECT bm.*, bi.title as idea_title 
        FROM business_models bm
        JOIN business_ideas bi ON bm.idea_id = bi.id
        WHERE bi.user_id = :user_id
        """
        params = {"user_id": current_user.id}
        
        if idea_id:
            query += " AND bm.idea_id = :idea_id"
            params["idea_id"] = idea_id
            
        query += " ORDER BY bm.created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        models = await db.execute(query, params)
        models_data = models.fetchall()
        
        # Format the response
        formatted_models = []
        for model in models_data:
            formatted_models.append({
                "id": model.id,
                "idea_id": model.idea_id,
                "idea_title": model.idea_title,
                "key_partners": model.key_partners or [],
                "key_activities": model.key_activities or [],
                "key_resources": model.key_resources or [],
                "value_propositions": model.value_propositions or [],
                "customer_relationships": model.customer_relationships or [],
                "channels": model.channels or [],
                "customer_segments": model.customer_segments or [],
                "cost_structure": model.cost_structure or [],
                "revenue_streams": model.revenue_streams or [],
                "revenue_model": model.revenue_model.value if model.revenue_model else None,
                "pricing_strategy": model.pricing_strategy,
                "competitive_advantage": model.competitive_advantage,
                "scalability_factors": model.scalability_factors or [],
                "risk_factors": model.risk_factors or [],
                "created_at": model.created_at.isoformat(),
                "updated_at": model.updated_at.isoformat() if model.updated_at else None
            })
        
        return formatted_models
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch business models: {str(e)}")

@router.get("/analytics/summary")
async def get_business_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get business analytics summary"""
    try:
        # Get analytics for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Query business ideas statistics
        ideas_query = """
        SELECT 
            COUNT(*) as total_ideas,
            COUNT(CASE WHEN status = 'validated' THEN 1 END) as validated_ideas,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_ideas,
            AVG(validation_score) as avg_validation_score,
            AVG(revenue_potential) as avg_revenue_potential,
            AVG(startup_cost) as avg_startup_cost
        FROM business_ideas 
        WHERE user_id = :user_id AND created_at >= :start_date
        """
        
        ideas_stats = await db.execute(ideas_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        ideas_data = ideas_stats.fetchone()
        
        # Query business models statistics
        models_query = """
        SELECT 
            COUNT(*) as total_models,
            COUNT(DISTINCT revenue_model) as revenue_models_used
        FROM business_models bm
        JOIN business_ideas bi ON bm.idea_id = bi.id
        WHERE bi.user_id = :user_id AND bm.created_at >= :start_date
        """
        
        models_stats = await db.execute(models_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        models_data = models_stats.fetchone()
        
        # Get industry breakdown
        industry_query = """
        SELECT industry, COUNT(*) as count
        FROM business_ideas 
        WHERE user_id = :user_id AND created_at >= :start_date
        GROUP BY industry
        """
        
        industries = await db.execute(industry_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        industry_data = industries.fetchall()
        
        industry_breakdown = {row.industry.value: row.count for row in industry_data}
        
        # Get top performing ideas
        top_ideas_query = """
        SELECT title, validation_score, revenue_potential, industry
        FROM business_ideas 
        WHERE user_id = :user_id AND created_at >= :start_date
        ORDER BY validation_score DESC
        LIMIT 5
        """
        
        top_ideas = await db.execute(top_ideas_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        top_ideas_data = top_ideas.fetchall()
        
        top_ideas_list = [
            {
                "title": row.title,
                "validation_score": row.validation_score,
                "revenue_potential": row.revenue_potential,
                "industry": row.industry.value
            }
            for row in top_ideas_data
        ]
        
        return {
            "business_ideas": {
                "total_ideas": ideas_data.total_ideas or 0,
                "validated_ideas": ideas_data.validated_ideas or 0,
                "pending_ideas": ideas_data.pending_ideas or 0,
                "avg_validation_score": round(ideas_data.avg_validation_score or 0, 2),
                "avg_revenue_potential": round(ideas_data.avg_revenue_potential or 0, 2),
                "avg_startup_cost": round(ideas_data.avg_startup_cost or 0, 2)
            },
            "business_models": {
                "total_models": models_data.total_models or 0,
                "revenue_models_used": models_data.revenue_models_used or 0
            },
            "industry_breakdown": industry_breakdown,
            "top_ideas": top_ideas_list,
            "period": "last_30_days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")

@router.get("/performance")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Purity's performance metrics"""
    try:
        # Get performance data for the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Query business creation performance
        performance_query = """
        SELECT 
            COUNT(*) as total_business_activities,
            COUNT(CASE WHEN created_at >= :start_date THEN 1 END) as recent_activities,
            COUNT(DISTINCT DATE(created_at)) as active_days
        FROM (
            SELECT created_at FROM business_ideas WHERE user_id = :user_id
            UNION ALL
            SELECT created_at FROM business_models WHERE idea_id IN (
                SELECT id FROM business_ideas WHERE user_id = :user_id
            )
        ) as all_activities
        """
        
        performance_stats = await db.execute(performance_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        performance_data = performance_stats.fetchone()
        
        return {
            "total_business_activities": performance_data.total_business_activities or 0,
            "recent_activities": performance_data.recent_activities or 0,
            "active_days": performance_data.active_days or 0,
            "business_creation_efficiency": round((performance_data.recent_activities or 0) / 7, 1),
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
    """Send a message to Purity's business creation chatbot"""
    try:
        # Enforce per-agent pause/automation guard
        core_db = await get_supabase()
        async with core_db.get_session() as core_session:
            res = await core_session.execute(
                select(UserSelectedAgent).where(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == "purity",
                )
            )
            row = res.scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=403, detail="Agent Purity is not selected")
            if row.status == "paused":
                raise HTTPException(status_code=403, detail="Agent Purity is paused")
        from ..services.business_mentor_service import BusinessMentorService
        
        mentor_service = BusinessMentorService()
        await mentor_service.initialize()
        
        message = request.get("message", "")
        context = request.get("context", {})
        
        # Process the message through Purity's business mentor AI
        response = await mentor_service.process_mentor_query(
            user_id=current_user.id,
            query=message,
            context=context,
            db=db
        )
        
        return {
            "success": True,
            "response": response.get("response", "I'm here to help you create and grow your business! How can I assist you today?"),
            "suggestions": response.get("suggestions", []),
            "business_idea_created": response.get("business_idea_created", False),
            "idea_id": response.get("idea_id"),
            "next_actions": response.get("next_actions", []),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.get("/health")
async def purity_health_check():
    """Health check for Purity services"""
    return {
        "status": "healthy",
        "agent": "Purity",
        "version": "1.0.0",
        "services": [
            "business_idea_generator",
            "market_research",
            "financial_planning",
            "brand_building",
            "launch_strategy",
            "investment_pitch"
        ],
        "timestamp": datetime.now().isoformat()
    }
