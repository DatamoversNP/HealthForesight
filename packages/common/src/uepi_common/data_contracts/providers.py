"""Canonical Provider Directory data contract"""
from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    """Provider type classification"""
    PHYSICIAN = "PHYSICIAN"
    NURSE_PRACTITIONER = "NURSE_PRACTITIONER"
    PHYSICIAN_ASSISTANT = "PHYSICIAN_ASSISTANT"
    FACILITY = "FACILITY"
    HOSPITAL = "HOSPITAL"
    ASC = "ASC"  # Ambulatory Surgical Center
    IMAGING_CENTER = "IMAGING_CENTER"
    LAB = "LAB"
    PHARMACY = "PHARMACY"
    HOME_HEALTH = "HOME_HEALTH"
    OTHER = "OTHER"


class Specialty(str, Enum):
    """Provider specialty classification (simplified set)"""
    PRIMARY_CARE = "PRIMARY_CARE"
    CARDIOLOGY = "CARDIOLOGY"
    ORTHOPEDICS = "ORTHOPEDICS"
    RADIOLOGY = "RADIOLOGY"
    ONCOLOGY = "ONCOLOGY"
    NEUROLOGY = "NEUROLOGY"
    SURGERY = "SURGERY"
    EMERGENCY_MEDICINE = "EMERGENCY_MEDICINE"
    URGENT_CARE = "URGENT_CARE"
    MENTAL_HEALTH = "MENTAL_HEALTH"
    PHYSICAL_THERAPY = "PHYSICAL_THERAPY"
    OTHER = "OTHER"


class FacilityType(str, Enum):
    """Facility type classification"""
    HOSPITAL = "HOSPITAL"
    HOSPITAL_OUTPATIENT = "HOSPITAL_OUTPATIENT"
    FREESTANDING_ASC = "FREESTANDING_ASC"
    FREESTANDING_IMAGING = "FREESTANDING_IMAGING"
    FREESTANDING_URGENT_CARE = "FREESTANDING_URGENT_CARE"
    OFFICE = "OFFICE"
    OTHER = "OTHER"


class NetworkStatus(str, Enum):
    """Network status"""
    IN_NETWORK = "IN_NETWORK"
    OUT_OF_NETWORK = "OUT_OF_NETWORK"
    TIERED = "TIERED"  # For tiered networks


class ProviderRecord(BaseModel):
    """Canonical Provider Directory record
    
    Required quarterly updates (can be monthly if provider network changes frequently).
    Each record represents one provider at a point in time.
    
    Schema Version: 1.0
    Expected Volume: 5k-20k providers
    Format: CSV or Parquet
    """
    
    # Primary Keys & Identifiers
    provider_id: str = Field(..., description="Provider identifier (payer-assigned or NPI)")
    npi: Optional[str] = Field(None, description="National Provider Identifier (NPI) - 10 digits")
    
    # Provider Classification
    provider_type: ProviderType = Field(..., description="Provider type classification")
    specialty: Optional[Specialty] = Field(None, description="Provider specialty (for physicians)")
    facility_type: Optional[FacilityType] = Field(None, description="Facility type (for facilities)")
    
    # Geographic & Market
    market: str = Field(..., description="Primary market/region (e.g., 'CA', 'TX')")
    state: Optional[str] = Field(None, description="State code (2-letter, e.g., 'CA')")
    zip_code: Optional[str] = Field(None, description="ZIP code (5 or 9 digits)")
    
    # Network Information
    network_status: NetworkStatus = Field(..., description="Network status")
    effective_date: date = Field(..., description="Effective date of this provider record (snapshot date)")
    termination_date: Optional[date] = Field(None, description="Provider termination date (if terminated from network)")
    
    # System Affiliation
    system_affiliation: Optional[str] = Field(None, description="Provider system/affiliation name (e.g., 'Kaiser', 'Sutter')")
    system_id: Optional[str] = Field(None, description="Provider system identifier")
    
    # Additional Context
    provider_name: Optional[str] = Field(None, description="Provider name (for display)")
    tax_id: Optional[str] = Field(None, description="Tax ID (if available)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider_id": "PRV-98765",
                "npi": "1234567890",
                "provider_type": "FACILITY",
                "facility_type": "FREESTANDING_IMAGING",
                "market": "CA",
                "state": "CA",
                "zip_code": "94102",
                "network_status": "IN_NETWORK",
                "effective_date": "2024-01-01",
                "system_affiliation": "Community Health Systems",
            }
        }

