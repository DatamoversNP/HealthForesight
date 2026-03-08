"""Export models"""
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import UUID as GenericUUID
from sqlalchemy.orm import relationship
# Use generic UUID that works with all databases
PGUUID = GenericUUID

from uepi_api.database import Base


class ExportType(str, Enum):
    """Export types"""
    PDF = "PDF"
    PPTX = "PPTX"
    AUDIT_PACK = "AUDIT_PACK"


class ExportStatus(str, Enum):
    """Export status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Export(Base):
    """Export model"""
    __tablename__ = "exports"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey("analyses.id"), nullable=True, index=True)
    export_type = Column(String, nullable=False)  # ExportType enum
    status = Column(String, nullable=False, default=ExportStatus.PENDING.value, index=True)
    file_uri = Column(String, nullable=True)  # S3 URI to generated file
    file_size_bytes = Column(Integer, nullable=True)
    download_count = Column(Integer, default=0, nullable=False)
    version_number = Column(Integer, default=1, nullable=False, index=True)  # Version number (1-based)
    parent_export_id = Column(PGUUID(as_uuid=True), ForeignKey("exports.id"), nullable=True)  # Parent export for versioning
    change_description = Column(Text, nullable=True)  # Description of changes in this version
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationship for version history
    parent_export_rel = relationship("Export", remote_side=[id], foreign_keys=[parent_export_id], backref="child_versions")

