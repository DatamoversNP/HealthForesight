"""Deterministic synthetic data generator using data contracts"""
import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

import numpy as np
import polars as pl

from uepi_common.data_contracts.claims import (
    ClaimsLine,
    ServiceCategory,
    PlaceOfService,
)
from uepi_common.data_contracts.enrollment import (
    EnrollmentRecord,
    AgeBand,
    Gender,
    NetworkTier,
)
from uepi_common.data_contracts.providers import (
    ProviderRecord,
    ProviderType,
    Specialty,
    FacilityType,
    NetworkStatus,
)
from uepi_common.data_contracts.benefits import BenefitDesignRecord
from uepi_common.data_contracts.manifest import IngestionManifest, DatasetType, IngestionMode


# Fixed seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# Configuration constants
MARKETS = ["CA", "TX", "NY", "FL", "IL"]
LOBS = ["Commercial", "Medicare", "Medicaid"]
AGE_BANDS = [AgeBand.ZERO_TO_EIGHTEEN, AgeBand.NINETEEN_TO_THIRTYFOUR, AgeBand.THIRTYFIVE_TO_FORTYNINE, AgeBand.FIFTY_TO_SIXTYFOUR, AgeBand.SIXTYFIVE_PLUS]


# Service categories with realistic codes and behavior
SERVICE_CATEGORIES = {
    ServiceCategory.IMAGING: {
        "cpt_codes": ["70450", "70460", "70470", "72141", "72142", "72146", "72148", "72149"],
        "hcpcs_codes": None,
        "base_allowed_range": (400, 2500),
        "pos_codes": [PlaceOfService.OFFICE, PlaceOfService.OUTPATIENT_HOSPITAL],
        "er_pos_codes": [PlaceOfService.ER],
        "er_allowed_range": (1000, 3500),
    },
    ServiceCategory.URGENT_CARE: {
        "cpt_codes": ["99281", "99282", "99283"],
        "hcpcs_codes": None,
        "base_allowed_range": (200, 600),
        "pos_codes": [PlaceOfService.URGENT_CARE],
    },
    ServiceCategory.EMERGENCY: {
        "cpt_codes": ["99284", "99285"],
        "hcpcs_codes": None,
        "base_allowed_range": (800, 2500),
        "pos_codes": [PlaceOfService.ER],
    },
    ServiceCategory.PRIMARY_CARE: {
        "cpt_codes": ["99213", "99214", "99215"],
        "hcpcs_codes": None,
        "base_allowed_range": (150, 400),
        "pos_codes": [PlaceOfService.OFFICE],
    },
    ServiceCategory.SPECIALTY_CARE: {
        "cpt_codes": ["99242", "99243", "99244", "99245"],
        "hcpcs_codes": None,
        "base_allowed_range": (300, 600),
        "pos_codes": [PlaceOfService.OFFICE],
    },
    ServiceCategory.REHAB: {
        "cpt_codes": ["97110", "97112", "97140", "97116"],
        "hcpcs_codes": None,
        "base_allowed_range": (80, 200),
        "pos_codes": [PlaceOfService.OFFICE, PlaceOfService.HOME],
    },
    ServiceCategory.PROCEDURE: {
        "cpt_codes": ["36415", "36416", "36417"],  # Venipuncture
        "hcpcs_codes": ["J9264", "J9265"],  # Chemotherapy drugs
        "base_allowed_range": (100, 500),
        "pos_codes": [PlaceOfService.OFFICE, PlaceOfService.OUTPATIENT_HOSPITAL],
    },
}


PROVIDER_SPECIALTIES = {
    Specialty.RADIOLOGY: {
        "provider_type": ProviderType.FACILITY,
        "facility_type": FacilityType.FREESTANDING_IMAGING,
        "service_categories": [ServiceCategory.IMAGING],
    },
    Specialty.ONCOLOGY: {
        "provider_type": ProviderType.FACILITY,
        "facility_type": FacilityType.HOSPITAL_OUTPATIENT,
        "service_categories": [ServiceCategory.PROCEDURE, ServiceCategory.SPECIALTY_CARE],
    },
    Specialty.PHYSICAL_THERAPY: {
        "provider_type": ProviderType.FACILITY,
        "facility_type": FacilityType.OFFICE,
        "service_categories": [ServiceCategory.REHAB],
    },
    Specialty.PRIMARY_CARE: {
        "provider_type": ProviderType.PHYSICIAN,
        "facility_type": None,
        "service_categories": [ServiceCategory.PRIMARY_CARE, ServiceCategory.URGENT_CARE],
    },
    Specialty.EMERGENCY_MEDICINE: {
        "provider_type": ProviderType.FACILITY,
        "facility_type": FacilityType.HOSPITAL,
        "service_categories": [ServiceCategory.EMERGENCY, ServiceCategory.IMAGING],
    },
}


