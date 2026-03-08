#!/usr/bin/env python3
"""
Update existing pipelines with correct field mappings and deduplication
Fixes missing required fields and deduplication key fields
"""
import sys
from pathlib import Path
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from uepi_api.storage_pipelines import list_pipelines, get_pipeline, update_pipeline

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

# Corrected pipeline configurations
PIPELINE_FIXES = {
    "Claim Header Pipeline": {
        "required_fields": ["claim_id", "claim_type", "member_id", "claim_status", "total_allowed", "total_paid"],
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["claim_id"]},
    },
    "Appeal Grievance Pipeline": {
        "required_fields": ["appeal_id", "member_id", "appeal_date", "outcome"],
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["appeal_id"]},
    },
    "Call Center Contact Pipeline": {
        "required_fields": ["contact_id", "member_id", "contact_date", "contact_topic"],
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["contact_id"]},
    },
    "Claims Lines Pipeline": {
        "required_fields": ["claim_id", "claim_line_id", "member_id", "service_date_from", "service_category", "place_of_service", "units", "allowed_amount", "paid_amount", "in_network_flag"],
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["claim_id", "claim_line_id"]},
    },
    "Member Diagnosis Pipeline": {
        "required_fields": ["member_id", "icd10_code", "onset_date"],
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["member_id", "icd10_code", "onset_date"]},
    },
    "Benefit Design Pipeline": {
        "required_fields": ["plan_id", "service_category"],
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["plan_id", "service_category"]},
    },
    "Referral Pipeline": {
        "required_fields": ["referral_id", "member_id", "referral_date", "referring_provider_id"],
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["referral_id"]},
    },
    "Provider Contract Pipeline": {
        "required_fields": ["contract_id", "effective_date"],
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["contract_id"]},
    },
    "Prior Authorization Request Pipeline": {
        "required_fields": ["pa_request_id", "member_id", "request_date", "service_code", "decision"],
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["pa_request_id"]},
    },
    "Member Accumulator Pipeline": {
        "required_fields": ["member_id", "accumulator_type", "accumulator_value"],
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["member_id"]},
    },
    "Member Risk Stratification Pipeline": {
        "required_fields": ["member_id", "risk_run_date", "risk_score"],
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["member_id", "risk_run_date"]},
    },
    "Pharmacy Claims Pipeline": {
        "required_fields": ["rx_claim_id", "member_id", "fill_date", "ndc", "days_supply", "quantity", "paid_amount", "allowed_amount"],
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["rx_claim_id"]},
    },
}

def update_pipelines():
    """Update existing pipelines with correct configurations"""
    print("=" * 80)
    print("UPDATING PIPELINE FIELD MAPPINGS AND DEDUPLICATION")
    print("=" * 80)
    print(f"Tenant ID: {DEFAULT_TENANT_ID}")
    print()
    
    pipelines = list_pipelines(DEFAULT_TENANT_ID)
    
    if not pipelines:
        print("❌ No pipelines found in database.")
        return
    
    print(f"📊 Found {len(pipelines)} pipelines in database")
    print()
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for pipeline in pipelines:
        name = pipeline.get("pipeline_name") or pipeline.get("name") or "Unknown"
        pipeline_id = pipeline.get("pipeline_id")
        
        if not pipeline_id:
            print(f"⚠️  Skipping {name} (no pipeline_id)")
            skipped_count += 1
            continue
        
        if name not in PIPELINE_FIXES:
            print(f"⏭️  Skipping {name} (no fixes needed)")
            skipped_count += 1
            continue
        
        try:
            # Get full pipeline data
            full_pipeline = get_pipeline(UUID(pipeline_id), DEFAULT_TENANT_ID)
            if not full_pipeline:
                print(f"⚠️  Could not retrieve pipeline: {name}")
                error_count += 1
                continue
            
            # Get fixes
            fixes = PIPELINE_FIXES[name]
            
            # Build update data - update_pipeline expects these fields directly
            # The function will merge them into steps_json
            update_data = {
                "required_fields": fixes.get("required_fields", full_pipeline.get("required_fields", [])),
                "deduplication": fixes.get("deduplication", full_pipeline.get("deduplication", {})),
            }
            
            result = update_pipeline(UUID(pipeline_id), DEFAULT_TENANT_ID, update_data)
            
            if result:
                print(f"✅ Updated pipeline: {name}")
                print(f"   Required Fields: {len(update_data['required_fields'])}")
                dedup_strategy = update_data['deduplication'].get('strategy', 'NONE')
                dedup_keys = update_data['deduplication'].get('key_fields', [])
                print(f"   Deduplication: {dedup_strategy}" + (f" - {dedup_keys}" if dedup_keys else ""))
                updated_count += 1
            else:
                print(f"❌ Failed to update pipeline: {name}")
                error_count += 1
                
        except Exception as e:
            print(f"❌ Error updating pipeline {name}: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Updated: {updated_count}")
    print(f"⏭️  Skipped: {skipped_count}")
    print(f"❌ Errors: {error_count}")
    print()
    
    if updated_count > 0:
        print("🎉 Successfully updated pipelines!")
        print("   Run validate_target_data_model.py to verify fixes")

if __name__ == "__main__":
    update_pipelines()

