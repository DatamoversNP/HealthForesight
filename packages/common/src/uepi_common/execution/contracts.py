"""Stable interfaces for job submission, execution, cancellation, and results.

Storage rule: large claims/results live in object/lake storage; messages and
PostgreSQL rows carry immutable references only (URI, checksum, version).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class WorkloadClass(str, Enum):
    """Separate concurrency and resource budgets per class."""

    INTERACTIVE = "INTERACTIVE"  # low-latency bounded recalculation
    ASYNC_COHORT = "ASYNC_COHORT"  # asynchronous cohort / policy analytics
    HEAVY_DISTRIBUTED = "HEAVY_DISTRIBUTED"  # Databricks-scale simulation


class JobStatus(str, Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    DEAD_LETTER = "DEAD_LETTER"
    DUPLICATE_PREVENTED = "DUPLICATE_PREVENTED"


class EvidenceType(str, Enum):
    EMPIRICAL_ANALYTICAL_RESULT = "EMPIRICAL_ANALYTICAL_RESULT"
    SYNTHETIC_ANALYTICAL_RESULT = "SYNTHETIC_ANALYTICAL_RESULT"
    PROVENANCE_RESULT = "PROVENANCE_RESULT"
    BLOCKED_PREFLIGHT_RESULT = "BLOCKED_PREFLIGHT_RESULT"


@dataclass(frozen=True)
class DatasetSnapshotRef:
    """Immutable reference to a claims/reference snapshot — never embed rows."""

    uri: str
    checksum_sha256: str
    format: str  # e.g. delta, parquet, postgres_extract
    version: str
    tenant_id: str
    row_estimate: Optional[int] = None
    partition_keys: tuple = ()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResultArtifactRef:
    """Published analytical evidence pointer (ADLS/Delta or blob)."""

    uri: str
    checksum_sha256: str
    content_type: str
    evidence_type: EvidenceType
    bytes_estimate: Optional[int] = None
    schema_version: str = "v1"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["evidence_type"] = self.evidence_type.value
        return d


@dataclass(frozen=True)
class CacheIdentity:
    """Cache keys must include tenant, snapshot, and configuration digest."""

    tenant_id: str
    dataset_snapshot_version: str
    configuration_digest: str
    analysis_type: str
    cohort_window: str

    def key(self) -> str:
        return "|".join(
            [
                self.tenant_id,
                self.dataset_snapshot_version,
                self.configuration_digest,
                self.analysis_type,
                self.cohort_window,
            ]
        )


@dataclass
class JobSubmitRequest:
    tenant_id: str
    job_type: str
    workload_class: WorkloadClass
    idempotency_key: str
    dataset_snapshot: Optional[DatasetSnapshotRef] = None
    configuration_digest: str = ""
    payload_ref: Optional[str] = None  # URI to small JSON params in object storage
    payload_inline: Optional[Dict[str, Any]] = None  # only small metadata
    timeout_s: Optional[int] = None
    priority: int = 5

    def validate(self) -> List[str]:
        errs: List[str] = []
        if not self.tenant_id:
            errs.append("tenant_id required")
        if not self.job_type:
            errs.append("job_type required")
        if not self.idempotency_key:
            errs.append("idempotency_key required")
        if self.payload_inline and len(str(self.payload_inline)) > 32_000:
            errs.append("payload_inline too large — use payload_ref / ADLS")
        return errs


@dataclass
class JobRecord:
    job_id: str
    tenant_id: str
    job_type: str
    workload_class: WorkloadClass
    status: JobStatus
    idempotency_key: str
    attempt: int = 0
    lease_owner: Optional[str] = None
    lease_expires_at: Optional[str] = None
    heartbeat_at: Optional[str] = None
    queue_enqueued_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error_category: Optional[str] = None
    error_message: Optional[str] = None
    result_artifact: Optional[ResultArtifactRef] = None
    dataset_snapshot: Optional[DatasetSnapshotRef] = None
    configuration_digest: str = ""
    cancellation_requested: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["workload_class"] = self.workload_class.value
        d["status"] = self.status.value
        if self.result_artifact:
            d["result_artifact"] = self.result_artifact.to_dict()
        if self.dataset_snapshot:
            d["dataset_snapshot"] = self.dataset_snapshot.to_dict()
        return d


@dataclass(frozen=True)
class CancellationRequest:
    job_id: str
    tenant_id: str
    reason: str = ""
    hard: bool = True  # propagate to DB/compute terminate
