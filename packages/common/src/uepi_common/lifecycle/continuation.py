"""Continuation vs policy-effect predictive impact and exposure-aware reconciliation.

Pure functions. No I/O. Mechanism engines call these with already-scoped totals.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

STATUS_AVAILABLE = "AVAILABLE"
STATUS_UNESTIMATED = "UNESTIMATED"
STATUS_NOT_MEASURABLE = "NOT_MEASURABLE"
STATUS_UNAVAILABLE = "UNAVAILABLE"
STATUS_NOT_SUPPORTED = "NOT_SUPPORTED"
STATUS_INCONCLUSIVE = "INCONCLUSIVE"
STATUS_BLOCKED = "BLOCKED"


def pmpm(amount: float, member_months: float) -> Optional[float]:
    if member_months <= 0:
        return None
    return float(amount) / float(member_months)


def annualized_service_rate_per_1k(services: float, member_months: float) -> Optional[float]:
    """Services per 1,000 member-years from monthly exposure."""
    if member_months <= 0:
        return None
    return (float(services) / float(member_months)) * 12.0 * 1000.0


def compute_historical_rates(
    *,
    eligible_services: float,
    eligible_member_months: float,
    total_allowed: float,
) -> Dict[str, Any]:
    """Descriptive historical rates. Not a prior-authorization effect."""
    if eligible_member_months <= 0:
        return {
            "status": STATUS_BLOCKED,
            "reason": "eligible_member_months_required",
            "service_rate_per_member_month": None,
            "allowed_pmpm": None,
            "allowed_per_service": None,
            "services_per_1k_member_years": None,
        }
    service_rate = float(eligible_services) / float(eligible_member_months)
    allowed = pmpm(total_allowed, eligible_member_months)
    per_service = (
        float(total_allowed) / float(eligible_services) if eligible_services > 0 else None
    )
    return {
        "status": STATUS_AVAILABLE,
        "prediction_type": "HISTORICAL_RATES",
        "eligible_services": float(eligible_services),
        "eligible_member_months": float(eligible_member_months),
        "total_allowed": float(total_allowed),
        "service_rate_per_member_month": service_rate,
        "allowed_pmpm": allowed,
        "allowed_per_service": per_service,
        "services_per_1k_member_years": annualized_service_rate_per_1k(
            eligible_services, eligible_member_months
        ),
        "note": "Descriptive historical rates, not estimated prior-authorization effects.",
    }


def compute_continuation_forecast(
    *,
    historical_rates: Mapping[str, Any],
    forecast_member_months_by_month: Sequence[float],
    freeze_timestamp: Optional[str] = None,
    model_id: str = "historical_rate_continuation_v1",
) -> Dict[str, Any]:
    """Frozen continuation prediction: expected outcomes if historical rates continue.

    Monthly series are computed from monthly exposure. Aggregate-only totals must
    not be divided arbitrarily to manufacture a monthly line.
    """
    if historical_rates.get("status") != STATUS_AVAILABLE:
        return {
            "status": STATUS_BLOCKED,
            "prediction_type": "CONTINUATION",
            "reason": historical_rates.get("reason") or "baseline_rates_unavailable",
        }
    service_rate = historical_rates.get("service_rate_per_member_month")
    allowed_pmpm = historical_rates.get("allowed_pmpm")
    if service_rate is None or allowed_pmpm is None:
        return {
            "status": STATUS_BLOCKED,
            "prediction_type": "CONTINUATION",
            "reason": "historical_rates_incomplete",
        }
    if not forecast_member_months_by_month:
        return {
            "status": STATUS_BLOCKED,
            "prediction_type": "CONTINUATION",
            "reason": "forecast_exposure_undefined",
        }

    series = []
    total_mm = 0.0
    total_services = 0.0
    total_allowed = 0.0
    for idx, mm in enumerate(forecast_member_months_by_month):
        mm_f = float(mm)
        if mm_f < 0:
            return {
                "status": STATUS_BLOCKED,
                "prediction_type": "CONTINUATION",
                "reason": "negative_forecast_exposure",
            }
        pred_services = float(service_rate) * mm_f
        pred_allowed = float(allowed_pmpm) * mm_f
        total_mm += mm_f
        total_services += pred_services
        total_allowed += pred_allowed
        series.append(
            {
                "month_index": idx + 1,
                "forecast_member_months": mm_f,
                "predicted_services": pred_services,
                "predicted_allowed": pred_allowed,
                "predicted_allowed_pmpm": float(allowed_pmpm),
            }
        )

    return {
        "status": STATUS_AVAILABLE,
        "prediction_type": "CONTINUATION",
        "model_id": model_id,
        "freeze_timestamp": freeze_timestamp,
        "historical_allowed_pmpm": float(allowed_pmpm),
        "historical_service_rate_per_member_month": float(service_rate),
        "series": series,
        "horizon_totals": {
            "forecast_member_months": total_mm,
            "predicted_services": total_services,
            "predicted_allowed": total_allowed,
            "predicted_allowed_pmpm": float(allowed_pmpm),
        },
        "note": (
            "Forecast expectations under historical continuation. "
            "Not actual claim counts and not predicted policy savings."
        ),
    }


def compute_policy_effect_prediction(
    *,
    intervention_model: Optional[Mapping[str, Any]] = None,
    clinical_criteria_supported: bool = False,
) -> Dict[str, Any]:
    """Policy-effect prediction is separate from continuation.

    Missing models yield UNESTIMATED. Zero is never substituted for absence.
    """
    if not intervention_model:
        return {
            "status": STATUS_UNESTIMATED,
            "prediction_type": "POLICY_EFFECT",
            "avoided_services": STATUS_UNESTIMATED,
            "avoided_allowed_spending": STATUS_UNESTIMATED,
            "savings_pmpm": STATUS_UNESTIMATED,
            "confidence_interval": STATUS_UNAVAILABLE,
            "clinical_decision_prediction": (
                STATUS_AVAILABLE if clinical_criteria_supported else STATUS_NOT_SUPPORTED
            ),
            "reason": "no_supported_intervention_model",
            "note": (
                "Do not set policy effect to zero. Zero is a measured or modeled value; "
                "UNESTIMATED means the required model is absent."
            ),
        }

    return {
        "status": STATUS_AVAILABLE,
        "prediction_type": "POLICY_EFFECT",
        "model": dict(intervention_model),
        "avoided_services": intervention_model.get("avoided_services"),
        "avoided_allowed_spending": intervention_model.get("avoided_allowed_spending"),
        "savings_pmpm": intervention_model.get("savings_pmpm"),
        "confidence_interval": intervention_model.get("confidence_interval", STATUS_UNAVAILABLE),
        "clinical_decision_prediction": (
            STATUS_AVAILABLE if clinical_criteria_supported else STATUS_NOT_SUPPORTED
        ),
    }


def compute_observations(
    *,
    eligible_member_months: float,
    services: float,
    allowed_amount: float,
    paid_amount: Optional[float] = None,
    distinct_members: Optional[float] = None,
    authorization_events_present: bool = False,
    authorization_metrics: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Actual post-period metrics. Independent of predictions and What-If."""
    out: Dict[str, Any] = {
        "status": STATUS_AVAILABLE if eligible_member_months > 0 else STATUS_BLOCKED,
        "eligible_member_months": float(eligible_member_months),
        "services": float(services),
        "allowed_amount": float(allowed_amount),
        "paid_amount": None if paid_amount is None else float(paid_amount),
        "distinct_members": None if distinct_members is None else float(distinct_members),
        "allowed_pmpm": pmpm(allowed_amount, eligible_member_months),
        "services_per_1k_member_years": annualized_service_rate_per_1k(
            services, eligible_member_months
        ),
        "source": "post_period_canonical_records",
        "independent_of_prediction": True,
    }
    if authorization_events_present and authorization_metrics is not None:
        out["authorization"] = {
            "status": STATUS_AVAILABLE,
            **dict(authorization_metrics),
        }
    else:
        out["authorization"] = {
            "status": STATUS_NOT_MEASURABLE,
            "requests": STATUS_NOT_MEASURABLE,
            "approval_rate": STATUS_NOT_MEASURABLE,
            "denial_rate": STATUS_NOT_MEASURABLE,
            "turnaround_time": STATUS_NOT_MEASURABLE,
            "reason": "authorization_event_feed_missing",
            "note": (
                "Matching MRI claims cannot substitute for authorization requests. "
                "Missing feed is NOT_MEASURABLE, not zero."
            ),
        }
    return out


