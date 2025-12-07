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
from ..models import VideoTemplate, VoiceTemplate, AnimationAsset, DesignElement

logger = logging.getLogger(__name__)

class EnhancedVideoVoiceService:
    def __init__(self):
        self.db = None
        self.nlp_processor = None
        self.redis_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize enhanced video voice service"""
        if self._initialized:
            return
        
        try:
            self.db = await get_jackie_database()
            self.nlp_processor = NLPUtils()
            await self.nlp_processor.initialize()
            self.redis_client = await init_redis()
            self._initialized = True
            logger.info("Enhanced video voice service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize enhanced video voice service: {e}")
            raise
    
    async def create_video_template(self, template_type: str, template_config: Dict[str, Any], brand_guidelines: Dict[str, Any]) -> Dict[str, Any]:
        """Create a video template with brand guidelines"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                template_id = str(uuid.uuid4())
                
                prompt = f"""
                Template Type: {template_type}
                Template Config: {template_config}
                Brand Guidelines: {brand_guidelines}
                
                Create a video template with brand guidelines and configuration.
                """
                
                template_result = await self.nlp_processor.create_video_template(prompt)
                
                template = VideoTemplate(
                    id=template_id, template_type=template_type, template_config=json.dumps(template_config),
                    brand_guidelines=json.dumps(brand_guidelines), template_data=json.dumps(template_result),
                    created_at=datetime.utcnow()
                )
                session.add(template)
                await session.commit()
                
                return {"template_id": template_id, "template_data": template_result}
        except Exception as e:
            logger.error(f"Failed to create video template: {e}")
            raise
    
    async def create_voice_template(self, voice_type: str, voice_config: Dict[str, Any], audio_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create a voice template for audio content"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                voice_id = str(uuid.uuid4())
                
                prompt = f"""
                Voice Type: {voice_type}
                Voice Config: {voice_config}
                Audio Requirements: {audio_requirements}
                
                Create a voice template for audio content generation.
                """
                
                voice_result = await self.nlp_processor.create_voice_template(prompt)
                
                voice = VoiceTemplate(
                    id=voice_id, voice_type=voice_type, voice_config=json.dumps(voice_config),
                    audio_requirements=json.dumps(audio_requirements), voice_data=json.dumps(voice_result),
                    created_at=datetime.utcnow()
                )
                session.add(voice)
                await session.commit()
                
                return {"voice_id": voice_id, "voice_data": voice_result}
        except Exception as e:
            logger.error(f"Failed to create voice template: {e}")
            raise
    
    async def create_animation_asset(self, animation_type: str, animation_config: Dict[str, Any], visual_style: Dict[str, Any]) -> Dict[str, Any]:
        """Create an animation asset for visual content"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                animation_id = str(uuid.uuid4())
                
                prompt = f"""
                Animation Type: {animation_type}
                Animation Config: {animation_config}
                Visual Style: {visual_style}
                
                Create an animation asset for visual content.
                """
                
                animation_result = await self.nlp_processor.create_animation_asset(prompt)
                
                animation = AnimationAsset(
                    id=animation_id, animation_type=animation_type, animation_config=json.dumps(animation_config),
                    visual_style=json.dumps(visual_style), animation_data=json.dumps(animation_result),
                    created_at=datetime.utcnow()
                )
                session.add(animation)
                await session.commit()
                
                return {"animation_id": animation_id, "animation_data": animation_result}
        except Exception as e:
            logger.error(f"Failed to create animation asset: {e}")
            raise
    
    async def create_design_element(self, element_type: str, element_config: Dict[str, Any], design_guidelines: Dict[str, Any]) -> Dict[str, Any]:
        """Create a design element for visual content"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                element_id = str(uuid.uuid4())
                
                prompt = f"""
                Element Type: {element_type}
                Element Config: {element_config}
                Design Guidelines: {design_guidelines}
                
                Create a design element for visual content.
                """
                
                element_result = await self.nlp_processor.create_design_element(prompt)
                
                element = DesignElement(
                    id=element_id, element_type=element_type, element_config=json.dumps(element_config),
                    design_guidelines=json.dumps(design_guidelines), element_data=json.dumps(element_result),
                    created_at=datetime.utcnow()
                )
                session.add(element)
                await session.commit()
                
                return {"element_id": element_id, "element_data": element_result}
        except Exception as e:
            logger.error(f"Failed to create design element: {e}")
            raise
    
    async def get_enhanced_video_voice_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        """Get enhanced video voice analytics for specified timeframe"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
                
                video_templates_created_query = select(func.count(VideoTemplate.id)).where(VideoTemplate.created_at >= cutoff_date)
                voice_templates_created_query = select(func.count(VoiceTemplate.id)).where(VoiceTemplate.created_at >= cutoff_date)
                animation_assets_created_query = select(func.count(AnimationAsset.id)).where(AnimationAsset.created_at >= cutoff_date)
                design_elements_created_query = select(func.count(DesignElement.id)).where(DesignElement.created_at >= cutoff_date)
                
                video_templates_created = await session.scalar(video_templates_created_query)
                voice_templates_created = await session.scalar(voice_templates_created_query)
                animation_assets_created = await session.scalar(animation_assets_created_query)
                design_elements_created = await session.scalar(design_elements_created_query)
                
                return {
                    "timeframe": timeframe, "video_templates_created": video_templates_created,
                    "voice_templates_created": voice_templates_created, "animation_assets_created": animation_assets_created,
                    "design_elements_created": design_elements_created
                }
        except Exception as e:
            logger.error(f"Failed to get enhanced video voice analytics: {e}")
            raise
