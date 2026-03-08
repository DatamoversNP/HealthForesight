#!/usr/bin/env python3
"""
Validate that pipelines match target data model structures from http://localhost:3050/data-mode
"""
import sys
from pathlib import Path
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from uepi_api.storage_pipelines import list_pipelines

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

# Target data model definitions from DataModelViewerPage
TARGET_MODELS = {
    "ClaimLine": {
        "required_fields": ["claim_line_id", "claim_id", "member_id", "service_date_from", "service_category", "place_of_service", "units", "allowed_amount", "paid_amount", "in_network_flag"],
        "key_fields": ["claim_id", "claim_line_id"]
    },
    "ClaimHeader": {
        "required_fields": ["claim_id", "claim_type", "member_id", "claim_status", "total_allowed", "total_paid"],
        "key_fields": ["claim_id"]
    },
    "EligibilityEnrollment": {
        "required_fields": ["member_id", "coverage_month", "plan_id", "line_of_business", "coverage_status"],
        "key_fields": ["member_id", "coverage_month", "plan_id"]
    },
    "MemberMaster": {
        "required_fields": ["member_id"],
        "key_fields": ["member_id"]
    },
    "MemberRiskStratification": {
        "required_fields": ["member_id", "risk_run_date", "risk_score"],
        "key_fields": ["member_id", "risk_run_date"]
    },
    "ProviderMaster": {
        "required_fields": ["provider_id", "provider_type"],
        "key_fields": ["provider_id"]
    },
    "FacilityMaster": {
        "required_fields": ["facility_id", "facility_type"],
        "key_fields": ["facility_id"]
    },
    "PharmacyClaim": {
        "required_fields": ["rx_claim_id", "member_id", "fill_date", "ndc", "days_supply", "quantity", "paid_amount", "allowed_amount"],
        "key_fields": ["rx_claim_id"]
    },
    "MemberAccumulator": {
        "required_fields": ["member_id", "accumulator_type", "accumulator_value"],
        "key_fields": ["member_id"]
    },
    "BenefitDesign": {
        "required_fields": ["plan_id", "service_category"],
        "key_fields": ["plan_id", "service_category"]
    },
    "MemberDiagnosis": {
        "required_fields": ["member_id", "icd10_code", "onset_date"],
        "key_fields": ["member_id", "icd10_code", "onset_date"]
    },
    "ProblemList": {
        "required_fields": ["problem_id", "member_id"],
        "key_fields": ["problem_id"]
    },
    "EpisodeOfCare": {
        "required_fields": ["episode_id", "member_id", "episode_type", "episode_start_date"],
        "key_fields": ["episode_id"]
    },
    "PriorAuthorizationRequest": {
        "required_fields": ["pa_request_id", "member_id", "request_date", "service_code", "decision"],
        "key_fields": ["pa_request_id"]
    },
    "ConcurrentReview": {
        "required_fields": ["review_id", "member_id", "review_date"],
        "key_fields": ["review_id"]
    },
    "AppealGrievance": {
        "required_fields": ["appeal_id", "member_id", "appeal_date", "outcome"],
        "key_fields": ["appeal_id"]
    },
    "Referral": {
        "required_fields": ["referral_id", "member_id", "referral_date", "referring_provider_id"],
        "key_fields": ["referral_id"]
    },
    "CareManagementEnrollment": {
        "required_fields": ["enrollment_id", "member_id", "program_id", "enrollment_date"],
        "key_fields": ["enrollment_id"]
    },
    "CallCenterContact": {
        "required_fields": ["contact_id", "member_id", "contact_date", "contact_topic"],
        "key_fields": ["contact_id"]
    },
    "MarketEvent": {
        "required_fields": ["event_id", "event_type", "event_date"],
        "key_fields": ["event_id"]
    },
    "NetworkConfiguration": {
        "required_fields": ["network_id"],
        "key_fields": ["network_id"]
    },
    "ProviderContract": {
        "required_fields": ["contract_id", "effective_date"],
        "key_fields": ["contract_id"]
    },
}

def validate_pipelines():
    """Validate pipelines match target data model"""
    print("=" * 80)
    print("TARGET DATA MODEL VALIDATION")
    print("=" * 80)
    print(f"Tenant ID: {DEFAULT_TENANT_ID}")
    print()
    
    pipelines = list_pipelines(DEFAULT_TENANT_ID)
    
    if not pipelines:
        print("❌ No pipelines found in database.")
        return
    
    print(f"📊 Validating {len(pipelines)} pipelines against target data model...\n")
    
    issues = []
    valid_count = 0
    
    for pipeline in pipelines:
        name = pipeline.get("pipeline_name") or pipeline.get("name") or "Unknown"
        target_model = pipeline.get("target_model") or "Unknown"
        required_fields = pipeline.get("required_fields", [])
        dedup = pipeline.get("deduplication", {})
        key_fields = dedup.get("key_fields", []) if isinstance(dedup, dict) else []
        
        # Check if target model is defined
        if target_model not in TARGET_MODELS:
            issues.append({
                "pipeline": name,
                "target_model": target_model,
                "issue": f"Target model '{target_model}' not found in target data model definitions",
                "recommendation": "Verify target model name matches DataModelViewerPage definitions"
            })
            continue
        
        model_def = TARGET_MODELS[target_model]
        expected_required = set(model_def["required_fields"])
        actual_required = set(required_fields)
        
        # Check required fields
        missing_required = expected_required - actual_required
        if missing_required:
            issues.append({
                "pipeline": name,
                "target_model": target_model,
                "issue": f"Missing required fields: {', '.join(missing_required)}",
                "recommendation": f"Add missing required fields to pipeline configuration"
            })
        
        # Check deduplication key fields
        expected_keys = set(model_def["key_fields"])
        actual_keys = set(key_fields)
        if expected_keys and not actual_keys.issuperset(expected_keys):
            issues.append({
                "pipeline": name,
                "target_model": target_model,
                "issue": f"Deduplication key fields should include: {', '.join(expected_keys)}",
                "recommendation": f"Update deduplication.key_fields to include: {', '.join(expected_keys)}"
            })
        
        if not missing_required and (not expected_keys or actual_keys.issuperset(expected_keys)):
            valid_count += 1
            print(f"✅ {name}")
            print(f"   Target Model: {target_model}")
            print(f"   Required Fields: {len(required_fields)} configured")
            print(f"   Deduplication Keys: {', '.join(key_fields) if key_fields else 'HASH'}")
            print()
    
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"✅ Valid pipelines: {valid_count}")
    print(f"⚠️  Issues found: {len(issues)}")
    print()
    
    if issues:
        print("ISSUES TO FIX:")
        print("-" * 80)
        for issue in issues:
            print(f"Pipeline: {issue['pipeline']}")
            print(f"  Target Model: {issue['target_model']}")
            print(f"  Issue: {issue['issue']}")
            print(f"  Recommendation: {issue['recommendation']}")
            print()
    else:
        print("🎉 All pipelines match target data model definitions!")
        print()
        print("All pipelines are configured with:")
        print("  ✅ Correct target model names")
        print("  ✅ Required fields matching target data model")
        print("  ✅ Proper deduplication key fields")

if __name__ == "__main__":
    validate_pipelines()

