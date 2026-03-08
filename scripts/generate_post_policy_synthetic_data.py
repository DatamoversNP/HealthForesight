"""Generate synthetic data from today onwards that reflects policy impacts (Stage 4)"""
import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

# Import from existing generator
from scripts.synth.generate import (
    generate_members,
    generate_providers,
    SERVICE_CATEGORIES,
    MARKETS,
    LOBS,
)

# Seed for reproducibility
RANDOM_SEED = 42

# Service category mapping
SERVICE_CATEGORY_MAP = {
    "MRI": "ADVANCED_IMAGING",
    "ER_IMAGING": "ADVANCED_IMAGING",
    "INFUSION": "SPECIALTY_SERVICES",
    "PT": "REHABILITATION",
    "SPECIALTY_VISIT": "SPECIALTY_CARE",
    "URGENT_CARE": "URGENT_CARE",
}


def generate_post_policy_claims_lines(
    members_df: pd.DataFrame,
    providers_df: pd.DataFrame,
    start_date: datetime,
    end_date: datetime,
    tenant_id: str,
    policy_scenarios: dict[str, Any],
) -> pd.DataFrame:
    """Generate claims lines from start_date onwards with policy impacts applied
    
    This generates data where policies are effective from the start_date (today),
    so all generated data reflects policy impacts.
    
    Args:
        members_df: Member enrollment DataFrame
        providers_df: Provider directory DataFrame
        start_date: Start date (typically today) - policies are effective from this date
        end_date: End date for data generation
        tenant_id: Tenant ID
        policy_scenarios: Dictionary of policy scenarios with effective dates (should be <= start_date)
        
    Returns:
        DataFrame of claims lines
    """
    claims = []
    current_date = start_date
    
    # Create member and provider lookups
    members_by_market_lob = {}
    for _, member in members_df.iterrows():
        key = (member["market"], member["lob"])
        if key not in members_by_market_lob:
            members_by_market_lob[key] = []
        members_by_market_lob[key].append(member)
    
    providers_by_market = {}
    for _, provider in providers_df.iterrows():
        if provider["market"] not in providers_by_market:
            providers_by_market[provider["market"]] = []
        providers_by_market[provider["market"]].append(provider)
    
    # Generate claims month by month
    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        
        # Generate claims for this month
        claims_per_month = random.randint(5000, 20000)
        
        for _ in range(claims_per_month):
            # Select member
            market = random.choice(MARKETS)
            lob = random.choice(LOBS)
            key = (market, lob)
            if key not in members_by_market_lob or not members_by_market_lob[key]:
                continue
            member = random.choice(members_by_market_lob[key])
            
            # Select provider
            if market not in providers_by_market or not providers_by_market[market]:
                continue
            provider = random.choice(providers_by_market[market])
            
            # Select service category
            category = random.choice(list(SERVICE_CATEGORIES.keys()))
            service_info = SERVICE_CATEGORIES[category]
            code = random.choice(service_info["codes"])
            pos_code = random.choice(service_info["pos_codes"])
            
            # Apply policy scenario effects (all dates are >= start_date, so policies are active)
            base_volume = 1.0
            base_allowed = random.uniform(100, 1000)
            
            # Policy 1: Tighten PA for outpatient MRI
            if "policy_1" in policy_scenarios:
                scenario = policy_scenarios["policy_1"]
                # Since current_date >= start_date (today), policy is effective
                if category == "MRI" and pos_code == "11":  # Outpatient MRI
                    base_volume *= 0.7  # 30% reduction due to PA
                elif category == "ER_IMAGING":  # ER imaging increases (substitution)
                    base_volume *= 1.4  # 40% increase
            
            # Policy 2: Site-of-care restriction for infusion
            if "policy_2" in policy_scenarios:
                scenario = policy_scenarios["policy_2"]
                if category == "INFUSION" and pos_code == "22":  # Hospital OP
                    base_volume *= 0.6  # Reduction at hospital OP
                elif category == "INFUSION" and pos_code == "19":  # Freestanding
                    base_volume *= 1.5  # Increase at freestanding
            
            # Policy 3: Coverage relaxation for PT
            if "policy_3" in policy_scenarios:
                scenario = policy_scenarios["policy_3"]
                if category == "PT":
                    base_volume *= 1.3  # Increase due to relaxed coverage
            
            # Policy 4: Step therapy for high-cost biologic
            if "policy_4" in policy_scenarios:
                scenario = policy_scenarios["policy_4"]
                if category == "INFUSION" and code in ["96413", "96415"]:
                    base_volume *= 0.8  # Reduction due to step therapy
                elif category == "SPECIALTY_VISIT":
                    base_volume *= 1.2  # Increase in specialty visits
            
            # Policy 5: Urgent care copay increase
            if "policy_5" in policy_scenarios:
                scenario = policy_scenarios["policy_5"]
                if category == "URGENT_CARE":
                    base_volume *= 0.7  # Reduction due to higher copay
                elif category == "ER_IMAGING":
                    base_volume *= 1.3  # ER increase
            
            # Generate claim
            service_from = current_date + timedelta(days=random.randint(1, 28))
            service_to = service_from + timedelta(days=random.randint(0, 7))
            paid_date = service_to + timedelta(days=random.randint(30, 90))
            
            allowed_amount = base_allowed * base_volume
            paid_amount = allowed_amount * random.uniform(0.8, 1.0)
            units = base_volume * random.uniform(0.5, 2.0)
            
            # Map service category from category name
            service_category = SERVICE_CATEGORY_MAP.get(category, "OTHER")
            
            claims.append({
                "tenant_id": tenant_id,
                "member_id": member["member_id"],
                "claim_id": f"CLM_{uuid4().hex[:8]}",
                "claim_line_id": f"CLM_{uuid4().hex[:12]}",
                "service_date_from": service_from.strftime("%Y-%m-%d"),  # Changed from service_from_date
                "service_from_date": service_from.strftime("%Y-%m-%d"),  # Keep for backward compatibility
                "service_to_date": service_to.strftime("%Y-%m-%d"),
                "paid_date": paid_date.strftime("%Y-%m-%d"),
                "lob": lob,
                "market": market,
                "place_of_service": pos_code,
                "cpt_hcpcs": code,
                "service_category": service_category,  # Added required field
                "rendering_npi": provider["npi"],
                "billing_npi": provider["npi"] if random.random() > 0.3 else None,
                "allowed_amount": round(allowed_amount, 2),
                "paid_amount": round(paid_amount, 2),
                "units": round(units, 2),
                "in_network_flag": random.random() > 0.2,
                "modifier_1": random.choice([None, "26", "TC", "59"]) if random.random() > 0.7 else None,
                "diag_1": f"M{random.randint(10, 99)}.{random.randint(0, 9)}" if random.random() > 0.5 else None,
            })
        
        # Move to next month
        if month == 12:
            current_date = datetime(year + 1, 1, 1)
        else:
            current_date = datetime(year, month + 1, 1)
    
    return pd.DataFrame(claims)


