"""Schedule models"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
    Boolean,
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


class Schedule(Base):
    """Schedule - stored in database (replaces file-based storage)"""
    __tablename__ = "schedules"
    __table_args__ = (
        Index("ix_schedules_tenant", "tenant_id"),
        Index("ix_schedules_enabled", "enabled"),
        Index("ix_schedules_next_run", "next_run_at"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Schedule identification
    schedule_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Schedule configuration
    schedule_type = Column(String, nullable=False)  # "CRON", "INTERVAL", "ONCE", etc.
    cron_expression = Column(String, nullable=True)  # Cron expression if schedule_type is CRON
    interval_seconds = Column(Integer, nullable=True)  # Interval in seconds if schedule_type is INTERVAL
    
    # Schedule target (polymorphic)
    target_type = Column(String, nullable=False)  # "PIPELINE", "ANALYSIS", "BASELINE", etc.
    target_id = Column(String, nullable=False)  # Target ID (string for compatibility)
    
    # Status
    enabled = Column(Boolean, default=True, nullable=False)  # (indexed via __table_args__)
    last_run_at = Column(DateTime, nullable=True, index=True)
    next_run_at = Column(DateTime, nullable=True)  # (indexed via __table_args__)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

