"""Phase 2: Evidence pack structure for observations.

Returns a structured document (baseline summary, prediction, observation, comparison, verdict, run refs)
for governance and export.
"""
from typing import Any, Dict, Optional
from uuid import UUID

from uepi_api.storage_observations import get_observation


def build_evidence_pack(tenant_id: UUID, observation_id: str) -> Optional[Dict[str, Any]]:
    """Build structured evidence pack for an observation.

    Sections: baseline_summary, prediction_summary, observation_summary,
    comparison, behavioral_summary, verdict, run_refs.
    """
    obs = get_observation(tenant_id, observation_id)
    if not obs:
        return None

    comparisons = obs.get("comparisons") or {}
    vs_baseline = comparisons.get("vs_baseline") or {}
    vs_predicted = comparisons.get("vs_predicted") or {}
    by_measure_b = vs_baseline.get("comparison_by_measure") or {}
    by_measure_p = vs_predicted.get("comparison_by_measure") or {}

    baseline_summary = {
        "baseline_measures": vs_baseline.get("baseline_measures") or {},
        "comparison_by_measure": by_measure_b,
    }

    prediction_summary = {
        "predicted_measures": vs_predicted.get("predicted_measures") or {},
        "comparison_by_measure": by_measure_p,
    }

    observation_summary = {
        "observed_measures": obs.get("observed_measures") or {},
        "metrics": {k: v for k, v in (obs.get("metrics") or {}).items() if k != "observed_measures"},
        "observation_period_start": obs.get("observation_period_start"),
        "observation_period_end": obs.get("observation_period_end"),
        "computed_at": obs.get("computed_at"),
    }

    comparison = {
        "vs_baseline": vs_baseline,
        "vs_predicted": vs_predicted,
    }

    behavioral_summary = {
        "summary": (obs.get("behavioral_explanation") or {}).get("summary"),
        "risk_factors": (obs.get("behavioral_explanation") or {}).get("risk_factors") or [],
        "recommendations": (obs.get("behavioral_explanation") or {}).get("recommendations") or [],
    }

    verdict = {
        "verdict_status": obs.get("verdict_status"),
        "verdict_reason": obs.get("verdict_reason"),
        "recommendation": obs.get("recommendation"),
        "verdict_rule_version": obs.get("verdict_rule_version"),
    }

    # One-page executive summary: savings estimate, confidence, reason if wrong, decision recommendation
    vs_b = comparisons.get("vs_baseline") or {}
    vs_p = comparisons.get("vs_predicted") or {}
    cost_change_pmpm = vs_b.get("cost_change_pmpm")
    cost_change_pct = vs_b.get("cost_change_pct")
    confidence_pct = vs_p.get("prediction_accuracy_pct")
    executive_summary = {
        "verdict": verdict.get("verdict_status"),
        "verdict_label": _exec_verdict_label(verdict.get("verdict_status")),
        "savings_or_cost_impact_pmpm": cost_change_pmpm,
        "cost_impact_pct": cost_change_pct,
        "confidence_pct": confidence_pct,
        "one_line_reason": verdict.get("verdict_reason"),
        "decision_recommendation": verdict.get("recommendation"),
    }

    run_refs = {}
    if obs.get("analytics_run_id"):
        run_refs["analytics_run_id"] = obs["analytics_run_id"]
    run_refs["baseline_version_id"] = obs.get("baseline_version_id")
    run_refs["prediction_id"] = obs.get("prediction_id")
    run_refs["analysis_id"] = obs.get("analysis_id")
    run_refs["policy_id"] = obs.get("policy_id")

    return {
        "observation_id": observation_id,
        "policy_id": obs.get("policy_id"),
        "evidence_pack_version": "1.0",
        "executive_summary": executive_summary,
        "baseline_summary": baseline_summary,
        "prediction_summary": prediction_summary,
        "observation_summary": observation_summary,
        "comparison": comparison,
        "behavioral_summary": behavioral_summary,
        "verdict": verdict,
        "run_refs": run_refs,
    }


def _exec_verdict_label(status: Optional[str]) -> str:
    if status == "ON_TRACK":
        return "Saving / on track"
    if status == "AT_RISK":
        return "At risk"
    if status == "BACKFIRE":
        return "Backfire risk"
    if status == "INCONCLUSIVE":
        return "Inconclusive"
    return "Unknown"
