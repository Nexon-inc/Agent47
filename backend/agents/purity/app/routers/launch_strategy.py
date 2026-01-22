from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import PurityBusinessIdea, PurityLaunchStrategy, PurityBusinessModel, PurityMarketResearch
from ..services.launch_strategy_service import LaunchStrategyService

router = APIRouter(prefix="/launch-strategy", tags=["Launch Strategy"])

class LaunchStrategyRequest(BaseModel):
    business_idea_id: int
    target_market: str
    launch_budget: float = Field(..., ge=0)
    timeline_months: int = Field(6, ge=1, le=24)
    launch_channels: List[str]
    success_metrics: List[str]
    risk_factors: Optional[List[str]] = None

class LaunchStrategyResponse(BaseModel):
    id: int
    business_idea_id: int
    target_market: str
    launch_budget: float
    timeline_months: int
    launch_channels: List[str]
    success_metrics: List[str]
    mvp_blueprint: dict
    go_to_market_strategy: dict
    launch_timeline: List[dict]
    risk_mitigation_plan: dict
    launch_roi_projection: float
    created_at: datetime
    updated_at: datetime

class MVPBlueprintRequest(BaseModel):
    business_idea_id: int
    development_budget: float = Field(..., ge=0)
    timeline_weeks: int = Field(12, ge=4, le=52)
    core_features: List[str]
    technical_requirements: Optional[List[str]] = None
    platform_preferences: Optional[List[str]] = None

class MVPBlueprintResponse(BaseModel):
    id: int
    business_idea_id: int
    development_budget: float
    timeline_weeks: int
    core_features: List[str]
    feature_prioritization: List[dict]
    technical_stack: List[str]
    development_phases: List[dict]
    resource_requirements: dict
    estimated_development_cost: float
    created_at: datetime

class GoToMarketRequest(BaseModel):
    business_idea_id: int
    target_customer_segments: List[str]
    value_proposition: str
    pricing_strategy: str
    distribution_channels: List[str]
    marketing_channels: List[str]

class GoToMarketResponse(BaseModel):
    id: int
    business_idea_id: int
    target_customer_segments: List[str]
    value_proposition: str
    pricing_strategy: str
    distribution_channels: List[str]
    marketing_channels: List[str]
    customer_acquisition_strategy: dict
    pricing_model: dict
    marketing_campaign_plan: dict
    sales_process: dict
    created_at: datetime

class LaunchTimelineRequest(BaseModel):
    business_idea_id: int
    launch_date: datetime
    pre_launch_activities: List[str]
    launch_activities: List[str]
    post_launch_activities: List[str]
    milestone_dates: Optional[dict] = None

class LaunchTimelineResponse(BaseModel):
    id: int
    business_idea_id: int
    launch_date: datetime
    pre_launch_activities: List[str]
    launch_activities: List[str]
    post_launch_activities: List[str]
    detailed_timeline: List[dict]
    milestone_tracking: dict
    resource_allocation: dict
    created_at: datetime

