#!/usr/bin/env python3
"""Run pending impact analyses synchronously (without worker) - calls worker task directly"""
import sys
import os
from pathlib import Path
from uuid import UUID
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
# Add packages/common/src to path for uepi_common
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "apps" / "worker" / "src"))

# Set environment variables for database connection
os.environ.setdefault("DATABASE_URL", os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/uepi"))

from uepi_api.database import SessionLocal
from uepi_api.models.analysis import Analysis, AnalysisStatus, AnalysisConfig, ImpactAnalysisResult
from uepi_api.models.policy import Policy, PolicyVersion

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def run_analysis_sync(analysis_id: UUID, tenant_id: UUID):
    """Run a single analysis synchronously by calling worker task function directly"""
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
        
        print(f"   🚀 Running analysis {analysis_id}...")
        
        # Get policy
        policy = db.query(Policy).filter(
            Policy.id == analysis.policy_id,
            Policy.tenant_id == tenant_id
        ).first()
        
        if not policy:
            print(f"   ❌ Policy not found")
            return False
        
        # Get policy version
        version = db.query(PolicyVersion).filter(
            PolicyVersion.policy_id == analysis.policy_id,
            PolicyVersion.tenant_id == tenant_id
        ).order_by(PolicyVersion.version_number.desc()).first()
        
        if not version:
            print(f"   ❌ Policy version not found")
            return False
        
        # Get analysis config
        config = db.query(AnalysisConfig).filter(
            AnalysisConfig.analysis_id == analysis_id
        ).first()
        
        if not config:
            print(f"   ❌ Analysis config not found")
            return False
        
        treatment_filters = config.treatment_filters if hasattr(config, 'treatment_filters') else {}
        control_filters = config.control_filters if hasattr(config, 'control_filters') else None
        pre_months = config.pre_window_months if hasattr(config, 'pre_window_months') else 6
        post_months = config.post_window_months if hasattr(config, 'post_window_months') else 6
        
        # Build config dict
        config_dict = {
            "treatment_filters": treatment_filters,
            "control_filters": control_filters,
            "matching_strategy": config.matching_strategy if hasattr(config, 'matching_strategy') else None,
            "pre_window_months": pre_months,
            "post_window_months": post_months,
        }
        
        # Call worker task function directly (synchronously)
        print(f"   ⏳ Running impact analysis...")
        try:
            from uepi_worker.tasks import policy_impact_job
            from celery import Task
            
            # Create a mock task object
            class MockTask:
                def __init__(self):
                    self.request = type('obj', (object,), {'id': str(analysis_id)})()
                    self.max_retries = 3
                    self.retry = lambda *args, **kwargs: None
            
            mock_task = MockTask()
            
            # Call the worker function directly
            result = policy_impact_job(
                mock_task,
                str(tenant_id),
                str(analysis.policy_id),
                str(analysis_id),
                config_dict
            )
            
            if result.get("status") == "completed":
                print(f"   ✅ Completed!")
                return True
            else:
                print(f"   ❌ Failed: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error running analysis: {str(e)[:200]}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    print("\n" + "="*60)
    print("Running Pending Impact Analyses Synchronously")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Get all pending impact analyses
        pending_analyses = db.query(Analysis).filter(
            Analysis.tenant_id == DEFAULT_TENANT_ID,
            Analysis.analysis_type == "IMPACT",
            Analysis.status == AnalysisStatus.PENDING.value
        ).limit(5).all()  # Limit to 5 for testing
        
        if not pending_analyses:
            print("\n✅ No pending analyses found")
            return
        
        print(f"\n📊 Found {len(pending_analyses)} pending analyses (processing first 5)")
        print(f"\n🚀 Running analyses...\n")
        
        completed = 0
        failed = 0
        
        for i, analysis in enumerate(pending_analyses, 1):
            policy_id = analysis.policy_id
            analysis_id = analysis.id
            
            # Get policy name for display
            policy = db.query(Policy).filter(Policy.id == policy_id).first()
            policy_name = policy.name if policy else "Unknown"
            
            print(f"[{i}/{len(pending_analyses)}] {policy_name[:50]} ({policy_id})")
            
            if run_analysis_sync(analysis_id, DEFAULT_TENANT_ID):
                completed += 1
            else:
                failed += 1
        
        # Summary
        print("\n" + "="*60)
        print("Summary")
        print("="*60)
        print(f"✅ Completed: {completed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total processed: {len(pending_analyses)}")
        print("="*60)
        
        if completed > 0:
            print(f"\n🎉 {completed} analyses completed!")
            print("   The observation monitor will automatically create observations now.")
            print("   Run this script again to process more analyses.")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
