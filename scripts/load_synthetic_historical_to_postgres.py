#!/usr/bin/env python3
"""
Generate synthetic claims / enrollment / providers for a fixed calendar window and
bulk-load into PostgreSQL (canonical tables) via CanonicalDataRepository.

Typical Azure fresh demo (Jan 2023 – Dec 2025, ≥1000 unique members by default):
  export DATABASE_URL='postgresql+psycopg2://...'
  export PYTHONPATH=apps/api/src:packages/common/src
  python3 scripts/load_synthetic_historical_to_postgres.py

Run from repo root. Uses scripts/synth/generate.py (claims_per_month_range for density).
"""
from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence
from uuid import UUID, uuid4

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
API_SRC = REPO_ROOT / "apps" / "api" / "src"
COMMON_SRC = REPO_ROOT / "packages" / "common" / "src"
SYNTH_DIR = REPO_ROOT / "scripts" / "synth"
for p in (str(API_SRC), str(COMMON_SRC), str(SYNTH_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.pop("CORS_ORIGINS", None)

_env = REPO_ROOT / "apps" / "api" / ".env"
if _env.exists():
    with open(_env) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                if k in ("CORS_ORIGINS",):
                    continue
                os.environ.setdefault(k, v.strip().replace('"', "").replace("'", ""))

from generate import (  # noqa: E402
    LOBS,
    MARKETS,
    PLANS,
    REGIONS,
    STATES,
    generate_claims_lines,
    generate_members,
    generate_providers,
)


def _month_starts(d0: date, d1: date) -> Iterator[date]:
    y, m = d0.year, d0.month
    while (y, m) <= (d1.year, d1.month):
        yield date(y, m, 1)
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1


def _age_band(dob_year: Any, ref_year: int) -> str:
    if dob_year is None or (isinstance(dob_year, float) and pd.isna(dob_year)):
        return "UNKNOWN"
    try:
        age = ref_year - int(dob_year)
    except (TypeError, ValueError):
        return "UNKNOWN"
    if age < 18:
        return "0-17"
    if age < 35:
        return "18-34"
    if age < 50:
        return "35-49"
    if age < 65:
        return "50-64"
    return "65+"


def _cpts_from_service_category_names(names: Sequence[str]) -> List[str]:
    keymap = {
        "URGENT_CARE": ["99281", "99282", "99283"],
        "REHABILITATION": ["97110", "97112", "97140"],
        "ADVANCED_IMAGING": ["70551", "70450", "72148", "75574"],
        "SPECIALTY_CARE": ["99213", "99214", "99215"],
        "SPECIALTY_SERVICES": ["96413", "96415", "J0135"],
    }
    out: List[str] = []
    for s in names:
        u = str(s).replace(" ", "_").upper()
        out.extend(keymap.get(u, []))
    return list(dict.fromkeys(out))


def _service_category_for_code(code: str, preferred: Optional[List[str]] = None) -> str:
    if preferred:
        return str(preferred[0])
    c = str(code).strip().upper()
    if c.startswith("J"):
        return "SPECIALTY_SERVICES"
    if c in {"97110", "97112", "97140", "97165", "97166", "97167", "97168"}:
        return "REHABILITATION"
    if c in {"99281", "99282", "99283"}:
        return "URGENT_CARE"
    if c in {"70551", "70552", "70553", "70450", "70460", "72148", "72149", "72158", "75574", "75572", "75573"}:
        return "ADVANCED_IMAGING"
    return "SPECIALTY_CARE"


def _map_scope_markets_for_demo(markets: Optional[List[str]]) -> Optional[List[str]]:
    if not markets:
        return None
    alias = {"CHICAGO": "DFW", "LA": "BOS", "LAX": "BOS"}
    demo = set(MARKETS)
    out: List[str] = []
    for m in markets:
        mapped = alias.get(str(m).upper(), str(m))
        if mapped in demo:
            out.append(mapped)
    return list(dict.fromkeys(out)) if out else None


def _sample_member_row(mdf: pd.DataFrame, lobs: Any, mkts: Optional[List[str]]) -> Optional[pd.Series]:
    q = mdf
    if lobs:
        lob_list = [lobs] if isinstance(lobs, str) else list(lobs)
        q = q[q["lob"].isin(lob_list)]
    if mkts:
        q = q[q["market"].isin(mkts)]
    if q.empty:
        q = mdf
        if lobs:
            lob_list = [lobs] if isinstance(lobs, str) else list(lobs)
            q = q[q["lob"].isin(lob_list)]
    if q.empty:
        return None
    return q.sample(1).iloc[0]


def _policy_aligned_claims_df(
    tenant_id: UUID,
    members_df: pd.DataFrame,
    providers_df: pd.DataFrame,
    start_d: date,
    end_d: date,
    per_policy_per_month: int,
) -> pd.DataFrame:
    """Extra claim lines so build_policy_claims_filters scopes hit real CPT/category volume."""
    from uepi_api.services.policy_scoped_data_generation import build_policy_claims_filters
    from uepi_api.storage_policies import get_policy, list_policies

    rows: List[Dict[str, Any]] = []
    plist = list_policies(tenant_id) or []
    for p in plist:
        pid = p.get("id")
        if not pid:
            continue
        pol = get_policy(UUID(pid) if isinstance(pid, str) else pid, tenant_id)
        if not pol:
            continue
        pf = build_policy_claims_filters(pol)
        cpts = [str(c).strip() for c in (pf.get("cpt_codes") or []) if c and str(c).strip().upper() != "ALL"]
        svc_names = pf.get("service_categories") or []
        if isinstance(svc_names, str):
            svc_names = [svc_names]
        if not cpts and svc_names:
            cpts = _cpts_from_service_category_names(svc_names)
        if not cpts and "infusion" in (pol.get("name") or "").lower():
            cpts = ["96413", "96415", "96417"]
        if not cpts:
            cpts = ["99213", "99214"]

        lobs_f = pf.get("lob")
        mk_raw = pf.get("markets")
        mkts_f = _map_scope_markets_for_demo(list(mk_raw) if mk_raw else None)

        for month0 in _month_starts(start_d, end_d):
            y, month = month0.year, month0.month
            for _ in range(per_policy_per_month):
                mbr = _sample_member_row(members_df, lobs_f, mkts_f)
                if mbr is None:
                    continue
                market = str(mbr["market"])
                lob = str(mbr["lob"])
                psub = providers_df[providers_df["market"] == market]
                if psub.empty:
                    psub = providers_df
                prov = psub.sample(1).iloc[0]
                code = random.choice(cpts)
                svc_cat = _service_category_for_code(code, list(svc_names) if svc_names else None)
                day_offset = random.randint(0, 27)
                service_from = datetime(y, month, 1) + timedelta(days=day_offset)
                service_to = service_from + timedelta(days=random.randint(0, 5))
                paid_date = service_to + timedelta(days=random.randint(25, 80))
                base_allowed = random.uniform(120, 950)
                paid_amt = base_allowed * random.uniform(0.82, 0.99)
                in_net = random.random() > 0.15
                network_tier = prov["network_tier"] if in_net else "TIER_3"
                pos_code = random.choice(["11", "22", "19", "23"])

                rows.append(
                    {
                        "tenant_id": str(tenant_id),
                        "member_id": mbr["member_id"],
                        "claim_id": f"PA_{uuid4().hex[:8]}",
                        "claim_line_id": f"PA_{uuid4().hex}{uuid4().hex[:8]}",
                        "service_from_date": service_from.strftime("%Y-%m-%d"),
                        "service_to_date": service_to.strftime("%Y-%m-%d"),
                        "paid_date": paid_date.strftime("%Y-%m-%d"),
                        "lob": lob,
                        "market": market,
                        "plan_id": mbr.get("plan_id", random.choice(PLANS)),
                        "product_type": mbr.get("product_type", "PPO"),
                        "state": mbr.get("state", STATES.get(market, "NY")),
                        "region": mbr.get("region", REGIONS.get(market, "NORTHEAST")),
                        "place_of_service": pos_code,
                        "cpt_hcpcs": code,
                        "service_category": svc_cat,
                        "rendering_npi": prov["npi"],
                        "billing_npi": prov["npi"] if random.random() > 0.35 else None,
                        "network_tier": network_tier,
                        "allowed_amount": round(base_allowed, 2),
                        "paid_amount": round(paid_amt, 2),
                        "units": round(random.uniform(0.8, 2.2), 2),
                        "in_network_flag": in_net,
                        "modifier_1": random.choice([None, "26", "59"]) if random.random() > 0.75 else None,
                        "diag_1": f"M54.{random.randint(0, 9)}" if random.random() > 0.4 else None,
                        "diagnosis_group": "MUSCULOSKELETAL",
                    }
                )

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _tier_to_network_status(tier: Any) -> str:
    t = str(tier or "").upper()
    if "TIER_3" in t:
        return "OUT_OF_NETWORK"
    return "IN_NETWORK"


def _claim_row_to_dict(row: pd.Series) -> Dict[str, Any]:
    sfd = row.get("service_from_date")
    if hasattr(sfd, "strftime"):
        service_date = sfd.date() if hasattr(sfd, "date") else sfd
    else:
        service_date = str(sfd)[:10] if sfd else None

    paid_raw = row.get("paid_date")
    if hasattr(paid_raw, "strftime"):
        paid_date = paid_raw.date() if hasattr(paid_raw, "date") else paid_raw
    elif paid_raw:
        paid_date = str(paid_raw)[:10]
    else:
        paid_date = None

    code = str(row.get("cpt_hcpcs") or "").strip()
    diag = row.get("diag_1")
    icd10 = [str(diag)] if diag and str(diag).strip() else None

    npi = str(row.get("rendering_npi") or "").strip()

    return {
        "claim_id": str(row.get("claim_id") or ""),
        "claim_line_id": str(row.get("claim_line_id") or ""),
        "member_id": str(row.get("member_id") or ""),
        "provider_id": npi or "UNKNOWN",
        "service_date": service_date,
        "paid_date": paid_date,
        "adjudication_date": None,
        "lob": str(row.get("lob") or ""),
        "market": str(row.get("market") or ""),
        "cpt_code": code or None,
        "hcpcs_code": code or None,
        "service_category": str(row.get("service_category") or "OTHER"),
        "place_of_service": str(row.get("place_of_service") or ""),
        "units": float(row.get("units") or 0),
        "allowed_amount": float(row.get("allowed_amount") or 0),
        "paid_amount": float(row.get("paid_amount") or 0),
        "member_cost_share": 0.0,
        "in_network": bool(row.get("in_network_flag", True)),
        "requires_prior_auth": False,
        "rendering_provider_id": npi or None,
        "billing_provider_id": str(row.get("billing_npi") or "") or None,
        "icd10_diagnosis_codes": icd10,
        "system_affiliation": row.get("system_affiliation"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Load synthetic historical canonical data into Postgres")
    parser.add_argument(
        "--tenant-id",
        type=str,
        default="00000000-0000-0000-0000-000000000001",
        help="Tenant UUID",
    )
    parser.add_argument("--start", type=str, default="2023-01-01", help="History start (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default="2025-12-31", help="History end (YYYY-MM-DD)")
    parser.add_argument(
        "--members",
        type=int,
        default=1200,
        help="Synthetic member count (unique member_ids; default ≥1000 demo minimum)",
    )
    parser.add_argument(
        "--allow-fewer-members",
        action="store_true",
        help="Allow --members below 1000 (local dev only)",
    )
    parser.add_argument(
        "--providers",
        type=int,
        default=None,
        help="Synthetic provider count (default: max(50, members/8))",
    )
    parser.add_argument(
        "--claims-min-per-month",
        type=int,
        default=120,
        help="Minimum random claims per calendar month (inclusive)",
    )
    parser.add_argument(
        "--claims-max-per-month",
        type=int,
        default=450,
        help="Maximum random claims per calendar month (inclusive)",
    )
    parser.add_argument("--claims-batch-size", type=int, default=2500, help="Rows per bulk_insert_claims_lines call")
    parser.add_argument(
        "--skip-policy-aligned-claims",
        action="store_true",
        help="Do not add DB-driven claims matched to seeded policy CPT/category scope",
    )
    parser.add_argument(
        "--policy-claims-per-month",
        type=int,
        default=12,
        help="Supplemental claim lines per policy per calendar month (policy-aligned)",
    )
    args = parser.parse_args()

    if args.members < 1000 and not args.allow_fewer_members:
        print(
            "ERROR: --members must be at least 1000 (use --allow-fewer-members to override for dev).",
            file=sys.stderr,
        )
        sys.exit(2)

    tenant_id = UUID(args.tenant_id)
    start_d = date.fromisoformat(args.start)
    end_d = date.fromisoformat(args.end)
    start_dt = datetime(start_d.year, start_d.month, start_d.day)
    end_dt = datetime(end_d.year, end_d.month, end_d.day)

    prov_n = args.providers if args.providers is not None else max(50, args.members // 8)
    crange = (args.claims_min_per_month, args.claims_max_per_month)
    if crange[0] > crange[1]:
        print("claims-min-per-month must be <= claims-max-per-month", file=sys.stderr)
        sys.exit(1)

    from uepi_api.database import SessionLocal
    from uepi_api.repositories.canonical_data import CanonicalDataRepository

    print(f"Generating synthetic population: members={args.members}, providers={prov_n}")
    members_df = generate_members(args.members, LOBS, MARKETS)
    providers_df = generate_providers(prov_n, MARKETS)

    scenarios: Dict[str, Any] = {}
    print(f"Generating claims {start_d} .. {end_d} (claims/month in {crange})...")
    claims_df = generate_claims_lines(
        members_df,
        providers_df,
        start_dt,
        end_dt,
        str(tenant_id),
        scenarios,
        claims_per_month_range=crange,
    )
    print(f"  Claims rows: {len(claims_df)}")

    if not args.skip_policy_aligned_claims:
        from uepi_api.storage_policies import list_policies as _list_policies_for_align

        n_pol = len(_list_policies_for_align(tenant_id) or [])
        print(
            f"Adding policy-aligned claims ({args.policy_claims_per_month}/policy/month); "
            f"policies in DB: {n_pol}..."
        )
        extra_df = _policy_aligned_claims_df(
            tenant_id,
            members_df,
            providers_df,
            start_d,
            end_d,
            args.policy_claims_per_month,
        )
        if not extra_df.empty:
            claims_df = pd.concat([claims_df, extra_df], ignore_index=True)
            print(f"  Policy-aligned supplemental claims: {len(extra_df)} (total claims {len(claims_df)})")
        else:
            print("  No policy-aligned rows (no policies in DB or filters could not be applied).")

    ingestion_id = uuid4()
    source_system = "synthetic_historical_loader"
    source_file_id = f"synth_{ingestion_id.hex[:12]}"

    enrollment_rows: List[Dict[str, Any]] = []
    ref_year = end_d.year
    for _, mrow in members_df.iterrows():
        mid = str(mrow.get("member_id") or "")
        g = mrow.get("gender")
        if g is None or (isinstance(g, float) and pd.isna(g)) or str(g).strip() == "":
            gender = "U"
        else:
            gender = str(g)
        rs = mrow.get("risk_score")
        risk = float(rs) if rs is not None and not (isinstance(rs, float) and pd.isna(rs)) else 1.0
        ab = _age_band(mrow.get("dob_year"), ref_year)
        for em in _month_starts(start_d, end_d):
            enrollment_rows.append(
                {
                    "member_id": mid,
                    "enrollment_month": em.isoformat(),
                    "lob": str(mrow.get("lob") or "COMMERCIAL"),
                    "market": str(mrow.get("market") or "NYC"),
                    "age_band": ab,
                    "gender": gender,
                    "risk_score": risk,
                    "network_tier": "TIER_1",
                    "enrolled_flag": True,
                    "enrollment_start_date": start_d.isoformat(),
                    "enrollment_end_date": end_d.isoformat(),
                    "product_type": mrow.get("product_type"),
                    "segment": None,
                }
            )

    provider_rows: List[Dict[str, Any]] = []
    for _, prow in providers_df.iterrows():
        npi = str(prow.get("npi") or "").strip()
        provider_rows.append(
            {
                "provider_id": npi or f"PRV_{uuid4().hex[:10]}",
                "npi": npi or None,
                "provider_type": "PHYSICIAN",
                "specialty": str(prow.get("specialty") or "PRIMARY_CARE"),
                "market": str(prow.get("market") or "NYC"),
                "network_status": _tier_to_network_status(prow.get("network_tier")),
                "effective_date": start_d.isoformat(),
                "termination_date": None,
                "system_affiliation": prow.get("system_affiliation"),
                "provider_name": prow.get("provider_name"),
                "tax_id": prow.get("tax_id"),
            }
        )

    db = SessionLocal()
    try:
        repo = CanonicalDataRepository(db)
        print(f"Bulk insert providers ({len(provider_rows)})...")
        n_prov = repo.bulk_insert_provider_records(
            tenant_id, provider_rows, source_system, source_file_id, ingestion_id
        )
        print(f"  inserted {n_prov}")

        print(f"Bulk insert enrollment ({len(enrollment_rows)})...")
        n_enr = repo.bulk_insert_enrollment_records(
            tenant_id, enrollment_rows, source_system, source_file_id, ingestion_id
        )
        print(f"  inserted {n_enr}")

        batch: List[Dict[str, Any]] = []
        print("Bulk insert claims (batched)...")
        for _, row in claims_df.iterrows():
            batch.append(_claim_row_to_dict(row))
            if len(batch) >= args.claims_batch_size:
                repo.bulk_insert_claims_lines(tenant_id, batch, source_system, source_file_id, ingestion_id)
                batch = []
        if batch:
            repo.bulk_insert_claims_lines(tenant_id, batch, source_system, source_file_id, ingestion_id)
        print("  claims batches finished")
    finally:
        db.close()

    print("")
    print("Done. Run scripts/refresh_baseline_from_canonical.py then scripts/run_demo_day.py --predicted-all --no-observations")


if __name__ == "__main__":
    main()
