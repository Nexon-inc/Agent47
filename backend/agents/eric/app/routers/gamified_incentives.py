from fastapi import APIRouter, HTTPException, Depends, Query, Body, Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
import json
from sqlalchemy import select

from ..services.gamified_incentives_service import GamifiedIncentivesService
from ..database import get_eric_database
from ..models import EricSalesRep

router = APIRouter()

class SalesChallengeRequest(BaseModel):
    title: str
    description: str
    challenge_type: str
    target_value: float
    start_date: str
    end_date: str
    reward_points: int
    reward_description: str
    participants: List[int] = []
    brand_id: int
    created_by: int

class PointsAwardRequest(BaseModel):
    rep_id: int
    points: int
    reason: str
    achievement_type: Optional[str] = None

class ChallengeResponse(BaseModel):
    success: bool
    challenge: Dict[str, Any]

class LeaderboardResponse(BaseModel):
    success: bool
    leaderboard: List[Dict[str, Any]]
    period: str
    last_updated: str

class PointsAwardResponse(BaseModel):
    success: bool
    award: Dict[str, Any]

class PerformanceResponse(BaseModel):
    success: bool
    performance: Dict[str, Any]

class TeamChallengesResponse(BaseModel):
    success: bool
    challenges: List[Dict[str, Any]]

@router.post("/gamification/challenges", response_model=ChallengeResponse)
async def create_sales_challenge(request: SalesChallengeRequest):
    """Create a new sales challenge for the team"""
    try:
        service = GamifiedIncentivesService()
        challenge_data = request.dict()
        result = await service.create_sales_challenge(challenge_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gamification/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    brand_id: int = Query(..., description="Brand ID"),
    period: str = Query("month", description="Time period (week, month, quarter, year)")
):
    """Get sales team leaderboard"""
    try:
        service = GamifiedIncentivesService()
        result = await service.get_leaderboard(brand_id, period)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gamification/award-points", response_model=PointsAwardResponse)
