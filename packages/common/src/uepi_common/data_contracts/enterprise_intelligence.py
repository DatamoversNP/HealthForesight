"""Enterprise intelligence contracts for BCBS NC Dec 4 extensions.

Additive to existing PolicyType / lifecycle — does not replace flat policy_type.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PrimaryDomain(str, Enum):
    MEDICAL = "MEDICAL"
    PHARMACY = "PHARMACY"
    REIMBURSEMENT = "REIMBURSEMENT"
    BENEFIT = "BENEFIT"
    NETWORK = "NETWORK"
    ADMINISTRATIVE = "ADMINISTRATIVE"
    MEDICARE_COVERAGE = "MEDICARE_COVERAGE"
    CODING_EDIT = "CODING_EDIT"


class PolicyMechanism(str, Enum):
    PRIOR_AUTH = "PRIOR_AUTH"
    MEDICAL_NECESSITY = "MEDICAL_NECESSITY"
    SITE_OF_CARE = "SITE_OF_CARE"
    CLINICAL_CRITERIA = "CLINICAL_CRITERIA"
    STEP_THERAPY = "STEP_THERAPY"
    QUANTITY_LIMIT = "QUANTITY_LIMIT"
    COST_SHARING = "COST_SHARING"
    REIMBURSEMENT = "REIMBURSEMENT"
    CODING_EDIT = "CODING_EDIT"
    COVERAGE = "COVERAGE"
    NETWORK_RESTRICTION = "NETWORK_RESTRICTION"
    COMPOSITE = "COMPOSITE"


class EvidenceClassification(str, Enum):
    CAUSAL = "CAUSAL"
    ASSOCIATIONAL = "ASSOCIATIONAL"
    DESCRIPTIVE = "DESCRIPTIVE"
    INCONCLUSIVE = "INCONCLUSIVE"


class ColdStartEvidenceTier(str, Enum):
    A_DIRECT_COMPARABLE = "A_DIRECT_COMPARABLE"
    B_RELATED_ANALOG = "B_RELATED_ANALOG"
    C_ASSUMPTION_DRIVEN = "C_ASSUMPTION_DRIVEN"
    D_EXPLORATORY_ONLY = "D_EXPLORATORY_ONLY"


class PolicyComposition(BaseModel):
    policy_id: str
    policy_name: str
    primary_domain: PrimaryDomain
    mechanisms: List[PolicyMechanism] = Field(default_factory=list)
    service_scope: List[str] = Field(default_factory=list)
    authority: Optional[str] = None
    source_provenance: Optional[str] = None
    lob: List[str] = Field(default_factory=list)
    jurisdiction: Optional[str] = None
    hierarchy: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    catalog_policy_type: Optional[str] = None  # backward-compatible flat type


class ExternalFactor(BaseModel):
    factor_id: str
    name: str
    category: str
    timing: str
    plausible_direction: str
    evidence_status: str


class CausalImpactResult(BaseModel):
    policy_id: str
    fixture_id: str
    labeled_synthetic: bool = True
    method: str
    formula: Optional[str] = None
    unit: Optional[Dict[str, Any]] = None
    outcome: str
    denominator: str
    treatment_definition: Any = None  # str or structured dict
    comparison_population: Any = None
    periods: Optional[Dict[str, Any]] = None
    calculation: Optional[Dict[str, Any]] = None
    observed_change: Optional[float] = None
    expected_change_without_policy: Optional[float] = None
    estimated_incremental_effect: Optional[float] = None
    uncertainty_interval: Dict[str, Any] = Field(default_factory=dict)
    diagnostics: Dict[str, Any] = Field(default_factory=dict)
    external_factors: List[ExternalFactor] = Field(default_factory=list)
    evidence_classification: EvidenceClassification
    limitations: List[str] = Field(default_factory=list)
    series: List[Dict[str, Any]] = Field(default_factory=list)
    known_true_effect: Optional[float] = None
    recovered_within_tolerance: Optional[bool] = None
    implementation_class: Optional[str] = None


class ProviderBehaviorSignal(BaseModel):
    provider_id: str
    provider_name: str
    signal: str
    baseline_value: Optional[float] = None
    observed_value: Optional[float] = None
    change: Optional[float] = None
    peer_adjusted_change: Optional[float] = None
    unit: str
    denominator: Optional[str] = None
    n: int
    suppressed: bool = False
    interpretation: str  # observed finding only — no intent


class ProviderBehaviorPanel(BaseModel):
    policy_id: str
    labeled_synthetic: bool = True
    peer_selection: Optional[Dict[str, Any]] = None
    minimum_n: int = 30
    signals: List[ProviderBehaviorSignal] = Field(default_factory=list)
    caveats: List[str] = Field(default_factory=list)
    implementation_class: Optional[str] = None


class ColdStartAssumption(BaseModel):
    assumption_id: str
    text: str
    source: str
    source_version: str
    as_of: str
    applicability: Optional[str] = None
    uncertainty_rationale: str
    tier_contribution: Optional[str] = None


class ColdStartForecast(BaseModel):
    policy_id: str
    policy_name: str
    evidence_tier: ColdStartEvidenceTier
    tier_selection_reason: Optional[str] = None
    baseline_available: bool
    prior_intervention_history: bool
    assumptions: List[str] = Field(default_factory=list)
    assumption_records: List[ColdStartAssumption] = Field(default_factory=list)
    analog_policies: List[Any] = Field(default_factory=list)
    directional_forecast: str
    numeric_scenario: Optional[Dict[str, Any]] = None
    recalibration_rule: Optional[str] = None
    uncertainty_note: str
    provenance: List[str] = Field(default_factory=list)
    implementation_class: Optional[str] = None
    labeled_synthetic: bool = True


class ApplicabilityResolution(BaseModel):
    query: Dict[str, Any]
    program_family: Optional[str] = None
    program: str
    state: str
    contractor: Optional[str] = None
    jurisdiction: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    status: Optional[str] = None
    disclaimer: str


class UnifiedVerdictAssessments(BaseModel):
    forecast_performance: str  # WITHIN_EXPECTED_RANGE | OUTSIDE_RANGE | NOT_MEASURABLE
    causal_evidence: str  # SUPPORTED_EFFECT | INCONCLUSIVE | NOT_ESTIMABLE
    policy_governance: str  # MAINTAIN | INVESTIGATE | CONSIDER_ADJUSTMENT | ESCALATE


class UnifiedVerdictEvidence(BaseModel):
    policy_id: str
    policy_name: str
    policy_version: Optional[str] = None
    assessments: UnifiedVerdictAssessments
    assessment_note: Optional[str] = None
    composition: Optional[Dict[str, Any]] = None
    causal_summary: Optional[Dict[str, Any]] = None
    provider_behavior_summary: Optional[Dict[str, Any]] = None
    cold_start: Optional[Dict[str, Any]] = None
    applicability_summary: Optional[Dict[str, Any]] = None
    decision_options: List[str] = Field(default_factory=list)
    lineage: Dict[str, Any] = Field(default_factory=dict)
