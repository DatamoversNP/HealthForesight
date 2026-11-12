"""Synthetic measurement book for reviewed-248 candidate policies.

Illustrative only. Candidate codes from PDFs after removing known-bad E/M dumps.
Not certified payer includes / adjudication.
"""

from __future__ import annotations

import calendar
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from uuid import uuid4

import numpy as np

SOURCE_SYSTEM = "SYNTHETIC_REVIEWED_248_V1"
MEMBER_PREFIX = "R248_"
TENANT = "00000000-0000-0000-0000-000000000001"
PRE_START = date(2025, 1, 1)
PRE_END = date(2025, 12, 31)
POST_START = date(2026, 1, 1)
POST_END = date(2026, 10, 31)
DEFAULT_N_MEMBERS = 12000  # increased from 5k for multi-policy depth


def _months(start: date, end: date) -> List[date]:
    out: List[date] = []
    y, m = start.year, start.month
    while date(y, m, 1) <= end:
        out.append(date(y, m, 1))
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return out


def _month_span(month: date) -> Tuple[date, date]:
    last = calendar.monthrange(month.year, month.month)[1]
    return month, date(month.year, month.month, last) + timedelta(days=1)


def _money(allowed: float) -> Tuple[float, float]:
    paid = round(allowed * 0.8, 2)
    return paid, round(allowed - paid, 2)


