#!/usr/bin/env python3
"""
Comprehensive Synthetic Healthcare Data Generator
Enterprise-grade, deterministic, with realistic behavioral patterns
Generates datasets beyond minimum specifications for full platform capabilities
"""
from __future__ import annotations

import argparse
import json
import numpy as np
import pandas as pd
import polars as pl
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Any, Optional, Dict, List
from uuid import uuid4
import hashlib

# Fixed seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# ============================================================================
# CONFIGURATION
# ============================================================================

MARKETS = ["NYC", "DFW", "BOS", "CHI", "LA", "SEA", "PHX", "ATL"]
LOBS = ["COMMERCIAL", "MA", "MEDICAID", "SELF_INSURED"]
AGE_BANDS = ["0-17", "18-34", "35-49", "50-64", "65+"]
GENDERS = ["M", "F", "U"]
NETWORK_TIERS = ["STANDARD", "NARROW", "BROAD"]

# Comprehensive service categories with realistic codes
SERVICE_CATEGORIES = {
    "MRI": {
        "codes": ["72141", "72142", "72146", "72148", "72149", "72158", "70551", "70552", "70553"],
        "pos_codes": ["11", "22", "23"],  # Office, Hospital OP, ER
        "base_allowed_range": (800, 2500),
        "er_allowed_range": (1200, 3500),
    },
    "CT": {
        "codes": ["70450", "70460", "70470", "71250", "72125", "74150", "74160"],
        "pos_codes": ["11", "22", "23"],
        "base_allowed_range": (400, 1200),
        "er_allowed_range": (800, 2000),
    },
    "ER_IMAGING": {
        "codes": ["70450", "70460", "72141", "70470", "71250"],
        "pos_codes": ["23"],
        "base_allowed_range": (1000, 3500),
    },
    "INFUSION": {
        "codes": ["96413", "96415", "96417", "96416", "96365", "96372"],
        "pos_codes": ["22", "19", "11"],
        "base_allowed_range": (500, 2000),
        "freestanding_allowed_range": (300, 1200),
    },
    "PT": {
        "codes": ["97110", "97112", "97140", "97116", "97161", "97162", "97163"],
        "pos_codes": ["11", "12"],
        "base_allowed_range": (80, 200),
    },
    "SPECIALTY_VISIT": {
        "codes": ["99213", "99214", "99215", "99242", "99243", "99244", "99254", "99255"],
        "pos_codes": ["11"],
        "base_allowed_range": (150, 400),
    },
    "URGENT_CARE": {
        "codes": ["99281", "99282", "99283"],
        "pos_codes": ["20"],
        "base_allowed_range": (200, 600),
    },
    "ER_VISIT": {
        "codes": ["99284", "99285"],
        "pos_codes": ["23"],
        "base_allowed_range": (800, 2500),
    },
    "LAB": {
        "codes": ["80053", "85025", "85027", "80061", "82947"],
        "pos_codes": ["11", "22"],
        "base_allowed_range": (20, 150),
    },
    "PHARMACY": {
        "codes": ["J9264", "J1745", "J9218", "J9306"],
        "pos_codes": ["01"],
        "base_allowed_range": (100, 5000),
    },
    "SURGERY": {
        "codes": ["27447", "29881", "29882", "45378", "45385"],
        "pos_codes": ["24", "22"],
        "base_allowed_range": (2000, 15000),
    },
}

PROVIDER_SPECIALTIES = {
    "RADIOLOGY": {"codes": ["MRI", "CT", "ER_IMAGING"], "facility_type": "FREESTANDING"},
    "ONCOLOGY": {"codes": ["INFUSION", "SPECIALTY_VISIT"], "facility_type": "HOSPITAL_OP"},
    "PHYSICAL_THERAPY": {"codes": ["PT"], "facility_type": "OFFICE"},
    "PRIMARY_CARE": {"codes": ["SPECIALTY_VISIT"], "facility_type": "OFFICE"},
    "EMERGENCY": {"codes": ["ER_VISIT", "ER_IMAGING", "URGENT_CARE"], "facility_type": "ER"},
    "ORTHOPEDICS": {"codes": ["SPECIALTY_VISIT", "PT", "MRI", "SURGERY"], "facility_type": "OFFICE"},
    "LAB": {"codes": ["LAB"], "facility_type": "FREESTANDING"},
    "SURGERY": {"codes": ["SURGERY"], "facility_type": "HOSPITAL_OP"},
}

