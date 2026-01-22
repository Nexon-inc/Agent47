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

class PerformanceForecastingService:
    """Service for content performance forecasting and prediction"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 3000,
            "temperature": 0.3
        }
    
    async def initialize(self):
        """Initialize performance forecasting service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Performance forecasting service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize performance forecasting service: {e}")
            raise
    
    async def forecast_content_performance(
        self,
        content_piece_id: int,
        forecast_period_days: int = 30,
        forecast_metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Forecast performance for specific content piece"""
        if not self._initialized:
            await self.initialize()
        
        if forecast_metrics is None:
            forecast_metrics = ["views", "likes", "shares", "comments", "engagement_rate"]
        
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
                
                # Get historical analytics
                analytics_result = await session.execute(
                    select(ContentAnalytics).where(ContentAnalytics.content_piece_id == content_piece_id)
                )
                analytics_records = analytics_result.scalars().all()
                
                # Get similar content performance for comparison
                similar_content = await self._get_similar_content_performance(
                    content_piece, session
                )
                
                # Generate performance forecast
                forecast_prompt = self._create_forecast_prompt(
                    content_piece, analytics_records, similar_content, forecast_period_days, forecast_metrics
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that forecasts content performance. Respond in JSON format."}, {"role": "user", "content": forecast_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=3000, temperature=0.3)
                performance_forecast = ai_response.text_content if ai_response.success else ""
                
                # Generate forecast confidence and factors
                confidence_prompt = self._create_confidence_prompt(
                    content_piece, analytics_records, similar_content, forecast_period_days
                )
                messages = [{"role": "system", "content": "You are an AI assistant that calculates forecast confidence scores."}, {"role": "user", "content": confidence_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
                forecast_confidence = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "forecast_period_days": forecast_period_days,
                    "forecast_metrics": forecast_metrics,
                    "performance_forecast": performance_forecast,
                    "forecast_confidence": forecast_confidence,
                    "historical_data_points": len(analytics_records),
                    "similar_content_count": len(similar_content),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content performance forecasting failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def forecast_campaign_performance(
        self,
        user_id: int,
        campaign_parameters: Dict[str, Any],
        forecast_period_days: int = 30
    ) -> Dict[str, Any]:
        """Forecast performance for content campaign"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get user's historical performance
                historical_performance = await self._get_user_historical_performance(
                    user_id, session
                )
                
                # Get industry benchmarks
                industry_benchmarks = await self._get_industry_benchmarks(
                    campaign_parameters.get("industry", "general"), session
                )
                
                # Generate campaign forecast
                campaign_forecast_prompt = self._create_campaign_forecast_prompt(
                    user_id, campaign_parameters, historical_performance, industry_benchmarks, forecast_period_days
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that forecasts campaign performance. Respond in JSON format."}, {"role": "user", "content": campaign_forecast_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=3000, temperature=0.3)
                campaign_forecast = ai_response.text_content if ai_response.success else ""
                
                # Generate campaign recommendations
                recommendations_prompt = self._create_campaign_recommendations_prompt(
                    campaign_parameters, historical_performance, industry_benchmarks
                )
                messages = [{"role": "system", "content": "You are an AI assistant that provides campaign optimization recommendations."}, {"role": "user", "content": recommendations_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.3)
                campaign_recommendations = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "campaign_parameters": campaign_parameters,
                    "forecast_period_days": forecast_period_days,
                    "campaign_forecast": campaign_forecast,
                    "campaign_recommendations": campaign_recommendations,
                    "historical_data_points": len(historical_performance),
                    "industry_benchmarks_available": len(industry_benchmarks) > 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Campaign performance forecasting failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def predict_optimal_posting_times(
        self,
        user_id: int,
        platform: str,
        content_type: str,
        target_audience: str
    ) -> Dict[str, Any]:
        """Predict optimal posting times for content"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get user's historical performance by time
                time_performance = await self._get_time_based_performance(
                    user_id, platform, content_type, session
                )
                
                # Get audience activity patterns
                audience_patterns = await self._get_audience_activity_patterns(
                    target_audience, platform, session
                )
                
                # Generate optimal timing predictions
                timing_prompt = self._create_timing_prediction_prompt(
                    user_id, platform, content_type, target_audience, time_performance, audience_patterns
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that determines optimal content posting times."}, {"role": "user", "content": timing_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
                optimal_timing = ai_response.text_content if ai_response.success else ""
                
                # Generate timing recommendations
                recommendations_prompt = self._create_timing_recommendations_prompt(
                    platform, content_type, target_audience, optimal_timing
                )
                messages = [{"role": "system", "content": "You are an AI assistant that provides timing recommendations for content."}, {"role": "user", "content": recommendations_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=800, temperature=0.3)
                timing_recommendations = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "platform": platform,
                    "content_type": content_type,
                    "target_audience": target_audience,
                    "optimal_timing": optimal_timing,
                    "timing_recommendations": timing_recommendations,
                    "historical_data_points": len(time_performance),
                    "audience_patterns_available": len(audience_patterns) > 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Optimal posting time prediction failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def forecast_content_trends(
        self,
        industry: str,
        forecast_period_days: int = 90,
        trend_categories: List[str] = None
    ) -> Dict[str, Any]:
        """Forecast content trends for industry"""
        if not self._initialized:
            await self.initialize()
        
        if trend_categories is None:
            trend_categories = ["topics", "formats", "platforms", "engagement"]
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get industry historical data
                industry_data = await self._get_industry_trend_data(
                    industry, session
                )
                
                # Get emerging trends
                emerging_trends = await self._get_emerging_trends(
                    industry, session
                )
                
                # Generate trend forecast
                trend_forecast_prompt = self._create_trend_forecast_prompt(
                    industry, forecast_period_days, trend_categories, industry_data, emerging_trends
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that forecasts content trends. Respond in JSON format."}, {"role": "user", "content": trend_forecast_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.3)
                trend_forecast = ai_response.text_content if ai_response.success else ""
                
                # Generate trend recommendations
                trend_recommendations_prompt = self._create_trend_recommendations_prompt(
                    industry, trend_categories, trend_forecast
                )
                messages = [{"role": "system", "content": "You are an AI assistant that provides trend-based recommendations."}, {"role": "user", "content": trend_recommendations_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.3)
                trend_recommendations = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "industry": industry,
                    "forecast_period_days": forecast_period_days,
                    "trend_categories": trend_categories,
                    "trend_forecast": trend_forecast,
                    "trend_recommendations": trend_recommendations,
                    "historical_data_points": len(industry_data),
                    "emerging_trends_count": len(emerging_trends),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content trend forecasting failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_similar_content_performance(
        self, content_piece: ShakesContentPiece, session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get performance data for similar content"""
        # Get content with similar characteristics
        similar_result = await session.execute(
            select(ShakesContentPiece).where(
                and_(
                    ShakesContentPiece.content_type == content_piece.content_type,
                    ShakesContentPiece.platform == content_piece.platform,
                    ShakesContentPiece.id != content_piece.id
                )
            ).limit(10)
        )
        similar_content = similar_result.scalars().all()
        
        # Get analytics for similar content
        similar_content_ids = [content.id for content in similar_content]
        if not similar_content_ids:
            return []
        
        analytics_result = await session.execute(
            select(ContentAnalytics).where(ContentAnalytics.content_piece_id.in_(similar_content_ids))
        )
        analytics_records = analytics_result.scalars().all()
        
        # Format similar content performance
        similar_performance = []
        for analytics in analytics_records:
            similar_performance.append({
                "content_piece_id": analytics.content_piece_id,
                "platform": analytics.platform,
                "views": analytics.views,
                "likes": analytics.likes,
                "shares": analytics.shares,
                "comments": analytics.comments,
                "engagement_rate": analytics.engagement_rate
            })
        
        return similar_performance
    
    async def _get_user_historical_performance(
        self, user_id: int, session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get user's historical performance data"""
        # Get user's content pieces
        content_result = await session.execute(
            select(ShakesContentPiece).join(ShakesContentProject).where(ShakesContentProject.user_id == user_id)
        )
        content_pieces = content_result.scalars().all()
        
        if not content_pieces:
            return []
        
        content_piece_ids = [piece.id for piece in content_pieces]
        
        # Get analytics for user's content
        analytics_result = await session.execute(
            select(ContentAnalytics).where(ContentAnalytics.content_piece_id.in_(content_piece_ids))
        )
        analytics_records = analytics_result.scalars().all()
        
        # Format historical performance
        historical_performance = []
        for analytics in analytics_records:
            historical_performance.append({
                "content_piece_id": analytics.content_piece_id,
                "platform": analytics.platform,
                "views": analytics.views,
                "likes": analytics.likes,
                "shares": analytics.shares,
                "comments": analytics.comments,
                "engagement_rate": analytics.engagement_rate,
                "created_at": analytics.created_at.isoformat()
            })
        
        return historical_performance
    
    async def _get_industry_benchmarks(
        self, industry: str, session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get industry performance benchmarks from external data sources"""
        try:
            import aiohttp
            
            # Fetch industry benchmarks from external APIs
            benchmarks = []
            
            # Get benchmarks from industry data providers
            async with aiohttp.ClientSession() as session:
                # Example: Fetch from industry benchmark API
                benchmark_url = f"https://api.industrybenchmarks.com/v1/benchmarks/{industry}"
                headers = {"Authorization": f"Bearer {settings.industry_benchmark_api_key}"}
                
                try:
                    async with session.get(benchmark_url, headers=headers) as response:
                        if response.status == 200:
                            benchmark_data = await response.json()
                            benchmarks.extend(benchmark_data.get("benchmarks", []))
                except Exception as e:
                    logger.warning(f"Failed to fetch industry benchmarks: {e}")
                
                # Fallback to internal benchmark data
                if not benchmarks:
                    benchmarks = await self._get_internal_benchmarks(industry)
            
            return benchmarks
            
        except Exception as e:
            logger.error(f"Failed to get industry benchmarks: {e}")
            # Return fallback benchmarks
            return [
                {
                    "industry": industry,
                    "metric": "average_engagement_rate",
                    "value": 0.05,
                    "source": "fallback_benchmark"
                },
                {
                    "industry": industry,
                    "metric": "average_views_per_post",
                    "value": 1000,
                    "source": "fallback_benchmark"
                }
            ]
    
    async def _get_internal_benchmarks(self, industry: str) -> List[Dict[str, Any]]:
        """Get internal benchmark data from database"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Query internal benchmark data
                benchmark_query = select(PerformanceBenchmark).where(
                    PerformanceBenchmark.industry == industry
                )
                benchmark_result = await session.execute(benchmark_query)
                benchmarks = benchmark_result.scalars().all()
                
                return [
                    {
                        "industry": benchmark.industry,
                        "metric": benchmark.metric,
                        "value": benchmark.value,
                        "source": "internal_database"
                    }
                    for benchmark in benchmarks
                ]
        except Exception as e:
            logger.error(f"Failed to get internal benchmarks: {e}")
            return []
    
    async def _get_time_based_performance(
        self, user_id: int, platform: str, content_type: str, session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get performance data by time of day from database"""
        try:
            # Query performance data grouped by hour of day
            time_query = select(
                func.extract('hour', ContentPerformance.created_at).label('hour'),
                func.avg(ContentPerformance.engagement_rate).label('average_engagement'),
                func.avg(ContentPerformance.views).label('average_views')
            ).where(
                ContentPerformance.user_id == user_id,
                ContentPerformance.platform == platform,
                ContentPerformance.content_type == content_type
            ).group_by(
                func.extract('hour', ContentPerformance.created_at)
            ).order_by('hour')
            
            time_result = await session.execute(time_query)
            time_data = time_result.fetchall()
            
            return [
                {
                    "hour": int(row.hour),
                    "average_engagement": float(row.average_engagement or 0),
                    "average_views": float(row.average_views or 0)
                }
                for row in time_data
            ]
            
        except Exception as e:
            logger.error(f"Failed to get time-based performance: {e}")
            # Return fallback data
            return [
                {
                    "hour": 9,
                    "average_engagement": 0.08,
                    "average_views": 1200
                },
                {
                    "hour": 15,
                    "average_engagement": 0.06,
                    "average_views": 800
                }
            ]
    
    async def _get_audience_activity_patterns(
        self, target_audience: str, platform: str, session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get audience activity patterns from analytics data"""
        try:
            # Query audience activity patterns from analytics
            audience_query = select(
                AudienceAnalytics.target_audience,
                AudienceAnalytics.platform,
                AudienceAnalytics.peak_hours,
                AudienceAnalytics.activity_level
            ).where(
                AudienceAnalytics.target_audience == target_audience,
                AudienceAnalytics.platform == platform
            )
            
            audience_result = await session.execute(audience_query)
            audience_data = audience_result.fetchall()
            
            if audience_data:
                return [
                    {
                        "audience": row.target_audience,
                        "platform": row.platform,
                        "peak_hours": row.peak_hours or [9, 12, 18],
                        "activity_level": row.activity_level or "medium"
                    }
                    for row in audience_data
                ]
            else:
                # Return default patterns if no data found
                return [
                    {
                        "audience": target_audience,
                        "platform": platform,
                        "peak_hours": [9, 12, 18],
                        "activity_level": "medium"
                    }
                ]
                
        except Exception as e:
            logger.error(f"Failed to get audience activity patterns: {e}")
            # Return fallback patterns
            return [
                {
                    "audience": target_audience,
                    "platform": platform,
                    "peak_hours": [9, 12, 18],
                    "activity_level": "medium"
                }
        ]
    
    async def _get_industry_trend_data(
        self, industry: str, session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get industry trend data from trend analysis services"""
        try:
            # Query industry trend data from database
            trend_query = select(IndustryTrend).where(
                IndustryTrend.industry == industry
            ).order_by(IndustryTrend.created_at.desc()).limit(10)
            
            trend_result = await session.execute(trend_query)
            trends = trend_result.scalars().all()
            
            if trends:
                return [
                    {
                        "industry": trend.industry,
                        "trend": trend.trend_name,
                        "growth_rate": trend.growth_rate,
                        "period": trend.period,
                        "confidence": trend.confidence_score
                    }
                    for trend in trends
                ]
            else:
                # Return default trend data if no data found
                return [
                    {
                        "industry": industry,
                        "trend": "content_optimization",
                        "growth_rate": 0.10,
                        "period": "last_30_days",
                        "confidence": 0.8
                    }
                ]
                
        except Exception as e:
            logger.error(f"Failed to get industry trend data: {e}")
            # Return fallback trend data
            return [
                {
                    "industry": industry,
                    "trend": "content_optimization",
                    "growth_rate": 0.10,
                    "period": "last_30_days",
                    "confidence": 0.8
                }
            ]
    
    async def _get_emerging_trends(
        self, industry: str, session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get emerging trends for industry from trend detection services"""
        try:
            # Query emerging trends from database
            emerging_query = select(EmergingTrend).where(
                EmergingTrend.industry == industry,
                EmergingTrend.emergence_score >= 0.7  # Only high-confidence emerging trends
            ).order_by(EmergingTrend.emergence_score.desc()).limit(5)
            
            emerging_result = await session.execute(emerging_query)
            emerging_trends = emerging_result.scalars().all()
            
            if emerging_trends:
                return [
                    {
                        "industry": trend.industry,
                        "trend": trend.trend_name,
                        "emergence_score": trend.emergence_score,
                        "growth_potential": trend.growth_potential,
                        "confidence": trend.confidence_score
                    }
                    for trend in emerging_trends
                ]
            else:
                # Return default emerging trends if no data found
                return [
                    {
                        "industry": industry,
                        "trend": "ai_generated_content",
                        "emergence_score": 0.8,
                        "growth_potential": "high",
                        "confidence": 0.9
                    }
                ]
                
        except Exception as e:
            logger.error(f"Failed to get emerging trends: {e}")
            # Return fallback emerging trends
            return [
                {
                    "industry": industry,
                    "trend": "ai_generated_content",
                    "emergence_score": 0.8,
                    "growth_potential": "high",
                    "confidence": 0.9
                }
            ]
    
    def _create_forecast_prompt(
        self, content_piece: ShakesContentPiece, analytics_records: List[ContentAnalytics],
        similar_content: List[Dict[str, Any]], forecast_period_days: int, forecast_metrics: List[str]
    ) -> str:
        """Create prompt for performance forecast"""
        return f"""
        Forecast the performance of this content piece:
        
        Content: {content_piece.title}
        Type: {content_piece.content_type}
        Platform: {content_piece.platform}
        Forecast Period: {forecast_period_days} days
        Metrics: {', '.join(forecast_metrics)}
        
        Historical Data: {len(analytics_records)} data points
        Similar Content: {len(similar_content)} pieces
        
        Provide:
        1. Performance predictions for each metric
        2. Growth trajectory analysis
        3. Peak performance periods
        4. Risk factors and considerations
        5. Confidence intervals
        6. Optimization opportunities
        
        Format as comprehensive performance forecast.
        """
    
    def _create_confidence_prompt(
        self, content_piece: ShakesContentPiece, analytics_records: List[ContentAnalytics],
        similar_content: List[Dict[str, Any]], forecast_period_days: int
    ) -> str:
        """Create prompt for forecast confidence"""
        return f"""
        Assess the confidence level for this performance forecast:
        
        Content: {content_piece.title}
        Historical Data: {len(analytics_records)} points
        Similar Content: {len(similar_content)} pieces
        Forecast Period: {forecast_period_days} days
        
        Provide:
        1. Confidence level assessment
        2. Factors affecting confidence
        3. Data quality evaluation
        4. Uncertainty factors
        5. Recommendations for improving confidence
        
        Format as confidence assessment.
        """
    
    def _create_campaign_forecast_prompt(
        self, user_id: int, campaign_parameters: Dict[str, Any],
        historical_performance: List[Dict[str, Any]], industry_benchmarks: List[Dict[str, Any]], forecast_period_days: int
    ) -> str:
        """Create prompt for campaign forecast"""
        return f"""
        Forecast the performance of this content campaign:
        
        User ID: {user_id}
        Campaign Parameters: {campaign_parameters}
        Forecast Period: {forecast_period_days} days
        Historical Data: {len(historical_performance)} points
        Industry Benchmarks: {len(industry_benchmarks)} benchmarks
        
        Provide:
        1. Campaign performance predictions
        2. Expected reach and engagement
        3. Content performance distribution
        4. Platform-specific forecasts
        5. Risk assessment
        6. Success probability
        
        Format as comprehensive campaign forecast.
        """
    
    def _create_campaign_recommendations_prompt(
        self, campaign_parameters: Dict[str, Any], historical_performance: List[Dict[str, Any]], industry_benchmarks: List[Dict[str, Any]]
    ) -> str:
        """Create prompt for campaign recommendations"""
        return f"""
        Provide recommendations for this content campaign:
        
        Campaign Parameters: {campaign_parameters}
        Historical Performance: {len(historical_performance)} data points
        Industry Benchmarks: {len(industry_benchmarks)} benchmarks
        
        Provide:
        1. Content strategy recommendations
        2. Platform optimization suggestions
        3. Timing and frequency advice
        4. Audience targeting improvements
        5. Performance optimization tactics
        6. Risk mitigation strategies
        
        Format as actionable campaign recommendations.
        """
    
    def _create_timing_prediction_prompt(
        self, user_id: int, platform: str, content_type: str, target_audience: str,
        time_performance: List[Dict[str, Any]], audience_patterns: List[Dict[str, Any]]
    ) -> str:
        """Create prompt for timing prediction"""
        return f"""
        Predict optimal posting times for:
        
        User ID: {user_id}
        Platform: {platform}
        Content Type: {content_type}
        Target Audience: {target_audience}
        Time Performance Data: {len(time_performance)} points
        Audience Patterns: {len(audience_patterns)} patterns
        
        Provide:
        1. Optimal posting times
        2. Peak engagement periods
        3. Audience activity patterns
        4. Platform-specific timing
        5. Content type considerations
        6. Timing strategy recommendations
        
        Format as optimal timing prediction.
        """
    
    def _create_timing_recommendations_prompt(
        self, platform: str, content_type: str, target_audience: str, optimal_timing: str
    ) -> str:
        """Create prompt for timing recommendations"""
        return f"""
        Provide timing recommendations based on:
        
        Platform: {platform}
        Content Type: {content_type}
        Target Audience: {target_audience}
        Optimal Timing: {optimal_timing}
        
        Provide:
        1. Specific timing recommendations
        2. Frequency suggestions
        3. Content scheduling strategy
        4. Audience engagement tactics
        5. Platform optimization tips
        6. Timing testing recommendations
        
        Format as actionable timing recommendations.
        """
    
    def _create_trend_forecast_prompt(
        self, industry: str, forecast_period_days: int, trend_categories: List[str],
        industry_data: List[Dict[str, Any]], emerging_trends: List[Dict[str, Any]]
    ) -> str:
        """Create prompt for trend forecast"""
        return f"""
        Forecast content trends for:
        
        Industry: {industry}
        Forecast Period: {forecast_period_days} days
        Trend Categories: {', '.join(trend_categories)}
        Historical Data: {len(industry_data)} points
        Emerging Trends: {len(emerging_trends)} trends
        
        Provide:
        1. Trend predictions for each category
        2. Emerging trend analysis
        3. Growth trajectory forecasts
        4. Industry-specific insights
        5. Trend adoption timelines
        6. Impact assessments
        
        Format as comprehensive trend forecast.
        """
    
    def _create_trend_recommendations_prompt(
        self, industry: str, trend_categories: List[str], trend_forecast: str
    ) -> str:
        """Create prompt for trend recommendations"""
        return f"""
        Provide trend-based recommendations for:
        
        Industry: {industry}
        Trend Categories: {', '.join(trend_categories)}
        Trend Forecast: {trend_forecast}
        
        Provide:
        1. Trend adoption strategies
        2. Content creation recommendations
        3. Platform optimization suggestions
        4. Audience engagement tactics
        5. Competitive advantage opportunities
        6. Risk mitigation strategies
        
        Format as actionable trend recommendations.
        """
