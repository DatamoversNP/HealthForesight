"""Scorecard models"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Float, Integer, JSON, String, Text
from sqlalchemy import UUID as GenericUUID
# Use generic UUID that works with all databases
PGUUID = GenericUUID
from sqlalchemy.orm import relationship

from uepi_api.database import Base


class Scorecard(Base):
    """Scorecard model (policy effectiveness index)"""
    __tablename__ = "scorecards"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id"), nullable=False, index=True)
    period = Column(String, nullable=False, index=True)  # e.g., "2026-Q1"
    # Nullable when predicted impact lacks attributed % / confidence (UNESTIMATED).
    effectiveness_index = Column(Float, nullable=True)  # 0-100 composite score, or null
    cost_impact_score = Column(Float, nullable=True)
    behavioral_risk_score = Column(Float, nullable=True)
    access_impact_score = Column(Float, nullable=True)
    regulatory_defensibility_score = Column(Float, nullable=True)
    weights = Column(JSON, nullable=True)  # Tenant-specific weights
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    entries = relationship("ScorecardEntry", back_populates="scorecard", cascade="all, delete-orphan")


class ScorecardEntry(Base):
    """Scorecard entry (detailed breakdown)"""
    __tablename__ = "scorecard_entries"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    scorecard_id = Column(PGUUID(as_uuid=True), ForeignKey("scorecards.id"), nullable=False, index=True)
    dimension = Column(String, nullable=False)  # e.g., "COST", "BEHAVIORAL", "ACCESS", "REGULATORY"
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=True)  # null when measure is unavailable
    metric_unit = Column(String, nullable=True)
    trend = Column(String, nullable=True)  # e.g., "UP", "DOWN", "STABLE"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    scorecard = relationship("Scorecard", back_populates="entries")

