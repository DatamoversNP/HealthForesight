"""Enqueue one observation job per active policy for the previous calendar month.

Used by the lean-staging monthly schedule. Writes analytical_jobs + job_outbox
in one transaction; the existing outbox relay publishes them. Does not compute
observations inline.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import UUID

from uepi_api.models.policy import Policy
from uepi_api.services.execution.outbox import create_job_with_outbox


def previous_month(now: datetime | None = None) -> tuple[int, int]:
    now = now or datetime.now(timezone.utc)
    if now.month == 1:
        return now.year - 1, 12
    return now.year, now.month - 1


def enqueue_monthly_observations(tenant_id: UUID, *, now: datetime | None = None) -> int:
    """Return how many new jobs were inserted (existing idempotency keys are skipped)."""
    from uepi_api.database import SessionLocal

    year, month = previous_month(now)
    period = f"{year:04d}-{month:02d}"
    destination = "service_bus" if os.environ.get("AZURE_SERVICE_BUS_CONNECTION_STRING") else "celery"

    db = SessionLocal()
    inserted = 0
    try:
        policy_ids = [
            row[0]
            for row in db.query(Policy.id)
            .filter(Policy.tenant_id == tenant_id, Policy.status == "ACTIVE")
            .all()
        ]
        for policy_id in policy_ids:
            job_id = f"aj_obs_{period}_{policy_id}"
            idem = f"monthly-obs:{tenant_id}:{policy_id}:{period}"
            from uepi_api.services.execution.outbox import AnalyticalJob

            if db.query(AnalyticalJob).filter(AnalyticalJob.idempotency_key == idem).first():
                continue
            create_job_with_outbox(
                db,
                job_id=job_id,
                tenant_id=tenant_id,
                job_type="PERIODIC_OBSERVATION",
                workload_class="OBSERVATION",
                idempotency_key=idem,
                destination=destination,
                payload={
                    "job_id": job_id,
                    "tenant_id": str(tenant_id),
                    "workload_class": "OBSERVATION",
                    "idempotency_key": idem,
                    "policy_id": str(policy_id),
                    "period": period,
                    "payload_inline": {
                        "policy_id": str(policy_id),
                        "period": period,
                        "pathway": "PERIODIC_MONTHLY",
                    },
                },
                configuration_digest=f"monthly-obs-{period}",
                metadata={"source": "monthly_observations", "period": period},
            )
            inserted += 1
        db.commit()
        return inserted
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
