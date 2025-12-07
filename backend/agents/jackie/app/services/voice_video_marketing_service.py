import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from backend.core.utils.nlp_utils import NLPProcessor
from backend.core.cache.redis_manager import RedisManager
from ..models import VoiceContent, VideoContent, AudioAd, VideoAd

class VoiceVideoMarketingService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def generate_voiceover(self, script: str, voice_style: str, language: str = "en") -> Dict[str, Any]:
        voice_id = str(uuid.uuid4())
        voiceover_result = self.nlp_processor.generate_voiceover(f"Script: {script}, Style: {voice_style}")
        
        voice_content = VoiceContent(
            id=voice_id, script=script, voice_style=voice_style, language=language,
            audio_url=voiceover_result.get("audio_url", ""),
            transcription=voiceover_result.get("transcription", script),
            created_at=datetime.utcnow()
        )
        self.db.add(voice_content)
        self.db.commit()
        
        return {"voice_id": voice_id, "audio_url": voiceover_result.get("audio_url", "")}
    
    def create_promotional_video(self, video_brief: Dict[str, Any], target_audience: List[str],
                                platform: str) -> Dict[str, Any]:
        video_id = str(uuid.uuid4())
        video_result = self.nlp_processor.create_promotional_video(f"Brief: {video_brief}, Platform: {platform}")
        
        video_content = VideoContent(
            id=video_id, video_brief=json.dumps(video_brief), target_audience=json.dumps(target_audience),
            platform=platform, video_url=video_result.get("video_url", ""),
            script=video_result.get("script", ""), created_at=datetime.utcnow()
        )
        self.db.add(video_content)
        self.db.commit()
        
        return {"video_id": video_id, "video_url": video_result.get("video_url", "")}
    
    def create_audio_ad(self, ad_brief: Dict[str, Any], target_platform: str) -> Dict[str, Any]:
        ad_id = str(uuid.uuid4())
        audio_ad_result = self.nlp_processor.create_audio_ad(f"Brief: {ad_brief}, Platform: {target_platform}")
        
        audio_ad = AudioAd(
            id=ad_id, ad_brief=json.dumps(ad_brief), target_platform=target_platform,
            audio_url=audio_ad_result.get("audio_url", ""),
            script=audio_ad_result.get("script", ""), created_at=datetime.utcnow()
        )
        self.db.add(audio_ad)
        self.db.commit()
        
        return {"ad_id": ad_id, "audio_url": audio_ad_result.get("audio_url", "")}
    
    def create_video_ad(self, ad_brief: Dict[str, Any], target_platform: str) -> Dict[str, Any]:
        ad_id = str(uuid.uuid4())
        video_ad_result = self.nlp_processor.create_video_ad(f"Brief: {ad_brief}, Platform: {target_platform}")
        
        video_ad = VideoAd(
            id=ad_id, ad_brief=json.dumps(ad_brief), target_platform=target_platform,
            video_url=video_ad_result.get("video_url", ""),
            script=video_ad_result.get("script", ""), created_at=datetime.utcnow()
        )
        self.db.add(video_ad)
        self.db.commit()
        
        return {"ad_id": ad_id, "video_url": video_ad_result.get("video_url", "")}
    
    def get_voice_video_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        voice_content_count = self.db.query(VoiceContent).filter(VoiceContent.created_at >= cutoff_date).count()
        video_content_count = self.db.query(VideoContent).filter(VideoContent.created_at >= cutoff_date).count()
        audio_ads_count = self.db.query(AudioAd).filter(AudioAd.created_at >= cutoff_date).count()
        video_ads_count = self.db.query(VideoAd).filter(VideoAd.created_at >= cutoff_date).count()
        
        return {
            "timeframe": timeframe, "voice_content_count": voice_content_count,
            "video_content_count": video_content_count, "audio_ads_count": audio_ads_count,
            "video_ads_count": video_ads_count
        }
