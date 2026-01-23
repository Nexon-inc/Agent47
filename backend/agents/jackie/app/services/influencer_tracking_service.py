import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import InfluencerPerformance, PerformanceMetric, ROIAnalysis, ReachTracking

class InfluencerTrackingService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def track_influencer_performance(self, influencer_id: str, campaign_id: str, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        tracking_id = str(uuid.uuid4())
        tracking_result = self.nlp_processor.track_influencer_performance(f"JackieInfluencer ID: {influencer_id}")
        
        tracking = InfluencerPerformance(
            id=tracking_id, influencer_id=influencer_id, campaign_id=campaign_id,
            performance_data=json.dumps(performance_data), tracking_result=json.dumps(tracking_result),
            created_at=datetime.utcnow()
        )
        self.db.add(tracking)
        self.db.commit()
        
        return {"tracking_id": tracking_id, "tracking_result": tracking_result}
    
    def calculate_influencer_roi(self, campaign_id: str, investment_amount: float, revenue_generated: float) -> Dict[str, Any]:
        roi_id = str(uuid.uuid4())
        roi_result = self.nlp_processor.calculate_influencer_roi(f"JackieCampaign ID: {campaign_id}")
        
        roi = ROIAnalysis(
            id=roi_id, campaign_id=campaign_id, investment_amount=investment_amount,
            revenue_generated=revenue_generated, roi_data=json.dumps(roi_result),
            created_at=datetime.utcnow()
        )
        self.db.add(roi)
        self.db.commit()
        
        return {"roi_id": roi_id, "roi_data": roi_result}
    
    def get_influencer_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        performance_trackings = self.db.query(InfluencerPerformance).filter(InfluencerPerformance.created_at >= cutoff_date).count()
        roi_analyses = self.db.query(ROIAnalysis).filter(ROIAnalysis.created_at >= cutoff_date).count()
        
        return {
            "timeframe": timeframe, "performance_trackings": performance_trackings,
            "roi_analyses": roi_analyses
        }
