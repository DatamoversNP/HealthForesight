#!/usr/bin/env python3
"""
Fresh Start Workflow - Clean up and regenerate everything correctly:
1. Clean up existing baselines and observations
2. Generate historical data (BEFORE policy activation) for baselines
3. Create baselines using historical data only
4. Generate post-activation data for observations
5. Create observations from post-activation data

IMPORTANT:
- Baselines use data BEFORE policy activation
- Observations use data FROM policy activation date onwards
- All data stored in same database tables (claims_lines)
"""
import requests
import time
import json
from datetime import datetime, timedelta, date
from pathlib import Path
from uuid import UUID

API_BASE_URL = "http://localhost:8000/api/v1"
TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

def make_request(method, endpoint, **kwargs):
    """Make API request"""
    url = f"{API_BASE_URL}{endpoint}"
    timeout = kwargs.pop('timeout', 300)
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout, **kwargs)
        elif method.upper() == "POST":
            response = requests.post(url, timeout=timeout, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 400:
            return {"error": response.text, "status_code": 400}
        else:
            return {"error": response.text, "status_code": response.status_code}
    except Exception as e:
        return {"error": str(e), "status_code": 500}

def step1_cleanup():
    """Step 1: Clean up existing baselines and observations"""
    print("\n" + "="*80)
    print("STEP 1: CLEANUP EXISTING BASELINES AND OBSERVATIONS")
    print("="*80)
    
    # Note: We'll need to add DELETE endpoints or use direct DB
    # For now, just report what exists
    baselines = make_request("GET", "/baselines", timeout=30)
    observations = make_request("GET", "/observations", timeout=30)
    
    baseline_count = len(baselines) if isinstance(baselines, list) else 0
    obs_count = len(observations) if isinstance(observations, list) else 0
    
    print(f"Found: {baseline_count} baselines, {obs_count} observations")
    print("⚠️  Manual cleanup needed via database or DELETE endpoints")
    print("   Run: cd apps/api && PYTHONPATH=src python3 -c 'from uepi_api.database import SessionLocal; from uepi_api.models.baseline import Baseline; from uepi_api.models.observation import Observation; from uuid import UUID; db = SessionLocal(); tenant_id = UUID(\"00000000-0000-0000-0000-000000000001\"); db.query(Observation).filter(Observation.tenant_id == tenant_id).delete(); db.query(Baseline).filter(Baseline.tenant_id == tenant_id).delete(); db.commit(); db.close()'")
    
    return True

def step2_generate_historical_data():
    """Step 2: Generate historical data BEFORE policy activation"""
    print("\n" + "="*80)
    print("STEP 2: GENERATE HISTORICAL DATA (BEFORE POLICY ACTIVATION)")
    print("="*80)
    
    # Get policies
    policies = make_request("GET", "/policies", timeout=30)
    if not policies:
        print("❌ No policies found")
        return False
    
    active_policies = [p for p in policies if p.get("status") == "ACTIVE"]
    print(f"Found {len(active_policies)} active policies\n")
    
    # Get activation dates from effective_period
    activation_dates = {}
    for policy in active_policies:
        policy_id = str(policy.get("id"))
        # Check effective_period at top level
        effective_period = policy.get("effective_period", {})
        if effective_period:
            activation_str = effective_period.get("start_date")
            if activation_str:
                try:
                    if isinstance(activation_str, str):
                        if 'T' in activation_str:
                            activation_str = activation_str.split('T')[0]
                        activation_dates[policy_id] = datetime.strptime(activation_str, "%Y-%m-%d").date()
                    elif hasattr(activation_str, 'date'):
                        activation_dates[policy_id] = activation_str.date()
                except Exception as e:
                    print(f"   ⚠️  Could not parse activation date for {policy_id}: {e}")
        
        # Fallback: check versions if effective_period not found
        if policy_id not in activation_dates:
            versions = policy.get("versions", [])
            if versions:
                latest = max(versions, key=lambda v: v.get("effective_start_date", ""))
                activation_str = latest.get("effective_start_date")
                if activation_str:
                    try:
                        if 'T' in activation_str:
                            activation_str = activation_str.split('T')[0]
                        activation_dates[policy_id] = datetime.strptime(activation_str, "%Y-%m-%d").date()
                    except:
                        pass
    
    print(f"Found activation dates for {len(activation_dates)} policies\n")
    
    # Generate general historical data (12 months before today)
    print("📊 Generating general historical data...")
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=365)
    
    current = start_date.replace(day=1)
    general_count = 0
    
    while current <= end_date:
        month_end = (current.replace(month=current.month+1) - timedelta(days=1)) if current.month < 12 else date(current.year+1, 1, 1) - timedelta(days=1)
        month_end = min(month_end, end_date)
        
        # Generate for 2-3 days per month
        days_in_month = (month_end - current).days + 1
        sample_days = min(3, max(1, days_in_month // 10))
        step = max(1, days_in_month // sample_days)
        
        for day_offset in range(0, days_in_month, step):
            target_date = current + timedelta(days=day_offset)
            if target_date > end_date:
                break
            
            result = make_request("POST", "/data/generate-claims",
                                json={"target_date": target_date.isoformat(), 
                                     "member_count": 5000, "claims_per_member": 2.0},
                                timeout=60)
            
            if result and (result.get("success") or result.get("status_code") == 400):
                general_count += 1
        
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    
    print(f"   ✅ Generated general data for {general_count} date periods\n")
    
    # Generate policy-specific historical data (BEFORE activation)
    print("📊 Generating policy-specific historical data (BEFORE activation)...")
    policy_count = 0
    
    for policy in active_policies[:10]:  # Limit to 10 for now
        policy_id = str(policy.get("id"))
        policy_name = policy.get("name", "Unknown")[:40]
        activation_date = activation_dates.get(policy_id)
        
        if not activation_date:
            print(f"   ⏭️  {policy_name}: No activation date")
            continue
        
        # Generate data for 12 months BEFORE activation
        end_date_hist = activation_date - timedelta(days=1)
        start_date_hist = end_date_hist - timedelta(days=365)
        
        print(f"   📋 {policy_name}")
        print(f"      Activation: {activation_date}, Historical: {start_date_hist} to {end_date_hist}")
        
        # Generate for a few sample days
        current = start_date_hist.replace(day=1)
        success = 0
        
        while current <= end_date_hist:
            month_end = (current.replace(month=current.month+1) - timedelta(days=1)) if current.month < 12 else date(current.year+1, 1, 1) - timedelta(days=1)
            month_end = min(month_end, end_date_hist)
            
            days_in_month = (month_end - current).days + 1
            sample_days = min(2, max(1, days_in_month // 15))
            step = max(1, days_in_month // sample_days)
            
            for day_offset in range(0, days_in_month, step):
                target_date = current + timedelta(days=day_offset)
                if target_date > end_date_hist:
                    break
                
                result = make_request("POST", f"/data/generate-claims/policy-scoped",
                                     params={"policy_id": policy_id},
                                     json={"target_date": target_date.isoformat(), 
                                          "member_count": 1500, "claims_per_member": 1.2},
                                     timeout=60)
                
                if result and (result.get("success") or result.get("status_code") == 400):
                    success += 1
                
                time.sleep(0.1)
            
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        if success > 0:
            policy_count += 1
            print(f"      ✅ {success} date periods")
        else:
            print(f"      ⚠️  No data generated")
        
        time.sleep(0.5)
    
    print(f"\n✅ Historical data: General={general_count}, Policy-specific={policy_count} policies")
    return True

def step3_create_baselines():
    """Step 3: Create baselines using historical data only"""
    print("\n" + "="*80)
    print("STEP 3: CREATE BASELINES (USING HISTORICAL DATA ONLY)")
    print("="*80)
    
    # Create general baseline
    print("Creating general baseline...")
    result = make_request("POST", "/baselines/refresh",
                         json={"baseline_type": "ROLLING", "window_months": 12, "refresh_reason": "FRESH_START"},
                         timeout=600)
    
    if result and result.get("baseline_id"):
        print(f"   ✅ General baseline: {result.get('baseline_id')[:8]}...")
    else:
        print(f"   ⚠️  General baseline failed: {result.get('error', 'Unknown')[:100]}")
    
    # Create policy-specific baselines
    policies = make_request("GET", "/policies", timeout=30)
    active_policies = [p for p in policies if p.get("status") == "ACTIVE"] if policies else []
    
    print(f"\nCreating policy-specific baselines ({len(active_policies)} policies)...")
    success_count = 0
    
    for i, policy in enumerate(active_policies[:10], 1):  # Limit to 10
        policy_id = policy.get("id")
        policy_name = policy.get("name", "Unknown")[:40]
        
        result = make_request("POST", "/baselines/refresh",
                             json={"policy_id": policy_id, "baseline_type": "ROLLING", 
                                  "window_months": 12, "refresh_reason": "FRESH_START"},
                             timeout=600)
        
        if result and result.get("baseline_id"):
            success_count += 1
            print(f"   ✅ {i}. {policy_name}")
        elif result and result.get("status_code") == 400:
            print(f"   ℹ️  {i}. {policy_name}: {result.get('error', 'No data')[:50]}")
        else:
            print(f"   ⚠️  {i}. {policy_name}: Failed")
        
        time.sleep(1)
    
    print(f"\n✅ Baselines: General=1, Policy-specific={success_count}/{len(active_policies[:10])}")
    return True

def main():
    print("="*80)
    print("🚀 FRESH START WORKFLOW")
    print("="*80)
    print("This will:")
    print("1. Clean up existing baselines and observations")
    print("2. Generate historical data (BEFORE policy activation)")
    print("3. Create baselines using historical data only")
    print("4. All data stored in claims_lines table")
    print("="*80)
    
    # Check API
    health = make_request("GET", "/health", timeout=5)
    if not health or health.get("status") != "healthy":
        print("❌ API server not responding")
        return
    
    print("✅ API server connected\n")
    
    # Run steps
    step1_cleanup()
    step2_generate_historical_data()
    step3_create_baselines()
    
    print("\n" + "="*80)
    print("✅ FRESH START WORKFLOW COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("- Generate post-activation data for observations")
    print("- Create observations from post-activation data")

if __name__ == "__main__":
    main()
