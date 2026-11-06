"""Gate A presentation rules for rates, annualization, and uncertainty.

Claimant-based numbers may remain on legacy keys. Authoritative labels must not
call those numbers enrolled utilization or enrolled PMPM.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

RATE_KEYS = (
    "util_rate_total_per_1000_mm",
    "util_rate_target_per_1000_mm",
    "utilization_per_1k",
    "allowed_pmpm_total",
    "allowed_pmpm_target",
    "allowed_pmpm",
    "paid_pmpm_total",
    "paid_pmpm_target",
    "paid_pmpm",
    "cost_pmpm",
    "cost_per_member",
)

_UTIL_KEYS = {
    "util_rate_total_per_1000_mm",
    "util_rate_target_per_1000_mm",
    "utilization_per_1k",
    "utilization",
}
_COST_KEYS = {
    "allowed_pmpm_total",
    "allowed_pmpm_target",
    "allowed_pmpm",
    "paid_pmpm_total",
    "paid_pmpm_target",
    "paid_pmpm",
    "cost_pmpm",
    "cost_per_member",
    "cost",
}


def enrolled_rate(metrics: Optional[Dict[str, Any]]) -> bool:
    if not metrics:
        return False
    return (
        metrics.get("denominator_basis") == "ENROLLMENT"
        and metrics.get("enrolled_rate_status") == "MEASURED"
    )


def authoritative_measure_label(metric_key: str, metrics: Optional[Dict[str, Any]] = None) -> str:
    """Label a rate for an authoritative consumer.

    Missing basis is treated as not enrolled. A claimant-based legacy number
    must not be captioned as member-months or PMPM.
    """
    enrolled = enrolled_rate(metrics)
    if metric_key in _UTIL_KEYS:
        if enrolled:
            return "Utilization per 1,000 eligible member-months"
        return "Claim lines per 1,000 claimants (not enrolled utilization)"
    if metric_key in _COST_KEYS:
        if enrolled:
            return "Dollars per enrolled member-month"
        return "Dollars per claimant-month (not enrolled PMPM)"
    if metric_key == "allowed_total_annualized":
        return annualization_label(metrics)
    return metric_key


def annualization_label(metrics: Optional[Dict[str, Any]] = None) -> str:
    if enrolled_rate(metrics) or (metrics or {}).get("annualization_basis") == "ENROLLMENT":
        return "Annualized enrolled-population total"
    return "Claimant-based annualized total. Not enrolled-population spend."


def uncertainty_fields() -> Dict[str, Any]:
    return {
        "uncertainty_status": "UNVERIFIED_INFERENTIAL",
        "resample_grain": "CLAIM_LINE",
        "uncertainty_label": (
            "Line-level resample range. Not a validated confidence interval "
            "and not inferential uncertainty."
        ),
    }


def annotate_claimant_exposure(
    metrics: Dict[str, Any],
    unique_members: int,
    *,
    enrollment_measured: bool = False,
) -> Dict[str, Any]:
    """Attach basis flags. Null enrolled-style rates when the claimant count is 0."""
    if enrollment_measured:
        metrics["denominator_basis"] = "ENROLLMENT"
        metrics["enrolled_rate_status"] = "MEASURED"
        metrics["measurement_status"] = "MEASURED"
    else:
        metrics["denominator_basis"] = "CLAIMANT_MONTHS"
        metrics["enrolled_rate_status"] = "NOT_MEASURABLE"
        if unique_members <= 0:
            for key in RATE_KEYS:
                if key in metrics:
                    metrics[key] = None
            metrics["member_months"] = None
            metrics["claims_per_member"] = None
            metrics["measurement_status"] = "NOT_MEASURABLE"
            metrics["measurement_reason"] = "EMPTY_DENOMINATOR"
        else:
            metrics["measurement_status"] = "CLAIMANT_RATIO"
    if "allowed_total_annualized" in metrics and not enrollment_measured:
        metrics["annualization_basis"] = "CLAIMANT_MONTHS"
    metrics["display_labels"] = {
        "utilization": authoritative_measure_label("utilization_per_1k", metrics),
        "cost": authoritative_measure_label("allowed_pmpm", metrics),
        "annualized": annualization_label(metrics),
    }
    return metrics


def presents_as_enrolled(label: str) -> bool:
    """True when a label claims an enrolled denominator without a negation."""
    lowered = label.lower()
    if "not enrolled" in lowered:
        return False
    return "member-month" in lowered or "pmpm" in lowered


def first_present(*values: Any) -> Any:
    """First value that is present. Zero is present. None and blank are not."""
    for value in values:
        if value is None or value == "":
            continue
        return value
    return None


def as_optional_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def paid_rate(metrics: Optional[Dict[str, Any]]) -> Optional[float]:
    """Paid dollars only. Allowed dollars are never a substitute."""
    if not isinstance(metrics, dict):
        return None
    paid = first_present(
        metrics.get("paid_pmpm"),
        metrics.get("paid_pmpm_target"),
        metrics.get("paid_pmpm_total"),
    )
    if paid is None and metrics.get("cost_pmpm_meaning") != "ALLOWED":
        paid = first_present(metrics.get("cost_pmpm"), metrics.get("cost_per_member"))
    return as_optional_float(paid)


def allowed_rate(metrics: Optional[Dict[str, Any]]) -> Optional[float]:
    if not isinstance(metrics, dict):
        return None
    if metrics.get("cost_pmpm_meaning") == "ALLOWED":
        allowed = first_present(metrics.get("cost_pmpm"), metrics.get("allowed_pmpm"))
    else:
        allowed = None
    allowed = first_present(
        metrics.get("allowed_pmpm"),
        metrics.get("allowed_pmpm_target"),
        metrics.get("allowed_pmpm_total"),
        allowed,
    )
    return as_optional_float(allowed)


def prediction_baseline_inputs(baseline_metrics: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Inputs for the prediction generator. Missing rates stay missing. Allowed is not paid."""
    if not isinstance(baseline_metrics, dict) or not baseline_metrics:
        return None
    util = as_optional_float(first_present(
        baseline_metrics.get("util_rate_target_per_1000_mm"),
        baseline_metrics.get("util_rate_total_per_1000_mm"),
        baseline_metrics.get("utilization_per_1k"),
    ))
    paid = paid_rate(baseline_metrics)
    allowed = allowed_rate(baseline_metrics)
    unique = baseline_metrics.get("unique_members")
    member_months = as_optional_float(baseline_metrics.get("member_months"))
    out: Dict[str, Any] = {}
    if util is not None:
        out["utilization_per_1k"] = util
    if paid is not None:
        out["cost_pmpm"] = paid
        out["cost_pmpm_meaning"] = "PAID"
    if allowed is not None:
        out["allowed_pmpm"] = allowed
    if unique not in (None, "", 0):
        out["member_count"] = int(unique)
    if member_months not in (None, 0):
        out["member_months"] = member_months
    return out or None
