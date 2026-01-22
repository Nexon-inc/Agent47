from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.geo_campaign_service import GeoCampaignService
from ..models import AriaBrandProfile
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/geo-campaign", tags=["Geo-Specific AriaCampaign Planner"])

geo_campaign_service = GeoCampaignService()


@router.post("/create")
async def create_geo_campaign(
    brand_id: int,
    target_regions: List[str],
    campaign_type: str,
    content_theme: str,
    budget: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a geo-specific campaign targeting specific regions"""
    try:
        result = await geo_campaign_service.create_geo_campaign(
            brand_id=brand_id,
            target_regions=target_regions,
            campaign_type=campaign_type,
            content_theme=content_theme,
            budget=budget,
            start_date=start_date,
            end_date=end_date
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create geo-campaign: {str(e)}")


@router.get("/regions")
async def get_all_regions():
    """Get all available regions for campaign targeting"""
    try:
        result = await geo_campaign_service.get_all_regions()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get regions: {str(e)}")


@router.get("/regions/{region_name}")
async def get_region_insights(region_name: str):
    """Get detailed insights for a specific region"""
    try:
        result = await geo_campaign_service.get_region_insights(region_name)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get region insights: {str(e)}")


@router.post("/templates/{template_name}")
async def create_campaign_from_template(
    template_name: str,
    brand_id: int,
    target_regions: Optional[List[str]] = None,
    customizations: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a campaign from a predefined template"""
    try:
        result = await geo_campaign_service.create_campaign_from_template(
            brand_id=brand_id,
            template_name=template_name,
            target_regions=target_regions,
            customizations=customizations
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create campaign from template: {str(e)}")


@router.get("/templates")
async def get_available_templates():
    """Get all available campaign templates"""
    templates = {
        "african_cultural_celebration": {
            "name": "African Cultural Celebration",
            "description": "Celebrate African heritage and culture across multiple regions",
            "campaign_type": "cultural",
            "content_theme": "Celebrating African Heritage and Culture",
            "default_regions": ["kenya", "nigeria", "south_africa", "ghana"],
            "content_pillars": [
                "Traditional celebrations",
                "Modern African innovation",
                "Cultural heritage",
                "Community unity",
                "African excellence"
            ]
        },
        "african_business_spotlight": {
            "name": "African Business Spotlight",
            "description": "Showcase African business innovation and entrepreneurship",
            "campaign_type": "business",
            "content_theme": "Showcasing African Business Innovation",
            "default_regions": ["kenya", "nigeria", "south_africa", "ghana"],
            "content_pillars": [
                "Startup success stories",
                "Traditional business wisdom",
                "Innovation hubs",
                "Economic growth",
                "Business opportunities"
            ]
        },
        "african_tourism": {
            "name": "African Tourism Discovery",
            "description": "Promote African destinations and travel experiences",
            "campaign_type": "tourism",
            "content_theme": "Discovering African Destinations",
            "default_regions": ["kenya", "south_africa", "morocco", "egypt"],
            "content_pillars": [
                "Natural wonders",
                "Cultural experiences",
                "Adventure activities",
                "Local cuisine",
                "Historical sites"
            ]
        },
        "african_tech_innovation": {
            "name": "African Tech Innovation",
            "description": "Highlight African technology innovation and digital transformation",
            "campaign_type": "technology",
            "content_theme": "African Tech Innovation and Digital Transformation",
            "default_regions": ["kenya", "nigeria", "south_africa", "rwanda"],
            "content_pillars": [
                "Fintech solutions",
                "Digital inclusion",
                "Tech startups",
                "Innovation hubs",
                "Digital skills"
            ]
        }
    }
    
    return {
        "success": True,
        "templates": templates,
        "total_templates": len(templates)
    }


@router.get("/african-countries")
async def get_african_countries():
    """Get all African countries available for targeting"""
    try:
        result = await geo_campaign_service.get_all_regions()
        return {
            "success": True,
            "african_countries": result["african_regions"],
            "total_countries": len(result["african_regions"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get African countries: {str(e)}")


@router.get("/african-cities")
async def get_african_cities():
    """Get all African cities available for targeting"""
    try:
        result = await geo_campaign_service.get_all_regions()
        return {
            "success": True,
            "african_cities": result["african_cities"],
            "total_cities": len(result["african_cities"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get African cities: {str(e)}")


@router.get("/regions/{region_name}/hashtags")
async def get_region_hashtags(region_name: str):
    """Get popular hashtags for a specific region"""
    try:
        result = await geo_campaign_service.get_region_insights(region_name)
        
        if result["success"]:
            region_data = result["region"]
            hashtags = region_data.get("popular_hashtags", [])
            
            return {
                "success": True,
                "region": region_name,
                "hashtags": hashtags,
                "total_hashtags": len(hashtags),
                "primary_hashtags": hashtags[:3],
                "secondary_hashtags": hashtags[3:6] if len(hashtags) > 3 else []
            }
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get region hashtags: {str(e)}")


@router.get("/regions/{region_name}/posting-schedule")
async def get_region_posting_schedule(region_name: str):
    """Get optimal posting schedule for a specific region"""
    try:
        result = await geo_campaign_service.get_region_insights(region_name)
        
        if result["success"]:
            region_data = result["region"]
            timezone = region_data.get("timezone", "UTC")
            
            # Generate posting schedule based on region
            if "Africa" in timezone:
                schedule = {
                    "timezone": timezone,
                    "optimal_times": [
                        "08:00-10:00",  # Morning commute
                        "12:00-14:00",  # Lunch break
                        "17:00-19:00",  # Evening commute
                        "20:00-22:00"   # Evening relaxation
                    ],
                    "best_days": ["Monday", "Wednesday", "Friday", "Saturday"],
                    "frequency": "3-4 posts per week",
                    "content_mix": [
                        "Monday: Motivational/Start of week",
                        "Wednesday: Mid-week engagement",
                        "Friday: Weekend anticipation",
                        "Saturday: Community/entertainment"
                    ]
                }
            else:
                schedule = {
                    "timezone": timezone,
                    "optimal_times": [
                        "09:00-11:00",  # Morning
                        "13:00-15:00",  # Afternoon
                        "18:00-20:00",  # Evening
                        "21:00-23:00"   # Night
                    ],
                    "best_days": ["Tuesday", "Wednesday", "Thursday", "Saturday"],
                    "frequency": "4-5 posts per week",
                    "content_mix": [
                        "Tuesday: Educational/How-to",
                        "Wednesday: Hump day content",
                        "Thursday: Throwback/Inspiration",
                        "Saturday: Entertainment/Weekend"
                    ]
                }
            
            return {
                "success": True,
                "region": region_name,
                "posting_schedule": schedule
            }
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get posting schedule: {str(e)}")


@router.get("/regions/{region_name}/cultural-insights")
async def get_region_cultural_insights(region_name: str):
    """Get cultural insights and adaptation tips for a specific region"""
    try:
        result = await geo_campaign_service.get_region_insights(region_name)
        
        if result["success"]:
            return {
                "success": True,
                "region": region_name,
                "cultural_insights": result["insights"]
            }
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cultural insights: {str(e)}")