def compute_reconciliation(
    *,
    frozen_predicted_services: float,
    frozen_predicted_allowed: float,
    forecast_member_months: float,
    frozen_allowed_pmpm: float,
    frozen_service_rate_per_member_month: float,
    observed_services: float,
    observed_allowed: float,
    actual_member_months: float,
) -> Dict[str, Any]:
    """Compare frozen continuation to observation. Raw and exposure-adjusted.

    Exposure-adjusted expectations are standardized comparisons derived from the
    frozen rate. They do not rewrite the frozen prediction.
    """
    raw_allowed_variance = float(observed_allowed) - float(frozen_predicted_allowed)
    raw_service_variance = float(observed_services) - float(frozen_predicted_services)

    exposure_adjusted_expected_allowed = float(frozen_allowed_pmpm) * float(actual_member_months)
    exposure_adjusted_allowed_variance = (
        float(observed_allowed) - exposure_adjusted_expected_allowed
    )
    exposure_adjusted_expected_services = (
        float(frozen_service_rate_per_member_month) * float(actual_member_months)
    )
    exposure_adjusted_service_variance = (
        float(observed_services) - exposure_adjusted_expected_services
    )

    observed_pmpm = pmpm(observed_allowed, actual_member_months)
    pmpm_variance = (
        None
        if observed_pmpm is None
        else float(observed_pmpm) - float(frozen_allowed_pmpm)
    )

    return {
        "status": STATUS_AVAILABLE,
        "comparability": {
            "calendar_period_aligned": True,
            "exposure_differs": float(forecast_member_months) != float(actual_member_months),
            "forecast_member_months": float(forecast_member_months),
            "actual_member_months": float(actual_member_months),
        },
        "frozen_prediction": {
            "services": float(frozen_predicted_services),
            "allowed": float(frozen_predicted_allowed),
            "allowed_pmpm": float(frozen_allowed_pmpm),
            "member_months": float(forecast_member_months),
        },
        "observed": {
            "services": float(observed_services),
            "allowed": float(observed_allowed),
            "allowed_pmpm": observed_pmpm,
            "member_months": float(actual_member_months),
        },
        "raw": {
            "service_variance": raw_service_variance,
            "allowed_variance": raw_allowed_variance,
        },
        "exposure_adjusted": {
            "expected_allowed": exposure_adjusted_expected_allowed,
            "allowed_variance": exposure_adjusted_allowed_variance,
            "expected_services": exposure_adjusted_expected_services,
            "service_variance": exposure_adjusted_service_variance,
            "allowed_pmpm_variance": pmpm_variance,
            "label": (
                "Standardized continuation expectation from frozen rate at actual "
                "exposure. Not a new frozen prediction. Not policy-attributable savings."
            ),
        },
        "attribution": {
            "policy_effect": STATUS_UNESTIMATED,
            "note": (
                "Deviation from historical continuation is not services prevented "
                "by prior authorization without a supported effect model."
            ),
        },
    }


