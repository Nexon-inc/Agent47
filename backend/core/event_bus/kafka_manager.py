import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List, Union
from datetime import datetime
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError
from ..config import settings

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.handlers: Dict[str, List[Callable]] = {}
        self._initialized = False
        self._running = False
    
    async def initialize(self):
        if self._initialized:
            return
        
        try:
            # Build kwargs and filter them to the constructor signature of AIOKafkaProducer
            import inspect

            producer_kwargs = {
                'bootstrap_servers': settings.kafka.kafka_bootstrap_servers,
                'client_id': settings.kafka.kafka_client_id,
                'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
                'key_serializer': lambda k: k.encode('utf-8') if k else None,
                'acks': 'all',
                'retries': 3,
                'max_in_flight_requests_per_connection': 5
            }

            producer_kwargs['request_timeout_ms'] = 10000
            producer_kwargs['metadata_max_age_ms'] = 300000
            producer_kwargs['connections_max_idle_ms'] = 540000

            try:
                sig = inspect.signature(AIOKafkaProducer.__init__)
                accepted = {p for p in sig.parameters.keys() if p != 'self'}
                filtered = {k: v for k, v in producer_kwargs.items() if k in accepted}
                self.producer = AIOKafkaProducer(**filtered)
            except Exception:
                self.producer = AIOKafkaProducer(**producer_kwargs)
            
            try:
                await asyncio.wait_for(self.producer.start(), timeout=10.0)
                self._initialized = True
                logger.info("Kafka producer initialized successfully")
            except asyncio.TimeoutError:
                logger.error("Kafka producer start timed out after 10s")
                self.producer = None
                raise asyncio.TimeoutError("Kafka producer initialization timed out")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None
            raise
    
    async def close(self):
        """Close all Kafka connections"""
        self._running = False
        
        # Close consumers
        for consumer in self.consumers.values():
            try:
                await consumer.stop()
            except Exception as e:
                logger.error(f"Error closing consumer: {e}")
        
        # Close producer
        if self.producer:
            try:
                await self.producer.stop()
            except Exception as e:
                logger.error(f"Error closing producer: {e}")
        
        self._initialized = False
        logger.info("Kafka connections closed")
    
    async def health_check(self) -> bool:
        """Check Kafka health"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Try to send a test message
            await self.producer.send_and_wait(
                topic="health_check",
                value={"timestamp": datetime.utcnow().isoformat()},
                key="health_check"
            )
            return True
        except Exception as e:
            logger.error(f"Kafka health check failed: {e}")
            return False
    
    async def publish_event(
        self,
        topic: str,
        event_data: Dict[str, Any],
        key: Optional[str] = None,
        partition: Optional[int] = None,
        timestamp: Optional[int] = None
    ) -> bool:
        """Publish an event to a topic"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Add metadata to event
            event_with_metadata = {
                "data": event_data,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "agent47_core",
                    "version": "1.0.0"
                }
            }
            
            await self.producer.send_and_wait(
                topic=topic,
                value=event_with_metadata,
                key=key,
                partition=partition,
                timestamp=timestamp
            )
            
            logger.info(f"Event published to topic {topic}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event to topic {topic}: {e}")
            return False
    
    async def subscribe_to_topic(
        self,
        topic: str,
        group_id: Optional[str] = None,
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = True
    ) -> bool:
        """Subscribe to a topic"""
        if not self._initialized:
            await self.initialize()
        
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=settings.kafka.kafka_bootstrap_servers,
                group_id=group_id or f"{settings.kafka.kafka_group_id}_{topic}",
                auto_offset_reset=auto_offset_reset,
                enable_auto_commit=enable_auto_commit,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda m: m.decode('utf-8') if m else None
            )
            
            await consumer.start()
            self.consumers[topic] = consumer
            
            # Start consuming messages
            asyncio.create_task(self._consume_messages(topic, consumer))
            
            logger.info(f"Subscribed to topic {topic}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to topic {topic}: {e}")
            return False
    
    async def _consume_messages(self, topic: str, consumer: AIOKafkaConsumer):
        """Consume messages from a topic"""
        try:
            async for message in consumer:
                try:
                    # Process the message
                    await self._process_message(topic, message)
                    
                    # Commit offset if auto-commit is disabled
                    if not consumer._auto_commit:
                        await consumer.commit()
                        
                except Exception as e:
                    logger.error(f"Error processing message from topic {topic}: {e}")
                    
        except Exception as e:
            logger.error(f"Error consuming messages from topic {topic}: {e}")
        finally:
            try:
                await consumer.stop()
            except Exception as e:
                logger.error(f"Error stopping consumer for topic {topic}: {e}")
    
    async def _process_message(self, topic: str, message):
        """Process a received message"""
        try:
            # Extract event data
            event_data = message.value
            event_key = message.key
            
            # Call registered handlers
            if topic in self.handlers:
                for handler in self.handlers[topic]:
                    try:
                        await handler(event_data, event_key, topic)
                    except Exception as e:
                        logger.error(f"Error in event handler for topic {topic}: {e}")
            
            logger.debug(f"Processed message from topic {topic}")
            
        except Exception as e:
            logger.error(f"Failed to process message from topic {topic}: {e}")
    
    def register_handler(self, topic: str, handler: Callable):
        """Register a handler for a topic"""
        if topic not in self.handlers:
            self.handlers[topic] = []
        
        self.handlers[topic].append(handler)
        logger.info(f"Handler registered for topic {topic}")
    
    def unregister_handler(self, topic: str, handler: Callable):
        """Unregister a handler from a topic"""
        if topic in self.handlers and handler in self.handlers[topic]:
            self.handlers[topic].remove(handler)
            logger.info(f"Handler unregistered from topic {topic}")
    
    async def create_topic(self, topic: str, num_partitions: int = 1, replication_factor: int = 1) -> bool:
        """Create a new topic (requires admin privileges)"""
        try:
            from kafka.admin import KafkaAdminClient, NewTopic
            
            admin_client = KafkaAdminClient(
                bootstrap_servers=settings.kafka.kafka_bootstrap_servers
            )
            
            new_topic = NewTopic(
                name=topic,
                num_partitions=num_partitions,
                replication_factor=replication_factor
            )
            
            admin_client.create_topics([new_topic])
            admin_client.close()
            
            logger.info(f"Topic {topic} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create topic {topic}: {e}")
            return False
    
    async def list_topics(self) -> List[str]:
        """List all available topics"""
        try:
            from kafka import KafkaConsumer
            
            consumer = KafkaConsumer(
                bootstrap_servers=settings.kafka.kafka_bootstrap_servers
            )
            
            topics = list(consumer.topics())
            consumer.close()
            
            return topics
            
        except Exception as e:
            logger.error(f"Failed to list topics: {e}")
            return []
    
    async def get_topic_info(self, topic: str) -> Dict[str, Any]:
        """Get information about a topic"""
        try:
            from kafka import KafkaConsumer
            
            consumer = KafkaConsumer(
                bootstrap_servers=settings.kafka.kafka_bootstrap_servers
            )
            
            partitions = consumer.partitions_for_topic(topic)
            if not partitions:
                return {"error": "Topic not found"}
            
            topic_info = {
                "name": topic,
                "partitions": len(partitions),
                "partition_info": {}
            }
            
            for partition in partitions:
                # Get partition metadata
                partition_metadata = consumer.partitions_for_topic(topic)
                if partition_metadata:
                    topic_info["partition_info"][partition] = {
                        "leader": partition_metadata.get(partition, {}).get("leader"),
                        "replicas": partition_metadata.get(partition, {}).get("replicas", [])
                    }
            
            consumer.close()
            return topic_info
            
        except Exception as e:
            logger.error(f"Failed to get topic info for {topic}: {e}")
            return {"error": str(e)}
    
    async def publish_batch_events(
        self,
        topic: str,
        events: List[Dict[str, Any]],
        keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Publish multiple events in batch"""
        if not self._initialized:
            await self.initialize()
        
        try:
            results = {
                "published": 0,
                "failed": 0,
                "errors": []
            }
            
            for i, event_data in enumerate(events):
                key = keys[i] if keys and i < len(keys) else None
                
                try:
                    await self.publish_event(topic, event_data, key)
                    results["published"] += 1
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({
                        "index": i,
                        "error": str(e)
                    })
            
            logger.info(f"Batch publish completed for topic {topic}: {results['published']} published, {results['failed']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Failed to publish batch events to topic {topic}: {e}")
            return {"published": 0, "failed": len(events), "errors": [{"error": str(e)}]}

class KafkaManager:
    def __init__(self):
        self.event_bus = EventBus()
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        
        await self.event_bus.initialize()
        self._initialized = True
    
    async def close(self):
        await self.event_bus.close()
        self._initialized = False
    
    async def health_check(self) -> bool:
        return await self.event_bus.health_check()
    
    async def publish_event(self, topic: str, event_data: Dict[str, Any], key: Optional[str] = None) -> bool:
        return await self.event_bus.publish_event(topic, event_data, key)
    
    async def subscribe_to_topic(self, topic: str, group_id: Optional[str] = None) -> bool:
        return await self.event_bus.subscribe_to_topic(topic, group_id)
    
    def register_handler(self, topic: str, handler: Callable):
        self.event_bus.register_handler(topic, handler)
    
    def unregister_handler(self, topic: str, handler: Callable):
        self.event_bus.unregister_handler(topic, handler)
    
    async def create_topic(self, topic: str, num_partitions: int = 1, replication_factor: int = 1) -> bool:
        return await self.event_bus.create_topic(topic, num_partitions, replication_factor)
    
    async def list_topics(self) -> List[str]:
        return await self.event_bus.list_topics()
    
    async def get_topic_info(self, topic: str) -> Dict[str, Any]:
        return await self.event_bus.get_topic_info(topic)
    
    async def publish_batch_events(self, topic: str, events: List[Dict[str, Any]], keys: Optional[List[str]] = None) -> Dict[str, Any]:
        return await self.event_bus.publish_batch_events(topic, events, keys)

# Global Kafka manager instance
kafka_manager = KafkaManager()

async def get_kafka() -> KafkaManager:
    return kafka_manager

async def init_kafka():
    await kafka_manager.initialize()

async def close_kafka():
    await kafka_manager.close()


def get_event_bus() -> EventBus:
    """Return the EventBus instance for use as a FastAPI dependency.

    Note: this returns the EventBus object; callers who need it initialized
    should call its initialize method asynchronously.
    """
    return kafka_manager.event_bus
