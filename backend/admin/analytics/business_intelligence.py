import asyncio
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid

from backend.core.database import get_database
from backend.core.cache import get_redis
from backend.core.logs import get_logger
from backend.core.config import get_config


class MetricPeriod(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class BusinessMetric(Enum):
    REVENUE = "revenue"
    USER_GROWTH = "user_growth"
    RETENTION = "retention"
    CONVERSION = "conversion"
    CHURN = "churn"
    LTV = "ltv"
    CAC = "cac"
    ARPU = "arpu"
    MRR = "mrr"
    ACTIVATION = "activation"


@dataclass
class BusinessKPI:
    metric: BusinessMetric
    value: float
    target: float
    period: MetricPeriod
    date: datetime
    trend: str
    change_percentage: float
    status: str  # "on_track", "at_risk", "behind"


@dataclass
class BusinessInsight:
    id: str
    insight_type: str
    title: str
    description: str
    impact_score: float
    confidence: float
    recommendation: str
    metrics_affected: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class Forecast:
    metric: BusinessMetric
    current_value: float
    forecast_value: float
    confidence_interval: Tuple[float, float]
    period: MetricPeriod
    forecast_date: datetime
    factors: List[str]


@dataclass
class BusinessReport:
    id: str
    report_type: str
    title: str
    summary: str
    period_start: datetime
    period_end: datetime
    kpis: List[BusinessKPI]
    insights: List[BusinessInsight]
    forecasts: List[Forecast]
    recommendations: List[str]
    generated_at: datetime


class BusinessIntelligence:
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()
        self.cache_ttl = 1800  # 30 minutes cache

    async def initialize(self):
        """Initialize the business intelligence system"""
        try:
            self.logger.info("BusinessIntelligence initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize BusinessIntelligence: {e}")
            raise

    async def get_business_kpis(self, period: MetricPeriod, 
                               date: Optional[datetime] = None) -> List[BusinessKPI]:
        """Get key business performance indicators"""
        try:
            if date is None:
                date = datetime.utcnow()
            
            # Check cache first
            cache_key = f"business_kpis:{period.value}:{date.date()}"
            cached_kpis = await self.redis.get(cache_key)
            if cached_kpis:
                return [BusinessKPI(**kpi) for kpi in cached_kpis]
            
            kpis = []
            
            # Revenue KPI
            revenue_kpi = await self._calculate_revenue_kpi(period, date)
            if revenue_kpi:
                kpis.append(revenue_kpi)
            
            # User Growth KPI
            user_growth_kpi = await self._calculate_user_growth_kpi(period, date)
            if user_growth_kpi:
                kpis.append(user_growth_kpi)
            
            # Retention KPI
            retention_kpi = await self._calculate_retention_kpi(period, date)
            if retention_kpi:
                kpis.append(retention_kpi)
            
            # Conversion KPI
            conversion_kpi = await self._calculate_conversion_kpi(period, date)
            if conversion_kpi:
                kpis.append(conversion_kpi)
            
            # Churn KPI
            churn_kpi = await self._calculate_churn_kpi(period, date)
            if churn_kpi:
                kpis.append(churn_kpi)
            
            # Cache the results
            await self.redis.set(cache_key, [kpi.__dict__ for kpi in kpis], expire=self.cache_ttl)
            
            return kpis
            
        except Exception as e:
            self.logger.error(f"Error getting business KPIs: {e}")
            return []

    async def _calculate_revenue_kpi(self, period: MetricPeriod, date: datetime) -> Optional[BusinessKPI]:
        """Calculate revenue KPI"""
        try:
            # Get current period revenue
            current_revenue = await self._get_revenue_for_period(period, date)
            
            # Get previous period revenue
            previous_date = self._get_previous_period_date(period, date)
            previous_revenue = await self._get_revenue_for_period(period, previous_date)
            
            # Calculate change percentage
            change_percentage = 0.0
            if previous_revenue > 0:
                change_percentage = ((current_revenue - previous_revenue) / previous_revenue) * 100
            
            # Determine trend
            trend = "stable"
            if change_percentage > 5:
                trend = "increasing"
            elif change_percentage < -5:
                trend = "decreasing"
            
            # Set target (example: 10% growth)
            target = previous_revenue * 1.10 if previous_revenue > 0 else current_revenue
            
            # Determine status
            status = "on_track"
            if change_percentage < 0:
                status = "behind"
            elif change_percentage < 5:
                status = "at_risk"
            
            return BusinessKPI(
                metric=BusinessMetric.REVENUE,
                value=current_revenue,
                target=target,
                period=period,
                date=date,
                trend=trend,
                change_percentage=change_percentage,
                status=status
            )
            
        except Exception as e:
            self.logger.warning(f"Could not calculate revenue KPI: {e}")
            return None

    async def _get_revenue_for_period(self, period: MetricPeriod, date: datetime) -> float:
        """Get revenue for a specific period"""
        try:
            start_date, end_date = self._get_period_dates(period, date)
            
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT COALESCE(SUM(amount), 0) as total_revenue
                    FROM payments
                    WHERE status = 'completed' 
                    AND created_at >= :start_date 
                    AND created_at <= :end_date
                """, {
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                row = result.fetchone()
                return float(row.total_revenue) if row else 0.0
                
        except Exception as e:
            self.logger.warning(f"Could not get revenue for period: {e}")
            return 0.0

    async def _calculate_user_growth_kpi(self, period: MetricPeriod, date: datetime) -> Optional[BusinessKPI]:
        """Calculate user growth KPI"""
        try:
            # Get current period user count
            current_users = await self._get_users_for_period(period, date)
            
            # Get previous period user count
            previous_date = self._get_previous_period_date(period, date)
            previous_users = await self._get_users_for_period(period, previous_date)
            
            # Calculate change percentage
            change_percentage = 0.0
            if previous_users > 0:
                change_percentage = ((current_users - previous_users) / previous_users) * 100
            
            # Determine trend
            trend = "stable"
            if change_percentage > 5:
                trend = "increasing"
            elif change_percentage < -5:
                trend = "decreasing"
            
            # Set target (example: 15% growth)
            target = previous_users * 1.15 if previous_users > 0 else current_users
            
            # Determine status
            status = "on_track"
            if change_percentage < 0:
                status = "behind"
            elif change_percentage < 5:
                status = "at_risk"
            
            return BusinessKPI(
                metric=BusinessMetric.USER_GROWTH,
                value=current_users,
                target=target,
                period=period,
                date=date,
                trend=trend,
                change_percentage=change_percentage,
                status=status
            )
            
        except Exception as e:
            self.logger.warning(f"Could not calculate user growth KPI: {e}")
            return None

    async def _get_users_for_period(self, period: MetricPeriod, date: datetime) -> int:
        """Get user count for a specific period"""
        try:
            start_date, end_date = self._get_period_dates(period, date)
            
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT COUNT(*) as user_count
                    FROM users
                    WHERE created_at >= :start_date AND created_at <= :end_date
                """, {
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                row = result.fetchone()
                return int(row.user_count) if row else 0
                
        except Exception as e:
            self.logger.warning(f"Could not get users for period: {e}")
            return 0

    async def _calculate_retention_kpi(self, period: MetricPeriod, date: datetime) -> Optional[BusinessKPI]:
        """Calculate retention KPI"""
        try:
            # Get retention rate for the period
            retention_rate = await self._get_retention_rate(period, date)
            
            # Get previous period retention
            previous_date = self._get_previous_period_date(period, date)
            previous_retention = await self._get_retention_rate(period, previous_date)
            
            # Calculate change percentage
            change_percentage = 0.0
            if previous_retention > 0:
                change_percentage = ((retention_rate - previous_retention) / previous_retention) * 100
            
            # Determine trend
            trend = "stable"
            if change_percentage > 2:
                trend = "increasing"
            elif change_percentage < -2:
                trend = "decreasing"
            
            # Set target (industry standard: 80%+)
            target = max(80.0, previous_retention * 1.02) if previous_retention > 0 else 80.0
            
            # Determine status
            status = "on_track"
            if retention_rate < 70:
                status = "behind"
            elif retention_rate < 80:
                status = "at_risk"
            
            return BusinessKPI(
                metric=BusinessMetric.RETENTION,
                value=retention_rate,
                target=target,
                period=period,
                date=date,
                trend=trend,
                change_percentage=change_percentage,
                status=status
            )
            
        except Exception as e:
            self.logger.warning(f"Could not calculate retention KPI: {e}")
            return None

    async def _get_retention_rate(self, period: MetricPeriod, date: datetime) -> float:
        """Get retention rate for a specific period"""
        try:
            start_date, end_date = self._get_period_dates(period, date)
            
            async with self.db.get_session() as session:
                # Get users who were active in the previous period
                previous_start, previous_end = self._get_period_dates(period, start_date - timedelta(days=1))
                
                result = await session.execute("""
                    SELECT 
                        COUNT(DISTINCT u.id) as total_users,
                        COUNT(DISTINCT CASE WHEN ua.user_id IS NOT NULL THEN u.id END) as retained_users
                    FROM users u
                    LEFT JOIN user_activities ua ON u.id = ua.user_id 
                        AND ua.timestamp >= :start_date AND ua.timestamp <= :end_date
                    WHERE u.created_at >= :previous_start AND u.created_at <= :previous_end
                """, {
                    "start_date": start_date,
                    "end_date": end_date,
                    "previous_start": previous_start,
                    "previous_end": previous_end
                })
                
                row = result.fetchone()
                if row and row.total_users > 0:
                    return (row.retained_users / row.total_users) * 100
                
                return 0.0
                
        except Exception as e:
            self.logger.warning(f"Could not get retention rate: {e}")
            return 0.0

    async def _calculate_conversion_kpi(self, period: MetricPeriod, date: datetime) -> Optional[BusinessKPI]:
        """Calculate conversion KPI"""
        try:
            # Get conversion rate for the period
            conversion_rate = await self._get_conversion_rate(period, date)
            
            # Get previous period conversion
            previous_date = self._get_previous_period_date(period, date)
            previous_conversion = await self._get_conversion_rate(period, previous_date)
            
            # Calculate change percentage
            change_percentage = 0.0
            if previous_conversion > 0:
                change_percentage = ((conversion_rate - previous_conversion) / previous_conversion) * 100
            
            # Determine trend
            trend = "stable"
            if change_percentage > 3:
                trend = "increasing"
            elif change_percentage < -3:
                trend = "decreasing"
            
            # Set target (industry standard: 3-5%)
            target = max(3.0, previous_conversion * 1.05) if previous_conversion > 0 else 3.0
            
            # Determine status
            status = "on_track"
            if conversion_rate < 2:
                status = "behind"
            elif conversion_rate < 3:
                status = "at_risk"
            
            return BusinessKPI(
                metric=BusinessMetric.CONVERSION,
                value=conversion_rate,
                target=target,
                period=period,
                date=date,
                trend=trend,
                change_percentage=change_percentage,
                status=status
            )
            
        except Exception as e:
            self.logger.warning(f"Could not calculate conversion KPI: {e}")
            return None

    async def _get_conversion_rate(self, period: MetricPeriod, date: datetime) -> float:
        """Get conversion rate for a specific period"""
        try:
            start_date, end_date = self._get_period_dates(period, date)
            
            async with self.db.get_session() as session:
                # Get total users and paying users
                result = await session.execute("""
                    SELECT 
                        COUNT(DISTINCT u.id) as total_users,
                        COUNT(DISTINCT s.user_id) as paying_users
                    FROM users u
                    LEFT JOIN subscriptions s ON u.id = s.user_id 
                        AND s.status = 'active'
                        AND s.created_at >= :start_date AND s.created_at <= :end_date
                    WHERE u.created_at >= :start_date AND u.created_at <= :end_date
                """, {
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                row = result.fetchone()
                if row and row.total_users > 0:
                    return (row.paying_users / row.total_users) * 100
                
                return 0.0
                
        except Exception as e:
            self.logger.warning(f"Could not get conversion rate: {e}")
            return 0.0

    async def _calculate_churn_kpi(self, period: MetricPeriod, date: datetime) -> Optional[BusinessKPI]:
        """Calculate churn KPI"""
        try:
            # Get churn rate for the period
            churn_rate = await self._get_churn_rate(period, date)
            
            # Get previous period churn
            previous_date = self._get_previous_period_date(period, date)
            previous_churn = await self._get_churn_rate(period, previous_date)
            
            # Calculate change percentage
            change_percentage = 0.0
            if previous_churn > 0:
                change_percentage = ((churn_rate - previous_churn) / previous_churn) * 100
            
            # Determine trend (lower is better for churn)
            trend = "stable"
            if change_percentage < -5:
                trend = "improving"
            elif change_percentage > 5:
                trend = "worsening"
            
            # Set target (industry standard: <5%)
            target = min(5.0, previous_churn * 0.95) if previous_churn > 0 else 5.0
            
            # Determine status
            status = "on_track"
            if churn_rate > 7:
                status = "behind"
            elif churn_rate > 5:
                status = "at_risk"
            
            return BusinessKPI(
                metric=BusinessMetric.CHURN,
                value=churn_rate,
                target=target,
                period=period,
                date=date,
                trend=trend,
                change_percentage=change_percentage,
                status=status
            )
            
        except Exception as e:
            self.logger.warning(f"Could not calculate churn KPI: {e}")
            return None

    async def _get_churn_rate(self, period: MetricPeriod, date: datetime) -> float:
        """Get churn rate for a specific period"""
        try:
            start_date, end_date = self._get_period_dates(period, date)
            
            async with self.db.get_session() as session:
                # Get users who cancelled subscriptions
                result = await session.execute("""
                    SELECT 
                        COUNT(DISTINCT s.user_id) as churned_users,
                        COUNT(DISTINCT s2.user_id) as total_subscribers
                    FROM subscriptions s
                    LEFT JOIN subscriptions s2 ON s2.user_id = s.user_id 
                        AND s2.status = 'active'
                        AND s2.created_at < :start_date
                    WHERE s.status = 'cancelled'
                    AND s.updated_at >= :start_date AND s.updated_at <= :end_date
                """, {
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                row = result.fetchone()
                if row and row.total_subscribers > 0:
                    return (row.churned_users / row.total_subscribers) * 100
                
                return 0.0
                
        except Exception as e:
            self.logger.warning(f"Could not get churn rate: {e}")
            return 0.0

    def _get_period_dates(self, period: MetricPeriod, date: datetime) -> Tuple[datetime, datetime]:
        """Get start and end dates for a specific period"""
        if period == MetricPeriod.DAILY:
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1) - timedelta(microseconds=1)
        elif period == MetricPeriod.WEEKLY:
            start_date = date - timedelta(days=date.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(weeks=1) - timedelta(microseconds=1)
        elif period == MetricPeriod.MONTHLY:
            start_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if date.month == 12:
                end_date = date.replace(year=date.year + 1, month=1, day=1) - timedelta(microseconds=1)
            else:
                end_date = date.replace(month=date.month + 1, day=1) - timedelta(microseconds=1)
        elif period == MetricPeriod.QUARTERLY:
            quarter = (date.month - 1) // 3
            start_date = date.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            if quarter == 3:
                end_date = date.replace(year=date.year + 1, month=1, day=1) - timedelta(microseconds=1)
            else:
                end_date = date.replace(month=(quarter + 1) * 3 + 1, day=1) - timedelta(microseconds=1)
        else:  # YEARLY
            start_date = date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = date.replace(year=date.year + 1, month=1, day=1) - timedelta(microseconds=1)
        
        return start_date, end_date

    def _get_previous_period_date(self, period: MetricPeriod, date: datetime) -> datetime:
        """Get the date for the previous period"""
        if period == MetricPeriod.DAILY:
            return date - timedelta(days=1)
        elif period == MetricPeriod.WEEKLY:
            return date - timedelta(weeks=1)
        elif period == MetricPeriod.MONTHLY:
            if date.month == 1:
                return date.replace(year=date.year - 1, month=12)
            else:
                return date.replace(month=date.month - 1)
        elif period == MetricPeriod.QUARTERLY:
            if date.month <= 3:
                return date.replace(year=date.year - 1, month=10)
            elif date.month <= 6:
                return date.replace(month=1)
            elif date.month <= 9:
                return date.replace(month=4)
            else:
                return date.replace(month=7)
        else:  # YEARLY
            return date.replace(year=date.year - 1)

    async def generate_business_insights(self, period: MetricPeriod = MetricPeriod.MONTHLY) -> List[BusinessInsight]:
        """Generate business insights based on current data"""
        try:
            insights = []
            
            # Get current KPIs
            kpis = await self.get_business_kpis(period)
            
            # Revenue insights
            revenue_kpi = next((kpi for kpi in kpis if kpi.metric == BusinessMetric.REVENUE), None)
            if revenue_kpi and revenue_kpi.status == "behind":
                insights.append(BusinessInsight(
                    id=f"insight_{uuid.uuid4().hex[:8]}",
                    insight_type="revenue_decline",
                    title="Revenue Decline Detected",
                    description=f"Revenue has declined by {abs(revenue_kpi.change_percentage):.1f}% compared to the previous period",
                    impact_score=0.8,
                    confidence=0.85,
                    recommendation="Review pricing strategy, customer acquisition costs, and product-market fit",
                    metrics_affected=["revenue", "arpu", "ltv"],
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=30)
                ))
            
            # User growth insights
            growth_kpi = next((kpi for kpi in kpis if kpi.metric == BusinessMetric.USER_GROWTH), None)
            if growth_kpi and growth_kpi.status == "behind":
                insights.append(BusinessInsight(
                    id=f"insight_{uuid.uuid4().hex[:8]}",
                    insight_type="user_growth_slowdown",
                    title="User Growth Slowdown",
                    description=f"User growth has slowed to {growth_kpi.change_percentage:.1f}% compared to the previous period",
                    impact_score=0.7,
                    confidence=0.80,
                    recommendation="Optimize onboarding, improve user experience, and review marketing channels",
                    metrics_affected=["user_growth", "activation", "conversion"],
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=30)
                ))
            
            # Retention insights
            retention_kpi = next((kpi for kpi in kpis if kpi.metric == BusinessMetric.RETENTION), None)
            if retention_kpi and retention_kpi.status == "behind":
                insights.append(BusinessInsight(
                    id=f"insight_{uuid.uuid4().hex[:8]}",
                    insight_type="retention_issue",
                    title="Retention Rate Below Target",
                    description=f"Retention rate is {retention_kpi.value:.1f}%, below the target of {retention_kpi.target:.1f}%",
                    impact_score=0.9,
                    confidence=0.90,
                    recommendation="Improve product engagement, customer support, and feature adoption",
                    metrics_affected=["retention", "ltv", "churn"],
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=30)
                ))
            
            # Churn insights
            churn_kpi = next((kpi for kpi in kpis if kpi.metric == BusinessMetric.CHURN), None)
            if churn_kpi and churn_kpi.status == "behind":
                insights.append(BusinessInsight(
                    id=f"insight_{uuid.uuid4().hex[:8]}",
                    insight_type="high_churn",
                    title="High Churn Rate Detected",
                    description=f"Churn rate is {churn_kpi.value:.1f}%, above the target of {churn_kpi.target:.1f}%",
                    impact_score=0.9,
                    confidence=0.85,
                    recommendation="Investigate churn reasons, improve customer success, and enhance product value",
                    metrics_affected=["churn", "ltv", "revenue"],
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=30)
                ))
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating business insights: {e}")
            return []

    async def generate_forecasts(self, period: MetricPeriod = MetricPeriod.MONTHLY, 
                               months_ahead: int = 3) -> List[Forecast]:
        """Generate business forecasts"""
        try:
            forecasts = []
            
            # Get historical data
            historical_data = await self._get_historical_data(period, months_ahead * 2)
            
            # Revenue forecast
            revenue_forecast = await self._forecast_revenue(historical_data, months_ahead)
            if revenue_forecast:
                forecasts.append(revenue_forecast)
            
            # User growth forecast
            user_forecast = await self._forecast_user_growth(historical_data, months_ahead)
            if user_forecast:
                forecasts.append(user_forecast)
            
            # Retention forecast
            retention_forecast = await self._forecast_retention(historical_data, months_ahead)
            if retention_forecast:
                forecasts.append(retention_forecast)
            
            return forecasts
            
        except Exception as e:
            self.logger.error(f"Error generating forecasts: {e}")
            return []

    async def _get_historical_data(self, period: MetricPeriod, months_back: int) -> Dict[str, List[float]]:
        """Get historical data for forecasting"""
        try:
            data = {
                "revenue": [],
                "users": [],
                "retention": []
            }
            
            current_date = datetime.utcnow()
            
            for i in range(months_back):
                date = current_date - timedelta(days=30 * i)
                start_date, end_date = self._get_period_dates(period, date)
                
                # Get revenue
                revenue = await self._get_revenue_for_period(period, date)
                data["revenue"].append(revenue)
                
                # Get users
                users = await self._get_users_for_period(period, date)
                data["users"].append(users)
                
                # Get retention
                retention = await self._get_retention_rate(period, date)
                data["retention"].append(retention)
            
            # Reverse to get chronological order
            for key in data:
                data[key].reverse()
            
            return data
            
        except Exception as e:
            self.logger.warning(f"Could not get historical data: {e}")
            return {"revenue": [], "users": [], "retention": []}

    async def _forecast_revenue(self, historical_data: Dict[str, List[float]], 
                              months_ahead: int) -> Optional[Forecast]:
        """Forecast revenue based on historical data"""
        try:
            revenue_data = historical_data.get("revenue", [])
            if len(revenue_data) < 3:
                return None
            
            # Simple linear regression forecast
            n = len(revenue_data)
            x_values = list(range(n))
            
            # Calculate trend
            x_mean = statistics.mean(x_values)
            y_mean = statistics.mean(revenue_data)
            
            numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, revenue_data))
            denominator = sum((x - x_mean) ** 2 for x in x_values)
            
            if denominator == 0:
                return None
            
            slope = numerator / denominator
            intercept = y_mean - slope * x_mean
            
            # Forecast next periods
            current_value = revenue_data[-1]
            forecast_value = intercept + slope * (n + months_ahead - 1)
            
            # Calculate confidence interval (simplified)
            confidence_range = current_value * 0.1  # 10% range
            confidence_interval = (forecast_value - confidence_range, forecast_value + confidence_range)
            
            return Forecast(
                metric=BusinessMetric.REVENUE,
                current_value=current_value,
                forecast_value=forecast_value,
                confidence_interval=confidence_interval,
                period=MetricPeriod.MONTHLY,
                forecast_date=datetime.utcnow(),
                factors=["historical_trend", "seasonality", "market_conditions"]
            )
            
        except Exception as e:
            self.logger.warning(f"Could not forecast revenue: {e}")
            return None

    async def _forecast_user_growth(self, historical_data: Dict[str, List[float]], 
                                  months_ahead: int) -> Optional[Forecast]:
        """Forecast user growth based on historical data"""
        try:
            user_data = historical_data.get("users", [])
            if len(user_data) < 3:
                return None
            
            # Calculate growth rates
            growth_rates = []
            for i in range(1, len(user_data)):
                if user_data[i-1] > 0:
                    growth_rate = ((user_data[i] - user_data[i-1]) / user_data[i-1]) * 100
                    growth_rates.append(growth_rate)
            
            if not growth_rates:
                return None
            
            # Average growth rate
            avg_growth_rate = statistics.mean(growth_rates)
            
            # Forecast
            current_value = user_data[-1]
            forecast_value = current_value * (1 + avg_growth_rate / 100) ** months_ahead
            
            # Confidence interval
            confidence_range = current_value * 0.15  # 15% range
            confidence_interval = (forecast_value - confidence_range, forecast_value + confidence_range)
            
            return Forecast(
                metric=BusinessMetric.USER_GROWTH,
                current_value=current_value,
                forecast_value=forecast_value,
                confidence_interval=confidence_interval,
                period=MetricPeriod.MONTHLY,
                forecast_date=datetime.utcnow(),
                factors=["growth_trend", "acquisition_channels", "market_expansion"]
            )
            
        except Exception as e:
            self.logger.warning(f"Could not forecast user growth: {e}")
            return None

    async def _forecast_retention(self, historical_data: Dict[str, List[float]], 
                                months_ahead: int) -> Optional[Forecast]:
        """Forecast retention based on historical data"""
        try:
            retention_data = historical_data.get("retention", [])
            if len(retention_data) < 3:
                return None
            
            # Simple moving average forecast
            current_value = retention_data[-1]
            
            # Use recent trend
            if len(retention_data) >= 2:
                recent_trend = retention_data[-1] - retention_data[-2]
                forecast_value = current_value + (recent_trend * months_ahead)
            else:
                forecast_value = current_value
            
            # Ensure forecast is within reasonable bounds
            forecast_value = max(0, min(100, forecast_value))
            
            # Confidence interval
            confidence_range = 5.0  # 5% range
            confidence_interval = (forecast_value - confidence_range, forecast_value + confidence_range)
            
            return Forecast(
                metric=BusinessMetric.RETENTION,
                current_value=current_value,
                forecast_value=forecast_value,
                confidence_interval=confidence_interval,
                period=MetricPeriod.MONTHLY,
                forecast_date=datetime.utcnow(),
                factors=["product_improvements", "customer_success", "engagement_features"]
            )
            
        except Exception as e:
            self.logger.warning(f"Could not forecast retention: {e}")
            return None

    async def generate_business_report(self, report_type: str, period: MetricPeriod,
                                     custom_title: Optional[str] = None) -> BusinessReport:
        """Generate a comprehensive business report"""
        try:
            report_id = f"report_{uuid.uuid4().hex[:8]}"
            current_date = datetime.utcnow()
            
            # Get period dates
            start_date, end_date = self._get_period_dates(period, current_date)
            
            # Get KPIs
            kpis = await self.get_business_kpis(period)
            
            # Generate insights
            insights = await self.generate_business_insights(period)
            
            # Generate forecasts
            forecasts = await self.generate_forecasts(period)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(kpis, insights)
            
            # Create report
            title = custom_title or f"{period.value.title()} Business Report"
            summary = self._generate_report_summary(kpis, insights)
            
            report = BusinessReport(
                id=report_id,
                report_type=report_type,
                title=title,
                summary=summary,
                period_start=start_date,
                period_end=end_date,
                kpis=kpis,
                insights=insights,
                forecasts=forecasts,
                recommendations=recommendations,
                generated_at=current_date
            )
            
            self.logger.info(f"Generated business report {report_id}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating business report: {e}")
            raise

    def _generate_recommendations(self, kpis: List[BusinessKPI], 
                                insights: List[BusinessInsight]) -> List[str]:
        """Generate actionable recommendations based on KPIs and insights"""
        try:
            recommendations = []
            
            # Revenue recommendations
            revenue_kpi = next((kpi for kpi in kpis if kpi.metric == BusinessMetric.REVENUE), None)
            if revenue_kpi and revenue_kpi.status in ["behind", "at_risk"]:
                recommendations.append("Implement pricing optimization strategies and improve customer acquisition")
            
            # User growth recommendations
            growth_kpi = next((kpi for kpi in kpis if kpi.metric == BusinessMetric.USER_GROWTH), None)
            if growth_kpi and growth_kpi.status in ["behind", "at_risk"]:
                recommendations.append("Optimize onboarding flow and expand marketing channels")
            
            # Retention recommendations
            retention_kpi = next((kpi for kpi in kpis if kpi.metric == BusinessMetric.RETENTION), None)
            if retention_kpi and retention_kpi.status in ["behind", "at_risk"]:
                recommendations.append("Enhance customer success programs and improve product engagement")
            
            # Churn recommendations
            churn_kpi = next((kpi for kpi in kpis if kpi.metric == BusinessMetric.CHURN), None)
            if churn_kpi and churn_kpi.status in ["behind", "at_risk"]:
                recommendations.append("Investigate churn reasons and implement retention strategies")
            
            # Add general recommendations
            if not recommendations:
                recommendations.append("Continue monitoring KPIs and maintain current performance levels")
            
            return recommendations
            
        except Exception as e:
            self.logger.warning(f"Could not generate recommendations: {e}")
            return ["Review business performance and adjust strategies accordingly"]

    def _generate_report_summary(self, kpis: List[BusinessKPI], 
                               insights: List[BusinessInsight]) -> str:
        """Generate a summary of the business report"""
        try:
            if not kpis:
                return "No KPI data available for the reporting period."
            
            # Count statuses
            on_track = len([kpi for kpi in kpis if kpi.status == "on_track"])
            at_risk = len([kpi for kpi in kpis if kpi.status == "at_risk"])
            behind = len([kpi for kpi in kpis if kpi.status == "behind"])
            
            total_kpis = len(kpis)
            
            summary = f"Business performance summary: {on_track}/{total_kpis} KPIs on track"
            
            if at_risk > 0:
                summary += f", {at_risk} at risk"
            
            if behind > 0:
                summary += f", {behind} behind target"
            
            if insights:
                summary += f". {len(insights)} key insights identified requiring attention."
            
            return summary
            
        except Exception as e:
            self.logger.warning(f"Could not generate report summary: {e}")
            return "Business report generated successfully."

    async def close(self):
        """Clean up resources"""
        self.logger.info("BusinessIntelligence closed")


# Singleton instances
_business_intelligence = None


async def get_business_intelligence() -> BusinessIntelligence:
    """Get the BusinessIntelligence singleton instance"""
    global _business_intelligence
    if _business_intelligence is None:
        _business_intelligence = BusinessIntelligence()
        await _business_intelligence.initialize()
    return _business_intelligence


async def init_business_intelligence() -> BusinessIntelligence:
    """Initialize and return a new BusinessIntelligence instance"""
    bi = BusinessIntelligence()
    await bi.initialize()
    return bi
