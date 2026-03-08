#!/usr/bin/env python3
"""
Validate and Run All Pipelines
"""
import sys
import os
from pathlib import Path
import requests
import json
import time

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'packages/common/src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'apps/api/src')))

API_BASE = "http://localhost:8000/api/v1"
HEADERS = {
    "Authorization": "Bearer demo-token",
    "Content-Type": "application/json"
}

def validate_pipelines():
    """Validate all pipelines"""
    print("🔍 Validating Pipelines")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/pipelines", headers=HEADERS, timeout=10)
        response.raise_for_status()
        pipelines = response.json()
        
        print(f"✅ Found {len(pipelines)} pipelines")
        
        # Validate each pipeline
        valid_count = 0
        invalid_count = 0
        
        for pipeline in pipelines:
            pipeline_id = pipeline.get("pipeline_id") or pipeline.get("id")
            pipeline_name = pipeline.get("pipeline_name") or pipeline.get("name", "Unknown")
            
            # Basic validation checks
            issues = []
            
            if not pipeline_id:
                issues.append("Missing pipeline_id")
            if not pipeline.get("target_dataset_type"):
                issues.append("Missing target_dataset_type")
            if not pipeline.get("field_mappings"):
                issues.append("Missing field_mappings")
            if not pipeline.get("active", True):
                issues.append("Pipeline is inactive")
            
            if issues:
                print(f"  ⚠️  {pipeline_name}: {', '.join(issues)}")
                invalid_count += 1
            else:
                print(f"  ✅ {pipeline_name}")
                valid_count += 1
        
        print(f"\n📊 Validation Summary:")
        print(f"   ✅ Valid: {valid_count}")
        print(f"   ⚠️  Issues: {invalid_count}")
        print(f"   📦 Total: {len(pipelines)}")
        
        return pipelines, valid_count == len(pipelines)
        
    except Exception as e:
        print(f"❌ Error validating pipelines: {e}")
        return [], False

def run_pipelines(pipelines):
    """Run all active pipelines"""
    print("\n🚀 Running All Pipelines")
    print("=" * 60)
    
    active_pipelines = [p for p in pipelines if p.get("active", True)]
    print(f"📦 Running {len(active_pipelines)} active pipelines\n")
    
    results = []
    
    for i, pipeline in enumerate(active_pipelines, 1):
        pipeline_id = pipeline.get("pipeline_id") or pipeline.get("id")
        pipeline_name = pipeline.get("pipeline_name") or pipeline.get("name", "Unknown")
        
        if not pipeline_id:
            print(f"[{i}/{len(active_pipelines)}] ⏭️  Skipping {pipeline_name} (no ID)")
            continue
        
        print(f"[{i}/{len(active_pipelines)}] 🔄 Running: {pipeline_name}")
        
        try:
            response = requests.post(
                f"{API_BASE}/pipelines/{pipeline_id}/run",
                headers=HEADERS,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status", "UNKNOWN")
                print(f"   ✅ Started successfully (Status: {status})")
                results.append({
                    "pipeline": pipeline_name,
                    "status": "success",
                    "result": result
                })
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text[:100]}")
                results.append({
                    "pipeline": pipeline_name,
                    "status": "failed",
                    "error": response.text[:200]
                })
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:200]}")
            results.append({
                "pipeline": pipeline_name,
                "status": "error",
                "error": str(e)[:200]
            })
        
        # Small delay between runs
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Execution Summary")
    print("=" * 60)
    
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful
    
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📦 Total: {len(results)}")
    
    if failed > 0:
        print("\n⚠️  Failed Pipelines:")
        for r in results:
            if r["status"] != "success":
                print(f"   - {r['pipeline']}: {r.get('error', 'Unknown error')}")
    
    return results

def main():
    print("🔍 Validating and Running All Pipelines")
    print("=" * 60)
    print()
    
    # Step 1: Validate pipelines
    pipelines, all_valid = validate_pipelines()
    
    if not pipelines:
        print("\n❌ No pipelines found. Cannot proceed.")
        return
    
    if not all_valid:
        print("\n⚠️  Some pipelines have validation issues, but proceeding...")
    
    # Step 2: Run pipelines
    print()
    results = run_pipelines(pipelines)
    
    print("\n✅ Complete!")
    print("\n💡 Next steps:")
    print("   - Check pipeline status at: http://localhost:3050/pipeline-monitoring")
    print("   - View data at: http://localhost:3050/data-explorer")

if __name__ == "__main__":
    main()


