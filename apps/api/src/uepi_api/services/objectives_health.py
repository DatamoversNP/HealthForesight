"""Deterministic Objectives Health snapshot.

Stability contract (same tenant, permissions, policy set, observations,
predicted impacts, decisions, calculation_version):
- Two consecutive builds return equal JSON (aside from generated_at).
- Status comes from the same verdict engine as /policy-verdicts.
- Forecasts come from persisted predicted-impact rows — never N+1 probes
  and never silent synthetic fill when data is missing.
- Predicted-only metrics are never treated as observed health.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

CALCULATION_VERSION = "objectives-health-v1"

OBJECTIVE_LABELS = {
    "PRIOR_AUTH": "Utilization & cost management",
    "STEP_THERAPY": "Appropriate therapy progression",
    "SITE_OF_CARE": "Site-of-care optimization",
    "QUANTITY_LIMIT": "Quantity and cost control",
    "UM": "Utilization management",
}


def _objective_label(policy_type: Optional[str]) -> str:
    return OBJECTIVE_LABELS.get((policy_type or "").upper(), "Policy objective")


def _verdict_to_health(verdict: str) -> str:
    if verdict == "ON_TRACK":
        return "on_track"
    if verdict in ("AT_RISK", "BACKFIRE"):
        return "at_risk"
    # UNKNOWN / INCONCLUSIVE — insufficient evidence, not invented on_track
    return "no_data"


def _verdict_display_label(status: str) -> str:
    return {
        "ON_TRACK": "Saving / on track",
        "AT_RISK": "At risk",
        "BACKFIRE": "Backfire risk",
        "INCONCLUSIVE": "Inconclusive",
        "UNKNOWN": "No observation yet",
    }.get(status, status)


def build_objectives_health_snapshot(
    *,
    tenant_id: UUID,
    policies: List[Dict[str, Any]],
    latest_observations: List[Dict[str, Any]],
    predicted_impacts: List[Dict[str, Any]],
    decisions: List[Dict[str, Any]],
    generated_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Pure builder — unit-testable for reproducibility."""
    from uepi_api.verdict import compute_verdict

    # Stable policy order
    policy_rows_src = sorted(
        policies,
        key=lambda p: (
            (p.get("name") or p.get("policy_name") or "").lower(),
            str(p.get("id") or p.get("policy_id") or ""),
        ),
    )

    by_policy_obs: Dict[str, List[dict]] = defaultdict(list)
    for obs in latest_observations:
        pid = str(obs.get("policy_id") or "")
        if pid:
            by_policy_obs[pid].append(obs)
    for pid in by_policy_obs:
        by_policy_obs[pid].sort(
            key=lambda x: (x.get("observation_period_end") or "", x.get("computed_at") or ""),
            reverse=True,
        )

    forecast_ids: Set[str] = set()
    for pi in predicted_impacts:
        pid = str(pi.get("policy_id") or "")
        metrics = pi.get("metrics") or {}
        if pid and isinstance(metrics, dict) and metrics:
            forecast_ids.add(pid)

    decision_ids: Set[str] = set()
    for d in decisions:
        pid = str(d.get("policy_id") or d.get("policyId") or "")
        if pid:
            decision_ids.add(pid)

    policy_rows: List[Dict[str, Any]] = []
    backfire_ids: List[str] = []
    observation_ids: List[str] = []
    behavior_ids: List[str] = []
    forecast_id_list: List[str] = []

    for p in policy_rows_src:
        pid = str(p.get("id") or p.get("policy_id") or "")
        if not pid:
            continue
        name = p.get("name") or p.get("policy_name") or "Unnamed"
        ptype = p.get("policy_type") or "UM"
        eff = p.get("effective_period") or {}
        policy_effective_date = eff.get("start_date") if isinstance(eff, dict) else None

        obs_list = by_policy_obs.get(pid) or []
        if obs_list:
            latest = obs_list[0]
            comparisons = latest.get("comparisons") or {}
            behavioral = latest.get("behavioral_explanation") or {}
            vs_b = comparisons.get("vs_baseline") or {}
            vs_p = comparisons.get("vs_predicted") or {}
            verdict_status, verdict_reason, recommendation = compute_verdict(comparisons, behavioral)
            cost_pmpm = vs_b.get("cost_change_pmpm")
            util_pct = vs_b.get("utilization_change_pct") or vs_b.get("change_from_baseline_pct")
            observation_ids.append(pid)
            if verdict_status == "BACKFIRE":
                backfire_ids.append(pid)
            beh = behavioral if isinstance(behavioral, dict) else {}
            if beh.get("provider_response") or beh.get("patient_response") or beh.get(
                "provider_archetype_shares"
            ) or beh.get("patient_response_shares"):
                behavior_ids.append(pid)
            policy_rows.append(
                {
                    "policy_id": pid,
                    "name": name,
                    "policy_type": ptype,
                    "objective_label": _objective_label(ptype),
                    "status": _verdict_to_health(verdict_status),
                    "verdict": verdict_status,
                    "verdict_label": _verdict_display_label(verdict_status),
                    "utilization_change_pct": util_pct,
                    "cost_impact_pmpm": cost_pmpm,
                    "confidence_pct": vs_p.get("prediction_accuracy_pct"),
                    "observation_count": len(obs_list),
                    "observation_id": latest.get("observation_id"),
                    "policy_effective_date": policy_effective_date,
                    "latest_observation_period_end": latest.get("observation_period_end"),
                    "verdict_reason": verdict_reason or latest.get("verdict_reason") or "",
                    "recommendation": recommendation or latest.get("recommendation") or "",
                    "has_forecast": pid in forecast_ids,
                    "has_decision": pid in decision_ids,
                    "is_predicted_only": False,
                }
            )
        else:
            policy_rows.append(
                {
                    "policy_id": pid,
                    "name": name,
                    "policy_type": ptype,
                    "objective_label": _objective_label(ptype),
                    "status": "no_data",
                    "verdict": "UNKNOWN",
                    "verdict_label": "No observation yet",
                    "utilization_change_pct": None,
                    "cost_impact_pmpm": None,
                    "confidence_pct": None,
                    "observation_count": 0,
                    "observation_id": None,
                    "policy_effective_date": policy_effective_date,
                    "latest_observation_period_end": None,
                    "verdict_reason": "Run baseline and create an observation to get a verdict.",
                    "recommendation": "Add observed data and run comparison.",
                    "has_forecast": pid in forecast_ids,
                    "has_decision": pid in decision_ids,
                    "is_predicted_only": False,
                }
            )

        if pid in forecast_ids:
            forecast_id_list.append(pid)

    # Stable sorted id lists for strategic cards
    forecast_id_list = sorted(set(forecast_id_list))
    observation_ids = sorted(set(observation_ids))
    backfire_ids = sorted(set(backfire_ids))
    behavior_ids = sorted(set(behavior_ids))
    decision_id_list = sorted(decision_ids)
    evidence_ready = sorted(set(observation_ids) & set(forecast_id_list))

    total = len(policy_rows)
    summary = {
        "total": total,
        "on_track": sum(1 for r in policy_rows if r["status"] == "on_track"),
        "at_risk": sum(1 for r in policy_rows if r["status"] == "at_risk"),
        "no_data": sum(1 for r in policy_rows if r["status"] == "no_data"),
    }

    def _why(count: int, noun: str) -> str:
        if total == 0:
            return "No policies in portfolio."
        if count == total:
            return f"All {total} policies have {noun}."
        return f"{count} of {total} policies have {noun}."

    strategic = [
        {
            "key": "A",
            "title": "Predictable Medical Cost Outcomes",
            "description": "Policy-level forecasts with ranges and validity window",
            "count": len(forecast_id_list),
            "total": total,
            "why_met": _why(len(forecast_id_list), "forecasts")
            if total
            else "No policies in portfolio.",
            "policy_ids": forecast_id_list,
        },
        {
            "key": "B",
            "title": "Early Detection of Backfire",
            "description": "Early warning signals (provider resistance, patient deferral, site-of-care)",
            "count": len(backfire_ids),
            "total": total,
            "why_met": (
                f"{len(backfire_ids)} of {total} policies have been flagged as backfire risk "
                "(aligned with Policy Verdicts)."
                if total
                else "No policies in portfolio."
            ),
            "policy_ids": backfire_ids,
        },
        {
            "key": "C",
            "title": "True Measurement of Policy Effectiveness",
            "description": "Single impact verdict per policy (expected vs observed, attribution)",
            "count": len(observation_ids),
            "total": total,
            "why_met": _why(len(observation_ids), "an impact verdict (from observation)"),
            "policy_ids": observation_ids,
        },
        {
            "key": "D",
            "title": "Behavioral Transparency",
            "description": "Provider and patient behavior profiles, time-based, linked to outcomes",
            "count": len(behavior_ids),
            "total": total,
            "why_met": _why(len(behavior_ids), "behavior profiles"),
            "policy_ids": behavior_ids,
        },
        {
            "key": "E",
            "title": "Executive-Grade Governance",
            "description": "Decision packets: what changed, why, what if no action, recommended action",
            "count": len(decision_id_list),
            "total": total,
            "why_met": _why(len(decision_id_list), "a decision packet"),
            "policy_ids": decision_id_list,
        },
        {
            "key": "F",
            "title": "Employer & Regulator Confidence",
            "description": "Auto-generated evidence packs (pre-policy, observed, mitigations, confidence)",
            "count": len(evidence_ready),
            "total": total,
            "why_met": _why(len(evidence_ready), "evidence-pack-ready data (forecast + observation)"),
            "policy_ids": evidence_ready,
        },
    ]

    # "Met" = at least one policy contributes — preserved product semantics, but explicit
    objectives_met_count = sum(1 for s in strategic if s["count"] > 0)

    return {
        "calculation_version": CALCULATION_VERSION,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "tenant_id": str(tenant_id),
        "summary": summary,
        "objectives_met_count": objectives_met_count,
        "policy_rows": policy_rows,
        "strategic": strategic,
        "stability": {
            "status_source": "compute_verdict(latest_observation.comparisons) — same as /policy-verdicts",
            "forecast_source": "persisted policy_predicted_impacts (list_latest)",
            "never_uses": [
                "client N+1 predicted-impact probes",
                "dashboard/policy-performance predicted fill as observed health",
                "silent empty fallbacks that invent on_track",
            ],
        },
    }


