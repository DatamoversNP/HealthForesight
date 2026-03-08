#!/usr/bin/env python3
"""
Cleanup baselines and observations from database
Run from project root: python3 scripts/cleanup_db.py
"""
import sys
from pathlib import Path

# Add necessary paths
project_root = Path(__file__).parent.parent
api_src = project_root / "apps" / "api" / "src"
common_src = project_root / "packages" / "common" / "src"

sys.path.insert(0, str(api_src))
sys.path.insert(0, str(common_src))

from uepi_api.database import SessionLocal
from uepi_api.models.baseline import Baseline
from uepi_api.models.observation import Observation
from uuid import UUID

def main():
    print("="*80)
    print("🧹 CLEANUP BASELINES AND OBSERVATIONS")
    print("="*80)
    
    tenant_id = UUID("00000000-0000-0000-0000-000000000001")
    db = SessionLocal()
    
    try:
        # Count existing records
        obs_count = db.query(Observation).filter(Observation.tenant_id == tenant_id).count()
        baseline_count = db.query(Baseline).filter(Baseline.tenant_id == tenant_id).count()
        
        print(f"\nFound:")
        print(f"  Observations: {obs_count}")
        print(f"  Baselines: {baseline_count}")
        
        if obs_count == 0 and baseline_count == 0:
            print("\n✅ Nothing to clean up!")
            return
        
        # Delete observations
        if obs_count > 0:
            db.query(Observation).filter(Observation.tenant_id == tenant_id).delete()
            print(f"\n✅ Deleted {obs_count} observations")
        
        # Delete baselines
        if baseline_count > 0:
            db.query(Baseline).filter(Baseline.tenant_id == tenant_id).delete()
            print(f"✅ Deleted {baseline_count} baselines")
        
        db.commit()
        print(f"\n✅ Cleanup complete!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
