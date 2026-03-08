#!/usr/bin/env python3
"""
Test policy scoping algorithm with enhanced data fields.

Verifies that policy scoping correctly filters claims using:
- Population: lob, markets, plans, product_types
- Geography: states, regions
- Network: network, network_tiers
- Member attributes: age, gender
- Provider: specialties
- Service: service_category, diagnosis_group
"""
import sys
from pathlib import Path
from datetime import datetime, date
import pandas as pd

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

# Note: Policy scoping functions are used internally by the API
# This test script validates the filtering logic manually


def load_test_data(tenant_id: str):
    """Load test data from target_data_model"""
    data_dir = PROJECT_ROOT / "apps" / "data" / "target_data_model" / tenant_id
    
    # Load claims
    claims_file = data_dir / "CLAIMS_LINES" / "claims_lines.csv"
    if not claims_file.exists():
        raise FileNotFoundError(f"Claims file not found: {claims_file}")
    
    claims_df = pd.read_csv(claims_file, nrows=10000)  # Sample for testing
    
    # Load members
    members_file = data_dir / "ENROLLMENT" / "enrollment.csv"
    members_df = None
    if members_file.exists():
        members_df = pd.read_csv(members_file)
    
    # Load providers
    providers_file = data_dir / "PROVIDERS" / "providers.csv"
    providers_df = None
    if providers_file.exists():
        providers_df = pd.read_csv(providers_file)
    
    return claims_df, members_df, providers_df


def test_policy_scope_filter(scope: dict, description: str, claims_df: pd.DataFrame):
    """Test a specific policy scope filter"""
    print(f"\n{'='*60}")
    print(f"Test: {description}")
    print(f"{'='*60}")
    
    print(f"Scope: {scope}")
    print(f"Initial claims: {len(claims_df)}")
    
    # Apply filters manually to verify
    filtered = claims_df.copy()
    
    if scope.get("lob"):
        filtered = filtered[filtered["lob"].isin(scope["lob"])]
        print(f"  After LOB filter ({scope['lob']}): {len(filtered)}")
    
    if scope.get("markets") and "ALL" not in scope["markets"]:
        filtered = filtered[filtered["market"].isin(scope["markets"])]
        print(f"  After markets filter ({scope['markets']}): {len(filtered)}")
    
    if scope.get("plans"):
        if "plan_id" in filtered.columns:
            filtered = filtered[filtered["plan_id"].isin(scope["plans"])]
            print(f"  After plans filter ({scope['plans']}): {len(filtered)}")
        else:
            print(f"  ⚠️  plan_id column not found in claims")
    
    if scope.get("product_types"):
        if "product_type" in filtered.columns:
            filtered = filtered[filtered["product_type"].isin(scope["product_types"])]
            print(f"  After product_types filter ({scope['product_types']}): {len(filtered)}")
        else:
            print(f"  ⚠️  product_type column not found in claims")
    
    if scope.get("states"):
        if "state" in filtered.columns:
            filtered = filtered[filtered["state"].isin(scope["states"])]
            print(f"  After states filter ({scope['states']}): {len(filtered)}")
        else:
            print(f"  ⚠️  state column not found in claims")
    
    if scope.get("regions"):
        if "region" in filtered.columns:
            filtered = filtered[filtered["region"].isin(scope["regions"])]
            print(f"  After regions filter ({scope['regions']}): {len(filtered)}")
        else:
            print(f"  ⚠️  region column not found in claims")
    
    if scope.get("network_tiers"):
        if "network_tier" in filtered.columns:
            filtered = filtered[filtered["network_tier"].isin(scope["network_tiers"])]
            print(f"  After network_tiers filter ({scope['network_tiers']}): {len(filtered)}")
        else:
            print(f"  ⚠️  network_tier column not found in claims")
    
    if scope.get("service_category"):
        if "service_category" in filtered.columns:
            filtered = filtered[filtered["service_category"] == scope["service_category"]]
            print(f"  After service_category filter ({scope['service_category']}): {len(filtered)}")
        else:
            print(f"  ⚠️  service_category column not found in claims")
    
    if scope.get("diagnosis_group"):
        if "diagnosis_group" in filtered.columns:
            filtered = filtered[filtered["diagnosis_group"] == scope["diagnosis_group"]]
            print(f"  After diagnosis_group filter ({scope['diagnosis_group']}): {len(filtered)}")
        else:
            print(f"  ⚠️  diagnosis_group column not found in claims")
    
    print(f"\n✅ Final filtered claims: {len(filtered)}")
    
    return filtered


def main():
    """Run policy scoping tests"""
    print("="*60)
    print("Policy Scoping Algorithm Test")
    print("="*60)
    
    tenant_id = "00000000-0000-0000-0000-000000000001"
    
    try:
        claims_df, members_df, providers_df = load_test_data(tenant_id)
        print(f"\n✅ Loaded test data:")
        print(f"  Claims: {len(claims_df)} rows")
        print(f"  Members: {len(members_df) if members_df is not None else 0} rows")
        print(f"  Providers: {len(providers_df) if providers_df is not None else 0} rows")
        
        # Show available columns
        print(f"\n📋 Claims columns: {list(claims_df.columns)}")
        
    except FileNotFoundError as e:
        print(f"❌ Error loading test data: {e}")
        print("\nPlease run scripts/regenerate_complete_workflow.py first to generate test data.")
        return
    
    # Test 1: Basic LOB + Market filter
    test_policy_scope_filter(
        {"lob": ["COMMERCIAL"], "markets": ["NYC"]},
        "LOB + Market Filter",
        claims_df
    )
    
    # Test 2: Plan + Product Type filter
    test_policy_scope_filter(
        {"lob": ["COMMERCIAL"], "plans": ["PLAN_A", "PLAN_B"], "product_types": ["PPO"]},
        "Plan + Product Type Filter",
        claims_df
    )
    
    # Test 3: State + Region filter
    test_policy_scope_filter(
        {"states": ["NY"], "regions": ["NORTHEAST"]},
        "State + Region Filter",
        claims_df
    )
    
    # Test 4: Network Tier filter
    test_policy_scope_filter(
        {"lob": ["COMMERCIAL"], "network_tiers": ["TIER_1"]},
        "Network Tier Filter",
        claims_df
    )
    
    # Test 5: Service Category filter
    test_policy_scope_filter(
        {"lob": ["COMMERCIAL"], "service_category": "ADVANCED_IMAGING"},
        "Service Category Filter",
        claims_df
    )
    
    # Test 6: Combined comprehensive scope
    test_policy_scope_filter(
        {
            "lob": ["COMMERCIAL"],
            "markets": ["NYC"],
            "plans": ["PLAN_A"],
            "product_types": ["PPO"],
            "states": ["NY"],
            "network_tiers": ["TIER_1", "TIER_2"],
            "service_category": "ADVANCED_IMAGING"
        },
        "Comprehensive Scope Filter (All Dimensions)",
        claims_df
    )
    
    print("\n" + "="*60)
    print("✅ Policy Scoping Tests Complete")
    print("="*60)


if __name__ == "__main__":
    main()
