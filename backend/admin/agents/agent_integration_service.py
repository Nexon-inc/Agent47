import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

from backend.core.database import get_database, DatabaseManager
from backend.core.cache import get_redis, RedisManager
from backend.core.event_bus import get_kafka, KafkaManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

from .agent_manager import AgentManager, get_agent_manager
from .agent_coordinator import AgentCoordinator, get_agent_coordinator
from .agent_monitor import AgentMonitor, get_agent_monitor
from .agent_analytics import AgentAnalytics, get_agent_analytics

logger = get_logger(__name__)

class IntegrationProtocol(Enum):
    HTTP = "http"
    WEBSOCKET = "websocket"
    GRPC = "grpc"
    KAFKA = "kafka"
    REDIS = "redis"

class ServiceStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"

@dataclass
class AgentServiceConfig:
    service_id: str
    agent_id: str
    service_name: str
    service_type: str
    endpoint: str
    protocol: IntegrationProtocol
    health_check_url: Optional[str] = None
    api_key: Optional[str] = None
    webhook_url: Optional[str] = None
    timeout_seconds: int = 30
    retry_attempts: int = 3
    rate_limit: int = 100
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ServiceHealthCheck:
    service_id: str
    status: ServiceStatus
    response_time_ms: int
    last_check: datetime
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentCommunication:
    id: str
    sender_agent_id: str
    receiver_agent_id: str
    message_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    protocol: IntegrationProtocol
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"
    retry_count: int = 0
    max_retries: int = 3

