#!/usr/bin/env python3
"""
Generate comprehensive, realistic synthetic healthcare data with large coverage
to support all product use cases including:
- Multiple service categories (imaging, specialty, rehab, etc.)
- Various policy scenarios (prior auth, site-of-care, step therapy, etc.)
- Multiple markets, LOBs, and time periods
- Provider networks and tiers
- Member demographics and risk scores
- Realistic utilization patterns
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
import random
import pandas as pd
import numpy as np

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.storage_auth import DEFAULT_TENANT_ID

# Configuration
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Markets and LOBs - expanded for comprehensive coverage
MARKETS = ["CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]
LOBS = ["COMMERCIAL", "MA", "MEDICAID"]
STATES = {
    "CA": "California", "TX": "Texas", "NY": "New York", "FL": "Florida",
    "IL": "Illinois", "PA": "Pennsylvania", "OH": "Ohio", "GA": "Georgia",
    "NC": "North Carolina", "MI": "Michigan"
}

# Service categories with realistic codes
SERVICE_CATEGORIES = {
    "PRIMARY_CARE": {
        "cpt_codes": ["99213", "99214", "99215"],
        "pos": "11",
        "avg_cost": 150.0,
        "utilization_rate": 0.8,  # 80% of members
    },
    "SPECIALTY_CARE": {
        "cpt_codes": ["99243", "99244", "99245", "99254", "99255"],
        "pos": "11",
        "avg_cost": 300.0,
        "utilization_rate": 0.4,
    },
    "IMAGING": {
        "cpt_codes": ["72141", "72142", "72146", "70450", "70460", "73721", "73722"],
        "pos": ["11", "22", "49"],
        "avg_cost": 800.0,
        "utilization_rate": 0.25,
    },
    "EMERGENCY": {
        "cpt_codes": ["99281", "99282", "99283", "99284", "99285"],
        "pos": "23",
        "avg_cost": 1200.0,
        "utilization_rate": 0.15,
    },
    "URGENT_CARE": {
        "cpt_codes": ["99281", "99282", "99283"],
        "pos": "20",
        "avg_cost": 200.0,
        "utilization_rate": 0.2,
    },
    "PHARMACY": {
        "hcpcs_codes": ["J9264", "J1745", "J0897"],
        "pos": "01",
        "avg_cost": 150.0,
        "utilization_rate": 0.9,
    },
    "REHAB": {
        "cpt_codes": ["97110", "97112", "97140", "97161", "97162"],
        "pos": ["11", "12"],
        "avg_cost": 100.0,
        "utilization_rate": 0.1,
    },
    "INPATIENT": {
        "drg_codes": ["470", "871", "872", "291", "292"],
        "pos": "21",
        "avg_cost": 15000.0,
        "utilization_rate": 0.05,
    },
    "LAB": {
        "cpt_codes": ["80053", "85027", "81001", "81025"],
        "pos": "11",
        "avg_cost": 50.0,
        "utilization_rate": 0.7,
    },
    "PROCEDURE": {
        "cpt_codes": ["45378", "43239", "29881", "29882"],
        "pos": ["11", "22", "24"],
        "avg_cost": 2000.0,
        "utilization_rate": 0.1,
    },
}

# Provider specialties
PROVIDER_SPECIALTIES = [
    "PRIMARY_CARE", "CARDIOLOGY", "ORTHOPEDICS", "RADIOLOGY", "ONCOLOGY",
    "NEUROLOGY", "SURGERY", "EMERGENCY_MEDICINE", "URGENT_CARE",
    "MENTAL_HEALTH", "PHYSICAL_THERAPY", "OCCUPATIONAL_THERAPY"
]

NETWORK_TIERS = ["TIER_1", "TIER_2", "TIER_3", "OUT_OF_NETWORK"]
AGE_BANDS = ["0-18", "19-34", "35-49", "50-64", "65+"]
GENDERS = ["M", "F", "O", "U"]


def generate_members(count: int, lobs: list, markets: list) -> pd.DataFrame:
    """Generate comprehensive member enrollment data"""
    members = []
    enrollment_start = date(2023, 1, 1)
    
    for i in range(count):
        market = random.choice(markets)
        lob = random.choice(lobs)
        age_band = random.choices(AGE_BANDS, weights=[15, 25, 25, 20, 15])[0]
        gender = random.choice(GENDERS)
        
        # Risk score based on age and random factor
        base_risk = {
            "0-18": 0.5, "19-34": 0.7, "35-49": 1.0,
            "50-64": 1.5, "65+": 2.0
        }.get(age_band, 1.0)
        risk_score = round(base_risk * random.uniform(0.8, 1.5), 4)
        
        # Generate enrollment months (24 months of data)
        for month_offset in range(24):
            enrollment_month = date(2023, 1, 1) + timedelta(days=month_offset * 30)
            
            # Some members disenroll
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


def generate_providers(count: int, markets: list) -> pd.DataFrame:
    """Generate comprehensive provider directory"""
    providers = []
    
    for i in range(count):
        market = random.choice(markets)
        specialty = random.choice(PROVIDER_SPECIALTIES)
        provider_type = "PHYSICIAN" if specialty not in ["PHYSICAL_THERAPY", "OCCUPATIONAL_THERAPY"] else "FACILITY"
        
        # Effective date (some providers join/leave network)
        effective_date = date(2023, 1, 1) + timedelta(days=random.randint(0, 365))
        termination_date = None
        if random.random() < 0.1:  # 10% terminate
            termination_date = effective_date + timedelta(days=random.randint(180, 365))
        
        providers.append({
            "provider_id": f"PRV_{i:06d}",
            "npi": f"{random.randint(1000000000, 9999999999)}",
            "provider_type": provider_type,
            "specialty": specialty,
            "facility_type": random.choice(["HOSPITAL", "FREESTANDING_ASC", "OFFICE", "FREESTANDING_IMAGING"]) if provider_type == "FACILITY" else None,
            "market": market,
            "state": STATES.get(market, "CA"),
            "zip_code": f"{random.randint(10000, 99999)}",
            "network_status": random.choices(["IN_NETWORK", "OUT_OF_NETWORK"], weights=[85, 15])[0],
            "effective_date": effective_date,
            "termination_date": termination_date,
            "system_affiliation": f"System {random.randint(1, 10)}" if random.random() < 0.4 else None,
            "system_id": f"SYS_{random.randint(1, 10)}" if random.random() < 0.4 else None,
            "provider_name": f"{specialty} Provider {i}",
            "tax_id": f"{random.randint(100000000, 999999999)}" if random.random() < 0.7 else None,
        })
    
    return pd.DataFrame(providers)


def generate_claims_lines(
    members_df: pd.DataFrame,
    providers_df: pd.DataFrame,
    start_date: date,
    end_date: date,
    tenant_id: UUID,
    policy_cpt_codes: Optional[list] = None,
    policy_service_categories: Optional[list] = None,
) -> pd.DataFrame:
    """Generate comprehensive claims lines. When policy_cpt_codes (and optionally policy_service_categories)
    are provided, the majority of claims use those codes/categories so baselines find matching data."""
    claims = []
    use_policy_codes = policy_cpt_codes and len(policy_cpt_codes) > 0
    use_policy_cats = policy_service_categories and len(policy_service_categories) > 0

    # Create lookups
    members_dict = {}
    for _, member in members_df.iterrows():
        key = (member["member_id"], member["enrollment_month"])
        if key not in members_dict:
            members_dict[key] = []
        members_dict[key].append(member)

    providers_by_market = {}
    for _, provider in providers_df.iterrows():
        if provider["market"] not in providers_by_market:
            providers_by_market[provider["market"]] = []
        providers_by_market[provider["market"]].append(provider)

    # Generate claims month by month
    current_date = start_date
    claim_counter = 0

    while current_date <= end_date:
        month_start = date(current_date.year, current_date.month, 1)
        active_members = members_df[
            (members_df["enrollment_month"] <= month_start) &
            ((members_df["enrollment_end_date"].isna()) | (members_df["enrollment_end_date"] >= month_start)) &
            (members_df["enrolled_flag"] == True)
        ]

        if len(active_members) == 0:
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
            continue

        # ~3x coverage for realistic demo: 1.5–3.0 claims per member per month, cap 150k/month
        claims_per_member_per_month = random.uniform(1.5, 3.0)
        num_claims = int(len(active_members) * claims_per_member_per_month)
        num_claims = min(num_claims, 150000)

        for _ in range(num_claims):
            member = active_members.sample(1).iloc[0]
            market = member["market"]

            if market not in providers_by_market or len(providers_by_market[market]) == 0:
                continue

            provider = random.choice(providers_by_market[market])

            # Prefer policy-aligned codes/categories so baselines find data (e.g. 90% of claims)
            if use_policy_codes and random.random() < 0.9:
                code = random.choice(policy_cpt_codes)
                code_str = str(code).strip()
                # CPT: typically 5 digits; HCPCS: often starts with letter (e.g. J0135)
                if code_str.isdigit() or (len(code_str) >= 5 and code_str[:1].isdigit()):
                    cpt_code = code_str
                    hcpcs_code = None
                else:
                    cpt_code = None
                    hcpcs_code = code_str
                category = random.choice(policy_service_categories) if use_policy_cats else "IMAGING"
                pos = "11"
                base_cost = 400.0
                drg_code = None
            else:
                category = random.choices(
                    list(SERVICE_CATEGORIES.keys()),
                    weights=[cat["utilization_rate"] for cat in SERVICE_CATEGORIES.values()]
                )[0]
                service_config = SERVICE_CATEGORIES[category]
                if "cpt_codes" in service_config:
                    code = random.choice(service_config["cpt_codes"])
                    cpt_code = code
                    hcpcs_code = None
                elif "hcpcs_codes" in service_config:
                    code = random.choice(service_config["hcpcs_codes"])
                    cpt_code = None
                    hcpcs_code = code
                else:
                    cpt_code = None
                    hcpcs_code = None
                pos = service_config["pos"]
                if isinstance(pos, list):
                    pos = random.choice(pos)
                base_cost = service_config["avg_cost"]
                drg_code = random.choice(service_config.get("drg_codes", [None])) if "drg_codes" in service_config else None

            service_date = date(
                current_date.year,
                current_date.month,
                random.randint(1, 28)
            )
            cost_multiplier = random.uniform(0.7, 1.5)
            allowed_amount = Decimal(str(round(base_cost * cost_multiplier, 2)))
            paid_amount = allowed_amount * Decimal("0.85")
            member_cost_share = allowed_amount - paid_amount

            in_network = provider["network_status"] == "IN_NETWORK"
            if not in_network:
                allowed_amount = allowed_amount * Decimal("1.5")
                paid_amount = allowed_amount * Decimal("0.5")
                member_cost_share = allowed_amount - paid_amount

            requires_prior_auth = category in ["IMAGING", "INPATIENT", "PROCEDURE"]
            prior_auth_approved = True if requires_prior_auth and random.random() > 0.1 else None
            prior_auth_id = f"PA_{claim_counter}" if requires_prior_auth else None

            claim_id = f"CLM_{current_date.strftime('%Y%m%d')}_{claim_counter:06d}"
            claim_line_id = f"{claim_id}_001"

            claim = {
                "claim_id": claim_id,
                "claim_line_id": claim_line_id,
                "member_id": member["member_id"],
                "provider_id": provider["provider_id"],
                "service_date": service_date,
                "paid_date": service_date + timedelta(days=random.randint(15, 45)),
                "adjudication_date": service_date + timedelta(days=random.randint(10, 30)),
                "lob": member["lob"],
                "market": market,
                "cpt_code": cpt_code,
                "hcpcs_code": hcpcs_code,
                "drg_code": drg_code,
                "icd10_diagnosis_codes": [f"E{random.randint(11, 11)}.{random.randint(0, 9)}"] if random.random() < 0.8 else None,
                "icd10_procedure_codes": None,
                "service_category": category,
                "place_of_service": pos,
                "units": Decimal(str(round(random.uniform(1.0, 3.0), 2))),
                "allowed_amount": allowed_amount,
                "paid_amount": paid_amount,
                "member_cost_share": member_cost_share,
                "in_network": in_network,
                "requires_prior_auth": requires_prior_auth,
                "prior_auth_approved": prior_auth_approved,
                "prior_auth_id": prior_auth_id,
                "facility_type": provider.get("facility_type"),
                "system_affiliation": provider.get("system_affiliation"),
                "rendering_provider_id": provider["provider_id"],
                "billing_provider_id": provider["provider_id"],
                "referring_provider_id": f"PRV_{random.randint(0, 1000):06d}" if random.random() < 0.3 else None,
            }

            claims.append(claim)
            claim_counter += 1

        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, 1)
        else:
            current_date = date(current_date.year, current_date.month + 1, 1)

    return pd.DataFrame(claims)


def main():
    """Generate comprehensive synthetic data"""
    print("="*60)
    print("Generating Comprehensive Realistic Synthetic Data")
    print("="*60)
    
    tenant_id = DEFAULT_TENANT_ID
    start_date = date(2023, 1, 1)
    end_date = date(2024, 12, 31)  # 24 months of data
    
    # Generate data (reduced size for faster generation - can be increased later)
    print("\n1. Generating Members...")
    # Reduced from 50000 to 10000 for faster generation
    members_df = generate_members(count=10000, lobs=LOBS, markets=MARKETS)
    print(f"   ✅ Generated {len(members_df):,} member-month records")
    
    print("\n2. Generating Providers...")
    # Reduced from 5000 to 1000 for faster generation
    providers_df = generate_providers(count=1000, markets=MARKETS)
    print(f"   ✅ Generated {len(providers_df):,} provider records")
    
    print("\n3. Generating Claims Lines...")
    claims_df = generate_claims_lines(
        members_df=members_df,
        providers_df=providers_df,
        start_date=start_date,
        end_date=end_date,
        tenant_id=tenant_id,
    )
    print(f"   ✅ Generated {len(claims_df):,} claims lines")
    
    # Save to CSV files (for pipeline ingestion)
    output_dir = Path("apps/api/data/source_data") / str(tenant_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n4. Saving to source data directory...")
    
    # Save claims
    claims_file = output_dir / "claims_lines.csv"
    claims_df.to_csv(claims_file, index=False)
    print(f"   ✅ Saved claims to: {claims_file}")
    print(f"      Size: {claims_file.stat().st_size / (1024*1024):.1f} MB")
    
    # Save enrollment (deduplicate by member_id + enrollment_month)
    enrollment_df = members_df.drop_duplicates(subset=["member_id", "enrollment_month"])
    enrollment_file = output_dir / "enrollment.csv"
    enrollment_df.to_csv(enrollment_file, index=False)
    print(f"   ✅ Saved enrollment to: {enrollment_file}")
    print(f"      Size: {enrollment_file.stat().st_size / (1024*1024):.1f} MB")
    
    # Save providers (deduplicate by provider_id + effective_date)
    provider_file = output_dir / "providers.csv"
    providers_df.to_csv(provider_file, index=False)
    print(f"   ✅ Saved providers to: {provider_file}")
    print(f"      Size: {provider_file.stat().st_size / (1024*1024):.1f} MB")
    
    # Summary
    print("\n" + "="*60)
    print("DATA GENERATION SUMMARY")
    print("="*60)
    print(f"Members: {members_df['member_id'].nunique():,} unique")
    print(f"Member-Month Records: {len(members_df):,}")
    print(f"Providers: {len(providers_df):,}")
    print(f"Claims Lines: {len(claims_df):,}")
    print(f"Date Range: {start_date} to {end_date}")
    print(f"Markets: {', '.join(MARKETS)}")
    print(f"LOBs: {', '.join(LOBS)}")
    print(f"Service Categories: {len(SERVICE_CATEGORIES)}")
    print(f"\nOutput Directory: {output_dir}")
    print("="*60)
    print("\n✅ Synthetic data generation complete!")
    print("   Next: Run pipelines to load data into database")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

