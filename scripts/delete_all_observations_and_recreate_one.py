#!/usr/bin/env python3
"""Delete all existing observations and recreate one for a single policy"""
import requests
from uuid import UUID
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer dev-token-123", "Content-Type": "application/json"}

def delete_all_observations():
    """Delete all observations using API endpoint"""
    try:
        # First, count existing observations
        observations = requests.get(
            f"{API_BASE}/observations",
            headers=HEADERS,
            timeout=60
        ).json()
        count = len(observations) if isinstance(observations, list) else 0
        print(f"📊 Found {count} existing observations")
        
        if count == 0:
            print("✅ No observations to delete")
            return 0
        
        # Delete all observations via API
        response = requests.delete(
            f"{API_BASE}/observations/all",
            headers=HEADERS,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            deleted = result.get('deleted', 0)
            print(f"✅ Deleted {deleted} observations")
            return deleted
        else:
            print(f"❌ Failed to delete: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return 0
            
    except Exception as e:
        print(f"❌ Error deleting observations: {e}")
        import traceback
        traceback.print_exc()
        return 0

def get_policy_with_analysis():
    """Get a policy that has a baseline analysis"""
    # Get all policies
    policies = requests.get(f"{API_BASE}/policies", headers=HEADERS, timeout=60).json()
    active_policies = [p for p in policies if p.get('status') == 'ACTIVE']
    
    if not active_policies:
        print("❌ No active policies found")
        return None, None
    
    # Get baseline analyses
    analyses = requests.get(
        f"{API_BASE}/analyses",
        headers=HEADERS,
        params={'analysis_type': 'BASELINE'},
        timeout=60
    ).json()
    
    # Find a policy with a COMPLETED baseline analysis
    for policy in active_policies:
        policy_id = str(policy.get('id') or policy.get('policy_id'))
        
        # Find a COMPLETED baseline analysis for this policy
        for analysis in analyses:
            if analysis.get('policy_id') == policy_id and analysis.get('status') == 'COMPLETED':
                return policy, analysis
    
    # If no policy-specific analysis found, try to find a general one
    general_analyses = [a for a in analyses if not a.get('policy_id') and a.get('status') == 'COMPLETED']
    if general_analyses and active_policies:
        return active_policies[0], general_analyses[0]
    
    print("❌ No COMPLETED baseline analyses found")
    return None, None

def create_observation_for_policy(policy, analysis):
    """Create an observation for a policy using an analysis"""
    policy_id = str(policy.get('id') or policy.get('policy_id'))
    analysis_id = analysis.get('id')
    policy_name = policy.get('name', 'Unknown Policy')
    
    print(f"\n📋 Creating observation for:")
    print(f"   Policy: {policy_name[:60]}")
    print(f"   Policy ID: {policy_id}")
    print(f"   Analysis ID: {analysis_id}")
    
    try:
        # Create observation from analysis
        response = requests.post(
            f"{API_BASE}/observations/from-analysis/{analysis_id}",
            headers=HEADERS,
            params={'policy_id': policy_id},
            timeout=300  # 5 minutes
        )
        
        if response.status_code == 201:
            observation = response.json()
            print(f"✅ Observation created successfully!")
            print(f"   Observation ID: {observation.get('observation_id', 'N/A')}")
            print(f"   Policy ID: {observation.get('policy_id', 'N/A')}")
            print(f"   Status: Created")
            return True
        else:
            print(f"❌ Failed to create observation: {response.status_code}")
            print(f"   Error: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating observation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 70)
    print("DELETE ALL OBSERVATIONS AND RECREATE ONE")
    print("=" * 70)
    print()
    
    # Step 1: Delete all existing observations
    print("Step 1: Deleting all existing observations...")
    deleted_count = delete_all_observations()
    print()
    
    # Step 2: Get a policy with a baseline analysis
    print("Step 2: Finding a policy with baseline analysis...")
    policy, analysis = get_policy_with_analysis()
    
    if not policy or not analysis:
        print("❌ Cannot proceed: No policy with baseline analysis found")
        return
    
    print(f"✅ Found policy: {policy.get('name', 'Unknown')[:60]}")
    print()
    
    # Step 3: Create observation for the policy
    print("Step 3: Creating observation for selected policy...")
    success = create_observation_for_policy(policy, analysis)
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ Deleted: {deleted_count} observations")
    if success:
        print(f"✅ Created: 1 new observation")
        print(f"   Policy: {policy.get('name', 'Unknown')[:60]}")
    else:
        print(f"❌ Failed to create new observation")
    print()

if __name__ == "__main__":
    main()
