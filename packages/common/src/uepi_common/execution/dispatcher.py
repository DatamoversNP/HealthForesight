"""Dispatcher protocol — Celery today, Service Bus tomorrow."""
from __future__ import annotations

from typing import Optional, Protocol

from uepi_common.execution.contracts import (
    CancellationRequest,
    JobRecord,
    JobSubmitRequest,
)


class JobDispatcher(Protocol):
    """Queue-agnostic dispatch + cancel surface."""

    def submit(self, request: JobSubmitRequest) -> JobRecord:
        """Persist job metadata then enqueue; return authoritative JobRecord.

        Duplicate idempotency_key must return existing record with
        DUPLICATE_PREVENTED or prior SUCCEEDED — never a second authoritative result.
        """
        ...

    def cancel(self, request: CancellationRequest) -> JobRecord:
        """Request cancellation; hard=True requires compute/DB termination best-effort."""
        ...

    def get(self, job_id: str, tenant_id: str) -> Optional[JobRecord]:
        ...


class ResultPublisher(Protocol):
    """Atomic publication of evidence references into the result index."""

    def publish_atomic(
        self,
        job_id: str,
        tenant_id: str,
        artifact_uri: str,
        checksum_sha256: str,
        evidence_type: str,
        metadata: dict,
    ) -> None:
        """Only mark SUCCEEDED after artifact is durable and checksum verified."""
        ...
