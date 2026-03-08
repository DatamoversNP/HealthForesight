"""
PolicyLogic Schema
Canonical structure for representing policies with support for standalone and composite (multi-lever) policies
"""
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, date
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from .policy_metadata import LeverType, ConditionType, ExceptionType


class EnforcementLevel(str, Enum):
    """Enforcement level for policy levers"""
    HARD = "HARD"  # Strictly enforced
    SOFT = "SOFT"  # Advisory/warning
    MONITOR = "MONITOR"  # Monitoring only


class PolicyScope(BaseModel):
    """Scope definition for a policy - applies to all levers unless overridden"""
    line_of_business: List[str] = Field(default_factory=list, description="Lines of business (Commercial, MA, Medicaid, etc.)")
    markets: List[str] = Field(default_factory=list, description="Geographic markets")
    network_id: Optional[str] = Field(None, description="Network identifier")
    network_tier: Optional[str] = Field(None, description="Network tier")
    member_segments: List[str] = Field(default_factory=list, description="Member segments")
    provider_groups: List[str] = Field(default_factory=list, description="Provider groups")
    service_categories: List[str] = Field(default_factory=list, description="Service categories")


class ConditionRule(BaseModel):
    """A condition rule with AND/OR logic"""
    type: ConditionType = Field(..., description="Condition type")
    operator: str = Field("equals", description="Operator (equals, in, not_in, greater_than, less_than)")
    value: Union[str, int, float, List[Any]] = Field(..., description="Condition value")
    description: Optional[str] = Field(None, description="Human-readable description")


class ConditionGroup(BaseModel):
    """Group of conditions with AND/OR logic"""
    logic: str = Field("AND", description="Logic operator (AND, OR)")
    conditions: List[Union[ConditionRule, "ConditionGroup"]] = Field(default_factory=list, description="Conditions or nested groups")


class ExceptionRule(BaseModel):
    """An exception rule"""
    type: ExceptionType = Field(..., description="Exception type")
    operator: str = Field("equals", description="Operator")
    value: Union[str, int, float, List[Any]] = Field(..., description="Exception value")
    description: Optional[str] = Field(None, description="Human-readable description")


class ExceptionGroup(BaseModel):
    """Group of exceptions with AND/OR logic"""
    logic: str = Field("OR", description="Logic operator (AND, OR)")
    exceptions: List[Union[ExceptionRule, "ExceptionGroup"]] = Field(default_factory=list, description="Exceptions or nested groups")


class PolicyLever(BaseModel):
    """A single policy lever (atomic control)"""
    lever_id: UUID = Field(default_factory=UUID, description="Unique lever identifier")
    lever_type: LeverType = Field(..., description="Type of lever")
    name: str = Field(..., description="Lever name/description")
    
    # Lever-specific parameters (dynamic based on lever_type)
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Lever-specific parameters")
    
    # Conditions (when this lever applies)
    conditions: Optional[ConditionGroup] = Field(None, description="Conditions for this lever")
    
    # Exceptions (when this lever does NOT apply)
    exceptions: Optional[ExceptionGroup] = Field(None, description="Exceptions for this lever")
    
    # Override scope (if different from policy scope)
    scope_override: Optional[PolicyScope] = Field(None, description="Scope override for this lever")
    
    # Metadata
    enabled: bool = Field(True, description="Whether lever is enabled")
    priority: int = Field(0, description="Priority order (lower = higher priority)")
    notes: Optional[str] = Field(None, description="Notes about this lever")


class PolicyVersion(BaseModel):
    """A versioned snapshot of a policy"""
    version_id: UUID = Field(default_factory=UUID, description="Version identifier")
    version_number: str = Field(..., description="Version number (e.g., '1.0', '2.1')")
    effective_date: date = Field(..., description="Effective start date")
    expiration_date: Optional[date] = Field(None, description="Expiration date (None = active)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    created_by: str = Field(..., description="Creator identifier")
    change_description: Optional[str] = Field(None, description="Description of changes in this version")
    
    # Policy content at this version
    policy_logic: "PolicyLogic" = Field(..., description="Policy logic at this version")
    
    # Status
    status: str = Field("DRAFT", description="Status (DRAFT, ACTIVE, RETIRED)")
    
    # Approval workflow
    approved_by: Optional[str] = Field(None, description="Approver identifier")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")


class PolicyLogic(BaseModel):
    """Canonical policy logic structure - supports standalone and composite policies"""
    # Policy container metadata
    policy_id: UUID = Field(default_factory=UUID, description="Policy identifier")
    policy_name: str = Field(..., description="Policy name")
    policy_description: Optional[str] = Field(None, description="Policy description")
    policy_owner: str = Field(..., description="Policy owner/team")
    policy_category: str = Field("UTILIZATION", description="Policy category")
    
    # Scope (applies to all levers unless overridden)
    scope: PolicyScope = Field(..., description="Policy scope")
    
    # Levers (one or more - supports both standalone and composite)
    levers: List[PolicyLever] = Field(default_factory=list, description="Policy levers")
    
    # Global conditions (apply to all levers)
    global_conditions: Optional[ConditionGroup] = Field(None, description="Global conditions")
    
    # Global exceptions (apply to all levers)
    global_exceptions: Optional[ExceptionGroup] = Field(None, description="Global exceptions")
    
    # Effective period
    effective_start: date = Field(..., description="Effective start date")
    effective_end: Optional[date] = Field(None, description="Effective end date")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Analytics readiness
    analytics_ready: bool = Field(False, description="Whether policy is ready for analytics")
    readiness_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Readiness score (0-1)")
    readiness_issues: List[str] = Field(default_factory=list, description="Readiness issues")
    
    @field_validator('levers')
    @classmethod
    def validate_levers(cls, v: List[PolicyLever]) -> List[PolicyLever]:
        """Validate that policy has at least one lever"""
        if not v:
            raise ValueError("Policy must have at least one lever")
        return v
    
    def is_standalone(self) -> bool:
        """Check if this is a standalone policy (single lever)"""
        return len(self.levers) == 1
    
    def is_composite(self) -> bool:
        """Check if this is a composite policy (multiple levers)"""
        return len(self.levers) > 1
    
    def get_lever_by_type(self, lever_type: LeverType) -> List[PolicyLever]:
        """Get all levers of a specific type"""
        return [lever for lever in self.levers if lever.lever_type == lever_type]
    
    def get_human_readable_summary(self) -> str:
        """Generate human-readable policy summary"""
        lines = [f"Policy: {self.policy_name}"]
        lines.append(f"Scope: {', '.join(self.scope.line_of_business) if self.scope.line_of_business else 'All LOBs'}")
        lines.append(f"Effective: {self.effective_start} to {self.effective_end or 'Ongoing'}")
        lines.append(f"Levers ({len(self.levers)}):")
        for lever in self.levers:
            lines.append(f"  - {lever.lever_type.value}: {lever.name}")
        return "\n".join(lines)


# Update forward references
ConditionGroup.model_rebuild()
ExceptionGroup.model_rebuild()
PolicyVersion.model_rebuild()

