import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.core.utils.nlp_utils import NLPUtils
from backend.core.cache.redis_manager import init_redis
from ..database import get_jackie_database
from ..models import CrossChannelAnalytics, UnifiedMetrics, ChannelComparison, PerformanceInsight

logger = logging.getLogger(__name__)

class CrossChannelAnalyticsService:
    def __init__(self):
        self.db = None
        self.nlp_processor = None
        self.redis_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize cross-channel analytics service"""
        if self._initialized:
            return
        
        try:
            self.db = await get_jackie_database()
            self.nlp_processor = NLPUtils()
            await self.nlp_processor.initialize()
            self.redis_client = await init_redis()
            self._initialized = True
            logger.info("Cross-channel analytics service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize cross-channel analytics service: {e}")
            raise
    
    async def unify_channel_metrics(self, campaign_id: str, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Unify metrics from multiple channels into a comprehensive analytics view"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                unified_id = str(uuid.uuid4())
                
                prompt = f"""
                Campaign ID: {campaign_id}
                Channel Data: {channel_data}
                
                Unify metrics from multiple channels into a comprehensive analytics view.
                """
                
                unified_result = await self.nlp_processor.unify_channel_metrics(prompt)
                
                unified = UnifiedMetrics(
                    id=unified_id, campaign_id=campaign_id, channel_data=json.dumps(channel_data),
                    unified_data=json.dumps(unified_result), created_at=datetime.utcnow()
                )
                session.add(unified)
                await session.commit()
                
                return {"unified_id": unified_id, "unified_data": unified_result}
        except Exception as e:
            logger.error(f"Failed to unify channel metrics: {e}")
            raise
    
    async def compare_channel_performance(self, channels: List[str], comparison_metrics: List[str]) -> Dict[str, Any]:
        """Compare performance across different marketing channels"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                comparison_id = str(uuid.uuid4())
                
                prompt = f"""
                Channels: {channels}
                Comparison Metrics: {comparison_metrics}
                
                Compare performance across different marketing channels.
                """
                
                comparison_result = await self.nlp_processor.compare_channel_performance(prompt)
                
                comparison = ChannelComparison(
                    id=comparison_id, channels=json.dumps(channels), comparison_metrics=json.dumps(comparison_metrics),
                    comparison_data=json.dumps(comparison_result), created_at=datetime.utcnow()
                )
                session.add(comparison)
                await session.commit()
                
                return {"comparison_id": comparison_id, "comparison_data": comparison_result}
        except Exception as e:
            logger.error(f"Failed to compare channel performance: {e}")
            raise
    
    async def generate_performance_insights(self, analytics_data: Dict[str, Any], insight_focus: List[str]) -> Dict[str, Any]:
        """Generate actionable insights from cross-channel performance data"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                insight_id = str(uuid.uuid4())
                
                prompt = f"""
                Analytics Data: {analytics_data}
                Insight Focus: {insight_focus}
                
                Generate actionable insights from cross-channel performance data.
                """
                
                insight_result = await self.nlp_processor.generate_performance_insights(prompt)
                
                insight = PerformanceInsight(
                    id=insight_id, analytics_data=json.dumps(analytics_data), insight_focus=json.dumps(insight_focus),
                    insight_data=json.dumps(insight_result), created_at=datetime.utcnow()
                )
                session.add(insight)
                await session.commit()
                
                return {"insight_id": insight_id, "insight_data": insight_result}
        except Exception as e:
            logger.error(f"Failed to generate performance insights: {e}")
            raise
    
    async def get_cross_channel_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        """Get cross-channel analytics for specified timeframe"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
                
                metrics_unified_query = select(func.count(UnifiedMetrics.id)).where(UnifiedMetrics.created_at >= cutoff_date)
                comparisons_made_query = select(func.count(ChannelComparison.id)).where(ChannelComparison.created_at >= cutoff_date)
                insights_generated_query = select(func.count(PerformanceInsight.id)).where(PerformanceInsight.created_at >= cutoff_date)
                
                metrics_unified = await session.scalar(metrics_unified_query)
                comparisons_made = await session.scalar(comparisons_made_query)
                insights_generated = await session.scalar(insights_generated_query)
                
                return {
                    "timeframe": timeframe, "metrics_unified": metrics_unified,
                    "comparisons_made": comparisons_made, "insights_generated": insights_generated
                }
        except Exception as e:
            logger.error(f"Failed to get cross-channel analytics: {e}")
            raise
