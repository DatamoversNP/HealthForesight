#!/usr/bin/env python3
"""
Generate All Comprehensive Synthetic Data
Creates source data files for all 15+ comprehensive canonical data models
"""
from __future__ import annotations

import argparse
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Any, Optional, Dict, List
from uuid import UUID, uuid4
from decimal import Decimal

# Fixed seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Import comprehensive canonical models
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "common" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api" / "src"))

from uepi_common.data_contracts.canonical_base import CanonicalBase
from uepi_common.data_contracts.comprehensive.member import (
    MemberMaster, EligibilityEnrollment, MemberRiskStratification,
    Gender, UrbanicityIndex, EmploymentStatus, CoverageStatus
)
from uepi_common.data_contracts.comprehensive.claims import (
    ClaimHeader, ClaimLine, EpisodeOfCare,
    ClaimType, ClaimStatus, FormType, PricingMethod, SiteOfCareClass, BenefitCategory
)
from uepi_common.data_contracts.comprehensive.provider import (
    ProviderMaster, FacilityMaster, NetworkConfiguration, ProviderContract,
    ProviderType, RateType, CodeType
)
from uepi_common.data_contracts.comprehensive.pharmacy import PharmacyClaim
from uepi_common.data_contracts.comprehensive.benefits import BenefitDesign, MemberAccumulator
from uepi_common.data_contracts.comprehensive.um import (
    PriorAuthorizationRequest, ConcurrentReview, AppealGrievance,
    PADecision, AppealOutcome
)
from uepi_common.data_contracts.comprehensive.clinical import MemberDiagnosis, DiagnosisSource
from uepi_common.data_contracts.comprehensive.referrals import Referral, ReferralStatus
from uepi_common.data_contracts.comprehensive.care_management import CareManagementEnrollment
from uepi_common.data_contracts.comprehensive.member_experience import CallCenterContact, ContactTopic, Sentiment
from uepi_common.data_contracts.comprehensive.market_events import MarketEvent, MarketEventType

# Configuration
MARKETS = ["NYC", "DFW", "BOS", "CHI", "LA", "SEA", "PHX", "ATL"]
LOBS = ["COMMERCIAL", "MA", "MEDICAID", "SELF_INSURED"]
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
DEFAULT_SOURCE_SYSTEM = "SYNTHETIC_GENERATOR"
DEFAULT_INGESTION_ID = UUID("00000000-0000-0000-0000-000000000002")

# Synthetic data directory
SYNTHETIC_DATA_DIR = Path(__file__).parent.parent / "data" / "source_data" / "synthetic"


def generate_member_master(count: int) -> pd.DataFrame:
    """Generate MemberMaster records"""
    records = []
    for i in range(count):
        records.append({
            "tenant_id": str(DEFAULT_TENANT_ID),
            "source_system": DEFAULT_SOURCE_SYSTEM,
            "source_file_id": "member_master.csv",
            "ingestion_id": str(DEFAULT_INGESTION_ID),
            "member_id": f"MEM_{i:08d}",
            "subscriber_id": f"SUB_{i:08d}",
            "family_id": f"FAM_{i // 3:06d}" if np.random.random() > 0.3 else None,
            "dob": (date(1950, 1, 1) + timedelta(days=np.random.randint(0, 25550))).isoformat(),
            "age": np.random.randint(18, 85),
            "gender": np.random.choice(["M", "F", "U"]),
            "race": np.random.choice(["WHITE", "BLACK", "ASIAN", "HISPANIC", "OTHER", None], p=[0.6, 0.15, 0.1, 0.1, 0.04, 0.01]),
            "ethnicity": np.random.choice(["HISPANIC", "NON_HISPANIC", None], p=[0.15, 0.8, 0.05]),
            "address_zip5": f"{np.random.randint(10000, 99999)}",
            "county": f"County_{np.random.choice(MARKETS)}",
            "state": np.random.choice(["NY", "TX", "CA", "MA", "IL"]),
            "rural_flag": np.random.random() < 0.2,
        })
    return pd.DataFrame(records)


