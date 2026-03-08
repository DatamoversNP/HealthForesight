"""Shared data models"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TenantRole(str, Enum):
    """User roles"""
    POLICY_ADMIN = "POLICY_ADMIN"
    UM_LEADER = "UM_LEADER"
    ACTUARIAL = "ACTUARIAL"
    STRATEGY = "STRATEGY"
    COMPLIANCE = "COMPLIANCE"
    EXEC_VIEWER = "EXEC_VIEWER"


class PolicyType(str, Enum):
    """Policy types - Comprehensive real-world taxonomy
    
    Tier 1: Core Utilization Controls (Primary UI options)
    Tier 2: Utilization Management Extensions
    Tier 3: Network & Provider-Based Controls
    Tier 4: Financial & Incentive-Based Policies
    Tier 5: Administrative & Access Controls
    """
    # Tier 1: Core Utilization Controls (Primary - default view)
    PRIOR_AUTH = "PRIOR_AUTH"  # Prior Authorization
    SITE_OF_CARE = "SITE_OF_CARE"
    COVERAGE = "COVERAGE"
    STEP_THERAPY = "STEP_THERAPY"
    BENEFIT = "BENEFIT"
    
    # Tier 2: Utilization Management Extensions (Advanced - expandable)
    CLINICAL_CRITERIA = "CLINICAL_CRITERIA"  # Medical necessity, MCG/InterQual
    DURATION_FREQUENCY_LIMIT = "DURATION_FREQUENCY_LIMIT"  # Visit limits, time-based restrictions
    QUANTITY_LIMIT = "QUANTITY_LIMIT"  # Units per day/episode, dose limits
    
    # Tier 3: Network & Provider-Based Controls
    NETWORK_RESTRICTION = "NETWORK_RESTRICTION"  # In/out-of-network rules, tiered networks
    PROVIDER_ELIGIBILITY = "PROVIDER_ELIGIBILITY"  # Provider type restrictions
    REFERRAL_REQUIREMENT = "REFERRAL_REQUIREMENT"  # PCP referral, gatekeeping
    
    # Tier 4: Financial & Incentive-Based Policies
    COST_SHARING = "COST_SHARING"  # Copay/coinsurance changes
    PAYMENT_POLICY = "PAYMENT_POLICY"  # Reimbursement caps, bundled payments
    
    # Tier 5: Administrative & Access Controls (Optional)
    ADMINISTRATIVE_REQUIREMENT = "ADMINISTRATIVE_REQUIREMENT"  # Documentation, attestation
    ACCESS_AVAILABILITY_RULE = "ACCESS_AVAILABILITY_RULE"  # Time-to-service, availability constraints
    
    # Composite type for compound policies
    COMPOSITE = "COMPOSITE"  # Multiple levers (e.g., PA + frequency limit)
    
    # Legacy aliases for backward compatibility
    PA = "PRIOR_AUTH"  # Alias for PRIOR_AUTH
    FREQUENCY_LIMIT = "FREQUENCY_LIMIT"  # Alias for DURATION_FREQUENCY_LIMIT (DB/seed data)


class LineOfBusiness(str, Enum):
    """Lines of business"""
    COMMERCIAL = "COMMERCIAL"
    MA = "MA"  # Medicare Advantage
    MEDICARE = "MEDICARE"  # Traditional Medicare
    MEDICAID = "MEDICAID"


class ChangeType(str, Enum):
    """Policy change types"""
    NEW = "NEW"
    TIGHTEN = "TIGHTEN"
    RELAX = "RELAX"
    RETIRE = "RETIRE"


class EnforcementStrength(str, Enum):
    """Policy enforcement strength"""
    SOFT = "SOFT"
    HARD = "HARD"
    PASSIVE = "PASSIVE"  # Policy enforced passively (e.g., benefit accumulator)


class EnforcementMechanism(str, Enum):
    """How policy is enforced"""
    HARD = "HARD"  # Blocked at claim edit / PA workflow
    SOFT = "SOFT"  # Warnings, may be overridden
    PASSIVE = "PASSIVE"  # Applied via benefit accumulator, no blocking


class PolicyTouchpoint(str, Enum):
    """Where policy is enforced"""
    CLAIM_EDIT = "CLAIM_EDIT"  # Applied during claims processing
    PA_WORKFLOW = "PA_WORKFLOW"  # Applied in prior auth workflow
    BENEFIT_ACCUMULATOR = "BENEFIT_ACCUMULATOR"  # Applied via benefit accumulator
    PRECERT = "PRECERT"  # Applied during precertification
    AUTHORIZATION = "AUTHORIZATION"  # Authorization / UM workflow
    CARE_MANAGEMENT = "CARE_MANAGEMENT"  # Care management touchpoint


class PolicyStatus(str, Enum):
    """Policy lifecycle status"""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"
    SUSPENDED = "SUSPENDED"


class CodeType(str, Enum):
    """Code types for policy code sets"""
    CPT = "CPT"
    HCPCS = "HCPCS"
    DRG = "DRG"
    REV = "REV"  # Revenue code


class BaseEntity(BaseModel):
    """Base entity with common fields"""
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FilterSpec(BaseModel):
    """Canonical filter specification for cohorts and analyses"""
    lob: Optional[list[LineOfBusiness]] = None
    markets: Optional[list[str]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    pre_window_months: Optional[int] = None
    post_window_months: Optional[int] = None
    in_network_only: Optional[bool] = None
    member_risk_bands: Optional[list[str]] = None
    provider_specialties: Optional[list[str]] = None
    facility_only: Optional[bool] = None
    code_groups: Optional[list[str]] = None
    cpt_codes: Optional[list[str]] = None
    hcpcs_codes: Optional[list[str]] = None
    
    class Config:
        use_enum_values = True


class PolicyScope(BaseModel):
    """
    Policy scope - FIRST-CLASS concept defining who/what is affected.
    
    In real payer operations, policies are ALWAYS selectively scoped, not universal.
    This scope defines the population, geography, plans, and high-level filters.
    
    Detailed service/provider/site/clinical filters are in PolicyLever.targets,
    PolicyLever.apply_when (conditions), and PolicyLever.exceptions.
    """
    # Population dimensions
    lob: Optional[list[LineOfBusiness]] = None  # ["COMMERCIAL", "MA", "MEDICAID"] or None = all
    markets: Optional[list[str]] = None  # ["NYC", "DFW", "BOS"] or ["ALL"] or None = all
    plans: Optional[list[str]] = None  # Plan/product IDs or names (HMO, PPO, Exchange, etc.)
    product_types: Optional[list[str]] = None  # ["HMO", "PPO", "POS", "EXCHANGE"]
    
    # Geography (if markets isn't sufficient)
    states: Optional[list[str]] = None  # State codes if needed beyond markets
    regions: Optional[list[str]] = None  # Geographic regions
    
    # Network restrictions
    network: Optional[list[str]] = None  # ["IN"] = in-network only, ["OUT"] = OON allowed, None = all
    network_tiers: Optional[list[str]] = None  # ["TIER1", "TIER2"] for tiered networks
    
    # Member attribute filters (high-level - detailed ones in lever conditions)
    member_age_min: Optional[int] = None  # e.g., 18 (age >= 18)
    member_age_max: Optional[int] = None  # e.g., 65 (age <= 65)
    exclude_pregnant: Optional[bool] = None  # True = exclude pregnant members
    gender_filters: Optional[list[str]] = None  # ["M", "F"] or None = all
    
    # Provider filters (high-level - detailed ones in lever configs)
    exclude_centers_of_excellence: Optional[bool] = None  # True = exclude COEs
    include_provider_types: Optional[list[str]] = None  # ["FACILITY", "PHYSICIAN", "ASC"]
    exclude_provider_types: Optional[list[str]] = None
    provider_specialties: Optional[list[str]] = None  # Include only these specialties
    
    # Site of care filters (high-level - detailed ones in SiteOfCareLeverConfig)
    exclude_er: Optional[bool] = None  # True = exclude ER
    exclude_hospital_op: Optional[bool] = None  # True = exclude HOPD
    allowed_sites: Optional[list[str]] = None  # ["OFFICE", "FREESTANDING", "ASC"]
    
    # Explicit "all population" flag (for benefit design policies)
    applies_to_all: bool = False  # True = explicit "all population" policy (benefit design)


class EffectivePeriod(BaseModel):
    """Policy effective period"""
    start_date: datetime
    end_date: Optional[datetime] = None


class Enforcement(BaseModel):
    """Policy enforcement configuration"""
    mechanism: EnforcementMechanism
    touchpoint: list[PolicyTouchpoint]
    override_allowed: bool = False


class PolicyLever(BaseModel):
    """Flexible policy lever - supports all lever types via parameters"""
    lever_type: PolicyType
    parameters: dict[str, Any] = Field(default_factory=dict)
    # Examples:
    # PRIOR_AUTH: {"codes": ["72148"], "site_of_care": "OUTPATIENT"}
    # FREQUENCY_LIMIT: {"codes": ["97110"], "max_visits": 20, "time_period": "YEAR"}
    # COST_SHARING: {"service_category": "URGENT_CARE", "copay_change": {"from": 40, "to": 75}}


class Condition(BaseModel):
    """Policy condition (IF statement)"""
    field: str  # e.g., "place_of_service", "age", "diagnosis"
    operator: str  # "IN", "EQUALS", "GREATER_THAN", "LESS_THAN", "CONTAINS", "NOT_IN"
    value: Any  # Single value or list depending on operator


class Exception(BaseModel):
    """Policy exception (do not apply when)"""
    field: str
    operator: str
    value: Any
    description: Optional[str] = None  # Human-readable explanation


class RuleGroup(BaseModel):
    """Group of conditions combined with AND"""
    conditions: list[Condition] = Field(default_factory=list)
    operator: str = "AND"  # AND or OR within group


class LeverTargets(BaseModel):
    """Target codes/services for a lever"""
    code_type: str  # "CPT", "HCPCS", "DRG", "REVENUE"
    codes: list[str] = Field(default_factory=list)
    code_groups: Optional[list[str]] = None  # Pre-defined code groups
    all_codes_in_category: Optional[bool] = False  # Apply to all codes in category


class PriorAuthLeverConfig(BaseModel):
    """Prior Authorization lever configuration"""
    requires_pa: bool = True
    pa_touchpoint: str = "PA_WORKFLOW"  # Where PA is applied
    override_allowed: bool = False
    auto_approve_conditions: Optional[list[Condition]] = None  # When to auto-approve


class SiteOfCareLeverConfig(BaseModel):
    """Site of Care lever configuration"""
    allowed_sites: list[str] = Field(default_factory=list)  # ["OFFICE", "FREESTANDING"]
    disallowed_sites: list[str] = Field(default_factory=list)  # ["HOSPITAL_OP", "ER"]
    redirect_to: Optional[str] = None  # Preferred site if disallowed
    deny_if_disallowed: bool = True  # Deny or redirect?


class FrequencyLimitLeverConfig(BaseModel):
    """Frequency/Duration Limit lever configuration"""
    max_visits: Optional[int] = None
    max_units: Optional[float] = None
    time_period: str = "YEAR"  # "YEAR", "QUARTER", "MONTH", "LIFETIME"
    reset_date: Optional[str] = None  # Calendar year vs rolling
    accumulate_across_providers: bool = False


class QuantityLimitLeverConfig(BaseModel):
    """Quantity Limit lever configuration"""
    max_units_per_day: Optional[float] = None
    max_units_per_episode: Optional[float] = None
    max_units_per_visit: Optional[float] = None
    dosage_limit: Optional[float] = None  # For pharmacy-like services


class CostSharingLeverConfig(BaseModel):
    """Cost Sharing lever configuration"""
    copay: Optional[float] = None
    coinsurance: Optional[float] = None  # Percentage (0.0-1.0)
    deductible_applies: bool = False
    out_of_pocket_applies: bool = True
    differential_by_site: Optional[dict[str, dict[str, float]]] = None  # {"HOSPITAL_OP": {"copay": 100}}


class NetworkRestrictionLeverConfig(BaseModel):
    """Network Restriction lever configuration"""
    allowed_network: list[str] = Field(default_factory=list)  # ["IN", "OUT", "TIERED"]
    tier_restrictions: Optional[dict[str, dict[str, Any]]] = None  # Tier-specific rules
    oon_allowed: bool = False
    oon_cost_sharing: Optional[dict[str, float]] = None  # Higher cost-sharing for OON


class ReferralRequirementLeverConfig(BaseModel):
    """Referral Requirement lever configuration"""
    requires_referral: bool = True
    referral_from: list[str] = Field(default_factory=list)  # ["PCP", "SPECIALIST"]
    referral_age_limit: Optional[int] = None  # Age exemption
    referral_exemptions: Optional[list[Condition]] = None


class ClinicalCriteriaLeverConfig(BaseModel):
    """Clinical Criteria lever configuration (MCG/InterQual-like)"""
    criteria_type: str = "MEDICAL_NECESSITY"  # "MEDICAL_NECESSITY", "APPROPRIATENESS", "GUIDELINE"
    guideline_source: Optional[str] = None  # "MCG", "InterQual", "CUSTOM"
    required_diagnosis: Optional[list[str]] = None  # ICD-10 codes
    contraindications: Optional[list[str]] = None  # Conditions that prevent approval
    documentation_required: bool = True


class PolicyLeverLogic(BaseModel):
    """Complete lever logic with conditions and exceptions"""
    lever_type: PolicyType
    targets: LeverTargets
    config: dict[str, Any] = Field(default_factory=dict)  # Lever-specific config (PriorAuthLeverConfig, etc.)
    apply_when: list[RuleGroup] = Field(default_factory=list)  # AND/OR rule groups
    exceptions: list[Exception] = Field(default_factory=list)  # Do not apply when
    priority: int = 1  # Execution order if multiple levers


class PolicyLogic(BaseModel):
    """Complete policy logic structure (what drives analytics)"""
    scope: PolicyScope
    effective_period: EffectivePeriod
    levers: list[PolicyLeverLogic] = Field(default_factory=list)
    global_exceptions: list[Exception] = Field(default_factory=list)  # Apply to all levers
    version: int = 1
    change_description: Optional[str] = None


class ExpectedBehavioralResponse(BaseModel):
    """Expected behavioral responses to policy"""
    responses: list[str]  # e.g., ["DECREASE_TARGET_SERVICE", "INCREASE_ER_IMAGING", "SITE_SHIFT"]


class AnalyticsExpectations(BaseModel):
    """Analytics configuration for this policy"""
    primary_metrics: list[str]  # e.g., ["UTIL_PER_1K", "ALLOWED_PMPM"]
    secondary_metrics: Optional[list[str]] = None  # e.g., ["ER_UTILIZATION", "ALTERNATE_IMAGING"]
    lag_days: Optional[list[int]] = None  # [30, 60, 90] - time windows for analysis


class UIHints(BaseModel):
    """UI configuration hints for policy display"""
    show_substitution_warning: bool = False
    show_site_comparison: bool = False
    show_accumulator: bool = False
    show_financial_impact: bool = False
    show_compound_policy: bool = False
    require_warning_ack: bool = False
    elasticity_model: bool = False


class CanonicalPolicy(BaseModel):
    """Complete canonical policy object - engine contract"""
    policy_id: Union[UUID, str]
    policy_name: str
    policy_type: PolicyType
    description: Optional[str] = None
    status: PolicyStatus = PolicyStatus.ACTIVE
    effective_period: EffectivePeriod
    scope: PolicyScope
    enforcement: Enforcement
    policy_levers: list[PolicyLever] = Field(default_factory=list)
    # New: Structured policy logic (replaces free-form JSON)
    policy_logic: Optional[PolicyLogic] = None
    expected_behavioral_response: Optional[ExpectedBehavioralResponse] = None
    analytics_expectations: Optional[AnalyticsExpectations] = None
    ui_hints: Optional[UIHints] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

