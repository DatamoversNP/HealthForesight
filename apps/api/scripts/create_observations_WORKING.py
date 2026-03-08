#!/usr/bin/env python3
"""
WORKING SOLUTION - Uses the from-analysis endpoint which auto-completes analyses
This endpoint already works and I've modified it to handle PENDING analyses.
"""
import requests
import time
from uuid import UUID

API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer dev-token-123", "Content-Type": "application/json"}

def wait_for_server(max_wait=60):
    """Wait for server to be ready"""
    print("⏳ Waiting for API server...")
    for i in range(max_wait):
        try:
            resp = requests.get(f"{API_BASE_URL}/policies", headers=HEADERS, timeout=2)
            if resp.status_code == 200:
                print("✅ Server is ready!")
                return True
        except:
            pass
        if i % 5 == 0:
            print(f"   Still waiting... ({i}/{max_wait}s)")
        time.sleep(1)
    return False

def main():
    print("\n" + "="*70)
    print("CREATE OBSERVATIONS - WORKING SOLUTION")
    print("="*70)
    
    # Wait for server
    if not wait_for_server():
        print("\n❌ Server not responding. Please start it manually:")
        print("   cd apps/api/src")
        print("   python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    print("\n📊 Step 1: Getting policies and analyses...")
    
    # Get policies
    try:
        policies_resp = requests.get(f"{API_BASE_URL}/policies", headers=HEADERS, timeout=30)
        policies_resp.raise_for_status()
        policies = policies_resp.json()
        print(f"✅ Found {len(policies)} policies")
    except Exception as e:
        print(f"❌ Error getting policies: {e}")
        return
    
    # Get analyses
    try:
        analyses_resp = requests.get(f"{API_BASE_URL}/analyses", headers=HEADERS, params={"analysis_type": "IMPACT"}, timeout=30)
        analyses_resp.raise_for_status()
        analyses = analyses_resp.json()
        pending = [a for a in analyses if a.get("status") == "PENDING"]
        print(f"✅ Found {len(pending)} pending analyses")
    except Exception as e:
        print(f"❌ Error getting analyses: {e}")
        return
    
    # Check existing observations
    try:
        obs_resp = requests.get(f"{API_BASE_URL}/observations", headers=HEADERS, timeout=30)
        existing = obs_resp.json() if obs_resp.status_code == 200 else []
        existing_policies = {obs.get("policy_id") for obs in existing if obs.get("policy_id")}
        print(f"✅ Found {len(existing)} existing observations")
    except:
        existing_policies = set()
    
    if len(existing) >= len(policies):
        print(f"\n✅ All policies already have observations!")
        return
    
    # Group analyses by policy
    policy_analyses = {}
    for a in pending:
        pid = a.get("policy_id")
        if pid not in policy_analyses:
            policy_analyses[pid] = []
        policy_analyses[pid].append(a)
    
    print(f"\n🚀 Step 2: Creating observations...")
    print(f"   Using /observations/from-analysis endpoint (auto-completes analyses)\n")
    
    created = 0
    failed = 0
    skipped = 0
    
    for i, (policy_id, analyses_list) in enumerate(policy_analyses.items(), 1):
        # Skip if exists
        if policy_id in existing_policies:
            skipped += 1
            continue
        
        analysis = analyses_list[0]
        analysis_id = analysis.get("id")
        
        # Get policy name
        policy = next((p for p in policies if (p.get("id") or p.get("policy_id")) == policy_id), None)
        policy_name = policy.get("name", "Unknown")[:45] if policy else "Unknown"
        
        print(f"[{i}/{len(policy_analyses)}] {policy_name}")
        
        # Use the from-analysis endpoint (it auto-completes PENDING analyses)
        try:
            resp = requests.post(
                f"{API_BASE_URL}/observations/from-analysis/{analysis_id}",
                headers=HEADERS,
                params={"policy_id": policy_id},
                timeout=120
            )
            
            if resp.status_code == 201:
                obs = resp.json()
                obs_id = obs.get('observation_id', 'unknown')[:8]
                print(f"   ✅ Created: {obs_id}...")
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
    print("SUMMARY")
    print("="*70)
    print(f"✅ Created: {created}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total policies: {len(policy_analyses)}")
    print("="*70)
    
    if created > 0:
        print(f"\n🎉 {created} observations created!")
        print("   Refresh the web page to see them!")
    elif failed > 0:
        print(f"\n⚠️  {failed} failed. Check server logs.")

if __name__ == "__main__":
    main()
