#!/usr/bin/env python3
"""
Cleanup script to remove all existing baselines and observations
"""
import requests
from pathlib import Path

API_BASE_URL = "http://localhost:8000/api/v1"

def cleanup_baselines():
    """Delete all baselines"""
    print("🧹 Cleaning up baselines...")
    
    # Get all baselines
    response = requests.get(f"{API_BASE_URL}/baselines", timeout=30)
    if response.status_code != 200:
        print(f"   ⚠️  Could not fetch baselines: {response.status_code}")
        return 0
    
    baselines = response.json()
    print(f"   Found {len(baselines)} baselines")
    
    deleted = 0
    for baseline in baselines:
        baseline_id = baseline.get("baseline_id") or baseline.get("id")
        if not baseline_id:
            continue
        
        # Note: We'll need to add a DELETE endpoint, or use direct DB access
        # For now, we'll just report what needs to be deleted
        print(f"   Would delete: {baseline_id[:8]}...")
        deleted += 1
    
    print(f"   ✅ {deleted} baselines marked for deletion")
    return deleted

def cleanup_observations():
    """Delete all observations"""
    print("🧹 Cleaning up observations...")
    
    # Get all observations
    response = requests.get(f"{API_BASE_URL}/observations", timeout=30)
    if response.status_code != 200:
        print(f"   ⚠️  Could not fetch observations: {response.status_code}")
        return 0
    
    observations = response.json()
    print(f"   Found {len(observations)} observations")
    
    deleted = 0
    for obs in observations:
        obs_id = obs.get("id")
        if not obs_id:
            continue
        
        # Note: We'll need to add a DELETE endpoint, or use direct DB access
        print(f"   Would delete: {obs_id[:8]}...")
        deleted += 1
    
    print(f"   ✅ {deleted} observations marked for deletion")
    return deleted

def cleanup_via_database():
    """Cleanup via direct database access"""
    print("🧹 Cleaning up via database...")
    
    import sys
    from pathlib import Path
    # Add API src to path
    api_src = Path(__file__).parent.parent / "apps" / "api" / "src"
    sys.path.insert(0, str(api_src))
    
    from uepi_api.database import SessionLocal
    from uepi_api.models.baseline import Baseline
    from uepi_api.models.observation import Observation
    from uuid import UUID
    
    tenant_id = UUID("00000000-0000-0000-0000-000000000001")
    db = SessionLocal()
    
    try:
        # Delete observations
        obs_count = db.query(Observation).filter(Observation.tenant_id == tenant_id).count()
        db.query(Observation).filter(Observation.tenant_id == tenant_id).delete()
        print(f"   ✅ Deleted {obs_count} observations")
        
        # Delete baselines
        baseline_count = db.query(Baseline).filter(Baseline.tenant_id == tenant_id).count()
        db.query(Baseline).filter(Baseline.tenant_id == tenant_id).delete()
        print(f"   ✅ Deleted {baseline_count} baselines")
        
        db.commit()
        print(f"\n✅ Cleanup complete: {obs_count} observations, {baseline_count} baselines deleted")
        return obs_count + baseline_count
    except Exception as e:
        db.rollback()
        print(f"   ❌ Error: {e}")
        return 0
    finally:
        db.close()

def main():
    print("="*80)
    print("🧹 CLEANUP BASELINES AND OBSERVATIONS")
    print("="*80)
    
    # Cleanup via database (more reliable)
    total_deleted = cleanup_via_database()
    
    print("\n" + "="*80)
    print(f"✅ Cleanup complete: {total_deleted} records deleted")
    print("="*80)

if __name__ == "__main__":
    main()
