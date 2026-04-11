"""Synthetic data generator with behavioral scenarios"""
import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Tuple
from uuid import uuid4

import pandas as pd
import polars as pl


# Seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)


# Markets and LOBs
MARKETS = ["NYC", "DFW", "BOS"]
LOBS = ["COMMERCIAL", "MA", "MEDICAID"]

# Additional data for comprehensive scope
STATES = {"NYC": "NY", "DFW": "TX", "BOS": "MA"}
REGIONS = {"NYC": "NORTHEAST", "DFW": "SOUTH", "BOS": "NORTHEAST"}
PLANS = ["PLAN_A", "PLAN_B", "PLAN_C", "PLAN_D", "PLAN_E"]
PRODUCT_TYPES = ["HMO", "PPO", "EPO", "POS", "HDHP"]
NETWORK_TIERS = ["TIER_1", "TIER_2", "TIER_3"]

# Service category mapping
SERVICE_CATEGORY_MAP = {
    "MRI": "ADVANCED_IMAGING",
    "ER_IMAGING": "ADVANCED_IMAGING",
    "INFUSION": "SPECIALTY_SERVICES",
    "PT": "REHABILITATION",
    "SPECIALTY_VISIT": "SPECIALTY_CARE",
    "URGENT_CARE": "URGENT_CARE",
}

# Service categories and codes
SERVICE_CATEGORIES = {
    "MRI": {
        "codes": ["72141", "72142", "72146", "72148", "72149", "72158"],  # align with seeded PA MRI policies
        "pos_codes": ["11", "22"],  # Office, Outpatient Hospital
    },
    "ER_IMAGING": {
        "codes": ["70450", "70460", "72141", "70551", "70552", "70553"],  # CT / MRI overlap with seeded imaging policies
        "pos_codes": ["23"],  # Emergency Room
    },
    "INFUSION": {
        "codes": ["96413", "96415", "96417"],  # Chemotherapy infusion
        "pos_codes": ["22", "19"],  # Outpatient Hospital, Off Campus
    },
    "PT": {
        "codes": ["97110", "97112", "97140"],  # Physical therapy
        "pos_codes": ["11", "12"],  # Office, Home
    },
    "SPECIALTY_VISIT": {
        "codes": ["99213", "99214", "99215"],  # Office visits
        "pos_codes": ["11"],
    },
    "URGENT_CARE": {
        "codes": ["99281", "99282", "99283"],  # ER visits
        "pos_codes": ["20"],  # Urgent Care
    },
}


def generate_members(count: int, lobs: list[str], markets: list[str]) -> pd.DataFrame:
    """Generate member enrollment data with comprehensive scope fields"""
    members = []
    for i in range(count):
        market = random.choice(markets)
        lob = random.choice(lobs)
        members.append({
            "member_id": f"MEM_{i:06d}",
            "lob": lob,
            "market": market,
            "plan_id": random.choice(PLANS),
            "product_type": random.choice(["HMO", "PPO"]) if lob == "COMMERCIAL" else "HMO",
            "state": STATES.get(market, "NY"),
            "region": REGIONS.get(market, "NORTHEAST"),
            "gender": random.choice(["M", "F", None]),
            "dob_year": random.randint(1950, 2000) if random.random() > 0.1 else None,
            "risk_score": round(random.uniform(0.5, 2.5), 2) if random.random() > 0.2 else None,
            "enrolled_flag": True,
        })
    return pd.DataFrame(members)


def generate_providers(count: int, markets: list[str]) -> pd.DataFrame:
    """Generate provider directory with comprehensive scope fields"""
    specialties = ["RADIOLOGY", "ONCOLOGY", "PHYSICAL_THERAPY", "PRIMARY_CARE", "EMERGENCY"]
    providers = []
    for i in range(count):
        providers.append({
            "npi": f"{random.randint(1000000000, 9999999999)}",
            "provider_name": f"Provider {i}",
            "specialty": random.choice(specialties),
            "market": random.choice(markets),
            "network_tier": random.choices(NETWORK_TIERS, weights=[50, 40, 10])[0],  # 50% TIER_1, 40% TIER_2, 10% TIER_3
            "facility_flag": random.random() > 0.6,
            "tax_id": f"TAX_{random.randint(100000, 999999)}" if random.random() > 0.3 else None,
            "system_affiliation": f"System {random.randint(1, 5)}" if random.random() > 0.5 else None,
        })
    return pd.DataFrame(providers)


