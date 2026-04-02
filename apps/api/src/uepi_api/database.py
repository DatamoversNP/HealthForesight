"""Database configuration and session management - PostgreSQL only"""
import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session as OrmSession
from typing import Generator, Any, Optional

from uepi_api.config import get_settings

# Database-only mode - file storage is disabled
USE_FILE_STORAGE = False

# Lazy engine: do not validate DATABASE_URL or connect at import time.
# Lets the API boot (e.g. /api/v1/ping) when Azure misconfig would previously raise at import → 503 HTML.
_engine: Optional[Any] = None
_SessionLocal: Optional[Any] = None

Base = declarative_base()


def _build_engine():
    settings = get_settings()
    db_url = (settings.database.url or "").strip()
    if not db_url:
        raise ValueError(
            "DATABASE_URL is empty or missing. Set Application Setting DATABASE_URL on the API app "
            "(postgresql://... with sslmode=require for Azure Database for PostgreSQL)."
        )
    if not db_url.startswith("postgresql") and not db_url.startswith("postgresql+psycopg2"):
        raise ValueError(
            "Invalid database URL: expected PostgreSQL connection string starting with "
            "'postgresql://' or 'postgresql+psycopg2://', "
            f"got: {db_url[:80]!r}...\n"
            "Update DATABASE_URL environment variable."
        )
    try:
        st_ms = int(os.environ.get("PG_STATEMENT_TIMEOUT_MS", "10000"))
    except ValueError:
        st_ms = 10000
    st_ms = max(1000, min(st_ms, 600_000))
    return create_engine(
        db_url,
        pool_size=getattr(settings.database, "pool_size", 5),
        max_overflow=getattr(settings.database, "max_overflow", 10),
        echo=getattr(settings.database, "echo", False),
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            "connect_timeout": 5,
            "options": f"-c statement_timeout={st_ms}",
        },
    )


def get_engine():
    """Return the shared SQLAlchemy engine (creates on first use)."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = _build_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


class _LazyEngineProxy:
    """Backward-compatible ``engine`` that resolves on first attribute access."""

    def __getattr__(self, name: str):
        return getattr(get_engine(), name)


engine = _LazyEngineProxy()


class _LazySessionLocal:
    """Callable like sessionmaker; creates factory on first use."""

    def __call__(self, **kwargs):
        get_engine()
        assert _SessionLocal is not None
        return _SessionLocal(**kwargs)

    def __getattr__(self, name: str):
        get_engine()
        assert _SessionLocal is not None
        return getattr(_SessionLocal, name)


SessionLocal = _LazySessionLocal()


def init_db():
    """Initialize database tables"""
    # Import all models to register them with SQLAlchemy
    from uepi_api.models import (  # noqa: F401
        Tenant,
        User,
        Role,
        AuditEvent,
        Policy,
        PolicyVersion,
        PolicyCodeSet,
        PolicyAssumption,
        PolicyGuardrail,
        PolicyChangelog,
        PolicyPredictedImpact,
        Baseline,
        Observation,
        Scenario,
        ScenarioAccuracy,
        Pipeline,
        PipelineRun,
        Risk,
        Forecast,
        DataPeriod,
        ElasticityModel,
        ModelAccuracyHistory,
        BehaviorProfile,
        BehaviorCluster,
        AlertRule,
        AlertEvent,
        Comment,
        Task,
        Approval,
        ActivityEvent,
        Evidence,
        Schedule,
        ExportTemplate,
        ExportPack,
        Ingestion,
        IngestionError,
        Dataset,
        Analysis,
        AnalysisRun,
        AnalysisResultIndex,
        BaselineAnalysisResult,
        AnalysisNarrative,
        AnalysisConfig,
        BaselineAnalysisResult,
        Job,  # Job model for daily job tracking
        ImpactAnalysisResult,
    )
    from uepi_api.models.data_quality import (
        DataQualityReport,
        DataQualityIssue,
    )
    from uepi_api.models.scorecard import (
        Scorecard,
        ScorecardEntry,
    )
    from uepi_api.models.export import (
        Export,
    )
    from uepi_api.models.cohort import (
        Cohort,
    )
    from uepi_api.models.decision import (
        PolicyDecision,
        DecisionAttachment,
    )
    from uepi_api.models.lineage import (
        DatasetSnapshot,
    )
    from uepi_api.models.notification import (
        Notification,
        NotificationPreference,
    )
    from uepi_api.models.canonical_data import (
        ClaimsLineDB,
        EnrollmentRecordDB,
        ProviderRecordDB,
    )
    from uepi_api.models.job import Job
    Base.metadata.create_all(bind=get_engine(), checkfirst=True)


def set_local_statement_timeout(db: OrmSession, milliseconds: int) -> None:
    """Raise Postgres ``statement_timeout`` for the current transaction only (heavy COUNT/analytics)."""
    ms = max(1000, min(int(milliseconds), 600_000))
    db.execute(text(f"SET LOCAL statement_timeout = {ms}"))


def get_db() -> Generator:
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Add tenant_id filtering to all queries (all ORM sessions)
@event.listens_for(OrmSession, "before_flush")
def receive_before_flush(session, flush_context, instances):
    """Ensure tenant_id is set on all entities before flush"""
    for instance in session.new:
        if hasattr(instance, "tenant_id") and instance.tenant_id is None:
            # This should be set by the application layer, but we validate here
            raise ValueError(f"tenant_id must be set on {type(instance).__name__}")
