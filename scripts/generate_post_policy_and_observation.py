#!/usr/bin/env python3
"""
Generate post-policy data from Jan 1, 2026 to today and run observation analysis

This script:
1. Generates post-policy synthetic data from Jan 1, 2026 to today (Jan 16, 2026)
2. Loads data to target_data_model
3. Runs impact analysis for each policy
4. Creates observations from impact analysis results
"""
import argparse
import subprocess
import sys
import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
from uuid import UUID

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

# Import generation functions
import importlib.util
import pandas as pd

# Load synth.generate module
synth_generate_path = PROJECT_ROOT / "scripts" / "synth" / "generate.py"
spec = importlib.util.spec_from_file_location("synth_generate", synth_generate_path)
synth_generate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(synth_generate)

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

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer dev-token-123"}
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def generate_post_policy_data(policy_effective_date: datetime, end_date: datetime, tenant_id: str):
    """Generate post-policy data from policy_effective_date to end_date"""
    print("\n" + "="*60)
    print(f"Generating Post-Policy Data: {policy_effective_date.date()} to {end_date.date()}")
    print("="*60)
    
    # Load existing members and providers (from baseline data)
    data_root = PROJECT_ROOT / "apps" / "data" / "target_data_model" / tenant_id
    
    # Load members
    members_file = data_root / "MEMBERS" / "members.csv"
    if not members_file.exists():
        print(f"⚠️  Members file not found: {members_file}")
        print("   Generating new members...")
        members_df = generate_members(50000, LOBS, MARKETS)
    else:
        print(f"✅ Loading members from: {members_file}")
        members_df = pd.read_csv(members_file)
    
    # Load providers
    providers_file = data_root / "PROVIDERS" / "providers.csv"
    if not providers_file.exists():
        print(f"⚠️  Providers file not found: {providers_file}")
        print("   Generating new providers...")
        providers_df = generate_providers(5000, MARKETS)
    else:
        print(f"✅ Loading providers from: {providers_file}")
        providers_df = pd.read_csv(providers_file)
    
    # Policy scenarios (policies effective from Jan 1, 2026)
    policy_scenarios = {
        "policy_effective_date": policy_effective_date,
        "scenarios": {
            "scenario_1": {"effective_date": policy_effective_date},
            "scenario_2": {"effective_date": policy_effective_date},
        }
    }
    
    # Generate post-policy claims
    print(f"\nGenerating post-policy claims from {policy_effective_date.date()} to {end_date.date()}...")
    post_policy_claims_df = generate_post_policy_claims_lines(
        members_df,
        providers_df,
        policy_effective_date,
        end_date,
        tenant_id,
        policy_scenarios.get("scenarios", {}),
    )
    
    print(f"✅ Generated {len(post_policy_claims_df)} post-policy claims")
    
    # Load existing claims and append post-policy claims
    claims_file = data_root / "CLAIMS_LINES" / "claims_lines.csv"
    
    if claims_file.exists():
        print(f"✅ Loading existing claims from: {claims_file}")
        existing_claims_df = pd.read_csv(claims_file)
        
        # Append post-policy claims
        combined_claims_df = pd.concat([existing_claims_df, post_policy_claims_df], ignore_index=True)
        print(f"✅ Combined claims: {len(existing_claims_df)} existing + {len(post_policy_claims_df)} new = {len(combined_claims_df)} total")
    else:
        print(f"⚠️  No existing claims file found. Using only post-policy claims.")
        combined_claims_df = post_policy_claims_df
    
    # Save combined claims
    claims_file.parent.mkdir(parents=True, exist_ok=True)
    combined_claims_df.to_csv(claims_file, index=False)
    print(f"✅ Saved combined claims to: {claims_file}")
    
    return combined_claims_df


