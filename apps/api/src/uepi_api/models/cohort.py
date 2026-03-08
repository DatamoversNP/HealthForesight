"""Cohort models"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy import UUID as GenericUUID
# Use generic UUID that works with all databases
PGUUID = GenericUUID
from sqlalchemy.orm import relationship

from uepi_api.database import Base


class Cohort(Base):
    """Saved cohort (filter specification)"""
    __tablename__ = "cohorts"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    filters_json = Column(JSON, nullable=False)  # FilterSpec canonical format
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

