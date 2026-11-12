"""API adapter for continuation / policy-effect / reconciliation lifecycle math.

Uses shared uepi_common.lifecycle calculators. Mechanism engines supply
already-scoped totals; this module does not invent eligibility from
preferred_source_system or policy_key stamps.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence

from uepi_common.lifecycle import (
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


def build_continuation_prediction_from_baseline(
    *,
    eligible_services: float,
    eligible_member_months: float,
    total_allowed: float,
    forecast_member_months_by_month: Sequence[float],
    freeze_timestamp: Optional[str] = None,
    intervention_model: Optional[Mapping[str, Any]] = None,
    clinical_criteria_supported: bool = False,
) -> Dict[str, Any]:
    """Typed predictive impact: continuation AVAILABLE; effect separate."""
    rates = compute_historical_rates(
        eligible_services=eligible_services,
        eligible_member_months=eligible_member_months,
        total_allowed=total_allowed,
    )
    continuation = compute_continuation_forecast(
        historical_rates=rates,
        forecast_member_months_by_month=forecast_member_months_by_month,
        freeze_timestamp=freeze_timestamp,
    )
    policy_effect = compute_policy_effect_prediction(
        intervention_model=intervention_model,
        clinical_criteria_supported=clinical_criteria_supported,
    )
    return {
        "historical_rates": rates,
        "continuation": continuation,
        "policy_effect": policy_effect,
        "invariants": {
            "continuation_is_not_policy_effect": True,
            "zero_not_substituted_for_unestimated": policy_effect["status"] == STATUS_UNESTIMATED
            or policy_effect.get("savings_pmpm") != 0
            or intervention_model is not None,
        },
    }


def build_observation_and_reconciliation(
    *,
    continuation: Mapping[str, Any],
    month_index: int,
    observed_services: float,
    observed_allowed: float,
    actual_member_months: float,
    paid_amount: Optional[float] = None,
    distinct_members: Optional[float] = None,
    authorization_events_present: bool = False,
    endpoint_contract: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    """Independent observation + exposure-aware reconciliation + verdict gate."""
    series = (continuation or {}).get("series") or []
    if month_index < 1 or month_index > len(series):
        return {"status": "BLOCKED", "reason": "month_index_out_of_range"}
    month = series[month_index - 1]
    obs = compute_observations(
        eligible_member_months=actual_member_months,
        services=observed_services,
        allowed_amount=observed_allowed,
        paid_amount=paid_amount,
        distinct_members=distinct_members,
        authorization_events_present=authorization_events_present,
    )
    recon = compute_reconciliation(
        frozen_predicted_services=month["predicted_services"],
        frozen_predicted_allowed=month["predicted_allowed"],
        forecast_member_months=month["forecast_member_months"],
        frozen_allowed_pmpm=continuation["historical_allowed_pmpm"],
        frozen_service_rate_per_member_month=continuation[
            "historical_service_rate_per_member_month"
        ],
        observed_services=observed_services,
        observed_allowed=observed_allowed,
        actual_member_months=actual_member_months,
    )
    effect_status = STATUS_UNESTIMATED
    verdict = compute_verdict_prerequisites(
        endpoint_contract=endpoint_contract,
        authorization_events_present=authorization_events_present,
        policy_effect_status=effect_status,
        observations_available=True,
        continuation_available=continuation.get("status") == "AVAILABLE",
    )
    return {
        "observations": obs,
        "reconciliation": recon,
        "verdict": verdict,
    }


def whatif_continuation_exposure(
    continuation: Mapping[str, Any],
    *,
    scenario_member_months: float,
    scenario_id: str,
) -> Dict[str, Any]:
    return compute_whatif_continuation(
        frozen_continuation=continuation,
        scenario_member_months=scenario_member_months,
        scenario_id=scenario_id,
    )


def claim_in_scope(**kwargs: Any) -> Dict[str, Any]:
    return evaluate_claim_scope(**kwargs)


def mri_reference_fixture_run() -> Dict[str, Any]:
    """Deterministic MRI oracle run for QA agents and acceptance reports."""
    return run_mri_lifecycle_fixture()
