#!/usr/bin/env python3
"""Create impact analyses and observations for all policies"""
import sys
import os
from pathlib import Path
from uuid import UUID
import requests
import time
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))

# API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
HEADERS = {
    "Authorization": "Bearer dev-token-123",
    "Content-Type": "application/json",
}


def get_all_policies() -> List[Dict[str, Any]]:
    """Get all policies"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/policies",
            headers=HEADERS,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        # Handle both list and {items: []} response formats
        return data if isinstance(data, list) else data.get("items", [])
    except Exception as e:
        print(f"❌ Error fetching policies: {e}")
        return []


def get_policy_analyses(policy_id: str) -> List[Dict[str, Any]]:
    """Get all impact analyses for a policy (filter client-side; API doesn't filter by policy_id)"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/analyses",
            headers=HEADERS,
            params={"analysis_type": "IMPACT", "limit": 500},
            timeout=30,
        )
        response.raise_for_status()
        analyses = response.json()
        if not isinstance(analyses, list):
            return []
        # Filter by policy_id (API returns all IMPACT analyses for tenant)
        return [a for a in analyses if str(a.get("policy_id", "")) == str(policy_id)]
    except Exception as e:
        print(f"   ⚠️  Error fetching analyses for policy {policy_id}: {e}")
        return []


def get_policy_details(policy_id: str) -> Dict[str, Any] | None:
    """Fetch policy details for scope/filters"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/policies/{policy_id}",
            headers=HEADERS,
            timeout=15,
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def create_impact_analysis(policy_id: str, policy: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    """Create an impact analysis for a policy (matches frontend flow)"""
    # Get policy scope for treatment_filters (like frontend)
    scope = {}
    if policy:
        scope = policy.get("scope") or policy.get("metadata", {}).get("scope") or {}
    
    lob = scope.get("lob") or ["COMMERCIAL"]
    markets = scope.get("markets") or []
    network = scope.get("network") or []
    in_network_only = "IN" in network if isinstance(network, list) else bool(network)
    
    treatment_filters = {
        "lob": lob if isinstance(lob, list) else [lob],
        "markets": markets if isinstance(markets, list) else [markets] if markets else [],
        "in_network_only": in_network_only,
    }
    
    analysis_data = {
        "policy_id": policy_id,
        "treatment_filters": treatment_filters,
        "control_filters": None,
        "matching_strategy": "PROPENSITY_SCORE",
        "pre_window_months": 6,
        "post_window_months": 6,
        "run_substitution": False,
        "run_provider_segmentation": False,
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyses/impact",
            headers=HEADERS,
            json=analysis_data,
            timeout=60,
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            error_detail = response.text[:500]
            print(f"   ⚠️  Analysis creation failed: {response.status_code}")
            print(f"      {error_detail}")
            return None
    except Exception as e:
        print(f"   ⚠️  Error creating analysis: {str(e)[:200]}")
        return None


def wait_for_analysis_completion(analysis_id: str, max_wait_seconds: int = 300) -> bool:
    """Wait for analysis to complete"""
    print(f"   ⏳ Waiting for analysis {analysis_id} to complete...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        try:
            response = requests.get(
                f"{API_BASE_URL}/analyses/{analysis_id}",
                headers=HEADERS,
                timeout=30,
            )
            if response.status_code == 200:
                analysis = response.json()
                status = analysis.get("status")
                
                if status == "COMPLETED":
                    print(f"   ✅ Analysis completed!")
                    return True
                elif status == "FAILED":
                    print(f"   ❌ Analysis failed!")
                    return False
                else:
                    # Still running
                    elapsed = int(time.time() - start_time)
                    print(f"   ⏳ Status: {status} (waited {elapsed}s)...", end="\r")
                    time.sleep(5)
            else:
                print(f"   ⚠️  Error checking analysis status: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ⚠️  Error checking analysis: {e}")
            return False
    
    print(f"   ⏰ Timeout waiting for analysis to complete")
    return False


def create_observation_from_analysis(analysis_id: str, policy_id: str) -> Dict[str, Any] | None:
    """Create observation from impact analysis (same flow as frontend)"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/observations/from-analysis/{analysis_id}",
            headers=HEADERS,
            params={"policy_id": policy_id},
            timeout=180,
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            error_detail = response.text[:500]
            print(f"   ⚠️  Observation creation failed: {response.status_code}")
            print(f"      {error_detail}")
            return None
    except Exception as e:
        print(f"   ⚠️  Error creating observation: {str(e)[:200]}")
        return None


def main():
    print("\n" + "="*60)
    print("Creating Impact Analyses and Observations for All Policies")
    print("="*60)
    
    # Get all policies
    print("\n📋 Fetching all policies...")
    policies = get_all_policies()
    
    if not policies:
        print("❌ No policies found")
        return
    
    print(f"✅ Found {len(policies)} policies")
    
    # Process each policy
    total_analyses_created = 0
    total_observations_created = 0
    total_failed = 0
    total_skipped = 0
    
    for i, policy in enumerate(policies, 1):
        policy_id = policy.get("id") or policy.get("policy_id")
        policy_name = policy.get("name", "Unknown")
        
        print(f"\n[{i}/{len(policies)}] Processing policy: {policy_name} ({policy_id})")
        
        # Check existing analyses
        analyses = get_policy_analyses(policy_id)
        completed_analyses = [a for a in analyses if a.get("status") == "COMPLETED"]
        
        if completed_analyses:
            print(f"   ✅ Found {len(completed_analyses)} completed analysis(es)")
            # Use the most recent completed analysis
            latest_analysis = completed_analyses[0]
            analysis_id = latest_analysis.get("id")
        else:
            # Create new analysis
            print(f"   🚀 Creating new impact analysis...")
            policy_details = get_policy_details(policy_id)
            analysis = create_impact_analysis(policy_id, policy_details)
            
            if not analysis:
                print(f"   ❌ Failed to create analysis")
                total_failed += 1
                continue
            
            analysis_id = analysis.get("id")
            total_analyses_created += 1
            print(f"   ✅ Analysis created: {analysis_id}")
            
            # Wait for completion (with timeout)
            if not wait_for_analysis_completion(analysis_id, max_wait_seconds=60):
                print(f"   ⏭️  Analysis not completed yet - skipping observation creation")
                total_skipped += 1
                continue
        
        # Check if observation already exists for this policy
        try:
            response = requests.get(
                f"{API_BASE_URL}/observations",
                headers=HEADERS,
                params={"policy_id": policy_id},
                timeout=30,
            )
            if response.status_code == 200:
                existing_observations = response.json()
                if existing_observations:
                    print(f"   ✅ Observation already exists - skipping")
                    total_skipped += 1
                    continue
        except Exception as e:
            print(f"   ⚠️  Error checking existing observations: {e}")
        
        # Create observation
        print(f"   🚀 Creating observation...")
        observation = create_observation_from_analysis(analysis_id, policy_id)
        
        if observation:
            observation_id = observation.get("observation_id")
            print(f"   ✅ Observation created: {observation_id}")
            total_observations_created += 1
        else:
            print(f"   ❌ Failed to create observation")
            total_failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"📊 Analyses created: {total_analyses_created}")
    print(f"✅ Observations created: {total_observations_created}")
    print(f"⏭️  Skipped: {total_skipped}")
    print(f"❌ Failed: {total_failed}")
    print(f"📊 Total policies: {len(policies)}")
    print("="*60)


if __name__ == "__main__":
    main()
