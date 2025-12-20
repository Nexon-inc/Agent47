import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import BrandVoice, ContentGeneration, ToneAnalysis, StyleGuide

class BrandVoiceService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def create_brand_voice(self, brand_name: str, voice_characteristics: Dict[str, Any],
                          industry: str, target_audience: List[str], 
                          voice_samples: List[str]) -> Dict[str, Any]:
        voice_id = str(uuid.uuid4())
        voice_profile = self.nlp_processor.create_brand_voice(f"Brand: {brand_name}, Characteristics: {voice_characteristics}")
        
        brand_voice = BrandVoice(
            id=voice_id, brand_name=brand_name, voice_characteristics=json.dumps(voice_characteristics),
            industry=industry, target_audience=json.dumps(target_audience),
            voice_samples=json.dumps(voice_samples), voice_profile=json.dumps(voice_profile),
            created_at=datetime.utcnow()
        )
        self.db.add(brand_voice)
        self.db.commit()
        return {"voice_id": voice_id, "brand_name": brand_name, "voice_profile": voice_profile}
    
    def generate_content_with_brand_voice(self, voice_id: str, content_type: str,
                                        content_prompt: str, target_audience: List[str],
                                        content_length: str = "medium") -> Dict[str, Any]:
        brand_voice = self.db.query(BrandVoice).filter(BrandVoice.id == voice_id).first()
        if not brand_voice:
            raise Exception("Brand voice not found")
        
        generation_id = str(uuid.uuid4())
        generated_content = self.nlp_processor.generate_brand_content(f"Voice: {json.loads(brand_voice.voice_profile)}, Prompt: {content_prompt}")
        
        content_record = ContentGeneration(
            id=generation_id, voice_id=voice_id, content_type=content_type,
            content_prompt=content_prompt, target_audience=json.dumps(target_audience),
            content_length=content_length, generated_content=generated_content.get("content", ""),
            tone_score=generated_content.get("tone_score", 0.0), created_at=datetime.utcnow()
        )
        self.db.add(content_record)
        self.db.commit()
        return {"generation_id": generation_id, "generated_content": generated_content.get("content", "")}
    
    def analyze_content_tone(self, content: str, voice_id: str) -> Dict[str, Any]:
        brand_voice = self.db.query(BrandVoice).filter(BrandVoice.id == voice_id).first()
        if not brand_voice:
            raise Exception("Brand voice not found")
        
        analysis_id = str(uuid.uuid4())
        tone_analysis = self.nlp_processor.analyze_content_tone(f"Content: {content}, Voice: {json.loads(brand_voice.voice_profile)}")
        
        analysis_record = ToneAnalysis(
            id=analysis_id, voice_id=voice_id, content=content,
            tone_analysis=json.dumps(tone_analysis), created_at=datetime.utcnow()
        )
        self.db.add(analysis_record)
        self.db.commit()
        return {"analysis_id": analysis_id, "tone_analysis": tone_analysis}
    
    def optimize_content_tone(self, content: str, voice_id: str, optimization_goals: Dict[str, Any]) -> Dict[str, Any]:
        brand_voice = self.db.query(BrandVoice).filter(BrandVoice.id == voice_id).first()
        if not brand_voice:
            raise Exception("Brand voice not found")
        
        optimization_result = self.nlp_processor.optimize_content_tone(f"Content: {content}, Voice: {json.loads(brand_voice.voice_profile)}")
        return {"optimized_content": optimization_result.get("optimized_content", content)}
    
    def generate_style_guide(self, voice_id: str, style_guide_type: str = "comprehensive") -> Dict[str, Any]:
        brand_voice = self.db.query(BrandVoice).filter(BrandVoice.id == voice_id).first()
        if not brand_voice:
            raise Exception("Brand voice not found")
        
        guide_id = str(uuid.uuid4())
        style_guide = self.nlp_processor.generate_style_guide(f"Voice: {json.loads(brand_voice.voice_profile)}, Type: {style_guide_type}")
        
        guide_record = StyleGuide(
            id=guide_id, voice_id=voice_id, style_guide_type=style_guide_type,
            style_guide_content=json.dumps(style_guide), created_at=datetime.utcnow()
        )
        self.db.add(guide_record)
        self.db.commit()
        return {"guide_id": guide_id, "style_guide": style_guide}
    
    def check_brand_consistency(self, content: str, voice_id: str) -> Dict[str, Any]:
        brand_voice = self.db.query(BrandVoice).filter(BrandVoice.id == voice_id).first()
        if not brand_voice:
            raise Exception("Brand voice not found")
        
        consistency_result = self.nlp_processor.check_brand_consistency(f"Content: {content}, Voice: {json.loads(brand_voice.voice_profile)}")
        return {"consistency_score": consistency_result.get("consistency_score", 0.0)}
    
    def get_brand_voice_analytics(self, voice_id: str, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        content_generations = self.db.query(ContentGeneration).filter(
            ContentGeneration.voice_id == voice_id,
            ContentGeneration.created_at >= cutoff_date
        ).count()
        
        avg_tone_score = self.db.query(ContentGeneration).filter(
            ContentGeneration.voice_id == voice_id,
            ContentGeneration.created_at >= cutoff_date
        ).with_entities(ContentGeneration.tone_score).all()
        
        avg_tone_score_value = sum(score[0] for score in avg_tone_score) / len(avg_tone_score) if avg_tone_score else 0.0
        
        return {"content_generations": content_generations, "average_tone_score": avg_tone_score_value}
    
    def batch_generate_content(self, voice_id: str, content_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for content_item in content_batch:
            try:
                result = self.generate_content_with_brand_voice(
                    voice_id, content_item.get("content_type", "general"),
                    content_item.get("content_prompt", ""), content_item.get("target_audience", [])
                )
                results.append({"content_id": content_item.get("id"), "result": result})
            except Exception as e:
                results.append({"content_id": content_item.get("id"), "error": str(e)})
        return results
