"""Comprehensive logging configuration for UEPI API"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import json
import traceback

# Project root: .../apps (from apps/api/src/uepi_api/logging_config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
# Do not mkdir at import — Azure App Service may use a read-only app dir; setup_logging handles dirs safely.

# Log file paths
API_LOG_FILE = LOG_DIR / "api.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"
ACTIONS_LOG_FILE = LOG_DIR / "actions.log"
REQUESTS_LOG_FILE = LOG_DIR / "requests.log"


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }
        
        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        return json.dumps(log_data, default=str)


class DetailedFormatter(logging.Formatter):
    """Detailed human-readable formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level = record.levelname.ljust(8)
        logger = record.name.ljust(30)
        message = record.getMessage()
        
        log_line = f"{timestamp} | {level} | {logger} | {message}"
        
        # Add location info
        if record.module and record.funcName:
            log_line += f" | {record.module}.{record.funcName}:{record.lineno}"
        
        # Add exception info
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_line += f"\n  Exception: {exc_type.__name__}: {exc_value}"
            log_line += f"\n  Traceback:\n" + "".join(traceback.format_tb(exc_tb))
        
        # Add extra data
        if hasattr(record, "extra_data"):
            log_line += f"\n  Extra: {json.dumps(record.extra_data, default=str, indent=2)}"
        
        return log_line


def setup_logging(log_level: str = "INFO", enable_file_logging: bool = True) -> None:
    """Setup comprehensive logging configuration"""
    from uepi_api.runtime_env import is_azure_app_service

    # Linux Web App for Containers: WEBSITE_INSTANCE_ID is often missing; file logs under /app fail
    # and can abort FastAPI lifespan before Uvicorn binds → HTML 503. Console-only unless opted in.
    if enable_file_logging and is_azure_app_service():
        if os.getenv("UEPI_ENABLE_FILE_LOG", "").strip().lower() not in ("1", "true", "yes"):
            enable_file_logging = False

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(DetailedFormatter())
    root_logger.addHandler(console_handler)
    
    if enable_file_logging:
        log_dir = LOG_DIR
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            # Azure Linux containers often disallow writes under /app — fall back to /tmp
            log_dir = Path(os.environ.get("TMPDIR", "/tmp")) / "uepi_logs"
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                logging.warning(
                    "File logging disabled: could not create log directory (%s); using console only",
                    e,
                )
                enable_file_logging = False

        if enable_file_logging:
            try:
                api_path = log_dir / "api.log"
                err_path = log_dir / "errors.log"
                act_path = log_dir / "actions.log"
                req_path = log_dir / "requests.log"
                # API log file (all logs)
                api_handler = logging.handlers.RotatingFileHandler(
                    api_path,
                    maxBytes=10 * 1024 * 1024,  # 10MB
                    backupCount=5,
                    encoding='utf-8'
                )
                api_handler.setLevel(logging.DEBUG)
                api_handler.setFormatter(JSONFormatter())
                root_logger.addHandler(api_handler)

                # Error log file (errors only)
                error_handler = logging.handlers.RotatingFileHandler(
                    err_path,
                    maxBytes=10 * 1024 * 1024,  # 10MB
                    backupCount=10,
                    encoding='utf-8'
                )
                error_handler.setLevel(logging.ERROR)
                error_handler.setFormatter(JSONFormatter())
                root_logger.addHandler(error_handler)

                # Actions log file (action tracking)
                actions_handler = logging.handlers.RotatingFileHandler(
                    act_path,
                    maxBytes=10 * 1024 * 1024,  # 10MB
                    backupCount=5,
                    encoding='utf-8'
                )
                actions_handler.setLevel(logging.INFO)
                actions_handler.addFilter(lambda record: hasattr(record, "action_type"))
                actions_handler.setFormatter(JSONFormatter())
                root_logger.addHandler(actions_handler)

                # Requests log file (HTTP requests)
                requests_handler = logging.handlers.RotatingFileHandler(
                    req_path,
                    maxBytes=10 * 1024 * 1024,  # 10MB
                    backupCount=5,
                    encoding='utf-8'
                )
                requests_handler.setLevel(logging.INFO)
                requests_handler.addFilter(lambda record: hasattr(record, "request_id"))
                requests_handler.setFormatter(JSONFormatter())
                root_logger.addHandler(requests_handler)
            except OSError as e:
                logging.warning(
                    "File logging disabled: RotatingFileHandler failed (%s); console only",
                    e,
                )
                enable_file_logging = False
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    logging.info("Logging configured", extra={
        "log_level": log_level,
        "file_logging": enable_file_logging,
        "log_dir": str(LOG_DIR),
    })


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


def log_action(
    logger: logging.Logger,
    action: str,
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    level: int = logging.INFO
) -> None:
    """Log a user action with full details"""
    extra_data = {
        "action_type": action,
        "action_details": details or {},
        "user_id": user_id,
        "tenant_id": tenant_id,
    }
    logger.log(level, f"Action: {action}", extra={"extra_data": extra_data, "action_type": action})


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None
) -> None:
    """Log an error with full context"""
    extra_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "error_context": context or {},
        "user_id": user_id,
        "tenant_id": tenant_id,
        "traceback": traceback.format_exception(type(error), error, error.__traceback__),
    }
    logger.error(
        f"Error: {type(error).__name__}: {str(error)}",
        exc_info=True,
        extra={"extra_data": extra_data}
    )


def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    request_body: Optional[Any] = None,
    response_body: Optional[Any] = None,
    error: Optional[Exception] = None
) -> None:
    """Log HTTP request with full details"""
    extra_data = {
        "request_id": request_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "user_id": user_id,
        "tenant_id": tenant_id,
    }
    
    # Add request/response bodies (truncated for large payloads)
    if request_body is not None:
        body_str = json.dumps(request_body, default=str) if isinstance(request_body, dict) else str(request_body)
        extra_data["request_body"] = body_str[:1000] if len(body_str) > 1000 else body_str
    
    if response_body is not None:
        body_str = json.dumps(response_body, default=str) if isinstance(response_body, dict) else str(response_body)
        extra_data["response_body"] = body_str[:1000] if len(body_str) > 1000 else body_str
    
    if error:
        extra_data["error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exception(type(error), error, error.__traceback__),
        }
    
    logger.info(
        f"Request: {method} {path} -> {status_code} ({duration_ms:.2f}ms)",
        extra={"extra_data": extra_data, "request_id": request_id}
    )

