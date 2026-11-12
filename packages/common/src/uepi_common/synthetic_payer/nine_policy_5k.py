"""Generate a 5,000-member additive mock-client book for the nine PDF policies.

Windows:
  PRE  (baseline):    2025-01-01 .. 2025-12-31
  POST (observation): 2026-01-01 .. 2026-10-31

Produces full target-model entity dicts plus operational claim/enrollment rows.
Synthetic illustrative only — not commercial benchmarks or certified authority.
"""
from __future__ import annotations

import calendar
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple
from uuid import uuid4

import numpy as np

SOURCE_SYSTEM = "SYNTHETIC_NINE_POLICY_5K_V1"
SEED = 20261107
N_MEMBERS = 5000
TENANT = "00000000-0000-0000-0000-000000000001"
MEMBER_PREFIX = "N5K_"

PRE_START = date(2025, 1, 1)
PRE_END = date(2025, 12, 31)
POST_START = date(2026, 1, 1)
POST_END = date(2026, 10, 31)

# Candidate codes only — not certified payer includes.
POLICY_SPECS: Dict[str, Dict[str, Any]] = {
    "mri": {
        "codes": ["72148", "72149"],
        "pos": ["22", "11"],
        "allowed": (900, 2200),
        "category": "mri",
        "requires_pa": True,
    },
    "ncd": {
        "codes": ["70551", "70553"],
        "pos": ["22"],
        "allowed": (700, 1800),
        "category": "ncd",
        "requires_pa": False,
    },
    "lcd": {
        "codes": ["70540", "70542"],
        "pos": ["22"],
        "allowed": (600, 1500),
        "category": "lcd",
        "requires_pa": False,
    },
    "infusion": {
        "codes": ["96413", "J1745"],
        "pos": ["22", "11", "12"],
        "allowed": (800, 3500),
        "category": "infusion",
        "requires_pa": False,
    },
    "therapy": {
        "codes": ["97110", "97112", "97140"],
        "pos": ["11"],
        "allowed": (70, 180),
        "category": "therapy",
        "requires_pa": False,
    },
    "mue": {
        "codes": ["97110"],
        "pos": ["11"],
        "allowed": (70, 120),
        "category": "mue",
        "units": (1, 8),
        "requires_pa": False,
    },
    "ptp": {
        "codes": ["70553", "70551"],
        "pos": ["22"],
        "allowed": (500, 1600),
        "category": "ptp",
        "requires_pa": False,
    },
    "sos": {
        "codes": ["72148", "72149"],
        "pos": ["22", "11"],
        "allowed": (900, 2200),
        "category": "sos",
        "requires_pa": False,
    },
    "mppr": {
        "codes": ["27447", "64483"],
        "pos": ["24"],
        "allowed": (1200, 4000),
        "category": "mppr",
        "requires_pa": False,
    },
}

BACKGROUND = {
    "PROFESSIONAL": {"codes": ["99213", "99214"], "pos": ["11"], "allowed": (120, 280)},
    "OUTPATIENT": {"codes": ["80053", "85025"], "pos": ["22"], "allowed": (40, 180)},
    "EMERGENCY": {"codes": ["99284", "99285"], "pos": ["23"], "allowed": (800, 2500)},
    "INPATIENT": {"codes": ["99223"], "pos": ["21"], "allowed": (1500, 5000)},
}


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


def _age_band(age: int) -> str:
    if age < 18:
        return "0-17"
    if age < 45:
        return "18-44"
    if age < 65:
        return "45-64"
    return "65+"


def _money(allowed: float) -> Tuple[float, float]:
    paid = round(allowed * 0.8, 2)
    share = round(allowed - paid, 2)
    return paid, share


def _rand_day(rng: np.random.Generator, start: date, end: date) -> date:
    span = (end - start).days
    return start + timedelta(days=int(rng.integers(0, max(span, 1) + 1)))


