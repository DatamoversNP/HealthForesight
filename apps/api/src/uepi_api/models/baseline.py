"""Baseline models"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    Integer,
    Boolean,
    Index,
    UniqueConstraint,
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


class Baseline(Base):
    """Baseline metrics - stored in database (replaces file-based storage)"""
    __tablename__ = "baselines"
    __table_args__ = (
        Index("ix_baselines_tenant_policy", "tenant_id", "policy_id"),
        Index("ix_baselines_type", "baseline_type"),
        Index("ix_baselines_window", "window_start_date", "window_end_date"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Baseline identification
    baseline_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    version = Column(Integer, nullable=False, default=1)
    baseline_type = Column(String, nullable=False, index=True)  # "ROLLING", "FIXED", "CUSTOM"
    
    # Time window
    window_start_date = Column(DateTime, nullable=False, index=True)
    window_end_date = Column(DateTime, nullable=False, index=True)
    
    # Relationships
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="SET NULL"), nullable=True, index=True)
    parent_baseline_id = Column(PGUUID(as_uuid=True), ForeignKey("baselines.id", ondelete="SET NULL"), nullable=True)
    
    # Data period references (stored as JSON array of IDs)
    data_period_ids_json = Column(JSONType, nullable=True)  # Array of data period IDs

    # Phase 1: run that produced this baseline (lineage)
    analytics_run_id = Column(PGUUID(as_uuid=True), ForeignKey("analytics_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Metrics stored as JSONB
    baseline_metrics_json = Column(JSONType, nullable=False)  # All baseline metrics
    
    # Computation metadata
    computed_at = Column(DateTime, nullable=False, index=True)
    computed_by = Column(String, nullable=True)  # User/system that computed
    
    # Shift detection
    shift_detected = Column(Boolean, default=False, nullable=False, index=True)
    shift_summary_json = Column(JSONType, nullable=True)  # Shift detection details
    refresh_reason = Column(String, nullable=True)  # "NEW_DATA", "SHIFT_DETECTED", etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    policy = relationship("Policy", backref="baselines")
    parent_baseline = relationship("Baseline", remote_side=[id], backref="child_baselines")
    analytics_run = relationship("AnalyticsRun", backref="baselines")

