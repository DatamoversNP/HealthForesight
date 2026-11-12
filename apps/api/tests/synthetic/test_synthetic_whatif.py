"""Population what-if uses the payment engines and a separate oracle."""

from uepi_api.services.synthetic_whatif import WhatIfRejected, run_population_whatif


def _line(**kwargs):
    base = {
        "claim_id": "C1",
        "claim_line_id": "L1",
        "cpt_code": "27447",
        "allowed_amount": 1000.0,
        "paid_amount": 800.0,
        "member_cost_share": 200.0,
        "units": 1,
        "place_of_service": "11",
        "line_status": "ACTIVE",
        "policy_key": "mppr",
    }
    base.update(kwargs)
    return base


def test_mppr_matches_oracle_and_separates_plan_paid():
    lines = [
        _line(claim_line_id="L1", cpt_code="27447", allowed_amount=1000, paid_amount=800, member_cost_share=200),
        _line(claim_line_id="L2", cpt_code="64483", allowed_amount=400, paid_amount=320, member_cost_share=80),
    ]
    result = run_population_whatif(lines, "mppr", {"secondary_pct": 0.5}, member_months=1000)
    assert result["status"] == "completed"
    assert result["oracle_match"] is True
    assert result["baseline_allowed"] == 1400
    assert result["simulated_allowed"] == 1200
    assert result["allowed_difference"] == -200
    assert result["baseline_plan_paid"] == 1120
    assert result["simulated_plan_paid"] == 960
    assert result["payment_impact_dollars"] == 200
    assert result["allowed_difference_per_enrolled_member_month"] == -0.2
    assert result["confidence_interval"] is None
    assert result["p_value"] is None
    assert result["utilization_change_pct"] is None


def test_sos_neutral_is_a_real_zero():
    lines = [_line(policy_key="sos", cpt_code="72148", place_of_service="22", allowed_amount=1000, paid_amount=800)]
    result = run_population_whatif(lines, "sos", {"hospital_pct": 1.0}, member_months=10)
    assert result["status"] == "completed"
    assert result["payment_impact_dollars"] == 0
    assert result["allowed_difference"] == 0
    assert result["oracle_match"] is True


def test_clinical_policy_has_no_outcome():
    lines = [_line(policy_key="mri", cpt_code="72148")]
    result = run_population_whatif(lines, "mri", {}, member_months=10)
    assert result["status"] == "unavailable"
    assert result["outcome_status"] == "NOT_MEASURABLE"
    assert result["baseline_allowed"] is None
    assert result["payment_impact_dollars"] is None
    assert result["lines_included"] == 1


def test_empty_payment_scope_is_unavailable_not_zero():
    result = run_population_whatif([], "therapy", {}, member_months=10)
    assert result["status"] == "unavailable"
    assert result["allowed_difference"] is None


def test_parameter_outside_range_is_rejected():
    try:
        run_population_whatif([_line()], "mppr", {"secondary_pct": 1.5}, member_months=10)
    except WhatIfRejected:
        return
    raise AssertionError("expected rejection")
