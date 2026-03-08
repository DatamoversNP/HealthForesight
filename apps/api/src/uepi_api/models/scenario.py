"""Scenario models"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
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


class Scenario(Base):
    """What-if scenario - stored in database (replaces file-based storage)"""
    __tablename__ = "scenarios"
    __table_args__ = (
        Index("ix_scenarios_tenant_policy", "tenant_id", "policy_id"),
        Index("ix_scenarios_name", "name"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Scenario identification
    scenario_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    name = Column(String, nullable=False)  # (indexed via __table_args__)
    description = Column(Text, nullable=True)
    
    # Relationships
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Scenario configuration stored as JSONB
    assumptions_json = Column(JSONType, nullable=False)  # Scenario assumptions/parameters
    results_json = Column(JSONType, nullable=True)  # Scenario results
    
    # Metadata
    scenario_type = Column(String, nullable=True)  # "WHAT_IF", "SENSITIVITY", etc.
    status = Column(String, nullable=False, default="DRAFT", index=True)  # "DRAFT", "RUNNING", "COMPLETED", "FAILED"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    policy = relationship("Policy", backref="scenarios")


class ScenarioAccuracy(Base):
    """Scenario accuracy tracking - stored in database"""
    __tablename__ = "scenario_accuracy"
    __table_args__ = (
        Index("ix_scenario_accuracy_tenant_scenario", "tenant_id", "scenario_id"),
        Index("ix_scenario_accuracy_evaluated_at", "evaluated_at"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    scenario_id = Column(PGUUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Accuracy metrics stored as JSONB
    actual_vs_predicted_json = Column(JSONType, nullable=False)  # Comparison of actual vs predicted
    metrics_json = Column(JSONType, nullable=True)  # Accuracy metrics (MAE, RMSE, etc.)
    
    # Optional: link to policy and observation (for scenario-accuracy flows)
    linked_policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="SET NULL"), nullable=True, index=True)
    linked_at = Column(DateTime, nullable=True)
    observation_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    metadata_json = Column(JSONType, nullable=True)  # predicted_metrics, observed_metrics, accuracy_metrics
    overall_accuracy_pct = Column(Float, nullable=True)
    utilization_accuracy_pct = Column(Float, nullable=True)
    cost_accuracy_pct = Column(Float, nullable=True)
    
    # Evaluation metadata (computed_at alias: use evaluated_at)
    evaluated_at = Column(DateTime, nullable=False)  # (indexed via __table_args__)
    evaluation_period_start = Column(DateTime, nullable=True)
    evaluation_period_end = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    scenario = relationship("Scenario", backref="accuracy_records")

