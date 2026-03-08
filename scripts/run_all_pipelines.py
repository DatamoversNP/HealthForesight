#!/usr/bin/env python3
"""
Run All Pipelines with Synthetic Data
Executes all preconfigured pipelines with matching synthetic data files
"""
import sys
import os
from pathlib import Path
from uuid import UUID
from typing import List
import requests
import json

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../packages/common/src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api/src')))

# API base URL
API_BASE = "http://localhost:8000/api/v1"

# Synthetic data directory
SYNTHETIC_DATA_DIR = Path(__file__).parent.parent / "data" / "source_data" / "synthetic"

# Pipeline to data file mapping (prefer CSV files)
PIPELINE_DATA_MAPPING = {
    "Claims Lines Pipeline": {
        "files": ["claims/2025/*.csv", "claims/2024/*.csv", "claims/2023/*.csv"],
        "pattern": "claims",
    },
    "Member Master Pipeline": {
        "files": ["member_master.csv", "member_master.parquet"],
        "pattern": "member_master",
    },
    "Eligibility Enrollment Pipeline": {
        "files": ["eligibility_enrollment.csv", "eligibility_enrollment.parquet"],
        "pattern": "eligibility",
    },
    "Member Risk Stratification Pipeline": {
        "files": ["risk_stratification.csv", "risk_stratification.parquet"],
        "pattern": "risk",
    },
    "Claim Header Pipeline": {
        "files": ["claim_header.csv", "claim_header.parquet"],
        "pattern": "claim_header",
    },
    "Episode of Care Pipeline": {
        "files": ["episode_of_care.csv", "episode_of_care.parquet"],
        "pattern": "episode",
    },
    "Provider Master Pipeline": {
        "files": ["provider_master.csv", "provider_master.parquet"],
        "pattern": "provider_master",
    },
    "Facility Master Pipeline": {
        "files": ["facility_master.csv", "facility_master.parquet"],
        "pattern": "facility",
    },
    "Network Configuration Pipeline": {
        "files": ["network_configuration.csv", "network_configuration.parquet"],
        "pattern": "network",
    },
    "Provider Contract Pipeline": {
        "files": ["provider_contract.csv", "provider_contract.parquet"],
        "pattern": "contract",
    },
    "Pharmacy Claims Pipeline": {
        "files": ["pharmacy_claims.csv", "pharmacy_claims.parquet"],
        "pattern": "pharmacy",
    },
    "Benefit Design Pipeline": {
        "files": ["benefit_design.csv", "benefit_design.parquet"],
        "pattern": "benefit",
    },
    "Member Accumulator Pipeline": {
        "files": ["member_accumulator.csv", "member_accumulator.parquet"],
        "pattern": "accumulator",
    },
    "Prior Authorization Request Pipeline": {
        "files": ["prior_authorization_request.csv", "prior_authorization_request.parquet"],
        "pattern": "prior_authorization",
    },
    "Concurrent Review Pipeline": {
        "files": ["concurrent_review.csv", "concurrent_review.parquet"],
        "pattern": "concurrent",
    },
    "Appeal Grievance Pipeline": {
        "files": ["appeal_grievance.csv", "appeal_grievance.parquet"],
        "pattern": "appeal",
    },
    "Member Diagnosis Pipeline": {
        "files": ["member_diagnosis.csv", "member_diagnosis.parquet"],
        "pattern": "diagnosis",
    },
    "Problem List Pipeline": {
        "files": ["problem_list.csv", "problem_list.parquet"],
        "pattern": "problem",
    },
    "Referral Pipeline": {
        "files": ["referral.csv", "referral.parquet"],
        "pattern": "referral",
    },
    "Care Management Enrollment Pipeline": {
        "files": ["care_management_enrollment.csv", "care_management_enrollment.parquet"],
        "pattern": "care_management",
    },
    "Call Center Contact Pipeline": {
        "files": ["call_center_contact.csv", "call_center_contact.parquet"],
        "pattern": "call_center",
    },
    "Market Event Pipeline": {
        "files": ["market_event.csv", "market_event.parquet"],
        "pattern": "market_event",
    },
}


