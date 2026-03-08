#!/usr/bin/env python3
"""
Phase 2: Generate 24 months historical source data (July 2023 – June 2025) for 1000 members.

Writes pipeline-ready CSVs to --output-dir: claims_lines.csv, enrollment.csv, providers.csv.
Uses the same schema as CanonicalDataRepository / load_data_direct_to_db.

When policies exist for the tenant, collects LOB/market/CPT/service_categories from all policies
and generates claims that match those filters so baseline computation finds data.

Run from repo root:
  python3 scripts/generate_24mo_historical_demo_data.py --output-dir data/source_data/00000000-0000-0000-0000-000000000001/historical
"""
import argparse
import sys
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal
import random
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

# Reuse config and generators from comprehensive script
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "scripts"))
try:
    from generate_comprehensive_realistic_data import (
        SERVICE_CATEGORIES,
        MARKETS,
        LOBS,
        STATES,
        NETWORK_TIERS,
        AGE_BANDS,
        GENDERS,
        PROVIDER_SPECIALTIES,
        generate_providers,
        generate_claims_lines,
    )
except ImportError:
    MARKETS = ["CA", "TX", "NY", "FL", "IL"]
    LOBS = ["COMMERCIAL", "MA", "MEDICAID"]
    STATES = {"CA": "California", "TX": "Texas", "NY": "New York", "FL": "Florida", "IL": "Illinois"}
    NETWORK_TIERS = ["TIER_1", "TIER_2", "TIER_3", "OUT_OF_NETWORK"]
    AGE_BANDS = ["0-18", "19-34", "35-49", "50-64", "65+"]
    GENDERS = ["M", "F", "O", "U"]
    PROVIDER_SPECIALTIES = ["PRIMARY_CARE", "CARDIOLOGY", "ORTHOPEDICS", "RADIOLOGY", "ONCOLOGY"]
    SERVICE_CATEGORIES = {}
    def generate_providers(*a, **k):
        return pd.DataFrame()
    def generate_claims_lines(*a, **k):
        return pd.DataFrame()


def collect_policy_filter_union(tenant_id):
    """Load all policies for tenant and return union of LOB, markets, procedure_codes, service_categories.
    So generated claims match policy filters and baseline finds data."""
    try:
        from uepi_api.storage_policies import list_policies
        from uepi_api.services.policy_scoped_data_generation import build_policy_claims_filters
    except ImportError:
        return None, None, None, None
    policies = list_policies(tenant_id)
    if not policies:
        return None, None, None, None
    all_lob = set()
    all_markets = set()
    all_codes = set()
    all_service_cats = set()
    for p in policies:
        try:
            pf = build_policy_claims_filters(p)
            lob = pf.get("lob")
            if lob:
                if isinstance(lob, list):
                    all_lob.update(lob)
                else:
                    all_lob.add(lob)
            market = pf.get("markets") or pf.get("market")
            if market:
                if isinstance(market, list):
                    for m in market:
                        if m and str(m).upper() != "ALL":
                            all_markets.add(m)
                    if not all_markets and market:
                        all_markets.update(["NYC", "CHICAGO", "LA", "DFW"])
                elif market and str(market).upper() != "ALL":
                    all_markets.add(market)
            codes = pf.get("procedure_codes") or pf.get("cpt_codes") or []
            if codes:
                all_codes.update(c if isinstance(c, str) else str(c) for c in codes)
            cats = pf.get("service_categories") or ([pf["service_category"]] if pf.get("service_category") else [])
            if cats:
                all_service_cats.update(c for c in cats if c)
        except Exception:
            continue
    # Policies often use city-style markets (NYC, CHICAGO, LA, DFW); ensure we have them if any policy uses ALL
    if not all_markets and policies:
        all_markets = {"NYC", "CHICAGO", "LA", "DFW"}
    if not all_lob:
        all_lob = {"COMMERCIAL", "MA", "MEDICAID"}
    if not all_markets:
        all_markets = {"NYC", "CHICAGO", "LA", "DFW"}
    return (
        list(all_lob) if all_lob else None,
        list(all_markets) if all_markets else None,
        list(all_codes) if all_codes else None,
        list(all_service_cats) if all_service_cats else None,
    )


