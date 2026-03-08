#!/usr/bin/env python3
"""Test policy-specific baseline creation with one policy"""
import requests
import sys
from uuid import UUID

API_BASE_URL = "http://localhost:8000/api/v1"

def test_policy_baseline(policy_id: str):
    """Test creating a baseline for a specific policy"""
    print(f"Testing baseline creation for policy: {policy_id}")
    print("-" * 80)
    
    # Get policy details first
    try:
        response = requests.get(f"{API_BASE_URL}/policies", timeout=10)
        if response.status_code == 200:
            policies = response.json()
            policy = next((p for p in policies if str(p.get("id")) == policy_id), None)
            if policy:
                print(f"Policy Name: {policy.get('name', 'Unknown')}")
                print(f"Policy Status: {policy.get('status', 'Unknown')}")
                scope = policy.get("scope", {})
                print(f"Policy Scope: {scope}")
                # Check both locations for levers
                levers = policy.get("policy_levers", [])
                if not levers:
                    logic = policy.get("logic", {}) or policy.get("policy_logic", {})
                    levers = logic.get("policy_levers", []) or logic.get("levers", [])
                print(f"Policy Levers: {len(levers)} levers")
                for i, lever in enumerate(levers[:3], 1):
                    targets = lever.get("targets", {})
                    parameters = lever.get("parameters", {})
                    print(f"  Lever {i} targets: {targets}")
                    print(f"  Lever {i} parameters: {parameters}")
    except Exception as e:
        print(f"Error getting policy: {e}")
    
    print("\n" + "-" * 80)
    print("Creating baseline...")
    print("-" * 80)
    
    # Try to create baseline
    try:
        response = requests.post(
            f"{API_BASE_URL}/baselines/refresh",
            json={
                "policy_id": policy_id,
                "baseline_type": "ROLLING",
                "window_months": 12,
                "refresh_reason": "TEST"
            },
            timeout=120
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Baseline created successfully!")
            print(f"Baseline ID: {result.get('baseline_id', 'N/A')}")
            print(f"Baseline Type: {result.get('baseline_type', 'N/A')}")
            metrics = result.get('baseline_metrics', {})
            if metrics:
                print(f"Metrics: {len(metrics)} metrics computed")
                print(f"  - Total Claims: {metrics.get('total_claims', 0)}")
                print(f"  - Unique Members: {metrics.get('unique_members', 0)}")
                print(f"  - Utilization per 1k: {metrics.get('util_rate_target_per_1000_mm', 0):.2f}")
        else:
            print(f"\n❌ Baseline creation failed")
            try:
                error_detail = response.json()
                print(f"Error Detail: {error_detail}")
            except:
                print(f"Error Text: {response.text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/test_policy_baseline.py <policy_id>")
        print("\nTo get a policy ID, run:")
        print("  curl http://localhost:8000/api/v1/policies | jq '.[0].id'")
        sys.exit(1)
    
    policy_id = sys.argv[1]
    test_policy_baseline(policy_id)