def compute_verdict_prerequisites(
    *,
    endpoint_contract: Optional[Sequence[Mapping[str, Any]]] = None,
    authorization_events_present: bool = False,
    policy_effect_status: str = STATUS_UNESTIMATED,
    clinical_criteria_supported: bool = False,
    observations_available: bool = True,
    continuation_available: bool = True,
) -> Dict[str, Any]:
    """Verdict requires an approved endpoint contract. No contract → INCONCLUSIVE."""
    reasons = []
    if not endpoint_contract:
        reasons.append("missing_approved_endpoint_contract")
    if not observations_available:
        reasons.append("observations_unavailable")
    if not continuation_available:
        reasons.append("continuation_forecast_unavailable")
    if not authorization_events_present:
        reasons.append("authorization_decision_evidence_unavailable")
    if not clinical_criteria_supported:
        reasons.append("clinical_criteria_pending")
    if policy_effect_status == STATUS_UNESTIMATED:
        reasons.append("policy_effect_model_unestimated")

    if not endpoint_contract:
        return {
            "verdict": STATUS_INCONCLUSIVE,
            "reason_codes": reasons,
            "note": (
                "No endpoint contract means no ON_TRACK or AT_RISK verdict. "
                "Negative cost variance is not success."
            ),
        }

    # Contract present — caller still must score measurable endpoints.
    return {
        "verdict": "EVALUATION_PERMITTED",
        "reason_codes": reasons,
        "endpoint_contract": [dict(e) for e in endpoint_contract],
        "note": "Endpoint contract present; score only measurable endpoints from evidence.",
    }


