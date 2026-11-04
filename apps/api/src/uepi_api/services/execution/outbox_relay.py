"""Outbox relay: PENDING rows → Celery (now) or Service Bus (Wave 2+)."""
from __future__ import annotations

from typing import Optional

from uepi_api.services.execution.outbox import JobOutbox, list_pending_outbox, mark_outbox_published


def publish_celery_outbox_row(row: JobOutbox, *, task_name: str) -> str:
    from uepi_api.celery_client import send_task

    payload = row.payload_json or {}
    # Map to existing lifecycle task kwargs when present
    kwargs = {
        "job_id": payload.get("job_id") or row.job_id,
        "policy_id": (payload.get("payload_inline") or {}).get("policy_id")
        or payload.get("policy_id")
        or "00000000-0000-0000-0000-000000000000",
        "pathway": (payload.get("payload_inline") or {}).get("pathway") or "PROVENANCE_ONLY",
        "configuration_digest": payload.get("configuration_digest") or "",
        "cohort_count": int((payload.get("payload_inline") or {}).get("cohort_count") or 0),
    }
    queue = "policy_analytics"
    ar = send_task(task_name, kwargs=kwargs, queue=queue)
    return str(ar.id)


def drain_pending_outbox(db, *, limit: int = 50, task_name: Optional[str] = None) -> dict:
    task_name = task_name or "uepi_worker.tasks.policy_analytics_lifecycle_job"
    published = 0
    failed = 0
    for row in list_pending_outbox(db, limit=limit):
        if row.destination != "celery":
            # service_bus path deferred until Azure module authorized
            continue
        try:
            publish_celery_outbox_row(row, task_name=task_name)
            mark_outbox_published(db, row)
            published += 1
        except Exception as e:
            row.attempts = (row.attempts or 0) + 1
            row.last_error = str(e)[:500]
            failed += 1
    db.commit()
    return {"published": published, "failed": failed}
