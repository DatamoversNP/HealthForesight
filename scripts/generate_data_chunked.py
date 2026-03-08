#!/usr/bin/env python3
"""
Chunked data generation - Generate data in small batches that can be resumed
"""
import requests
import time
import json
from datetime import datetime, timedelta, date
from pathlib import Path

API_BASE_URL = "http://localhost:8000/api/v1"
PROGRESS_FILE = Path("data_generation_progress.json")

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
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "timeout", "status_code": 408}
    except requests.exceptions.ConnectionError:
        return {"error": "connection_error", "status_code": 503}
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            return {"error": e.response.text, "status_code": 400}
        return {"error": str(e), "status_code": e.response.status_code}
    except Exception as e:
        return {"error": str(e), "status_code": 500}

def generate_data_for_month(year, month, policies, chunk_size=5):
    """Generate data for one month in small chunks"""
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)
    
    days_in_month = (month_end - month_start).days + 1
    sample_days = min(chunk_size, max(2, days_in_month // 7))
    
    step = max(1, days_in_month // sample_days)
    success_count = 0
    
    print(f"   📅 {month_start.strftime('%Y-%m')}: Generating for {sample_days} days...")
    
    for day_offset in range(0, days_in_month, step):
        target_date = month_start + timedelta(days=day_offset)
        if target_date > date.today():
            break
        
        # Generate general data
        result = make_request("POST", "/data/generate-claims",
                             json={"target_date": target_date.isoformat(), 
                                  "member_count": 3000, "claims_per_member": 1.5},
                             timeout=60)
        
        if result and result.get("success") and result.get("claims_loaded", 0) > 0:
            success_count += 1
        
        # Generate policy-specific data for first 5 policies only (to keep it fast)
        for policy in policies[:5]:
            policy_id = policy.get("id")
            if not policy_id:
                continue
            
            result = make_request("POST", f"/data/generate-claims/policy-scoped",
                                 params={"policy_id": policy_id},
                                 json={"target_date": target_date.isoformat(), 
                                      "member_count": 1000, "claims_per_member": 1.0},
                                 timeout=60)
            
            if result and result.get("success"):
                pass  # Counted separately
        
        time.sleep(0.2)  # Small delay
    
    return success_count

def main():
    print("="*80)
    print("📊 CHUNKED DATA GENERATION")
    print("="*80)
    
    # Load progress
    progress = load_progress()
    completed_months = set(progress.get("completed_months", []))
    
    print(f"Resuming from progress: {len(completed_months)} months already completed")
    
    # Check API
    health = make_request("GET", "/health", timeout=5)
    if not health or health.get("status") != "healthy":
        print("❌ API server not responding")
        return
    
    print("✅ API server connected\n")
    
    # Get policies
    policies = make_request("GET", "/policies", timeout=10)
    if not policies:
        print("❌ No policies found")
        return
    
    active_policies = [p for p in policies if p.get("status") == "ACTIVE"]
    print(f"Found {len(active_policies)} active policies\n")
    
    # Calculate date range (last 12 months)
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    
    print(f"📅 Target Window: {start_date} to {end_date} (12 months)")
    print(f"Generating data in small chunks...\n")
    
    # Generate for each month
    current = start_date.replace(day=1)
    total_success = 0
    
    while current <= end_date:
        month_key = f"{current.year}-{current.month:02d}"
        
        if month_key in completed_months:
            print(f"   ⏭️  {month_key}: Already completed, skipping...")
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
            continue
        
        try:
            success = generate_data_for_month(current.year, current.month, active_policies, chunk_size=3)
            if success > 0:
                total_success += success
                completed_months.add(month_key)
                progress["completed_months"] = list(completed_months)
                save_progress(progress)
                print(f"      ✅ {month_key}: {success} dates completed")
            else:
                print(f"      ⚠️  {month_key}: No data generated")
        except KeyboardInterrupt:
            print(f"\n⚠️  Interrupted! Progress saved. Run again to resume.")
            save_progress(progress)
            return
        except Exception as e:
            print(f"      ❌ {month_key}: Error - {e}")
            # Continue with next month
        
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
        
        time.sleep(0.5)  # Brief pause between months
    
    print(f"\n✅ Data generation complete: {total_success} date periods across {len(completed_months)} months")
    print(f"\nNext: Run baseline creation")
    print("="*80)

if __name__ == "__main__":
    main()
