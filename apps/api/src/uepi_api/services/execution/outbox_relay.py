"""Outbox relay: PENDING rows → Celery (compat) or Service Bus (lean/enterprise target)."""
from __future__ import annotations

import json
import os
from typing import Optional

from uepi_api.services.execution.outbox import JobOutbox, list_pending_outbox, mark_outbox_published


def queue_for_workload(workload_class: str) -> str:
    """Map workload class to Service Bus queue name (lean staging Standard)."""
    wc = (workload_class or "").upper()
    if wc in {"INTERACTIVE", "SYNC"}:
        return "interactive"
    return "policy-analytics"


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


def publish_service_bus_outbox_row(
    row: JobOutbox,
    *,
    connection_string: Optional[str] = None,
) -> str:
    """Publish one outbox row to Azure Service Bus Standard/Premium.

    Requires ``azure-servicebus`` and ``AZURE_SERVICE_BUS_CONNECTION_STRING``
    (or explicit connection_string). Staging must never use demo namespace.
    """
    from azure.servicebus import ServiceBusClient, ServiceBusMessage

    cs = connection_string or os.environ.get("AZURE_SERVICE_BUS_CONNECTION_STRING")
    if not cs:
        raise RuntimeError(
            "AZURE_SERVICE_BUS_CONNECTION_STRING required for destination=service_bus"
        )

    payload = dict(row.payload_json or {})
    payload.setdefault("job_id", row.job_id)
    payload.setdefault("tenant_id", str(row.tenant_id))
    workload = str(payload.get("workload_class") or "ASYNC_COHORT")
    queue = queue_for_workload(workload)
    body = json.dumps(payload, default=str)
    message_id = payload.get("idempotency_key") or row.job_id

    with ServiceBusClient.from_connection_string(cs) as client:
        with client.get_queue_sender(queue) as sender:
            msg = ServiceBusMessage(body, message_id=str(message_id)[:128])
            sender.send_messages(msg)
    return f"sb:{queue}:{message_id}"


def drain_pending_outbox(db, *, limit: int = 50, task_name: Optional[str] = None) -> dict:
    task_name = task_name or "uepi_worker.tasks.policy_analytics_lifecycle_job"
    published = 0
    failed = 0
    skipped = 0
    for row in list_pending_outbox(db, limit=limit):
        try:
            if row.destination == "celery":
                publish_celery_outbox_row(row, task_name=task_name)
            elif row.destination == "service_bus":
                publish_service_bus_outbox_row(row)
            else:
                skipped += 1
                continue
            mark_outbox_published(db, row)
            published += 1
        except Exception as e:
            row.attempts = (row.attempts or 0) + 1
            row.last_error = str(e)[:500]
            failed += 1
    db.commit()
    return {"published": published, "failed": failed, "skipped": skipped}