def generate_eligibility_enrollment(members_df: pd.DataFrame, num_months: int) -> pd.DataFrame:
    """Generate EligibilityEnrollment records"""
    records = []
    start_date = date(2023, 12, 1)
    for month_idx in range(num_months):
        # Calculate month correctly
        year = start_date.year + (start_date.month + month_idx - 1) // 12
        month = ((start_date.month + month_idx - 1) % 12) + 1
        current_month = date(year, month, 1)
        
        for _, member in members_df.iterrows():
            records.append({
                "tenant_id": str(DEFAULT_TENANT_ID),
                "source_system": DEFAULT_SOURCE_SYSTEM,
                "source_file_id": "eligibility_enrollment.csv",
                "ingestion_id": str(DEFAULT_INGESTION_ID),
                "member_id": member["member_id"],
                "coverage_month": current_month.strftime("%Y-%m"),
                "plan_id": f"PLAN_{member['member_id'].split('_')[1][:4]}",
                "line_of_business": np.random.choice(LOBS),
                "coverage_status": "ACTIVE" if np.random.random() > 0.02 else "TERMED",
            })
    return pd.DataFrame(records)


def generate_risk_stratification(members_df: pd.DataFrame, num_months: int) -> pd.DataFrame:
    """Generate MemberRiskStratification records"""
    records = []
    start_date = date(2023, 12, 1)
    for month_idx in range(0, num_months, 3):  # Quarterly
        risk_date = start_date + timedelta(days=month_idx * 30)
        for _, member in members_df.head(10000).iterrows():  # Sample
            records.append({
                "tenant_id": str(DEFAULT_TENANT_ID),
                "source_system": DEFAULT_SOURCE_SYSTEM,
                "source_file_id": "risk_stratification.csv",
                "ingestion_id": str(DEFAULT_INGESTION_ID),
                "member_id": member["member_id"],
                "risk_run_date": risk_date.isoformat(),
                "risk_score": round(np.random.gamma(2.0, 0.5), 2),
                "risk_model_name": "HCC",
                "predicted_cost_pmpm": round(np.random.uniform(200, 2000), 2),
            })
    return pd.DataFrame(records)


def generate_provider_master(count: int) -> pd.DataFrame:
    """Generate ProviderMaster records"""
    records = []
    for i in range(count):
        records.append({
            "tenant_id": str(DEFAULT_TENANT_ID),
            "source_system": DEFAULT_SOURCE_SYSTEM,
            "source_file_id": "provider_master.csv",
            "ingestion_id": str(DEFAULT_INGESTION_ID),
            "provider_id": f"PROV_{i:06d}",
            "npi": f"{np.random.randint(1000000000, 9999999999)}",
            "provider_name": f"Provider {i}",
            "provider_type": np.random.choice(["PHYSICIAN", "FACILITY", "OTHER"]),
            "specialty_primary": np.random.choice(["RADIOLOGY", "ONCOLOGY", "PRIMARY_CARE", "EMERGENCY"]),
        })
    return pd.DataFrame(records)


def generate_facility_master(count: int) -> pd.DataFrame:
    """Generate FacilityMaster records"""
    records = []
    for i in range(count):
        records.append({
            "tenant_id": str(DEFAULT_TENANT_ID),
            "source_system": DEFAULT_SOURCE_SYSTEM,
            "source_file_id": "facility_master.csv",
            "ingestion_id": str(DEFAULT_INGESTION_ID),
            "facility_id": f"FAC_{i:06d}",
            "facility_name": f"Facility {i}",
            "facility_type": np.random.choice(["HOSPITAL", "CLINIC", "URGENT_CARE", "SURGERY_CENTER"]),
            "address_zip5": f"{np.random.randint(10000, 99999)}",
        })
    return pd.DataFrame(records)


def generate_network_configuration(count: int) -> pd.DataFrame:
    """Generate NetworkConfiguration records"""
    records = []
    for i in range(count):
        records.append({
            "tenant_id": str(DEFAULT_TENANT_ID),
            "source_system": DEFAULT_SOURCE_SYSTEM,
            "source_file_id": "network_configuration.csv",
            "ingestion_id": str(DEFAULT_INGESTION_ID),
            "network_id": f"NET_{i:03d}",
            "network_name": f"Network {i}",
            "network_tier": np.random.choice(["STANDARD", "NARROW", "BROAD"]),
        })
    return pd.DataFrame(records)


