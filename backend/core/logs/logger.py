import logging
import time
import json
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List
from functools import wraps
import os
import sys
from pathlib import Path

# Global logger instance
_logger_instance: Optional[logging.Logger] = None

class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger(self.__class__.__name__)
    
    def log_info(self, message: str, **kwargs):
        """Log info message with additional context."""
        self.logger.info(message, extra=kwargs)
    
    def log_error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message with exception details."""
        if error:
            kwargs['error_type'] = type(error).__name__
            kwargs['error_message'] = str(error)
            kwargs['traceback'] = traceback.format_exc()
        self.logger.error(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with additional context."""
        self.logger.warning(message, extra=kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message with additional context."""
        self.logger.debug(message, extra=kwargs)

class PerformanceLogger:
    """Specialized logger for performance monitoring and metrics."""
    
    def __init__(self, name: str = "performance"):
        self.logger = get_logger(f"performance.{name}")
        self.metrics: Dict[str, List[float]] = {}
    
    def start_timer(self, operation: str) -> float:
        """Start timing an operation."""
        start_time = time.time()
        self.logger.debug(f"Started timing operation: {operation}")
        return start_time
    
    def end_timer(self, operation: str, start_time: float, **context):
        """End timing an operation and log the duration."""
        duration = time.time() - start_time
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)
        
        self.logger.info(
            f"Operation completed: {operation}",
            extra={
                "operation": operation,
                "duration_ms": round(duration * 1000, 2),
                "duration_seconds": round(duration, 4),
                **context
            }
        )
        return duration
    
    def log_metric(self, metric_name: str, value: float, **context):
        """Log a custom metric."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)
        
        self.logger.info(
            f"Metric recorded: {metric_name}",
            extra={
                "metric_name": metric_name,
                "metric_value": value,
                **context
            }
        )
    
    def get_average(self, metric_name: str) -> Optional[float]:
        """Get average value for a metric."""
        if metric_name in self.metrics and self.metrics[metric_name]:
            return sum(self.metrics[metric_name]) / len(self.metrics[metric_name])
        return None
    
    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {}
        
        values = self.metrics[metric_name]
        return {
            "count": len(values),
            "average": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "total": sum(values)
        }

class SecurityLogger:
    """Specialized logger for security events and audit trails."""
    
    def __init__(self, name: str = "security"):
        self.logger = get_logger(f"security.{name}")
    
    def log_login_attempt(self, user_id: str, success: bool, ip_address: str, user_agent: str, **context):
        """Log login attempt."""
        self.logger.info(
            f"Login attempt: {'SUCCESS' if success else 'FAILED'} for user {user_id}",
            extra={
                "event_type": "login_attempt",
                "user_id": user_id,
                "success": success,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.utcnow().isoformat(),
                **context
            }
        )
    
    def log_permission_check(self, user_id: str, resource: str, action: str, granted: bool, **context):
        """Log permission check."""
        self.logger.info(
            f"Permission check: {'GRANTED' if granted else 'DENIED'} {action} on {resource} for user {user_id}",
            extra={
                "event_type": "permission_check",
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "granted": granted,
                "timestamp": datetime.utcnow().isoformat(),
                **context
            }
        )
    
    def log_data_access(self, user_id: str, data_type: str, operation: str, record_id: str, **context):
        """Log data access."""
        self.logger.info(
            f"Data access: {operation} on {data_type} record {record_id} by user {user_id}",
            extra={
                "event_type": "data_access",
                "user_id": user_id,
                "data_type": data_type,
                "operation": operation,
                "record_id": record_id,
                "timestamp": datetime.utcnow().isoformat(),
                **context
            }
        )
    
    def log_security_violation(self, violation_type: str, user_id: Optional[str], details: str, **context):
        """Log security violation."""
        self.logger.warning(
            f"Security violation: {violation_type}",
            extra={
                "event_type": "security_violation",
                "violation_type": violation_type,
                "user_id": user_id,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
                **context
            }
        )
    
    def log_audit_trail(self, user_id: str, action: str, target: str, changes: Dict[str, Any], **context):
        """Log audit trail entry."""
        self.logger.info(
            f"Audit trail: {action} on {target} by user {user_id}",
            extra={
                "event_type": "audit_trail",
                "user_id": user_id,
                "action": action,
                "target": target,
                "changes": json.dumps(changes),
                "timestamp": datetime.utcnow().isoformat(),
                **context
            }
        )

class APILogger:
    """Specialized logger for API requests and responses."""
    
    def __init__(self, name: str = "api"):
        self.logger = get_logger(f"api.{name}")
    
    def log_request(self, method: str, path: str, user_id: Optional[str], ip_address: str, 
                   user_agent: str, request_id: str, **context):
        """Log incoming API request."""
        self.logger.info(
            f"API Request: {method} {path}",
            extra={
                "event_type": "api_request",
                "method": method,
                "path": path,
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                **context
            }
        )
    
    def log_response(self, method: str, path: str, status_code: int, response_time: float,
                    request_id: str, **context):
        """Log API response."""
        self.logger.info(
            f"API Response: {method} {path} - {status_code} ({response_time:.3f}s)",
            extra={
                "event_type": "api_response",
                "method": method,
                "path": path,
                "status_code": status_code,
                "response_time": response_time,
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                **context
            }
        )
    
    def log_error(self, method: str, path: str, error: Exception, request_id: str, **context):
        """Log API error."""
        self.logger.error(
            f"API Error: {method} {path} - {type(error).__name__}: {str(error)}",
            extra={
                "event_type": "api_error",
                "method": method,
                "path": path,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                **context
            }
        )

def setup_logger(name: str = "agent47", level: str = "INFO", 
                log_file: Optional[str] = None, 
                log_format: Optional[str] = None) -> logging.Logger:
    """
    Setup and configure the logger.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        log_format: Optional custom log format
    
    Returns:
        Configured logger instance
    """
    global _logger_instance
    
    if _logger_instance is not None:
        return _logger_instance
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Default format
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    _logger_instance = logger
    return logger

def get_logger(name: str = "agent47") -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    if _logger_instance is None:
        return setup_logger(name)
    
    if name == "agent47":
        return _logger_instance
    
    return logging.getLogger(name)

def log_function_call(func):
    """Decorator to log function calls with timing."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(f"{func.__module__}.{func.__name__}")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(
                f"Function {func.__name__} completed successfully in {duration:.3f}s",
                extra={
                    "function": func.__name__,
                    "duration": duration,
                    "success": True
                }
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Function {func.__name__} failed after {duration:.3f}s: {str(e)}",
                extra={
                    "function": func.__name__,
                    "duration": duration,
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            )
            raise
    
    return wrapper

def log_async_function_call(func):
    """Decorator to log async function calls with timing."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger(f"{func.__module__}.{func.__name__}")
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(
                f"Async function {func.__name__} completed successfully in {duration:.3f}s",
                extra={
                    "function": func.__name__,
                    "duration": duration,
                    "success": True
                }
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Async function {func.__name__} failed after {duration:.3f}s: {str(e)}",
                extra={
                    "function": func.__name__,
                    "duration": duration,
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            )
            raise
    
    return wrapper