def generate_book(n_members: int = N_MEMBERS, seed: int = SEED) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)
    ingestion_id = str(uuid4())

    providers: List[Dict[str, Any]] = []
    facilities: List[Dict[str, Any]] = []
    for i in range(40):
        pid = f"N5K_PRV_{i:04d}"
        fid = f"N5K_FAC_{i:04d}"
        specialty = ["RADIOLOGY", "ORTHOPEDICS", "PHYSICAL_THERAPY", "ONCOLOGY", "PRIMARY_CARE", "EMERGENCY"][i % 6]
        providers.append(
            {
                "tenant_id": TENANT,
                "source_system": SOURCE_SYSTEM,
                "provider_id": pid,
                "npi": f"1{i:09d}",
                "provider_type": "PHYSICIAN" if i % 3 else "FACILITY",
                "specialty": specialty,
                "network_status": "IN" if i % 10 else "OUT",
                "market": "SYNTHETIC",
            }
        )
        facilities.append(
            {
                "tenant_id": TENANT,
                "source_system": SOURCE_SYSTEM,
                "facility_id": fid,
                "facility_name": f"Synthetic Facility {i}",
                "facility_type": ["HOPD", "ASC", "OFFICE", "FREESTANDING"][i % 4],
                "market": "SYNTHETIC",
                "provider_id": pid,
            }
        )

    networks = [
        {
            "tenant_id": TENANT,
            "source_system": SOURCE_SYSTEM,
            "network_id": "N5K_NET_STANDARD",
            "network_name": "Synthetic Standard Network",
            "tier": "STANDARD",
            "effective_start": PRE_START.isoformat(),
        }
    ]
    contracts = [
        {
            "tenant_id": TENANT,
            "source_system": SOURCE_SYSTEM,
            "contract_id": f"N5K_CTR_{i:04d}",
            "provider_id": p["provider_id"],
            "network_id": "N5K_NET_STANDARD",
            "rate_type": "FEE_SCHEDULE",
            "effective_start": PRE_START.isoformat(),
        }
        for i, p in enumerate(providers)
    ]

    benefits = [
        {
            "tenant_id": TENANT,
            "source_system": SOURCE_SYSTEM,
            "benefit_design_id": "N5K_BD_COMM",
            "product_type": "PPO",
            "lob": "COMMERCIAL",
            "plan_name": "Synthetic Commercial PPO",
            "deductible_individual": 1500,
            "oop_max_individual": 6000,
            "effective_start": PRE_START.isoformat(),
        },
        {
            "tenant_id": TENANT,
            "source_system": SOURCE_SYSTEM,
            "benefit_design_id": "N5K_BD_MA",
            "product_type": "MA",
            "lob": "MA",
            "plan_name": "Synthetic Medicare Advantage",
            "deductible_individual": 0,
            "oop_max_individual": 5500,
            "effective_start": PRE_START.isoformat(),
        },
    ]

    members: List[Dict[str, Any]] = []
    eligibility: List[Dict[str, Any]] = []
    risk: List[Dict[str, Any]] = []
    accumulators: List[Dict[str, Any]] = []
    months = _months(PRE_START, POST_END)

    for i in range(n_members):
        mid = f"{MEMBER_PREFIX}{i:08d}"
        lob = str(rng.choice(["COMMERCIAL", "COMMERCIAL", "COMMERCIAL", "MA", "MEDICAID"]))
        age = int(rng.integers(18, 85))
        sex = str(rng.choice(["M", "F"]))
        dob = date(PRE_START.year - age, int(rng.integers(1, 13)), int(rng.integers(1, 28)))
        bd = "N5K_BD_MA" if lob == "MA" else "N5K_BD_COMM"
        members.append(
            {
                "tenant_id": TENANT,
                "source_system": SOURCE_SYSTEM,
                "member_id": mid,
                "subscriber_id": mid,
                "dob": dob.isoformat(),
                "birth_year": dob.year,
                "age": age,
                "gender": sex,
                "lob": lob,
                "market": "SYNTHETIC",
                "coverage_status": "ACTIVE",
                "benefit_design_id": bd,
            }
        )
        for month in months:
            start, end = _month_span(month)
            eligibility.append(
                {
                    "tenant_id": TENANT,
                    "source_system": SOURCE_SYSTEM,
                    "member_id": mid,
                    "enrollment_month": month.isoformat(),
                    "coverage_start": start.isoformat(),
                    "coverage_end": (end - timedelta(days=1)).isoformat(),
                    "lob": lob,
                    "product_type": "PPO" if lob == "COMMERCIAL" else lob,
                    "coverage_status": "ACTIVE",
                    "benefit_design_id": bd,
                }
            )
        for qmonth in months[::3]:
            risk.append(
                {
                    "tenant_id": TENANT,
                    "source_system": SOURCE_SYSTEM,
                    "member_id": mid,
                    "risk_run_date": qmonth.isoformat(),
                    "month": qmonth.strftime("%Y-%m"),
                    "risk_score": round(float(rng.gamma(2.0, 0.5)), 3),
                    "risk_model_name": "SYNTHETIC_HCC",
                    "risk_model_version": "mock-1",
                }
            )
        accumulators.append(
            {
                "tenant_id": TENANT,
                "source_system": SOURCE_SYSTEM,
                "member_id": mid,
                "benefit_design_id": bd,
                "plan_year": 2025,
                "deductible_met": round(float(rng.uniform(0, 1500)), 2),
                "oop_met": round(float(rng.uniform(0, 4000)), 2),
            }
        )

    claim_headers: List[Dict[str, Any]] = []
    claim_lines: List[Dict[str, Any]] = []
    episodes: List[Dict[str, Any]] = []
    pharmacy: List[Dict[str, Any]] = []
    pa_requests: List[Dict[str, Any]] = []
    appeals: List[Dict[str, Any]] = []
    line_seq = 0

    def add_line(
        *,
        member_id: str,
        provider_id: str,
        service_date: date,
        cpt: Optional[str],
        allowed: float,
        units: float,
        pos: str,
        category: str,
        policy_key: str,
        period: str,
        requires_pa: bool = False,
        role: Optional[str] = None,
        modifier: Optional[str] = None,
        site: Optional[str] = None,
        hcpcs: Optional[str] = None,
        pharmacy_flag: bool = False,
        claim_id: Optional[str] = None,
    ) -> str:
        nonlocal line_seq
        line_seq += 1
        cid = claim_id or f"N5K_CLM_{line_seq:08d}"
        # Always include line_seq so multi-event same-day groups stay unique.
        lid = f"{cid}-{role or 'L'}-{line_seq:08d}"
        paid, share = _money(allowed)
        extras = {
            "policy_key": policy_key,
            "period": period,
            "line_status": "ACTIVE",
            "role": role,
            "modifier": modifier,
            "site": site,
            "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
            "book": "nine_policy_5k",
        }
        claim_lines.append(
            {
                "tenant_id": TENANT,
                "claim_id": cid,
                "claim_line_id": lid,
                "member_id": member_id,
                "provider_id": provider_id,
                "service_date": service_date.isoformat(),
                "paid_date": (service_date + timedelta(days=21)).isoformat(),
                "adjudication_date": (service_date + timedelta(days=14)).isoformat(),
                "lob": "COMMERCIAL",
                "market": "SYNTHETIC",
                "cpt_code": cpt if cpt and not str(cpt).startswith("J") else None,
                "hcpcs_code": hcpcs or (cpt if cpt and str(cpt).startswith("J") else None),
                "service_category": "PHARMACY" if pharmacy_flag else category,
                "place_of_service": pos,
                "units": units,
                "allowed_amount": round(allowed, 2),
                "paid_amount": paid,
                "member_cost_share": share,
                "in_network": True,
                "requires_prior_auth": requires_pa,
                "prior_auth_approved": None,
                "facility_type": site,
                "source_system": SOURCE_SYSTEM,
                "record_hash": json.dumps(extras, separators=(",", ":")),
                "policy_key": policy_key,
                "period": period,
            }
        )
        return cid

    # Assign each member a primary policy affinity + background utilization.
    policy_keys = list(POLICY_SPECS.keys())
    for mi, member in enumerate(members):
        mid = member["member_id"]
        affinity = policy_keys[mi % len(policy_keys)]
        secondary = policy_keys[(mi * 3 + 1) % len(policy_keys)]
        for period, start, end in (
            ("PRE", PRE_START, PRE_END),
            ("POST", POST_START, POST_END),
        ):
            # Policy-tagged events
            for key in {affinity, secondary}:
                spec = POLICY_SPECS[key]
                n_events = int(rng.integers(1, 4 if period == "PRE" else 3))
                for _ in range(n_events):
                    day = _rand_day(rng, start, end)
                    prov = providers[int(rng.integers(0, len(providers)))]
                    lo, hi = spec["allowed"]
                    if key == "mppr":
                        cid = f"N5K_MPPR_{mi:05d}_{period}_{line_seq + 1:08d}"
                        a1 = float(rng.uniform(2000, 4000))
                        a2 = float(rng.uniform(400, 900))
                        add_line(
                            member_id=mid,
                            provider_id=prov["provider_id"],
                            service_date=day,
                            cpt="27447",
                            allowed=a1,
                            units=1,
                            pos="24",
                            category="mppr",
                            policy_key="mppr",
                            period=period,
                            role="primary",
                            claim_id=cid,
                        )
                        add_line(
                            member_id=mid,
                            provider_id=prov["provider_id"],
                            service_date=day,
                            cpt="64483",
                            allowed=a2,
                            units=1,
                            pos="24",
                            category="mppr",
                            policy_key="mppr",
                            period=period,
                            role="secondary",
                            claim_id=cid,
                        )
                        claim_headers.append(
                            {
                                "tenant_id": TENANT,
                                "source_system": SOURCE_SYSTEM,
                                "claim_id": cid,
                                "member_id": mid,
                                "claim_type": "PROFESSIONAL",
                                "service_from": day.isoformat(),
                                "total_allowed": round(a1 + a2, 2),
                                "period": period,
                                "policy_key": "mppr",
                            }
                        )
                    elif key == "ptp":
                        cid = f"N5K_PTP_{mi:05d}_{period}_{line_seq + 1:08d}"
                        mod = "59" if rng.random() < 0.2 else None
                        add_line(
                            member_id=mid,
                            provider_id=prov["provider_id"],
                            service_date=day,
                            cpt="70553",
                            allowed=float(rng.uniform(900, 1600)),
                            units=1,
                            pos="22",
                            category="ptp",
                            policy_key="ptp",
                            period=period,
                            role="column_one",
                            claim_id=cid,
                        )
                        add_line(
                            member_id=mid,
                            provider_id=prov["provider_id"],
                            service_date=day,
                            cpt="70551",
                            allowed=float(rng.uniform(500, 1100)),
                            units=1,
                            pos="22",
                            category="ptp",
                            policy_key="ptp",
                            period=period,
                            role="column_two",
                            modifier=mod,
                            claim_id=cid,
                        )
                    elif key == "mue":
                        units = float(rng.integers(1, 9))
                        unit_price = float(rng.uniform(*spec["allowed"]))
                        add_line(
                            member_id=mid,
                            provider_id=prov["provider_id"],
                            service_date=day,
                            cpt="97110",
                            allowed=round(unit_price * units, 2),
                            units=units,
                            pos="11",
                            category="mue",
                            policy_key="mue",
                            period=period,
                        )
                    elif key == "infusion":
                        site = str(rng.choice(["HOPD", "OFFICE", "HOME"]))
                        pos = {"HOPD": "22", "OFFICE": "11", "HOME": "12"}[site]
                        code = str(rng.choice(spec["codes"]))
                        cid = add_line(
                            member_id=mid,
                            provider_id=prov["provider_id"],
                            service_date=day,
                            cpt=None if code.startswith("J") else code,
                            hcpcs=code if code.startswith("J") else None,
                            allowed=float(rng.uniform(*spec["allowed"])),
                            units=1,
                            pos=pos,
                            category="infusion",
                            policy_key="infusion",
                            period=period,
                            site=site,
                        )
                        episodes.append(
                            {
                                "tenant_id": TENANT,
                                "source_system": SOURCE_SYSTEM,
                                "episode_id": f"EP_{cid}",
                                "member_id": mid,
                                "episode_type": "INFUSION",
                                "start_date": day.isoformat(),
                                "site": site,
                                "period": period,
                            }
                        )
                    elif key == "sos":
                        site = str(rng.choice(["HOPD", "FREESTANDING"]))
                        pos = "22" if site == "HOPD" else "11"
                        code = str(rng.choice(spec["codes"]))
                        add_line(
                            member_id=mid,
                            provider_id=prov["provider_id"],
                            service_date=day,
                            cpt=code,
                            allowed=float(rng.uniform(*spec["allowed"])),
                            units=1,
                            pos=pos,
                            category="sos",
                            policy_key="sos",
                            period=period,
                            site=site,
                        )
                    else:
                        code = str(rng.choice(spec["codes"]))
                        is_j = code.startswith("J")
                        cid = add_line(
                            member_id=mid,
                            provider_id=prov["provider_id"],
                            service_date=day,
                            cpt=None if is_j else code,
                            hcpcs=code if is_j else None,
                            allowed=float(rng.uniform(*spec["allowed"])),
                            units=1,
                            pos=str(rng.choice(spec["pos"])),
                            category=spec["category"],
                            policy_key=key,
                            period=period,
                            requires_pa=bool(spec.get("requires_pa")),
                        )
                        if key == "mri":
                            pa_id = f"N5K_PA_{mi:05d}_{period}_{day.isoformat().replace('-', '')}"
                            pa_requests.append(
                                {
                                    "tenant_id": TENANT,
                                    "source_system": SOURCE_SYSTEM,
                                    "pa_request_id": pa_id,
                                    "member_id": mid,
                                    "requested_service_code": code,
                                    "request_date": (day - timedelta(days=7)).isoformat(),
                                    "service_date": day.isoformat(),
                                    "decision_status": "REVIEW_REQUIRED",
                                    "period": period,
                                    "policy_key": "mri",
                                    "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
                                }
                            )
                            if rng.random() < 0.08:
                                appeals.append(
                                    {
                                        "tenant_id": TENANT,
                                        "source_system": SOURCE_SYSTEM,
                                        "appeal_id": f"N5K_APL_{pa_id}",
                                        "member_id": mid,
                                        "related_pa_request_id": pa_id,
                                        "appeal_date": day.isoformat(),
                                        "outcome": "PENDING",
                                        "period": period,
                                    }
                                )

            # Background utilization
            for cat, bg in BACKGROUND.items():
                if rng.random() < (0.55 if cat == "PROFESSIONAL" else 0.18):
                    day = _rand_day(rng, start, end)
                    prov = providers[int(rng.integers(0, len(providers)))]
                    code = str(rng.choice(bg["codes"]))
                    add_line(
                        member_id=mid,
                        provider_id=prov["provider_id"],
                        service_date=day,
                        cpt=code,
                        allowed=float(rng.uniform(*bg["allowed"])),
                        units=1,
                        pos=str(rng.choice(bg["pos"])),
                        category=cat,
                        policy_key="background",
                        period=period,
                    )

            # Pharmacy entity + claim line token
            if rng.random() < 0.45:
                day = _rand_day(rng, start, end)
                allowed = float(rng.uniform(15, 350))
                paid, share = _money(allowed)
                rx_id = f"N5K_RX_{mi:05d}_{period}_{line_seq + 1:08d}"
                pharmacy.append(
                    {
                        "tenant_id": TENANT,
                        "source_system": SOURCE_SYSTEM,
                        "pharmacy_claim_id": rx_id,
                        "member_id": mid,
                        "fill_date": day.isoformat(),
                        "ndc": f"00000-{int(rng.integers(1000, 9999))}-{int(rng.integers(10, 99))}",
                        "days_supply": int(rng.choice([30, 90])),
                        "quantity": float(rng.choice([30, 60, 90])),
                        "allowed_amount": round(allowed, 2),
                        "paid_amount": paid,
                        "member_cost_share": share,
                        "period": period,
                    }
                )
                add_line(
                    member_id=mid,
                    provider_id=providers[0]["provider_id"],
                    service_date=day,
                    cpt=None,
                    allowed=allowed,
                    units=1,
                    pos="01",
                    category="PHARMACY",
                    policy_key="pharmacy",
                    period=period,
                    pharmacy_flag=True,
                    claim_id=rx_id,
                )

    # Build claim headers for remaining single-line claims (sample)
    seen = {h["claim_id"] for h in claim_headers}
    for line in claim_lines:
        if line["claim_id"] in seen:
            continue
        if line["policy_key"] in {"background", "pharmacy"}:
            continue
        seen.add(line["claim_id"])
        claim_headers.append(
            {
                "tenant_id": TENANT,
                "source_system": SOURCE_SYSTEM,
                "claim_id": line["claim_id"],
                "member_id": line["member_id"],
                "claim_type": "PROFESSIONAL",
                "service_from": line["service_date"],
                "total_allowed": line["allowed_amount"],
                "period": line["period"],
                "policy_key": line["policy_key"],
            }
        )

    enrollment_ops = list(_iter_enrollment_ops(members, months))

    return {
        "meta": {
            "source_system": SOURCE_SYSTEM,
            "seed": seed,
            "n_members": n_members,
            "baseline_window": [PRE_START.isoformat(), PRE_END.isoformat()],
            "observation_window": [POST_START.isoformat(), POST_END.isoformat()],
            "ingestion_id": ingestion_id,
            "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
            "additive_to": "SYNTHETIC_LONGITUDINAL_V1",
        },
        "entities": {
            "MemberMaster": members,
            "EligibilityEnrollment": eligibility,
            "MemberRiskStratification": risk,
            "ClaimHeader": claim_headers,
            "ClaimLine": claim_lines,
            "EpisodeOfCare": episodes,
            "PharmacyClaim": pharmacy,
            "ProviderMaster": providers,
            "FacilityMaster": facilities,
            "NetworkConfiguration": networks,
            "ProviderContract": contracts,
            "BenefitDesign": benefits,
            "MemberAccumulator": accumulators,
            "PriorAuthorizationRequest": pa_requests,
            "AppealGrievance": appeals,
        },
        "operational": {
            "claims_lines": claim_lines,
            "enrollment_records": enrollment_ops,
        },
    }


