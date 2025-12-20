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
from ..models import MarketingCampaign, CampaignContent, AdCampaign, CampaignStatus, CampaignType, PlatformType
from ..services.campaign_service import CampaignService
from ..services.analytics_service import AnalyticsService
from ..services.content_service import ContentService

router = APIRouter(prefix="/jackie", tags=["Jackie Dashboard"])

@router.get("/campaigns")
async def get_campaigns(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    campaign_type: Optional[str] = None,
    limit: int = 50
):
    """Get marketing campaigns for the user/organization"""
    try:
        # Query campaigns
        query = "SELECT * FROM marketing_campaigns WHERE user_id = :user_id"
        params = {"user_id": current_user.id}
        
        if status:
            query += " AND status = :status"
            params["status"] = status
            
        if campaign_type:
            query += " AND campaign_type = :campaign_type"
            params["campaign_type"] = campaign_type
            
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        campaigns = await db.execute(query, params)
        campaigns_data = campaigns.fetchall()
        
        # Format the response
        formatted_campaigns = []
        for campaign in campaigns_data:
            formatted_campaigns.append({
                "id": campaign.id,
                "campaign_id": campaign.campaign_id,
                "name": campaign.name,
                "description": campaign.description,
                "campaign_type": campaign.campaign_type.value,
                "status": campaign.status.value,
                "platforms": campaign.platforms or [],
                "budget": campaign.budget,
                "spent_budget": campaign.spent_budget,
                "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
                "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
                "goals": campaign.goals or {},
                "performance_metrics": campaign.performance_metrics or {},
                "created_at": campaign.created_at.isoformat(),
                "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None
            })
        
        return formatted_campaigns
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch campaigns: {str(e)}")

@router.get("/content")
async def get_content(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    campaign_id: Optional[int] = None,
    content_type: Optional[str] = None,
    limit: int = 50
):
    """Get campaign content for the user/organization"""
    try:
        # Query content
        query = """
        SELECT cc.*, mc.name as campaign_name 
        FROM campaign_contents cc
        JOIN marketing_campaigns mc ON cc.campaign_id = mc.id
        WHERE mc.user_id = :user_id
        """
        params = {"user_id": current_user.id}
        
        if campaign_id:
            query += " AND cc.campaign_id = :campaign_id"
            params["campaign_id"] = campaign_id
            
        if content_type:
            query += " AND cc.content_type = :content_type"
            params["content_type"] = content_type
            
        query += " ORDER BY cc.created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        content = await db.execute(query, params)
        content_data = content.fetchall()
        
        # Format the response
        formatted_content = []
        for item in content_data:
            formatted_content.append({
                "id": item.id,
                "campaign_id": item.campaign_id,
                "campaign_name": item.campaign_name,
                "content_type": item.content_type.value,
                "platform": item.platform.value,
                "title": item.title,
                "content": item.content,
                "media_urls": item.media_urls or [],
                "hashtags": item.hashtags or [],
                "scheduled_time": item.scheduled_time.isoformat() if item.scheduled_time else None,
                "published_time": item.published_time.isoformat() if item.published_time else None,
                "engagement_metrics": item.engagement_metrics or {},
                "ai_generated": item.ai_generated,
                "brand_voice_applied": item.brand_voice_applied,
                "created_at": item.created_at.isoformat()
            })
        
        return formatted_content
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch content: {str(e)}")

