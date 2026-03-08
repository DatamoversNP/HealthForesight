"""Canonical Benefit Design data contract"""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from uepi_common.data_contracts.claims import ServiceCategory


class BenefitDesignRecord(BaseModel):
    """Canonical Benefit Design record - LOB/service-level cost sharing
    
    Required annual updates (or when benefit design changes).
    Each record represents cost sharing rules for a service category within a LOB.
    
    Schema Version: 1.0
    Expected Volume: ~100-500 records (LOB x service categories)
    Format: CSV or Parquet
    """
    
    # Primary Keys & Identifiers
    lob: str = Field(..., description="Line of business (e.g., 'Commercial', 'Medicaid')")
    service_category: ServiceCategory = Field(..., description="Service category")
    
    # Effective Period
    effective_date: date = Field(..., description="Effective start date of benefit design")
    termination_date: Optional[date] = Field(None, description="Termination date (if benefit design changed)")
    
    # Cost Sharing (all amounts in USD)
    copay_in_network: Optional[Decimal] = Field(None, ge=0, description="In-network copay amount")
    copay_out_of_network: Optional[Decimal] = Field(None, ge=0, description="Out-of-network copay amount")
    coinsurance_in_network: Optional[Decimal] = Field(None, ge=0, le=100, description="In-network coinsurance percentage (0-100)")
    coinsurance_out_of_network: Optional[Decimal] = Field(None, ge=0, le=100, description="Out-of-network coinsurance percentage (0-100)")
    
    # Deductible & OOP Maximum
    deductible_applies: bool = Field(default=True, description="Whether deductible applies before cost sharing")
    oop_maximum_in_network: Optional[Decimal] = Field(None, ge=0, description="Out-of-pocket maximum (in-network)")
    oop_maximum_out_of_network: Optional[Decimal] = Field(None, ge=0, description="Out-of-pocket maximum (out-of-network)")
    
    # Additional Context
    benefit_variant: Optional[str] = Field(None, description="Benefit variant (e.g., 'Standard', 'High Deductible', 'Zero Copay')")
    market: Optional[str] = Field(None, description="Market-specific benefit (if varies by market)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "lob": "Commercial",
                "service_category": "URGENT_CARE",
                "effective_date": "2024-01-01",
                "copay_in_network": 50.00,
                "copay_out_of_network": 100.00,
                "coinsurance_in_network": 0.0,
                "coinsurance_out_of_network": 40.0,
                "deductible_applies": True,
                "oop_maximum_in_network": 5000.00,
                "benefit_variant": "Standard",
                "market": "CA",
            }
        }

