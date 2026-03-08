"""Alert models"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
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


class AlertRule(Base):
    """Alert rule - stored in database (replaces file-based storage)"""
    __tablename__ = "alert_rules"
    __table_args__ = (
        Index("ix_alert_rules_tenant", "tenant_id"),
        Index("ix_alert_rules_enabled", "enabled"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Rule identification
    rule_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Rule configuration stored as JSONB
    condition_json = Column(JSONType, nullable=False)  # Alert condition logic
    
    # Action configuration
    action = Column(String, nullable=False)  # "EMAIL", "WEBHOOK", "NOTIFICATION", etc.
    action_config_json = Column(JSONType, nullable=True)  # Action configuration
    
    # Status
    enabled = Column(Boolean, default=True, nullable=False)  # (indexed via __table_args__)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    events = relationship("AlertEvent", back_populates="rule", cascade="all, delete-orphan")


class AlertEvent(Base):
    """Alert event - stored in database (replaces file-based storage)"""
    __tablename__ = "alert_events"
    __table_args__ = (
        Index("ix_alert_events_tenant_rule", "tenant_id", "rule_id"),
        Index("ix_alert_events_policy", "policy_id"),
        Index("ix_alert_events_severity", "severity"),
        Index("ix_alert_events_triggered_at", "triggered_at"),
        Index("ix_alert_events_resolved", "resolved_at"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    rule_id = Column(PGUUID(as_uuid=True), ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Event identification
    event_id = Column(String, nullable=False, unique=True, index=True)  # String ID for compatibility
    
    # Event details
    severity = Column(String, nullable=False)  # "LOW", "MEDIUM", "HIGH", "CRITICAL" (indexed via __table_args__)
    details_json = Column(JSONType, nullable=True)  # Event details
    
    # Status
    triggered_at = Column(DateTime, nullable=False)  # (indexed via __table_args__)
    resolved_at = Column(DateTime, nullable=True)  # (indexed via __table_args__)
    resolved_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    rule = relationship("AlertRule", back_populates="events")
    policy = relationship("Policy", backref="alert_events")
    resolved_by = relationship("User", backref="resolved_alerts")

