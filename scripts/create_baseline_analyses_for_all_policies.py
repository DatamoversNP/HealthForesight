#!/usr/bin/env python3
"""Create baseline analyses for all policies that don't have them"""
import requests
import time
from datetime import datetime, timedelta, date

API_BASE = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer dev-token-123", "Content-Type": "application/json"}

def check_analysis_status(analysis_id, max_wait=300):
    """Wait for analysis to complete"""
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                f"{API_BASE}/analyses/{analysis_id}",
                headers=HEADERS,
                timeout=30
            )
            if response.status_code == 200:
                analysis = response.json()
                status = analysis.get('status')
                if status == 'COMPLETED':
                    return True
                elif status == 'FAILED':
                    return False
                # Still running, wait a bit
                time.sleep(5)
            else:
                time.sleep(5)
        except Exception as e:
            print(f"   ⚠️  Error checking status: {e}")
            time.sleep(5)
    return False

def create_baseline_analysis_for_policy(policy_id, policy_name):
    """Create a baseline analysis for a specific policy"""
    try:
        # Generate a unique name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_name = f"Baseline - {policy_name[:40]} - {timestamp}"
        
        # Calculate date range (12 months ending 1 day before today)
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=365)
        
        print(f"   Creating: {analysis_name}")
        print(f"   Date range: {start_date} to {end_date}")
        
        # Create baseline analysis
        response = requests.post(
            f"{API_BASE}/analyses/baseline",
            headers=HEADERS,
            json={
                "name": analysis_name,
                "baseline_type": "POLICY_SPECIFIC",
                "policy_id": str(policy_id),
                "n_clusters": 5,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            timeout=600  # 10 minutes for creation
        )
        
        if response.status_code == 201:
            analysis = response.json()
            analysis_id = analysis.get('id')
            print(f"   ✅ Created analysis: {analysis_id[:8]}...")
            print(f"   Status: {analysis.get('status')}")
            
            # Wait for completion (if it's async)
            if analysis.get('status') == 'PENDING':
                print(f"   ⏳ Waiting for completion...")
                if check_analysis_status(analysis_id, max_wait=600):
                    print(f"   ✅ Analysis completed successfully!")
                    return True
                else:
                    print(f"   ⚠️  Analysis still running or failed (check manually)")
                    return True  # Still count as created
            elif analysis.get('status') == 'COMPLETED':
                print(f"   ✅ Analysis completed immediately!")
                return True
            else:
                print(f"   ⚠️  Analysis status: {analysis.get('status')}")
                return True  # Count as created
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")
        return False

def main():
    print("=" * 70)
    print("CREATE BASELINE ANALYSES FOR ALL POLICIES")
    print("=" * 70)
    print()
    
    # Get all policies
    policies = requests.get(f"{API_BASE}/policies", headers=HEADERS, timeout=60).json()
    active_policies = [p for p in policies if p.get('status') == 'ACTIVE']
    
    print(f"📊 Total active policies: {len(active_policies)}")
    print()
    
    # Get existing baseline analyses
    analyses = requests.get(
        f"{API_BASE}/analyses",
        headers=HEADERS,
        params={'analysis_type': 'BASELINE'},
        timeout=60
    ).json()
    
    # Find policies with baseline analyses
    policies_with_analyses = set()
    for a in analyses:
        policy_id = a.get('policy_id')
        if policy_id:
            policies_with_analyses.add(str(policy_id))
    
    print(f"📊 Policies with baseline analyses: {len(policies_with_analyses)}")
    print()
    
    # Find policies without baseline analyses
    policies_to_create = []
    for p in active_policies:
        policy_id = str(p.get('id') or p.get('policy_id'))
        if policy_id not in policies_with_analyses:
            policies_to_create.append({
                'id': policy_id,
                'name': p.get('name', 'Unknown Policy')
            })
    
    print(f"📋 Policies needing baseline analyses: {len(policies_to_create)}")
    print()
    
    if not policies_to_create:
        print("✅ All policies already have baseline analyses!")
        return
    
    # Create baseline analyses
    created = 0
    failed = 0
    
    for i, policy in enumerate(policies_to_create, 1):
        print(f"{i}. Policy: {policy['name'][:60]}")
        print(f"   Policy ID: {policy['id']}")
        
        if create_baseline_analysis_for_policy(policy['id'], policy['name']):
            created += 1
        else:
            failed += 1
        
        print()
        
        # Small delay between requests
        if i < len(policies_to_create):
            time.sleep(2)
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ Created: {created}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {len(policies_to_create)}")
    print()
    
    if created > 0:
        print("✅ Baseline analyses created!")
        print("   Note: Some analyses may still be running (PENDING status).")
        print("   They will complete automatically and appear as COMPLETED.")
    else:
        print("⚠️  No analyses were created. Check errors above.")

if __name__ == "__main__":
    main()
