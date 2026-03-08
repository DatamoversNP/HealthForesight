"""Data Period models"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    Index,
    UniqueConstraint,
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


class DataPeriod(Base):
    """Data period definition - stored in database (replaces file-based storage)"""
    __tablename__ = "data_periods"
    __table_args__ = (
        Index("ix_data_periods_tenant", "tenant_id"),
        Index("ix_data_periods_period", "period_start_date", "period_end_date"),
        UniqueConstraint("tenant_id", "period_id", name="uq_data_period_tenant_period"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Period identification
    period_id = Column(String, nullable=False, index=True)  # String ID for compatibility
    name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    # Time period
    period_start_date = Column(DateTime, nullable=False, index=True)
    period_end_date = Column(DateTime, nullable=False, index=True)
    
    # Data snapshot reference
    data_snapshot_id = Column(PGUUID(as_uuid=True), ForeignKey("dataset_snapshots.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Metadata stored as JSONB
    metadata_json = Column(JSONType, nullable=True)  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    data_snapshot = relationship("DatasetSnapshot", backref="data_periods")

