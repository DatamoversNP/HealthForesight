"""
J. Clinical Programs & Care Management
Comprehensive canonical model for care management enrollment
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field

from uepi_common.data_contracts.canonical_base import CanonicalBase


# J1) Care Management Enrollment
class CareManagementEnrollment(CanonicalBase):
    """Care Management Enrollment - care management program enrollment"""
    
    # Primary Key
    enrollment_id: str = Field(..., description="Enrollment identifier")
    member_id: str = Field(..., description="Member identifier")
    program_id: str = Field(..., description="Program identifier")
    
    # Enrollment Period
    start_date: date = Field(..., description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    
    # Interventions
    interventions_logged: Optional[int] = Field(None, ge=0, description="Interventions logged count")
    outreach_counts: Optional[int] = Field(None, ge=0, description="Outreach counts")

