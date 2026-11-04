"""Durable analytical execution contracts (queue-agnostic).

Celery (current) and Service Bus + Container Apps Jobs (target) both implement
these interfaces. Business calculation semantics stay outside this package.
"""
from uepi_common.execution.contracts import (
    WorkloadClass,
    DatasetSnapshotRef,
    JobSubmitRequest,
    JobRecord,
    JobStatus,
    ResultArtifactRef,
    EvidenceType,
    CancellationRequest,
    CacheIdentity,
)
from uepi_common.execution.idempotency import make_idempotency_key
from uepi_common.execution.scheduling import (
    ScheduleDefinition,
    ScheduleOccurrence,
    ScheduleTriggerKind,
    OverlapPolicy,
    MisfirePolicy,
    OccurrenceStatus,
)

__all__ = [
    "WorkloadClass",
    "DatasetSnapshotRef",
    "JobSubmitRequest",
    "JobRecord",
    "JobStatus",
    "ResultArtifactRef",
    "EvidenceType",
    "CancellationRequest",
    "CacheIdentity",
    "make_idempotency_key",
    "ScheduleDefinition",
    "ScheduleOccurrence",
    "ScheduleTriggerKind",
    "OverlapPolicy",
    "MisfirePolicy",
    "OccurrenceStatus",
]
