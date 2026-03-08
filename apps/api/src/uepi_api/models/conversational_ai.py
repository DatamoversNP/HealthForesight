"""Data models for Conversational Policy Intelligence Layer"""
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean, JSON
from sqlalchemy import UUID as GenericUUID
from sqlalchemy.orm import relationship

from uepi_api.database import Base

PGUUID = GenericUUID


class ConversationMode(str, Enum):
    """Conversational AI modes"""
    DRAFT = "DRAFT"  # AI proposes configurations
    EXPLAIN = "EXPLAIN"  # AI explains system outputs
    QUERY = "QUERY"  # AI queries existing data/models


class ConversationDomain(str, Enum):
    """Conversational AI domains"""
    POLICY = "POLICY"  # Policy creation & modification
    DATA = "DATA"  # Data onboarding & ingestion
    BASELINE = "BASELINE"  # Baseline creation & explanation
    IMPACT = "IMPACT"  # Observed impact analysis
    GOVERNANCE = "GOVERNANCE"  # Decision & governance support


class ConversationStatus(str, Enum):
    """Conversation status"""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class Conversation(Base):
    """Conversation session model"""
    __tablename__ = "conversations"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    title = Column(String, nullable=True)  # Auto-generated from first message
    mode = Column(String, nullable=False)  # ConversationMode
    domain = Column(String, nullable=True)  # ConversationDomain
    status = Column(String, nullable=False, default=ConversationStatus.ACTIVE.value)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")
    artifacts = relationship("ConversationArtifact", back_populates="conversation", cascade="all, delete-orphan")


class ConversationMessage(Base):
    """Individual message in a conversation"""
    __tablename__ = "conversation_messages"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(PGUUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    structured_data = Column(JSON, nullable=True)  # Parsed structured output
    message_metadata = Column(JSON, nullable=True)  # Additional metadata (renamed from 'metadata' to avoid SQLAlchemy conflict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    conversation = relationship("Conversation", back_populates="messages")


class ConversationArtifact(Base):
    """Structured artifacts generated from conversations"""
    __tablename__ = "conversation_artifacts"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(PGUUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    artifact_type = Column(String, nullable=False)  # "POLICY_DRAFT", "PIPELINE_CONFIG", "BASELINE_CONFIG", etc.
    artifact_data = Column(JSON, nullable=False)  # The structured artifact
    status = Column(String, nullable=False, default="DRAFT")  # DRAFT, SUBMITTED, APPROVED, REJECTED
    workflow_entry_id = Column(PGUUID(as_uuid=True), nullable=True)  # Link to workflow if submitted
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    conversation = relationship("Conversation", back_populates="artifacts")


class ConversationAuditLog(Base):
    """Audit log for all conversational AI actions"""
    __tablename__ = "conversation_audit_logs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_roles = Column(JSON, nullable=False)  # Array of role names
    conversation_id = Column(PGUUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)
    action_type = Column(String, nullable=False)  # "MESSAGE", "ARTIFACT_CREATED", "ARTIFACT_SUBMITTED", etc.
    prompt = Column(Text, nullable=True)
    ai_response = Column(Text, nullable=True)
    structured_output = Column(JSON, nullable=True)
    generated_artifacts = Column(JSON, nullable=True)  # Array of artifact IDs
    downstream_workflow_entry = Column(PGUUID(as_uuid=True), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    conversation = relationship("Conversation")

