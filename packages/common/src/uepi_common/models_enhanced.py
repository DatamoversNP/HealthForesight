"""Enhanced data models for enterprise product uplift"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional, List, Dict
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ============================================================================
# Epic 1: Role-Based Experience
# ============================================================================

class PersonaRole(str, Enum):
    """Persona roles for role-based dashboards"""
    EXECUTIVE = "EXECUTIVE"  # CFO/Actuary/CMO
    POLICY_OWNER = "POLICY_OWNER"
    ANALYST = "ANALYST"
    OPS_CLINICAL = "OPS_CLINICAL"


class ResourceType(str, Enum):
    """Resource types for RBAC"""
    POLICY = "POLICY"
    ANALYSIS = "ANALYSIS"
    DECISION = "DECISION"
    DATASET = "DATASET"
    MODEL = "MODEL"
    EXPORT = "EXPORT"
    SCORECARD = "SCORECARD"
    COHORT = "COHORT"


class ActionType(str, Enum):
    """Action types for permissions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    EXPORT = "export"
    EXECUTE = "execute"


class ResourceScope(BaseModel):
    """Resource-level access scope"""
    resource_type: ResourceType
    resource_id: Optional[UUID] = None  # None = all resources of this type
    tenant_id: UUID
    restrictions: Optional[Dict[str, Any]] = None  # e.g., {"lob": ["COMMERCIAL"]}


class Permission(BaseModel):
    """Permission definition"""
    resource: ResourceType
    actions: List[ActionType]
    scope: Optional[ResourceScope] = None


