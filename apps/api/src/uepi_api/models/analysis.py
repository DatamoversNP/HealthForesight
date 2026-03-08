"""Analysis models"""
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Index
from sqlalchemy import UUID as GenericUUID
# Use generic UUID that works with all databases
PGUUID = GenericUUID
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

try:
    JSONType = JSONB
except ImportError:
    from sqlalchemy import JSON
    JSONType = JSON

from uepi_api.database import Base


class AnalysisStatus(str, Enum):
    """Analysis status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisType(str, Enum):
    """Analysis types"""
    IMPACT = "IMPACT"
    SIMULATE = "SIMULATE"
    SUBSTITUTION = "SUBSTITUTION"
    PROVIDER_SEGMENTATION = "PROVIDER_SEGMENTATION"
    ELASTICITY = "ELASTICITY"


class Analysis(Base):
    """Analysis model"""
    __tablename__ = "analyses"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id"), nullable=True, index=True)
    analysis_type = Column(String, nullable=False)  # AnalysisType enum
    name = Column(String, nullable=True)  # User-provided name for the analysis
    status = Column(String, nullable=False, default=AnalysisStatus.PENDING.value, index=True)
    error_message = Column(Text, nullable=True)  # Set by worker when status is FAILED
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        # Unique constraint: name must be unique per tenant per analysis_type
        # This allows same name for different analysis types but not for same type
        UniqueConstraint('tenant_id', 'analysis_type', 'name', name='uq_analysis_name_per_tenant_type'),
    )
    
    config = relationship("AnalysisConfig", back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    runs = relationship("AnalysisRun", back_populates="analysis", cascade="all, delete-orphan")
    narratives = relationship("AnalysisNarrative", back_populates="analysis", cascade="all, delete-orphan")
    result_index = relationship("AnalysisResultIndex", back_populates="analysis", cascade="all, delete-orphan")


class AnalysisConfig(Base):
    """Analysis configuration (filters, control groups, etc.)"""
    __tablename__ = "analysis_configs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False, unique=True, index=True)
    treatment_filters = Column(JSON, nullable=False)  # FilterSpec
    control_filters = Column(JSON, nullable=True)  # FilterSpec (optional)
    matching_strategy = Column(String, nullable=True)  # e.g., "DID", "PRE_POST", "MATCHED"
    pre_window_months = Column(Integer, default=6, nullable=False)
    post_window_months = Column(Integer, default=6, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    analysis = relationship("Analysis", back_populates="config")


class AnalysisRun(Base):
    """Analysis run (execution instance)"""
    __tablename__ = "analysis_runs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False, index=True)
    snapshot_id = Column(PGUUID(as_uuid=True), ForeignKey("dataset_snapshots.id", name="fk_analysis_run_snapshot"), nullable=True, index=True)
    status = Column(String, nullable=False, index=True)
    model_version = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    metrics = Column(JSON, nullable=True)  # Duration, record counts, etc.
    logs_uri = Column(String, nullable=True)  # S3 URI to logs
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    analysis = relationship("Analysis", back_populates="runs")


class AnalysisResultIndex(Base):
    """Index of analysis results stored in object storage"""
    __tablename__ = "analysis_results_index"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False, index=True)
    result_type = Column(String, nullable=False)  # e.g., "SUMMARY", "TIMESERIES", "SUBSTITUTION", "PROVIDER_SEGMENTATION"
    data_uri = Column(String, nullable=True)  # S3 URI to Parquet or JSON (optional if stored in DB)
    schema_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    analysis = relationship("Analysis", back_populates="result_index")


class BaselineAnalysisResult(Base):
    """Full baseline analysis results stored in database"""
    __tablename__ = "baseline_analysis_results"
    __table_args__ = (
        Index("ix_baseline_results_analysis", "analysis_id"),
        Index("ix_baseline_results_tenant", "tenant_id"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Full result data stored as JSONB
    result_data_json = Column(JSONType, nullable=False)  # Complete BaselineAnalysisResult as JSON
    
    # Metadata
    schema_version = Column(String, nullable=True, default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    analysis = relationship("Analysis", backref="baseline_result")


class ImpactAnalysisResult(Base):
    """Full policy impact analysis results stored in database"""
    __tablename__ = "impact_analysis_results"
    __table_args__ = (
        Index("ix_impact_results_analysis", "analysis_id"),
        Index("ix_impact_results_tenant", "tenant_id"),
        Index("ix_impact_results_policy", "policy_id"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id"), nullable=True, index=True)
    
    # Full result data stored as JSONB
    result_data_json = Column(JSONType, nullable=False)  # Complete impact analysis result as JSON
    
    # Metadata
    schema_version = Column(String, nullable=True, default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    analysis = relationship("Analysis", backref="impact_result")


class WhatIfScenarioResult(Base):
    """Full what-if scenario analysis results stored in database"""
    __tablename__ = "whatif_scenario_results"
    __table_args__ = (
        Index("ix_whatif_results_analysis", "analysis_id"),
        Index("ix_whatif_results_tenant", "tenant_id"),
        Index("ix_whatif_results_policy", "policy_id"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id"), nullable=True, index=True)
    
    # Full result data stored as JSONB
    result_data_json = Column(JSONType, nullable=False)  # Complete ScenarioResult as JSON
    
    # Metadata
    schema_version = Column(String, nullable=True, default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    analysis = relationship("Analysis", backref="whatif_result")


class ElasticityAnalysisResult(Base):
    """Full elasticity analysis results stored in database"""
    __tablename__ = "elasticity_analysis_results"
    __table_args__ = (
        Index("ix_elasticity_results_analysis", "analysis_id"),
        Index("ix_elasticity_results_tenant", "tenant_id"),
        Index("ix_elasticity_results_policy", "policy_id"),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id"), nullable=True, index=True)

    result_data_json = Column(JSONType, nullable=False)

    schema_version = Column(String, nullable=True, default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    analysis = relationship("Analysis", backref="elasticity_result")


class AnalysisNarrative(Base):
    """Analysis narrative (editable, versioned)"""
    __tablename__ = "analysis_narratives"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    content_md = Column(Text, nullable=False)
    generated_by = Column(String, nullable=False)  # "SYSTEM" or "USER"
    locked = Column(String, default="false", nullable=False)  # Using String for compatibility
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    analysis = relationship("Analysis", back_populates="narratives")

