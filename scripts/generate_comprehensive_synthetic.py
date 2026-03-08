#!/usr/bin/env python3
"""
Comprehensive Synthetic Data Generator
Uses comprehensive canonical schemas and generates 24 months of data
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
AGE_BANDS = ["0-17", "18-34", "35-49", "50-64", "65+"]
GENDERS = ["M", "F", "U"]
NETWORK_TIERS = ["STANDARD", "NARROW", "BROAD"]

SERVICE_CATEGORIES = {
    "MRI": {"codes": ["72141", "72142", "72146", "72148", "72149", "72158"], "pos": ["11", "22", "23"], "allowed": (800, 2500)},
    "CT": {"codes": ["70450", "70460", "70470", "71250"], "pos": ["11", "22", "23"], "allowed": (400, 1200)},
    "INFUSION": {"codes": ["96413", "96415", "96417"], "pos": ["22", "19", "11"], "allowed": (500, 2000)},
    "PT": {"codes": ["97110", "97112", "97140"], "pos": ["11", "12"], "allowed": (80, 200)},
    "SPECIALTY_VISIT": {"codes": ["99213", "99214", "99215"], "pos": ["11"], "allowed": (150, 400)},
    "URGENT_CARE": {"codes": ["99281", "99282", "99283"], "pos": ["20"], "allowed": (200, 600)},
    "ER_VISIT": {"codes": ["99284", "99285"], "pos": ["23"], "allowed": (800, 2500)},
}

PROVIDER_SPECIALTIES = ["RADIOLOGY", "ONCOLOGY", "PHYSICAL_THERAPY", "PRIMARY_CARE", "EMERGENCY", "ORTHOPEDICS"]

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
DEFAULT_SOURCE_SYSTEM = "SYNTHETIC_GENERATOR"
DEFAULT_INGESTION_ID = UUID("00000000-0000-0000-0000-000000000002")


def generate_member_master(count: int, start_date: date) -> List[Dict[str, Any]]:
    """Generate MemberMaster records"""
    members = []
    for i in range(count):
        lob = np.random.choice(LOBS, p=[0.5, 0.25, 0.2, 0.05])
        market = np.random.choice(MARKETS)
        
        # Age distribution by LOB
        if lob == "MA":
            age_band = np.random.choice(AGE_BANDS, p=[0.0, 0.05, 0.15, 0.35, 0.45])
        elif lob == "MEDICAID":
            age_band = np.random.choice(AGE_BANDS, p=[0.4, 0.3, 0.15, 0.1, 0.05])
        else:
            age_band = np.random.choice(AGE_BANDS, p=[0.15, 0.25, 0.25, 0.25, 0.1])
        
        # Calculate age from age band
        age = int(age_band.split("-")[0]) if "-" in age_band else 65
        if age_band == "65+":
            age = np.random.randint(65, 90)
        else:
            age = np.random.randint(int(age_band.split("-")[0]), int(age_band.split("-")[1]) + 1)
        
        birth_year = start_date.year - age
        dob = date(birth_year, np.random.randint(1, 13), np.random.randint(1, 29))
        
        # Risk score (skewed right)
        risk_score = max(0.5, min(3.0, np.random.gamma(2.0, 0.5)))
        
        member = {
            "tenant_id": str(DEFAULT_TENANT_ID),
            "source_system": DEFAULT_SOURCE_SYSTEM,
            "source_file_id": "member_master.csv",
            "ingestion_id": str(DEFAULT_INGESTION_ID),
            "member_id": f"MEM_{i:08d}",
            "subscriber_id": f"SUB_{i:08d}",
            "family_id": f"FAM_{i // 3:06d}" if np.random.random() > 0.3 else None,
            "household_id": f"HH_{i // 2:06d}" if np.random.random() > 0.4 else None,
            "dob": dob.isoformat(),
            "birth_year": birth_year,
            "age": age,
            "gender": np.random.choice(["M", "F", "U"]),
            "race": np.random.choice(["WHITE", "BLACK", "ASIAN", "HISPANIC", "OTHER", None], p=[0.6, 0.15, 0.1, 0.1, 0.04, 0.01]),
            "ethnicity": np.random.choice(["HISPANIC", "NON_HISPANIC", None], p=[0.15, 0.8, 0.05]),
            "preferred_language": np.random.choice(["EN", "ES", "OTHER", None], p=[0.85, 0.1, 0.04, 0.01]),
            "address_zip5": f"{np.random.randint(10000, 99999)}",
            "county": f"County_{market}",
            "state": market[:2] if len(market) > 2 else "NY",
            "rural_flag": np.random.random() < 0.2,
            "urbanicity_index": np.random.choice(["URBAN", "SUBURBAN", "RURAL"]),
            "income_band": np.random.choice(["LOW", "MEDIUM", "HIGH", None], p=[0.3, 0.5, 0.15, 0.05]),
            "education_band": np.random.choice(["HIGH_SCHOOL", "SOME_COLLEGE", "COLLEGE", "GRADUATE", None], p=[0.3, 0.25, 0.3, 0.1, 0.05]),
            "employment_status": np.random.choice(["EMPLOYED", "UNEMPLOYED", "RETIRED", "DISABLED", None], p=[0.6, 0.1, 0.2, 0.05, 0.05]),
            "housing_insecurity_flag": np.random.random() < 0.1,
            "food_insecurity_flag": np.random.random() < 0.08,
            "transportation_barrier_flag": np.random.random() < 0.12,
            "neighborhood_deprivation_index": round(np.random.uniform(0, 1), 3) if np.random.random() > 0.3 else None,
            "area_vulnerability_index": round(np.random.uniform(0, 1), 3) if np.random.random() > 0.3 else None,
            "pregnancy_flag": np.random.random() < 0.05,
            "frailty_flag": np.random.random() < 0.1 if age > 65 else False,
            "disability_flag": np.random.random() < 0.15,
            "hospice_flag": np.random.random() < 0.02,
            "ESRD_flag": np.random.random() < 0.01,
            "dual_eligible_flag": np.random.random() < 0.1 if lob in ["MA", "MEDICAID"] else False,
            "portal_user_flag": np.random.random() < 0.4,
            "preferred_contact_channel": np.random.choice(["EMAIL", "PHONE", "PORTAL", "MAIL", None], p=[0.3, 0.4, 0.2, 0.05, 0.05]),
        }
        members.append(member)
    return members


def generate_eligibility_enrollment(members: List[Dict], start_date: date, num_months: int) -> List[Dict[str, Any]]:
    """Generate EligibilityEnrollment records"""
    enrollments = []
    current_month = start_date.replace(day=1)
    
    for month_idx in range(num_months):
        for member in members:
            coverage_month = current_month.strftime("%Y-%m")
            plan_id = f"PLAN_{member['member_id'].split('_')[1][:4]}"
            
            enrollment = {
                "tenant_id": str(DEFAULT_TENANT_ID),
                "source_system": DEFAULT_SOURCE_SYSTEM,
                "source_file_id": "eligibility_enrollment.csv",
                "ingestion_id": str(DEFAULT_INGESTION_ID),
                "member_id": member["member_id"],
                "coverage_month": coverage_month,
                "plan_id": plan_id,
                "line_of_business": member.get("lob", np.random.choice(LOBS)),
                "product_id": f"PROD_{np.random.randint(1, 5)}",
                "benefit_package_id": f"BEN_{np.random.randint(1, 3)}",
                "group_id": f"GRP_{np.random.randint(1, 100)}" if np.random.random() > 0.3 else None,
                "segment": np.random.choice(["ASO", "FI", None], p=[0.4, 0.5, 0.1]),
                "network_id": f"NET_{np.random.randint(1, 5)}",
                "network_tier": np.random.choice(["STANDARD", "NARROW", "BROAD"]),
                "enrollment_start_date": (current_month - timedelta(days=365)).isoformat() if month_idx == 0 else None,
                "enrollment_end_date": None,
                "coverage_status": "ACTIVE" if np.random.random() > 0.02 else "TERMED",
                "reason_code": None,
                "member_cost_share_level": np.random.choice(["BRONZE", "SILVER", "GOLD", "PLATINUM", None], p=[0.2, 0.3, 0.3, 0.15, 0.05]),
                "PCP_id": f"PCP_{np.random.randint(1, 1000)}" if np.random.random() > 0.4 else None,
                "care_management_program_id": f"CMP_{np.random.randint(1, 10)}" if np.random.random() > 0.7 else None,
            }
            enrollments.append(enrollment)
        
        # Move to next month
        if current_month.month == 12:
            current_month = date(current_month.year + 1, 1, 1)
        else:
            current_month = date(current_month.year, current_month.month + 1, 1)
    
    return enrollments


def generate_claim_lines(members: List[Dict], providers: List[Dict], start_date: date, num_months: int) -> List[Dict[str, Any]]:
    """Generate ClaimLine records with behavioral patterns"""
    claims = []
    current_date = start_date
    
    # Policy effective dates
    policy_dates = {
        "PA_MRI_OP_001": start_date + timedelta(days=180),
        "SOC_INFUSION_002": start_date + timedelta(days=210),
        "PT_FREQ_003": start_date + timedelta(days=240),
    }
    
    for month_idx in range(num_months):
        year = current_date.year
        month = current_date.month
        
        # Claims per month (seasonality)
        base_claims = 50000
        seasonality = 1.0 + 0.2 * np.sin(2 * np.pi * month / 12)
        claims_this_month = int(base_claims * seasonality * np.random.uniform(0.8, 1.2))
        
        for claim_idx in range(claims_this_month):
            member = np.random.choice(members)
            provider = np.random.choice(providers)
            
            service_category = np.random.choice(list(SERVICE_CATEGORIES.keys()))
            service_info = SERVICE_CATEGORIES[service_category]
            code = np.random.choice(service_info["codes"])
            pos = np.random.choice(service_info["pos"])
            
            # Apply behavioral patterns
            volume_mult = 1.0
            cost_mult = 1.0
            
            # Prior Auth Backfire
            if current_date >= policy_dates["PA_MRI_OP_001"]:
                if service_category == "MRI" and pos == "11":
                    volume_mult *= 0.7
                elif service_category in ["CT", "ER_IMAGING"]:
                    volume_mult *= 1.4
                    cost_mult *= 1.2
            
            # Site-of-Care Success
            if current_date >= policy_dates["SOC_INFUSION_002"]:
                if service_category == "INFUSION":
                    if pos == "22":
                        volume_mult *= 0.6
                    elif pos == "19":
                        volume_mult *= 1.5
                        cost_mult *= 0.7
            
            if np.random.random() > volume_mult:
                continue
            
            service_date = current_date + timedelta(days=np.random.randint(0, 28))
            paid_date = service_date + timedelta(days=np.random.randint(30, 60))
            
            base_allowed = np.random.uniform(*service_info["allowed"])
            allowed_amount = base_allowed * cost_mult * np.random.uniform(0.9, 1.1)
            paid_amount = allowed_amount * np.random.uniform(0.85, 0.95)
            
            claim_line = {
                "tenant_id": str(DEFAULT_TENANT_ID),
                "source_system": DEFAULT_SOURCE_SYSTEM,
                "source_file_id": f"claims_{year}_{month:02d}.csv",
                "ingestion_id": str(DEFAULT_INGESTION_ID),
                "claim_line_id": f"CLM_{uuid4().hex[:16].upper()}",
                "claim_id": f"CLM_{uuid4().hex[:12].upper()}",
                "member_id": member["member_id"],
                "cpt_hcpcs": code,
                "service_date_from": service_date.isoformat(),
                "service_date_to": service_date.isoformat(),
                "place_of_service": pos,
                "service_category": service_category,
                "site_of_care_class": "OFFICE" if pos == "11" else "HOSPITAL_OP" if pos == "22" else "ER",
                "units": round(np.random.uniform(0.5, 2.0) * volume_mult, 2),
                "unit_type": "VISIT",
                "rendering_provider_id": provider["provider_id"],
                "facility_id": provider.get("facility_id"),
                "in_network_flag": np.random.random() > 0.2,
                "network_id": f"NET_{np.random.randint(1, 5)}",
                "network_tier": np.random.choice(["STANDARD", "NARROW", "BROAD"]),
                "benefit_category": "OUTPATIENT" if pos in ["11", "22"] else "EMERGENCY",
                "prior_auth_required_flag": np.random.random() < 0.1,
                "referral_required_flag": np.random.random() < 0.15,
                "billed_amount": round(allowed_amount * 1.2, 2),
                "allowed_amount": round(allowed_amount, 2),
                "paid_amount": round(paid_amount, 2),
                "copay_amount": round(np.random.uniform(20, 100), 2) if np.random.random() > 0.5 else None,
                "coinsurance_amount": round(allowed_amount * 0.2, 2) if np.random.random() > 0.6 else None,
                "deductible_amount": round(np.random.uniform(0, 500), 2) if np.random.random() > 0.7 else None,
                "member_resp_amount": round(np.random.uniform(0, 200), 2),
                "emergency_flag": pos == "23",
                "avoidable_ed_flag": pos == "23" and np.random.random() < 0.3,
            }
            claims.append(claim_line)
        
        # Move to next month
        if month == 12:
            current_date = date(year + 1, 1, 1)
        else:
            current_date = date(year, month + 1, 1)
    
    return claims


def generate_provider_master(count: int) -> List[Dict[str, Any]]:
    """Generate ProviderMaster records"""
    providers = []
    for i in range(count):
        specialty = np.random.choice(PROVIDER_SPECIALTIES)
        market = np.random.choice(MARKETS)
        
        provider = {
            "tenant_id": str(DEFAULT_TENANT_ID),
            "source_system": DEFAULT_SOURCE_SYSTEM,
            "source_file_id": "provider_master.csv",
            "ingestion_id": str(DEFAULT_INGESTION_ID),
            "provider_id": f"PROV_{i:08d}",
            "npi": f"{np.random.randint(1000000000, 9999999999)}",
            "provider_name": f"{specialty} Provider {i+1}",
            "provider_type": "FACILITY" if np.random.random() > 0.6 else "INDIVIDUAL",
            "specialty_primary": specialty,
            "specialty_secondary": np.random.choice(PROVIDER_SPECIALTIES) if np.random.random() > 0.7 else None,
            "taxonomy_codes": [f"TAX_{np.random.randint(100, 999)}"],
            "org_id": f"ORG_{np.random.randint(1, 50)}" if np.random.random() > 0.4 else None,
            "system_affiliation_id": f"SYS_{np.random.randint(1, 10)}" if np.random.random() > 0.5 else None,
            "practice_location_zip": f"{np.random.randint(10000, 99999)}",
            "practice_location_county": f"County_{market}",
            "practice_location_state": market[:2] if len(market) > 2 else "NY",
            "accepting_new_patients_flag": np.random.random() > 0.3,
            "telehealth_capable_flag": np.random.random() > 0.6,
            "languages": ["EN"] + (["ES"] if np.random.random() > 0.7 else []),
        }
        providers.append(provider)
    return providers


def main():
    parser = argparse.ArgumentParser(description="Generate comprehensive synthetic healthcare data (24 months)")
    parser.add_argument("--out", type=str, default="data/synthetic", help="Output directory")
    parser.add_argument("--members", type=int, default=100000, help="Number of members")
    parser.add_argument("--providers", type=int, default=10000, help="Number of providers")
    parser.add_argument("--months", type=int, default=24, help="Number of months (default: 24)")
    
    args = parser.parse_args()
    
    # Set seed
    np.random.seed(RANDOM_SEED)
    
    # Create output directory
    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Calculate start date (24 months ago from today)
    end_date = date.today()
    start_date = date(end_date.year - 2, end_date.month, 1) if end_date.month > 1 else date(end_date.year - 3, 12, 1)
    
    print(f"Generating comprehensive synthetic data...")
    print(f"Members: {args.members}, Providers: {args.providers}, Months: {args.months}")
    print(f"Date range: {start_date} to {end_date}")
    print()
    
    # 1. Generate Member Master
    print("1. Generating Member Master...")
    members = generate_member_master(args.members, start_date)
    members_df = pd.DataFrame(members)
    members_df.to_parquet(out_path / "member_master.parquet", index=False)
    members_df.to_csv(out_path / "member_master.csv", index=False)
    print(f"   ✅ Generated {len(members):,} members")
    
    # 2. Generate Eligibility & Enrollment
    print("2. Generating Eligibility & Enrollment...")
    enrollments = generate_eligibility_enrollment(members, start_date, args.months)
    enrollments_df = pd.DataFrame(enrollments)
    enrollments_df.to_parquet(out_path / "eligibility_enrollment.parquet", index=False)
    enrollments_df.to_csv(out_path / "eligibility_enrollment.csv", index=False)
    print(f"   ✅ Generated {len(enrollments):,} enrollment records")
    
    # 3. Generate Provider Master
    print("3. Generating Provider Master...")
    providers = generate_provider_master(args.providers)
    providers_df = pd.DataFrame(providers)
    providers_df.to_parquet(out_path / "provider_master.parquet", index=False)
    providers_df.to_csv(out_path / "provider_master.csv", index=False)
    print(f"   ✅ Generated {len(providers):,} providers")
    
    # 4. Generate Claims Lines (partitioned by month)
    print("4. Generating Claims Lines (this may take a while)...")
    claims = generate_claim_lines(members, providers, start_date, args.months)
    
    # Write claims partitioned by year/month
    claims_df = pd.DataFrame(claims)
    for year in range(start_date.year, end_date.year + 1):
        year_dir = out_path / "claims" / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)
        
        for month in range(1, 13):
            if year == start_date.year and month < start_date.month:
                continue
            if year == end_date.year and month > end_date.month:
                continue
            
            month_claims = claims_df[
                (pd.to_datetime(claims_df["service_date_from"]).dt.year == year) &
                (pd.to_datetime(claims_df["service_date_from"]).dt.month == month)
            ]
            
            if len(month_claims) > 0:
                month_claims.to_parquet(year_dir / f"claims_{year}_{month:02d}.parquet", index=False)
                if len(month_claims) < 100000:  # Only write CSV for smaller files
                    month_claims.to_csv(year_dir / f"claims_{year}_{month:02d}.csv", index=False)
    
    print(f"   ✅ Generated {len(claims):,} claim lines")
    
    # 5. Generate sample data for other domains
    print("5. Generating additional datasets...")
    
    # Risk Stratification (sample)
    risk_records = []
    for member in members[:10000]:  # Sample
        for month_idx in range(0, args.months, 3):  # Quarterly
            risk_date = start_date + timedelta(days=month_idx * 30)
            risk_records.append({
                "tenant_id": str(DEFAULT_TENANT_ID),
                "source_system": DEFAULT_SOURCE_SYSTEM,
                "source_file_id": "risk_stratification.csv",
                "ingestion_id": str(DEFAULT_INGESTION_ID),
                "member_id": member["member_id"],
                "risk_run_date": risk_date.isoformat(),
                "month": risk_date.strftime("%Y-%m"),
                "risk_score": round(np.random.gamma(2.0, 0.5), 2),
                "risk_model_name": "HCC",
                "risk_model_version": "2024.1",
                "predicted_cost_pmpm": round(np.random.uniform(200, 2000), 2),
                "predicted_admission_risk": round(np.random.uniform(0, 0.3), 3),
                "predicted_ed_risk": round(np.random.uniform(0, 0.2), 3),
                "chronic_condition_count": np.random.randint(0, 5),
            })
    
    risk_df = pd.DataFrame(risk_records)
    risk_df.to_parquet(out_path / "risk_stratification.parquet", index=False)
    risk_df.to_csv(out_path / "risk_stratification.csv", index=False)
    print(f"   ✅ Generated {len(risk_records):,} risk stratification records")
    
    print()
    print("✅ All datasets generated successfully!")
    print(f"📁 Output directory: {out_path.absolute()}")
    print()
    print("Generated files:")
    print("  - member_master.parquet / .csv")
    print("  - eligibility_enrollment.parquet / .csv")
    print("  - provider_master.parquet / .csv")
    print("  - claims/YYYY/claims_YYYY_MM.parquet (partitioned)")
    print("  - risk_stratification.parquet / .csv")


if __name__ == "__main__":
    main()

