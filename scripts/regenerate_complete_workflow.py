#!/usr/bin/env python3
"""
Complete workflow script:
1. Regenerate data with proper dates (24 months: Jan 2024 - Dec 2025)
2. Load data to target_data_model
3. Run baseline analysis
4. Generate predicted impact for all policies
5. Generate post-policy data for last 5 days (Dec 27-31, 2025)
6. Enable observation analysis

This ensures all data has proper service_from_date values and supports the full product use case.
"""
import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import json

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

# Import generation functions
import importlib.util

# Load synth.generate module
synth_generate_path = PROJECT_ROOT / "scripts" / "synth" / "generate.py"
spec = importlib.util.spec_from_file_location("synth_generate", synth_generate_path)
synth_generate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(synth_generate)

generate_claims_lines = synth_generate.generate_claims_lines
generate_members = synth_generate.generate_members
generate_providers = synth_generate.generate_providers
MARKETS = synth_generate.MARKETS
LOBS = synth_generate.LOBS

# Load post_policy module
post_policy_path = PROJECT_ROOT / "scripts" / "generate_post_policy_synthetic_data.py"
spec2 = importlib.util.spec_from_file_location("post_policy", post_policy_path)
post_policy = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(post_policy)

generate_post_policy_claims_lines = post_policy.generate_post_policy_claims_lines


def regenerate_baseline_data(out_dir: Path, tenant_id: str, months: int = 24):
    """Generate baseline data for 24 months (Jan 2024 - Dec 2025)"""
    print("\n" + "="*60)
    print("STEP 1: Generating Baseline Data (24 months)")
    print("="*60)
    
    start_date = datetime(2024, 1, 1)
    end_date = start_date + timedelta(days=months * 30)
    
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    print(f"Generating members...")
    members_df = generate_members(50000, LOBS, MARKETS)
    
    print(f"Generating providers...")
    providers_df = generate_providers(5000, MARKETS)
    
    print(f"Generating claims...")
    # Define scenarios (for baseline, no policy effects yet)
    scenarios = {
        "scenario_1": {"effective_date": start_date + timedelta(days=180)},
        "scenario_2": {"effective_date": start_date + timedelta(days=210)},
    }
    
    claims_df = generate_claims_lines(
        members_df, providers_df, start_date, end_date, tenant_id, scenarios
    )
    
    print(f"✅ Generated {len(claims_df)} claims")
    print(f"✅ Date column 'service_from_date' present: {'service_from_date' in claims_df.columns}")
    
    # Verify dates are populated
    date_count = claims_df['service_from_date'].notna().sum()
    empty_count = (claims_df['service_from_date'].astype(str).str.strip() == '').sum()
    print(f"✅ Non-null dates: {date_count} / {len(claims_df)}")
    print(f"✅ Empty date strings: {empty_count}")
    
    if empty_count > 0 or date_count < len(claims_df):
        print(f"⚠️  WARNING: Some dates are missing! Fixing...")
        # Remove rows with empty dates
        claims_df = claims_df[claims_df['service_from_date'].notna()]
        claims_df = claims_df[claims_df['service_from_date'].astype(str).str.strip() != '']
        print(f"✅ After cleanup: {len(claims_df)} claims with valid dates")
    
    return members_df, providers_df, claims_df


def load_to_target_data_model(
    claims_df: pd.DataFrame,
    members_df: pd.DataFrame,
    providers_df: pd.DataFrame,
    tenant_id: str,
    target_dir: Path
):
    """Load claims, members, and providers data to target_data_model directory"""
    print("\n" + "="*60)
    print("STEP 2: Loading Data to target_data_model")
    print("="*60)
    
    tenant_dir = target_dir / tenant_id
    tenant_dir.mkdir(parents=True, exist_ok=True)
    
    # Claims
    claims_dir = tenant_dir / "CLAIMS_LINES"
    claims_dir.mkdir(parents=True, exist_ok=True)
    claims_file = claims_dir / "claims_lines.csv"
    
    # Ensure service_from_date is the first date column (for compatibility)
    if 'service_from_date' in claims_df.columns:
        cols = ['service_from_date'] + [c for c in claims_df.columns if c != 'service_from_date']
        claims_df = claims_df[cols]
    
    claims_df.to_csv(claims_file, index=False)
    print(f"✅ Wrote {len(claims_df)} claims to {claims_file}")
    
    # Members (enrollment)
    members_dir = tenant_dir / "ENROLLMENT"
    members_dir.mkdir(parents=True, exist_ok=True)
    members_file = members_dir / "enrollment.csv"
    members_df.to_csv(members_file, index=False)
    print(f"✅ Wrote {len(members_df)} members to {members_file}")
    
    # Providers
    providers_dir = tenant_dir / "PROVIDERS"
    providers_dir.mkdir(parents=True, exist_ok=True)
    providers_file = providers_dir / "providers.csv"
    providers_df.to_csv(providers_file, index=False)
    print(f"✅ Wrote {len(providers_df)} providers to {providers_file}")
    
    # Verify comprehensive scope fields
    print("\n📊 Verifying Comprehensive Scope Fields:")
    
    # Check claims fields
    required_claims_fields = [
        "service_from_date", "lob", "market", "plan_id", "product_type",
        "state", "region", "network_tier", "service_category", "diagnosis_group"
    ]
    missing_claims = [f for f in required_claims_fields if f not in claims_df.columns]
    if missing_claims:
        print(f"  ⚠️  Missing claims fields: {missing_claims}")
    else:
        print(f"  ✅ All {len(required_claims_fields)} required claims fields present")
    
    # Check members fields
    required_members_fields = ["member_id", "lob", "market", "plan_id", "product_type", "state", "region"]
    missing_members = [f for f in required_members_fields if f not in members_df.columns]
    if missing_members:
        print(f"  ⚠️  Missing members fields: {missing_members}")
    else:
        print(f"  ✅ All {len(required_members_fields)} required members fields present")
    
    # Check providers fields
    required_providers_fields = ["npi", "specialty", "market", "network_tier"]
    missing_providers = [f for f in required_providers_fields if f not in providers_df.columns]
    if missing_providers:
        print(f"  ⚠️  Missing providers fields: {missing_providers}")
    else:
        print(f"  ✅ All {len(required_providers_fields)} required providers fields present")
    
    # Show sample values
    print("\n📋 Sample Data Values:")
    print(f"  Claims - Plans: {claims_df['plan_id'].unique()[:5].tolist()}")
    print(f"  Claims - Product Types: {claims_df['product_type'].unique().tolist()}")
    print(f"  Claims - Network Tiers: {claims_df['network_tier'].unique().tolist()}")
    print(f"  Claims - Service Categories: {claims_df['service_category'].unique().tolist()}")
    
    # Verify dates in written file
    verify_df = pd.read_csv(claims_file, nrows=100)
    if 'service_from_date' in verify_df.columns:
        date_count = verify_df['service_from_date'].notna().sum()
        print(f"\n✅ Verified: {date_count}/100 sample rows have dates")
        print(f"   Sample dates: {verify_df['service_from_date'].head(3).tolist()}")
    else:
        print(f"\n⚠️  WARNING: service_from_date column not found in written file!")
        print(f"   Available columns: {list(verify_df.columns)}")
    
    return claims_file


