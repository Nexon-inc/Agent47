import asyncio
import subprocess
import psutil
import socket
import platform
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import os
import time
from sqlalchemy import text

from backend.core.database import get_database, DatabaseManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class ServerStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"

class ServerType(Enum):
    WEB = "web"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    STORAGE = "storage"
    LOAD_BALANCER = "load_balancer"

@dataclass
class ServerInfo:
    server_id: str
    hostname: str
    ip_address: str
    server_type: ServerType
    status: ServerStatus
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    uptime_seconds: int
    last_check: datetime
    services: List[str]

class ServerManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.servers = {}
        self.monitoring_active = False
        self.health_check_interval = 60
        self.server_configs = {}

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing ServerManager...")
            self.database = get_database()
            await self._setup_server_tables()
            await self._load_server_configs()
            await self._discover_servers()
            self.logger.info("ServerManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize ServerManager: {str(e)}")
            return False

    async def _setup_server_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS servers (
                    id SERIAL PRIMARY KEY,
                    server_id VARCHAR(255) UNIQUE NOT NULL,
                    hostname VARCHAR(255) NOT NULL,
                    ip_address INET NOT NULL,
                    server_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) DEFAULT 'offline',
                    cpu_usage FLOAT DEFAULT 0,
                    memory_usage FLOAT DEFAULT 0,
                    disk_usage FLOAT DEFAULT 0,
                    uptime_seconds INTEGER DEFAULT 0,
                    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    services JSONB,
                    config JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS server_health_checks (
                    id SERIAL PRIMARY KEY,
                    server_id VARCHAR(255) NOT NULL,
                    check_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    response_time_ms INTEGER,
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS server_alerts (
                    id SERIAL PRIMARY KEY,
                    server_id VARCHAR(255) NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    metric_value FLOAT,
                    threshold_value FLOAT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_servers_status 
                ON servers(status)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_server_health_checks_timestamp 
                ON server_health_checks(timestamp)
            """))
            
            await session.commit()

    async def _load_server_configs(self):
        self.server_configs = {
            "web_servers": [
                {"hostname": "web-01", "ip": "192.168.1.10", "type": ServerType.WEB},
                {"hostname": "web-02", "ip": "192.168.1.11", "type": ServerType.WEB}
            ],
            "database_servers": [
                {"hostname": "db-01", "ip": "192.168.1.20", "type": ServerType.DATABASE}
            ],
            "cache_servers": [
                {"hostname": "cache-01", "ip": "192.168.1.30", "type": ServerType.CACHE}
            ],
            "queue_servers": [
                {"hostname": "queue-01", "ip": "192.168.1.40", "type": ServerType.QUEUE}
            ]
        }

    async def _discover_servers(self):
        for server_type, servers in self.server_configs.items():
            for server_config in servers:
                server_id = f"{server_config['hostname']}_{server_config['ip'].replace('.', '_')}"
                
                server_info = ServerInfo(
                    server_id=server_id,
                    hostname=server_config['hostname'],
                    ip_address=server_config['ip'],
                    server_type=server_config['type'],
                    status=ServerStatus.OFFLINE,
                    cpu_usage=0.0,
                    memory_usage=0.0,
                    disk_usage=0.0,
                    uptime_seconds=0,
                    last_check=datetime.utcnow(),
                    services=[]
                )
                
                self.servers[server_id] = server_info
                await self._save_server_info(server_info)

    async def _save_server_info(self, server_info: ServerInfo):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO servers (
                        server_id, hostname, ip_address, server_type, status, cpu_usage,
                        memory_usage, disk_usage, uptime_seconds, last_check, services
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (server_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        cpu_usage = EXCLUDED.cpu_usage,
                        memory_usage = EXCLUDED.memory_usage,
                        disk_usage = EXCLUDED.disk_usage,
                        uptime_seconds = EXCLUDED.uptime_seconds,
                        last_check = EXCLUDED.last_check,
                        services = EXCLUDED.services,
                        updated_at = CURRENT_TIMESTAMP
                """), (
                    server_info.server_id,
                    server_info.hostname,
                    server_info.ip_address,
                    server_info.server_type.value,
                    server_info.status.value,
                    server_info.cpu_usage,
                    server_info.memory_usage,
                    server_info.disk_usage,
                    server_info.uptime_seconds,
                    server_info.last_check,
                    server_info.services
                ))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to save server info: {str(e)}")

    async def start_monitoring(self):
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        self.monitoring_active = False

    async def _monitoring_loop(self):
        while self.monitoring_active:
            try:
                for server_id, server_info in self.servers.items():
                    await self._check_server_health(server_info)
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Server monitoring loop error: {str(e)}")
                await asyncio.sleep(self.health_check_interval)

    async def _check_server_health(self, server_info: ServerInfo):
        try:
            start_time = datetime.utcnow()
            
            if await self._ping_server(server_info.ip_address):
                server_info.status = ServerStatus.ONLINE
                await self._collect_server_metrics(server_info)
            else:
                server_info.status = ServerStatus.OFFLINE
            
            server_info.last_check = datetime.utcnow()
            await self._save_server_info(server_info)
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self._log_health_check(server_info.server_id, "ping", 
                                       server_info.status.value, response_time)
            
            await self._check_alerts(server_info)
            
        except Exception as e:
            self.logger.error(f"Failed to check server health for {server_info.server_id}: {str(e)}")
            server_info.status = ServerStatus.DEGRADED
            await self._save_server_info(server_info)

    async def _ping_server(self, ip_address: str) -> bool:
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "5", ip_address],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Ping failed for {ip_address}: {str(e)}")
            return False

    async def _collect_server_metrics(self, server_info: ServerInfo):
        try:
            if server_info.ip_address == "127.0.0.1" or server_info.ip_address == "localhost":
                await self._collect_local_metrics(server_info)
            else:
                await self._collect_remote_metrics(server_info)
        except Exception as e:
            self.logger.error(f"Failed to collect metrics for {server_info.server_id}: {str(e)}")

    async def _collect_local_metrics(self, server_info: ServerInfo):
        try:
            server_info.cpu_usage = psutil.cpu_percent(interval=1)
            server_info.memory_usage = psutil.virtual_memory().percent
            server_info.disk_usage = psutil.disk_usage('/').percent
            server_info.uptime_seconds = int(time.time() - psutil.boot_time())
            server_info.services = await self._get_running_services()
        except Exception as e:
            self.logger.error(f"Failed to collect local metrics: {str(e)}")

    async def _collect_remote_metrics(self, server_info: ServerInfo):
        try:
            ssh_command = f"ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@{server_info.ip_address}"
            
            cpu_cmd = f"{ssh_command} 'top -bn1 | grep Cpu | awk \"{{print \\$2}}\" | cut -d'%' -f1'"
            memory_cmd = f"{ssh_command} 'free | grep Mem | awk \"{{printf \\\"%.1f\\\", \\$3/\\$2 * 100.0}}\"'"
            disk_cmd = f"{ssh_command} 'df / | tail -1 | awk \"{{print \\$5}}\" | cut -d'%' -f1'"
            uptime_cmd = f"{ssh_command} 'uptime -s | xargs -I {{}} date -d {{}} +%s'"
            
            server_info.cpu_usage = float(subprocess.check_output(cpu_cmd, shell=True).decode().strip())
            server_info.memory_usage = float(subprocess.check_output(memory_cmd, shell=True).decode().strip())
            server_info.disk_usage = float(subprocess.check_output(disk_cmd, shell=True).decode().strip())
            
            uptime_start = int(subprocess.check_output(uptime_cmd, shell=True).decode().strip())
            server_info.uptime_seconds = int(time.time() - uptime_start)
            
        except Exception as e:
            self.logger.error(f"Failed to collect remote metrics: {str(e)}")

    async def _get_running_services(self) -> List[str]:
        try:
            services = []
            service_commands = [
                "systemctl list-units --type=service --state=running",
                "ps aux | grep -E '(nginx|apache|postgres|redis|kafka)' | grep -v grep"
            ]
            
            for cmd in service_commands:
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        services.extend(result.stdout.split('\n')[:10])
                except Exception:
                    continue
            
            return [s.strip() for s in services if s.strip()]
        except Exception as e:
            self.logger.error(f"Failed to get running services: {str(e)}")
            return []

    async def _log_health_check(self, server_id: str, check_type: str, status: str, response_time: float):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO server_health_checks (server_id, check_type, status, response_time_ms)
                    VALUES (%s, %s, %s, %s)
                """), (server_id, check_type, status, response_time))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to log health check: {str(e)}")

    async def _check_alerts(self, server_info: ServerInfo):
        alerts = []
        
        if server_info.cpu_usage > 90:
            alerts.append(("HIGH_CPU", "critical", f"High CPU usage: {server_info.cpu_usage:.1f}%"))
        
        if server_info.memory_usage > 90:
            alerts.append(("HIGH_MEMORY", "critical", f"High memory usage: {server_info.memory_usage:.1f}%"))
        
        if server_info.disk_usage > 90:
            alerts.append(("HIGH_DISK", "critical", f"High disk usage: {server_info.disk_usage:.1f}%"))
        
        if server_info.status == ServerStatus.DEGRADED:
            alerts.append(("DEGRADED_STATUS", "warning", "Server is in degraded state"))
        
        for alert_type, severity, message in alerts:
            await self._create_server_alert(server_info.server_id, alert_type, severity, message)

    async def _create_server_alert(self, server_id: str, alert_type: str, severity: str, message: str):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO server_alerts (server_id, alert_type, severity, message)
                    VALUES (%s, %s, %s, %s)
                """), (server_id, alert_type, severity, message))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to create server alert: {str(e)}")

    async def get_server_status(self) -> Dict[str, Any]:
        try:
            total_servers = len(self.servers)
            online_servers = sum(1 for s in self.servers.values() if s.status == ServerStatus.ONLINE)
            offline_servers = sum(1 for s in self.servers.values() if s.status == ServerStatus.OFFLINE)
            degraded_servers = sum(1 for s in self.servers.values() if s.status == ServerStatus.DEGRADED)
            
            return {
                "total_servers": total_servers,
                "online_servers": online_servers,
                "offline_servers": offline_servers,
                "degraded_servers": degraded_servers,
                "uptime_percentage": (online_servers / total_servers * 100) if total_servers > 0 else 0,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to get server status: {str(e)}")
            return {}

    async def get_server_details(self, server_id: str) -> Dict[str, Any]:
        if server_id not in self.servers:
            return {"error": "Server not found"}
        
        server_info = self.servers[server_id]
        return {
            "server_id": server_info.server_id,
            "hostname": server_info.hostname,
            "ip_address": server_info.ip_address,
            "server_type": server_info.server_type.value,
            "status": server_info.status.value,
            "cpu_usage": server_info.cpu_usage,
            "memory_usage": server_info.memory_usage,
            "disk_usage": server_info.disk_usage,
            "uptime_seconds": server_info.uptime_seconds,
            "last_check": server_info.last_check.isoformat(),
            "services": server_info.services
        }

    async def list_servers(self) -> List[Dict[str, Any]]:
        servers = []
        for server_info in self.servers.values():
            servers.append({
                "server_id": server_info.server_id,
                "hostname": server_info.hostname,
                "ip_address": server_info.ip_address,
                "server_type": server_info.server_type.value,
                "status": server_info.status.value,
                "cpu_usage": server_info.cpu_usage,
                "memory_usage": server_info.memory_usage,
                "disk_usage": server_info.disk_usage,
                "last_check": server_info.last_check.isoformat()
            })
        return servers

    async def get_server_alerts(self, server_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                query = """
                    SELECT id, server_id, alert_type, severity, message, metric_value, 
                           threshold_value, timestamp, resolved, resolved_at
                    FROM server_alerts 
                """
                params = []
                
                if server_id:
                    query += " WHERE server_id = %s"
                    params.append(server_id)
                
                query += " ORDER BY timestamp DESC LIMIT %s"
                params.append(limit)
                
                result = await session.execute(text(query), params)
                
                alerts = []
                for row in result.fetchall():
                    alerts.append({
                        "id": row[0],
                        "server_id": row[1],
                        "alert_type": row[2],
                        "severity": row[3],
                        "message": row[4],
                        "metric_value": row[5],
                        "threshold_value": row[6],
                        "timestamp": row[7].isoformat(),
                        "resolved": row[8],
                        "resolved_at": row[9].isoformat() if row[9] else None
                    })
                
                return alerts
        except Exception as e:
            self.logger.error(f"Failed to get server alerts: {str(e)}")
            return []

    async def resolve_server_alert(self, alert_id: int) -> bool:
        if not self.database:
            return False
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    UPDATE server_alerts 
                    SET resolved = TRUE, resolved_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """), (alert_id,))
                await session.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to resolve server alert: {str(e)}")
            return False

    async def add_server(self, hostname: str, ip_address: str, server_type: ServerType) -> Dict[str, Any]:
        server_id = f"{hostname}_{ip_address.replace('.', '_')}"
        
        if server_id in self.servers:
            return {"error": "Server already exists"}
        
        server_info = ServerInfo(
            server_id=server_id,
            hostname=hostname,
            ip_address=ip_address,
            server_type=server_type,
            status=ServerStatus.OFFLINE,
            cpu_usage=0.0,
            memory_usage=0.0,
            disk_usage=0.0,
            uptime_seconds=0,
            last_check=datetime.utcnow(),
            services=[]
        )
        
        self.servers[server_id] = server_info
        await self._save_server_info(server_info)
        
        return {
            "success": True,
            "server_id": server_id,
            "message": "Server added successfully"
        }

    async def remove_server(self, server_id: str) -> bool:
        if server_id not in self.servers:
            return False
        
        try:
            del self.servers[server_id]
            
            if self.database:
                async with self.database.get_session() as session:
                    await session.execute(text("DELETE FROM servers WHERE server_id = %s"), (server_id,))
                    await session.commit()
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove server: {str(e)}")
            return False

    async def shutdown(self):
        self.logger.info("Shutting down ServerManager...")
        await self.stop_monitoring()
        self.logger.info("ServerManager shutdown complete")
