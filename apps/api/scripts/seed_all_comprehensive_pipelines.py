#!/usr/bin/env python3
"""
Seed All Comprehensive Pipelines
Creates pipelines for all 15+ comprehensive canonical data models
"""
import json
import sys
import os
from uuid import UUID, uuid4
from datetime import datetime, timezone
from pathlib import Path

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../packages/common/src')))

from uepi_api.storage_pipelines import create_pipeline, list_pipelines
from uepi_api.storage_auth import DEFAULT_TENANT_ID

# All comprehensive data models that need pipelines
COMPREHENSIVE_PIPELINES = [
    # Member & Eligibility Domain
    {
        "pipeline_name": "Member Master Pipeline",
        "pipeline_description": "Ingest member master data into MemberMaster canonical model",
        "source_type": "CSV",
        "target_dataset_type": "MEMBER_MASTER",
        "target_model": "MemberMaster",
        "field_mappings": [
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "subscriber_id", "target_field": "subscriber_id", "required": False},
            {"source_field": "family_id", "target_field": "family_id", "required": False},
            {"source_field": "dob", "target_field": "dob", "transform_function": "to_date", "required": False},
            {"source_field": "age", "target_field": "age", "transform_function": "to_int", "required": False},
            {"source_field": "gender", "target_field": "gender", "required": False},
            {"source_field": "race", "target_field": "race", "required": False},
            {"source_field": "ethnicity", "target_field": "ethnicity", "required": False},
            {"source_field": "zip5", "target_field": "address_zip5", "required": False},
            {"source_field": "county", "target_field": "county", "required": False},
            {"source_field": "state", "target_field": "state", "required": False},
            {"source_field": "rural_flag", "target_field": "rural_flag", "transform_function": "to_bool", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["member_id"]},
        "required_fields": ["member_id"],
        "tags": ["member", "demographics", "preconfigured"],
    },
    {
        "pipeline_name": "Eligibility Enrollment Pipeline",
        "pipeline_description": "Ingest eligibility and enrollment data into EligibilityEnrollment canonical model",
        "source_type": "CSV",
        "target_dataset_type": "ELIGIBILITY_ENROLLMENT",
        "target_model": "EligibilityEnrollment",
        "field_mappings": [
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "coverage_month", "target_field": "coverage_month", "required": True},
            {"source_field": "plan_id", "target_field": "plan_id", "required": True},
            {"source_field": "lob", "target_field": "line_of_business", "required": True},
            {"source_field": "product_id", "target_field": "product_id", "required": False},
            {"source_field": "network_id", "target_field": "network_id", "required": False},
            {"source_field": "coverage_status", "target_field": "coverage_status", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["member_id", "coverage_month", "plan_id"]},
        "required_fields": ["member_id", "coverage_month", "plan_id", "line_of_business", "coverage_status"],
        "tags": ["enrollment", "eligibility", "preconfigured"],
    },
    {
        "pipeline_name": "Member Risk Stratification Pipeline",
        "pipeline_description": "Ingest member risk stratification data into MemberRiskStratification canonical model",
        "source_type": "CSV",
        "target_dataset_type": "MEMBER_RISK_STRATIFICATION",
        "target_model": "MemberRiskStratification",
        "field_mappings": [
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "risk_run_date", "target_field": "risk_run_date", "transform_function": "to_date", "required": True},
            {"source_field": "risk_score", "target_field": "risk_score", "transform_function": "to_float", "required": False},
            {"source_field": "risk_model_name", "target_field": "risk_model_name", "required": False},
            {"source_field": "predicted_cost_pmpm", "target_field": "predicted_cost_pmpm", "transform_function": "to_float", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["member_id", "risk_run_date"]},
        "required_fields": ["member_id", "risk_run_date"],
        "tags": ["member", "risk", "preconfigured"],
    },
    # Claims Domain
    {
        "pipeline_name": "Claim Header Pipeline",
        "pipeline_description": "Ingest claim header data into ClaimHeader canonical model",
        "source_type": "CSV",
        "target_dataset_type": "CLAIM_HEADER",
        "target_model": "ClaimHeader",
        "field_mappings": [
            {"source_field": "claim_id", "target_field": "claim_id", "required": True},
            {"source_field": "claim_type", "target_field": "claim_type", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "billing_provider_id", "target_field": "billing_provider_id", "required": False},
            {"source_field": "claim_received_date", "target_field": "claim_received_date", "transform_function": "to_date", "required": False},
            {"source_field": "claim_status", "target_field": "claim_status", "required": False},
            {"source_field": "total_allowed", "target_field": "total_allowed", "transform_function": "to_float", "required": False},
            {"source_field": "total_paid", "target_field": "total_paid", "transform_function": "to_float", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["claim_id"]},
        "required_fields": ["claim_id", "claim_type", "member_id"],
        "tags": ["claims", "medical", "preconfigured"],
    },
    {
        "pipeline_name": "Claims Lines Pipeline",
        "pipeline_description": "Ingest medical claims lines into ClaimLine canonical model",
        "source_type": "CSV",
        "target_dataset_type": "CLAIMS_LINES",
        "target_model": "ClaimLine",
        "field_mappings": [
            {"source_field": "claim_line_id", "target_field": "claim_line_id", "required": True},
            {"source_field": "claim_id", "target_field": "claim_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "cpt_hcpcs", "target_field": "cpt_hcpcs", "required": False},
            {"source_field": "service_date", "target_field": "service_date_from", "transform_function": "to_date", "required": True},
            {"source_field": "place_of_service", "target_field": "place_of_service", "required": True},
            {"source_field": "allowed_amount", "target_field": "allowed_amount", "transform_function": "to_float", "required": True},
            {"source_field": "paid_amount", "target_field": "paid_amount", "transform_function": "to_float", "required": True},
            {"source_field": "rendering_provider_id", "target_field": "rendering_provider_id", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "HASH"},
        "required_fields": ["claim_line_id", "claim_id", "member_id", "service_date_from"],
        "tags": ["claims", "medical", "preconfigured"],
    },
    {
        "pipeline_name": "Episode of Care Pipeline",
        "pipeline_description": "Ingest episode of care data into EpisodeOfCare canonical model",
        "source_type": "CSV",
        "target_dataset_type": "EPISODE_OF_CARE",
        "target_model": "EpisodeOfCare",
        "field_mappings": [
            {"source_field": "episode_id", "target_field": "episode_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "episode_type", "target_field": "episode_type", "required": True},
            {"source_field": "episode_start_date", "target_field": "episode_start_date", "transform_function": "to_date", "required": True},
            {"source_field": "episode_end_date", "target_field": "episode_end_date", "transform_function": "to_date", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["episode_id"]},
        "required_fields": ["episode_id", "member_id", "episode_type", "episode_start_date"],
        "tags": ["claims", "episode", "preconfigured"],
    },
    # Provider Domain
    {
        "pipeline_name": "Provider Master Pipeline",
        "pipeline_description": "Ingest provider master data into ProviderMaster canonical model",
        "source_type": "CSV",
        "target_dataset_type": "PROVIDER_MASTER",
        "target_model": "ProviderMaster",
        "field_mappings": [
            {"source_field": "provider_id", "target_field": "provider_id", "required": True},
            {"source_field": "npi", "target_field": "npi", "required": False},
            {"source_field": "provider_name", "target_field": "provider_name", "required": False},
            {"source_field": "provider_type", "target_field": "provider_type", "required": True},
            {"source_field": "specialty_primary", "target_field": "specialty_primary", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["provider_id"]},
        "required_fields": ["provider_id", "provider_type"],
        "tags": ["provider", "network", "preconfigured"],
    },
    {
        "pipeline_name": "Facility Master Pipeline",
        "pipeline_description": "Ingest facility master data into FacilityMaster canonical model",
        "source_type": "CSV",
        "target_dataset_type": "FACILITY_MASTER",
        "target_model": "FacilityMaster",
        "field_mappings": [
            {"source_field": "facility_id", "target_field": "facility_id", "required": True},
            {"source_field": "facility_name", "target_field": "facility_name", "required": False},
            {"source_field": "facility_type", "target_field": "facility_type", "required": True},
            {"source_field": "address_zip5", "target_field": "address_zip5", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["facility_id"]},
        "required_fields": ["facility_id", "facility_type"],
        "tags": ["provider", "facility", "preconfigured"],
    },
    {
        "pipeline_name": "Network Configuration Pipeline",
        "pipeline_description": "Ingest network configuration data into NetworkConfiguration canonical model",
        "source_type": "CSV",
        "target_dataset_type": "NETWORK_CONFIGURATION",
        "target_model": "NetworkConfiguration",
        "field_mappings": [
            {"source_field": "network_id", "target_field": "network_id", "required": True},
            {"source_field": "network_name", "target_field": "network_name", "required": False},
            {"source_field": "network_tier", "target_field": "network_tier", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["network_id"]},
        "required_fields": ["network_id"],
        "tags": ["provider", "network", "preconfigured"],
    },
    {
        "pipeline_name": "Provider Contract Pipeline",
        "pipeline_description": "Ingest provider contract data into ProviderContract canonical model",
        "source_type": "CSV",
        "target_dataset_type": "PROVIDER_CONTRACT",
        "target_model": "ProviderContract",
        "field_mappings": [
            {"source_field": "contract_id", "target_field": "contract_id", "required": True},
            {"source_field": "provider_id", "target_field": "provider_id", "required": True},
            {"source_field": "network_id", "target_field": "network_id", "required": False},
            {"source_field": "effective_date", "target_field": "effective_date", "transform_function": "to_date", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["contract_id"]},
        "required_fields": ["contract_id", "provider_id"],
        "tags": ["provider", "contract", "preconfigured"],
    },
    # Pharmacy Domain
    {
        "pipeline_name": "Pharmacy Claims Pipeline",
        "pipeline_description": "Ingest pharmacy claims into PharmacyClaim canonical model",
        "source_type": "CSV",
        "target_dataset_type": "PHARMACY_CLAIMS",
        "target_model": "PharmacyClaim",
        "field_mappings": [
            {"source_field": "rx_claim_id", "target_field": "rx_claim_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "fill_date", "target_field": "fill_date", "transform_function": "to_date", "required": True},
            {"source_field": "ndc", "target_field": "ndc", "required": True},
            {"source_field": "days_supply", "target_field": "days_supply", "transform_function": "to_int", "required": True},
            {"source_field": "paid_amount", "target_field": "paid_amount", "transform_function": "to_float", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "HASH"},
        "required_fields": ["rx_claim_id", "member_id", "fill_date", "ndc"],
        "tags": ["pharmacy", "preconfigured"],
    },
    # Benefits Domain
    {
        "pipeline_name": "Benefit Design Pipeline",
        "pipeline_description": "Ingest benefit design data into BenefitDesign canonical model",
        "source_type": "CSV",
        "target_dataset_type": "BENEFIT_DESIGN",
        "target_model": "BenefitDesign",
        "field_mappings": [
            {"source_field": "benefit_design_id", "target_field": "benefit_design_id", "required": True},
            {"source_field": "plan_id", "target_field": "plan_id", "required": True},
            {"source_field": "service_category", "target_field": "service_category", "required": False},
            {"source_field": "copay_amount", "target_field": "copay_amount", "transform_function": "to_float", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["benefit_design_id"]},
        "required_fields": ["benefit_design_id", "plan_id"],
        "tags": ["benefits", "preconfigured"],
    },
    {
        "pipeline_name": "Member Accumulator Pipeline",
        "pipeline_description": "Ingest member accumulator data into MemberAccumulator canonical model",
        "source_type": "CSV",
        "target_dataset_type": "MEMBER_ACCUMULATOR",
        "target_model": "MemberAccumulator",
        "field_mappings": [
            {"source_field": "accumulator_id", "target_field": "accumulator_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "accumulator_type", "target_field": "accumulator_type", "required": True},
            {"source_field": "accumulator_value", "target_field": "accumulator_value", "transform_function": "to_float", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["accumulator_id"]},
        "required_fields": ["accumulator_id", "member_id", "accumulator_type"],
        "tags": ["benefits", "accumulator", "preconfigured"],
    },
    # UM Operations Domain
    {
        "pipeline_name": "Prior Authorization Request Pipeline",
        "pipeline_description": "Ingest prior authorization requests into PriorAuthorizationRequest canonical model",
        "source_type": "CSV",
        "target_dataset_type": "PRIOR_AUTHORIZATION_REQUEST",
        "target_model": "PriorAuthorizationRequest",
        "field_mappings": [
            {"source_field": "pa_request_id", "target_field": "pa_request_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "request_date", "target_field": "request_date", "transform_function": "to_date", "required": True},
            {"source_field": "service_code", "target_field": "service_code", "required": False},
            {"source_field": "decision", "target_field": "decision", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["pa_request_id"]},
        "required_fields": ["pa_request_id", "member_id", "request_date"],
        "tags": ["um", "pa", "preconfigured"],
    },
    {
        "pipeline_name": "Concurrent Review Pipeline",
        "pipeline_description": "Ingest concurrent review data into ConcurrentReview canonical model",
        "source_type": "CSV",
        "target_dataset_type": "CONCURRENT_REVIEW",
        "target_model": "ConcurrentReview",
        "field_mappings": [
            {"source_field": "review_id", "target_field": "review_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "review_date", "target_field": "review_date", "transform_function": "to_date", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["review_id"]},
        "required_fields": ["review_id", "member_id", "review_date"],
        "tags": ["um", "concurrent", "preconfigured"],
    },
    {
        "pipeline_name": "Appeal Grievance Pipeline",
        "pipeline_description": "Ingest appeal and grievance data into AppealGrievance canonical model",
        "source_type": "CSV",
        "target_dataset_type": "APPEAL_GRIEVANCE",
        "target_model": "AppealGrievance",
        "field_mappings": [
            {"source_field": "appeal_id", "target_field": "appeal_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "appeal_date", "target_field": "appeal_date", "transform_function": "to_date", "required": True},
            {"source_field": "outcome", "target_field": "outcome", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["appeal_id"]},
        "required_fields": ["appeal_id", "member_id", "appeal_date"],
        "tags": ["um", "appeal", "preconfigured"],
    },
    # Clinical Domain
    {
        "pipeline_name": "Member Diagnosis Pipeline",
        "pipeline_description": "Ingest member diagnosis data into MemberDiagnosis canonical model",
        "source_type": "CSV",
        "target_dataset_type": "MEMBER_DIAGNOSIS",
        "target_model": "MemberDiagnosis",
        "field_mappings": [
            {"source_field": "diagnosis_id", "target_field": "diagnosis_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "icd10_code", "target_field": "icd10_code", "required": True},
            {"source_field": "onset_date", "target_field": "onset_date", "transform_function": "to_date", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["diagnosis_id"]},
        "required_fields": ["diagnosis_id", "member_id", "icd10_code"],
        "tags": ["clinical", "diagnosis", "preconfigured"],
    },
    {
        "pipeline_name": "Problem List Pipeline",
        "pipeline_description": "Ingest problem list data into ProblemList canonical model",
        "source_type": "CSV",
        "target_dataset_type": "PROBLEM_LIST",
        "target_model": "ProblemList",
        "field_mappings": [
            {"source_field": "problem_id", "target_field": "problem_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "condition_registry_id", "target_field": "condition_registry_id", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["problem_id"]},
        "required_fields": ["problem_id", "member_id"],
        "tags": ["clinical", "problem", "preconfigured"],
    },
    # Referrals Domain
    {
        "pipeline_name": "Referral Pipeline",
        "pipeline_description": "Ingest referral data into Referral canonical model",
        "source_type": "CSV",
        "target_dataset_type": "REFERRAL",
        "target_model": "Referral",
        "field_mappings": [
            {"source_field": "referral_id", "target_field": "referral_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "referral_date", "target_field": "referral_date", "transform_function": "to_date", "required": True},
            {"source_field": "referring_provider_id", "target_field": "referring_provider_id", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["referral_id"]},
        "required_fields": ["referral_id", "member_id", "referral_date"],
        "tags": ["referral", "preconfigured"],
    },
    # Care Management Domain
    {
        "pipeline_name": "Care Management Enrollment Pipeline",
        "pipeline_description": "Ingest care management enrollment data into CareManagementEnrollment canonical model",
        "source_type": "CSV",
        "target_dataset_type": "CARE_MANAGEMENT_ENROLLMENT",
        "target_model": "CareManagementEnrollment",
        "field_mappings": [
            {"source_field": "enrollment_id", "target_field": "enrollment_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "program_id", "target_field": "program_id", "required": True},
            {"source_field": "enrollment_date", "target_field": "enrollment_date", "transform_function": "to_date", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["enrollment_id"]},
        "required_fields": ["enrollment_id", "member_id", "program_id", "enrollment_date"],
        "tags": ["care_management", "preconfigured"],
    },
    # Member Experience Domain
    {
        "pipeline_name": "Call Center Contact Pipeline",
        "pipeline_description": "Ingest call center contact data into CallCenterContact canonical model",
        "source_type": "CSV",
        "target_dataset_type": "CALL_CENTER_CONTACT",
        "target_model": "CallCenterContact",
        "field_mappings": [
            {"source_field": "contact_id", "target_field": "contact_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "contact_date", "target_field": "contact_date", "transform_function": "to_date", "required": True},
            {"source_field": "contact_topic", "target_field": "contact_topic", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["contact_id"]},
        "required_fields": ["contact_id", "member_id", "contact_date"],
        "tags": ["member_experience", "preconfigured"],
    },
    # Market Events Domain
    {
        "pipeline_name": "Market Event Pipeline",
        "pipeline_description": "Ingest market event data into MarketEvent canonical model",
        "source_type": "CSV",
        "target_dataset_type": "MARKET_EVENT",
        "target_model": "MarketEvent",
        "field_mappings": [
            {"source_field": "event_id", "target_field": "event_id", "required": True},
            {"source_field": "event_type", "target_field": "event_type", "required": True},
            {"source_field": "event_date", "target_field": "event_date", "transform_function": "to_date", "required": True},
            {"source_field": "market", "target_field": "market", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["event_id"]},
        "required_fields": ["event_id", "event_type", "event_date"],
        "tags": ["market_events", "preconfigured"],
    },
]


def seed_all_pipelines():
    """Seed all comprehensive pipelines"""
    print(f"Seeding all comprehensive pipelines for tenant: {DEFAULT_TENANT_ID}")
    created_count = 0
    skipped_count = 0
    
    existing_pipelines = list_pipelines(DEFAULT_TENANT_ID)
    existing_pipeline_names = {p.get("pipeline_name") for p in existing_pipelines}
    
    for pipeline_data in COMPREHENSIVE_PIPELINES:
        pipeline_name = pipeline_data["pipeline_name"]
        if pipeline_name in existing_pipeline_names:
            print(f"  ⏩ Skipping {pipeline_name}: Already exists")
            skipped_count += 1
            continue
        
        try:
            # Add control fields if not present
            if "control_fields" not in pipeline_data:
                pipeline_data["control_fields"] = {
                    "created_at": "CURRENT_TIMESTAMP",
                    "updated_at": "CURRENT_TIMESTAMP",
                    "active_flag": True,
                }
            
            created = create_pipeline(DEFAULT_TENANT_ID, pipeline_data)
            print(f"  ✅ Created {pipeline_name}")
            created_count += 1
        except Exception as e:
            print(f"  ❌ Failed to create {pipeline_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ Seeding complete!")
    print(f"   Created: {created_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total: {len(COMPREHENSIVE_PIPELINES)}")


if __name__ == "__main__":
    seed_all_pipelines()

