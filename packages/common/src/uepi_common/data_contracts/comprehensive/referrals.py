"""
I. Referrals & Care Pathways
Comprehensive canonical model for referrals
"""
from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from uepi_common.data_contracts.canonical_base import CanonicalBase


class ReferralStatus(str, Enum):
    """Referral status"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


# I1) Referrals
# Grain: referral_id
class Referral(CanonicalBase):
    """Referral - referral and care pathway tracking"""
    
    # Primary Key
    referral_id: str = Field(..., description="Referral identifier")
    
    # Member
    member_id: str = Field(..., description="Member identifier")
    
    # Providers
    ordering_provider_id: str = Field(..., description="Ordering provider identifier")
    referred_to_provider_id: str = Field(..., description="Referred-to provider identifier")
    
    # Service
    service_category: str = Field(..., description="Service category")
    
    # Dates
    created_date: date = Field(..., description="Created date")
    status: ReferralStatus = Field(..., description="Status")
    expiration_date: Optional[date] = Field(None, description="Expiration date")

