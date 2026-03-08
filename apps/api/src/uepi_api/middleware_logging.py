"""Request/Response logging middleware"""
import time
import uuid
from typing import Callable
import json

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

from uepi_api.logging_config import get_logger, log_request

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get user info if available
        user_id = None
        tenant_id = None
        if hasattr(request.state, "current_user"):
            user = request.state.current_user
            user_id = str(user.user_id) if hasattr(user, "user_id") else None
            tenant_id = str(user.tenant_id) if hasattr(user, "tenant_id") else None
        
        # Start timer
        start_time = time.time()
        
        # Capture request body for POST/PUT/PATCH
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    try:
                        request_body = json.loads(body.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        request_body = body.decode(errors='replace')[:500]  # Truncate if not JSON
            except Exception as e:
                logger.warning(f"Failed to capture request body: {e}")
        
        # Process request
        error = None
        status_code = 500
        response_body = None
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Capture response body for errors
            if status_code >= 400:
                try:
                    # Read response body
                    response_body_bytes = b""
                    async for chunk in response.body_iterator:
                        response_body_bytes += chunk
                    
                    # Try to parse as JSON
                    try:
                        response_body = json.loads(response_body_bytes.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        response_body = response_body_bytes.decode(errors='replace')[:500]
                    
                    # Recreate response with body
                    async def new_body_iterator():
                        yield response_body_bytes
                    
                    response = Response(
                        content=response_body_bytes,
                        status_code=status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type
                    )
                except Exception as e:
                    logger.warning(f"Failed to capture error response body: {e}")
            
        except Exception as e:
            error = e
            status_code = 500
            logger.error(f"Request failed with exception: {e}", exc_info=True)
            # Re-raise to let FastAPI handle it
            raise
        
        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request (skip health checks and static files)
            if request.url.path not in ["/health", "/docs", "/openapi.json", "/redoc", "/metrics"]:
                log_request(
                    logger=logger,
                    method=request.method,
                    path=str(request.url.path),
                    status_code=status_code,
                    duration_ms=duration_ms,
                    request_id=request_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    request_body=request_body,
                    response_body=response_body,
                    error=error
                )
        
        return response

