import asyncio
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from backend.core.database import get_database
from backend.core.cache import get_redis
from backend.core.logs import get_logger
from backend.core.config import get_config


class UserMetricType(Enum):
    ACTIVITY = "activity"
    ENGAGEMENT = "engagement"
    RETENTION = "retention"
    CONVERSION = "conversion"
    BEHAVIOR = "behavior"
    SATISFACTION = "satisfaction"


class UserSegment(Enum):
    NEW = "new"
    ACTIVE = "active"
    INACTIVE = "inactive"
    CHURNED = "churned"
    PREMIUM = "premium"


@dataclass
class UserMetrics:
    user_id: str
    email: str
    tier: str
    segment: UserSegment
    timeframe: str
    start_date: datetime
    end_date: datetime
    total_sessions: int
    total_actions: int
    agent_interactions: int
    api_calls: int
    storage_used: float
    last_activity: datetime
    days_since_signup: int
    days_since_last_activity: int
    engagement_score: float
    retention_score: float
    conversion_probability: float


@dataclass
class UserBehavior:
    user_id: str
    email: str
    behavior_type: str
    frequency: int
    last_occurrence: datetime
    pattern_strength: float
    context: Dict[str, Any]
    recommendations: List[str]


@dataclass
class UserSegment:
    segment_name: str
    user_count: int
    percentage: float
    average_engagement: float
    average_retention: float
    conversion_rate: float
    characteristics: List[str]
    growth_trend: str


@dataclass
class UserInsight:
    user_id: str
    email: str
    insight_type: str
    insight_message: str
    confidence: float
    recommendation: str
    impact_score: float
    timestamp: datetime