def generate_provider_contract(providers_df: pd.DataFrame, networks_df: pd.DataFrame) -> pd.DataFrame:
    """Generate ProviderContract records"""
    records = []
    for _, provider in providers_df.iterrows():
        for _ in range(np.random.randint(1, 3)):  # 1-2 contracts per provider
            records.append({
                "tenant_id": str(DEFAULT_TENANT_ID),
                "source_system": DEFAULT_SOURCE_SYSTEM,
                "source_file_id": "provider_contract.csv",
                "ingestion_id": str(DEFAULT_INGESTION_ID),
                "contract_id": f"CNT_{len(records):08d}",
                "provider_id": provider["provider_id"],
                "network_id": np.random.choice(networks_df["network_id"].tolist()) if len(networks_df) > 0 else f"NET_001",
                "effective_date": (date(2023, 1, 1) + timedelta(days=np.random.randint(0, 730))).isoformat(),
            })
    return pd.DataFrame(records)


def generate_claim_header(claims_lines_df: pd.DataFrame) -> pd.DataFrame:
    """Generate ClaimHeader records from claim lines"""
    claim_ids = claims_lines_df["claim_id"].unique()
    records = []
    for claim_id in claim_ids[:10000]:  # Sample
        claim_lines = claims_lines_df[claims_lines_df["claim_id"] == claim_id]
        records.append({
            "tenant_id": str(DEFAULT_TENANT_ID),
            "source_system": DEFAULT_SOURCE_SYSTEM,
            "source_file_id": "claim_header.csv",
            "ingestion_id": str(DEFAULT_INGESTION_ID),
            "claim_id": claim_id,
            "claim_type": np.random.choice(["INPATIENT", "OUTPATIENT", "PROFESSIONAL"]),
            "member_id": claim_lines.iloc[0]["member_id"] if len(claim_lines) > 0 else f"MEM_{np.random.randint(0, 10000):08d}",
            "claim_received_date": (date(2023, 12, 1) + timedelta(days=np.random.randint(0, 730))).isoformat(),
            "claim_status": np.random.choice(["PAID", "DENIED", "PENDING"]),
            "total_allowed": round(np.random.uniform(100, 5000), 2),
            "total_paid": round(np.random.uniform(80, 4500), 2),
        })
    return pd.DataFrame(records)


def generate_episode_of_care(members_df: pd.DataFrame, num_months: int) -> pd.DataFrame:
    """Generate EpisodeOfCare records"""
    records = []
    start_date = date(2023, 12, 1)
    for month_idx in range(num_months):
        episode_date = start_date + timedelta(days=month_idx * 30)
        for _, member in members_df.head(5000).iterrows():  # Sample
            if np.random.random() < 0.1:  # 10% have episodes
                records.append({
                    "tenant_id": str(DEFAULT_TENANT_ID),
                    "source_system": DEFAULT_SOURCE_SYSTEM,
                    "source_file_id": "episode_of_care.csv",
                    "ingestion_id": str(DEFAULT_INGESTION_ID),
                    "episode_id": f"EPI_{len(records):08d}",
                    "member_id": member["member_id"],
                    "episode_type": np.random.choice(["ACUTE", "CHRONIC", "PREVENTIVE"]),
                    "episode_start_date": episode_date.isoformat(),
                    "episode_end_date": (episode_date + timedelta(days=np.random.randint(1, 90))).isoformat(),
                })
    return pd.DataFrame(records)


def generate_pharmacy_claims(members_df: pd.DataFrame, num_months: int) -> pd.DataFrame:
    """Generate PharmacyClaim records"""
    records = []
    start_date = date(2023, 12, 1)
    ndc_codes = [f"{np.random.randint(10000, 99999)}-{np.random.randint(1000, 9999)}-{np.random.randint(10, 99)}" for _ in range(100)]
    
    for month_idx in range(num_months):
        fill_date = start_date + timedelta(days=month_idx * 30 + np.random.randint(0, 30))
        for _, member in members_df.head(8000).iterrows():  # Sample
            if np.random.random() < 0.3:  # 30% have pharmacy claims
                records.append({
                    "tenant_id": str(DEFAULT_TENANT_ID),
                    "source_system": DEFAULT_SOURCE_SYSTEM,
                    "source_file_id": "pharmacy_claims.csv",
                    "ingestion_id": str(DEFAULT_INGESTION_ID),
                    "rx_claim_id": f"RX_{len(records):08d}",
                    "member_id": member["member_id"],
                    "fill_date": fill_date.isoformat(),
                    "ndc": np.random.choice(ndc_codes),
                    "days_supply": np.random.randint(7, 90),
                    "quantity": round(np.random.uniform(1, 100), 2),
                    "paid_amount": round(np.random.uniform(10, 500), 2),
                    "allowed_amount": round(np.random.uniform(12, 600), 2),
                })
    return pd.DataFrame(records)


