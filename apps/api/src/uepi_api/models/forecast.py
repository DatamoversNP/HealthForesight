"""Forecast models"""
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


class Forecast(Base):
    """Forecast - stored in database (replaces file-based storage)"""
    __tablename__ = "forecasts"
    __table_args__ = (
        Index("ix_forecasts_tenant_policy", "tenant_id", "policy_id"),
        Index("ix_forecasts_forecast_date", "forecast_date"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Forecast identification
    forecast_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    
    # Forecast data stored as JSONB
    projections_json = Column(JSONType, nullable=False)  # Forecast projections
    confidence_intervals_json = Column(JSONType, nullable=True)  # Confidence intervals
    
    # Forecast metadata
    forecast_date = Column(DateTime, nullable=False)  # Date forecast was made (indexed via __table_args__)
    forecast_horizon = Column(String, nullable=True)  # "1M", "3M", "6M", "1Y", etc.
    forecast_method = Column(String, nullable=True)  # "TIME_SERIES", "ML", "ELASTICITY", etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    policy = relationship("Policy", backref="forecasts")

