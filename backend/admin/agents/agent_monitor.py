import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from backend.core.database import get_database
from backend.core.cache import get_redis
from backend.core.logs import get_logger
from backend.core.config import get_settings
from backend.core.event_bus import get_kafka
from sqlalchemy import text


class AgentStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    IDLE = "idle"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    STARTING = "starting"
    STOPPING = "stopping"


class MonitorEvent(Enum):
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"
    AGENT_BUSY = "agent_busy"
    AGENT_IDLE = "agent_idle"
    AGENT_HEARTBEAT = "agent_heartbeat"
    AGENT_TASK_STARTED = "agent_task_started"
    AGENT_TASK_COMPLETED = "agent_task_completed"
    AGENT_TASK_FAILED = "agent_task_failed"
    AGENT_PERFORMANCE_ALERT = "agent_performance_alert"


@dataclass
class AgentHeartbeat:
    agent_id: str
    agent_name: str
    timestamp: datetime
    status: AgentStatus
    cpu_usage: float
    memory_usage: float
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    response_time: float
    error_count: int
    last_error: Optional[str] = None


@dataclass
class AgentTask:
    task_id: str
    agent_id: str
    agent_name: str
    task_type: str
    task_data: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


@dataclass
class AgentPerformance:
    agent_id: str
    agent_name: str
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    response_time: float
    throughput: float
    error_rate: float
    availability: float
    efficiency_score: float


@dataclass
class AgentAlert:
    id: str
    agent_id: str
    agent_name: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