def generate_members_for_range(
    count: int,
    start_date: date,
    end_date: date,
    lobs: list,
    markets: list,
) -> pd.DataFrame:
    """Generate member-month enrollment from start_date to end_date (one row per member per month)."""
    members = []
    enrollment_start = start_date
    months_count = max(1, (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1)

    for i in range(count):
        market = random.choice(markets)
        lob = random.choice(lobs)
        age_band = random.choices(AGE_BANDS, weights=[15, 25, 25, 20, 15])[0]
        gender = random.choice(GENDERS)
        base_risk = {"0-18": 0.5, "19-34": 0.7, "35-49": 1.0, "50-64": 1.5, "65+": 2.0}.get(age_band, 1.0)
        risk_score = round(base_risk * random.uniform(0.8, 1.5), 4)

        for month_offset in range(months_count):
            y = start_date.year + (start_date.month - 1 + month_offset) // 12
            m = (start_date.month - 1 + month_offset) % 12 + 1
            enrollment_month = date(y, m, 1)
            if enrollment_month > end_date:
                break
            if month_offset > 12 and random.random() < 0.1:
                enrolled_flag = False
                enrollment_end_date = enrollment_month
            else:
                enrolled_flag = True
                enrollment_end_date = None
            members.append({
                "member_id": f"MEM_{i:06d}",
                "enrollment_month": enrollment_month,
                "lob": lob,
                "market": market,
                "age_band": age_band,
                "gender": gender,
                "risk_score": risk_score,
                "network_tier": random.choices(NETWORK_TIERS, weights=[50, 30, 15, 5])[0],
                "enrolled_flag": enrolled_flag,
                "enrollment_start_date": enrollment_start,
                "enrollment_end_date": enrollment_end_date,
                "product_type": random.choice(["HMO", "PPO", "EPO"]) if lob == "COMMERCIAL" else "HMO",
                "segment": random.choice(["Individual", "Small Group", "Large Group"]) if lob == "COMMERCIAL" else None,
            })
    return pd.DataFrame(members)


def main():
    parser = argparse.ArgumentParser(description="Generate 24 months historical demo data (July 2023 - June 2025), 1000 members")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for CSVs (default: data/source_data/<tenant>/historical)")
    parser.add_argument("--tenant-id", type=str, default="00000000-0000-0000-0000-000000000001")
    parser.add_argument("--start", type=str, default="2022-01-01", help="Start date YYYY-MM-DD (default 36mo historical)")
    parser.add_argument("--end", type=str, default="2025-06-30", help="End date YYYY-MM-DD")
    parser.add_argument("--members", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    output_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / "data" / "source_data" / args.tenant_id / "historical"
    output_dir.mkdir(parents=True, exist_ok=True)

    from uuid import UUID
    tenant_id = UUID(args.tenant_id)

    print("=" * 60)
    print("PHASE 2: Generate historical demo data (default 2022-01 to 2025-06)")
    print("=" * 60)
    print(f"Start: {start_date}, End: {end_date}, Members: {args.members}")
    print(f"Output: {output_dir}")
    print()

    # Align data with policy filters so Phase 4 baseline finds claims for every policy
    policy_lobs, policy_markets, policy_cpt_codes, policy_service_cats = collect_policy_filter_union(tenant_id)
    use_lobs = policy_lobs or LOBS
    use_markets = policy_markets or MARKETS
    if policy_lobs or policy_markets or policy_cpt_codes:
        print("   Policy-aligned generation: LOBs =", use_lobs[:8], "Markets =", use_markets[:8],
              "CPT codes =", len(policy_cpt_codes or []), "service_categories =", len(policy_service_cats or []))
    if not SERVICE_CATEGORIES:
        print("WARNING: SERVICE_CATEGORIES empty; claims may be empty. Ensure generate_comprehensive_realistic_data is importable.")
    print("1. Generating members (enrollment)...")
    members_df = generate_members_for_range(args.members, start_date, end_date, use_lobs, use_markets)
    print(f"   Generated {len(members_df):,} member-month records ({members_df['member_id'].nunique():,} unique members)")

    print("2. Generating providers...")
    providers_df = generate_providers(count=min(500, args.members * 2), markets=use_markets)
    print(f"   Generated {len(providers_df):,} providers")

    print("3. Generating claims lines (policy-aligned CPT/LOB/market)...")
    claims_df = generate_claims_lines(
        members_df=members_df,
        providers_df=providers_df,
        start_date=start_date,
        end_date=end_date,
        tenant_id=tenant_id,
        policy_cpt_codes=policy_cpt_codes,
        policy_service_categories=policy_service_cats,
    )
    print(f"   Generated {len(claims_df):,} claims lines")

    print("4. Writing CSVs...")
    claims_file = output_dir / "claims_lines.csv"
    claims_df.to_csv(claims_file, index=False, date_format="%Y-%m-%d")
    print(f"   {claims_file} ({claims_file.stat().st_size / (1024*1024):.1f} MB)")

    enrollment_df = members_df.drop_duplicates(subset=["member_id", "enrollment_month"])
    enrollment_file = output_dir / "enrollment.csv"
    enrollment_df.to_csv(enrollment_file, index=False, date_format="%Y-%m-%d")
    print(f"   {enrollment_file} ({enrollment_file.stat().st_size / (1024*1024):.1f} MB)")

    provider_file = output_dir / "providers.csv"
    providers_df.to_csv(provider_file, index=False, date_format="%Y-%m-%d")
    print(f"   {provider_file} ({provider_file.stat().st_size / (1024*1024):.1f} MB)")

    print()
    print("=" * 60)
    print("Phase 2 complete. Next: run Phase 3 (load historical into DB).")
    print("=" * 60)


if __name__ == "__main__":
    main()
