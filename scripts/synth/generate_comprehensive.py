"""
Comprehensive Synthetic Healthcare Data Generator
Enterprise-grade, deterministic, with realistic behavioral patterns
"""
from __future__ import annotations

import argparse
import json
import numpy as np
import pandas as pd
import polars as pl
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from uuid import UUID
import hashlib

# Fixed seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# ============================================================================
# CONFIGURATION - Markets, LOBs, Service Categories
# ============================================================================

MARKETS = ["NYC", "DFW", "BOS"]
LOBS = ["COMMERCIAL", "MA", "MEDICAID"]
AGE_BANDS = ["0-17", "18-34", "35-49", "50-64", "65+"]
GENDERS = ["M", "F", "U"]

# Comprehensive service categories with realistic codes
SERVICE_CATEGORIES = {
    "MRI": {
        "codes": ["72141", "72142", "72146", "72148", "72149", "72158"],  # Lumbar, Cervical MRI
        "pos_codes": ["11", "22"],  # Office, Outpatient Hospital
        "base_allowed_range": (800, 2500),
        "er_allowed_range": (1200, 3500),  # ER is more expensive
    },
    "CT": {
        "codes": ["70450", "70460", "70470", "71250", "72125"],  # CT Head, Chest, Abdomen, Chest w/ contrast
        "pos_codes": ["11", "22", "23"],  # Office, Hospital OP, ER
        "base_allowed_range": (400, 1200),
        "er_allowed_range": (800, 2000),
    },
    "ER_IMAGING": {
        "codes": ["70450", "70460", "72141", "70470"],  # CT/MRI in ER
        "pos_codes": ["23"],  # Emergency Room
        "base_allowed_range": (1000, 3500),
        "er_allowed_range": (1000, 3500),
    },
    "INFUSION": {
        "codes": ["96413", "96415", "96417", "96416"],  # Chemotherapy, infusion services
        "pos_codes": ["22", "19", "11"],  # Hospital OP, Off Campus, Office
        "base_allowed_range": (500, 2000),
        "freestanding_allowed_range": (300, 1200),  # Freestanding is cheaper
    },
    "PT": {
        "codes": ["97110", "97112", "97140", "97116"],  # Physical therapy, therapeutic exercises
        "pos_codes": ["11", "12"],  # Office, Home
        "base_allowed_range": (80, 200),
        "base_allowed_range_office": (80, 200),
    },
    "SPECIALTY_VISIT": {
        "codes": ["99213", "99214", "99215", "99242", "99243", "99244"],  # Office visits, consults
        "pos_codes": ["11"],
        "base_allowed_range": (150, 400),
    },
    "URGENT_CARE": {
        "codes": ["99281", "99282", "99283"],  # ER visits (level 1-3)
        "pos_codes": ["20"],  # Urgent Care
        "base_allowed_range": (200, 600),
    },
    "ER_VISIT": {
        "codes": ["99284", "99285"],  # ER visits (level 4-5)
        "pos_codes": ["23"],  # Emergency Room
        "base_allowed_range": (800, 2500),
    },
    "IMAGING_ADVANCED": {
        "codes": ["70551", "70552", "70553"],  # Advanced imaging (brain MRI w/wo contrast)
        "pos_codes": ["11", "22"],
        "base_allowed_range": (1500, 4000),
        "er_allowed_range": (2000, 5000),
    },
}

PROVIDER_SPECIALTIES = {
    "RADIOLOGY": {"codes": ["MRI", "CT", "ER_IMAGING", "IMAGING_ADVANCED"], "facility_type": "FREESTANDING"},
    "ONCOLOGY": {"codes": ["INFUSION", "SPECIALTY_VISIT"], "facility_type": "HOSPITAL_OP"},
    "PHYSICAL_THERAPY": {"codes": ["PT"], "facility_type": "OFFICE"},
    "PRIMARY_CARE": {"codes": ["SPECIALTY_VISIT"], "facility_type": "OFFICE"},
    "EMERGENCY": {"codes": ["ER_VISIT", "ER_IMAGING", "URGENT_CARE"], "facility_type": "ER"},
    "ORTHOPEDICS": {"codes": ["SPECIALTY_VISIT", "PT", "MRI"], "facility_type": "OFFICE"},
}

FACILITY_TYPES = {
    "11": "OFFICE",
    "12": "HOME",
    "19": "FREESTANDING",  # Off campus outpatient
    "20": "URGENT_CARE",
    "22": "HOSPITAL_OP",
    "23": "ER",
}

# ============================================================================
# VOLUME TIERS
# ============================================================================