FACILITY_TYPES = {
    "11": "OFFICE",
    "12": "HOME",
    "19": "FREESTANDING",
    "20": "URGENT_CARE",
    "22": "HOSPITAL_OP",
    "23": "ER",
    "24": "ASC",
}

# Policy definitions (matches seed_policies.py)
POLICIES_DATA = [
    {
        "policy_id": "PA_MRI_OP_001",
        "policy_name": "Outpatient MRI Prior Authorization",
        "policy_type": "PRIOR_AUTH",
        "effective_date": "2024-07-01",
        "affected_codes": ["72148", "72149", "72158"],
        "affected_pos": ["11"],
        "scope": {"lob": ["COMMERCIAL"], "markets": ["NYC", "DFW"]},
    },
    {
        "policy_id": "SOC_INFUSION_002",
        "policy_name": "Infusion Site-of-Care Optimization",
        "policy_type": "SITE_OF_CARE",
        "effective_date": "2023-07-01",
        "affected_codes": ["96413", "96415", "96417"],
        "affected_pos": ["22"],
        "preferred_pos": ["19"],
        "scope": {"lob": ["COMMERCIAL", "MA"], "markets": ["ALL"]},
    },
    {
        "policy_id": "PT_FREQ_003",
        "policy_name": "Physical Therapy Visit Limit",
        "policy_type": "DURATION_FREQUENCY_LIMIT",
        "effective_date": "2023-01-01",
        "affected_codes": ["97110", "97112", "97140"],
        "max_visits": 20,
        "scope": {"lob": ["COMMERCIAL", "MEDICAID"], "markets": ["ALL"]},
    },
    {
        "policy_id": "CS_UCC_004",
        "policy_name": "Urgent Care Copay Increase",
        "policy_type": "COST_SHARING",
        "effective_date": "2024-04-01",
        "affected_codes": ["99281", "99282", "99283"],
        "copay_change": {"from": 40, "to": 75},
        "scope": {"lob": ["COMMERCIAL"], "markets": ["ALL"]},
    },
    {
        "policy_id": "COMPOUND_IMG_005",
        "policy_name": "Advanced Imaging Control Bundle",
        "policy_type": "COMPOSITE",
        "effective_date": "2024-01-01",
        "affected_codes": ["70551", "70552", "70553"],
        "scope": {"lob": ["COMMERCIAL"], "markets": ["NYC"]},
    },
]


def generate_member_enrollment(count: int, start_month: date, num_months: int) -> pd.DataFrame:
    """Generate comprehensive member enrollment dataset"""
    records = []
    
    # Generate members
    members = []
    for i in range(count):
        lob = np.random.choice(LOBS, p=[0.5, 0.25, 0.2, 0.05])
        market = np.random.choice(MARKETS)
        
        # Age distribution varies by LOB
        if lob == "MA":
            age_band = np.random.choice(AGE_BANDS, p=[0.0, 0.05, 0.15, 0.35, 0.45])
        elif lob == "MEDICAID":
            age_band = np.random.choice(AGE_BANDS, p=[0.4, 0.3, 0.15, 0.1, 0.05])
        else:
            age_band = np.random.choice(AGE_BANDS, p=[0.15, 0.25, 0.25, 0.25, 0.1])
        
        # Risk score (skewed right - most members low risk)
        risk_score = np.random.gamma(shape=2.0, scale=0.5)  # Skewed right
        risk_score = max(0.5, min(3.0, risk_score))  # Clamp to [0.5, 3.0]
        
        # Network tier
        network_tier = np.random.choice(NETWORK_TIERS, p=[0.6, 0.25, 0.1, 0.05])
        
        members.append({
            "member_id": f"MEM_{i:08d}",
            "lob": lob,
            "market": market,
            "age_band": age_band,
            "gender": np.random.choice(GENDERS),
            "risk_score": round(risk_score, 2),
            "network_tier": network_tier,
        })
    
    # Generate enrollment records month by month
    current_month = start_month
    for month_idx in range(num_months):
        for member in members:
            # Members can disenroll/reenroll
            enrolled = True
            if month_idx > 0:
                # Small chance of disenrollment
                if np.random.random() < 0.02:  # 2% monthly churn
                    enrolled = False
            
            records.append({
                "member_id": member["member_id"],
                "lob": member["lob"],
                "market": member["market"],
                "enrollment_month": current_month.strftime("%Y-%m"),
                "age_band": member["age_band"],
                "gender": member["gender"],
                "risk_score": member["risk_score"],
                "network_tier": member["network_tier"],
                "enrolled_flag": enrolled,
            })
        
        # Move to next month
        if current_month.month == 12:
            current_month = date(current_month.year + 1, 1, 1)
        else:
            current_month = date(current_month.year, current_month.month + 1, 1)
    
    return pd.DataFrame(records)


