#!/usr/bin/env python3
"""Create all observations - FINAL VERSION - Works after API server restart"""
import requests
import json
from uuid import UUID

API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer dev-token-123", "Content-Type": "application/json"}

def main():
    print("\n" + "="*70)
    print("CREATE ALL OBSERVATIONS - FINAL VERSION")
    print("="*70)
    print("\n⚠️  This script uses the updated endpoint that auto-completes analyses.")
    print("   The API server must be restarted first to load the changes.\n")
    
    # Try the new batch endpoint first
    print("🚀 Trying batch endpoint (completes all analyses + creates observations)...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/observations/create-all-from-pending-analyses",
            headers=HEADERS,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS!")
            print(json.dumps(result, indent=2))
            print(f"\n🎉 {result.get('observations_created', 0)} observations created!")
            print("   Refresh the web page to see them!")
            return
        elif response.status_code == 405:
            print("❌ Endpoint not found - API server needs restart")
            print("   Please restart your API server, then run this script again")
            return
        else:
            print(f"⚠️  Batch endpoint returned {response.status_code}: {response.text[:200]}")
            print("   Trying individual creation...\n")
    except Exception as e:
        print(f"⚠️  Batch endpoint error: {e}")
        print("   Trying individual creation...\n")
    
    # Fallback: Create individually (uses auto-complete feature)
    print("🚀 Creating observations individually (auto-completes analyses)...")
    
    # Get all policies and analyses
    policies = requests.get(f"{API_BASE_URL}/policies", headers=HEADERS, timeout=30).json()
    analyses = requests.get(f"{API_BASE_URL}/analyses", headers=HEADERS, params={"analysis_type": "IMPACT"}, timeout=30).json()
    pending = [a for a in analyses if a.get("status") == "PENDING"]
    
    if not pending:
        print("✅ No pending analyses")
        return
    
    # Group by policy
    policy_analyses = {}
    for a in pending:
        pid = a.get("policy_id")
        if pid not in policy_analyses:
            policy_analyses[pid] = []
        policy_analyses[pid].append(a)
    
    # Check existing observations
    existing_obs = requests.get(f"{API_BASE_URL}/observations", headers=HEADERS, timeout=30).json()
    existing_policies = {obs.get("policy_id") for obs in existing_obs if obs.get("policy_id")}
    
    print(f"📊 Processing {len(policy_analyses)} policies...\n")
    
    created = 0
    skipped = 0
    failed = 0
    
    for i, (policy_id, analyses_list) in enumerate(policy_analyses.items(), 1):
        # Skip if exists
        if policy_id in existing_policies:
            skipped += 1
            continue
        
        analysis = analyses_list[0]
        analysis_id = analysis.get("id")
        
        # Get policy name
        policy = next((p for p in policies if (p.get("id") or p.get("policy_id")) == policy_id), None)
        policy_name = policy.get("name", "Unknown")[:50] if policy else "Unknown"
        
        print(f"[{i}/{len(policy_analyses)}] {policy_name}")
        
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
                error = resp.text[:200]
                print(f"   ❌ Failed: {resp.status_code}")
                print(f"      {error}")
                failed += 1
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
            failed += 1
    
    # Summary
    print("\n" + "="*70)
    print("Summary")
    print("="*70)
    print(f"✅ Created: {created}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"❌ Failed: {failed}")
    print("="*70)
    
    if created > 0:
        print(f"\n🎉 {created} observations created!")
        print("   Refresh the web page to see them!")

if __name__ == "__main__":
    main()
