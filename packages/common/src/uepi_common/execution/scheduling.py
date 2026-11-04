"""Enterprise schedule registry contracts (data-aware, calendar + event).

Authoritative schedule definitions live in PostgreSQL. Azure Container Apps
scheduled Jobs only wake a dispatcher — they are not per-policy crons.
Celery Beat is NOT the long-term authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ScheduleTriggerKind(str, Enum):
    CALENDAR = "CALENDAR"
    DATA_EVENT = "DATA_EVENT"
    DEPENDENCY = "DEPENDENCY"
    MANUAL = "MANUAL"
    RECOVERY = "RECOVERY"


class OverlapPolicy(str, Enum):
    SKIP = "SKIP"
    QUEUE = "QUEUE"
    REPLACE = "REPLACE"


class MisfirePolicy(str, Enum):
    FIRE_ONCE = "FIRE_ONCE"
    FIRE_ALL = "FIRE_ALL"
    SKIP = "SKIP"


class OccurrenceStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    DISPATCHED = "DISPATCHED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"
    DEFERRED_DATA_NOT_READY = "DEFERRED_DATA_NOT_READY"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


@dataclass
class ScheduleDefinition:
    schedule_id: str
    tenant_id: str
    job_type: str
    target_reference: str
    schedule_expression: str  # cron or RRULE; empty if event-only
    timezone: str  # IANA
    enabled: bool = True
    trigger_kind: ScheduleTriggerKind = ScheduleTriggerKind.CALENDAR
    effective_start: Optional[str] = None
    effective_end: Optional[str] = None
    next_due_at: Optional[str] = None
    misfire_policy: MisfirePolicy = MisfirePolicy.FIRE_ONCE
    overlap_policy: OverlapPolicy = OverlapPolicy.SKIP
    retry_policy_json: Dict[str, Any] = field(default_factory=lambda: {"max": 3, "backoff_s": 60})
    execution_budget_s: int = 3600
    required_data_watermark: Optional[str] = None  # e.g. claims_snapshot>=vN
    priority: int = 5
    configuration_version: str = "v1"
    workload_class: str = "OBSERVATION"

    def validate(self) -> List[str]:
        errs: List[str] = []
        if not self.schedule_id or not self.tenant_id or not self.job_type:
            errs.append("schedule_id, tenant_id, job_type required")
        if self.trigger_kind == ScheduleTriggerKind.CALENDAR and not self.schedule_expression:
            errs.append("calendar schedules require schedule_expression")
        if not self.timezone:
            errs.append("IANA timezone required")
        return errs

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["trigger_kind"] = self.trigger_kind.value
        d["misfire_policy"] = self.misfire_policy.value
        d["overlap_policy"] = self.overlap_policy.value
        return d


@dataclass
class ScheduleOccurrence:
    """Exactly one logical occurrence per (schedule_id, occurrence_key, configuration_version)."""

    occurrence_id: str
    schedule_id: str
    tenant_id: str
    occurrence_key: str  # e.g. 2026-11-04T00:00:00Z period id
    configuration_version: str
    status: OccurrenceStatus
    due_at_utc: str
    data_watermark_satisfied: Optional[bool] = None
    analytical_job_id: Optional[str] = None
    error_message: Optional[str] = None
