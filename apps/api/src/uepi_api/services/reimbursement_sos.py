"""Site-of-service payment differential — Representative Payer demo.

Hospital outpatient (POS 22) paid at hospital_pct of allowed after policy;
freestanding / office (POS 11) remains 100% of allowed. Volume held constant.

Not actual Blue Cross NC site differentials. Sign convention: payment_impact =
payer savings (baseline_paid − post_policy_paid); positive = payer pays less.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

CALC_VERSION = "reimbursement-sos-v1"
DEFAULT_HOSPITAL_PCT = 0.80
HOSPITAL_POS = {"22", "19"}  # outpatient hospital / off-campus outpatient
FREESTANDING_POS = {"11", "49"}  # office / independent clinic


def apply_sos(
    lines: Sequence[Mapping[str, Any]],
    *,
    hospital_pct: float = DEFAULT_HOSPITAL_PCT,
) -> Dict[str, Any]:
    line_results: List[Dict[str, Any]] = []
    baseline_paid = 0.0
    post_paid = 0.0
    hospital_lines = 0
    freestanding_lines = 0

    for raw in lines:
        allowed = float(raw.get("allowed_amount") or 0.0)
        pos = str(raw.get("place_of_service") or "").strip()
        units = float(raw.get("units") or 1.0)
        pre = allowed  # pre-policy: paid = allowed at all sites
        if pos in HOSPITAL_POS:
            post = round(allowed * hospital_pct, 2)
            site = "HOSPITAL_OUTPATIENT"
            hospital_lines += 1
        else:
            post = allowed
            site = "FREESTANDING_OR_OTHER"
            freestanding_lines += 1
        baseline_paid += pre
        post_paid += post
        line_results.append(
            {
                "claim_line_id": str(raw.get("claim_line_id") or raw.get("line_id")),
                "cpt_code": str(raw.get("cpt_code") or ""),
                "place_of_service": pos,
                "site_class": site,
                "units": units,
                "allowed_amount": round(allowed, 2),
                "baseline_paid": round(pre, 2),
                "post_policy_paid": round(post, 2),
                "payment_reduction": round(pre - post, 2),
            }
        )

    payment_impact = round(baseline_paid - post_paid, 2)
    return {
        "calculation_version": CALC_VERSION,
        "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
        "catalog_class": "DEMO_SYNTHETIC",
        "sign_convention": {
            "payment_impact": "Payer savings (baseline_paid − post_policy_paid); positive = payer pays less",
            "provider_payment_change": -payment_impact,
            "delta_payment_impact": "Incremental payer savings vs base scenario",
        },
        "rule": {
            "hospital_pos": sorted(HOSPITAL_POS),
            "freestanding_pos": sorted(FREESTANDING_POS),
            "hospital_pct_of_allowed": hospital_pct,
            "freestanding_pct_of_allowed": 1.0,
            "volume_held_constant": True,
        },
        "totals": {
            "line_count": len(line_results),
            "hospital_lines": hospital_lines,
            "freestanding_lines": freestanding_lines,
            "volume_units": sum(float(r.get("units") or 1) for r in lines),
            "baseline_allowed": round(sum(float(r.get("allowed_amount") or 0) for r in lines), 2),
            "baseline_paid": round(baseline_paid, 2),
            "post_policy_paid": round(post_paid, 2),
            "payment_impact": payment_impact,
            "payer_savings": payment_impact,
            "provider_payment_change": round(-payment_impact, 2),
            "payment_impact_pct": (
                round(100.0 * payment_impact / baseline_paid, 4) if baseline_paid else 0.0
            ),
            "reconciliation": {
                "volume_effect": 0.0,
                "mix_effect": 0.0,
                "price_effect": payment_impact,
                "residual": 0.0,
                "identity": "payment_impact = price_effect (volume & mix held at 0)",
            },
        },
        "lines": line_results,
        "not_claiming": [
            "Actual Blue Cross NC site-of-service fee differentials",
            "Empirical payer claims outcomes",
            "Utilization reduction (UM) formula",
        ],
    }


KNOWN_ANSWER_LINES: List[Dict[str, Any]] = [
    # Freestanding MRI-like — no reduction
    {"claim_line_id": "S1", "cpt_code": "70553", "allowed_amount": 800.0, "place_of_service": "11", "units": 1},
    {"claim_line_id": "S2", "cpt_code": "72148", "allowed_amount": 600.0, "place_of_service": "11", "units": 1},
    # Hospital OP — 80% after policy
    {"claim_line_id": "S3", "cpt_code": "70553", "allowed_amount": 1200.0, "place_of_service": "22", "units": 1},
    {"claim_line_id": "S4", "cpt_code": "73721", "allowed_amount": 900.0, "place_of_service": "22", "units": 1},
    {"claim_line_id": "S5", "cpt_code": "72141", "allowed_amount": 500.0, "place_of_service": "19", "units": 1},
]

# baseline 800+600+1200+900+500 = 4000
# post: 800+600 + 960+720+400 = 3480; impact 520
KNOWN_ANSWER_EXPECTED = {
    "baseline_paid": 4000.0,
    "post_policy_paid": 3480.0,
    "payment_impact": 520.0,
    "hospital_lines": 3,
    "freestanding_lines": 2,
}


def verify_known_answer(hospital_pct: float = DEFAULT_HOSPITAL_PCT) -> Dict[str, Any]:
    result = apply_sos(KNOWN_ANSWER_LINES, hospital_pct=hospital_pct)
    t = result["totals"]
    checks = {
        "baseline_paid": abs(t["baseline_paid"] - KNOWN_ANSWER_EXPECTED["baseline_paid"]) < 0.01,
        "post_policy_paid": abs(t["post_policy_paid"] - KNOWN_ANSWER_EXPECTED["post_policy_paid"]) < 0.01,
        "payment_impact": abs(t["payment_impact"] - KNOWN_ANSWER_EXPECTED["payment_impact"]) < 0.01,
        "hospital_lines": t["hospital_lines"] == KNOWN_ANSWER_EXPECTED["hospital_lines"],
        "volume_effect_zero": abs(t["reconciliation"]["volume_effect"]) < 1e-9,
        "price_equals_impact": abs(t["reconciliation"]["price_effect"] - t["payment_impact"]) < 0.01,
        "provider_change_negates_savings": abs(
            t["provider_payment_change"] + t["payer_savings"]
        )
        < 0.01,
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "expected": KNOWN_ANSWER_EXPECTED,
        "actual_totals": t,
        "calculation_version": CALC_VERSION,
    }