def generate_provider_directory(count: int) -> pd.DataFrame:
    """Generate comprehensive provider directory"""
    providers = []
    
    for i in range(count):
        specialty = np.random.choice(list(PROVIDER_SPECIALTIES.keys()))
        market = np.random.choice(MARKETS)
        provider_type = "FACILITY" if np.random.random() > 0.6 else "PHYSICIAN"
        
        # NPI (10 digits)
        npi = f"{np.random.randint(1000000000, 9999999999)}"
        
        # System affiliation (clusters behavior)
        has_system = np.random.random() > 0.4
        system_affiliation = f"System_{np.random.randint(1, 10)}" if has_system else None
        
        # Network status
        network_status = "IN" if np.random.random() > 0.2 else "OUT"
        
        specialty_info = PROVIDER_SPECIALTIES[specialty]
        facility_type = specialty_info["facility_type"]
        
        providers.append({
            "provider_id": f"PROV_{i:08d}",
            "npi": npi,
            "provider_type": provider_type,
            "specialty": specialty,
            "facility_type": facility_type,
            "market": market,
            "network_status": network_status,
            "system_affiliation": system_affiliation,
        })
    
    return pd.DataFrame(providers)


def apply_behavioral_patterns(
    claim_date: date,
    service_category: str,
    pos_code: str,
    member_lob: str,
    member_market: str,
    policy_id: Optional[str],
    policies_active: Dict[str, Any],
) -> Dict[str, float]:
    """
    Apply behavioral patterns based on active policies
    Returns multipliers for volume and cost
    """
    volume_mult = 1.0
    cost_mult = 1.0
    
    for pol_id, policy in policies_active.items():
        if claim_date < datetime.strptime(policy["effective_date"], "%Y-%m-%d").date():
            continue
        
        # Pattern 1: Prior Auth Backfire
        if pol_id == "PA_MRI_OP_001":
            if service_category == "MRI" and pos_code in policy.get("affected_pos", []):
                if member_market in policy["scope"].get("markets", []) or "ALL" in policy["scope"].get("markets", []):
                    if member_lob in policy["scope"].get("lob", []):
                        volume_mult *= 0.7  # 30% reduction
            elif service_category == "ER_IMAGING":
                # Substitution effect
                volume_mult *= 1.4  # 40% increase
                cost_mult *= 1.2  # Higher cost in ER
        
        # Pattern 2: Site-of-Care Success
        elif pol_id == "SOC_INFUSION_002":
            if service_category == "INFUSION":
                if pos_code == "22":  # Hospital OP
                    volume_mult *= 0.6  # Shift away
                elif pos_code == "19":  # Freestanding
                    volume_mult *= 1.5  # Shift to
                    cost_mult *= 0.7  # Cheaper
        
        # Pattern 3: Frequency Limit Substitution
        elif pol_id == "PT_FREQ_003":
            if service_category == "PT":
                # After limit, members shift to imaging
                if claim_date >= datetime.strptime(policy["effective_date"], "%Y-%m-%d").date() + timedelta(days=60):
                    volume_mult *= 0.3  # Strong reduction
            elif service_category == "MRI" and pos_code == "11":
                # Substitution after PT limit
                if claim_date >= datetime.strptime(policy["effective_date"], "%Y-%m-%d").date() + timedelta(days=60):
                    volume_mult *= 1.3
        
        # Pattern 4: Cost Sharing Spillover
        elif pol_id == "CS_UCC_004":
            if service_category == "URGENT_CARE":
                volume_mult *= 0.8  # Decrease UC visits
            elif service_category == "ER_VISIT":
                # Spillover to ER
                volume_mult *= 1.3  # Increase ER visits
                cost_mult *= 1.15
        
        # Pattern 5: Provider Circumvention
        elif pol_id == "COMPOUND_IMG_005":
            if service_category in ["MRI", "CT"]:
                # Some providers shift coding or sites
                if np.random.random() < 0.2:  # 20% circumvention
                    if pos_code == "11":
                        # Shift to hospital OP
                        pos_code = "22"
                        cost_mult *= 1.25
    
    return {"volume_mult": volume_mult, "cost_mult": cost_mult, "adjusted_pos": pos_code}


