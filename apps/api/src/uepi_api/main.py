"""UEPI API Service"""
import concurrent.futures
import os
import re
import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
# OpenTelemetry imports (optional - skip if not available or incompatible)
OPENTELEMETRY_AVAILABLE = False
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    OPENTELEMETRY_AVAILABLE = True
except (ImportError, TypeError, Exception):
    # Skip OpenTelemetry if not available or incompatible (e.g., Python 3.14 + protobuf issues)
    OPENTELEMETRY_AVAILABLE = False
    trace = None
    OTLPSpanExporter = None
    FastAPIInstrumentor = None
    SQLAlchemyInstrumentor = None
    TracerProvider = None
    BatchSpanProcessor = None

# Database-only mode - no file storage initialization needed
# from uepi_api.storage_file import init_storage  # Removed - database-only
# metrics imported inside /metrics only — prometheus registration is not free on cold start
from uepi_api.logging_config import setup_logging, get_logger, log_error_with_context
from uepi_api.middleware_logging import RequestLoggingMiddleware
from uepi_api.app_extended_routes import register_extended_routes, path_skips_extended_loading


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Keep startup before ``yield`` empty so Gunicorn/Uvicorn binds immediately (Azure HTML 503 if blocked)."""
    yield
    if os.getenv("UEPI_ENABLE_SCHEDULE_EXECUTOR", "").strip().lower() in ("1", "true", "yes"):
        try:
            from uepi_api.routers.schedule_executor_service import stop_schedule_executor

            stop_schedule_executor()
        except Exception as e:
            print(f"uepi_api: stop_schedule_executor: {e}", flush=True)


def _start_background_startup(settings: object) -> None:
    """Logging, DB seed, optional scheduler — after HTTP listener is up."""

    def _run() -> None:
        log_level = os.getenv("LOG_LEVEL", getattr(settings, "log_level", "INFO"))
        try:
            setup_logging(log_level=log_level, enable_file_logging=True)
        except Exception as e:
            print(f"uepi_api: setup_logging failed (bg): {e}", flush=True)
            import traceback

            traceback.print_exc()
        try:
            logger = get_logger(__name__)
            logger.info(
                "Application started (background)",
                extra={"extra_data": {"environment": getattr(settings, "environment", ""), "log_level": log_level}},
            )
        except Exception:
            pass
        try:
            from uepi_api.storage_auth import ensure_demo_tenant_and_user

            ensure_demo_tenant_and_user()
        except Exception as e:
            print(f"uepi_api: ensure_demo_tenant_and_user (bg): {e}", flush=True)
        if os.getenv("UEPI_ENABLE_SCHEDULE_EXECUTOR", "").strip().lower() in ("1", "true", "yes"):
            try:
                from uepi_api.routers.schedule_executor_service import start_schedule_executor

                start_schedule_executor(interval_seconds=60)
                print("Schedule executor started", flush=True)
            except Exception as e:
                print(f"uepi_api: schedule executor (bg): {e}", flush=True)
                import traceback

                traceback.print_exc()
        # Warm policy-rollout recommendations so the first UI hit is cache-fast.
        if os.getenv("UEPI_WARM_POLICY_ROLLOUTS", "1").strip().lower() in ("1", "true", "yes"):
            try:
                from uuid import UUID

                from uepi_api.database import SessionLocal
                from uepi_api.services.policy_rollout_recommendations import (
                    compute_policy_rollout_recommendations,
                )

                def _warm_rollouts() -> None:
                    db = SessionLocal()
                    try:
                        tenant_id = UUID("00000000-0000-0000-0000-000000000001")
                        compute_policy_rollout_recommendations(
                            db, tenant_id, months_lookback=12, limit=25
                        )
                        print("uepi_api: policy rollout recommendations warmed", flush=True)
                    except Exception as warm_err:
                        print(f"uepi_api: rollout warm skipped: {warm_err}", flush=True)
                    finally:
                        db.close()

                threading.Thread(target=_warm_rollouts, daemon=True, name="uepi-warm-rollouts").start()
            except Exception as e:
                print(f"uepi_api: rollout warm setup failed: {e}", flush=True)

    threading.Thread(target=_run, daemon=True, name="uepi-bg-startup").start()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    from uepi_api.config import get_settings
    
    settings = get_settings()
    
    app = FastAPI(
        title="UEPI API",
        description="Utilization Elasticity & Policy Impact Intelligence API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = settings
    
    # CORS - Allow requests from web server (comprehensive list)
    cors_origins_list = [
        "http://localhost:3050",
        "http://localhost:5173",
        "http://127.0.0.1:3050",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://gentle-flower-01dffcd0f.2.azurestaticapps.net",
        "https://proud-glacier-0c52b8e0f.6.azurestaticapps.net",
        "https://healthforesight-web.azurestaticapps.net",
        "https://healthforesight-web.azurewebsites.net",
        "https://data-voyager.vercel.app",
        "https://www.healthforesight.ai",
    ]
    # Add any additional origins from settings
    if hasattr(settings, 'cors_origins') and settings.cors_origins:
        cors_origins_list.extend(settings.cors_origins)
    
    # Store CORS origins in app state for exception handlers
    app.state.cors_origins = cors_origins_list

    # Frontend on Azure App Service: healthforesight-web[--slot].azurewebsites.net
    _CORS_HEALTHFORESIGHT_APP = re.compile(
        r"^https://healthforesight-[a-z0-9-]+\.azurewebsites\.net$",
        re.IGNORECASE,
    )
    # Data Voyager / HealthForesight Vercel (prod + preview URLs)
    _CORS_VERCEL_APP = re.compile(
        r"^https://([a-z0-9-]+\.)*vercel\.app$",
        re.IGNORECASE,
    )

    def _cors_allow_origin(origin: str | None) -> str | None:
        o = (origin or "").strip()
        if not o:
            return None
        if o in cors_origins_list:
            return o
        if o.startswith("https://") and ".azurestaticapps.net" in o:
            return o
        if _CORS_HEALTHFORESIGHT_APP.match(o):
            return o
        if _CORS_VERCEL_APP.match(o):
            return o
        if o.startswith("http://localhost") or o.startswith("http://127.0.0.1"):
            return o
        return None

    class ExplicitCORSMiddleware(BaseHTTPMiddleware):
        """Handles preflight + response CORS (avoids missing headers behind Azure / Starlette quirks)."""

        async def dispatch(self, request: Request, call_next):
            origin = request.headers.get("origin")
            allowed = _cors_allow_origin(origin)
            if request.method == "OPTIONS" and allowed:
                req_h = request.headers.get("access-control-request-headers", "authorization,content-type")
                return Response(
                    status_code=200,
                    content="",
                    headers={
                        "Access-Control-Allow-Origin": allowed,
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD",
                        "Access-Control-Allow-Headers": req_h,
                        "Access-Control-Max-Age": "86400",
                    },
                )
            response = await call_next(request)
            if allowed:
                response.headers["Access-Control-Allow-Origin"] = allowed
                response.headers["Access-Control-Allow-Credentials"] = "true"
            return response

    class LazyExtendedRoutesMiddleware(BaseHTTPMiddleware):
        """Load polars/pandas-heavy routers on first request that needs them (not at import).

        Import/registration runs in a worker thread so DNS/DB stalls during lazy
        warm-up cannot freeze the event loop (liveness /health must stay responsive).
        """

        async def dispatch(self, request: Request, call_next):
            if not path_skips_extended_loading(request.url.path):
                import asyncio

                await asyncio.to_thread(register_extended_routes, request.app)
            return await call_next(request)

    # Starlette: last-added middleware is outermost on the request. Order here is
    # Lazy (innermost, just before routing) → logging → CORS (outer, OPTIONS first).
    app.add_middleware(LazyExtendedRoutesMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ExplicitCORSMiddleware)
    
    # OpenTelemetry instrumentation (if available)
    if OPENTELEMETRY_AVAILABLE and settings.environment != "development":
        FastAPIInstrumentor.instrument_app(app)
    
    # Light routers only at startup; heavy stack loads on first non-skip request (see LazyExtendedRoutesMiddleware).
    from uepi_api.routers import auth

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])

    from uepi_api.routers import access

    app.include_router(access.router, prefix="/api/v1/access", tags=["Access"])

    # Error handlers for comprehensive logging
    logger = get_logger(__name__)
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions with logging and CORS headers"""
        user_id = None
        tenant_id = None
        if hasattr(request.state, "current_user"):
            user = request.state.current_user
            user_id = str(user.user_id) if hasattr(user, "user_id") else None
            tenant_id = str(user.tenant_id) if hasattr(user, "tenant_id") else None
        
        log_error_with_context(
            logger=logger,
            error=exc,
            context={
                "path": str(request.url.path),
                "method": request.method,
                "status_code": exc.status_code,
            },
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        # Get origin from request headers for CORS
        origin = request.headers.get("origin")
        headers = {}
        # Get CORS origins from app state
        cors_origins = getattr(request.app.state, 'cors_origins', [])
        if origin and (origin in cors_origins or any(origin.startswith(o.replace('*', '')) for o in cors_origins if '*' in o)):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
        
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "status_code": exc.status_code},
            headers=headers
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors with logging"""
        user_id = None
        tenant_id = None
        if hasattr(request.state, "current_user"):
            user = request.state.current_user
            user_id = str(user.user_id) if hasattr(user, "user_id") else None
            tenant_id = str(user.tenant_id) if hasattr(user, "tenant_id") else None
        
        log_error_with_context(
            logger=logger,
            error=exc,
            context={
                "path": str(request.url.path),
                "method": request.method,
                "validation_errors": exc.errors(),
            },
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "status_code": 422}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions with logging and CORS headers"""
        user_id = None
        tenant_id = None
        if hasattr(request.state, "current_user"):
            user = request.state.current_user
            user_id = str(user.user_id) if hasattr(user, "user_id") else None
            tenant_id = str(user.tenant_id) if hasattr(user, "tenant_id") else None
        
        log_error_with_context(
            logger=logger,
            error=exc,
            context={
                "path": str(request.url.path),
                "method": request.method,
            },
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        # Get origin from request headers for CORS
        origin = request.headers.get("origin")
        headers = {}
        # Get CORS origins from app state
        cors_origins = getattr(request.app.state, 'cors_origins', [])
        if origin and (origin in cors_origins or any(origin.startswith(o.replace('*', '')) for o in cors_origins if '*' in o)):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
        
        settings = getattr(request.app.state, "settings", None)
        expose = os.getenv("UEPI_EXPOSE_ERRORS", "").strip().lower() in ("1", "true", "yes")
        if settings and getattr(settings, "debug", False):
            expose = True
        detail_msg = "Internal server error"
        if expose:
            detail_msg = f"{type(exc).__name__}: {exc}"
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": detail_msg, "status_code": 500},
            headers=headers
        )
    
    # Health check endpoints
    # Liveness (/health, /live, /ping): process + event loop only — never touch Postgres.
    # Readiness (/ready, /health/detailed): dependency check in a worker thread with hard timeout.
    @app.get("/health")
    @app.get("/api/v1/health")
    @app.get("/live")
    @app.get("/api/v1/live")
    async def health():
        """Liveness — API process and event loop are responsive. No database I/O."""
        return {
            "status": "healthy",
            "check": "liveness",
            "service": "uepi-api",
            "database": "not_checked",
        }
    
    @app.get("/api/v1/ping")
    async def ping():
        """Instant OK — no DB. Use to verify API is reachable (through web proxy or direct)."""
        return {"ok": True, "service": "uepi-api", "check": "liveness"}

    def _db_ping_status() -> str:
        from uepi_api.database import SessionLocal
        from sqlalchemy import text

        try:
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1")).scalar()
                return "connected"
            finally:
                db.close()
        except Exception as e:
            return f"error: {str(e)[:200]}"

    @app.get("/ready")
    @app.get("/api/v1/ready")
    @app.get("/api/v1/health/detailed")
    async def health_detailed():
        """Readiness — Postgres must respond within ~6s. Never blocks the event loop."""
        db_status = "unknown"
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(_db_ping_status)
                db_status = fut.result(timeout=6)
        except concurrent.futures.TimeoutError:
            db_status = (
                "timeout (>6s): PostgreSQL not responding — check DATABASE_URL on this API app, "
                "PostgreSQL firewall (allow Azure services or App Service outbound IPs), and VNet rules."
            )
        except Exception as e:
            db_status = f"check_failed: {str(e)[:200]}"

        ready = db_status == "connected"
        return {
            "status": "healthy" if ready else "not_ready",
            "check": "readiness",
            "service": "uepi-api",
            "database": db_status,
            "ready": ready,
            "hint": "If database is not connected, login will fail. Fix Postgres access from healthforesight-api.",
        }
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        from fastapi import Response
        from uepi_api.metrics import generate_latest, CONTENT_TYPE_LATEST

        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    _start_background_startup(settings)

    return app


def _degraded_app(exc: BaseException) -> FastAPI:
    """Last resort: still answer /api/v1/ping so Azure sees a healthy listener while you fix logs."""
    from fastapi import FastAPI as FF

    d = FF(title="UEPI API (degraded)", version="0.0.0")

    @d.get("/api/v1/ping")
    async def ping_degraded():
        return {
            "ok": False,
            "service": "uepi-api",
            "degraded": True,
            "error": str(exc)[:300],
        }

    @d.get("/health")
    async def health_degraded():
        return {"status": "degraded", "detail": str(exc)[:300]}

    return d


try:
    app = create_app()
except Exception as e:
    import traceback

    traceback.print_exc()
    app = _degraded_app(e)

