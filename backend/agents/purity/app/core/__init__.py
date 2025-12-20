"""Compatibility shim for agent-level `core` package imports.

Many agent service modules use relative imports like `from ..core.kafka_manager import KafkaManager`.
Create local shims that re-export symbols from the centralized `backend.core` package so those
relative imports continue to work without touching every service implementation.
"""
from core.event_bus.kafka_manager import KafkaManager, EventBus, kafka_manager, get_kafka, init_kafka, close_kafka, get_event_bus
from core.cache.redis_manager import RedisManager, get_redis, init_redis, close_redis
from core.integrations.integration_manager import IntegrationManager, integration_manager, get_integration_manager, init_integrations
from core.platforms.platform_manager import PlatformManager, platform_manager, get_platform_manager, init_platforms

__all__ = [
    "KafkaManager", "EventBus", "kafka_manager", "get_kafka", "init_kafka", "close_kafka", "get_event_bus",
    "RedisManager", "get_redis", "init_redis", "close_redis",
    "IntegrationManager", "integration_manager", "get_integration_manager", "init_integrations",
    "PlatformManager", "platform_manager", "get_platform_manager", "init_platforms",
]