def generate_claims_lines(
    members_df: pd.DataFrame,
    providers_df: pd.DataFrame,
    start_date: date,
    end_date: date,
    tenant_id: str,
) -> pd.DataFrame:
    """Generate comprehensive claims lines with behavioral patterns"""
    claims = []
    
    # Build lookup structures
    members_by_lob_market = {}
    for _, member in members_df.iterrows():
        key = (member["lob"], member["market"])
        if key not in members_by_lob_market:
            members_by_lob_market[key] = []
        members_by_lob_market[key].append(member.to_dict())
    
    providers_by_market_specialty = {}
    for _, provider in providers_df.iterrows():
        key = (provider["market"], provider["specialty"])
        if key not in providers_by_market_specialty:
            providers_by_market_specialty[key] = []
        providers_by_market_specialty[key].append(provider.to_dict())
    
    # Build policy lookup
    policies_active = {p["policy_id"]: p for p in POLICIES_DATA}
    
    # Generate claims month by month
    current_date = start_date
    while current_date <= end_date:
        # Claims per month varies (seasonality)
        base_claims = 50000
        seasonality = 1.0 + 0.2 * np.sin(2 * np.pi * current_date.month / 12)  # Winter peak
        claims_per_month = int(base_claims * seasonality * np.random.uniform(0.8, 1.2))
        
        for _ in range(claims_per_month):
            # Select member
            lob = np.random.choice(LOBS)
            market = np.random.choice(MARKETS)
            key = (lob, market)
            
            if key not in members_by_lob_market or not members_by_lob_market[key]:
                continue
            
            member = np.random.choice(members_by_lob_market[key])
            
            # Select service category
            service_category = np.random.choice(list(SERVICE_CATEGORIES.keys()))
            service_info = SERVICE_CATEGORIES[service_category]
            
            # Select provider by specialty
            matching_specialties = [s for s, info in PROVIDER_SPECIALTIES.items() 
                                   if service_category in info["codes"]]
            if not matching_specialties:
                continue
            
            specialty = np.random.choice(matching_specialties)
            provider_key = (market, specialty)
            
            if provider_key not in providers_by_market_specialty or not providers_by_market_specialty[provider_key]:
                continue
            
            provider = np.random.choice(providers_by_market_specialty[provider_key])
            
            # Select code and POS
            code = np.random.choice(service_info["codes"])
            pos_code = np.random.choice(service_info["pos_codes"])
            
            # Check which policies apply
            applicable_policy = None
            for pol_id, policy in policies_active.items():
                if code in policy.get("affected_codes", []):
                    if member["market"] in policy["scope"].get("markets", []) or "ALL" in policy["scope"].get("markets", []):
                        if member["lob"] in policy["scope"].get("lob", []):
                            applicable_policy = pol_id
                            break
            
            # Apply behavioral patterns
            patterns = apply_behavioral_patterns(
                current_date,
                service_category,
                pos_code,
                member["lob"],
                member["market"],
                applicable_policy,
                policies_active,
            )
            
            pos_code = patterns.get("adjusted_pos", pos_code)
            volume_mult = patterns["volume_mult"]
            cost_mult = patterns["cost_mult"]
            
            # Skip claim if volume multiplier makes it unlikely
            if np.random.random() > volume_mult:
                continue
            
            # Calculate allowed amount
            if pos_code == "23" and "er_allowed_range" in service_info:
                base_allowed = np.random.uniform(*service_info["er_allowed_range"])
            elif pos_code == "19" and "freestanding_allowed_range" in service_info:
                base_allowed = np.random.uniform(*service_info["freestanding_allowed_range"])
            else:
                base_allowed = np.random.uniform(*service_info["base_allowed_range"])
            
            allowed_amount = base_allowed * cost_mult * np.random.uniform(0.9, 1.1)
            paid_amount = allowed_amount * np.random.uniform(0.85, 0.95)  # Payer pays 85-95%
            
            # Service date
            service_date = current_date + timedelta(days=np.random.randint(0, 28))
            paid_date = service_date + timedelta(days=np.random.randint(30, 60))
            
            # Units
            units = np.random.uniform(0.5, 2.0) * volume_mult
            
            claims.append({
                "tenant_id": tenant_id,
                "claim_id": f"CLM_{uuid4().hex[:12].upper()}",
                "claim_line_id": f"CLM_{uuid4().hex[:16].upper()}",
                "member_id": member["member_id"],
                "provider_id": provider["provider_id"],
                "service_date": service_date.strftime("%Y-%m-%d"),
                "paid_date": paid_date.strftime("%Y-%m-%d"),
                "lob": member["lob"],
                "market": member["market"],
                "cpt_code": code,
                "service_category": service_category,
                "place_of_service": pos_code,
                "units": round(units, 2),
                "allowed_amount": round(allowed_amount, 2),
                "paid_amount": round(paid_amount, 2),
                "in_network": provider["network_status"] == "IN",
            })
        
        # Move to next month
        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, 1)
        else:
            current_date = date(current_date.year, current_date.month + 1, 1)
    
    return pd.DataFrame(claims)


