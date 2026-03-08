"""
E. Pharmacy Domain
Comprehensive canonical model for pharmacy claims
"""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from uepi_common.data_contracts.canonical_base import CanonicalBase


# E1) Pharmacy Claims
# Grain: rx_claim_id
class PharmacyClaim(CanonicalBase):
    """Pharmacy Claim - comprehensive pharmacy utilization"""
    
    # Primary Key
    rx_claim_id: str = Field(..., description="Pharmacy claim identifier")
    
    # Member
    member_id: str = Field(..., description="Member identifier")
    
    # Fill Information
    fill_date: date = Field(..., description="Fill date")
    
    # Drug Coding
    ndc: str = Field(..., description="NDC code")
    gpi: Optional[str] = Field(None, description="GPI code")
    rxnorm: Optional[str] = Field(None, description="RxNorm code")
    drug_name: Optional[str] = Field(None, description="Drug name")
    therapeutic_class: Optional[str] = Field(None, description="Therapeutic class")
    
    # Quantity & Supply
    days_supply: int = Field(..., ge=0, description="Days supply")
    quantity: Decimal = Field(..., ge=0, description="Quantity")
    quantity_uom: Optional[str] = Field(None, description="Quantity unit of measure")
    refills: Optional[int] = Field(None, ge=0, description="Refills")
    
    # Providers
    prescriber_id: Optional[str] = Field(None, description="Prescriber identifier")
    pharmacy_id: Optional[str] = Field(None, description="Pharmacy identifier")
    
    # Financial
    paid_amount: Decimal = Field(..., ge=0, description="Paid amount")
    allowed_amount: Decimal = Field(..., ge=0, description="Allowed amount")
    member_pay: Optional[Decimal] = Field(None, ge=0, description="Member pay amount")
    
    # Formulary & UM
    formulary_tier: Optional[str] = Field(None, description="Formulary tier")
    pa_required_flag: Optional[bool] = Field(None, description="Prior authorization required flag")
    step_therapy_flag: Optional[bool] = Field(None, description="Step therapy flag")
    specialty_flag: Optional[bool] = Field(None, description="Specialty flag")
    generic_flag: Optional[bool] = Field(None, description="Generic flag")
    mail_order_flag: Optional[bool] = Field(None, description="Mail order flag")

