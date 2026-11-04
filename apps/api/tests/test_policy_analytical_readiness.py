"""Analytical readiness flags — never invent decision-grade metrics."""
from uepi_api.services.policy_analytical_readiness import (
    build_portfolio_readiness,
    compute_policy_readiness,
)


def test_reimbursement_not_modeled_as_utilization_reduction():
    r = compute_policy_readiness(
        policy={"id": "1", "name": "Modifier Edit", "policy_type": "CODING_AND_BILLING"},
        has_baseline=False,
        has_forecast=False,
        has_observation=False,
        causal_supported=False,
    )
    assert r["mechanism_family"] == "REIMBURSEMENT"
    assert "allowed_paid_unit_price" in r["primary_metrics"]
    assert "utilization reduction" in r["measurement_note"].lower() or "unit price" in r["measurement_note"].lower()
    assert r["flags"]["IMPACT_ASSESSABLE"] is False
    assert r["causal_status"] == "NOT_ESTIMABLE"


def test_observation_without_causal_design_is_inconclusive_not_supported():
    r = compute_policy_readiness(
        policy={"id": "2", "name": "Old LCD", "policy_type": "MEDICAL_NECESSITY"},
        has_baseline=True,
        has_forecast=True,
        has_observation=True,
        causal_supported=False,
    )
    assert r["flags"]["OBSERVATION_READY"] is True
    assert r["flags"]["IMPACT_ASSESSABLE"] is False
    assert r["causal_status"] == "INCONCLUSIVE"


def test_portfolio_totals_from_sets_only():
    out = build_portfolio_readiness(
        policies=[
            {"id": "a", "name": "A", "policy_type": "PRIOR_AUTH"},
            {"id": "b", "name": "B", "policy_type": "CODING_AND_BILLING"},
        ],
        baseline_policy_ids={"a"},
        forecast_policy_ids={"a"},
        observation_policy_ids={"a"},
        impact_assessable_ids=set(),
    )
    assert out["totals"]["inventory"] == 2
    assert out["totals"]["baseline_ready"] == 1
    assert out["totals"]["impact_assessable"] == 0
    assert out["by_mechanism_family"]["UTILIZATION_MANAGEMENT"]["baseline_ready"] == 1
    assert out["by_mechanism_family"]["REIMBURSEMENT"]["inventory"] == 1
