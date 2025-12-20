"""Compatibility shim for Shakes agent core imports.

This module re-exports commonly used utilities from the shared `backend.core`
package so agent-local imports like `from .core import *` continue to work.
"""
from core.event_bus.kafka_manager import KafkaManager, kafka_manager, get_event_bus
from core.cache.redis_manager import RedisManager, get_redis, init_redis, close_redis
from core.integrations.integration_manager import IntegrationManager, integration_manager
from core.platforms.platform_manager import PlatformManager, platform_manager
from core.event_bus.kafka_manager import EventBus

__all__ = [
    "KafkaManager",
    "kafka_manager",
    "get_event_bus",
    "RedisManager",
    "get_redis",
    "init_redis",
    "close_redis",
    "IntegrationManager",
    "integration_manager",
    "PlatformManager",
    "platform_manager",
    "EventBus",
]
