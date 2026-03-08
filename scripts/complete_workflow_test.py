#!/usr/bin/env python3
"""Complete workflow test - Generate data, create baselines, generate predicted impacts, create observations"""
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from uuid import UUID
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from sqlalchemy.orm import Session
from uepi_api.database import SessionLocal
from uepi_api.services.data_generation_service import generate_claims_data_for_date
from uepi_api.services.daily_pipeline_service import load_daily_data_from_source
from uepi_api.baseline_refresh import refresh_baseline
from uepi_api.storage_policies import list_policies
from uepi_api.storage_baselines import get_latest_baseline
from uepi_api.routers.observations import create_observation_from_analysis_route
from uepi_api.routers.analyses import create_impact_analysis
from uepi_api.models.analysis import Analysis, AnalysisStatus
from uepi_api.models.policy import Policy

def print_step(step_num: int, description: str):
    """Print formatted step header"""
    print("\n" + "=" * 80)
    print(f"STEP {step_num}: {description}")
    print("=" * 80)

def main():
    """Complete workflow test"""
    tenant_id = UUID('00000000-0000-0000-0000-000000000001')
    db = SessionLocal()
    
    try:
        # STEP 1: Generate data for last 3 days
        print_step(1, "GENERATING CLAIMS DATA FOR LAST 3 DAYS")
        today = datetime.now().date()
        dates_to_generate = [
            today - timedelta(days=1),  # Yesterday
            today - timedelta(days=2),  # 2 days ago
            today - timedelta(days=3),  # 3 days ago
        ]
        
        total_claims = 0
        for target_date in dates_to_generate:
            print(f"\n📅 Generating data for {target_date}...")
            result = generate_claims_data_for_date(
                tenant_id=tenant_id,
                target_date=target_date,
                member_count=10000,
                claims_per_member=2.5,
                db=db,
            )
            if result.get("success"):
                claims_count = result.get("claims_loaded", 0)
                total_claims += claims_count
                print(f"✅ Generated and loaded {claims_count} claims")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        print(f"\n✅ Total: {total_claims} claims generated across 3 days")
        
        # STEP 2: Create General Baseline
        print_step(2, "CREATING GENERAL BASELINE")
        general_baseline = refresh_baseline(
            tenant_id=tenant_id,
            policy_id=None,
            baseline_type="ROLLING",
            window_months=12,
            refresh_reason="INITIAL_SETUP",
        )
        if general_baseline:
            print(f"✅ General baseline created: {general_baseline.get('baseline_id')}")
        else:
            print("❌ Failed to create general baseline")
            return
        
        # STEP 3: Get all policies and create policy-specific baselines
        print_step(3, "CREATING POLICY-SPECIFIC BASELINES")
        policies = list_policies(tenant_id)
        print(f"Found {len(policies)} policies")
        
        policy_baselines = {}
        for policy in policies:
            policy_id = UUID(policy.get("id") or policy.get("policy_id"))
            policy_name = policy.get("name", "Unknown")
            print(f"\n📋 Creating baseline for policy: {policy_name}")
            
            baseline = refresh_baseline(
                tenant_id=tenant_id,
                policy_id=policy_id,
                baseline_type="ROLLING",
                window_months=12,
                refresh_reason="INITIAL_SETUP",
            )
            if baseline:
                policy_baselines[str(policy_id)] = baseline
                print(f"✅ Policy-specific baseline created: {baseline.get('baseline_id')}")
            else:
                print(f"⚠️  Could not create policy-specific baseline (may not have enough data)")
        
        print(f"\n✅ Created {len(policy_baselines)} policy-specific baselines")
        
        # STEP 4: Generate predicted impacts for all policies
        print_step(4, "GENERATING PREDICTED IMPACTS FOR ALL POLICIES")
        print("Note: This requires the API endpoint to be called")
        print("Use: POST /api/v1/policies/generate-predicted-impact")
        print("Or use the UI button: 'Generate Predicted Impact (All)' in Policy Catalog")
        
        # STEP 5: Create observations for each policy
        print_step(5, "CREATING OBSERVATIONS FOR EACH POLICY")
        observations_created = 0
        
        for policy in policies:
            policy_id = UUID(policy.get("id") or policy.get("policy_id"))
            policy_name = policy.get("name", "Unknown")
            
            # Get latest impact analysis for this policy
            analyses = db.query(Analysis).filter(
                Analysis.tenant_id == tenant_id,
                Analysis.policy_id == policy_id,
                Analysis.analysis_type == "IMPACT",
                Analysis.status == AnalysisStatus.COMPLETED.value,
            ).order_by(Analysis.created_at.desc()).all()
            
            if not analyses:
                print(f"⚠️  No completed impact analysis found for policy: {policy_name}")
                continue
            
            latest_analysis = analyses[0]
            print(f"\n📊 Creating observation for policy: {policy_name}")
            print(f"   Using analysis: {latest_analysis.id}")
            
            # Create observation
            try:
                from uepi_api.routers.observations import create_observation_from_analysis
                from uepi_api.storage_analyses import get_analysis_result
                
                # Get analysis result
                analysis_result_data = get_analysis_result(latest_analysis.id, tenant_id)
                if not analysis_result_data:
                    print(f"   ⚠️  No analysis result found")
                    continue
                
                observation = create_observation_from_analysis(
                    tenant_id=tenant_id,
                    policy_id=policy_id,
                    analysis_id=latest_analysis.id,
                    analysis_result=analysis_result_data,
                    data_period_id=None,
                )
                
                if observation:
                    observations_created += 1
                    print(f"   ✅ Observation created: {observation.get('observation_id')}")
                else:
                    print(f"   ❌ Failed to create observation")
            except Exception as e:
                print(f"   ❌ Error creating observation: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n✅ Created {observations_created} observations")
        
        # STEP 6: Summary
        print_step(6, "WORKFLOW COMPLETE - SUMMARY")
        print(f"✅ Generated {total_claims} claims across 3 days")
        print(f"✅ Created 1 general baseline")
        print(f"✅ Created {len(policy_baselines)} policy-specific baselines")
        print(f"✅ Created {observations_created} observations")
        print("\n📝 Next Steps:")
        print("   1. Use UI to generate predicted impacts for all policies")
        print("   2. View observations in Observation Analysis page")
        print("   3. Compare against baselines and predicted impacts")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
