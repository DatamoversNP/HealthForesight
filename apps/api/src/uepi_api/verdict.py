"""Phase 2: Versioned verdict logic.

Computes policy verdict (ON_TRACK | AT_RISK | BACKFIRE | INCONCLUSIVE)
and recommendation from comparison metrics and behavioral explanation.
"""
from typing import Any, Dict, Optional, Tuple

VERDICT_RULE_VERSION = "v1.1-endpoints"

_UTIL_ENDPOINT_IDS = {
    "utilization_per_1k",
    "util_rate_target_per_1000_mm",
    "util_rate_total_per_1000_mm",
}
_COST_ENDPOINT_IDS = {
    "allowed_pmpm",
    "allowed_pmpm_target",
    "allowed_pmpm_total",
    "paid_pmpm",
    "paid_pmpm_target",
    "paid_pmpm_total",
    "cost_pmpm",
    "cost_per_member",
}


def endpoint_contract_from_policy(policy: Optional[Dict[str, Any]]) -> Optional[list]:
    """Read a policy endpoint contract. Absence means the verdict stays inconclusive."""
    if not isinstance(policy, dict):
        return None
    direct = policy.get("required_endpoints")
    meta = policy.get("policy_metadata_json") or policy.get("metadata") or {}
    if not isinstance(meta, dict):
        meta = {}
    measurement = meta.get("measurement") if isinstance(meta.get("measurement"), dict) else {}
    contract = direct or meta.get("required_endpoints") or measurement.get("required_endpoints")
    if not isinstance(contract, list) or not contract:
        return None
    return contract


def _endpoint_change(endpoint: Dict[str, Any], vs_baseline: Dict[str, Any]) -> Any:
    metric_id = str(endpoint.get("metric_id") or "")
    if metric_id in _UTIL_ENDPOINT_IDS:
        change = vs_baseline.get("utilization_change_pct")
        if change is None:
            change = vs_baseline.get("change_from_baseline_pct")
        return change
    if metric_id in _COST_ENDPOINT_IDS:
        return vs_baseline.get("cost_change_pct")
    return vs_baseline.get(f"{metric_id}_change_pct")


def _direction_met(direction: str, change: float) -> Optional[bool]:
    if direction == "decrease":
        return change <= 0
    if direction == "increase":
        return change >= 0
    if direction == "monitor_only":
        return None
    return None


def compute_verdict(
    comparisons: Dict[str, Any],
    behavioral_explanation: Dict[str, Any],
    required_endpoints: list | None = None,
) -> Tuple[str, str, str]:
    """Compute verdict status, reason, and recommendation.

    Returns:
        (verdict_status, verdict_reason, recommendation)
    """
    if not required_endpoints:
        return (
            "INCONCLUSIVE",
            "No policy endpoint contract is defined. A change in utilization or cost is not a verdict.",
            "Declare the required endpoints and their direction before scoring this policy.",
        )
    if not comparisons:
        return (
            "INCONCLUSIVE",
            "No comparison data available for the required endpoints.",
            "Run baseline comparisons for the declared endpoints.",
        )

    vs_baseline = comparisons.get("vs_baseline") or {}
    scored = []
    for endpoint in required_endpoints:
        if not isinstance(endpoint, dict):
            return (
                "INCONCLUSIVE",
                "The endpoint contract is not readable.",
                "Each endpoint needs a metric id and a direction.",
            )
        direction = str(endpoint.get("direction") or "")
        raw = _endpoint_change(endpoint, vs_baseline)
        try:
            change = float(raw) if raw is not None else None
        except (TypeError, ValueError):
            change = None
        met = _direction_met(direction, change) if change is not None else None
        if direction == "monitor_only":
            continue
        if direction not in {"decrease", "increase"} or change is None or met is None:
            return (
                "INCONCLUSIVE",
                f"Required endpoint {endpoint.get('metric_id') or '?'} has no measured change.",
                "Do not score a missing endpoint as on track.",
            )
        scored.append((endpoint, change, met))

    if not scored:
        return (
            "INCONCLUSIVE",
            "The endpoint contract is monitor-only, so it does not produce ON_TRACK.",
            "Add a directional endpoint before scoring.",
        )

    missed = [item for item in scored if not item[2]]
    if not missed:
        names = ", ".join(str(item[0].get("metric_id")) for item in scored)
        return (
            "ON_TRACK",
            f"Required endpoints moved in the declared direction: {names}.",
            "Continue monitoring the declared endpoints.",
        )

    risk_factors = (behavioral_explanation or {}).get("risk_factors") or []
    has_warning = bool(risk_factors or (behavioral_explanation or {}).get("actionable_insights"))
    detail = ", ".join(
        f"{item[0].get('metric_id')} {item[1]:+.1f}% vs {item[0].get('direction')}"
        for item in missed
    )
    if has_warning:
        return (
            "BACKFIRE",
            f"A required endpoint missed its direction and behavioral warnings are present: {detail}.",
            "Review the declared endpoint and the behavioral explanation.",
        )
    return (
        "AT_RISK",
        f"A required endpoint missed its direction: {detail}.",
        "Review the declared endpoint. Cost is not required unless the contract lists it.",
    )
