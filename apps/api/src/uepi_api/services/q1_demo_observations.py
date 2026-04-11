"""Q1 demo: policy-scoped claims + weekly observation helpers (2026-01-01 .. 2026-03-31).

Used by scripts/seed_q1_2026_observations_demo.py. Keeps narrative curves out of routers."""
from __future__ import annotations

import math
import random
from datetime import date, timedelta
from typing import Any, Dict, Iterator, List, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from uepi_api.models.policy import PolicyCodeSet, PolicyVersion
from uepi_api.repositories.canonical_data import CanonicalDataRepository
from uepi_api.services.database_baseline_computation import DEMO_MARKETS_WHEN_ALL
from uepi_api.services.policy_scoped_data_generation import (
    build_policy_claims_filters,
    extract_policy_target_codes,
)


def monday_on_or_before(d: date) -> date:
    return d - timedelta(days=d.weekday())


def iter_iso_week_slices(range_start: date, range_end: date) -> Iterator[Tuple[date, date, int]]:
    """Yield (slice_start, slice_end, week_index) for each ISO week overlapping [range_start, range_end]."""
    cur = monday_on_or_before(range_start)
    idx = 0
    while cur <= range_end:
        wk_end = cur + timedelta(days=6)
        sl_start = max(cur, range_start)
        sl_end = min(wk_end, range_end)
        if sl_start <= sl_end:
            yield sl_start, sl_end, idx
            idx += 1
        cur += timedelta(days=7)


def narrative_volume_multiplier(policy_index: int, week_index: int) -> float:
    """Per-policy weekly volume vs baseline (1.0). Designed for varied ON_TRACK / AT_RISK / BACKFIRE demos."""
    t = week_index / 13.0
    archetype = policy_index % 5
    if archetype == 0:
        return 1.0 + 0.06 * math.sin(t * math.pi * 2)
    if archetype == 1:
        return 0.98 - 0.12 * t + 0.03 * math.sin(t * math.pi * 3)
    if archetype == 2:
        return 1.0 + 0.18 * t + 0.04 * math.sin(t * math.pi * 2)
    if archetype == 3:
        return 1.0 + 0.12 * math.sin(t * math.pi * 4) + 0.05 * math.cos(t * math.pi * 2)
    # archetype 4: mid-quarter stress then partial recovery
    spike = 0.28 * math.exp(-((week_index - 7) ** 2) / 4.0)
    return 1.0 + spike - 0.05 * t


