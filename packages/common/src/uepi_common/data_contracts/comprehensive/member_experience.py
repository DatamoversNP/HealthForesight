"""
K. Member Experience / Contact Center
Comprehensive canonical model for call center contacts and complaints
"""
from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from uepi_common.data_contracts.canonical_base import CanonicalBase


class ContactTopic(str, Enum):
    """Contact topic"""
    PRIOR_AUTH = "PRIOR_AUTH"
    BILLING = "BILLING"
    ACCESS = "ACCESS"
    BENEFITS = "BENEFITS"
    CLAIMS = "CLAIMS"
    OTHER = "OTHER"


class Sentiment(str, Enum):
    """Sentiment"""
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


# K1) Call Center / Complaints
class CallCenterContact(CanonicalBase):
    """Call Center Contact - member contact and complaint tracking"""
    
    # Primary Key
    contact_id: str = Field(..., description="Contact identifier")
    member_id: str = Field(..., description="Member identifier")
    
    # Contact Information
    contact_date: date = Field(..., description="Contact date")
    topic: ContactTopic = Field(..., description="Topic (PA, billing, access)")
    sentiment: Optional[Sentiment] = Field(None, description="Sentiment")
    escalation: Optional[bool] = Field(None, description="Escalation flag")
    resolution: Optional[str] = Field(None, description="Resolution")

