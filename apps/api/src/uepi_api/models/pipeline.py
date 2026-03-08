"""Pipeline models"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    Index,
    Boolean,
)
from sqlalchemy import UUID as GenericUUID
PGUUID = GenericUUID
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

try:
    JSONType = JSONB
except ImportError:
    from sqlalchemy import JSON
    JSONType = JSON

from uepi_api.database import Base


class Pipeline(Base):
    """Data pipeline definition - stored in database (replaces file-based storage)"""
    __tablename__ = "pipelines"
    __table_args__ = (
        Index("ix_pipelines_tenant_name", "tenant_id", "name"),
        Index("ix_pipelines_status", "status"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Pipeline identification
    pipeline_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Pipeline configuration stored as JSONB
    steps_json = Column(JSONType, nullable=False)  # Pipeline steps/configuration
    schedule_json = Column(JSONType, nullable=True)  # Schedule configuration (cron, etc.)
    
    # Status
    status = Column(String, nullable=False, default="ACTIVE")  # "ACTIVE", "PAUSED", "ARCHIVED" (indexed via __table_args__)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    
    # Metadata
    pipeline_type = Column(String, nullable=True)  # "INGESTION", "TRANSFORMATION", "ANALYSIS", etc.
    version = Column(String, nullable=True, default="1.0")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    runs = relationship("PipelineRun", back_populates="pipeline", cascade="all, delete-orphan")


class PipelineRun(Base):
    """Pipeline execution run - stored in database (replaces file-based storage)"""
    __tablename__ = "pipeline_runs"
    __table_args__ = (
        Index("ix_pipeline_runs_tenant_pipeline", "tenant_id", "pipeline_id"),
        Index("ix_pipeline_runs_status", "status"),
        Index("ix_pipeline_runs_started_at", "started_at"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    pipeline_id = Column(PGUUID(as_uuid=True), ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Run identification
    run_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    
    # Status
    status = Column(String, nullable=False)  # "PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED" (indexed via __table_args__)
    
    # Execution metadata
    started_at = Column(DateTime, nullable=True)  # (indexed via __table_args__)
    ended_at = Column(DateTime, nullable=True, index=True)
    logs_uri = Column(String, nullable=True)  # URI to logs (S3, blob storage, etc.)
    
    # Metrics stored as JSONB
    metrics_json = Column(JSONType, nullable=True)  # Duration, record counts, errors, etc.
    error_details_json = Column(JSONType, nullable=True)  # Error details if failed
    
    # Trigger information
    triggered_by = Column(String, nullable=True)  # "SCHEDULE", "MANUAL", "API", etc.
    triggered_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    pipeline = relationship("Pipeline", back_populates="runs")
    user = relationship("User", backref="pipeline_runs")

