"""Export template models"""
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


class ExportTemplate(Base):
    """Export template - stored in database (replaces file-based storage)"""
    __tablename__ = "export_templates"
    __table_args__ = (
        Index("ix_export_templates_tenant", "tenant_id"),
        Index("ix_export_templates_type", "template_type"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Template identification
    template_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Template configuration stored as JSONB
    template_type = Column(String, nullable=False, index=True)  # "PDF", "PPTX", "EXCEL", "CSV", etc.
    configuration_json = Column(JSONType, nullable=False)  # Template configuration
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ExportPack(Base):
    """Export pack (collection of exports) - stored in database (replaces file-based storage)"""
    __tablename__ = "export_packs"
    __table_args__ = (
        Index("ix_export_packs_tenant", "tenant_id"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Pack identification
    pack_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Exports stored as JSONB array of export IDs
    exports_json = Column(JSONType, nullable=False)  # Array of export IDs
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

