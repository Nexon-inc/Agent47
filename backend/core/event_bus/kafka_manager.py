import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List, Union
from datetime import datetime

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import KafkaError, UnknownTopicOrPartitionError

# ─── Google Auth imports (for fallback) ─────────────────────────────────
from google.auth import default
from google.auth.transport.requests import Request

from aiokafka.abc import AbstractTokenProvider

from ..config import settings

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.handlers: Dict[str, List[Callable]] = {}
        self._initialized = False
        self._running = False

    def _get_kafka_connection_kwargs(self) -> Dict[str, Any]:
        """Build common Kafka connection kwargs with SSL/TLS and SASL configuration"""
        kwargs = {
            'bootstrap_servers': settings.kafka.bootstrap_servers,
        }

        is_managed_kafka = '.managedkafka.' in settings.kafka.bootstrap_servers.lower()
        is_confluent = 'confluent.cloud' in settings.kafka.bootstrap_servers.lower()

        security_protocol = settings.kafka.security_protocol

        if is_managed_kafka:
            if security_protocol in ('PLAINTEXT', None):
                logger.info("Detected Google Cloud Managed Kafka → forcing SASL_SSL + OAUTHBEARER")
                security_protocol = 'SASL_SSL'

        if is_confluent:
            logger.info("Detected Confluent Cloud Kafka → forcing SASL_SSL + PLAIN authentication")
            security_protocol = 'SASL_SSL'

        # SSL/TLS configuration
        if security_protocol in ('SSL', 'SASL_SSL'):
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = settings.kafka.ssl_check_hostname

            if not settings.kafka.ssl_check_hostname:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            if settings.kafka.ssl_cafile:
                ssl_context.load_verify_locations(settings.kafka.ssl_cafile)

            if settings.kafka.ssl_certfile and settings.kafka.ssl_keyfile:
                ssl_context.load_cert_chain(
                    certfile=settings.kafka.ssl_certfile,
                    keyfile=settings.kafka.ssl_keyfile
                )

            kwargs['ssl_context'] = ssl_context

        # SASL configuration
        if security_protocol in ('SASL_PLAINTEXT', 'SASL_SSL'):
            if is_confluent:
                if settings.kafka.sasl_username and settings.kafka.sasl_password:
                    logger.info("Applying Confluent SASL/PLAIN credentials")
                    kwargs.update({
                        'security_protocol': 'SASL_SSL',
                        'sasl_mechanism': 'PLAIN',
                        'sasl_plain_username': settings.kafka.sasl_username,
                        'sasl_plain_password': settings.kafka.sasl_password,
                    })
                else:
                    logger.error("Confluent detected but missing SASL username or password!")

            elif is_managed_kafka:
                logger.info("Configuring OAUTHBEARER for Google Managed Kafka")
                credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

                class GoogleOAuthTokenProvider(AbstractTokenProvider):
                    def __init__(self, credentials):
                        self.credentials = credentials

                    async def token(self):
                        if not self.credentials.valid:
                            logger.info("Refreshing Google OAuth token for Kafka...")
                            self.credentials.refresh(Request())
                        return {
                            'token': self.credentials.token,
                            'extensions': {}
                        }

                token_provider = GoogleOAuthTokenProvider(credentials)

                kwargs.update({
                    'security_protocol': 'SASL_SSL',
                    'sasl_mechanism': 'OAUTHBEARER',
                    'sasl_oauth_token_provider': token_provider,
                })

            elif settings.kafka.sasl_mechanism:
                kwargs['security_protocol'] = security_protocol
                kwargs['sasl_mechanism'] = settings.kafka.sasl_mechanism

                if settings.kafka.sasl_username and settings.kafka.sasl_password:
                    kwargs['sasl_plain_username'] = settings.kafka.sasl_username
                    kwargs['sasl_plain_password'] = settings.kafka.sasl_password
                elif settings.kafka.sasl_mechanism == 'OAUTHBEARER':
                    logger.warning("OAUTHBEARER configured but no token provider provided")

            else:
                logger.warning(f"Security protocol {security_protocol} requires SASL mechanism but none specified")

        elif security_protocol != 'PLAINTEXT':
            kwargs['security_protocol'] = security_protocol

        return kwargs

    async def initialize(self):
        if self._initialized:
            return

        try:
            import inspect

            connection_kwargs = self._get_kafka_connection_kwargs()

            producer_kwargs = {
                'client_id': settings.kafka.client_id or "agent47-backend",
                'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
                'key_serializer': lambda k: k.encode('utf-8') if k else None,
                'acks': 'all',
                'retries': 3,
                'max_in_flight_requests_per_connection': 5,
                'request_timeout_ms': 15000,
                'metadata_max_age_ms': 300000,
                'connections_max_idle_ms': 540000,
                **connection_kwargs
            }

            try:
                sig = inspect.signature(AIOKafkaProducer.__init__)
                accepted = {p for p in sig.parameters.keys() if p != 'self'}
                filtered = {k: v for k, v in producer_kwargs.items() if k in accepted}
                self.producer = AIOKafkaProducer(**filtered)
            except Exception:
                self.producer = AIOKafkaProducer(**producer_kwargs)

            logger.info(f"Starting Kafka producer - bootstrap: {settings.kafka.bootstrap_servers}")

            await asyncio.wait_for(self.producer.start(), timeout=25.0)  # slightly longer timeout
            self._initialized = True
            logger.info("Kafka producer started successfully")

            # Ensure health_check topic exists
            try:
                admin_client = AIOKafkaAdminClient(**connection_kwargs)
                await admin_client.start()
                topics = await admin_client.list_topics()
                if "health_check" not in topics:
                    logger.info("health_check topic missing → creating it")
                    new_topic = NewTopic("health_check", num_partitions=1, replication_factor=1)
                    await admin_client.create_topics([new_topic])
                    logger.info("health_check topic created")
                    await asyncio.sleep(3)  # give broker time to propagate metadata
                else:
                    logger.debug("health_check topic already exists")
                await admin_client.close()
            except Exception as e:
                logger.warning(f"Failed to ensure health_check topic: {str(e)}")

        except asyncio.TimeoutError:
            logger.error(f"Producer start timed out after 25s - bootstrap: {settings.kafka.bootstrap_servers}")
            if self.producer:
                try:
                    await self.producer.stop()
                except Exception as cleanup_e:
                    logger.warning(f"Stop failed during timeout cleanup: {cleanup_e}")
            self.producer = None
            raise

        except Exception as e:
            logger.error(f"Kafka producer initialization failed: {str(e)}", exc_info=True)
            if self.producer:
                try:
                    await self.producer.stop()
                except Exception as cleanup_e:
                    logger.warning(f"Cleanup failed: {cleanup_e}")
            self.producer = None
            raise

    async def close(self):
        self._running = False
        for consumer in self.consumers.values():
            try:
                await consumer.stop()
            except Exception as e:
                logger.error(f"Error stopping consumer: {e}")
        if self.producer:
            try:
                await self.producer.stop()
            except Exception as e:
                logger.error(f"Error stopping producer: {e}")
        self._initialized = False
        logger.info("Kafka connections closed")

    async def health_check(self) -> bool:
        try:
            if not self._initialized:
                await self.initialize()

            # Give extra time after possible topic creation
            await asyncio.sleep(3)

            await self.producer.send_and_wait(
                topic="health_check",
                value={"timestamp": datetime.utcnow().isoformat(), "status": "health_check"},
                key="health_check"
            )
            logger.info("Kafka health check passed - test message sent")
            return True

        except (KafkaError, UnknownTopicOrPartitionError) as e:
            logger.warning(f"Health check failed (possibly transient): {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Kafka health check failed critically: {str(e)}", exc_info=True)
            return False

    async def publish_event(
        self,
        topic: str,
        event_data: Dict[str, Any],
        key: Optional[str] = None,
        partition: Optional[int] = None,
        timestamp: Optional[int] = None
    ) -> bool:
        if not self._initialized:
            await self.initialize()
        try:
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
            logger.info(f"Published event to topic: {topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {str(e)}")
            return False

    # ... (all other methods like subscribe_to_topic, create_topic, etc. remain unchanged)


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
        # Implement if needed
        return True  # placeholder

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

    async def publish_batch_events(
        self,
        topic: str,
        events: List[Dict[str, Any]],
        keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        return await self.event_bus.publish_batch_events(topic, events, keys)


# Global singleton
kafka_manager = KafkaManager()


async def get_kafka() -> KafkaManager:
    return kafka_manager


async def init_kafka():
    await kafka_manager.initialize()


async def close_kafka():
    await kafka_manager.close()


def get_event_bus() -> EventBus:
    """FastAPI dependency"""
    return kafka_manager.event_bus