#!/usr/bin/env python3
"""
Load newly generated post-policy data and run observation analysis

This script:
1. Generates post-policy data (Jan 1-16, 2026)
2. Loads data via ingestion pipeline (directly using processor, not API)
3. Runs impact analysis for each policy
4. Creates observations comparing observed vs predicted vs baseline
"""
import argparse
import sys
import json
import os
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

# Import ingestion and storage modules
from uepi_api.storage_auth import DEFAULT_TENANT_ID
from uepi_api.storage_policies import list_policies
from uepi_common.ingestion.comprehensive_processor import ComprehensiveIngestionProcessor
from uepi_common.data_contracts.manifest import DatasetType


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
    
    # Save to temp file for ingestion
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
        post_policy_claims_df.to_csv(tmp_file.name, index=False)
        tmp_path = tmp_file.name
    
    return post_policy_claims_df, tmp_path


def load_data_via_ingestion_pipeline(file_path: str, tenant_id: UUID):
    """Load data via ingestion pipeline directly (without API)"""
    print("\n" + "="*60)
    print("Loading Data via Ingestion Pipeline")
    print("="*60)
    
    ingestion_id = UUID('00000000-0000-0000-0000-000000000001')  # Use a fixed ID for this run
    
    try:
        processor = ComprehensiveIngestionProcessor(
            tenant_id=tenant_id,
            dataset_type=DatasetType.CLAIMS_LINES,
            source_system="SYNTHETIC_GENERATOR",
            ingestion_id=ingestion_id,
        )
        
        print(f"📤 Processing file: {file_path}")
        result = processor.process_file(
            file_path=file_path,
            auto_detect_schema=True,
        )
        
        if result.get("success"):
            records_valid = result.get("records_valid", 0)
            curated_partitions = result.get("curated_partitions", [])
            
            print(f"✅ Ingestion successful!")
            print(f"   Valid records: {records_valid:,}")
            print(f"   Curated partitions: {len(curated_partitions)}")
            
            if curated_partitions:
                print(f"   Partition URIs:")
                for partition_uri in curated_partitions[:5]:
                    print(f"     - {partition_uri}")
                if len(curated_partitions) > 5:
                    print(f"     ... and {len(curated_partitions) - 5} more")
            
            return True, result
        else:
            print(f"❌ Ingestion failed")
            print(f"   Result: {result}")
            errors = result.get("errors", [])
            warnings = result.get("warnings", [])
            
            if errors:
                print(f"   Errors ({len(errors)}):")
                for i, error in enumerate(errors[:10], 1):
                    print(f"     {i}. {error}")
                if len(errors) > 10:
                    print(f"     ... and {len(errors) - 10} more errors")
            else:
                print(f"   No errors in result dict")
            
            if warnings:
                print(f"   Warnings ({len(warnings)}):")
                for i, warning in enumerate(warnings[:5], 1):
                    print(f"     {i}. {warning}")
            
            return False, result
            
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return False, {"error": str(e)}
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            os.unlink(file_path)


def run_impact_analysis_via_api(policy_id: UUID, policy_effective_date: datetime, tenant_id: UUID, use_api: bool = True):
    """Run impact analysis for a policy via API"""
    import requests
    
    if not use_api:
        print(f"  ⚠️  API server not available - skipping impact analysis for policy {policy_id}")
        return None, None
    
    print(f"  Running impact analysis for policy {policy_id}...")
    
    API_BASE_URL = "http://localhost:8000/api/v1"
    HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer dev-token-123"}
    
    treatment_filters = {
        "lob": ["COMMERCIAL", "MA", "MEDICAID"],
        "markets": ["BOS", "DFW", "NYC"],
        "in_network_only": True,
    }
    
    pre_window_months = 6
    post_window_months = 1  # Only ~16 days available
    
    payload = {
        "policy_id": str(policy_id),
        "treatment_filters": treatment_filters,
        "control_filters": None,
        "matching_strategy": None,
        "pre_window_months": pre_window_months,
        "post_window_months": post_window_months,
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyses/impact",
            headers=HEADERS,
            json=payload,
            timeout=300,
        )
        response.raise_for_status()
        result = response.json()
        
        analysis_id = result.get("id")
        status = result.get("status")
        
        print(f"    ✅ Impact analysis created: {analysis_id}, Status: {status}")
        return analysis_id, result
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Error running impact analysis: {e}")
        return None, None


