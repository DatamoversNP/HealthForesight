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
    effectiveness_index = Column(Float, nullable=False)  # 0-100 composite score
    cost_impact_score = Column(Float, nullable=False)
    behavioral_risk_score = Column(Float, nullable=False)
    access_impact_score = Column(Float, nullable=False)
    regulatory_defensibility_score = Column(Float, nullable=False)
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
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String, nullable=True)
    trend = Column(String, nullable=True)  # e.g., "UP", "DOWN", "STABLE"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    scorecard = relationship("Scorecard", back_populates="entries")

