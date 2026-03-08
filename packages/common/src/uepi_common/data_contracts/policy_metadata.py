"""
Policy Metadata Schema
Defines policy types (levers) and their capabilities for dynamic UI generation and AI model selection
"""
from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class LeverType(str, Enum):
    """Policy lever types - these are the atomic controls"""
    PRIOR_AUTH = "PRIOR_AUTH"
    SITE_OF_CARE = "SITE_OF_CARE"
    COVERAGE_RULE = "COVERAGE_RULE"
    STEP_THERAPY = "STEP_THERAPY"
    BENEFIT_LIMIT = "BENEFIT_LIMIT"
    FREQUENCY_LIMIT = "FREQUENCY_LIMIT"
    QUANTITY_LIMIT = "QUANTITY_LIMIT"
    CLINICAL_CRITERIA = "CLINICAL_CRITERIA"
    COST_SHARING = "COST_SHARING"
    PAYMENT_POLICY = "PAYMENT_POLICY"
    NETWORK_RESTRICTION = "NETWORK_RESTRICTION"
    PROVIDER_ELIGIBILITY = "PROVIDER_ELIGIBILITY"
    REFERRAL_REQUIREMENT = "REFERRAL_REQUIREMENT"
    DOCUMENTATION_REQUIREMENT = "DOCUMENTATION_REQUIREMENT"
    ACCESS_AVAILABILITY_RULE = "ACCESS_AVAILABILITY_RULE"


class ConditionType(str, Enum):
    """Types of conditions that can be applied to policy levers"""
    PLACE_OF_SERVICE = "PLACE_OF_SERVICE"
    PROVIDER_SPECIALTY = "PROVIDER_SPECIALTY"
    DIAGNOSIS_GROUP = "DIAGNOSIS_GROUP"
    MEMBER_TIER = "MEMBER_TIER"
    AGE_BAND = "AGE_BAND"
    PROVIDER_SYSTEM = "PROVIDER_SYSTEM"
    DISTANCE_ACCESS = "DISTANCE_ACCESS"
    PRIOR_TREATMENT_HISTORY = "PRIOR_TREATMENT_HISTORY"
    MEMBER_ELIGIBILITY = "MEMBER_ELIGIBILITY"
    CLINICAL_COMPLEXITY = "CLINICAL_COMPLEXITY"


class ExceptionType(str, Enum):
    """Types of exceptions that can be applied to policy levers"""
    ER = "ER"
    URGENT = "URGENT"
    AGE_BASED = "AGE_BASED"
    RURAL_ACCESS = "RURAL_ACCESS"
    MEDICAL_NECESSITY_OVERRIDE = "MEDICAL_NECESSITY_OVERRIDE"
    CONTRAINDICATIONS = "CONTRAINDICATIONS"
    FAILURE_DOCUMENTATION = "FAILURE_DOCUMENTATION"
    CATASTROPHIC_CASES = "CATASTROPHIC_CASES"
    CLINICAL_COMPLEXITY = "CLINICAL_COMPLEXITY"


class LeverParameter(BaseModel):
    """Parameter definition for a policy lever"""
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, number, boolean, array, object)")
    required: bool = Field(False, description="Whether parameter is required")
    description: str = Field("", description="Parameter description")
    default_value: Optional[Any] = Field(None, description="Default value")
    allowed_values: Optional[List[Any]] = Field(None, description="Allowed values for enum types")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")