def generate_claims_lines(
    members_df: pd.DataFrame,
    providers_df: pd.DataFrame,
    start_date: datetime,
    end_date: datetime,
    tenant_id: str,
    scenarios: dict[str, Any],
    claims_per_month_range: Optional[Tuple[int, int]] = None,
) -> pd.DataFrame:
    """Generate claims lines with embedded behavioral scenarios"""
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
        
        # Generate claims for this month (default: heavy; use claims_per_month_range for long histories)
        if claims_per_month_range is None:
            lo, hi = 5000, 20000
        else:
            lo, hi = int(claims_per_month_range[0]), int(claims_per_month_range[1])
        claims_per_month = random.randint(lo, hi)
        
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
            
            # Apply scenario effects
            base_volume = 1.0
            base_allowed = random.uniform(100, 1000)
            
            # Scenario 1: Tighten PA for outpatient MRI (effective date: 6 months in)
            if "scenario_1" in scenarios:
                scenario = scenarios["scenario_1"]
                effective_date = scenario["effective_date"]
                if current_date >= effective_date and category == "MRI" and pos_code == "11":
                    # MRI volume down, but ER imaging up
                    base_volume *= 0.7  # 30% reduction
                elif current_date >= effective_date and category == "ER_IMAGING":
                    # ER imaging increases
                    base_volume *= 1.4  # 40% increase
            
            # Scenario 2: Site-of-care restriction for infusion
            if "scenario_2" in scenarios:
                scenario = scenarios["scenario_2"]
                effective_date = scenario["effective_date"]
                if current_date >= effective_date and category == "INFUSION" and pos_code == "22":
                    # Hospital outpatient down
                    base_volume *= 0.6
                elif current_date >= effective_date and category == "INFUSION" and pos_code == "19":
                    # Freestanding up
                    base_volume *= 1.5
            
            # Scenario 3: Coverage relaxation for PT
            if "scenario_3" in scenarios:
                scenario = scenarios["scenario_3"]
                effective_date = scenario["effective_date"]
                if current_date >= effective_date and category == "PT":
                    base_volume *= 1.3
                # Offset: reduced imaging 60 days later
                elif current_date >= effective_date + timedelta(days=60) and category == "MRI":
                    base_volume *= 0.9
            
            # Scenario 4: Step therapy for high-cost biologic (proxy)
            if "scenario_4" in scenarios:
                scenario = scenarios["scenario_4"]
                effective_date = scenario["effective_date"]
                if current_date >= effective_date and category == "INFUSION" and code in ["96413", "96415"]:
                    base_volume *= 0.8
                elif current_date >= effective_date and category == "SPECIALTY_VISIT":
                    base_volume *= 1.2
            
            # Scenario 5: Urgent care copay increase
            if "scenario_5" in scenarios:
                scenario = scenarios["scenario_5"]
                effective_date = scenario["effective_date"]
                if current_date >= effective_date and category == "URGENT_CARE":
                    base_volume *= 0.7
                elif current_date >= effective_date and category == "ER_IMAGING":
                    base_volume *= 1.3
            
            # Generate claim
            service_from = current_date + timedelta(days=random.randint(1, 28))
            service_to = service_from + timedelta(days=random.randint(0, 7))
            paid_date = service_to + timedelta(days=random.randint(30, 90))
            
            allowed_amount = base_allowed * base_volume
            paid_amount = allowed_amount * random.uniform(0.8, 1.0)
            units = base_volume * random.uniform(0.5, 2.0)
            
            # Determine network tier (align with in_network_flag)
            in_network = random.random() > 0.2
            network_tier = provider["network_tier"] if in_network else "TIER_3"
            
            # Map service category
            service_category = SERVICE_CATEGORY_MAP.get(category, "OTHER")
            
            # Generate diagnosis and group
            diag_1 = None
            diagnosis_group = "OTHER"
            if random.random() > 0.5:
                diag_code = random.choice(["M10", "M20", "M50", "Z00", "Z87"])
                diag_1 = f"{diag_code}.{random.randint(0, 9)}"
                if diag_code.startswith("M"):
                    diagnosis_group = "MUSCULOSKELETAL"
                elif diag_code.startswith("Z"):
                    diagnosis_group = "PREVENTIVE"
            
            claims.append({
                "tenant_id": tenant_id,
                "member_id": member["member_id"],
                "claim_id": f"CLM_{uuid4().hex[:8]}",
                "claim_line_id": f"CLM_{uuid4().hex[:12]}",
                "service_from_date": service_from.strftime("%Y-%m-%d"),
                "service_to_date": service_to.strftime("%Y-%m-%d"),
                "paid_date": paid_date.strftime("%Y-%m-%d"),
                "lob": lob,
                "market": market,
                "plan_id": member.get("plan_id", random.choice(PLANS)),
                "product_type": member.get("product_type", "PPO"),
                "state": member.get("state", STATES.get(market, "NY")),
                "region": member.get("region", REGIONS.get(market, "NORTHEAST")),
                "place_of_service": pos_code,
                "cpt_hcpcs": code,
                "service_category": service_category,
                "rendering_npi": provider["npi"],
                "billing_npi": provider["npi"] if random.random() > 0.3 else None,
                "network_tier": network_tier,
                "allowed_amount": round(allowed_amount, 2),
                "paid_amount": round(paid_amount, 2),
                "units": round(units, 2),
                "in_network_flag": in_network,
                "modifier_1": random.choice([None, "26", "TC", "59"]) if random.random() > 0.7 else None,
                "diag_1": diag_1,
                "diagnosis_group": diagnosis_group,
            })
        
        # Move to next month
        if month == 12:
            current_date = datetime(year + 1, 1, 1)
        else:
            current_date = datetime(year, month + 1, 1)
    
    return pd.DataFrame(claims)