def generate_book_for_policies(
    policy_specs: Sequence[Dict[str, Any]],
    *,
    n_members: int = DEFAULT_N_MEMBERS,
    seed: int = 20261107,
) -> Dict[str, Any]:
    """Generate enrollment + claim lines for candidate-measure policies only."""
    measurable = [p for p in policy_specs if p.get("decision") == "CANDIDATE_MEASURE" and p.get("candidate_codes")]
    rng = np.random.default_rng(seed)
    months = _months(PRE_START, POST_END)
    ingestion_id = str(uuid4())

    members: List[Dict[str, Any]] = []
    enrollment: List[Dict[str, Any]] = []
    for i in range(n_members):
        mid = f"{MEMBER_PREFIX}{i:08d}"
        lob = str(rng.choice(["COMMERCIAL", "COMMERCIAL", "COMMERCIAL", "MA", "MEDICAID"]))
        product = "PPO" if lob == "COMMERCIAL" else lob
        gender = str(rng.choice(["M", "F"]))
        age = int(rng.integers(18, 85))
        age_band = "18-44" if age < 45 else ("45-64" if age < 65 else "65+")
        members.append(
            {
                "member_id": mid,
                "lob": lob,
                "product_type": product,
                "gender": gender,
                "age": age,
                "age_band": age_band,
            }
        )
        for month in months:
            start, end = _month_span(month)
            enrollment.append(
                {
                    "member_id": mid,
                    "enrollment_month": month,
                    "enrollment_start_date": start,
                    "enrollment_end_date": end,
                    "lob": lob,
                    "market": "SYNTHETIC",
                    "age_band": age_band,
                    "gender": gender,
                    "risk_score": round(float(rng.uniform(0.4, 2.5)), 3),
                    "network_tier": "STANDARD",
                    "enrolled_flag": True,
                    "product_type": product,
                    "segment": "CONTIGUOUS",
                    "source_system": SOURCE_SYSTEM,
                }
            )

    claims: List[Dict[str, Any]] = []
    pharmacy: List[Dict[str, Any]] = []
    line_id = 0

    # Background noise so book isn't only target codes
    background = [
        ("99213", "professional", (120, 280)),
        ("80053", "lab", (40, 120)),
        ("97110", "therapy", (70, 150)),
    ]

    for month in months:
        m_start, m_end_excl = _month_span(month)
        period = "PRE" if month.year == 2025 else "POST"
        # Background volume
        for _ in range(max(80, n_members // 40)):
            mem = members[int(rng.integers(0, n_members))]
            code, cat, band = background[int(rng.integers(0, len(background)))]
            svc = m_start + timedelta(days=int(rng.integers(0, (m_end_excl - m_start).days)))
            allowed = float(rng.uniform(*band))
            paid, share = _money(allowed)
            line_id += 1
            claims.append(
                {
                    "claim_id": f"R248_BG_{line_id:08d}",
                    "claim_line_id": f"R248_BG_{line_id:08d}_1",
                    "member_id": mem["member_id"],
                    "provider_id": f"R248_PRV_{(line_id % 40):04d}",
                    "service_date": svc,
                    "cpt_code": code,
                    "hcpcs_code": None,
                    "service_category": cat,
                    "allowed_amount": round(allowed, 2),
                    "paid_amount": paid,
                    "member_cost_share": share,
                    "units": 1.0,
                    "lob": mem["lob"],
                    "market": "SYNTHETIC",
                    "place_of_service": "11",
                    "in_network": True,
                    "requires_prior_auth": False,
                    "facility_type": "OFFICE",
                    "source_system": SOURCE_SYSTEM,
                    "record_hash": json.dumps(
                        {"line_status": "ACTIVE", "policy_key": "background", "period": period}
                    ),
                }
            )

        for spec in measurable:
            codes = list(spec["candidate_codes"])
            cat = spec.get("service_category") or "general"
            bands = spec.get("allowed_bands") or {}
            # ~1.2% of members touch each policy/month → depth scales with n_members
            n_events = max(8, int(n_members * 0.012))
            for _ in range(n_events):
                mem = members[int(rng.integers(0, n_members))]
                code = str(rng.choice(codes))
                band = bands.get(code) or (100.0, 900.0)
                svc = m_start + timedelta(days=int(rng.integers(0, (m_end_excl - m_start).days)))
                allowed = float(rng.uniform(*band))
                paid, share = _money(allowed)
                is_hcpcs = bool(code and code[0].isalpha())
                line_id += 1
                claims.append(
                    {
                        "claim_id": f"R248_{spec['register_index']:03d}_{line_id:08d}",
                        "claim_line_id": f"R248_{spec['register_index']:03d}_{line_id:08d}_1",
                        "member_id": mem["member_id"],
                        "provider_id": f"R248_PRV_{(line_id % 40):04d}",
                        "service_date": svc,
                        "cpt_code": None if is_hcpcs else code,
                        "hcpcs_code": code if is_hcpcs else None,
                        "service_category": cat,
                        "allowed_amount": round(allowed, 2),
                        "paid_amount": paid,
                        "member_cost_share": share,
                        "units": float(rng.integers(1, 4)),
                        "lob": mem["lob"],
                        "market": "SYNTHETIC",
                        "place_of_service": "22" if cat in {"imaging", "surgery", "ambulance"} else "11",
                        "in_network": True,
                        "requires_prior_auth": "PRIOR_AUTH" in str(spec.get("policy_type") or "").upper(),
                        "facility_type": "HOPD" if cat in {"imaging", "surgery"} else "OFFICE",
                        "source_system": SOURCE_SYSTEM,
                        "record_hash": json.dumps(
                            {
                                "line_status": "ACTIVE",
                                "policy_key": f"r248_{spec['register_index']}",
                                "period": period,
                                "candidate": True,
                            }
                        ),
                    }
                )
                if cat == "pharmacy" or (is_hcpcs and code[0] in "JS"):
                    pharmacy.append(
                        {
                            "member_id": mem["member_id"],
                            "fill_date": svc.isoformat(),
                            "ndc": f"00000{line_id % 100000:05d}",
                            "days_supply": int(rng.choice([30, 90])),
                            "quantity": float(rng.integers(30, 90)),
                            "allowed_amount": round(allowed, 2),
                            "paid_amount": paid,
                            "source_system": SOURCE_SYSTEM,
                            "policy_key": f"r248_{spec['register_index']}",
                        }
                    )

    return {
        "meta": {
            "source_system": SOURCE_SYSTEM,
            "seed": seed,
            "n_members": n_members,
            "ingestion_id": ingestion_id,
            "baseline_window": [PRE_START.isoformat(), PRE_END.isoformat()],
            "observation_window": [POST_START.isoformat(), POST_END.isoformat()],
            "measurable_policies": len(measurable),
            "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
            "note": "Candidate codes only after removing bad E/M exports; not certified.",
        },
        "members": members,
        "enrollment_records": enrollment,
        "claims_lines": claims,
        "pharmacy_claims": pharmacy,
        "policy_specs": [
            {
                "register_index": p["register_index"],
                "name": p["name"],
                "candidate_codes": p["candidate_codes"],
                "service_category": p.get("service_category"),
            }
            for p in measurable
        ],
    }


def write_entity_pack(book: Dict[str, Any], out_dir: Path) -> Dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for key in ("members", "enrollment_records", "claims_lines", "pharmacy_claims", "policy_specs"):
        path = out_dir / f"{key}.jsonl"
        rows = book.get(key) or []
        with path.open("w") as f:
            for row in rows:
                f.write(json.dumps(row, default=str) + "\n")
        counts[key] = len(rows)
    (out_dir / "meta.json").write_text(json.dumps(book["meta"], indent=2, default=str))
    return counts
