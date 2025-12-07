"""
Settings Manager for Agent47 Admin Panel
Manages system-wide configuration settings with versioning and audit trails
"""

import asyncio
import uuid
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy import text

from backend.core.database import get_database, DatabaseManager
from backend.core.cache import get_redis, RedisManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class SettingCategory(Enum):
    GENERAL = "general"
    SECURITY = "security"
    BILLING = "billing"
    INTEGRATIONS = "integrations"
    NOTIFICATIONS = "notifications"
    PERFORMANCE = "performance"
    FEATURES = "features"
    AI_SERVICES = "ai_services"

class SettingType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    ARRAY = "array"

@dataclass
class Setting:
    key: str
    value: Any
    setting_type: SettingType
    category: SettingCategory
    description: str
    is_encrypted: bool = False
    is_public: bool = False
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    default_value: Any = None
    updated_by: Optional[str] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

@dataclass
class SettingChange:
    id: str
    setting_key: str
    old_value: Any
    new_value: Any
    changed_by: str
    change_reason: str
    timestamp: datetime
    reverted: bool = False

class SettingsManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.settings = get_settings()
        self.logger = logger
        
        self.settings_cache: Dict[str, Setting] = {}
        self.settings_history: Dict[str, List[SettingChange]] = {}
        
        # Default system settings
        self.default_settings = {
            "system.maintenance_mode": {
                "value": False,
                "type": SettingType.BOOLEAN,
                "category": SettingCategory.GENERAL,
                "description": "Enable/disable maintenance mode",
                "is_public": True
            },
            "system.max_login_attempts": {
                "value": 5,
                "type": SettingType.INTEGER,
                "category": SettingCategory.SECURITY,
                "description": "Maximum login attempts before lockout",
                "validation_rules": {"min": 3, "max": 10}
            },
            "system.session_timeout_hours": {
                "value": 24,
                "type": SettingType.INTEGER,
                "category": SettingCategory.SECURITY,
                "description": "Session timeout in hours",
                "validation_rules": {"min": 1, "max": 168}
            },
            "billing.free_tier_llm_tokens": {
                "value": 10000,
                "type": SettingType.INTEGER,
                "category": SettingCategory.BILLING,
                "description": "Free tier LLM token limit per month",
                "validation_rules": {"min": 0}
            },
            "billing.starter_tier_llm_tokens": {
                "value": 100000,
                "type": SettingType.INTEGER,
                "category": SettingCategory.BILLING,
                "description": "Starter tier LLM token limit per month",
                "validation_rules": {"min": 0}
            },
            "billing.pro_tier_llm_tokens": {
                "value": 1000000,
                "type": SettingType.INTEGER,
                "category": SettingCategory.BILLING,
                "description": "Pro tier LLM token limit per month",
                "validation_rules": {"min": 0}
            },
            "ai.groq_enabled": {
                "value": True,
                "type": SettingType.BOOLEAN,
                "category": SettingCategory.AI_SERVICES,
                "description": "Enable Groq AI services",
                "is_public": True
            },
            "ai.openai_enabled": {
                "value": True,
                "type": SettingType.BOOLEAN,
                "category": SettingCategory.AI_SERVICES,
                "description": "Enable OpenAI services",
                "is_public": True
            },
            "ai.ollama_enabled": {
                "value": True,
                "type": SettingType.BOOLEAN,
                "category": SettingCategory.AI_SERVICES,
                "description": "Enable Ollama services",
                "is_public": True
            },
            "notifications.email_enabled": {
                "value": True,
                "type": SettingType.BOOLEAN,
                "category": SettingCategory.NOTIFICATIONS,
                "description": "Enable email notifications",
                "is_public": True
            },
            "notifications.sms_enabled": {
                "value": False,
                "type": SettingType.BOOLEAN,
                "category": SettingCategory.NOTIFICATIONS,
                "description": "Enable SMS notifications",
                "is_public": True
            },
            "performance.rate_limit_per_minute": {
                "value": 60,
                "type": SettingType.INTEGER,
                "category": SettingCategory.PERFORMANCE,
                "description": "API rate limit per minute",
                "validation_rules": {"min": 1, "max": 1000}
            },
            "features.user_registration_enabled": {
                "value": True,
                "type": SettingType.BOOLEAN,
                "category": SettingCategory.FEATURES,
                "description": "Enable user registration",
                "is_public": True
            },
            "features.agent_intercommunication": {
                "value": True,
                "type": SettingType.BOOLEAN,
                "category": SettingCategory.FEATURES,
                "description": "Enable agent intercommunication",
                "is_public": True
            }
        }

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing SettingsManager...")
            
            self.database = get_database()
            self.redis = await get_redis()
            
            await self._setup_settings_tables()
            await self._initialize_default_settings()
            await self._load_settings()
            
            self.logger.info("SettingsManager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SettingsManager: {str(e)}")
            return False

    async def _setup_settings_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    id SERIAL PRIMARY KEY,
                    setting_key VARCHAR(255) UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    setting_type VARCHAR(50) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    description TEXT,
                    is_encrypted BOOLEAN DEFAULT FALSE,
                    is_public BOOLEAN DEFAULT FALSE,
                    validation_rules JSONB,
                    default_value TEXT,
                    updated_by VARCHAR(255),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS setting_changes (
                    id VARCHAR(255) PRIMARY KEY,
                    setting_key VARCHAR(255) NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    changed_by VARCHAR(255) NOT NULL,
                    change_reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reverted BOOLEAN DEFAULT FALSE
                )
            """))
            
            await session.commit()

    async def _initialize_default_settings(self):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                for key, setting_data in self.default_settings.items():
                    # Check if setting exists
                    result = await session.execute(
                        text("SELECT setting_key FROM system_settings WHERE setting_key = :key"),
                        {"key": key}
                    )
                    
                    if not result.fetchone():
                        # Insert default setting
                        await session.execute(
                            text("""
                                INSERT INTO system_settings (
                                    setting_key, setting_value, setting_type, category,
                                    description, is_public, validation_rules, default_value
                                )
                                VALUES (:key, :value, :type, :category, :description, :is_public, :validation, :default)
                            """),
                            {
                                "key": key,
                                "value": str(setting_data["value"]),
                                "type": setting_data["type"].value,
                                "category": setting_data["category"].value,
                                "description": setting_data.get("description", ""),
                                "is_public": setting_data.get("is_public", False),
                                "validation": json.dumps(setting_data.get("validation_rules", {})),
                                "default": str(setting_data.get("default_value", setting_data["value"]))
                            }
                        )
                
                await session.commit()
                self.logger.info("Default settings initialized successfully")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize default settings: {str(e)}")

    async def _load_settings(self):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT setting_key, setting_value, setting_type, category, description,
                           is_encrypted, is_public, validation_rules, default_value,
                           updated_by, updated_at, version
                    FROM system_settings
                """))
                
                rows = result.fetchall()
                for row in rows:
                    setting = Setting(
                        key=row[0],
                        value=self._parse_value(row[1], SettingType(row[2])),
                        setting_type=SettingType(row[2]),
                        category=SettingCategory(row[3]),
                        description=row[4] or "",
                        is_encrypted=row[5],
                        is_public=row[6],
                        validation_rules=row[7] if row[7] else {},
                        default_value=self._parse_value(row[8], SettingType(row[2])) if row[8] else None,
                        updated_by=row[9],
                        updated_at=row[10],
                        version=row[11]
                    )
                    self.settings_cache[setting.key] = setting
                
                self.logger.info(f"Loaded {len(self.settings_cache)} settings from database")
        
        except Exception as e:
            self.logger.error(f"Failed to load settings: {str(e)}")

    def _parse_value(self, value: str, setting_type: SettingType) -> Any:
        """Parse setting value based on type"""
        if value is None:
            return None
        
        try:
            if setting_type == SettingType.BOOLEAN:
                return value.lower() in ("true", "1", "yes", "on")
            elif setting_type == SettingType.INTEGER:
                return int(value)
            elif setting_type == SettingType.FLOAT:
                return float(value)
            elif setting_type == SettingType.JSON:
                return json.loads(value)
            elif setting_type == SettingType.ARRAY:
                return json.loads(value) if isinstance(value, str) else value
            else:
                return value
        except (ValueError, json.JSONDecodeError) as e:
            self.logger.warning(f"Failed to parse value {value} as {setting_type.value}: {str(e)}")
            return value

    async def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key"""
        if key in self.settings_cache:
            return self.settings_cache[key].value
        
        # Try to load from database
        if self.database:
            try:
                async with self.database.get_session() as session:
                    result = await session.execute(
                        text("SELECT setting_value, setting_type FROM system_settings WHERE setting_key = :key"),
                        {"key": key}
                    )
                    row = result.fetchone()
                    if row:
                        value = self._parse_value(row[0], SettingType(row[1]))
                        return value
            except Exception as e:
                self.logger.error(f"Failed to get setting {key}: {str(e)}")
        
        return default

    async def get_all_settings(self, category: Optional[SettingCategory] = None, 
                             public_only: bool = False) -> Dict[str, Setting]:
        """Get all settings, optionally filtered by category"""
        settings = self.settings_cache.copy()
        
        if category:
            settings = {k: v for k, v in settings.items() if v.category == category}
        
        if public_only:
            settings = {k: v for k, v in settings.items() if v.is_public}
        
        return settings

    async def update_setting(self, key: str, value: Any, updated_by: str, 
                           change_reason: str = "") -> bool:
        """Update a setting value"""
        if key not in self.settings_cache:
            self.logger.warning(f"Setting {key} not found")
            return False
        
        setting = self.settings_cache[key]
        old_value = setting.value
        
        # Validate value
        if not self._validate_value(value, setting):
            self.logger.error(f"Invalid value for setting {key}")
            return False
        
        # Update setting
        setting.value = value
        setting.updated_by = updated_by
        setting.updated_at = datetime.utcnow()
        setting.version += 1
        
        # Log change
        change = SettingChange(
            id=str(uuid.uuid4()),
            setting_key=key,
            old_value=old_value,
            new_value=value,
            changed_by=updated_by,
            change_reason=change_reason,
            timestamp=datetime.utcnow()
        )
        
        if key not in self.settings_history:
            self.settings_history[key] = []
        self.settings_history[key].append(change)
        
        # Save to database
        if self.database:
            try:
                async with self.database.get_session() as session:
                    await session.execute(
                        text("""
                            UPDATE system_settings
                            SET setting_value = :value, updated_by = :updated_by,
                                updated_at = :updated_at, version = version + 1
                            WHERE setting_key = :key
                        """),
                        {
                            "value": str(value),
                            "updated_by": updated_by,
                            "updated_at": setting.updated_at,
                            "key": key
                        }
                    )
                    
                    await session.execute(
                        text("""
                            INSERT INTO setting_changes (
                                id, setting_key, old_value, new_value,
                                changed_by, change_reason, timestamp
                            )
                            VALUES (:id, :key, :old_value, :new_value, :changed_by, :reason, :timestamp)
                        """),
                        {
                            "id": change.id,
                            "key": key,
                            "old_value": str(old_value),
                            "new_value": str(value),
                            "changed_by": updated_by,
                            "reason": change_reason,
                            "timestamp": change.timestamp
                        }
                    )
                    
                    await session.commit()
            except Exception as e:
                self.logger.error(f"Failed to update setting {key}: {str(e)}")
                return False
        
        # Update cache
        if self.redis:
            try:
                await self.redis.set(f"setting:{key}", str(value), expire=3600)
            except Exception as e:
                self.logger.warning(f"Failed to update Redis cache for setting {key}: {str(e)}")
        
        self.logger.info(f"Setting {key} updated by {updated_by}")
        return True

    def _validate_value(self, value: Any, setting: Setting) -> bool:
        """Validate setting value against validation rules"""
        validation_rules = setting.validation_rules
        
        if setting.setting_type == SettingType.INTEGER:
            if not isinstance(value, int):
                return False
            if "min" in validation_rules and value < validation_rules["min"]:
                return False
            if "max" in validation_rules and value > validation_rules["max"]:
                return False
        
        elif setting.setting_type == SettingType.FLOAT:
            if not isinstance(value, (int, float)):
                return False
            if "min" in validation_rules and value < validation_rules["min"]:
                return False
            if "max" in validation_rules and value > validation_rules["max"]:
                return False
        
        elif setting.setting_type == SettingType.BOOLEAN:
            if not isinstance(value, bool):
                return False
        
        elif setting.setting_type == SettingType.STRING:
            if not isinstance(value, str):
                return False
            if "min_length" in validation_rules and len(value) < validation_rules["min_length"]:
                return False
            if "max_length" in validation_rules and len(value) > validation_rules["max_length"]:
                return False
        
        return True

    async def get_setting_history(self, key: str, limit: int = 50) -> List[SettingChange]:
        """Get change history for a setting"""
        if key in self.settings_history:
            return self.settings_history[key][-limit:]
        
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    text("""
                        SELECT id, setting_key, old_value, new_value, changed_by,
                               change_reason, timestamp, reverted
                        FROM setting_changes
                        WHERE setting_key = :key
                        ORDER BY timestamp DESC
                        LIMIT :limit
                    """),
                    {"key": key, "limit": limit}
                )
                
                changes = []
                for row in result.fetchall():
                    changes.append(SettingChange(
                        id=row[0],
                        setting_key=row[1],
                        old_value=row[2],
                        new_value=row[3],
                        changed_by=row[4],
                        change_reason=row[5] or "",
                        timestamp=row[6],
                        reverted=row[7]
                    ))
                
                return changes
        
        except Exception as e:
            self.logger.error(f"Failed to get setting history for {key}: {str(e)}")
            return []

    async def revert_setting(self, key: str, change_id: str, reverted_by: str) -> bool:
        """Revert a setting to a previous value"""
        history = await self.get_setting_history(key)
        change = next((c for c in history if c.id == change_id), None)
        
        if not change:
            return False
        
        # Update setting to old value
        success = await self.update_setting(
            key, change.old_value, reverted_by,
            f"Reverted from change {change_id}"
        )
        
        if success and self.database:
            try:
                async with self.database.get_session() as session:
                    await session.execute(
                        text("UPDATE setting_changes SET reverted = TRUE WHERE id = :id"),
                        {"id": change_id}
                    )
                    await session.commit()
            except Exception as e:
                self.logger.error(f"Failed to mark change as reverted: {str(e)}")
        
        return success

    async def create_setting(self, key: str, value: Any, setting_type: SettingType,
                           category: SettingCategory, description: str,
                           created_by: str, is_public: bool = False,
                           validation_rules: Dict[str, Any] = None) -> bool:
        """Create a new setting"""
        if key in self.settings_cache:
            self.logger.warning(f"Setting {key} already exists")
            return False
        
        setting = Setting(
            key=key,
            value=value,
            setting_type=setting_type,
            category=category,
            description=description,
            is_public=is_public,
            validation_rules=validation_rules or {},
            updated_by=created_by
        )
        
        if not self._validate_value(value, setting):
            self.logger.error(f"Invalid value for new setting {key}")
            return False
        
        self.settings_cache[key] = setting
        
        if self.database:
            try:
                async with self.database.get_session() as session:
                    await session.execute(
                        text("""
                            INSERT INTO system_settings (
                                setting_key, setting_value, setting_type, category,
                                description, is_public, validation_rules, updated_by
                            )
                            VALUES (:key, :value, :type, :category, :description, :is_public, :validation, :updated_by)
                        """),
                        {
                            "key": key,
                            "value": str(value),
                            "type": setting_type.value,
                            "category": category.value,
                            "description": description,
                            "is_public": is_public,
                            "validation": json.dumps(validation_rules or {}),
                            "updated_by": created_by
                        }
                    )
                    await session.commit()
            except Exception as e:
                self.logger.error(f"Failed to create setting {key}: {str(e)}")
                del self.settings_cache[key]
                return False
        
        self.logger.info(f"Setting {key} created by {created_by}")
        return True

    async def delete_setting(self, key: str, deleted_by: str) -> bool:
        """Delete a setting (soft delete by setting to default)"""
        if key not in self.settings_cache:
            return False
        
        setting = self.settings_cache[key]
        if setting.default_value is None:
            self.logger.warning(f"Cannot delete setting {key} - no default value")
            return False
        
        # Revert to default
        return await self.update_setting(
            key, setting.default_value, deleted_by,
            "Setting reset to default value"
        )

    async def get_settings_by_category(self, category: SettingCategory) -> Dict[str, Setting]:
        """Get all settings in a category"""
        return {k: v for k, v in self.settings_cache.items() if v.category == category}

    async def close(self):
        self.logger.info("Closing SettingsManager...")
        if self.database:
            await self.database.close()

# Global instances
_settings_manager: Optional[SettingsManager] = None

async def init_settings_manager() -> SettingsManager:
    global _settings_manager
    if not _settings_manager:
        _settings_manager = SettingsManager()
        await _settings_manager.initialize()
    return _settings_manager

async def get_settings_manager() -> SettingsManager:
    global _settings_manager
    if not _settings_manager:
        _settings_manager = await init_settings_manager()
    return _settings_manager