async def award_points(request: PointsAwardRequest):
    """Award points to a sales representative"""
    try:
        service = GamifiedIncentivesService()
        result = await service.award_points(
            request.rep_id,
            request.points,
            request.reason,
            request.achievement_type
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gamification/performance/{rep_id}", response_model=PerformanceResponse)
async def get_rep_performance(
    rep_id: int,
    period: str = Query("month", description="Time period (week, month, quarter, year)")
):
    """Get detailed performance for a sales representative"""
    try:
        service = GamifiedIncentivesService()
        result = await service.get_rep_performance(rep_id, period)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gamification/challenges", response_model=TeamChallengesResponse)
async def get_team_challenges(
    brand_id: int = Query(..., description="Brand ID")
):
    """Get active team challenges"""
    try:
        service = GamifiedIncentivesService()
        result = await service.get_team_challenges(brand_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gamification/achievements/{rep_id}")
async def get_rep_achievements(
    rep_id: int = Path(..., description="Sales Representative ID")
):
    """Get achievements for a sales representative"""
    try:
        service = GamifiedIncentivesService()
        achievements = await service._get_rep_achievements(rep_id)
        
        return {
            "success": True,
            "achievements": achievements
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gamification/points/{rep_id}")
async def get_rep_points(
    rep_id: int = Path(..., description="Sales Representative ID")
):
    """Get total points for a sales representative"""
    try:
        service = GamifiedIncentivesService()
        points_key = f"points:{rep_id}"
        points = await service.redis_manager.get(points_key)
        
        return {
            "success": True,
            "rep_id": rep_id,
            "total_points": int(points) if points else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gamification/achievement-types")
async def get_achievement_types():
    """Get available achievement types and their configurations"""
    try:
        service = GamifiedIncentivesService()
        
        return {
            "success": True,
            "achievement_types": service.achievement_types
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gamification/team-stats")
async def get_team_stats(
    brand_id: int = Query(..., description="Brand ID"),
    period: str = Query("month", description="Time period")
):
    """Get team-wide statistics for gamification"""
    try:
        service = GamifiedIncentivesService()
        db = await get_eric_database()
        async with db.get_session() as session:
            start_date = await service._get_period_start_date(period)
            
            sales_reps = await session.execute(
                select(EricSalesRep).where(EricSalesRep.brand_id == brand_id)
            )
            sales_reps = sales_reps.scalars().all()
            
            team_stats = {
                "total_reps": len(sales_reps),
                "total_points": 0,
                "total_achievements": 0,
                "top_performer": None,
                "average_points": 0
            }
            
            rep_points = []
            for rep in sales_reps:
                rep_stats = await service._calculate_rep_stats(session, rep.id, start_date)
                rep_achievements = await service._get_rep_achievements(rep.id)
                rep_points_total = await service._calculate_total_points(rep_stats, rep_achievements)
                
                rep_points.append({
                    "rep_id": rep.id,
                    "rep_name": f"{rep.first_name} {rep.last_name}",
                    "points": rep_points_total,
                    "achievements_count": len(rep_achievements)
                })
                
                team_stats["total_points"] += rep_points_total
                team_stats["total_achievements"] += len(rep_achievements)
            
            if rep_points:
                rep_points.sort(key=lambda x: x["points"], reverse=True)
                team_stats["top_performer"] = rep_points[0]
                team_stats["average_points"] = team_stats["total_points"] / len(rep_points)
            
            return {
                "success": True,
                "team_stats": team_stats,
                "rep_rankings": rep_points
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gamification/challenges/{challenge_id}/join")
async def join_challenge(
    challenge_id: str,
    rep_id: int = Query(..., description="Sales Representative ID")
):
    """Join a sales challenge"""
    try:
        service = GamifiedIncentivesService()
        challenge_key = f"challenge:{challenge_id}"
        challenge_data = await service.redis_manager.get(challenge_key)
        
        if not challenge_data:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        challenge = json.loads(challenge_data)
        
        if rep_id not in challenge["participants"]:
            challenge["participants"].append(rep_id)
            challenge["updated_at"] = datetime.utcnow()
            
            await service.redis_manager.set(
                challenge_key,
                json.dumps(challenge, default=str),
                expire=86400 * 30
            )
        
        return {
            "success": True,
            "message": "Successfully joined challenge",
            "challenge_id": challenge_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gamification/challenges/{challenge_id}/leave")
async def leave_challenge(
    challenge_id: str,
    rep_id: int = Query(..., description="Sales Representative ID")
):
    """Leave a sales challenge"""
    try:
        service = GamifiedIncentivesService()
        challenge_key = f"challenge:{challenge_id}"
        challenge_data = await service.redis_manager.get(challenge_key)
        
        if not challenge_data:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        challenge = json.loads(challenge_data)
        
        if rep_id in challenge["participants"]:
            challenge["participants"].remove(rep_id)
            challenge["updated_at"] = datetime.utcnow()
            
            await service.redis_manager.set(
                challenge_key,
                json.dumps(challenge, default=str),
                expire=86400 * 30
            )
        
        return {
            "success": True,
            "message": "Successfully left challenge",
            "challenge_id": challenge_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gamification/challenges/{challenge_id}/progress")
async def get_challenge_progress(
    challenge_id: str,
    brand_id: int = Query(..., description="Brand ID")
):
    """Get progress for a specific challenge"""
    try:
        service = GamifiedIncentivesService()
        challenge_key = f"challenge:{challenge_id}"
        challenge_data = await service.redis_manager.get(challenge_key)
        
        if not challenge_data:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        challenge = json.loads(challenge_data)
        
        if challenge["brand_id"] != brand_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        db = await get_eric_database()
        async with db.get_session() as session:
            progress_data = []
            
            for rep_id in challenge["participants"]:
                rep = await session.execute(
                    select(EricSalesRep).where(EricSalesRep.id == rep_id)
                )
                rep = rep.scalar_one_or_none()
                
                if rep:
                    start_date = datetime.fromisoformat(challenge["start_date"])
                    rep_stats = await service._calculate_rep_stats(session, rep_id, start_date)
                    
                    progress = {
                        "rep_id": rep_id,
                        "rep_name": f"{rep.first_name} {rep.last_name}",
                        "current_value": rep_stats.get(challenge["challenge_type"], 0),
                        "target_value": challenge["target_value"],
                        "progress_percentage": min(100, (rep_stats.get(challenge["challenge_type"], 0) / challenge["target_value"]) * 100)
                    }
                    
                    progress_data.append(progress)
            
            return {
                "success": True,
                "challenge": challenge,
                "progress": progress_data
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