class SyntheticDataGenerator:
    """Deterministic synthetic data generator with embedded behavioral patterns
    
    This generator creates realistic healthcare datasets with:
    - Deterministic behavior (fixed seed)
    - Embedded policy impact scenarios
    - Ground truth outcomes for validation
    - Realistic distributions and relationships
    """
    
    def __init__(self, seed: int = RANDOM_SEED):
        """Initialize generator with seed
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
    
    def generate_enrollment(
        self,
        tenant_id: UUID,
        member_count: int,
        start_date: date,
        end_date: date,
    ) -> list[EnrollmentRecord]:
        """Generate enrollment records (member-month level)
        
        Args:
            tenant_id: Tenant ID
            member_count: Number of unique members
            start_date: First enrollment month
            end_date: Last enrollment month
            
        Returns:
            List of EnrollmentRecord objects
        """
        records = []
        member_ids = [f"MEM_{i:06d}" for i in range(member_count)]
        
        # Generate enrollment months
        current_month = start_date
        while current_month <= end_date:
            for member_id in member_ids:
                # Skip some members randomly (disenrollment simulation)
                if random.random() < 0.95:  # 95% enrollment rate
                    # Calculate age band (simplified)
                    age_val = random.choice([
                        (0, AgeBand.ZERO_TO_EIGHTEEN),
                        (1, AgeBand.NINETEEN_TO_THIRTYFOUR),
                        (2, AgeBand.THIRTYFIVE_TO_FORTYNINE),
                        (3, AgeBand.FIFTY_TO_SIXTYFOUR),
                        (4, AgeBand.SIXTYFIVE_PLUS),
                    ])
                    age_band = age_val[1]
                    
                    # Generate risk score (skewed distribution - most members have low risk)
                    risk_score = Decimal(str(np.random.lognormal(mean=0, sigma=0.5)))
                    if risk_score > Decimal("3.0"):
                        risk_score = Decimal("3.0")  # Cap at 3.0
                    
                    record = EnrollmentRecord(
                        member_id=member_id,
                        enrollment_month=current_month,
                        lob=random.choice(LOBS),
                        market=random.choice(MARKETS),
                        age_band=age_band,
                        gender=random.choice(list(Gender)),
                        risk_score=risk_score,
                        network_tier=random.choice(list(NetworkTier)),
                        enrolled_flag=True,
                    )
                    records.append(record)
            
            # Move to next month (first day of next month)
            if current_month.month == 12:
                current_month = date(current_month.year + 1, 1, 1)
            else:
                current_month = date(current_month.year, current_month.month + 1, 1)
        
        return records
    
    def generate_providers(
        self,
        provider_count: int,
        effective_date: date,
    ) -> list[ProviderRecord]:
        """Generate provider directory records
        
        Args:
            provider_count: Number of providers
            effective_date: Effective date for provider records
            
        Returns:
            List of ProviderRecord objects
        """
        records = []
        
        for i in range(provider_count):
            # Assign specialty and type
            specialty = random.choice(list(Specialty))
            specialty_info = PROVIDER_SPECIALTIES[specialty]
            
            # Generate NPI (10 digits)
            npi = f"{random.randint(1000000000, 9999999999)}"
            
            # Assign to market
            market = random.choice(MARKETS)
            
            # System affiliation (some providers are independent, some in systems)
            if random.random() < 0.4:  # 40% in systems
                system_affiliation = random.choice([
                    "Community Health Systems",
                    "Sutter Health",
                    "Kaiser Permanente",
                    "UnitedHealth Group",
                ])
                system_id = f"SYS_{hash(system_affiliation) % 10000:04d}"
            else:
                system_affiliation = None
                system_id = None
            
            record = ProviderRecord(
                provider_id=f"PRV_{i:06d}",
                npi=npi,
                provider_type=specialty_info["provider_type"],
                specialty=specialty,
                facility_type=specialty_info["facility_type"],
                market=market,
                state=market[:2] if len(market) >= 2 else "CA",
                zip_code=f"{random.randint(10000, 99999)}",
                network_status=NetworkStatus.IN_NETWORK if random.random() < 0.85 else NetworkStatus.OUT_OF_NETWORK,
                effective_date=effective_date,
                system_affiliation=system_affiliation,
                system_id=system_id,
            )
            records.append(record)
        
        return records
    
    def generate_claims_lines(
        self,
        tenant_id: UUID,
        enrollment_records: list[EnrollmentRecord],
        provider_records: list[ProviderRecord],
        start_date: date,
        end_date: date,
        policy_events: Optional[list[dict[str, Any]]] = None,
    ) -> list[ClaimsLine]:
        """Generate claims lines with embedded policy impact scenarios
        
        Args:
            tenant_id: Tenant ID
            enrollment_records: Enrollment records for members
            provider_records: Provider directory records
            start_date: Start date for claims
            end_date: End date for claims
            policy_events: Optional policy events to simulate impacts
            
        Returns:
            List of ClaimsLine objects
        """
        claims = []
        
        # Build lookup structures
        members_by_market_lob: dict[tuple[str, str], list[EnrollmentRecord]] = {}
        for record in enrollment_records:
            key = (record.market, record.lob)
            if key not in members_by_market_lob:
                members_by_market_lob[key] = []
            members_by_market_lob[key].append(record)
        
        providers_by_market: dict[str, list[ProviderRecord]] = {}
        for provider in provider_records:
            if provider.market not in providers_by_market:
                providers_by_market[provider.market] = []
            providers_by_market[provider.market].append(provider)
        
        # Policy events lookup (by date and service category)
        policy_impacts: dict[tuple[date, ServiceCategory], dict[str, Any]] = {}
        if policy_events:
            for event in policy_events:
                effective_date = event.get("effective_date")
                service_category = event.get("service_category")
                if effective_date and service_category:
                    key = (effective_date, service_category)
                    policy_impacts[key] = event
        
        # Generate claims day by day
        current_date = start_date
        claim_id_counter = 1
        claim_line_id_counter = 1
        
        while current_date <= end_date:
            # Claims volume per day (varies by day of week)
            day_of_week = current_date.weekday()
            base_claims_per_day = 100 if day_of_week < 5 else 50  # Weekday vs weekend
            
            # Generate claims for this day
            claims_per_day = int(np.random.poisson(base_claims_per_day))
            
            for _ in range(claims_per_day):
                # Select market and LOB
                market = random.choice(MARKETS)
                lob = random.choice(LOBS)
                key = (market, lob)
                
                if key not in members_by_market_lob or not members_by_market_lob[key]:
                    continue
                
                # Select member
                member_record = random.choice(members_by_market_lob[key])
                
                # Select provider from same market
                if market not in providers_by_market or not providers_by_market[market]:
                    continue
                
                provider = random.choice(providers_by_market[market])
                
                # Select service category (weighted by provider specialty)
                service_category = self._select_service_category(provider.specialty if provider.specialty else Specialty.PRIMARY_CARE)
                
                if service_category not in SERVICE_CATEGORIES:
                    continue
                
                service_info = SERVICE_CATEGORIES[service_category]
                
                # Select CPT code
                cpt_code = random.choice(service_info["cpt_codes"])
                
                # Select POS code
                if PlaceOfService.ER in service_info.get("pos_codes", []):
                    # Some services can be in ER
                    pos_code = PlaceOfService.ER if random.random() < 0.1 else random.choice(service_info["pos_codes"])
                else:
                    pos_code = random.choice(service_info["pos_codes"])
                
                # Check for policy impacts
                volume_multiplier = 1.0
                cost_multiplier = 1.0
                
                # Check policy impacts
                for (policy_date, policy_category), policy_event in policy_impacts.items():
                    if current_date >= policy_date and service_category == policy_category:
                        volume_multiplier *= policy_event.get("volume_multiplier", 1.0)
                        cost_multiplier *= policy_event.get("cost_multiplier", 1.0)
                
                # Generate claim if volume multiplier allows
                if random.random() > volume_multiplier:
                    continue  # Policy impact: claim not filed
                
                # Generate financial amounts
                if pos_code == PlaceOfService.ER and "er_allowed_range" in service_info:
                    allowed_amount = Decimal(str(np.random.uniform(*service_info["er_allowed_range"])))
                else:
                    allowed_amount = Decimal(str(np.random.uniform(*service_info["base_allowed_range"])))
                
                allowed_amount *= Decimal(str(cost_multiplier))
                
                # Paid amount (typically 80-90% of allowed for in-network)
                paid_pct = Decimal("0.85") if provider.network_status == NetworkStatus.IN_NETWORK else Decimal("0.60")
                paid_amount = allowed_amount * paid_pct
                member_cost_share = allowed_amount - paid_amount
                
                # Generate claim
                claim_id = f"CLM-{tenant_id.hex[:8]}-{claim_id_counter:08d}"
                claim_line_id = f"{claim_id}-{claim_line_id_counter:03d}"
                
                claim = ClaimsLine(
                    claim_id=claim_id,
                    claim_line_id=claim_line_id,
                    member_id=member_record.member_id,
                    provider_id=provider.provider_id,
                    service_date=current_date,
                    paid_date=current_date + timedelta(days=random.randint(7, 30)),
                    adjudication_date=current_date + timedelta(days=random.randint(5, 25)),
                    lob=member_record.lob,
                    market=member_record.market,
                    cpt_code=cpt_code,
                    service_category=service_category,
                    place_of_service=pos_code,
                    units=Decimal("1.0"),
                    allowed_amount=allowed_amount,
                    paid_amount=paid_amount,
                    member_cost_share=member_cost_share,
                    in_network=provider.network_status == NetworkStatus.IN_NETWORK,
                    requires_prior_auth=random.random() < 0.1,  # 10% require PA
                    prior_auth_approved=random.random() < 0.8 if random.random() < 0.1 else None,
                    facility_type=provider.facility_type.value if provider.facility_type else None,
                    system_affiliation=provider.system_affiliation,
                )
                
                claims.append(claim)
                claim_line_id_counter += 1
            
            claim_id_counter += 1
            claim_line_id_counter = 1
            current_date += timedelta(days=1)
        
        return claims
    
    def _select_service_category(self, provider_specialty: Specialty) -> ServiceCategory:
        """Select service category based on provider specialty"""
        if provider_specialty in PROVIDER_SPECIALTIES:
            categories = PROVIDER_SPECIALTIES[provider_specialty]["service_categories"]
            return random.choice(categories)
        return random.choice(list(SERVICE_CATEGORIES.keys()))
    
    def generate_benefit_design(
        self,
        effective_date: date,
    ) -> list[BenefitDesignRecord]:
        """Generate benefit design records
        
        Args:
            effective_date: Effective date for benefit design
            
        Returns:
            List of BenefitDesignRecord objects
        """
        records = []
        
        for lob in LOBS:
            for service_category in ServiceCategory:
                # Different cost sharing by LOB and service
                if lob == "Commercial":
                    copay = Decimal(str(np.random.uniform(25, 75)))
                    coinsurance = Decimal("0.0") if random.random() < 0.7 else Decimal(str(np.random.uniform(10, 30)))
                elif lob == "Medicare":
                    copay = Decimal("0.0")
                    coinsurance = Decimal(str(np.random.uniform(10, 20)))
                else:  # Medicaid
                    copay = Decimal("0.0")
                    coinsurance = Decimal("0.0")
                
                record = BenefitDesignRecord(
                    lob=lob,
                    service_category=service_category,
                    effective_date=effective_date,
                    copay_in_network=copay if copay > 0 else None,
                    copay_out_of_network=copay * Decimal("2.0") if copay > 0 else None,
                    coinsurance_in_network=coinsurance if coinsurance > 0 else None,
                    coinsurance_out_of_network=coinsurance * Decimal("1.5") if coinsurance > 0 else None,
                    deductible_applies=True if lob == "Commercial" else False,
                    oop_maximum_in_network=Decimal("5000.00") if lob == "Commercial" else None,
                )
                records.append(record)
        
        return records


# Fix missing import
from typing import Optional

