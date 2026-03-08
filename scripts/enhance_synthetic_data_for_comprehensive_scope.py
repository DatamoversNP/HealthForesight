#!/usr/bin/env python3
"""
Enhance synthetic data generation to support comprehensive policy scope fields.

This adds missing fields needed for policy scoping:
- Claims: plan_id, product_type, network_tier, state, region, service_category, diagnosis_group
- Members: plan_id, product_type, state, region
- Providers: network_tier

Allows policies to filter by these dimensions as specified in PolicyScope.
"""
import sys
from pathlib import Path
import pandas as pd
import random
from typing import Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import existing generation functions
from scripts.synth.generate import (
    generate_members,
    generate_providers,
    generate_claims_lines,
    LOBS,
    MARKETS,
    SERVICE_CATEGORIES,
)


# Additional data for comprehensive scope
STATES = ["NY", "TX", "MA", "CA", "FL", "IL"]  # States for markets
REGIONS = ["NORTHEAST", "SOUTH", "WEST", "MIDWEST"]
PLANS = ["PLAN_A", "PLAN_B", "PLAN_C", "PLAN_D", "PLAN_E"]
PRODUCT_TYPES = ["HMO", "PPO", "EPO", "POS", "HDHP"]
NETWORK_TIERS = ["TIER_1", "TIER_2", "TIER_3"]

# Mapping from market to state/region
MARKET_TO_STATE = {
    "NYC": "NY",
    "DFW": "TX",
    "BOS": "MA",
}
MARKET_TO_REGION = {
    "NYC": "NORTHEAST",
    "DFW": "SOUTH",
    "BOS": "NORTHEAST",
}

# Service category mapping (extend SERVICE_CATEGORIES)
SERVICE_CATEGORY_MAP = {
    "MRI": "ADVANCED_IMAGING",
    "ER_IMAGING": "ADVANCED_IMAGING",
    "INFUSION": "SPECIALTY_SERVICES",
    "PT": "REHABILITATION",
    "SPECIALTY_VISIT": "SPECIALTY_CARE",
    "URGENT_CARE": "URGENT_CARE",
}

# Diagnosis group mapping (simplified)
DIAGNOSIS_GROUP_MAP = {
    "M10": "MUSCULOSKELETAL",
    "M20": "MUSCULOSKELETAL",
    "M50": "MUSCULOSKELETAL",
    "Z00": "PREVENTIVE",
    "Z87": "PREVENTIVE",
}


def enhance_members_df(members_df: pd.DataFrame) -> pd.DataFrame:
    """Add plan_id, product_type, state, region to members"""
    enhanced = members_df.copy()
    
    # Add plan_id
    enhanced["plan_id"] = enhanced.apply(
        lambda row: random.choice(PLANS),
        axis=1
    )
    
    # Add product_type (correlated with LOB)
    enhanced["product_type"] = enhanced.apply(
        lambda row: random.choice(["HMO", "PPO"]) if row["lob"] == "COMMERCIAL" else "HMO",
        axis=1
    )
    
    # Add state and region from market
    enhanced["state"] = enhanced["market"].map(MARKET_TO_STATE).fillna("NY")
    enhanced["region"] = enhanced["market"].map(MARKET_TO_REGION).fillna("NORTHEAST")
    
    return enhanced


def enhance_providers_df(providers_df: pd.DataFrame) -> pd.DataFrame:
    """Add network_tier to providers"""
    enhanced = providers_df.copy()
    
    # Assign network tier (TIER_1 = preferred, TIER_2 = standard, TIER_3 = out-of-network)
    # Most providers are TIER_1 or TIER_2
    enhanced["network_tier"] = enhanced.apply(
        lambda row: random.choices(
            NETWORK_TIERS,
            weights=[50, 40, 10]  # 50% TIER_1, 40% TIER_2, 10% TIER_3
        )[0],
        axis=1
    )
    
    return enhanced


