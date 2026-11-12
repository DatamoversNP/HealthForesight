"""Deterministic MRI prior-authorization lifecycle fixture (synthetic oracle).

Illustrative mock-client numbers from the HealthForesight MRI lifecycle
execution specification. Not staging results.
"""

from __future__ import annotations

from typing import Any, Dict

from .continuation import (
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
)

MRI_LIFECYCLE_FIXTURE: Dict[str, Any] = {
    "policy": {
        "id": "MOCK-UM-MRI-001",
        "version": "1.0",
        "name": "Outpatient MRI Prior Authorization",
        "mechanism": "PRIOR_AUTH",
        "candidate_cpts": ["72148", "72149"],
        "excluded_cpts": ["99213", "99214"],
        "product": "Mock Commercial PPO",
        "baseline_window": "2025-01-01/2025-12-31",
        "prediction_freeze": "2025-12-31",
        "policy_start": "2026-01-01",
        "prediction_horizon": "2026-01-01/2026-12-31",
        "observation_window": "2026-01-01/2026-09-30",
        "financial_basis": "ALLOWED",
    },
    "baseline_totals": {
        "eligible_services": 14400,
        "eligible_member_months": 4_800_000,
        "total_allowed": 11_520_000,
    },
    "forecast_exposure": {
        "member_months_per_month": 405_000,
        "months": 12,
    },
    "january_2026_observation": {
        "eligible_member_months": 407_000,
        "services": 1170,
        "allowed_amount": 936_000,
        "paid_amount": 742_000,
        "distinct_members": 1110,
    },
    "whatif_exposure": 420_000,
    "oracle": {
        "service_rate_per_member_month": 0.003,
        "allowed_pmpm": 2.40,
        "services_per_1k_member_years": 36.0,
        "jan_predicted_services": 1215.0,
        "jan_predicted_allowed": 972_000.0,
        "horizon_predicted_services": 14_580.0,
        "horizon_predicted_allowed": 11_664_000.0,
        "observed_allowed_pmpm": 936_000 / 407_000,
        "observed_services_per_1k": (1170 / 407_000) * 12 * 1000,
        "raw_allowed_variance": -36_000.0,
        "exposure_adjusted_expected_allowed": 976_800.0,
        "exposure_adjusted_allowed_variance": -40_800.0,
        "exposure_adjusted_expected_services": 1221.0,
        "exposure_adjusted_service_variance": -51.0,
        "whatif_continuation_allowed": 1_008_000.0,
    },
}


def run_mri_lifecycle_fixture() -> Dict[str, Any]:
    """Execute the full MRI lifecycle calculator against the fixture oracle."""
    fx = MRI_LIFECYCLE_FIXTURE
    rates = compute_historical_rates(**fx["baseline_totals"])
    monthly_mm = [fx["forecast_exposure"]["member_months_per_month"]] * fx["forecast_exposure"]["months"]
    continuation = compute_continuation_forecast(
        historical_rates=rates,
        forecast_member_months_by_month=monthly_mm,
        freeze_timestamp=fx["policy"]["prediction_freeze"],
    )
    policy_effect = compute_policy_effect_prediction(
        intervention_model=None,
        clinical_criteria_supported=False,
    )
    obs = compute_observations(
        authorization_events_present=False,
        **fx["january_2026_observation"],
    )
    jan = continuation["series"][0]
    recon = compute_reconciliation(
        frozen_predicted_services=jan["predicted_services"],
        frozen_predicted_allowed=jan["predicted_allowed"],
        forecast_member_months=jan["forecast_member_months"],
        frozen_allowed_pmpm=continuation["historical_allowed_pmpm"],
        frozen_service_rate_per_member_month=continuation[
            "historical_service_rate_per_member_month"
        ],
        observed_services=obs["services"],
        observed_allowed=obs["allowed_amount"],
        actual_member_months=obs["eligible_member_months"],
    )
    verdict = compute_verdict_prerequisites(
        endpoint_contract=None,
        authorization_events_present=False,
        policy_effect_status=policy_effect["status"],
        clinical_criteria_supported=False,
        observations_available=obs["status"] == STATUS_AVAILABLE,
        continuation_available=continuation["status"] == STATUS_AVAILABLE,
    )
    whatif = compute_whatif_continuation(
        frozen_continuation=continuation,
        scenario_member_months=fx["whatif_exposure"],
        scenario_id="mri-exposure-420k",
    )
    scope_cases = {
        "cpt_72148_in_scope": evaluate_claim_scope(
            procedure_code="72148",
            included_codes=fx["policy"]["candidate_cpts"],
            excluded_codes=fx["policy"]["excluded_cpts"],
        ),
        "cpt_99213_excluded": evaluate_claim_scope(
            procedure_code="99213",
            included_codes=fx["policy"]["candidate_cpts"],
            excluded_codes=fx["policy"]["excluded_cpts"],
        ),
        "out_of_scope_product": evaluate_claim_scope(
            procedure_code="72148",
            included_codes=fx["policy"]["candidate_cpts"],
            excluded_codes=fx["policy"]["excluded_cpts"],
            product_in_scope=False,
        ),
        "missing_enrollment": evaluate_claim_scope(
            procedure_code="72148",
            included_codes=fx["policy"]["candidate_cpts"],
            excluded_codes=fx["policy"]["excluded_cpts"],
            covered_on_service_date=False,
        ),
    }

    acceptance_matrix = {
        "policy_definition": "Configured fixture",
        "baseline": "Testable",
        "continuation_prediction": "Testable",
        "policy_effect_prediction": STATUS_UNESTIMATED,
        "claims_observations": "Testable",
        "authorization_outcomes": STATUS_NOT_MEASURABLE,
        "reconciliation": "Testable",
        "verdict": STATUS_INCONCLUSIVE,
        "whatif_continuation": "Testable",
    }

    return {
        "fixture": fx,
        "historical_rates": rates,
        "continuation": continuation,
        "policy_effect": policy_effect,
        "observations": obs,
        "reconciliation": recon,
        "verdict": verdict,
        "whatif": whatif,
        "scope_cases": scope_cases,
        "acceptance_matrix": acceptance_matrix,
        "dashboard_projection": {
            "title": fx["policy"]["name"],
            "subtitle": "Illustrative Jan 2026 lifecycle",
            "verdict_badge": STATUS_INCONCLUSIVE,
            "historical_allowed_pmpm": rates["allowed_pmpm"],
            "observed_allowed_pmpm": obs["allowed_pmpm"],
            "frozen_continuation_forecast": jan["predicted_allowed"],
            "observed_allowed": obs["allowed_amount"],
            "comparison_bars": {
                "continuation": jan["predicted_allowed"],
                "observed": obs["allowed_amount"],
                "exposure_adjusted": recon["exposure_adjusted"]["expected_allowed"],
            },
            "policy_effect_impact": STATUS_UNESTIMATED,
        },
    }
