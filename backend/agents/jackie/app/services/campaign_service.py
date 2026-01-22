import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from core.utils.nlp_utils import NLPUtils
from core.event_bus.kafka_manager import EventBus
from ..database import get_jackie_database
from ..models import (
    JackieMarketingCampaign, JackieCampaignContent, JackieAdCampaign, JackieCampaignAnalytics,
    CampaignStatus, CampaignType, PlatformType, ContentType
)

logger = logging.getLogger(__name__)

class CampaignService:
    def __init__(self):
        self.db = None
        self.nlp_utils = None
        self.event_bus = None
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        
        self.db = await get_jackie_database()
        self.nlp_utils = NLPUtils()
        self.event_bus = EventBus()
        await self.event_bus.initialize()
        self._initialized = True
    
    async def create_campaign(
        self,
        user_id: int,
        name: str,
        description: Optional[str],
        campaign_type: CampaignType,
        platforms: List[PlatformType],
        target_audience: Dict[str, Any],
        budget: float,
        start_date: Optional[str],
        end_date: Optional[str],
        goals: Dict[str, Any],
        kpis: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                campaign_id = f"CAMP_{uuid.uuid4().hex[:8].upper()}"
                
                campaign = JackieMarketingCampaign(
                    campaign_id=campaign_id,
                    user_id=user_id,
                    name=name,
                    description=description,
                    campaign_type=campaign_type,
                    status=CampaignStatus.DRAFT,
                    platforms=[p.value for p in platforms],
                    target_audience=target_audience,
                    budget=budget,
                    start_date=datetime.fromisoformat(start_date) if start_date else None,
                    end_date=datetime.fromisoformat(end_date) if end_date else None,
                    goals=goals,
                    kpis=kpis,
                    performance_metrics={},
                    ai_optimization_settings={
                        "auto_optimize": True,
                        "target_roas": 3.0,
                        "budget_pacing": "standard"
                    },
                    brand_voice_settings={
                        "tone": "professional",
                        "style": "conversational"
                    }
                )
                
                session.add(campaign)
                await session.commit()
                await session.refresh(campaign)
                
                await self.event_bus.publish(
                    "marketing.campaign.created",
                    {
                        "campaign_id": campaign.id,
                        "user_id": user_id,
                        "campaign_type": campaign_type.value,
                        "platforms": [p.value for p in platforms]
                    }
                )
                
                return {
                    "success": True,
                    "campaign": {
                        "id": campaign.id,
                        "campaign_id": campaign.campaign_id,
                        "name": campaign.name,
                        "status": campaign.status.value,
                        "campaign_type": campaign.campaign_type.value,
                        "platforms": campaign.platforms,
                        "budget": campaign.budget,
                        "created_at": campaign.created_at.isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_campaign_details(self, campaign_id: int) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieMarketingCampaign).where(JackieMarketingCampaign.id == campaign_id)
                result = await session.execute(query)
                campaign = result.scalar_one_or_none()
                
                if not campaign:
                    return {"success": False, "error": "Campaign not found"}
                
                return {
                    "success": True,
                    "campaign": {
                        "id": campaign.id,
                        "campaign_id": campaign.campaign_id,
                        "user_id": campaign.user_id,
                        "name": campaign.name,
                        "description": campaign.description,
                        "campaign_type": campaign.campaign_type.value,
                        "status": campaign.status.value,
                        "platforms": campaign.platforms,
                        "target_audience": campaign.target_audience,
                        "budget": campaign.budget,
                        "spent_budget": campaign.spent_budget,
                        "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
                        "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
                        "goals": campaign.goals,
                        "kpis": campaign.kpis,
                        "performance_metrics": campaign.performance_metrics,
                        "ai_optimization_settings": campaign.ai_optimization_settings,
                        "brand_voice_settings": campaign.brand_voice_settings,
                        "created_at": campaign.created_at.isoformat(),
                        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get campaign details: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_campaign(
        self,
        campaign_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[CampaignStatus] = None,
        budget: Optional[float] = None,
        target_audience: Optional[Dict[str, Any]] = None,
        goals: Optional[Dict[str, Any]] = None,
        kpis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieMarketingCampaign).where(JackieMarketingCampaign.id == campaign_id)
                result = await session.execute(query)
                campaign = result.scalar_one_or_none()
                
                if not campaign:
                    return {"success": False, "error": "Campaign not found"}
                
                update_data = {}
                if name is not None:
                    update_data["name"] = name
                if description is not None:
                    update_data["description"] = description
                if status is not None:
                    update_data["status"] = status
                if budget is not None:
                    update_data["budget"] = budget
                if target_audience is not None:
                    update_data["target_audience"] = target_audience
                if goals is not None:
                    update_data["goals"] = goals
                if kpis is not None:
                    update_data["kpis"] = kpis
                
                if update_data:
                    stmt = update(JackieMarketingCampaign).where(JackieMarketingCampaign.id == campaign_id).values(**update_data)
                    await session.execute(stmt)
                    await session.commit()
                
                await self.event_bus.publish(
                    "marketing.campaign.updated",
                    {
                        "campaign_id": campaign_id,
                        "user_id": campaign.user_id,
                        "updates": update_data
                    }
                )
                
                return {"success": True, "message": "Campaign updated successfully"}
                
        except Exception as e:
            logger.error(f"Failed to update campaign: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_campaign(self, campaign_id: int) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieMarketingCampaign).where(JackieMarketingCampaign.id == campaign_id)
                result = await session.execute(query)
                campaign = result.scalar_one_or_none()
                
                if not campaign:
                    return {"success": False, "error": "Campaign not found"}
                
                stmt = delete(JackieMarketingCampaign).where(JackieMarketingCampaign.id == campaign_id)
                await session.execute(stmt)
                await session.commit()
                
                await self.event_bus.publish(
                    "marketing.campaign.deleted",
                    {
                        "campaign_id": campaign_id,
                        "user_id": campaign.user_id
                    }
                )
                
                return {"success": True, "message": "Campaign deleted successfully"}
                
        except Exception as e:
            logger.error(f"Failed to delete campaign: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_campaigns(
        self,
        user_id: int,
        status: Optional[CampaignStatus] = None,
        campaign_type: Optional[CampaignType] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieMarketingCampaign).where(JackieMarketingCampaign.user_id == user_id)
                
                if status:
                    query = query.where(JackieMarketingCampaign.status == status)
                if campaign_type:
                    query = query.where(JackieMarketingCampaign.campaign_type == campaign_type)
                
                query = query.offset(offset).limit(limit)
                result = await session.execute(query)
                campaigns = result.scalars().all()
                
                campaign_list = []
                for campaign in campaigns:
                    campaign_list.append({
                        "id": campaign.id,
                        "campaign_id": campaign.campaign_id,
                        "name": campaign.name,
                        "campaign_type": campaign.campaign_type.value,
                        "status": campaign.status.value,
                        "platforms": campaign.platforms,
                        "budget": campaign.budget,
                        "spent_budget": campaign.spent_budget,
                        "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
                        "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
                        "created_at": campaign.created_at.isoformat()
                    })
                
                return {
                    "success": True,
                    "campaigns": campaign_list,
                    "total": len(campaign_list),
                    "limit": limit,
                    "offset": offset
                }
                
        except Exception as e:
            logger.error(f"Failed to list campaigns: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_campaign(self, campaign_id: int) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieMarketingCampaign).where(JackieMarketingCampaign.id == campaign_id)
                result = await session.execute(query)
                campaign = result.scalar_one_or_none()
                
                if not campaign:
                    return {"success": False, "error": "Campaign not found"}
                
                optimization_result = await self._perform_ai_optimization(campaign)
                
                await self.event_bus.publish(
                    "marketing.campaign.optimized",
                    {
                        "campaign_id": campaign_id,
                        "user_id": campaign.user_id,
                        "optimization_result": optimization_result
                    }
                )
                
                return {
                    "success": True,
                    "optimization_result": optimization_result
                }
                
        except Exception as e:
            logger.error(f"Failed to optimize campaign: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_campaign_analytics(
        self,
        campaign_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieCampaignAnalytics).where(JackieCampaignAnalytics.campaign_id == campaign_id)
                
                if start_date:
                    start_dt = datetime.fromisoformat(start_date)
                    query = query.where(JackieCampaignAnalytics.date >= start_dt)
                if end_date:
                    end_dt = datetime.fromisoformat(end_date)
                    query = query.where(JackieCampaignAnalytics.date <= end_dt)
                
                result = await session.execute(query)
                analytics = result.scalars().all()
                
                analytics_data = []
                for analytic in analytics:
                    analytics_data.append({
                        "date": analytic.date.isoformat(),
                        "impressions": analytic.impressions,
                        "clicks": analytic.clicks,
                        "conversions": analytic.conversions,
                        "spend": analytic.spend,
                        "ctr": analytic.ctr,
                        "cpc": analytic.cpc,
                        "cpm": analytic.cpm,
                        "roas": analytic.roas,
                        "engagement_rate": analytic.engagement_rate,
                        "reach": analytic.reach,
                        "frequency": analytic.frequency,
                        "platform_metrics": analytic.platform_metrics
                    })
                
                return {
                    "success": True,
                    "analytics": analytics_data,
                    "summary": await self._calculate_analytics_summary(analytics_data)
                }
                
        except Exception as e:
            logger.error(f"Failed to get campaign analytics: {e}")
            return {"success": False, "error": str(e)}
    
    async def duplicate_campaign(self, campaign_id: int, new_name: str) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieMarketingCampaign).where(JackieMarketingCampaign.id == campaign_id)
                result = await session.execute(query)
                original_campaign = result.scalar_one_or_none()
                
                if not original_campaign:
                    return {"success": False, "error": "Campaign not found"}
                
                new_campaign_id = f"CAMP_{uuid.uuid4().hex[:8].upper()}"
                
                new_campaign = JackieMarketingCampaign(
                    campaign_id=new_campaign_id,
                    user_id=original_campaign.user_id,
                    name=new_name,
                    description=original_campaign.description,
                    campaign_type=original_campaign.campaign_type,
                    status=CampaignStatus.DRAFT,
                    platforms=original_campaign.platforms,
                    target_audience=original_campaign.target_audience,
                    budget=original_campaign.budget,
                    start_date=None,
                    end_date=None,
                    goals=original_campaign.goals,
                    kpis=original_campaign.kpis,
                    performance_metrics={},
                    ai_optimization_settings=original_campaign.ai_optimization_settings,
                    brand_voice_settings=original_campaign.brand_voice_settings
                )
                
                session.add(new_campaign)
                await session.commit()
                await session.refresh(new_campaign)
                
                return {
                    "success": True,
                    "campaign": {
                        "id": new_campaign.id,
                        "campaign_id": new_campaign.campaign_id,
                        "name": new_campaign.name,
                        "status": new_campaign.status.value
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to duplicate campaign: {e}")
            return {"success": False, "error": str(e)}
    
    async def schedule_campaign(self, campaign_id: int, scheduled_time: str) -> Dict[str, Any]:
        try:
            scheduled_dt = datetime.fromisoformat(scheduled_time)
            
            async with self.db.get_session() as session:
                stmt = update(JackieMarketingCampaign).where(JackieMarketingCampaign.id == campaign_id).values(
                    status=CampaignStatus.SCHEDULED,
                    start_date=scheduled_dt
                )
                await session.execute(stmt)
                await session.commit()
                
                return {"success": True, "message": "Campaign scheduled successfully"}
                
        except Exception as e:
            logger.error(f"Failed to schedule campaign: {e}")
            return {"success": False, "error": str(e)}
    
    async def pause_campaign(self, campaign_id: int) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                stmt = update(JackieMarketingCampaign).where(JackieMarketingCampaign.id == campaign_id).values(
                    status=CampaignStatus.PAUSED
                )
                await session.execute(stmt)
                await session.commit()
                
                return {"success": True, "message": "Campaign paused successfully"}
                
        except Exception as e:
            logger.error(f"Failed to pause campaign: {e}")
            return {"success": False, "error": str(e)}
    
    async def resume_campaign(self, campaign_id: int) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                stmt = update(JackieMarketingCampaign).where(JackieMarketingCampaign.id == campaign_id).values(
                    status=CampaignStatus.ACTIVE
                )
                await session.execute(stmt)
                await session.commit()
                
                return {"success": True, "message": "Campaign resumed successfully"}
                
        except Exception as e:
            logger.error(f"Failed to resume campaign: {e}")
            return {"success": False, "error": str(e)}
    
    async def _perform_ai_optimization(self, campaign: JackieMarketingCampaign) -> Dict[str, Any]:
        optimization_suggestions = []
        
        if campaign.spent_budget > 0 and campaign.budget > 0:
            budget_utilization = campaign.spent_budget / campaign.budget
            if budget_utilization > 0.8:
                optimization_suggestions.append({
                    "type": "budget_optimization",
                    "suggestion": "Consider increasing budget or optimizing ad spend allocation",
                    "priority": "high"
                })
        
        if campaign.performance_metrics:
            roas = campaign.performance_metrics.get("roas", 0)
            if roas < 2.0:
                optimization_suggestions.append({
                    "type": "performance_optimization",
                    "suggestion": "Optimize targeting and ad creative to improve ROAS",
                    "priority": "high"
                })
        
        return {
            "suggestions": optimization_suggestions,
            "optimized_at": datetime.utcnow().isoformat()
        }
    
    async def _calculate_analytics_summary(self, analytics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not analytics_data:
            return {}
        
        total_impressions = sum(a["impressions"] for a in analytics_data)
        total_clicks = sum(a["clicks"] for a in analytics_data)
        total_conversions = sum(a["conversions"] for a in analytics_data)
        total_spend = sum(a["spend"] for a in analytics_data)
        
        avg_ctr = total_clicks / total_impressions if total_impressions > 0 else 0
        avg_cpc = total_spend / total_clicks if total_clicks > 0 else 0
        avg_roas = total_conversions * 100 / total_spend if total_spend > 0 else 0
        
        return {
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "total_spend": total_spend,
            "avg_ctr": avg_ctr,
            "avg_cpc": avg_cpc,
            "avg_roas": avg_roas
        }
