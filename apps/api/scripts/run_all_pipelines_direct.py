#!/usr/bin/env python3
"""
Run all pipelines directly (not via API)
Processes source files and writes to target data model
"""
import sys
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from uepi_api.storage_pipelines import list_pipelines, get_pipeline
from uepi_common.ingestion.pipeline_engine import PipelineEngine
from uepi_common.ingestion.pipeline_metadata import PipelineMetadata, FieldMapping, DeduplicationConfig, PipelineMode, DeduplicationStrategy
from uepi_common.ingestion.monitoring import MonitoringService

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
SOURCE_DATA_DIR = project_root / "data" / "source_data" / "synthetic"
TARGET_DATA_DIR = project_root / "data" / "target_data_model"

# Pipeline to source file mapping
PIPELINE_SOURCE_MAPPING = {
    "Claims Lines Pipeline (CSV)": {
        "files": lambda: list((SOURCE_DATA_DIR / "claims").rglob("*.csv")),
        "pattern": "claims/**/*.csv"
    },
    "Claims Lines Pipeline (Parquet)": {
        "files": lambda: list((SOURCE_DATA_DIR / "claims").rglob("*.parquet")),
        "pattern": "claims/**/*.parquet"
    },
    "Claim Header Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "claim_header.csv", SOURCE_DATA_DIR / "claim_header.parquet"] if f.exists()],
        "pattern": "claim_header.*"
    },
    "Eligibility Enrollment Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "eligibility_enrollment.csv", SOURCE_DATA_DIR / "eligibility_enrollment.parquet"] if f.exists()],
        "pattern": "eligibility_enrollment.*"
    },
    "Member Master Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "member_master.csv", SOURCE_DATA_DIR / "member_master.parquet"] if f.exists()],
        "pattern": "member_master.*"
    },
    "Risk Stratification Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "risk_stratification.csv", SOURCE_DATA_DIR / "risk_stratification.parquet"] if f.exists()],
        "pattern": "risk_stratification.*"
    },
    "Provider Master Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "provider_master.csv", SOURCE_DATA_DIR / "provider_master.parquet"] if f.exists()],
        "pattern": "provider_master.*"
    },
    "Facility Master Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "facility_master.csv", SOURCE_DATA_DIR / "facility_master.parquet"] if f.exists()],
        "pattern": "facility_master.*"
    },
    "Pharmacy Claims Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "pharmacy_claims.csv", SOURCE_DATA_DIR / "pharmacy_claims.parquet"] if f.exists()],
        "pattern": "pharmacy_claims.*"
    },
    "Member Accumulator Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "member_accumulator.csv", SOURCE_DATA_DIR / "member_accumulator.parquet"] if f.exists()],
        "pattern": "member_accumulator.*"
    },
    "Benefit Design Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "benefit_design.csv", SOURCE_DATA_DIR / "benefit_design.parquet"] if f.exists()],
        "pattern": "benefit_design.*"
    },
    "Member Diagnosis Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "member_diagnosis.csv", SOURCE_DATA_DIR / "member_diagnosis.parquet"] if f.exists()],
        "pattern": "member_diagnosis.*"
    },
    "Problem List Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "problem_list.csv", SOURCE_DATA_DIR / "problem_list.parquet"] if f.exists()],
        "pattern": "problem_list.*"
    },
    "Episode of Care Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "episode_of_care.csv", SOURCE_DATA_DIR / "episode_of_care.parquet"] if f.exists()],
        "pattern": "episode_of_care.*"
    },
    "Prior Authorization Request Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "prior_authorization_request.csv", SOURCE_DATA_DIR / "prior_authorization_request.parquet"] if f.exists()],
        "pattern": "prior_authorization_request.*"
    },
    "Concurrent Review Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "concurrent_review.csv", SOURCE_DATA_DIR / "concurrent_review.parquet"] if f.exists()],
        "pattern": "concurrent_review.*"
    },
    "Appeal Grievance Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "appeal_grievance.csv", SOURCE_DATA_DIR / "appeal_grievance.parquet"] if f.exists()],
        "pattern": "appeal_grievance.*"
    },
    "Referral Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "referral.csv", SOURCE_DATA_DIR / "referral.parquet"] if f.exists()],
        "pattern": "referral.*"
    },
    "Care Management Enrollment Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "care_management_enrollment.csv", SOURCE_DATA_DIR / "care_management_enrollment.parquet"] if f.exists()],
        "pattern": "care_management_enrollment.*"
    },
    "Call Center Contact Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "call_center_contact.csv", SOURCE_DATA_DIR / "call_center_contact.parquet"] if f.exists()],
        "pattern": "call_center_contact.*"
    },
    "Market Event Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "market_event.csv", SOURCE_DATA_DIR / "market_event.parquet"] if f.exists()],
        "pattern": "market_event.*"
    },
    "Network Configuration Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "network_configuration.csv", SOURCE_DATA_DIR / "network_configuration.parquet"] if f.exists()],
        "pattern": "network_configuration.*"
    },
    "Provider Contract Pipeline": {
        "files": lambda: [f for f in [SOURCE_DATA_DIR / "provider_contract.csv", SOURCE_DATA_DIR / "provider_contract.parquet"] if f.exists()],
        "pattern": "provider_contract.*"
    },
}

