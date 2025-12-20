from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from core.authentication.auth_manager import get_current_user
from core.database.models import User
from ..database import get_db
from ..models import SocialAccount, AnalyticsSnapshot, ScheduledPost, PublishedPost
from ..services.analytics_service import AnalyticsService
from ..services.content_service import ContentService

router = APIRouter(prefix="/aria", tags=["Aria Dashboard"])

@router.get("/accounts")
async def get_social_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's connected social media accounts"""
    try:
        # Query social accounts for the user
        accounts = await db.execute(
            "SELECT * FROM social_accounts WHERE user_id = :user_id AND is_active = true",
            {"user_id": current_user.id}
        )
        accounts_data = accounts.fetchall()
        
        # Format the response
        formatted_accounts = []
        for account in accounts_data:
            formatted_accounts.append({
                "id": account.id,
                "platform": account.platform.value,
                "handle": account.handle,
                "followers": 0,  # This would come from platform API
                "is_connected": account.is_active,
                "last_sync": account.updated_at.isoformat() if account.updated_at else "Never"
            })
        
        return formatted_accounts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch social accounts: {str(e)}")

@router.get("/analytics/summary")
async def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics summary for the user"""
    try:
        analytics_service = AnalyticsService()
        
        # Get analytics data for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Query analytics snapshots
        snapshots = await db.execute(
            "SELECT * FROM analytics_snapshots WHERE user_id = :user_id AND snapshot_at >= :start_date",
            {"user_id": current_user.id, "start_date": start_date}
        )
        snapshots_data = snapshots.fetchall()
        
        # Calculate summary metrics
        total_reach = sum(snapshot.impressions for snapshot in snapshots_data)
        total_engagement = sum(
            snapshot.likes + snapshot.comments + snapshot.shares 
            for snapshot in snapshots_data
        )
        engagement_rate = (total_engagement / total_reach * 100) if total_reach > 0 else 0
        
        # Get platform breakdown
        platform_breakdown = {}
        for snapshot in snapshots_data:
            platform = snapshot.platform.value
            if platform not in platform_breakdown:
                platform_breakdown[platform] = 0
            platform_breakdown[platform] += snapshot.impressions
        
        # Calculate percentages
        total_platform_reach = sum(platform_breakdown.values())
        if total_platform_reach > 0:
            platform_breakdown = {
                platform: round((reach / total_platform_reach) * 100, 1)
                for platform, reach in platform_breakdown.items()
            }
        
        return {
            "total_reach": total_reach,
            "engagement_rate": round(engagement_rate, 1),
            "new_followers": 156,  # This would come from platform API
            "platform_breakdown": platform_breakdown,
            "period": "last_30_days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")

@router.get("/posts/recent")
async def get_recent_posts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 10
):
    """Get recent posts for the user"""
    try:
        # Query recent scheduled and published posts
        posts = await db.execute(
            """
            SELECT sp.*, pp.platform, pp.published_at, pp.status as publish_status
            FROM scheduled_posts sp
            LEFT JOIN published_posts pp ON sp.id = pp.scheduled_post_id
            WHERE sp.user_id = :user_id
            ORDER BY sp.created_at DESC
            LIMIT :limit
            """,
            {"user_id": current_user.id, "limit": limit}
        )
        posts_data = posts.fetchall()
        
        # Format the response
        formatted_posts = []
        for post in posts_data:
            # Get engagement data from analytics
            engagement_data = await db.execute(
                """
                SELECT SUM(impressions) as reach, SUM(likes) as likes, 
                       SUM(comments) as comments, SUM(shares) as shares
                FROM analytics_snapshots 
                WHERE user_id = :user_id AND post_ref = :post_ref
                """,
                {"user_id": current_user.id, "post_ref": f"post_{post.id}"}
            )
            engagement = engagement_data.fetchone()
            
            formatted_posts.append({
                "id": post.id,
                "content": post.caption or "No content",
                "platform": post.platform_targets[0] if post.platform_targets else "Unknown",
                "scheduled_at": post.scheduled_at.isoformat(),
                "status": post.status.value,
                "engagement": {
                    "likes": engagement.likes or 0,
                    "comments": engagement.comments or 0,
                    "shares": engagement.shares or 0,
                    "reach": engagement.reach or 0
                }
            })
        
        return formatted_posts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent posts: {str(e)}")

@router.get("/health")
async def aria_health_check():
    """Health check for Aria services"""
    return {
        "status": "healthy",
        "agent": "Aria",
        "version": "1.0.0",
        "services": [
            "social_media_management",
            "ai_content_creation",
            "smart_scheduling",
            "trend_monitoring",
            "analytics",
            "chat_interface"
        ],
        "timestamp": datetime.now().isoformat()
    }

@router.post("/content/generate")
async def generate_content(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate content using Aria's AI"""
    try:
        content_service = ContentService()
        await content_service.initialize()
        
        # Generate content based on request
        content_type = request.get("type", "post")
        topic = request.get("topic", "")
        tone = request.get("tone", "professional")
        
        if content_type == "post":
            result = await content_service.generate_caption(
                current_user.id, 
                {"topic": topic, "tone": tone}
            )
        elif content_type == "hashtags":
            result = await content_service.suggest_hashtags(
                current_user.id, 
                topic, 
                10
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported content type")
        
        return {
            "success": True,
            "content": result,
            "type": content_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")

@router.get("/trends")
async def get_trending_topics(
    current_user: User = Depends(get_current_user),
    platform: Optional[str] = None,
    region: str = "global"
):
    """Get trending topics for content inspiration"""
    try:
        # This would integrate with trend monitoring services
        trending_topics = [
            {
                "topic": "AI Productivity",
                "trend_score": 85,
                "platform": "LinkedIn",
                "growth": "+23%"
            },
            {
                "topic": "Remote Work Tips",
                "trend_score": 72,
                "platform": "Twitter",
                "growth": "+15%"
            },
            {
                "topic": "Sustainability",
                "trend_score": 68,
                "platform": "Instagram",
                "growth": "+8%"
            }
        ]
        
        # Filter by platform if specified
        if platform:
            trending_topics = [t for t in trending_topics if t["platform"].lower() == platform.lower()]
        
        return {
            "success": True,
            "trends": trending_topics,
            "region": region,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trends: {str(e)}")
