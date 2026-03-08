#!/usr/bin/env python3
"""
Run all pipelines with source data files
Automatically matches pipelines to source files and executes them
"""
import sys
from pathlib import Path
from uuid import UUID
import requests
import json
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from uepi_api.storage_pipelines import list_pipelines, get_pipeline

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
SOURCE_DATA_DIR = project_root / "data" / "source_data" / "synthetic"
API_BASE_URL = "http://localhost:8000/api/v1"

# Pipeline to source file mapping
PIPELINE_SOURCE_MAPPING = {
    "Claims Lines Pipeline (CSV)": {
        "files": list((SOURCE_DATA_DIR / "claims").rglob("*.csv")),
        "pattern": "claims/**/*.csv"
    },
    "Claims Lines Pipeline (Parquet)": {
        "files": list((SOURCE_DATA_DIR / "claims").rglob("*.parquet")),
        "pattern": "claims/**/*.parquet"
    },
    "Claim Header Pipeline": {
        "files": [SOURCE_DATA_DIR / "claim_header.csv", SOURCE_DATA_DIR / "claim_header.parquet"],
        "pattern": "claim_header.*"
    },
    "Eligibility Enrollment Pipeline": {
        "files": [SOURCE_DATA_DIR / "eligibility_enrollment.csv", SOURCE_DATA_DIR / "eligibility_enrollment.parquet"],
        "pattern": "eligibility_enrollment.*"
    },
    "Member Master Pipeline": {
        "files": [SOURCE_DATA_DIR / "member_master.csv", SOURCE_DATA_DIR / "member_master.parquet"],
        "pattern": "member_master.*"
    },
    "Risk Stratification Pipeline": {
        "files": [SOURCE_DATA_DIR / "risk_stratification.csv", SOURCE_DATA_DIR / "risk_stratification.parquet"],
        "pattern": "risk_stratification.*"
    },
    "Provider Master Pipeline": {
        "files": [SOURCE_DATA_DIR / "provider_master.csv", SOURCE_DATA_DIR / "provider_master.parquet"],
        "pattern": "provider_master.*"
    },
    "Facility Master Pipeline": {
        "files": [SOURCE_DATA_DIR / "facility_master.csv", SOURCE_DATA_DIR / "facility_master.parquet"],
        "pattern": "facility_master.*"
    },
    "Pharmacy Claims Pipeline": {
        "files": [SOURCE_DATA_DIR / "pharmacy_claims.csv", SOURCE_DATA_DIR / "pharmacy_claims.parquet"],
        "pattern": "pharmacy_claims.*"
    },
    "Member Accumulator Pipeline": {
        "files": [SOURCE_DATA_DIR / "member_accumulator.csv", SOURCE_DATA_DIR / "member_accumulator.parquet"],
        "pattern": "member_accumulator.*"
    },
    "Benefit Design Pipeline": {
        "files": [SOURCE_DATA_DIR / "benefit_design.csv", SOURCE_DATA_DIR / "benefit_design.parquet"],
        "pattern": "benefit_design.*"
    },
    "Member Diagnosis Pipeline": {
        "files": [SOURCE_DATA_DIR / "member_diagnosis.csv", SOURCE_DATA_DIR / "member_diagnosis.parquet"],
        "pattern": "member_diagnosis.*"
    },
    "Problem List Pipeline": {
        "files": [SOURCE_DATA_DIR / "problem_list.csv", SOURCE_DATA_DIR / "problem_list.parquet"],
        "pattern": "problem_list.*"
    },
    "Episode of Care Pipeline": {
        "files": [SOURCE_DATA_DIR / "episode_of_care.csv", SOURCE_DATA_DIR / "episode_of_care.parquet"],
        "pattern": "episode_of_care.*"
    },
    "Prior Authorization Request Pipeline": {
        "files": [SOURCE_DATA_DIR / "prior_authorization_request.csv", SOURCE_DATA_DIR / "prior_authorization_request.parquet"],
        "pattern": "prior_authorization_request.*"
    },
    "Concurrent Review Pipeline": {
        "files": [SOURCE_DATA_DIR / "concurrent_review.csv", SOURCE_DATA_DIR / "concurrent_review.parquet"],
        "pattern": "concurrent_review.*"
    },
    "Appeal Grievance Pipeline": {
        "files": [SOURCE_DATA_DIR / "appeal_grievance.csv", SOURCE_DATA_DIR / "appeal_grievance.parquet"],
        "pattern": "appeal_grievance.*"
    },
    "Referral Pipeline": {
        "files": [SOURCE_DATA_DIR / "referral.csv", SOURCE_DATA_DIR / "referral.parquet"],
        "pattern": "referral.*"
    },
    "Care Management Enrollment Pipeline": {
        "files": [SOURCE_DATA_DIR / "care_management_enrollment.csv", SOURCE_DATA_DIR / "care_management_enrollment.parquet"],
        "pattern": "care_management_enrollment.*"
    },
    "Call Center Contact Pipeline": {
        "files": [SOURCE_DATA_DIR / "call_center_contact.csv", SOURCE_DATA_DIR / "call_center_contact.parquet"],
        "pattern": "call_center_contact.*"
    },
    "Market Event Pipeline": {
        "files": [SOURCE_DATA_DIR / "market_event.csv", SOURCE_DATA_DIR / "market_event.parquet"],
        "pattern": "market_event.*"
    },
    "Network Configuration Pipeline": {
        "files": [SOURCE_DATA_DIR / "network_configuration.csv", SOURCE_DATA_DIR / "network_configuration.parquet"],
        "pattern": "network_configuration.*"
    },
    "Provider Contract Pipeline": {
        "files": [SOURCE_DATA_DIR / "provider_contract.csv", SOURCE_DATA_DIR / "provider_contract.parquet"],
        "pattern": "provider_contract.*"
    },
}

