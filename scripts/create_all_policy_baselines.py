#!/usr/bin/env python3
"""Create policy-specific baselines for all policies via API"""
import requests
from uuid import UUID

print("=" * 70)
print("CREATE POLICY-SPECIFIC BASELINES FOR ALL POLICIES")
print("=" * 70)
print()

# Get all policies
policies = requests.get('http://localhost:8000/api/v1/policies', timeout=60).json()

# Filter to active policies
active_policies = [p for p in policies if p.get('status') == 'ACTIVE']

print(f"📋 Found {len(active_policies)} active policies")
print()

if not active_policies:
    print("⚠️  No active policies found")
    exit(1)

created = 0
failed = 0
skipped = 0

for i, policy in enumerate(active_policies, 1):
    policy_id = policy.get('id') or policy.get('policy_id')
    policy_name = policy.get('name', 'Unknown Policy')
    
    if not policy_id:
        print(f"{i}. ⚠️  Skipping {policy_name[:60]}: No policy ID")
        skipped += 1
        continue
    
    print(f"{i}. Creating baseline for: {policy_name[:60]}")
    print(f"   Policy ID: {policy_id}")
    
    try:
        # Create policy-specific baseline via API
        response = requests.post(
            'http://localhost:8000/api/v1/baselines/refresh',
            headers={'Authorization': 'Bearer dev-token-123', 'Content-Type': 'application/json'},
            json={
                'policy_id': str(policy_id),
                'baseline_type': 'ROLLING',
                'window_months': 12,
                'refresh_reason': 'POLICY_SPECIFIC_BASELINE_CREATION'
            },
            timeout=120
        )
        
        if response.status_code == 201:
            baseline = response.json()
            metrics = baseline.get('baseline_metrics', {})
            util = metrics.get('util_rate_target_per_1000_mm', metrics.get('utilization_per_1k', 0))
            cost = metrics.get('paid_pmpm_target', metrics.get('allowed_pmpm_target', metrics.get('cost_pmpm', 0)))
            
            print(f"   ✅ Created baseline: {baseline.get('baseline_id', 'N/A')[:8]}...")
            print(f"      Utilization: {util:.2f} per 1K")
            print(f"      Cost PMPM: ${cost:.2f}")
            created += 1
        elif response.status_code == 400:
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"   ⚠️  No data: {error_detail[:80]}")
            failed += 1
        else:
            print(f"   ❌ Failed: {response.status_code} - {response.text[:100]}")
            failed += 1
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")
        failed += 1
    
    print()

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"✅ Created: {created}")
print(f"❌ Failed: {failed}")
print(f"⚠️  Skipped: {skipped}")
print(f"📊 Total: {len(active_policies)}")
print()

if created > 0:
    print("✅ Policy-specific baselines created successfully!")
    print("   They will now appear in the Policy Baseline tab of observations.")
else:
    print("⚠️  No baselines were created. Check if:")
    print("   1. Claims data exists in the database")
    print("   2. Data matches policy scope (procedure codes, LOB, market, etc.)")
    print("   3. Policy effective dates are set correctly")
