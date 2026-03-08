"""Risk models"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    Index,
    Float,
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


class Risk(Base):
    """Policy risk register - stored in database (replaces file-based storage)"""
    __tablename__ = "risks"
    __table_args__ = (
        Index("ix_risks_tenant_policy", "tenant_id", "policy_id"),
        Index("ix_risks_driver", "risk_driver"),
        Index("ix_risks_status", "status"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Risk identification
    risk_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    risk_driver = Column(String, nullable=False)  # Risk driver name/type (indexed via __table_args__)
    
    # Risk assessment
    probability = Column(Float, nullable=False)  # 0.0-1.0
    impact = Column(String, nullable=False)  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    risk_score = Column(Float, nullable=True)  # Calculated risk score
    
    # Risk details stored as JSONB
    description = Column(Text, nullable=True)
    mitigation_json = Column(JSONType, nullable=True)  # Mitigation strategies
    impact_details_json = Column(JSONType, nullable=True)  # Detailed impact description
    
    # Status
    status = Column(String, nullable=False, default="OPEN")  # "OPEN", "MITIGATED", "ACCEPTED", "CLOSED" (indexed via __table_args__)
    
    # Ownership
    owner_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    mitigated_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    policy = relationship("Policy", backref="risks")
    owner = relationship("User", backref="owned_risks")

