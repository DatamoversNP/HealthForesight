#!/usr/bin/env python3
"""
Generate realistic claims data for baseline computation
Generates data across the last 12 months with realistic distribution
"""
import requests
import time
from datetime import datetime, timedelta, date
from collections import defaultdict

API_BASE_URL = "http://localhost:8000/api/v1"

def generate_data_for_date_range(start_date: date, end_date: date, policies: list):
    """Generate data for a date range with realistic distribution"""
    print(f"\n📅 Generating data from {start_date} to {end_date}")
    
    # Calculate total days
    total_days = (end_date - start_date).days + 1
    
    # Distribute data across months (more recent months have more data)
    # This simulates realistic data accumulation
    months_data = defaultdict(int)
    current_date = start_date
    
    # Generate data for each month
    while current_date <= end_date:
        month_key = (current_date.year, current_date.month)
        # More recent months get more data (realistic scenario)
        months_ago = (end_date.year - current_date.year) * 12 + (end_date.month - current_date.month)
        weight = max(1, 12 - months_ago)  # More weight for recent months
        months_data[month_key] = weight
        current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
    
    total_weight = sum(months_data.values())
    
    # Generate data for each month
    success_count = 0
    for (year, month), weight in months_data.items():
        # Generate data for a few days in each month (to keep it realistic but not too slow)
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        
        # Generate data for 3-5 days per month (distributed)
        days_in_month = (month_end - month_start).days + 1
        sample_days = min(5, max(3, days_in_month // 7))  # 3-5 days per month
        
        # Select days to generate data for
        step = days_in_month // sample_days
        for day_offset in range(0, days_in_month, step):
            target_date = month_start + timedelta(days=day_offset)
            if target_date > end_date:
                break
            
            # Generate general data first
            try:
                result = requests.post(
                    f"{API_BASE_URL}/data/generate-claims",
                    json={
                        "target_date": target_date.isoformat(),
                        "member_count": int(5000 * (weight / total_weight)),  # Scale by month weight
                        "claims_per_member": 2.0
                    },
                    timeout=60
                )
                if result.status_code == 200:
                    data = result.json()
                    if data.get("success") and data.get("claims_loaded", 0) > 0:
                        success_count += 1
            except Exception as e:
                print(f"      ⚠️  Error generating general data for {target_date}: {e}")
            
            # Generate policy-specific data for first 10 policies (to avoid timeout)
            for policy in policies[:10]:
                policy_id = policy.get("id")
                if not policy_id:
                    continue
                
                try:
                    result = requests.post(
                        f"{API_BASE_URL}/data/generate-claims/policy-scoped",
                        params={"policy_id": policy_id},
                        json={
                            "target_date": target_date.isoformat(),
                            "member_count": int(1000 * (weight / total_weight)),  # Scale by month weight
                            "claims_per_member": 1.2
                        },
                        timeout=60
                    )
                    if result.status_code == 200:
                        data = result.json()
                        if data.get("success") and data.get("claims_loaded", 0) > 0:
                            pass  # Counted separately
                except Exception as e:
                    pass  # Continue with other policies
            
            time.sleep(0.1)  # Small delay to avoid overwhelming server
    
    return success_count

def main():
    print("="*80)
    print("📊 GENERATE BASELINE DATA (12-Month Window)")
    print("="*80)
    print(f"Started at: {datetime.now().isoformat()}\n")
    
    # Check API connection
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Connected to API server\n")
        else:
            print("❌ API server not responding")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        return
    
    # Get active policies
    try:
        response = requests.get(f"{API_BASE_URL}/policies", timeout=10)
        if response.status_code == 200:
            policies = response.json()
            active_policies = [p for p in policies if p.get("status") == "ACTIVE"]
            print(f"Found {len(active_policies)} active policies")
        else:
            print("⚠️  Could not fetch policies")
            active_policies = []
    except Exception as e:
        print(f"⚠️  Error fetching policies: {e}")
        active_policies = []
    
    # Calculate date range (last 12 months)
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    
    print(f"\n📅 Date Range: {start_date} to {end_date} (12 months)")
    print(f"   This ensures baseline computation can find data across the full window\n")
    
    # Generate data
    success_count = generate_data_for_date_range(start_date, end_date, active_policies)
    
    print(f"\n✅ Data generation completed: {success_count} date periods with data")
    print(f"\n📊 Next Steps:")
    print(f"   1. Run baseline creation: python3 scripts/generate_data_and_create_baselines_observations.py")
    print(f"   2. Or create baselines via API: POST /api/v1/baselines/refresh")
    print("="*80)

if __name__ == "__main__":
    main()
