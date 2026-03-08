#!/usr/bin/env python3
"""
Seed comprehensive pipelines for all source-to-target data mappings
Creates pipelines for ingesting source data into target canonical models
"""
import sys
import os
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from uepi_api.database import SessionLocal, init_db
from uepi_api.models.pipeline import Pipeline
from uepi_api.storage_pipelines import create_pipeline

# Default tenant ID
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


# Comprehensive pipeline definitions
PIPELINE_DEFINITIONS = [
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Claims Lines Pipeline",
        "pipeline_description": "Ingest claims line data (CSV/Parquet) into ClaimsLine canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "CLAIMS_LINES",
        "target_model": "ClaimsLine",
        "field_mappings": [
            {"source_field": "claim_id", "target_field": "claim_id", "required": True},
            {"source_field": "claim_line_id", "target_field": "claim_line_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "rendering_provider_id", "target_field": "provider_id", "required": True, "default": "UNKNOWN"},
            {"source_field": "service_date_from", "target_field": "service_date", "transform_function": "to_date", "required": True},
            {"source_field": "service_date_to", "target_field": "service_date", "transform_function": "to_date", "required": False, "fallback": "service_date_from"},
            {"source_field": "lob", "target_field": "lob", "required": False, "default": "COMMERCIAL"},
            {"source_field": "market", "target_field": "market", "required": False},
            {"source_field": "cpt_hcpcs", "target_field": "cpt_code", "transform_function": "extract_cpt", "required": False},
            {"source_field": "cpt_hcpcs", "target_field": "hcpcs_code", "transform_function": "extract_hcpcs", "required": False},
            {"source_field": "service_category", "target_field": "service_category", "required": True},
            {"source_field": "place_of_service", "target_field": "place_of_service", "required": True},
            {"source_field": "units", "target_field": "units", "transform_function": "to_decimal", "required": True},
            {"source_field": "allowed_amount", "target_field": "allowed_amount", "transform_function": "to_decimal", "required": True},
            {"source_field": "paid_amount", "target_field": "paid_amount", "transform_function": "to_decimal", "required": True},
            {"source_field": "member_resp_amount", "target_field": "member_cost_share", "transform_function": "to_decimal", "required": False},
            {"source_field": "in_network_flag", "target_field": "in_network", "transform_function": "to_bool", "required": True},
            {"source_field": "prior_auth_required_flag", "target_field": "requires_prior_auth", "transform_function": "to_bool", "required": False},
            {"source_field": "site_of_care_class", "target_field": "facility_type", "required": False},
            {"source_field": "rendering_provider_id", "target_field": "rendering_provider_id", "required": False},
            {"source_field": "facility_id", "target_field": "billing_provider_id", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {
            "strategy": "KEY_FIELDS",
            "key_fields": ["claim_id", "claim_line_id"]
        },
        "required_fields": ["claim_id", "claim_line_id", "member_id", "service_date_from", "service_category", "place_of_service", "units", "allowed_amount", "paid_amount", "in_network_flag"],
        "tags": ["claims", "preconfigured", "primary"],
    },
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Enrollment Records Pipeline",
        "pipeline_description": "Ingest enrollment data (CSV/Parquet) into EnrollmentRecord canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "ENROLLMENT",
        "target_model": "EnrollmentRecord",
        "field_mappings": [
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "coverage_month", "target_field": "enrollment_month", "transform_function": "coverage_month_to_date", "required": True},
            {"source_field": "line_of_business", "target_field": "lob", "required": True},
            {"source_field": "plan_id", "target_field": "product_type", "required": False},
            {"source_field": "coverage_status", "target_field": "enrolled_flag", "transform_function": "coverage_status_to_bool", "required": True},
            # Note: age_band, gender, risk_score, network_tier need to be joined from member_master
            # These will be populated during pipeline processing via lookups
        ],
        "mode": "APPEND",
        "deduplication": {
            "strategy": "KEY_FIELDS",
            "key_fields": ["member_id", "enrollment_month"]
        },
        "required_fields": ["member_id", "coverage_month", "line_of_business", "coverage_status"],
        "tags": ["enrollment", "preconfigured", "primary"],
    },
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Member Master Pipeline",
        "pipeline_description": "Ingest member master data (CSV/Parquet) into MemberMaster canonical model",
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
            {"source_field": "zip5", "target_field": "address_zip5", "required": False},
            {"source_field": "address_zip5", "target_field": "address_zip5", "required": False},
            {"source_field": "county", "target_field": "county", "required": False},
            {"source_field": "state", "target_field": "state", "required": False},
            {"source_field": "rural_flag", "target_field": "rural_flag", "transform_function": "to_bool", "required": False},
            {"source_field": "income_band", "target_field": "income_band", "required": False},
            {"source_field": "education_band", "target_field": "education_band", "required": False},
            {"source_field": "employment_status", "target_field": "employment_status", "required": False},
            {"source_field": "housing_insecurity_flag", "target_field": "housing_insecurity_flag", "transform_function": "to_bool", "required": False},
            {"source_field": "food_insecurity_flag", "target_field": "food_insecurity_flag", "transform_function": "to_bool", "required": False},
            {"source_field": "lob", "target_field": "lob", "required": False},
            {"source_field": "market", "target_field": "market", "required": False},
            {"source_field": "plan_id", "target_field": "plan_id", "required": False},
            {"source_field": "product_type", "target_field": "product_type", "required": False},
        ],
        "mode": "UPSERT",
        "deduplication": {
            "strategy": "KEY_FIELDS",
            "key_fields": ["member_id"]
        },
        "required_fields": ["member_id"],
        "tags": ["member", "preconfigured", "primary"],
    },
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Provider Master Pipeline",
        "pipeline_description": "Ingest provider master data (CSV/Parquet) into ProviderMaster canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "PROVIDER_MASTER",
        "target_model": "ProviderMaster",
        "field_mappings": [
            {"source_field": "provider_id", "target_field": "provider_id", "required": True},
            {"source_field": "npi", "target_field": "npi", "required": False},
            {"source_field": "provider_name", "target_field": "provider_name", "required": False},
            {"source_field": "specialty_primary", "target_field": "specialty", "required": False},
            {"source_field": "provider_type", "target_field": "provider_type", "required": False},
            {"source_field": "facility_flag", "target_field": "facility_flag", "transform_function": "to_bool", "required": False},
            {"source_field": "tax_id", "target_field": "tax_id", "required": False},
            {"source_field": "system_affiliation", "target_field": "system_affiliation", "required": False},
        ],
        "mode": "UPSERT",
        "deduplication": {
            "strategy": "KEY_FIELDS",
            "key_fields": ["provider_id"]
        },
        "required_fields": ["provider_id"],
        "tags": ["provider", "preconfigured", "primary"],
    },
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Claims Lines Parquet Pipeline",
        "pipeline_description": "Ingest claims line data from Parquet files into ClaimsLine canonical model",
        "version": "1.0",
        "source_type": "PARQUET",
        "target_dataset_type": "CLAIMS_LINES",
        "target_model": "ClaimsLine",
        "field_mappings": [
            {"source_field": "claim_id", "target_field": "claim_id", "required": True},
            {"source_field": "claim_line_id", "target_field": "claim_line_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "provider_id", "target_field": "provider_id", "required": True},
            {"source_field": "service_date_from", "target_field": "service_date", "transform_function": "to_date", "required": True},
            {"source_field": "lob", "target_field": "lob", "required": False, "default": "COMMERCIAL"},
            {"source_field": "market", "target_field": "market", "required": False},
            {"source_field": "cpt_hcpcs", "target_field": "cpt_code", "transform_function": "extract_cpt", "required": False},
            {"source_field": "service_category", "target_field": "service_category", "required": True},
            {"source_field": "place_of_service", "target_field": "place_of_service", "required": True},
            {"source_field": "units", "target_field": "units", "transform_function": "to_decimal", "required": True},
            {"source_field": "allowed_amount", "target_field": "allowed_amount", "transform_function": "to_decimal", "required": True},
            {"source_field": "paid_amount", "target_field": "paid_amount", "transform_function": "to_decimal", "required": True},
            {"source_field": "in_network_flag", "target_field": "in_network", "transform_function": "to_bool", "required": True},
        ],
        "mode": "APPEND",
        "deduplication": {
            "strategy": "KEY_FIELDS",
            "key_fields": ["claim_id", "claim_line_id"]
        },
        "required_fields": ["claim_id", "claim_line_id", "member_id", "service_date_from", "service_category", "place_of_service", "units", "allowed_amount", "paid_amount", "in_network_flag"],
        "tags": ["claims", "preconfigured", "parquet"],
    },
    {
        "pipeline_id": str(uuid4()),
        "pipeline_name": "Pharmacy Claims Pipeline",
        "pipeline_description": "Ingest pharmacy claims data (CSV/Parquet) into PharmacyClaim canonical model",
        "version": "1.0",
        "source_type": "CSV",
        "target_dataset_type": "PHARMACY_CLAIMS",
        "target_model": "PharmacyClaim",
        "field_mappings": [
            {"source_field": "rx_claim_id", "target_field": "rx_claim_id", "required": True},
            {"source_field": "member_id", "target_field": "member_id", "required": True},
            {"source_field": "fill_date", "target_field": "fill_date", "transform_function": "to_date", "required": True},
            {"source_field": "ndc", "target_field": "ndc", "required": True},
            {"source_field": "gpi", "target_field": "gpi", "required": False},
            {"source_field": "rxnorm", "target_field": "rxnorm", "required": False},
            {"source_field": "drug_name", "target_field": "drug_name", "required": False},
            {"source_field": "therapeutic_class", "target_field": "therapeutic_class", "required": False},
            {"source_field": "days_supply", "target_field": "days_supply", "transform_function": "to_int", "required": True},
            {"source_field": "quantity", "target_field": "quantity", "transform_function": "to_decimal", "required": True},
            {"source_field": "quantity_uom", "target_field": "quantity_uom", "required": False},
            {"source_field": "refills", "target_field": "refills", "transform_function": "to_int", "required": False},
            {"source_field": "prescriber_id", "target_field": "prescriber_id", "required": False},
            {"source_field": "pharmacy_id", "target_field": "pharmacy_id", "required": False},
            {"source_field": "paid_amount", "target_field": "paid_amount", "transform_function": "to_decimal", "required": True},
            {"source_field": "allowed_amount", "target_field": "allowed_amount", "transform_function": "to_decimal", "required": True},
            {"source_field": "member_pay", "target_field": "member_pay", "transform_function": "to_decimal", "required": False},
            {"source_field": "formulary_tier", "target_field": "formulary_tier", "required": False},
            {"source_field": "pa_required_flag", "target_field": "pa_required_flag", "transform_function": "to_bool", "required": False},
            {"source_field": "step_therapy_flag", "target_field": "step_therapy_flag", "transform_function": "to_bool", "required": False},
            {"source_field": "specialty_flag", "target_field": "specialty_flag", "transform_function": "to_bool", "required": False},
            {"source_field": "generic_flag", "target_field": "generic_flag", "transform_function": "to_bool", "required": False},
            {"source_field": "mail_order_flag", "target_field": "mail_order_flag", "transform_function": "to_bool", "required": False},
        ],
        "mode": "APPEND",
        "deduplication": {
            "strategy": "KEY_FIELDS",
            "key_fields": ["rx_claim_id"]
        },
        "required_fields": ["rx_claim_id", "member_id", "fill_date", "ndc", "days_supply", "quantity", "paid_amount", "allowed_amount"],
        "tags": ["pharmacy", "preconfigured", "primary"],
    },
]


