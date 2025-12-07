from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ..services.gamified_performance_service import GamifiedPerformanceService

router = APIRouter()

# Pydantic models for request/response
class LeaderboardRequest(BaseModel):
    period: str = "monthly"  # daily, weekly, monthly, yearly
    limit: int = 20
    category: Optional[str] = None

class AchievementsRequest(BaseModel):
    agent_id: int
    period: str = "all_time"  # daily, weekly, monthly, yearly, all_time

class TeamChallengesRequest(BaseModel):
    team_id: Optional[int] = None
    period: str = "monthly"  # weekly, monthly, quarterly

# Dependency
async def get_gamified_performance_service() -> GamifiedPerformanceService:
    service = GamifiedPerformanceService()
    await service.initialize()
    return service

@router.post("/leaderboard/agents", response_model=Dict[str, Any])
async def get_agent_leaderboard(
    request: LeaderboardRequest,
    service: GamifiedPerformanceService = Depends(get_gamified_performance_service)
):
    """Get agent performance leaderboard"""
    try:
        result = await service.get_agent_leaderboard(
            period=request.period,
            limit=request.limit,
            category=request.category
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/achievements/agent", response_model=Dict[str, Any])
async def get_agent_achievements(
    request: AchievementsRequest,
    service: GamifiedPerformanceService = Depends(get_gamified_performance_service)
):
    """Get agent achievements and milestones"""
    try:
        result = await service.get_agent_achievements(
            agent_id=request.agent_id,
            period=request.period
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/challenges/team", response_model=Dict[str, Any])
async def get_team_challenges(
    request: TeamChallengesRequest,
    service: GamifiedPerformanceService = Depends(get_gamified_performance_service)
):
    """Get team challenges and goals"""
    try:
        result = await service.get_team_challenges(
            team_id=request.team_id,
            period=request.period
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/overview", response_model=Dict[str, Any])
async def get_performance_overview(
    service: GamifiedPerformanceService = Depends(get_gamified_performance_service)
):
    """Get overview of gamified performance system"""
    try:
        # Get monthly leaderboard
        leaderboard_result = await service.get_agent_leaderboard(
            period="monthly",
            limit=10
        )
        
        # Get team challenges
        challenges_result = await service.get_team_challenges(period="monthly")
        
        overview = {
            "success": True,
            "performance_overview": {
                "top_agents": {
                    "available": leaderboard_result["success"],
                    "top_10": leaderboard_result.get("leaderboard", {}).get("top_agents", []) if leaderboard_result["success"] else []
                },
                "team_challenges": {
                    "available": challenges_result["success"],
                    "active_challenges": challenges_result.get("challenges", []) if challenges_result["success"] else [],
                    "overall_progress": challenges_result.get("overall_progress", 0) if challenges_result["success"] else 0
                }
            },
            "last_updated": "2024-01-01T00:00:00Z"  # This would be dynamic
        }
        
        return overview
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/achievements", response_model=Dict[str, Any])
async def get_achievement_statistics(
    service: GamifiedPerformanceService = Depends(get_gamified_performance_service)
):
    """Get achievement statistics across all agents"""
    try:
        # Get achievement statistics from the service
        stats = await service.get_achievement_statistics()
        
        return {
            "success": True,
            "achievement_statistics": stats
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/leaderboard", response_model=Dict[str, Any])
async def get_leaderboard_statistics(
    service: GamifiedPerformanceService = Depends(get_gamified_performance_service)
):
    """Get leaderboard statistics and trends"""
    try:
        # Get leaderboard statistics from the service
        stats = await service.get_leaderboard_statistics()
        
        return {
            "success": True,
            "leaderboard_statistics": stats
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
