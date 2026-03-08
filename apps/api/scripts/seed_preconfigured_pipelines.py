#!/usr/bin/env python3
"""
Seed Preconfigured Pipelines
Creates preconfigured pipelines for all comprehensive canonical models
"""
import json
import sys
import os
from uuid import UUID, uuid4
from datetime import datetime, timezone
from pathlib import Path

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../packages/common/src')))

from uepi_api.storage_pipelines import create_pipeline, list_pipelines

# Default tenant ID
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

# Preconfigured pipelines based on comprehensive canonical models
PRECONFIGURED_PIPELINES = [
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
            {"source_field": "service_category", "target_field": "service_category", "required": True},
            {"source_field": "allowed_amount", "target_field": "allowed_amount", "transform_function": "to_float", "required": True},
            {"source_field": "paid_amount", "target_field": "paid_amount", "transform_function": "to_float", "required": True},
            {"source_field": "in_network", "target_field": "in_network_flag", "transform_function": "to_bool", "required": True},
            {"source_field": "rendering_provider_id", "target_field": "rendering_provider_id", "required": False},
            {"source_field": "facility_id", "target_field": "facility_id", "required": False},
            {"source_field": "units", "target_field": "units", "transform_function": "to_float", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "HASH"},
        "control_fields": {
            "created_at": "CURRENT_TIMESTAMP",
            "updated_at": "CURRENT_TIMESTAMP",
            "active_flag": True,
        },
        "required_fields": ["claim_line_id", "claim_id", "member_id", "service_date_from", "place_of_service", "service_category", "allowed_amount", "paid_amount", "in_network_flag", "units"],
        "tags": ["claims", "medical", "preconfigured"],
    },
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
            {"source_field": "income_band", "target_field": "income_band", "required": False},
            {"source_field": "education_band", "target_field": "education_band", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["member_id"]},
        "control_fields": {
            "created_at": "CURRENT_TIMESTAMP",
            "updated_at": "CURRENT_TIMESTAMP",
            "active_flag": True,
        },
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
            {"source_field": "network_tier", "target_field": "network_tier", "required": False},
            {"source_field": "enrollment_start", "target_field": "enrollment_start_date", "transform_function": "to_date", "required": False},
            {"source_field": "enrollment_end", "target_field": "enrollment_end_date", "transform_function": "to_date", "required": False},
            {"source_field": "coverage_status", "target_field": "coverage_status", "required": True},
            {"source_field": "PCP_id", "target_field": "PCP_id", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["member_id", "coverage_month", "plan_id"]},
        "control_fields": {
            "created_at": "CURRENT_TIMESTAMP",
            "updated_at": "CURRENT_TIMESTAMP",
            "active_flag": True,
        },
        "required_fields": ["member_id", "coverage_month", "plan_id", "line_of_business", "coverage_status"],
        "tags": ["enrollment", "eligibility", "preconfigured"],
    },
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
            {"source_field": "specialty_secondary", "target_field": "specialty_secondary", "required": False},
            {"source_field": "practice_location_zip", "target_field": "practice_location_zip", "required": False},
            {"source_field": "practice_location_county", "target_field": "practice_location_county", "required": False},
            {"source_field": "practice_location_state", "target_field": "practice_location_state", "required": False},
            {"source_field": "accepting_new_patients", "target_field": "accepting_new_patients_flag", "transform_function": "to_bool", "required": False},
            {"source_field": "telehealth_capable", "target_field": "telehealth_capable_flag", "transform_function": "to_bool", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "KEY_FIELDS", "key_fields": ["provider_id"]},
        "control_fields": {
            "created_at": "CURRENT_TIMESTAMP",
            "updated_at": "CURRENT_TIMESTAMP",
            "active_flag": True,
        },
        "required_fields": ["provider_id", "provider_type"],
        "tags": ["provider", "network", "preconfigured"],
    },
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
            {"source_field": "drug_name", "target_field": "drug_name", "required": False},
            {"source_field": "days_supply", "target_field": "days_supply", "transform_function": "to_int", "required": True},
            {"source_field": "quantity", "target_field": "quantity", "transform_function": "to_float", "required": True},
            {"source_field": "prescriber_id", "target_field": "prescriber_id", "required": False},
            {"source_field": "pharmacy_id", "target_field": "pharmacy_id", "required": False},
            {"source_field": "paid_amount", "target_field": "paid_amount", "transform_function": "to_float", "required": True},
            {"source_field": "allowed_amount", "target_field": "allowed_amount", "transform_function": "to_float", "required": True},
            {"source_field": "formulary_tier", "target_field": "formulary_tier", "required": False},
            {"source_field": "pa_required", "target_field": "pa_required_flag", "transform_function": "to_bool", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {"strategy": "HASH"},
        "control_fields": {
            "created_at": "CURRENT_TIMESTAMP",
            "updated_at": "CURRENT_TIMESTAMP",
            "active_flag": True,
        },
        "required_fields": ["rx_claim_id", "member_id", "fill_date", "ndc", "days_supply", "quantity", "paid_amount", "allowed_amount"],
        "tags": ["pharmacy", "preconfigured"],
    },
]


def seed_pipelines():
    """Seed preconfigured pipelines"""
    print(f"Seeding preconfigured pipelines for tenant: {DEFAULT_TENANT_ID}")
    created_count = 0
    skipped_count = 0
    
    existing_pipelines = list_pipelines(DEFAULT_TENANT_ID)
    existing_pipeline_names = {p.get("pipeline_name") for p in existing_pipelines}
    
    for pipeline_data in PRECONFIGURED_PIPELINES:
        pipeline_name = pipeline_data["pipeline_name"]
        if pipeline_name in existing_pipeline_names:
            print(f"  ⏩ Skipping {pipeline_name}: Pipeline already exists.")
            skipped_count += 1
            continue
        
        try:
            created = create_pipeline(DEFAULT_TENANT_ID, pipeline_data)
            print(f"  ✅ Created {pipeline_name}")
            created_count += 1
        except Exception as e:
            print(f"  ❌ Failed to create {pipeline_name}: {e}")
    
    print(f"\n✅ Seeding complete!")
    print(f"   Created: {created_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total: {created_count + skipped_count}")


if __name__ == "__main__":
    seed_pipelines()

