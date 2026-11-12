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


def _comparison_block(observation: Dict[str, Any]) -> Dict[str, Any]:
    comparisons = observation.get("comparisons")
    if not isinstance(comparisons, dict):
        return {}
    vs_baseline = comparisons.get("vs_baseline")
    return vs_baseline if isinstance(vs_baseline, dict) else {}


def _metrics_block(observation: Dict[str, Any]) -> Dict[str, Any]:
    metrics = observation.get("metrics")
    return metrics if isinstance(metrics, dict) else {}


def utilization_change_pct(observation: Optional[Dict[str, Any]]) -> Optional[float]:
    """Measured utilization percent change. Missing stays missing. Zero stays zero."""
    if not isinstance(observation, dict):
        return None
    vs_baseline = _comparison_block(observation)
    metrics = _metrics_block(observation)
    return as_optional_float(first_present(
        vs_baseline.get("utilization_change_pct"),
        vs_baseline.get("change_from_baseline_pct"),
        metrics.get("observed_percent_change"),
        metrics.get("utilization_change_pct"),
    ))


def paid_change_amount(observation: Optional[Dict[str, Any]]) -> Optional[float]:
    """Paid dollar change only. Utilization level change is not a dollar amount."""
    if not isinstance(observation, dict):
        return None
    vs_baseline = _comparison_block(observation)
    return as_optional_float(first_present(
        vs_baseline.get("cost_change_pmpm"),
        vs_baseline.get("cost_change"),
    ))


def denominator_class(observation: Optional[Dict[str, Any]]) -> str:
    """ENROLLMENT only when enrollment is verified. Otherwise claimant or unavailable."""
    if not isinstance(observation, dict):
        return "UNAVAILABLE"
    metrics = _metrics_block(observation)
    basis = metrics.get("denominator_basis")
    enrolled_status = metrics.get("enrolled_rate_status")
    if basis == "ENROLLMENT" and enrolled_status == "MEASURED":
        return "ENROLLMENT"
    if basis == "CLAIMANT_MONTHS":
        return "CLAIMANT_MONTHS"
    return "UNAVAILABLE"


def classify_observation_rollup(observation: Dict[str, Any]) -> Dict[str, Any]:
    util = utilization_change_pct(observation)
    cost = paid_change_amount(observation)
    klass = denominator_class(observation)
    cost_included = cost is not None and klass in {"ENROLLMENT", "CLAIMANT_MONTHS"}
    vs_baseline = _comparison_block(observation)
    metrics = _metrics_block(observation)
    member_months = as_optional_float(
        first_present(
            metrics.get("member_months"),
            metrics.get("eligible_member_months"),
            vs_baseline.get("baseline_member_months"),
            (vs_baseline.get("member_months") or {}).get("observed")
            if isinstance(vs_baseline.get("member_months"), dict)
            else None,
        )
    )
    # Period dollars = rate × exposure. Rates alone are not portfolio dollars.
    period_dollars = None
    if cost_included and cost is not None and member_months is not None and member_months > 0:
        period_dollars = cost * member_months
    kind = vs_baseline.get("cost_change_kind")
    if kind is None and vs_baseline.get("cost_change_meaning") == (
        "Change in simulated allowed dollars per enrolled member-month."
    ):
        kind = "simulated_allowed_difference_per_enrolled_member_month"
    return {
        "utilization_change_pct": util,
        "cost_change": cost if cost_included else None,
        "cost_change_period_dollars": period_dollars,
        "member_months": member_months if cost_included else None,
        "cost_change_kind": kind if cost_included else None,
        "cost_change_present": cost is not None,
        "cost_included": cost_included,
        "denominator_class": klass,
        "policy_id": observation.get("policy_id"),
        "policy_name": observation.get("policy_name"),
        "observation_date": observation.get("computed_at") or observation.get("observation_date"),
        "is_predicted": bool(observation.get("is_predicted")),
    }


