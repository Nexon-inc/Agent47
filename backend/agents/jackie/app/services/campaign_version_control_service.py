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
from ..models import CampaignVersion, VersionChange, CampaignRollback, VersionHistory

logger = logging.getLogger(__name__)

class CampaignVersionControlService:
    def __init__(self):
        self.db = None
        self.nlp_processor = None
        self.redis_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize campaign version control service"""
        if self._initialized:
            return
        
        try:
            self.db = await get_jackie_database()
            self.nlp_processor = NLPUtils()
            await self.nlp_processor.initialize()
            self.redis_client = await init_redis()
            self._initialized = True
            logger.info("Campaign version control service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize campaign version control service: {e}")
            raise
    
    async def create_campaign_version(self, campaign_id: str, version_data: Dict[str, Any], version_notes: str = "") -> Dict[str, Any]:
        """Create a new version of a campaign"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                version_id = str(uuid.uuid4())
                
                prompt = f"""
                Campaign ID: {campaign_id}
                Version Data: {version_data}
                Version Notes: {version_notes}
                
                Create a new version of the campaign with proper versioning.
                """
                
                version_result = await self.nlp_processor.create_campaign_version(prompt)
                
                version = CampaignVersion(
                    id=version_id, campaign_id=campaign_id, version_data=json.dumps(version_data),
                    version_notes=version_notes, version_result=json.dumps(version_result),
                    created_at=datetime.utcnow()
                )
                session.add(version)
                await session.commit()
                
                return {"version_id": version_id, "version_result": version_result}
        except Exception as e:
            logger.error(f"Failed to create campaign version: {e}")
            raise
    
    async def track_version_changes(self, version_id: str, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Track changes made in a campaign version"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                change_id = str(uuid.uuid4())
                
                prompt = f"""
                Version ID: {version_id}
                Changes: {changes}
                
                Track and document changes made in the campaign version.
                """
                
                change_result = await self.nlp_processor.track_version_changes(prompt)
                
                change = VersionChange(
                    id=change_id, version_id=version_id, changes=json.dumps(changes),
                    change_result=json.dumps(change_result), created_at=datetime.utcnow()
                )
                session.add(change)
                await session.commit()
                
                return {"change_id": change_id, "change_result": change_result}
        except Exception as e:
            logger.error(f"Failed to track version changes: {e}")
            raise
    
    async def rollback_campaign_version(self, campaign_id: str, target_version_id: str) -> Dict[str, Any]:
        """Rollback campaign to a previous version"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                rollback_id = str(uuid.uuid4())
                
                prompt = f"""
                Campaign ID: {campaign_id}
                Target Version ID: {target_version_id}
                
                Rollback campaign to the specified version.
                """
                
                rollback_result = await self.nlp_processor.rollback_campaign_version(prompt)
                
                rollback = CampaignRollback(
                    id=rollback_id, campaign_id=campaign_id, target_version_id=target_version_id,
                    rollback_result=json.dumps(rollback_result), created_at=datetime.utcnow()
                )
                session.add(rollback)
                await session.commit()
                
                return {"rollback_id": rollback_id, "rollback_result": rollback_result}
        except Exception as e:
            logger.error(f"Failed to rollback campaign version: {e}")
            raise
    
    async def get_version_history(self, campaign_id: str) -> Dict[str, Any]:
        """Get version history for a campaign"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                history_id = str(uuid.uuid4())
                
                prompt = f"""
                Campaign ID: {campaign_id}
                
                Retrieve and format the version history for the campaign.
                """
                
                history_result = await self.nlp_processor.get_version_history(prompt)
                
                history = VersionHistory(
                    id=history_id, campaign_id=campaign_id, history_data=json.dumps(history_result),
                    created_at=datetime.utcnow()
                )
                session.add(history)
                await session.commit()
                
                return {"history_id": history_id, "history_data": history_result}
        except Exception as e:
            logger.error(f"Failed to get version history: {e}")
            raise
    
    async def get_version_control_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        """Get version control analytics for specified timeframe"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
                
                versions_created_query = select(func.count(CampaignVersion.id)).where(CampaignVersion.created_at >= cutoff_date)
                changes_tracked_query = select(func.count(VersionChange.id)).where(VersionChange.created_at >= cutoff_date)
                rollbacks_performed_query = select(func.count(CampaignRollback.id)).where(CampaignRollback.created_at >= cutoff_date)
                
                versions_created = await session.scalar(versions_created_query)
                changes_tracked = await session.scalar(changes_tracked_query)
                rollbacks_performed = await session.scalar(rollbacks_performed_query)
                
                return {
                    "timeframe": timeframe, "versions_created": versions_created,
                    "changes_tracked": changes_tracked, "rollbacks_performed": rollbacks_performed
                }
        except Exception as e:
            logger.error(f"Failed to get version control analytics: {e}")
            raise