class PolicyTypeMetadata(BaseModel):
    """Metadata for a policy type (lever type)"""
    lever_type: LeverType = Field(..., description="Lever type identifier")
    display_name: str = Field(..., description="Human-readable display name")
    description: str = Field(..., description="Policy type description")
    category: str = Field(..., description="Category (CORE, ADVANCED_UM, FINANCIAL, NETWORK, ADMIN)")
    
    # Supported capabilities
    supported_parameters: List[LeverParameter] = Field(default_factory=list, description="Supported parameters")
    supported_conditions: List[ConditionType] = Field(default_factory=list, description="Supported condition types")
    supported_exceptions: List[ExceptionType] = Field(default_factory=list, description="Supported exception types")
    
    # AI/Analytics capabilities
    supports_elasticity: bool = Field(True, description="Whether this lever type supports elasticity modeling")
    supports_substitution: bool = Field(True, description="Whether this lever type supports substitution detection")
    supports_what_if: bool = Field(True, description="Whether this lever type supports what-if analysis")
    elasticity_impact: str = Field("MEDIUM", description="Expected elasticity impact (HIGH, MEDIUM, LOW)")
    substitution_risk: str = Field("MEDIUM", description="Expected substitution risk (HIGH, MEDIUM, LOW)")
    
    # UI hints
    ui_form_config: Optional[Dict[str, Any]] = Field(None, description="UI form configuration for dynamic generation")
    help_text: Optional[str] = Field(None, description="Help text for users")
    examples: Optional[List[Dict[str, Any]]] = Field(None, description="Example configurations")


