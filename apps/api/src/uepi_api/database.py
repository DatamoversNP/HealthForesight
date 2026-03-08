"""Database configuration and session management - PostgreSQL only"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Generator

from uepi_api.config import get_settings

settings = get_settings()

# Database-only mode - file storage is disabled
USE_FILE_STORAGE = False

# Database mode - PostgreSQL required
db_url = settings.database.url

# Validate that we're using PostgreSQL
if not db_url.startswith("postgresql") and not db_url.startswith("postgresql+psycopg2"):
    raise ValueError(
        f"Invalid database URL: expected PostgreSQL connection string starting with 'postgresql://' or 'postgresql+psycopg2://', "
        f"got: {db_url[:50]}...\n"
        "This application requires PostgreSQL. Update DATABASE_URL environment variable."
    )

# Create engine with connection pooling and timeouts
engine = create_engine(
    db_url,
    pool_size=getattr(settings.database, 'pool_size', 5),
    max_overflow=getattr(settings.database, 'max_overflow', 10),
    echo=getattr(settings.database, 'echo', False),
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    connect_args={
        "connect_timeout": 5,  # 5 second connection timeout (reduced from 10)
        "options": "-c statement_timeout=10000",  # 10 second query timeout (reduced from 30)
    },
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


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
    Base.metadata.create_all(bind=engine, checkfirst=True)


def get_db() -> Generator:
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Add tenant_id filtering to all queries
@event.listens_for(SessionLocal, "before_flush")
def receive_before_flush(session, flush_context, instances):
    """Ensure tenant_id is set on all entities before flush"""
    for instance in session.new:
        if hasattr(instance, "tenant_id") and instance.tenant_id is None:
            # This should be set by the application layer, but we validate here
            raise ValueError(f"tenant_id must be set on {type(instance).__name__}")
