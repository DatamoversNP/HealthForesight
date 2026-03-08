"""Audit logging models"""
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, JSON, String, Text
from sqlalchemy import UUID as GenericUUID
# Use generic UUID that works with all databases
PGUUID = GenericUUID

from uepi_api.database import Base


class AuditAction(str, Enum):
    """Audit action types"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VIEW = "VIEW"
    EXPORT = "EXPORT"
    DOWNLOAD = "DOWNLOAD"


class AuditEvent(Base):
    """Audit event log"""
    __tablename__ = "audit_events"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    object_type = Column(String, nullable=False, index=True)
    object_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    diff_summary = Column(JSON, nullable=True)  # Summary of changes
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    metadata_json = Column(JSON, nullable=True)  # Additional context - renamed from 'metadata' to avoid SQLAlchemy conflict

