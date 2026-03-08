"""Observation models"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    Index,
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


class Observation(Base):
    """Observation of policy impact - stored in database (replaces file-based storage)"""
    __tablename__ = "observations"
    __table_args__ = (
        Index("ix_observations_tenant_policy", "tenant_id", "policy_id"),
        Index("ix_observations_period", "observation_period_start", "observation_period_end"),
        Index("ix_observations_type", "observation_type"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Observation identification
    observation_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    
    # Relationships
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=True, index=True)
    policy_version_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    baseline_version_id = Column(PGUUID(as_uuid=True), ForeignKey("baselines.id", ondelete="SET NULL"), nullable=True, index=True)
    prediction_id = Column(PGUUID(as_uuid=True), ForeignKey("policy_predicted_impacts.id", ondelete="SET NULL"), nullable=True, index=True)
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Data period references
    data_period_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    data_period_ids_json = Column(JSONType, nullable=True)  # Array of data period IDs
    
    # Observation metadata
    observation_type = Column(String, nullable=False, index=True)  # "PERIODIC", "AD_HOC", "TRIGGERED"
    observation_period_start = Column(DateTime, nullable=False, index=True)
    observation_period_end = Column(DateTime, nullable=False, index=True)
    
    # Metrics and comparisons stored as JSONB
    metrics_json = Column(JSONType, nullable=False)  # Observed metrics
    comparisons_json = Column(JSONType, nullable=True)  # vs_baseline, vs_predicted comparisons
    behavioral_explanation_json = Column(JSONType, nullable=True)  # Behavioral analysis

    # Phase 1: run that produced this observation (lineage)
    analytics_run_id = Column(PGUUID(as_uuid=True), ForeignKey("analytics_runs.id", ondelete="SET NULL"), nullable=True, index=True)

    # Phase 2: verdict and recommendation (versioned logic)
    verdict_status = Column(String(32), nullable=True, index=True)  # ON_TRACK | AT_RISK | BACKFIRE | INCONCLUSIVE
    verdict_reason = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    verdict_rule_version = Column(String(32), nullable=True)
    
    # Computation metadata
    computed_at = Column(DateTime, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    policy = relationship("Policy", backref="observations")
    baseline = relationship("Baseline", backref="observations")
    predicted_impact = relationship("PolicyPredictedImpact", backref="observations")
    analysis = relationship("Analysis", backref="observations")
    analytics_run = relationship("AnalyticsRun", backref="observations")