def enrich_policy_dict_with_code_sets(
    db: Session,
    tenant_id: UUID,
    policy_id: UUID,
    policy_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """If metadata has no procedure codes, attach codes from policy_code_sets (latest version)."""
    pf = build_policy_claims_filters(policy_dict)
    if pf.get("procedure_codes") or pf.get("cpt_codes"):
        return policy_dict

    rows = (
        db.query(PolicyCodeSet.code)
        .join(PolicyVersion, PolicyCodeSet.version_id == PolicyVersion.id)
        .filter(
            PolicyCodeSet.tenant_id == tenant_id,
            PolicyVersion.policy_id == policy_id,
        )
        .all()
    )
    codes = list({str(r[0]).strip() for r in rows if r and r[0]})
    if not codes:
        return policy_dict

    meta = dict(policy_dict.get("metadata") or {})
    scope = dict(meta.get("scope") or policy_dict.get("scope") or {})
    existing = scope.get("procedure_codes")
    if isinstance(existing, list):
        scope["procedure_codes"] = list({*existing, *codes})
    else:
        scope["procedure_codes"] = codes
    meta["scope"] = scope
    out = {**policy_dict, "metadata": meta, "scope": scope}
    return out


def _service_categories_for_codes(procedure_codes: List[str]) -> Dict[str, Dict[str, Any]]:
    default_service_categories = {
        "PRIMARY_CARE": {"codes": ["99213", "99214", "99215"], "avg_cost": 150.0},
        "SPECIALTY_CARE": {"codes": ["99243", "99244", "99245"], "avg_cost": 300.0},
        "ADVANCED_IMAGING": {"codes": ["70450", "72141", "72142"], "avg_cost": 800.0},
        "LABORATORY": {"codes": ["80053", "85025", "85027"], "avg_cost": 50.0},
        "URGENT_CARE": {"codes": ["99281", "99282", "99283"], "avg_cost": 200.0},
        "INFUSION": {"codes": ["96413", "96415"], "avg_cost": 1200.0},
    }
    service_categories: Dict[str, Dict[str, Any]] = {}
    for code in procedure_codes:
        c = str(code).strip()
        if c.startswith(("99213", "99214", "99215")):
            cat = "PRIMARY_CARE"
        elif c.startswith("992"):
            cat = "SPECIALTY_CARE"
        elif c.startswith(("704", "721", "705")):
            cat = "ADVANCED_IMAGING"
        elif c.startswith("8"):
            cat = "LABORATORY"
        elif c.startswith(("99281", "99282", "99283")):
            cat = "URGENT_CARE"
        elif c.startswith("964"):
            cat = "INFUSION"
        else:
            cat = "SPECIALTY_CARE"
        if cat not in service_categories:
            ac = default_service_categories.get(cat, {"codes": [], "avg_cost": 400.0})
            service_categories[cat] = {"codes": [], "avg_cost": ac["avg_cost"]}
        if c not in service_categories[cat]["codes"]:
            service_categories[cat]["codes"].append(c)
    for cat, info in list(service_categories.items()):
        if not info["codes"]:
            del service_categories[cat]
    return service_categories


def generate_claims_for_policy_date_range(
    db: Session,
    tenant_id: UUID,
    policy_id: UUID,
    policy_dict: Dict[str, Any],
    range_start: date,
    range_end: date,
    policy_index: int,
    member_ids: List[str],
    provider_ids: List[str],
    ingestion_id: UUID,
    base_claims_per_day: int = 14,
    rng_seed: int = 20260101,
) -> int:
    """Insert claims_lines for each day in range; returns rows inserted (best effort)."""
    target_codes = extract_policy_target_codes(policy_dict)
    procedure_codes = target_codes["procedure_codes"]
    if not procedure_codes:
        return 0

    service_categories = _service_categories_for_codes(procedure_codes)
    if not service_categories:
        return 0

    lob_options = target_codes["lob"] if target_codes["lob"] else ["COMMERCIAL"]
    market_options = target_codes["markets"] if target_codes["markets"] else DEMO_MARKETS_WHEN_ALL
    if not lob_options:
        lob_options = ["COMMERCIAL"]
    if not market_options:
        market_options = list(DEMO_MARKETS_WHEN_ALL)

    diagnosis_codes = target_codes["diagnosis_codes"] if target_codes["diagnosis_codes"] else ["E11.9", "I10", "M79.3", "Z00.00"]

    repo = CanonicalDataRepository(db)
    total_inserted = 0
    day_offset = 0
    d = range_start
    while d <= range_end:
        week_idx = (d - range_start).days // 7
        mult = narrative_volume_multiplier(policy_index, week_idx)
        n = max(4, int(base_claims_per_day * mult))
        rnd = random.Random(rng_seed + policy_index * 100_003 + day_offset * 1_001)

        claims_data: List[Dict[str, Any]] = []
        for i in range(n):
            member_id = rnd.choice(member_ids)
            provider_id = rnd.choice(provider_ids)
            category = rnd.choice(list(service_categories.keys()))
            code_info = service_categories[category]
            cpt_code = rnd.choice(code_info["codes"])
            base_cost = code_info["avg_cost"]
            cost_variation = rnd.uniform(0.75, 1.28)
            allowed_amount = base_cost * cost_variation
            paid_amount = allowed_amount * rnd.uniform(0.82, 0.99)
            system_affiliations = ["HOSPITAL_SYSTEM_A", "HOSPITAL_SYSTEM_B", "INDEPENDENT", "PHYSICIAN_GROUP"]
            unique_suffix = uuid4().hex[:10]
            dx = rnd.choice(diagnosis_codes)
            claims_data.append(
                {
                    "claim_id": f"Q1CLM_{d.isoformat()}_{policy_id.hex[:8]}_{i:05d}_{unique_suffix}",
                    "claim_line_id": f"Q1LIN_{d.isoformat()}_{policy_id.hex[:8]}_{i:05d}_{unique_suffix}",
                    "member_id": member_id,
                    "provider_id": provider_id,
                    "service_date": d,
                    "paid_date": d + timedelta(days=rnd.randint(1, 21)),
                    "lob": rnd.choice(lob_options),
                    "market": rnd.choice(market_options),
                    "cpt_code": cpt_code,
                    "hcpcs_code": None,
                    "icd10_diagnosis_codes": [dx],
                    "service_category": category,
                    "place_of_service": rnd.choice(["11", "22", "23"]),
                    "units": float(rnd.randint(1, 3)),
                    "allowed_amount": float(allowed_amount),
                    "paid_amount": float(paid_amount),
                    "member_cost_share": float(max(0.0, allowed_amount - paid_amount)),
                    "in_network": rnd.choice([True, True, True, False]),
                    "requires_prior_auth": rnd.choice([True, False, False]),
                    "prior_auth_approved": rnd.choice([True, None]),
                    "facility_type": rnd.choice(["HOSPITAL", "CLINIC", "OFFICE", "URGENT_CARE"]),
                    "system_affiliation": rnd.choice(system_affiliations),
                }
            )

        loaded = repo.bulk_insert_claims_lines(
            tenant_id=tenant_id,
            claims_data=claims_data,
            source_system="Q1_2026_DEMO",
            source_file_id=f"q1_2026_demo_{policy_id.hex[:8]}_{d.isoformat()}",
            ingestion_id=ingestion_id,
        )
        total_inserted += loaded
        day_offset += 1
        d += timedelta(days=1)

    return total_inserted


def behavioral_hint_for_week(mult: float) -> Dict[str, Any]:
    if mult > 1.22:
        return {
            "risk_factors": [
                "Elevated target-service volume vs plan",
                "Possible substitution or access friction",
            ],
            "recommendations": ["Review network adequacy", "Tighten UM where clinically appropriate"],
            "demo_note": "High-volume week seeded for demo narrative.",
        }
    if mult < 0.92:
        return {
            "summary": "Lower observed utilization this week vs typical baseline period.",
            "demo_note": "Low-volume week seeded for demo narrative.",
        }
    return {}
