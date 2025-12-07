import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from ..config import settings

logger = logging.getLogger(__name__)

@dataclass
class GrokMetrics:
    """Grok LLM performance metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    concurrent_requests: int = 0
    last_request_time: Optional[datetime] = None
    health_status: str = "unknown"
    error_count: int = 0
    success_rate: float = 0.0

class GrokHealthMonitor:
    """Production health monitoring for Grok LLM system"""
    
    def __init__(self):
        self.metrics = GrokMetrics()
        self.health_history: List[Dict[str, Any]] = []
        self.alert_history: List[Dict[str, Any]] = []
        self.last_health_check = None
        self.monitoring_active = False
        
        # Prometheus metrics
        self.request_counter = Counter('grok_requests_total', 'Total requests to Grok LLM')
        self.success_counter = Counter('grok_requests_successful', 'Successful requests to Grok LLM')
        self.failure_counter = Counter('grok_requests_failed', 'Failed requests to Grok LLM')
        self.response_time_histogram = Histogram('grok_response_time_seconds', 'Response time in seconds')
        self.concurrent_requests_gauge = Gauge('grok_concurrent_requests', 'Current concurrent requests')
        self.health_status_gauge = Gauge('grok_health_status', 'Current health status (1=healthy, 0=unhealthy)')
        
        # Start Prometheus metrics server
        if settings.monitoring.enable_monitoring:
            try:
                start_http_server(
                    settings.monitoring.prometheus_port,
                    addr=settings.monitoring.prometheus_host
                )
                logger.info(f"Prometheus metrics server started on port {settings.monitoring.prometheus_port}")
            except Exception as e:
                logger.error(f"Failed to start Prometheus server: {e}")
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        logger.info("Starting Grok LLM health monitoring")
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        logger.info("Stopping Grok LLM health monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                await self._perform_health_check()
                await self._check_performance_thresholds()
                await self._update_metrics()
                
                # Wait for next check interval
                await asyncio.sleep(settings.monitoring.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    async def _perform_health_check(self):
        """Perform comprehensive health check"""
        try:
            from ..utils.nlp_utils import get_ollama_client
            
            ollama_client = await get_ollama_client()
            health_result = await ollama_client.health_check()
            
            # Update health status
            self.metrics.health_status = health_result.get("status", "unknown")
            self.health_status_gauge.set(1 if health_result["healthy"] else 0)
            
            # Store health history
            health_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "status": health_result["status"],
                "healthy": health_result["healthy"],
                "error": health_result.get("error"),
                "response_time": health_result.get("response_time", 0)
            }
            
            self.health_history.append(health_record)
            
            # Keep only last 1000 health records
            if len(self.health_history) > 1000:
                self.health_history = self.health_history[-1000:]
            
            self.last_health_check = datetime.utcnow()
            
            # Log health status
            if not health_result["healthy"]:
                logger.warning(f"Grok LLM health check failed: {health_result.get('error', 'Unknown error')}")
            else:
                logger.debug("Grok LLM health check passed")
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.metrics.health_status = "error"
            self.health_status_gauge.set(0)
    
    async def _check_performance_thresholds(self):
        """Check performance against configured thresholds"""
        try:
            # Check response time threshold
            if self.metrics.average_response_time > settings.monitoring.max_response_time:
                await self._trigger_alert(
                    "high_response_time",
                    f"Average response time {self.metrics.average_response_time:.2f}s exceeds threshold {settings.monitoring.max_response_time}s"
                )
            
            # Check error rate threshold
            if self.metrics.total_requests > 0:
                current_error_rate = self.metrics.failed_requests / self.metrics.total_requests
                if current_error_rate > settings.monitoring.max_error_rate:
                    await self._trigger_alert(
                        "high_error_rate",
                        f"Error rate {current_error_rate:.2%} exceeds threshold {settings.monitoring.max_error_rate:.2%}"
                    )
                
                # Check success rate threshold
                if self.metrics.success_rate < settings.monitoring.min_success_rate:
                    await self._trigger_alert(
                        "low_success_rate",
                        f"Success rate {self.metrics.success_rate:.2%} below threshold {settings.monitoring.min_success_rate:.2%}"
                    )
            
            # Check concurrent requests limit
            if self.metrics.concurrent_requests >= settings.grok.grok_max_concurrent_requests:
                await self._trigger_alert(
                    "high_concurrency",
                    f"Concurrent requests {self.metrics.concurrent_requests} at limit {settings.grok.grok_max_concurrent_requests}"
                )
                
        except Exception as e:
            logger.error(f"Performance threshold check failed: {e}")
    
    async def _trigger_alert(self, alert_type: str, message: str):
        """Trigger alert for monitoring issues"""
        alert = {
            "id": f"{alert_type}_{int(time.time())}",
            "type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "warning" if alert_type in ["high_response_time", "high_concurrency"] else "critical",
            "acknowledged": False
        }
        
        self.alert_history.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        # Log alert
        logger.warning(f"ALERT [{alert['severity'].upper()}]: {message}")
        
        # Send alert if enabled
        if settings.monitoring.enable_alerts:
            await self._send_alert(alert)
    
    async def _send_alert(self, alert: Dict[str, Any]):
        """Send alert through configured channels"""
        try:
            # Email alert
            if settings.monitoring.alert_email:
                await self._send_email_alert(alert)
            
            # Webhook alert
            if settings.monitoring.alert_webhook:
                await self._send_webhook_alert(alert)
                
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def _send_email_alert(self, alert: Dict[str, Any]):
        """Send email alert"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            if not settings.monitoring.alert_email:
                logger.warning("No alert email configured, skipping email alert")
                return
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = settings.email.from_email or "agent47assist@gmail.com"
            msg['To'] = settings.monitoring.alert_email
            msg['Subject'] = f"Grok Monitor Alert: {alert.get('type', 'Unknown')}"
            
            # Create email body
            body = f"""
            Alert Type: {alert.get('type', 'Unknown')}
            Severity: {alert.get('severity', 'Unknown')}
            Message: {alert.get('message', 'No message')}
            Timestamp: {alert.get('timestamp', 'Unknown')}
            Agent: {alert.get('agent', 'Unknown')}
            
            Details:
            {alert.get('details', 'No additional details')}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            if settings.monitoring.smtp_server and settings.monitoring.smtp_port:
                server = smtplib.SMTP(settings.monitoring.smtp_server, settings.monitoring.smtp_port)
                if settings.monitoring.smtp_username and settings.monitoring.smtp_password:
                    server.starttls()
                    server.login(settings.monitoring.smtp_username, settings.monitoring.smtp_password)
                server.send_message(msg)
                server.quit()
                logger.info(f"Email alert sent to {settings.monitoring.alert_email}")
            else:
                logger.warning("SMTP server not configured, cannot send email alert")
                
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_webhook_alert(self, alert: Dict[str, Any]):
        """Send webhook alert"""
        try:
            import aiohttp
            
            if not settings.monitoring.alert_webhook:
                logger.warning("No webhook URL configured, skipping webhook alert")
                return
            
            # Prepare webhook payload
            payload = {
                "alert_type": alert.get('type', 'unknown'),
                "severity": alert.get('severity', 'unknown'),
                "message": alert.get('message', 'No message'),
                "timestamp": alert.get('timestamp', 'unknown'),
                "agent": alert.get('agent', 'unknown'),
                "details": alert.get('details', {}),
                "source": "grok_monitor"
            }
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    settings.monitoring.alert_webhook,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 201, 202]:
                        logger.info(f"Webhook alert sent to {settings.monitoring.alert_webhook}")
                    else:
                        logger.error(f"Webhook alert failed with status {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    async def _update_metrics(self):
        """Update Prometheus metrics"""
        try:
            # Update counters
            self.request_counter.inc(self.metrics.total_requests)
            self.success_counter.inc(self.metrics.successful_requests)
            self.failure_counter.inc(self.metrics.failed_requests)
            
            # Update gauges
            self.concurrent_requests_gauge.set(self.metrics.concurrent_requests)
            
            # Update response time histogram
            if self.metrics.average_response_time > 0:
                self.response_time_histogram.observe(self.metrics.average_response_time)
                
        except Exception as e:
            logger.error(f"Failed to update Prometheus metrics: {e}")
    
    def update_request_metrics(self, success: bool, response_time: float, concurrent: int):
        """Update metrics from request processing"""
        self.metrics.total_requests += 1
        
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        
        # Update response time average
        if self.metrics.successful_requests > 0:
            current_avg = self.metrics.average_response_time
            self.metrics.average_response_time = (
                (current_avg * (self.metrics.successful_requests - 1) + response_time) / 
                self.metrics.successful_requests
            )
        
        # Update concurrent requests
        self.metrics.concurrent_requests = concurrent
        
        # Update success rate
        self.metrics.success_rate = self.metrics.successful_requests / max(self.metrics.total_requests, 1)
        
        # Update last request time
        self.metrics.last_request_time = datetime.utcnow()
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary"""
        return {
            "overall_health": self.metrics.health_status == "healthy",
            "status": self.metrics.health_status,
            "last_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": self.metrics.success_rate,
                "average_response_time": self.metrics.average_response_time,
                "concurrent_requests": self.metrics.concurrent_requests
            },
            "alerts": {
                "total": len(self.alert_history),
                "unacknowledged": len([a for a in self.alert_history if not a["acknowledged"]]),
                "recent": self.alert_history[-10:] if self.alert_history else []
            },
            "monitoring": {
                "active": self.monitoring_active,
                "interval": settings.monitoring.monitoring_interval
            }
        }
    
    async def auto_scale_check(self) -> Dict[str, Any]:
        """Check if auto-scaling is needed"""
        if not settings.monitoring.enable_auto_scaling:
            return {"scaling_needed": False, "reason": "Auto-scaling disabled"}
        
        try:
            # Calculate current resource usage
            current_usage = self.metrics.concurrent_requests / settings.grok.grok_max_concurrent_requests
            
            scaling_action = None
            reason = ""
            
            # Check if scale up is needed
            if current_usage > settings.monitoring.scale_up_threshold:
                scaling_action = "scale_up"
                reason = f"High resource usage: {current_usage:.2%}"
            
            # Check if scale down is needed
            elif current_usage < settings.monitoring.scale_down_threshold:
                scaling_action = "scale_down"
                reason = f"Low resource usage: {current_usage:.2%}"
            
            if scaling_action:
                await self._trigger_alert(
                    "auto_scaling",
                    f"Auto-scaling {scaling_action} recommended: {reason}"
                )
            
            return {
                "scaling_needed": scaling_action is not None,
                "action": scaling_action,
                "reason": reason,
                "current_usage": current_usage
            }
            
        except Exception as e:
            logger.error(f"Auto-scaling check failed: {e}")
            return {"scaling_needed": False, "error": str(e)}
    
    async def cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            # Clean up old health records (keep last 7 days)
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            self.health_history = [
                record for record in self.health_history
                if datetime.fromisoformat(record["timestamp"]) > cutoff_date
            ]
            
            # Clean up old alerts (keep last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            self.alert_history = [
                alert for alert in self.alert_history
                if datetime.fromisoformat(alert["timestamp"]) > cutoff_date
            ]
            
            logger.info("Cleaned up old monitoring data")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")

# Global monitoring instance
grok_monitor = GrokHealthMonitor()

async def get_grok_monitor() -> GrokHealthMonitor:
    return grok_monitor

async def start_grok_monitoring():
    await grok_monitor.start_monitoring()

async def stop_grok_monitoring():
    await grok_monitor.stop_monitoring()
