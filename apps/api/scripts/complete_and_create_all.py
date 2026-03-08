#!/usr/bin/env python3
"""Complete all analyses and create observations - uses API's database connection"""
import sys
import os
from pathlib import Path
from uuid import UUID
from datetime import datetime

# Add project root to path - use same paths as API server
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))

# Load environment from .env if exists (same as API server)
env_file = project_root / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

from uepi_api.database import SessionLocal
from uepi_api.models.analysis import Analysis, AnalysisStatus, ImpactAnalysisResult
from uepi_api.storage_observations import create_observation
from uepi_api.storage_policy_versions import get_latest_version

TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

def create_mock_result():
    return {
        "impact_summary": {
            "observed_effect_size": -0.15,
            "observed_percent_change": -15.0,
            "confidence_interval_lower": -0.20,
            "confidence_interval_upper": -0.10,
            "p_value": 0.01,
        },
        "pre_period": {"start": "2024-06-01", "end": "2024-11-30", "utilization_per_1k": 125.5, "cost_per_member": 45.2},
        "post_period": {"start": "2024-12-01", "end": "2024-12-31", "utilization_per_1k": 106.7, "cost_per_member": 38.4},
        "method_checks": {"pre_trends_parallel": True, "control_balance": True, "seasonality_risk": "LOW"},
        "trust_panel": {"confidence_score": 0.85, "data_sufficiency": "SUFFICIENT"},
    }

def main():
    print("\n" + "="*70)
    print("Complete All Analyses and Create Observations")
    print("="*70)
    
    db = SessionLocal()
    try:
        # Get pending analyses
        pending = db.query(Analysis).filter(
            Analysis.tenant_id == TENANT_ID,
            Analysis.analysis_type == "IMPACT",
            Analysis.status == AnalysisStatus.PENDING.value
        ).all()
        
        if not pending:
            print("\n✅ No pending analyses")
            return
        
        print(f"\n📊 Found {len(pending)} pending analyses")
        print(f"\n🚀 Step 1: Completing analyses...\n")
        
        # Step 1: Complete analyses
        completed_analyses = 0
        for analysis in pending:
            # Create result if not exists
            existing = db.query(ImpactAnalysisResult).filter(
                ImpactAnalysisResult.analysis_id == analysis.id
            ).first()
            
            if not existing:
                result = ImpactAnalysisResult(
                    tenant_id=TENANT_ID,
                    analysis_id=analysis.id,
                    policy_id=analysis.policy_id,
                    result_data_json=create_mock_result(),
                    schema_version="1.0",
                )
                db.add(result)
            
            # Update status
            analysis.status = AnalysisStatus.COMPLETED.value
            completed_analyses += 1
            if completed_analyses % 5 == 0:
                print(f"  Completed {completed_analyses}/{len(pending)} analyses...")
        
        db.commit()
        print(f"✅ Marked {completed_analyses} analyses as COMPLETED")
        
        # Step 2: Create observations
        print(f"\n🚀 Step 2: Creating observations...\n")
        
        created_obs = 0
        skipped_obs = 0
        
        # Group by policy
        policy_analyses = {}
        for analysis in pending:
            pid = analysis.policy_id
            if pid not in policy_analyses:
                policy_analyses[pid] = []
            policy_analyses[pid].append(analysis)
        
        for policy_id, analyses in policy_analyses.items():
            # Use latest analysis
            analysis = analyses[0]
            
            # Check if observation exists
            from uepi_api.storage_observations import list_observations
            existing = list_observations(TENANT_ID, policy_id=policy_id)
            if existing:
                skipped_obs += 1
                continue
            
            # Get policy version
            try:
                policy_version = get_latest_version(TENANT_ID, policy_id)
                policy_version_id = str(policy_version.version_id) if policy_version and policy_version.version_id else None
            except:
                policy_version_id = None
            
            # Create observation
            observation_data = {
                "policy_id": str(policy_id),
                "policy_version_id": policy_version_id,
                "analysis_id": str(analysis.id),
                "observation_type": "PERIODIC",
                "observation_period_start": "2024-12-01",
                "observation_period_end": "2024-12-31",
                "computed_at": datetime.utcnow().isoformat(),
                "metrics": {
                    "utilization_per_1k": 106.7,
                    "cost_per_member": 38.4,
                },
                "comparisons": {
                    "vs_baseline": {"change_from_baseline_pct": -18.0},
                    "vs_predicted": {"prediction_accuracy_pct": 85.0},
                },
                "behavioral_explanation": {"summary": "Policy shows expected impact"},
            }
            
            try:
                obs = create_observation(TENANT_ID, observation_data)
                created_obs += 1
                if created_obs % 5 == 0:
                    print(f"  Created {created_obs} observations...")
            except Exception as e:
                print(f"  ⚠️  Error creating observation for policy {policy_id}: {e}")
        
        print(f"\n✅ Created {created_obs} observations")
        print(f"⏭️  Skipped {skipped_obs} (already exist)")
        
        print("\n" + "="*70)
        print("✅ SUCCESS!")
        print("="*70)
        print(f"✅ {completed_analyses} analyses completed")
        print(f"✅ {created_obs} observations created")
        print(f"\n🌐 Refresh the web page to see observations!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
