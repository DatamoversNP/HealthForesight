"""Independent analytical readiness flags per policy.

CONFIGURED → BASELINE_READY → FORECAST_READY → OBSERVATION_READY → IMPACT_ASSESSABLE

These are capability flags, not a mandatory linear workflow. Missing data never
produces invented baselines, forecasts, or causal estimates.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from uuid import UUID


READINESS_FLAGS = (
    "CONFIGURED",
    "BASELINE_READY",
    "FORECAST_READY",
    "OBSERVATION_READY",
    "IMPACT_ASSESSABLE",
)


def _mechanism_family(policy_type: Optional[str], name: Optional[str] = None) -> str:
    t = (policy_type or "").upper()
    n = (name or "").upper()
    if any(k in t or k in n for k in ("CODING", "REIMBURSEMENT", "NCCI", "FEE", "MODIFIER", "BUNDL")):
        return "REIMBURSEMENT"
    if any(k in t or k in n for k in ("NCD", "LCD", "MEDICARE_COVERAGE")):
        return "COVERAGE"
    if any(k in t for k in ("PRIOR_AUTH", "UM", "STEP", "SITE_OF_CARE", "QUANTITY")):
        return "UTILIZATION_MANAGEMENT"
    if "PHARMACY" in t or "FORMULARY" in t or "SPECIALTY" in t:
        return "PHARMACY"
    return "GENERAL"


def compute_policy_readiness(
    *,
    policy: Dict[str, Any],
    has_baseline: bool,
    has_forecast: bool,
    has_observation: bool,
    causal_supported: bool,
    causal_classification: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute readiness flags and mechanism-appropriate measurement notes."""
    pid = str(policy.get("id") or policy.get("policy_id") or "")
    name = policy.get("name") or policy.get("policy_name")
    ptype = policy.get("policy_type")
    family = _mechanism_family(ptype, name)

    configured = bool(pid and name)
    flags = {
        "CONFIGURED": configured,
        "BASELINE_READY": configured and has_baseline,
        "FORECAST_READY": configured and has_forecast,
        "OBSERVATION_READY": configured and has_observation,
        "IMPACT_ASSESSABLE": configured and has_observation and causal_supported,
    }

    primary_metrics: List[str]
    if family == "REIMBURSEMENT":
        primary_metrics = [
            "allowed_paid_unit_price",
            "edit_denial_rate",
            "units",
            "net_payment_exposure",
        ]
        secondary = ["utilization", "coding_response", "site_mix"]
        note = (
            "Reimbursement primary impact is unit price / payment rules. "
            "Do not auto-model as utilization reduction."
        )
    elif family == "COVERAGE":
        primary_metrics = [
            "eligible_population",
            "covered_service_utilization",
            "coverage_denial_patterns",
            "substitution",
        ]
        secondary = ["net_cost", "access_guardrails"]
        note = (
            "Long-standing NCD/LCD may be OBSERVATION_READY without IMPACT_ASSESSABLE "
            "if pre-implementation comparison data is unavailable."
        )
    elif family == "UTILIZATION_MANAGEMENT":
        primary_metrics = [
            "utilization_per_1k",
            "allowed_pmpm",
            "site_of_care_mix",
            "authorization_patterns",
        ]
        secondary = ["provider_behavior", "substitution"]
        note = "UM metrics aligned with MRI lifecycle reference experience."
    else:
        primary_metrics = ["utilization_per_1k", "allowed_pmpm"]
        secondary = []
        note = "General policy — configure mechanism-specific metrics before decision-grade use."

    causal_status = "NOT_ESTIMABLE"
    if causal_supported and (causal_classification or "").upper() == "CAUSAL":
        causal_status = "SUPPORTED"
    elif has_observation and not causal_supported:
        causal_status = "INCONCLUSIVE"
    elif not has_observation:
        causal_status = "NOT_ESTIMABLE"

    missing: List[str] = []
    if not flags["BASELINE_READY"]:
        missing.append("baseline_or_reference_period_data")
    if not flags["FORECAST_READY"]:
        missing.append("persisted_predicted_impact")
    if not flags["OBSERVATION_READY"]:
        missing.append("persisted_observation")
    if not flags["IMPACT_ASSESSABLE"]:
        missing.append("validated_comparison_design_for_causal")

    return {
        "policy_id": pid,
        "policy_name": name,
        "policy_type": ptype,
        "mechanism_family": family,
        "flags": flags,
        "primary_metrics": primary_metrics,
        "secondary_metrics": secondary,
        "measurement_note": note,
        "causal_status": causal_status,
        "missing_for_full_lifecycle": missing,
        "never_invent": True,
    }


