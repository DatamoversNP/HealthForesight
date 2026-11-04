"""Unit tests for durable execution contracts (no Azure provisioning)."""
from uepi_common.execution import (
    CacheIdentity,
    DatasetSnapshotRef,
    EvidenceType,
    JobSubmitRequest,
    WorkloadClass,
    make_idempotency_key,
)
from uepi_common.execution.contracts import ResultArtifactRef


def test_idempotency_key_stable():
    a = make_idempotency_key(
        tenant_id="t1",
        policy_id="p1",
        configuration_digest="abc",
        analysis_type="EMPIRICAL_COHORT",
        dataset_snapshot_version="v9",
        cohort_window="2025-01-01:2025-12-31",
    )
    b = make_idempotency_key(
        tenant_id="t1",
        policy_id="p1",
        configuration_digest="abc",
        analysis_type="EMPIRICAL_COHORT",
        dataset_snapshot_version="v9",
        cohort_window="2025-01-01:2025-12-31",
    )
    assert a == b
    assert a.startswith("idem_")


def test_submit_request_rejects_large_inline_payload():
    req = JobSubmitRequest(
        tenant_id="t1",
        job_type="policy_analytics",
        workload_class=WorkloadClass.ASYNC_COHORT,
        idempotency_key="k1",
        payload_inline={"blob": "x" * 40_000},
    )
    errs = req.validate()
    assert any("payload_inline too large" in e for e in errs)


def test_dataset_snapshot_ref_is_reference_only():
    ref = DatasetSnapshotRef(
        uri="abfss://claims@lake/tenant/t1/snap/v1",
        checksum_sha256="deadbeef",
        format="delta",
        version="v1",
        tenant_id="t1",
        row_estimate=3_500_000,
    )
    d = ref.to_dict()
    assert "uri" in d and "rows" not in d


def test_cache_identity_includes_tenant_snapshot_config():
    cid = CacheIdentity(
        tenant_id="t1",
        dataset_snapshot_version="v1",
        configuration_digest="cfg",
        analysis_type="whatif",
        cohort_window="w",
    )
    assert "t1" in cid.key() and "v1" in cid.key() and "cfg" in cid.key()


def test_result_artifact_evidence_types():
    art = ResultArtifactRef(
        uri="abfss://results@lake/j1.json",
        checksum_sha256="abc",
        content_type="application/json",
        evidence_type=EvidenceType.BLOCKED_PREFLIGHT_RESULT,
    )
    assert art.to_dict()["evidence_type"] == "BLOCKED_PREFLIGHT_RESULT"
