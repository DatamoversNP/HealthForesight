"""Population adapters. These call the payment engines. The oracle does not."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

from uepi_api.services.expansion_demo_scenarios import (
    apply_infusion_soc,
    apply_ncci_mue,
    apply_ncci_ptp,
    apply_therapy_coverage,
)
from uepi_api.services.reimbursement_mppr import apply_mppr
from uepi_api.services.reimbursement_sos import apply_sos


def _active(lines: List[Mapping[str, Any]], key: str) -> List[Mapping[str, Any]]:
    return [row for row in lines if row.get("policy_key") == key and row.get("line_status") == "ACTIVE"]


def _infusion_per_claim(lines: List[Mapping[str, Any]]) -> Dict[str, Any]:
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for row in lines:
        grouped.setdefault(str(row.get("claim_id") or ""), []).append(row)
    baseline = 0.0
    post = 0.0
    steered = 0
    for claim_lines in grouped.values():
        part = apply_infusion_soc(claim_lines, steer_hopd_count=1, office_allowed=3200.0)
        baseline += part["totals"]["baseline_paid"]
        post += part["totals"]["post_policy_paid"]
        steered += part["totals"]["episodes_steered"]
    impact = round(baseline - post, 2)
    return {
        "catalog_class": "DEMO_SYNTHETIC",
        "calculation_version": "reimbursement-infusion-soc-v1-per-claim",
        "totals": {
            "baseline_paid": round(baseline, 2),
            "post_policy_paid": round(post, 2),
            "payment_impact": impact,
            "episodes_steered": steered,
        },
    }


def simulate_payment_population(lines: List[Mapping[str, Any]]) -> Dict[str, Any]:
    """Synthetic simulations on generated lines. Not CMS adjudication."""
    return {
        "mppr_favorable": apply_mppr(_active(lines, "mppr"), secondary_pct=0.5),
        "sos_policy": apply_sos(_active(lines, "sos"), hospital_pct=0.8),
        "sos_neutral": apply_sos(_active(lines, "sos"), hospital_pct=1.0),
        "sos_adverse": apply_sos(_active(lines, "sos"), hospital_pct=1.1),
        "ptp": apply_ncci_ptp(_active(lines, "ptp")),
        "mue": apply_ncci_mue(_active(lines, "mue"), mue_value=4),
        "therapy": apply_therapy_coverage(_active(lines, "therapy")),
        "infusion": _infusion_per_claim(_active(lines, "infusion")),
    }