VOLUME_TIERS = {
    "dev": {"members": 5000, "providers": 500, "claims_per_month_ratio": 0.04},  # 200k claims
    "demo": {"members": 50000, "providers": 5000, "claims_per_month_ratio": 0.4},  # 2M claims
    "pilot": {"members": 150000, "providers": 15000, "claims_per_month_ratio": 1.0},  # 8M claims
}


# ============================================================================
# MEMBER / ENROLLMENT DATASET (Monthly Snapshots)
# ============================================================================

def generate_enrollment_monthly(
    member_count: int,
    lobs: list[str],
    markets: list[str],
    start_date: datetime,
    months: int,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Generate monthly enrollment snapshots - deterministic"""
    np.random.seed(seed)
    
    enrollment_records = []
    member_ids = [f"MEM_{i:08d}" for i in range(member_count)]
    
    for month_offset in range(months):
        current_date = start_date + timedelta(days=30 * month_offset)
        enrollment_month = current_date.strftime("%Y-%m")
        
        # Generate enrollment for this month
        # Members can enroll/disenroll (realistic churn)
        enrolled_members = int(member_count * np.random.uniform(0.95, 1.0))  # 95-100% enrolled
        
        # Deterministic selection based on month and seed
        np.random.seed(seed + month_offset)
        selected_indices = np.random.choice(len(member_ids), enrolled_members, replace=False)
        
        for idx in selected_indices:
            member_id = member_ids[idx]
            
            # Deterministic attributes based on member_id hash
            member_hash = int(hashlib.md5(member_id.encode()).hexdigest(), 16) % (10**10)
            np.random.seed(member_hash)
            
            lob = np.random.choice(lobs)
            market = np.random.choice(markets)
            gender = np.random.choice(GENDERS + [None], p=[0.45, 0.45, 0.1])
            
            # Age distribution (realistic payer distribution)
            age_probs = [0.15, 0.20, 0.25, 0.25, 0.15]  # Skewed toward middle age
            age_band = np.random.choice(AGE_BANDS, p=age_probs)
            
            # Risk score (skewed right - few high-risk members)
            risk_score = np.random.beta(2, 5) * 2.5 + 0.5  # Beta distribution (0.5-3.0)
            
            # Network tier (most members in standard network)
            network_tier = np.random.choice(["STANDARD", "NARROW"], p=[0.8, 0.2])
            
            enrollment_records.append({
                "member_id": member_id,
                "lob": lob,
                "market": market,
                "enrollment_month": enrollment_month,
                "age_band": age_band,
                "gender": gender,
                "risk_score": round(risk_score, 3),
                "network_tier": network_tier,
                "enrolled_flag": True,
            })
        
        # Reset seed for next month
        np.random.seed(seed + month_offset + 1)
    
    return pd.DataFrame(enrollment_records)


# ============================================================================
# PROVIDER DIRECTORY DATASET
# ============================================================================

def generate_providers(
    provider_count: int,
    markets: list[str],
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Generate provider directory with system affiliations - deterministic"""
    np.random.seed(seed)
    
    providers = []
    specialties_list = list(PROVIDER_SPECIALTIES.keys())
    
    # Create system affiliations (clustered behavior)
    system_count = max(3, provider_count // 500)  # ~500 providers per system
    systems = [f"SYSTEM_{i:03d}" for i in range(1, system_count + 1)]
    
    for i in range(provider_count):
        # Deterministic NPI (9 digits)
        np.random.seed(seed + i)
        npi = f"{np.random.randint(100000000, 999999999)}"
        
        # Deterministic attributes
        specialty = np.random.choice(specialties_list)
        market = np.random.choice(markets)
        
        # System affiliation (clustered - some providers in systems)
        system_affiliation = None
        if np.random.random() < 0.6:  # 60% of providers in systems
            system_affiliation = np.random.choice(systems)
        
        # Provider type based on specialty
        specialty_info = PROVIDER_SPECIALTIES[specialty]
        facility_type = specialty_info.get("facility_type", "OFFICE")
        provider_type = "FACILITY" if facility_type in ["HOSPITAL_OP", "ER", "FREESTANDING"] else "PHYSICIAN"
        
        # Network status (most in-network)
        network_status = np.random.choice(["IN", "OUT"], p=[0.85, 0.15])
        
        # Provider name
        provider_name = f"{specialty.replace('_', ' ')} Provider {i+1}"
        if system_affiliation:
            provider_name = f"{system_affiliation} - {provider_name}"
        
        providers.append({
            "provider_id": f"PROV_{i:08d}",
            "npi": npi,
            "provider_type": provider_type,
            "specialty": specialty,
            "facility_type": facility_type,
            "market": market,
            "network_status": network_status,
            "system_affiliation": system_affiliation,
            "provider_name": provider_name,
        })
    
    return pd.DataFrame(providers)


# ============================================================================
# CLAIMS LINES DATASET (Most Important - with Behavioral Patterns)
# ============================================================================

def generate_claims_lines(
    enrollment_df: pd.DataFrame,
    providers_df: pd.DataFrame,
    start_date: datetime,
    months: int,
    tenant_id: str,
    policy_events: list[dict[str, Any]],
    benefit_design: pd.DataFrame,
    volume_tier: str = "demo",
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Generate claims lines with embedded behavioral patterns - deterministic"""
    np.random.seed(seed)
    
    claims = []
    
    # Calculate claims per month based on tier
    tier_config = VOLUME_TIERS[volume_tier]
    members_per_month = enrollment_df.groupby("enrollment_month").size().mean()
    claims_per_month = int(members_per_month * tier_config["claims_per_month_ratio"] * 12)  # Annual ratio
    
    # Build lookup structures
    members_by_month = {}
    for _, member in enrollment_df.iterrows():
        month = member["enrollment_month"]
        if month not in members_by_month:
            members_by_month[month] = []
        members_by_month[month].append(member.to_dict())
    
    providers_by_market_specialty = {}
    for _, provider in providers_df.iterrows():
        key = (provider["market"], provider["specialty"])
        if key not in providers_by_market_specialty:
            providers_by_market_specialty[key] = []
        providers_by_market_specialty[key].append(provider.to_dict())
    
    # Generate claims month by month
    for month_offset in range(months):
        current_date = start_date + timedelta(days=30 * month_offset)
        enrollment_month = current_date.strftime("%Y-%m")
        
        if enrollment_month not in members_by_month:
            continue
        
        members_this_month = members_by_month[enrollment_month]
        claims_this_month = int(claims_per_month * np.random.uniform(0.9, 1.1))  # ±10% variation
        
        # Apply seasonality (higher in winter months)
        month_num = current_date.month
        seasonality_factor = 1.0 + 0.15 * np.sin((month_num - 1) * np.pi / 6)  # Peak in Jan/Feb
        claims_this_month = int(claims_this_month * seasonality_factor)
        
        np.random.seed(seed + month_offset * 10000)
        
        for claim_idx in range(claims_this_month):
            # Select member (deterministic)
            member = np.random.choice(members_this_month)
            market = member["market"]
            lob = member["lob"]
            
            # Select service category (weighted by prevalence)
            category_weights = {
                "SPECIALTY_VISIT": 0.30,
                "PT": 0.15,
                "MRI": 0.10,
                "CT": 0.12,
                "INFUSION": 0.08,
                "ER_IMAGING": 0.08,
                "URGENT_CARE": 0.10,
                "ER_VISIT": 0.05,
                "IMAGING_ADVANCED": 0.02,
            }
            categories = list(category_weights.keys())
            weights = list(category_weights.values())
            category = np.random.choice(categories, p=weights)
            
            service_info = SERVICE_CATEGORIES[category]
            code = np.random.choice(service_info["codes"])
            pos_code = np.random.choice(service_info["pos_codes"])
            
            # Select provider (matching specialty and market)
            # Find providers that can perform this service
            matching_specialties = [
                spec for spec, info in PROVIDER_SPECIALTIES.items()
                if category in info["codes"]
            ]
            
            if not matching_specialties:
                matching_specialties = ["PRIMARY_CARE"]  # Fallback
            
            provider = None
            for specialty in matching_specialties:
                key = (market, specialty)
                if key in providers_by_market_specialty and providers_by_market_specialty[key]:
                    provider = np.random.choice(providers_by_market_specialty[key])
                    break
            
            if not provider:
                continue  # Skip if no matching provider
            
            # ================================================================
            # APPLY POLICY EFFECTS (Behavioral Patterns)
            # ================================================================
            
            base_volume_multiplier = 1.0
            base_cost_multiplier = 1.0
            substitution_effect = False
            provider_circumvention = False
            
            # Check active policies for this date
            active_policies = [
                pe for pe in policy_events
                if pe["event_type"] in ["ACTIVATED", "MODIFIED"]
                and datetime.strptime(pe["event_date"], "%Y-%m-%d") <= current_date
            ]
            
            for policy_event in active_policies:
                policy_id = policy_event["policy_id"]
                policy_type = policy_event.get("policy_type", "")
                
                # Pattern 1: Prior Auth Backfire (MRI PA → ER imaging increases)
                if policy_id == "PA_MRI_OP_001" and category == "MRI" and pos_code == "11":
                    # Target MRI volume decreases
                    base_volume_multiplier *= 0.65  # 35% reduction
                    # But ER imaging increases (substitution effect)
                    substitution_effect = True
                elif policy_id == "PA_MRI_OP_001" and category == "ER_IMAGING":
                    # ER imaging increases due to substitution
                    if substitution_effect:
                        base_volume_multiplier *= 1.45  # 45% increase
                        base_cost_multiplier *= 1.3  # ER is more expensive
                
                # Pattern 2: Site-of-Care Success (Infusion redirect)
                elif policy_id == "SOC_INFUSION_002" and category == "INFUSION":
                    if pos_code == "22":  # Hospital OP
                        base_volume_multiplier *= 0.55  # 45% reduction
                    elif pos_code == "19":  # Freestanding
                        base_volume_multiplier *= 1.55  # 55% increase
                        base_cost_multiplier *= 0.7  # Freestanding is cheaper
                
                # Pattern 3: Frequency Limit Substitution (PT cap → imaging increases)
                elif policy_id == "PT_FREQ_003" and category == "PT":
                    # Check if member has exceeded limit (simplified - 20 visits/year)
                    # For realism, some members hit limit
                    if np.random.random() < 0.3:  # 30% hit limit
                        base_volume_multiplier *= 0.1  # 90% reduction after limit
                    else:
                        base_volume_multiplier *= 0.95  # Slight reduction
                elif policy_id == "PT_FREQ_003" and category in ["MRI", "IMAGING_ADVANCED"]:
                    # Imaging increases 60-90 days after PT limit
                    days_since_policy = (current_date - datetime.strptime(policy_event["event_date"], "%Y-%m-%d")).days
                    if 60 <= days_since_policy <= 90:
                        base_volume_multiplier *= 1.25  # 25% increase (deferred care)
                
                # Pattern 4: Cost Sharing Spillover (UC copay ↑ → ER ↑)
                elif policy_id == "CS_UCC_004" and category == "URGENT_CARE":
                    base_volume_multiplier *= 0.68  # 32% reduction (copay increase)
                elif policy_id == "CS_UCC_004" and category == "ER_VISIT":
                    base_volume_multiplier *= 1.35  # 35% increase (spillover to ER)
                
                # Pattern 5: Compound Policy (Advanced Imaging Bundle)
                elif policy_id == "COMPOUND_IMG_005" and category == "IMAGING_ADVANCED":
                    # Both PA and frequency limit apply
                    base_volume_multiplier *= 0.50  # 50% reduction (strong effect)
                    # Provider circumvention - coding shifts
                    if np.random.random() < 0.15:  # 15% circumvention rate
                        provider_circumvention = True
                        # Shift to similar codes not covered
                        code = np.random.choice(["70450", "70460"])  # CT instead of MRI
                        category = "CT"
            
            # ================================================================
            # PROVIDER ADAPTATION PATTERNS
            # ================================================================
            
            # System-affiliated providers adapt together (clustered behavior)
            if provider.get("system_affiliation") and provider_circumvention:
                # System providers shift coding patterns together
                if category in ["MRI", "IMAGING_ADVANCED"]:
                    # Some systems shift to alternative codes
                    if np.random.random() < 0.25:  # 25% of system providers adapt
                        code = np.random.choice(["70450", "70460", "72125"])  # CT codes
                        category = "CT"
            
            # ================================================================
            # COST SHARING EFFECTS (from benefit_design)
            # ================================================================
            
            # Apply cost-sharing effects if benefit design exists
            if not benefit_design.empty:
                matching_benefit = benefit_design[
                    (benefit_design["lob"] == lob) &
                    (benefit_design["service_category"] == category) &
                    (benefit_design["effective_date"] <= current_date.strftime("%Y-%m-%d"))
                ]
                
                if not matching_benefit.empty:
                    benefit = matching_benefit.iloc[-1]  # Most recent
                    copay = benefit.get("copay", 0)
                    coinsurance = benefit.get("coinsurance", 0)
                    
                    # Higher cost-sharing reduces utilization
                    if copay > 50 or coinsurance > 0.2:
                        base_volume_multiplier *= 0.85  # 15% reduction
            
            # ================================================================
            # GENERATE CLAIM WITH REALISTIC DISTRIBUTIONS
            # ================================================================
            
            # Service dates (within month)
            day_in_month = np.random.randint(1, 28)
            service_from_date = current_date + timedelta(days=day_in_month)
            service_to_date = service_from_date + timedelta(days=np.random.choice([0, 1, 2, 7], p=[0.3, 0.4, 0.2, 0.1]))
            paid_date = service_to_date + timedelta(days=np.random.randint(30, 90))
            
            # Allowed amount (varies by site of care)
            if pos_code == "23":  # ER
                allowed_range = service_info.get("er_allowed_range", service_info["base_allowed_range"])
            elif pos_code == "19":  # Freestanding
                allowed_range = service_info.get("freestanding_allowed_range", service_info["base_allowed_range"])
            else:
                allowed_range = service_info["base_allowed_range"]
            
            base_allowed = np.random.uniform(allowed_range[0], allowed_range[1])
            allowed_amount = base_allowed * base_cost_multiplier
            
            # Units (varies by service type)
            if category == "PT":
                units = np.random.choice([1.0, 2.0, 3.0], p=[0.4, 0.4, 0.2]) * base_volume_multiplier
            elif category == "INFUSION":
                units = np.random.uniform(0.5, 2.0) * base_volume_multiplier
            else:
                units = 1.0 * base_volume_multiplier
            
            # Paid amount (typically 80-95% of allowed)
            paid_amount = allowed_amount * np.random.uniform(0.80, 0.95)
            
            # In-network flag (deterministic based on provider)
            in_network = provider.get("network_status") == "IN"
            
            # Generate claim ID (deterministic)
            claim_hash = int(hashlib.md5(
                f"{member['member_id']}{current_date.strftime('%Y%m%d')}{claim_idx}{seed}".encode()
            ).hexdigest(), 16) % (10**12)
            claim_id = f"CLM_{claim_hash:012d}"
            claim_line_id = f"{claim_id}_L{claim_idx % 10}"
            
            # Service category (for analytics)
            service_category = category
            
            claims.append({
                "tenant_id": tenant_id,
                "member_id": member["member_id"],
                "claim_id": claim_id,
                "claim_line_id": claim_line_id,
                "service_date": service_from_date.strftime("%Y-%m-%d"),
                "service_from_date": service_from_date.strftime("%Y-%m-%d"),
                "service_to_date": service_to_date.strftime("%Y-%m-%d"),
                "paid_date": paid_date.strftime("%Y-%m-%d"),
                "lob": lob,
                "market": market,
                "cpt_code": code,
                "cpt_hcpcs": code,  # Alias for compatibility
                "service_category": service_category,
                "place_of_service": pos_code,
                "pos_code": pos_code,  # Alias
                "units": round(float(units), 2),
                "allowed_amount": round(float(allowed_amount), 2),
                "paid_amount": round(float(paid_amount), 2),
                "in_network": in_network,
                "in_network_flag": in_network,  # Alias
                "rendering_npi": provider["npi"],
                "billing_npi": provider["npi"] if np.random.random() > 0.3 else None,
                "modifier_1": np.random.choice([None, "26", "TC", "59", "LT", "RT"], p=[0.7, 0.1, 0.05, 0.05, 0.05, 0.05]) if np.random.random() > 0.7 else None,
                "diag_1": f"M{np.random.randint(10, 99)}.{np.random.randint(0, 9)}" if np.random.random() > 0.5 else None,
                "drg": f"DRG{np.random.randint(100, 999)}" if category == "ER_VISIT" and np.random.random() > 0.7 else None,
            })
    
    return pd.DataFrame(claims)


# ============================================================================
# POLICY EVENTS DATASET (Critical for Pre/Post Analysis)
# ============================================================================

def generate_policy_events(
    start_date: datetime,
    months: int,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Generate policy events (activation, modification, retirement) - deterministic"""
    np.random.seed(seed)
    
    # Use canonical policies from earlier
    canonical_policies = [
        {
            "policy_id": "10000000-0000-0000-0000-000000000001",
            "policy_name": "Outpatient MRI Prior Authorization",
            "policy_type": "PRIOR_AUTH",
            "event_date": (start_date + timedelta(days=180)).strftime("%Y-%m-%d"),  # 6 months in
            "event_type": "ACTIVATED",
            "change_description": "Require PA for outpatient MRI",
        },
        {
            "policy_id": "10000000-0000-0000-0000-000000000002",
            "policy_name": "Infusion Site-of-Care Optimization",
            "policy_type": "SITE_OF_CARE",
            "event_date": (start_date + timedelta(days=210)).strftime("%Y-%m-%d"),  # 7 months
            "event_type": "ACTIVATED",
            "change_description": "Redirect infusion to freestanding centers",
        },
        {
            "policy_id": "10000000-0000-0000-0000-000000000003",
            "policy_name": "Physical Therapy Visit Limit",
            "policy_type": "DURATION_FREQUENCY_LIMIT",
            "event_date": (start_date + timedelta(days=365)).strftime("%Y-%m-%d"),  # 12 months
            "event_type": "ACTIVATED",
            "change_description": "Limit PT to 20 visits/year",
        },
        {
            "policy_id": "10000000-0000-0000-0000-000000000004",
            "policy_name": "Urgent Care Copay Increase",
            "policy_type": "COST_SHARING",
            "event_date": (start_date + timedelta(days=120)).strftime("%Y-%m-%d"),  # 4 months
            "event_type": "ACTIVATED",
            "change_description": "Increase UC copay from $40 to $75",
        },
        {
            "policy_id": "10000000-0000-0000-0000-000000000005",
            "policy_name": "Advanced Imaging Control Bundle",
            "policy_type": "COMPOSITE",
            "event_date": (start_date + timedelta(days=270)).strftime("%Y-%m-%d"),  # 9 months
            "event_type": "ACTIVATED",
            "change_description": "PA + frequency limit for advanced imaging",
        },
    ]
    
    events = []
    for policy in canonical_policies:
        events.append({
            "policy_id": policy["policy_id"],
            "event_type": policy["event_type"],
            "event_date": policy["event_date"],
            "change_description": policy["change_description"],
            "policy_name": policy["policy_name"],
            "policy_type": policy["policy_type"],
        })
        
        # Some policies get modified later
        if policy["policy_id"] == "10000000-0000-0000-0000-000000000004":
            # UC copay policy modified (tightened further)
            events.append({
                "policy_id": policy["policy_id"],
                "event_type": "MODIFIED",
                "event_date": (datetime.strptime(policy["event_date"], "%Y-%m-%d") + timedelta(days=180)).strftime("%Y-%m-%d"),
                "change_description": "Further increase UC copay to $100",
                "policy_name": policy["policy_name"],
                "policy_type": policy["policy_type"],
            })
    
    return pd.DataFrame(events)


# ============================================================================
# BENEFIT / COST SHARING DATASET
# ============================================================================

def generate_benefit_design(
    lobs: list[str],
    start_date: datetime,
    months: int,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Generate benefit design with cost-sharing changes - deterministic"""
    np.random.seed(seed)
    
    benefits = []
    service_categories_list = ["ER", "URGENT_CARE", "OFFICE", "IMAGING", "INFUSION"]
    
    for lob in lobs:
        for category in service_categories_list:
            # Base benefits
            if category == "ER":
                copay = 150.0
                coinsurance = 0.1  # 10%
            elif category == "URGENT_CARE":
                copay = 40.0
                coinsurance = 0.0
            elif category == "OFFICE":
                copay = 25.0
                coinsurance = 0.0
            elif category == "IMAGING":
                copay = 50.0
                coinsurance = 0.2  # 20%
            else:  # INFUSION
                copay = 0.0
                coinsurance = 0.2  # 20%
            
            benefits.append({
                "lob": lob,
                "service_category": category,
                "copay": copay,
                "coinsurance": coinsurance,
                "effective_date": start_date.strftime("%Y-%m-%d"),
            })
            
            # UC copay change (matches policy event)
            if category == "URGENT_CARE":
                benefits.append({
                    "lob": lob,
                    "service_category": category,
                    "copay": 75.0,  # Increased
                    "coinsurance": 0.0,
                    "effective_date": (start_date + timedelta(days=120)).strftime("%Y-%m-%d"),
                })
    
    return pd.DataFrame(benefits)


# ============================================================================
# GROUND TRUTH DATASET (For Validation)
# ============================================================================

def generate_ground_truth(
    policy_events: pd.DataFrame,
) -> dict[str, Any]:
    """Generate expected outcomes for validation"""
    ground_truth = {}
    
    for _, event in policy_events[policy_events["event_type"] == "ACTIVATED"].iterrows():
        policy_id = event["policy_id"]
        policy_type = event["policy_type"]
        
        expected_effects = {}
        
        if policy_id == "10000000-0000-0000-0000-000000000001":  # MRI PA
            expected_effects = {
                "target_utilization": "DECREASE",
                "target_utilization_magnitude": 0.35,  # 35% reduction
                "substitution": ["ER_IMAGING"],
                "substitution_magnitude": 0.45,  # 45% increase
                "net_cost": "INCREASE",  # ER is more expensive
                "lag_days": [30, 60, 90],
            }
        elif policy_id == "10000000-0000-0000-0000-000000000002":  # Infusion SOC
            expected_effects = {
                "target_utilization": "MIXED",  # Hospital OP down, freestanding up
                "target_utilization_magnitude": -0.45,  # Hospital OP 45% reduction
                "substitution": ["FREESTANDING_INFUSION"],
                "substitution_magnitude": 0.55,  # Freestanding 55% increase
                "net_cost": "DECREASE",  # Freestanding cheaper
                "lag_days": [0, 30],
            }
        elif policy_id == "10000000-0000-0000-0000-000000000003":  # PT limit
            expected_effects = {
                "target_utilization": "DECREASE",
                "target_utilization_magnitude": 0.30,  # After limit hits
                "substitution": ["ORTHOPEDIC_IMAGING"],
                "substitution_magnitude": 0.25,  # Deferred imaging
                "net_cost": "MIXED",
                "lag_days": [60, 90],
            }
        elif policy_id == "10000000-0000-0000-0000-000000000004":  # UC copay
            expected_effects = {
                "target_utilization": "DECREASE",
                "target_utilization_magnitude": 0.32,  # 32% reduction
                "substitution": ["ER_VISIT"],
                "substitution_magnitude": 0.35,  # ER increases
                "net_cost": "INCREASE",  # ER more expensive
                "lag_days": [0, 30],
            }
        elif policy_id == "10000000-0000-0000-0000-000000000005":  # Compound
            expected_effects = {
                "target_utilization": "DECREASE",
                "target_utilization_magnitude": 0.50,  # 50% reduction (strong)
                "substitution": ["ALTERNATE_IMAGING", "PROVIDER_CIRCUMVENTION"],
                "substitution_magnitude": 0.15,  # 15% circumvention
                "net_cost": "MIXED",
                "lag_days": [30, 60, 90],
            }
        
        if expected_effects:
            ground_truth[policy_id] = {
                "policy_name": event["policy_name"],
                "policy_type": policy_type,
                "expected_effects": expected_effects,
            }
    
    return ground_truth


# ============================================================================
# MAIN GENERATOR FUNCTION
# ============================================================================

def generate_comprehensive_datasets(
    output_dir: Path,
    volume_tier: str = "demo",
    start_date: datetime = datetime(2024, 1, 1),
    months: int = 24,
    tenant_id: str = "00000000-0000-0000-0000-000000000002",
    seed: int = RANDOM_SEED,
    format: str = "parquet",  # "parquet" or "csv"
) -> dict[str, Any]:
    """Generate all comprehensive datasets"""
    
    print(f"🎯 Generating {volume_tier.upper()} tier synthetic data...")
    print(f"   Seed: {seed} (deterministic)")
    print(f"   Period: {start_date.strftime('%Y-%m-%d')} to {(start_date + timedelta(days=30*months)).strftime('%Y-%m-%d')}")
    print("")
    
    tier_config = VOLUME_TIERS[volume_tier]
    member_count = tier_config["members"]
    provider_count = tier_config["providers"]
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Generate Enrollment (Monthly Snapshots)
    print("📊 Generating enrollment_monthly dataset...")
    enrollment_df = generate_enrollment_monthly(member_count, LOBS, MARKETS, start_date, months, seed)
    enrollment_path = output_dir / f"enrollment_monthly.{format}"
    if format == "parquet":
        enrollment_df.to_parquet(enrollment_path, index=False)
    else:
        enrollment_df.to_csv(enrollment_path, index=False)
    print(f"   ✅ Created: {enrollment_path} ({len(enrollment_df):,} records)")
    
    # 2. Generate Providers
    print("🏥 Generating providers dataset...")
    providers_df = generate_providers(provider_count, MARKETS, seed)
    providers_path = output_dir / f"providers.{format}"
    if format == "parquet":
        providers_df.to_parquet(providers_path, index=False)
    else:
        providers_df.to_csv(providers_path, index=False)
    print(f"   ✅ Created: {providers_path} ({len(providers_df):,} records)")
    
    # 3. Generate Policy Events
    print("📋 Generating policy_events dataset...")
    policy_events_df = generate_policy_events(start_date, months, seed)
    policy_events_list = policy_events_df.to_dict("records")
    policy_events_path = output_dir / f"policy_events.{format}"
    if format == "parquet":
        policy_events_df.to_parquet(policy_events_path, index=False)
    else:
        policy_events_df.to_csv(policy_events_path, index=False)
    print(f"   ✅ Created: {policy_events_path} ({len(policy_events_df):,} records)")
    
    # 4. Generate Benefit Design
    print("💰 Generating benefit_design dataset...")
    benefit_df = generate_benefit_design(LOBS, start_date, months, seed)
    benefit_path = output_dir / f"benefit_design.{format}"
    if format == "parquet":
        benefit_df.to_parquet(benefit_path, index=False)
    else:
        benefit_df.to_csv(benefit_path, index=False)
    print(f"   ✅ Created: {benefit_path} ({len(benefit_df):,} records)")
    
    # 5. Generate Claims Lines (Most Important - with Behavioral Patterns)
    print("💳 Generating claims_lines dataset (this may take a while)...")
    claims_df = generate_claims_lines(
        enrollment_df, providers_df, start_date, months,
        tenant_id, policy_events_list, benefit_df, volume_tier, seed
    )
    
    # Write claims by month (partitioned for realistic ingestion)
    claims_paths = []
    for year_month, group in claims_df.groupby(claims_df["service_date"].str[:7]):
        month_path = output_dir / f"claims_lines_{year_month.replace('-', '')}.{format}"
        if format == "parquet":
            group.to_parquet(month_path, index=False)
        else:
            group.to_csv(month_path, index=False)
        claims_paths.append(str(month_path))
    print(f"   ✅ Created: {len(claims_paths)} monthly claim files ({len(claims_df):,} total claims)")
    
    # 6. Generate Ground Truth
    print("✅ Generating ground_truth expected outcomes...")
    ground_truth = generate_ground_truth(policy_events_df)
    ground_truth_path = output_dir / "expected_outcomes.json"
    with open(ground_truth_path, "w") as f:
        json.dump(ground_truth, f, indent=2, default=str)
    print(f"   ✅ Created: {ground_truth_path} ({len(ground_truth)} policies)")
    
    # 7. Create Ingestion Manifest
    print("📦 Creating ingestion manifest...")
    manifest = {
        "tenant_id": tenant_id,
        "generated_at": datetime.utcnow().isoformat(),
        "volume_tier": volume_tier,
        "seed": seed,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "months": months,
        "files": [
            {"type": "enrollment", "uri": f"s3://bucket/{tenant_id}/raw/enrollment_monthly.{format}"},
            {"type": "providers", "uri": f"s3://bucket/{tenant_id}/raw/providers.{format}"},
            {"type": "claims_lines", "uri": f"s3://bucket/{tenant_id}/raw/claims_lines_{ym.replace('-', '')}.{format}"}
            for ym in claims_df["service_date"].str[:7].unique()
        ],
        "policy_events_uri": f"s3://bucket/{tenant_id}/raw/policy_events.{format}",
        "benefit_design_uri": f"s3://bucket/{tenant_id}/raw/benefit_design.{format}",
        "ground_truth_uri": f"s3://bucket/{tenant_id}/raw/expected_outcomes.json",
    }
    manifest_path = output_dir / "ingestion_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)
    print(f"   ✅ Created: {manifest_path}")
    
    # Summary
    summary = {
        "enrollment_records": len(enrollment_df),
        "provider_records": len(providers_df),
        "claims_records": len(claims_df),
        "policy_events": len(policy_events_df),
        "benefit_records": len(benefit_df),
        "claims_files": len(claims_paths),
        "unique_members": enrollment_df["member_id"].nunique(),
        "unique_providers": providers_df["provider_id"].nunique(),
        "date_range": {
            "start": claims_df["service_date"].min() if not claims_df.empty else None,
            "end": claims_df["service_date"].max() if not claims_df.empty else None,
        },
        "markets": claims_df["market"].nunique() if not claims_df.empty else 0,
        "lobs": claims_df["lob"].nunique() if not claims_df.empty else 0,
    }
    
    summary_path = output_dir / "generation_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    
    print("")
    print("=" * 60)
    print("✅ COMPREHENSIVE DATA GENERATION COMPLETE!")
    print("=" * 60)
    print(f"📊 Summary:")
    print(f"   Enrollment records: {summary['enrollment_records']:,}")
    print(f"   Unique members: {summary['unique_members']:,}")
    print(f"   Provider records: {summary['provider_records']:,}")
    print(f"   Claims records: {summary['claims_records']:,}")
    print(f"   Policy events: {summary['policy_events']:,}")
    print(f"   Benefit records: {summary['benefit_records']:,}")
    print(f"   Date range: {summary['date_range']['start']} to {summary['date_range']['end']}")
    print(f"   Markets: {summary['markets']}, LOBs: {summary['lobs']}")
    print("")
    print(f"📁 Output directory: {output_dir}")
    print("")
    
    return summary


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive synthetic healthcare datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate demo tier data (50k members, 2M claims)
  python generate_comprehensive.py --tier demo
  
  # Generate dev tier data (5k members, 200k claims)
  python generate_comprehensive.py --tier dev --format csv
  
  # Generate pilot tier data (150k members, 8M claims)
  python generate_comprehensive.py --tier pilot --months 36
        """,
    )
    parser.add_argument("--out", type=str, default="data/synthetic", help="Output directory")
    parser.add_argument("--tier", type=str, choices=["dev", "demo", "pilot"], default="demo", help="Volume tier")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for determinism")
    parser.add_argument("--months", type=int, default=24, help="Number of months of data")
    parser.add_argument("--start-date", type=str, default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--format", type=str, choices=["parquet", "csv"], default="parquet", help="Output format")
    parser.add_argument("--tenant-id", type=str, default="00000000-0000-0000-0000-000000000002", help="Tenant ID")
    
    args = parser.parse_args()
    
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    output_dir = Path(args.out) / args.tier
    
    summary = generate_comprehensive_datasets(
        output_dir=output_dir,
        volume_tier=args.tier,
        start_date=start_date,
        months=args.months,
        tenant_id=args.tenant_id,
        seed=args.seed,
        format=args.format,
    )
    
    print("🎉 All datasets generated successfully!")


if __name__ == "__main__":
    main()

