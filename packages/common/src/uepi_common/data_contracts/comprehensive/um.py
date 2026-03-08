"""
H. Utilization Management Operations (UM)
Comprehensive canonical models for prior authorization, concurrent review, and appeals
"""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

from uepi_common.data_contracts.canonical_base import CanonicalBase


class PADecision(str, Enum):
    """Prior authorization decision"""
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    PARTIAL = "PARTIAL"
    PENDED = "PENDED"


class AppealOutcome(str, Enum):
    """Appeal outcome"""
    UPHELD = "UPHELD"
    OVERTURNED = "OVERTURNED"
    PARTIAL = "PARTIAL"
    WITHDRAWN = "WITHDRAWN"
    PENDING = "PENDING"


# H1) Prior Authorization Requests (Must for "friction realism")
# Grain: pa_request_id
class PriorAuthorizationRequest(CanonicalBase):
    """Prior Authorization Request - comprehensive PA tracking"""
    
    # Primary Key
    pa_request_id: str = Field(..., description="Prior authorization request identifier")
    
    # Member & Provider
    member_id: str = Field(..., description="Member identifier")
    requesting_provider_id: str = Field(..., description="Requesting provider identifier")
    
    # Service Requested
    service_codes: List[str] = Field(..., description="Service code(s)")
    code_type: str = Field(..., description="Code type (CPT/HCPCS)")
    requested_units: Optional[Decimal] = Field(None, ge=0, description="Requested units")
    
    # Dates
    request_date: date = Field(..., description="Request date")
    decision_date: Optional[date] = Field(None, description="Decision date")
    
    # Decision
    decision: PADecision = Field(..., description="Decision (approved/denied/partial/pended)")
    denial_reason_codes: Optional[List[str]] = Field(None, description="Denial reason code(s)")
    
    # Processing
    turnaround_time_days: Optional[int] = Field(None, ge=0, description="Turnaround time (days)")
    peer_to_peer_flag: Optional[bool] = Field(None, description="Peer-to-peer flag")
    expedited_flag: Optional[bool] = Field(None, description="Expedited flag")
    
    # Site of Care
    site_of_care_requested: Optional[str] = Field(None, description="Site of care requested")
    site_of_care_authorized: Optional[str] = Field(None, description="Site of care authorized")
    
    # Authorization Period
    auth_valid_from: Optional[date] = Field(None, description="Authorization valid from date")
    auth_valid_to: Optional[date] = Field(None, description="Authorization valid to date")
    auth_number: Optional[str] = Field(None, description="Authorization number")
    
    # Linked Claims
    linked_claim_ids: Optional[List[str]] = Field(None, description="Linked claim identifier(s)")


# H2) Concurrent Review / Case Review (Optional)
class ConcurrentReview(CanonicalBase):
    """Concurrent Review - admission review and length-of-stay approvals"""
    
    # Primary Key
    review_id: str = Field(..., description="Review identifier")
    
    # Member & Claim
    member_id: str = Field(..., description="Member identifier")
    claim_id: Optional[str] = Field(None, description="Claim identifier")
    
    # Review Type
    review_type: str = Field(..., description="Review type (admission/length_of_stay)")
    review_date: date = Field(..., description="Review date")
    
    # Approval
    approved_flag: Optional[bool] = Field(None, description="Approved flag")
    approved_days: Optional[int] = Field(None, ge=0, description="Approved days")
    denial_reason: Optional[str] = Field(None, description="Denial reason")


# H3) Appeals & Grievances
# Grain: appeal_id
class AppealGrievance(CanonicalBase):
    """Appeal & Grievance - appeals and grievances tracking"""
    
    # Primary Key
    appeal_id: str = Field(..., description="Appeal identifier")
    
    # Related Records
    related_pa_id: Optional[str] = Field(None, description="Related prior authorization identifier")
    related_claim_id: Optional[str] = Field(None, description="Related claim identifier")
    
    # Member
    member_id: str = Field(..., description="Member identifier")
    
    # Dates
    filed_date: date = Field(..., description="Filed date")
    resolved_date: Optional[date] = Field(None, description="Resolved date")
    
    # Outcome
    outcome: AppealOutcome = Field(..., description="Outcome")
    overturn_flag: Optional[bool] = Field(None, description="Overturn flag")
    reason_categories: Optional[List[str]] = Field(None, description="Reason categories")
    external_review_flag: Optional[bool] = Field(None, description="External review flag")

