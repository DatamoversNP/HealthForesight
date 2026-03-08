"""
F. Provider, Facility & Network Domain
Comprehensive canonical models for providers, facilities, networks, and contracts
"""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

from uepi_common.data_contracts.canonical_base import CanonicalBase


class ProviderType(str, Enum):
    """Provider type"""
    INDIVIDUAL = "INDIVIDUAL"
    FACILITY = "FACILITY"


class RateType(str, Enum):
    """Rate type"""
    FFS = "FFS"  # Fee-for-service
    DRG = "DRG"
    PER_DIEM = "PER_DIEM"
    CAPITATION = "CAPITATION"
    BUNDLE = "BUNDLE"


class CodeType(str, Enum):
    """Code type"""
    CPT = "CPT"
    HCPCS = "HCPCS"
    DRG = "DRG"
    REVENUE = "REVENUE"


# F1) Provider Master
# Grain: provider_id (SCD)
class ProviderMaster(CanonicalBase):
    """Provider Master - comprehensive provider dimension"""
    
    # Primary Key
    provider_id: str = Field(..., description="Provider identifier")
    npi: Optional[str] = Field(None, description="National Provider Identifier (10 digits)")
    
    # Provider Information
    provider_name: Optional[str] = Field(None, description="Provider name")
    provider_type: ProviderType = Field(..., description="Provider type (individual/facility)")
    specialty_primary: Optional[str] = Field(None, description="Primary specialty")
    specialty_secondary: Optional[str] = Field(None, description="Secondary specialty")
    taxonomy_codes: Optional[List[str]] = Field(None, description="Taxonomy codes")
    
    # Organization & System
    org_id: Optional[str] = Field(None, description="Organization identifier")
    system_affiliation_id: Optional[str] = Field(None, description="System affiliation identifier")
    
    # Practice Location
    practice_location_zip: Optional[str] = Field(None, description="Practice location ZIP code")
    practice_location_county: Optional[str] = Field(None, description="Practice location county")
    practice_location_state: Optional[str] = Field(None, description="Practice location state")
    
    # Capabilities
    accepting_new_patients_flag: Optional[bool] = Field(None, description="Accepting new patients flag")
    telehealth_capable_flag: Optional[bool] = Field(None, description="Telehealth capable flag")
    languages: Optional[List[str]] = Field(None, description="Languages spoken")
    
    # Quality & Capacity
    quality_scores: Optional[dict] = Field(None, description="Quality scores (if available)")
    capacity_indicators: Optional[dict] = Field(None, description="Capacity indicators (panel size, appt wait)")


# F2) Facility Master
class FacilityMaster(CanonicalBase):
    """Facility Master - facility dimension"""
    
    # Primary Key
    facility_id: str = Field(..., description="Facility identifier")
    facility_name: Optional[str] = Field(None, description="Facility name")
    facility_type: str = Field(..., description="Facility type (HOPD, ASC, freestanding imaging, SNF, etc.)")
    
    # Facility Characteristics
    trauma_level: Optional[str] = Field(None, description="Trauma level")
    bed_count: Optional[int] = Field(None, ge=0, description="Bed count")
    ownership_type: Optional[str] = Field(None, description="Ownership type")
    
    # Geography
    facility_zip: Optional[str] = Field(None, description="Facility ZIP code")
    facility_county: Optional[str] = Field(None, description="Facility county")
    facility_state: Optional[str] = Field(None, description="Facility state")
    geo_lat: Optional[Decimal] = Field(None, description="Latitude")
    geo_lon: Optional[Decimal] = Field(None, description="Longitude")


# F3) Network Configuration
# Grain: network_id × provider_id × effective_period
class NetworkConfiguration(CanonicalBase):
    """Network Configuration - provider-network relationships"""
    
    # Primary Keys
    network_id: str = Field(..., description="Network identifier")
    network_name: Optional[str] = Field(None, description="Network name")
    network_tier: Optional[str] = Field(None, description="Network tier")
    provider_id: str = Field(..., description="Provider identifier")
    
    # Network Status
    in_network_flag: bool = Field(..., description="In-network flag")
    effective_start: date = Field(..., description="Effective start date")
    effective_end: Optional[date] = Field(None, description="Effective end date")
    
    # Exclusions & Rules
    exclusions: Optional[List[str]] = Field(None, description="Exclusions")
    referral_required_rules: Optional[dict] = Field(None, description="Referral required rules (high-level)")


# F4) Provider Contract & Rates
# Grain: contract_id × code × effective_period
class ProviderContract(CanonicalBase):
    """Provider Contract & Rates - contract and rate information"""
    
    # Primary Keys
    contract_id: str = Field(..., description="Contract identifier")
    provider_id: Optional[str] = Field(None, description="Provider identifier")
    facility_id: Optional[str] = Field(None, description="Facility identifier")
    code: str = Field(..., description="Code (CPT/HCPCS/DRG/revenue)")
    effective_start: date = Field(..., description="Effective start date")
    effective_end: Optional[date] = Field(None, description="Effective end date")
    
    # Rate Information
    rate_type: RateType = Field(..., description="Rate type (FFS/DRG/per diem/capitation/bundle)")
    fee_schedule_id: Optional[str] = Field(None, description="Fee schedule identifier")
    code_type: CodeType = Field(..., description="Code type (CPT/HCPCS/DRG/revenue)")
    allowed_rate: Optional[Decimal] = Field(None, ge=0, description="Allowed rate")
    percent_of_medicare: Optional[Decimal] = Field(None, ge=0, description="Percent of Medicare")
    
    # Stoploss Terms
    stoploss_terms: Optional[dict] = Field(None, description="Stoploss terms (optional)")

