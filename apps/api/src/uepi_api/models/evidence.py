"""Evidence models"""
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


class Evidence(Base):
    """Evidence document - stored in database (replaces file-based storage)"""
    __tablename__ = "evidence"
    __table_args__ = (
        Index("ix_evidence_tenant_resource", "tenant_id", "resource_type", "resource_id"),
        Index("ix_evidence_type", "evidence_type"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Resource reference (polymorphic)
    resource_type = Column(String, nullable=False, index=True)  # "POLICY", "ANALYSIS", etc.
    resource_id = Column(String, nullable=False, index=True)  # Resource ID (string for compatibility)
    
    # Evidence details
    evidence_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    evidence_type = Column(String, nullable=False, index=True)  # "DOCUMENT", "CHART", "DATA_EXPORT", etc.
    uri = Column(String, nullable=False)  # URI to evidence (S3, blob storage, etc.)
    metadata_json = Column(JSONType, nullable=True)  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