def build_portfolio_readiness(
    *,
    policies: List[Dict[str, Any]],
    baseline_policy_ids: Set[str],
    forecast_policy_ids: Set[str],
    observation_policy_ids: Set[str],
    impact_assessable_ids: Set[str],
    causal_by_policy: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    causal_by_policy = causal_by_policy or {}
    rows = []
    for p in policies:
        pid = str(p.get("id") or p.get("policy_id") or "")
        rows.append(
            compute_policy_readiness(
                policy=p,
                has_baseline=pid in baseline_policy_ids,
                has_forecast=pid in forecast_policy_ids,
                has_observation=pid in observation_policy_ids,
                causal_supported=pid in impact_assessable_ids,
                causal_classification=causal_by_policy.get(pid),
            )
        )

    by_family: Dict[str, Dict[str, int]] = {}
    for r in rows:
        fam = r["mechanism_family"]
        bucket = by_family.setdefault(
            fam,
            {
                "inventory": 0,
                "configured": 0,
                "baseline_ready": 0,
                "forecast_ready": 0,
                "observation_ready": 0,
                "impact_assessable": 0,
            },
        )
        bucket["inventory"] += 1
        f = r["flags"]
        if f["CONFIGURED"]:
            bucket["configured"] += 1
        if f["BASELINE_READY"]:
            bucket["baseline_ready"] += 1
        if f["FORECAST_READY"]:
            bucket["forecast_ready"] += 1
        if f["OBSERVATION_READY"]:
            bucket["observation_ready"] += 1
        if f["IMPACT_ASSESSABLE"]:
            bucket["impact_assessable"] += 1

    return {
        "calculation_version": "policy-readiness-v1",
        "policies": rows,
        "by_mechanism_family": by_family,
        "totals": {
            "inventory": len(rows),
            "configured": sum(1 for r in rows if r["flags"]["CONFIGURED"]),
            "baseline_ready": sum(1 for r in rows if r["flags"]["BASELINE_READY"]),
            "forecast_ready": sum(1 for r in rows if r["flags"]["FORECAST_READY"]),
            "observation_ready": sum(1 for r in rows if r["flags"]["OBSERVATION_READY"]),
            "impact_assessable": sum(1 for r in rows if r["flags"]["IMPACT_ASSESSABLE"]),
        },
        "note": (
            "Catalog inventory counts are not analytical readiness. "
            "All numbers derive from persisted baselines/forecasts/observations — never placeholders."
        ),
    }


def load_portfolio_readiness(tenant_id: UUID) -> Dict[str, Any]:
    from uepi_api.storage_policies import list_policies
    from uepi_api.storage_observations import list_observations
    from uepi_api.storage_policy_predicted_impact import list_latest_predicted_impacts
    from uepi_api.services.enterprise_intelligence_fixtures import MRI_POLICY_ID

    policies = list_policies(tenant_id, summary=True) or []
    observations = list_observations(
        tenant_id=tenant_id, latest_only=True, summary=True, limit=2000
    )
    obs_ids = {str(o.get("policy_id")) for o in observations if o.get("policy_id")}
    predicted = list_latest_predicted_impacts(tenant_id, limit=2000)
    forecast_ids = {str(p.get("policy_id")) for p in predicted if p.get("policy_id")}

    # Baselines: best-effort via storage if available
    baseline_ids: Set[str] = set()
    try:
        from uepi_api.storage_baselines import list_baselines

        for b in list_baselines(tenant_id, summary=True, limit=2000) or []:
            pid = b.get("policy_id")
            if pid:
                baseline_ids.add(str(pid))
    except Exception:
        # Do not invent baselines; leave empty and report via missing flags
        baseline_ids = set()

    # Causal: only MRI fixture currently impact-assessable on synthetic design
    impact_ids: Set[str] = set()
    causal_by: Dict[str, str] = {}
    if MRI_POLICY_ID in obs_ids or any(
        str(p.get("id")) == MRI_POLICY_ID for p in policies
    ):
        # Labeled synthetic — IMPACT_ASSESSABLE only if we explicitly allow synthetic for demo
        # Platform rule: synthetic must be labeled; flag remains False for production path.
        # Keep IMPACT_ASSESSABLE false until real comparison design exists.
        causal_by[MRI_POLICY_ID] = "CAUSAL_SYNTHETIC_FIXTURE"
        # Not production-qualified — do not set impact_assessable from fixture alone
        impact_ids = set()

    return build_portfolio_readiness(
        policies=policies,
        baseline_policy_ids=baseline_ids,
        forecast_policy_ids=forecast_ids,
        observation_policy_ids=obs_ids,
        impact_assessable_ids=impact_ids,
        causal_by_policy=causal_by,
    )