def generate_benefit_design(plans: List[str]) -> pd.DataFrame:
    """Generate BenefitDesign records"""
    records = []
    service_categories = ["MEDICAL", "PHARMACY", "DENTAL", "VISION", "MENTAL_HEALTH"]
    for plan_id in plans:
        for service_cat in service_categories:
            records.append({
                "tenant_id": str(DEFAULT_TENANT_ID),
                "source_system": DEFAULT_SOURCE_SYSTEM,
                "source_file_id": "benefit_design.csv",
                "ingestion_id": str(DEFAULT_INGESTION_ID),
                "benefit_design_id": f"BEN_{len(records):08d}",
                "plan_id": plan_id,
                "service_category": service_cat,
                "copay_amount": round(np.random.uniform(10, 100), 2) if np.random.random() > 0.3 else None,
            })
    return pd.DataFrame(records)


def generate_member_accumulator(members_df: pd.DataFrame) -> pd.DataFrame:
    """Generate MemberAccumulator records"""
    records = []
    accumulator_types = ["DEDUCTIBLE", "OOP_MAX", "COINSURANCE"]
    for _, member in members_df.head(5000).iterrows():  # Sample
        for acc_type in accumulator_types:
            records.append({
                "tenant_id": str(DEFAULT_TENANT_ID),
                "source_system": DEFAULT_SOURCE_SYSTEM,
                "source_file_id": "member_accumulator.csv",
                "ingestion_id": str(DEFAULT_INGESTION_ID),
                "accumulator_id": f"ACC_{len(records):08d}",
                "member_id": member["member_id"],
                "accumulator_type": acc_type,
                "accumulator_value": round(np.random.uniform(0, 5000), 2),
            })
    return pd.DataFrame(records)


def generate_prior_authorization(members_df: pd.DataFrame, num_months: int) -> pd.DataFrame:
    """Generate PriorAuthorizationRequest records"""
    records = []
    start_date = date(2023, 12, 1)
    service_codes = ["72148", "72149", "70450", "96413", "99214"]
    
    for month_idx in range(num_months):
        request_date = start_date + timedelta(days=month_idx * 30 + np.random.randint(0, 30))
        for _, member in members_df.head(2000).iterrows():  # Sample
            if np.random.random() < 0.05:  # 5% have PA requests
                records.append({
                    "tenant_id": str(DEFAULT_TENANT_ID),
                    "source_system": DEFAULT_SOURCE_SYSTEM,
                    "source_file_id": "prior_authorization_request.csv",
                    "ingestion_id": str(DEFAULT_INGESTION_ID),
                    "pa_request_id": f"PA_{len(records):08d}",
                    "member_id": member["member_id"],
                    "request_date": request_date.isoformat(),
                    "service_code": np.random.choice(service_codes),
                    "decision": np.random.choice(["APPROVED", "DENIED", "PENDING"]),
                })
    return pd.DataFrame(records)


def generate_concurrent_review(members_df: pd.DataFrame, num_months: int) -> pd.DataFrame:
    """Generate ConcurrentReview records"""
    records = []
    start_date = date(2023, 12, 1)
    for month_idx in range(num_months):
        review_date = start_date + timedelta(days=month_idx * 30 + np.random.randint(0, 30))
        for _, member in members_df.head(1000).iterrows():  # Sample
            if np.random.random() < 0.02:  # 2% have concurrent reviews
                records.append({
                    "tenant_id": str(DEFAULT_TENANT_ID),
                    "source_system": DEFAULT_SOURCE_SYSTEM,
                    "source_file_id": "concurrent_review.csv",
                    "ingestion_id": str(DEFAULT_INGESTION_ID),
                    "review_id": f"REV_{len(records):08d}",
                    "member_id": member["member_id"],
                    "review_date": review_date.isoformat(),
                })
    return pd.DataFrame(records)


