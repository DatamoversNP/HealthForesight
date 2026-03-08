#!/usr/bin/env python3
"""Re-queue pending analyses to Celery worker"""
import sys
import os
from pathlib import Path
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "apps" / "worker" / "src"))

from uepi_api.database import SessionLocal
from uepi_api.models.analysis import Analysis, AnalysisStatus, AnalysisConfig
from uepi_worker.main import app  # Get Celery app

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def requeue_analysis(analysis_id: UUID, tenant_id: UUID):
    """Re-queue a single analysis to Celery"""
    db = SessionLocal()
    try:
        # Get analysis
        analysis = db.query(Analysis).filter(
            Analysis.id == analysis_id,
            Analysis.tenant_id == tenant_id
        ).first()
        
        if not analysis:
            print(f"   ❌ Analysis {analysis_id} not found")
            return False
        
        if analysis.status == AnalysisStatus.COMPLETED.value:
            print(f"   ⏭️  Already completed")
            return True
        
        # Get config
        config = db.query(AnalysisConfig).filter(
            AnalysisConfig.analysis_id == analysis_id
        ).first()
        
        if not config:
            print(f"   ❌ Config not found")
            return False
        
        # Build config dict
        config_dict = {
            "treatment_filters": config.treatment_filters if hasattr(config, 'treatment_filters') else {},
            "control_filters": config.control_filters if hasattr(config, 'control_filters') else None,
            "matching_strategy": config.matching_strategy if hasattr(config, 'matching_strategy') else None,
            "pre_window_months": config.pre_window_months if hasattr(config, 'pre_window_months') else 6,
            "post_window_months": config.post_window_months if hasattr(config, 'post_window_months') else 6,
        }
        
        # Queue to Celery using send_task to avoid import issues
        print(f"   🚀 Queuing to worker...")
        app.send_task(
            'uepi_worker.tasks.policy_impact_job',
            args=[
                str(tenant_id),
                str(analysis.policy_id),
                str(analysis_id),
                config_dict
            ]
        )
        
        print(f"   ✅ Queued successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    print("\n" + "="*60)
    print("Re-queuing Pending Analyses to Worker")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Get all pending impact analyses
        pending_analyses = db.query(Analysis).filter(
            Analysis.tenant_id == DEFAULT_TENANT_ID,
            Analysis.analysis_type == "IMPACT",
            Analysis.status == AnalysisStatus.PENDING.value
        ).all()
        
        if not pending_analyses:
            print("\n✅ No pending analyses found")
            return
        
        print(f"\n📊 Found {len(pending_analyses)} pending analyses")
        print(f"\n🚀 Re-queuing to worker...\n")
        
        queued = 0
        failed = 0
        
        for i, analysis in enumerate(pending_analyses, 1):
            analysis_id = analysis.id
            policy_id = analysis.policy_id
            
            # Get policy name
            from uepi_api.models.policy import Policy
            policy = db.query(Policy).filter(Policy.id == policy_id).first()
            policy_name = policy.name if policy else "Unknown"
            
            print(f"[{i}/{len(pending_analyses)}] {policy_name[:50]} ({policy_id})")
            
            if requeue_analysis(analysis_id, DEFAULT_TENANT_ID):
                queued += 1
            else:
                failed += 1
        
        # Summary
        print("\n" + "="*60)
        print("Summary")
        print("="*60)
        print(f"✅ Queued: {queued}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total: {len(pending_analyses)}")
        print("="*60)
        
        if queued > 0:
            print(f"\n🎉 {queued} analyses queued to worker!")
            print("   Worker should start processing them now.")
            print("   Check status: cd apps/api/scripts && ./check_status.sh")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