class UserAnalytics:
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()
        self.cache_ttl = 3600  # 1 hour cache

    async def initialize(self):
        """Initialize the user analytics system"""
        try:
            self.logger.info("UserAnalytics initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize UserAnalytics: {e}")
            raise

    async def get_user_metrics(self, user_id: str, timeframe: str = "30d") -> UserMetrics:
        """Get comprehensive metrics for a specific user"""
        try:
            # Check cache first
            cache_key = f"user_metrics:{user_id}:{timeframe}"
            cached_metrics = await self.redis.get(cache_key)
            if cached_metrics:
                return UserMetrics(**cached_metrics)
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, timeframe)
            
            # Get metrics from database
            metrics = await self._calculate_user_metrics(user_id, start_date, end_date)
            
            # Cache the results
            await self.redis.set(cache_key, metrics.__dict__, expire=self.cache_ttl)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting user metrics: {e}")
            raise

    def _calculate_start_date(self, end_date: datetime, timeframe: str) -> datetime:
        """Calculate start date based on timeframe string"""
        if timeframe.endswith('d'):
            days = int(timeframe[:-1])
            return end_date - timedelta(days=days)
        elif timeframe.endswith('w'):
            weeks = int(timeframe[:-1])
            return end_date - timedelta(weeks=weeks)
        elif timeframe.endswith('m'):
            months = int(timeframe[:-1])
            return end_date - timedelta(days=months * 30)
        else:
            return end_date - timedelta(days=30)

    async def _calculate_user_metrics(self, user_id: str, start_date: datetime, 
                                    end_date: datetime) -> UserMetrics:
        """Calculate comprehensive metrics for a user"""
        try:
            async with self.db.get_session() as session:
                # Get user basic info
                user_result = await session.execute("""
                    SELECT email, tier, created_at FROM users WHERE id = :user_id
                """, {"user_id": user_id})
                
                user_row = user_result.fetchone()
                if not user_row:
                    raise ValueError(f"User {user_id} not found")
                
                email = user_row.email
                tier = user_row.tier
                created_at = user_row.created_at
                
                # Get session data
                session_result = await session.execute("""
                    SELECT COUNT(*) as total_sessions, MAX(created_at) as last_session
                    FROM user_sessions
                    WHERE user_id = :user_id AND created_at >= :start_date
                """, {
                    "user_id": user_id,
                    "start_date": start_date
                })
                
                session_row = session_result.fetchone()
                total_sessions = session_row.total_sessions or 0
                last_session = session_row.last_session
                
                # Get activity data
                activity_result = await session.execute("""
                    SELECT COUNT(*) as total_actions, MAX(timestamp) as last_activity
                    FROM user_activities
                    WHERE user_id = :user_id AND timestamp >= :start_date
                """, {
                    "user_id": user_id,
                    "start_date": start_date
                })
                
                activity_row = activity_result.fetchone()
                total_actions = activity_row.total_actions or 0
                last_activity = activity_row.last_activity
                
                # Get agent interaction data
                agent_result = await session.execute("""
                    SELECT COUNT(*) as agent_interactions
                    FROM agent_tasks
                    WHERE user_id = :user_id AND started_at >= :start_date
                """, {
                    "user_id": user_id,
                    "start_date": start_date
                })
                
                agent_row = agent_result.fetchone()
                agent_interactions = agent_row.agent_interactions or 0
                
                # Get API usage data
                api_result = await session.execute("""
                    SELECT COUNT(*) as api_calls
                    FROM api_usage
                    WHERE user_id = :user_id AND timestamp >= :start_date
                """, {
                    "user_id": user_id,
                    "start_date": start_date
                })
                
                api_row = api_result.fetchone()
                api_calls = api_row.api_calls or 0
                
                # Get storage usage
                storage_result = await session.execute("""
                    SELECT COALESCE(SUM(storage_used), 0) as total_storage
                    FROM storage_usage
                    WHERE user_id = :user_id AND timestamp >= :start_date
                """, {
                    "user_id": user_id,
                    "start_date": start_date
                })
                
                storage_row = storage_result.fetchone()
                storage_used = storage_row.total_storage or 0.0
                
                # Calculate derived metrics
                days_since_signup = (datetime.utcnow() - created_at).days
                days_since_last_activity = (datetime.utcnow() - last_activity).days if last_activity else days_since_signup
                
                # Determine user segment
                segment = self._determine_user_segment(days_since_signup, days_since_last_activity, tier, total_actions)
                
                # Calculate scores
                engagement_score = self._calculate_engagement_score(total_sessions, total_actions, agent_interactions, api_calls)
                retention_score = self._calculate_retention_score(days_since_signup, days_since_last_activity, total_actions)
                conversion_probability = self._calculate_conversion_probability(tier, engagement_score, retention_score)
                
                metrics = UserMetrics(
                    user_id=user_id,
                    email=email,
                    tier=tier,
                    segment=segment,
                    timeframe="30d",
                    start_date=start_date,
                    end_date=end_date,
                    total_sessions=total_sessions,
                    total_actions=total_actions,
                    agent_interactions=agent_interactions,
                    api_calls=api_calls,
                    storage_used=storage_used,
                    last_activity=last_activity or created_at,
                    days_since_signup=days_since_signup,
                    days_since_last_activity=days_since_last_activity,
                    engagement_score=engagement_score,
                    retention_score=retention_score,
                    conversion_probability=conversion_probability
                )
                
                return metrics
                
        except Exception as e:
            self.logger.error(f"Error calculating user metrics: {e}")
            raise

    def _determine_user_segment(self, days_since_signup: int, days_since_last_activity: int, 
                               tier: str, total_actions: int) -> UserSegment:
        """Determine user segment based on behavior patterns"""
        try:
            if tier in ["pro"]:
                return UserSegment.PREMIUM
            
            if days_since_signup <= 7:
                return UserSegment.NEW
            elif days_since_last_activity <= 7 and total_actions > 10:
                return UserSegment.ACTIVE
            elif days_since_last_activity <= 30:
                return UserSegment.INACTIVE
            else:
                return UserSegment.CHURNED
                
        except Exception as e:
            self.logger.warning(f"Could not determine user segment: {e}")
            return UserSegment.INACTIVE

    def _calculate_engagement_score(self, total_sessions: int, total_actions: int, 
                                  agent_interactions: int, api_calls: int) -> float:
        """Calculate user engagement score"""
        try:
            # Session engagement (30% weight)
            session_score = min(100, (total_sessions / 10) * 100)
            
            # Action engagement (30% weight)
            action_score = min(100, (total_actions / 50) * 100)
            
            # Agent interaction engagement (25% weight)
            agent_score = min(100, (agent_interactions / 20) * 100)
            
            # API usage engagement (15% weight)
            api_score = min(100, (api_calls / 100) * 100)
            
            # Weighted average
            engagement_score = (session_score * 0.3 + action_score * 0.3 + 
                              agent_score * 0.25 + api_score * 0.15)
            
            return min(100.0, max(0.0, engagement_score))
            
        except Exception as e:
            self.logger.warning(f"Could not calculate engagement score: {e}")
            return 0.0

    def _calculate_retention_score(self, days_since_signup: int, days_since_last_activity: int, 
                                 total_actions: int) -> float:
        """Calculate user retention score"""
        try:
            # Time-based retention (40% weight)
            if days_since_signup == 0:
                time_score = 100
            else:
                time_score = max(0, 100 - (days_since_last_activity / days_since_signup) * 100)
            
            # Activity-based retention (60% weight)
            if days_since_signup <= 7:
                activity_score = min(100, (total_actions / 5) * 100)
            elif days_since_signup <= 30:
                activity_score = min(100, (total_actions / 20) * 100)
            else:
                activity_score = min(100, (total_actions / 50) * 100)
            
            # Weighted average
            retention_score = (time_score * 0.4 + activity_score * 0.6)
            
            return min(100.0, max(0.0, retention_score))
            
        except Exception as e:
            self.logger.warning(f"Could not calculate retention score: {e}")
            return 0.0

    def _calculate_conversion_probability(self, tier: str, engagement_score: float, 
                                        retention_score: float) -> float:
        """Calculate probability of user upgrading to paid tier"""
        try:
            # Base conversion probability based on current tier
            base_probability = {
                "free": 0.15,
                "starter": 0.25,
                "pro": 0.05
            }.get(tier, 0.15)
            
            # Engagement factor (40% weight)
            engagement_factor = engagement_score / 100
            
            # Retention factor (40% weight)
            retention_factor = retention_score / 100
            
            # Tier factor (20% weight)
            tier_factor = 1.0 if tier == "free" else 0.5
            
            # Calculate final probability
            conversion_probability = base_probability * (
                engagement_factor * 0.4 + 
                retention_factor * 0.4 + 
                tier_factor * 0.2
            )
            
            return min(1.0, max(0.0, conversion_probability))
            
        except Exception as e:
            self.logger.warning(f"Could not calculate conversion probability: {e}")
            return 0.15

    async def get_user_behavior_patterns(self, user_id: str) -> List[UserBehavior]:
        """Analyze user behavior patterns and identify trends"""
        try:
            behaviors = []
            
            # Get user activities
            async with self.db.get_session() as session:
                # Analyze session patterns
                session_result = await session.execute("""
                    SELECT 
                        DATE_TRUNC('hour', created_at) as hour_bucket,
                        COUNT(*) as session_count
                    FROM user_sessions
                    WHERE user_id = :user_id
                    AND created_at >= :start_date
                    GROUP BY DATE_TRUNC('hour', created_at)
                    ORDER BY hour_bucket
                """, {
                    "user_id": user_id,
                    "start_date": datetime.utcnow() - timedelta(days=30)
                })
                
                session_data = session_result.fetchall()
                if session_data:
                    peak_hours = self._find_peak_activity_hours(session_data)
                    behaviors.append(UserBehavior(
                        user_id=user_id,
                        email=await self._get_user_email(user_id),
                        behavior_type="session_timing",
                        frequency=len(session_data),
                        last_occurrence=session_data[-1].hour_bucket,
                        pattern_strength=self._calculate_pattern_strength(session_data),
                        context={"peak_hours": peak_hours, "total_sessions": len(session_data)},
                        recommendations=[
                            "Schedule maintenance during off-peak hours",
                            "Send notifications during peak activity times"
                        ]
                    ))
                
                # Analyze agent usage patterns
                agent_result = await session.execute("""
                    SELECT 
                        agent_name,
                        COUNT(*) as usage_count,
                        AVG(execution_time) as avg_execution_time
                    FROM agent_tasks
                    WHERE user_id = :user_id
                    AND started_at >= :start_date
                    GROUP BY agent_name
                    ORDER BY usage_count DESC
                """, {
                    "user_id": user_id,
                    "start_date": datetime.utcnow() - timedelta(days=30)
                })
                
                agent_data = agent_result.fetchall()
                if agent_data:
                    preferred_agents = [row.agent_name for row in agent_data[:3]]
                    behaviors.append(UserBehavior(
                        user_id=user_id,
                        email=await self._get_user_email(user_id),
                        behavior_type="agent_preference",
                        frequency=sum(row.usage_count for row in agent_data),
                        last_occurrence=datetime.utcnow(),
                        pattern_strength=0.8,
                        context={
                            "preferred_agents": preferred_agents,
                            "total_agent_usage": sum(row.usage_count for row in agent_data)
                        },
                        recommendations=[
                            f"Provide training on {preferred_agents[0]} capabilities",
                            "Suggest complementary agents for workflow optimization"
                        ]
                    ))
                
                # Analyze feature usage patterns
                feature_result = await session.execute("""
                    SELECT 
                        activity_type,
                        COUNT(*) as usage_count
                    FROM user_activities
                    WHERE user_id = :user_id
                    AND timestamp >= :start_date
                    GROUP BY activity_type
                    ORDER BY usage_count DESC
                """, {
                    "user_id": user_id,
                    "start_date": datetime.utcnow() - timedelta(days=30)
                })
                
                feature_data = feature_result.fetchall()
                if feature_data:
                    top_features = [row.activity_type for row in feature_data[:5]]
                    behaviors.append(UserBehavior(
                        user_id=user_id,
                        email=await self._get_user_email(user_id),
                        behavior_type="feature_usage",
                        frequency=sum(row.usage_count for row in feature_data),
                        last_occurrence=datetime.utcnow(),
                        pattern_strength=0.7,
                        context={
                            "top_features": top_features,
                            "feature_diversity": len(feature_data)
                        },
                        recommendations=[
                            "Highlight advanced features for power users",
                            "Provide tutorials on underutilized features"
                        ]
                    ))
            
            return behaviors
            
        except Exception as e:
            self.logger.error(f"Error getting user behavior patterns: {e}")
            return []

    def _find_peak_activity_hours(self, session_data) -> List[int]:
        """Find peak activity hours from session data"""
        try:
            hour_counts = {}
            for row in session_data:
                hour = row.hour_bucket.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + row.session_count
            
            # Find top 3 peak hours
            sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
            return [hour for hour, count in sorted_hours[:3]]
            
        except Exception as e:
            self.logger.warning(f"Could not find peak activity hours: {e}")
            return []

    def _calculate_pattern_strength(self, data) -> float:
        """Calculate the strength of a behavioral pattern"""
        try:
            if len(data) < 2:
                return 0.0
            
            # Simple variance-based pattern strength
            values = [row.session_count for row in data]
            mean_value = statistics.mean(values)
            variance = statistics.variance(values) if len(values) > 1 else 0
            
            # Lower variance indicates stronger pattern
            pattern_strength = max(0, 1 - (variance / (mean_value ** 2)))
            
            return min(1.0, pattern_strength)
            
        except Exception as e:
            self.logger.warning(f"Could not calculate pattern strength: {e}")
            return 0.0

    async def _get_user_email(self, user_id: str) -> str:
        """Get user email from user_id"""
        try:
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT email FROM users WHERE id = :user_id
                """, {"user_id": user_id})
                
                row = result.fetchone()
                return row.email if row else "Unknown"
                
        except Exception as e:
            self.logger.warning(f"Could not get user email: {e}")
            return "Unknown"

    async def get_user_segments(self) -> List[UserSegment]:
        """Get analysis of all user segments"""
        try:
            async with self.db.get_session() as session:
                # Get total user count
                total_result = await session.execute("SELECT COUNT(*) as total FROM users")
                total_users = total_result.fetchone().total
                
                segments = []
                
                # Analyze each segment
                segment_configs = [
                    ("new", "users WHERE created_at >= :start_date"),
                    ("active", "users WHERE last_login >= :start_date"),
                    ("inactive", "users WHERE last_login < :start_date AND last_login >= :inactive_start"),
                    ("churned", "users WHERE last_login < :inactive_start"),
                    ("premium", "users WHERE tier = 'pro'")
                ]
                
                start_date = datetime.utcnow() - timedelta(days=7)
                inactive_start = datetime.utcnow() - timedelta(days=30)
                
                for segment_name, query in segment_configs:
                    # Get segment count
                    count_result = await session.execute(f"SELECT COUNT(*) as count FROM {query}", {
                        "start_date": start_date,
                        "inactive_start": inactive_start
                    })
                    
                    segment_count = count_result.fetchone().count
                    percentage = (segment_count / max(total_users, 1)) * 100
                    
                    # Get segment metrics
                    metrics = await self._get_segment_metrics(session, segment_name, start_date)
                    
                    segments.append(UserSegment(
                        segment_name=segment_name,
                        user_count=segment_count,
                        percentage=percentage,
                        average_engagement=metrics.get("engagement", 0.0),
                        average_retention=metrics.get("retention", 0.0),
                        conversion_rate=metrics.get("conversion", 0.0),
                        characteristics=self._get_segment_characteristics(segment_name),
                        growth_trend=self._get_segment_growth_trend(segment_name)
                    ))
                
                return segments
                
        except Exception as e:
            self.logger.error(f"Error getting user segments: {e}")
            return []

    async def _get_segment_metrics(self, session, segment_name: str, start_date: datetime) -> Dict[str, float]:
        """Get metrics for a specific user segment"""
        try:
            metrics = {}
            
            # Get engagement metrics
            if segment_name in ["new", "active", "premium"]:
                engagement_result = await session.execute("""
                    SELECT AVG(engagement_score) as avg_engagement
                    FROM user_metrics
                    WHERE segment = :segment_name
                """, {"segment_name": segment_name})
                
                engagement_row = engagement_result.fetchone()
                metrics["engagement"] = engagement_row.avg_engagement or 0.0
            
            # Get retention metrics
            if segment_name in ["new", "active"]:
                retention_result = await session.execute("""
                    SELECT AVG(retention_score) as avg_retention
                    FROM user_metrics
                    WHERE segment = :segment_name
                """, {"segment_name": segment_name})
                
                retention_row = retention_result.fetchone()
                metrics["retention"] = retention_row.avg_retention or 0.0
            
            # Get conversion metrics
            if segment_name in ["free", "starter"]:
                conversion_result = await session.execute("""
                    SELECT AVG(conversion_probability) as avg_conversion
                    FROM user_metrics
                    WHERE segment = :segment_name
                """, {"segment_name": segment_name})
                
                conversion_row = conversion_result.fetchone()
                metrics["conversion"] = conversion_row.avg_conversion or 0.0
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"Could not get segment metrics for {segment_name}: {e}")
            return {}

    def _get_segment_characteristics(self, segment_name: str) -> List[str]:
        """Get characteristics for a user segment"""
        characteristics = {
            "new": ["Recently signed up", "Exploring features", "Low engagement", "High potential"],
            "active": ["Regular usage", "Feature adoption", "Good engagement", "Stable retention"],
            "inactive": ["Declining usage", "Reduced engagement", "Risk of churn", "Need re-engagement"],
            "churned": ["No recent activity", "Low retention", "High churn risk", "Requires reactivation"],
            "premium": ["Paid subscription", "High engagement", "Feature power users", "Strong retention"]
        }
        
        return characteristics.get(segment_name, [])

    def _get_segment_growth_trend(self, segment_name: str) -> str:
        """Get growth trend for a user segment"""
        trends = {
            "new": "stable",
            "active": "growing",
            "inactive": "declining",
            "churned": "declining",
            "premium": "growing"
        }
        
        return trends.get(segment_name, "stable")

    async def generate_user_insights(self, user_id: str) -> List[UserInsight]:
        """Generate insights and recommendations for a user"""
        try:
            insights = []
            
            # Get user metrics
            metrics = await self.get_user_metrics(user_id)
            
            # Analyze engagement
            if metrics.engagement_score < 30:
                insights.append(UserInsight(
                    user_id=user_id,
                    email=metrics.email,
                    insight_type="low_engagement",
                    insight_message=f"User engagement score is {metrics.engagement_score:.1f}, indicating low platform usage",
                    confidence=0.85,
                    recommendation="Send onboarding emails and feature discovery content",
                    impact_score=0.7,
                    timestamp=datetime.utcnow()
                ))
            
            # Analyze retention
            if metrics.retention_score < 50:
                insights.append(UserInsight(
                    user_id=user_id,
                    email=metrics.email,
                    insight_type="retention_risk",
                    insight_message=f"User retention score is {metrics.retention_score:.1f}, indicating high churn risk",
                    confidence=0.80,
                    recommendation="Implement re-engagement campaigns and personalized outreach",
                    impact_score=0.8,
                    timestamp=datetime.utcnow()
                ))
            
            # Analyze conversion potential
            if metrics.conversion_probability > 0.3 and metrics.tier == "free":
                insights.append(UserInsight(
                    user_id=user_id,
                    email=metrics.email,
                    insight_type="conversion_opportunity",
                    insight_message=f"User has {metrics.conversion_probability:.1%} probability of upgrading",
                    confidence=0.75,
                    recommendation="Target with premium feature demos and upgrade incentives",
                    impact_score=0.6,
                    timestamp=datetime.utcnow()
                ))
            
            # Analyze usage patterns
            if metrics.agent_interactions == 0:
                insights.append(UserInsight(
                    user_id=user_id,
                    email=metrics.email,
                    insight_type="feature_adoption",
                    insight_message="User has not interacted with any AI agents",
                    confidence=0.90,
                    recommendation="Provide agent tutorials and use case examples",
                    impact_score=0.5,
                    timestamp=datetime.utcnow()
                ))
            
            # Analyze storage usage
            if metrics.storage_used > 1000:  # 1GB threshold
                insights.append(UserInsight(
                    user_id=user_id,
                    email=metrics.email,
                    insight_type="storage_usage",
                    insight_message=f"User is using {metrics.storage_used:.1f}MB of storage",
                    confidence=0.70,
                    recommendation="Suggest storage optimization and cleanup strategies",
                    impact_score=0.4,
                    timestamp=datetime.utcnow()
                ))
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating user insights: {e}")
            return []

    async def get_system_wide_user_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        """Get system-wide user analytics"""
        try:
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, timeframe)
            
            async with self.db.get_session() as session:
                # Get overall user metrics
                result = await session.execute("""
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(CASE WHEN created_at >= :start_date THEN 1 END) as new_users,
                        COUNT(CASE WHEN last_login >= :start_date THEN 1 END) as active_users,
                        COUNT(CASE WHEN tier = 'pro' THEN 1 END) as premium_users
                    FROM users
                """, {"start_date": start_date})
                
                row = result.fetchone()
                total_users = row.total_users or 0
                new_users = row.new_users or 0
                active_users = row.active_users or 0
                premium_users = row.premium_users or 0
                
                # Get engagement metrics
                engagement_result = await session.execute("""
                    SELECT 
                        AVG(engagement_score) as avg_engagement,
                        AVG(retention_score) as avg_retention
                    FROM user_metrics
                    WHERE timestamp >= :start_date
                """, {"start_date": start_date})
                
                engagement_row = engagement_result.fetchone()
                avg_engagement = engagement_row.avg_engagement or 0.0
                avg_retention = engagement_row.avg_retention or 0.0
                
                # Calculate derived metrics
                growth_rate = (new_users / max(total_users - new_users, 1)) * 100
                activation_rate = (active_users / max(total_users, 1)) * 100
                premium_rate = (premium_users / max(total_users, 1)) * 100
                
                analytics = {
                    "timeframe": timeframe,
                    "period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "overview": {
                        "total_users": total_users,
                        "new_users": new_users,
                        "active_users": active_users,
                        "premium_users": premium_users
                    },
                    "metrics": {
                        "growth_rate": growth_rate,
                        "activation_rate": activation_rate,
                        "premium_rate": premium_rate,
                        "average_engagement": avg_engagement,
                        "average_retention": avg_retention
                    },
                    "trends": {
                        "user_growth": "growing" if growth_rate > 5 else "stable",
                        "engagement_trend": "improving" if avg_engagement > 60 else "declining",
                        "retention_trend": "improving" if avg_retention > 70 else "declining"
                    }
                }
                
                return analytics
                
        except Exception as e:
            self.logger.error(f"Error getting system-wide user analytics: {e}")
            return {}

    async def close(self):
        """Clean up resources"""
        self.logger.info("UserAnalytics closed")


# Singleton instances
_user_analytics = None


async def get_user_analytics() -> UserAnalytics:
    """Get the UserAnalytics singleton instance"""
    global _user_analytics
    if _user_analytics is None:
        _user_analytics = UserAnalytics()
        await _user_analytics.initialize()
    return _user_analytics


async def init_user_analytics() -> UserAnalytics:
    """Initialize and return a new UserAnalytics instance"""
    analytics = UserAnalytics()
    await analytics.initialize()
    return analytics