def generate_appeal_grievance(members_df: pd.DataFrame, num_months: int) -> pd.DataFrame:
    """Generate AppealGrievance records"""
    records = []
    start_date = date(2023, 12, 1)
    for month_idx in range(num_months):
        appeal_date = start_date + timedelta(days=month_idx * 30 + np.random.randint(0, 30))
        for _, member in members_df.head(500).iterrows():  # Sample
            if np.random.random() < 0.01:  # 1% have appeals
                records.append({
                    "tenant_id": str(DEFAULT_TENANT_ID),
                    "source_system": DEFAULT_SOURCE_SYSTEM,
                    "source_file_id": "appeal_grievance.csv",
                    "ingestion_id": str(DEFAULT_INGESTION_ID),
                    "appeal_id": f"APL_{len(records):08d}",
                    "member_id": member["member_id"],
                    "appeal_date": appeal_date.isoformat(),
                    "outcome": np.random.choice(["UPHELD", "OVERTURNED", "PENDING"]),
                })
    return pd.DataFrame(records)


def generate_member_diagnosis(members_df: pd.DataFrame) -> pd.DataFrame:
    """Generate MemberDiagnosis records"""
    records = []
    icd10_codes = ["E11.9", "I10", "M79.3", "F32.9", "J44.1", "N18.6"]
    for _, member in members_df.head(8000).iterrows():  # Sample
        for _ in range(np.random.randint(0, 3)):  # 0-2 diagnoses per member
            records.append({
                "tenant_id": str(DEFAULT_TENANT_ID),
                "source_system": DEFAULT_SOURCE_SYSTEM,
                "source_file_id": "member_diagnosis.csv",
                "ingestion_id": str(DEFAULT_INGESTION_ID),
                "diagnosis_id": f"DX_{len(records):08d}",
                "member_id": member["member_id"],
                "icd10_code": np.random.choice(icd10_codes),
                "onset_date": (date(2023, 1, 1) + timedelta(days=np.random.randint(0, 730))).isoformat(),
            })
    return pd.DataFrame(records)


def generate_problem_list(members_df: pd.DataFrame) -> pd.DataFrame:
    """Generate ProblemList records"""
    records = []
    for _, member in members_df.head(3000).iterrows():  # Sample
        records.append({
            "tenant_id": str(DEFAULT_TENANT_ID),
            "source_system": DEFAULT_SOURCE_SYSTEM,
            "source_file_id": "problem_list.csv",
            "ingestion_id": str(DEFAULT_INGESTION_ID),
            "problem_id": f"PRB_{len(records):08d}",
            "member_id": member["member_id"],
            "condition_registry_id": f"REG_{np.random.randint(1, 20)}",
        })
    return pd.DataFrame(records)


def generate_referral(members_df: pd.DataFrame, num_months: int) -> pd.DataFrame:
    """Generate Referral records"""
    records = []
    start_date = date(2023, 12, 1)
    for month_idx in range(num_months):
        referral_date = start_date + timedelta(days=month_idx * 30 + np.random.randint(0, 30))
        for _, member in members_df.head(3000).iterrows():  # Sample
            if np.random.random() < 0.1:  # 10% have referrals
                records.append({
                    "tenant_id": str(DEFAULT_TENANT_ID),
                    "source_system": DEFAULT_SOURCE_SYSTEM,
                    "source_file_id": "referral.csv",
                    "ingestion_id": str(DEFAULT_INGESTION_ID),
                    "referral_id": f"REF_{len(records):08d}",
                    "member_id": member["member_id"],
                    "referral_date": referral_date.isoformat(),
                    "referring_provider_id": f"PROV_{np.random.randint(0, 1000):06d}",
                })
    return pd.DataFrame(records)


def generate_care_management_enrollment(members_df: pd.DataFrame, num_months: int) -> pd.DataFrame:
    """Generate CareManagementEnrollment records"""
    records = []
    start_date = date(2023, 12, 1)
    for month_idx in range(num_months):
        enrollment_date = start_date + timedelta(days=month_idx * 30 + np.random.randint(0, 30))
        for _, member in members_df.head(2000).iterrows():  # Sample
            if np.random.random() < 0.15:  # 15% enrolled in care management
                records.append({
                    "tenant_id": str(DEFAULT_TENANT_ID),
                    "source_system": DEFAULT_SOURCE_SYSTEM,
                    "source_file_id": "care_management_enrollment.csv",
                    "ingestion_id": str(DEFAULT_INGESTION_ID),
                    "enrollment_id": f"CMP_{len(records):08d}",
                    "member_id": member["member_id"],
                    "program_id": f"PROG_{np.random.randint(1, 10)}",
                    "enrollment_date": enrollment_date.isoformat(),
                })
    return pd.DataFrame(records)


