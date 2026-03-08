"""Predicted Impact models"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    Index,
    Float,
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


class PolicyPredictedImpact(Base):
    """Policy predicted impact - stored in database (replaces file-based storage)"""
    __tablename__ = "policy_predicted_impacts"
    __table_args__ = (
        Index("ix_predicted_impact_tenant_policy", "tenant_id", "policy_id"),
        Index("ix_predicted_impact_predicted_at", "predicted_at"),
        UniqueConstraint("tenant_id", "policy_id", "predicted_at", name="uq_predicted_impact_tenant_policy_date"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Metrics stored as JSONB for flexibility
    metrics_json = Column(JSONType, nullable=False)  # utilization_change_per_1k, cost_change_pmpm, etc.
    
    # Metadata
    model_version = Column(String, nullable=True)  # Version of prediction model used
    confidence = Column(Float, nullable=True)  # Overall confidence (0.0-1.0)
    predicted_at = Column(DateTime, nullable=False, index=True)  # When prediction was made
    prediction_method = Column(String, nullable=True)  # "ELASTICITY", "HISTORICAL", "ML", etc.
    
    # Relationships
    baseline_id = Column(PGUUID(as_uuid=True), ForeignKey("baselines.id", ondelete="SET NULL"), nullable=True, index=True)
    data_period_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)  # Data period used for prediction
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    policy = relationship("Policy", backref="predicted_impacts")
    baseline = relationship("Baseline", backref="predicted_impacts")

