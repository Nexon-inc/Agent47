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
from ..models import CustomerFeedback, SurveyData, FeedbackAnalysis, CampaignRefinement

logger = logging.getLogger(__name__)

class CustomerFeedbackService:
    def __init__(self):
        self.db = None
        self.nlp_processor = None
        self.redis_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize customer feedback service"""
        if self._initialized:
            return
        
        try:
            self.db = await get_jackie_database()
            self.nlp_processor = NLPUtils()
            await self.nlp_processor.initialize()
            self.redis_client = await init_redis()
            self._initialized = True
            logger.info("Customer feedback service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize customer feedback service: {e}")
            raise
    
    async def collect_customer_feedback(self, campaign_id: str, feedback_data: Dict[str, Any], feedback_type: str = "survey") -> Dict[str, Any]:
        """Collect and process customer feedback for campaign refinement"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                feedback_id = str(uuid.uuid4())
                
                prompt = f"""
                Campaign ID: {campaign_id}
                Feedback Data: {feedback_data}
                Feedback Type: {feedback_type}
                
                Collect and process customer feedback for campaign refinement.
                """
                
                feedback_result = await self.nlp_processor.collect_customer_feedback(prompt)
                
                feedback = CustomerFeedback(
                    id=feedback_id, campaign_id=campaign_id, feedback_data=json.dumps(feedback_data),
                    feedback_type=feedback_type, feedback_result=json.dumps(feedback_result),
                    created_at=datetime.utcnow()
                )
                session.add(feedback)
                await session.commit()
                
                return {"feedback_id": feedback_id, "feedback_result": feedback_result}
        except Exception as e:
            logger.error(f"Failed to collect customer feedback: {e}")
            raise
    
    async def analyze_survey_data(self, survey_id: str, survey_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze survey data to extract actionable insights"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                analysis_id = str(uuid.uuid4())
                
                prompt = f"""
                Survey ID: {survey_id}
                Survey Responses: {survey_responses}
                
                Analyze survey data to extract actionable insights for campaign improvement.
                """
                
                analysis_result = await self.nlp_processor.analyze_survey_data(prompt)
                
                analysis = SurveyData(
                    id=analysis_id, survey_id=survey_id, survey_responses=json.dumps(survey_responses),
                    analysis_result=json.dumps(analysis_result), created_at=datetime.utcnow()
                )
                session.add(analysis)
                await session.commit()
                
                return {"analysis_id": analysis_id, "analysis_result": analysis_result}
        except Exception as e:
            logger.error(f"Failed to analyze survey data: {e}")
            raise
    
    async def refine_campaign_based_on_feedback(self, campaign_id: str, feedback_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Refine campaign strategy based on customer feedback insights"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                refinement_id = str(uuid.uuid4())
                
                prompt = f"""
                Campaign ID: {campaign_id}
                Feedback Insights: {feedback_insights}
                
                Refine campaign strategy and content based on customer feedback insights.
                """
                
                refinement_result = await self.nlp_processor.refine_campaign_based_on_feedback(prompt)
                
                refinement = CampaignRefinement(
                    id=refinement_id, campaign_id=campaign_id, feedback_insights=json.dumps(feedback_insights),
                    refinement_data=json.dumps(refinement_result), created_at=datetime.utcnow()
                )
                session.add(refinement)
                await session.commit()
                
                return {"refinement_id": refinement_id, "refinement_data": refinement_result}
        except Exception as e:
            logger.error(f"Failed to refine campaign based on feedback: {e}")
            raise
    
    async def get_feedback_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        """Get feedback analytics for specified timeframe"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
                
                feedback_query = select(func.count(CustomerFeedback.id)).where(CustomerFeedback.created_at >= cutoff_date)
                survey_query = select(func.count(SurveyData.id)).where(SurveyData.created_at >= cutoff_date)
                refinement_query = select(func.count(CampaignRefinement.id)).where(CampaignRefinement.created_at >= cutoff_date)
                
                feedback_collected = await session.scalar(feedback_query)
                surveys_analyzed = await session.scalar(survey_query)
                campaigns_refined = await session.scalar(refinement_query)
                
                return {
                    "timeframe": timeframe, "feedback_collected": feedback_collected,
                    "surveys_analyzed": surveys_analyzed, "campaigns_refined": campaigns_refined
                }
        except Exception as e:
            logger.error(f"Failed to get feedback analytics: {e}")
            raise