class AgentMonitor:
    def __init__(self):
        self.config = get_settings()
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()
        self.kafka = get_kafka()
        self.monitoring = False
        self.monitoring_task = None
        self.heartbeat_task = None
        self.agent_heartbeats: Dict[str, AgentHeartbeat] = {}
        self.agent_tasks: Dict[str, AgentTask] = {}
        self.agent_alerts: List[AgentAlert] = []
        self.monitoring_interval = 30  # seconds
        self.heartbeat_timeout = 120  # seconds
        self.retention_days = 30
        self.performance_thresholds = {
            "cpu_usage": {"warning": 80.0, "critical": 90.0},
            "memory_usage": {"warning": 85.0, "critical": 95.0},
            "response_time": {"warning": 2000.0, "critical": 5000.0},
            "error_rate": {"warning": 10.0, "critical": 20.0}
        }

    async def initialize(self):
        """Initialize the agent monitor and create necessary tables"""
        try:
            await self._setup_agent_monitor_tables()
            await self._start_monitoring()
            await self._start_heartbeat_monitoring()
            self.logger.info("AgentMonitor initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize AgentMonitor: {e}")
            raise

    async def _setup_agent_monitor_tables(self):
        """Create agent monitoring tables"""
        async with self.db.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS agent_heartbeats (
                    id SERIAL PRIMARY KEY,
                    agent_id VARCHAR(100) NOT NULL,
                    agent_name VARCHAR(100) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    cpu_usage DOUBLE PRECISION NOT NULL,
                    memory_usage DOUBLE PRECISION NOT NULL,
                    active_tasks INTEGER NOT NULL,
                    completed_tasks INTEGER NOT NULL,
                    failed_tasks INTEGER NOT NULL,
                    response_time DOUBLE PRECISION NOT NULL,
                    error_count INTEGER NOT NULL,
                    last_error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS agent_tasks (
                    id VARCHAR(100) PRIMARY KEY,
                    agent_id VARCHAR(100) NOT NULL,
                    agent_name VARCHAR(100) NOT NULL,
                    task_type VARCHAR(100) NOT NULL,
                    task_data JSONB NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    status VARCHAR(20) NOT NULL,
                    result JSONB,
                    error TEXT,
                    execution_time DOUBLE PRECISION,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS agent_performance (
                    id SERIAL PRIMARY KEY,
                    agent_id VARCHAR(100) NOT NULL,
                    agent_name VARCHAR(100) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    cpu_usage DOUBLE PRECISION NOT NULL,
                    memory_usage DOUBLE PRECISION NOT NULL,
                    response_time DOUBLE PRECISION NOT NULL,
                    throughput DOUBLE PRECISION NOT NULL,
                    error_rate DOUBLE PRECISION NOT NULL,
                    availability DOUBLE PRECISION NOT NULL,
                    efficiency_score DOUBLE PRECISION NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS agent_alerts (
                    id VARCHAR(100) PRIMARY KEY,
                    agent_id VARCHAR(100) NOT NULL,
                    agent_name VARCHAR(100) NOT NULL,
                    alert_type VARCHAR(100) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP,
                    resolved_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.commit()

    async def _start_monitoring(self):
        """Start the agent monitoring loop"""
        if not self.monitoring:
            self.monitoring = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.logger.info("Agent monitoring started")

    async def _start_heartbeat_monitoring(self):
        """Start the heartbeat monitoring loop"""
        self.heartbeat_task = asyncio.create_task(self._heartbeat_monitoring_loop())
        self.logger.info("Agent heartbeat monitoring started")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                await self._check_agent_health()
                await self._update_agent_performance()
                await self._cleanup_old_data()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"Error in agent monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def _heartbeat_monitoring_loop(self):
        """Monitor agent heartbeats and detect offline agents"""
        while self.monitoring:
            try:
                await self._check_agent_heartbeats()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in heartbeat monitoring loop: {e}")
                await asyncio.sleep(10)

    async def _check_agent_health(self):
        """Check the health of all monitored agents"""
        try:
            current_time = datetime.utcnow()
            
            for agent_id, heartbeat in self.agent_heartbeats.items():
                # Check if agent is responding
                if (current_time - heartbeat.timestamp).total_seconds() > self.heartbeat_timeout:
                    await self._mark_agent_offline(agent_id, "Heartbeat timeout")
                
                # Check performance thresholds
                await self._check_agent_performance(heartbeat)
                
        except Exception as e:
            self.logger.error(f"Error checking agent health: {e}")

    async def _check_agent_performance(self, heartbeat: AgentHeartbeat):
        """Check if agent performance is within acceptable thresholds"""
        try:
            alerts_created = []
            
            # Check CPU usage
            if heartbeat.cpu_usage >= self.performance_thresholds["cpu_usage"]["critical"]:
                await self._create_agent_alert(
                    heartbeat.agent_id, heartbeat.agent_name,
                    "high_cpu_usage", "critical",
                    f"CPU usage is {heartbeat.cpu_usage:.2f}%"
                )
                alerts_created.append("cpu_critical")
            elif heartbeat.cpu_usage >= self.performance_thresholds["cpu_usage"]["warning"]:
                await self._create_agent_alert(
                    heartbeat.agent_id, heartbeat.agent_name,
                    "high_cpu_usage", "warning",
                    f"CPU usage is {heartbeat.cpu_usage:.2f}%"
                )
                alerts_created.append("cpu_warning")
            
            # Check memory usage
            if heartbeat.memory_usage >= self.performance_thresholds["memory_usage"]["critical"]:
                await self._create_agent_alert(
                    heartbeat.agent_id, heartbeat.agent_name,
                    "high_memory_usage", "critical",
                    f"Memory usage is {heartbeat.memory_usage:.2f}%"
                )
                alerts_created.append("memory_critical")
            elif heartbeat.memory_usage >= self.performance_thresholds["memory_usage"]["warning"]:
                await self._create_agent_alert(
                    heartbeat.agent_id, heartbeat.agent_name,
                    "high_memory_usage", "warning",
                    f"Memory usage is {heartbeat.memory_usage:.2f}%"
                )
                alerts_created.append("memory_warning")
            
            # Check response time
            if heartbeat.response_time >= self.performance_thresholds["response_time"]["critical"]:
                await self._create_agent_alert(
                    heartbeat.agent_id, heartbeat.agent_name,
                    "high_response_time", "critical",
                    f"Response time is {heartbeat.response_time:.2f}ms"
                )
                alerts_created.append("response_critical")
            elif heartbeat.response_time >= self.performance_thresholds["response_time"]["warning"]:
                await self._create_agent_alert(
                    heartbeat.agent_id, heartbeat.agent_name,
                    "high_response_time", "warning",
                    f"Response time is {heartbeat.response_time:.2f}ms"
                )
                alerts_created.append("response_warning")
            
            # Check error rate
            if heartbeat.error_count > 0:
                error_rate = (heartbeat.failed_tasks / max(heartbeat.completed_tasks + heartbeat.failed_tasks, 1)) * 100
                if error_rate >= self.performance_thresholds["error_rate"]["critical"]:
                    await self._create_agent_alert(
                        heartbeat.agent_id, heartbeat.agent_name,
                        "high_error_rate", "critical",
                        f"Error rate is {error_rate:.2f}%"
                    )
                    alerts_created.append("error_critical")
                elif error_rate >= self.performance_thresholds["error_rate"]["warning"]:
                    await self._create_agent_alert(
                        heartbeat.agent_id, heartbeat.agent_name,
                        "high_error_rate", "warning",
                        f"Error rate is {error_rate:.2f}%"
                    )
                    alerts_created.append("error_warning")
            
        except Exception as e:
            self.logger.error(f"Error checking agent performance: {e}")

    async def _check_agent_heartbeats(self):
        """Check for stale heartbeats and mark agents as offline"""
        try:
            current_time = datetime.utcnow()
            offline_agents = []
            
            for agent_id, heartbeat in self.agent_heartbeats.items():
                if (current_time - heartbeat.timestamp).total_seconds() > self.heartbeat_timeout:
                    offline_agents.append(agent_id)
            
            for agent_id in offline_agents:
                await self._mark_agent_offline(agent_id, "No heartbeat received")
                
        except Exception as e:
            self.logger.error(f"Error checking agent heartbeats: {e}")

    async def _mark_agent_offline(self, agent_id: str, reason: str):
        """Mark an agent as offline"""
        try:
            if agent_id in self.agent_heartbeats:
                heartbeat = self.agent_heartbeats[agent_id]
                heartbeat.status = AgentStatus.OFFLINE
                
                # Update in database
                async with self.db.get_session() as session:
                    await session.execute("""
                        UPDATE agent_heartbeats 
                        SET status = :status, last_error = :last_error
                        WHERE agent_id = :agent_id
                    """, {
                        "status": AgentStatus.OFFLINE.value,
                        "last_error": reason,
                        "agent_id": agent_id
                    })
                    await session.commit()
                
                # Create offline alert
                await self._create_agent_alert(
                    agent_id, heartbeat.agent_name,
                    "agent_offline", "critical",
                    f"Agent went offline: {reason}"
                )
                
                self.logger.warning(f"Agent {heartbeat.agent_name} ({agent_id}) marked as offline: {reason}")
                
        except Exception as e:
            self.logger.error(f"Error marking agent {agent_id} as offline: {e}")

    async def _create_agent_alert(self, agent_id: str, agent_name: str, 
                                 alert_type: str, severity: str, message: str):
        """Create an agent alert"""
        try:
            # Check if alert already exists
            existing_alert = next(
                (alert for alert in self.agent_alerts 
                 if alert.agent_id == agent_id and alert.alert_type == alert_type and not alert.resolved), None
            )
            
            if existing_alert:
                return  # Alert already exists
            
            alert_id = f"agent_{alert_type}_{agent_id}_{int(time.time())}"
            
            alert = AgentAlert(
                id=alert_id,
                agent_id=agent_id,
                agent_name=agent_name,
                alert_type=alert_type,
                severity=severity,
                message=message,
                timestamp=datetime.utcnow()
            )
            
            # Save to database
            async with self.db.get_session() as session:
                await session.execute("""
                    INSERT INTO agent_alerts (
                        id, agent_id, agent_name, alert_type, severity, message, timestamp
                    ) VALUES (
                        :id, :agent_id, :agent_name, :alert_type, :severity, :message, :timestamp
                    )
                """, {
                    "id": alert.id,
                    "agent_id": alert.agent_id,
                    "agent_name": alert.agent_name,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp
                })
                await session.commit()
            
            # Add to active alerts
            self.agent_alerts.append(alert)
            
            # Log alert
            self.logger.warning(f"Agent alert: {message} (Agent: {agent_name}, Level: {severity})")
            
            # Send notification
            await self._send_agent_alert_notification(alert)
            
            # Broadcast agent alert via WebSocket (to admins)
            try:
                from backend.core.realtime.websocket_router import broadcast_alert
                await broadcast_alert({
                    "id": alert.id,
                    "source": "agent",
                    "severity": severity,
                    "title": f"Agent Alert: {agent_name}",
                    "message": message,
                    "status": "active",
                    "created_at": alert.timestamp.isoformat() if alert.timestamp else datetime.utcnow().isoformat(),
                    "metadata": {
                        "alert_id": alert.id,
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                        "alert_type": alert_type
                    }
                })
            except Exception as e:
                self.logger.warning(f"Failed to broadcast agent alert: {e}")
            
            # Publish event to Kafka
            await self._publish_monitor_event(MonitorEvent.AGENT_PERFORMANCE_ALERT, {
                "alert_id": alert.id,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "alert_type": alert_type,
                "severity": severity,
                "message": message
            })
            
        except Exception as e:
            self.logger.error(f"Error creating agent alert: {e}")

    async def _send_agent_alert_notification(self, alert: AgentAlert):
        """Send agent alert notification"""
        try:
            notification_data = {
                "type": "agent_alert",
                "alert_id": alert.id,
                "agent_id": alert.agent_id,
                "agent_name": alert.agent_name,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat()
            }
            
            # Store in Redis for notification service
            await self.redis.set(
                f"notifications:agent:{alert.id}",
                notification_data,
                expire=3600
            )
            
        except Exception as e:
            self.logger.warning(f"Could not send agent alert notification: {e}")

    async def _publish_monitor_event(self, event_type: MonitorEvent, data: Dict[str, Any]):
        """Publish monitoring event to Kafka"""
        try:
            event_data = {
                "event_type": event_type.value,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            await self.kafka.publish_event("agent_monitoring", event_data)
            
        except Exception as e:
            self.logger.warning(f"Could not publish monitor event: {e}")

    async def _update_agent_performance(self):
        """Update agent performance metrics"""
        try:
            current_time = datetime.utcnow()
            
            for agent_id, heartbeat in self.agent_heartbeats.items():
                if heartbeat.status == AgentStatus.ONLINE:
                    # Calculate performance metrics
                    availability = await self._calculate_availability(agent_id)
                    efficiency_score = self._calculate_efficiency_score(heartbeat)
                    
                    performance = AgentPerformance(
                        agent_id=agent_id,
                        agent_name=heartbeat.agent_name,
                        timestamp=current_time,
                        cpu_usage=heartbeat.cpu_usage,
                        memory_usage=heartbeat.memory_usage,
                        response_time=heartbeat.response_time,
                        throughput=heartbeat.completed_tasks / max((current_time - heartbeat.timestamp).total_seconds() / 3600, 1),
                        error_rate=(heartbeat.failed_tasks / max(heartbeat.completed_tasks + heartbeat.failed_tasks, 1)) * 100,
                        availability=availability,
                        efficiency_score=efficiency_score
                    )
                    
                    # Save to database
                    await self._save_agent_performance(performance)
                    
        except Exception as e:
            self.logger.error(f"Error updating agent performance: {e}")

    async def _calculate_availability(self, agent_id: str) -> float:
        """Calculate agent availability percentage based on uptime vs downtime"""
        try:
            if not self.database:
                return 0.0
            
            # Calculate availability over the last 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            async with self.database.get_session() as session:
                # Get all heartbeats for this agent in the last 24 hours
                result = await session.execute(
                    text("""
                        SELECT status, timestamp 
                        FROM agent_heartbeats 
                        WHERE agent_id = :agent_id 
                        AND timestamp >= :cutoff_time
                        ORDER BY timestamp ASC
                    """),
                    {"agent_id": agent_id, "cutoff_time": cutoff_time}
                )
                heartbeats = result.fetchall()
                
                if not heartbeats:
                    # If no heartbeats, check current status
                    if agent_id in self.agent_heartbeats:
                        current_status = self.agent_heartbeats[agent_id].status
                        return 100.0 if current_status == AgentStatus.ONLINE else 0.0
                    return 0.0
                
                # Calculate total time and online time
                total_time = timedelta(hours=24).total_seconds()
                online_time = 0.0
                last_timestamp = cutoff_time
                
                for heartbeat in heartbeats:
                    status = heartbeat.status
                    timestamp = heartbeat.timestamp
                    
                    # Calculate time since last heartbeat
                    time_diff = (timestamp - last_timestamp).total_seconds()
                    
                    # If agent was online during this period, add to online_time
                    if status == AgentStatus.ONLINE.value or status == AgentStatus.BUSY.value:
                        online_time += time_diff
                    
                    last_timestamp = timestamp
                
                # Check current status for remaining time
                if agent_id in self.agent_heartbeats:
                    current_status = self.agent_heartbeats[agent_id].status
                    remaining_time = (datetime.utcnow() - last_timestamp).total_seconds()
                    if current_status == AgentStatus.ONLINE or current_status == AgentStatus.BUSY:
                        online_time += remaining_time
                
                # Calculate availability percentage
                availability = (online_time / total_time) * 100 if total_time > 0 else 0.0
                return min(100.0, max(0.0, availability))
                
        except Exception as e:
            self.logger.warning(f"Could not calculate availability for agent {agent_id}: {e}")
            # Fallback: check current status
            if agent_id in self.agent_heartbeats:
                current_status = self.agent_heartbeats[agent_id].status
                return 100.0 if current_status == AgentStatus.ONLINE else 0.0
            return 0.0

    def _calculate_efficiency_score(self, heartbeat: AgentHeartbeat) -> float:
        """Calculate agent efficiency score"""
        try:
            # Calculate efficiency based on multiple factors
            cpu_score = max(0, 100 - heartbeat.cpu_usage)
            memory_score = max(0, 100 - heartbeat.memory_usage)
            response_score = max(0, 100 - (heartbeat.response_time / 100))
            error_score = max(0, 100 - (heartbeat.error_count * 10))
            
            # Weighted average
            efficiency = (cpu_score * 0.3 + memory_score * 0.3 + 
                        response_score * 0.2 + error_score * 0.2)
            
            return min(100.0, max(0.0, efficiency))
            
        except Exception as e:
            self.logger.warning(f"Could not calculate efficiency score: {e}")
            return 0.0

    async def _save_agent_performance(self, performance: AgentPerformance):
        """Save agent performance to database"""
        try:
            async with self.db.get_session() as session:
                await session.execute("""
                    INSERT INTO agent_performance (
                        agent_id, agent_name, timestamp, cpu_usage, memory_usage,
                        response_time, throughput, error_rate, availability, efficiency_score
                    ) VALUES (
                        :agent_id, :agent_name, :timestamp, :cpu_usage, :memory_usage,
                        :response_time, :throughput, :error_rate, :availability, :efficiency_score
                    )
                """, {
                    "agent_id": performance.agent_id,
                    "agent_name": performance.agent_name,
                    "timestamp": performance.timestamp,
                    "cpu_usage": performance.cpu_usage,
                    "memory_usage": performance.memory_usage,
                    "response_time": performance.response_time,
                    "throughput": performance.throughput,
                    "error_rate": performance.error_rate,
                    "availability": performance.availability,
                    "efficiency_score": performance.efficiency_score
                })
                await session.commit()
        except Exception as e:
            self.logger.error(f"Error saving agent performance: {e}")

    async def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            
            async with self.db.get_session() as session:
                # Clean up old heartbeats
                await session.execute(
                    "DELETE FROM agent_heartbeats WHERE timestamp < :cutoff_date",
                    {"cutoff_date": cutoff_date}
                )
                
                # Clean up old performance data
                await session.execute(
                    "DELETE FROM agent_performance WHERE timestamp < :cutoff_date",
                    {"cutoff_date": cutoff_date}
                )
                
                # Clean up old tasks
                await session.execute(
                    "DELETE FROM agent_tasks WHERE started_at < :cutoff_date",
                    {"cutoff_date": cutoff_date}
                )
                
                # Clean up resolved alerts older than 7 days
                alert_cutoff = datetime.utcnow() - timedelta(days=7)
                await session.execute("""
                    DELETE FROM agent_alerts 
                    WHERE resolved = TRUE AND resolved_at < :alert_cutoff
                """, {"alert_cutoff": alert_cutoff})
                
                await session.commit()
                
        except Exception as e:
            self.logger.warning(f"Error cleaning up old monitoring data: {e}")

    async def register_agent_heartbeat(self, heartbeat: AgentHeartbeat):
        """Register a heartbeat from an agent"""
        try:
            # Update in memory
            self.agent_heartbeats[heartbeat.agent_id] = heartbeat
            
            # Save to database
            async with self.db.get_session() as session:
                await session.execute("""
                    INSERT INTO agent_heartbeats (
                        agent_id, agent_name, timestamp, status, cpu_usage, memory_usage,
                        active_tasks, completed_tasks, failed_tasks, response_time, error_count, last_error
                    ) VALUES (
                        :agent_id, :agent_name, :timestamp, :status, :cpu_usage, :memory_usage,
                        :active_tasks, :completed_tasks, :failed_tasks, :response_time, :error_count, :last_error
                    )
                """, {
                    "agent_id": heartbeat.agent_id,
                    "agent_name": heartbeat.agent_name,
                    "timestamp": heartbeat.timestamp,
                    "status": heartbeat.status.value,
                    "cpu_usage": heartbeat.cpu_usage,
                    "memory_usage": heartbeat.memory_usage,
                    "active_tasks": heartbeat.active_tasks,
                    "completed_tasks": heartbeat.completed_tasks,
                    "failed_tasks": heartbeat.failed_tasks,
                    "response_time": heartbeat.response_time,
                    "error_count": heartbeat.error_count,
                    "last_error": heartbeat.last_error
                })
                await session.commit()
            
            # Publish heartbeat event
            await self._publish_monitor_event(MonitorEvent.AGENT_HEARTBEAT, {
                "agent_id": heartbeat.agent_id,
                "agent_name": heartbeat.agent_name,
                "status": heartbeat.status.value,
                "timestamp": heartbeat.timestamp.isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error registering agent heartbeat: {e}")

    async def register_agent_task(self, task: AgentTask):
        """Register a new agent task"""
        try:
            # Store in memory
            self.agent_tasks[task.task_id] = task
            
            # Save to database
            async with self.db.get_session() as session:
                await session.execute("""
                    INSERT INTO agent_tasks (
                        id, agent_id, agent_name, task_type, task_data, started_at, status
                    ) VALUES (
                        :id, :agent_id, :agent_name, :task_type, :task_data, :started_at, :status
                    )
                """, {
                    "id": task.id,
                    "agent_id": task.agent_id,
                    "agent_name": task.agent_name,
                    "task_type": task.task_type,
                    "task_data": task.task_data,
                    "started_at": task.started_at,
                    "status": task.status
                })
                await session.commit()
            
            # Publish task started event
            await self._publish_monitor_event(MonitorEvent.AGENT_TASK_STARTED, {
                "task_id": task.task_id,
                "agent_id": task.agent_id,
                "agent_name": task.agent_name,
                "task_type": task.task_type,
                "started_at": task.started_at.isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error registering agent task: {e}")

    async def update_agent_task(self, task_id: str, status: str, result: Optional[Dict] = None, 
                               error: Optional[str] = None):
        """Update an agent task status"""
        try:
            if task_id in self.agent_tasks:
                task = self.agent_tasks[task_id]
                task.status = status
                task.completed_at = datetime.utcnow() if status in ["completed", "failed"] else None
                task.result = result
                task.error = error
                
                if task.completed_at and task.started_at:
                    task.execution_time = (task.completed_at - task.started_at).total_seconds()
                
                # Update in database
                async with self.db.get_session() as session:
                    await session.execute("""
                        UPDATE agent_tasks 
                        SET status = :status, completed_at = :completed_at, 
                            result = :result, error = :error, execution_time = :execution_time
                        WHERE id = :task_id
                    """, {
                        "status": status,
                        "completed_at": task.completed_at,
                        "result": task.result,
                        "error": task.error,
                        "execution_time": task.execution_time,
                        "task_id": task_id
                    })
                    await session.commit()
                
                # Publish appropriate event
                if status == "completed":
                    await self._publish_monitor_event(MonitorEvent.AGENT_TASK_COMPLETED, {
                        "task_id": task_id,
                        "agent_id": task.agent_id,
                        "agent_name": task.agent_name,
                        "execution_time": task.execution_time
                    })
                elif status == "failed":
                    await self._publish_monitor_event(MonitorEvent.AGENT_TASK_FAILED, {
                        "task_id": task_id,
                        "agent_id": task.agent_id,
                        "agent_name": task.agent_name,
                        "error": error,
                        "execution_time": task.execution_time
                    })
                
        except Exception as e:
            self.logger.error(f"Error updating agent task {task_id}: {e}")

    async def get_agent_status(self, agent_id: str) -> Optional[AgentStatus]:
        """Get current status of an agent"""
        try:
            if agent_id in self.agent_heartbeats:
                return self.agent_heartbeats[agent_id].status
            return None
        except Exception as e:
            self.logger.error(f"Error getting agent status: {e}")
            return None

    async def get_all_agent_statuses(self) -> Dict[str, AgentStatus]:
        """Get status of all monitored agents"""
        try:
            return {agent_id: heartbeat.status for agent_id, heartbeat in self.agent_heartbeats.items()}
        except Exception as e:
            self.logger.error(f"Error getting all agent statuses: {e}")
            return {}

    async def get_agent_performance(self, agent_id: str, hours: int = 24) -> List[AgentPerformance]:
        """Get performance history for a specific agent"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT * FROM agent_performance
                    WHERE agent_id = :agent_id AND timestamp >= :cutoff_time
                    ORDER BY timestamp ASC
                """, {
                    "agent_id": agent_id,
                    "cutoff_time": cutoff_time
                })
                
                rows = result.fetchall()
                return [
                    AgentPerformance(
                        agent_id=row.agent_id,
                        agent_name=row.agent_name,
                        timestamp=row.timestamp,
                        cpu_usage=row.cpu_usage,
                        memory_usage=row.memory_usage,
                        response_time=row.response_time,
                        throughput=row.throughput,
                        error_rate=row.error_rate,
                        availability=row.availability,
                        efficiency_score=row.efficiency_score
                    )
                    for row in rows
                ]
                
        except Exception as e:
            self.logger.error(f"Error getting agent performance: {e}")
            return []

    async def get_active_alerts(self) -> List[AgentAlert]:
        """Get all active agent alerts"""
        try:
            return [alert for alert in self.agent_alerts if not alert.resolved]
        except Exception as e:
            self.logger.error(f"Error getting active alerts: {e}")
            return []

    async def resolve_alert(self, alert_id: str, resolved_by: str):
        """Resolve an agent alert"""
        try:
            async with self.db.get_session() as session:
                await session.execute("""
                    UPDATE agent_alerts
                    SET resolved = TRUE, resolved_at = :resolved_at, resolved_by = :resolved_by
                    WHERE id = :alert_id
                """, {
                    "alert_id": alert_id,
                    "resolved_at": datetime.utcnow(),
                    "resolved_by": resolved_by
                })
                await session.commit()
            
            # Update in memory
            for alert in self.agent_alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.utcnow()
                    alert.resolved_by = resolved_by
                    break
            
            self.logger.info(f"Agent alert {alert_id} resolved by {resolved_by}")
            
        except Exception as e:
            self.logger.error(f"Error resolving alert {alert_id}: {e}")

    async def get_agent_summary(self) -> Dict[str, Any]:
        """Get summary of all agent monitoring data"""
        try:
            summary = {
                "total_agents": len(self.agent_heartbeats),
                "online_agents": len([h for h in self.agent_heartbeats.values() if h.status == AgentStatus.ONLINE]),
                "offline_agents": len([h for h in self.agent_heartbeats.values() if h.status == AgentStatus.OFFLINE]),
                "busy_agents": len([h for h in self.agent_heartbeats.values() if h.status == AgentStatus.BUSY]),
                "error_agents": len([h for h in self.agent_heartbeats.values() if h.status == AgentStatus.ERROR]),
                "total_tasks": len(self.agent_tasks),
                "active_tasks": len([t for t in self.agent_tasks.values() if t.status == "running"]),
                "completed_tasks": len([t for t in self.agent_tasks.values() if t.status == "completed"]),
                "failed_tasks": len([t for t in self.agent_tasks.values() if t.status == "failed"]),
                "active_alerts": len([a for a in self.agent_alerts if not a.resolved])
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting agent summary: {e}")
            return {}

    async def stop_monitoring(self):
        """Stop agent monitoring"""
        self.monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Agent monitoring stopped")

    async def close(self):
        """Clean up resources"""
        await self.stop_monitoring()
        self.logger.info("AgentMonitor closed")


# Singleton instances
_agent_monitor = None


async def get_agent_monitor() -> AgentMonitor:
    """Get the AgentMonitor singleton instance"""
    global _agent_monitor
    if _agent_monitor is None:
        _agent_monitor = AgentMonitor()
        await _agent_monitor.initialize()
    return _agent_monitor


async def init_agent_monitor() -> AgentMonitor:
    """Initialize and return a new AgentMonitor instance"""
    monitor = AgentMonitor()
    await monitor.initialize()
    return monitor
