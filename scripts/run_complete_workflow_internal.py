#!/usr/bin/env python3
"""
Complete Workflow Script (Internal API):
1. Run daily job to generate source data and load to target database tables
2. Create baseline analyses for all policies
3. Generate observations for all remaining policies

This script uses internal API functions directly (no HTTP calls).
"""
import sys
import os
from datetime import datetime, timedelta, date
from uuid import UUID

# Add the API source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api', 'src'))

from uepi_api.database import SessionLocal
from uepi_api.storage_policies import list_policies
from uepi_api.services.data_generation_service import generate_claims_data_for_date
from uepi_api.services.daily_pipeline_service import load_daily_data_from_source
from uepi_api.observation_enhancement import create_observation_from_analysis
from uepi_api.storage_observations import list_observations
from uepi_api.models.analysis import Analysis, AnalysisStatus, ImpactAnalysisResult, BaselineAnalysisResult
from uepi_api.models.policy import Policy
from uepi_api.baseline_refresh import refresh_baseline
from sqlalchemy import and_

# Default tenant ID
TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

def run_daily_data_generation_and_loading():
    """Step 1: Generate claims data and load to database"""
    print("\n🔄 Step 1: Generating claims data and loading to database...")
    
    # Generate data for yesterday
    yesterday = date.today() - timedelta(days=1)
    print(f"   Generating claims data for {yesterday}...")
    
    try:
        result = generate_claims_data_for_date(TENANT_ID, yesterday)
        if result.get("error"):
            print(f"   ⚠️  Error generating data: {result.get('error')}")
            return False
        claims_generated = result.get("claims_generated", 0)
        print(f"   ✅ Generated {claims_generated} claims")
    except Exception as e:
        print(f"   ⚠️  Error generating data: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Load data from source to database
    print(f"   Loading data from source to database...")
    try:
        result = load_daily_data_from_source(TENANT_ID, yesterday)
        if result.get("error"):
            print(f"   ⚠️  Error loading data: {result.get('error')}")
            return False
        claims_loaded = result.get("claims_loaded", 0)
        print(f"   ✅ Loaded {claims_loaded} claims to database")
        return True
    except Exception as e:
        print(f"   ⚠️  Error loading data: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_baselines_for_all_policies():
    """Step 2: Create baseline analyses for all policies"""
    print("\n📊 Step 2: Creating baseline analyses for all policies...")
    
    db = SessionLocal()
    try:
        # Get all policies
        policies = list_policies(TENANT_ID)
        if not policies:
            print("   ⚠️  No policies found")
            return {"success": 0, "total": 0}
        
        print(f"   Found {len(policies)} policies")
        
        # First, refresh general baseline
        print("   Refreshing general baseline...")
        try:
            general_baseline = refresh_baseline(
                tenant_id=TENANT_ID,
                policy_id=None,
                baseline_type="ROLLING",
                window_months=12,
                refresh_reason="MANUAL",
                db=db
            )
            if general_baseline:
                print(f"   ✅ General baseline refreshed: {general_baseline.get('baseline_id')}")
            else:
                print(f"   ⚠️  General baseline refresh returned None (may not have data)")
        except Exception as e:
            print(f"   ⚠️  Error refreshing general baseline: {e}")
        
        # Refresh policy-specific baselines
        success_count = 0
        for policy in policies:
            policy_id = policy.get("id")
            policy_name = policy.get("name", "Unknown")
            
            if not policy_id:
                continue
            
            try:
                policy_id_uuid = UUID(str(policy_id)) if isinstance(policy_id, str) else policy_id
                print(f"   Creating baseline for: {policy_name} ({policy_id_uuid})...")
                
                policy_baseline = refresh_baseline(
                    tenant_id=TENANT_ID,
                    policy_id=policy_id_uuid,
                    baseline_type="ROLLING",
                    window_months=12,
                    refresh_reason="MANUAL",
                    db=db
                )
                
                if policy_baseline:
                    print(f"      ✅ Policy baseline created: {policy_baseline.get('baseline_id')}")
                    success_count += 1
                else:
                    print(f"      ⚠️  Policy baseline returned None (may not have data)")
                    
            except Exception as e:
                print(f"      ❌ Error creating baseline for {policy_name}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n   ✅ Baseline creation complete: {success_count}/{len(policies)} policies")
        return {"success": success_count, "total": len(policies)}
        
    finally:
        db.close()

def create_observations_for_all_policies():
    """Step 3: Create observations for all policies with completed analyses"""
    print("\n📈 Step 3: Creating observations for all policies...")
    
    db = SessionLocal()
    try:
        # Get all policies
        policies = list_policies(TENANT_ID)
        if not policies:
            print("   ⚠️  No policies found")
            return {"created": 0, "failed": 0}
        
        # Get all completed impact analyses
        analyses = db.query(Analysis).filter(
            and_(
                Analysis.tenant_id == TENANT_ID,
                Analysis.analysis_type == "IMPACT",
                Analysis.status == AnalysisStatus.COMPLETED.value
            )
        ).all()
        
        print(f"   Found {len(analyses)} completed impact analyses")
        
        # Get existing observations to avoid duplicates
        existing_observations = list_observations(TENANT_ID)
        existing_analysis_ids = set()
        for obs in existing_observations:
            if obs.get("analysis_id"):
                existing_analysis_ids.add(UUID(str(obs["analysis_id"])))
        
        print(f"   Found {len(existing_observations)} existing observations")
        
        created_count = 0
        failed_count = 0
        skipped_count = 0
        
        # Create observations for each analysis
        for analysis in analyses:
            analysis_id = analysis.id
            policy_id = analysis.policy_id
            
            # Skip if observation already exists
            if analysis_id in existing_analysis_ids:
                skipped_count += 1
                continue
            
            # Get analysis result
            impact_result = db.query(ImpactAnalysisResult).filter(
                ImpactAnalysisResult.analysis_id == analysis_id
            ).first()
            
            if not impact_result or not impact_result.result_data_json:
                print(f"   ⚠️  Analysis {analysis_id} has no result data, skipping...")
                failed_count += 1
                continue
            
            analysis_result = impact_result.result_data_json
            
            # Get policy name for logging
            policy_name = "Unknown"
            for p in policies:
                if str(p.get("id")) == str(policy_id):
                    policy_name = p.get("name", "Unknown")
                    break
            
            print(f"   Creating observation for {policy_name} (analysis {analysis_id})...")
            
            try:
                observation = create_observation_from_analysis(
                    tenant_id=TENANT_ID,
                    policy_id=policy_id,
                    analysis_id=analysis_id,
                    analysis_result=analysis_result,
                    data_period_id=None,
                )
                
                if observation:
                    obs_id = observation.get("observation_id")
                    print(f"      ✅ Created observation: {obs_id}")
                    created_count += 1
                else:
                    print(f"      ❌ Failed to create observation (returned None)")
                    failed_count += 1
                    
            except Exception as e:
                print(f"      ❌ Error creating observation: {e}")
                import traceback
                traceback.print_exc()
                failed_count += 1
        
        print(f"\n   ✅ Observation creation complete: {created_count} created, {skipped_count} skipped, {failed_count} failed")
        return {"created": created_count, "skipped": skipped_count, "failed": failed_count}
        
    finally:
        db.close()

def main():
    """Run the complete workflow"""
    print("=" * 80)
    print("🚀 COMPLETE WORKFLOW AUTOMATION (Internal API)")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Step 1: Generate data and load to database
    daily_success = run_daily_data_generation_and_loading()
    
    # Step 2: Create baselines for all policies
    baseline_result = create_baselines_for_all_policies()
    
    # Step 3: Create observations for all policies
    observation_result = create_observations_for_all_policies()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 WORKFLOW SUMMARY")
    print("=" * 80)
    print(f"Daily Data Generation & Loading: {'✅ Success' if daily_success else '❌ Failed'}")
    print(f"Baselines Created: {baseline_result.get('success', 0)}/{baseline_result.get('total', 0)}")
    print(f"Observations Created: {observation_result.get('created', 0)}")
    print(f"Observations Skipped: {observation_result.get('skipped', 0)}")
    print(f"Observations Failed: {observation_result.get('failed', 0)}")
    print(f"\nCompleted at: {datetime.now().isoformat()}")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Workflow failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
