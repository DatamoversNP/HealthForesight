"""
B. Member & Eligibility Domain
Comprehensive canonical models for member master, eligibility, and risk stratification
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from uepi_common.data_contracts.canonical_base import CanonicalBase


class Gender(str, Enum):
    """Gender classification"""
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"
    UNKNOWN = "U"


class UrbanicityIndex(str, Enum):
    """Urbanicity classification"""
    URBAN = "URBAN"
    SUBURBAN = "SUBURBAN"
    RURAL = "RURAL"
    FRONTIER = "FRONTIER"


class EmploymentStatus(str, Enum):
    """Employment status"""
    EMPLOYED = "EMPLOYED"
    UNEMPLOYED = "UNEMPLOYED"
    RETIRED = "RETIRED"
    DISABLED = "DISABLED"
    STUDENT = "STUDENT"
    UNKNOWN = "UNKNOWN"


class CoverageStatus(str, Enum):
    """Coverage status"""
    ACTIVE = "ACTIVE"
    TERMED = "TERMED"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"


class RiskModelType(str, Enum):
    """Risk model type"""
    HCC = "HCC"
    ACG = "ACG"
    DxCG = "DxCG"
    CUSTOM = "CUSTOM"


# B1) Member Master (Member Dimension)
# Grain: member_id (slowly changing)
class MemberMaster(CanonicalBase):
    """Member Master - comprehensive member dimension with SDOH and clinical flags"""
    
    # Primary Key
    member_id: str = Field(..., description="Member identifier (de-identified)")
    
    # Identifiers
    subscriber_id: Optional[str] = Field(None, description="Subscriber identifier")
    family_id: Optional[str] = Field(None, description="Family identifier")
    household_id: Optional[str] = Field(None, description="Household identifier")
    payer_member_key: Optional[str] = Field(None, description="Payer member key (encrypted/tokenized)")
    hicn: Optional[str] = Field(None, description="Medicare HICN (tokenized)")
    mbi: Optional[str] = Field(None, description="Medicare MBI (tokenized)")
    
    # Demographics
    dob: Optional[date] = Field(None, description="Date of birth")
    birth_year: Optional[int] = Field(None, ge=1900, le=2100, description="Birth year (if DOB not available)")
    age: Optional[int] = Field(None, ge=0, le=150, description="Age (calculated or provided)")
    gender: Optional[Gender] = Field(None, description="Gender")
    race: Optional[str] = Field(None, description="Race")
    ethnicity: Optional[str] = Field(None, description="Ethnicity")
    preferred_language: Optional[str] = Field(None, description="Preferred language")
    
    # Address & Geography
    address_zip3: Optional[str] = Field(None, description="ZIP code (3 digits)")
    address_zip5: Optional[str] = Field(None, description="ZIP code (5 digits)")
    county: Optional[str] = Field(None, description="County")
    state: Optional[str] = Field(None, description="State (2-letter code)")
    geo_lat: Optional[Decimal] = Field(None, description="Latitude")
    geo_lon: Optional[Decimal] = Field(None, description="Longitude")
    rural_flag: Optional[bool] = Field(None, description="Rural flag")
    urbanicity_index: Optional[UrbanicityIndex] = Field(None, description="Urbanicity index")
    
    # Socioeconomic / SDOH
    income_band: Optional[str] = Field(None, description="Income band")
    education_band: Optional[str] = Field(None, description="Education band")
    employment_status: Optional[EmploymentStatus] = Field(None, description="Employment status")
    housing_insecurity_flag: Optional[bool] = Field(None, description="Housing insecurity flag")
    food_insecurity_flag: Optional[bool] = Field(None, description="Food insecurity flag")
    transportation_barrier_flag: Optional[bool] = Field(None, description="Transportation barrier flag")
    neighborhood_deprivation_index: Optional[Decimal] = Field(None, description="Neighborhood deprivation index")
    area_vulnerability_index: Optional[Decimal] = Field(None, description="Area vulnerability index (SVI/ADI)")
    
    # Clinical flags
    pregnancy_flag: Optional[bool] = Field(None, description="Pregnancy flag")
    frailty_flag: Optional[bool] = Field(None, description="Frailty flag")
    disability_flag: Optional[bool] = Field(None, description="Disability flag")
    hospice_flag: Optional[bool] = Field(None, description="Hospice flag")
    ESRD_flag: Optional[bool] = Field(None, description="End-stage renal disease flag")
    dual_eligible_flag: Optional[bool] = Field(None, description="Dual eligible (Medicare/Medicaid) flag")
    
    # Engagement
    portal_user_flag: Optional[bool] = Field(None, description="Portal user flag")
    preferred_contact_channel: Optional[str] = Field(None, description="Preferred contact channel")


# B2) Eligibility & Enrollment (Coverage Fact)
# Grain: member_id × coverage_month × plan_id
class EligibilityEnrollment(CanonicalBase):
    """Eligibility & Enrollment - coverage fact table"""
    
    # Primary Keys
    member_id: str = Field(..., description="Member identifier")
    coverage_month: str = Field(..., description="Coverage month (YYYY-MM)")
    plan_id: str = Field(..., description="Plan identifier")
    
    # Line of Business & Product
    line_of_business: str = Field(..., description="Line of business (Commercial/MA/Medicaid/Exchange)")
    product_id: Optional[str] = Field(None, description="Product identifier")
    benefit_package_id: Optional[str] = Field(None, description="Benefit package identifier")
    
    # Group & Segment
    group_id: Optional[str] = Field(None, description="Group identifier (employer)")
    segment: Optional[str] = Field(None, description="Segment (ASO/FI)")
    
    # Network
    network_id: Optional[str] = Field(None, description="Network identifier")
    network_tier: Optional[str] = Field(None, description="Network tier")
    
    # Enrollment Period
    enrollment_start_date: Optional[date] = Field(None, description="Enrollment start date")
    enrollment_end_date: Optional[date] = Field(None, description="Enrollment end date")
    coverage_status: CoverageStatus = Field(..., description="Coverage status")
    reason_code: Optional[str] = Field(None, description="Termination reason code")
    
    # Cost Share & Care
    member_cost_share_level: Optional[str] = Field(None, description="Member cost share level (plan tier)")
    PCP_id: Optional[str] = Field(None, description="Primary care provider identifier (if assigned)")
    care_management_program_id: Optional[str] = Field(None, description="Care management program identifier (if enrolled)")


# B3) Risk & Stratification
# Grain: member_id × month (or risk_run_date)
class MemberRiskStratification(CanonicalBase):
    """Member Risk & Stratification - risk scores and predictions"""
    
    # Primary Keys
    member_id: str = Field(..., description="Member identifier")
    risk_run_date: date = Field(..., description="Risk run date")
    month: Optional[str] = Field(None, description="Month (YYYY-MM) - alternative to risk_run_date")
    
    # Risk Score
    risk_score: Decimal = Field(..., ge=0, description="Risk score (HCC/ACG/custom)")
    risk_model_name: Optional[str] = Field(None, description="Risk model name")
    risk_model_version: Optional[str] = Field(None, description="Risk model version")
    
    # Predictions
    predicted_cost_pmpm: Optional[Decimal] = Field(None, ge=0, description="Predicted cost per member per month")
    predicted_admission_risk: Optional[Decimal] = Field(None, ge=0, le=1, description="Predicted admission risk (0-1)")
    predicted_ed_risk: Optional[Decimal] = Field(None, ge=0, le=1, description="Predicted ED risk (0-1)")
    predicted_readmission_risk: Optional[Decimal] = Field(None, ge=0, le=1, description="Predicted readmission risk (0-1)")
    
    # Care Gaps & Conditions
    gaps_in_care_count: Optional[int] = Field(None, ge=0, description="Gaps in care count")
    chronic_condition_count: Optional[int] = Field(None, ge=0, description="Chronic condition count")
    utilization_intensity_index: Optional[Decimal] = Field(None, ge=0, description="Utilization intensity index")
    
    # Specialty Risk Scores
    pharmacy_risk_score: Optional[Decimal] = Field(None, ge=0, description="Pharmacy risk score")
    behavioral_health_risk_score: Optional[Decimal] = Field(None, ge=0, description="Behavioral health risk score")