class Role(BaseModel):
    """Role definition"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    persona: Optional[PersonaRole] = None  # Maps to persona dashboard
    permissions: List[Permission]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserRole(BaseModel):
    """User role assignment"""
    user_id: UUID
    role_id: UUID
    resource_scopes: Optional[List[ResourceScope]] = None  # Additional scoping
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: UUID


# ============================================================================
# Epic 2: Policy Lifecycle Management
# ============================================================================

class PolicyLifecycleState(str, Enum):
    """Enhanced policy lifecycle states"""
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    MONITORING = "MONITORING"
    ITERATING = "ITERATING"
    SUNSET = "SUNSET"


class PolicyObjective(BaseModel):
    """Policy objective"""
    cost_target: Optional[float] = None
    access_constraints: Optional[List[str]] = None
    quality_guardrails: Optional[List[str]] = None
    utilization_targets: Optional[Dict[str, float]] = None


class ElasticityRange(BaseModel):
    """Elasticity assumption range"""
    min_value: float
    max_value: float
    best_estimate: float
    confidence_level: float = 0.95  # 95% confidence


class PolicyAssumption(BaseModel):
    """Policy assumption"""
    assumption_type: str  # "elasticity", "substitution", "lag", etc.
    description: str
    range: Optional[ElasticityRange] = None
    # Seeds and DB store human-readable ranges ("0.10-0.15", "TBD"), not only floats.
    value: Optional[float | str] = None
    source: Optional[str] = None  # Where assumption came from
    confidence: float = 0.5  # 0-1 confidence score


class PolicyGuardrail(BaseModel):
    """Policy guardrail/rollback trigger"""
    metric_name: str
    threshold_type: str  # "max", "min", "change_pct"
    threshold_value: float
    action: str  # "alert", "suspend", "rollback"
    description: str


class PolicyVersion(BaseModel):
    """Policy version with change tracking"""
    version_number: int
    policy_id: UUID
    effective_start_date: datetime
    effective_end_date: Optional[datetime] = None
    state: PolicyLifecycleState
    change_summary: str
    change_details: Dict[str, Any]  # What changed
    created_by: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None


class PolicyChangeLog(BaseModel):
    """Change log entry for policy"""
    change_id: UUID = Field(default_factory=uuid4)
    policy_id: UUID
    version_number: int
    changed_by: UUID
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    change_type: str  # "created", "updated", "state_change", "assumption_change"
    field_name: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    reason: Optional[str] = None


# ============================================================================
# Epic 3: Decision Audit & Defensibility
# ============================================================================

class ConfidenceInterval(BaseModel):
    """Confidence interval for uncertainty"""
    lower_bound: float
    upper_bound: float
    confidence_level: float = 0.95
    distribution_type: Optional[str] = None  # "normal", "lognormal", etc.


class UncertaintyRange(BaseModel):
    """Uncertainty range (P10/P50/P90)"""
    p10: float
    p50: float
    p90: float
    mean: Optional[float] = None
    std_dev: Optional[float] = None


class EvidenceLink(BaseModel):
    """Link to evidence supporting decision"""
    evidence_type: str  # "analysis", "dataset", "model", "baseline"
    evidence_id: UUID
    evidence_version: Optional[str] = None
    snapshot_hash: Optional[str] = None  # For reproducibility
    description: Optional[str] = None


class Decision(BaseModel):
    """Decision record with full audit trail"""
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    title: str
    recommendation: str
    rationale: str
    confidence_score: float  # 0-1
    uncertainty_range: Optional[UncertaintyRange] = None
    confidence_interval: Optional[ConfidenceInterval] = None
    
    # Links
    policy_id: Optional[UUID] = None
    policy_version_id: Optional[UUID] = None
    analysis_ids: List[UUID] = []
    evidence_links: List[EvidenceLink] = []
    
    # Assumptions snapshot
    assumptions_snapshot: Dict[str, Any]  # Frozen assumptions at decision time
    
    # Approvals
    approvals: List[Dict[str, Any]] = []  # [{user_id, role, approved_at, comment}]
    status: str = "DRAFT"  # DRAFT, PENDING_APPROVAL, APPROVED, FINAL
    
    # Metadata
    created_by: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    finalized_at: Optional[datetime] = None
    finalized_by: Optional[UUID] = None


class AuditTrailEntry(BaseModel):
    """Audit trail entry"""
    entry_id: UUID = Field(default_factory=uuid4)
    decision_id: UUID
    step_type: str  # "data_ingestion", "transformation", "analysis", "model", "decision", "export"
    step_id: UUID
    step_version: Optional[str] = None
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    performed_by: Optional[UUID] = None


# ============================================================================
# Epic 4: Uncertainty & Risk Visualization
# ============================================================================

class ForecastDistribution(BaseModel):
    """Forecast with distribution"""
    forecast_id: UUID = Field(default_factory=uuid4)
    metric_name: str
    point_estimate: float
    uncertainty_range: UncertaintyRange
    confidence_interval: ConfidenceInterval
    distribution_data: Optional[Dict[str, Any]] = None  # Full distribution if available
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SensitivityParameter(BaseModel):
    """Sensitivity analysis parameter"""
    parameter_name: str
    base_value: float
    min_value: float
    max_value: float
    step_size: Optional[float] = None


class ScenarioRun(BaseModel):
    """Scenario run with sensitivity"""
    scenario_id: UUID = Field(default_factory=uuid4)
    scenario_name: str
    parameters: Dict[str, float]  # Parameter values used
    sensitivity_parameters: List[SensitivityParameter]
    results: Dict[str, ForecastDistribution]  # Metric -> distribution
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RiskDriver(BaseModel):
    """Uncertainty driver for risk register"""
    driver_name: str
    impact_score: float  # 0-1
    uncertainty_contribution: float  # How much this driver contributes to uncertainty
    mitigation_action: Optional[str] = None
    owner: Optional[UUID] = None


class RiskRegister(BaseModel):
    """Risk register for policy"""
    policy_id: UUID
    top_drivers: List[RiskDriver]  # Top 5 uncertainty drivers
    overall_risk_score: float  # 0-1
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Epic 5: Behavioral Signal Detection
# ============================================================================

class BehaviorType(str, Enum):
    """Provider behavior types"""
    COMPLIANCE = "COMPLIANCE"
    ADAPTATION = "ADAPTATION"
    RESISTANCE = "RESISTANCE"
    CIRCUMVENTION = "CIRCUMVENTION"
    NEUTRAL = "NEUTRAL"


class SignalMetric(BaseModel):
    """Behavioral signal metric"""
    metric_name: str
    metric_type: str  # "appeals_volume", "denial_rate", "site_shift", "coding_change", "lag_pattern"
    value: float
    baseline_value: float
    change_pct: float
    significance: float  # Statistical significance
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class ProviderBehaviorProfile(BaseModel):
    """Provider behavior profile"""
    provider_id: str
    provider_name: Optional[str] = None
    behavior_type: BehaviorType
    confidence: float  # 0-1
    signals: List[SignalMetric]
    policy_version_id: Optional[UUID] = None  # Which policy version triggered this
    first_detected: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class BehaviorCluster(BaseModel):
    """Cluster of providers with similar behavior"""
    cluster_id: UUID = Field(default_factory=uuid4)
    cluster_name: str
    behavior_type: BehaviorType
    provider_ids: List[str]
    cluster_characteristics: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AlertRule(BaseModel):
    """Alert rule for behavior signals"""
    rule_id: UUID = Field(default_factory=uuid4)
    rule_name: str
    signal_type: str
    threshold: float
    condition: str  # "greater_than", "less_than", "change_pct"
    action: str  # "notify", "escalate", "suspend_policy"
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AlertEvent(BaseModel):
    """Alert event"""
    alert_id: UUID = Field(default_factory=uuid4)
    rule_id: UUID
    policy_id: Optional[UUID] = None
    provider_id: Optional[str] = None
    signal_value: float
    threshold: float
    severity: str  # "low", "medium", "high", "critical"
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_by: Optional[UUID] = None
    acknowledged_at: Optional[datetime] = None


# ============================================================================
# Epic 6: Collaboration Workflows
# ============================================================================

class Comment(BaseModel):
    """Comment on policy/analysis/decision"""
    comment_id: UUID = Field(default_factory=uuid4)
    resource_type: ResourceType
    resource_id: UUID
    user_id: UUID
    content: str
    mentions: List[UUID] = []  # @mentioned user IDs
    parent_comment_id: Optional[UUID] = None  # For threaded comments
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Task(BaseModel):
    """Task assignment"""
    task_id: UUID = Field(default_factory=uuid4)
    resource_type: ResourceType
    resource_id: UUID
    title: str
    description: str
    assigned_to: UUID
    assigned_by: UUID
    due_date: Optional[datetime] = None
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ApprovalRequest(BaseModel):
    """Approval request"""
    request_id: UUID = Field(default_factory=uuid4)
    resource_type: ResourceType
    resource_id: UUID
    requested_by: UUID
    requested_for: List[UUID]  # Users/roles who need to approve
    required_approvals: int  # How many approvals needed
    current_approvals: int = 0
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, CANCELLED
    comments: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ActivityEvent(BaseModel):
    """Activity log event"""
    event_id: UUID = Field(default_factory=uuid4)
    resource_type: ResourceType
    resource_id: UUID
    event_type: str  # "created", "updated", "commented", "approved", "state_changed"
    user_id: UUID
    description: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Epic 7: Executive Narrative Layer
# ============================================================================

class NarrativeMode(BaseModel):
    """Narrative mode output"""
    narrative_id: UUID = Field(default_factory=uuid4)
    resource_type: ResourceType
    resource_id: UUID
    executive_summary: str
    key_findings: List[str]  # Top 3 findings
    risks: List[Dict[str, str]]  # [{risk: "...", mitigation: "..."}]
    recommended_action: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: UUID


class ExportTemplate(BaseModel):
    """Export template"""
    template_type: str  # "board_pack", "regulator_pack", "provider_pack"
    title: str
    sections: List[Dict[str, Any]]
    chart_configs: List[Dict[str, Any]]
    assumptions_included: bool = True
    audit_trail_included: bool = True


class ExportPack(BaseModel):
    """Generated export pack"""
    export_id: UUID = Field(default_factory=uuid4)
    template_type: str
    resource_id: UUID
    resource_type: ResourceType
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: UUID
    file_path: Optional[str] = None  # Path to generated file
    file_hash: Optional[str] = None  # For integrity verification


