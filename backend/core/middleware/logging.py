import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from core.logs import APILogger

# Create logger instance
api_logger = APILogger()

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging API requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Get user ID if authenticated
        user_id = None
        try:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                import jwt
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = payload.get("sub")
        except:
            pass
        
        # Log request
        start_time = time.time()
        api_logger.log_request(
            method=request.method,
            path=str(request.url.path),
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent,
            request_id=request_id
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Log response
            api_logger.log_response(
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                response_time=response_time,
                user_id=user_id,
                request_id=request_id
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            
            return response
            
        except Exception as e:
            # Calculate response time
            response_time = time.time() - start_time
            
            # Log error
            api_logger.log_api_error(
                method=request.method,
                path=str(request.url.path),
                error=str(e),
                user_id=user_id,
                request_id=request_id
            )
            
            # Re-raise the exception
            raise
