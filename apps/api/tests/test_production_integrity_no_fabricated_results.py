"""Production paths must not invent a financial result or a confidence score."""

from uuid import uuid4

from uepi_api.services.prediction_enhancement_service import enhance_prediction_with_confidence_and_ramp_up
from uepi_common.metrics.measurement_integrity import aggregate_policy_observation_rollups


def test_missing_baseline_does_not_become_a_stand_in_rate_or_confidence():
    enhanced = enhance_prediction_with_confidence_and_ramp_up(
        tenant_id=uuid4(),
        policy_id=uuid4(),
        predicted_impact={"metrics": {}, "confidence": None, "prediction_method": None},
        baseline_metrics={"source": "test-without-rates"},
    )
    assert enhanced["confidence"] is None
    assert enhanced["confidence_intervals"]["cost"]["status"] == "UNAVAILABLE"
    assert enhanced["ramp_up_projections"]["utilization"]["status"] == "UNAVAILABLE"
    blob = str(enhanced)
    assert "50.0" not in blob
    assert "0.7" not in blob


def test_continuation_comparisons_are_not_added_to_payment_rule_results():
    rollup = aggregate_policy_observation_rollups([
        {
            "policy_id": "payment",
            "metrics": {"denominator_basis": "ENROLLMENT", "enrolled_rate_status": "MEASURED"},
            "comparisons": {"vs_baseline": {
                "cost_change": -2.0,
                "cost_change_kind": "observed_post_period_allowed_difference_per_enrolled_member_month",
            }},
        },
        {
            "policy_id": "continuation",
            "metrics": {"denominator_basis": "ENROLLMENT", "enrolled_rate_status": "MEASURED"},
            "comparisons": {"vs_baseline": {
                "cost_change": -15.0,
                "cost_change_kind": "observed_versus_frozen_continuation_per_enrolled_member_month",
            }},
        },
    ])
    assert rollup["total_cost_impact"] == -2.0
    assert rollup["continuation_allowed_difference"] == -15.0
    assert "not a portfolio savings total" in rollup["continuation_allowed_difference_label"]
