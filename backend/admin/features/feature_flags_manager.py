"""
Feature Flags Manager for Agent47 Admin Panel
Dynamic feature toggling with user/tier-based targeting
"""

import asyncio
import uuid
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy import text

from backend.core.database import get_database, DatabaseManager
from backend.core.cache import get_redis, RedisManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class FeatureFlagStatus(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    ROLLING_OUT = "rolling_out"

class TargetingType(Enum):
    ALL_USERS = "all_users"
    PERCENTAGE = "percentage"
    USER_IDS = "user_ids"
    USER_TIERS = "user_tiers"
    CUSTOM = "custom"

@dataclass
class FeatureFlag:
    key: str
    name: str
    description: str
    status: FeatureFlagStatus
    targeting_type: TargetingType
    targeting_config: Dict[str, Any]
    enabled_percentage: float = 0.0
    enabled_user_ids: Set[str] = field(default_factory=set)
    enabled_tiers: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: str = ""
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeatureFlagEvaluation:
    flag_key: str
    user_id: Optional[str]
    user_tier: Optional[str]
    enabled: bool
    reason: str
    evaluated_at: datetime

class FeatureFlagsManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.settings = get_settings()
        self.logger = logger
        
        self.feature_flags: Dict[str, FeatureFlag] = {}
        self.evaluation_cache: Dict[str, FeatureFlagEvaluation] = {}
        self.cache_ttl = 300  # 5 minutes

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing FeatureFlagsManager...")
            
            self.database = get_database()
            self.redis = await get_redis()
            
            await self._setup_feature_flags_tables()
            await self._load_feature_flags()
            await self._start_cache_cleanup_task()
            
            self.logger.info("FeatureFlagsManager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize FeatureFlagsManager: {str(e)}")
            return False

    async def _setup_feature_flags_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS feature_flags (
                    id SERIAL PRIMARY KEY,
                    flag_key VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    status VARCHAR(50) NOT NULL,
                    targeting_type VARCHAR(50) NOT NULL,
                    targeting_config JSONB NOT NULL,
                    enabled_percentage DECIMAL(5,2) DEFAULT 0.0,
                    enabled_user_ids JSONB DEFAULT '[]',
                    enabled_tiers JSONB DEFAULT '[]',
                    created_by VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by VARCHAR(255),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS feature_flag_evaluations (
                    id SERIAL PRIMARY KEY,
                    flag_key VARCHAR(255) NOT NULL,
                    user_id VARCHAR(255),
                    user_tier VARCHAR(50),
                    enabled BOOLEAN NOT NULL,
                    reason TEXT,
                    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.commit()

    async def _load_feature_flags(self):
        """Load all feature flags from database"""
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT flag_key, name, description, status, targeting_type,
                           targeting_config, enabled_percentage, enabled_user_ids,
                           enabled_tiers, created_by, created_at, updated_by,
                           updated_at, metadata
                    FROM feature_flags
                """))
                
                rows = result.fetchall()
                for row in rows:
                    flag = FeatureFlag(
                        key=row[0],
                        name=row[1],
                        description=row[2] or "",
                        status=FeatureFlagStatus(row[3]),
                        targeting_type=TargetingType(row[4]),
                        targeting_config=row[5] if row[5] else {},
                        enabled_percentage=float(row[6]) if row[6] else 0.0,
                        enabled_user_ids=set(row[7] if row[7] else []),
                        enabled_tiers=row[8] if row[8] else [],
                        created_by=row[9] or "",
                        created_at=row[10],
                        updated_by=row[11] or "",
                        updated_at=row[12],
                        metadata=row[13] if row[13] else {}
                    )
                    self.feature_flags[flag.key] = flag
                
                self.logger.info(f"Loaded {len(self.feature_flags)} feature flags")
        
        except Exception as e:
            self.logger.error(f"Failed to load feature flags: {str(e)}")

    async def _start_cache_cleanup_task(self):
        """Start background task to clean up evaluation cache"""
        async def cleanup_cache():
            while True:
                try:
                    await asyncio.sleep(600)  # Run every 10 minutes
                    await self._cleanup_evaluation_cache()
                except Exception as e:
                    self.logger.error(f"Error in cache cleanup task: {str(e)}")
        
        asyncio.create_task(cleanup_cache())

    async def _cleanup_evaluation_cache(self):
        """Remove old evaluation cache entries"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.cache_ttl)
        keys_to_remove = [
            key for key, eval in self.evaluation_cache.items()
            if eval.evaluated_at < cutoff_time
        ]
        for key in keys_to_remove:
            del self.evaluation_cache[key]

    async def create_feature_flag(self, key: str, name: str, description: str,
                                 created_by: str, status: FeatureFlagStatus = FeatureFlagStatus.DISABLED,
                                 targeting_type: TargetingType = TargetingType.ALL_USERS,
                                 targeting_config: Dict[str, Any] = None) -> bool:
        """Create a new feature flag"""
        if key in self.feature_flags:
            self.logger.warning(f"Feature flag {key} already exists")
            return False
        
        flag = FeatureFlag(
            key=key,
            name=name,
            description=description,
            status=status,
            targeting_type=targeting_type,
            targeting_config=targeting_config or {},
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_by=created_by,
            updated_at=datetime.utcnow()
        )
        
        self.feature_flags[key] = flag
        
        if self.database:
            try:
                async with self.database.get_session() as session:
                    await session.execute(
                        text("""
                            INSERT INTO feature_flags (
                                flag_key, name, description, status, targeting_type,
                                targeting_config, created_by, updated_by
                            )
                            VALUES (:key, :name, :description, :status, :targeting_type,
                                    :targeting_config, :created_by, :updated_by)
                        """),
                        {
                            "key": key,
                            "name": name,
                            "description": description,
                            "status": status.value,
                            "targeting_type": targeting_type.value,
                            "targeting_config": json.dumps(targeting_config or {}),
                            "created_by": created_by,
                            "updated_by": created_by
                        }
                    )
                    await session.commit()
            except Exception as e:
                self.logger.error(f"Failed to create feature flag {key}: {str(e)}")
                del self.feature_flags[key]
                return False
        
        self.logger.info(f"Feature flag {key} created by {created_by}")
        return True

    async def update_feature_flag(self, key: str, updates: Dict[str, Any], updated_by: str) -> bool:
        """Update a feature flag"""
        if key not in self.feature_flags:
            return False
        
        flag = self.feature_flags[key]
        
        if "status" in updates:
            flag.status = FeatureFlagStatus(updates["status"])
        if "targeting_type" in updates:
            flag.targeting_type = TargetingType(updates["targeting_type"])
        if "targeting_config" in updates:
            flag.targeting_config = updates["targeting_config"]
        if "enabled_percentage" in updates:
            flag.enabled_percentage = float(updates["enabled_percentage"])
        if "enabled_user_ids" in updates:
            flag.enabled_user_ids = set(updates["enabled_user_ids"])
        if "enabled_tiers" in updates:
            flag.enabled_tiers = updates["enabled_tiers"]
        if "description" in updates:
            flag.description = updates["description"]
        if "metadata" in updates:
            flag.metadata = updates["metadata"]
        
        flag.updated_by = updated_by
        flag.updated_at = datetime.utcnow()
        
        if self.database:
            try:
                async with self.database.get_session() as session:
                    await session.execute(
                        text("""
                            UPDATE feature_flags
                            SET status = :status, targeting_type = :targeting_type,
                                targeting_config = :targeting_config,
                                enabled_percentage = :enabled_percentage,
                                enabled_user_ids = :enabled_user_ids,
                                enabled_tiers = :enabled_tiers,
                                description = :description, metadata = :metadata,
                                updated_by = :updated_by, updated_at = :updated_at
                            WHERE flag_key = :key
                        """),
                        {
                            "key": key,
                            "status": flag.status.value,
                            "targeting_type": flag.targeting_type.value,
                            "targeting_config": json.dumps(flag.targeting_config),
                            "enabled_percentage": flag.enabled_percentage,
                            "enabled_user_ids": json.dumps(list(flag.enabled_user_ids)),
                            "enabled_tiers": json.dumps(flag.enabled_tiers),
                            "description": flag.description,
                            "metadata": json.dumps(flag.metadata),
                            "updated_by": updated_by,
                            "updated_at": flag.updated_at
                        }
                    )
                    await session.commit()
            except Exception as e:
                self.logger.error(f"Failed to update feature flag {key}: {str(e)}")
                return False
        
        # Clear evaluation cache for this flag
        cache_keys_to_remove = [k for k in self.evaluation_cache.keys() if k.startswith(f"{key}:")]
        for cache_key in cache_keys_to_remove:
            del self.evaluation_cache[cache_key]
        
        self.logger.info(f"Feature flag {key} updated by {updated_by}")
        return True

    async def is_feature_enabled(self, flag_key: str, user_id: Optional[str] = None,
                                 user_tier: Optional[str] = None) -> FeatureFlagEvaluation:
        """Check if a feature is enabled for a user"""
        # Check cache first
        cache_key = f"{flag_key}:{user_id}:{user_tier}"
        if cache_key in self.evaluation_cache:
            eval = self.evaluation_cache[cache_key]
            if (datetime.utcnow() - eval.evaluated_at).total_seconds() < self.cache_ttl:
                return eval
        
        # Get feature flag
        flag = self.feature_flags.get(flag_key)
        if not flag:
            eval = FeatureFlagEvaluation(
                flag_key=flag_key,
                user_id=user_id,
                user_tier=user_tier,
                enabled=False,
                reason="Feature flag not found",
                evaluated_at=datetime.utcnow()
            )
            return eval
        
        # Evaluate based on status
        if flag.status == FeatureFlagStatus.DISABLED:
            eval = FeatureFlagEvaluation(
                flag_key=flag_key,
                user_id=user_id,
                user_tier=user_tier,
                enabled=False,
                reason="Feature flag is disabled",
                evaluated_at=datetime.utcnow()
            )
        elif flag.status == FeatureFlagStatus.ENABLED:
            eval = FeatureFlagEvaluation(
                flag_key=flag_key,
                user_id=user_id,
                user_tier=user_tier,
                enabled=True,
                reason="Feature flag is enabled for all",
                evaluated_at=datetime.utcnow()
            )
        else:  # ROLLING_OUT
            enabled, reason = await self._evaluate_rolling_out(flag, user_id, user_tier)
            eval = FeatureFlagEvaluation(
                flag_key=flag_key,
                user_id=user_id,
                user_tier=user_tier,
                enabled=enabled,
                reason=reason,
                evaluated_at=datetime.utcnow()
            )
        
        # Cache evaluation
        self.evaluation_cache[cache_key] = eval
        
        # Log evaluation
        await self._log_evaluation(eval)
        
        return eval

    async def _evaluate_rolling_out(self, flag: FeatureFlag, user_id: Optional[str],
                                   user_tier: Optional[str]) -> Tuple[bool, str]:
        """Evaluate if feature should be enabled for rolling out flag"""
        if flag.targeting_type == TargetingType.ALL_USERS:
            return True, "Rolling out to all users"
        
        elif flag.targeting_type == TargetingType.PERCENTAGE:
            # Use user_id hash for consistent percentage-based rollout
            if user_id:
                import hashlib
                hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
                percentage = (hash_value % 100) + 1
                enabled = percentage <= flag.enabled_percentage
                return enabled, f"Percentage-based rollout: {percentage}% <= {flag.enabled_percentage}%"
            return False, "No user_id provided for percentage evaluation"
        
        elif flag.targeting_type == TargetingType.USER_IDS:
            enabled = user_id in flag.enabled_user_ids if user_id else False
            return enabled, f"User ID targeting: {user_id} in enabled list" if enabled else "User ID not in enabled list"
        
        elif flag.targeting_type == TargetingType.USER_TIERS:
            enabled = user_tier in flag.enabled_tiers if user_tier else False
            return enabled, f"Tier targeting: {user_tier} in enabled tiers" if enabled else "Tier not in enabled list"
        
        elif flag.targeting_type == TargetingType.CUSTOM:
            # Custom targeting logic from targeting_config
            custom_logic = flag.targeting_config.get("custom_logic", {})
            
            # Evaluate custom rules
            if not custom_logic:
                return False, "No custom logic defined"
            
            # Support simple condition evaluation
            # Format: {"conditions": [{"field": "user_id", "operator": "in", "value": ["user1", "user2"]}, ...]}
            conditions = custom_logic.get("conditions", [])
            
            if not conditions:
                return False, "No conditions defined in custom logic"
            
            all_conditions_met = True
            for condition in conditions:
                field = condition.get("field")
                operator = condition.get("operator")
                value = condition.get("value")
                
                if field == "user_id":
                    field_value = user_id
                elif field == "user_tier":
                    field_value = user_tier
                else:
                    all_conditions_met = False
                    break
                
                # Evaluate condition
                if operator == "equals":
                    if field_value != value:
                        all_conditions_met = False
                        break
                elif operator == "in":
                    if field_value not in value:
                        all_conditions_met = False
                        break
                elif operator == "not_in":
                    if field_value in value:
                        all_conditions_met = False
                        break
                elif operator == "exists":
                    if field_value is None:
                        all_conditions_met = False
                        break
                else:
                    all_conditions_met = False
                    break
            
            if all_conditions_met:
                return True, "Custom targeting conditions met"
            else:
                return False, "Custom targeting conditions not met"
        
        return False, "Unknown targeting type"

    async def _log_evaluation(self, evaluation: FeatureFlagEvaluation):
        """Log feature flag evaluation"""
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(
                    text("""
                        INSERT INTO feature_flag_evaluations (
                            flag_key, user_id, user_tier, enabled, reason
                        )
                        VALUES (:flag_key, :user_id, :user_tier, :enabled, :reason)
                    """),
                    {
                        "flag_key": evaluation.flag_key,
                        "user_id": evaluation.user_id,
                        "user_tier": evaluation.user_tier,
                        "enabled": evaluation.enabled,
                        "reason": evaluation.reason
                    }
                )
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to log evaluation: {str(e)}")

    async def get_feature_flag(self, key: str) -> Optional[FeatureFlag]:
        """Get a feature flag by key"""
        return self.feature_flags.get(key)

    async def get_all_feature_flags(self) -> List[FeatureFlag]:
        """Get all feature flags"""
        return list(self.feature_flags.values())

    async def delete_feature_flag(self, key: str, deleted_by: str) -> bool:
        """Delete a feature flag"""
        if key not in self.feature_flags:
            return False
        
        if self.database:
            try:
                async with self.database.get_session() as session:
                    await session.execute(
                        text("DELETE FROM feature_flags WHERE flag_key = :key"),
                        {"key": key}
                    )
                    await session.commit()
            except Exception as e:
                self.logger.error(f"Failed to delete feature flag {key}: {str(e)}")
                return False
        
        del self.feature_flags[key]
        self.logger.info(f"Feature flag {key} deleted by {deleted_by}")
        return True

    async def get_feature_flag_statistics(self, flag_key: str, hours: int = 24) -> Dict[str, Any]:
        """Get statistics for a feature flag"""
        if not self.database:
            return {}
        
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            async with self.database.get_session() as session:
                # Total evaluations
                result = await session.execute(
                    text("""
                        SELECT COUNT(*) FROM feature_flag_evaluations
                        WHERE flag_key = :key AND evaluated_at >= :start_time
                    """),
                    {"key": flag_key, "start_time": start_time}
                )
                total_evaluations = result.scalar()
                
                # Enabled evaluations
                result = await session.execute(
                    text("""
                        SELECT COUNT(*) FROM feature_flag_evaluations
                        WHERE flag_key = :key AND enabled = TRUE AND evaluated_at >= :start_time
                    """),
                    {"key": flag_key, "start_time": start_time}
                )
                enabled_count = result.scalar()
                
                # Enable rate
                enable_rate = (enabled_count / total_evaluations * 100) if total_evaluations > 0 else 0
                
                return {
                    "flag_key": flag_key,
                    "total_evaluations": total_evaluations,
                    "enabled_count": enabled_count,
                    "disabled_count": total_evaluations - enabled_count,
                    "enable_rate": round(enable_rate, 2),
                    "period_hours": hours
                }
        
        except Exception as e:
            self.logger.error(f"Failed to get feature flag statistics: {str(e)}")
            return {}

    async def close(self):
        self.logger.info("Closing FeatureFlagsManager...")

# Global instances
_feature_flags_manager: Optional[FeatureFlagsManager] = None

async def init_feature_flags_manager() -> FeatureFlagsManager:
    global _feature_flags_manager
    if not _feature_flags_manager:
        _feature_flags_manager = FeatureFlagsManager()
        await _feature_flags_manager.initialize()
    return _feature_flags_manager

async def get_feature_flags_manager() -> FeatureFlagsManager:
    global _feature_flags_manager
    if not _feature_flags_manager:
        _feature_flags_manager = await init_feature_flags_manager()
    return _feature_flags_manager

