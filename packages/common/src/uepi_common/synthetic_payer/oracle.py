"""Independent payment oracle.

These formulas follow the published demo rules. They do not call
apply_mppr, apply_sos, apply_ncci_ptp, apply_ncci_mue, apply_therapy_coverage,
or apply_infusion_soc. Results are SYNTHETIC / ILLUSTRATIVE.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

EVIDENCE_CLASS = "SYNTHETIC_ILLUSTRATIVE"
HOSPITAL_POS = {"22", "19"}
PTP_MODIFIERS = {"59", "XE", "XP", "XS", "XU"}


def _money(value: float) -> float:
    return round(float(value), 2)


def percent_change(baseline: Optional[float], post: Optional[float]) -> Optional[float]:
    if baseline is None or post is None or baseline <= 0:
        return None
    return round(100.0 * (post - baseline) / baseline, 4)


def rate_per_exposure(amount: Optional[float], exposure: Optional[float]) -> Optional[float]:
    if amount is None or exposure is None or exposure <= 0:
        return None
    return amount / exposure


def verdict_without_contract() -> Dict[str, str]:
    return {
        "screen_verdict": "INCONCLUSIVE",
        "reason": "No policy endpoint contract is defined. A change in utilization or cost is not a verdict.",
    }


def oracle_mppr(lines: Sequence[Mapping[str, Any]], secondary_pct: float = 0.5) -> Dict[str, Any]:
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for line in lines:
        grouped.setdefault(str(line["claim_id"]), []).append(line)
    baseline = 0.0
    post = 0.0
    multi = 0
    secondary = 0
    for claim_id in sorted(grouped):
        ranked = sorted(grouped[claim_id], key=lambda row: (-float(row["allowed_amount"]), str(row["claim_line_id"])))
        if len(ranked) >= 2:
            multi += 1
        for rank, line in enumerate(ranked, start=1):
            allowed = float(line["allowed_amount"])
            baseline += allowed
            if rank == 1:
                post += allowed
            else:
                post += round(allowed * secondary_pct, 2)
                secondary += 1
    impact = _money(baseline - post)
    return _payment_result(
        "mppr",
        baseline=_money(baseline),
        post=_money(post),
        impact=impact,
        extra={"multi_procedure_claims": multi, "secondary_lines_reduced": secondary, "secondary_pct": secondary_pct},
    )


def oracle_sos(lines: Sequence[Mapping[str, Any]], hospital_pct: float = 0.8) -> Dict[str, Any]:
    baseline = 0.0
    post = 0.0
    hospital = 0
    for line in lines:
        allowed = float(line["allowed_amount"])
        baseline += allowed
        pos = str(line.get("place_of_service") or "")
        if pos in HOSPITAL_POS:
            post += round(allowed * hospital_pct, 2)
            hospital += 1
        else:
            post += allowed
    impact = _money(baseline - post)
    direction = "neutral" if impact == 0 else "adverse_to_payer" if impact < 0 else "favorable_to_payer"
    return _payment_result(
        "sos",
        baseline=_money(baseline),
        post=_money(post),
        impact=impact,
        extra={"hospital_lines": hospital, "hospital_pct": hospital_pct, "scenario_direction": direction},
    )


def oracle_ptp(lines: Sequence[Mapping[str, Any]], modifier_indicator: str = "1") -> Dict[str, Any]:
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for line in lines:
        grouped.setdefault(str(line.get("claim_id")), []).append(line)
    baseline = 0.0
    post = 0.0
    pairs = 0
    bypassed = 0
    for claim_lines in grouped.values():
        roles = {str(line.get("role")) for line in claim_lines}
        hit = "column_one" in roles and "column_two" in roles
        if hit:
            pairs += 1
        modifier = None
        for line in claim_lines:
            if str(line.get("role")) == "column_two":
                modifier = (str(line.get("modifier") or "").strip().upper() or None)
        bypass = hit and modifier_indicator == "1" and modifier in PTP_MODIFIERS
        if bypass:
            bypassed += 1
        for line in claim_lines:
            allowed = float(line.get("allowed_amount") or 0)
            baseline += allowed
            deny = hit and (not bypass) and str(line.get("role")) == "column_two" and modifier_indicator in {"0", "1"}
            post += 0.0 if deny else allowed
    impact = _money(baseline - post)
    return _payment_result(
        "ptp",
        baseline=_money(baseline),
        post=_money(post),
        impact=impact,
        extra={"ptp_pairs_hit": pairs, "ptp_pairs_bypassed_with_modifier": bypassed},
    )


def oracle_mue(lines: Sequence[Mapping[str, Any]], mue_value: int = 4) -> Dict[str, Any]:
    baseline = 0.0
    post = 0.0
    capped = 0
    for line in lines:
        units = float(line.get("units") or 0)
        if line.get("allowed_per_unit") is not None:
            per_unit = float(line["allowed_per_unit"])
        elif units:
            per_unit = float(line.get("allowed_amount") or 0) / units
        else:
            per_unit = 0.0
        baseline += units * per_unit
        paid_units = min(units, float(mue_value))
        post += paid_units * per_unit
        if units > mue_value:
            capped += 1
    impact = _money(baseline - post)
    return _payment_result(
        "mue",
        baseline=_money(baseline),
        post=_money(post),
        impact=impact,
        extra={
            "lines_capped": capped,
            "mue_value": mue_value,
            "mue_value_note": "Demo cap. Not a CMS MUE.",
        },
    )


def oracle_therapy(lines: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    baseline = 0.0
    post = 0.0
    for line in lines:
        units = float(line.get("units") or 0)
        per_unit = float(line.get("allowed_per_unit") or 0)
        necessary = float(line.get("medically_necessary_units") if line.get("medically_necessary_units") is not None else units)
        baseline += units * per_unit
        post += min(units, necessary) * per_unit
    impact = _money(baseline - post)
    return _payment_result("therapy", baseline=_money(baseline), post=_money(post), impact=impact, extra={})


def oracle_infusion(
    lines: Sequence[Mapping[str, Any]],
    office_allowed: float = 3200.0,
    steer_hopd_count: int = 2,
) -> Dict[str, Any]:
    baseline = 0.0
    post = 0.0
    hopd_seen = 0
    steered = 0
    for line in lines:
        allowed = float(line.get("allowed_amount") or 0)
        baseline += allowed
        paid = allowed
        if str(line.get("site") or "") == "HOPD":
            hopd_seen += 1
            if hopd_seen <= steer_hopd_count:
                paid = office_allowed
                steered += 1
        post += paid
    impact = _money(baseline - post)
    return _payment_result(
        "infusion",
        baseline=_money(baseline),
        post=_money(post),
        impact=impact,
        extra={"episodes_steered": steered, "codeset_closed": False},
    )


def oracle_infusion_by_claim(
    lines: Sequence[Mapping[str, Any]],
    office_allowed: float = 3200.0,
    steer_hopd_count: int = 1,
) -> Dict[str, Any]:
    """Apply the infusion price rule inside each claim.

    The known-answer sample steers 2 of 3 HOPD lines in one fixture.
    A population run uses that same price rule on the first HOPD line of
    each generated claim. It does not steer only the first two lines in the file.
    """
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for line in lines:
        grouped.setdefault(str(line.get("claim_id") or ""), []).append(line)
    baseline = 0.0
    post = 0.0
    steered = 0
    for claim_lines in grouped.values():
        part = oracle_infusion(claim_lines, office_allowed=office_allowed, steer_hopd_count=steer_hopd_count)
        baseline += part["baseline_paid"]
        post += part["post_policy_paid"]
        steered += part["episodes_steered"]
    impact = _money(baseline - post)
    return _payment_result(
        "infusion",
        baseline=_money(baseline),
        post=_money(post),
        impact=impact,
        extra={"episodes_steered": steered, "codeset_closed": False, "applied": "per_claim"},
    )


def oracle_not_measurable(policy_key: str, event_count: int, reason: str) -> Dict[str, Any]:
    return {
        "policy_key": policy_key,
        "evidence_class": EVIDENCE_CLASS,
        "execution_status": "NOT_MEASURABLE",
        "event_count": event_count,
        "payment_impact": None,
        "utilization_change_pct": None,
        "reason": reason,
        "outcome_claimed": False,
        "verdict": verdict_without_contract(),
        "real_world_savings": False,
        "cms_adjudication": False,
    }


def _payment_result(
    policy_key: str,
    *,
    baseline: float,
    post: float,
    impact: float,
    extra: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "policy_key": policy_key,
        "evidence_class": EVIDENCE_CLASS,
        "execution_status": "SYNTHETIC_SIMULATION",
        "baseline_paid": baseline,
        "post_policy_paid": post,
        "payment_impact": impact,
        "payment_impact_pct": None if baseline <= 0 else round(100.0 * impact / baseline, 4),
        "payer_savings_label": "Synthetic payer payment difference. Not real-world savings.",
        "verdict": verdict_without_contract(),
        "real_world_savings": False,
        "cms_adjudication": False,
        "clinical_certification": False,
        **extra,
    }


def sum_allowed(lines: Iterable[Mapping[str, Any]]) -> float:
    return _money(sum(float(line.get("allowed_amount") or 0) for line in lines))
