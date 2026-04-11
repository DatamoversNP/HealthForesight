"""Policy models"""
from datetime import datetime
from uuid import UUID, uuid4
import json

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
    Index,
    UniqueConstraint,
    Float,
)
from sqlalchemy import UUID as GenericUUID
# Use generic UUID that works with all databases
PGUUID = GenericUUID
from sqlalchemy.orm import relationship
# Use JSON for database-agnostic support (PostgreSQL will use JSONB under the hood via dialect)
# For explicit JSONB indexing/querying, use postgresql.JSONB in migrations if needed
from sqlalchemy.dialects.postgresql import JSONB

# For PostgreSQL, use JSONB for better performance. For other DBs, fallback to JSON
try:
    JSONType = JSONB  # PostgreSQL-specific JSONB type
except ImportError:
    from sqlalchemy import JSON
    JSONType = JSON  # Fallback for non-PostgreSQL databases

from uepi_api.database import Base
from uepi_common.models import (
    ChangeType,
    CodeType,
    EnforcementStrength,
    PolicyType,
    PolicyStatus,
)


class Policy(Base):
    """Policy model - supports canonical policy structure"""
    __tablename__ = "policies"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    name = Column(String, nullable=False)
    policy_type = Column(String, nullable=False)  # PolicyType enum
    owner_role = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="ACTIVE")  # PolicyStatus enum
    # Store flexible policy structure as JSON (PostgreSQL JSONB for efficient querying)
    # For compound policies, policy_levers, scope, enforcement, etc.
    policy_metadata_json = Column(JSONType, nullable=True)  # JSONB for PostgreSQL, JSON fallback for others
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    versions = relationship("PolicyVersion", back_populates="policy", cascade="all, delete-orphan")


class PolicyVersion(Base):
    """Policy version model - supports enforcement and scope"""
    __tablename__ = "policy_versions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    effective_start_date = Column(DateTime, nullable=False, index=True)
    effective_end_date = Column(DateTime, nullable=True, index=True)
    change_type = Column(String, nullable=False)  # ChangeType enum
    enforcement_strength = Column(String, nullable=False)  # EnforcementStrength enum
    justification = Column(Text, nullable=True)
    # Store version-specific metadata (scope, enforcement details, levers)
    version_metadata_json = Column(JSONType, nullable=True)  # JSONB for PostgreSQL, JSON fallback for others
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    policy = relationship("Policy", back_populates="versions")
    code_sets = relationship("PolicyCodeSet", back_populates="version", cascade="all, delete-orphan")


class PolicyCodeSet(Base):
    """Policy code set (CPT, HCPCS, DRG, revenue codes)"""
    __tablename__ = "policy_code_sets"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    version_id = Column(PGUUID(as_uuid=True), ForeignKey("policy_versions.id"), nullable=False, index=True)
    code_type = Column(String, nullable=False)  # CodeType enum
    code = Column(String, nullable=False, index=True)
    code_group = Column(String, nullable=True, index=True)  # e.g., "MRI_LUMBAR", "ADV_IMAGING"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    version = relationship("PolicyVersion", back_populates="code_sets")


# Database models for Policy Workspace (migrated from file-based storage)
class PolicyAssumption(Base):
    """Policy assumption - stored in database (replaces file-based metadata.assumptions)"""
    __tablename__ = "policy_assumptions"
    __table_args__ = (
        Index("ix_policy_assumptions_tenant_policy", "tenant_id", "policy_id"),
        Index("ix_policy_assumptions_type", "assumption_type"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)
    assumption_type = Column(String, nullable=False)  # e.g., "ELASTICITY", "UTILIZATION", "COST" (indexed via __table_args__)
    description = Column(Text, nullable=True)
    range_json = Column(JSONType, nullable=True)  # ElasticityRange structure (min, max, unit)
    value = Column(String, nullable=True)  # Store as string to handle various types
    source = Column(String, nullable=True)  # Source of assumption
    confidence = Column(Float, nullable=True, default=0.5)  # Confidence level (0.0-1.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    policy = relationship("Policy", backref="assumptions")


class PolicyGuardrail(Base):
    """Policy guardrail - stored in database (replaces file-based metadata.guardrails)"""
    __tablename__ = "policy_guardrails"
    __table_args__ = (
        Index("ix_policy_guardrails_tenant_policy", "tenant_id", "policy_id"),
        Index("ix_policy_guardrails_metric", "metric_name"),
        Index("ix_policy_guardrails_triggered", "triggered"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name = Column(String, nullable=False)  # e.g., "utilization_rate", "cost_per_member" (indexed via __table_args__)
    threshold_type = Column(String, nullable=False)  # "max", "min", "change_pct"
    threshold_value = Column(Float, nullable=False)  # Numeric threshold value
    action = Column(String, nullable=False, default="alert")  # "alert", "block", "notify"
    description = Column(Text, nullable=True)
    triggered = Column(Boolean, default=False, nullable=False)  # (indexed via __table_args__)
    last_checked_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    policy = relationship("Policy", backref="guardrails")


class PolicyChangelog(Base):
    """Policy changelog entry - stored in database (replaces file-based metadata.changelog)"""
    __tablename__ = "policy_changelog"
    __table_args__ = (
        Index("ix_policy_changelog_tenant_policy", "tenant_id", "policy_id"),
        Index("ix_policy_changelog_type", "entry_type"),
        Index("ix_policy_changelog_changed_at", "changed_at"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_type = Column(String, nullable=False)  # "CREATED", "UPDATED", "VERSION_CREATED", "STATUS_CHANGED", etc. (indexed via __table_args__)
    description = Column(Text, nullable=True)
    changed_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # (indexed via __table_args__)
    changes_json = Column(JSONType, nullable=True)  # Detailed change structure (before/after)
    
    policy = relationship("Policy", backref="changelog_entries")
    user = relationship("User", backref="policy_changes")


from uepi_api.models.tenant import User as _User  # noqa: F401