@router.post("/strategy", response_model=LaunchStrategyResponse)
async def create_launch_strategy(
    request: LaunchStrategyRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = LaunchStrategyService()
        strategy = await service.create_launch_strategy(
            db=db,
            business_idea_id=request.business_idea_id,
            target_market=request.target_market,
            launch_budget=request.launch_budget,
            timeline_months=request.timeline_months,
            launch_channels=request.launch_channels,
            success_metrics=request.success_metrics,
            risk_factors=request.risk_factors
        )
        return LaunchStrategyResponse(
            id=strategy.id,
            business_idea_id=strategy.business_idea_id,
            target_market=strategy.target_market,
            launch_budget=strategy.launch_budget,
            timeline_months=strategy.timeline_months,
            launch_channels=json.loads(strategy.launch_channels),
            success_metrics=json.loads(strategy.success_metrics),
            mvp_blueprint=json.loads(strategy.mvp_blueprint),
            go_to_market_strategy=json.loads(strategy.go_to_market_strategy),
            launch_timeline=json.loads(strategy.launch_timeline),
            risk_mitigation_plan=json.loads(strategy.risk_mitigation_plan),
            launch_roi_projection=strategy.launch_roi_projection,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/mvp-blueprint", response_model=MVPBlueprintResponse)
async def create_mvp_blueprint(
    request: MVPBlueprintRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = LaunchStrategyService()
        blueprint = await service.create_mvp_blueprint(
            db=db,
            business_idea_id=request.business_idea_id,
            development_budget=request.development_budget,
            timeline_weeks=request.timeline_weeks,
            core_features=request.core_features,
            technical_requirements=request.technical_requirements,
            platform_preferences=request.platform_preferences
        )
        return MVPBlueprintResponse(
            id=blueprint.id,
            business_idea_id=blueprint.business_idea_id,
            development_budget=blueprint.development_budget,
            timeline_weeks=blueprint.timeline_weeks,
            core_features=json.loads(blueprint.core_features),
            feature_prioritization=json.loads(blueprint.feature_prioritization),
            technical_stack=json.loads(blueprint.technical_stack),
            development_phases=json.loads(blueprint.development_phases),
            resource_requirements=json.loads(blueprint.resource_requirements),
            estimated_development_cost=blueprint.estimated_development_cost,
            created_at=blueprint.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/go-to-market", response_model=GoToMarketResponse)
async def create_go_to_market_strategy(
    request: GoToMarketRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = LaunchStrategyService()
        gtm_strategy = await service.create_go_to_market_strategy(
            db=db,
            business_idea_id=request.business_idea_id,
            target_customer_segments=request.target_customer_segments,
            value_proposition=request.value_proposition,
            pricing_strategy=request.pricing_strategy,
            distribution_channels=request.distribution_channels,
            marketing_channels=request.marketing_channels
        )
        return GoToMarketResponse(
            id=gtm_strategy.id,
            business_idea_id=gtm_strategy.business_idea_id,
            target_customer_segments=json.loads(gtm_strategy.target_customer_segments),
            value_proposition=gtm_strategy.value_proposition,
            pricing_strategy=gtm_strategy.pricing_strategy,
            distribution_channels=json.loads(gtm_strategy.distribution_channels),
            marketing_channels=json.loads(gtm_strategy.marketing_channels),
            customer_acquisition_strategy=json.loads(gtm_strategy.customer_acquisition_strategy),
            pricing_model=json.loads(gtm_strategy.pricing_model),
            marketing_campaign_plan=json.loads(gtm_strategy.marketing_campaign_plan),
            sales_process=json.loads(gtm_strategy.sales_process),
            created_at=gtm_strategy.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/timeline", response_model=LaunchTimelineResponse)
async def create_launch_timeline(
    request: LaunchTimelineRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = LaunchStrategyService()
        timeline = await service.create_launch_timeline(
            db=db,
            business_idea_id=request.business_idea_id,
            launch_date=request.launch_date,
            pre_launch_activities=request.pre_launch_activities,
            launch_activities=request.launch_activities,
            post_launch_activities=request.post_launch_activities,
            milestone_dates=request.milestone_dates
        )
        return LaunchTimelineResponse(
            id=timeline.id,
            business_idea_id=timeline.business_idea_id,
            launch_date=timeline.launch_date,
            pre_launch_activities=json.loads(timeline.pre_launch_activities),
            launch_activities=json.loads(timeline.launch_activities),
            post_launch_activities=json.loads(timeline.post_launch_activities),
            detailed_timeline=json.loads(timeline.detailed_timeline),
            milestone_tracking=json.loads(timeline.milestone_tracking),
            resource_allocation=json.loads(timeline.resource_allocation),
            created_at=timeline.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/strategy/{strategy_id}", response_model=LaunchStrategyResponse)
async def get_launch_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityLaunchStrategy).where(PurityLaunchStrategy.id == strategy_id))
        strategy = result.scalar_one_or_none()
        if not strategy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Launch strategy not found")
        return LaunchStrategyResponse(
            id=strategy.id,
            business_idea_id=strategy.business_idea_id,
            target_market=strategy.target_market,
            launch_budget=strategy.launch_budget,
            timeline_months=strategy.timeline_months,
            launch_channels=json.loads(strategy.launch_channels),
            success_metrics=json.loads(strategy.success_metrics),
            mvp_blueprint=json.loads(strategy.mvp_blueprint),
            go_to_market_strategy=json.loads(strategy.go_to_market_strategy),
            launch_timeline=json.loads(strategy.launch_timeline),
            risk_mitigation_plan=json.loads(strategy.risk_mitigation_plan),
            launch_roi_projection=strategy.launch_roi_projection,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/strategy/business/{business_idea_id}", response_model=List[LaunchStrategyResponse])
async def get_business_launch_strategies(
    business_idea_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityLaunchStrategy).where(PurityLaunchStrategy.business_idea_id == business_idea_id))
        strategies = result.scalars().all()
        return [
            LaunchStrategyResponse(
                id=strategy.id,
                business_idea_id=strategy.business_idea_id,
                target_market=strategy.target_market,
                launch_budget=strategy.launch_budget,
                timeline_months=strategy.timeline_months,
                launch_channels=json.loads(strategy.launch_channels),
                success_metrics=json.loads(strategy.success_metrics),
                mvp_blueprint=json.loads(strategy.mvp_blueprint),
                go_to_market_strategy=json.loads(strategy.go_to_market_strategy),
                launch_timeline=json.loads(strategy.launch_timeline),
                risk_mitigation_plan=json.loads(strategy.risk_mitigation_plan),
                launch_roi_projection=strategy.launch_roi_projection,
                created_at=strategy.created_at,
                updated_at=strategy.updated_at
            )
            for strategy in strategies
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/strategy/{strategy_id}", response_model=LaunchStrategyResponse)
async def update_launch_strategy(
    strategy_id: int,
    request: LaunchStrategyRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityLaunchStrategy).where(PurityLaunchStrategy.id == strategy_id))
        strategy = result.scalar_one_or_none()
        if not strategy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Launch strategy not found")
        
        service = LaunchStrategyService()
        updated_strategy = await service.update_launch_strategy(
            db=db,
            strategy_id=strategy_id,
            target_market=request.target_market,
            launch_budget=request.launch_budget,
            timeline_months=request.timeline_months,
            launch_channels=request.launch_channels,
            success_metrics=request.success_metrics,
            risk_factors=request.risk_factors
        )
        return LaunchStrategyResponse(
            id=updated_strategy.id,
            business_idea_id=updated_strategy.business_idea_id,
            target_market=updated_strategy.target_market,
            launch_budget=updated_strategy.launch_budget,
            timeline_months=updated_strategy.timeline_months,
            launch_channels=json.loads(updated_strategy.launch_channels),
            success_metrics=json.loads(updated_strategy.success_metrics),
            mvp_blueprint=json.loads(updated_strategy.mvp_blueprint),
            go_to_market_strategy=json.loads(updated_strategy.go_to_market_strategy),
            launch_timeline=json.loads(updated_strategy.launch_timeline),
            risk_mitigation_plan=json.loads(updated_strategy.risk_mitigation_plan),
            launch_roi_projection=updated_strategy.launch_roi_projection,
            created_at=updated_strategy.created_at,
            updated_at=updated_strategy.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/strategy/{strategy_id}")
async def delete_launch_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityLaunchStrategy).where(PurityLaunchStrategy.id == strategy_id))
        strategy = result.scalar_one_or_none()
        if not strategy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Launch strategy not found")
        await db.delete(strategy)
        await db.commit()
        return {"message": "Launch strategy deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/mvp-blueprint/{blueprint_id}", response_model=MVPBlueprintResponse)
async def get_mvp_blueprint(
    blueprint_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityLaunchStrategy).where(PurityLaunchStrategy.id == blueprint_id))
        blueprint = result.scalar_one_or_none()
        if not blueprint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MVP blueprint not found")
        return MVPBlueprintResponse(
            id=blueprint.id,
            business_idea_id=blueprint.business_idea_id,
            development_budget=blueprint.development_budget,
            timeline_weeks=blueprint.timeline_weeks,
            core_features=json.loads(blueprint.core_features),
            feature_prioritization=json.loads(blueprint.feature_prioritization),
            technical_stack=json.loads(blueprint.technical_stack),
            development_phases=json.loads(blueprint.development_phases),
            resource_requirements=json.loads(blueprint.resource_requirements),
            estimated_development_cost=blueprint.estimated_development_cost,
            created_at=blueprint.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/go-to-market/{gtm_id}", response_model=GoToMarketResponse)
async def get_go_to_market_strategy(
    gtm_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityLaunchStrategy).where(PurityLaunchStrategy.id == gtm_id))
        gtm_strategy = result.scalar_one_or_none()
        if not gtm_strategy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Go-to-market strategy not found")
        return GoToMarketResponse(
            id=gtm_strategy.id,
            business_idea_id=gtm_strategy.business_idea_id,
            target_customer_segments=json.loads(gtm_strategy.target_customer_segments),
            value_proposition=gtm_strategy.value_proposition,
            pricing_strategy=gtm_strategy.pricing_strategy,
            distribution_channels=json.loads(gtm_strategy.distribution_channels),
            marketing_channels=json.loads(gtm_strategy.marketing_channels),
            customer_acquisition_strategy=json.loads(gtm_strategy.customer_acquisition_strategy),
            pricing_model=json.loads(gtm_strategy.pricing_model),
            marketing_campaign_plan=json.loads(gtm_strategy.marketing_campaign_plan),
            sales_process=json.loads(gtm_strategy.sales_process),
            created_at=gtm_strategy.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/timeline/{timeline_id}", response_model=LaunchTimelineResponse)
async def get_launch_timeline(
    timeline_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityLaunchStrategy).where(PurityLaunchStrategy.id == timeline_id))
        timeline = result.scalar_one_or_none()
        if not timeline:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Launch timeline not found")
        return LaunchTimelineResponse(
            id=timeline.id,
            business_idea_id=timeline.business_idea_id,
            launch_date=timeline.launch_date,
            pre_launch_activities=json.loads(timeline.pre_launch_activities),
            launch_activities=json.loads(timeline.launch_activities),
            post_launch_activities=json.loads(timeline.post_launch_activities),
            detailed_timeline=json.loads(timeline.detailed_timeline),
            milestone_tracking=json.loads(timeline.milestone_tracking),
            resource_allocation=json.loads(timeline.resource_allocation),
            created_at=timeline.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