# Policy Type Metadata Catalog
POLICY_TYPE_CATALOG: Dict[LeverType, PolicyTypeMetadata] = {
    LeverType.PRIOR_AUTH: PolicyTypeMetadata(
        lever_type=LeverType.PRIOR_AUTH,
        display_name="Prior Authorization",
        description="Requires approval before service delivery",
        category="CORE",
        supported_parameters=[
            LeverParameter(name="codes", type="array", required=True, description="CPT/HCPCS/DRG codes"),
            LeverParameter(name="enforcement", type="string", required=True, allowed_values=["HARD", "SOFT"], description="Enforcement level"),
            LeverParameter(name="site_of_care", type="string", required=False, description="Site of care restriction"),
        ],
        supported_conditions=[ConditionType.PLACE_OF_SERVICE, ConditionType.PROVIDER_SPECIALTY, ConditionType.DIAGNOSIS_GROUP],
        supported_exceptions=[ExceptionType.ER, ExceptionType.URGENT, ExceptionType.AGE_BASED],
        supports_elasticity=True,
        supports_substitution=True,
        supports_what_if=True,
        elasticity_impact="HIGH",
        substitution_risk="VERY_HIGH",
        help_text="Prior authorization policies require approval before services are delivered. High elasticity and substitution risk.",
    ),
    
    LeverType.SITE_OF_CARE: PolicyTypeMetadata(
        lever_type=LeverType.SITE_OF_CARE,
        display_name="Site of Care",
        description="Restricts or incentivizes where care is delivered",
        category="CORE",
        supported_parameters=[
            LeverParameter(name="allowed_sites", type="array", required=False, description="Allowed sites of care"),
            LeverParameter(name="disallowed_sites", type="array", required=False, description="Disallowed sites of care"),
            LeverParameter(name="differential_cost_sharing", type="object", required=False, description="Differential cost sharing by site"),
        ],
        supported_conditions=[ConditionType.PROVIDER_SYSTEM, ConditionType.DISTANCE_ACCESS],
        supported_exceptions=[ExceptionType.CLINICAL_COMPLEXITY, ExceptionType.RURAL_ACCESS],
        supports_elasticity=True,
        supports_substitution=True,
        supports_what_if=True,
        elasticity_impact="HIGH",
        substitution_risk="HIGH",
        help_text="Site of care policies control where services can be delivered. Strong cost impact and site substitution modeling required.",
    ),
    
    LeverType.COVERAGE_RULE: PolicyTypeMetadata(
        lever_type=LeverType.COVERAGE_RULE,
        display_name="Coverage Rule",
        description="Defines whether a service is covered at all",
        category="CORE",
        supported_parameters=[
            LeverParameter(name="covered", type="boolean", required=True, description="Whether service is covered"),
            LeverParameter(name="conditional_coverage", type="object", required=False, description="Conditional coverage rules"),
        ],
        supported_conditions=[ConditionType.DIAGNOSIS_GROUP, ConditionType.MEMBER_ELIGIBILITY],
        supported_exceptions=[ExceptionType.MEDICAL_NECESSITY_OVERRIDE],
        supports_elasticity=True,
        supports_substitution=False,
        supports_what_if=True,
        elasticity_impact="HIGH",
        substitution_risk="LOW",
        help_text="Coverage rules define whether services are covered. Binary utilization impact with high access risk.",
    ),
    
    LeverType.STEP_THERAPY: PolicyTypeMetadata(
        lever_type=LeverType.STEP_THERAPY,
        display_name="Step Therapy",
        description="Requires lower-cost therapy before higher-cost option",
        category="CORE",
        supported_parameters=[
            LeverParameter(name="step_sequence", type="array", required=True, description="Sequence of required steps"),
            LeverParameter(name="required_duration_per_step", type="object", required=False, description="Required duration for each step"),
        ],
        supported_conditions=[ConditionType.DIAGNOSIS_GROUP, ConditionType.PRIOR_TREATMENT_HISTORY],
        supported_exceptions=[ExceptionType.CONTRAINDICATIONS, ExceptionType.FAILURE_DOCUMENTATION],
        supports_elasticity=True,
        supports_substitution=True,
        supports_what_if=True,
        elasticity_impact="MEDIUM",
        substitution_risk="MEDIUM",
        help_text="Step therapy requires trying lower-cost options first. Lagged utilization shifts and downstream cost modeling.",
    ),
    
    LeverType.BENEFIT_LIMIT: PolicyTypeMetadata(
        lever_type=LeverType.BENEFIT_LIMIT,
        display_name="Benefit Limit",
        description="Caps usage via benefit design",
        category="CORE",
        supported_parameters=[
            LeverParameter(name="max_visits", type="number", required=False, description="Maximum visits allowed"),
            LeverParameter(name="max_dollars", type="number", required=False, description="Maximum dollars allowed"),
            LeverParameter(name="time_window", type="string", required=True, description="Time window (YEAR, MONTH, LIFETIME)"),
        ],
        supported_conditions=[ConditionType.MEMBER_TIER, ConditionType.AGE_BAND],
        supported_exceptions=[ExceptionType.CATASTROPHIC_CASES],
        supports_elasticity=True,
        supports_substitution=True,
        supports_what_if=True,
        elasticity_impact="MEDIUM",
        substitution_risk="MEDIUM",
        help_text="Benefit limits cap usage through benefit design. Deferred care modeling and long-term substitution risk.",
    ),
    
    LeverType.FREQUENCY_LIMIT: PolicyTypeMetadata(
        lever_type=LeverType.FREQUENCY_LIMIT,
        display_name="Frequency / Duration Limit",
        description="Limits how often a service can occur",
        category="ADVANCED_UM",
        supported_parameters=[
            LeverParameter(name="max_occurrences", type="number", required=True, description="Maximum occurrences"),
            LeverParameter(name="time_period", type="string", required=True, description="Time period (MONTH, YEAR)"),
        ],
        supported_conditions=[ConditionType.DIAGNOSIS_GROUP, ConditionType.MEMBER_TIER],
        supported_exceptions=[ExceptionType.MEDICAL_NECESSITY_OVERRIDE],
        supports_elasticity=True,
        supports_substitution=True,
        supports_what_if=True,
        elasticity_impact="MEDIUM",
        substitution_risk="HIGH",
        help_text="Frequency limits control how often services can occur. Often causes hidden substitution.",
    ),
    
    LeverType.QUANTITY_LIMIT: PolicyTypeMetadata(
        lever_type=LeverType.QUANTITY_LIMIT,
        display_name="Quantity Limit",
        description="Caps units per service",
        category="ADVANCED_UM",
        supported_parameters=[
            LeverParameter(name="units_per_episode", type="number", required=False, description="Units per episode"),
            LeverParameter(name="units_per_day", type="number", required=False, description="Units per day"),
        ],
        supported_conditions=[ConditionType.DIAGNOSIS_GROUP],
        supported_exceptions=[ExceptionType.MEDICAL_NECESSITY_OVERRIDE],
        supports_elasticity=True,
        supports_substitution=True,
        supports_what_if=True,
        elasticity_impact="MEDIUM",
        substitution_risk="MEDIUM",
        help_text="Quantity limits cap units per service. Unit inflation detection and provider response modeling.",
    ),
    
    LeverType.CLINICAL_CRITERIA: PolicyTypeMetadata(
        lever_type=LeverType.CLINICAL_CRITERIA,
        display_name="Clinical Criteria",
        description="Medical necessity rules beyond PA",
        category="ADVANCED_UM",
        supported_parameters=[
            LeverParameter(name="criteria_set", type="string", required=True, description="Criteria set reference (e.g., MCG)"),
            LeverParameter(name="strictness_level", type="string", required=True, allowed_values=["STRICT", "MEDIUM", "LENIENT"], description="Strictness level"),
        ],
        supported_conditions=[ConditionType.DIAGNOSIS_GROUP],
        supported_exceptions=[ExceptionType.MEDICAL_NECESSITY_OVERRIDE],
        supports_elasticity=True,
        supports_substitution=False,
        supports_what_if=True,
        elasticity_impact="MEDIUM",
        substitution_risk="LOW",
        help_text="Clinical criteria define medical necessity. Appeals risk and access delays.",
    ),
    
    LeverType.COST_SHARING: PolicyTypeMetadata(
        lever_type=LeverType.COST_SHARING,
        display_name="Cost Sharing",
        description="Member financial responsibility rules",
        category="FINANCIAL",
        supported_parameters=[
            LeverParameter(name="copay", type="number", required=False, description="Copay amount"),
            LeverParameter(name="coinsurance", type="number", required=False, description="Coinsurance percentage"),
            LeverParameter(name="differential_by_site", type="object", required=False, description="Differential cost sharing by site"),
        ],
        supported_conditions=[ConditionType.MEMBER_TIER, ConditionType.PLACE_OF_SERVICE],
        supported_exceptions=[ExceptionType.CATASTROPHIC_CASES],
        supports_elasticity=True,
        supports_substitution=True,
        supports_what_if=True,
        elasticity_impact="HIGH",
        substitution_risk="HIGH",
        help_text="Cost sharing controls member financial responsibility. Member elasticity and ER substitution risk.",
    ),
    
    LeverType.PAYMENT_POLICY: PolicyTypeMetadata(
        lever_type=LeverType.PAYMENT_POLICY,
        display_name="Payment Policy",
        description="Reimbursement structure controls",
        category="FINANCIAL",
        supported_parameters=[
            LeverParameter(name="fee_caps", type="object", required=False, description="Fee caps by code"),
            LeverParameter(name="bundles", type="array", required=False, description="Bundled payment codes"),
            LeverParameter(name="global_payments", type="object", required=False, description="Global payment arrangements"),
        ],
        supported_conditions=[ConditionType.PROVIDER_SPECIALTY, ConditionType.PROVIDER_SYSTEM],
        supported_exceptions=[],
        supports_elasticity=True,
        supports_substitution=True,
        supports_what_if=True,
        elasticity_impact="MEDIUM",
        substitution_risk="HIGH",
        help_text="Payment policies control reimbursement. Provider behavior shift and coding substitution.",
    ),
    
    LeverType.NETWORK_RESTRICTION: PolicyTypeMetadata(
        lever_type=LeverType.NETWORK_RESTRICTION,
        display_name="Network Restriction",
        description="Limits eligible providers",
        category="NETWORK",
        supported_parameters=[
            LeverParameter(name="network_tier", type="string", required=False, description="Network tier"),
            LeverParameter(name="provider_list", type="array", required=False, description="Specific provider list"),
        ],
        supported_conditions=[ConditionType.PROVIDER_SYSTEM],
        supported_exceptions=[ExceptionType.RURAL_ACCESS],
        supports_elasticity=True,
        supports_substitution=True,
        supports_what_if=True,
        elasticity_impact="MEDIUM",
        substitution_risk="HIGH",
        help_text="Network restrictions limit eligible providers. Leakage and access risk.",
    ),
    
    LeverType.PROVIDER_ELIGIBILITY: PolicyTypeMetadata(
        lever_type=LeverType.PROVIDER_ELIGIBILITY,
        display_name="Provider Eligibility",
        description="Who can render the service",
        category="NETWORK",
        supported_parameters=[
            LeverParameter(name="provider_type", type="array", required=True, description="Allowed provider types"),
            LeverParameter(name="credential_requirements", type="object", required=False, description="Credential requirements"),
        ],
        supported_conditions=[ConditionType.PROVIDER_SPECIALTY],
        supported_exceptions=[],
        supports_elasticity=False,
        supports_substitution=False,
        supports_what_if=False,
        elasticity_impact="LOW",
        substitution_risk="LOW",
        help_text="Provider eligibility defines who can render services.",
    ),
    
    LeverType.REFERRAL_REQUIREMENT: PolicyTypeMetadata(
        lever_type=LeverType.REFERRAL_REQUIREMENT,
        display_name="Referral Requirement",
        description="PCP or specialist referral needed",
        category="NETWORK",
        supported_parameters=[
            LeverParameter(name="referral_type", type="string", required=True, allowed_values=["PCP", "SPECIALIST"], description="Referral type"),
            LeverParameter(name="required_for", type="array", required=True, description="Services requiring referral"),
        ],
        supported_conditions=[ConditionType.PROVIDER_SPECIALTY],
        supported_exceptions=[ExceptionType.URGENT],
        supports_elasticity=True,
        supports_substitution=False,
        supports_what_if=True,
        elasticity_impact="MEDIUM",
        substitution_risk="LOW",
        help_text="Referral requirements control access to specialists. Access delay and downstream utilization shift.",
    ),
    
    LeverType.DOCUMENTATION_REQUIREMENT: PolicyTypeMetadata(
        lever_type=LeverType.DOCUMENTATION_REQUIREMENT,
        display_name="Documentation Requirement",
        description="Required records or attestations",
        category="ADMIN",
        supported_parameters=[
            LeverParameter(name="required_documents", type="array", required=True, description="Required document types"),
            LeverParameter(name="attestation_required", type="boolean", required=False, description="Whether attestation is required"),
        ],
        supported_conditions=[],
        supported_exceptions=[],
        supports_elasticity=False,
        supports_substitution=False,
        supports_what_if=False,
        elasticity_impact="LOW",
        substitution_risk="LOW",
        help_text="Documentation requirements specify required records or attestations.",
    ),
    
    LeverType.ACCESS_AVAILABILITY_RULE: PolicyTypeMetadata(
        lever_type=LeverType.ACCESS_AVAILABILITY_RULE,
        display_name="Access / Availability Rule",
        description="Time-to-service constraints",
        category="ADMIN",
        supported_parameters=[
            LeverParameter(name="max_wait_days", type="number", required=True, description="Maximum wait time in days"),
            LeverParameter(name="service_category", type="string", required=True, description="Service category"),
        ],
        supported_conditions=[ConditionType.PLACE_OF_SERVICE],
        supported_exceptions=[ExceptionType.URGENT],
        supports_elasticity=False,
        supports_substitution=False,
        supports_what_if=False,
        elasticity_impact="LOW",
        substitution_risk="LOW",
        help_text="Access rules define time-to-service constraints.",
    ),
}


def get_policy_type_metadata(lever_type: LeverType) -> Optional[PolicyTypeMetadata]:
    """Get metadata for a policy type"""
    return POLICY_TYPE_CATALOG.get(lever_type)


def get_all_policy_types() -> List[PolicyTypeMetadata]:
    """Get all policy type metadata"""
    return list(POLICY_TYPE_CATALOG.values())


def get_policy_types_by_category(category: str) -> List[PolicyTypeMetadata]:
    """Get policy types by category"""
    return [metadata for metadata in POLICY_TYPE_CATALOG.values() if metadata.category == category]