def generate_call_center_contact(members_df: pd.DataFrame, num_months: int) -> pd.DataFrame:
    """Generate CallCenterContact records"""
    records = []
    start_date = date(2023, 12, 1)
    for month_idx in range(num_months):
        contact_date = start_date + timedelta(days=month_idx * 30 + np.random.randint(0, 30))
        for _, member in members_df.head(5000).iterrows():  # Sample
            if np.random.random() < 0.2:  # 20% have call center contacts
                records.append({
                    "tenant_id": str(DEFAULT_TENANT_ID),
                    "source_system": DEFAULT_SOURCE_SYSTEM,
                    "source_file_id": "call_center_contact.csv",
                    "ingestion_id": str(DEFAULT_INGESTION_ID),
                    "contact_id": f"CNT_{len(records):08d}",
                    "member_id": member["member_id"],
                    "contact_date": contact_date.isoformat(),
                    "contact_topic": np.random.choice(["CLAIM", "BENEFIT", "AUTHORIZATION", "GENERAL"]),
                })
    return pd.DataFrame(records)


def generate_market_event(num_months: int) -> pd.DataFrame:
    """Generate MarketEvent records"""
    records = []
    start_date = date(2023, 12, 1)
    event_types = ["MARKET_ENTRY", "MARKET_EXIT", "NETWORK_CHANGE", "REGULATORY_CHANGE"]
    for month_idx in range(num_months):
        event_date = start_date + timedelta(days=month_idx * 30 + np.random.randint(0, 30))
        if np.random.random() < 0.3:  # 30% chance of event per month
            records.append({
                "tenant_id": str(DEFAULT_TENANT_ID),
                "source_system": DEFAULT_SOURCE_SYSTEM,
                "source_file_id": "market_event.csv",
                "ingestion_id": str(DEFAULT_INGESTION_ID),
                "event_id": f"EVT_{len(records):08d}",
                "event_type": np.random.choice(event_types),
                "event_date": event_date.isoformat(),
                "market": np.random.choice(MARKETS),
            })
    return pd.DataFrame(records)


