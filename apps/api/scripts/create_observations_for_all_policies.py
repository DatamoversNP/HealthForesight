#!/usr/bin/env python3
"""Create observations for all policies that have impact analyses"""
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
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching policies: {e}")
        return []


def get_policy_analyses(policy_id: str) -> List[Dict[str, Any]]:
    """Get all impact analyses for a policy"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/analyses",
            headers=HEADERS,
            params={"policy_id": policy_id, "analysis_type": "IMPACT"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"   ⚠️  Error fetching analyses for policy {policy_id}: {e}")
        return []


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
            print(f"   ⚠️  Observation creation failed: {response.status_code}")
            print(f"      {error_detail}")
            return None
    except Exception as e:
        print(f"   ⚠️  Error creating observation: {str(e)[:200]}")
        return None


def main():
    print("\n" + "="*60)
    print("Creating Observations for All Policies")
    print("="*60)
    
    # Get all policies
    print("\n📋 Fetching all policies...")
    policies = get_all_policies()
    
    if not policies:
        print("❌ No policies found")
        return
    
    print(f"✅ Found {len(policies)} policies")
    
    # Process each policy
    total_created = 0
    total_failed = 0
    total_skipped = 0
    
    for i, policy in enumerate(policies, 1):
        policy_id = policy.get("id") or policy.get("policy_id")
        policy_name = policy.get("name", "Unknown")
        
        print(f"\n[{i}/{len(policies)}] Processing policy: {policy_name} ({policy_id})")
        
        # Get impact analyses for this policy
        analyses = get_policy_analyses(policy_id)
        
        if not analyses:
            print(f"   ⏭️  No impact analyses found - skipping")
            total_skipped += 1
            continue
        
        # Filter for completed analyses
        completed_analyses = [a for a in analyses if a.get("status") == "COMPLETED"]
        
        if not completed_analyses:
            print(f"   ⏭️  No completed impact analyses found - skipping")
            total_skipped += 1
            continue
        
        print(f"   📊 Found {len(completed_analyses)} completed impact analyses")
        
        # Use the most recent analysis
        latest_analysis = completed_analyses[0]  # Already sorted by created_at desc
        analysis_id = latest_analysis.get("id")
        
        print(f"   🔍 Using analysis: {analysis_id}")
        
        # Check if observation already exists
        try:
            response = requests.get(
                f"{API_BASE_URL}/observations",
                headers=HEADERS,
                params={"policy_id": policy_id, "analysis_id": analysis_id},
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
            total_created += 1
        else:
            print(f"   ❌ Failed to create observation")
            total_failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"✅ Created: {total_created}")
    print(f"⏭️  Skipped: {total_skipped}")
    print(f"❌ Failed: {total_failed}")
    print(f"📊 Total: {len(policies)}")
    print("="*60)


if __name__ == "__main__":
    main()
