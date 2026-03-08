#!/usr/bin/env python3
"""
SIMPLE SOLUTION: Create observations using existing working endpoints
This bypasses the complex endpoint and uses what already works.
"""
import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer dev-token-123", "Content-Type": "application/json"}

def main():
    print("\n" + "="*60)
    print("CREATE OBSERVATIONS - SIMPLE APPROACH")
    print("="*60)
    print("\nStep 1: Get all policies and analyses...")
    
    # Get policies
    policies_resp = requests.get(f"{API_BASE_URL}/policies", headers=HEADERS, timeout=30)
    policies = policies_resp.json()
    print(f"✅ Found {len(policies)} policies")
    
    # Get analyses
    analyses_resp = requests.get(f"{API_BASE_URL}/analyses", headers=HEADERS, params={"analysis_type": "IMPACT"}, timeout=30)
    analyses = analyses_resp.json()
    pending = [a for a in analyses if a.get("status") == "PENDING"]
    print(f"✅ Found {len(pending)} pending analyses")
    
    # Check existing observations
    obs_resp = requests.get(f"{API_BASE_URL}/observations", headers=HEADERS, timeout=30)
    existing = obs_resp.json() if obs_resp.status_code == 200 else []
    existing_policies = {obs.get("policy_id") for obs in existing if obs.get("policy_id")}
    print(f"✅ Found {len(existing)} existing observations")
    
    if len(existing) >= len(policies):
        print(f"\n✅ All policies already have observations!")
        return
    
    print(f"\nStep 2: Creating observations...")
    print(f"   (Using the from-analysis endpoint which auto-completes analyses)\n")
    
    # Group analyses by policy
    policy_analyses = {}
    for a in pending:
        pid = a.get("policy_id")
        if pid not in policy_analyses:
            policy_analyses[pid] = []
        policy_analyses[pid].append(a)
    
    created = 0
    failed = 0
    
    for i, (policy_id, analyses_list) in enumerate(policy_analyses.items(), 1):
        # Skip if exists
        if policy_id in existing_policies:
            continue
        
        analysis = analyses_list[0]
        analysis_id = analysis.get("id")
        
        # Get policy name
        policy = next((p for p in policies if (p.get("id") or p.get("policy_id")) == policy_id), None)
        policy_name = policy.get("name", "Unknown")[:40] if policy else "Unknown"
        
        print(f"[{i}/{len(policy_analyses)}] {policy_name}")
        
        # Use the from-analysis endpoint (it auto-completes PENDING analyses)
        try:
            resp = requests.post(
                f"{API_BASE_URL}/observations/from-analysis/{analysis_id}",
                headers=HEADERS,
                params={"policy_id": policy_id},
                timeout=60
            )
            
            if resp.status_code == 201:
                obs = resp.json()
                print(f"   ✅ Created: {obs.get('observation_id', 'unknown')[:8]}...")
                created += 1
            else:
                error = resp.text[:150]
                print(f"   ❌ Failed: {resp.status_code}")
                print(f"      {error}")
                failed += 1
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
            failed += 1
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✅ Created: {created}")
    print(f"❌ Failed: {failed}")
    print(f"⏭️  Skipped: {len(existing_policies)} (already exist)")
    print("="*60)
    
    if created > 0:
        print(f"\n🎉 {created} observations created!")
        print("   Refresh the web page to see them!")

if __name__ == "__main__":
    main()
