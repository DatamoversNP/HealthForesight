"""
G. Benefits & Accumulators Domain
Comprehensive canonical models for benefit design and member accumulators
"""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict
from pydantic import BaseModel, Field

from uepi_common.data_contracts.canonical_base import CanonicalBase


# G1) Benefit Design
# Grain: plan_id × benefit_component × effective_period
class BenefitDesign(CanonicalBase):
    """Benefit Design - plan benefit structure"""
    
    # Primary Keys
    plan_id: str = Field(..., description="Plan identifier")
    benefit_package_id: Optional[str] = Field(None, description="Benefit package identifier")
    service_category: str = Field(..., description="Service category")
    effective_start: date = Field(..., description="Effective start date")
    effective_end: Optional[date] = Field(None, description="Effective end date")
    
    # Cost Sharing
    copay: Optional[Decimal] = Field(None, ge=0, description="Copay amount")
    coinsurance: Optional[Decimal] = Field(None, ge=0, le=1, description="Coinsurance rate (0-1)")
    deductible: Optional[Decimal] = Field(None, ge=0, description="Deductible amount")
    oop_max: Optional[Decimal] = Field(None, ge=0, description="Out-of-pocket maximum")
    
    # Limits
    visit_limit: Optional[int] = Field(None, ge=0, description="Visit limit")
    unit_limit: Optional[int] = Field(None, ge=0, description="Unit limit")
    
    # UM Indicators
    prior_auth_indicator: Optional[bool] = Field(None, description="Prior authorization indicator (plan-level)")
    referral_indicator: Optional[bool] = Field(None, description="Referral indicator")
    
    # Tiered Cost Sharing
    tiered_cost_sharing_by_site: Optional[Dict[str, dict]] = Field(None, description="Tiered cost sharing by site (structured)")


# G2) Accumulators (Optional but powerful)
# Grain: member_id × month
class MemberAccumulator(CanonicalBase):
    """Member Accumulator - member benefit accumulator status"""
    
    # Primary Keys
    member_id: str = Field(..., description="Member identifier")
    month: str = Field(..., description="Month (YYYY-MM)")
    
    # Deductible
    deductible_met: Optional[Decimal] = Field(None, ge=0, description="Deductible met amount")
    deductible_remaining: Optional[Decimal] = Field(None, ge=0, description="Deductible remaining amount")
    
    # Out-of-Pocket
    oop_met: Optional[Decimal] = Field(None, ge=0, description="Out-of-pocket met amount")
    oop_remaining: Optional[Decimal] = Field(None, ge=0, description="Out-of-pocket remaining amount")
    
    # Remaining Visits (by category)
    remaining_visits: Optional[Dict[str, int]] = Field(None, description="Remaining visits by category")
    
    # Remaining Units (by category)
    remaining_units: Optional[Dict[str, Decimal]] = Field(None, description="Remaining units by category")

