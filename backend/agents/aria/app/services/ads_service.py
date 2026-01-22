from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx
from core.config import settings
from core.database.connection import get_supabase
from core.platforms.platform_manager import get_platform_manager
from ..models import AriaCampaign
import json


class AdsService:
    def __init__(self):
        self.platforms = None

    async def initialize(self):
        self.platforms = await get_platform_manager()

    async def create_instagram_ad_campaign(self, user_id: int, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Instagram ad campaign using Facebook Marketing API (free alternative)"""
        try:
            # Get user's Facebook/Instagram credentials
            credentials = await self._get_platform_credentials(user_id, "facebook")
            if not credentials:
                return {"success": False, "error": "Facebook credentials not found"}

            # Create campaign using Facebook Marketing API
            campaign_result = await self._create_facebook_campaign(
                credentials["access_token"],
                campaign_data,
                "instagram"
            )

            if campaign_result.get("success"):
                # Store campaign in database
                campaign_id = await self._store_campaign(user_id, campaign_data, "instagram", campaign_result)
                
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "platform": "instagram",
                    "facebook_campaign_id": campaign_result.get("campaign_id"),
                    "status": "created",
                    "message": "Instagram ad campaign created successfully"
                }
            else:
                return {"success": False, "error": campaign_result.get("error")}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_linkedin_ad_campaign(self, user_id: int, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create LinkedIn ad campaign using LinkedIn Ads API (free alternative)"""
        try:
            # Get user's LinkedIn credentials
            credentials = await self._get_platform_credentials(user_id, "linkedin")
            if not credentials:
                return {"success": False, "error": "LinkedIn credentials not found"}

            # Create campaign using LinkedIn Ads API
            campaign_result = await self._create_linkedin_campaign(
                credentials["access_token"],
                campaign_data
            )

            if campaign_result.get("success"):
                # Store campaign in database
                campaign_id = await self._store_campaign(user_id, campaign_data, "linkedin", campaign_result)
                
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "platform": "linkedin",
                    "linkedin_campaign_id": campaign_result.get("campaign_id"),
                    "status": "created",
                    "message": "LinkedIn ad campaign created successfully"
                }
            else:
                return {"success": False, "error": campaign_result.get("error")}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _create_facebook_campaign(self, access_token: str, campaign_data: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Create Facebook/Instagram campaign using Marketing API"""
        try:
            # Facebook Marketing API endpoints
            base_url = "https://graph.facebook.com/v18.0"
            
            # Step 1: Create AriaCampaign
            campaign_payload = {
                "name": campaign_data.get("name", "Instagram Ad AriaCampaign"),
                "objective": self._map_objective_to_facebook(campaign_data.get("objective", "AWARENESS")),
                "status": "PAUSED",  # Start paused for safety
                "special_ad_categories": [],
                "access_token": access_token
            }

            async with httpx.AsyncClient() as client:
                # Create campaign
                campaign_response = await client.post(
                    f"{base_url}/act_{campaign_data.get('ad_account_id', 'me')}/campaigns",
                    data=campaign_payload,
                    timeout=30.0
                )

                if campaign_response.status_code != 200:
                    return {"success": False, "error": f"AriaCampaign creation failed: {campaign_response.text}"}

                campaign_result = campaign_response.json()
                campaign_id = campaign_result.get("id")

                # Step 2: Create Ad Set
                adset_payload = {
                    "name": f"Ad Set for {campaign_data.get('name')}",
                    "campaign_id": campaign_id,
                    "daily_budget": campaign_data.get("daily_budget_cents", 1000),  # $10.00 in cents
                    "billing_event": "IMPRESSIONS",
                    "optimization_goal": self._map_optimization_goal(campaign_data.get("objective")),
                    "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
                    "targeting": self._build_facebook_targeting(campaign_data.get("targeting", {})),
                    "access_token": access_token
                }

                adset_response = await client.post(
                    f"{base_url}/act_{campaign_data.get('ad_account_id', 'me')}/adsets",
                    data=adset_payload,
                    timeout=30.0
                )

                if adset_response.status_code != 200:
                    return {"success": False, "error": f"Ad set creation failed: {adset_response.text}"}

                adset_result = adset_response.json()
                adset_id = adset_result.get("id")

                # Step 3: Create Ad Creative
                creative_payload = {
                    "name": f"Creative for {campaign_data.get('name')}",
                    "object_story_spec": {
                        "instagram": {
                            "image_hash": campaign_data.get("image_hash", ""),
                            "caption": campaign_data.get("caption", ""),
                            "link": campaign_data.get("website_url", "")
                        }
                    },
                    "access_token": access_token
                }

                creative_response = await client.post(
                    f"{base_url}/act_{campaign_data.get('ad_account_id', 'me')}/adcreatives",
                    data=creative_payload,
                    timeout=30.0
                )

                if creative_response.status_code != 200:
                    return {"success": False, "error": f"Creative creation failed: {creative_response.text}"}

                creative_result = creative_response.json()
                creative_id = creative_result.get("id")

                # Step 4: Create Ad
                ad_payload = {
                    "name": f"Ad for {campaign_data.get('name')}",
                    "adset_id": adset_id,
                    "creative": {"creative_id": creative_id},
                    "status": "PAUSED",
                    "access_token": access_token
                }

                ad_response = await client.post(
                    f"{base_url}/act_{campaign_data.get('ad_account_id', 'me')}/ads",
                    data=ad_payload,
                    timeout=30.0
                )

                if ad_response.status_code != 200:
                    return {"success": False, "error": f"Ad creation failed: {ad_response.text}"}

                ad_result = ad_response.json()

                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "adset_id": adset_id,
                    "creative_id": creative_id,
                    "ad_id": ad_result.get("id"),
                    "platform": platform,
                    "status": "created"
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _create_linkedin_campaign(self, access_token: str, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create LinkedIn campaign using LinkedIn Ads API"""
        try:
            # LinkedIn Ads API endpoints
            base_url = "https://api.linkedin.com/v2"
            
            # Step 1: Create AriaCampaign
            campaign_payload = {
                "name": campaign_data.get("name", "LinkedIn Ad AriaCampaign"),
                "campaignGroup": f"urn:li:sponsoredCampaignGroup:{campaign_data.get('campaign_group_id', 'default')}",
                "status": "PAUSED",  # Start paused for safety
                "format": "TEXT_AD",
                "objective": self._map_objective_to_linkedin(campaign_data.get("objective", "AWARENESS")),
                "targetingCriteria": self._build_linkedin_targeting(campaign_data.get("targeting", {})),
                "budget": {
                    "amount": campaign_data.get("daily_budget_cents", 1000),
                    "currency": "USD"
                }
            }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }

            async with httpx.AsyncClient() as client:
                # Create campaign
                campaign_response = await client.post(
                    f"{base_url}/adCampaigns",
                    json=campaign_payload,
                    headers=headers,
                    timeout=30.0
                )

                if campaign_response.status_code != 201:
                    return {"success": False, "error": f"AriaCampaign creation failed: {campaign_response.text}"}

                campaign_result = campaign_response.json()
                campaign_id = campaign_result.get("id")

                # Step 2: Create Ad
                ad_payload = {
                    "name": f"Ad for {campaign_data.get('name')}",
                    "campaign": f"urn:li:sponsoredCampaign:{campaign_id}",
                    "status": "PAUSED",
                    "format": "TEXT_AD",
                    "content": {
                        "text": campaign_data.get("caption", ""),
                        "title": campaign_data.get("headline", ""),
                        "landingPageUrl": campaign_data.get("website_url", "")
                    }
                }

                ad_response = await client.post(
                    f"{base_url}/ads",
                    json=ad_payload,
                    headers=headers,
                    timeout=30.0
                )

                if ad_response.status_code != 201:
                    return {"success": False, "error": f"Ad creation failed: {ad_response.text}"}

                ad_result = ad_response.json()

                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "ad_id": ad_result.get("id"),
                    "platform": "linkedin",
                    "status": "created"
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_platform_credentials(self, user_id: int, platform: str) -> Optional[Dict[str, Any]]:
        """Get user's platform credentials"""
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            from core.platforms.models import PlatformCredential, SocialPlatform
            
            # Get platform ID
            platform_query = select(SocialPlatform).where(SocialPlatform.name == platform)
            platform_result = await session.execute(platform_query)
            platform_obj = platform_result.scalar_one_or_none()
            
            if not platform_obj:
                return None
            
            # Get credentials
            cred_query = select(PlatformCredential).where(
                PlatformCredential.user_id == user_id,
                PlatformCredential.platform_id == platform_obj.id
            )
            cred_result = await session.execute(cred_query)
            credentials = cred_result.scalar_one_or_none()
            
            if credentials:
                return {
                    "access_token": credentials.access_token,
                    "platform": platform,
                    "status": credentials.status.value
                }
            
            return None

    async def _store_campaign(self, user_id: int, campaign_data: Dict[str, Any], platform: str, api_result: Dict[str, Any]) -> int:
        """Store campaign in database"""
        db = await get_supabase()
        async with db.get_session() as session:
            campaign = AriaCampaign(
                user_id=user_id,
                name=campaign_data.get("name", ""),
                objective=campaign_data.get("objective", ""),
                budget_cents=campaign_data.get("daily_budget_cents", 0),
                start_at=campaign_data.get("start_date"),
                end_at=campaign_data.get("end_date"),
                status="active",
                metrics={
                    "platform": platform,
                    "platform_campaign_id": api_result.get("campaign_id"),
                    "adset_id": api_result.get("adset_id"),
                    "creative_id": api_result.get("creative_id"),
                    "ad_id": api_result.get("ad_id"),
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            session.add(campaign)
            await session.commit()
            
            return campaign.id

    def _map_objective_to_facebook(self, objective: str) -> str:
        """Map campaign objective to Facebook objective"""
        mapping = {
            "AWARENESS": "BRAND_AWARENESS",
            "CONSIDERATION": "CONSIDERATION",
            "CONVERSIONS": "CONVERSIONS",
            "ENGAGEMENT": "POST_ENGAGEMENT",
            "LEADS": "LEAD_GENERATION",
            "SALES": "CONVERSIONS",
            "TRAFFIC": "LINK_CLICKS"
        }
        return mapping.get(objective.upper(), "BRAND_AWARENESS")

    def _map_objective_to_linkedin(self, objective: str) -> str:
        """Map campaign objective to LinkedIn objective"""
        mapping = {
            "AWARENESS": "BRAND_AWARENESS",
            "CONSIDERATION": "CONSIDERATION",
            "CONVERSIONS": "CONVERSIONS",
            "ENGAGEMENT": "ENGAGEMENT",
            "LEADS": "LEAD_GENERATION",
            "SALES": "CONVERSIONS",
            "TRAFFIC": "WEBSITE_TRAFFIC"
        }
        return mapping.get(objective.upper(), "BRAND_AWARENESS")

    def _map_optimization_goal(self, objective: str) -> str:
        """Map objective to Facebook optimization goal"""
        mapping = {
            "AWARENESS": "REACH",
            "CONSIDERATION": "LINK_CLICKS",
            "CONVERSIONS": "CONVERSIONS",
            "ENGAGEMENT": "POST_ENGAGEMENT",
            "LEADS": "LEAD_GENERATION",
            "SALES": "CONVERSIONS",
            "TRAFFIC": "LINK_CLICKS"
        }
        return mapping.get(objective.upper(), "REACH")

    def _build_facebook_targeting(self, targeting: Dict[str, Any]) -> Dict[str, Any]:
        """Build Facebook targeting criteria"""
        targeting_spec = {}
        
        if targeting.get("age_min"):
            targeting_spec["age_min"] = targeting["age_min"]
        if targeting.get("age_max"):
            targeting_spec["age_max"] = targeting["age_max"]
        if targeting.get("genders"):
            targeting_spec["genders"] = targeting["genders"]
        if targeting.get("geo_locations"):
            targeting_spec["geo_locations"] = targeting["geo_locations"]
        if targeting.get("interests"):
            targeting_spec["interests"] = targeting["interests"]
        if targeting.get("behaviors"):
            targeting_spec["behaviors"] = targeting["behaviors"]
        
        return targeting_spec

    def _build_linkedin_targeting(self, targeting: Dict[str, Any]) -> Dict[str, Any]:
        """Build LinkedIn targeting criteria"""
        targeting_spec = {}
        
        if targeting.get("age_min") or targeting.get("age_max"):
            targeting_spec["ageRanges"] = []
            if targeting.get("age_min") and targeting.get("age_max"):
                targeting_spec["ageRanges"].append({
                    "minimum": targeting["age_min"],
                    "maximum": targeting["age_max"]
                })
        
        if targeting.get("genders"):
            targeting_spec["genders"] = targeting["genders"]
        
        if targeting.get("locations"):
            targeting_spec["locations"] = targeting["locations"]
        
        if targeting.get("jobFunctions"):
            targeting_spec["jobFunctions"] = targeting["jobFunctions"]
        
        if targeting.get("industries"):
            targeting_spec["industries"] = targeting["industries"]
        
        return targeting_spec

    async def get_campaign_status(self, user_id: int, campaign_id: int) -> Dict[str, Any]:
        """Get campaign status and performance"""
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            from ..models import AriaCampaign
            
            query = select(AriaCampaign).where(AriaCampaign.id == campaign_id, AriaCampaign.user_id == user_id)
            result = await session.execute(query)
            campaign = result.scalar_one_or_none()
            
            if not campaign:
                return {"success": False, "error": "AriaCampaign not found"}
            
            return {
                "success": True,
                "campaign_id": campaign.id,
                "name": campaign.name,
                "objective": campaign.objective,
                "budget_cents": campaign.budget_cents,
                "status": campaign.status,
                "metrics": campaign.metrics,
                "start_at": campaign.start_at.isoformat() if campaign.start_at else None,
                "end_at": campaign.end_at.isoformat() if campaign.end_at else None
            }

    async def update_campaign_budget(self, user_id: int, campaign_id: int, new_budget_cents: int) -> Dict[str, Any]:
        """Update campaign budget"""
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            from ..models import AriaCampaign
            
            query = select(AriaCampaign).where(AriaCampaign.id == campaign_id, AriaCampaign.user_id == user_id)
            result = await session.execute(query)
            campaign = result.scalar_one_or_none()
            
            if not campaign:
                return {"success": False, "error": "AriaCampaign not found"}
            
            # Update budget
            campaign.budget_cents = new_budget_cents
            campaign.updated_at = datetime.utcnow()
            
            await session.commit()
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "new_budget_cents": new_budget_cents,
                "message": "AriaCampaign budget updated successfully"
            }

    async def pause_campaign(self, user_id: int, campaign_id: int) -> Dict[str, Any]:
        """Pause a campaign"""
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            from ..models import AriaCampaign
            
            query = select(AriaCampaign).where(AriaCampaign.id == campaign_id, AriaCampaign.user_id == user_id)
            result = await session.execute(query)
            campaign = result.scalar_one_or_none()
            
            if not campaign:
                return {"success": False, "error": "AriaCampaign not found"}
            
            # Update status
            campaign.status = "paused"
            campaign.updated_at = datetime.utcnow()
            
            await session.commit()
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "status": "paused",
                "message": "AriaCampaign paused successfully"
            }

    async def get_user_campaigns(self, user_id: int, status: str = None) -> Dict[str, Any]:
        """Get all campaigns for a user"""
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            from ..models import AriaCampaign
            
            query = select(AriaCampaign).where(AriaCampaign.user_id == user_id)
            if status:
                query = query.where(AriaCampaign.status == status)
            
            result = await session.execute(query)
            campaigns = result.scalars().all()
            
            campaign_list = []
            for campaign in campaigns:
                campaign_list.append({
                    "id": campaign.id,
                    "name": campaign.name,
                    "objective": campaign.objective,
                    "budget_cents": campaign.budget_cents,
                    "status": campaign.status,
                    "platform": campaign.metrics.get("platform") if campaign.metrics else None,
                    "start_at": campaign.start_at.isoformat() if campaign.start_at else None,
                    "end_at": campaign.end_at.isoformat() if campaign.end_at else None
                })
            
            return {
                "success": True,
                "campaigns": campaign_list,
                "total_campaigns": len(campaign_list)
            }


