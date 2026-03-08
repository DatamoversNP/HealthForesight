#!/usr/bin/env python3
"""Diagnostic script to check why observations don't have observed values"""

import sys
from pathlib import Path
import json
from datetime import datetime
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from uepi_api.storage_observations import list_observations
from uepi_api.storage_analyses import get_analysis
from uepi_api.storage_policies import list_policies

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def check_claims_data(tenant_id: UUID):
    """Check if claims data exists in target data model"""
    print("\n" + "="*80)
    print("1. CHECKING CLAIMS DATA")
    print("="*80)
    
    target_data_root = project_root / "apps" / "data" / "target_data_model" / str(tenant_id) / "CLAIMS_LINES"
    claims_file = target_data_root / "claims_lines.csv"
    
    if claims_file.exists():
        print(f"✅ Claims file exists: {claims_file}")
        # Try to get file size
        size_mb = claims_file.stat().st_size / (1024 * 1024)
        print(f"   File size: {size_mb:.2f} MB")
        
        # Try to count lines (first 5 lines)
        try:
            import polars as pl
            df = pl.scan_csv(str(claims_file)).limit(5).collect()
            print(f"   Sample rows available: {len(df)}")
            if not df.is_empty():
                print(f"   Columns: {', '.join(df.columns[:10])}")
                # Check date range
                if "service_date_from" in df.columns:
                    dates = df["service_date_from"]
                    print(f"   Sample dates: {dates.min()} to {dates.max()}")
        except Exception as e:
            print(f"   ⚠️  Could not read claims file: {e}")
    else:
        print(f"❌ Claims file NOT FOUND: {claims_file}")
        print(f"   This means no claims data has been loaded!")
        print(f"   Expected location: {target_data_root}")
        return False
    
    return True


def check_analyses(tenant_id: UUID):
    """Check if analyses have treatment_post metrics"""
    print("\n" + "="*80)
    print("2. CHECKING IMPACT ANALYSES")
    print("="*80)
    
    # Get all policies
    policies = list_policies(tenant_id)
    print(f"Found {len(policies)} policies")
    
    analyses_with_data = 0
    analyses_without_data = 0
    
    for policy in policies[:5]:  # Check first 5 policies
        policy_id = policy.get("id")
        policy_name = policy.get("name", "Unknown")
        
        # Try to find analyses for this policy
        # Note: This is a simplified check - in reality you'd query analyses by policy_id
        print(f"\n  Policy: {policy_name} ({policy_id})")
        
        # Check if we can find analysis results
        analysis_results_dir = project_root / "apps" / "api" / "src" / "data" / "analyses" / str(tenant_id)
        if analysis_results_dir.exists():
            analysis_files = list(analysis_results_dir.glob(f"*{policy_id}*.json"))
            if analysis_files:
                for analysis_file in analysis_files[:1]:  # Check first analysis
                    try:
                        with open(analysis_file) as f:
                            analysis_result = json.load(f)
                        
                        metrics = analysis_result.get("metrics", {})
                        treatment_post = metrics.get("treatment_post", {})
                        
                        if treatment_post and treatment_post.get("utilization_per_1k", 0) > 0:
                            print(f"    ✅ Analysis has treatment_post data:")
                            print(f"       Utilization: {treatment_post.get('utilization_per_1k', 0):.2f}")
                            print(f"       Cost PMPM: {treatment_post.get('allowed_pmpm', 0):.2f}")
                            analyses_with_data += 1
                        else:
                            print(f"    ❌ Analysis has NO treatment_post data")
                            print(f"       Metrics keys: {list(metrics.keys())}")
                            analyses_without_data += 1
                    except Exception as e:
                        print(f"    ⚠️  Error reading analysis: {e}")
            else:
                print(f"    ⚠️  No analysis files found for this policy")
        else:
            print(f"    ⚠️  Analysis results directory not found: {analysis_results_dir}")
    
    print(f"\n  Summary: {analyses_with_data} analyses with data, {analyses_without_data} without")
    return analyses_with_data > 0


def check_observations(tenant_id: UUID):
    """Check if observations have observed values"""
    print("\n" + "="*80)
    print("3. CHECKING OBSERVATIONS")
    print("="*80)
    
    observations = list_observations(tenant_id)
    print(f"Found {len(observations)} observations")
    
    observations_with_data = 0
    observations_without_data = 0
    
    for obs in observations[:10]:  # Check first 10
        obs_id = obs.get("observation_id")
        metrics = obs.get("metrics", {})
        comparisons = obs.get("comparisons", {})
        
        utilization = metrics.get("utilization_per_1k", 0)
        cost = metrics.get("cost_pmpm") or metrics.get("cost_per_member", 0)
        
        vs_baseline = comparisons.get("vs_baseline", {})
        vs_predicted = comparisons.get("vs_predicted", {})
        
        if utilization > 0 or cost > 0:
            print(f"\n  ✅ Observation {obs_id[:8]}... has data:")
            print(f"     Utilization: {utilization:.2f}")
            print(f"     Cost PMPM: {cost:.2f}")
            print(f"     vs_baseline.observed_utilization_per_1k: {vs_baseline.get('observed_utilization_per_1k', 'N/A')}")
            print(f"     vs_predicted.observed_utilization: {vs_predicted.get('observed_utilization', 'N/A')}")
            observations_with_data += 1
        else:
            print(f"\n  ❌ Observation {obs_id[:8]}... has NO data:")
            print(f"     Metrics: {metrics}")
            observations_without_data += 1
    
    print(f"\n  Summary: {observations_with_data} observations with data, {observations_without_data} without")
    return observations_with_data > 0


def main():
    print("="*80)
    print("OBSERVATION DATA DIAGNOSTIC")
    print("="*80)
    print(f"Tenant ID: {DEFAULT_TENANT_ID}")
    print(f"Project Root: {project_root}")
    
    # Check 1: Claims data
    has_claims = check_claims_data(DEFAULT_TENANT_ID)
    
    # Check 2: Analyses
    has_analyses = check_analyses(DEFAULT_TENANT_ID)
    
    # Check 3: Observations
    has_observations = check_observations(DEFAULT_TENANT_ID)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY & RECOMMENDATIONS")
    print("="*80)
    
    if not has_claims:
        print("\n❌ PROBLEM: No claims data found!")
        print("   SOLUTION: Run the daily job to generate/load claims data:")
        print("   - POST /api/v1/jobs/daily-data-and-observations")
        print("   - Or run: scripts/daily_post_policy_job.py")
    
    if not has_analyses:
        print("\n❌ PROBLEM: Analyses don't have treatment_post data!")
        print("   SOLUTION: Run impact analyses on policies with actual claims data:")
        print("   - POST /api/v1/analyses/impact")
        print("   - Make sure claims data exists first")
    
    if not has_observations:
        print("\n❌ PROBLEM: Observations don't have observed values!")
        print("   SOLUTION: Create observations from analyses that have actual data:")
        print("   - POST /api/v1/observations/from-analysis/{analysis_id}")
        print("   - Or run the daily job with run_observations=true")
    
    if has_claims and has_analyses and has_observations:
        print("\n✅ All checks passed! Observations should have data.")
    else:
        print("\n⚠️  Some checks failed. Follow the solutions above.")


if __name__ == "__main__":
    main()
