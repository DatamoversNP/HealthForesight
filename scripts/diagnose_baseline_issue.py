#!/usr/bin/env python3
"""
Diagnostic script to understand why baseline can't find data
"""
import requests
from datetime import date, timedelta
from uuid import UUID

API_BASE_URL = "http://localhost:8000/api/v1"
TENANT_ID = "00000000-0000-0000-0000-000000000001"
POLICY_ID = "6744b13c-12dd-4f71-8884-0f4944205015"

def main():
    print("="*80)
    print("🔍 BASELINE DIAGNOSTIC")
    print("="*80)
    
    # Get policy details
    response = requests.get(f"{API_BASE_URL}/policies", timeout=10)
    policies = response.json() if response.status_code == 200 else []
    policy = next((p for p in policies if str(p.get('id')) == POLICY_ID), None)
    
    if not policy:
        print(f"❌ Policy {POLICY_ID} not found")
        return
    
    scope = policy.get('scope', {})
    levers = policy.get('policy_levers', [])
    codes = []
    for lever in levers:
        params = lever.get('parameters', {})
        if params.get('codes'):
            codes.extend(params['codes'])
    
    print(f"\n📋 Policy Requirements:")
    print(f"   LOB: {scope.get('lob')}")
    print(f"   Markets: {scope.get('markets')}")
    print(f"   Codes: {codes}")
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    print(f"\n📅 Baseline Date Range: {start_date} to {end_date}")
    
    # Generate test data with EXACT match
    print(f"\n🧪 Generating test data with EXACT match...")
    test_date = end_date - timedelta(days=1)
    
    # Generate policy-scoped data
    response = requests.post(
        f"{API_BASE_URL}/data/generate-claims/policy-scoped?policy_id={POLICY_ID}",
        json={'target_date': test_date.isoformat(), 'member_count': 1000, 'claims_per_member': 1.5},
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Generated: {result.get('claims_loaded', 0)} claims for {test_date}")
    else:
        print(f"   ❌ Generation failed: {response.status_code}")
    
    # Wait a moment
    import time
    time.sleep(2)
    
    # Try baseline with shorter window (just last month)
    print(f"\n🧪 Testing baseline with 1-month window...")
    response = requests.post(
        f"{API_BASE_URL}/baselines/refresh",
        json={'policy_id': POLICY_ID, 'baseline_type': 'ROLLING', 'window_months': 1, 'refresh_reason': 'TEST'},
        timeout=180
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ SUCCESS! Baseline created")
        metrics = result.get('baseline_metrics', {})
        print(f"   Claims: {metrics.get('total_claims', 0)}, Members: {metrics.get('unique_members', 0)}")
    else:
        print(f"   ❌ Failed: {response.text[:400]}")
    
    # Try without policy filter (general baseline for same window)
    print(f"\n🧪 Testing general baseline with 1-month window...")
    response = requests.post(
        f"{API_BASE_URL}/baselines/refresh",
        json={'baseline_type': 'ROLLING', 'window_months': 1, 'refresh_reason': 'TEST'},
        timeout=180
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ SUCCESS! General baseline created")
        metrics = result.get('baseline_metrics', {})
        print(f"   Claims: {metrics.get('total_claims', 0)}, Members: {metrics.get('unique_members', 0)}")
    else:
        print(f"   ❌ Failed: {response.text[:400]}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