def run_pipeline_via_api(pipeline_id: UUID, source_file: Path) -> Dict:
    """Run a pipeline via API"""
    url = f"{API_BASE_URL}/pipelines/{pipeline_id}/run"
    
    # Use file:// URI for local files
    source_uri = f"file://{source_file.absolute()}"
    
    try:
        response = requests.post(
            url,
            data={"source_uri": source_uri},
            timeout=300  # 5 minute timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "success": False}

def run_all_pipelines():
    """Run all pipelines with their source files"""
    print("=" * 80)
    print("RUNNING ALL PIPELINES WITH SOURCE DATA")
    print("=" * 80)
    print(f"Tenant ID: {DEFAULT_TENANT_ID}")
    print(f"Source Directory: {SOURCE_DATA_DIR}")
    print(f"API Base URL: {API_BASE_URL}")
    print()
    
    # Get all pipelines
    pipelines = list_pipelines(DEFAULT_TENANT_ID)
    
    if not pipelines:
        print("❌ No pipelines found in database.")
        return
    
    print(f"📊 Found {len(pipelines)} pipelines")
    print()
    
    results = []
    
    for pipeline in pipelines:
        name = pipeline.get("pipeline_name") or pipeline.get("name") or "Unknown"
        pipeline_id = pipeline.get("pipeline_id")
        
        if not pipeline_id:
            print(f"⚠️  Skipping {name} (no pipeline_id)")
            continue
        
        if not pipeline.get("active", True):
            print(f"⏭️  Skipping {name} (inactive)")
            continue
        
        # Find source files for this pipeline
        if name not in PIPELINE_SOURCE_MAPPING:
            print(f"⚠️  No source mapping for {name}")
            continue
        
        mapping = PIPELINE_SOURCE_MAPPING[name]
        source_files = [f for f in mapping["files"] if f.exists()]
        
        if not source_files:
            print(f"⚠️  No source files found for {name}")
            continue
        
        print(f"🚀 Running {name}")
        print(f"   Pipeline ID: {pipeline_id}")
        print(f"   Source Files: {len(source_files)}")
        
        # Run pipeline with each source file
        for source_file in source_files:
            print(f"   Processing: {source_file.name}")
            result = run_pipeline_via_api(UUID(pipeline_id), source_file)
            
            if result.get("success", False):
                print(f"   ✅ Success: {result.get('records_processed', 0):,} records")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("✅ Pipeline execution complete!")
    print("   Run count_target_records.py to see results")

if __name__ == "__main__":
    run_all_pipelines()

