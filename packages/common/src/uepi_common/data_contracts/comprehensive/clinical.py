"""
C. Clinical Condition Domain
Comprehensive canonical models for diagnoses and problem lists
"""
from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from uepi_common.data_contracts.canonical_base import CanonicalBase


class DiagnosisSource(str, Enum):
    """Diagnosis source"""
    CLAIMS = "CLAIMS"
    EHR = "EHR"
    REGISTRY = "REGISTRY"


class ConditionStatus(str, Enum):
    """Condition status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    RESOLVED = "RESOLVED"


# C1) Diagnoses (Member Condition History)
# Grain: member_id × dx_code × onset_date
class MemberDiagnosis(CanonicalBase):
    """Member Diagnosis - diagnosis history"""
    
    # Primary Keys
    member_id: str = Field(..., description="Member identifier")
    icd10_code: str = Field(..., description="ICD-10 code")
    onset_date: date = Field(..., description="Onset date")
    
    # Diagnosis Information
    dx_description: Optional[str] = Field(None, description="Diagnosis description")
    dx_group: Optional[str] = Field(None, description="Diagnosis group (CCS/HCC group)")
    resolved_date: Optional[date] = Field(None, description="Resolved date")
    chronic_flag: Optional[bool] = Field(None, description="Chronic flag")
    source: Optional[DiagnosisSource] = Field(None, description="Source (claims, EHR, registry)")
    severity_stage: Optional[str] = Field(None, description="Severity stage (if known)")


# C2) Problem List / Registry (Optional)
class ProblemList(CanonicalBase):
    """Problem List - problem list and registry"""
    
    # Primary Key
    problem_id: str = Field(..., description="Problem identifier")
    member_id: str = Field(..., description="Member identifier")
    
    # Condition
    condition_registry_id: Optional[str] = Field(None, description="Condition registry identifier")
    condition_status: ConditionStatus = Field(..., description="Condition status (active/inactive)")
    icd10_code: Optional[str] = Field(None, description="ICD-10 code")
    
    # Attribution
    attribution_provider_id: Optional[str] = Field(None, description="Attribution provider identifier")
    attribution_date: Optional[date] = Field(None, description="Attribution date")

