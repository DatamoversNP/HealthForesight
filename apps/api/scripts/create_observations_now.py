#!/usr/bin/env python3
"""Create observations for all policies with completed analyses - runs automatically"""
import sys
import os
from pathlib import Path
from uuid import UUID
import requests
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))

# API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
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
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching policies: {e}")
        return []


def get_completed_analyses(policy_id: str) -> List[Dict[str, Any]]:
    """Get completed impact analyses for a policy"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/analyses",
            headers=HEADERS,
            params={"policy_id": policy_id, "analysis_type": "IMPACT"},
            timeout=30,
        )
        response.raise_for_status()
        analyses = response.json()
        # Filter for completed only
        return [a for a in analyses if a.get("status") == "COMPLETED"]
    except Exception as e:
        print(f"   ⚠️  Error fetching analyses: {e}")
        return []


def check_existing_observation(policy_id: str, analysis_id: str) -> bool:
    """Check if observation already exists for this analysis"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/observations",
            headers=HEADERS,
            params={"policy_id": policy_id},
            timeout=30,
        )
        if response.status_code == 200:
            observations = response.json()
            # Check if any observation has this analysis_id
            for obs in observations:
                if obs.get("analysis_id") == analysis_id:
                    return True
        return False
    except Exception:
        return False


def create_observation_from_analysis(analysis_id: str, policy_id: str) -> Dict[str, Any] | None:
    """Create observation from impact analysis"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/observations/from-analysis/{analysis_id}",
            headers=HEADERS,
            params={"policy_id": policy_id},
            timeout=120,
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            error_detail = response.text[:500]
            print(f"   ⚠️  Failed: {response.status_code} - {error_detail}")
            return None
    except Exception as e:
        print(f"   ⚠️  Error: {str(e)[:200]}")
        return None


def main():
    print("\n" + "="*60)
    print("Creating Observations for All Policies (Auto)")
    print("="*60)
    
    # Get all policies
    print("\n📋 Fetching policies...")
    policies = get_all_policies()
    
    if not policies:
        print("❌ No policies found")
        return
    
    print(f"✅ Found {len(policies)} policies\n")
    
    # Process each policy
    total_created = 0
    total_skipped = 0
    total_failed = 0
    total_no_analyses = 0
    
    for i, policy in enumerate(policies, 1):
        policy_id = policy.get("id") or policy.get("policy_id")
        policy_name = policy.get("name", "Unknown")
        
        print(f"[{i}/{len(policies)}] {policy_name[:50]}")
        
        # Get completed analyses
        completed_analyses = get_completed_analyses(policy_id)
        
        if not completed_analyses:
            print(f"   ⏭️  No completed analyses")
            total_no_analyses += 1
            continue
        
        # Use the most recent completed analysis
        latest_analysis = completed_analyses[0]
        analysis_id = latest_analysis.get("id")
        
        # Check if observation already exists
        if check_existing_observation(policy_id, analysis_id):
            print(f"   ✅ Observation already exists")
            total_skipped += 1
            continue
        
        # Create observation
        print(f"   🚀 Creating observation from analysis {analysis_id[:8]}...")
        observation = create_observation_from_analysis(analysis_id, policy_id)
        
        if observation:
            observation_id = observation.get("observation_id", "unknown")
            print(f"   ✅ Created: {observation_id[:8]}...")
            total_created += 1
        else:
            print(f"   ❌ Failed")
            total_failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"✅ Created: {total_created}")
    print(f"⏭️  Skipped (already exist): {total_skipped}")
    print(f"⏭️  No completed analyses: {total_no_analyses}")
    print(f"❌ Failed: {total_failed}")
    print(f"📊 Total policies: {len(policies)}")
    print("="*60)


if __name__ == "__main__":
    main()
