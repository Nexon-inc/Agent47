from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.account_analysis_service import AccountAnalysisService
from ..models import BrandProfile
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/account-analysis", tags=["Account Analysis"])

account_analysis_service = AccountAnalysisService()


@router.post("/analyze")
async def analyze_accounts(
    user_id: int,
    brand_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Analyze all connected social media accounts for a user/brand"""
    try:
        result = await account_analysis_service.analyze_accounts(
            user_id=user_id,
            brand_id=brand_id,
            db=db
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze accounts: {str(e)}")


@router.get("/summary/{user_id}")
async def get_account_summary(
    user_id: int,
    brand_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get a summary of account analysis without full details"""
    try:
        result = await account_analysis_service.analyze_accounts(
            user_id=user_id,
            brand_id=brand_id,
            db=db
        )
        
        if result["success"]:
            # Return only summary information
            return {
                "success": True,
                "summary": result["analysis_summary"],
                "brand_analysis": result["brand_analysis"],
                "recommendations": result["recommendations"],
                "action_plan": result["action_plan"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get account summary: {str(e)}")


@router.get("/health-score/{user_id}")
async def get_account_health_scores(
    user_id: int,
    brand_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get health scores for all accounts"""
    try:
        result = await account_analysis_service.analyze_accounts(
            user_id=user_id,
            brand_id=brand_id,
            db=db
        )
        
        if result["success"]:
            # Extract health scores
            health_scores = []
            for analysis in result["account_analyses"]:
                health_scores.append({
                    "platform": analysis.get("platform"),
                    "username": analysis.get("username"),
                    "health_score": analysis.get("health_score"),
                    "health_status": analysis.get("health_status"),
                    "total_posts": analysis.get("total_posts"),
                    "engagement_rate": analysis.get("engagement_rate")
                })
            
            return {
                "success": True,
                "overall_health_score": result["brand_analysis"]["overall_health_score"],
                "overall_health_status": result["brand_analysis"]["overall_health_status"],
                "account_health_scores": health_scores
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health scores: {str(e)}")


@router.get("/recommendations/{user_id}")
async def get_account_recommendations(
    user_id: int,
    brand_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get AI-powered recommendations for account improvement"""
    try:
        result = await account_analysis_service.analyze_accounts(
            user_id=user_id,
            brand_id=brand_id,
            db=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "recommendations": result["recommendations"],
                "action_plan": result["action_plan"],
                "next_steps": result["next_steps"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/platform-insights/{user_id}")
async def get_platform_insights(
    user_id: int,
    brand_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get platform-specific insights and recommendations"""
    try:
        result = await account_analysis_service.analyze_accounts(
            user_id=user_id,
            brand_id=brand_id,
            db=db
        )
        
        if result["success"]:
            # Extract platform insights
            platform_insights = {}
            for analysis in result["account_analyses"]:
                platform = analysis.get("platform")
                if platform:
                    platform_insights[platform] = {
                        "username": analysis.get("username"),
                        "health_score": analysis.get("health_score"),
                        "platform_insights": analysis.get("platform_insights"),
                        "recommendations": analysis.get("recommendations")
                    }
            
            return {
                "success": True,
                "platform_insights": platform_insights,
                "cross_platform_consistency": result["brand_analysis"]["cross_platform_consistency"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get platform insights: {str(e)}")


@router.get("/content-analysis/{user_id}")
async def get_content_analysis(
    user_id: int,
    brand_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get content performance analysis for all accounts"""
    try:
        result = await account_analysis_service.analyze_accounts(
            user_id=user_id,
            brand_id=brand_id,
            db=db
        )
        
        if result["success"]:
            # Extract content analysis
            content_analysis = []
            for analysis in result["account_analyses"]:
                content_analysis.append({
                    "platform": analysis.get("platform"),
                    "username": analysis.get("username"),
                    "content_analysis": analysis.get("content_analysis"),
                    "best_performing_content": analysis.get("content_analysis", {}).get("best_performing_content", [])
                })
            
            return {
                "success": True,
                "content_analysis": content_analysis,
                "overall_content_quality": result["brand_analysis"].get("content_performance", {})
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get content analysis: {str(e)}")


@router.get("/engagement-analysis/{user_id}")
async def get_engagement_analysis(
    user_id: int,
    brand_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get engagement pattern analysis for all accounts"""
    try:
        result = await account_analysis_service.analyze_accounts(
            user_id=user_id,
            brand_id=brand_id,
            db=db
        )
        
        if result["success"]:
            # Extract engagement analysis
            engagement_analysis = []
            for analysis in result["account_analyses"]:
                engagement_analysis.append({
                    "platform": analysis.get("platform"),
                    "username": analysis.get("username"),
                    "engagement_analysis": analysis.get("engagement_analysis"),
                    "peak_engagement_times": analysis.get("engagement_analysis", {}).get("peak_engagement_times", [])
                })
            
            return {
                "success": True,
                "engagement_analysis": engagement_analysis,
                "overall_engagement_trends": result["brand_analysis"].get("engagement_trends", "No data available")
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get engagement analysis: {str(e)}")


@router.get("/growth-potential/{user_id}")
async def get_growth_potential(
    user_id: int,
    brand_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get growth potential assessment for the brand"""
    try:
        result = await account_analysis_service.analyze_accounts(
            user_id=user_id,
            brand_id=brand_id,
            db=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "growth_potential": result["brand_analysis"]["brand_growth_potential"],
                "overall_health_score": result["brand_analysis"]["overall_health_score"],
                "total_followers": result["analysis_summary"]["total_followers"],
                "total_engagement": result["analysis_summary"]["total_engagement"],
                "engagement_rate": round(
                    (result["analysis_summary"]["total_engagement"] / result["analysis_summary"]["total_followers"] * 100) 
                    if result["analysis_summary"]["total_followers"] > 0 else 0, 2
                )
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get growth potential: {str(e)}")
