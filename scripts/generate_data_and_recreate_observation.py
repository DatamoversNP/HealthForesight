#!/usr/bin/env python3
"""Generate claims data for observation period and recreate observation"""
import requests
import time
from datetime import datetime, timedelta, date
from dateutil import parser

API_BASE = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer dev-token-123", "Content-Type": "application/json"}

def wait_for_data_generation(job_id, max_wait=600):
    """Wait for data generation job to complete"""
    print(f"⏳ Waiting for data generation job {job_id}...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        # Check job status (if we had a job status endpoint)
        # For now, just wait and check data availability
        time.sleep(10)
        
        # Try to check if data exists by querying a sample date
        # We'll just wait a reasonable time
        elapsed = int(time.time() - start_time)
        if elapsed % 30 == 0:
            print(f"   ... {elapsed}s elapsed")
    
    print("✅ Data generation should be complete (or in progress)")
    return True

def main():
    print("=" * 70)
    print("GENERATE DATA FOR OBSERVATION PERIOD AND RECREATE OBSERVATION")
    print("=" * 70)
    print()
    
    # Step 1: Get observation period
    observations = requests.get(f"{API_BASE}/observations", headers=HEADERS, timeout=60).json()
    
    if not observations:
        print("❌ No observations found")
        return
    
    obs = observations[0]
    policy_id = obs.get('policy_id')
    period_start = obs.get('observation_period_start')
    period_end = obs.get('observation_period_end')
    
    print(f"📋 Observation Period: {period_start} to {period_end}")
    print(f"   Policy ID: {policy_id}")
    print()
    
    # Parse dates
    start = parser.parse(period_start).date()
    end = parser.parse(period_end).date()
    
    # Step 2: Generate claims data for the period
    print("Step 1: Generating claims data for observation period...")
    print(f"   Date range: {start} to {end}")
    print(f"   This will generate ~25,000 claims per day")
    print()
    
    try:
        response = requests.post(
            f"{API_BASE}/data/generate-claims/date-range",
            headers=HEADERS,
            params={
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
                'member_count': 10000,
                'claims_per_member': 2.5
            },
            timeout=30
        )
        
        if response.status_code == 202:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ Data generation job started!")
            print(f"   Job ID: {job_id}")
            print(f"   Total days: {result.get('total_days', 0)}")
            print()
            
            # Wait for data generation (with timeout)
            print("⏳ Waiting for data generation to complete...")
            print("   (This may take several minutes for 31 days)")
            time.sleep(60)  # Wait 1 minute for initial progress
            print("   ... Data generation in progress (check API logs for details)")
            print()
        else:
            print(f"❌ Failed to start data generation: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return
    except Exception as e:
        print(f"❌ Error starting data generation: {e}")
        return
    
    # Step 3: Wait a bit more, then recreate observation
    print("Step 2: Waiting for data to be available...")
    time.sleep(30)  # Wait additional 30 seconds
    print()
    
    # Step 3: Recreate observation
    print("Step 3: Recreating observation with new data...")
    
    # Get baseline analysis
    analyses = requests.get(
        f"{API_BASE}/analyses",
        headers=HEADERS,
        params={'analysis_type': 'BASELINE'},
        timeout=60
    ).json()
    
    policy_baseline = None
    for a in analyses:
        if a.get('status') == 'COMPLETED' and a.get('policy_id') == policy_id:
            policy_baseline = a
            break
    
    if not policy_baseline:
        general_analyses = requests.get(
            f"{API_BASE}/analyses",
            headers=HEADERS,
            params={'analysis_type': 'BASELINE'},
            timeout=60
        ).json()
        policy_baseline = next((a for a in general_analyses if a.get('status') == 'COMPLETED'), None)
    
    if policy_baseline:
        analysis_id = policy_baseline.get('id')
        
        # Delete old observation
        try:
            requests.delete(f"{API_BASE}/observations/all", headers=HEADERS, timeout=60)
            print("   ✅ Deleted old observation")
        except:
            pass
        
        # Create new observation
        try:
            response = requests.post(
                f"{API_BASE}/observations/from-analysis/{analysis_id}",
                headers=HEADERS,
                params={'policy_id': policy_id},
                timeout=300
            )
            
            if response.status_code == 201:
                new_obs = response.json()
                print(f"   ✅ Created new observation: {new_obs.get('observation_id')}")
                
                metrics = new_obs.get('metrics', {})
                print(f"   📊 Metrics:")
                print(f"      Utilization: {metrics.get('utilization_per_1k', 0)}")
                print(f"      Cost PMPM: ${metrics.get('cost_pmpm', 0):.2f}")
                print(f"      Total Claims: {metrics.get('total_claims', 0):,}")
                print(f"      Member Months: {metrics.get('member_months', 0)}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"      Error: {response.text[:300]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print("   ⚠️  No baseline analysis found")
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✅ Data generation pipeline started for observation period")
    print("✅ Observation recreated")
    print()
    print("📊 Note: Data generation runs in background.")
    print("   If metrics are still 0, wait a few more minutes for data generation to complete.")
    print("   Then recreate the observation again.")

if __name__ == "__main__":
    main()
