#!/usr/bin/env python3
"""
Create policy-specific baselines for all policies
This script creates baselines for each policy using actual database data
"""
import sys
import os

# Add the API source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api', 'src'))

from uuid import UUID
from datetime import date, timedelta
from uepi_api.database import SessionLocal
from uepi_api.storage_policies import list_policies
from uepi_api.baseline_refresh import refresh_baseline

# Default tenant ID
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def create_policy_specific_baselines():
    """Create policy-specific baselines for all policies"""
    print("=" * 70)
    print("CREATE POLICY-SPECIFIC BASELINES FOR ALL POLICIES")
    print("=" * 70)
    print()
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get all policies
        print("📋 Getting all policies...")
        policies = list_policies(DEFAULT_TENANT_ID)
        
        # Filter to active policies only
        active_policies = [p for p in policies if p.get('status') == 'ACTIVE']
        
        print(f"✅ Found {len(active_policies)} active policies")
        print()
        
        if not active_policies:
            print("⚠️  No active policies found. Exiting.")
            return
        
        # Create baselines for each policy
        created = 0
        failed = 0
        skipped = 0
        
        for i, policy in enumerate(active_policies, 1):
            policy_id_str = policy.get('id') or policy.get('policy_id')
            policy_name = policy.get('name', 'Unknown Policy')
            
            if not policy_id_str:
                print(f"{i}. ⚠️  Skipping {policy_name}: No policy ID")
                skipped += 1
                continue
            
            try:
                policy_id = UUID(policy_id_str) if isinstance(policy_id_str, str) else policy_id_str
            except (ValueError, AttributeError):
                print(f"{i}. ⚠️  Skipping {policy_name}: Invalid policy ID format")
                skipped += 1
                continue
            
            print(f"{i}. Creating baseline for: {policy_name[:60]}")
            print(f"   Policy ID: {policy_id}")
            
            try:
                # Create policy-specific baseline
                # Use 12-month window ending 1 day before policy activation (or today if no activation date)
                baseline = refresh_baseline(
                    tenant_id=DEFAULT_TENANT_ID,
                    policy_id=policy_id,
                    baseline_type="ROLLING",
                    window_months=12,
                    refresh_reason="POLICY_SPECIFIC_BASELINE_CREATION",
                    db=db,
                )
                
                if baseline:
                    metrics = baseline.get('baseline_metrics', {})
                    util = metrics.get('util_rate_target_per_1000_mm', metrics.get('utilization_per_1k', 0))
                    cost = metrics.get('paid_pmpm_target', metrics.get('allowed_pmpm_target', metrics.get('cost_pmpm', 0)))
                    
                    print(f"   ✅ Created baseline: {baseline.get('baseline_id', 'N/A')[:8]}...")
                    print(f"      Utilization: {util:.2f} per 1K")
                    print(f"      Cost PMPM: ${cost:.2f}")
                    created += 1
                else:
                    print(f"   ⚠️  No data found for baseline computation")
                    failed += 1
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
                import traceback
                traceback.print_exc()
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
        
    finally:
        db.close()


if __name__ == "__main__":
    create_policy_specific_baselines()
