"""Idempotency key construction for durable analytical jobs."""
from __future__ import annotations

import hashlib


def make_idempotency_key(
    *,
    tenant_id: str,
    policy_id: str,
    configuration_digest: str,
    analysis_type: str,
    dataset_snapshot_version: str,
    cohort_window: str,
) -> str:
    raw = "|".join(
        [
            tenant_id,
            policy_id,
            configuration_digest,
            analysis_type,
            dataset_snapshot_version,
            cohort_window,
        ]
    )
    return "idem_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]
