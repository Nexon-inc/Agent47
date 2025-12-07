import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from backend.core.utils.nlp_utils import NLPProcessor
from backend.core.cache.redis_manager import RedisManager
from ..models import VoiceAd, AudioContent, VoiceScript, AdPlatform

class VoiceAdGeneratorService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def generate_voice_ad(self, ad_brief: Dict[str, Any], platform: str = "spotify", duration: str = "30s") -> Dict[str, Any]:
        ad_id = str(uuid.uuid4())
        ad_result = self.nlp_processor.generate_voice_ad(f"Ad Brief: {ad_brief}")
        
        ad = VoiceAd(
            id=ad_id, ad_brief=json.dumps(ad_brief), platform=platform, duration=duration,
            ad_content=json.dumps(ad_result), created_at=datetime.utcnow()
        )
        self.db.add(ad)
        self.db.commit()
        
        return {"ad_id": ad_id, "ad_content": ad_result}
    
    def create_voice_script(self, script_brief: Dict[str, Any], voice_style: str, target_audience: str) -> Dict[str, Any]:
        script_id = str(uuid.uuid4())
        script_result = self.nlp_processor.create_voice_script(f"Script Brief: {script_brief}")
        
        script = VoiceScript(
            id=script_id, script_brief=json.dumps(script_brief), voice_style=voice_style,
            target_audience=target_audience, script_content=json.dumps(script_result),
            created_at=datetime.utcnow()
        )
        self.db.add(script)
        self.db.commit()
        
        return {"script_id": script_id, "script_content": script_result}
    
    def optimize_for_platform(self, platform: str, ad_content: Dict[str, Any], platform_requirements: Dict[str, Any]) -> Dict[str, Any]:
        optimization_id = str(uuid.uuid4())
        
        prompt = f"""
        Platform: {platform}
        Ad Content: {ad_content}
        Platform Requirements: {platform_requirements}
        
        Optimize voice ad content for the specific platform requirements.
        """
        
        optimization_result = self.nlp_processor.optimize_for_platform(prompt)
        
        platform_opt = AdPlatform(
            id=optimization_id, platform=platform, ad_content=json.dumps(ad_content),
            platform_requirements=json.dumps(platform_requirements), optimization_data=json.dumps(optimization_result),
            created_at=datetime.utcnow()
        )
        self.db.add(platform_opt)
        self.db.commit()
        
        return {"optimization_id": optimization_id, "optimization_data": optimization_result}
    
    def get_voice_ad_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        ads_generated = self.db.query(VoiceAd).filter(VoiceAd.created_at >= cutoff_date).count()
        scripts_created = self.db.query(VoiceScript).filter(VoiceScript.created_at >= cutoff_date).count()
        
        return {
            "timeframe": timeframe, "ads_generated": ads_generated,
            "scripts_created": scripts_created
        }
