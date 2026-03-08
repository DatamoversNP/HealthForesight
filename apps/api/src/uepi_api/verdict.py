"""Phase 2: Versioned verdict logic.

Computes policy verdict (ON_TRACK | AT_RISK | BACKFIRE | INCONCLUSIVE)
and recommendation from comparison metrics and behavioral explanation.
"""
from typing import Any, Dict, Tuple

VERDICT_RULE_VERSION = "v1.0"


def compute_verdict(
    comparisons: Dict[str, Any],
    behavioral_explanation: Dict[str, Any],
) -> Tuple[str, str, str]:
    """Compute verdict status, reason, and recommendation.

    Returns:
        (verdict_status, verdict_reason, recommendation)
    """
    if not comparisons:
        return (
            "INCONCLUSIVE",
            "No comparison data available.",
            "Run baseline and prediction comparisons to get a verdict.",
        )

    vs_baseline = comparisons.get("vs_baseline") or {}
    vs_predicted = comparisons.get("vs_predicted") or {}
    by_measure_baseline = vs_baseline.get("comparison_by_measure") or {}
    by_measure_predicted = vs_predicted.get("comparison_by_measure") or {}

    # Utilization and cost from comparison_by_measure (canonical keys)
    util_key = "util_rate_target_per_1000_mm"
    cost_key = "allowed_pmpm_target"
    obs_util = by_measure_baseline.get(util_key, {}).get("observed") or by_measure_predicted.get(util_key, {}).get("observed")
    base_util = by_measure_baseline.get(util_key, {}).get("baseline")
    pred_util = by_measure_predicted.get(util_key, {}).get("predicted")
    obs_cost = by_measure_baseline.get(cost_key, {}).get("observed") or by_measure_predicted.get(cost_key, {}).get("observed")
    base_cost = by_measure_baseline.get(cost_key, {}).get("baseline")
    pred_cost = by_measure_predicted.get(cost_key, {}).get("predicted")

    # Fallback to legacy comparison fields
    if obs_util is None:
        obs_util = vs_baseline.get("observed_utilization_per_1k") or vs_predicted.get("observed_utilization_per_1k")
    if base_util is None:
        base_util = vs_baseline.get("baseline_utilization_per_1k")
    if pred_util is None:
        pred_util = vs_predicted.get("predicted_utilization_per_1k")
    if obs_cost is None:
        obs_cost = vs_baseline.get("observed_cost_pmpm") or vs_predicted.get("observed_cost_pmpm")
    if base_cost is None:
        base_cost = vs_baseline.get("baseline_cost_pmpm")
    if pred_cost is None:
        pred_cost = vs_predicted.get("predicted_cost_pmpm")

    # Percent changes (vs baseline)
    util_change_pct = vs_baseline.get("utilization_change_pct") or vs_baseline.get("change_from_baseline_pct")
    cost_change_pct = vs_baseline.get("cost_change_pct")

    # Prediction error
    util_error_pct = vs_predicted.get("utilization_prediction_error_pct")
    cost_error_pct = vs_predicted.get("cost_prediction_error_pct")

    # Parse percent changes first so outcome drives verdict; behavioral signals only escalate.
    try:
        u_c = float(util_change_pct) if util_change_pct is not None else None
        c_c = float(cost_change_pct) if cost_change_pct is not None else None
    except (TypeError, ValueError):
        u_c, c_c = None, None

    # Rule v1.0: on track if utilization and cost both at or below baseline (improvement or flat)
    # Check this first so good outcomes are not overridden by generic behavioral notes.
    if u_c is not None and c_c is not None:
        if u_c <= 0 and c_c <= 0:
            return (
                "ON_TRACK",
                "Observed utilization and cost are at or below baseline; policy is performing as intended.",
                "Continue monitoring; consider expanding scope if sustained.",
            )
        if u_c > 5 or c_c > 10:
            # Bad numbers: consider backfire only if we also have strong behavioral signals
            risk_factors = (behavioral_explanation or {}).get("risk_factors") or []
            recommendations_beh = (behavioral_explanation or {}).get("recommendations") or []
            has_early_warning = bool(
                risk_factors or
                (behavioral_explanation or {}).get("actionable_insights") or
                (behavioral_explanation or {}).get("provider_response", {}).get("recommendations")
            )
            if has_early_warning and (risk_factors or len(recommendations_beh) > 1):
                return (
                    "BACKFIRE",
                    "Observed utilization or cost above baseline with early warning signals: behavioral risk factors or provider/patient response concerns.",
                    "Review behavioral explanation and consider policy adjustment or targeted interventions.",
                )
            return (
                "AT_RISK",
                f"Observed utilization or cost is above baseline (util change: {u_c:.1f}%, cost change: {c_c:.1f}%).",
                "Review policy design and execution; check for substitution or unintended effects.",
            )

    # Prediction error based
    try:
        u_err = float(util_error_pct) if util_error_pct is not None else None
        c_err = float(cost_error_pct) if cost_error_pct is not None else None
    except (TypeError, ValueError):
        u_err, c_err = None, None

    if u_err is not None and abs(u_err) > 20:
        return (
            "AT_RISK",
            f"Observed utilization deviates from prediction by {u_err:.1f}%.",
            "Validate assumptions and data; consider recalibrating forecast.",
        )
    if c_err is not None and abs(c_err) > 25:
        return (
            "AT_RISK",
            f"Observed cost deviates from prediction by {c_err:.1f}%.",
            "Validate assumptions and data; review cost drivers.",
        )

    if u_c is not None or c_c is not None or u_err is not None or c_err is not None:
        return (
            "ON_TRACK",
            "Observed impact is within acceptable range vs baseline and prediction.",
            "Continue monitoring.",
        )

    return (
        "INCONCLUSIVE",
        "Insufficient comparison metrics to determine verdict.",
        "Ensure baseline and predicted impact are available and re-run observation.",
    )
