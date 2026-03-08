"""Notification models"""
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, Boolean
from sqlalchemy import UUID as GenericUUID
# Use generic UUID that works with all databases
PGUUID = GenericUUID
from sqlalchemy.orm import relationship

from uepi_api.database import Base


class NotificationType(str, Enum):
    """Notification types"""
    INGESTION_COMPLETE = "INGESTION_COMPLETE"
    INGESTION_FAILED = "INGESTION_FAILED"
    ANALYSIS_COMPLETE = "ANALYSIS_COMPLETE"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    EXPORT_COMPLETE = "EXPORT_COMPLETE"
    EXPORT_FAILED = "EXPORT_FAILED"
    DECISION_DUE = "DECISION_DUE"
    DECISION_OVERDUE = "DECISION_OVERDUE"
    SCORECARD_UPDATE = "SCORECARD_UPDATE"
    SYSTEM_ALERT = "SYSTEM_ALERT"
    USER_MENTION = "USER_MENTION"


class NotificationChannel(str, Enum):
    """Notification channels"""
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    WEBHOOK = "WEBHOOK"


class NotificationPriority(str, Enum):
    """Notification priority"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)  # null = broadcast to all users
    notification_type = Column(String, nullable=False, index=True)
    channel = Column(String, nullable=False, default=NotificationChannel.IN_APP.value)
    priority = Column(String, nullable=False, default=NotificationPriority.MEDIUM.value)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)  # Additional context (links, IDs, etc.) - renamed from 'metadata' to avoid SQLAlchemy conflict
    read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Related entity references (optional)
    related_entity_type = Column(String, nullable=True)  # e.g., "ingestion", "analysis", "export"
    related_entity_id = Column(PGUUID(as_uuid=True), nullable=True)
    
    user = relationship("User", back_populates="notifications")


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Channel preferences
    in_app_enabled = Column(Boolean, default=True, nullable=False)
    email_enabled = Column(Boolean, default=True, nullable=False)
    webhook_enabled = Column(Boolean, default=False, nullable=False)
    webhook_url = Column(String, nullable=True)
    
    # Type-specific preferences (JSON: {type: {channel: enabled}})
    type_preferences = Column(JSON, nullable=True)
    
    # Quiet hours (no notifications during these times)
    quiet_hours_start = Column(String, nullable=True)  # HH:MM format
    quiet_hours_end = Column(String, nullable=True)  # HH:MM format
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="notification_preferences")

