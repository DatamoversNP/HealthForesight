#!/usr/bin/env python3
"""
Script to create baseline analyses for policies
"""
import sys
import os
import json
import requests
from datetime import datetime, timedelta
from uuid import UUID

# API base URL
API_BASE_URL = "http://localhost:8000/api/v1"

def get_demo_token():
    """Get demo user token"""
    # For demo mode, we can use a simple approach
    return "demo-token"

def create_baseline_analysis(name, start_date, end_date, baseline_type="GENERAL", policy_id=None, n_clusters=5):
    """Create a baseline analysis via API"""
    url = f"{API_BASE_URL}/analyses/baseline"
    headers = {
        "Authorization": f"Bearer {get_demo_token()}",
        "Content-Type": "application/json"
    }
    
    data = {
        "name": name,
        "start_date": start_date,
        "end_date": end_date,
        "n_clusters": n_clusters,
        "baseline_type": baseline_type,
    }
    
    if policy_id:
        data["policy_id"] = policy_id
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=300)
        if response.status_code == 201:
            return response.json()
        else:
            print(f"  ❌ Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return None

def get_policies():
    """Get policies from API"""
    url = f"{API_BASE_URL}/policies"
    headers = {
        "Authorization": f"Bearer {get_demo_token()}",
    }
    try:
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching policies: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Exception fetching policies: {e}")
        return []

print("=" * 60)
print("FETCHING POLICIES FOR BASELINE CREATION")
print("=" * 60)

policies_data = get_policies()
policies = []

if isinstance(policies_data, list):
    policies = policies_data
elif isinstance(policies_data, dict) and 'items' in policies_data:
    policies = policies_data['items']
else:
    policies = []

for policy in policies[:10]:  # Limit to first 10
    print(f"\nPolicy: {policy.get('name', 'N/A')}")
    print(f"  ID: {policy.get('id', 'N/A')}")
    print(f"  Type: {policy.get('policy_type', 'N/A')}")
    if policy.get('effective_period'):
        ep = policy['effective_period']
        print(f"  Effective Start: {ep.get('start_date', 'N/A')}")
        print(f"  Effective End: {ep.get('end_date', 'N/A')}")
    if policy.get('scope'):
        print(f"  Scope: {list(policy['scope'].keys())}")

print(f"\n\nTotal policies found: {len(policies)}")
print("\n" + "=" * 60)

# Select first 3-5 policies to create baselines for
policies_to_process = policies[:5] if len(policies) >= 5 else policies

print("\n" + "=" * 60)
print("CREATING BASELINE ANALYSES")
print("=" * 60)

# First, create a general baseline with unique name
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
print("\n1. Creating General Baseline...")
general_start = "2023-01-01"
general_end = "2023-12-31"
result = create_baseline_analysis(
    name=f"General Baseline 2023 - {timestamp}",
    start_date=general_start,
    end_date=general_end,
    baseline_type="GENERAL",
    n_clusters=5
)
if result:
    print(f"  ✅ Created: {result.get('id', 'N/A')}")
else:
    print("  ❌ Failed to create general baseline")

# Then create policy-specific baselines
for i, policy in enumerate(policies_to_process, start=2):
    if not policy.get('effective_period'):
        print(f"\n{i}. Skipping {policy['name']} - no effective period")
        continue
    
    effective_start = policy['effective_period'].get('start_date')
    if not effective_start:
        print(f"\n{i}. Skipping {policy['name']} - no effective start date")
        continue
    
    # Parse effective start date
    try:
        eff_date = datetime.fromisoformat(effective_start.replace('Z', '+00:00'))
        # Baseline period: 6 months before effective date
        baseline_end = eff_date - timedelta(days=1)
        baseline_start = baseline_end - timedelta(days=180)  # ~6 months
        
        baseline_start_str = baseline_start.date().isoformat()
        baseline_end_str = baseline_end.date().isoformat()
        
        print(f"\n{i}. Creating Policy-Specific Baseline for: {policy['name']}")
        print(f"   Policy ID: {policy['id']}")
        print(f"   Baseline Period: {baseline_start_str} to {baseline_end_str}")
        print(f"   Policy Effective: {effective_start}")
        
        result = create_baseline_analysis(
            name=f"Baseline - {policy['name'][:40]} - {timestamp}",
            start_date=baseline_start_str,
            end_date=baseline_end_str,
            baseline_type="POLICY_SPECIFIC",
            policy_id=policy['id'],
            n_clusters=5
        )
        
        if result:
            print(f"   ✅ Created: {result.get('id', 'N/A')}")
        else:
            print(f"   ❌ Failed")
            
    except Exception as e:
        print(f"\n{i}. Error processing {policy['name']}: {e}")

print("\n" + "=" * 60)
print("BASELINE CREATION COMPLETE")
print("=" * 60)
