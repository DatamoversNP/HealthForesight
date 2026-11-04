"""Objectives Health stability contract — same inputs ⇒ same outputs."""
from copy import deepcopy
from uuid import uuid4

from uepi_api.services.objectives_health import (
    CALCULATION_VERSION,
    build_objectives_health_snapshot,
)


TENANT = uuid4()
POLICY_A = str(uuid4())
POLICY_B = str(uuid4())


def _fixture_inputs():
    policies = [
        {"id": POLICY_B, "name": "Zebra Policy", "policy_type": "PRIOR_AUTH", "effective_period": {}},
        {"id": POLICY_A, "name": "Alpha MRI", "policy_type": "PRIOR_AUTH", "effective_period": {"start_date": "2024-01-01"}},
    ]
    observations = [
        {
            "policy_id": POLICY_A,
            "observation_id": "obs-1",
            "observation_period_end": "2024-06-30",
            "computed_at": "2024-07-01T00:00:00Z",
            "comparisons": {
                "vs_baseline": {
                    "cost_change_pmpm": -1.2,
                    "utilization_change_pct": -8.0,
                    "cost_change_pct": -5.0,
                },
                "vs_predicted": {"prediction_accuracy_pct": 90.0},
            },
            "behavioral_explanation": {
                "provider_response": {"summary": "volume down"},
            },
        }
    ]
    predicted = [
        {
            "policy_id": POLICY_A,
            "metrics": {"cost_change_pmpm": -1.0, "utilization_change_pct": -7.0},
        }
    ]
    decisions = [{"policy_id": POLICY_A}]
    return policies, observations, predicted, decisions


def test_snapshot_is_deterministic_across_builds():
    policies, observations, predicted, decisions = _fixture_inputs()
    a = build_objectives_health_snapshot(
        tenant_id=TENANT,
        policies=deepcopy(policies),
        latest_observations=deepcopy(observations),
        predicted_impacts=deepcopy(predicted),
        decisions=deepcopy(decisions),
        generated_at="FIXED",
    )
    b = build_objectives_health_snapshot(
        tenant_id=TENANT,
        policies=list(reversed(deepcopy(policies))),  # input order must not matter
        latest_observations=deepcopy(observations),
        predicted_impacts=deepcopy(predicted),
        decisions=deepcopy(decisions),
        generated_at="FIXED",
    )
    assert a["calculation_version"] == CALCULATION_VERSION
    assert a == b
    assert a["policy_rows"][0]["name"] == "Alpha MRI"  # sorted by name
    assert a["policy_rows"][0]["status"] in ("on_track", "at_risk", "no_data")
    assert a["policy_rows"][1]["status"] == "no_data"
    assert a["policy_rows"][1]["verdict"] == "UNKNOWN"
    assert POLICY_A in a["strategic"][0]["policy_ids"]  # A = forecasts
    assert POLICY_A in a["strategic"][2]["policy_ids"]  # C = observations
    assert POLICY_A in a["strategic"][3]["policy_ids"]  # D = behavior
    assert POLICY_B not in a["strategic"][0]["policy_ids"]


def test_no_observation_never_inherits_predicted_as_on_track():
    """Predicted-only policies must remain no_data — not fabricated observed health."""
    policies = [
        {"id": POLICY_A, "name": "New Policy", "policy_type": "CODING_AND_BILLING"},
    ]
    predicted = [
        {
            "policy_id": POLICY_A,
            "metrics": {"cost_change_pmpm": -50.0, "utilization_change_pct": -20.0},
        }
    ]
    snap = build_objectives_health_snapshot(
        tenant_id=TENANT,
        policies=policies,
        latest_observations=[],
        predicted_impacts=predicted,
        decisions=[],
        generated_at="FIXED",
    )
    row = snap["policy_rows"][0]
    assert row["status"] == "no_data"
    assert row["verdict"] == "UNKNOWN"
    assert row["utilization_change_pct"] is None
    assert row["cost_impact_pmpm"] is None
    assert row["has_forecast"] is True
    assert snap["summary"]["on_track"] == 0
    assert snap["strategic"][0]["count"] == 1  # forecast still counted for objective A


def test_refresh_equivalence_ignoring_timestamp():
    policies, observations, predicted, decisions = _fixture_inputs()
    a = build_objectives_health_snapshot(
        tenant_id=TENANT,
        policies=policies,
        latest_observations=observations,
        predicted_impacts=predicted,
        decisions=decisions,
        generated_at="T1",
    )
    b = build_objectives_health_snapshot(
        tenant_id=TENANT,
        policies=policies,
        latest_observations=observations,
        predicted_impacts=predicted,
        decisions=decisions,
        generated_at="T2",
    )
    a2 = {**a, "generated_at": None}
    b2 = {**b, "generated_at": None}
    assert a2 == b2


def test_objectives_health_verdicts_match_compute_verdict_invariant():
    """Invariant: OH status maps from the same compute_verdict as Policy Verdicts."""
    from uepi_api.verdict import compute_verdict
    from uepi_api.services.objectives_health import _verdict_to_health

    policies, observations, predicted, decisions = _fixture_inputs()
    obs = observations[0]
    verdict_status, _, _ = compute_verdict(
        obs.get("comparisons") or {},
        obs.get("behavioral_explanation") or {},
    )
    snap = build_objectives_health_snapshot(
        tenant_id=TENANT,
        policies=policies,
        latest_observations=observations,
        predicted_impacts=predicted,
        decisions=decisions,
        generated_at="FIXED",
    )
    row = next(r for r in snap["policy_rows"] if r["policy_id"] == POLICY_A)
    assert row["verdict"] == verdict_status
    assert row["status"] == _verdict_to_health(verdict_status)

    # Forecast-only policy must remain UNKNOWN / no_data — never observed on_track
    forecast_only = build_objectives_health_snapshot(
        tenant_id=TENANT,
        policies=[{"id": POLICY_B, "name": "Forecast Only", "policy_type": "PRIOR_AUTH"}],
        latest_observations=[],
        predicted_impacts=[
            {"policy_id": POLICY_B, "metrics": {"cost_change_pmpm": -99, "utilization_change_pct": -50}}
        ],
        decisions=[],
        generated_at="FIXED",
    )
    fo = forecast_only["policy_rows"][0]
    assert fo["verdict"] == "UNKNOWN"
    assert fo["status"] == "no_data"
    assert fo["has_forecast"] is True
    assert fo["utilization_change_pct"] is None
    assert fo["cost_impact_pmpm"] is None
