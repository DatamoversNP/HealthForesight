#!/usr/bin/env python3
"""
Focused script to:
1. Generate policy-scoped data for last 3 days
2. Create baselines (general + policy-specific)
3. Create observations for all policies

This script is production-ready and safe - only uses POST endpoints for data generation.
"""
import requests
import time
from datetime import datetime, timedelta
from uuid import UUID

API_BASE_URL = "http://localhost:8000/api/v1"

def make_request(method, endpoint, **kwargs):
    """Make API request with error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    
    # Extract timeout from kwargs or use default
    timeout = kwargs.pop('timeout', None)
    if timeout is None:
        timeout = 300 if method.upper() == "POST" else 60  # 5 minutes for POST, 1 minute for GET
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout, **kwargs)
        elif method.upper() == "POST":
            response = requests.post(url, timeout=timeout, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print(f"⏱️  Request timed out after {timeout}s: {endpoint}")
        return {"error": "timeout", "status_code": 408}
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API server at {API_BASE_URL}")
        print("   Please start the API server first:")
        print("   cd apps/api && python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000")
        return None
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if e.response else str(e)
        if e.response.status_code == 400:
            # 400 errors are expected for some cases (e.g., no data for baseline)
            return {"error": error_detail, "status_code": 400}
        print(f"❌ HTTP Error {e.response.status_code}: {error_detail[:200]}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def step1_generate_policy_scoped_data():
    """Step 1: Generate policy-scoped data for baseline window (12 months)"""
    print("\n" + "="*80)
    print("📊 STEP 1: Generating Policy-Scoped Data for Baseline Window")
    print("="*80)
    
    # Get all active policies
    policies = make_request("GET", "/policies")
    if not policies:
        print("   ⚠️  No policies found")
        return False
    
    active_policies = [p for p in policies if p.get("status") == "ACTIVE"]
    print(f"   Found {len(active_policies)} active policies")
    
    if len(active_policies) == 0:
        print("   ⚠️  No active policies found")
        return False
    
    # Calculate baseline window (last 12 months)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)
    print(f"\n   📅 Baseline Window: {start_date} to {end_date} (12 months)")
    print(f"   Generating data across this window with realistic distribution...")
    
    # Generate data for each month in the window (more data in recent months)
    success_count = 0
    current_date = start_date
    months_processed = 0
    
    while current_date <= end_date:
        # Get month boundaries
        month_start = current_date.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
        
        # Don't go past end_date
        if month_end > end_date:
            month_end = end_date
        
        # Calculate weight for this month (more recent = more data)
        months_ago = (end_date.year - month_start.year) * 12 + (end_date.month - month_start.month)
        weight = max(1, 13 - months_ago)  # More weight for recent months (1-12)
        
        # Generate data for 3-5 days per month (distributed across the month)
        days_in_month = (month_end - month_start).days + 1
        sample_days = min(5, max(3, days_in_month // 7))  # 3-5 days per month
        
        print(f"\n   📅 Month {month_start.strftime('%Y-%m')} (weight: {weight}, {sample_days} sample days)...")
        
        month_success = 0
        step = max(1, days_in_month // sample_days)
        
        for day_offset in range(0, days_in_month, step):
            target_date = month_start + timedelta(days=day_offset)
            if target_date > end_date:
                break
            
            # Scale member count by month weight (recent months have more data)
            member_count = int(8000 * (weight / 12))
            policy_member_count = int(1500 * (weight / 12))
            
            # Generate general data
            result = make_request("POST", "/data/generate-claims",
                                 json={"target_date": target_date.strftime("%Y-%m-%d"), 
                                      "member_count": member_count, 
                                      "claims_per_member": 2.0})
            
            if result and result.get("success") and result.get("claims_loaded", 0) > 0:
                month_success += 1
            
            # Generate policy-specific data for first 10 policies (to avoid timeout)
            for i, policy in enumerate(active_policies[:10], 1):
                policy_id = policy.get("id")
                if not policy_id:
                    continue
                
                result = make_request("POST", f"/data/generate-claims/policy-scoped",
                                     params={"policy_id": policy_id},
                                     json={"target_date": target_date.strftime("%Y-%m-%d"), 
                                          "member_count": policy_member_count, 
                                          "claims_per_member": 1.2})
                
                if result and result.get("success"):
                    pass  # Counted separately
                
                time.sleep(0.05)  # Small delay
            
            time.sleep(0.1)  # Small delay between dates
        
        if month_success > 0:
            success_count += month_success
            months_processed += 1
            print(f"      ✅ Generated data for {month_success} days in {month_start.strftime('%Y-%m')}")
        
        # Move to next month
        if month_start.month == 12:
            current_date = month_start.replace(year=month_start.year + 1, month=1)
        else:
            current_date = month_start.replace(month=month_start.month + 1)
    
    print(f"\n   ✅ Data generation: {success_count} date periods across {months_processed} months")
    return success_count > 0

def step2_create_baselines():
    """Step 2: Create baselines (general + policy-specific)"""
    print("\n" + "="*80)
    print("📊 STEP 2: Creating Baselines")
    print("="*80)
    
    # Get all policies
    policies = make_request("GET", "/policies")
    if not policies:
        print("   ⚠️  No policies found")
        return {"success": 0, "total": 0}
    
    active_policies = [p for p in policies if p.get("status") == "ACTIVE"]
    print(f"   Found {len(active_policies)} active policies")
    
    # Create general baseline first
    print("\n   Creating general baseline...")
    print("   (This may take a few minutes with 12 months of data...)")
    general_result = make_request("POST", "/baselines/refresh",
                                 json={"baseline_type": "ROLLING", "window_months": 12, "refresh_reason": "MANUAL"},
                                 timeout=600)  # 10 minutes for baseline computation
    if general_result and general_result.get("baseline_id"):
        print(f"   ✅ General baseline created: {general_result.get('baseline_id')[:8]}...")
        general_success = 1
    elif general_result and general_result.get("status_code") == 408:
        print("   ⏱️  General baseline creation timed out (data may be too large)")
        general_success = 0
    else:
        print("   ⚠️  General baseline creation failed (may not have enough data)")
        general_success = 0
    
    # Create policy-specific baselines
    print(f"\n   Creating policy-specific baselines...")
    policy_success = 0
    for i, policy in enumerate(active_policies, 1):
        policy_id = policy.get("id")
        policy_name = policy.get("name", "Unknown")[:50]
        
        if not policy_id:
            continue
        
        result = make_request("POST", "/baselines/refresh",
                             json={"policy_id": policy_id, "baseline_type": "ROLLING", 
                                  "window_months": 12, "refresh_reason": "MANUAL"},
                             timeout=600)  # 10 minutes per policy baseline
        
        if result and result.get("baseline_id"):
            policy_success += 1
            if i <= 5:  # Show first 5
                print(f"      ✅ Policy {i}: {policy_name[:40]}")
        elif result and result.get("status_code") == 400:
            # Expected - may not have matching data for this policy
            if i <= 5:
                print(f"      ℹ️  Policy {i}: {policy_name[:40]} (no matching data)")
        elif result and result.get("status_code") == 408:
            # Timeout - skip and continue
            if i <= 5:
                print(f"      ⏱️  Policy {i}: {policy_name[:40]} (timeout - skipping)")
        
        if i % 10 == 0:
            print(f"      Progress: {i}/{len(active_policies)} policies processed...")
        
        time.sleep(0.5)  # Slightly longer delay to avoid overwhelming server
    
    print(f"\n   ✅ Baselines: General={general_success}, Policy-specific={policy_success}/{len(active_policies)}")
    return {"general": general_success, "policy_specific": policy_success, "total": len(active_policies)}

def step3_create_observations():
    """Step 3: Create observations for all policies"""
    print("\n" + "="*80)
    print("📈 STEP 3: Creating Observations")
    print("="*80)
    
    # Complete pending analyses first
    print("   Completing pending analyses...")
    complete_result = make_request("POST", "/analyses/complete-all-pending")
    if complete_result:
        print(f"   ✅ Completed {complete_result.get('completed', 0)} analyses")
    
    # Get all policies
    policies = make_request("GET", "/policies")
    if not policies:
        return {"created": 0, "skipped": 0, "failed": 0}
    
    # Get all analyses
    analyses = make_request("GET", "/analyses", params={"analysis_type": "IMPACT", "limit": 1000})
    if not analyses:
        print("   ⚠️  No analyses found")
        return {"created": 0, "skipped": 0, "failed": 0}
    
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
    
    print(f"\n   Creating observations from {len(completed_analyses)} analyses...")
    for i, analysis in enumerate(completed_analyses, 1):
        analysis_id = analysis.get("id")
        policy_id = analysis.get("policy_id")
        
        if not analysis_id or not policy_id:
            continue
        
        if analysis_id in existing_analysis_ids:
            skipped += 1
            continue
        
        # Find policy name
        policy_name = "Unknown"
        for p in policies:
            if str(p.get("id")) == str(policy_id):
                policy_name = p.get("name", "Unknown")
                break
        
        result = make_request("POST", f"/observations/from-analysis/{analysis_id}",
                             params={"policy_id": policy_id})
        
        if result and result.get("observation_id"):
            created += 1
            if created <= 5:  # Show first 5
                print(f"      ✅ Created: {policy_name[:40]}")
        else:
            failed += 1
            if failed <= 3:  # Show first 3 failures
                print(f"      ⚠️  Failed: {policy_name[:40]}")
        
        if i % 10 == 0:
            print(f"      Progress: {i}/{len(completed_analyses)} analyses processed...")
        
        time.sleep(0.2)
    
    print(f"\n   ✅ Observations: {created} created, {skipped} skipped, {failed} failed")
    return {"created": created, "skipped": skipped, "failed": failed}

def main():
    print("="*80)
    print("🚀 GENERATE DATA, CREATE BASELINES & OBSERVATIONS")
    print("="*80)
    print(f"Started at: {datetime.now().isoformat()}")
    
    # Check API connection
    health = make_request("GET", "/health")
    if not health:
        print("\n❌ Cannot connect to API server. Please start it first:")
        print("   cd apps/api && python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    print("✅ Connected to API server\n")
    
    # Step 1: Generate policy-scoped data
    data_success = step1_generate_policy_scoped_data()
    
    # Step 2: Create baselines
    baseline_result = step2_create_baselines()
    
    # Step 3: Create observations
    observation_result = step3_create_observations()
    
    # Summary
    print("\n" + "="*80)
    print("📊 FINAL SUMMARY")
    print("="*80)
    print(f"Data Generation: {'✅ Success' if data_success else '❌ Failed'}")
    print(f"Baselines: General={baseline_result.get('general', 0)}, Policy-specific={baseline_result.get('policy_specific', 0)}/{baseline_result.get('total', 0)}")
    print(f"Observations: {observation_result.get('created', 0)} created, {observation_result.get('skipped', 0)} skipped, {observation_result.get('failed', 0)} failed")
    print(f"\nCompleted at: {datetime.now().isoformat()}")
    print("="*80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
