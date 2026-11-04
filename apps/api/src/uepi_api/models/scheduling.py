"""PostgreSQL schedule registry + occurrence ledger.

STAGING / enterprise path. Do NOT enable dispatcher against Dec4 demo until
Phase A freeze + staging validation. Demo DB must remain at alembic ≤012
unless separately authorized.
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    JSON,
)
from sqlalchemy import UUID as GenericUUID

from uepi_api.database import Base

PGUUID = GenericUUID


class JobSchedule(Base):
    __tablename__ = "job_schedules"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    schedule_id = Column(String, nullable=False, unique=True, index=True)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    job_type = Column(String, nullable=False, index=True)
    target_reference = Column(String, nullable=False)
    schedule_expression = Column(String, nullable=True)
    timezone = Column(String, nullable=False, default="UTC")
    enabled = Column(Boolean, nullable=False, default=False)  # default OFF
    trigger_kind = Column(String, nullable=False, default="CALENDAR")
    effective_start = Column(DateTime, nullable=True)
    effective_end = Column(DateTime, nullable=True)
    next_due_at = Column(DateTime, nullable=True, index=True)
    misfire_policy = Column(String, nullable=False, default="FIRE_ONCE")
    overlap_policy = Column(String, nullable=False, default="SKIP")
    retry_policy_json = Column(JSON, nullable=True)
    execution_budget_s = Column(Integer, nullable=False, default=3600)
    required_data_watermark = Column(String, nullable=True)
    priority = Column(Integer, nullable=False, default=5)
    configuration_version = Column(String, nullable=False, default="v1")
    workload_class = Column(String, nullable=False, default="OBSERVATION")
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class JobScheduleOccurrence(Base):
    __tablename__ = "job_schedule_occurrences"
    __table_args__ = (
        UniqueConstraint(
            "schedule_id",
            "occurrence_key",
            "configuration_version",
            name="uq_schedule_occurrence_identity",
        ),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    occurrence_id = Column(String, nullable=False, unique=True, index=True)
    schedule_id = Column(String, nullable=False, index=True)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    occurrence_key = Column(String, nullable=False)
    configuration_version = Column(String, nullable=False, default="v1")
    status = Column(String, nullable=False, index=True)
    due_at_utc = Column(DateTime, nullable=False)
    data_watermark_satisfied = Column(Boolean, nullable=True)
    analytical_job_id = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
