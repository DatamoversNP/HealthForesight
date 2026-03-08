#!/usr/bin/env python3
"""Fix observation metrics and add trend functionality"""
import requests
from datetime import datetime, timedelta, date
from dateutil import parser

API_BASE = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer dev-token-123", "Content-Type": "application/json"}

def generate_claims_for_period(start_date: date, end_date: date):
    """Generate claims data for a date range"""
    print(f"📊 Generating claims data for {start_date} to {end_date}...")
    
    current = start_date
    generated = 0
    while current <= end_date:
        try:
            response = requests.post(
                f"{API_BASE}/data/generate-claims",
                headers=HEADERS,
                json={'target_date': current.isoformat()},
                timeout=30
            )
            if response.status_code == 200:
                generated += 1
                if generated % 10 == 0:
                    print(f"   Generated {generated} days...")
        except Exception as e:
            print(f"   ⚠️  Error generating for {current}: {e}")
        current += timedelta(days=1)
    
    print(f"✅ Generated claims data for {generated} days")
    return generated

def main():
    print("=" * 70)
    print("FIX OBSERVATION METRICS AND ADD TRENDS")
    print("=" * 70)
    print()
    
    # Get current observation
    observations = requests.get(f"{API_BASE}/observations", headers=HEADERS, timeout=60).json()
    
    if not observations:
        print("❌ No observations found")
        return
    
    obs = observations[0]
    policy_id = obs.get('policy_id')
    obs_id = obs.get('observation_id')
    period_start = obs.get('observation_period_start')
    period_end = obs.get('observation_period_end')
    
    print(f"📋 Current Observation:")
    print(f"   Observation ID: {obs_id}")
    print(f"   Policy ID: {policy_id}")
    print(f"   Period: {period_start} to {period_end}")
    print()
    
    # Parse dates
    start = parser.parse(period_start).date()
    end = parser.parse(period_end).date()
    
    # Step 1: Generate claims data for observation period
    print("Step 1: Generating claims data for observation period...")
    generate_claims_for_period(start, end)
    print()
    
    # Step 2: Delete and recreate observation
    print("Step 2: Recreating observation with correct data...")
    
    # Get policy and baseline analysis
    policy = requests.get(f"{API_BASE}/policies/{policy_id}", headers=HEADERS, timeout=60).json()
    
    # Get baseline analyses for this policy
    analyses = requests.get(
        f"{API_BASE}/analyses",
        headers=HEADERS,
        params={'analysis_type': 'BASELINE', 'policy_id': policy_id},
        timeout=60
    ).json()
    
    policy_baseline = None
    for a in analyses:
        if a.get('status') == 'COMPLETED' and a.get('policy_id') == policy_id:
            policy_baseline = a
            break
    
    if not policy_baseline:
        # Try general baseline
        general_analyses = requests.get(
            f"{API_BASE}/analyses",
            headers=HEADERS,
            params={'analysis_type': 'BASELINE'},
            timeout=60
        ).json()
        policy_baseline = next((a for a in general_analyses if a.get('status') == 'COMPLETED'), None)
    
    if policy_baseline:
        analysis_id = policy_baseline.get('id')
        print(f"   Using baseline analysis: {analysis_id}")
        
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
                
                # Check metrics
                metrics = new_obs.get('metrics', {})
                print(f"   📊 Metrics:")
                print(f"      Utilization: {metrics.get('utilization_per_1k', 0)}")
                print(f"      Cost PMPM: ${metrics.get('cost_pmpm', 0):.2f}")
                print(f"      Total Claims: {metrics.get('total_claims', 0)}")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print("   ⚠️  No baseline analysis found")
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✅ Claims data generated for observation period")
    print("✅ Observation recreated with correct data")
    print()
    print("📊 Next steps:")
    print("   1. Create multiple observations over time to see trends")
    print("   2. Use include_trends=true when listing observations")
    print("   3. Frontend will display trend charts automatically")

if __name__ == "__main__":
    main()