def generate_post_policy_data(
    members_df: pd.DataFrame,
    providers_df: pd.DataFrame,
    tenant_id: str,
    target_file: Path,
    days: int = 5
):
    """Generate post-policy data for last N days and append to existing claims"""
    print("\n" + "="*60)
    print(f"STEP 5: Generating Post-Policy Data (last {days} days)")
    print("="*60)
    
    # Last 5 days of 2025
    end_date = datetime(2025, 12, 31)
    start_date = end_date - timedelta(days=days - 1)
    
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    print(f"Policies are effective - all data reflects policy impacts")
    
    # Define policy scenarios (all effective from start_date)
    policy_scenarios = {
        "policy_1": {"effective_date": start_date},
        "policy_2": {"effective_date": start_date},
        "policy_3": {"effective_date": start_date},
        "policy_4": {"effective_date": start_date},
        "policy_5": {"effective_date": start_date},
    }
    
    post_policy_df = generate_post_policy_claims_lines(
        members_df, providers_df, start_date, end_date, tenant_id, policy_scenarios
    )
    
    print(f"✅ Generated {len(post_policy_df)} post-policy claims")
    
    # Verify dates
    date_count = post_policy_df['service_from_date'].notna().sum()
    print(f"✅ Non-null dates: {date_count} / {len(post_policy_df)}")
    print(f"   Sample dates: {post_policy_df['service_from_date'].head(3).tolist()}")
    
    # Append to existing claims file
    print(f"📝 Appending to existing claims file...")
    existing_df = pd.read_csv(target_file)
    print(f"   Existing claims: {len(existing_df)}")
    
    # Ensure column order matches
    post_policy_df = post_policy_df[existing_df.columns]
    
    combined_df = pd.concat([existing_df, post_policy_df], ignore_index=True)
    combined_df.to_csv(target_file, index=False)
    
    print(f"✅ Combined file now has {len(combined_df)} total claims")
    print(f"   Added {len(post_policy_df)} post-policy claims")
    
    return post_policy_df


def main():
    parser = argparse.ArgumentParser(description="Complete data regeneration and workflow")
    parser.add_argument("--tenant-id", type=str, default="00000000-0000-0000-0000-000000000001")
    parser.add_argument("--months", type=int, default=24, help="Months of baseline data (default: 24)")
    parser.add_argument("--post-days", type=int, default=5, help="Days of post-policy data (default: 5)")
    parser.add_argument("--skip-post-policy", action="store_true", help="Skip post-policy data generation")
    
    args = parser.parse_args()
    
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data" / "synthetic"
    # Use apps/api/data/target_data_model to match API expectations
    TARGET_DATA_DIR = PROJECT_ROOT / "apps" / "api" / "data" / "target_data_model"
    
    # Clean old data
    print("🧹 Cleaning old data...")
    if (TARGET_DATA_DIR / args.tenant_id).exists():
        import shutil
        shutil.rmtree(TARGET_DATA_DIR / args.tenant_id)
    (TARGET_DATA_DIR / args.tenant_id).mkdir(parents=True, exist_ok=True)
    
    # Step 1: Generate baseline data
    members_df, providers_df, claims_df = regenerate_baseline_data(
        DATA_DIR, args.tenant_id, months=args.months
    )
    
    # Step 2: Load to target_data_model
    target_file = load_to_target_data_model(
        claims_df, members_df, providers_df, args.tenant_id, TARGET_DATA_DIR
    )
    
    # Step 3: Post-policy data (if not skipped)
    if not args.skip_post_policy:
        generate_post_policy_data(
            members_df, providers_df, args.tenant_id, target_file, days=args.post_days
        )
    
    print("\n" + "="*60)
    print("✅ DATA REGENERATION COMPLETE!")
    print("="*60)
    print("\nNext steps (via UI or API):")
    print("  1. Run baseline analysis: POST /api/v1/analyses/baseline")
    print("  2. Generate predicted impact: POST /api/v1/policies/{policy_id}/predicted-impact")
    print("  3. Run observation analysis: POST /api/v1/observations/from-analysis/{analysis_id}")
    print(f"\nData location: {target_file}")
    print("")


if __name__ == "__main__":
    main()
