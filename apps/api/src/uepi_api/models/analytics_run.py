"""Analytics run model - Phase 1: lineage and reproducibility.

Records each execution of baseline, prediction, or observation computation
with input refs and output refs so "what produced this?" is answerable.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text, Index
from sqlalchemy import UUID as PGUUID
from sqlalchemy.dialects.postgresql import JSONB

try:
    JSONType = JSONB
except ImportError:
    from sqlalchemy import JSON
    JSONType = JSON

from uepi_api.database import Base


class AnalyticsRun(Base):
    """Run of a baseline, prediction, or observation computation.

    run_type: BASELINE | PREDICTION | OBSERVATION
    input_refs: { policy_id?, baseline_id?, data_period_id?, data_period_ids?, analysis_id?, config_hash? }
    output_refs: { baseline_id? | predicted_impact_id? | observation_id? }
    """
    __tablename__ = "analytics_runs"
    __table_args__ = (
        Index("ix_analytics_runs_tenant_type", "tenant_id", "run_type"),
        Index("ix_analytics_runs_status", "status"),
        Index("ix_analytics_runs_started_at", "started_at"),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    run_type = Column(String(32), nullable=False, index=True)  # BASELINE | PREDICTION | OBSERVATION
    status = Column(String(32), nullable=False, default="RUNNING")  # RUNNING | COMPLETED | FAILED; ix in __table_args__
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Input refs for reproducibility (policy_id, baseline_id, data_period_id, analysis_id, etc.)
    input_refs_json = Column(JSONType, nullable=True)
    # Config snapshot (e.g. window dates, options) for determinism
    config_snapshot_json = Column(JSONType, nullable=True)
    # Output refs: produced baseline_id, predicted_impact_id, or observation_id
    output_refs_json = Column(JSONType, nullable=True)

    triggered_by_user_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