def enhance_claims_df(
    claims_df: pd.DataFrame,
    members_df: pd.DataFrame,
    providers_df: pd.DataFrame,
) -> pd.DataFrame:
    """Add plan_id, product_type, network_tier, state, region, service_category, diagnosis_group to claims"""
    enhanced = claims_df.copy()
    
    # Merge member fields (plan_id, product_type, state, region)
    member_fields = members_df[["member_id", "plan_id", "product_type", "state", "region"]].copy()
    enhanced = enhanced.merge(member_fields, on="member_id", how="left")
    
    # Merge provider fields (network_tier)
    provider_fields = providers_df[["npi", "network_tier"]].copy()
    provider_fields = provider_fields.rename(columns={"npi": "rendering_npi"})
    enhanced = enhanced.merge(provider_fields, on="rendering_npi", how="left")
    
    # Add service_category from CPT code
    # Map CPT codes to service categories
    cpt_to_category = {}
    for category, info in SERVICE_CATEGORIES.items():
        for code in info.get("codes", []):
            cpt_to_category[code] = SERVICE_CATEGORY_MAP.get(category, "OTHER")
    
    enhanced["service_category"] = enhanced["cpt_hcpcs"].map(cpt_to_category).fillna("OTHER")
    
    # Add diagnosis_group from diag_1
    enhanced["diagnosis_group"] = enhanced["diag_1"].apply(
        lambda d: DIAGNOSIS_GROUP_MAP.get(str(d)[:3], "OTHER") if pd.notna(d) and str(d).startswith("M") else "OTHER"
    )
    
    # Ensure network_tier aligns with in_network_flag
    # If in_network_flag is False, network_tier should be TIER_3 or None
    enhanced.loc[enhanced["in_network_flag"] == False, "network_tier"] = "TIER_3"
    
    # Fill any remaining nulls with defaults
    enhanced["plan_id"] = enhanced["plan_id"].fillna(random.choice(PLANS))
    enhanced["product_type"] = enhanced["product_type"].fillna("PPO")
    enhanced["state"] = enhanced["state"].fillna("NY")
    enhanced["region"] = enhanced["region"].fillna("NORTHEAST")
    enhanced["network_tier"] = enhanced["network_tier"].fillna("TIER_2")
    enhanced["service_category"] = enhanced["service_category"].fillna("OTHER")
    enhanced["diagnosis_group"] = enhanced["diagnosis_group"].fillna("OTHER")
    
    return enhanced


def verify_enhanced_data(claims_df: pd.DataFrame, members_df: pd.DataFrame, providers_df: pd.DataFrame) -> None:
    """Verify that all required fields are present"""
    required_claims_fields = [
        "service_from_date", "service_to_date", "paid_date",
        "tenant_id", "member_id", "claim_id", "claim_line_id",
        "lob", "market", "plan_id", "product_type", "state", "region",
        "place_of_service", "cpt_hcpcs", "service_category",
        "rendering_npi", "network_tier",
        "allowed_amount", "paid_amount", "units",
        "in_network_flag",
        "diag_1", "diagnosis_group",
    ]
    
    required_members_fields = [
        "member_id", "lob", "market", "plan_id", "product_type", "state", "region",
        "gender", "dob_year", "risk_score", "enrolled_flag",
    ]
    
    required_providers_fields = [
        "npi", "provider_name", "specialty", "market", "network_tier",
        "facility_flag",
    ]
    
    print("\n" + "="*60)
    print("Verifying Enhanced Data Structure")
    print("="*60)
    
    # Check claims
    missing_claims = [f for f in required_claims_fields if f not in claims_df.columns]
    if missing_claims:
        print(f"❌ Missing claims fields: {missing_claims}")
    else:
        print(f"✅ All {len(required_claims_fields)} claims fields present")
    
    # Check members
    missing_members = [f for f in required_members_fields if f not in members_df.columns]
    if missing_members:
        print(f"❌ Missing members fields: {missing_members}")
    else:
        print(f"✅ All {len(required_members_fields)} members fields present")
    
    # Check providers
    missing_providers = [f for f in required_providers_fields if f not in providers_df.columns]
    if missing_providers:
        print(f"❌ Missing providers fields: {missing_providers}")
    else:
        print(f"✅ All {len(required_providers_fields)} providers fields present")
    
    # Show sample values
    print("\nSample Claims Data:")
    print(f"  - Columns: {list(claims_df.columns)[:10]}... ({len(claims_df.columns)} total)")
    print(f"  - Sample plan_id values: {claims_df['plan_id'].unique()[:5].tolist()}")
    print(f"  - Sample product_type values: {claims_df['product_type'].unique().tolist()}")
    print(f"  - Sample network_tier values: {claims_df['network_tier'].unique().tolist()}")
    print(f"  - Sample states: {claims_df['state'].unique().tolist()}")
    print(f"  - Sample service_category values: {claims_df['service_category'].unique().tolist()}")
    
    print("\nSample Members Data:")
    print(f"  - Sample plan_id values: {members_df['plan_id'].unique()[:5].tolist()}")
    print(f"  - Sample product_type values: {members_df['product_type'].unique().tolist()}")
    print(f"  - Sample states: {members_df['state'].unique().tolist()}")
    
    print("\nSample Providers Data:")
    print(f"  - Sample network_tier values: {providers_df['network_tier'].unique().tolist()}")


if __name__ == "__main__":
    print("="*60)
    print("Synthetic Data Enhancement for Comprehensive Policy Scope")
    print("="*60)
    print("\nThis script demonstrates how to enhance synthetic data")
    print("to support all PolicyScope dimensions.\n")
    print("To apply these enhancements to your data generation,")
    print("integrate the enhance_* functions into scripts/synth/generate.py\n")
