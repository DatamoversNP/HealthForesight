"""Multiple Procedure Payment Reduction (MPPR) — Representative Payer demo.

Deterministic, mechanism-specific payment math. Not utilization elasticity.
Not actual Blue Cross NC fee schedules or proprietary edits.

Demo rule (documented known-answer):
  Within a claim_id session, rank lines by allowed_amount descending.
  Primary (rank 1): paid = 100% of allowed
  Secondary+ (rank ≥2): paid = secondary_pct of allowed (default 50%)
  Volume/units held constant — impact is price/payment only.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


DEFAULT_SECONDARY_PCT = 0.50
CALC_VERSION = "reimbursement-mppr-v1"


@dataclass(frozen=True)
class ClaimLine:
    claim_id: str
    claim_line_id: str
    cpt_code: str
    allowed_amount: float
    units: float = 1.0
    paid_amount: Optional[float] = None


def apply_mppr(
    lines: Sequence[ClaimLine] | Sequence[Mapping[str, Any]],
    *,
    secondary_pct: float = DEFAULT_SECONDARY_PCT,
) -> Dict[str, Any]:
    """Apply demo MPPR and return reconciliation + line results."""
    parsed: List[ClaimLine] = []
    for raw in lines:
        if isinstance(raw, ClaimLine):
            parsed.append(raw)
            continue
        parsed.append(
            ClaimLine(
                claim_id=str(raw["claim_id"]),
                claim_line_id=str(raw.get("claim_line_id") or raw.get("line_id")),
                cpt_code=str(raw.get("cpt_code") or ""),
                allowed_amount=float(raw.get("allowed_amount") or 0.0),
                units=float(raw.get("units") or 1.0),
                paid_amount=(
                    float(raw["paid_amount"]) if raw.get("paid_amount") is not None else None
                ),
            )
        )

    by_claim: Dict[str, List[ClaimLine]] = defaultdict(list)
    for ln in parsed:
        by_claim[ln.claim_id].append(ln)

    line_results: List[Dict[str, Any]] = []
    baseline_paid = 0.0
    post_paid = 0.0
    secondary_lines = 0
    multi_proc_claims = 0

    for claim_id, claim_lines in sorted(by_claim.items()):
        ranked = sorted(claim_lines, key=lambda x: (-x.allowed_amount, x.claim_line_id))
        if len(ranked) >= 2:
            multi_proc_claims += 1
        for rank, ln in enumerate(ranked, start=1):
            # Pre-policy baseline: paid = allowed (full fee schedule)
            pre = ln.allowed_amount
            if rank == 1:
                post = ln.allowed_amount
                reduction_pct = 0.0
            else:
                post = round(ln.allowed_amount * secondary_pct, 2)
                reduction_pct = 1.0 - secondary_pct
                secondary_lines += 1
            baseline_paid += pre
            post_paid += post
            line_results.append(
                {
                    "claim_id": claim_id,
                    "claim_line_id": ln.claim_line_id,
                    "cpt_code": ln.cpt_code,
                    "rank_by_allowed": rank,
                    "units": ln.units,
                    "allowed_amount": round(ln.allowed_amount, 2),
                    "baseline_paid": round(pre, 2),
                    "post_policy_paid": round(post, 2),
                    "payment_reduction": round(pre - post, 2),
                    "reduction_pct": reduction_pct,
                    "role": "PRIMARY" if rank == 1 else "SECONDARY",
                }
            )

    payment_impact = round(baseline_paid - post_paid, 2)
    volume_units = sum(ln.units for ln in parsed)
    return {
        "calculation_version": CALC_VERSION,
        "mechanism": "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION",
        "catalog_class": "DEMO_SYNTHETIC",
        "display_label": "Representative Payer Policies",
        "sign_convention": {
            "payment_impact": (
                "Payer savings = baseline_paid − post_policy_paid. "
                "Positive means the payer pays less (provider receives less)."
            ),
            "payer_savings": "Alias of payment_impact (payer perspective).",
            "provider_payment_change": "Negative of payment_impact (provider perspective).",
            "delta_payment_impact": (
                "Incremental payer savings vs base scenario. "
                "Positive = additional payer savings, not increased provider payment."
            ),
        },
        "rule": {
            "primary_pct": 1.0,
            "secondary_pct": secondary_pct,
            "ranking": "allowed_amount DESC within claim_id",
            "volume_held_constant": True,
        },
        "totals": {
            "line_count": len(parsed),
            "claim_count": len(by_claim),
            "multi_procedure_claims": multi_proc_claims,
            "secondary_lines_reduced": secondary_lines,
            "volume_units": volume_units,
            "baseline_allowed": round(sum(ln.allowed_amount for ln in parsed), 2),
            "baseline_paid": round(baseline_paid, 2),
            "post_policy_paid": round(post_paid, 2),
            "payment_impact": payment_impact,
            "payer_savings": payment_impact,
            "provider_payment_change": round(-payment_impact, 2),
            "payment_impact_pct": (
                round(100.0 * payment_impact / baseline_paid, 4) if baseline_paid else 0.0
            ),
            # Mix/price/volume decomposition (volume fixed → all impact is price)
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
            "Actual Blue Cross NC MPPR schedule",
            "Empirical payer claims outcomes",
            "Utilization reduction (UM) formula",
        ],
    }


# Deterministic fixture for independent financial checks (known answers).
KNOWN_ANSWER_LINES: List[Dict[str, Any]] = [
    # Claim A: primary 1000, secondary 400 → post 1000 + 200 = 1200; impact 200
    {"claim_id": "KA-A", "claim_line_id": "A1", "cpt_code": "27447", "allowed_amount": 1000.0, "units": 1},
    {"claim_id": "KA-A", "claim_line_id": "A2", "cpt_code": "64483", "allowed_amount": 400.0, "units": 1},
    # Claim B: three lines 800/500/300 → post 800 + 250 + 150 = 1200; impact 400
    {"claim_id": "KA-B", "claim_line_id": "B1", "cpt_code": "29881", "allowed_amount": 800.0, "units": 1},
    {"claim_id": "KA-B", "claim_line_id": "B2", "cpt_code": "29876", "allowed_amount": 500.0, "units": 1},
    {"claim_id": "KA-B", "claim_line_id": "B3", "cpt_code": "20610", "allowed_amount": 300.0, "units": 1},
    # Claim C: single line — no reduction
    {"claim_id": "KA-C", "claim_line_id": "C1", "cpt_code": "99213", "allowed_amount": 150.0, "units": 1},
]

KNOWN_ANSWER_EXPECTED = {
    "baseline_paid": 3150.0,  # 1000+400+800+500+300+150
    "post_policy_paid": 2550.0,  # 1000+200+800+250+150+150
    "payment_impact": 600.0,
    "multi_procedure_claims": 2,
    "secondary_lines_reduced": 3,
}


def verify_known_answer(secondary_pct: float = DEFAULT_SECONDARY_PCT) -> Dict[str, Any]:
    result = apply_mppr(KNOWN_ANSWER_LINES, secondary_pct=secondary_pct)
    t = result["totals"]
    checks = {
        "baseline_paid": abs(t["baseline_paid"] - KNOWN_ANSWER_EXPECTED["baseline_paid"]) < 0.01,
        "post_policy_paid": abs(t["post_policy_paid"] - KNOWN_ANSWER_EXPECTED["post_policy_paid"]) < 0.01,
        "payment_impact": abs(t["payment_impact"] - KNOWN_ANSWER_EXPECTED["payment_impact"]) < 0.01,
        "multi_procedure_claims": t["multi_procedure_claims"]
        == KNOWN_ANSWER_EXPECTED["multi_procedure_claims"],
        "secondary_lines_reduced": t["secondary_lines_reduced"]
        == KNOWN_ANSWER_EXPECTED["secondary_lines_reduced"],
        "volume_effect_zero": abs(t["reconciliation"]["volume_effect"]) < 1e-9,
        "price_equals_impact": abs(t["reconciliation"]["price_effect"] - t["payment_impact"]) < 0.01,
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "expected": KNOWN_ANSWER_EXPECTED,
        "actual_totals": t,
        "calculation_version": CALC_VERSION,
    }
