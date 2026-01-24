import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import JackieCustomerSegment, JackiePersonalizationRule, JackieDynamicContent
from pydantic import BaseModel

class CRMIntegration(BaseModel):
    id: str
    crm_type: str
    integration_data: str  # JSON string
    created_at: datetime = datetime.utcnow()

class DynamicPersonalizationService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def create_customer_segment(self, segment_criteria: Dict[str, Any], segment_name: str) -> Dict[str, Any]:
        segment_id = str(uuid.uuid4())
        segment_result = self.nlp_processor.create_customer_segment(f"Segment Criteria: {segment_criteria}")
        
        segment = JackieCustomerSegment(
            id=segment_id, segment_criteria=json.dumps(segment_criteria), segment_name=segment_name,
            segment_data=json.dumps(segment_result), created_at=datetime.utcnow()
        )
        self.db.add(segment)
        self.db.commit()
        
        return {"segment_id": segment_id, "segment_data": segment_result}
    
    def generate_dynamic_content(self, content_template: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        content_id = str(uuid.uuid4())
        content_result = self.nlp_processor.generate_dynamic_content(f"Content Template: {content_template}")
        
        content = JackieDynamicContent(
            id=content_id, content_template=content_template, customer_data=json.dumps(customer_data),
            content_data=json.dumps(content_result), created_at=datetime.utcnow()
        )
        self.db.add(content)
        self.db.commit()
        
        return {"content_id": content_id, "content_data": content_result}
    
    def get_personalization_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        segments_created = self.db.query(JackieCustomerSegment).filter(JackieCustomerSegment.created_at >= cutoff_date).count()
        dynamic_content = self.db.query(JackieDynamicContent).filter(JackieDynamicContent.created_at >= cutoff_date).count()
        
        return {
            "timeframe": timeframe, "segments_created": segments_created,
            "dynamic_content": dynamic_content
        }
