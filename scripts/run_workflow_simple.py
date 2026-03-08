#!/usr/bin/env python3
"""
Simple workflow script that uses API endpoints.
Make sure the API server is running before executing this script.

Usage:
    python3 scripts/run_workflow_simple.py
"""
import requests
import time
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8000/api/v1"

def make_request(method, endpoint, **kwargs):
    """Make API request with error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=300, **kwargs)
        elif method.upper() == "POST":
            response = requests.post(url, timeout=300, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API server at {API_BASE_URL}")
        print("   Make sure the API server is running: cd apps/api && python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error {e.response.status_code}: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def step1_daily_job():
    """Step 1: Run daily job"""
    print("\n🔄 Step 1: Running daily job (generate data + load to database)...")
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"   Target date: {yesterday}")
    
    result = make_request("POST", "/jobs/daily-data-and-observations", 
                        params={"target_date": yesterday, "run_observations": False})
    
    if not result:
        return False
    
    job_id = result.get("job_id")
    print(f"   ✅ Job started: {job_id}")
    print("   ⏳ Waiting for job to complete...")
    
    # Poll for completion
    max_wait = 600
    wait_time = 0
    while wait_time < max_wait:
        time.sleep(5)
        wait_time += 5
        
        status = make_request("GET", f"/jobs/daily-data-and-observations/status/{job_id}")
        if status:
            status_val = status.get("status", "").upper()
            message = status.get("message", "")
            print(f"   Status: {status_val} - {message}")
            
            if status_val in ["COMPLETED", "SUCCESS"]:
                print("   ✅ Daily job completed")
                return True
            elif status_val in ["FAILED", "ERROR"]:
                print(f"   ❌ Daily job failed: {status.get('error', message)}")
                return False
    
    print("   ⏰ Job timed out")
    return False

def step2_create_baselines():
    """Step 2: Create baselines for all policies"""
    print("\n📊 Step 2: Creating baselines for all policies...")
    
    # Get all policies
    policies = make_request("GET", "/policies")
    if not policies:
        return {"success": 0, "total": 0}
    
    print(f"   Found {len(policies)} policies")
    
    # Refresh general baseline
    print("   Refreshing general baseline...")
    general_result = make_request("POST", "/baselines/refresh",
                                 json={"baseline_type": "ROLLING", "window_months": 12, "refresh_reason": "MANUAL"})
    if general_result:
        print(f"   ✅ General baseline: {general_result.get('baseline_id')}")
    else:
        print("   ⚠️  General baseline refresh failed or no data available")
    
    # Refresh policy-specific baselines
    success = 0
    for policy in policies:
        policy_id = policy.get("id")
        policy_name = policy.get("name", "Unknown")
        
        print(f"   Creating baseline for: {policy_name}...")
        result = make_request("POST", "/baselines/refresh",
                             json={"policy_id": policy_id, "baseline_type": "ROLLING", 
                                  "window_months": 12, "refresh_reason": "MANUAL"})
        if result:
            print(f"      ✅ Baseline created: {result.get('baseline_id')}")
            success += 1
        else:
            print(f"      ⚠️  Baseline creation failed or no data available")
        
        time.sleep(0.5)
    
    print(f"\n   ✅ Baselines: {success}/{len(policies)} policies")
    return {"success": success, "total": len(policies)}

def step3_create_observations():
    """Step 3: Create observations for all policies"""
    print("\n📈 Step 3: Creating observations for all policies...")
    
    # Complete pending analyses first
    print("   Completing pending analyses...")
    complete_result = make_request("POST", "/analyses/complete-all-pending")
    if complete_result:
        print(f"   ✅ Completed {complete_result.get('completed', 0)} analyses")
    
    # Get all policies
    policies = make_request("GET", "/policies")
    if not policies:
        return {"created": 0, "failed": 0}
    
    # Get all analyses
    analyses = make_request("GET", "/analyses", params={"analysis_type": "IMPACT", "limit": 1000})
    if not analyses:
        print("   ⚠️  No analyses found")
        return {"created": 0, "failed": 0}
    
    # Filter completed analyses
    completed_analyses = [a for a in analyses if a.get("status") == "COMPLETED"]
    print(f"   Found {len(completed_analyses)} completed analyses")
    
    # Get existing observations
    observations = make_request("GET", "/observations")
    existing_analysis_ids = set()
    if observations:
        for obs in observations:
            if obs.get("analysis_id"):
                existing_analysis_ids.add(obs["analysis_id"])
        print(f"   Found {len(observations)} existing observations")
    
    created = 0
    failed = 0
    skipped = 0
    
    for analysis in completed_analyses:
        analysis_id = analysis.get("id")
        policy_id = analysis.get("policy_id")
        
        if analysis_id in existing_analysis_ids:
            skipped += 1
            continue
        
        policy_name = "Unknown"
        for p in policies:
            if str(p.get("id")) == str(policy_id):
                policy_name = p.get("name", "Unknown")
                break
        
        print(f"   Creating observation for {policy_name}...")
        result = make_request("POST", f"/observations/from-analysis/{analysis_id}",
                             params={"policy_id": policy_id})
        
        if result:
            print(f"      ✅ Created: {result.get('observation_id')}")
            created += 1
        else:
            print(f"      ❌ Failed")
            failed += 1
        
        time.sleep(0.5)
    
    print(f"\n   ✅ Observations: {created} created, {skipped} skipped, {failed} failed")
    return {"created": created, "skipped": skipped, "failed": failed}

def main():
    print("=" * 80)
    print("🚀 COMPLETE WORKFLOW AUTOMATION")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Check API connection
    health = make_request("GET", "/health")
    if not health:
        print("❌ Cannot connect to API server. Please start it first:")
        print("   cd apps/api && python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    print("✅ Connected to API server")
    
    # Run steps
    step1_result = step1_daily_job()
    step2_result = step2_create_baselines()
    step3_result = step3_create_observations()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 WORKFLOW SUMMARY")
    print("=" * 80)
    print(f"Daily Job: {'✅ Success' if step1_result else '❌ Failed'}")
    print(f"Baselines: {step2_result.get('success', 0)}/{step2_result.get('total', 0)} policies")
    print(f"Observations: {step3_result.get('created', 0)} created, {step3_result.get('skipped', 0)} skipped, {step3_result.get('failed', 0)} failed")
    print(f"\nCompleted at: {datetime.now().isoformat()}")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
