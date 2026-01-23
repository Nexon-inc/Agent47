import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import JackieDeepAnalytics, JackieSentimentAnalysis, BenchmarkData, JackieActionableInsight

class DeepAnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def analyze_campaign_performance(self, campaign_id: str, analysis_depth: str = "comprehensive",
                                   include_sentiment: bool = True) -> Dict[str, Any]:
        analysis_id = str(uuid.uuid4())
        
        prompt = f"""
        JackieCampaign ID: {campaign_id}
        Analysis Depth: {analysis_depth}
        Include Sentiment: {include_sentiment}
        
        Perform deep campaign performance analysis with actionable insights.
        """
        
        analysis_result = self.nlp_processor.analyze_campaign_performance(prompt)
        
        analysis = JackieDeepAnalytics(
            id=analysis_id, campaign_id=campaign_id, analysis_depth=analysis_depth,
            include_sentiment=include_sentiment, analysis_data=json.dumps(analysis_result),
            created_at=datetime.utcnow()
        )
        self.db.add(analysis)
        self.db.commit()
        
        return {"analysis_id": analysis_id, "analysis_data": analysis_result}
    
    def perform_sentiment_analysis(self, content_data: List[Dict[str, Any]], 
                                 analysis_type: str = "comprehensive") -> Dict[str, Any]:
        sentiment_id = str(uuid.uuid4())
        
        prompt = f"""
        Content Data: {content_data}
        Analysis Type: {analysis_type}
        
        Perform comprehensive sentiment analysis on the content data.
        """
        
        sentiment_result = self.nlp_processor.perform_sentiment_analysis(prompt)
        
        sentiment = SentimentAnalysis(
            id=sentiment_id, content_data=json.dumps(content_data), analysis_type=analysis_type,
            sentiment_results=json.dumps(sentiment_result), created_at=datetime.utcnow()
        )
        self.db.add(sentiment)
        self.db.commit()
        
        return {"sentiment_id": sentiment_id, "sentiment_results": sentiment_result}
    
    def benchmark_campaign_performance(self, campaign_id: str, benchmark_metrics: List[str],
                                     industry_standard: str = "auto") -> Dict[str, Any]:
        benchmark_id = str(uuid.uuid4())
        
        prompt = f"""
        JackieCampaign ID: {campaign_id}
        Benchmark Metrics: {benchmark_metrics}
        Industry Standard: {industry_standard}
        
        Benchmark campaign performance against industry standards and competitors.
        """
        
        benchmark_result = self.nlp_processor.benchmark_campaign_performance(prompt)
        
        benchmark = BenchmarkData(
            id=benchmark_id, campaign_id=campaign_id, benchmark_metrics=json.dumps(benchmark_metrics),
            industry_standard=industry_standard, benchmark_results=json.dumps(benchmark_result),
            created_at=datetime.utcnow()
        )
        self.db.add(benchmark)
        self.db.commit()
        
        return {"benchmark_id": benchmark_id, "benchmark_results": benchmark_result}
    
    def generate_actionable_insights(self, campaign_data: Dict[str, Any], 
                                   insight_focus: List[str]) -> Dict[str, Any]:
        insight_id = str(uuid.uuid4())
        
        prompt = f"""
        JackieCampaign Data: {campaign_data}
        Insight Focus: {insight_focus}
        
        Generate actionable insights and recommendations based on campaign data.
        """
        
        insight_result = self.nlp_processor.generate_actionable_insights(prompt)
        
        insight = JackieActionableInsight(
            id=insight_id, campaign_data=json.dumps(campaign_data), insight_focus=json.dumps(insight_focus),
            insights=json.dumps(insight_result), created_at=datetime.utcnow()
        )
        self.db.add(insight)
        self.db.commit()
        
        return {"insight_id": insight_id, "insights": insight_result}
    
    def analyze_cross_channel_performance(self, campaign_ids: List[str],
                                        channel_metrics: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        JackieCampaign IDs: {campaign_ids}
        Channel Metrics: {channel_metrics}
        
        Analyze cross-channel performance and identify optimization opportunities.
        """
        
        cross_channel_result = self.nlp_processor.analyze_cross_channel_performance(prompt)
        
        return {
            "campaign_ids": campaign_ids, "channel_metrics": channel_metrics,
            "cross_channel_analysis": cross_channel_result
        }
    
    def generate_performance_report(self, campaign_id: str, report_type: str = "comprehensive",
                                  include_recommendations: bool = True) -> Dict[str, Any]:
        prompt = f"""
        JackieCampaign ID: {campaign_id}
        Report Type: {report_type}
        Include Recommendations: {include_recommendations}
        
        Generate a comprehensive performance report with insights and recommendations.
        """
        
        report_result = self.nlp_processor.generate_performance_report(prompt)
        
        return {
            "campaign_id": campaign_id, "report_type": report_type,
            "performance_report": report_result
        }
    
    def analyze_audience_behavior(self, audience_data: Dict[str, Any],
                                behavior_metrics: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Audience Data: {audience_data}
        Behavior Metrics: {behavior_metrics}
        
        Analyze audience behavior patterns and engagement trends.
        """
        
        behavior_result = self.nlp_processor.analyze_audience_behavior(prompt)
        
        return {
            "audience_data": audience_data, "behavior_metrics": behavior_metrics,
            "behavior_analysis": behavior_result
        }
    
    def get_deep_analytics_summary(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        analyses_count = self.db.query(JackieDeepAnalytics).filter(
            JackieDeepAnalytics.created_at >= cutoff_date
        ).count()
        
        sentiment_analyses = self.db.query(SentimentAnalysis).filter(
            SentimentAnalysis.created_at >= cutoff_date
        ).count()
        
        benchmarks_count = self.db.query(BenchmarkData).filter(
            BenchmarkData.created_at >= cutoff_date
        ).count()
        
        insights_count = self.db.query(JackieActionableInsight).filter(
            JackieActionableInsight.created_at >= cutoff_date
        ).count()
        
        return {
            "timeframe": timeframe, "analyses_count": analyses_count,
            "sentiment_analyses": sentiment_analyses, "benchmarks_count": benchmarks_count,
            "insights_count": insights_count
        }