def generate_policies(tenant_id: str, start_date: datetime) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate policy metadata"""
    policies_data = []
    versions_data = []
    code_sets_data = []
    
    # Scenario policies
    scenarios = [
        {
            "policy_id": "POL_001",
            "name": "Tighten PA for Outpatient MRI",
            "policy_type": "PA",
            "effective_date": start_date + timedelta(days=180),  # 6 months in
            "codes": SERVICE_CATEGORIES["MRI"]["codes"],
            "code_group": "MRI_LUMBAR",
        },
        {
            "policy_id": "POL_002",
            "name": "Site-of-Care Restriction for Infusion",
            "policy_type": "SITE_OF_CARE",
            "effective_date": start_date + timedelta(days=210),
            "codes": SERVICE_CATEGORIES["INFUSION"]["codes"],
            "code_group": "INFUSION",
        },
        {
            "policy_id": "POL_003",
            "name": "Coverage Relaxation for PT",
            "policy_type": "COVERAGE",
            "effective_date": start_date + timedelta(days=240),
            "codes": SERVICE_CATEGORIES["PT"]["codes"],
            "code_group": "PT",
        },
        {
            "policy_id": "POL_004",
            "name": "Step Therapy for High-Cost Biologic",
            "policy_type": "STEP_THERAPY",
            "effective_date": start_date + timedelta(days=270),
            "codes": ["96413", "96415"],
            "code_group": "BIOLOGIC",
        },
        {
            "policy_id": "POL_005",
            "name": "Urgent Care Copay Increase",
            "policy_type": "BENEFIT",
            "effective_date": start_date + timedelta(days=300),
            "codes": SERVICE_CATEGORIES["URGENT_CARE"]["codes"],
            "code_group": "URGENT_CARE",
        },
    ]
    
    for scenario in scenarios:
        policies_data.append({
            "policy_id": scenario["policy_id"],
            "policy_name": scenario["name"],
            "policy_type": scenario["policy_type"],
            "owner_role": "UM_LEADER",
            "description": f"Policy: {scenario['name']}",
        })
        
        versions_data.append({
            "policy_id": scenario["policy_id"],
            "version_id": f"{scenario['policy_id']}_V1",
            "effective_start_date": scenario["effective_date"].strftime("%Y-%m-%d"),
            "effective_end_date": None,
            "change_type": "TIGHTEN" if "Tighten" in scenario["name"] or "Restriction" in scenario["name"] else "RELAX",
            "enforcement_strength": "HARD",
            "justification": "Cost management",
        })
        
        for code in scenario["codes"]:
            code_sets_data.append({
                "version_id": f"{scenario['policy_id']}_V1",
                "code_type": "CPT",
                "code": code,
                "code_group": scenario["code_group"],
            })
    
    return (
        pd.DataFrame(policies_data),
        pd.DataFrame(versions_data),
        pd.DataFrame(code_sets_data),
    )


def generate_ground_truth(scenarios: dict[str, Any]) -> dict[str, Any]:
    """Generate ground truth expected impacts"""
    return {
        "POL_001": {
            "expected_direction": {
                "utilization": "DOWN",
                "cost": "UP",  # Net increase due to ER substitution
            },
            "expected_substitution_codes": ["70450", "70460"],  # ER imaging
        },
        "POL_002": {
            "expected_direction": {
                "utilization": "MIXED",
                "cost": "DOWN",  # Net decrease
            },
            "expected_substitution_codes": [],
        },
        "POL_003": {
            "expected_direction": {
                "utilization": "UP",
                "cost": "MIXED",
            },
            "expected_substitution_codes": [],
        },
        "POL_004": {
            "expected_direction": {
                "utilization": "MIXED",
                "cost": "MIXED",
            },
            "expected_substitution_codes": ["99213", "99214"],
        },
        "POL_005": {
            "expected_direction": {
                "utilization": "DOWN",
                "cost": "UP",  # ER increases
            },
            "expected_substitution_codes": ["70450", "70460"],
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic UEPI data")
    parser.add_argument("--out", type=str, default="data/demo", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--members", type=int, default=50000, help="Number of members")
    parser.add_argument("--providers", type=int, default=5000, help="Number of providers")
    parser.add_argument("--months", type=int, default=24, help="Number of months of data")
    
    args = parser.parse_args()
    
    # Set seed
    random.seed(args.seed)
    
    # Create output directory
    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    print("Generating members...")
    members_df = generate_members(args.members, LOBS, MARKETS)
    members_df.to_csv(out_path / "enrollment_202401.csv", index=False)
    
    print("Generating providers...")
    providers_df = generate_providers(args.providers, MARKETS)
    providers_df.to_csv(out_path / "providers.csv", index=False)
    
    print("Generating claims...")
    start_date = datetime(2024, 1, 1)
    end_date = start_date + timedelta(days=args.months * 30)
    
    tenant_id = "00000000-0000-0000-0000-000000000001"
    
    # Define scenarios with effective dates
    scenarios = {
        "scenario_1": {"effective_date": start_date + timedelta(days=180)},
        "scenario_2": {"effective_date": start_date + timedelta(days=210)},
        "scenario_3": {"effective_date": start_date + timedelta(days=240)},
        "scenario_4": {"effective_date": start_date + timedelta(days=270)},
        "scenario_5": {"effective_date": start_date + timedelta(days=300)},
    }
    
    claims_df = generate_claims_lines(
        members_df, providers_df, start_date, end_date, tenant_id, scenarios
    )
    
    # Write claims by month
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
    
    print("Generating policies...")
    policies_df, versions_df, code_sets_df = generate_policies(tenant_id, start_date)
    policies_df.to_csv(out_path / "policies.csv", index=False)
    versions_df.to_csv(out_path / "policy_versions.csv", index=False)
    code_sets_df.to_csv(out_path / "policy_code_sets.csv", index=False)
    
    print("Generating ground truth...")
    ground_truth = generate_ground_truth(scenarios)
    with open(out_path / "ground_truth_expected_impacts.json", "w") as f:
        json.dump(ground_truth, f, indent=2)
    
    print(f"Data generation complete! Output: {out_path}")
    print(f"Generated {len(claims_df)} claims lines")
    print(f"Generated {len(members_df)} members")
    print(f"Generated {len(providers_df)} providers")


if __name__ == "__main__":
    main()