def create_observation_via_api(policy_id: UUID, analysis_id: UUID, tenant_id: UUID, use_api: bool = True):
    """Create observation from impact analysis result via API"""
    import requests
    
    if not use_api:
        print(f"  ⚠️  API server not available - skipping observation creation")
        return None, None
    
    print(f"    Creating observation from analysis {analysis_id}...")
    
    API_BASE_URL = "http://localhost:8000/api/v1"
    HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer dev-token-123"}
    
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
        return None, None


def check_api_server():
    """Check if API server is running"""
    try:
        import requests
        response = requests.get("http://localhost:8000/api/v1/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def main():
    parser = argparse.ArgumentParser(description="Load post-policy data and run observation analysis")
    parser.add_argument("--policy-date", type=str, default="2026-01-01", help="Policy effective date (default: 2026-01-01)")
    parser.add_argument("--end-date", type=str, default=None, help="End date for data generation (default: today)")
    parser.add_argument("--tenant-id", type=str, default=str(DEFAULT_TENANT_ID), help="Tenant ID")
    parser.add_argument("--skip-impact-analysis", action="store_true", help="Skip impact analysis (only generate and load data)")
    
    args = parser.parse_args()
    
    # Parse dates
    policy_effective_date = datetime.fromisoformat(args.policy_date)
    end_date = datetime.fromisoformat(args.end_date) if args.end_date else datetime.now()
    tenant_id = UUID(args.tenant_id)
    
    print("\n" + "="*60)
    print("POST-POLICY DATA GENERATION & OBSERVATION ANALYSIS")
    print("="*60)
    print(f"Policy effective date: {policy_effective_date.date()}")
    print(f"End date: {end_date.date()}")
    print(f"Tenant ID: {tenant_id}")
    print("="*60)
    
    # Check API server
    api_available = check_api_server()
    if api_available:
        print("✅ API server is running")
    else:
        print("⚠️  API server is not running - will only generate and load data")
        print("   To run impact analysis, start API server: cd apps/api && python -m uvicorn uepi_api.main:app --reload")
    
    # Step 1: Generate post-policy data
    print("\n" + "="*60)
    print("STEP 1: Generating Post-Policy Data")
    print("="*60)
    
    claims_df, temp_file_path = generate_post_policy_data(policy_effective_date, end_date, str(tenant_id))
    
    # Step 2: Load data via ingestion pipeline
    print("\n" + "="*60)
    print("STEP 2: Loading Data via Ingestion Pipeline")
    print("="*60)
    
    success, ingestion_result = load_data_via_ingestion_pipeline(temp_file_path, tenant_id)
    
    if not success:
        print("❌ Failed to load data via ingestion pipeline")
        return 1
    
    # Step 3: Run impact analysis and create observations (if API available)
    if not args.skip_impact_analysis and api_available:
        print("\n" + "="*60)
        print("STEP 3: Running Impact Analysis & Creating Observations")
        print("="*60)
        
        policies = list_policies(tenant_id)
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
            analysis_id, analysis_result = run_impact_analysis_via_api(
                policy_id, policy_effective_date, tenant_id, use_api=api_available
            )
            
            if analysis_id:
                results["analyses_created"] += 1
                
                # Wait a bit for analysis to complete (if async)
                import time
                time.sleep(2)
                
                # Create observation from analysis
                observation_id, observation_result = create_observation_via_api(
                    policy_id, analysis_id, tenant_id, use_api=api_available
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
    elif not api_available:
        print("\n⏭️  Skipping impact analysis (API server not available)")
        print("   Start API server and run again to create observations")
    else:
        print("\n⏭️  Skipping impact analysis (--skip-impact-analysis flag)")
    
    print("\n✅ Complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
