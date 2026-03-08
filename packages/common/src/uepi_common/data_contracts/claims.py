"""Canonical Claims Lines data contract"""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ServiceCategory(str, Enum):
    """Service category classification"""
    INPATIENT = "INPATIENT"
    OUTPATIENT = "OUTPATIENT"
    EMERGENCY = "EMERGENCY"
    URGENT_CARE = "URGENT_CARE"
    PRIMARY_CARE = "PRIMARY_CARE"
    SPECIALTY_CARE = "SPECIALTY_CARE"
    IMAGING = "IMAGING"
    LAB = "LAB"
    PHARMACY = "PHARMACY"
    PROCEDURE = "PROCEDURE"
    REHAB = "REHAB"
    MENTAL_HEALTH = "MENTAL_HEALTH"
    OTHER = "OTHER"


class PlaceOfService(str, Enum):
    """Place of service codes (CMS standard)"""
    # Common POS codes
    HOSPITAL = "21"  # Inpatient Hospital
    OUTPATIENT_HOSPITAL = "22"  # Outpatient Hospital
    ER = "23"  # Emergency Room
    URGENT_CARE = "20"  # Urgent Care Facility
    OFFICE = "11"  # Office
    HOME = "12"  # Home
    FREESTANDING_ASC = "24"  # Ambulatory Surgical Center
    FREESTANDING_IMAGING = "49"  # Independent Clinic
    OTHER = "99"  # Other Place of Service


class ClaimsLine(BaseModel):
    """Canonical Claims Line record - primary analytical dataset
    
    This is the most important dataset. Every claim line represents a billed service.
    Required monthly updates.
    
    Schema Version: 1.0
    Expected Volume: 5-15M lines per month (depending on member population)
    Format: CSV or Parquet (Parquet preferred for large datasets)
    """
    
    # Primary Keys & Identifiers
    claim_id: str = Field(..., description="Unique claim identifier (payer-assigned)")
    claim_line_id: str = Field(..., description="Unique claim line identifier (payer-assigned)")
    member_id: str = Field(..., description="Member identifier (anonymized/pseudonymized)")
    provider_id: str = Field(..., description="Provider identifier (NPI or payer-assigned)")
    
    # Temporal Fields
    service_date: date = Field(..., description="Date of service (YYYY-MM-DD)")
    paid_date: Optional[date] = Field(None, description="Date claim was paid (YYYY-MM-DD)")
    adjudication_date: Optional[date] = Field(None, description="Date claim was adjudicated (YYYY-MM-DD)")
    
    # Line of Business & Market
    lob: str = Field(..., description="Line of business (e.g., 'Commercial', 'Medicaid', 'Medicare')")
    market: str = Field(..., description="Market/region (e.g., 'CA', 'TX', 'Northeast')")
    
    # Service Coding
    cpt_code: Optional[str] = Field(None, description="CPT procedure code (5 digits, e.g., '99213')")
    hcpcs_code: Optional[str] = Field(None, description="HCPCS code (e.g., 'J9264')")
    drg_code: Optional[str] = Field(None, description="DRG code (e.g., '470') - for inpatient")
    icd10_diagnosis_codes: Optional[list[str]] = Field(
        None, 
        description="List of ICD-10 diagnosis codes (e.g., ['E11.9', 'I10'])"
    )
    icd10_procedure_codes: Optional[list[str]] = Field(
        None,
        description="List of ICD-10 procedure codes (for inpatient)"
    )
    
    # Service Classification
    service_category: ServiceCategory = Field(..., description="Service category classification")
    place_of_service: PlaceOfService = Field(..., description="Place of service code (CMS standard)")
    
    # Utilization Metrics
    units: Decimal = Field(..., ge=0, description="Units of service (e.g., 1.0, 2.5)")
    
    # Financial Fields
    allowed_amount: Decimal = Field(..., ge=0, description="Allowed amount (negotiated rate)")
    paid_amount: Decimal = Field(..., ge=0, description="Amount paid by payer")
    member_cost_share: Decimal = Field(default=Decimal("0"), ge=0, description="Member cost share (copay + coinsurance)")
    
    # Network & Authorization
    in_network: bool = Field(..., description="Whether provider is in-network")
    requires_prior_auth: bool = Field(default=False, description="Whether service requires prior auth")
    prior_auth_approved: Optional[bool] = Field(None, description="Whether prior auth was approved")
    prior_auth_id: Optional[str] = Field(None, description="Prior authorization identifier")
    
    # Site-of-Care Information
    facility_type: Optional[str] = Field(None, description="Facility type (e.g., 'HOSPITAL', 'ASC', 'FREESTANDING')")
    system_affiliation: Optional[str] = Field(None, description="Provider system/affiliation name")
    
    # Additional Context
    rendering_provider_id: Optional[str] = Field(None, description="Rendering provider NPI (if different from billing)")
    billing_provider_id: Optional[str] = Field(None, description="Billing provider NPI")
    referring_provider_id: Optional[str] = Field(None, description="Referring provider NPI")
    
    @field_validator('cpt_code')
    @classmethod
    def validate_cpt_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate CPT code format (5 digits)"""
        if v is None:
            return v
        # Remove dots/dashes, should be 5 digits
        cleaned = v.replace('.', '').replace('-', '').strip()
        if len(cleaned) != 5 or not cleaned.isdigit():
            raise ValueError(f"CPT code must be 5 digits, got: {v}")
        return cleaned
    
    @field_validator('hcpcs_code')
    @classmethod
    def validate_hcpcs_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate HCPCS code format"""
        if v is None:
            return v
        # HCPCS codes are typically 5 characters (alphanumeric)
        cleaned = v.strip().upper()
        if len(cleaned) != 5:
            raise ValueError(f"HCPCS code must be 5 characters, got: {v}")
        return cleaned
    
    @field_validator('icd10_diagnosis_codes', 'icd10_procedure_codes')
    @classmethod
    def validate_icd10_codes(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate ICD-10 codes (format: A00.0 - Z99.9)"""
        if v is None or len(v) == 0:
            return v
        cleaned = []
        for code in v:
            cleaned_code = code.strip().upper()
            # Basic validation: should start with letter, followed by 2 digits, optional dot and digits
            if not (len(cleaned_code) >= 3 and cleaned_code[0].isalpha() and cleaned_code[1:3].isdigit()):
                raise ValueError(f"Invalid ICD-10 code format: {code}")
            cleaned.append(cleaned_code)
        return cleaned
    
    class Config:
        json_schema_extra = {
            "example": {
                "claim_id": "CLM-2024-00123456",
                "claim_line_id": "CLM-2024-00123456-001",
                "member_id": "MEM-12345",
                "provider_id": "PRV-98765",
                "service_date": "2024-01-15",
                "paid_date": "2024-01-25",
                "adjudication_date": "2024-01-22",
                "lob": "Commercial",
                "market": "CA",
                "cpt_code": "99213",
                "service_category": "PRIMARY_CARE",
                "place_of_service": "11",
                "units": 1.0,
                "allowed_amount": 150.00,
                "paid_amount": 120.00,
                "member_cost_share": 30.00,
                "in_network": True,
                "requires_prior_auth": False,
                "facility_type": "OFFICE",
            }
        }

