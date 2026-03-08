"""Canonical Enrollment data contract"""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AgeBand(str, Enum):
    """Age band classification"""
    ZERO_TO_EIGHTEEN = "0-18"
    NINETEEN_TO_THIRTYFOUR = "19-34"
    THIRTYFIVE_TO_FORTYNINE = "35-49"
    FIFTY_TO_SIXTYFOUR = "50-64"
    SIXTYFIVE_PLUS = "65+"


class Gender(str, Enum):
    """Gender classification"""
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"
    UNKNOWN = "U"


class NetworkTier(str, Enum):
    """Network tier classification"""
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"
    OUT_OF_NETWORK = "OUT_OF_NETWORK"


class EnrollmentRecord(BaseModel):
    """Canonical Enrollment record - member-month level
    
    Required monthly updates. Each record represents one member in one month.
    This dataset enables cohort building and population-level analysis.
    
    Schema Version: 1.0
    Expected Volume: 50k-200k members * 12-36 months
    Format: CSV or Parquet (Parquet preferred)
    """
    
    # Primary Keys & Identifiers
    member_id: str = Field(..., description="Member identifier (anonymized/pseudonymized)")
    enrollment_month: date = Field(..., description="Enrollment month (first day of month, YYYY-MM-01)")
    
    # Line of Business & Market
    lob: str = Field(..., description="Line of business (e.g., 'Commercial', 'Medicaid', 'Medicare')")
    market: str = Field(..., description="Market/region (e.g., 'CA', 'TX', 'Northeast')")
    
    # Demographics
    age_band: AgeBand = Field(..., description="Age band classification")
    gender: Gender = Field(..., description="Gender classification")
    risk_score: Decimal = Field(..., ge=0, description="Member risk score (e.g., HCC, DxCG, proprietary)")
    
    # Network & Coverage
    network_tier: NetworkTier = Field(..., description="Network tier classification")
    enrolled_flag: bool = Field(..., description="Whether member is actively enrolled (true) or disenrolled (false)")
    
    # Enrollment Status
    enrollment_start_date: Optional[date] = Field(None, description="Member enrollment start date")
    enrollment_end_date: Optional[date] = Field(None, description="Member disenrollment date (if disenrolled)")
    
    # Additional Context
    product_type: Optional[str] = Field(None, description="Product type (e.g., 'HMO', 'PPO', 'EPO')")
    segment: Optional[str] = Field(None, description="Member segment (e.g., 'Individual', 'Small Group', 'Large Group')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "member_id": "MEM-12345",
                "enrollment_month": "2024-01-01",
                "lob": "Commercial",
                "market": "CA",
                "age_band": "35-49",
                "gender": "M",
                "risk_score": 1.25,
                "network_tier": "TIER_1",
                "enrolled_flag": True,
                "enrollment_start_date": "2023-06-01",
                "product_type": "PPO",
                "segment": "Large Group",
            }
        }