@router.get("/analytics/summary")
async def get_marketing_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get marketing analytics summary"""
    try:
        # Get analytics for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Query campaign statistics
        campaigns_query = """
        SELECT 
            COUNT(*) as total_campaigns,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active_campaigns,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_campaigns,
            SUM(budget) as total_budget,
            SUM(spent_budget) as total_spent,
            AVG(spent_budget / NULLIF(budget, 0)) as avg_budget_utilization
        FROM marketing_campaigns 
        WHERE user_id = :user_id AND created_at >= :start_date
        """
        
        campaigns_stats = await db.execute(campaigns_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        campaigns_data = campaigns_stats.fetchone()
        
        # Query content statistics
        content_query = """
        SELECT 
            COUNT(*) as total_content,
            COUNT(CASE WHEN published_time IS NOT NULL THEN 1 END) as published_content,
            COUNT(CASE WHEN ai_generated = true THEN 1 END) as ai_generated_content,
            AVG(JSON_EXTRACT(engagement_metrics, '$.engagement_rate')) as avg_engagement_rate
        FROM campaign_contents cc
        JOIN marketing_campaigns mc ON cc.campaign_id = mc.id
        WHERE mc.user_id = :user_id AND cc.created_at >= :start_date
        """
        
        content_stats = await db.execute(content_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        content_data = content_stats.fetchone()
        
        # Get platform breakdown
        platform_query = """
        SELECT platform, COUNT(*) as count
        FROM campaign_contents cc
        JOIN marketing_campaigns mc ON cc.campaign_id = mc.id
        WHERE mc.user_id = :user_id AND cc.created_at >= :start_date
        GROUP BY platform
        """
        
        platforms = await db.execute(platform_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        platform_data = platforms.fetchall()
        
        platform_breakdown = {row.platform.value: row.count for row in platform_data}
        
        # Get campaign type breakdown
        type_query = """
        SELECT campaign_type, COUNT(*) as count
        FROM marketing_campaigns 
        WHERE user_id = :user_id AND created_at >= :start_date
        GROUP BY campaign_type
        """
        
        types = await db.execute(type_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        type_data = types.fetchall()
        
        type_breakdown = {row.campaign_type.value: row.count for row in type_data}
        
        return {
            "total_campaigns": campaigns_data.total_campaigns or 0,
            "active_campaigns": campaigns_data.active_campaigns or 0,
            "completed_campaigns": campaigns_data.completed_campaigns or 0,
            "total_budget": campaigns_data.total_budget or 0,
            "total_spent": campaigns_data.total_spent or 0,
            "budget_utilization": round((campaigns_data.avg_budget_utilization or 0) * 100, 1),
            "total_content": content_data.total_content or 0,
            "published_content": content_data.published_content or 0,
            "ai_generated_content": content_data.ai_generated_content or 0,
            "avg_engagement_rate": round(content_data.avg_engagement_rate or 0, 2),
            "platform_breakdown": platform_breakdown,
            "type_breakdown": type_breakdown,
            "period": "last_30_days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")

@router.get("/performance")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Jackie's performance metrics"""
    try:
        analytics_service = AnalyticsService()
        
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
            "campaigns_created": performance_data.get("campaigns_created", 0),
            "content_generated": performance_data.get("content_generated", 0),
            "ads_optimized": performance_data.get("ads_optimized", 0),
            "engagement_rate": performance_data.get("engagement_rate", 0),
            "conversion_rate": performance_data.get("conversion_rate", 0),
            "roi": performance_data.get("roi", 0),
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
    """Send a message to Jackie's marketing chatbot"""
    try:
        # Enforce per-agent pause/automation guard
        core_db = await get_supabase()
        async with core_db.get_session() as core_session:
            res = await core_session.execute(
                select(UserSelectedAgent).where(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == "jackie",
                )
            )
            row = res.scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=403, detail="Agent Jackie is not selected")
            if row.status == "paused":
                raise HTTPException(status_code=403, detail="Agent Jackie is paused")
        from ..services.human_chatbot_service import HumanChatbotService
        
        chatbot_service = HumanChatbotService()
        await chatbot_service.initialize()
        
        message = request.get("message", "")
        context = request.get("context", {})
        
        # Process the message through Jackie's conversational AI
        response = await chatbot_service.process_message(
            user_id=current_user.id,
            message=message,
            context=context,
            db=db
        )
        
        return {
            "success": True,
            "response": response.get("response", "I'm here to help with your marketing needs! How can I assist you today?"),
            "suggestions": response.get("suggestions", []),
            "campaign_created": response.get("campaign_created", False),
            "campaign_id": response.get("campaign_id"),
            "next_actions": response.get("next_actions", []),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.get("/health")
async def jackie_health_check():
    """Health check for Jackie services"""
    return {
        "status": "healthy",
        "agent": "Jackie",
        "version": "1.0.0",
        "services": [
            "campaign_management",
            "content_creation",
            "social_media_marketing",
            "email_marketing",
            "ad_management",
            "analytics",
            "seo_optimization",
            "influencer_marketing"
        ],
        "timestamp": datetime.now().isoformat()
    }
