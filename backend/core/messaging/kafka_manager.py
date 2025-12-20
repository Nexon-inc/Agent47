"""Compatibility shim for messaging.kafka_manager

Some legacy code imports backend.core.messaging.kafka_manager.KafkaManager. The
real implementation lives under backend.core.event_bus.kafka_manager. This
module re-exports the class and helper functions for compatibility.
"""
from typing import Optional

try:
    from core.event_bus.kafka_manager import (
        KafkaManager as _KafkaManager,
        kafka_manager as _kafka_manager,
        get_kafka as get_event_bus_kafka,
        init_kafka as init_event_bus_kafka,
        close_kafka as close_event_bus_kafka,
    )
except Exception:  # pragma: no cover
    _KafkaManager = None
    _kafka_manager = None
    def get_event_bus_kafka():
        raise ImportError("backend.core.event_bus.kafka_manager not available")
    def init_event_bus_kafka():
        raise ImportError("backend.core.event_bus.kafka_manager not available")
    def close_event_bus_kafka():
        raise ImportError("backend.core.event_bus.kafka_manager not available")

KafkaManager = _KafkaManager
kafka_manager = _kafka_manager
get_kafka = get_event_bus_kafka
init_kafka = init_event_bus_kafka
close_kafka = close_event_bus_kafka

__all__ = ["KafkaManager", "kafka_manager", "get_kafka", "init_kafka", "close_kafka"]
