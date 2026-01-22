import asyncio
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from core.utils.nlp_utils import NLPUtils
from core.event_bus.kafka_manager import EventBus
from ..database import get_jackie_database
from ..models import JackieAdCampaign, PlatformType

logger = logging.getLogger(__name__)

class AdsService:
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
    
    async def create_ad(
        self,
        user_id: int,
        platform: PlatformType,
        ad_type: str,
        ad_copy: str,
        targeting: Dict[str, Any],
        budget: float,
        bid_amount: float
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                ad_campaign = JackieAdCampaign(
                    campaign_id=None,
                    platform=platform,
                    ad_account_id="ad_account_123",
                    ad_campaign_id="campaign_456",
                    ad_set_id="adset_789",
                    ad_id="ad_101",
                    ad_type=ad_type,
                    ad_copy=ad_copy,
                    creative_urls=[],
                    targeting=targeting,
                    budget=budget,
                    bid_amount=bid_amount,
                    status="active",
                    performance_metrics={},
                    optimization_settings={
                        "auto_optimize": True,
                        "target_roas": 3.0
                    }
                )
                
                session.add(ad_campaign)
                await session.commit()
                await session.refresh(ad_campaign)
                
                await self.event_bus.publish(
                    "marketing.ad.created",
                    {
                        "ad_id": ad_campaign.id,
                        "user_id": user_id,
                        "platform": platform.value,
                        "ad_type": ad_type
                    }
                )
                
                return {
                    "success": True,
                    "ad": {
                        "id": ad_campaign.id,
                        "platform": ad_campaign.platform.value,
                        "ad_type": ad_campaign.ad_type,
                        "status": ad_campaign.status,
                        "budget": ad_campaign.budget,
                        "bid_amount": ad_campaign.bid_amount
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to create ad: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_ad(
        self,
        ad_id: int,
        optimization_type: str,
        target_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieAdCampaign).where(JackieAdCampaign.id == ad_id)
                result = await session.execute(query)
                ad = result.scalar_one_or_none()
                
                if not ad:
                    return {"success": False, "error": "Ad not found"}
                
                optimization_result = await self._perform_ad_optimization(
                    ad=ad,
                    optimization_type=optimization_type,
                    target_metrics=target_metrics
                )
                
                stmt = update(JackieAdCampaign).where(JackieAdCampaign.id == ad_id).values(
                    optimization_settings=optimization_result["settings"],
                    performance_metrics=optimization_result["metrics"]
                )
                await session.execute(stmt)
                await session.commit()
                
                return {
                    "success": True,
                    "optimization_result": optimization_result
                }
                
        except Exception as e:
            logger.error(f"Failed to optimize ad: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_ad_performance(self, ad_id: int) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieAdCampaign).where(JackieAdCampaign.id == ad_id)
                result = await session.execute(query)
                ad = result.scalar_one_or_none()
                
                if not ad:
                    return {"success": False, "error": "Ad not found"}
                
                return {
                    "success": True,
                    "ad_performance": {
                        "id": ad.id,
                        "platform": ad.platform.value,
                        "ad_type": ad.ad_type,
                        "status": ad.status,
                        "budget": ad.budget,
                        "bid_amount": ad.bid_amount,
                        "performance_metrics": ad.performance_metrics,
                        "optimization_settings": ad.optimization_settings
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get ad performance: {e}")
            return {"success": False, "error": str(e)}
    
    async def allocate_budget(
        self,
        campaign_id: int,
        platform: PlatformType,
        allocated_budget: float
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieAdCampaign).where(JackieAdCampaign.campaign_id == campaign_id)
                result = await session.execute(query)
                ads = result.scalars().all()
                
                if not ads:
                    return {"success": False, "error": "No ads found for campaign"}
                
                budget_per_ad = allocated_budget / len(ads)
                
                for ad in ads:
                    stmt = update(JackieAdCampaign).where(JackieAdCampaign.id == ad.id).values(
                        budget=budget_per_ad
                    )
                    await session.execute(stmt)
                
                await session.commit()
                
                return {
                    "success": True,
                    "budget_allocation": {
                        "campaign_id": campaign_id,
                        "platform": platform.value,
                        "total_budget": allocated_budget,
                        "budget_per_ad": budget_per_ad,
                        "ads_updated": len(ads)
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to allocate budget: {e}")
            return {"success": False, "error": str(e)}
    
    async def _perform_ad_optimization(
        self,
        ad: JackieAdCampaign,
        optimization_type: str,
        target_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        optimization_settings = ad.optimization_settings.copy()
        
        if optimization_type == "roas":
            target_roas = target_metrics.get("target_roas", 3.0)
            optimization_settings["target_roas"] = target_roas
            optimization_settings["auto_optimize"] = True
        
        elif optimization_type == "budget":
            new_budget = target_metrics.get("budget", ad.budget)
            optimization_settings["budget_limit"] = new_budget
        
        elif optimization_type == "targeting":
            new_targeting = target_metrics.get("targeting", {})
            optimization_settings["targeting_rules"] = new_targeting
        
        performance_metrics = {
            "impressions": 1000,
            "clicks": 50,
            "conversions": 5,
            "spend": ad.budget * 0.1,
            "ctr": 0.05,
            "cpc": ad.bid_amount,
            "roas": 3.2
        }
        
        return {
            "settings": optimization_settings,
            "metrics": performance_metrics,
            "optimization_type": optimization_type
        }