def _iter_enrollment_ops(members: List[Dict[str, Any]], months: List[date]) -> Iterator[Dict[str, Any]]:
    for member in members:
        for month in months:
            start, end_excl = _month_span(month)
            yield {
                "member_id": member["member_id"],
                "enrollment_month": month.isoformat(),
                "lob": member["lob"],
                "market": "SYNTHETIC",
                "age_band": _age_band(int(member["age"])),
                "gender": member["gender"],
                "risk_score": 0,
                "network_tier": "SYNTHETIC",
                "enrolled_flag": True,
                "enrollment_start_date": start.isoformat(),
                "enrollment_end_date": end_excl.isoformat(),
                "product_type": member.get("benefit_design_id"),
                "segment": "CONTIGUOUS",
                "record_hash": json.dumps(
                    {"book": "nine_policy_5k", "partial_month_convention": "SYNTHETIC_PARTIAL_MONTH_V1"},
                    separators=(",", ":"),
                ),
            }


def write_entity_pack(book: Dict[str, Any], out_dir: Path) -> Dict[str, int]:
    import pandas as pd

    out_dir.mkdir(parents=True, exist_ok=True)
    counts: Dict[str, int] = {}
    (out_dir / "meta.json").write_text(json.dumps(book["meta"], indent=2), encoding="utf-8")
    for name, rows in book["entities"].items():
        counts[name] = len(rows)
        df = pd.DataFrame(rows)
        df.to_parquet(out_dir / f"{name}.parquet", index=False)
        # CSV for smaller entities only
        if len(rows) <= 200_000:
            df.to_csv(out_dir / f"{name}.csv", index=False)
    # Operational convenience extracts
    pd.DataFrame(book["operational"]["claims_lines"]).to_parquet(out_dir / "operational_claims_lines.parquet", index=False)
    pd.DataFrame(book["operational"]["enrollment_records"]).to_parquet(
        out_dir / "operational_enrollment_records.parquet", index=False
    )
    counts["operational_claims_lines"] = len(book["operational"]["claims_lines"])
    counts["operational_enrollment_records"] = len(book["operational"]["enrollment_records"])
    (out_dir / "counts.json").write_text(json.dumps(counts, indent=2), encoding="utf-8")
    return counts
