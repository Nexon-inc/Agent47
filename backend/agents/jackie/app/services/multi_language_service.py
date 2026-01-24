import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.utils.nlp_utils import NLPUtils
from core.cache.redis_manager import init_redis
from ..database import get_jackie_database
from ..models import JackieMultiLanguageCampaign, JackieTranslationData, JackieCulturalAdaptation
from pydantic import BaseModel

class LanguageAnalytics(BaseModel):
    id: str
    language: str
    analytics_data: str  # JSON string
    created_at: datetime = datetime.utcnow()

logger = logging.getLogger(__name__)

class MultiLanguageService:
    def __init__(self):
        self.db = None
        self.nlp_processor = None
        self.redis_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize multi-language service"""
        if self._initialized:
            return
        
        try:
            self.db = await get_jackie_database()
            self.nlp_processor = NLPUtils()
            await self.nlp_processor.initialize()
            self.redis_client = await init_redis()
            self._initialized = True
            logger.info("Multi-language service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize multi-language service: {e}")
            raise
    
    async def create_multi_language_campaign(self, campaign_id: str, target_languages: List[str], source_content: Dict[str, Any]) -> Dict[str, Any]:
        """Create a multi-language campaign with translations"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                ml_campaign_id = str(uuid.uuid4())
                
                prompt = f"""
                JackieCampaign ID: {campaign_id}
                Target Languages: {target_languages}
                Source Content: {source_content}
                
                Create a multi-language campaign with proper translations.
                """
                
                campaign_result = await self.nlp_processor.create_multi_language_campaign(prompt)
                
                ml_campaign = JackieMultiLanguageCampaign(
                    id=ml_campaign_id, campaign_id=campaign_id, target_languages=json.dumps(target_languages),
                    source_content=json.dumps(source_content), campaign_data=json.dumps(campaign_result),
                    created_at=datetime.utcnow()
                )
                session.add(ml_campaign)
                await session.commit()
                
                return {"ml_campaign_id": ml_campaign_id, "campaign_data": campaign_result}
        except Exception as e:
            logger.error(f"Failed to create multi-language campaign: {e}")
            raise
    
    async def translate_campaign_content(self, campaign_id: str, content: str, target_language: str) -> Dict[str, Any]:
        """Translate campaign content to target language"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                translation_id = str(uuid.uuid4())
                
                prompt = f"""
                JackieCampaign ID: {campaign_id}
                Content: {content}
                Target Language: {target_language}
                
                Translate campaign content to the target language.
                """
                
                translation_result = await self.nlp_processor.translate_campaign_content(prompt)
                
                translation = JackieTranslationData(
                    id=translation_id, campaign_id=campaign_id, content=content,
                    target_language=target_language, translation_result=json.dumps(translation_result),
                    created_at=datetime.utcnow()
                )
                session.add(translation)
                await session.commit()
                
                return {"translation_id": translation_id, "translation_result": translation_result}
        except Exception as e:
            logger.error(f"Failed to translate campaign content: {e}")
            raise
    
    async def adapt_content_culturally(self, campaign_id: str, content: str, target_culture: str) -> Dict[str, Any]:
        """Adapt content for cultural relevance"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                adaptation_id = str(uuid.uuid4())
                
                prompt = f"""
                JackieCampaign ID: {campaign_id}
                Content: {content}
                Target Culture: {target_culture}
                
                Adapt content for cultural relevance and sensitivity.
                """
                
                adaptation_result = await self.nlp_processor.adapt_content_culturally(prompt)
                
                adaptation = JackieCulturalAdaptation(
                    id=adaptation_id, campaign_id=campaign_id, content=content,
                    target_culture=target_culture, adaptation_result=json.dumps(adaptation_result),
                    created_at=datetime.utcnow()
                )
                session.add(adaptation)
                await session.commit()
                
                return {"adaptation_id": adaptation_id, "adaptation_result": adaptation_result}
        except Exception as e:
            logger.error(f"Failed to adapt content culturally: {e}")
            raise
    
    async def get_multi_language_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        """Get multi-language analytics for specified timeframe"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
                
                campaigns_created_query = select(func.count(JackieMultiLanguageCampaign.id)).where(JackieMultiLanguageCampaign.created_at >= cutoff_date)
                translations_made_query = select(func.count(JackieTranslationData.id)).where(JackieTranslationData.created_at >= cutoff_date)
                adaptations_performed_query = select(func.count(JackieCulturalAdaptation.id)).where(JackieCulturalAdaptation.created_at >= cutoff_date)
                
                campaigns_created = await session.scalar(campaigns_created_query)
                translations_made = await session.scalar(translations_made_query)
                adaptations_performed = await session.scalar(adaptations_performed_query)
                
                return {
                    "timeframe": timeframe, "campaigns_created": campaigns_created,
                    "translations_made": translations_made, "adaptations_performed": adaptations_performed
                }
        except Exception as e:
            logger.error(f"Failed to get multi-language analytics: {e}")
            raise