def generate_policy_events(start_date: date, num_months: int) -> pd.DataFrame:
    """Generate policy event timeline"""
    events = []
    
    for policy in POLICIES_DATA:
        effective_date = datetime.strptime(policy["effective_date"], "%Y-%m-%d").date()
        
        # Activation event
        events.append({
            "policy_id": policy["policy_id"],
            "event_type": "ACTIVATED",
            "event_date": effective_date.strftime("%Y-%m-%d"),
            "change_description": f"Policy {policy['policy_name']} activated",
        })
        
        # Some policies get modified
        if np.random.random() < 0.3:  # 30% get modified
            mod_date = effective_date + timedelta(days=np.random.randint(90, 270))
            events.append({
                "policy_id": policy["policy_id"],
                "event_type": "MODIFIED",
                "event_date": mod_date.strftime("%Y-%m-%d"),
                "change_description": f"Policy {policy['policy_name']} modified",
            })
    
    return pd.DataFrame(events)


def generate_benefit_design() -> pd.DataFrame:
    """Generate benefit design/cost sharing dataset"""
    benefits = []
    
    service_categories = ["ER", "URGENT_CARE", "OFFICE", "IMAGING", "INFUSION", "PT", "LAB"]
    
    for lob in LOBS:
        for service_cat in service_categories:
            if lob == "COMMERCIAL":
                copay = np.random.uniform(20, 100)
                coinsurance = np.random.uniform(0.1, 0.3)
            elif lob == "MA":
                copay = np.random.uniform(0, 50)
                coinsurance = np.random.uniform(0.0, 0.2)
            else:  # MEDICAID
                copay = np.random.uniform(0, 10)
                coinsurance = 0.0
            
            benefits.append({
                "lob": lob,
                "service_category": service_cat,
                "copay": round(copay, 2),
                "coinsurance": round(coinsurance, 3),
                "effective_date": "2023-01-01",
            })
    
    return pd.DataFrame(benefits)