def load_data_to_target_model_via_pipeline(claims_df: pd.DataFrame, tenant_id: str):
    """Load claims data to target data model via ingestion pipeline"""
    print("\n" + "="*60)
    print("Loading Data to Target Model via Ingestion Pipeline")
    print("="*60)
    
    # Save claims to a temporary CSV file for ingestion
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
        claims_df.to_csv(tmp_file.name, index=False)
        tmp_path = tmp_file.name
    
    try:
        print(f"📤 Uploading {len(claims_df)} claims for ingestion...")
        
        # Upload file via ingestion API
        with open(tmp_path, 'rb') as f:
            files = {'file': ('claims_lines.csv', f, 'text/csv')}
            data = {
                'ingestion_type': 'CLAIMS_LINES',
                'auto_detect_schema': 'true',
            }
            
            response = requests.post(
                f"{API_BASE_URL}/ingestions/upload",
                headers={"Authorization": "Bearer dev-token-123"},  # Don't include Content-Type for multipart
                files=files,
                data=data,
                timeout=600,  # 10 minutes timeout for large files
            )
            response.raise_for_status()
            result = response.json()
        
        ingestion_id = result.get("ingestion_id")
        records_valid = result.get("records_valid", 0)
        curated_partitions = result.get("curated_partitions", [])
        
        print(f"✅ Ingestion successful!")
        print(f"   Ingestion ID: {ingestion_id}")
        print(f"   Valid records: {records_valid:,}")
        print(f"   Curated partitions: {len(curated_partitions)}")
        
        if curated_partitions:
            print(f"   Partition URIs:")
            for partition_uri in curated_partitions[:5]:  # Show first 5
                print(f"     - {partition_uri}")
            if len(curated_partitions) > 5:
                print(f"     ... and {len(curated_partitions) - 5} more")
        
        return True, ingestion_id
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error uploading via ingestion API: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                print(f"   Error detail: {error_detail}")
            except:
                print(f"   Status code: {e.response.status_code}")
                print(f"   Response: {e.response.text[:500]}")
        return False, None
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def get_all_policies():
    """Get all policies from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/policies", headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching policies: {e}")
        return []


def run_impact_analysis(policy_id: UUID, policy_effective_date: datetime, tenant_id: UUID):
    """Run impact analysis for a policy"""
    print(f"\n  Running impact analysis for policy {policy_id}...")
    
    # Build treatment filters from policy scope (default to all if not available)
    treatment_filters = {
        "lob": ["COMMERCIAL", "MA", "MEDICAID"],  # Default - should come from policy scope
        "markets": ["BOS", "DFW", "NYC"],  # Default - should come from policy scope
        "in_network_only": True,
    }
    
    # Calculate date windows (6 months pre, 6 months post - but we only have ~16 days post)
    pre_window_months = 6
    post_window_months = 1  # Only ~16 days available, so 1 month window
    
    payload = {
        "policy_id": str(policy_id),
        "treatment_filters": treatment_filters,
        "control_filters": None,  # No control group for now
        "matching_strategy": None,
        "pre_window_months": pre_window_months,
        "post_window_months": post_window_months,
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyses/impact",
            headers=HEADERS,
            json=payload,
            timeout=300,  # 5 minutes timeout for analysis
        )
        response.raise_for_status()
        result = response.json()
        
        analysis_id = result.get("id")
        status = result.get("status")
        
        print(f"    ✅ Impact analysis created: {analysis_id}, Status: {status}")
        return analysis_id, result
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Error running impact analysis: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                print(f"       Error detail: {error_detail}")
            except:
                print(f"       Status code: {e.response.status_code}")
        return None, None


def create_observation_from_analysis(policy_id: UUID, analysis_id: UUID, tenant_id: UUID):
    """Create observation from impact analysis result"""
    print(f"    Creating observation from analysis {analysis_id}...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/observations/from-analysis/{analysis_id}",
            headers=HEADERS,
            params={"policy_id": str(policy_id)},
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        
        observation_id = result.get("observation_id")
        print(f"    ✅ Observation created: {observation_id}")
        return observation_id, result
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Error creating observation: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                print(f"       Error detail: {error_detail}")
            except:
                print(f"       Status code: {e.response.status_code}")
        return None, None


def main():
    parser = argparse.ArgumentParser(description="Generate post-policy data and run observation analysis")
    parser.add_argument("--policy-date", type=str, default="2026-01-01", help="Policy effective date (default: 2026-01-01)")
    parser.add_argument("--end-date", type=str, default=None, help="End date for data generation (default: today)")
    parser.add_argument("--tenant-id", type=str, default=str(DEFAULT_TENANT_ID), help="Tenant ID")
    parser.add_argument("--skip-data-generation", action="store_true", help="Skip data generation (use existing data)")
    parser.add_argument("--skip-impact-analysis", action="store_true", help="Skip impact analysis (only generate data)")
    
    args = parser.parse_args()
    
    # Parse dates
    policy_effective_date = datetime.fromisoformat(args.policy_date)
    end_date = datetime.fromisoformat(args.end_date) if args.end_date else datetime.now()
    tenant_id = args.tenant_id
    
    print("\n" + "="*60)
    print("POST-POLICY DATA GENERATION & OBSERVATION ANALYSIS")
    print("="*60)
    print(f"Policy effective date: {policy_effective_date.date()}")
    print(f"End date: {end_date.date()}")
    print(f"Tenant ID: {tenant_id}")
    print("="*60)
    
    # Step 1: Generate post-policy data and load via pipeline
    ingestion_id = None
    if not args.skip_data_generation:
        claims_df = generate_post_policy_data(policy_effective_date, end_date, tenant_id)
        success, ingestion_id = load_data_to_target_model_via_pipeline(claims_df, tenant_id)
        if not success:
            print("❌ Failed to load data to target model via ingestion pipeline")
            return 1
        print(f"✅ Data ingested successfully. Ingestion ID: {ingestion_id}")
    else:
        print("\n⏭️  Skipping data generation (using existing data)")
    
    # Step 2: Run impact analysis for each policy
    if not args.skip_impact_analysis:
        print("\n" + "="*60)
        print("Running Impact Analysis for All Policies")
        print("="*60)
        
        policies = get_all_policies()
        print(f"Found {len(policies)} policies")
        
        results = {
            "total_policies": len(policies),
            "analyses_created": 0,
            "observations_created": 0,
            "errors": 0,
        }
        
        for policy in policies:
            policy_id = UUID(policy.get("id") or policy.get("policy_id"))
            policy_name = policy.get("name") or policy.get("policy_name", "Unknown")
            
            print(f"\n📋 Policy: {policy_name} ({policy_id})")
            
            # Run impact analysis
            analysis_id, analysis_result = run_impact_analysis(policy_id, policy_effective_date, UUID(tenant_id))
            
            if analysis_id:
                results["analyses_created"] += 1
                
                # Wait a bit for analysis to complete (if async)
                # In production, would poll status
                import time
                time.sleep(2)
                
                # Create observation from analysis
                observation_id, observation_result = create_observation_from_analysis(
                    policy_id, analysis_id, UUID(tenant_id)
                )
                
                if observation_id:
                    results["observations_created"] += 1
                else:
                    results["errors"] += 1
            else:
                results["errors"] += 1
        
        print("\n" + "="*60)
        print("OBSERVATION ANALYSIS COMPLETE")
        print("="*60)
        print(f"Total policies: {results['total_policies']}")
        print(f"Analyses created: {results['analyses_created']}")
        print(f"Observations created: {results['observations_created']}")
        print(f"Errors: {results['errors']}")
        print("="*60)
        print("\nNext steps:")
        print("  1. View observations in UI: http://localhost:3050/policies")
        print("  2. Compare observed vs predicted impact")
    else:
        print("\n⏭️  Skipping impact analysis")
    
    print("\n✅ Complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
