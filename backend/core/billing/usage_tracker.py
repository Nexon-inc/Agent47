import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from ..database.models import (
    Usage, User, Subscription, SubscriptionStatus, BillingPlan, BillingTier
)
from ..database.connection import get_database
from .billing_plans import get_billing_plans
from .subscription_manager import get_subscription_manager

logger = logging.getLogger(__name__)

class UsageTracker:
    """Tracks and manages user usage for Agent47 billing system."""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        """Initialize the usage tracker."""
        if self._initialized:
            return
        
        # Initialize dependencies
        await get_billing_plans()
        await get_subscription_manager()
        
        self._initialized = True
        logger.info("Usage tracker initialized successfully")
    
    async def track_api_call(self, user_id: int, endpoint: str, response_time: float, success: bool = True) -> bool:
        """Track an API call made by a user."""
        db = get_database()
        
        try:
            async with db.get_session() as session:
                # Get current month
                current_month = datetime.utcnow().strftime("%Y-%m")
                
                # Get or create usage record for current month
                usage = await session.execute(
                    select(Usage).where(
                        and_(
                            Usage.user_id == user_id,
                            Usage.month == current_month
                        )
                    )
                )
                usage = usage.scalar_one_or_none()
                
                if not usage:
                    # Create new usage record
                    subscription = await self._get_user_subscription(user_id)
                    if not subscription:
                        logger.warning(f"No active subscription found for user {user_id}")
                        return False
                    
                    usage = Usage(
                        user_id=user_id,
                        subscription_id=subscription.id,
                        month=current_month,
                        api_calls_count=0,
                        agent_usage={},
                        storage_used_mb=0.0
                    )
                    session.add(usage)
                
                # Increment API call count
                usage.api_calls_count += 1
                
                # Update agent usage if endpoint contains agent information
                if "agent" in endpoint.lower():
                    agent_name = self._extract_agent_from_endpoint(endpoint)
                    if agent_name:
                        current_agent_usage = usage.agent_usage.get(agent_name, {})
                        current_agent_usage["api_calls"] = current_agent_usage.get("api_calls", 0) + 1
                        current_agent_usage["last_used"] = datetime.utcnow().isoformat()
                        current_agent_usage["total_response_time"] = current_agent_usage.get("total_response_time", 0) + response_time
                        current_agent_usage["average_response_time"] = current_agent_usage["total_response_time"] / current_agent_usage["api_calls"]
                        
                        if not success:
                            current_agent_usage["failed_calls"] = current_agent_usage.get("failed_calls", 0) + 1
                        
                        usage.agent_usage[agent_name] = current_agent_usage
                
                usage.updated_at = datetime.utcnow()
                session.add(usage)
                await session.commit()
                
                logger.debug(f"Tracked API call for user {user_id}: {endpoint}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to track API call for user {user_id}: {e}")
            return False
    
    async def track_agent_usage(self, user_id: int, agent_name: str, usage_type: str, duration_seconds: Optional[float] = None, data_processed_mb: Optional[float] = None) -> bool:
        """Track agent usage by a user."""
        db = get_database()
        
        try:
            async with db.get_session() as session:
                current_month = datetime.utcnow().strftime("%Y-%m")
                
                # Get or create usage record
                usage = await session.execute(
                    select(Usage).where(
                        and_(
                            Usage.user_id == user_id,
                            Usage.month == current_month
                        )
                    )
                )
                usage = usage.scalar_one_or_none()
                
                if not usage:
                    subscription = await self._get_user_subscription(user_id)
                    if not subscription:
                        logger.warning(f"No active subscription found for user {user_id}")
                        return False
                    
                    usage = Usage(
                        user_id=user_id,
                        subscription_id=subscription.id,
                        month=current_month,
                        api_calls_count=0,
                        agent_usage={},
                        storage_used_mb=0.0
                    )
                    session.add(usage)
                
                # Update agent usage
                current_agent_usage = usage.agent_usage.get(agent_name, {})
                
                if usage_type == "session":
                    current_agent_usage["sessions"] = current_agent_usage.get("sessions", 0) + 1
                    if duration_seconds:
                        current_agent_usage["total_session_time"] = current_agent_usage.get("total_session_time", 0) + duration_seconds
                        current_agent_usage["average_session_time"] = current_agent_usage["total_session_time"] / current_agent_usage["sessions"]
                
                elif usage_type == "task":
                    current_agent_usage["tasks"] = current_agent_usage.get("tasks", 0) + 1
                    if duration_seconds:
                        current_agent_usage["total_task_time"] = current_agent_usage.get("total_task_time", 0) + duration_seconds
                        current_agent_usage["average_task_time"] = current_agent_usage["total_task_time"] / current_agent_usage["tasks"]
                
                elif usage_type == "data_processing":
                    current_agent_usage["data_processing_operations"] = current_agent_usage.get("data_processing_operations", 0) + 1
                    if data_processed_mb:
                        current_agent_usage["total_data_processed_mb"] = current_agent_usage.get("total_data_processed_mb", 0) + data_processed_mb
                
                current_agent_usage["last_used"] = datetime.utcnow().isoformat()
                usage.agent_usage[agent_name] = current_agent_usage
                
                usage.updated_at = datetime.utcnow()
                session.add(usage)
                await session.commit()
                
                logger.debug(f"Tracked agent usage for user {user_id}, agent {agent_name}: {usage_type}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to track agent usage for user {user_id}: {e}")
            return False
    
    async def track_storage_usage(self, user_id: int, storage_mb: float, operation: str = "add") -> bool:
        """Track storage usage by a user."""
        db = get_database()
        
        try:
            async with db.get_session() as session:
                current_month = datetime.utcnow().strftime("%Y-%m")
                
                # Get or create usage record
                usage = await session.execute(
                    select(Usage).where(
                        and_(
                            Usage.user_id == user_id,
                            Usage.month == current_month
                        )
                    )
                )
                usage = usage.scalar_one_or_none()
                
                if not usage:
                    subscription = await self._get_user_subscription(user_id)
                    if not subscription:
                        logger.warning(f"No active subscription found for user {user_id}")
                        return False
                    
                    usage = Usage(
                        user_id=user_id,
                        subscription_id=subscription.id,
                        month=current_month,
                        api_calls_count=0,
                        agent_usage={},
                        storage_used_mb=0.0
                    )
                    session.add(usage)
                
                # Update storage usage
                if operation == "add":
                    usage.storage_used_mb += storage_mb
                elif operation == "remove":
                    usage.storage_used_mb = max(0, usage.storage_used_mb - storage_mb)
                elif operation == "set":
                    usage.storage_used_mb = storage_mb
                
                usage.updated_at = datetime.utcnow()
                session.add(usage)
                await session.commit()
                
                logger.debug(f"Tracked storage usage for user {user_id}: {operation} {storage_mb}MB")
                return True
                
        except Exception as e:
            logger.error(f"Failed to track storage usage for user {user_id}: {e}")
            return False
    
    async def get_user_usage(self, user_id: int, month: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get usage statistics for a user."""
        db = get_database()
        
        if not month:
            month = datetime.utcnow().strftime("%Y-%m")
        
        async with db.get_session() as session:
            usage = await session.execute(
                select(Usage).where(
                    and_(
                        Usage.user_id == user_id,
                        Usage.month == month
                    )
                )
            )
            usage = usage.scalar_one_or_none()
            
            if not usage:
                return None
            
            # Get subscription details
            subscription = await session.execute(
                select(Subscription, BillingPlan).join(
                    BillingPlan, Subscription.plan_id == BillingPlan.id
                ).where(Subscription.id == usage.subscription_id)
            )
            subscription_data = subscription.first()
            
            if subscription_data:
                subscription_obj, plan = subscription_data
                return {
                    "month": usage.month,
                    "tier": plan.tier.value,
                    "api_calls_count": usage.api_calls_count,
                    "agent_usage": usage.agent_usage,
                    "storage_used_mb": usage.storage_used_mb,
                    "limits": {
                        "max_api_calls": plan.max_api_calls_per_month,
                        "max_storage_mb": plan.features.get("storage_limit_mb"),
                        "max_agents": plan.max_agents
                    },
                    "usage_percentage": {
                        "api_calls": self._calculate_usage_percentage(
                            usage.api_calls_count, 
                            plan.max_api_calls_per_month
                        ),
                        "storage": self._calculate_usage_percentage(
                            usage.storage_used_mb, 
                            plan.features.get("storage_limit_mb")
                        )
                    }
                }
            
            return {
                "month": usage.month,
                "api_calls_count": usage.api_calls_count,
                "agent_usage": usage.agent_usage,
                "storage_used_mb": usage.storage_used_mb
            }
    
    async def get_usage_summary(self, user_id: int, months: int = 6) -> List[Dict[str, Any]]:
        """Get usage summary for a user over multiple months."""
        db = get_database()
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months * 30)
        
        async with db.get_session() as session:
            result = await session.execute(
                select(Usage).where(
                    and_(
                        Usage.user_id == user_id,
                        Usage.month >= start_date.strftime("%Y-%m"),
                        Usage.month <= end_date.strftime("%Y-%m")
                    )
                ).order_by(Usage.month.desc())
            )
            
            usages = result.scalars().all()
            summary = []
            
            for usage in usages:
                usage_data = await self.get_user_usage(user_id, usage.month)
                if usage_data:
                    summary.append(usage_data)
            
            return summary
    
    async def check_usage_limits(self, user_id: int) -> Dict[str, Any]:
        """Check if user has exceeded usage limits."""
        current_usage = await self.get_user_usage(user_id)
        if not current_usage:
            return {"within_limits": True, "warnings": []}
        
        warnings = []
        within_limits = True
        
        # Check API call limits
        if "limits" in current_usage:
            api_limit = current_usage["limits"]["max_api_calls"]
            if api_limit and current_usage["api_calls_count"] >= api_limit:
                warnings.append("API call limit reached")
                within_limits = False
            elif api_limit and current_usage["api_calls_count"] >= api_limit * 0.8:
                warnings.append("API call limit approaching (80% used)")
            
            # Check storage limits
            storage_limit = current_usage["limits"]["max_storage_mb"]
            if storage_limit and current_usage["storage_used_mb"] >= storage_limit:
                warnings.append("Storage limit reached")
                within_limits = False
            elif storage_limit and current_usage["storage_used_mb"] >= storage_limit * 0.8:
                warnings.append("Storage limit approaching (80% used)")
        
        return {
            "within_limits": within_limits,
            "warnings": warnings,
            "usage": current_usage
        }
    
    async def get_system_usage_statistics(self, month: Optional[str] = None) -> Dict[str, Any]:
        """Get system-wide usage statistics."""
        db = get_database()
        
        if not month:
            month = datetime.utcnow().strftime("%Y-%m")
        
        async with db.get_session() as session:
            # Total API calls
            total_api_calls = await session.execute(
                select(func.sum(Usage.api_calls_count))
                .where(Usage.month == month)
            )
            total_api_calls = total_api_calls.scalar() or 0
            
            # Total storage used
            total_storage = await session.execute(
                select(func.sum(Usage.storage_used_mb))
                .where(Usage.month == month)
            )
            total_storage = total_storage.scalar() or 0
            
            # Usage by tier
            tier_usage = await session.execute(
                select(
                    BillingPlan.tier,
                    func.sum(Usage.api_calls_count),
                    func.sum(Usage.storage_used_mb),
                    func.count(Usage.user_id)
                ).join(
                    Subscription, Usage.subscription_id == Subscription.id
                ).join(
                    BillingPlan, Subscription.plan_id == BillingPlan.id
                ).where(
                    and_(
                        Usage.month == month,
                        Subscription.status == SubscriptionStatus.ACTIVE
                    )
                ).group_by(BillingPlan.tier)
            )
            
            tier_stats = {}
            for tier, api_calls, storage, user_count in tier_usage:
                tier_stats[tier.value] = {
                    "api_calls": api_calls or 0,
                    "storage_mb": storage or 0,
                    "user_count": user_count or 0
                }
            
            # Top users by API calls
            top_api_users = await session.execute(
                select(
                    Usage.user_id,
                    Usage.api_calls_count
                ).where(
                    Usage.month == month
                ).order_by(
                    Usage.api_calls_count.desc()
                ).limit(10)
            )
            
            top_api_users_list = [
                {"user_id": user_id, "api_calls": count}
                for user_id, count in top_api_users
            ]
            
            # Top users by storage
            top_storage_users = await session.execute(
                select(
                    Usage.user_id,
                    Usage.storage_used_mb
                ).where(
                    Usage.month == month
                ).order_by(
                    Usage.storage_used_mb.desc()
                ).limit(10)
            )
            
            top_storage_users_list = [
                {"user_id": user_id, "storage_mb": storage}
                for user_id, storage in top_storage_users
            ]
            
            return {
                "month": month,
                "total_api_calls": total_api_calls,
                "total_storage_mb": total_storage,
                "usage_by_tier": tier_stats,
                "top_api_users": top_api_users_list,
                "top_storage_users": top_storage_users_list
            }
    
    async def cleanup_old_usage_records(self, months_to_keep: int = 24) -> int:
        """Clean up old usage records to save storage."""
        db = get_database()
        
        cutoff_date = datetime.utcnow() - timedelta(days=months_to_keep * 30)
        cutoff_month = cutoff_date.strftime("%Y-%m")
        
        async with db.get_session() as session:
            result = await session.execute(
                select(Usage).where(Usage.month < cutoff_month)
            )
            
            old_records = result.scalars().all()
            count = len(old_records)
            
            for record in old_records:
                await session.delete(record)
            
            await session.commit()
            
            logger.info(f"Cleaned up {count} old usage records older than {cutoff_month}")
            return count
    
    def _extract_agent_from_endpoint(self, endpoint: str) -> Optional[str]:
        """Extract agent name from API endpoint."""
        # Common patterns for agent endpoints
        if "/agents/" in endpoint:
            parts = endpoint.split("/agents/")
            if len(parts) > 1:
                agent_part = parts[1].split("/")[0]
                # Remove any query parameters or additional path segments
                agent_name = agent_part.split("?")[0].split("/")[0]
                return agent_name.lower()
        return None
    
    def _calculate_usage_percentage(self, used: float, limit: Optional[float]) -> Optional[float]:
        """Calculate usage percentage."""
        if not limit or limit == 0:
            return None
        return min(100.0, (used / limit) * 100)
    
    async def _get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get user's active subscription."""
        subscription_manager = await get_subscription_manager()
        return await subscription_manager.get_active_subscription(user_id)

# Global instance
usage_tracker = UsageTracker()

async def get_usage_tracker() -> UsageTracker:
    """Get the global usage tracker instance."""
    if not usage_tracker._initialized:
        await usage_tracker.initialize()
    return usage_tracker
