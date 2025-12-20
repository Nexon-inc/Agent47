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
from ..models import ContentProject, ContentPiece, ContentType, ContentStatus, PlatformType, SEOStatus
from ..services.ai_generation_service import AIGenerationService
from ..services.content_analytics_service import ContentAnalyticsService
from ..services.seo_optimization_service import SEOOptimizationService

router = APIRouter(prefix="/shakes", tags=["Shakes Dashboard"])

@router.get("/content-projects")
async def get_content_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    content_type: Optional[str] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """Get content projects for the user/organization"""
    try:
        # Query content projects
        query = "SELECT * FROM content_projects WHERE user_id = :user_id"
        params = {"user_id": current_user.id}
        
        if content_type:
            query += " AND content_type = :content_type"
            params["content_type"] = content_type
            
        if platform:
            query += " AND platform = :platform"
            params["platform"] = platform
            
        if status:
            query += " AND status = :status"
            params["status"] = status
            
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        projects = await db.execute(query, params)
        projects_data = projects.fetchall()
        
        # Format the response
        formatted_projects = []
        for project in projects_data:
            formatted_projects.append({
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "content_type": project.content_type.value,
                "platform": project.platform.value,
                "target_audience": project.target_audience,
                "brand_voice": project.brand_voice,
                "tone": project.tone.value,
                "keywords": project.keywords or [],
                "seo_status": project.seo_status.value,
                "status": project.status.value,
                "word_count_target": project.word_count_target,
                "deadline": project.deadline.isoformat() if project.deadline else None,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                "published_at": project.published_at.isoformat() if project.published_at else None
            })
        
        return formatted_projects
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch content projects: {str(e)}")

@router.get("/content-pieces")
async def get_content_pieces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    project_id: Optional[int] = None,
    content_type: Optional[str] = None,
    limit: int = 50
):
    """Get content pieces for the user/organization"""
    try:
        # Query content pieces
        query = """
        SELECT cp.*, cproj.title as project_title 
        FROM content_pieces cp
        JOIN content_projects cproj ON cp.project_id = cproj.id
        WHERE cproj.user_id = :user_id
        """
        params = {"user_id": current_user.id}
        
        if project_id:
            query += " AND cp.project_id = :project_id"
            params["project_id"] = project_id
            
        if content_type:
            query += " AND cp.content_type = :content_type"
            params["content_type"] = content_type
            
        query += " ORDER BY cp.created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        pieces = await db.execute(query, params)
        pieces_data = pieces.fetchall()
        
        # Format the response
        formatted_pieces = []
        for piece in pieces_data:
            formatted_pieces.append({
                "id": piece.id,
                "project_id": piece.project_id,
                "project_title": piece.project_title,
                "title": piece.title,
                "content": piece.content,
                "content_type": piece.content_type.value,
                "platform": piece.platform.value,
                "word_count": piece.word_count,
                "character_count": piece.character_count,
                "reading_time": piece.reading_time,
                "status": piece.status.value,
                "seo_score": piece.seo_score,
                "readability_score": piece.readability_score,
                "sentiment_score": piece.sentiment_score,
                "created_at": piece.created_at.isoformat(),
                "updated_at": piece.updated_at.isoformat() if piece.updated_at else None,
                "published_at": piece.published_at.isoformat() if piece.published_at else None
            })
        
        return formatted_pieces
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch content pieces: {str(e)}")

