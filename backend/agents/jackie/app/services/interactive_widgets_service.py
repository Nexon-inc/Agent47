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
from ..models import InteractiveWidget, AdPoll, CallToAction, WidgetAnalytics

logger = logging.getLogger(__name__)

class InteractiveWidgetsService:
    def __init__(self):
        self.db = None
        self.nlp_processor = None
        self.redis_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize interactive widgets service"""
        if self._initialized:
            return
        
        try:
            self.db = await get_jackie_database()
            self.nlp_processor = NLPUtils()
            await self.nlp_processor.initialize()
            self.redis_client = await init_redis()
            self._initialized = True
            logger.info("Interactive widgets service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize interactive widgets service: {e}")
            raise
    
    async def create_interactive_widget(self, widget_type: str, widget_config: Dict[str, Any], ad_id: str) -> Dict[str, Any]:
        """Create an interactive widget for embedding in ads"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                widget_id = str(uuid.uuid4())
                
                prompt = f"""
                Widget Type: {widget_type}
                Widget Config: {widget_config}
                Ad ID: {ad_id}
                
                Create an interactive widget for embedding in ads.
                """
                
                widget_result = await self.nlp_processor.create_interactive_widget(prompt)
                
                widget = InteractiveWidget(
                    id=widget_id, widget_type=widget_type, widget_config=json.dumps(widget_config),
                    ad_id=ad_id, widget_data=json.dumps(widget_result), created_at=datetime.utcnow()
                )
                session.add(widget)
                await session.commit()
                
                return {"widget_id": widget_id, "widget_data": widget_result}
        except Exception as e:
            logger.error(f"Failed to create interactive widget: {e}")
            raise
    
    async def create_ad_poll(self, poll_question: str, poll_options: List[str], ad_id: str) -> Dict[str, Any]:
        """Create an interactive poll for embedding in ads"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                poll_id = str(uuid.uuid4())
                
                prompt = f"""
                Poll Question: {poll_question}
                Poll Options: {poll_options}
                Ad ID: {ad_id}
                
                Create an interactive poll for embedding in ads.
                """
                
                poll_result = await self.nlp_processor.create_ad_poll(prompt)
                
                poll = AdPoll(
                    id=poll_id, poll_question=poll_question, poll_options=json.dumps(poll_options),
                    ad_id=ad_id, poll_data=json.dumps(poll_result), created_at=datetime.utcnow()
                )
                session.add(poll)
                await session.commit()
                
                return {"poll_id": poll_id, "poll_data": poll_result}
        except Exception as e:
            logger.error(f"Failed to create ad poll: {e}")
            raise
    
    async def create_call_to_action(self, cta_text: str, cta_type: str, action_url: str, ad_id: str) -> Dict[str, Any]:
        """Create a compelling call-to-action for embedding in ads"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                cta_id = str(uuid.uuid4())
                
                prompt = f"""
                CTA Text: {cta_text}
                CTA Type: {cta_type}
                Action URL: {action_url}
                Ad ID: {ad_id}
                
                Create a compelling call-to-action for embedding in ads.
                """
                
                cta_result = await self.nlp_processor.create_call_to_action(prompt)
                
                cta = CallToAction(
                    id=cta_id, cta_text=cta_text, cta_type=cta_type, action_url=action_url,
                    ad_id=ad_id, cta_data=json.dumps(cta_result), created_at=datetime.utcnow()
                )
                session.add(cta)
                await session.commit()
                
                return {"cta_id": cta_id, "cta_data": cta_result}
        except Exception as e:
            logger.error(f"Failed to create call to action: {e}")
            raise
    
    async def get_widget_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        """Get widget analytics for specified timeframe"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
                
                widgets_created_query = select(func.count(InteractiveWidget.id)).where(InteractiveWidget.created_at >= cutoff_date)
                polls_created_query = select(func.count(AdPoll.id)).where(AdPoll.created_at >= cutoff_date)
                ctas_created_query = select(func.count(CallToAction.id)).where(CallToAction.created_at >= cutoff_date)
                
                widgets_created = await session.scalar(widgets_created_query)
                polls_created = await session.scalar(polls_created_query)
                ctas_created = await session.scalar(ctas_created_query)
                
                return {
                    "timeframe": timeframe, "widgets_created": widgets_created,
                    "polls_created": polls_created, "ctas_created": ctas_created
                }
        except Exception as e:
            logger.error(f"Failed to get widget analytics: {e}")
            raise
