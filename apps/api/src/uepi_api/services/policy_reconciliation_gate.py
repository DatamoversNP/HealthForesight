"""Policy Coverage and Analytical Readiness Reconciliation Gate.

For every policy version, explain inventory provenance, applicability,
baseline/forecast/observation readiness, causal defensibility, and verdict
readiness — without inventing missing evidence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from uepi_api.services.policy_analytical_readiness import compute_policy_readiness
from uepi_api.services.objectives_health import CALCULATION_VERSION as OH_CALC_VERSION


GATE_VERSION = "policy-reconciliation-gate-v1"


def reconcile_policy_version(
    *,
    policy: Dict[str, Any],
    inventory_family: str,
    inventory_status: str,
    source_provenance: Optional[Dict[str, Any]],
    applicability: Optional[Dict[str, Any]],
    has_baseline: bool,
    has_forecast: bool,
    forecast_evidence_tier: Optional[str],
    has_observation: bool,
    observation_verdict: Optional[str],
    causal_status: str,
    causal_limitations: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Single policy-version reconciliation explanation."""
    readiness = compute_policy_readiness(
        policy=policy,
        has_baseline=has_baseline,
        has_forecast=has_forecast,
        has_observation=has_observation,
        causal_supported=causal_status == "SUPPORTED",
        causal_classification="CAUSAL" if causal_status == "SUPPORTED" else None,
    )

    why_in_inventory = (
        f"Classified under family '{inventory_family}' with status {inventory_status}."
    )
    if inventory_status in (
        "SOURCE_ADAPTER_MISSING",
        "FIXTURE_ONLY_NOT_RECONCILED",
        "CATALOG_ROWS_PRESENT_UNRECONCILED",
    ):
        why_in_inventory += (
            " Present in the working catalog; not yet reconciled to an authoritative source manifest."
        )

    source = source_provenance or {
        "status": "UNKNOWN_OR_UNRECONCILED",
        "note": "Authoritative source adapter not yet attached for this policy version.",
    }

    appl = applicability or {
        "status": "NOT_RESOLVED",
        "note": "Applicability not resolved for selected payer/program/jurisdiction/date.",
    }

    baseline_explanation = (
        "Baseline (or reference-period) data exists and is marked BASELINE_READY."
        if has_baseline
        else "Baseline data is missing or insufficient — no decision-grade baseline produced."
    )

    if has_forecast:
        tier = (forecast_evidence_tier or "UNKNOWN").upper()
        if tier.startswith("C") or "SCENARIO" in tier or "ASSUMPTION" in tier:
            forecast_explanation = (
                f"Forecast present as scenario/assumption-driven ({tier}) — not an empirically "
                "validated point estimate."
            )
            forecast_mode = "SCENARIO_ONLY"
        else:
            forecast_explanation = f"Persisted predicted impact exists (evidence tier: {tier})."
            forecast_mode = "SUPPORTED"
    else:
        forecast_explanation = "No persisted predicted impact — forecast unavailable (not invented)."
        forecast_mode = "UNAVAILABLE"

    observation_explanation = (
        f"Observation available; observation verdict={observation_verdict or 'PRESENT'}."
        if has_observation
        else "No observation yet — observed performance unavailable (forecast must not substitute)."
    )

    if causal_status == "SUPPORTED":
        causal_explanation = "Causal assessment marked supported under documented identification assumptions."
    elif causal_status == "INCONCLUSIVE":
        causal_explanation = (
            "Observations exist but comparison design is insufficient for a defensible causal claim."
        )
    else:
        causal_explanation = "Causal assessment not estimable for this policy version."
    if causal_limitations:
        causal_explanation += " Limitations: " + "; ".join(causal_limitations[:5])

    # Verdict readiness
    if has_observation and observation_verdict and observation_verdict not in ("UNKNOWN",):
        if observation_verdict == "INCONCLUSIVE":
            verdict_state = "INCONCLUSIVE"
            verdict_explanation = (
                "Verdict computed but inconclusive — evidence insufficient for ON_TRACK/AT_RISK/BACKFIRE."
            )
        else:
            verdict_state = "READY"
            verdict_explanation = (
                f"Verdict ready from observation comparisons (status={observation_verdict}); "
                f"aligned with Objectives Health / Policy Verdicts calculation ({OH_CALC_VERSION} / compute_verdict)."
            )
    elif has_forecast and not has_observation:
        verdict_state = "LIMITED"
        verdict_explanation = (
            "Forecast exists without observation — portfolio may show forecast readiness, "
            "but observed performance / verdict remains UNKNOWN. Forecast ≠ observed health."
        )
    else:
        verdict_state = "INCONCLUSIVE"
        verdict_explanation = "Insufficient evidence for a policy impact verdict."

    return {
        "gate_version": GATE_VERSION,
        "policy_id": readiness["policy_id"],
        "policy_name": readiness["policy_name"],
        "policy_type": readiness["policy_type"],
        "mechanism_family": readiness["mechanism_family"],
        "explanations": {
            "why_in_inventory": why_in_inventory,
            "authoritative_definition_source": source,
            "applicability": appl,
            "baseline": baseline_explanation,
            "forecast": forecast_explanation,
            "observations": observation_explanation,
            "causal_assessment": causal_explanation,
            "verdict": verdict_explanation,
        },
        "states": {
            "inventory_status": inventory_status,
            "inventory_family": inventory_family,
            "forecast_mode": forecast_mode,
            "causal_status": causal_status,
            "verdict_state": verdict_state,
            "readiness_flags": readiness["flags"],
        },
        "primary_metrics": readiness["primary_metrics"],
        "measurement_note": readiness["measurement_note"],
        "missing_for_full_lifecycle": readiness["missing_for_full_lifecycle"],
        "never_invent": True,
    }


