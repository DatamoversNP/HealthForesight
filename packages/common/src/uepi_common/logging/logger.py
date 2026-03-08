"""Structured JSON logging configuration"""
import json
import logging
import sys
from contextvars import ContextVar
from typing import Any, Optional
from uuid import UUID

# Context variables for request-scoped logging
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
tenant_id_ctx: ContextVar[Optional[UUID]] = ContextVar("tenant_id", default=None)
user_id_ctx: ContextVar[Optional[UUID]] = ContextVar("user_id", default=None)
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add context variables if available
        correlation_id = correlation_id_ctx.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id
        
        tenant_id = tenant_id_ctx.get()
        if tenant_id:
            log_data["tenant_id"] = str(tenant_id)
        
        user_id = user_id_ctx.get()
        if user_id:
            log_data["user_id"] = str(user_id)
        
        request_id = request_id_ctx.get()
        if request_id:
            log_data["request_id"] = request_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add any extra attributes that don't conflict
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info",
                "correlation_id", "tenant_id", "user_id", "request_id",
            }:
                try:
                    # Try to serialize, skip if not serializable
                    json.dumps(value)
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)
        
        return json.dumps(log_data, default=str)


class StructuredLogger:
    """Structured logger wrapper that adds context"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def _log(
        self,
        level: int,
        msg: str,
        *args: Any,
        correlation_id: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        request_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log with context"""
        # Set context variables for this log call
        if correlation_id:
            correlation_id_ctx.set(correlation_id)
        if tenant_id:
            tenant_id_ctx.set(tenant_id)
        if user_id:
            user_id_ctx.set(user_id)
        if request_id:
            request_id_ctx.set(request_id)
        
        # Add extra fields to the record
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        
        kwargs["extra"]["extra_fields"] = {
            k: v for k, v in {
                "correlation_id": correlation_id,
                "tenant_id": str(tenant_id) if tenant_id else None,
                "user_id": str(user_id) if user_id else None,
                "request_id": request_id,
            }.items() if v is not None
        }
        
        self.logger.log(level, msg, *args, **kwargs)
    
    def debug(
        self,
        msg: str,
        *args: Any,
        correlation_id: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        request_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log debug message"""
        self._log(logging.DEBUG, msg, *args, correlation_id=correlation_id, tenant_id=tenant_id, user_id=user_id, request_id=request_id, **kwargs)
    
    def info(
        self,
        msg: str,
        *args: Any,
        correlation_id: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        request_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log info message"""
        self._log(logging.INFO, msg, *args, correlation_id=correlation_id, tenant_id=tenant_id, user_id=user_id, request_id=request_id, **kwargs)
    
    def warning(
        self,
        msg: str,
        *args: Any,
        correlation_id: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        request_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log warning message"""
        self._log(logging.WARNING, msg, *args, correlation_id=correlation_id, tenant_id=tenant_id, user_id=user_id, request_id=request_id, **kwargs)
    
    def error(
        self,
        msg: str,
        *args: Any,
        correlation_id: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        request_id: Optional[str] = None,
        exc_info: Any = None,
        **kwargs: Any,
    ) -> None:
        """Log error message"""
        if exc_info:
            kwargs["exc_info"] = exc_info
        self._log(logging.ERROR, msg, *args, correlation_id=correlation_id, tenant_id=tenant_id, user_id=user_id, request_id=request_id, **kwargs)
    
    def critical(
        self,
        msg: str,
        *args: Any,
        correlation_id: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        request_id: Optional[str] = None,
        exc_info: Any = None,
        **kwargs: Any,
    ) -> None:
        """Log critical message"""
        if exc_info:
            kwargs["exc_info"] = exc_info
        self._log(logging.CRITICAL, msg, *args, correlation_id=correlation_id, tenant_id=tenant_id, user_id=user_id, request_id=request_id, **kwargs)


def setup_logging(
    level: str = "INFO",
    format_json: bool = True,
    stream: Any = None,
) -> None:
    """Setup structured logging configuration
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_json: Whether to use JSON formatting (default: True)
        stream: Output stream (default: sys.stdout)
    """
    if stream is None:
        stream = sys.stdout
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(stream)
    handler.setLevel(getattr(logging, level.upper()))
    
    # Set formatter
    if format_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        StructuredLogger instance
    """
    logger = logging.getLogger(name)
    return StructuredLogger(logger)


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context"""
    correlation_id_ctx.set(correlation_id)


def set_tenant_id(tenant_id: UUID) -> None:
    """Set tenant ID for current context"""
    tenant_id_ctx.set(tenant_id)


def set_user_id(user_id: UUID) -> None:
    """Set user ID for current context"""
    user_id_ctx.set(user_id)


def set_request_id(request_id: str) -> None:
    """Set request ID for current context"""
    request_id_ctx.set(request_id)

