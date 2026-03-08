"""
D. Claims & Utilization Domain (Medical)
Comprehensive canonical models for claim header, claim line, and episodes of care
"""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

from uepi_common.data_contracts.canonical_base import CanonicalBase


class ClaimType(str, Enum):
    """Claim type"""
    INSTITUTIONAL = "INSTITUTIONAL"
    PROFESSIONAL = "PROFESSIONAL"


class ClaimStatus(str, Enum):
    """Claim status"""
    PAID = "PAID"
    DENIED = "DENIED"
    ADJUSTED = "ADJUSTED"
    VOID = "VOID"
    PENDING = "PENDING"


class FormType(str, Enum):
    """Form type"""
    CMS1500 = "CMS1500"
    UB04 = "UB04"


class PricingMethod(str, Enum):
    """Pricing method"""
    FFS = "FFS"  # Fee-for-service
    BUNDLE = "BUNDLE"
    CAPITATED_SHADOW = "CAPITATED_SHADOW"
    PER_DIEM = "PER_DIEM"
    DRG = "DRG"


class AdmissionType(str, Enum):
    """Admission type"""
    ELECTIVE = "ELECTIVE"
    EMERGENT = "EMERGENT"
    URGENT = "URGENT"
    OBSERVATION = "OBSERVATION"


class SiteOfCareClass(str, Enum):
    """Site of care classification"""
    OFFICE = "OFFICE"
    ASC = "ASC"  # Ambulatory Surgical Center
    HOPD = "HOPD"  # Hospital Outpatient Department
    ER = "ER"  # Emergency Room
    INPATIENT = "INPATIENT"
    HOME = "HOME"
    SNF = "SNF"  # Skilled Nursing Facility
    OTHER = "OTHER"


class BenefitCategory(str, Enum):
    """Benefit category"""
    INPATIENT = "INPATIENT"
    OUTPATIENT = "OUTPATIENT"
    PROFESSIONAL = "PROFESSIONAL"
    DME = "DME"  # Durable Medical Equipment
    OTHER = "OTHER"


class EpisodeType(str, Enum):
    """Episode of care type"""
    SURGERY = "SURGERY"
    MATERNITY = "MATERNITY"
    CHRONIC = "CHRONIC"
    ACUTE = "ACUTE"
    OTHER = "OTHER"


# D1) Claim Header (Medical)
# Grain: claim_id
class ClaimHeader(CanonicalBase):
    """Claim Header - institutional or professional claim header"""
    
    # Primary Key
    claim_id: str = Field(..., description="Claim identifier")
    
    # Claim Classification
    claim_type: ClaimType = Field(..., description="Claim type (institutional/professional)")
    bill_type: Optional[str] = Field(None, description="Bill type code")
    form_type: Optional[FormType] = Field(None, description="Form type (CMS1500/UB04)")
    
    # Member
    member_id: str = Field(..., description="Member identifier")
    
    # Providers
    billing_provider_id: Optional[str] = Field(None, description="Billing provider identifier")
    pay_to_provider_id: Optional[str] = Field(None, description="Pay-to provider identifier")
    
    # Dates
    claim_received_date: Optional[date] = Field(None, description="Claim received date")
    claim_processed_date: Optional[date] = Field(None, description="Claim processed date")
    
    # Status
    claim_status: ClaimStatus = Field(..., description="Claim status")
    denial_category: Optional[str] = Field(None, description="Denial category")
    denial_reason_codes: Optional[List[str]] = Field(None, description="Denial reason codes")
    
    # Financial
    total_allowed: Decimal = Field(..., ge=0, description="Total allowed amount")
    total_paid: Decimal = Field(..., ge=0, description="Total paid amount")
    total_member_resp: Optional[Decimal] = Field(None, ge=0, description="Total member responsibility")
    
    # Pricing & Payment
    pricing_method: Optional[PricingMethod] = Field(None, description="Pricing method")
    payment_arrangement_id: Optional[str] = Field(None, description="Payment arrangement identifier (links to contracts)")
    
    # Adjustments
    adjustment_indicator: Optional[bool] = Field(None, description="Adjustment indicator")
    original_claim_id: Optional[str] = Field(None, description="Original claim identifier (if adjusted)")
    
    # DRG (if inpatient)
    DRG: Optional[str] = Field(None, description="DRG code")
    APR_DRG: Optional[str] = Field(None, description="APR-DRG code")
    MS_DRG: Optional[str] = Field(None, description="MS-DRG code")
    
    # Admission/Discharge (if inpatient)
    admission_date: Optional[date] = Field(None, description="Admission date")
    discharge_date: Optional[date] = Field(None, description="Discharge date")
    discharge_status: Optional[str] = Field(None, description="Discharge status")
    admission_type: Optional[AdmissionType] = Field(None, description="Admission type")
    readmission_flag: Optional[bool] = Field(None, description="Readmission flag")


