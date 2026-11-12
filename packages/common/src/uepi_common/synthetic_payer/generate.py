"""Deterministic synthetic members, coverage, and policy source events.

Does not import the legacy SyntheticDataGenerator and does not seed a target KPI.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any, Dict, List, Sequence, Tuple

from uepi_common.synthetic_payer.exposure import covers, member_months

GENERATOR_VERSION = "synthetic-payer-v1"
SEED = 20261106
WINDOW_START = date(2024, 1, 1)
WINDOW_END = date(2026, 10, 1)
REFERENCE_DATE = date(2025, 7, 1)
COINSURANCE = 0.20

POLICIES: Tuple[Dict[str, str], ...] = (
    {"key": "mppr", "policy_id": "d0eeb370-df14-4478-8755-dad6c3a35a47", "document_id": "HF-RP-PAY-MPPR-001", "execution": "SYNTHETIC_SIMULATION"},
    {"key": "sos", "policy_id": "d7441dd9-3bfe-405e-ae6c-0377204bbb7e", "document_id": "HF-RP-SOC-IMG-001", "execution": "SYNTHETIC_SIMULATION"},
    {"key": "ptp", "policy_id": "58b839b5-b6e0-59e0-9406-d817877c3ce8", "document_id": "HF-RP-CODE-PTP-001", "execution": "SYNTHETIC_SIMULATION"},
    {"key": "mue", "policy_id": "e11b049d-fcce-55cc-bcd7-71329038383b", "document_id": "HF-RP-CODE-MUE-001", "execution": "SYNTHETIC_SIMULATION"},
    {"key": "therapy", "policy_id": "f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b", "document_id": "HF-RP-COV-THER-001", "execution": "SYNTHETIC_SIMULATION"},
    {"key": "infusion", "policy_id": "11218053-bdc0-569f-a415-fb61c5dcda37", "document_id": "HF-RP-SOC-INF-001", "execution": "SYNTHETIC_SIMULATION"},
    {"key": "mri", "policy_id": "d403f101-08dd-45c9-ab83-d42e37c62018", "document_id": "HF-RP-UM-MRI-001", "execution": "NOT_MEASURABLE"},
    {"key": "ncd", "policy_id": "4f8c34e3-015b-509d-90ba-521261464258", "document_id": "HF-RP-COV-NCD2202-001", "execution": "NOT_MEASURABLE"},
    {"key": "lcd", "policy_id": "649b4ac8-ca82-5b84-aa87-84834490731a", "document_id": "HF-RP-COV-L34425-001", "execution": "NOT_MEASURABLE"},
)


def _cohort(index: int) -> str:
    slot = index % 100
    if slot < 2:
        return "mppr"
    if slot == 2:
        return "sos"
    if slot == 3:
        return "ptp"
    if slot == 4:
        return "mue"
    if slot == 5:
        return "therapy"
    if slot == 6:
        return "infusion"
    if slot in (7, 8):
        return "mri"
    if slot == 9:
        return "ncd"
    if slot == 10:
        return "lcd"
    if slot < 40:
        return "background"
    return "none"


def _money_split(allowed: float) -> Tuple[float, float]:
    share = round(allowed * COINSURANCE, 2)
    paid = round(allowed - share, 2)
    drift = round(allowed - paid - share, 2)
    return round(paid + drift, 2), share


def _service_day(rng: random.Random, intervals: Sequence[Tuple[date, date]]) -> date:
    choice = intervals[rng.randrange(len(intervals))]
    span = (choice[1] - choice[0]).days
    if span <= 1:
        return choice[0]
    return choice[0] + timedelta(days=rng.randrange(span))


def generate_population(lives: int, seed: int = SEED) -> Dict[str, Any]:
    rng = random.Random(seed)
    providers = []
    for index in range(40):
        providers.append(
            {
                "provider_id": f"SYNPROV-{index:04d}",
                "network_status": "OUT" if index % 5 == 0 else "IN",
                "organization": f"Synthetic Org {index % 8}",
            }
        )
    members = []
    intervals = []
    for index in range(lives):
        member_id = f"SYN-{seed}-{index:07d}"
        start_offset = rng.randint(0, 500)
        start = WINDOW_START + timedelta(days=start_offset)
        if start > REFERENCE_DATE:
            start = REFERENCE_DATE - timedelta(days=rng.randint(15, 120))
        end = REFERENCE_DATE + timedelta(days=rng.randint(45, 450))
        if end > WINDOW_END:
            end = WINDOW_END
        if end <= REFERENCE_DATE:
            end = REFERENCE_DATE + timedelta(days=1)
        member_intervals = [(start, end)]
        if index % 20 == 0 and start > WINDOW_START + timedelta(days=40):
            gap_end = start - timedelta(days=20)
            gap_start = max(WINDOW_START, gap_end - timedelta(days=60))
            if gap_start < gap_end:
                member_intervals.append((gap_start, gap_end))
        member_intervals.sort()
        age = 18 + (index * 7 + seed) % 65
        members.append(
            {
                "member_id": member_id,
                "age_years": age,
                "sex": "F" if index % 2 == 0 else "M",
                "product": "COMMERCIAL_SYNTHETIC",
                "coinsurance": COINSURANCE,
                "pharmacy_benefit": False,
                "cohort": _cohort(index),
                "reference_enrolled": covers(member_intervals, REFERENCE_DATE),
            }
        )
        for left, right in member_intervals:
            intervals.append(
                {
                    "member_id": member_id,
                    "start_date": left.isoformat(),
                    "end_date": right.isoformat(),
                    "interval_convention": "half_open_end_exclusive",
                }
            )
    return {
        "members": members,
        "coverage": intervals,
        "providers": providers,
        "benefits": {
            "product": "COMMERCIAL_SYNTHETIC",
            "coinsurance": COINSURANCE,
            "deductible_simulated": False,
            "pharmacy_benefit": False,
            "note": "Synthetic commercial coinsurance. Not an approved BCBS-NC benefit.",
        },
    }


def _line(
    *,
    member_id: str,
    provider_id: str,
    service_date: date,
    claim_id: str,
    line_id: str,
    cpt: str,
    allowed: float,
    units: float = 1,
    policy_key: str,
    **extra: Any,
) -> Dict[str, Any]:
    paid, share = _money_split(allowed)
    row = {
        "member_id": member_id,
        "provider_id": provider_id,
        "service_date": service_date.isoformat(),
        "claim_id": claim_id,
        "claim_line_id": line_id,
        "cpt_code": cpt,
        "units": units,
        "allowed_amount": round(allowed, 2),
        "plan_paid_amount": paid,
        "member_cost_share": share,
        "paid_amount": paid,
        "policy_key": policy_key,
        "line_status": "ACTIVE",
        "code_authority": "CANDIDATE_NOT_APPROVED",
        "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
    }
    row.update(extra)
    return row


def generate_events(population: Dict[str, Any], seed: int = SEED) -> List[Dict[str, Any]]:
    rng = random.Random(seed + 17)
    by_member = {}
    for row in population["coverage"]:
        by_member.setdefault(row["member_id"], []).append((date.fromisoformat(row["start_date"]), date.fromisoformat(row["end_date"])))
    providers = population["providers"]
    lines: List[Dict[str, Any]] = []
    for member in population["members"]:
        cohort = member["cohort"]
        if cohort == "none":
            continue
        member_id = member["member_id"]
        intervals = by_member[member_id]
        day = _service_day(rng, intervals)
        provider = providers[rng.randrange(len(providers))]["provider_id"]
        claim = f"{member_id}-C"
        if cohort == "mppr":
            lines.append(_line(member_id=member_id, provider_id=provider, service_date=day, claim_id=claim, line_id=claim + "-1", cpt="27447", allowed=1000, policy_key="mppr"))
            lines.append(_line(member_id=member_id, provider_id=provider, service_date=day, claim_id=claim, line_id=claim + "-2", cpt="64483", allowed=400, policy_key="mppr"))
        elif cohort == "sos":
            pos = "22" if (index_of(member_id) // 100) % 2 == 0 else "11"
            lines.append(_line(member_id=member_id, provider_id=provider, service_date=day, claim_id=claim, line_id=claim + "-1", cpt="72148", allowed=900, policy_key="sos", place_of_service=pos))
        elif cohort == "ptp":
            modifier = "59" if rng.random() < 0.25 else None
            lines.append(_line(member_id=member_id, provider_id=provider, service_date=day, claim_id=claim, line_id=claim + "-1", cpt="70553", allowed=800, policy_key="ptp", role="column_one", modifier=modifier if False else None))
            lines.append(_line(member_id=member_id, provider_id=provider, service_date=day, claim_id=claim, line_id=claim + "-2", cpt="70551", allowed=400, policy_key="ptp", role="column_two", modifier=modifier))
        elif cohort == "mue":
            units = 6 if rng.random() < 0.4 else 3
            lines.append(_line(member_id=member_id, provider_id=provider, service_date=day, claim_id=claim, line_id=claim + "-1", cpt="97110", allowed=50 * units, units=units, policy_key="mue", allowed_per_unit=50))
        elif cohort == "therapy":
            units = 5
            lines.append(_line(member_id=member_id, provider_id=provider, service_date=day, claim_id=claim, line_id=claim + "-1", cpt="97110", allowed=40 * units, units=units, policy_key="therapy", allowed_per_unit=40, medically_necessary_units=3))
        elif cohort == "infusion":
            site = "ASC_OR_OFFICE" if (index_of(member_id) // 100) % 4 == 3 else "HOPD"
            allowed = 5000 if site == "HOPD" else 3200
            lines.append(_line(member_id=member_id, provider_id=provider, service_date=day, claim_id=claim, line_id=claim + "-1", cpt="96413", allowed=allowed, policy_key="infusion", site=site))
        elif cohort == "mri":
            lines.append(_line(member_id=member_id, provider_id=provider, service_date=day, claim_id=claim, line_id=claim + "-1", cpt="72148", allowed=600, policy_key="mri", place_of_service="11", diagnosis="M54.16", anatomical_region="LUMBAR", auth_status="NOT_ADJUDICATED"))
        elif cohort == "ncd":
            lines.append(_line(member_id=member_id, provider_id=provider, service_date=day, claim_id=claim, line_id=claim + "-1", cpt="70551", allowed=700, policy_key="ncd", place_of_service="22", anatomical_region="MRI_NATIONAL", auth_status="NOT_ADJUDICATED"))
        elif cohort == "lcd":
            lines.append(_line(member_id=member_id, provider_id=provider, service_date=day, claim_id=claim, line_id=claim + "-1", cpt="70540", allowed=650, policy_key="lcd", place_of_service="22", anatomical_region="ORBIT_FACE_NECK_ONLY", auth_status="NOT_ADJUDICATED"))
        elif cohort == "background":
            lines.append(_line(member_id=member_id, provider_id=provider, service_date=day, claim_id=claim, line_id=claim + "-1", cpt="99213", allowed=150, policy_key="background", place_of_service="11"))
            if index_of(member_id) % 7 == 0:
                original = lines[-1]
                reversal = dict(original)
                reversal["claim_line_id"] = original["claim_line_id"] + "R"
                reversal["line_status"] = "REVERSAL"
                reversal["allowed_amount"] = -original["allowed_amount"]
                reversal["plan_paid_amount"] = -original["plan_paid_amount"]
                reversal["member_cost_share"] = -original["member_cost_share"]
                reversal["paid_amount"] = -original["paid_amount"]
                reversal["reverses_line_id"] = original["claim_line_id"]
                replacement = dict(original)
                replacement["claim_line_id"] = original["claim_line_id"] + "P"
                replacement["line_status"] = "REPLACEMENT"
                replacement["replaces_line_id"] = original["claim_line_id"]
                lines.extend([reversal, replacement])
    return lines


def index_of(member_id: str) -> int:
    return int(member_id.rsplit("-", 1)[-1])


def exposure_summary(population: Dict[str, Any]) -> Dict[str, float]:
    by_member: Dict[str, List[Tuple[date, date]]] = {}
    for row in population["coverage"]:
        by_member.setdefault(row["member_id"], []).append((date.fromisoformat(row["start_date"]), date.fromisoformat(row["end_date"])))
    total = 0.0
    year_2025 = 0.0
    obs_2026 = 0.0
    for intervals in by_member.values():
        total += member_months(intervals, WINDOW_START, WINDOW_END)
        year_2025 += member_months(intervals, date(2025, 1, 1), date(2026, 1, 1))
        obs_2026 += member_months(intervals, date(2026, 1, 1), date(2026, 10, 1))
    return {
        "member_months": round(total, 6),
        "member_months_2025": round(year_2025, 6),
        "member_months_2026_jan_sep": round(obs_2026, 6),
        "denominator_basis": "ENROLLMENT",
        "enrolled_rate_status": "MEASURED",
        "partial_month_convention": "SYNTHETIC_PARTIAL_MONTH_V1",
    }