def seed_pipelines():
    """Seed all predefined pipelines into the database"""
    print("=" * 80)
    print("SEEDING COMPREHENSIVE PIPELINES")
    print("=" * 80)
    print(f"Tenant ID: {DEFAULT_TENANT_ID}")
    print()
    
    # Check existing pipelines
    from uepi_api.storage_pipelines import list_pipelines
    existing_pipelines = list_pipelines(DEFAULT_TENANT_ID)
    existing_names = {p.get("pipeline_name") for p in existing_pipelines}
    existing_ids = {p.get("pipeline_id") for p in existing_pipelines if p.get("pipeline_id")}
    print(f"📊 Found {len(existing_pipelines)} existing pipelines in database")
    print()
    
    created_count = 0
    skipped_count = 0
    
    for pipeline_def in PIPELINE_DEFINITIONS:
        pipeline_name = pipeline_def["pipeline_name"]
        pipeline_id = pipeline_def["pipeline_id"]
        
        # Check if pipeline already exists (by name or ID)
        if pipeline_name in existing_names or pipeline_id in existing_ids:
            print(f"⏭️  Skipping {pipeline_name} (already exists)")
            skipped_count += 1
            continue
        
        try:
            # Build pipeline data dict (matching create_pipeline expected format)
            pipeline_data = {
                "pipeline_id": pipeline_def["pipeline_id"],
                "name": pipeline_name,  # create_pipeline expects "name" not "pipeline_name"
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
                
        except Exception as e:
            print(f"❌ Error creating pipeline {pipeline_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 80)
    print(f"✅ Pipeline seeding complete!")
    print(f"   Created: {created_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total: {len(PIPELINE_DEFINITIONS)}")
    print("=" * 80)


if __name__ == "__main__":
    seed_pipelines()

