from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.authentication.auth_manager import get_current_user
from backend.core.database.connection import get_supabase
from backend.core.database.models import UserSelectedAgent
from sqlalchemy import select
from backend.core.database.models import User
from ..database import get_db
from ..models import JoeMarketTrend, JoeCompetitorAnalysis, JoeSentimentAnalysis, KeywordResearch, ResearchType, ResearchStatus
from ..services.market_trend_analysis_service import MarketTrendAnalysisService
from ..services.competitor_analysis_service import CompetitorAnalysisService
from ..services.sentiment_tracking_service import SentimentTrackingService

router = APIRouter(prefix="/joe", tags=["Joe Dashboard"])

@router.get("/research")
async def get_research_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    research_type: Optional[str] = None,
    limit: int = 50
):
    """Get research data for the user/organization"""
    try:
        # Query market trends
        trends_query = "SELECT * FROM market_trends WHERE user_id = :user_id"
        params = {"user_id": current_user.id}
        
        if research_type:
            trends_query += " AND research_type = :research_type"
            params["research_type"] = research_type
            
        trends_query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        trends = await db.execute(trends_query, params)
        trends_data = trends.fetchall()
        
        # Query competitor analyses
        competitors_query = "SELECT * FROM competitor_analyses WHERE user_id = :user_id ORDER BY created_at DESC LIMIT :limit"
        competitors = await db.execute(competitors_query, {"user_id": current_user.id, "limit": limit})
        competitors_data = competitors.fetchall()
        
        # Query sentiment analyses
        sentiment_query = "SELECT * FROM sentiment_analyses WHERE user_id = :user_id ORDER BY created_at DESC LIMIT :limit"
        sentiment = await db.execute(sentiment_query, {"user_id": current_user.id, "limit": limit})
        sentiment_data = sentiment.fetchall()
        
        # Query keyword research
        keywords_query = "SELECT * FROM keyword_research WHERE user_id = :user_id ORDER BY created_at DESC LIMIT :limit"
        keywords = await db.execute(keywords_query, {"user_id": current_user.id, "limit": limit})
        keywords_data = keywords.fetchall()
        
        # Format the response
        formatted_data = {
            "market_trends": [],
            "competitor_analyses": [],
            "sentiment_analyses": [],
            "keyword_research": []
        }
        
        for trend in trends_data:
            formatted_data["market_trends"].append({
                "id": trend.id,
                "keyword": trend.keyword,
                "region": trend.region,
                "time_period": trend.time_period,
                "trend_data": trend.trend_data,
                "insights": trend.insights,
                "created_at": trend.created_at.isoformat(),
                "updated_at": trend.updated_at.isoformat() if trend.updated_at else None
            })
        
        for competitor in competitors_data:
            formatted_data["competitor_analyses"].append({
                "id": competitor.id,
                "competitor_name": competitor.competitor_name,
                "competitor_url": competitor.competitor_url,
                "analysis_type": competitor.analysis_type,
                "analysis_data": competitor.analysis_data,
                "insights": competitor.insights,
                "created_at": competitor.created_at.isoformat(),
                "updated_at": competitor.updated_at.isoformat() if competitor.updated_at else None
            })
        
        for sentiment in sentiment_data:
            formatted_data["sentiment_analyses"].append({
                "id": sentiment.id,
                "brand_name": sentiment.brand_name,
                "platform": sentiment.platform,
                "sentiment_data": sentiment.sentiment_data,
                "overall_sentiment": sentiment.overall_sentiment,
                "volume": sentiment.volume,
                "created_at": sentiment.created_at.isoformat(),
                "updated_at": sentiment.updated_at.isoformat() if sentiment.updated_at else None
            })
        
        for keyword in keywords_data:
            formatted_data["keyword_research"].append({
                "id": keyword.id,
                "keyword": keyword.keyword,
                "search_volume": keyword.search_volume,
                "competition": keyword.competition,
                "cpc": keyword.cpc,
                "trend_data": keyword.trend_data,
                "related_keywords": keyword.related_keywords,
                "created_at": keyword.created_at.isoformat(),
                "updated_at": keyword.updated_at.isoformat() if keyword.updated_at else None
            })
        
        return formatted_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch research data: {str(e)}")

