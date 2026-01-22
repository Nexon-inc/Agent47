import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from datetime import datetime, timedelta
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ShakesContentProject, ShakesContentPiece, ContentAnalytics

logger = logging.getLogger(__name__)

class ContentAnalyticsService:
    """Service for content analytics and performance tracking"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 3000,
            "temperature": 0.4
        }
    
    async def initialize(self):
        """Initialize content analytics service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Content analytics service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize content analytics service: {e}")
            raise
    
    async def track_content_performance(
        self,
        content_piece_id: int,
        platform: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track content performance metrics"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Create or update analytics record
                analytics_result = await session.execute(
                    select(ContentAnalytics).where(
                        and_(
                            ContentAnalytics.content_piece_id == content_piece_id,
                            ContentAnalytics.platform == platform
                        )
                    )
                )
                analytics = analytics_result.scalar_one_or_none()
                
                if analytics:
                    # Update existing analytics
                    analytics.views = metrics.get("views", analytics.views)
                    analytics.likes = metrics.get("likes", analytics.likes)
                    analytics.shares = metrics.get("shares", analytics.shares)
                    analytics.comments = metrics.get("comments", analytics.comments)
                    analytics.clicks = metrics.get("clicks", analytics.clicks)
                    analytics.engagement_rate = metrics.get("engagement_rate", analytics.engagement_rate)
                    analytics.reach = metrics.get("reach", analytics.reach)
                    analytics.impressions = metrics.get("impressions", analytics.impressions)
                    analytics.updated_at = datetime.utcnow()
                else:
                    # Create new analytics record
                    analytics = ContentAnalytics(
                        content_piece_id=content_piece_id,
                        platform=platform,
                        views=metrics.get("views", 0),
                        likes=metrics.get("likes", 0),
                        shares=metrics.get("shares", 0),
                        comments=metrics.get("comments", 0),
                        clicks=metrics.get("clicks", 0),
                        engagement_rate=metrics.get("engagement_rate", 0.0),
                        reach=metrics.get("reach", 0),
                        impressions=metrics.get("impressions", 0)
                    )
                    session.add(analytics)
                
                await session.flush()
                
                # Generate performance analysis
                analysis_prompt = self._create_performance_analysis_prompt(
                    content_piece, platform, metrics
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that analyzes content performance. Respond in JSON format."}, {"role": "user", "content": analysis_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=3000, temperature=0.4)
                performance_analysis = ai_response.text_content if ai_response.success else ""
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.content_performance_tracked", {
                    "content_piece_id": content_piece_id,
                    "platform": platform,
                    "analytics_id": analytics.id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "analytics_id": analytics.id,
                    "content_piece_id": content_piece_id,
                    "platform": platform,
                    "metrics": metrics,
                    "performance_analysis": performance_analysis,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content performance tracking failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_content_analytics(
        self,
        content_piece_id: int,
        platform: str = None
    ) -> Dict[str, Any]:
        """Get analytics for specific content piece"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Build query
                query = select(ContentAnalytics).where(ContentAnalytics.content_piece_id == content_piece_id)
                if platform:
                    query = query.where(ContentAnalytics.platform == platform)
                
                analytics_result = await session.execute(query)
                analytics_records = analytics_result.scalars().all()
                
                if not analytics_records:
                    return {"success": False, "error": "No analytics found for this content piece"}
                
                # Format analytics data
                analytics_data = []
                for analytics in analytics_records:
                    analytics_data.append({
                        "analytics_id": analytics.id,
                        "platform": analytics.platform,
                        "views": analytics.views,
                        "likes": analytics.likes,
                        "shares": analytics.shares,
                        "comments": analytics.comments,
                        "clicks": analytics.clicks,
                        "engagement_rate": analytics.engagement_rate,
                        "reach": analytics.reach,
                        "impressions": analytics.impressions,
                        "created_at": analytics.created_at.isoformat(),
                        "updated_at": analytics.updated_at.isoformat()
                    })
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "analytics_data": analytics_data,
                    "total_platforms": len(analytics_data),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content analytics retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_performance_summary(
        self,
        user_id: int,
        date_range_days: int = 30,
        platform: str = None
    ) -> Dict[str, Any]:
        """Get performance summary for user's content"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Calculate date range
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=date_range_days)
                
                # Get content pieces for user
                content_query = select(ShakesContentPiece).join(ShakesContentProject).where(
                    and_(
                        ShakesContentProject.user_id == user_id,
                        ShakesContentPiece.created_at >= start_date,
                        ShakesContentPiece.created_at <= end_date
                    )
                )
                content_result = await session.execute(content_query)
                content_pieces = content_result.scalars().all()
                
                if not content_pieces:
                    return {"success": False, "error": "No content found for the specified period"}
                
                content_piece_ids = [piece.id for piece in content_pieces]
                
                # Get analytics for content pieces
                analytics_query = select(ContentAnalytics).where(
                    ContentAnalytics.content_piece_id.in_(content_piece_ids)
                )
                if platform:
                    analytics_query = analytics_query.where(ContentAnalytics.platform == platform)
                
                analytics_result = await session.execute(analytics_query)
                analytics_records = analytics_result.scalars().all()
                
                # Calculate summary metrics
                total_views = sum(analytics.views for analytics in analytics_records)
                total_likes = sum(analytics.likes for analytics in analytics_records)
                total_shares = sum(analytics.shares for analytics in analytics_records)
                total_comments = sum(analytics.comments for analytics in analytics_records)
                total_clicks = sum(analytics.clicks for analytics in analytics_records)
                total_reach = sum(analytics.reach for analytics in analytics_records)
                total_impressions = sum(analytics.impressions for analytics in analytics_records)
                
                avg_engagement_rate = sum(analytics.engagement_rate for analytics in analytics_records) / len(analytics_records) if analytics_records else 0
                
                # Generate performance insights
                insights_prompt = self._create_performance_insights_prompt(
                    user_id, date_range_days, platform, total_views, total_likes, total_shares,
                    total_comments, total_clicks, avg_engagement_rate, total_reach, total_impressions
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that provides content performance insights."}, {"role": "user", "content": insights_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.4)
                performance_insights = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "date_range_days": date_range_days,
                    "platform": platform,
                    "summary_metrics": {
                        "total_content_pieces": len(content_pieces),
                        "total_views": total_views,
                        "total_likes": total_likes,
                        "total_shares": total_shares,
                        "total_comments": total_comments,
                        "total_clicks": total_clicks,
                        "total_reach": total_reach,
                        "total_impressions": total_impressions,
                        "average_engagement_rate": round(avg_engagement_rate, 3)
                    },
                    "performance_insights": performance_insights,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Performance summary retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def compare_content_performance(
        self,
        content_piece_ids: List[int],
        comparison_metrics: List[str]
    ) -> Dict[str, Any]:
        """Compare performance of multiple content pieces"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content pieces
                content_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id.in_(content_piece_ids))
                )
                content_pieces = content_result.scalars().all()
                
                if not content_pieces:
                    return {"success": False, "error": "No content pieces found"}
                
                # Get analytics for content pieces
                analytics_result = await session.execute(
                    select(ContentAnalytics).where(ContentAnalytics.content_piece_id.in_(content_piece_ids))
                )
                analytics_records = analytics_result.scalars().all()
                
                # Group analytics by content piece
                content_analytics = {}
                for analytics in analytics_records:
                    if analytics.content_piece_id not in content_analytics:
                        content_analytics[analytics.content_piece_id] = []
                    content_analytics[analytics.content_piece_id].append(analytics)
                
                # Format comparison data
                comparison_data = []
                for content_piece in content_pieces:
                    analytics_list = content_analytics.get(content_piece.id, [])
                    
                    # Aggregate metrics across platforms
                    total_views = sum(analytics.views for analytics in analytics_list)
                    total_likes = sum(analytics.likes for analytics in analytics_list)
                    total_shares = sum(analytics.shares for analytics in analytics_list)
                    total_comments = sum(analytics.comments for analytics in analytics_list)
                    total_clicks = sum(analytics.clicks for analytics in analytics_list)
                    avg_engagement_rate = sum(analytics.engagement_rate for analytics in analytics_list) / len(analytics_list) if analytics_list else 0
                    
                    comparison_data.append({
                        "content_piece_id": content_piece.id,
                        "title": content_piece.title,
                        "content_type": content_piece.content_type,
                        "platform": content_piece.platform,
                        "metrics": {
                            "views": total_views,
                            "likes": total_likes,
                            "shares": total_shares,
                            "comments": total_comments,
                            "clicks": total_clicks,
                            "engagement_rate": round(avg_engagement_rate, 3)
                        },
                        "created_at": content_piece.created_at.isoformat()
                    })
                
                # Generate comparison analysis
                comparison_prompt = self._create_comparison_analysis_prompt(
                    comparison_data, comparison_metrics
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that compares content performance."}, {"role": "user", "content": comparison_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.4)
                comparison_analysis = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "content_piece_ids": content_piece_ids,
                    "comparison_metrics": comparison_metrics,
                    "comparison_data": comparison_data,
                    "comparison_analysis": comparison_analysis,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content performance comparison failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_performance_analysis_prompt(
        self, content_piece: ShakesContentPiece, platform: str, metrics: Dict[str, Any]
    ) -> str:
        """Create prompt for performance analysis"""
        return f"""
        Analyze the performance of this content piece:
        
        Content Title: {content_piece.title}
        Content Type: {content_piece.content_type}
        Platform: {platform}
        Metrics: {metrics}
        
        Provide:
        1. Performance assessment
        2. Key strengths and weaknesses
        3. Engagement analysis
        4. Platform-specific insights
        5. Improvement recommendations
        6. Benchmark comparisons
        
        Format as comprehensive performance analysis.
        """
    
    def _create_performance_insights_prompt(
        self, user_id: int, date_range_days: int, platform: str, total_views: int,
        total_likes: int, total_shares: int, total_comments: int, total_clicks: int,
        avg_engagement_rate: float, total_reach: int, total_impressions: int
    ) -> str:
        """Create prompt for performance insights"""
        return f"""
        Generate performance insights for user {user_id}:
        
        Date Range: {date_range_days} days
        Platform: {platform or 'All platforms'}
        
        Performance Metrics:
        - Total Views: {total_views}
        - Total Likes: {total_likes}
        - Total Shares: {total_shares}
        - Total Comments: {total_comments}
        - Total Clicks: {total_clicks}
        - Average Engagement Rate: {avg_engagement_rate:.3f}
        - Total Reach: {total_reach}
        - Total Impressions: {total_impressions}
        
        Provide:
        1. Overall performance assessment
        2. Key trends and patterns
        3. Top performing content insights
        4. Engagement analysis
        5. Growth opportunities
        6. Actionable recommendations
        
        Format as comprehensive performance insights.
        """
    
    def _create_comparison_analysis_prompt(
        self, comparison_data: List[Dict[str, Any]], comparison_metrics: List[str]
    ) -> str:
        """Create prompt for comparison analysis"""
        return f"""
        Compare the performance of these content pieces:
        
        Content Pieces: {len(comparison_data)} pieces
        Comparison Metrics: {', '.join(comparison_metrics)}
        
        Content Data:
        {self._format_comparison_data(comparison_data)}
        
        Provide:
        1. Performance comparison analysis
        2. Top and bottom performers
        3. Key differences and patterns
        4. Content type and platform insights
        5. Recommendations for improvement
        6. Best practices identification
        
        Format as comprehensive comparison analysis.
        """
    
    def _format_comparison_data(self, comparison_data: List[Dict[str, Any]]) -> str:
        """Format comparison data for analysis"""
        formatted_data = []
        for item in comparison_data:
            formatted_data.append(f"- {item['title']} ({item['content_type']} on {item['platform']}): {item['metrics']}")
        return "\n".join(formatted_data)
