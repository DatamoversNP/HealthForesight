"""Ingestion models"""
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy import UUID as GenericUUID
# Use generic UUID that works with all databases
PGUUID = GenericUUID
from sqlalchemy.orm import relationship

from uepi_api.database import Base


class IngestionStatus(str, Enum):
    """Ingestion status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class IngestionType(str, Enum):
    """Ingestion types"""
    CLAIMS = "CLAIMS"
    ENROLLMENT = "ENROLLMENT"
    PROVIDERS = "PROVIDERS"
    BENEFIT_DESIGN = "BENEFIT_DESIGN"


class Ingestion(Base):
    """Ingestion job model"""
    __tablename__ = "ingestions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    ingestion_type = Column(String, nullable=False)  # IngestionType enum
    status = Column(String, nullable=False, default=IngestionStatus.PENDING.value, index=True)
    manifest_uri = Column(String, nullable=False)  # S3 URI to manifest JSON
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    metadata_json = Column(JSON, nullable=True)  # Additional context - renamed from 'metadata' to avoid SQLAlchemy conflict
    
    errors = relationship("IngestionError", back_populates="ingestion", cascade="all, delete-orphan")


class IngestionError(Base):
    """Ingestion error details"""
    __tablename__ = "ingestion_errors"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    ingestion_id = Column(PGUUID(as_uuid=True), ForeignKey("ingestions.id"), nullable=False, index=True)
    error_type = Column(String, nullable=False)  # e.g., "SCHEMA_ERROR", "VALIDATION_ERROR"
    error_message = Column(Text, nullable=False)
    row_number = Column(Integer, nullable=True)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    ingestion = relationship("Ingestion", back_populates="errors")


class Dataset(Base):
    """Dataset metadata (available claim months, LOB, markets)"""
    __tablename__ = "datasets"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    dataset_type = Column(String, nullable=False)  # IngestionType enum
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    lob = Column(String, nullable=True, index=True)
    market = Column(String, nullable=True, index=True)
    record_count = Column(Integer, nullable=True)
    data_uri = Column(String, nullable=False)  # S3 URI to curated Parquet
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

