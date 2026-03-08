"""Learning/ML models"""
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


class ElasticityModel(Base):
    """Elasticity model - stored in database (replaces file-based storage)"""
    __tablename__ = "elasticity_models"
    __table_args__ = (
        Index("ix_elasticity_models_tenant_policy", "tenant_id", "policy_id"),
        Index("ix_elasticity_models_type", "model_type"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Model identification
    model_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    model_type = Column(String, nullable=False, index=True)  # "LINEAR", "LOGISTIC", "NEURAL_NET", etc.
    
    # Model data stored as JSONB
    parameters_json = Column(JSONType, nullable=False)  # Model parameters
    accuracy_metrics_json = Column(JSONType, nullable=True)  # Accuracy metrics (R², MAE, etc.)
    
    # Training metadata
    trained_at = Column(DateTime, nullable=False, index=True)
    training_data_period_id = Column(PGUUID(as_uuid=True), nullable=True)
    model_version = Column(String, nullable=True)
    
    # Status
    status = Column(String, nullable=False, default="ACTIVE", index=True)  # "ACTIVE", "DEPRECATED", "ARCHIVED"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    policy = relationship("Policy", backref="elasticity_models")
    accuracy_history = relationship("ModelAccuracyHistory", back_populates="model", cascade="all, delete-orphan")


class ModelAccuracyHistory(Base):
    """Model accuracy evaluation history - stored in database"""
    __tablename__ = "model_accuracy_history"
    __table_args__ = (
        Index("ix_model_accuracy_tenant_model", "tenant_id", "model_id"),
        Index("ix_model_accuracy_evaluation_date", "evaluation_date"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    model_id = Column(PGUUID(as_uuid=True), ForeignKey("elasticity_models.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Evaluation data stored as JSONB
    metrics_json = Column(JSONType, nullable=False)  # Evaluation metrics (R², MAE, RMSE, etc.)
    
    # Evaluation metadata
    evaluation_date = Column(DateTime, nullable=False, index=True)
    evaluation_data_period_id = Column(PGUUID(as_uuid=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    model = relationship("ElasticityModel", back_populates="accuracy_history")