def generate_ground_truth() -> Dict[str, Any]:
    """Generate ground truth expected outcomes"""
    return {
        "PA_MRI_OP_001": {
            "expected_effects": {
                "target_utilization": "DECREASE",
                "substitution": ["ER_IMAGING"],
                "net_cost": "INCREASE",
                "confidence": "HIGH",
            }
        },
        "SOC_INFUSION_002": {
            "expected_effects": {
                "target_utilization": "STABLE",
                "site_shift": "FREESTANDING",
                "net_cost": "DECREASE",
                "confidence": "HIGH",
            }
        },
        "PT_FREQ_003": {
            "expected_effects": {
                "target_utilization": "CAPPED",
                "substitution": ["MRI", "ORTHOPEDICS"],
                "net_cost": "MIXED",
                "confidence": "MEDIUM",
            }
        },
        "CS_UCC_004": {
            "expected_effects": {
                "target_utilization": "DECREASE",
                "substitution": ["ER_VISIT"],
                "net_cost": "INCREASE",
                "confidence": "HIGH",
            }
        },
        "COMPOUND_IMG_005": {
            "expected_effects": {
                "target_utilization": "STRONG_DECREASE",
                "substitution_risk": "HIGH",
                "net_cost": "DECREASE",
                "confidence": "MEDIUM",
            }
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Generate comprehensive synthetic healthcare datasets")
    parser.add_argument("--out", type=str, default="data/synthetic", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--members", type=int, default=100000, help="Number of members")
    parser.add_argument("--providers", type=int, default=10000, help="Number of providers")
    parser.add_argument("--months", type=int, default=36, help="Number of months of data")
    parser.add_argument("--start-date", type=str, default="2023-01-01", help="Start date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    # Set seed
    np.random.seed(args.seed)
    
    # Create output directory
    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)
    
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = start_date + timedelta(days=args.months * 30)
    tenant_id = "00000000-0000-0000-0000-000000000001"
    
    print(f"Generating synthetic datasets (seed={args.seed})...")
    print(f"Members: {args.members}, Providers: {args.providers}, Months: {args.months}")
    print(f"Date range: {start_date} to {end_date}")
    print()
    
    # 1. Member Enrollment
    print("1. Generating member enrollment...")
    enrollment_df = generate_member_enrollment(args.members, start_date, args.months)
    enrollment_df.to_parquet(out_path / "enrollment_monthly.parquet", index=False)
    enrollment_df.to_csv(out_path / "enrollment_monthly.csv", index=False)
    print(f"   ✅ Generated {len(enrollment_df):,} enrollment records")
    
    # 2. Provider Directory
    print("2. Generating provider directory...")
    providers_df = generate_provider_directory(args.providers)
    providers_df.to_parquet(out_path / "providers.parquet", index=False)
    providers_df.to_csv(out_path / "providers.csv", index=False)
    print(f"   ✅ Generated {len(providers_df):,} providers")
    
    # 3. Claims Lines
    print("3. Generating claims lines (this may take a while)...")
    claims_df = generate_claims_lines(enrollment_df, providers_df, start_date, end_date, tenant_id)
    
    # Write claims partitioned by year/month
    for year in range(start_date.year, end_date.year + 1):
        year_dir = out_path / "claims" / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)
        
        for month in range(1, 13):
            if year == start_date.year and month < start_date.month:
                continue
            if year == end_date.year and month > end_date.month:
                continue
            
            month_df = claims_df[
                (pd.to_datetime(claims_df["service_date"]).dt.year == year) &
                (pd.to_datetime(claims_df["service_date"]).dt.month == month)
            ]
            
            if len(month_df) > 0:
                month_df.to_parquet(year_dir / f"claims_{year}_{month:02d}.parquet", index=False)
    
    # Also write single file for smaller datasets
    if len(claims_df) < 5_000_000:
        claims_df.to_parquet(out_path / "claims_lines.parquet", index=False)
        claims_df.to_csv(out_path / "claims_lines_sample.csv", index=False, nrows=100000)
    
    print(f"   ✅ Generated {len(claims_df):,} claim lines")
    
    # 4. Policy Metadata
    print("4. Generating policy metadata...")
    with open(out_path / "policies.json", "w") as f:
        json.dump(POLICIES_DATA, f, indent=2)
    print(f"   ✅ Generated {len(POLICIES_DATA)} policies")
    
    # 5. Policy Events
    print("5. Generating policy events...")
    policy_events_df = generate_policy_events(start_date, args.months)
    policy_events_df.to_parquet(out_path / "policy_events.parquet", index=False)
    policy_events_df.to_csv(out_path / "policy_events.csv", index=False)
    print(f"   ✅ Generated {len(policy_events_df)} policy events")
    
    # 6. Benefit Design
    print("6. Generating benefit design...")
    benefits_df = generate_benefit_design()
    benefits_df.to_parquet(out_path / "benefit_design.parquet", index=False)
    benefits_df.to_csv(out_path / "benefit_design.csv", index=False)
    print(f"   ✅ Generated {len(benefits_df)} benefit design records")
    
    # 7. Ground Truth
    print("7. Generating ground truth...")
    ground_truth = generate_ground_truth()
    with open(out_path / "expected_outcomes.json", "w") as f:
        json.dump(ground_truth, f, indent=2)
    print(f"   ✅ Generated ground truth for {len(ground_truth)} policies")
    
    print()
    print("✅ All datasets generated successfully!")
    print(f"📁 Output directory: {out_path.absolute()}")
    print()
    print("Generated files:")
    print("  - enrollment_monthly.parquet / .csv")
    print("  - providers.parquet / .csv")
    print("  - claims/YYYY/claims_YYYY_MM.parquet (partitioned)")
    print("  - policies.json")
    print("  - policy_events.parquet / .csv")
    print("  - benefit_design.parquet / .csv")
    print("  - expected_outcomes.json")


if __name__ == "__main__":
    main()

