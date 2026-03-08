#!/usr/bin/env python3
"""
Seed All 21 Comprehensive Pipelines
Creates pipelines for all source data files in data/source_data/synthetic/
"""
import sys
from pathlib import Path
from uuid import UUID, uuid4

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from uepi_api.storage_pipelines import create_pipeline, list_pipelines

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

# All 21 Pipeline Definitions
PIPELINE_DEFINITIONS = [
    # 1. Claims Lines (CSV)
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Claims Lines Pipeline (CSV)",
        "pipeline_description": "Ingest claims line data from CSV files into ClaimsLine canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "CLAIMS_LINES",
        "target_model": "ClaimLine",
        "field_mappings": [
            {"source_field": "claim_id", "target_field": "claim_id", "required": True},
            {"source_field": "claim_line_id", "target_field": "claim_line_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "rendering_provider_id", "target_field": "rendering_provider_id", "required": False},
            {"source_field": "service_date_from", "target_field": "service_date_from", "transform_function": "to_date", "required": True},
            {"source_field": "service_date_to", "target_field": "service_date_to", "transform_function": "to_date", "required": False},
            {"source_field": "cpt_hcpcs", "target_field": "cpt_hcpcs", "required": False},
            {"source_field": "place_of_service", "target_field": "place_of_service", "required": True},
            {"source_field": "service_category", "target_field": "service_category", "required": True},
            {"source_field": "site_of_care_class", "target_field": "site_of_care_class", "required": False},
            {"source_field": "units", "target_field": "units", "transform_function": "to_decimal", "required": True},
            {"source_field": "allowed_amount", "target_field": "allowed_amount", "transform_function": "to_decimal", "required": True},
            {"source_field": "paid_amount", "target_field": "paid_amount", "transform_function": "to_decimal", "required": True},
            {"source_field": "in_network_flag", "target_field": "in_network_flag", "transform_function": "to_bool", "required": True},
            {"source_field": "prior_auth_required_flag", "target_field": "prior_auth_required_flag", "transform_function": "to_bool", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["claim_id", "claim_line_id"]},
        "required_fields": ["claim_id", "claim_line_id", "member_id", "service_date_from", "service_category", "place_of_service", "units", "allowed_amount", "paid_amount", "in_network_flag"],
        "tags": ["claims", "preconfigured", "primary"],
    },
    # 2. Claims Lines (Parquet)
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Claims Lines Pipeline (Parquet)",
        "pipeline_description": "Ingest claims line data from Parquet files into ClaimsLine canonical model",
        "version": "1.0",
        "source_type": "PARQUET",
        "target_dataset_type": "CLAIMS_LINES",
        "target_model": "ClaimLine",
        "field_mappings": [
            {"source_field": "claim_id", "target_field": "claim_id", "required": True},
            {"source_field": "claim_line_id", "target_field": "claim_line_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "rendering_provider_id", "target_field": "rendering_provider_id", "required": False},
            {"source_field": "service_date_from", "target_field": "service_date_from", "transform_function": "to_date", "required": True},
            {"source_field": "service_date_to", "target_field": "service_date_to", "transform_function": "to_date", "required": False},
            {"source_field": "cpt_hcpcs", "target_field": "cpt_hcpcs", "required": False},
            {"source_field": "place_of_service", "target_field": "place_of_service", "required": True},
            {"source_field": "service_category", "target_field": "service_category", "required": True},
            {"source_field": "units", "target_field": "units", "transform_function": "to_decimal", "required": True},
            {"source_field": "allowed_amount", "target_field": "allowed_amount", "transform_function": "to_decimal", "required": True},
            {"source_field": "paid_amount", "target_field": "paid_amount", "transform_function": "to_decimal", "required": True},
            {"source_field": "in_network_flag", "target_field": "in_network_flag", "transform_function": "to_bool", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["claim_id", "claim_line_id"]},
        "required_fields": ["claim_id", "claim_line_id", "member_id", "service_date_from", "service_category", "place_of_service", "units", "allowed_amount", "paid_amount", "in_network_flag"],
        "tags": ["claims", "preconfigured", "parquet"],
    },
    # 3. Claim Header
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Claim Header Pipeline",
        "pipeline_description": "Ingest claim header data into ClaimHeader canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "CLAIM_HEADER",
        "target_model": "ClaimHeader",
        "field_mappings": [
            {"source_field": "claim_id", "target_field": "claim_id", "required": True},
            {"source_field": "claim_type", "target_field": "claim_type", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "claim_received_date", "target_field": "claim_received_date", "transform_function": "to_date", "required": False},
            {"source_field": "claim_status", "target_field": "claim_status", "required": True},
            {"source_field": "total_allowed", "target_field": "total_allowed", "transform_function": "to_decimal", "required": True},
            {"source_field": "total_paid", "target_field": "total_paid", "transform_function": "to_decimal", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["claim_id"]},
        "required_fields": ["claim_id", "claim_type", "member_id", "claim_status", "total_allowed", "total_paid"],
        "tags": ["claims", "preconfigured"],
    },
    # 4. Eligibility Enrollment
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Eligibility Enrollment Pipeline",
        "pipeline_description": "Ingest eligibility enrollment data into EligibilityEnrollment canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "ENROLLMENT",
        "target_model": "EligibilityEnrollment",
        "field_mappings": [
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "coverage_month", "target_field": "coverage_month", "required": True},
            {"source_field": "plan_id", "target_field": "plan_id", "required": True},
            {"source_field": "line_of_business", "target_field": "line_of_business", "required": True},
            {"source_field": "coverage_status", "target_field": "coverage_status", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["member_id", "coverage_month", "plan_id"]},
        "required_fields": ["member_id", "coverage_month", "plan_id", "line_of_business", "coverage_status"],
        "tags": ["enrollment", "preconfigured", "primary"],
    },
    # 5. Member Master
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Member Master Pipeline",
        "pipeline_description": "Ingest member master data into MemberMaster canonical model",
        "version": "1.0",
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
            {"source_field": "address_zip5", "target_field": "address_zip5", "required": False},
            {"source_field": "county", "target_field": "county", "required": False},
            {"source_field": "state", "target_field": "state", "required": False},
            {"source_field": "rural_flag", "target_field": "rural_flag", "transform_function": "to_bool", "required": False},
        ],
        "mode": "UPSERT",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["member_id"]},
        "required_fields": ["member_id"],
        "tags": ["member", "preconfigured", "primary"],
    },
    # 6. Risk Stratification
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Risk Stratification Pipeline",
        "pipeline_description": "Ingest risk stratification data into MemberRiskStratification canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "RISK_STRATIFICATION",
        "target_model": "MemberRiskStratification",
        "field_mappings": [
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "risk_run_date", "target_field": "risk_run_date", "transform_function": "to_date", "required": True},
            {"source_field": "risk_score", "target_field": "risk_score", "transform_function": "to_decimal", "required": True},
            {"source_field": "risk_model_name", "target_field": "risk_model_name", "required": False},
            {"source_field": "predicted_cost_pmpm", "target_field": "predicted_cost_pmpm", "transform_function": "to_decimal", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["member_id", "risk_run_date"]},
        "required_fields": ["member_id", "risk_run_date", "risk_score"],
        "tags": ["risk", "preconfigured"],
    },
    # 7. Provider Master
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Provider Master Pipeline",
        "pipeline_description": "Ingest provider master data into ProviderMaster canonical model",
        "version": "1.0",
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
        "mode": "UPSERT",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["provider_id"]},
        "required_fields": ["provider_id", "provider_type"],
        "tags": ["provider", "preconfigured", "primary"],
    },
    # 8. Facility Master
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Facility Master Pipeline",
        "pipeline_description": "Ingest facility master data into FacilityMaster canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "FACILITY_MASTER",
        "target_model": "FacilityMaster",
        "field_mappings": [
            {"source_field": "facility_id", "target_field": "facility_id", "required": True},
            {"source_field": "facility_name", "target_field": "facility_name", "required": False},
            {"source_field": "facility_type", "target_field": "facility_type", "required": True},
            {"source_field": "address_zip5", "target_field": "facility_zip", "required": False},
        ],
        "mode": "UPSERT",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["facility_id"]},
        "required_fields": ["facility_id", "facility_type"],
        "tags": ["facility", "preconfigured"],
    },
    # 9. Pharmacy Claims
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Pharmacy Claims Pipeline",
        "pipeline_description": "Ingest pharmacy claims data into PharmacyClaim canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "PHARMACY_CLAIMS",
        "target_model": "PharmacyClaim",
        "field_mappings": [
            {"source_field": "rx_claim_id", "target_field": "rx_claim_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "fill_date", "target_field": "fill_date", "transform_function": "to_date", "required": True},
            {"source_field": "ndc", "target_field": "ndc", "required": True},
            {"source_field": "days_supply", "target_field": "days_supply", "transform_function": "to_int", "required": True},
            {"source_field": "quantity", "target_field": "quantity", "transform_function": "to_decimal", "required": True},
            {"source_field": "paid_amount", "target_field": "paid_amount", "transform_function": "to_decimal", "required": True},
            {"source_field": "allowed_amount", "target_field": "allowed_amount", "transform_function": "to_decimal", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["rx_claim_id"]},
        "required_fields": ["rx_claim_id", "member_id", "fill_date", "ndc", "days_supply", "quantity", "paid_amount", "allowed_amount"],
        "tags": ["pharmacy", "preconfigured", "primary"],
    },
    # 10. Member Accumulator
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Member Accumulator Pipeline",
        "pipeline_description": "Ingest member accumulator data into MemberAccumulator canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "MEMBER_ACCUMULATOR",
        "target_model": "MemberAccumulator",
        "field_mappings": [
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "accumulator_type", "target_field": "accumulator_type", "required": True},
            {"source_field": "accumulator_value", "target_field": "accumulator_value", "transform_function": "to_decimal", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["member_id"]},
        "required_fields": ["member_id", "accumulator_type", "accumulator_value"],
        "tags": ["benefits", "preconfigured"],
    },
    # 11. Benefit Design
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Benefit Design Pipeline",
        "pipeline_description": "Ingest benefit design data into BenefitDesign canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "BENEFIT_DESIGN",
        "target_model": "BenefitDesign",
        "field_mappings": [
            {"source_field": "plan_id", "target_field": "plan_id", "required": True},
            {"source_field": "service_category", "target_field": "service_category", "required": True},
            {"source_field": "copay_amount", "target_field": "copay", "transform_function": "to_decimal", "required": False},
        ],
        "mode": "UPSERT",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["plan_id", "service_category"]},
        "required_fields": ["plan_id", "service_category"],
        "tags": ["benefits", "preconfigured"],
    },
    # 12. Member Diagnosis
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Member Diagnosis Pipeline",
        "pipeline_description": "Ingest member diagnosis data into MemberDiagnosis canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "MEMBER_DIAGNOSIS",
        "target_model": "MemberDiagnosis",
        "field_mappings": [
            {"source_field": "diagnosis_id", "target_field": "diagnosis_id", "required": False},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "icd10_code", "target_field": "icd10_code", "required": True},
            {"source_field": "onset_date", "target_field": "onset_date", "transform_function": "to_date", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["member_id", "icd10_code", "onset_date"]},
        "required_fields": ["member_id", "icd10_code", "onset_date"],
        "tags": ["clinical", "preconfigured"],
    },
    # 13. Problem List
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Problem List Pipeline",
        "pipeline_description": "Ingest problem list data into ProblemList canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "PROBLEM_LIST",
        "target_model": "ProblemList",
        "field_mappings": [
            {"source_field": "problem_id", "target_field": "problem_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "condition_registry_id", "target_field": "condition_registry_id", "required": False},
        ],
        "mode": "UPSERT",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["problem_id"]},
        "required_fields": ["problem_id", "member_id"],
        "tags": ["clinical", "preconfigured"],
    },
    # 14. Episode of Care
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Episode of Care Pipeline",
        "pipeline_description": "Ingest episode of care data into EpisodeOfCare canonical model",
        "version": "1.0",
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
        "tags": ["episodes", "preconfigured"],
    },
    # 15. Prior Authorization Request
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Prior Authorization Request Pipeline",
        "pipeline_description": "Ingest prior authorization request data into PriorAuthorizationRequest canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "PRIOR_AUTHORIZATION",
        "target_model": "PriorAuthorizationRequest",
        "field_mappings": [
            {"source_field": "pa_request_id", "target_field": "pa_request_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "request_date", "target_field": "request_date", "transform_function": "to_date", "required": True},
            {"source_field": "service_code", "target_field": "service_codes", "transform_function": "to_list", "required": True},
            {"source_field": "decision", "target_field": "decision", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["pa_request_id"]},
        "required_fields": ["pa_request_id", "member_id", "request_date", "service_code", "decision"],
        "tags": ["um", "preconfigured"],
    },
    # 16. Concurrent Review
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Concurrent Review Pipeline",
        "pipeline_description": "Ingest concurrent review data into ConcurrentReview canonical model",
        "version": "1.0",
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
        "tags": ["um", "preconfigured"],
    },
    # 17. Appeal Grievance
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Appeal Grievance Pipeline",
        "pipeline_description": "Ingest appeal grievance data into AppealGrievance canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "APPEAL_GRIEVANCE",
        "target_model": "AppealGrievance",
        "field_mappings": [
            {"source_field": "appeal_id", "target_field": "appeal_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "appeal_date", "target_field": "filed_date", "transform_function": "to_date", "required": True},
            {"source_field": "outcome", "target_field": "outcome", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["appeal_id"]},
        "required_fields": ["appeal_id", "member_id", "appeal_date", "outcome"],
        "tags": ["um", "preconfigured"],
    },
    # 18. Referral
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Referral Pipeline",
        "pipeline_description": "Ingest referral data into Referral canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "REFERRAL",
        "target_model": "Referral",
        "field_mappings": [
            {"source_field": "referral_id", "target_field": "referral_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "referral_date", "target_field": "created_date", "transform_function": "to_date", "required": True},
            {"source_field": "referring_provider_id", "target_field": "ordering_provider_id", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["referral_id"]},
        "required_fields": ["referral_id", "member_id", "referral_date", "referring_provider_id"],
        "tags": ["referrals", "preconfigured"],
    },
    # 19. Care Management Enrollment
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Care Management Enrollment Pipeline",
        "pipeline_description": "Ingest care management enrollment data into CareManagementEnrollment canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "CARE_MANAGEMENT",
        "target_model": "CareManagementEnrollment",
        "field_mappings": [
            {"source_field": "enrollment_id", "target_field": "enrollment_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "program_id", "target_field": "program_id", "required": True},
            {"source_field": "enrollment_date", "target_field": "start_date", "transform_function": "to_date", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["enrollment_id"]},
        "required_fields": ["enrollment_id", "member_id", "program_id", "enrollment_date"],
        "tags": ["care_management", "preconfigured"],
    },
    # 20. Call Center Contact
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Call Center Contact Pipeline",
        "pipeline_description": "Ingest call center contact data into CallCenterContact canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "CALL_CENTER_CONTACT",
        "target_model": "CallCenterContact",
        "field_mappings": [
            {"source_field": "contact_id", "target_field": "contact_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "contact_date", "target_field": "contact_date", "transform_function": "to_date", "required": True},
            {"source_field": "contact_topic", "target_field": "topic", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["contact_id"]},
        "required_fields": ["contact_id", "member_id", "contact_date", "contact_topic"],
        "tags": ["member_experience", "preconfigured"],
    },
    # 21. Market Event
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Market Event Pipeline",
        "pipeline_description": "Ingest market event data into MarketEvent canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "MARKET_EVENT",
        "target_model": "MarketEvent",
        "field_mappings": [
            {"source_field": "event_id", "target_field": "event_id", "required": True},
            {"source_field": "event_type", "target_field": "event_type", "required": True},
            {"source_field": "event_date", "target_field": "event_date", "transform_function": "to_date", "required": True},
            {"source_field": "market", "target_field": "affected_markets", "transform_function": "to_list", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["event_id"]},
        "required_fields": ["event_id", "event_type", "event_date"],
        "tags": ["market_events", "preconfigured"],
    },
    # 22. Network Configuration
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Network Configuration Pipeline",
        "pipeline_description": "Ingest network configuration data into NetworkConfiguration canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "NETWORK_CONFIGURATION",
        "target_model": "NetworkConfiguration",
        "field_mappings": [
            {"source_field": "network_id", "target_field": "network_id", "required": True},
            {"source_field": "network_name", "target_field": "network_name", "required": False},
            {"source_field": "network_tier", "target_field": "network_tier", "required": False},
        ],
        "mode": "UPSERT",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["network_id"]},
        "required_fields": ["network_id"],
        "tags": ["network", "preconfigured"],
    },
    # 23. Provider Contract
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Provider Contract Pipeline",
        "pipeline_description": "Ingest provider contract data into ProviderContract canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "PROVIDER_CONTRACT",
        "target_model": "ProviderContract",
        "field_mappings": [
            {"source_field": "contract_id", "target_field": "contract_id", "required": True},
            {"source_field": "provider_id", "target_field": "provider_id", "required": False},
            {"source_field": "network_id", "target_field": "network_id", "required": False},
            {"source_field": "effective_date", "target_field": "effective_start", "transform_function": "to_date", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["contract_id"]},
        "required_fields": ["contract_id", "effective_date"],
        "tags": ["provider", "preconfigured"],
    },
]


def seed_all_pipelines():
    """Seed all 21+ pipelines into the database"""
    print("=" * 80)
    print("SEEDING ALL 21+ COMPREHENSIVE PIPELINES")
    print("=" * 80)
    print(f"Tenant ID: {DEFAULT_TENANT_ID}")
    print()
    
    # Check existing pipelines
    existing_pipelines = list_pipelines(DEFAULT_TENANT_ID)
    existing_names = {p.get("pipeline_name") or p.get("name") for p in existing_pipelines}
    existing_ids = {p.get("pipeline_id") for p in existing_pipelines if p.get("pipeline_id")}
    print(f"📊 Found {len(existing_pipelines)} existing pipelines in database")
    print()
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    for pipeline_def in PIPELINE_DEFINITIONS:
        pipeline_name = pipeline_def["pipeline_name"]
        pipeline_id = pipeline_def["pipeline_id"]
        
        # Check if pipeline already exists
        if pipeline_name in existing_names or pipeline_id in existing_ids:
            print(f"⏭️  Skipping {pipeline_name} (already exists)")
            skipped_count += 1
            continue
        
        try:
            # Build pipeline data dict
            pipeline_data = {
                "pipeline_id": pipeline_def["pipeline_id"],
                "name": pipeline_name,
                "description": pipeline_def.get("pipeline_description", ""),
                "source_type": pipeline_def["source_type"],
                "target_dataset_type": pipeline_def["target_dataset_type"],
                "target_model": pipeline_def["target_model"],
                "field_mappings": pipeline_def["field_mappings"],
                "mode": pipeline_def.get("mode", "APPEND"),
                "deduplication": pipeline_def.get("deduplication", {"strategy": "HASH"}),
                "control_fields": {
                    "created_at": "CURRENT_TIMESTAMP",
                    "updated_at": "CURRENT_TIMESTAMP",
                    "active_flag": True,
                },
                "validation_rules": None,
                "required_fields": pipeline_def.get("required_fields", []),
                "batch_size": 10000,
                "error_threshold": 0.05,
                "continue_on_error": True,
                "status": "ACTIVE",
                "tags": pipeline_def.get("tags", []),  # Include tags from definition
                "notes": pipeline_def.get("notes"),  # Include notes from definition
            }
            
            # Create pipeline
            created = create_pipeline(DEFAULT_TENANT_ID, pipeline_data)
            
            if created:
                print(f"✅ Created pipeline: {pipeline_name}")
                print(f"   ID: {pipeline_def['pipeline_id']}")
                print(f"   Target: {pipeline_def['target_model']}")
                print(f"   Mappings: {len(pipeline_def['field_mappings'])} fields")
                created_count += 1
            else:
                print(f"❌ Failed to create pipeline: {pipeline_name}")
                error_count += 1
                
        except Exception as e:
            print(f"❌ Error creating pipeline {pipeline_name}: {e}")
            error_count += 1
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Created: {created_count}")
    print(f"⏭️  Skipped: {skipped_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Total: {len(PIPELINE_DEFINITIONS)}")
    print()
    
    if created_count > 0:
        print("🎉 Successfully created pipelines in database!")
        print("   Pipelines are now visible via /api/v1/pipelines endpoint")
    else:
        print("⚠️  No new pipelines were created")


if __name__ == "__main__":
    seed_all_pipelines()

