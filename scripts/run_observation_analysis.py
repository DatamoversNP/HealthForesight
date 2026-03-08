#!/usr/bin/env python3
"""
Run observation analysis to compare predicted vs observed outcomes

This script:
1. Lists all policies
2. For each policy, creates an impact analysis for the post-policy period (Dec 27-31, 2025)
3. Creates observations from the impact analyses
4. Compares observed outcomes with baseline and predicted impact
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Try to use httpx if available, otherwise use urllib
try:
    import httpx
    USE_HTTPX = True
except ImportError:
    try:
        import urllib.request
        import urllib.parse
        USE_HTTPX = False
    except ImportError:
        print("Error: Need either 'httpx' or 'urllib' to make HTTP requests")
        print("Install with: pip install httpx")
        sys.exit(1)

API_BASE_URL = "http://localhost:8000/api/v1"

def get_policies():
    """Get all policies"""
    url = f"{API_BASE_URL}/policies"
    try:
        if USE_HTTPX:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)
                response.raise_for_status()
                return response.json()
        else:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Error fetching policies: {e}")
        return []

def get_baseline_analyses():
    """Get completed baseline analyses"""
    url = f"{API_BASE_URL}/analyses?analysis_type=BASELINE"
    try:
        if USE_HTTPX:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)
                response.raise_for_status()
                analyses = response.json()
                # Filter for COMPLETED status
                return [a for a in analyses if a.get('status') == 'COMPLETED']
        else:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as response:
                analyses = json.loads(response.read().decode('utf-8'))
                return [a for a in analyses if a.get('status') == 'COMPLETED']
    except Exception as e:
        print(f"⚠️  Error fetching baseline analyses: {e}")
        return []

def create_impact_analysis(policy_id, policy_scope):
    """Create an impact analysis for post-policy period"""
    url = f"{API_BASE_URL}/analyses/impact"
    
    # Build treatment filters from policy scope
    treatment_filters = {}
    if policy_scope:
        if 'lob' in policy_scope:
            treatment_filters['lob'] = policy_scope['lob']
        if 'markets' in policy_scope:
            treatment_filters['markets'] = policy_scope['markets']
        if 'network' in policy_scope:
            treatment_filters['in_network_only'] = 'IN' in (policy_scope.get('network') or [])
    
    payload = {
        "policy_id": policy_id,
        "treatment_filters": treatment_filters,
        "control_filters": None,
        "pre_window_months": 6,
        "post_window_months": 1,  # Post-policy period is just 5 days (Dec 27-31)
    }
    
    try:
        if USE_HTTPX:
            with httpx.Client(timeout=300.0) as client:
                response = client.post(url, json=payload)
                if response.status_code == 201:
                    return response.json()
                else:
                    print(f"   ⚠️  Impact analysis creation failed: {response.status_code}")
                    print(f"      {response.text[:200]}")
                    return None
        else:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=300) as response:
                if response.getcode() == 201:
                    return json.loads(response.read().decode('utf-8'))
                return None
    except Exception as e:
        print(f"   ⚠️  Error creating impact analysis: {e}")
        return None

def create_observation_from_analysis(analysis_id, policy_id, baseline_id=None):
    """Create observation from impact analysis"""
    url = f"{API_BASE_URL}/observations/from-analysis/{analysis_id}?policy_id={policy_id}"
    if baseline_id:
        url += f"&baseline_version_id={baseline_id}"
    
    try:
        if USE_HTTPX:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url)
                if response.status_code == 201:
                    return response.json()
                else:
                    print(f"   ⚠️  Observation creation failed: {response.status_code}")
                    print(f"      {response.text[:200]}")
                    return None
        else:
            req = urllib.request.Request(
                url,
                data=b''.encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=120) as response:
                if response.getcode() == 201:
                    return json.loads(response.read().decode('utf-8'))
                return None
    except Exception as e:
        print(f"   ⚠️  Error creating observation: {str(e)[:200]}")
        return None

def main():
    print("\n" + "="*60)
    print("Running Observation Analysis")
    print("="*60)
    print()
    
    # Get baseline analyses
    print("1. Fetching baseline analyses...")
    baseline_analyses = get_baseline_analyses()
    baseline_id = baseline_analyses[0].get('id') if baseline_analyses else None
    if baseline_id:
        print(f"   ✅ Found baseline analysis: {baseline_id}")
    else:
        print(f"   ⚠️  No completed baseline analyses found")
    
    # Get all policies
    print("\n2. Fetching policies...")
    policies = get_policies()
    print(f"   ✅ Found {len(policies)} policies")
    
    if not policies:
        print("\n❌ No policies found. Cannot run observation analysis.")
        return
    
    # Process each policy
    print("\n3. Running impact analysis and creating observations...")
    print()
    
    results = {
        "total": len(policies),
        "impact_analysis_created": 0,
        "observations_created": 0,
        "failed": 0,
        "details": [],
    }
    
    for policy in policies:
        policy_id = policy.get('id') or policy.get('policy_id')
        policy_name = policy.get('policy_name') or policy.get('name', 'Unknown')
        
        if not policy_id:
            continue
        
        print(f"   Processing: {policy_name} ({policy_id[:8]}...)")
        
        # Create impact analysis
        policy_scope = policy.get('scope', {})
        impact_analysis = create_impact_analysis(policy_id, policy_scope)
        
        if impact_analysis:
            analysis_id = impact_analysis.get('id')
            results["impact_analysis_created"] += 1
            print(f"      ✅ Impact analysis created: {analysis_id[:8]}...")
            
            # Create observation from analysis
            observation = create_observation_from_analysis(analysis_id, policy_id, baseline_id)
            
            if observation:
                observation_id = observation.get('observation_id')
                results["observations_created"] += 1
                print(f"      ✅ Observation created: {observation_id[:8]}...")
                results["details"].append({
                    "policy_name": policy_name,
                    "policy_id": policy_id,
                    "analysis_id": analysis_id,
                    "observation_id": observation_id,
                    "status": "success",
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "policy_name": policy_name,
                    "policy_id": policy_id,
                    "analysis_id": analysis_id,
                    "status": "observation_failed",
                })
        else:
            results["failed"] += 1
            results["details"].append({
                "policy_name": policy_name,
                "policy_id": policy_id,
                "status": "impact_analysis_failed",
            })
        
        print()
    
    # Summary
    print("="*60)
    print("✅ Observation Analysis Complete!")
    print("="*60)
    print(f"Total policies: {results['total']}")
    print(f"Impact analyses created: {results['impact_analysis_created']}")
    print(f"Observations created: {results['observations_created']}")
    print(f"Failed: {results['failed']}")
    print()
    print("Next steps:")
    print("  - View observations in UI (if available)")
    print("  - Compare predicted vs observed outcomes")
    print()

if __name__ == "__main__":
    main()