def main():
    parser = argparse.ArgumentParser(
        description="Generate post-policy synthetic data from today onwards (Stage 4)"
    )
    parser.add_argument("--out", type=str, default="data/post_policy", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--members", type=int, default=50000, help="Number of members")
    parser.add_argument("--providers", type=int, default=5000, help="Number of providers")
    parser.add_argument("--months", type=int, default=6, help="Number of months of data to generate")
    parser.add_argument("--start-date", type=str, default=None, help="Start date (YYYY-MM-DD). Defaults to today.")
    parser.add_argument("--tenant-id", type=str, default="00000000-0000-0000-0000-000000000001", help="Tenant ID")
    
    args = parser.parse_args()
    
    # Set seed
    random.seed(args.seed)
    
    # Determine start date (default to today)
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    else:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate end date
    end_date = start_date + timedelta(days=args.months * 30)
    
    # Create output directory
    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating post-policy synthetic data from {start_date.date()} to {end_date.date()}")
    print(f"Policies are effective from {start_date.date()} (all data reflects policy impacts)")
    
    # Generate members and providers (or reuse existing)
    print("Generating members...")
    members_df = generate_members(args.members, LOBS, MARKETS)
    members_df.to_csv(out_path / "enrollment.csv", index=False)
    
    print("Generating providers...")
    providers_df = generate_providers(args.providers, MARKETS)
    providers_df.to_csv(out_path / "providers.csv", index=False)
    
    # Define policy scenarios (policies are effective from start_date)
    policy_scenarios = {
        "policy_1": {"effective_date": start_date},  # PA for MRI
        "policy_2": {"effective_date": start_date},  # Site-of-care for Infusion
        "policy_3": {"effective_date": start_date},  # Coverage relaxation for PT
        "policy_4": {"effective_date": start_date},  # Step therapy for Biologic
        "policy_5": {"effective_date": start_date},  # Urgent care copay increase
    }
    
    print("Generating claims with policy impacts...")
    claims_df = generate_post_policy_claims_lines(
        members_df, providers_df, start_date, end_date, args.tenant_id, policy_scenarios
    )
    
    # Write claims by month
    print("Writing claims by month...")
    for year in claims_df["service_from_date"].str[:4].unique():
        for month in range(1, 13):
            month_str = f"{year}{month:02d}"
            month_claims = claims_df[
                (claims_df["service_from_date"].str.startswith(f"{year}-{month:02d}"))
            ]
            if not month_claims.empty:
                month_claims.to_csv(
                    out_path / f"claims_lines_{month_str}.csv",
                    index=False,
                )
    
    # Create manifest file for ingestion
    manifest = {
        "tenant_id": args.tenant_id,
        "generated_date": datetime.now().isoformat(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "policy_effective_date": start_date.isoformat(),
        "files": [
            {
                "uri": str(out_path / f"claims_lines_{year}{month:02d}.csv"),
                "type": "claims_lines",
                "format": "csv",
            }
            for year in claims_df["service_from_date"].str[:4].unique()
            for month in range(1, 13)
            if not claims_df[(claims_df["service_from_date"].str.startswith(f"{year}-{month:02d}"))].empty
        ],
    }
    
    with open(out_path / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n✅ Post-policy data generation complete!")
    print(f"   Output directory: {out_path}")
    print(f"   Generated {len(claims_df)} claims lines")
    print(f"   Generated {len(members_df)} members")
    print(f"   Generated {len(providers_df)} providers")
    print(f"   Policy effective date: {start_date.date()}")
    print(f"   Manifest file: {out_path / 'manifest.json'}")
    print(f"\n📋 Next steps:")
    print(f"   1. Review the generated data in {out_path}")
    print(f"   2. Ingest the data using the manifest: {out_path / 'manifest.json'}")
    print(f"   3. Run Stage 4 impact analysis to compare:")
    print(f"      - Historical data (pre-policy) = baseline")
    print(f"      - New synthetic data (post-policy) = observed impact")


if __name__ == "__main__":
    main()
