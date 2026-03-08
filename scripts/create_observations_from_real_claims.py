#!/usr/bin/env python3
"""Create observations from real claims data by running impact analyses"""

import sys
import requests
import time
from uuid import UUID

API_BASE = "http://localhost:8000/api/v1"
AUTH_TOKEN = "dev-token-123"

def get_policies():
    """Get all policies"""
    response = requests.get(
        f"{API_BASE}/policies",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
    )
    if response.status_code == 200:
        return response.json()
    return []

def run_impact_analysis(policy_id, policy_name):
    """Run impact analysis for a policy using real claims data"""
    print(f"\nRunning impact analysis for: {policy_name}")
    
    # Get policy to determine effective date
    policy_response = requests.get(
        f"{API_BASE}/policies/{policy_id}",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
    )
    if policy_response.status_code != 200:
        print(f"  ⚠️  Could not get policy details")
        return None
    
    policy = policy_response.json()
    
    # Try to get effective date from policy version
    effective_date = "2024-12-01"  # Default fallback
    
    # Create impact analysis request
    analysis_data = {
        "policy_id": policy_id,
        "treatment_filters": {
            "lob": ["COMMERCIAL"],
            "markets": ["NYC", "CHICAGO", "LA"]
        },
        "pre_window_months": 6,
        "post_window_months": 1,  # Shorter post period for faster processing
        "matching_strategy": "PROPENSITY_SCORE",
        "run_substitution": False,
        "run_provider_segmentation": False,
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/analyses/impact",
            json=analysis_data,
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=300  # 5 minute timeout for processing
        )
        
        if response.status_code == 201:
            analysis = response.json()
            print(f"  ✅ Analysis created: {analysis['id']}")
            print(f"  Status: {analysis['status']}")
            return analysis['id']
        else:
            print(f"  ❌ Failed to create analysis: {response.status_code}")
            print(f"  Error: {response.text}")
            return None
    except requests.exceptions.Timeout:
        print(f"  ⚠️  Analysis timed out (processing large claims file)")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def create_observation_from_analysis(analysis_id, policy_id):
    """Create observation from completed analysis"""
    print(f"  Creating observation from analysis {analysis_id[:8]}...")
    
    try:
        response = requests.post(
            f"{API_BASE}/observations/from-analysis/{analysis_id}",
            params={"policy_id": policy_id},
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=60
        )
        
        if response.status_code == 201:
            observation = response.json()
            print(f"  ✅ Observation created: {observation['observation_id'][:8]}")
            return observation
        else:
            print(f"  ❌ Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def main():
    print("="*80)
    print("CREATE OBSERVATIONS FROM REAL CLAIMS DATA")
    print("="*80)
    print()
    print("This will:")
    print("  1. Run impact analyses that process real claims data")
    print("  2. Create observations from the analysis results")
    print("  3. Use actual metrics computed from claims files")
    print()
    print("⚠️  Note: This will process a 384MB claims file, which may take time.")
    print()
    
    # Get policies
    print("Step 1: Fetching policies...")
    policies = get_policies()
    print(f"  Found {len(policies)} policies")
    
    if not policies:
        print("  ❌ No policies found")
        return
    
    # Process first 5 policies as a test
    print()
    print("Step 2: Running impact analyses (processing real claims data)...")
    print("  Processing first 5 policies as a test...")
    
    created_observations = []
    for i, policy in enumerate(policies[:5], 1):
        policy_id = policy['id']
        policy_name = policy.get('name', 'Unknown')
        
        print(f"\n[{i}/5] Policy: {policy_name}")
        
        # Run impact analysis (this will process real claims data)
        analysis_id = run_impact_analysis(policy_id, policy_name)
        
        if analysis_id:
            # Wait a bit for analysis to process
            print(f"  Waiting for analysis to process claims data...")
            time.sleep(10)  # Give it time to process
            
            # Create observation
            observation = create_observation_from_analysis(analysis_id, policy_id)
            if observation:
                created_observations.append(observation)
        else:
            print(f"  ⚠️  Skipping observation creation (analysis failed)")
    
    print()
    print("="*80)
    print(f"✅ Created {len(created_observations)} observations from REAL claims data")
    print("="*80)
    print()
    print("These observations now contain:")
    print("  - Real utilization metrics computed from claims")
    print("  - Real cost metrics computed from claims")
    print("  - Actual pre/post period comparisons")
    print()
    print("Refresh your browser to see the updated observations!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
