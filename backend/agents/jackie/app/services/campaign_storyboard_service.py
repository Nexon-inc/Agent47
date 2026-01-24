import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import JackieStoryboardScene, JackieFlowVisualization
from pydantic import BaseModel

class CampaignStoryboard(BaseModel):
    id: str
    campaign_brief: str  # JSON string
    storyboard_type: str = "multi_channel"
    storyboard_data: str  # JSON string
    created_at: datetime = datetime.utcnow()

class ChannelFlow(BaseModel):
    id: str
    channel: str
    flow_data: str  # JSON string
    created_at: datetime = datetime.utcnow()

class CampaignStoryboardService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def create_campaign_storyboard(self, campaign_brief: Dict[str, Any], storyboard_type: str = "multi_channel") -> Dict[str, Any]:
        storyboard_id = str(uuid.uuid4())
        storyboard_result = self.nlp_processor.create_campaign_storyboard(f"JackieCampaign Brief: {campaign_brief}")
        
        storyboard = CampaignStoryboard(
            id=storyboard_id, campaign_brief=json.dumps(campaign_brief), storyboard_type=storyboard_type,
            storyboard_data=json.dumps(storyboard_result), created_at=datetime.utcnow()
        )
        self.db.add(storyboard)
        self.db.commit()
        
        return {"storyboard_id": storyboard_id, "storyboard_data": storyboard_result}
    
    def create_storyboard_scene(self, scene_data: Dict[str, Any], scene_order: int, channel: str) -> Dict[str, Any]:
        scene_id = str(uuid.uuid4())
        scene_result = self.nlp_processor.create_storyboard_scene(f"Scene Data: {scene_data}")
        
        scene = JackieStoryboardScene(
            id=scene_id, scene_data=json.dumps(scene_data), scene_order=scene_order, channel=channel,
            scene_content=json.dumps(scene_result), created_at=datetime.utcnow()
        )
        self.db.add(scene)
        self.db.commit()
        
        return {"scene_id": scene_id, "scene_content": scene_result}
    
    def get_storyboard_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        storyboards_created = self.db.query(CampaignStoryboard).filter(CampaignStoryboard.created_at >= cutoff_date).count()
        scenes_created = self.db.query(JackieStoryboardScene).filter(JackieStoryboardScene.created_at >= cutoff_date).count()
        
        return {
            "timeframe": timeframe, "storyboards_created": storyboards_created,
            "scenes_created": scenes_created
        }