def build_reconciliation_gate_for_tenant(
    *,
    tenant_id: UUID,
    policies: List[Dict[str, Any]],
    baseline_ids: set,
    forecast_by_policy: Dict[str, Dict[str, Any]],
    observation_by_policy: Dict[str, Dict[str, Any]],
    inventory_classify,
) -> Dict[str, Any]:
    rows = []
    for p in policies:
        pid = str(p.get("id") or p.get("policy_id") or "")
        if not pid:
            continue
        fam, inv_status = inventory_classify(p)
        obs = observation_by_policy.get(pid)
        fc = forecast_by_policy.get(pid)
        # Real causal designs are not production-qualified yet.
        # Observation without validated comparison design → INCONCLUSIVE (never invent SUPPORTED).
        causal_status = "INCONCLUSIVE" if obs else "NOT_ESTIMABLE"
        rows.append(
            reconcile_policy_version(
                policy=p,
                inventory_family=fam,
                inventory_status=inv_status,
                source_provenance=None,
                applicability=None,
                has_baseline=pid in baseline_ids,
                has_forecast=pid in forecast_by_policy,
                forecast_evidence_tier=(fc or {}).get("evidence_tier")
                or (fc or {}).get("prediction_method"),
                has_observation=obs is not None,
                observation_verdict=(obs or {}).get("verdict"),
                causal_status=causal_status,
            )
        )

    summary = {
        "policies": len(rows),
        "verdict_ready": sum(1 for r in rows if r["states"]["verdict_state"] == "READY"),
        "verdict_limited": sum(1 for r in rows if r["states"]["verdict_state"] == "LIMITED"),
        "verdict_inconclusive": sum(
            1 for r in rows if r["states"]["verdict_state"] == "INCONCLUSIVE"
        ),
        "forecast_scenario_only": sum(
            1 for r in rows if r["states"]["forecast_mode"] == "SCENARIO_ONLY"
        ),
        "impact_assessable": sum(
            1 for r in rows if r["states"]["readiness_flags"].get("IMPACT_ASSESSABLE")
        ),
    }
    return {
        "gate_version": GATE_VERSION,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "tenant_id": str(tenant_id),
        "summary": summary,
        "policies": rows,
        "note": (
            "Reconciliation gate explains readiness; it does not invent baselines, forecasts, "
            "observations, or causal effects."
        ),
    }


def load_reconciliation_gate(tenant_id: UUID) -> Dict[str, Any]:
    from uepi_api.storage_policies import list_policies
    from uepi_api.storage_observations import list_observations
    from uepi_api.storage_policy_predicted_impact import list_latest_predicted_impacts
    from uepi_api.verdict import compute_verdict
    from uepi_api.services.policy_inventory_manifest import _classify_catalog_row, DECLARED_SOURCE_FAMILIES

    adapter_by_family = {f["family_id"]: f["adapter_status"] for f in DECLARED_SOURCE_FAMILIES}

    def inventory_classify(p: Dict[str, Any]):
        fam = _classify_catalog_row(p)
        return fam, adapter_by_family.get(fam, "UNKNOWN")

    policies = list_policies(tenant_id, summary=True) or []
    baseline_ids = set()
    try:
        from uepi_api.storage_baselines import list_baselines

        for b in list_baselines(tenant_id, summary=True, limit=2000) or []:
            if b.get("policy_id"):
                baseline_ids.add(str(b["policy_id"]))
    except Exception:
        pass

    forecast_by_policy: Dict[str, Dict[str, Any]] = {}
    for pi in list_latest_predicted_impacts(tenant_id, limit=2000) or []:
        pid = str(pi.get("policy_id") or "")
        if pid:
            forecast_by_policy[pid] = pi

    observation_by_policy: Dict[str, Dict[str, Any]] = {}
    for obs in list_observations(
        tenant_id=tenant_id, latest_only=True, summary=True, limit=2000
    ) or []:
        pid = str(obs.get("policy_id") or "")
        if not pid:
            continue
        comparisons = obs.get("comparisons") or {}
        behavioral = obs.get("behavioral_explanation") or {}
        verdict_status, _, _ = compute_verdict(comparisons, behavioral)
        observation_by_policy[pid] = {
            **obs,
            "verdict": verdict_status,
        }

    return build_reconciliation_gate_for_tenant(
        tenant_id=tenant_id,
        policies=policies,
        baseline_ids=baseline_ids,
        forecast_by_policy=forecast_by_policy,
        observation_by_policy=observation_by_policy,
        inventory_classify=inventory_classify,
    )
