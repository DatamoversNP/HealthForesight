"""Behavior detection models"""
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


class BehaviorProfile(Base):
    """Behavior profile - stored in database (replaces file-based storage)"""
    __tablename__ = "behavior_profiles"
    __table_args__ = (
        Index("ix_behavior_profiles_tenant_member", "tenant_id", "member_id"),
        Index("ix_behavior_profiles_tenant_provider", "tenant_id", "provider_id"),
        Index("ix_behavior_profiles_type", "behavior_type"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Profile identification
    profile_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    behavior_type = Column(String, nullable=False, index=True)  # "UTILIZATION", "COST", "NETWORK", etc.
    
    # Entity references
    member_id = Column(String, nullable=True, index=True)  # Member ID (string for compatibility)
    provider_id = Column(String, nullable=True, index=True)  # Provider ID (string for compatibility)
    
    # Behavior signals stored as JSONB
    signals_json = Column(JSONType, nullable=False)  # Behavior signals/patterns
    
    # Detection metadata
    detected_at = Column(DateTime, nullable=False, index=True)
    confidence = Column(String, nullable=True)  # Confidence level
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Optional cluster reference (simplified - one cluster per profile)
    cluster_id = Column(PGUUID(as_uuid=True), ForeignKey("behavior_clusters.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    cluster = relationship("BehaviorCluster", back_populates="profiles")


class BehaviorCluster(Base):
    """Behavior cluster - stored in database (replaces file-based storage)"""
    __tablename__ = "behavior_clusters"
    __table_args__ = (
        Index("ix_behavior_clusters_tenant_type", "tenant_id", "cluster_type"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Cluster identification
    cluster_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    cluster_type = Column(String, nullable=False, index=True)  # "UTILIZATION", "COST", "NETWORK", etc.
    
    # Cluster data stored as JSONB
    members_json = Column(JSONType, nullable=False)  # Array of member/provider IDs
    characteristics_json = Column(JSONType, nullable=False)  # Cluster characteristics
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships (one-to-many with BehaviorProfile)
    profiles = relationship("BehaviorProfile", back_populates="cluster")

