"""Schedule dispatcher logic (invoked by Azure Container Apps cron Job).

Not wired as Celery Beat. Feature-flagged:
  ENABLE_ENTERPRISE_SCHEDULER=true required to claim due work.

Data-aware: if required_data_watermark is set and not satisfied → DEFERRED.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Callable, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from uepi_api.models.scheduling import JobSchedule, JobScheduleOccurrence


def enterprise_scheduler_enabled() -> bool:
    return os.environ.get("ENABLE_ENTERPRISE_SCHEDULER", "false").lower() in {
        "1",
        "true",
        "yes",
    }


def watermark_satisfied(required: Optional[str], checker: Optional[Callable[[str], bool]]) -> bool:
    if not required:
        return True
    if checker is None:
        return False
    return bool(checker(required))


def claim_due_occurrences(
    db: Session,
    *,
    now: Optional[datetime] = None,
    limit: int = 50,
    watermark_checker: Optional[Callable[[str], bool]] = None,
) -> List[JobScheduleOccurrence]:
    """Transactionally create occurrence rows for due enabled schedules.

    Uniqueness on (schedule_id, occurrence_key, configuration_version) prevents
    duplicate logical runs under concurrent dispatchers.
    """
    if not enterprise_scheduler_enabled():
        return []

    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    due = (
        db.query(JobSchedule)
        .filter(
            JobSchedule.enabled.is_(True),
            JobSchedule.next_due_at.isnot(None),
            JobSchedule.next_due_at <= now,
        )
        .order_by(JobSchedule.priority.asc(), JobSchedule.next_due_at.asc())
        .limit(limit)
        .with_for_update(skip_locked=True)
        .all()
    )
    created: List[JobScheduleOccurrence] = []
    for sched in due:
        occurrence_key = sched.next_due_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        existing = (
            db.query(JobScheduleOccurrence)
            .filter(
                JobScheduleOccurrence.schedule_id == sched.schedule_id,
                JobScheduleOccurrence.occurrence_key == occurrence_key,
                JobScheduleOccurrence.configuration_version == sched.configuration_version,
            )
            .first()
        )
        if existing:
            continue

        ready = watermark_satisfied(sched.required_data_watermark, watermark_checker)
        status = "SCHEDULED" if ready else "DEFERRED_DATA_NOT_READY"
        occ = JobScheduleOccurrence(
            occurrence_id=f"occ_{uuid4().hex[:20]}",
            schedule_id=sched.schedule_id,
            tenant_id=sched.tenant_id,
            occurrence_key=occurrence_key,
            configuration_version=sched.configuration_version,
            status=status,
            due_at_utc=sched.next_due_at,
            data_watermark_satisfied=ready,
        )
        db.add(occ)
        created.append(occ)
        # Advance cursor only when we accepted the occurrence (even if deferred)
        # Simple monthly/daily advance left to caller for expression parsing;
        # mark next_due far future if expression empty to avoid hot loop.
        if not sched.schedule_expression:
            sched.enabled = False
        else:
            # Placeholder: caller/ cron expression engine should set next_due;
            # bump by 1 day to avoid tight loop until engine wired.
            from datetime import timedelta

            sched.next_due_at = (sched.next_due_at or now) + timedelta(days=1)
    db.flush()
    return created