def load_objectives_health(tenant_id: UUID) -> Dict[str, Any]:
    """Load persisted inputs and build snapshot. Raises on hard failures — no silent empty."""
    from uepi_api.storage_policies import list_policies
    from uepi_api.storage_observations import list_observations
    from uepi_api.storage_policy_predicted_impact import list_latest_predicted_impacts
    from uepi_api.storage_decisions import list_decisions

    # summary=True avoids per-policy assumptions/guardrails/versions/changelog N+1
    # (hundreds of Azure round-trips that previously hung OH and wedged the API).
    policies = list_policies(tenant_id, summary=True) or []
    observations = list_observations(
        tenant_id=tenant_id,
        latest_only=True,
        summary=True,
        limit=2000,
    )
    predicted = list_latest_predicted_impacts(tenant_id, limit=2000)
    raw_decisions = list_decisions(tenant_id) or []
    decisions: List[Dict[str, Any]] = []
    for d in raw_decisions:
        if hasattr(d, "model_dump"):
            dd = d.model_dump(mode="json")
        elif isinstance(d, dict):
            dd = d
        else:
            dd = {"policy_id": getattr(d, "policy_id", None)}
        decisions.append(dd)

    return build_objectives_health_snapshot(
        tenant_id=tenant_id,
        policies=policies,
        latest_observations=observations,
        predicted_impacts=predicted,
        decisions=decisions,
    )
