"""Transactional outbox for durable job dispatch.

Pattern: write job row + outbox row in one DB transaction; a relay publishes
to the broker (Celery/Service Bus). Prevents "queued but not recorded" and
"recorded but never queued" splits.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean
from sqlalchemy import JSON
from sqlalchemy import UUID as GenericUUID

from uepi_api.database import Base

PGUUID = GenericUUID


class OutboxStatus(str, Enum):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class AnalyticalJob(Base):
    """Authoritative job-state store (extends beyond legacy jobs table)."""

    __tablename__ = "analytical_jobs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(String, nullable=False, unique=True, index=True)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    job_type = Column(String, nullable=False, index=True)
    workload_class = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    idempotency_key = Column(String, nullable=False, unique=True, index=True)
    attempt = Column(Integer, nullable=False, default=0)
    lease_owner = Column(String, nullable=True)
    lease_expires_at = Column(DateTime, nullable=True)
    heartbeat_at = Column(DateTime, nullable=True)
    queue_enqueued_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error_category = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    configuration_digest = Column(String, nullable=True)
    dataset_snapshot_json = Column(JSON, nullable=True)
    result_artifact_json = Column(JSON, nullable=True)
    cancellation_requested = Column(Boolean, nullable=False, default=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class JobOutbox(Base):
    """Outbox rows relayed to Celery / Service Bus."""

    __tablename__ = "job_outbox"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(String, nullable=False, index=True)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    destination = Column(String, nullable=False)  # celery | service_bus
    payload_json = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default=OutboxStatus.PENDING.value, index=True)
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)


def create_job_with_outbox(
    db,
    *,
    job_id: str,
    tenant_id,
    job_type: str,
    workload_class: str,
    idempotency_key: str,
    destination: str,
    payload: Dict[str, Any],
    configuration_digest: str = "",
    dataset_snapshot: Optional[dict] = None,
    metadata: Optional[dict] = None,
) -> AnalyticalJob:
    """Insert AnalyticalJob + PENDING outbox atomically (caller commits)."""
    existing = (
        db.query(AnalyticalJob)
        .filter(AnalyticalJob.idempotency_key == idempotency_key)
        .first()
    )
    if existing:
        return existing

    job = AnalyticalJob(
        job_id=job_id,
        tenant_id=tenant_id,
        job_type=job_type,
        workload_class=workload_class,
        status="PENDING",
        idempotency_key=idempotency_key,
        configuration_digest=configuration_digest,
        dataset_snapshot_json=dataset_snapshot,
        metadata_json=metadata or {},
    )
    outbox = JobOutbox(
        job_id=job_id,
        tenant_id=tenant_id,
        destination=destination,
        payload_json=payload,
        status=OutboxStatus.PENDING.value,
    )
    db.add(job)
    db.add(outbox)
    return job


def list_pending_outbox(db, limit: int = 50) -> List[JobOutbox]:
    return (
        db.query(JobOutbox)
        .filter(JobOutbox.status == OutboxStatus.PENDING.value)
        .order_by(JobOutbox.created_at.asc())
        .limit(limit)
        .all()
    )


def mark_outbox_published(db, row: JobOutbox) -> None:
    row.status = OutboxStatus.PUBLISHED.value
    row.published_at = datetime.utcnow()
    job = db.query(AnalyticalJob).filter(AnalyticalJob.job_id == row.job_id).first()
    if job and job.status == "PENDING":
        job.status = "QUEUED"
        job.queue_enqueued_at = datetime.utcnow()