# D2) Claim Line (Medical) — Primary Analytical Table
# Grain: claim_line_id
class ClaimLine(CanonicalBase):
    """Claim Line - primary analytical table for utilization analysis"""
    
    # Primary Key
    claim_line_id: str = Field(..., description="Claim line identifier")
    claim_id: str = Field(..., description="Claim identifier (links to ClaimHeader)")
    
    # Member
    member_id: str = Field(..., description="Member identifier")
    
    # Coding
    cpt_hcpcs: Optional[str] = Field(None, description="CPT/HCPCS code")
    modifier_1: Optional[str] = Field(None, description="Modifier 1")
    modifier_2: Optional[str] = Field(None, description="Modifier 2")
    modifier_3: Optional[str] = Field(None, description="Modifier 3")
    modifier_4: Optional[str] = Field(None, description="Modifier 4")
    revenue_code: Optional[str] = Field(None, description="Revenue code")
    ndc: Optional[str] = Field(None, description="NDC code (for J-codes/infusion)")
    drg: Optional[str] = Field(None, description="DRG code (if line-level)")
    diagnosis_pointers: Optional[List[str]] = Field(None, description="Diagnosis pointers (dx1..dxN)")
    diagnosis_list: Optional[List[str]] = Field(None, description="Diagnosis codes list")
    
    # Service Context
    service_date_from: date = Field(..., description="Service date from")
    service_date_to: Optional[date] = Field(None, description="Service date to")
    place_of_service: str = Field(..., description="Place of service code")
    type_of_service: Optional[str] = Field(None, description="Type of service")
    betos: Optional[str] = Field(None, description="BETOS code")
    service_category: str = Field(..., description="Service category")
    site_of_care_class: Optional[SiteOfCareClass] = Field(None, description="Site of care class")
    units: Decimal = Field(..., ge=0, description="Units")
    unit_type: Optional[str] = Field(None, description="Unit type")
    
    # Providers
    rendering_provider_id: Optional[str] = Field(None, description="Rendering provider identifier")
    referring_provider_id: Optional[str] = Field(None, description="Referring provider identifier")
    ordering_provider_id: Optional[str] = Field(None, description="Ordering provider identifier")
    facility_id: Optional[str] = Field(None, description="Facility identifier")
    
    # Network & Benefit
    in_network_flag: bool = Field(..., description="In-network flag")
    network_id: Optional[str] = Field(None, description="Network identifier")
    network_tier: Optional[str] = Field(None, description="Network tier")
    benefit_category: Optional[BenefitCategory] = Field(None, description="Benefit category")
    prior_auth_required_flag: Optional[bool] = Field(None, description="Prior authorization required flag")
    prior_auth_id: Optional[str] = Field(None, description="Prior authorization identifier (if linked)")
    referral_required_flag: Optional[bool] = Field(None, description="Referral required flag")
    referral_id: Optional[str] = Field(None, description="Referral identifier (if linked)")
    
    # Financial
    billed_amount: Optional[Decimal] = Field(None, ge=0, description="Billed amount")
    allowed_amount: Decimal = Field(..., ge=0, description="Allowed amount")
    paid_amount: Decimal = Field(..., ge=0, description="Paid amount")
    copay_amount: Optional[Decimal] = Field(None, ge=0, description="Copay amount")
    coinsurance_amount: Optional[Decimal] = Field(None, ge=0, description="Coinsurance amount")
    deductible_amount: Optional[Decimal] = Field(None, ge=0, description="Deductible amount")
    member_resp_amount: Optional[Decimal] = Field(None, ge=0, description="Member responsibility amount")
    cob_amount: Optional[Decimal] = Field(None, ge=0, description="Coordination of benefits amount")
    coordination_of_benefits_flag: Optional[bool] = Field(None, description="Coordination of benefits flag")
    
    # Quality / Utilization Tags
    emergency_flag: Optional[bool] = Field(None, description="Emergency flag")
    avoidable_ed_flag: Optional[bool] = Field(None, description="Avoidable ED flag (if derived)")
    preventable_hosp_flag: Optional[bool] = Field(None, description="Preventable hospitalization flag (if derived)")
    low_value_care_flag: Optional[bool] = Field(None, description="Low-value care flag (if derived)")
    guideline_concordant_flag: Optional[bool] = Field(None, description="Guideline concordant flag (if derived)")


# D3) Episodes of Care (Derived or Provided)
# Grain: episode_id
class EpisodeOfCare(CanonicalBase):
    """Episode of Care - derived or provided episode grouping"""
    
    # Primary Key
    episode_id: str = Field(..., description="Episode identifier")
    
    # Member
    member_id: str = Field(..., description="Member identifier")
    
    # Episode Classification
    episode_type: EpisodeType = Field(..., description="Episode type")
    start_date: date = Field(..., description="Episode start date")
    end_date: date = Field(..., description="Episode end date")
    
    # Attribution
    attributed_provider_id: Optional[str] = Field(None, description="Attributed provider identifier")
    attributed_system_id: Optional[str] = Field(None, description="Attributed system identifier")
    
    # Episode Metrics
    episode_cost_total: Decimal = Field(..., ge=0, description="Total episode cost")
    claim_count: Optional[int] = Field(None, ge=0, description="Claim count within episode")
    claim_line_count: Optional[int] = Field(None, ge=0, description="Claim line count within episode")
    admission_count: Optional[int] = Field(None, ge=0, description="Admission count")
    ed_visit_count: Optional[int] = Field(None, ge=0, description="ED visit count")
    readmission_count: Optional[int] = Field(None, ge=0, description="Readmission count")

