"""MRI lifecycle acceptance tests — independent oracle vs calculator."""

from pytest import approx

from uepi_common.lifecycle import (
    MRI_LIFECYCLE_FIXTURE,
    STATUS_AVAILABLE,
    STATUS_INCONCLUSIVE,
    STATUS_NOT_MEASURABLE,
    STATUS_UNESTIMATED,
    compute_continuation_forecast,
    compute_historical_rates,
    compute_observations,
    compute_policy_effect_prediction,
    compute_reconciliation,
    compute_verdict_prerequisites,
    compute_whatif_continuation,
    evaluate_claim_scope,
    run_mri_lifecycle_fixture,
)


def test_policy_scope_includes_candidate_cpt():
    result = evaluate_claim_scope(
        procedure_code="72148",
        included_codes=["72148", "72149"],
        excluded_codes=["99213", "99214"],
    )
    assert result["included"] is True


def test_incorrect_procedure_excluded():
    result = evaluate_claim_scope(
        procedure_code="99213",
        included_codes=["72148", "72149"],
        excluded_codes=["99213", "99214"],
    )
    assert result["included"] is False
    assert result["reason"] == "procedure_out_of_scope"


def test_incorrect_product_excluded():
    result = evaluate_claim_scope(
        procedure_code="72148",
        included_codes=["72148", "72149"],
        product_in_scope=False,
    )
    assert result["included"] is False
    assert result["reason"] == "product_out_of_scope"


def test_missing_enrollment_excluded():
    result = evaluate_claim_scope(
        procedure_code="72148",
        included_codes=["72148", "72149"],
        covered_on_service_date=False,
    )
    assert result["included"] is False
    assert result["reason"] == "missing_or_invalid_enrollment"


def test_historical_baseline_rates():
    rates = compute_historical_rates(
        eligible_services=14400,
        eligible_member_months=4_800_000,
        total_allowed=11_520_000,
    )
    assert rates["status"] == STATUS_AVAILABLE
    assert rates["service_rate_per_member_month"] == approx(0.003)
    assert rates["allowed_pmpm"] == approx(2.40)
    assert rates["services_per_1k_member_years"] == approx(36.0)
    assert rates["allowed_per_service"] == approx(800.0)


def test_monthly_continuation_forecast():
    rates = compute_historical_rates(
        eligible_services=14400,
        eligible_member_months=4_800_000,
        total_allowed=11_520_000,
    )
    forecast = compute_continuation_forecast(
        historical_rates=rates,
        forecast_member_months_by_month=[405_000] * 12,
        freeze_timestamp="2025-12-31",
    )
    assert forecast["status"] == STATUS_AVAILABLE
    assert forecast["prediction_type"] == "CONTINUATION"
    jan = forecast["series"][0]
    assert jan["predicted_services"] == 1215.0
    assert jan["predicted_allowed"] == 972_000.0
    assert jan["predicted_allowed_pmpm"] == 2.40
    assert forecast["horizon_totals"]["predicted_services"] == 14_580.0
    assert forecast["horizon_totals"]["predicted_allowed"] == 11_664_000.0
    # Explicit monthly computation — not aggregate divided by 12
    assert len(forecast["series"]) == 12
    assert all(m["predicted_allowed"] == 972_000.0 for m in forecast["series"])


def test_prediction_freeze_immutability_contract():
    rates = compute_historical_rates(
        eligible_services=14400,
        eligible_member_months=4_800_000,
        total_allowed=11_520_000,
    )
    frozen = compute_continuation_forecast(
        historical_rates=rates,
        forecast_member_months_by_month=[405_000] * 12,
        freeze_timestamp="2025-12-31",
    )
    # Post-freeze claims must not rewrite the frozen object in-place.
    snapshot = {
        "allowed": frozen["series"][0]["predicted_allowed"],
        "services": frozen["series"][0]["predicted_services"],
        "freeze": frozen["freeze_timestamp"],
    }
    # Simulate later claims arriving by recomputing with different baseline — original frozen stays.
    later_rates = compute_historical_rates(
        eligible_services=15000,
        eligible_member_months=4_800_000,
        total_allowed=12_000_000,
    )
    later = compute_continuation_forecast(
        historical_rates=later_rates,
        forecast_member_months_by_month=[405_000] * 12,
        freeze_timestamp="2026-02-01",
    )
    assert frozen["series"][0]["predicted_allowed"] == snapshot["allowed"]
    assert frozen["series"][0]["predicted_services"] == snapshot["services"]
    assert frozen["freeze_timestamp"] == snapshot["freeze"]
    assert later["series"][0]["predicted_allowed"] != snapshot["allowed"]


def test_observation_january_metrics():
    obs = compute_observations(
        eligible_member_months=407_000,
        services=1170,
        allowed_amount=936_000,
        paid_amount=742_000,
        distinct_members=1110,
        authorization_events_present=False,
    )
    # Spec illustrates ~$2.2998 and 34.50; exact float is 1170/407000*12*1000.
    assert obs["allowed_pmpm"] == approx(2.2998, abs=1e-4)
    assert obs["services_per_1k_member_years"] == approx(34.50, abs=0.01)
    assert obs["independent_of_prediction"] is True


