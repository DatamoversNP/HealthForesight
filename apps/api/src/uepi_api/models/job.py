"""Job status tracking model"""
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, JSON, String, Text
from sqlalchemy import UUID as GenericUUID
PGUUID = GenericUUID

from uepi_api.database import Base


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Job(Base):
    """Job status tracking model"""
    __tablename__ = "jobs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(String, nullable=False, unique=True, index=True)  # External job ID
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    job_type = Column(String, nullable=False)  # e.g., "daily_data_and_observations"
    status = Column(String, nullable=False, default=JobStatus.PENDING.value, index=True)
    message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)  # Additional job metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
