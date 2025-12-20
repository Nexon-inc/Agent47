from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import asyncio
import json
from fastapi import HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..models import (
    SalesRep, Deal, SalesActivity, Lead, CustomerProfile,
    TeamPerformanceMetric, SalesAnalytics, SalesForecast
)
from ..database import get_eric_database
from core.event_bus.kafka_manager import EventBus as KafkaProducer
from core.cache.redis_manager import RedisManager
from core.config import settings


class TeamDashboardMetrics(BaseModel):
    total_revenue: float
    total_deals: int
    conversion_rate: float
    average_deal_size: float
    pipeline_value: float
    win_rate: float
    response_time_avg: float
    activities_completed: int
    leads_generated: int
    team_efficiency_score: float


class SalesRepPerformance(BaseModel):
    rep_id: int
    name: str
    revenue: float
    deals_count: int
    conversion_rate: float
    activities_completed: int
    response_time_avg: float
    efficiency_score: float
    rank: int


class TeamSalesDashboardService:
    def __init__(self):
        self.ai_service_manager = None
        try:
            self.kafka_producer = KafkaProducer()
        except Exception:
            self.kafka_producer = None

        try:
            from core.cache.redis_manager import redis_manager as RedisClient
            self.redis_client = RedisClient
        except Exception:
            self.redis_client = None
        self.cache_ttl = 300  # 5 minutes
        self._initialized = False
    
    async def initialize(self):
        """Initialize team sales dashboard service"""
        if self._initialized:
            return
        
        try:
            from core.ai import get_ai_service_manager
            self.ai_service_manager = await get_ai_service_manager()
            if self.kafka_producer:
                await self.kafka_producer.initialize()
            # redis_client is already initialized
            self._initialized = True
            logger.info("Team sales dashboard service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize team sales dashboard service: {e}")
            raise

    async def get_team_dashboard_metrics(
        self, 
        db: Session, 
        team_id: int,
        date_range: str = "30d"
    ) -> TeamDashboardMetrics:
        """Get comprehensive team dashboard metrics"""
        cache_key = f"team_dashboard_metrics:{team_id}:{date_range}"
        
        # Check cache first
        cached_data = await self.redis_client.get(cache_key)
        if cached_data:
            return TeamDashboardMetrics(**json.loads(cached_data))
        
        # Calculate date range
        end_date = datetime.now()
        if date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif date_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get team members
        team_members = db.query(SalesRep).filter(
            SalesRep.team_id == team_id
        ).all()
        
        if not team_members:
            raise HTTPException(status_code=404, detail="Team not found")
        
        rep_ids = [rep.id for rep in team_members]
        
        # Calculate metrics
        metrics = await self._calculate_team_metrics(db, rep_ids, start_date, end_date)
        
        # Cache results
        await self.redis_client.setex(
            cache_key, 
            self.cache_ttl, 
            json.dumps(metrics.dict())
        )
        
        return metrics

    async def get_sales_rep_performance(
        self, 
        db: Session, 
        team_id: int,
        date_range: str = "30d",
        sort_by: str = "revenue"
    ) -> List[SalesRepPerformance]:
        """Get individual sales rep performance with rankings"""
        cache_key = f"sales_rep_performance:{team_id}:{date_range}:{sort_by}"
        
        # Check cache first
        cached_data = await self.redis_client.get(cache_key)
        if cached_data:
            return [SalesRepPerformance(**item) for item in json.loads(cached_data)]
        
        # Calculate date range
        end_date = datetime.now()
        if date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif date_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get team members
        team_members = db.query(SalesRep).filter(
            SalesRep.team_id == team_id
        ).all()
        
        if not team_members:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Calculate individual performance
        performance_data = []
        for rep in team_members:
            rep_metrics = await self._calculate_rep_metrics(
                db, rep.id, start_date, end_date
            )
            performance_data.append(rep_metrics)
        
        # Sort by specified criteria
        if sort_by == "revenue":
            performance_data.sort(key=lambda x: x.revenue, reverse=True)
        elif sort_by == "deals_count":
            performance_data.sort(key=lambda x: x.deals_count, reverse=True)
        elif sort_by == "conversion_rate":
            performance_data.sort(key=lambda x: x.conversion_rate, reverse=True)
        elif sort_by == "efficiency_score":
            performance_data.sort(key=lambda x: x.efficiency_score, reverse=True)
        
        # Add rankings
        for i, performance in enumerate(performance_data):
            performance.rank = i + 1
        
        # Cache results
        await self.redis_client.setex(
            cache_key, 
            self.cache_ttl, 
            json.dumps([p.dict() for p in performance_data])
        )
        
        return performance_data

    async def get_real_time_updates(
        self, 
        db: Session, 
        team_id: int
    ) -> Dict[str, Any]:
        """Get real-time dashboard updates"""
        # Get recent activities (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        
        # Get team members
        team_members = db.query(SalesRep).filter(
            SalesRep.team_id == team_id
        ).all()
        
        if not team_members:
            raise HTTPException(status_code=404, detail="Team not found")
        
        rep_ids = [rep.id for rep in team_members]
        
        # Recent deals
        recent_deals = db.query(Deal).filter(
            and_(
                Deal.sales_rep_id.in_(rep_ids),
                Deal.created_at >= yesterday
            )
        ).all()
        
        # Recent activities
        recent_activities = db.query(SalesActivity).filter(
            and_(
                SalesActivity.sales_rep_id.in_(rep_ids),
                SalesActivity.created_at >= yesterday
            )
        ).all()
        
        # Recent leads
        recent_leads = db.query(Lead).filter(
            and_(
                Lead.assigned_to.in_(rep_ids),
                Lead.created_at >= yesterday
            )
        ).all()
        
        return {
            "recent_deals": len(recent_deals),
            "recent_activities": len(recent_activities),
            "recent_leads": len(recent_leads),
            "total_revenue_today": sum(deal.value for deal in recent_deals if deal.status == "closed"),
            "activities_by_type": self._group_activities_by_type(recent_activities),
            "deals_by_stage": self._group_deals_by_stage(recent_deals),
            "last_updated": datetime.now().isoformat()
        }

    async def get_pipeline_analytics(
        self, 
        db: Session, 
        team_id: int
    ) -> Dict[str, Any]:
        """Get detailed pipeline analytics"""
        # Get team members
        team_members = db.query(SalesRep).filter(
            SalesRep.team_id == team_id
        ).all()
        
        if not team_members:
            raise HTTPException(status_code=404, detail="Team not found")
        
        rep_ids = [rep.id for rep in team_members]
        
        # Get all active deals
        active_deals = db.query(Deal).filter(
            and_(
                Deal.sales_rep_id.in_(rep_ids),
                Deal.status.in_(["prospecting", "qualification", "proposal", "negotiation"])
            )
        ).all()
        
        # Pipeline stages
        stages = ["prospecting", "qualification", "proposal", "negotiation"]
        pipeline_data = {}
        
        for stage in stages:
            stage_deals = [deal for deal in active_deals if deal.status == stage]
            pipeline_data[stage] = {
                "count": len(stage_deals),
                "value": sum(deal.value for deal in stage_deals),
                "avg_value": sum(deal.value for deal in stage_deals) / len(stage_deals) if stage_deals else 0
            }
        
        # Conversion rates between stages
        conversion_rates = await self._calculate_stage_conversion_rates(db, rep_ids)
        
        # Velocity metrics
        velocity_metrics = await self._calculate_pipeline_velocity(db, rep_ids)
        
        return {
            "pipeline_stages": pipeline_data,
            "conversion_rates": conversion_rates,
            "velocity_metrics": velocity_metrics,
            "total_pipeline_value": sum(stage["value"] for stage in pipeline_data.values()),
            "total_deals_in_pipeline": sum(stage["count"] for stage in pipeline_data.values())
        }

    async def get_team_comparison(
        self, 
        db: Session, 
        team_id: int,
        comparison_period: str = "30d"
    ) -> Dict[str, Any]:
        """Compare team performance with previous period"""
        # Calculate date ranges
        end_date = datetime.now()
        if comparison_period == "7d":
            current_start = end_date - timedelta(days=7)
            previous_start = current_start - timedelta(days=7)
        elif comparison_period == "30d":
            current_start = end_date - timedelta(days=30)
            previous_start = current_start - timedelta(days=30)
        else:
            current_start = end_date - timedelta(days=30)
            previous_start = current_start - timedelta(days=30)
        
        # Get team members
        team_members = db.query(SalesRep).filter(
            SalesRep.team_id == team_id
        ).all()
        
        if not team_members:
            raise HTTPException(status_code=404, detail="Team not found")
        
        rep_ids = [rep.id for rep in team_members]
        
        # Current period metrics
        current_metrics = await self._calculate_team_metrics(
            db, rep_ids, current_start, end_date
        )
        
        # Previous period metrics
        previous_metrics = await self._calculate_team_metrics(
            db, rep_ids, previous_start, current_start
        )
        
        # Calculate changes
        changes = {}
        for field in current_metrics.dict().keys():
            current_value = getattr(current_metrics, field)
            previous_value = getattr(previous_metrics, field)
            
            if previous_value != 0:
                change_percent = ((current_value - previous_value) / previous_value) * 100
            else:
                change_percent = 0 if current_value == 0 else 100
            
            changes[field] = {
                "current": current_value,
                "previous": previous_value,
                "change_percent": change_percent,
                "trend": "up" if change_percent > 0 else "down" if change_percent < 0 else "stable"
            }
        
        return {
            "comparison_period": comparison_period,
            "changes": changes,
            "summary": {
                "improved_metrics": [k for k, v in changes.items() if v["trend"] == "up"],
                "declined_metrics": [k for k, v in changes.items() if v["trend"] == "down"],
                "stable_metrics": [k for k, v in changes.items() if v["trend"] == "stable"]
            }
        }

    async def export_dashboard_data(
        self, 
        db: Session, 
        team_id: int,
        date_range: str = "30d",
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export dashboard data for reporting"""
        # Get all dashboard data
        metrics = await self.get_team_dashboard_metrics(db, team_id, date_range)
        performance = await self.get_sales_rep_performance(db, team_id, date_range)
        pipeline = await self.get_pipeline_analytics(db, team_id)
        comparison = await self.get_team_comparison(db, team_id, date_range)
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "team_id": team_id,
            "date_range": date_range,
            "metrics": metrics.dict(),
            "performance": [p.dict() for p in performance],
            "pipeline": pipeline,
            "comparison": comparison
        }
        
        # Send to Kafka for processing
        await self.kafka_producer.send_message(
            "dashboard_export",
            {
                "team_id": team_id,
                "data": export_data,
                "format": format
            }
        )
        
        return {
            "export_id": f"export_{team_id}_{int(datetime.now().timestamp())}",
            "data": export_data,
            "format": format,
            "status": "exported"
        }

    async def _calculate_team_metrics(
        self, 
        db: Session, 
        rep_ids: List[int], 
        start_date: datetime, 
        end_date: datetime
    ) -> TeamDashboardMetrics:
        """Calculate comprehensive team metrics"""
        # Total revenue
        total_revenue = db.query(func.sum(Deal.value)).filter(
            and_(
                Deal.sales_rep_id.in_(rep_ids),
                Deal.status == "closed",
                Deal.closed_at >= start_date,
                Deal.closed_at <= end_date
            )
        ).scalar() or 0
        
        # Total deals
        total_deals = db.query(func.count(Deal.id)).filter(
            and_(
                Deal.sales_rep_id.in_(rep_ids),
                Deal.status == "closed",
                Deal.closed_at >= start_date,
                Deal.closed_at <= end_date
            )
        ).scalar() or 0
        
        # Total leads
        total_leads = db.query(func.count(Lead.id)).filter(
            and_(
                Lead.assigned_to.in_(rep_ids),
                Lead.created_at >= start_date,
                Lead.created_at <= end_date
            )
        ).scalar() or 0
        
        # Conversion rate
        conversion_rate = (total_deals / total_leads * 100) if total_leads > 0 else 0
        
        # Average deal size
        average_deal_size = total_revenue / total_deals if total_deals > 0 else 0
        
        # Pipeline value
        pipeline_value = db.query(func.sum(Deal.value)).filter(
            and_(
                Deal.sales_rep_id.in_(rep_ids),
                Deal.status.in_(["prospecting", "qualification", "proposal", "negotiation"])
            )
        ).scalar() or 0
        
        # Win rate
        closed_deals = db.query(func.count(Deal.id)).filter(
            and_(
                Deal.sales_rep_id.in_(rep_ids),
                Deal.status == "closed",
                Deal.closed_at >= start_date,
                Deal.closed_at <= end_date
            )
        ).scalar() or 0
        
        total_deals_attempted = db.query(func.count(Deal.id)).filter(
            and_(
                Deal.sales_rep_id.in_(rep_ids),
                Deal.created_at >= start_date,
                Deal.created_at <= end_date
            )
        ).scalar() or 0
        
        win_rate = (closed_deals / total_deals_attempted * 100) if total_deals_attempted > 0 else 0
        
        # Average response time
        activities = db.query(SalesActivity).filter(
            and_(
                SalesActivity.sales_rep_id.in_(rep_ids),
                SalesActivity.created_at >= start_date,
                SalesActivity.created_at <= end_date
            )
        ).all()
        
        response_times = []
        for activity in activities:
            if activity.response_time:
                response_times.append(activity.response_time)
        
        response_time_avg = sum(response_times) / len(response_times) if response_times else 0
        
        # Activities completed
        activities_completed = len(activities)
        
        # Team efficiency score
        efficiency_score = await self._calculate_team_efficiency_score(
            total_revenue, total_deals, conversion_rate, response_time_avg, activities_completed
        )
        
        return TeamDashboardMetrics(
            total_revenue=total_revenue,
            total_deals=total_deals,
            conversion_rate=conversion_rate,
            average_deal_size=average_deal_size,
            pipeline_value=pipeline_value,
            win_rate=win_rate,
            response_time_avg=response_time_avg,
            activities_completed=activities_completed,
            leads_generated=total_leads,
            team_efficiency_score=efficiency_score
        )

    async def _calculate_rep_metrics(
        self, 
        db: Session, 
        rep_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> SalesRepPerformance:
        """Calculate individual sales rep metrics"""
        # Get rep info
        rep = db.query(SalesRep).filter(SalesRep.id == rep_id).first()
        if not rep:
            raise HTTPException(status_code=404, detail="Sales rep not found")
        
        # Revenue
        revenue = db.query(func.sum(Deal.value)).filter(
            and_(
                Deal.sales_rep_id == rep_id,
                Deal.status == "closed",
                Deal.closed_at >= start_date,
                Deal.closed_at <= end_date
            )
        ).scalar() or 0
        
        # Deals count
        deals_count = db.query(func.count(Deal.id)).filter(
            and_(
                Deal.sales_rep_id == rep_id,
                Deal.status == "closed",
                Deal.closed_at >= start_date,
                Deal.closed_at <= end_date
            )
        ).scalar() or 0
        
        # Leads count
        leads_count = db.query(func.count(Lead.id)).filter(
            and_(
                Lead.assigned_to == rep_id,
                Lead.created_at >= start_date,
                Lead.created_at <= end_date
            )
        ).scalar() or 0
        
        # Conversion rate
        conversion_rate = (deals_count / leads_count * 100) if leads_count > 0 else 0
        
        # Activities completed
        activities_completed = db.query(func.count(SalesActivity.id)).filter(
            and_(
                SalesActivity.sales_rep_id == rep_id,
                SalesActivity.created_at >= start_date,
                SalesActivity.created_at <= end_date
            )
        ).scalar() or 0
        
        # Average response time
        activities = db.query(SalesActivity).filter(
            and_(
                SalesActivity.sales_rep_id == rep_id,
                SalesActivity.created_at >= start_date,
                SalesActivity.created_at <= end_date
            )
        ).all()
        
        response_times = []
        for activity in activities:
            if activity.response_time:
                response_times.append(activity.response_time)
        
        response_time_avg = sum(response_times) / len(response_times) if response_times else 0
        
        # Efficiency score
        efficiency_score = await self._calculate_rep_efficiency_score(
            revenue, deals_count, conversion_rate, response_time_avg, activities_completed
        )
        
        return SalesRepPerformance(
            rep_id=rep_id,
            name=f"{rep.first_name} {rep.last_name}",
            revenue=revenue,
            deals_count=deals_count,
            conversion_rate=conversion_rate,
            activities_completed=activities_completed,
            response_time_avg=response_time_avg,
            efficiency_score=efficiency_score,
            rank=0  # Will be set later
        )

    async def _calculate_team_efficiency_score(
        self, 
        revenue: float, 
        deals: int, 
        conversion_rate: float, 
        response_time: float, 
        activities: int
    ) -> float:
        """Calculate team efficiency score"""
        # Normalize metrics
        revenue_score = min(revenue / 100000, 1.0) * 25  # Max 25 points
        deals_score = min(deals / 50, 1.0) * 20  # Max 20 points
        conversion_score = min(conversion_rate / 20, 1.0) * 25  # Max 25 points
        response_score = max(0, (24 - response_time) / 24) * 20  # Max 20 points (24 hours max)
        activity_score = min(activities / 100, 1.0) * 10  # Max 10 points
        
        return revenue_score + deals_score + conversion_score + response_score + activity_score

    async def _calculate_rep_efficiency_score(
        self, 
        revenue: float, 
        deals: int, 
        conversion_rate: float, 
        response_time: float, 
        activities: int
    ) -> float:
        """Calculate individual rep efficiency score"""
        # Similar to team score but with individual thresholds
        revenue_score = min(revenue / 50000, 1.0) * 25
        deals_score = min(deals / 25, 1.0) * 20
        conversion_score = min(conversion_rate / 15, 1.0) * 25
        response_score = max(0, (12 - response_time) / 12) * 20  # 12 hours max
        activity_score = min(activities / 50, 1.0) * 10
        
        return revenue_score + deals_score + conversion_score + response_score + activity_score

    async def _calculate_stage_conversion_rates(
        self, 
        db: Session, 
        rep_ids: List[int]
    ) -> Dict[str, float]:
        """Calculate conversion rates between pipeline stages"""
        stages = ["prospecting", "qualification", "proposal", "negotiation", "closed"]
        conversion_rates = {}
        
        for i in range(len(stages) - 1):
            current_stage = stages[i]
            next_stage = stages[i + 1]
            
            # Count deals that moved from current to next stage
            moved_deals = db.query(func.count(Deal.id)).filter(
                and_(
                    Deal.sales_rep_id.in_(rep_ids),
                    Deal.status == next_stage,
                    Deal.stage_history.contains(current_stage)
                )
            ).scalar() or 0
            
            # Count total deals in current stage
            total_deals = db.query(func.count(Deal.id)).filter(
                and_(
                    Deal.sales_rep_id.in_(rep_ids),
                    Deal.status == current_stage
                )
            ).scalar() or 0
            
            rate = (moved_deals / total_deals * 100) if total_deals > 0 else 0
            conversion_rates[f"{current_stage}_to_{next_stage}"] = rate
        
        return conversion_rates

    async def _calculate_pipeline_velocity(
        self, 
        db: Session, 
        rep_ids: List[int]
    ) -> Dict[str, float]:
        """Calculate pipeline velocity metrics"""
        # Average time in each stage
        stages = ["prospecting", "qualification", "proposal", "negotiation"]
        velocity_metrics = {}
        
        for stage in stages:
            deals = db.query(Deal).filter(
                and_(
                    Deal.sales_rep_id.in_(rep_ids),
                    Deal.status == stage
                )
            ).all()
            
            if deals:
                total_days = sum(
                    (datetime.now() - deal.created_at).days 
                    for deal in deals
                )
                avg_days = total_days / len(deals)
                velocity_metrics[f"avg_days_in_{stage}"] = avg_days
            else:
                velocity_metrics[f"avg_days_in_{stage}"] = 0
        
        return velocity_metrics

    def _group_activities_by_type(self, activities: List[SalesActivity]) -> Dict[str, int]:
        """Group activities by type"""
        grouped = {}
        for activity in activities:
            activity_type = activity.activity_type
            grouped[activity_type] = grouped.get(activity_type, 0) + 1
        return grouped

    def _group_deals_by_stage(self, deals: List[Deal]) -> Dict[str, int]:
        """Group deals by stage"""
        grouped = {}
        for deal in deals:
            stage = deal.status
            grouped[stage] = grouped.get(stage, 0) + 1
        return grouped

    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service"""
        try:
            # Test Redis connection
            await self.redis_client.ping()
            redis_status = "healthy"
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"
        
        try:
            # Test Kafka connection
            await self.kafka_producer.send_message("health_check", {"service": "team_sales_dashboard"})
            kafka_status = "healthy"
        except Exception as e:
            kafka_status = f"unhealthy: {str(e)}"
        
        return {
            "service": "team_sales_dashboard",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "dependencies": {
                "redis": redis_status,
                "kafka": kafka_status
            }
        }
