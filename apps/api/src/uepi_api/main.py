"""UEPI API Service"""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
from uepi_api.storage_auth import ensure_demo_tenant_and_user
from uepi_api.metrics import generate_latest, CONTENT_TYPE_LATEST
from uepi_api.logging_config import setup_logging, get_logger, log_error_with_context
from uepi_api.middleware_logging import RequestLoggingMiddleware
from uepi_api.routers import (
    analyses,
    auth,
    decisions,
    exports,
    lineage,
    notifications,
    policy_import,
    scorecards,
)
# Note: cohorts_file uses storage_cohorts which is database-only
# Note: RBAC uses access router which uses database models directly
from uepi_api.routers import policy_workspace
from uepi_api.routers import decisions_workspace
from uepi_api.routers import uncertainty_visualization
from uepi_api.routers import behavior_detection
from uepi_api.routers import collaboration
from uepi_api.routers import narratives

# Note: ingestions and datasets routers use database models directly


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events"""
    settings = app.state.settings
    
    # Setup comprehensive logging
    # Check environment variable first, then settings
    log_level = os.getenv('LOG_LEVEL', getattr(settings, 'log_level', 'INFO'))
    setup_logging(log_level=log_level, enable_file_logging=True)
    logger = get_logger(__name__)
    logger.info("Application starting", extra={"extra_data": {"environment": settings.environment, "log_level": log_level}})
    
    # Database-only mode - ensure demo tenant and user exist
    # Make this non-blocking - if database is unavailable, continue anyway
    try:
        ensure_demo_tenant_and_user()
    except Exception as e:
        logger.warning(f"Could not ensure demo tenant/user (database may be unavailable): {e}")
        # Continue startup - database operations will fail later if needed, but API can still serve some endpoints
    
    # Start schedule executor (Phase 10)
    try:
        from uepi_api.routers.schedule_executor_service import start_schedule_executor
        start_schedule_executor(interval_seconds=60)  # Check every minute
        print("✅ Schedule executor started")
    except Exception as e:
        print(f"⚠️  Failed to start schedule executor: {e}")
        import traceback
        traceback.print_exc()
    
    yield
    
    # Shutdown
    try:
        from uepi_api.routers.schedule_executor_service import stop_schedule_executor
        stop_schedule_executor()
        print("✅ Schedule executor stopped")
    except Exception as e:
        print(f"⚠️  Error stopping schedule executor: {e}")


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
    ]
    # Add any additional origins from settings
    if hasattr(settings, 'cors_origins') and settings.cors_origins:
        cors_origins_list.extend(settings.cors_origins)
    
    # Store CORS origins in app state for exception handlers
    app.state.cors_origins = cors_origins_list
    
    # Configure CORS with proper order - must be before other middleware
    # Use allow_origin_regex to allow all Azure Static Web Apps domains
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins_list,
        allow_origin_regex=r"https://.*\.azurestaticapps\.net",  # Allow all Azure Static Web Apps
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=3600,
    )
    
    # Add request logging middleware (after CORS, before routers)
    app.add_middleware(RequestLoggingMiddleware)
    
    # OpenTelemetry instrumentation (if available)
    if OPENTELEMETRY_AVAILABLE and settings.environment != "development":
        FastAPIInstrumentor.instrument_app(app)
    
    # Routers - Database-only (all use PostgreSQL)
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
    
    # Access control router (uses database models: Role, User)
    from uepi_api.routers import access
    app.include_router(access.router, prefix="/api/v1/access", tags=["Access"])
    
    # Database-based routers (use database storage)
    from uepi_api.routers import policies
    app.include_router(policies.router, prefix="/api/v1", tags=["Policies"])
    
    # Optional routers (may be None if imports fail)
    from uepi_api.routers import ingestions, datasets
    if ingestions is not None:
        app.include_router(ingestions.router, prefix="/api/v1", tags=["Ingestions"])
    if datasets is not None:
        app.include_router(datasets.router, prefix="/api/v1", tags=["Datasets"])
    
    # Other routers (database-only)
    app.include_router(policy_import.router, prefix="/api/v1", tags=["Policy Import"])
    # Add synchronous impact analysis endpoint FIRST (so it takes precedence)
    # This processes immediately without needing a worker
    try:
        from uepi_api.routers import analyses_file
        app.include_router(analyses_file.router, prefix="/api/v1", tags=["Analyses (Sync)"])
    except ImportError:
        pass  # analyses_file router not available
    # Database-based analyses router (creates PENDING, needs worker)
    app.include_router(analyses.router, prefix="/api/v1", tags=["Analyses"])
    app.include_router(scorecards.router, prefix="/api/v1", tags=["Scorecards"])
    app.include_router(exports.router, prefix="/api/v1", tags=["Exports"])
    # Database-based cohorts router (uses storage_cohorts which is database-only)
    from uepi_api.routers import cohorts_file
    app.include_router(cohorts_file.router, prefix="/api/v1", tags=["Cohorts"])
    # Note: cohorts_file uses storage_cohorts which is database-only
    # Note: Old decisions router removed - using decisions_workspace (Epic 3) instead
    # app.include_router(decisions.router, prefix="/api/v1", tags=["Decisions"])
    app.include_router(lineage.router, prefix="/api/v1", tags=["Lineage"])
    # notifications router is imported at top level and included above
    
    # Phase 1: Continuous System - Data Periods and Policy Versions
    try:
        from uepi_api.routers import data_periods
        app.include_router(data_periods.router, prefix="/api/v1", tags=["Data Periods"])
    except ImportError:
        pass  # data_periods router not available
    
    try:
        from uepi_api.routers import policy_versions
        app.include_router(policy_versions.router, prefix="/api/v1", tags=["Policy Versions"])
    except ImportError as e:
        print(f"Warning: Could not import policy_versions router: {e}")
        pass  # Continue without policy_versions router
    
    # Pipelines (uses database models: Pipeline, PipelineRun)
    from uepi_api.routers import pipelines
    app.include_router(pipelines.router, prefix="/api/v1", tags=["Pipelines"])
    
    # Optional pipeline monitoring (may be None if polars import fails)
    from uepi_api.routers import pipeline_monitoring
    if pipeline_monitoring is not None:
        app.include_router(pipeline_monitoring.router, prefix="/api/v1", tags=["Pipeline Monitoring"])
    
    # Data Explorer (reads data files, but metadata in database)
    from uepi_api.routers import data_explorer
    app.include_router(data_explorer.router, prefix="/api/v1", tags=["Data Explorer"])
    
    # Stage 2 Policy API (always available)
    from uepi_api.routers import policy_stage2
    app.include_router(policy_stage2.router, prefix="/api/v1", tags=["Policy Stage 2"])
    
    # Phase 2: Baselines
    from uepi_api.routers import baselines
    app.include_router(baselines.router, prefix="/api/v1", tags=["Baselines"])

    # Phase 3: Observations
    from uepi_api.routers import observations
    app.include_router(observations.router, prefix="/api/v1", tags=["Observations"])

    # Phase 1: Analytics runs (lineage)
    from uepi_api.routers import analytics_runs
    app.include_router(analytics_runs.router, prefix="/api/v1", tags=["Analytics Runs"])

    # Phase 4: Learning Loop
    from uepi_api.routers import learning
    app.include_router(learning.router, prefix="/api/v1", tags=["Learning"])

    # Phase 5: Traceability (for UI)
    from uepi_api.routers import traceability
    app.include_router(traceability.router, prefix="/api/v1", tags=["Traceability"])
    
    # Data Quality
    from uepi_api.routers import data_quality
    app.include_router(data_quality.router, prefix="/api/v1", tags=["Data Quality"])
    
    from uepi_api.routers import daily_jobs
    app.include_router(daily_jobs.router, prefix="/api/v1", tags=["Daily Jobs"])
    
    # Phase 7: Scenario Accuracy Tracking
    from uepi_api.routers import scenario_accuracy
    app.include_router(scenario_accuracy.router, prefix="/api/v1", tags=["Scenario Accuracy"])
    
    # Phase 8: Advanced Reporting & Exports (already included at line 113 above)
    
    # Phase 9: Executive Dashboards & Automation
    from uepi_api.routers import dashboard
    app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
    
    from uepi_api.routers import schedules
    app.include_router(schedules.router, prefix="/api/v1", tags=["Schedules"])
    
    # Notifications router (Phase 9)
    app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])
    
    # Enterprise Uplift: RBAC (Epic 1) - already included above as "Access"
    # Note: access router uses database models (Role, User) directly
    
    # Enterprise Uplift: Persona Dashboards (Epic 1)
    from uepi_api.routers import dashboards_persona
    app.include_router(dashboards_persona.router, prefix="/api/v1", tags=["Persona Dashboards"])
    
    # Enterprise Uplift: Policy Workspace (Epic 2)
    app.include_router(policy_workspace.router, prefix="/api/v1", tags=["Policy Workspace"])
    
    # Epic 3: Decision Audit & Defensibility
    app.include_router(decisions_workspace.router, prefix="/api/v1", tags=["Decision Workspace"])
    
    # Epic 4: Uncertainty & Risk Visualization
    app.include_router(uncertainty_visualization.router, prefix="/api/v1", tags=["Uncertainty Visualization"])
    
    # Epic 5: Behavioral Signal Detection
    app.include_router(behavior_detection.router, prefix="/api/v1", tags=["Behavior Detection"])
    
    # Epic 6: Collaboration Workflows
    app.include_router(collaboration.router, prefix="/api/v1", tags=["Collaboration"])
    
    # Epic 7: Executive Narrative Layer
    app.include_router(narratives.router, prefix="/api/v1", tags=["Narratives"])
    
    # Conversational Policy Intelligence Layer
    from uepi_api.routers import conversational_ai
    app.include_router(conversational_ai.router, prefix="/api/v1", tags=["Conversational AI"])
    
    # Database Viewer (for admin/developer tools)
    from uepi_api.routers import database_viewer
    app.include_router(database_viewer.router, prefix="/api/v1", tags=["Database Viewer"])
    
    # Data Generation
    from uepi_api.routers import data_generation
    app.include_router(data_generation.router, prefix="/api/v1", tags=["Data Generation"])
    
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
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "status_code": 500},
            headers=headers
        )
    
    # Health check endpoints
    @app.get("/health")
    @app.get("/api/v1/health")
    async def health():
        """Health check endpoint - quick check without database"""
        return {
            "status": "healthy",
            "service": "uepi-api",
            "database": "unknown"  # Don't check database in health endpoint to avoid timeouts
        }
    
    @app.get("/api/v1/health/detailed")
    async def health_detailed():
        """Detailed health check with database connectivity test"""
        from uepi_api.database import SessionLocal
        from sqlalchemy import text
        
        db_status = "unknown"
        try:
            db = SessionLocal()
            try:
                # Quick connection test with timeout
                result = db.execute(text("SELECT 1"))
                result.scalar()
                db_status = "connected"
            except Exception as e:
                db_status = f"error: {str(e)[:100]}"
            finally:
                db.close()
        except Exception as e:
            db_status = f"connection_failed: {str(e)[:100]}"
        
        return {
            "status": "healthy" if db_status == "connected" else "degraded",
            "service": "uepi-api",
            "database": db_status
        }
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        from fastapi import Response
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
    return app


app = create_app()