@router.get("/analytics/summary")
async def get_content_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get content analytics summary"""
    try:
        # Get analytics for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Query content projects statistics
        projects_query = """
        SELECT 
            COUNT(*) as total_projects,
            COUNT(CASE WHEN status = 'published' THEN 1 END) as published_projects,
            COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_projects,
            COUNT(CASE WHEN seo_status = 'fully_optimized' THEN 1 END) as seo_optimized_projects,
            AVG(word_count_target) as avg_word_count_target
        FROM content_projects 
        WHERE user_id = :user_id AND created_at >= :start_date
        """
        
        projects_stats = await db.execute(projects_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        projects_data = projects_stats.fetchone()
        
        # Query content pieces statistics
        pieces_query = """
        SELECT 
            COUNT(*) as total_pieces,
            COUNT(CASE WHEN status = 'published' THEN 1 END) as published_pieces,
            AVG(seo_score) as avg_seo_score,
            AVG(readability_score) as avg_readability_score,
            AVG(sentiment_score) as avg_sentiment_score,
            SUM(word_count) as total_words_written
        FROM content_pieces cp
        JOIN content_projects cproj ON cp.project_id = cproj.id
        WHERE cproj.user_id = :user_id AND cp.created_at >= :start_date
        """
        
        pieces_stats = await db.execute(pieces_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        pieces_data = pieces_stats.fetchone()
        
        # Get content type breakdown
        type_query = """
        SELECT content_type, COUNT(*) as count
        FROM content_projects 
        WHERE user_id = :user_id AND created_at >= :start_date
        GROUP BY content_type
        """
        
        types = await db.execute(type_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        type_data = types.fetchall()
        
        type_breakdown = {row.content_type.value: row.count for row in type_data}
        
        # Get platform breakdown
        platform_query = """
        SELECT platform, COUNT(*) as count
        FROM content_projects 
        WHERE user_id = :user_id AND created_at >= :start_date
        GROUP BY platform
        """
        
        platforms = await db.execute(platform_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        platform_data = platforms.fetchall()
        
        platform_breakdown = {row.platform.value: row.count for row in platform_data}
        
        # Get top performing content
        top_content_query = """
        SELECT cp.title, cp.seo_score, cp.readability_score, cproj.content_type
        FROM content_pieces cp
        JOIN content_projects cproj ON cp.project_id = cproj.id
        WHERE cproj.user_id = :user_id AND cp.created_at >= :start_date
        ORDER BY cp.seo_score DESC
        LIMIT 5
        """
        
        top_content = await db.execute(top_content_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        top_content_data = top_content.fetchall()
        
        top_content_list = [
            {
                "title": row.title,
                "seo_score": row.seo_score,
                "readability_score": row.readability_score,
                "content_type": row.content_type.value
            }
            for row in top_content_data
        ]
        
        return {
            "content_projects": {
                "total_projects": projects_data.total_projects or 0,
                "published_projects": projects_data.published_projects or 0,
                "draft_projects": projects_data.draft_projects or 0,
                "seo_optimized_projects": projects_data.seo_optimized_projects or 0,
                "avg_word_count_target": round(projects_data.avg_word_count_target or 0, 0)
            },
            "content_pieces": {
                "total_pieces": pieces_data.total_pieces or 0,
                "published_pieces": pieces_data.published_pieces or 0,
                "avg_seo_score": round(pieces_data.avg_seo_score or 0, 1),
                "avg_readability_score": round(pieces_data.avg_readability_score or 0, 1),
                "avg_sentiment_score": round(pieces_data.avg_sentiment_score or 0, 2),
                "total_words_written": pieces_data.total_words_written or 0
            },
            "type_breakdown": type_breakdown,
            "platform_breakdown": platform_breakdown,
            "top_content": top_content_list,
            "period": "last_30_days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")

@router.get("/performance")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Shakes' performance metrics"""
    try:
        # Get performance data for the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Query content creation performance
        performance_query = """
        SELECT 
            COUNT(*) as total_content_activities,
            COUNT(CASE WHEN created_at >= :start_date THEN 1 END) as recent_activities,
            COUNT(DISTINCT DATE(created_at)) as active_days
        FROM (
            SELECT created_at FROM content_projects WHERE user_id = :user_id
            UNION ALL
            SELECT created_at FROM content_pieces WHERE project_id IN (
                SELECT id FROM content_projects WHERE user_id = :user_id
            )
        ) as all_activities
        """
        
        performance_stats = await db.execute(performance_query, {
            "user_id": current_user.id,
            "start_date": start_date
        })
        performance_data = performance_stats.fetchone()
        
        return {
            "total_content_activities": performance_data.total_content_activities or 0,
            "recent_activities": performance_data.recent_activities or 0,
            "active_days": performance_data.active_days or 0,
            "content_creation_efficiency": round((performance_data.recent_activities or 0) / 7, 1),
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
    """Send a message to Shakes' content creation chatbot"""
    try:
        # Enforce per-agent pause/automation guard
        core_db = await get_supabase()
        async with core_db.get_session() as core_session:
            res = await core_session.execute(
                select(UserSelectedAgent).where(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == "shakes",
                )
            )
            row = res.scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=403, detail="Agent Shakes is not selected")
            if row.status == "paused":
                raise HTTPException(status_code=403, detail="Agent Shakes is paused")
        from ..services.ai_generation_service import AIGenerationService
        
        ai_service = AIGenerationService()
        await ai_service.initialize()
        
        message = request.get("message", "")
        context = request.get("context", {})
        
        # Process the message through Shakes' AI generation
        response = await ai_service.generate_content(
            user_id=current_user.id,
            prompt=message,
            context=context,
            db=db
        )
        
        return {
            "success": True,
            "response": response.get("response", "I'm here to help you create amazing content! How can I assist you today?"),
            "suggestions": response.get("suggestions", []),
            "content_created": response.get("content_created", False),
            "content_id": response.get("content_id"),
            "next_actions": response.get("next_actions", []),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.get("/health")
async def shakes_health_check():
    """Health check for Shakes services"""
    return {
        "status": "healthy",
        "agent": "Shakes",
        "version": "1.0.0",
        "services": [
            "blog_writing",
            "social_media_content",
            "seo_optimization",
            "video_scripting",
            "ad_copywriting",
            "content_analytics"
        ],
        "timestamp": datetime.now().isoformat()
    }