def aggregate_policy_observation_rollups(observations: Optional[list]) -> Dict[str, Any]:
    """Average measured utilization changes and sum dollar changes that share one denominator.

    Null measurements are excluded. A measured zero is kept. Claimant dollars are not
    labeled as enrolled PMPM. Mixed or missing denominators do not produce a dollar total.
    """
    util_values: list[float] = []
    claimant_values: list[float] = []
    claimant_period_values: list[float] = []
    enrolled_values: list[float] = []
    rows: list[Dict[str, Any]] = []
    null_utilization_count = 0
    continuation_values: list[float] = []
    for observation in observations or []:
        if not isinstance(observation, dict):
            continue
        row = classify_observation_rollup(observation)
        rows.append(row)
        if row["utilization_change_pct"] is None:
            null_utilization_count += 1
        else:
            util_values.append(row["utilization_change_pct"])
        if row["cost_included"] and row["cost_change_kind"] == "observed_versus_frozen_continuation_per_enrolled_member_month":
            continuation_values.append(row["cost_change"])
        elif row["cost_included"] and row["denominator_class"] == "ENROLLMENT":
            enrolled_values.append(row["cost_change"])
        elif row["cost_included"] and row["denominator_class"] == "CLAIMANT_MONTHS":
            claimant_values.append(row["cost_change"])
            if row.get("cost_change_period_dollars") is not None:
                claimant_period_values.append(float(row["cost_change_period_dollars"]))

    if util_values:
        avg_util = sum(util_values) / len(util_values)
        reduction_values = [abs(value) for value in util_values if value < 0]
        util_status = "MEASURED"
        util_reason = None
        reduction = sum(reduction_values) / len(util_values)
    else:
        avg_util = None
        reduction = None
        util_status = "UNAVAILABLE"
        util_reason = "No measured utilization changes. Missing values are not treated as zero."

    mixed = bool(claimant_values) and bool(enrolled_values)
    annualized_cost: Optional[float] = None
    if mixed or (not claimant_values and not enrolled_values):
        total_cost = None
        cost_status = "UNAVAILABLE"
        cost_basis = None
        cost_unit = None
        cost_display_unit = None
        cost_count = 0
        if mixed:
            cost_reason = "Cost changes use more than one denominator basis."
            cost_label = "Cost rollup unavailable because denominator bases differ."
        else:
            cost_reason = (
                "No cost change has a verified enrollment denominator or an explicit claimant-month basis."
            )
            cost_label = "Cost rollup unavailable. Missing denominators are not shown as zero."
    elif enrolled_values:
        total_cost = sum(enrolled_values)
        cost_status = "MEASURED"
        cost_basis = "ENROLLMENT"
        cost_count = len(enrolled_values)
        cost_reason = None
        simulated = [
            row for row in rows
            if row.get("cost_included")
            and row.get("denominator_class") == "ENROLLMENT"
            and row.get("cost_change_kind") == "simulated_allowed_difference_per_enrolled_member_month"
        ]
        observed = [
            row for row in rows
            if row.get("cost_included")
            and row.get("denominator_class") == "ENROLLMENT"
            and row.get("cost_change_kind") == "observed_post_period_allowed_difference_per_enrolled_member_month"
        ]
        if len(simulated) == len(enrolled_values):
            cost_unit = "simulated_allowed_per_enrolled_member_month"
            cost_display_unit = "$ / enrolled member-month"
            cost_label = (
                "Simulated allowed-dollar difference per enrolled member-month. "
                "Negative means simulated allowed is below baseline allowed. "
                "The figure is the sum of policy allowed differences divided by the shared enrolled member-month denominator. "
                "Not measured savings."
            )
        elif len(observed) == len(enrolled_values):
            cost_unit = "observed_post_period_allowed_per_enrolled_member_month"
            cost_display_unit = "$ / enrolled member-month"
            cost_label = (
                "Observed post-period payment-rule allowed difference per enrolled member-month. "
                "The frozen prediction is stored separately and is not subtracted here. Not measured savings."
            )
        else:
            cost_unit = "enrolled_pmpm_sum"
            cost_display_unit = "Σ enrolled ΔPMPM"
            cost_label = "Sum of enrolled member-month dollar changes."
    else:
        # Prefer absolute period dollars (Δ rate × member-months) for executive scale.
        # Fall back to summed rates only when exposure is missing.
        if claimant_period_values and len(claimant_period_values) == len(claimant_values):
            total_cost = sum(claimant_period_values)
            cost_unit = "claimant_period_dollar_sum"
            cost_display_unit = "period $"
            cost_label = (
                "Sum across policies of (observed vs baseline allowed $/claimant-month × member-months). "
                "Period absolute dollars for the observation window — not attributed policy savings. "
                f"Illustrative annualization (×12): ${round(total_cost * 12, 2):,.2f}."
            )
            annualized_cost = total_cost * 12
        else:
            total_cost = sum(claimant_values)
            cost_unit = "claimant_month_dollar_sum"
            cost_display_unit = "claimant-month $"
            cost_label = (
                "Sum of claimant-month dollar rate changes (not enrolled PMPM). "
                "Exposure missing for absolute period $."
            )
        cost_status = "MEASURED"
        cost_basis = "CLAIMANT_MONTHS"
        cost_count = len(claimant_values)
        cost_reason = None

    return {
        "rows": rows,
        "avg_utilization_change_pct": None if avg_util is None else round(avg_util, 2),
        "avg_utilization_change_status": util_status,
        "avg_utilization_change_reason": util_reason,
        "avg_utilization_observation_count": len(util_values),
        "avg_utilization_measured_zero_count": sum(1 for value in util_values if value == 0),
        "avg_utilization_null_count": null_utilization_count,
        "total_utilization_reduction_pct": None if reduction is None else round(reduction, 2),
        "total_cost_impact": None if total_cost is None else round(total_cost, 2),
        "total_cost_impact_annualized": None if annualized_cost is None else round(annualized_cost, 2),
        "total_cost_impact_status": cost_status,
        "total_cost_impact_reason": cost_reason,
        "total_cost_impact_unit": cost_unit,
        "total_cost_impact_display_unit": cost_display_unit,
        "total_cost_impact_label": cost_label,
        "total_cost_observation_count": cost_count,
        "cost_denominator_basis": cost_basis,
        "claimant_cost_change_sum": None if not claimant_values else round(sum(claimant_values), 2),
        "claimant_cost_period_dollar_sum": None
        if not claimant_period_values
        else round(sum(claimant_period_values), 2),
        "claimant_cost_observation_count": len(claimant_values),
        "enrolled_cost_change_sum": None if not enrolled_values else round(sum(enrolled_values), 2),
        "enrolled_cost_observation_count": len(enrolled_values),
        "continuation_allowed_difference": None if not continuation_values else round(sum(continuation_values), 2),
        "continuation_observation_count": len(continuation_values),
        "continuation_allowed_difference_label": (
            "Descriptive forecast-versus-observation difference. "
            "Each value is that policy's observed post-period allowed minus its frozen historical-rate continuation, "
            "divided by the shared enrolled member-months. The figures are then summed. "
            "Members and claims can match more than one policy, so the sum double-counts overlap. "
            "It is not a portfolio savings total, not a payment-rule effect, and not an intervention effect."
            if continuation_values else None
        ),
    }


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
