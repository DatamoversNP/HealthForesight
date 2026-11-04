"""Reconciliation gate — explains readiness without inventing evidence."""
from uepi_api.services.policy_reconciliation_gate import reconcile_policy_version


def test_forecast_without_observation_is_limited_not_ready_verdict():
    row = reconcile_policy_version(
        policy={"id": "r1", "name": "Modifier Edit", "policy_type": "CODING_AND_BILLING"},
        inventory_family="bcnc_commercial_reimbursement",
        inventory_status="CATALOG_ROWS_PRESENT_UNRECONCILED",
        source_provenance=None,
        applicability=None,
        has_baseline=False,
        has_forecast=True,
        forecast_evidence_tier="ELASTICITY_MODEL",
        has_observation=False,
        observation_verdict=None,
        causal_status="NOT_ESTIMABLE",
    )
    assert row["states"]["verdict_state"] == "LIMITED"
    assert "Forecast ≠ observed" in row["explanations"]["verdict"] or "forecast" in row["explanations"]["verdict"].lower()
    assert row["states"]["readiness_flags"]["OBSERVATION_READY"] is False
    assert row["never_invent"] is True
    assert row["mechanism_family"] == "REIMBURSEMENT"


def test_observation_verdict_ready_when_present():
    row = reconcile_policy_version(
        policy={"id": "m1", "name": "MRI PA", "policy_type": "PRIOR_AUTH"},
        inventory_family="bcnc_medical",
        inventory_status="PARTIAL_CATALOG_SEED",
        source_provenance={"status": "CATALOG", "id": "demo"},
        applicability={"status": "COMMERCIAL_NC"},
        has_baseline=True,
        has_forecast=True,
        forecast_evidence_tier="A",
        has_observation=True,
        observation_verdict="ON_TRACK",
        causal_status="INCONCLUSIVE",
        causal_limitations=["No production DiD on claims"],
    )
    assert row["states"]["verdict_state"] == "READY"
    assert row["states"]["causal_status"] == "INCONCLUSIVE"
    assert row["states"]["readiness_flags"]["IMPACT_ASSESSABLE"] is False
