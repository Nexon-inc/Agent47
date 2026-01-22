import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel, Field
import json

# NLPUtils removed - not used
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager
from core.analytics.analytics_manager import AnalyticsManager
from core.config import settings

from ..database import get_eric_database
from ..models import (
    EricLead, EricDeal, EricSalesActivity, EricSalesCampaign, EricSalesAnalytics,
    EricSalesForecast, EricSalesTeam, EricSalesRep
)

logger = logging.getLogger(__name__)

class FunnelStage(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    position: int
    conversion_rate: float = 0.0
    avg_days_in_stage: float = 0.0
    is_active: bool = True
    color: str = "#3B82F6"
    criteria: Dict[str, Any] = {}
    automation_rules: List[Dict[str, Any]] = []

class FunnelMetrics(BaseModel):
    total_leads: int
    conversion_rate: float
    avg_cycle_length: float
    revenue_per_lead: float
    stage_breakdown: Dict[str, Dict[str, Any]]
    bottlenecks: List[Dict[str, Any]]
    recommendations: List[str]

class SalesFunnelService:
    def __init__(self):
        # NLPUtils removed - not used
        self.ai_service_manager = None
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self.kafka_manager = KafkaManager()
        self.redis_manager = RedisManager()
        self.analytics_manager = AnalyticsManager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize sales funnel service"""
        if self._initialized:
            return
        
        try:
            from core.ai import get_ai_service_manager
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            await self.kafka_manager.initialize()
            await self.redis_manager.initialize()
            await self.analytics_manager.initialize()
            self._initialized = True
            logger.info("Sales funnel service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize sales funnel service: {e}")
            raise
        
    async def create_funnel_stage(self, stage_data: FunnelStage) -> FunnelStage:
        """Create a new funnel stage"""
        async with get_eric_database() as session:
            try:
                # Check if stage name already exists
                existing_stage = await session.execute(
                    select(EricSalesCampaign).where(
                        and_(
                            EricSalesCampaign.name == stage_data.name,
                            EricSalesCampaign.type == "funnel_stage"
                        )
                    )
                )
                
                if existing_stage.scalar_one_or_none():
                    raise ValueError(f"Funnel stage '{stage_data.name}' already exists")
                
                # Create funnel stage as a campaign
                funnel_stage = EricSalesCampaign(
                    name=stage_data.name,
                    description=stage_data.description,
                    type="funnel_stage",
                    status="active" if stage_data.is_active else "inactive",
                    metadata={
                        "position": stage_data.position,
                        "conversion_rate": stage_data.conversion_rate,
                        "avg_days_in_stage": stage_data.avg_days_in_stage,
                        "color": stage_data.color,
                        "criteria": stage_data.criteria,
                        "automation_rules": stage_data.automation_rules,
                        "created_at": datetime.utcnow().isoformat()
                    },
                    created_at=datetime.utcnow()
                )
                
                session.add(funnel_stage)
                await session.commit()
                await session.refresh(funnel_stage)
                
                # Update stage data with ID
                stage_data.id = funnel_stage.id
                
                # Publish event to Kafka
                await self.kafka_manager.publish_event(
                    "sales_funnel.stage_created",
                    {
                        "stage_id": funnel_stage.id,
                        "stage_name": stage_data.name,
                        "position": stage_data.position,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Created funnel stage: {stage_data.name}")
                return stage_data
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create funnel stage: {e}")
                raise
    
    async def get_funnel_stages(self, active_only: bool = True) -> List[FunnelStage]:
        """Get all funnel stages"""
        async with get_eric_database() as session:
            try:
                query = select(EricSalesCampaign).where(
                    and_(
                        EricSalesCampaign.type == "funnel_stage",
                        EricSalesCampaign.status == "active" if active_only else True
                    )
                ).order_by(asc(EricSalesCampaign.metadata['position'].astext.cast(int)))
                
                result = await session.execute(query)
                stages = result.scalars().all()
                
                funnel_stages = []
                for stage in stages:
                    metadata = stage.metadata or {}
                    funnel_stages.append(FunnelStage(
                        id=stage.id,
                        name=stage.name,
                        description=stage.description,
                        position=metadata.get("position", 0),
                        conversion_rate=metadata.get("conversion_rate", 0.0),
                        avg_days_in_stage=metadata.get("avg_days_in_stage", 0.0),
                        is_active=stage.status == "active",
                        color=metadata.get("color", "#3B82F6"),
                        criteria=metadata.get("criteria", {}),
                        automation_rules=metadata.get("automation_rules", [])
                    ))
                
                return funnel_stages
                
            except Exception as e:
                logger.error(f"Failed to get funnel stages: {e}")
                raise
    
    async def update_funnel_stage(self, stage_id: int, stage_data: FunnelStage) -> FunnelStage:
        """Update a funnel stage"""
        async with get_eric_database() as session:
            try:
                stage = await session.execute(
                    select(EricSalesCampaign).where(
                        and_(
                            EricSalesCampaign.id == stage_id,
                            EricSalesCampaign.type == "funnel_stage"
                        )
                    )
                )
                stage = stage.scalar_one_or_none()
                
                if not stage:
                    raise ValueError(f"Funnel stage with ID {stage_id} not found")
                
                # Update stage data
                stage.name = stage_data.name
                stage.description = stage_data.description
                stage.status = "active" if stage_data.is_active else "inactive"
                
                metadata = stage.metadata or {}
                metadata.update({
                    "position": stage_data.position,
                    "conversion_rate": stage_data.conversion_rate,
                    "avg_days_in_stage": stage_data.avg_days_in_stage,
                    "color": stage_data.color,
                    "criteria": stage_data.criteria,
                    "automation_rules": stage_data.automation_rules,
                    "updated_at": datetime.utcnow().isoformat()
                })
                stage.metadata = metadata
                
                await session.commit()
                await session.refresh(stage)
                
                # Update stage data with ID
                stage_data.id = stage.id
                
                # Publish event to Kafka
                await self.kafka_manager.publish_event(
                    "sales_funnel.stage_updated",
                    {
                        "stage_id": stage.id,
                        "stage_name": stage_data.name,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Updated funnel stage: {stage_data.name}")
                return stage_data
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update funnel stage: {e}")
                raise
    
    async def delete_funnel_stage(self, stage_id: int) -> bool:
        """Delete a funnel stage"""
        async with get_eric_database() as session:
            try:
                stage = await session.execute(
                    select(EricSalesCampaign).where(
                        and_(
                            EricSalesCampaign.id == stage_id,
                            EricSalesCampaign.type == "funnel_stage"
                        )
                    )
                )
                stage = stage.scalar_one_or_none()
                
                if not stage:
                    raise ValueError(f"Funnel stage with ID {stage_id} not found")
                
                # Check if stage has active deals
                active_deals = await session.execute(
                    select(func.count(EricDeal.id)).where(
                        and_(
                            EricDeal.stage == stage.name,
                            EricDeal.status.in_(["active", "negotiation", "proposal"])
                        )
                    )
                )
                
                if active_deals.scalar() > 0:
                    raise ValueError(f"Cannot delete stage '{stage.name}' - has active deals")
                
                await session.delete(stage)
                await session.commit()
                
                # Publish event to Kafka
                await self.kafka_manager.publish_event(
                    "sales_funnel.stage_deleted",
                    {
                        "stage_id": stage_id,
                        "stage_name": stage.name,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Deleted funnel stage: {stage.name}")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to delete funnel stage: {e}")
                raise
    
    async def get_funnel_metrics(self, date_range: Optional[Dict[str, str]] = None) -> FunnelMetrics:
        """Get comprehensive funnel metrics and analytics"""
        async with get_eric_database() as session:
            try:
                # Get date range
                if not date_range:
                    end_date = datetime.utcnow()
                    start_date = end_date - timedelta(days=30)
                else:
                    start_date = datetime.fromisoformat(date_range["start"])
                    end_date = datetime.fromisoformat(date_range["end"])
                
                # Get all deals in date range
                deals_query = select(EricDeal).where(
                    and_(
                        EricDeal.created_at >= start_date,
                        EricDeal.created_at <= end_date
                    )
                )
                deals_result = await session.execute(deals_query)
                deals = deals_result.scalars().all()
                
                # Get funnel stages
                stages = await self.get_funnel_stages()
                stage_names = [stage.name for stage in stages]
                
                # Calculate metrics
                total_leads = len(deals)
                closed_deals = [deal for deal in deals if deal.status == "closed"]
                conversion_rate = (len(closed_deals) / total_leads * 100) if total_leads > 0 else 0
                
                # Calculate average cycle length
                cycle_lengths = []
                for deal in closed_deals:
                    if deal.closed_at and deal.created_at:
                        cycle_length = (deal.closed_at - deal.created_at).days
                        cycle_lengths.append(cycle_length)
                
                avg_cycle_length = sum(cycle_lengths) / len(cycle_lengths) if cycle_lengths else 0
                
                # Calculate revenue per lead
                total_revenue = sum(deal.value for deal in closed_deals if deal.value)
                revenue_per_lead = total_revenue / total_leads if total_leads > 0 else 0
                
                # Stage breakdown
                stage_breakdown = {}
                for stage in stages:
                    stage_deals = [deal for deal in deals if deal.stage == stage.name]
                    stage_count = len(stage_deals)
                    stage_value = sum(deal.value for deal in stage_deals if deal.value)
                    
                    # Calculate stage conversion rate
                    next_stage_index = stage_names.index(stage.name) + 1
                    if next_stage_index < len(stage_names):
                        next_stage = stage_names[next_stage_index]
                        next_stage_deals = [deal for deal in deals if deal.stage == next_stage]
                        stage_conversion = (len(next_stage_deals) / stage_count * 100) if stage_count > 0 else 0
                    else:
                        stage_conversion = (len(closed_deals) / stage_count * 100) if stage_count > 0 else 0
                    
                    stage_breakdown[stage.name] = {
                        "count": stage_count,
                        "value": stage_value,
                        "conversion_rate": stage_conversion,
                        "avg_days": stage.avg_days_in_stage,
                        "color": stage.color
                    }
                
                # Identify bottlenecks
                bottlenecks = []
                for stage in stages:
                    if stage.name in stage_breakdown:
                        stage_data = stage_breakdown[stage.name]
                        if stage_data["conversion_rate"] < 20:  # Low conversion threshold
                            bottlenecks.append({
                                "stage": stage.name,
                                "issue": "Low conversion rate",
                                "current_rate": stage_data["conversion_rate"],
                                "recommendation": f"Optimize {stage.name} stage with better qualification or messaging"
                            })
                        
                        if stage_data["avg_days"] > 14:  # Long cycle threshold
                            bottlenecks.append({
                                "stage": stage.name,
                                "issue": "Long cycle time",
                                "current_days": stage_data["avg_days"],
                                "recommendation": f"Reduce time in {stage.name} stage with automation or better processes"
                            })
                
                # Generate recommendations
                recommendations = []
                if conversion_rate < 10:
                    recommendations.append("Overall conversion rate is low - review lead qualification process")
                if avg_cycle_length > 30:
                    recommendations.append("Sales cycle is too long - implement automation and better follow-up")
                if len(bottlenecks) > 2:
                    recommendations.append("Multiple bottlenecks detected - prioritize stage optimization")
                
                return FunnelMetrics(
                    total_leads=total_leads,
                    conversion_rate=conversion_rate,
                    avg_cycle_length=avg_cycle_length,
                    revenue_per_lead=revenue_per_lead,
                    stage_breakdown=stage_breakdown,
                    bottlenecks=bottlenecks,
                    recommendations=recommendations
                )
                
            except Exception as e:
                logger.error(f"Failed to get funnel metrics: {e}")
                raise
    
    async def move_deal_to_stage(self, deal_id: int, new_stage: str) -> bool:
        """Move a deal to a specific funnel stage"""
        async with get_eric_database() as session:
            try:
                deal = await session.execute(
                    select(EricDeal).where(EricDeal.id == deal_id)
                )
                deal = deal.scalar_one_or_none()
                
                if not deal:
                    raise ValueError(f"EricDeal with ID {deal_id} not found")
                
                # Validate stage exists
                stages = await self.get_funnel_stages()
                stage_names = [stage.name for stage in stages]
                
                if new_stage not in stage_names:
                    raise ValueError(f"Stage '{new_stage}' not found in funnel")
                
                # Update deal stage
                old_stage = deal.stage
                deal.stage = new_stage
                deal.updated_at = datetime.utcnow()
                
                # Create activity record
                activity = EricSalesActivity(
                    deal_id=deal.id,
                    type="stage_change",
                    description=f"Moved from {old_stage} to {new_stage}",
                    metadata={
                        "old_stage": old_stage,
                        "new_stage": new_stage,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    created_at=datetime.utcnow()
                )
                
                session.add(activity)
                await session.commit()
                
                # Publish event to Kafka
                await self.kafka_manager.publish_event(
                    "sales_funnel.deal_moved",
                    {
                        "deal_id": deal.id,
                        "old_stage": old_stage,
                        "new_stage": new_stage,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Moved deal {deal_id} from {old_stage} to {new_stage}")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to move deal to stage: {e}")
                raise
    
    async def get_funnel_visualization(self) -> Dict[str, Any]:
        """Get funnel visualization data for charts and graphs"""
        async with get_eric_database() as session:
            try:
                # Get funnel stages
                stages = await self.get_funnel_stages()
                
                # Get current deals by stage
                deals_by_stage = {}
                for stage in stages:
                    deals_query = select(EricDeal).where(
                        and_(
                            EricDeal.stage == stage.name,
                            EricDeal.status.in_(["active", "negotiation", "proposal"])
                        )
                    )
                    deals_result = await session.execute(deals_query)
                    deals = deals_result.scalars().all()
                    
                    deals_by_stage[stage.name] = {
                        "count": len(deals),
                        "value": sum(deal.value for deal in deals if deal.value),
                        "color": stage.color,
                        "position": stage.position
                    }
                
                # Get historical data for trends
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=90)
                
                historical_data = []
                for i in range(90):
                    date = start_date + timedelta(days=i)
                    next_date = date + timedelta(days=1)
                    
                    daily_deals = await session.execute(
                        select(EricDeal).where(
                            and_(
                                EricDeal.created_at >= date,
                                EricDeal.created_at < next_date
                            )
                        )
                    )
                    daily_deals = daily_deals.scalars().all()
                    
                    historical_data.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "total_leads": len(daily_deals),
                        "conversions": len([d for d in daily_deals if d.status == "closed"])
                    })
                
                return {
                    "stages": stages,
                    "current_data": deals_by_stage,
                    "historical_data": historical_data,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Failed to get funnel visualization: {e}")
                raise
    
    async def optimize_funnel_conversion(self, stage_name: str) -> Dict[str, Any]:
        """Analyze and optimize conversion for a specific funnel stage"""
        async with get_eric_database() as session:
            try:
                # Get deals in the stage
                stage_deals = await session.execute(
                    select(EricDeal).where(EricDeal.stage == stage_name)
                )
                stage_deals = stage_deals.scalars().all()
                
                if not stage_deals:
                    return {"message": f"No deals found in stage '{stage_name}'"}
                
                # Analyze deal characteristics
                deal_values = [deal.value for deal in stage_deals if deal.value]
                avg_value = sum(deal_values) / len(deal_values) if deal_values else 0
                
                # Get activities for these deals
                deal_ids = [deal.id for deal in stage_deals]
                activities = await session.execute(
                    select(EricSalesActivity).where(
                        and_(
                            EricSalesActivity.deal_id.in_(deal_ids),
                            EricSalesActivity.created_at >= datetime.utcnow() - timedelta(days=30)
                        )
                    )
                )
                activities = activities.scalars().all()
                
                # Analyze activity patterns
                activity_types = {}
                for activity in activities:
                    activity_type = activity.type
                    if activity_type not in activity_types:
                        activity_types[activity_type] = 0
                    activity_types[activity_type] += 1
                
                # Generate optimization recommendations
                recommendations = []
                
                if len(stage_deals) > 50:
                    recommendations.append("High volume stage - consider automation for repetitive tasks")
                
                if avg_value < 1000:
                    recommendations.append("Low average deal value - focus on qualification and value proposition")
                
                if "email" in activity_types and activity_types["email"] < len(stage_deals) * 2:
                    recommendations.append("Low email activity - increase follow-up frequency")
                
                if "call" not in activity_types or activity_types["call"] < len(stage_deals) * 0.5:
                    recommendations.append("Low call activity - increase phone outreach")
                
                # Calculate potential improvements from historical data
                historical_conversion = await self._get_historical_conversion_rate(stage_name)
                current_conversion = historical_conversion.get("current_rate", 0.15)
                industry_benchmark = historical_conversion.get("industry_benchmark", 0.20)
                potential_improvement = min(industry_benchmark - current_conversion, 0.05)  # Cap at 5%
                
                return {
                    "stage": stage_name,
                    "deal_count": len(stage_deals),
                    "avg_deal_value": avg_value,
                    "activity_breakdown": activity_types,
                    "recommendations": recommendations,
                    "potential_conversion_improvement": potential_improvement,
                    "estimated_revenue_impact": avg_value * len(stage_deals) * potential_improvement
                }
                
            except Exception as e:
                logger.error(f"Failed to optimize funnel conversion: {e}")
                raise
    
    async def create_funnel_automation(self, stage_name: str, automation_rules: List[Dict[str, Any]]) -> bool:
        """Create automation rules for a funnel stage"""
        async with get_eric_database() as session:
            try:
                # Get the funnel stage
                stage = await session.execute(
                    select(EricSalesCampaign).where(
                        and_(
                            EricSalesCampaign.name == stage_name,
                            EricSalesCampaign.type == "funnel_stage"
                        )
                    )
                )
                stage = stage.scalar_one_or_none()
                
                if not stage:
                    raise ValueError(f"Funnel stage '{stage_name}' not found")
                
                # Update stage with automation rules
                metadata = stage.metadata or {}
                metadata["automation_rules"] = automation_rules
                metadata["automation_updated_at"] = datetime.utcnow().isoformat()
                stage.metadata = metadata
                
                await session.commit()
                
                # Publish event to Kafka
                await self.kafka_manager.publish_event(
                    "sales_funnel.automation_created",
                    {
                        "stage_name": stage_name,
                        "rules_count": len(automation_rules),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Created automation rules for stage: {stage_name}")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create funnel automation: {e}")
                raise
    
    async def get_funnel_performance_report(self, date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate comprehensive funnel performance report"""
        async with get_eric_database() as session:
            try:
                # Get funnel metrics
                metrics = await self.get_funnel_metrics(date_range)
                
                # Get team performance
                team_performance = await session.execute(
                    select(
                        EricSalesRep.name,
                        func.count(EricDeal.id).label("deals_count"),
                        func.sum(EricDeal.value).label("total_value"),
                        func.avg(EricDeal.value).label("avg_value")
                    ).select_from(EricDeal).join(EricSalesRep).group_by(EricSalesRep.id, EricSalesRep.name)
                )
                team_performance = team_performance.all()
                
                # Get top performing stages
                stages = await self.get_funnel_stages()
                stage_performance = []
                for stage in stages:
                    stage_deals = await session.execute(
                        select(EricDeal).where(EricDeal.stage == stage.name)
                    )
                    stage_deals = stage_deals.scalars().all()
                    
                    if stage_deals:
                        stage_performance.append({
                            "stage": stage.name,
                            "deals_count": len(stage_deals),
                            "total_value": sum(deal.value for deal in stage_deals if deal.value),
                            "conversion_rate": stage.conversion_rate
                        })
                
                # Sort by performance
                stage_performance.sort(key=lambda x: x["total_value"], reverse=True)
                
                return {
                    "report_generated_at": datetime.utcnow().isoformat(),
                    "date_range": date_range or {"start": (datetime.utcnow() - timedelta(days=30)).isoformat(), "end": datetime.utcnow().isoformat()},
                    "overall_metrics": metrics,
                    "team_performance": [
                        {
                            "rep_name": row.name,
                            "deals_count": row.deals_count,
                            "total_value": row.total_value,
                            "avg_value": row.avg_value
                        }
                        for row in team_performance
                    ],
                    "top_stages": stage_performance[:5],
                    "bottlenecks": metrics.bottlenecks,
                    "recommendations": metrics.recommendations
                }
                
            except Exception as e:
                logger.error(f"Failed to generate funnel performance report: {e}")
                raise
