#!/usr/bin/env python3
"""Continue workflow: Load data via pipelines, run analyses"""
import sys
import os
import time
import requests
from pathlib import Path
from uuid import UUID

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.database import SessionLocal
from uepi_api.repositories.canonical_data import CanonicalDataRepository
from uepi_api.storage_auth import DEFAULT_TENANT_ID

API_BASE = os.getenv("API_URL", "http://localhost:8000/api/v1")
HEADERS = {
    "Authorization": "Bearer dev-token-123",
    "Content-Type": "application/json"
}

def check_api():
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def load_data_via_pipelines():
    """Load data into database via pipelines"""
    print("\n" + "="*60)
    print("Loading Data via Pipelines")
    print("="*60)
    
    if not check_api():
        print("  ❌ API server is not running")
        print("  💡 Start API with: ./start_api.sh or python -m uepi_api.main")
        return False
    
    # Get pipelines
    try:
        response = requests.get(f"{API_BASE}/pipelines", headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"  ❌ Failed to get pipelines: {response.status_code}")
            return False
        
        pipelines = response.json()
        if not isinstance(pipelines, list):
            pipelines = []
        
        print(f"  Found {len(pipelines)} pipelines")
        
        # Find source files
        source_dir = Path("apps/api/data/source_data") / str(DEFAULT_TENANT_ID)
        if not source_dir.exists():
            print(f"  ❌ Source data directory not found: {source_dir}")
            return False
        
        # Map files to pipeline types
        file_map = {
            "CLAIMS_LINES": source_dir / "claims_lines.csv",
            "ELIGIBILITY_ENROLLMENT": source_dir / "enrollment.csv",
            "PROVIDER_MASTER": source_dir / "providers.csv",
        }
        
        success = 0
        for pipeline in pipelines[:3]:  # Run first 3 matching pipelines
            pipeline_id = pipeline.get("id") or pipeline.get("pipeline_id")
            name = pipeline.get("name", "Unknown")
            target_type = pipeline.get("target_dataset_type") or pipeline.get("target_type")
            
            source_file = file_map.get(target_type)
            if not source_file or not source_file.exists():
                continue
            
            print(f"\n  Running: {name} ({target_type})...")
            print(f"    Source: {source_file.name} ({source_file.stat().st_size / (1024*1024):.1f} MB)")
            
            try:
                with open(source_file, 'rb') as f:
                    files = {'file': (source_file.name, f, 'text/csv')}
                    response = requests.post(
                        f"{API_BASE}/pipelines/{pipeline_id}/run",
                        headers={"Authorization": HEADERS["Authorization"]},
                        files=files,
                        timeout=600  # 10 minutes
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    records = result.get("records_succeeded", 0)
                    print(f"    ✅ Loaded {records:,} records")
                    success += 1
                else:
                    print(f"    ❌ Failed: {response.status_code}")
                    print(f"    {response.text[:200]}")
            except Exception as e:
                print(f"    ❌ Error: {e}")
            
            time.sleep(2)
        
        print(f"\n  ✅ Completed {success} pipeline(s)")
        return success > 0
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_data():
    """Verify data is in database"""
    print("\n" + "="*60)
    print("Verifying Data in Database")
    print("="*60)
    
    try:
        db = SessionLocal()
        try:
            repo = CanonicalDataRepository(db)
            
            claims = repo.count_claims_lines(DEFAULT_TENANT_ID)
            enrollment = repo.count_enrollment_records(DEFAULT_TENANT_ID)
            providers = repo.count_provider_records(DEFAULT_TENANT_ID)
            
            print(f"  Claims Lines: {claims:,}")
            print(f"  Enrollment Records: {enrollment:,}")
            print(f"  Provider Records: {providers:,}")
            
            if claims > 0 or enrollment > 0 or providers > 0:
                print("  ✅ Data is in database")
                return True
            else:
                print("  ⚠️  No data in database")
                return False
        finally:
            db.close()
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def run_baseline():
    """Run baseline analysis"""
    print("\n" + "="*60)
    print("Running Baseline Analysis")
    print("="*60)
    
    if not check_api():
        print("  ❌ API server is not running")
        return False
    
    try:
        data = {
            "name": "Comprehensive Baseline Analysis",
            "n_clusters": 5,
            "start_date": "2023-01-01",
            "end_date": "2024-12-31",
        }
        
        print("  Starting baseline analysis (this may take several minutes)...")
        response = requests.post(
            f"{API_BASE}/analyses/baseline",
            headers=HEADERS,
            json=data,
            timeout=600
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Baseline analysis completed")
            print(f"    Analysis ID: {result.get('id')}")
            return True
        else:
            print(f"  ⚠️  Response: {response.status_code}")
            print(f"    {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print("  ⚠️  Baseline analysis timed out (may still be running)")
        print("  💡 Check API logs or web UI for progress")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def run_data_quality():
    """Run data quality validation"""
    print("\n" + "="*60)
    print("Running Data Quality Validation")
    print("="*60)
    
    if not check_api():
        print("  ❌ API server is not running")
        return False
    
    try:
        print("  Triggering data quality validation...")
        response = requests.post(
            f"{API_BASE}/data-quality/validate",
            headers=HEADERS,
            timeout=300
        )
        
        if response.status_code in [200, 202]:
            print("  ✅ Data quality validation started")
            print("  💡 This runs in background - check status via API or web UI")
            return True
        else:
            print(f"  ⚠️  Response: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("="*60)
    print("CONTINUING DATABASE WORKFLOW")
    print("="*60)
    print("\nSteps:")
    print("  1. Load data via pipelines")
    print("  2. Verify data in database")
    print("  3. Run baseline analysis")
    print("  4. Run data quality validation")
    
    results = {}
    
    # Step 1: Load data
    results['load_data'] = load_data_via_pipelines()
    
    # Step 2: Verify
    results['verify'] = verify_data()
    
    # Step 3: Baseline
    if results['verify']:
        results['baseline'] = run_baseline()
    else:
        print("\n" + "="*60)
        print("Skipping Baseline (no data)")
        print("="*60)
        results['baseline'] = None
    
    # Step 4: Data Quality
    if results['verify']:
        results['dq'] = run_data_quality()
    else:
        print("\n" + "="*60)
        print("Skipping Data Quality (no data)")
        print("="*60)
        results['dq'] = None
    
    # Summary
    print("\n" + "="*60)
    print("WORKFLOW SUMMARY")
    print("="*60)
    for step, result in results.items():
        if result is None:
            status = "⏭️  SKIPPED"
        elif result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"  {step.upper()}: {status}")
    
    print("\n" + "="*60)
    print("✅ WORKFLOW COMPLETE")
    print("="*60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