def get_pipelines():
    """Get all pipelines from API"""
    try:
        response = requests.get(f"{API_BASE}/pipelines", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Failed to get pipelines: {e}")
        return []


def find_data_files(pipeline_name: str):
    """Find ALL matching data files for pipeline"""
    mapping = PIPELINE_DATA_MAPPING.get(pipeline_name)
    if not mapping:
        return []
    
    found_files = []
    
    # Try to find files matching the pattern
    for pattern in mapping["files"]:
        if "*" in pattern:
            # Glob pattern - handle nested paths
            parts = pattern.split("/")
            base_dir = SYNTHETIC_DATA_DIR
            for i, part in enumerate(parts):
                if "*" in part:
                    # This is the file pattern
                    file_pattern = "/".join(parts[i:])
                    break
                else:
                    base_dir = base_dir / part
            else:
                # No wildcard found, treat last as file
                file_pattern = parts[-1]
            
            files = list(base_dir.rglob(file_pattern))
            if files:
                # Prefer CSV files for easier processing (skip parquet if CSV available)
                csv_files = [f for f in files if f.suffix == '.csv']
                parquet_files = [f for f in files if f.suffix == '.parquet']
                if csv_files:
                    found_files.extend(csv_files)
                elif parquet_files:
                    # Only add parquet if no CSV files found
                    found_files.extend(parquet_files)
        else:
            # Direct file name
            file_path = SYNTHETIC_DATA_DIR / pattern
            if file_path.exists():
                found_files.append(file_path)
    
    # Fallback: search by pattern
    if not found_files:
        pattern = mapping["pattern"]
        # Prefer CSV files
        csv_files = []
        for file_path in SYNTHETIC_DATA_DIR.rglob("*.csv"):
            if pattern.lower() in file_path.name.lower():
                csv_files.append(file_path)
        
        if csv_files:
            found_files.extend(csv_files)
        else:
            # Only try parquet if no CSV found
            for file_path in SYNTHETIC_DATA_DIR.rglob("*.parquet"):
                if pattern.lower() in file_path.name.lower():
                    found_files.append(file_path)
    
    # Remove duplicates and sort
    return sorted(list(set(found_files)))


def run_pipeline(pipeline_id: str, data_file: Path):
    """Run a pipeline with a data file"""
    print(f"\n🔄 Running pipeline {pipeline_id} with {data_file.name}...")
    
    try:
        with open(data_file, 'rb') as f:
            files = {'file': (data_file.name, f, 'application/octet-stream')}
            response = requests.post(
                f"{API_BASE}/pipelines/{pipeline_id}/run",
                files=files,
                timeout=300,  # 5 minute timeout for large files
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"  ✅ Success!")
            print(f"     Records processed: {result.get('records_processed', 0):,}")
            print(f"     Records succeeded: {result.get('records_succeeded', 0):,}")
            print(f"     Records failed: {result.get('records_failed', 0):,}")
            print(f"     Records duplicated: {result.get('records_duplicated', 0):,}")
            
            if result.get('quality_report'):
                quality = result['quality_report']
                print(f"     Quality score: {quality.get('quality_score', 0):.2%}")
                print(f"     Completeness: {quality.get('completeness_score', 0):.2%}")
                print(f"     Validity: {quality.get('validity_score', 0):.2%}")
                issues = quality.get('issues', [])
                print(f"     Issues found: {len(issues)}")
                if issues:
                    # Show first 3 issues
                    for issue in issues[:3]:
                        print(f"       - {issue.get('issue_type')}: {issue.get('issue_description', '')[:60]}")
            
            if result.get('metrics'):
                metrics = result['metrics']
                if metrics.get('execution_time_seconds'):
                    print(f"     Duration: {metrics['execution_time_seconds']:.2f}s")
                if metrics.get('throughput_records_per_second'):
                    print(f"     Throughput: {metrics['throughput_records_per_second']:,.0f} records/sec")
            
            return True, result
            
    except requests.exceptions.Timeout:
        print(f"  ⏱️  Timeout - pipeline may still be running")
        return False, None
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"     Error detail: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"     Error: {e.response.text[:200]}")
        return False, None


def run_pipeline_with_all_files(pipeline_id: str, pipeline_name: str, data_files: List[Path]):
    """Run a pipeline with all matching data files"""
    if not data_files:
        print(f"\n⚠️  No data files found for {pipeline_name}")
        return {"success": False, "files_processed": 0, "total_records": 0}
    
    print(f"\n📦 Processing {len(data_files)} file(s) for {pipeline_name}...")
    
    total_records = 0
    successful_files = 0
    failed_files = 0
    
    for i, data_file in enumerate(data_files, 1):
        print(f"\n  [{i}/{len(data_files)}] Processing {data_file.name}...")
        success, result = run_pipeline(pipeline_id, data_file)
        
        if success:
            successful_files += 1
            total_records += result.get('records_succeeded', 0) if result else 0
        else:
            failed_files += 1
    
    return {
        "success": successful_files > 0,
        "files_processed": len(data_files),
        "successful_files": successful_files,
        "failed_files": failed_files,
        "total_records": total_records,
    }


def main():
    """Main execution"""
    print("🚀 Running All Pipelines with Synthetic Data")
    print("=" * 60)
    
    # Check if synthetic data directory exists
    if not SYNTHETIC_DATA_DIR.exists():
        print(f"❌ Synthetic data directory not found: {SYNTHETIC_DATA_DIR}")
        return
    
    # Get all pipelines
    print("\n📋 Fetching pipelines...")
    pipelines = get_pipelines()
    if not pipelines:
        print("❌ No pipelines found")
        return
    
    print(f"✅ Found {len(pipelines)} pipelines")
    
    # Filter to preconfigured pipelines
    preconfigured = [p for p in pipelines if p.get('tags') and 'preconfigured' in p.get('tags', [])]
    print(f"📌 Found {len(preconfigured)} preconfigured pipelines")
    
    # Run each pipeline with ALL matching source files
    results = []
    for pipeline in preconfigured:
        pipeline_id = pipeline.get('pipeline_id')
        pipeline_name = pipeline.get('pipeline_name')
        
        if not pipeline.get('active', True):
            print(f"\n⏭️  Skipping {pipeline_name} (inactive)")
            continue
        
        # Find ALL matching data files for this pipeline
        data_files = find_data_files(pipeline_name)
        if not data_files:
            print(f"\n⚠️  No data files found for {pipeline_name}")
            continue
        
        # Run pipeline with all files
        result = run_pipeline_with_all_files(pipeline_id, pipeline_name, data_files)
        results.append({
            'pipeline': pipeline_name,
            'success': result['success'],
            'files_processed': result['files_processed'],
            'successful_files': result['successful_files'],
            'failed_files': result['failed_files'],
            'total_records': result['total_records'],
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Execution Summary")
    print("=" * 60)
    
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📦 Total: {len(results)}")
    
    if successful > 0:
        print("\n✅ Successful pipelines:")
        for r in results:
            if r['success']:
                files_info = f" ({r.get('files_processed', 0)} files, {r.get('total_records', 0):,} records)"
                print(f"   - {r['pipeline']}{files_info}")
    
    if failed > 0:
        print("\n❌ Failed pipelines:")
        for r in results:
            if not r['success']:
                print(f"   - {r['pipeline']}")
    
    # Summary statistics
    total_files = sum(r.get('files_processed', 0) for r in results)
    total_records = sum(r.get('total_records', 0) for r in results)
    print(f"\n📊 Overall Statistics:")
    print(f"   Total files processed: {total_files}")
    print(f"   Total records loaded: {total_records:,}")


if __name__ == "__main__":
    main()
