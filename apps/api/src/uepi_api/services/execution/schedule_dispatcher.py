"""Schedule dispatcher logic (invoked by Azure Container Apps cron Job).

Not wired as Celery Beat. Feature-flagged:
  ENABLE_ENTERPRISE_SCHEDULER=true required to claim due work.

Data-aware: if required_data_watermark is set and not satisfied → DEFERRED.
"""
from __future__ import annotations

import calendar
import os
from datetime import datetime, timedelta, timezone
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
        if not sched.schedule_expression:
            sched.enabled = False
        else:
            sched.next_due_at = _advance_next_due(sched, sched.next_due_at or now)
    db.flush()
    return created


def _advance_next_due(sched: JobSchedule, due: datetime) -> datetime:
    """Advance the cursor without a tight loop.

    ``0 H D * *`` (minute hour day-of-month) is treated as calendar-monthly.
    Anything else stays on the previous +1 day placeholder.
    """
    expr = (sched.schedule_expression or "").split()
    if len(expr) == 5 and expr[2].isdigit() and expr[3] == "*" and expr[4] == "*":
        year, month = due.year, due.month + 1
        if month > 12:
            year, month = year + 1, 1
        day = min(int(expr[2]), calendar.monthrange(year, month)[1])
        hour = int(expr[1]) if expr[1].isdigit() else due.hour
        minute = int(expr[0]) if expr[0].isdigit() else due.minute
        return due.replace(year=year, month=month, day=day, hour=hour, minute=minute, second=0, microsecond=0)
    return due + timedelta(days=1)