@router.get("/analytics/summary")
async def get_research_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get research analytics summary"""
    try:
        # Get analytics for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Query market trends statistics
        trends_query = """
        SELECT 
            COUNT(*) as total_trends,
            COUNT(DISTINCT keyword) as unique_keywords,
            COUNT(DISTINCT region) as regions_analyzed
        FROM market_trends 
        WHERE user_id = :user_id AND created_at >= :start_date
        """
        
        trends_stats = await db.execute(trends_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        trends_data = trends_stats.fetchone()
        
        # Query competitor analysis statistics
        competitors_query = """
        SELECT 
            COUNT(*) as total_analyses,
            COUNT(DISTINCT competitor_name) as unique_competitors,
            COUNT(DISTINCT analysis_type) as analysis_types
        FROM competitor_analyses 
        WHERE user_id = :user_id AND created_at >= :start_date
        """
        
        competitors_stats = await db.execute(competitors_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        competitors_data = competitors_stats.fetchone()
        
        # Query sentiment analysis statistics
        sentiment_query = """
        SELECT 
            COUNT(*) as total_analyses,
            AVG(overall_sentiment) as avg_sentiment,
            SUM(volume) as total_volume,
            COUNT(DISTINCT platform) as platforms_monitored
        FROM sentiment_analyses 
        WHERE user_id = :user_id AND created_at >= :start_date
        """
        
        sentiment_stats = await db.execute(sentiment_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        sentiment_data = sentiment_stats.fetchone()
        
        # Query keyword research statistics
        keywords_query = """
        SELECT 
            COUNT(*) as total_keywords,
            AVG(search_volume) as avg_search_volume,
            AVG(competition) as avg_competition,
            AVG(cpc) as avg_cpc
        FROM keyword_research 
        WHERE user_id = :user_id AND created_at >= :start_date
        """
        
        keywords_stats = await db.execute(keywords_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        keywords_data = keywords_stats.fetchone()
        
        # Get top performing keywords
        top_keywords_query = """
        SELECT keyword, search_volume, competition
        FROM keyword_research 
        WHERE user_id = :user_id AND created_at >= :start_date
        ORDER BY search_volume DESC
        LIMIT 5
        """
        
        top_keywords = await db.execute(top_keywords_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        top_keywords_data = top_keywords.fetchall()
        
        top_keywords_list = [
            {
                "keyword": row.keyword,
                "search_volume": row.search_volume,
                "competition": row.competition
            }
            for row in top_keywords_data
        ]
        
        return {
            "market_trends": {
                "total_trends": trends_data.total_trends or 0,
                "unique_keywords": trends_data.unique_keywords or 0,
                "regions_analyzed": trends_data.regions_analyzed or 0
            },
            "competitor_analyses": {
                "total_analyses": competitors_data.total_analyses or 0,
                "unique_competitors": competitors_data.unique_competitors or 0,
                "analysis_types": competitors_data.analysis_types or 0
            },
            "sentiment_analyses": {
                "total_analyses": sentiment_data.total_analyses or 0,
                "avg_sentiment": round(sentiment_data.avg_sentiment or 0, 2),
                "total_volume": sentiment_data.total_volume or 0,
                "platforms_monitored": sentiment_data.platforms_monitored or 0
            },
            "keyword_research": {
                "total_keywords": keywords_data.total_keywords or 0,
                "avg_search_volume": round(keywords_data.avg_search_volume or 0, 0),
                "avg_competition": round(keywords_data.avg_competition or 0, 2),
                "avg_cpc": round(keywords_data.avg_cpc or 0, 2)
            },
            "top_keywords": top_keywords_list,
            "period": "last_30_days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")

@router.get("/performance")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Joe's performance metrics"""
    try:
        # Get performance data for the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Query research performance
        performance_query = """
        SELECT 
            COUNT(*) as total_research_tasks,
            COUNT(CASE WHEN created_at >= :start_date THEN 1 END) as recent_tasks,
            COUNT(DISTINCT DATE(created_at)) as active_days
        FROM (
            SELECT created_at FROM market_trends WHERE user_id = :user_id
            UNION ALL
            SELECT created_at FROM competitor_analyses WHERE user_id = :user_id
            UNION ALL
            SELECT created_at FROM sentiment_analyses WHERE user_id = :user_id
            UNION ALL
            SELECT created_at FROM keyword_research WHERE user_id = :user_id
        ) as all_research
        """
        
        performance_stats = await db.execute(performance_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        performance_data = performance_stats.fetchone()
        
        return {
            "total_research_tasks": performance_data.total_research_tasks or 0,
            "recent_tasks": performance_data.recent_tasks or 0,
            "active_days": performance_data.active_days or 0,
            "research_efficiency": round((performance_data.recent_tasks or 0) / 7, 1),
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
    """Send a message to Joe's research chatbot"""
    try:
        # Enforce per-agent pause/automation guard
        core_db = await get_supabase()
        async with core_db.get_session() as core_session:
            res = await core_session.execute(
                select(UserSelectedAgent).where(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == "joe",
                )
            )
            row = res.scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=403, detail="Agent Joe is not selected")
            if row.status == "paused":
                raise HTTPException(status_code=403, detail="Agent Joe is paused")
        from ..services.voice_queries_service import VoiceQueriesService
        
        voice_service = VoiceQueriesService()
        await voice_service.initialize()
        
        message = request.get("message", "")
        context = request.get("context", {})
        
        # Process the message through Joe's research AI
        response = await voice_service.process_voice_query(
            user_id=current_user.id,
            query=message,
            context=context,
            db=db
        )
        
        return {
            "success": True,
            "response": response.get("response", "I'm here to help with your research needs! How can I assist you today?"),
            "suggestions": response.get("suggestions", []),
            "research_created": response.get("research_created", False),
            "research_id": response.get("research_id"),
            "next_actions": response.get("next_actions", []),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.get("/health")
async def joe_health_check():
    """Health check for Joe services"""
    return {
        "status": "healthy",
        "agent": "Joe",
        "version": "1.0.0",
        "services": [
            "market_trend_analysis",
            "competitor_analysis",
            "sentiment_tracking",
            "keyword_research",
            "data_visualization",
            "research_automation"
        ],
        "timestamp": datetime.now().isoformat()
    }