def compute_whatif_continuation(
    *,
    frozen_continuation: Mapping[str, Any],
    scenario_member_months: float,
    scenario_id: str,
) -> Dict[str, Any]:
    """Isolated exposure sensitivity. Never mutates frozen prediction/observation."""
    if frozen_continuation.get("status") != STATUS_AVAILABLE:
        return {
            "status": STATUS_BLOCKED,
            "scenario_id": scenario_id,
            "reason": "parent_continuation_unavailable",
        }
    allowed_pmpm = frozen_continuation.get("historical_allowed_pmpm")
    service_rate = frozen_continuation.get("historical_service_rate_per_member_month")
    if allowed_pmpm is None or service_rate is None:
        return {
            "status": STATUS_BLOCKED,
            "scenario_id": scenario_id,
            "reason": "parent_rates_missing",
        }
    mm = float(scenario_member_months)
    return {
        "status": STATUS_AVAILABLE,
        "scenario_id": scenario_id,
        "scenario_type": "CONTINUATION_EXPOSURE_SENSITIVITY",
        "parent_prediction_type": "CONTINUATION",
        "scenario_member_months": mm,
        "scenario_continuation_allowed": float(allowed_pmpm) * mm,
        "scenario_continuation_services": float(service_rate) * mm,
        "policy_effect": STATUS_UNESTIMATED,
        "mutates_frozen_prediction": False,
        "mutates_observation": False,
        "note": (
            "Valid exposure sensitivity. Not a prediction that prior authorization "
            "will save any dollar amount."
        ),
    }


def evaluate_claim_scope(
    *,
    procedure_code: str,
    included_codes: Iterable[str],
    excluded_codes: Iterable[str] = (),
    product_in_scope: bool = True,
    covered_on_service_date: bool = True,
    outpatient_setting: bool = True,
    within_window: bool = True,
    valid_after_adjustment: bool = True,
) -> Dict[str, Any]:
    """Claim-line applicability from configured codesets and scope — not prediction."""
    code = str(procedure_code).strip()
    included = {str(c).strip() for c in included_codes}
    excluded = {str(c).strip() for c in excluded_codes}
    if code in excluded or code not in included:
        return {"included": False, "reason": "procedure_out_of_scope"}
    if not product_in_scope:
        return {"included": False, "reason": "product_out_of_scope"}
    if not covered_on_service_date:
        return {"included": False, "reason": "missing_or_invalid_enrollment"}
    if not outpatient_setting:
        return {"included": False, "reason": "setting_out_of_scope"}
    if not within_window:
        return {"included": False, "reason": "outside_observation_window"}
    if not valid_after_adjustment:
        return {"included": False, "reason": "void_or_adjustment_excluded"}
    return {"included": True, "reason": "in_scope"}
