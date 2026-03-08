"""Collaboration models"""
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


class Comment(Base):
    """Comment - stored in database (replaces file-based storage)"""
    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comments_tenant_resource", "tenant_id", "resource_type", "resource_id"),
        Index("ix_comments_user", "user_id"),
        Index("ix_comments_created_at", "created_at"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Resource reference (polymorphic)
    resource_type = Column(String, nullable=False, index=True)  # "POLICY", "ANALYSIS", "OBSERVATION", etc.
    resource_id = Column(String, nullable=False, index=True)  # Resource ID (string for compatibility)
    
    # Comment content
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)  # Indexed via __table_args__
    content = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # Indexed via __table_args__
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", backref="comments")


class Task(Base):
    """Task - stored in database (replaces file-based storage)"""
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_tenant_resource", "tenant_id", "resource_type", "resource_id"),
        Index("ix_tasks_assigned_to", "assigned_to_user_id"),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_due_date", "due_date"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Resource reference (polymorphic)
    resource_type = Column(String, nullable=False, index=True)  # "POLICY", "ANALYSIS", etc.
    resource_id = Column(String, nullable=False, index=True)  # Resource ID (string for compatibility)
    
    # Task details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    assigned_to_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Indexed via __table_args__
    status = Column(String, nullable=False, default="OPEN")  # "OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED" (indexed via __table_args__)
    due_date = Column(DateTime, nullable=True)  # (indexed via __table_args__)
    priority = Column(String, nullable=True)  # "LOW", "MEDIUM", "HIGH", "URGENT"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    assigned_to = relationship("User", backref="assigned_tasks")


class Approval(Base):
    """Approval - stored in database (replaces file-based storage)"""
    __tablename__ = "approvals"
    __table_args__ = (
        Index("ix_approvals_tenant_resource", "tenant_id", "resource_type", "resource_id"),
        Index("ix_approvals_status", "status"),
        Index("ix_approvals_requested_by", "requested_by_user_id"),
        Index("ix_approvals_approved_by", "approved_by_user_id"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Resource reference (polymorphic)
    resource_type = Column(String, nullable=False, index=True)  # "POLICY", "ANALYSIS", etc.
    resource_id = Column(String, nullable=False, index=True)  # Resource ID (string for compatibility)
    
    # Approval details
    requested_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)  # Indexed via __table_args__
    approved_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Indexed via __table_args__
    status = Column(String, nullable=False, default="PENDING")  # "PENDING", "APPROVED", "REJECTED", "CANCELLED" (indexed via __table_args__)
    reason = Column(Text, nullable=True)
    
    # Timestamps
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    approved_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    requested_by = relationship("User", foreign_keys=[requested_by_user_id], backref="requested_approvals")
    approved_by = relationship("User", foreign_keys=[approved_by_user_id], backref="approved_approvals")


class ActivityEvent(Base):
    """Activity event - stored in database (replaces file-based storage)"""
    __tablename__ = "activity_events"
    __table_args__ = (
        Index("ix_activity_events_tenant_resource", "tenant_id", "resource_type", "resource_id"),
        Index("ix_activity_events_user", "user_id"),
        Index("ix_activity_events_action", "action"),
        Index("ix_activity_events_created_at", "created_at"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Resource reference (polymorphic)
    resource_type = Column(String, nullable=False, index=True)  # "POLICY", "ANALYSIS", etc.
    resource_id = Column(String, nullable=False, index=True)  # Resource ID (string for compatibility)
    
    # Activity details
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Indexed via __table_args__
    action = Column(String, nullable=False)  # "CREATED", "UPDATED", "DELETED", "VIEWED", etc. (indexed via __table_args__)
    details_json = Column(JSONType, nullable=True)  # Additional activity details
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # Indexed via __table_args__
    
    # Relationships
    user = relationship("User", backref="activity_events")

