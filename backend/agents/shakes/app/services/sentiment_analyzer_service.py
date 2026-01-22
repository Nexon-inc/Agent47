import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ShakesContentProject, ShakesContentPiece

logger = logging.getLogger(__name__)

class SentimentAnalyzerService:
    """Service for content sentiment analysis and emotional impact assessment"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 2000,
            "temperature": 0.3
        }
    
    async def initialize(self):
        """Initialize sentiment analyzer service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Sentiment analyzer service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize sentiment analyzer service: {e}")
            raise
    
    async def analyze_content_sentiment(
        self,
        content_piece_id: int,
        analysis_depth: str = "comprehensive",
        sentiment_categories: List[str] = None
    ) -> Dict[str, Any]:
        """Analyze sentiment and emotional impact of content"""
        if not self._initialized:
            await self.initialize()
        
        if sentiment_categories is None:
            sentiment_categories = ["overall", "emotional_tone", "audience_impact", "brand_alignment"]
        
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
                
                # Perform sentiment analysis
                sentiment_analysis = await self._perform_sentiment_analysis(
                    content_piece, analysis_depth, sentiment_categories
                )
                
                # Generate sentiment insights
                insights_prompt = self._create_sentiment_insights_prompt(
                    content_piece, sentiment_analysis, sentiment_categories
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that analyzes content sentiment and provides insights."}, {"role": "user", "content": insights_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
                sentiment_insights = ai_response.text_content if ai_response.success else ""
                
                # Generate sentiment recommendations
                recommendations_prompt = self._create_sentiment_recommendations_prompt(
                    sentiment_analysis, sentiment_insights
                )
                messages = [{"role": "system", "content": "You are an AI assistant that provides sentiment-based recommendations."}, {"role": "user", "content": recommendations_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=800, temperature=0.3)
                sentiment_recommendations = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "analysis_depth": analysis_depth,
                    "sentiment_categories": sentiment_categories,
                    "sentiment_analysis": sentiment_analysis,
                    "sentiment_insights": sentiment_insights,
                    "sentiment_recommendations": sentiment_recommendations,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content sentiment analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_audience_sentiment(
        self,
        content_piece_id: int,
        audience_segments: List[str],
        sentiment_metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Analyze how different audience segments might perceive content"""
        if not self._initialized:
            await self.initialize()
        
        if sentiment_metrics is None:
            sentiment_metrics = ["emotional_response", "engagement_likelihood", "brand_perception", "action_intent"]
        
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
                
                # Analyze audience sentiment
                audience_sentiment = {}
                for segment in audience_segments:
                    segment_analysis = await self._analyze_audience_segment_sentiment(
                        content_piece, segment, sentiment_metrics
                    )
                    audience_sentiment[segment] = segment_analysis
                
                # Generate audience insights
                audience_insights = await self._generate_audience_insights(
                    audience_sentiment, audience_segments, sentiment_metrics
                )
                
                # Generate targeting recommendations
                targeting_recommendations = await self._generate_targeting_recommendations(
                    audience_sentiment, audience_insights
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "audience_segments": audience_segments,
                    "sentiment_metrics": sentiment_metrics,
                    "audience_sentiment": audience_sentiment,
                    "audience_insights": audience_insights,
                    "targeting_recommendations": targeting_recommendations,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Audience sentiment analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_content_sentiment(
        self,
        content_piece_id: int,
        target_sentiment: str,
        optimization_goals: List[str]
    ) -> Dict[str, Any]:
        """Optimize content sentiment for specific goals"""
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
                
                # Analyze current sentiment
                current_sentiment = await self._perform_sentiment_analysis(
                    content_piece, "comprehensive", ["overall", "emotional_tone"]
                )
                
                # Generate sentiment optimization
                sentiment_optimization = await self._generate_sentiment_optimization(
                    content_piece, current_sentiment, target_sentiment, optimization_goals
                )
                
                # Generate optimized content
                optimized_content = await self._generate_optimized_content(
                    content_piece, sentiment_optimization, target_sentiment
                )
                
                # Generate optimization report
                optimization_report = await self._generate_optimization_report(
                    current_sentiment, sentiment_optimization, optimized_content
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "target_sentiment": target_sentiment,
                    "optimization_goals": optimization_goals,
                    "current_sentiment": current_sentiment,
                    "sentiment_optimization": sentiment_optimization,
                    "optimized_content": optimized_content,
                    "optimization_report": optimization_report,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content sentiment optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_sentiment_trends(
        self,
        user_id: int,
        time_period_days: int = 30,
        trend_categories: List[str] = None
    ) -> Dict[str, Any]:
        """Analyze sentiment trends across user's content"""
        if not self._initialized:
            await self.initialize()
        
        if trend_categories is None:
            trend_categories = ["overall_sentiment", "emotional_tone", "audience_engagement", "brand_consistency"]
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get user's content
                from datetime import timedelta
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=time_period_days)
                
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
                    return {"success": False, "error": "No content found for trend analysis"}
                
                # Analyze sentiment trends
                sentiment_trends = await self._analyze_sentiment_trends(
                    content_pieces, trend_categories, time_period_days
                )
                
                # Generate trend insights
                trend_insights = await self._generate_trend_insights(
                    sentiment_trends, trend_categories, time_period_days
                )
                
                # Generate trend recommendations
                trend_recommendations = await self._generate_trend_recommendations(
                    sentiment_trends, trend_insights
                )
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "time_period_days": time_period_days,
                    "trend_categories": trend_categories,
                    "content_pieces_analyzed": len(content_pieces),
                    "sentiment_trends": sentiment_trends,
                    "trend_insights": trend_insights,
                    "trend_recommendations": trend_recommendations,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Sentiment trend analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _perform_sentiment_analysis(
        self, content_piece: ShakesContentPiece, analysis_depth: str, sentiment_categories: List[str]
    ) -> Dict[str, Any]:
        """Perform sentiment analysis on content"""
        analysis_prompt = self._create_sentiment_analysis_prompt(
            content_piece, analysis_depth, sentiment_categories
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that performs sentiment analysis. Respond in JSON format."}, {"role": "user", "content": analysis_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.3)
        analysis_result = ai_response.text_content if ai_response.success else ""
        
        # Parse analysis result into structured data
        sentiment_scores = self._extract_sentiment_scores(analysis_result)
        emotional_indicators = self._extract_emotional_indicators(analysis_result)
        
        return {
            "sentiment_scores": sentiment_scores,
            "emotional_indicators": emotional_indicators,
            "analysis_result": analysis_result,
            "analysis_depth": analysis_depth,
            "categories_analyzed": sentiment_categories
        }
    
    async def _analyze_audience_segment_sentiment(
        self, content_piece: ShakesContentPiece, segment: str, sentiment_metrics: List[str]
    ) -> Dict[str, Any]:
        """Analyze sentiment for specific audience segment"""
        segment_prompt = self._create_audience_segment_prompt(
            content_piece, segment, sentiment_metrics
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that analyzes sentiment for audience segments."}, {"role": "user", "content": segment_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
        segment_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "segment": segment,
            "sentiment_metrics": sentiment_metrics,
            "segment_analysis": segment_result,
            "emotional_response": self._extract_emotional_response(segment_result),
            "engagement_likelihood": self._extract_engagement_likelihood(segment_result)
        }
    
    async def _generate_audience_insights(
        self, audience_sentiment: Dict[str, Any], audience_segments: List[str], sentiment_metrics: List[str]
    ) -> str:
        """Generate audience insights"""
        insights_prompt = self._create_audience_insights_prompt(
            audience_sentiment, audience_segments, sentiment_metrics
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates audience sentiment insights."}, {"role": "user", "content": insights_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
        insights_result = ai_response.text_content if ai_response.success else ""
        return insights_result
    
    async def _generate_targeting_recommendations(
        self, audience_sentiment: Dict[str, Any], audience_insights: str
    ) -> List[Dict[str, Any]]:
        """Generate targeting recommendations"""
        recommendations_prompt = self._create_targeting_recommendations_prompt(
            audience_sentiment, audience_insights
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that provides sentiment-based recommendations."}, {"role": "user", "content": recommendations_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=800, temperature=0.3)
        recommendations_result = ai_response.text_content if ai_response.success else ""
        
        return [
            {
                "recommendation_type": "audience_targeting",
                "description": "Optimize content for specific audience segments",
                "priority": "high",
                "implementation": "medium"
            }
        ]
    
    async def _generate_sentiment_optimization(
        self, content_piece: ShakesContentPiece, current_sentiment: Dict[str, Any], target_sentiment: str, optimization_goals: List[str]
    ) -> Dict[str, Any]:
        """Generate sentiment optimization strategy"""
        optimization_prompt = self._create_sentiment_optimization_prompt(
            content_piece, current_sentiment, target_sentiment, optimization_goals
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that optimizes content based on sentiment analysis."}, {"role": "user", "content": optimization_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.3)
        optimization_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "target_sentiment": target_sentiment,
            "optimization_goals": optimization_goals,
            "optimization_strategy": optimization_result,
            "key_changes": [],
            "implementation_priority": "high"
        }
    
    async def _generate_optimized_content(
        self, content_piece: ShakesContentPiece, sentiment_optimization: Dict[str, Any], target_sentiment: str
    ) -> str:
        """Generate optimized content with target sentiment"""
        optimization_prompt = self._create_content_optimization_prompt(
            content_piece, sentiment_optimization, target_sentiment
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that optimizes content for better sentiment."}, {"role": "user", "content": optimization_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.3)
        optimized_result = ai_response.text_content if ai_response.success else ""
        return optimized_result
    
    async def _generate_optimization_report(
        self, current_sentiment: Dict[str, Any], sentiment_optimization: Dict[str, Any], optimized_content: str
    ) -> str:
        """Generate optimization report"""
        report_prompt = self._create_optimization_report_prompt(
            current_sentiment, sentiment_optimization, optimized_content
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates sentiment analysis reports."}, {"role": "user", "content": report_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.3)
        report_result = ai_response.text_content if ai_response.success else ""
        return report_result
    
    async def _analyze_sentiment_trends(
        self, content_pieces: List[ShakesContentPiece], trend_categories: List[str], time_period_days: int
    ) -> Dict[str, Any]:
        """Analyze sentiment trends across content pieces"""
        trends = {}
        
        for category in trend_categories:
            category_trends = []
            for piece in content_pieces:
                # Analyze sentiment for each piece
                sentiment_analysis = await self._perform_sentiment_analysis(
                    piece, "basic", [category]
                )
                category_trends.append({
                    "content_piece_id": piece.id,
                    "created_at": piece.created_at.isoformat(),
                    "sentiment_score": sentiment_analysis.get("sentiment_scores", {}).get(category, 0.5)
                })
            
            trends[category] = category_trends
        
        return trends
    
    async def _generate_trend_insights(
        self, sentiment_trends: Dict[str, Any], trend_categories: List[str], time_period_days: int
    ) -> str:
        """Generate trend insights"""
        insights_prompt = self._create_trend_insights_prompt(
            sentiment_trends, trend_categories, time_period_days
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates audience sentiment insights."}, {"role": "user", "content": insights_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
        insights_result = ai_response.text_content if ai_response.success else ""
        return insights_result
    
    async def _generate_trend_recommendations(
        self, sentiment_trends: Dict[str, Any], trend_insights: str
    ) -> List[Dict[str, Any]]:
        """Generate trend recommendations"""
        recommendations_prompt = self._create_trend_recommendations_prompt(
            sentiment_trends, trend_insights
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that provides sentiment-based recommendations."}, {"role": "user", "content": recommendations_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=800, temperature=0.3)
        recommendations_result = ai_response.text_content if ai_response.success else ""
        
        return [
            {
                "recommendation_type": "sentiment_consistency",
                "description": "Maintain consistent sentiment across content",
                "priority": "medium",
                "implementation": "easy"
            }
        ]
    
    def _extract_sentiment_scores(self, analysis_result: str) -> Dict[str, float]:
        """Extract sentiment scores from analysis result"""
        # Simple sentiment score extraction
        scores = {}
        if "positive" in analysis_result.lower():
            scores["positive"] = 0.8
        elif "negative" in analysis_result.lower():
            scores["negative"] = 0.8
        else:
            scores["neutral"] = 0.6
        
        scores["overall"] = scores.get("positive", 0.5)
        return scores
    
    def _extract_emotional_indicators(self, analysis_result: str) -> List[str]:
        """Extract emotional indicators from analysis result"""
        indicators = []
        if "excited" in analysis_result.lower():
            indicators.append("excitement")
        if "calm" in analysis_result.lower():
            indicators.append("calmness")
        if "urgent" in analysis_result.lower():
            indicators.append("urgency")
        if "friendly" in analysis_result.lower():
            indicators.append("friendliness")
        return indicators
    
    def _extract_emotional_response(self, segment_result: str) -> str:
        """Extract emotional response from segment analysis"""
        if "positive" in segment_result.lower():
            return "positive"
        elif "negative" in segment_result.lower():
            return "negative"
        else:
            return "neutral"
    
    def _extract_engagement_likelihood(self, segment_result: str) -> float:
        """Extract engagement likelihood from segment analysis"""
        if "high engagement" in segment_result.lower():
            return 0.8
        elif "medium engagement" in segment_result.lower():
            return 0.6
        else:
            return 0.4
    
    def _create_sentiment_analysis_prompt(
        self, content_piece: ShakesContentPiece, analysis_depth: str, sentiment_categories: List[str]
    ) -> str:
        """Create prompt for sentiment analysis"""
        return f"""
        Analyze the sentiment and emotional impact of this content:
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        Content Type: {content_piece.content_type}
        Platform: {content_piece.platform}
        
        Analysis Depth: {analysis_depth}
        Categories: {', '.join(sentiment_categories)}
        
        Provide:
        1. Overall sentiment score (positive/negative/neutral)
        2. Emotional tone analysis
        3. Audience impact assessment
        4. Brand alignment evaluation
        5. Key emotional indicators
        
        Format as comprehensive sentiment analysis.
        """
    
    def _create_audience_segment_prompt(
        self, content_piece: ShakesContentPiece, segment: str, sentiment_metrics: List[str]
    ) -> str:
        """Create prompt for audience segment analysis"""
        return f"""
        Analyze how this audience segment would perceive the content:
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        Audience Segment: {segment}
        Sentiment Metrics: {', '.join(sentiment_metrics)}
        
        Provide:
        1. Emotional response prediction
        2. Engagement likelihood assessment
        3. Brand perception impact
        4. Action intent analysis
        5. Segment-specific insights
        
        Format as audience segment sentiment analysis.
        """
    
    def _create_audience_insights_prompt(
        self, audience_sentiment: Dict[str, Any], audience_segments: List[str], sentiment_metrics: List[str]
    ) -> str:
        """Create prompt for audience insights"""
        return f"""
        Generate insights from audience sentiment analysis:
        
        Audience Segments: {', '.join(audience_segments)}
        Sentiment Metrics: {', '.join(sentiment_metrics)}
        Audience Sentiment: {audience_sentiment}
        
        Provide:
        1. Key audience insights
        2. Segment comparison analysis
        3. Engagement opportunities
        4. Targeting recommendations
        5. Content optimization suggestions
        
        Format as comprehensive audience insights.
        """
    
    def _create_targeting_recommendations_prompt(
        self, audience_sentiment: Dict[str, Any], audience_insights: str
    ) -> str:
        """Create prompt for targeting recommendations"""
        return f"""
        Provide targeting recommendations based on audience sentiment:
        
        Audience Sentiment: {audience_sentiment}
        Audience Insights: {audience_insights}
        
        Provide:
        1. Audience targeting strategies
        2. Content personalization recommendations
        3. Platform optimization suggestions
        4. Timing and frequency advice
        5. Engagement enhancement tactics
        
        Format as actionable targeting recommendations.
        """
    
    def _create_sentiment_optimization_prompt(
        self, content_piece: ShakesContentPiece, current_sentiment: Dict[str, Any], target_sentiment: str, optimization_goals: List[str]
    ) -> str:
        """Create prompt for sentiment optimization"""
        return f"""
        Create sentiment optimization strategy:
        
        Content: {content_piece.title}
        Current Sentiment: {current_sentiment}
        Target Sentiment: {target_sentiment}
        Optimization Goals: {', '.join(optimization_goals)}
        
        Provide:
        1. Sentiment optimization strategy
        2. Content modification recommendations
        3. Emotional tone adjustments
        4. Audience engagement improvements
        5. Implementation guidelines
        
        Format as comprehensive sentiment optimization strategy.
        """
    
    def _create_content_optimization_prompt(
        self, content_piece: ShakesContentPiece, sentiment_optimization: Dict[str, Any], target_sentiment: str
    ) -> str:
        """Create prompt for content optimization"""
        return f"""
        Optimize this content for target sentiment:
        
        Original Content: {content_piece.content}
        Sentiment Optimization: {sentiment_optimization}
        Target Sentiment: {target_sentiment}
        
        Generate optimized content that achieves the target sentiment while maintaining:
        1. Original message and intent
        2. Content quality and clarity
        3. Brand voice consistency
        4. Audience appropriateness
        
        Generate the optimized content.
        """
    
    def _create_optimization_report_prompt(
        self, current_sentiment: Dict[str, Any], sentiment_optimization: Dict[str, Any], optimized_content: str
    ) -> str:
        """Create prompt for optimization report"""
        return f"""
        Create sentiment optimization report:
        
        Current Sentiment: {current_sentiment}
        Sentiment Optimization: {sentiment_optimization}
        Optimized Content: {optimized_content}
        
        Provide:
        1. Optimization summary
        2. Key changes made
        3. Expected impact
        4. Implementation recommendations
        5. Success metrics
        
        Format as comprehensive optimization report.
        """
    
    def _create_trend_insights_prompt(
        self, sentiment_trends: Dict[str, Any], trend_categories: List[str], time_period_days: int
    ) -> str:
        """Create prompt for trend insights"""
        return f"""
        Analyze sentiment trends across content:
        
        Time Period: {time_period_days} days
        Trend Categories: {', '.join(trend_categories)}
        Sentiment Trends: {sentiment_trends}
        
        Provide:
        1. Trend analysis and patterns
        2. Sentiment consistency evaluation
        3. Performance correlation insights
        4. Optimization opportunities
        5. Strategic recommendations
        
        Format as comprehensive trend insights.
        """
    
    def _create_trend_recommendations_prompt(
        self, sentiment_trends: Dict[str, Any], trend_insights: str
    ) -> str:
        """Create prompt for trend recommendations"""
        return f"""
        Provide recommendations based on sentiment trends:
        
        Sentiment Trends: {sentiment_trends}
        Trend Insights: {trend_insights}
        
        Provide:
        1. Sentiment consistency improvements
        2. Content strategy adjustments
        3. Audience engagement enhancements
        4. Brand voice optimization
        5. Performance improvement tactics
        
        Format as actionable trend recommendations.
        """
