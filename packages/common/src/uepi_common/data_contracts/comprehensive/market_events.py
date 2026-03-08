"""
L. External Context & Confounders
Comprehensive canonical model for market events
"""
from datetime import date
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

from uepi_common.data_contracts.canonical_base import CanonicalBase


class MarketEventType(str, Enum):
    """Market event type"""
    CPT_FEE_SCHEDULE_CHANGE = "CPT_FEE_SCHEDULE_CHANGE"
    PROVIDER_ACQUISITION = "PROVIDER_ACQUISITION"
    HOSPITAL_CLOSURE = "HOSPITAL_CLOSURE"
    PUBLIC_HEALTH_EVENT = "PUBLIC_HEALTH_EVENT"
    NETWORK_CHANGE = "NETWORK_CHANGE"
    OTHER = "OTHER"


# L1) Market Events
class MarketEvent(CanonicalBase):
    """Market Event - external context and confounders"""
    
    # Primary Key
    event_id: str = Field(..., description="Event identifier")
    
    # Event Classification
    event_type: MarketEventType = Field(..., description="Event type")
    event_date: date = Field(..., description="Event date")
    description: Optional[str] = Field(None, description="Event description")
    
    # Affected Entities
    affected_markets: Optional[List[str]] = Field(None, description="Affected markets")
    affected_providers: Optional[List[str]] = Field(None, description="Affected provider identifiers")
    affected_facilities: Optional[List[str]] = Field(None, description="Affected facility identifiers")

