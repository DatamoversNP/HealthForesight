"""Longitudinal synthetic claims for the same member identities.

Pre-period and post-period claims use different random streams. The post-period
generator does not accept a prediction, a payment-engine total, or a scenario row.
Rates below are synthetic assumptions. They are not commercial benchmarks and
they are not a predicted percentage applied to the baseline.

The policy effective date is a hypothetical label for this test, not policy authority.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple

from uepi_common.synthetic_payer.generate import (
    COINSURANCE,
    POLICIES,
    REFERENCE_DATE,
    SEED,
    WINDOW_END,
    WINDOW_START,
    _cohort,
    _money_split,
)

GENERATOR_VERSION = "synthetic-longitudinal-v1"
HYPOTHETICAL_EFFECTIVE = date(2025, 7, 1)
EFFECTIVE_LABEL = "SYNTHETIC_HYPOTHETICAL_EFFECTIVE_DATE"
PRE_STREAM = 17
POST_STREAM = 104729

# Occurrence in the post period. These are not payment-rule percentages.
POST_OCCURRENCE = {
    "mppr": 0.62,
    "sos": 0.91,
    "ptp": 0.77,
    "mue": 0.55,
    "therapy": 0.83,
    "infusion": 0.70,
    "mri": 0.88,
    "ncd": 0.64,
    "lcd": 0.73,
}

FEE = {
    "27447": 1400.0,
    "64483": 400.0,
    "72148": 900.0,
    "70553": 1100.0,
    "70551": 700.0,
    "97110": 50.0,
    "96413": 5000.0,
    "70540": 650.0,
    "99213": 150.0,
    "99283": 800.0,
    "99223": 2200.0,
    "45378": 1200.0,
}
PHARMACY_ALLOWED = 85.0

ASSUMPTIONS = [
    "Member identities and coverage intervals reuse synthetic-payer-v1 and seed 20261106.",
    "Hypothetical effective date 2025-07-01 is a synthetic test label, not policy authority.",
    "Pre-period claims use random stream seed+17. Post-period claims use seed+104729.",
    "Post-period occurrence rates are fixed synthetic assumptions, not payment-engine percentages.",
    "Prices come from a fixed synthetic fee table. Post-period prices vary by that stream only.",
    "Background intensity is low on purpose so the run can finish. It is not a commercial book rate.",
    "Pharmacy rows use synthetic NDC tokens. They are not a formulary.",
    "No cited commercial utilization benchmark sets these frequencies.",
]


def _day(rng: random.Random, intervals: Sequence[Tuple[date, date]], start: date, end: date) -> Optional[date]:
    choices = []
    for left, right in intervals:
        lo = max(left, start)
        hi = min(right, end)
        if hi > lo:
            choices.append((lo, hi))
    if not choices:
        return None
    lo, hi = choices[rng.randrange(len(choices))]
    span = (hi - lo).days
    day = lo if span <= 1 else lo + timedelta(days=rng.randrange(span))
    if day.month in (1, 10) or rng.random() > 0.25:
        return day
    return min(day + timedelta(days=rng.randint(0, 20)), hi - timedelta(days=1)) if hi > lo + timedelta(days=1) else day


def _line(
    *,
    member_id: str,
    provider_id: str,
    claim_id: str,
    claim_line_id: str,
    service_date: date,
    cpt: Optional[str],
    allowed: float,
    units: float,
    pos: str,
    category: str,
    policy_key: str,
    period: str,
    role: Optional[str] = None,
    modifier: Optional[str] = None,
    site: Optional[str] = None,
    line_status: str = "ACTIVE",
    pharmacy: bool = False,
) -> Dict[str, Any]:
    paid, share = _money_split(allowed)
    return {
        "member_id": member_id,
        "provider_id": provider_id,
        "claim_id": claim_id,
        "claim_line_id": claim_line_id,
        "service_date": service_date.isoformat(),
        "adjudication_date": (service_date + timedelta(days=14)).isoformat(),
        "cpt_code": cpt,
        "allowed_amount": allowed if line_status != "REVERSAL" else -allowed,
        "paid_amount": paid if line_status != "REVERSAL" else -paid,
        "member_cost_share": share if line_status != "REVERSAL" else -share,
        "units": units,
        "place_of_service": pos,
        "service_category": "PHARMACY" if pharmacy else category,
        "policy_key": policy_key,
        "period": period,
        "line_status": line_status,
        "role": role,
        "modifier": modifier,
        "site": site,
        "pharmacy": pharmacy,
        "ndc": "SYN-NDC-0001" if pharmacy else None,
        "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
        "effective_date_label": EFFECTIVE_LABEL,
    }


def _price(code: str, rng: random.Random, vary: bool) -> float:
    base = FEE[code]
    if not vary:
        return base
    return round(base * (0.97 + rng.random() * 0.08), 2)


def generate_period_claims(population: Dict[str, Any], period: str, seed: int = SEED) -> List[Dict[str, Any]]:
    """Generate one period. period is PRE or POST. No prediction input is accepted."""
    if period not in {"PRE", "POST"}:
        raise ValueError(period)
    start, end = (WINDOW_START, HYPOTHETICAL_EFFECTIVE) if period == "PRE" else (HYPOTHETICAL_EFFECTIVE, WINDOW_END)
    rng = random.Random(seed + (PRE_STREAM if period == "PRE" else POST_STREAM))
    vary = period == "POST"
    intervals = {}
    for row in population["coverage"]:
        intervals.setdefault(row["member_id"], []).append(
            (date.fromisoformat(row["start_date"]), date.fromisoformat(row["end_date"]))
        )
    lines: List[Dict[str, Any]] = []
    providers = [row["provider_id"] for row in population["providers"]]
    for index, member in enumerate(population["members"]):
        member_id = member["member_id"]
        covered = intervals.get(member_id) or []
        day = _day(rng, covered, start, end)
        if day is None:
            continue
        provider = providers[index % len(providers)]
        cohort = _cohort(index)
        if cohort in POST_OCCURRENCE:
            occur = True if period == "PRE" else rng.random() < POST_OCCURRENCE[cohort]
            if occur:
                lines.extend(_policy_lines(rng, member_id, provider, day, cohort, period, vary, index))
        if period == "PRE":
            if index % 4 == 0:
                lines.append(_simple(rng, member_id, provider, day, "99213", "11", "PROFESSIONAL", "background", period, vary))
            if index % 19 == 0:
                lines.append(_simple(rng, member_id, provider, day, "99283", "23", "EMERGENCY", "background", period, vary))
            if index % 23 == 0:
                lines.append(_simple(rng, member_id, provider, day, None, "01", "PHARMACY", "pharmacy", period, vary, pharmacy=True))
            if index % 47 == 0:
                lines.append(_simple(rng, member_id, provider, day, "99223", "21", "INPATIENT", "background", period, vary))
            if index % 31 == 0:
                lines.append(_simple(rng, member_id, provider, day, "45378", "22", "OUTPATIENT", "background", period, vary))
        else:
            if rng.random() < 0.22:
                lines.append(_simple(rng, member_id, provider, day, "99213", "11", "PROFESSIONAL", "background", period, vary))
            if rng.random() < 0.04:
                lines.append(_simple(rng, member_id, provider, day, "99283", "23", "EMERGENCY", "background", period, vary))
            if rng.random() < 0.18:
                lines.append(_simple(rng, member_id, provider, day, None, "01", "PHARMACY", "pharmacy", period, vary, pharmacy=True))
            if rng.random() < 0.02:
                lines.append(_simple(rng, member_id, provider, day, "99223", "21", "INPATIENT", "background", period, vary))
            if rng.random() < 0.03:
                lines.append(_simple(rng, member_id, provider, day, "45378", "22", "OUTPATIENT", "background", period, vary))
    return lines


def _simple(rng, member_id, provider, day, cpt, pos, category, policy_key, period, vary, pharmacy=False):
    allowed = PHARMACY_ALLOWED if pharmacy else _price(cpt, rng, vary)
    if vary and pharmacy:
        allowed = round(PHARMACY_ALLOWED * (0.97 + rng.random() * 0.08), 2)
    claim = f"{period}-{member_id}-{category}"
    return _line(
        member_id=member_id,
        provider_id=provider,
        claim_id=claim,
        claim_line_id=f"{claim}-1",
        service_date=day,
        cpt=cpt,
        allowed=allowed,
        units=1,
        pos=pos,
        category=category,
        policy_key=policy_key,
        period=period,
        pharmacy=pharmacy,
    )


def _policy_lines(rng, member_id, provider, day, cohort, period, vary, index) -> List[Dict[str, Any]]:
    claim = f"{period}-{member_id}-{cohort}"
    if cohort == "mppr":
        return [
            _line(member_id=member_id, provider_id=provider, claim_id=claim, claim_line_id=f"{claim}-1", service_date=day, cpt="27447", allowed=_price("27447", rng, vary), units=1, pos="24", category="mppr", policy_key="mppr", period=period, role="primary"),
            _line(member_id=member_id, provider_id=provider, claim_id=claim, claim_line_id=f"{claim}-2", service_date=day, cpt="64483", allowed=_price("64483", rng, vary), units=1, pos="24", category="mppr", policy_key="mppr", period=period, role="secondary"),
        ]
    if cohort == "sos":
        pos = "22" if (index // 100) % 2 == 0 else "11"
        return [_line(member_id=member_id, provider_id=provider, claim_id=claim, claim_line_id=f"{claim}-1", service_date=day, cpt="72148", allowed=_price("72148", rng, vary), units=1, pos=pos, category="sos", policy_key="sos", period=period)]
    if cohort == "ptp":
        modifier = "59" if rng.random() < 0.25 else None
        return [
            _line(member_id=member_id, provider_id=provider, claim_id=claim, claim_line_id=f"{claim}-1", service_date=day, cpt="70553", allowed=_price("70553", rng, vary), units=1, pos="22", category="ptp", policy_key="ptp", period=period, role="column_one"),
            _line(member_id=member_id, provider_id=provider, claim_id=claim, claim_line_id=f"{claim}-2", service_date=day, cpt="70551", allowed=_price("70551", rng, vary), units=1, pos="22", category="ptp", policy_key="ptp", period=period, role="column_two", modifier=modifier),
        ]
    if cohort == "mue":
        units = 6 if period == "PRE" else rng.choice([3, 4, 5, 6, 8])
        return [_line(member_id=member_id, provider_id=provider, claim_id=claim, claim_line_id=f"{claim}-1", service_date=day, cpt="97110", allowed=round(_price("97110", rng, vary) * units, 2), units=units, pos="11", category="mue", policy_key="mue", period=period)]
    if cohort == "therapy":
        units = 6 if period == "PRE" else rng.choice([4, 5, 6, 7])
        necessary = 4 if period == "PRE" else rng.choice([3, 4, 5, 6])
        line = _line(member_id=member_id, provider_id=provider, claim_id=claim, claim_line_id=f"{claim}-1", service_date=day, cpt="97110", allowed=round(_price("97110", rng, vary) * units, 2), units=units, pos="11", category="therapy", policy_key="therapy", period=period)
        line["medically_necessary_units"] = necessary
        line["allowed_per_unit"] = round(line["allowed_amount"] / units, 6)
        return [line]
    if cohort == "infusion":
        site = "HOPD" if rng.random() < (0.75 if period == "PRE" else 0.60) else "ASC_OR_OFFICE"
        allowed = _price("96413", rng, vary) if site == "HOPD" else 3200.0
        return [_line(member_id=member_id, provider_id=provider, claim_id=claim, claim_line_id=f"{claim}-1", service_date=day, cpt="96413", allowed=allowed, units=1, pos="22" if site == "HOPD" else "11", category="infusion", policy_key="infusion", period=period, site=site)]
    code = {"mri": "72148", "ncd": "70551", "lcd": "70540"}[cohort]
    return [_line(member_id=member_id, provider_id=provider, claim_id=claim, claim_line_id=f"{claim}-1", service_date=day, cpt=code, allowed=_price(code, rng, vary), units=1, pos="22", category=cohort, policy_key=cohort, period=period)]


def period_bounds_hold(lines: Sequence[Dict[str, Any]], period: str) -> bool:
    for row in lines:
        day = date.fromisoformat(row["service_date"])
        if period == "PRE" and day >= HYPOTHETICAL_EFFECTIVE:
            return False
        if period == "POST" and day < HYPOTHETICAL_EFFECTIVE:
            return False
        paid = row["paid_amount"]
        share = row["member_cost_share"]
        allowed = row["allowed_amount"]
        if abs(allowed - paid - share) > 0.02:
            return False
    return True
