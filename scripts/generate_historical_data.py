#!/usr/bin/env python3
"""
Generate historical data for baseline computation (BEFORE policy activation)
This data should be realistic and match policy scopes where applicable
"""
import requests
import time
import json
from datetime import datetime, timedelta, date
from pathlib import Path
from uuid import UUID

API_BASE_URL = "http://localhost:8000/api/v1"
PROGRESS_FILE = Path("historical_data_progress.json")
TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

def load_progress():
    """Load progress from file"""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_progress(progress):
    """Save progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2, default=str)

def make_request(method, endpoint, **kwargs):
    """Make API request with error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    timeout = kwargs.pop('timeout', 60)
    
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
            # 400 might mean data already exists, which is OK
            return {"error": response.text, "status_code": 400, "already_exists": True}
        else:
            return {"error": response.text, "status_code": response.status_code}
    except requests.exceptions.Timeout:
        return {"error": "timeout", "status_code": 408}
    except requests.exceptions.ConnectionError:
        return {"error": "connection_error", "status_code": 503}
    except Exception as e:
        return {"error": str(e), "status_code": 500}

def get_policy_activation_dates():
    """Get activation dates for all policies"""
    policies = make_request("GET", "/policies", timeout=10)
    if not policies:
        return {}
    
    activation_dates = {}
    for policy in policies:
        policy_id = str(policy.get("id"))
        # Get latest version
        versions = policy.get("versions", [])
        if versions:
            latest = max(versions, key=lambda v: v.get("effective_start_date", ""))
            activation_date = latest.get("effective_start_date")
            if activation_date:
                try:
                    # Parse date string
                    if 'T' in activation_date:
                        activation_date = activation_date.split('T')[0]
                    activation_dates[policy_id] = datetime.strptime(activation_date, "%Y-%m-%d").date()
                except:
                    pass
    
    return activation_dates

def generate_historical_data_for_policy(policy_id, activation_date, months_before=12):
    """Generate historical data for a policy (before activation)"""
    end_date = activation_date - timedelta(days=1)  # Day before activation
    start_date = end_date - timedelta(days=months_before * 30)
    
    print(f"   📅 Historical window: {start_date} to {end_date} (before activation {activation_date})")
    
    # Generate data for a few sample days in each month
    current = start_date.replace(day=1)
    success_count = 0
    
    while current <= end_date:
        # Generate for 2-3 days per month
        month_end = (current.replace(month=current.month+1) - timedelta(days=1)) if current.month < 12 else date(current.year+1, 1, 1) - timedelta(days=1)
        month_end = min(month_end, end_date)
        
        # Pick 2-3 days in the month
        days_in_month = (month_end - current).days + 1
        sample_days = min(3, max(1, days_in_month // 10))
        step = max(1, days_in_month // sample_days)
        
        for day_offset in range(0, days_in_month, step):
            target_date = current + timedelta(days=day_offset)
            if target_date > end_date:
                break
            
            # Generate policy-scoped data
            result = make_request("POST", f"/data/generate-claims/policy-scoped",
                                 params={"policy_id": policy_id},
                                 json={"target_date": target_date.isoformat(), 
                                      "member_count": 1500, "claims_per_member": 1.2},
                                 timeout=60)
            
            if result and (result.get("success") or result.get("already_exists")):
                success_count += 1
            
            time.sleep(0.1)
        
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    
    return success_count

def main():
    print("="*80)
    print("📊 GENERATE HISTORICAL DATA FOR BASELINES")
    print("="*80)
    
    # Load progress
    progress = load_progress()
    completed_policies = set(progress.get("completed_policies", []))
    
    print(f"Resuming: {len(completed_policies)} policies already completed\n")
    
    # Check API
    health = make_request("GET", "/health", timeout=5)
    if not health or health.get("status") != "healthy":
        print("❌ API server not responding")
        return
    
    print("✅ API server connected\n")
    
    # Get policies and activation dates
    policies = make_request("GET", "/policies", timeout=10)
    if not policies:
        print("❌ No policies found")
        return
    
    active_policies = [p for p in policies if p.get("status") == "ACTIVE"]
    print(f"Found {len(active_policies)} active policies\n")
    
    # Get activation dates
    activation_dates = get_policy_activation_dates()
    print(f"Found activation dates for {len(activation_dates)} policies\n")
    
    # Generate general historical data (for general baseline)
    print("📊 Generating general historical data...")
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=365)
    
    current = start_date.replace(day=1)
    general_success = 0
    
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
            
            if result and (result.get("success") or result.get("already_exists")):
                general_success += 1
        
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    
    print(f"   ✅ Generated general data for {general_success} date periods\n")
    
    # Generate policy-specific historical data
    print("📊 Generating policy-specific historical data...")
    policy_success = 0
    
    for policy in active_policies:
        policy_id = str(policy.get("id"))
        policy_name = policy.get("name", "Unknown")[:40]
        
        if policy_id in completed_policies:
            print(f"   ⏭️  {policy_name}: Already completed")
            continue
        
        activation_date = activation_dates.get(policy_id)
        if not activation_date:
            print(f"   ⚠️  {policy_name}: No activation date, skipping")
            continue
        
        print(f"   📋 {policy_name}")
        print(f"      Activation: {activation_date}")
        
        try:
            success = generate_historical_data_for_policy(policy_id, activation_date, months_before=12)
            if success > 0:
                policy_success += 1
                completed_policies.add(policy_id)
                progress["completed_policies"] = list(completed_policies)
                save_progress(progress)
                print(f"      ✅ {success} date periods generated")
            else:
                print(f"      ⚠️  No data generated")
        except KeyboardInterrupt:
            print(f"\n⚠️  Interrupted! Progress saved.")
            save_progress(progress)
            return
        except Exception as e:
            print(f"      ❌ Error: {e}")
        
        time.sleep(0.5)
    
    print(f"\n✅ Historical data generation complete:")
    print(f"   General: {general_success} date periods")
    print(f"   Policy-specific: {policy_success} policies")
    print("="*80)

if __name__ == "__main__":
    main()
