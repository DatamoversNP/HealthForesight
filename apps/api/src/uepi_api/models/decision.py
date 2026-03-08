"""Decision Center models"""
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import UUID as GenericUUID
# Use generic UUID that works with all databases
PGUUID = GenericUUID
from sqlalchemy.orm import relationship

from uepi_api.database import Base


class DecisionStatus(str, Enum):
    """Decision status"""
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    DECIDED = "DECIDED"
    DEFERRED = "DEFERRED"


class RecommendedAction(str, Enum):
    """Recommended actions"""
    KEEP = "KEEP"
    MODIFY = "MODIFY"
    RETIRE = "RETIRE"
    REVIEW = "REVIEW"


class PolicyDecision(Base):
    """Policy decision model"""
    __tablename__ = "policy_decisions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id"), nullable=False, index=True)
    quarter = Column(String, nullable=False, index=True)  # e.g., "2026Q1"
    lob = Column(String, nullable=True, index=True)
    market = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, default=DecisionStatus.OPEN.value, index=True)
    recommended_action = Column(String, nullable=False)  # RecommendedAction enum
    decided_action = Column(String, nullable=True)  # RecommendedAction enum (when decided)
    owner_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    due_date = Column(DateTime, nullable=True)
    decision_rationale_md = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    attachments = relationship("DecisionAttachment", back_populates="decision", cascade="all, delete-orphan")


class DecisionAttachment(Base):
    """Decision attachment (links to exports, external URIs, or uploaded files)"""
    __tablename__ = "decision_attachments"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    decision_id = Column(PGUUID(as_uuid=True), ForeignKey("policy_decisions.id"), nullable=False, index=True)
    export_id = Column(PGUUID(as_uuid=True), ForeignKey("exports.id"), nullable=True)
    external_uri = Column(String, nullable=True)
    file_uri = Column(String, nullable=True)  # Storage URI for uploaded files
    file_name = Column(String, nullable=True)  # Original filename
    file_size_bytes = Column(Integer, nullable=True)
    content_type = Column(String, nullable=True)  # MIME type
    label = Column(String, nullable=False)
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    decision = relationship("PolicyDecision", back_populates="attachments")