def generate_claims_lines(members_df: pd.DataFrame, providers_df: pd.DataFrame, num_months: int) -> pd.DataFrame:
    """Generate ClaimLine records (simplified - reusing from existing generator)"""
    # This is a placeholder - the existing generator already creates claims
    # We'll use the existing claims files
    return pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description="Generate comprehensive synthetic data for all canonical models")
    parser.add_argument("--members", type=int, default=10000, help="Number of members")
    parser.add_argument("--providers", type=int, default=1000, help="Number of providers")
    parser.add_argument("--months", type=int, default=24, help="Number of months of data")
    parser.add_argument("--out", type=str, default=None, help="Output directory (default: data/source_data/synthetic)")
    
    args = parser.parse_args()
    
    out_path = Path(args.out) if args.out else SYNTHETIC_DATA_DIR
    out_path.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 Generating comprehensive synthetic data for {args.months} months")
    print(f"📁 Output directory: {out_path.absolute()}")
    print()
    
    # 1. Generate core member data
    print("1. Generating Member Master...")
    members_df = generate_member_master(args.members)
    members_df.to_parquet(out_path / "member_master.parquet", index=False)
    members_df.to_csv(out_path / "member_master.csv", index=False)
    print(f"   ✅ Generated {len(members_df):,} member records")
    
    # 2. Generate eligibility enrollment
    print("2. Generating Eligibility Enrollment...")
    enrollments_df = generate_eligibility_enrollment(members_df, args.months)
    enrollments_df.to_parquet(out_path / "eligibility_enrollment.parquet", index=False)
    enrollments_df.to_csv(out_path / "eligibility_enrollment.csv", index=False)
    print(f"   ✅ Generated {len(enrollments_df):,} enrollment records")
    
    # 3. Generate risk stratification
    print("3. Generating Risk Stratification...")
    risk_df = generate_risk_stratification(members_df, args.months)
    risk_df.to_parquet(out_path / "risk_stratification.parquet", index=False)
    risk_df.to_csv(out_path / "risk_stratification.csv", index=False)
    print(f"   ✅ Generated {len(risk_df):,} risk records")
    
    # 4. Generate provider data
    print("4. Generating Provider Master...")
    providers_df = generate_provider_master(args.providers)
    providers_df.to_parquet(out_path / "provider_master.parquet", index=False)
    providers_df.to_csv(out_path / "provider_master.csv", index=False)
    print(f"   ✅ Generated {len(providers_df):,} provider records")
    
    # 5. Generate facility master
    print("5. Generating Facility Master...")
    facilities_df = generate_facility_master(500)
    facilities_df.to_parquet(out_path / "facility_master.parquet", index=False)
    facilities_df.to_csv(out_path / "facility_master.csv", index=False)
    print(f"   ✅ Generated {len(facilities_df):,} facility records")
    
    # 6. Generate network configuration
    print("6. Generating Network Configuration...")
    networks_df = generate_network_configuration(10)
    networks_df.to_parquet(out_path / "network_configuration.parquet", index=False)
    networks_df.to_csv(out_path / "network_configuration.csv", index=False)
    print(f"   ✅ Generated {len(networks_df):,} network records")
    
    # 7. Generate provider contracts
    print("7. Generating Provider Contracts...")
    contracts_df = generate_provider_contract(providers_df, networks_df)
    contracts_df.to_parquet(out_path / "provider_contract.parquet", index=False)
    contracts_df.to_csv(out_path / "provider_contract.csv", index=False)
    print(f"   ✅ Generated {len(contracts_df):,} contract records")
    
    # 8. Generate claim headers (sample from existing claims)
    print("8. Generating Claim Headers...")
    # Read existing claims if available
    claims_files = list((out_path / "claims").rglob("*.csv")) if (out_path / "claims").exists() else []
    if claims_files:
        sample_claims = pd.read_csv(claims_files[0], nrows=10000)
        claim_headers_df = generate_claim_header(sample_claims)
    else:
        # Generate minimal sample
        claim_headers_df = pd.DataFrame([{
            "tenant_id": str(DEFAULT_TENANT_ID),
            "source_system": DEFAULT_SOURCE_SYSTEM,
            "source_file_id": "claim_header.csv",
            "ingestion_id": str(DEFAULT_INGESTION_ID),
            "claim_id": f"CLM_{i:08d}",
            "claim_type": "OUTPATIENT",
            "member_id": f"MEM_{np.random.randint(0, args.members):08d}",
            "claim_received_date": (date(2023, 12, 1) + timedelta(days=np.random.randint(0, 730))).isoformat(),
            "claim_status": "PAID",
            "total_allowed": round(np.random.uniform(100, 5000), 2),
            "total_paid": round(np.random.uniform(80, 4500), 2),
        } for i in range(5000)])
    claim_headers_df.to_parquet(out_path / "claim_header.parquet", index=False)
    claim_headers_df.to_csv(out_path / "claim_header.csv", index=False)
    print(f"   ✅ Generated {len(claim_headers_df):,} claim header records")
    
    # 9. Generate episode of care
    print("9. Generating Episode of Care...")
    episodes_df = generate_episode_of_care(members_df, args.months)
    episodes_df.to_parquet(out_path / "episode_of_care.parquet", index=False)
    episodes_df.to_csv(out_path / "episode_of_care.csv", index=False)
    print(f"   ✅ Generated {len(episodes_df):,} episode records")
    
    # 10. Generate pharmacy claims
    print("10. Generating Pharmacy Claims...")
    pharmacy_df = generate_pharmacy_claims(members_df, args.months)
    pharmacy_df.to_parquet(out_path / "pharmacy_claims.parquet", index=False)
    pharmacy_df.to_csv(out_path / "pharmacy_claims.csv", index=False)
    print(f"   ✅ Generated {len(pharmacy_df):,} pharmacy claim records")
    
    # 11. Generate benefit design
    print("11. Generating Benefit Design...")
    plan_ids = enrollments_df["plan_id"].unique().tolist()[:50]  # Sample plans
    benefits_df = generate_benefit_design(plan_ids)
    benefits_df.to_parquet(out_path / "benefit_design.parquet", index=False)
    benefits_df.to_csv(out_path / "benefit_design.csv", index=False)
    print(f"   ✅ Generated {len(benefits_df):,} benefit design records")
    
    # 12. Generate member accumulator
    print("12. Generating Member Accumulator...")
    accumulators_df = generate_member_accumulator(members_df)
    accumulators_df.to_parquet(out_path / "member_accumulator.parquet", index=False)
    accumulators_df.to_csv(out_path / "member_accumulator.csv", index=False)
    print(f"   ✅ Generated {len(accumulators_df):,} accumulator records")
    
    # 13. Generate prior authorization
    print("13. Generating Prior Authorization Requests...")
    pa_df = generate_prior_authorization(members_df, args.months)
    pa_df.to_parquet(out_path / "prior_authorization_request.parquet", index=False)
    pa_df.to_csv(out_path / "prior_authorization_request.csv", index=False)
    print(f"   ✅ Generated {len(pa_df):,} PA request records")
    
    # 14. Generate concurrent review
    print("14. Generating Concurrent Reviews...")
    concurrent_df = generate_concurrent_review(members_df, args.months)
    concurrent_df.to_parquet(out_path / "concurrent_review.parquet", index=False)
    concurrent_df.to_csv(out_path / "concurrent_review.csv", index=False)
    print(f"   ✅ Generated {len(concurrent_df):,} concurrent review records")
    
    # 15. Generate appeal grievance
    print("15. Generating Appeal Grievance...")
    appeals_df = generate_appeal_grievance(members_df, args.months)
    appeals_df.to_parquet(out_path / "appeal_grievance.parquet", index=False)
    appeals_df.to_csv(out_path / "appeal_grievance.csv", index=False)
    print(f"   ✅ Generated {len(appeals_df):,} appeal records")
    
    # 16. Generate member diagnosis
    print("16. Generating Member Diagnosis...")
    diagnosis_df = generate_member_diagnosis(members_df)
    diagnosis_df.to_parquet(out_path / "member_diagnosis.parquet", index=False)
    diagnosis_df.to_csv(out_path / "member_diagnosis.csv", index=False)
    print(f"   ✅ Generated {len(diagnosis_df):,} diagnosis records")
    
    # 17. Generate problem list
    print("17. Generating Problem List...")
    problems_df = generate_problem_list(members_df)
    problems_df.to_parquet(out_path / "problem_list.parquet", index=False)
    problems_df.to_csv(out_path / "problem_list.csv", index=False)
    print(f"   ✅ Generated {len(problems_df):,} problem records")
    
    # 18. Generate referral
    print("18. Generating Referrals...")
    referrals_df = generate_referral(members_df, args.months)
    referrals_df.to_parquet(out_path / "referral.parquet", index=False)
    referrals_df.to_csv(out_path / "referral.csv", index=False)
    print(f"   ✅ Generated {len(referrals_df):,} referral records")
    
    # 19. Generate care management enrollment
    print("19. Generating Care Management Enrollment...")
    cm_enrollments_df = generate_care_management_enrollment(members_df, args.months)
    cm_enrollments_df.to_parquet(out_path / "care_management_enrollment.parquet", index=False)
    cm_enrollments_df.to_csv(out_path / "care_management_enrollment.csv", index=False)
    print(f"   ✅ Generated {len(cm_enrollments_df):,} care management enrollment records")
    
    # 20. Generate call center contact
    print("20. Generating Call Center Contacts...")
    contacts_df = generate_call_center_contact(members_df, args.months)
    contacts_df.to_parquet(out_path / "call_center_contact.parquet", index=False)
    contacts_df.to_csv(out_path / "call_center_contact.csv", index=False)
    print(f"   ✅ Generated {len(contacts_df):,} call center contact records")
    
    # 21. Generate market event
    print("21. Generating Market Events...")
    market_events_df = generate_market_event(args.months)
    market_events_df.to_parquet(out_path / "market_event.parquet", index=False)
    market_events_df.to_csv(out_path / "market_event.csv", index=False)
    print(f"   ✅ Generated {len(market_events_df):,} market event records")
    
    print()
    print("✅ All comprehensive datasets generated successfully!")
    print(f"📁 Output directory: {out_path.absolute()}")
    print()
    print("Generated files:")
    for file in sorted(out_path.glob("*.csv")):
        print(f"  - {file.name}")


if __name__ == "__main__":
    main()