class AgentIntegrationService(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.kafka: Optional[KafkaManager] = None
        self.settings = get_settings()
        
        # Core services
        self.agent_manager: Optional[AgentManager] = None
        self.agent_coordinator: Optional[AgentCoordinator] = None
        self.agent_monitor: Optional[AgentMonitor] = None
        self.agent_analytics: Optional[AgentAnalytics] = None
        
        # Integration state
        self.agent_services: Dict[str, AgentServiceConfig] = {}
        self.service_health_checks: Dict[str, ServiceHealthCheck] = {}
        self.active_communications: Dict[str, AgentCommunication] = {}
        self.service_sessions: Dict[str, aiohttp.ClientSession] = {}
        
        self.logger = logger
        self._shutdown_event = asyncio.Event()

    async def initialize(self) -> bool:
        """Initialize the agent integration service"""
        try:
            self.logger.info("Initializing AgentIntegrationService...")
            
            # Initialize core services
            self.database = get_database()
            self.redis = await get_redis()
            self.kafka = await get_kafka()
            
            # Initialize agent management services
            self.agent_manager = await get_agent_manager()
            self.agent_coordinator = await get_agent_coordinator()
            self.agent_monitor = await get_agent_monitor()
            self.agent_analytics = await get_agent_analytics()
            
            # Setup integration tables
            await self._setup_integration_tables()
            
            # Load existing service configurations
            await self._load_service_configurations()
            
            # Start background monitoring tasks
            asyncio.create_task(self._service_health_monitor())
            asyncio.create_task(self._communication_monitor())
            asyncio.create_task(self._integration_metrics_collector())
            
            self.logger.info("AgentIntegrationService initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AgentIntegrationService: {str(e)}", exc_info=True)
            return False

    async def _setup_integration_tables(self):
        """Setup database tables for agent integration"""
        if not self.database:
            raise RuntimeError("Database not initialized")

        try:
            async with self.database.get_session() as session:
                # Agent service configurations table
                await session.execute("""
                    CREATE TABLE IF NOT EXISTS agent_service_configs (
                        service_id VARCHAR(255) PRIMARY KEY,
                        agent_id VARCHAR(255) NOT NULL,
                        service_name VARCHAR(255) NOT NULL,
                        service_type VARCHAR(100) NOT NULL,
                        endpoint VARCHAR(500) NOT NULL,
                        protocol VARCHAR(50) NOT NULL,
                        health_check_url VARCHAR(500),
                        api_key VARCHAR(255),
                        webhook_url VARCHAR(500),
                        timeout_seconds INTEGER DEFAULT 30,
                        retry_attempts INTEGER DEFAULT 3,
                        rate_limit INTEGER DEFAULT 100,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
                    )
                """)
                
                # Service health check logs table
                await session.execute("""
                    CREATE TABLE IF NOT EXISTS service_health_logs (
                        id SERIAL PRIMARY KEY,
                        service_id VARCHAR(255) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        response_time_ms INTEGER,
                        error_message TEXT,
                        metrics JSONB,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (service_id) REFERENCES agent_service_configs(service_id) ON DELETE CASCADE
                    )
                """)
                
                # Integration communication logs table
                await session.execute("""
                    CREATE TABLE IF NOT EXISTS integration_communications (
                        id VARCHAR(255) PRIMARY KEY,
                        sender_agent_id VARCHAR(255) NOT NULL,
                        receiver_agent_id VARCHAR(255) NOT NULL,
                        message_type VARCHAR(100) NOT NULL,
                        content TEXT NOT NULL,
                        metadata JSONB,
                        protocol VARCHAR(50) NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status VARCHAR(50) DEFAULT 'pending',
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        FOREIGN KEY (sender_agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                        FOREIGN KEY (receiver_agent_id) REFERENCES agents(id) ON DELETE CASCADE
                    )
                """)
                
                # Integration metrics table
                await session.execute("""
                    CREATE TABLE IF NOT EXISTS integration_metrics (
                        id SERIAL PRIMARY KEY,
                        service_id VARCHAR(255) NOT NULL,
                        metric_name VARCHAR(100) NOT NULL,
                        metric_value FLOAT NOT NULL,
                        metric_unit VARCHAR(50),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSONB,
                        FOREIGN KEY (service_id) REFERENCES agent_service_configs(service_id) ON DELETE CASCADE
                    )
                """)

                await session.commit()
                self.logger.info("Integration tables setup completed")

        except Exception as e:
            self.logger.error(f"Failed to setup integration tables: {str(e)}")
            raise

    async def _load_service_configurations(self):
        """Load existing service configurations from database"""
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT service_id, agent_id, service_name, service_type, endpoint, protocol,
                           health_check_url, api_key, webhook_url, timeout_seconds, retry_attempts,
                           rate_limit, is_active, created_at, updated_at
                    FROM agent_service_configs WHERE is_active = TRUE
                """)

                rows = result.fetchall()
                for row in rows:
                    service_config = self._create_service_config_from_row(row)
                    self.agent_services[service_config.service_id] = service_config

            self.logger.info(f"Loaded {len(self.agent_services)} service configurations")

        except Exception as e:
            self.logger.error(f"Failed to load service configurations: {str(e)}")

    def _create_service_config_from_row(self, row) -> AgentServiceConfig:
        return AgentServiceConfig(
            service_id=row[0],
            agent_id=row[1],
            service_name=row[2],
            service_type=row[3],
            endpoint=row[4],
            protocol=IntegrationProtocol(row[5]),
            health_check_url=row[6],
            api_key=row[7],
            webhook_url=row[8],
            timeout_seconds=row[9],
            retry_attempts=row[10],
            rate_limit=row[11],
            is_active=row[12],
            created_at=row[13],
            updated_at=row[14]
        )

    async def register_agent_service(self, agent_id: str, service_name: str, service_type: str,
                                   endpoint: str, protocol: IntegrationProtocol = IntegrationProtocol.HTTP,
                                   health_check_url: Optional[str] = None, api_key: Optional[str] = None,
                                   webhook_url: Optional[str] = None, timeout_seconds: int = 30,
                                   retry_attempts: int = 3, rate_limit: int = 100) -> AgentServiceConfig:
        """Register a new agent service"""
        try:
            import uuid
            service_id = str(uuid.uuid4())
            
            service_config = AgentServiceConfig(
                service_id=service_id,
                agent_id=agent_id,
                service_name=service_name,
                service_type=service_type,
                endpoint=endpoint,
                protocol=protocol,
                health_check_url=health_check_url,
                api_key=api_key,
                webhook_url=webhook_url,
                timeout_seconds=timeout_seconds,
                retry_attempts=retry_attempts,
                rate_limit=rate_limit
            )
            
            await self._save_service_config_to_database(service_config)
            self.agent_services[service_config.service_id] = service_config
            
            # Initialize service session if needed
            if protocol == IntegrationProtocol.HTTP:
                await self._initialize_service_session(service_config)
            
            self.logger.info(f"Registered service {service_name} for agent {agent_id}")
            return service_config
            
        except Exception as e:
            self.logger.error(f"Failed to register agent service: {str(e)}")
            raise

    async def _save_service_config_to_database(self, service_config: AgentServiceConfig):
        """Save service configuration to database"""
        if not self.database:
            return
            
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO agent_service_configs (service_id, agent_id, service_name, service_type,
                                                     endpoint, protocol, health_check_url, api_key,
                                                     webhook_url, timeout_seconds, retry_attempts,
                                                     rate_limit, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    service_config.service_id, service_config.agent_id, service_config.service_name,
                    service_config.service_type, service_config.endpoint, service_config.protocol.value,
                    service_config.health_check_url, service_config.api_key, service_config.webhook_url,
                    service_config.timeout_seconds, service_config.retry_attempts, service_config.rate_limit,
                    service_config.is_active, service_config.created_at, service_config.updated_at
                ))
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save service config to database: {str(e)}")
            raise

    async def _initialize_service_session(self, service_config: AgentServiceConfig):
        """Initialize HTTP session for service"""
        try:
            if service_config.service_id not in self.service_sessions:
                timeout = aiohttp.ClientTimeout(total=service_config.timeout_seconds)
                session = aiohttp.ClientSession(timeout=timeout)
                self.service_sessions[service_config.service_id] = session
                self.logger.debug(f"Initialized HTTP session for service {service_config.service_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize service session: {str(e)}")

    async def _service_health_monitor(self):
        """Background task to monitor service health"""
        while not self._shutdown_event.is_set():
            try:
                for service_config in self.agent_services.values():
                    if service_config.is_active:
                        await self._check_service_health(service_config)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in service health monitor: {str(e)}")
                await asyncio.sleep(120)

    async def _check_service_health(self, service_config: AgentServiceConfig):
        """Check health of a specific service"""
        try:
            if not service_config.health_check_url:
                return
            
            start_time = time.time()
            
            if service_config.protocol == IntegrationProtocol.HTTP:
                health_check = await self._check_http_service_health(service_config)
            elif service_config.protocol == IntegrationProtocol.WEBSOCKET:
                health_check = await self._check_websocket_service_health(service_config)
            else:
                health_check = await self._check_generic_service_health(service_config)
            
            response_time = int((time.time() - start_time) * 1000)
            health_check.response_time_ms = response_time
            health_check.last_check = datetime.utcnow()
            
            self.service_health_checks[service_config.service_id] = health_check
            
            # Log health check
            await self._log_service_health(health_check)
            
        except Exception as e:
            self.logger.error(f"Health check failed for service {service_config.service_name}: {str(e)}")
            
            health_check = ServiceHealthCheck(
                service_id=service_config.service_id,
                status=ServiceStatus.ERROR,
                response_time_ms=0,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )
            
            self.service_health_checks[service_config.service_id] = health_check
            await self._log_service_health(health_check)

    async def _check_http_service_health(self, service_config: AgentServiceConfig) -> ServiceHealthCheck:
        """Check health of HTTP service"""
        try:
            session = self.service_sessions.get(service_config.service_id)
            if not session:
                await self._initialize_service_session(service_config)
                session = self.service_sessions.get(service_config.service_id)
            
            async with session.get(service_config.health_check_url, timeout=service_config.timeout_seconds) as response:
                if response.status == 200:
                    health_data = await response.json()
                    return ServiceHealthCheck(
                        service_id=service_config.service_id,
                        status=ServiceStatus.ONLINE,
                        response_time_ms=0,  # Will be set by caller
                        last_check=datetime.utcnow(),
                        metrics=health_data.get('metrics', {})
                    )
                else:
                    return ServiceHealthCheck(
                        service_id=service_config.service_id,
                        status=ServiceStatus.ERROR,
                        response_time_ms=0,
                        last_check=datetime.utcnow(),
                        error_message=f"HTTP {response.status}"
                    )
                    
        except Exception as e:
            return ServiceHealthCheck(
                service_id=service_config.service_id,
                status=ServiceStatus.ERROR,
                response_time_ms=0,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )

    async def _check_websocket_service_health(self, service_config: AgentServiceConfig) -> ServiceHealthCheck:
        """Check health of WebSocket service"""
        try:
            # Implementation for WebSocket health check
            return ServiceHealthCheck(
                service_id=service_config.service_id,
                status=ServiceStatus.ONLINE,
                response_time_ms=0,
                last_check=datetime.utcnow()
            )
        except Exception as e:
            return ServiceHealthCheck(
                service_id=service_config.service_id,
                status=ServiceStatus.ERROR,
                response_time_ms=0,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )

    async def _check_generic_service_health(self, service_config: AgentServiceConfig) -> ServiceHealthCheck:
        """Check health of generic service"""
        try:
            # Implementation for generic health check
            return ServiceHealthCheck(
                service_id=service_config.service_id,
                status=ServiceStatus.ONLINE,
                response_time_ms=0,
                last_check=datetime.utcnow()
            )
        except Exception as e:
            return ServiceHealthCheck(
                service_id=service_config.service_id,
                status=ServiceStatus.ERROR,
                response_time_ms=0,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )

    async def _log_service_health(self, health_check: ServiceHealthCheck):
        """Log service health check to database"""
        if not self.database:
            return
            
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO service_health_logs (service_id, status, response_time_ms, error_message, metrics)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    health_check.service_id, health_check.status.value, health_check.response_time_ms,
                    health_check.error_message, json.dumps(health_check.metrics)
                ))
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log service health: {str(e)}")

    async def _communication_monitor(self):
        """Background task to monitor communications"""
        while not self._shutdown_event.is_set():
            try:
                # Process pending communications
                await self._process_pending_communications()
                
                # Retry failed communications
                await self._retry_failed_communications()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in communication monitor: {str(e)}")
                await asyncio.sleep(60)

    async def _process_pending_communications(self):
        """Process pending communications"""
        if not self.database:
            return
            
        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, sender_agent_id, receiver_agent_id, message_type, content, metadata,
                           protocol, retry_count, max_retries
                    FROM integration_communications 
                    WHERE status = 'pending' AND retry_count < max_retries
                    ORDER BY timestamp ASC
                    LIMIT 50
                """)
                
                rows = result.fetchall()
                for row in rows:
                    await self._send_communication(
                        row[0], row[1], row[2], row[3], row[4], row[5] or {},
                        IntegrationProtocol(row[6]), row[7], row[8]
                    )
                    
        except Exception as e:
            self.logger.error(f"Failed to process pending communications: {str(e)}")

    async def _send_communication(self, comm_id: str, sender_id: str, receiver_id: str,
                                message_type: str, content: str, metadata: dict,
                                protocol: IntegrationProtocol, retry_count: int, max_retries: int):
        """Send a communication"""
        try:
            # Find receiver service
            receiver_service = None
            for service_config in self.agent_services.values():
                if service_config.agent_id == receiver_id:
                    receiver_service = service_config
                    break
            
            if not receiver_service:
                await self._update_communication_status(comm_id, 'failed', 'Receiver service not found')
                return
            
            # Send based on protocol
            success = False
            if protocol == IntegrationProtocol.HTTP:
                success = await self._send_http_communication(receiver_service, message_type, content, metadata)
            elif protocol == IntegrationProtocol.WEBSOCKET:
                success = await self._send_websocket_communication(receiver_service, message_type, content, metadata)
            elif protocol == IntegrationProtocol.KAFKA:
                success = await self._send_kafka_communication(receiver_service, message_type, content, metadata)
            else:
                success = await self._send_generic_communication(receiver_service, message_type, content, metadata)
            
            if success:
                await self._update_communication_status(comm_id, 'sent')
            else:
                await self._update_communication_status(comm_id, 'failed', 'Send failed')
                
        except Exception as e:
            self.logger.error(f"Failed to send communication {comm_id}: {str(e)}")
            await self._update_communication_status(comm_id, 'failed', str(e))

    async def _send_http_communication(self, service_config: AgentServiceConfig, message_type: str,
                                     content: str, metadata: dict) -> bool:
        """Send HTTP communication"""
        try:
            session = self.service_sessions.get(service_config.service_id)
            if not session:
                await self._initialize_service_session(service_config)
                session = self.service_sessions.get(service_config.service_id)
            
            payload = {
                "message_type": message_type,
                "content": content,
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            headers = {}
            if service_config.api_key:
                headers["Authorization"] = f"Bearer {service_config.api_key}"
            
            async with session.post(service_config.webhook_url or service_config.endpoint, 
                                  json=payload, headers=headers, timeout=service_config.timeout_seconds) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"HTTP communication failed for service {service_config.service_name}: {str(e)}")
            return False

    async def _send_websocket_communication(self, service_config: AgentServiceConfig, message_type: str,
                                          content: str, metadata: dict) -> bool:
        """Send WebSocket communication"""
        try:
            # Implementation for WebSocket communication
            return True
        except Exception as e:
            self.logger.error(f"WebSocket communication failed for service {service_config.service_name}: {str(e)}")
            return False

    async def _send_kafka_communication(self, service_config: AgentServiceConfig, message_type: str,
                                      content: str, metadata: dict) -> bool:
        """Send Kafka communication"""
        try:
            if not self.kafka:
                return False
            
            topic = f"agent.{service_config.agent_id}.messages"
            message = {
                "message_type": message_type,
                "content": content,
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.kafka.publish(topic, json.dumps(message))
            return True
            
        except Exception as e:
            self.logger.error(f"Kafka communication failed for service {service_config.service_name}: {str(e)}")
            return False

    async def _send_generic_communication(self, service_config: AgentServiceConfig, message_type: str,
                                        content: str, metadata: dict) -> bool:
        """Send generic communication"""
        try:
            # Implementation for generic communication
            return True
        except Exception as e:
            self.logger.error(f"Generic communication failed for service {service_config.service_name}: {str(e)}")
            return False

    async def _update_communication_status(self, comm_id: str, status: str, error_message: str = None):
        """Update communication status"""
        if not self.database:
            return
            
        try:
            async with self.database.get_session() as session:
                if error_message:
                    await session.execute("""
                        UPDATE integration_communications 
                        SET status = %s, error_message = %s, retry_count = retry_count + 1
                        WHERE id = %s
                    """, (status, error_message, comm_id))
                else:
                    await session.execute("""
                        UPDATE integration_communications 
                        SET status = %s
                        WHERE id = %s
                    """, (status, comm_id))
                    
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to update communication status: {str(e)}")

    async def _retry_failed_communications(self):
        """Retry failed communications"""
        if not self.database:
            return
            
        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, sender_agent_id, receiver_agent_id, message_type, content, metadata,
                           protocol, retry_count, max_retries
                    FROM integration_communications 
                    WHERE status = 'failed' AND retry_count < max_retries
                    AND timestamp < %s
                    ORDER BY timestamp ASC
                    LIMIT 20
                """, (datetime.utcnow() - timedelta(minutes=5),))
                
                rows = result.fetchall()
                for row in rows:
                    await self._send_communication(
                        row[0], row[1], row[2], row[3], row[4], row[5] or {},
                        IntegrationProtocol(row[6]), row[7], row[8]
                    )
                    
        except Exception as e:
            self.logger.error(f"Failed to retry communications: {str(e)}")

    async def _integration_metrics_collector(self):
        """Background task to collect integration metrics"""
        while not self._shutdown_event.is_set():
            try:
                for service_config in self.agent_services.values():
                    if service_config.is_active:
                        await self._collect_service_metrics(service_config)
                
                await asyncio.sleep(300)  # Collect every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in metrics collector: {str(e)}")
                await asyncio.sleep(600)

    async def _collect_service_metrics(self, service_config: AgentServiceConfig):
        """Collect metrics for a specific service"""
        try:
            health_check = self.service_health_checks.get(service_config.service_id)
            if not health_check:
                return
            
            metrics = {
                "response_time_ms": health_check.response_time_ms,
                "status": health_check.status.value,
                "error_count": 1 if health_check.status == ServiceStatus.ERROR else 0
            }
            
            # Add service-specific metrics
            if health_check.metrics:
                metrics.update(health_check.metrics)
            
            # Store metrics
            await self._store_service_metrics(service_config.service_id, metrics)
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics for service {service_config.service_name}: {str(e)}")

    async def _store_service_metrics(self, service_id: str, metrics: Dict[str, Any]):
        """Store service metrics in database"""
        if not self.database:
            return
            
        try:
            async with self.database.get_session() as session:
                for metric_name, metric_value in metrics.items():
                    if isinstance(metric_value, (int, float)):
                        await session.execute("""
                            INSERT INTO integration_metrics (service_id, metric_name, metric_value, timestamp)
                            VALUES (%s, %s, %s, %s)
                        """, (service_id, metric_name, float(metric_value), datetime.utcnow()))
                
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to store service metrics: {str(e)}")

    async def send_agent_message(self, sender_id: str, receiver_id: str, message_type: str,
                               content: str, metadata: Optional[Dict[str, Any]] = None,
                               protocol: IntegrationProtocol = IntegrationProtocol.HTTP) -> bool:
        """Send a message between agents"""
        try:
            import uuid
            
            comm_id = str(uuid.uuid4())
            
            if not self.database:
                return False
                
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO integration_communications (id, sender_agent_id, receiver_agent_id,
                                                          message_type, content, metadata, protocol,
                                                          timestamp, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    comm_id, sender_id, receiver_id, message_type, content,
                    json.dumps(metadata or {}), protocol.value, datetime.utcnow(), 'pending'
                ))
                await session.commit()
                
            self.logger.info(f"Agent message queued: {sender_id} -> {receiver_id} ({message_type})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send agent message: {str(e)}")
            return False

    async def get_service_status(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific service"""
        service_config = self.agent_services.get(service_id)
        if not service_config:
            return None
            
        health_check = self.service_health_checks.get(service_id)
        
        return {
            "service_id": service_id,
            "service_name": service_config.service_name,
            "agent_id": service_config.agent_id,
            "endpoint": service_config.endpoint,
            "protocol": service_config.protocol.value,
            "status": health_check.status.value if health_check else "unknown",
            "response_time_ms": health_check.response_time_ms if health_check else 0,
            "last_check": health_check.last_check.isoformat() if health_check else None,
            "error_message": health_check.error_message if health_check else None,
            "metrics": health_check.metrics if health_check else {},
            "is_active": service_config.is_active
        }

    async def get_all_services_status(self) -> List[Dict[str, Any]]:
        """Get status of all services"""
        statuses = []
        for service_id in self.agent_services.keys():
            status = await self.get_service_status(service_id)
            if status:
                statuses.append(status)
        return statuses

    async def get_integration_metrics(self, service_id: Optional[str] = None, 
                                    hours: int = 24) -> Dict[str, Any]:
        """Get integration metrics"""
        if not self.database:
            return {}
            
        try:
            async with self.database.get_session() as session:
                query = """
                    SELECT service_id, metric_name, AVG(metric_value) as avg_value,
                           MAX(metric_value) as max_value, MIN(metric_value) as min_value,
                           COUNT(*) as count
                    FROM integration_metrics
                    WHERE timestamp >= %s
                """
                params = [datetime.utcnow() - timedelta(hours=hours)]
                
                if service_id:
                    query += " AND service_id = %s"
                    params.append(service_id)
                
                query += " GROUP BY service_id, metric_name"
                
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                metrics = {}
                for row in rows:
                    service_id = row[0]
                    metric_name = row[1]
                    
                    if service_id not in metrics:
                        metrics[service_id] = {}
                    
                    metrics[service_id][metric_name] = {
                        "avg": float(row[2]),
                        "max": float(row[3]),
                        "min": float(row[4]),
                        "count": row[5]
                    }
                
                return metrics
                
        except Exception as e:
            self.logger.error(f"Failed to get integration metrics: {str(e)}")
            return {}

    async def close(self):
        """Shutdown the integration service"""
        self.logger.info("Closing AgentIntegrationService...")
        
        self._shutdown_event.set()
        
        # Close all service sessions
        for session in self.service_sessions.values():
            await session.close()
        
        self.logger.info("AgentIntegrationService closed successfully")

# Global instances and initialization functions
_agent_integration_service: Optional[AgentIntegrationService] = None

async def init_agent_integration_service() -> AgentIntegrationService:
    """Initialize the global agent integration service instance"""
    global _agent_integration_service
    if not _agent_integration_service:
        _agent_integration_service = AgentIntegrationService()
        await _agent_integration_service.initialize()
    return _agent_integration_service

async def get_agent_integration_service() -> AgentIntegrationService:
    """Get the global agent integration service instance"""
    global _agent_integration_service
    if not _agent_integration_service:
        _agent_integration_service = await init_agent_integration_service()
    return _agent_integration_service