def test_raw_and_exposure_adjusted_reconciliation():
    rates = compute_historical_rates(
        eligible_services=14400,
        eligible_member_months=4_800_000,
        total_allowed=11_520_000,
    )
    forecast = compute_continuation_forecast(
        historical_rates=rates,
        forecast_member_months_by_month=[405_000],
        freeze_timestamp="2025-12-31",
    )
    jan = forecast["series"][0]
    recon = compute_reconciliation(
        frozen_predicted_services=jan["predicted_services"],
        frozen_predicted_allowed=jan["predicted_allowed"],
        forecast_member_months=jan["forecast_member_months"],
        frozen_allowed_pmpm=2.40,
        frozen_service_rate_per_member_month=0.003,
        observed_services=1170,
        observed_allowed=936_000,
        actual_member_months=407_000,
    )
    assert recon["raw"]["allowed_variance"] == -36_000.0
    assert recon["raw"]["service_variance"] == -45.0
    assert recon["exposure_adjusted"]["expected_allowed"] == 976_800.0
    assert recon["exposure_adjusted"]["allowed_variance"] == -40_800.0
    assert recon["exposure_adjusted"]["expected_services"] == 1221.0
    assert recon["exposure_adjusted"]["service_variance"] == -51.0
    assert recon["exposure_adjusted"]["allowed_pmpm_variance"] == approx(-0.1002, abs=1e-4)
    assert recon["attribution"]["policy_effect"] == STATUS_UNESTIMATED


def test_missing_authorization_feed_is_not_measurable():
    obs = compute_observations(
        eligible_member_months=407_000,
        services=1170,
        allowed_amount=936_000,
        authorization_events_present=False,
    )
    assert obs["authorization"]["status"] == STATUS_NOT_MEASURABLE
    assert obs["authorization"]["requests"] == STATUS_NOT_MEASURABLE
    assert obs["authorization"]["approval_rate"] != 0


def test_missing_effect_model_is_unestimated_not_zero():
    effect = compute_policy_effect_prediction(intervention_model=None)
    assert effect["status"] == STATUS_UNESTIMATED
    assert effect["avoided_services"] == STATUS_UNESTIMATED
    assert effect["avoided_allowed_spending"] == STATUS_UNESTIMATED
    assert effect["savings_pmpm"] == STATUS_UNESTIMATED
    assert effect["avoided_services"] != 0
    assert effect["savings_pmpm"] != 0


def test_missing_endpoint_contract_is_inconclusive():
    verdict = compute_verdict_prerequisites(endpoint_contract=None)
    assert verdict["verdict"] == STATUS_INCONCLUSIVE
    assert "missing_approved_endpoint_contract" in verdict["reason_codes"]


def test_whatif_exposure_sensitivity_does_not_mutate_parent():
    rates = compute_historical_rates(
        eligible_services=14400,
        eligible_member_months=4_800_000,
        total_allowed=11_520_000,
    )
    frozen = compute_continuation_forecast(
        historical_rates=rates,
        forecast_member_months_by_month=[405_000] * 12,
        freeze_timestamp="2025-12-31",
    )
    original_allowed = frozen["horizon_totals"]["predicted_allowed"]
    whatif = compute_whatif_continuation(
        frozen_continuation=frozen,
        scenario_member_months=420_000,
        scenario_id="mri-420k",
    )
    assert whatif["scenario_continuation_allowed"] == 1_008_000.0
    assert whatif["mutates_frozen_prediction"] is False
    assert whatif["policy_effect"] == STATUS_UNESTIMATED
    assert frozen["horizon_totals"]["predicted_allowed"] == original_allowed


def test_full_fixture_acceptance_matrix_and_dashboard():
    result = run_mri_lifecycle_fixture()
    oracle = MRI_LIFECYCLE_FIXTURE["oracle"]
    assert result["historical_rates"]["allowed_pmpm"] == oracle["allowed_pmpm"]
    assert result["continuation"]["series"][0]["predicted_allowed"] == oracle["jan_predicted_allowed"]
    assert result["policy_effect"]["status"] == STATUS_UNESTIMATED
    assert result["observations"]["authorization"]["status"] == STATUS_NOT_MEASURABLE
    assert result["reconciliation"]["raw"]["allowed_variance"] == oracle["raw_allowed_variance"]
    assert (
        result["reconciliation"]["exposure_adjusted"]["expected_allowed"]
        == oracle["exposure_adjusted_expected_allowed"]
    )
    assert result["verdict"]["verdict"] == STATUS_INCONCLUSIVE
    assert result["whatif"]["scenario_continuation_allowed"] == oracle["whatif_continuation_allowed"]
    matrix = result["acceptance_matrix"]
    assert matrix["continuation_prediction"] == "Testable"
    assert matrix["policy_effect_prediction"] == STATUS_UNESTIMATED
    assert matrix["authorization_outcomes"] == STATUS_NOT_MEASURABLE
    assert matrix["verdict"] == STATUS_INCONCLUSIVE
    dash = result["dashboard_projection"]
    assert dash["verdict_badge"] == STATUS_INCONCLUSIVE
    assert dash["frozen_continuation_forecast"] == 972_000.0
    assert dash["observed_allowed"] == 936_000.0
    assert dash["comparison_bars"]["exposure_adjusted"] == 976_800.0
    assert dash["policy_effect_impact"] == STATUS_UNESTIMATED
