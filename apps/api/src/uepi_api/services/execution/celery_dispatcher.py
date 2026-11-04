"""Celery-backed JobDispatcher implementing durable outbox + idempotency.

Service Bus adapter will share the same outbox table with destination=service_bus.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from uepi_common.execution.contracts import (
    CancellationRequest,
    JobRecord,
    JobStatus,
    JobSubmitRequest,
    WorkloadClass,
)
from uepi_common.execution.dispatcher import JobDispatcher
from uepi_api.services.execution.outbox import (
    AnalyticalJob,
    OutboxStatus,
    create_job_with_outbox,
    mark_outbox_published,
)


def _to_record(row: AnalyticalJob) -> JobRecord:
    return JobRecord(
        job_id=row.job_id,
        tenant_id=str(row.tenant_id),
        job_type=row.job_type,
        workload_class=WorkloadClass(row.workload_class),
        status=(
            JobStatus(row.status)
            if row.status in {s.value for s in JobStatus}
            else JobStatus.PENDING
        ),
        idempotency_key=row.idempotency_key,
        attempt=row.attempt or 0,
        lease_owner=row.lease_owner,
        lease_expires_at=row.lease_expires_at.isoformat() if row.lease_expires_at else None,
        heartbeat_at=row.heartbeat_at.isoformat() if row.heartbeat_at else None,
        queue_enqueued_at=row.queue_enqueued_at.isoformat() if row.queue_enqueued_at else None,
        started_at=row.started_at.isoformat() if row.started_at else None,
        finished_at=row.finished_at.isoformat() if row.finished_at else None,
        error_category=row.error_category,
        error_message=row.error_message,
        configuration_digest=row.configuration_digest or "",
        cancellation_requested=bool(row.cancellation_requested),
        metadata=row.metadata_json or {},
    )


class CeleryOutboxDispatcher(JobDispatcher):
    """Persists job+outbox, then best-effort publishes to Celery."""

    def __init__(self, db, *, task_name: str = "uepi_worker.tasks.policy_analytics_lifecycle_job"):
        self.db = db
        self.task_name = task_name

    def submit(self, request: JobSubmitRequest) -> JobRecord:
        errs = request.validate()
        if errs:
            raise ValueError("; ".join(errs))

        existing = (
            self.db.query(AnalyticalJob)
            .filter(AnalyticalJob.idempotency_key == request.idempotency_key)
            .first()
        )
        if existing:
            rec = _to_record(existing)
            if existing.status in {JobStatus.SUCCEEDED.value, "COMPLETED", "PROVENANCE_COMPLETED"}:
                rec.status = JobStatus.DUPLICATE_PREVENTED
            else:
                rec.status = JobStatus.DUPLICATE_PREVENTED
            return rec

        job_id = f"aj_{uuid4().hex[:24]}"
        payload = {
            "job_id": job_id,
            "job_type": request.job_type,
            "workload_class": request.workload_class.value,
            "idempotency_key": request.idempotency_key,
            "configuration_digest": request.configuration_digest,
            "payload_ref": request.payload_ref,
            "payload_inline": request.payload_inline or {},
            "dataset_snapshot": request.dataset_snapshot.to_dict() if request.dataset_snapshot else None,
        }
        job = create_job_with_outbox(
            self.db,
            job_id=job_id,
            tenant_id=UUID(request.tenant_id),
            job_type=request.job_type,
            workload_class=request.workload_class.value,
            idempotency_key=request.idempotency_key,
            destination="celery",
            payload=payload,
            configuration_digest=request.configuration_digest,
            dataset_snapshot=request.dataset_snapshot.to_dict() if request.dataset_snapshot else None,
        )
        self.db.commit()

        # Relay: publish outbox immediately (relay loop can also drain PENDING)
        from uepi_api.services.execution.outbox_relay import publish_celery_outbox_row
        from uepi_api.services.execution.outbox import JobOutbox

        row = (
            self.db.query(JobOutbox)
            .filter(
                JobOutbox.job_id == job_id,
                JobOutbox.status == OutboxStatus.PENDING.value,
            )
            .first()
        )
        if row:
            try:
                publish_celery_outbox_row(row, task_name=self.task_name)
                mark_outbox_published(self.db, row)
                self.db.commit()
            except Exception as e:
                row.attempts = (row.attempts or 0) + 1
                row.last_error = str(e)[:500]
                self.db.commit()
        return _to_record(
            self.db.query(AnalyticalJob).filter(AnalyticalJob.job_id == job_id).one()
        )

    def cancel(self, request: CancellationRequest) -> JobRecord:
        job = (
            self.db.query(AnalyticalJob)
            .filter(
                AnalyticalJob.job_id == request.job_id,
                AnalyticalJob.tenant_id == UUID(request.tenant_id),
            )
            .first()
        )
        if not job:
            raise KeyError(request.job_id)
        job.cancellation_requested = True
        if job.status in {"PENDING", "QUEUED"}:
            job.status = JobStatus.CANCELLED.value
            job.finished_at = datetime.utcnow()
        self.db.commit()
        # Hard cancel of RUNNING compute is worker-side (isolated_analytics / pg_terminate)
        return _to_record(job)

    def get(self, job_id: str, tenant_id: str) -> Optional[JobRecord]:
        job = (
            self.db.query(AnalyticalJob)
            .filter(
                AnalyticalJob.job_id == job_id,
                AnalyticalJob.tenant_id == UUID(tenant_id),
            )
            .first()
        )
        return _to_record(job) if job else None