def convert_pipeline_to_metadata(pipeline_dict: dict) -> PipelineMetadata:
    """Convert pipeline dict to PipelineMetadata"""
    pipeline_data = pipeline_dict.copy()
    
    # Convert pipeline_id to UUID
    if isinstance(pipeline_data.get("pipeline_id"), str):
        pipeline_data["pipeline_id"] = UUID(pipeline_data["pipeline_id"])
    
    # Convert field_mappings to FieldMapping objects
    if "field_mappings" in pipeline_data:
        pipeline_data["field_mappings"] = [
            FieldMapping(**m) if isinstance(m, dict) else m
            for m in pipeline_data["field_mappings"]
        ]
    
    # Convert deduplication config
    if "deduplication" in pipeline_data and isinstance(pipeline_data["deduplication"], dict):
        dedup_dict = pipeline_data["deduplication"].copy()
        if "strategy" in dedup_dict:
            dedup_dict["strategy"] = DeduplicationStrategy(dedup_dict["strategy"])
        pipeline_data["deduplication"] = DeduplicationConfig(**dedup_dict)
    
    # Convert mode
    if "mode" in pipeline_data and isinstance(pipeline_data["mode"], str):
        pipeline_data["mode"] = PipelineMode(pipeline_data["mode"])
    
    return PipelineMetadata(**pipeline_data)

def run_all_pipelines():
    """Run all pipelines directly"""
    print("=" * 80)
    print("RUNNING ALL PIPELINES WITH SOURCE DATA")
    print("=" * 80)
    print(f"Tenant ID: {DEFAULT_TENANT_ID}")
    print(f"Source Directory: {SOURCE_DATA_DIR}")
    print(f"Target Directory: {TARGET_DATA_DIR}")
    print()
    
    # Get all pipelines
    pipelines = list_pipelines(DEFAULT_TENANT_ID)
    
    if not pipelines:
        print("❌ No pipelines found in database.")
        return
    
    print(f"📊 Found {len(pipelines)} pipelines")
    print()
    
    results = []
    monitoring = MonitoringService()
    
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
        source_files = [f for f in mapping["files"]() if f.exists()]
        
        if not source_files:
            print(f"⚠️  No source files found for {name}")
            continue
        
        print(f"🚀 Running {name}")
        print(f"   Pipeline ID: {pipeline_id}")
        print(f"   Source Files: {len(source_files)}")
        
        # Convert pipeline to metadata
        try:
            pipeline_metadata = convert_pipeline_to_metadata(pipeline)
        except Exception as e:
            print(f"   ❌ Error converting pipeline: {e}")
            continue
        
        # Create engine
        engine = PipelineEngine(DEFAULT_TENANT_ID, pipeline_metadata, monitoring)
        
        # Prepare output directory
        target_dataset_type = pipeline_metadata.target_dataset_type
        output_dir = TARGET_DATA_DIR / str(DEFAULT_TENANT_ID) / target_dataset_type
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{target_dataset_type.lower()}.parquet"
        
        # Process each source file
        total_records = 0
        total_succeeded = 0
        total_failed = 0
        total_duplicates = 0
        
        for source_file in source_files:
            print(f"   Processing: {source_file.name}")
            try:
                run_id = uuid4()
                result = engine.execute(
                    source_file_path=source_file,
                    output_path=output_path,
                    run_id=run_id,
                    source_file_id_override=source_file.stem
                )
                
                if result.get("success", False):
                    records_processed = result.get("records_processed", 0)
                    records_succeeded = result.get("records_succeeded", 0)
                    records_failed = result.get("records_failed", 0)
                    records_duplicated = result.get("records_duplicated", 0)
                    
                    total_records += records_processed
                    total_succeeded += records_succeeded
                    total_failed += records_failed
                    total_duplicates += records_duplicated
                    
                    print(f"      ✅ Success: {records_succeeded:,} records processed")
                    if records_duplicated > 0:
                        print(f"      📊 Duplicates removed: {records_duplicated:,}")
                    if records_failed > 0:
                        print(f"      ⚠️  Failed: {records_failed:,}")
                else:
                    print(f"      ❌ Error: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"      ❌ Exception: {e}")
                import traceback
                traceback.print_exc()
        
        if total_succeeded > 0:
            print(f"   📊 Total: {total_succeeded:,} records ingested")
            if total_duplicates > 0:
                print(f"   📉 Duplicates removed: {total_duplicates:,}")
            results.append({
                "pipeline": name,
                "success": True,
                "records": total_succeeded,
                "duplicates": total_duplicates
            })
        else:
            results.append({
                "pipeline": name,
                "success": False,
                "records": 0,
                "duplicates": 0
            })
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"✅ Successful: {len(successful)}")
    for r in successful:
        print(f"   {r['pipeline']}: {r['records']:,} records")
        if r['duplicates'] > 0:
            print(f"      (Duplicates removed: {r['duplicates']:,})")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}")
        for r in failed:
            print(f"   {r['pipeline']}")
    
    total_records = sum(r["records"] for r in successful)
    total_duplicates = sum(r["duplicates"] for r in successful)
    print(f"\n📊 Total Records Ingested: {total_records:,}")
    if total_duplicates > 0:
        print(f"📉 Total Duplicates Removed: {total_duplicates:,}")
    print()
    print("✅ Pipeline execution complete!")
    print("   Run count_target_records.py to see results")

if __name__ == "__main__":
    run_all_pipelines()

