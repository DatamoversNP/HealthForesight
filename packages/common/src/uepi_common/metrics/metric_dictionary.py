"""Metric dictionary - Authoritative definitions for all baseline/predicted/observed metrics"""

from typing import Dict, Any, Optional
from enum import Enum


class MetricType(str, Enum):
    """Metric type categories"""
    PRIMARY_OUTCOME = "primary_outcome"
    MIX = "mix"
    BEHAVIORAL = "behavioral"
    LEARNING = "learning"


class MetricDefinition:
    """Definition of a single metric"""
    
    def __init__(
        self,
        name: str,
        formula: str,
        unit: str,
        denominator: str,
        scope: str,
        metric_type: MetricType,
        description: str,
        required_for_cards: bool = False,
    ):
        self.name = name
        self.formula = formula
        self.unit = unit
        self.denominator = denominator
        self.scope = scope  # "global" or "policy_target"
        self.metric_type = metric_type
        self.description = description
        self.required_for_cards = required_for_cards


# Metric Dictionary - Authoritative source
METRIC_DICTIONARY: Dict[str, MetricDefinition] = {}

# ============================================================================
# D1-D3: Denominator Definitions
# ============================================================================
METRIC_DICTIONARY["member_months"] = MetricDefinition(
    name="member_months",
    formula="Σ over members (number of months enrolled in period)",
    unit="member-months",
    denominator="enrollment_table",
    scope="global",
    metric_type=MetricType.PRIMARY_OUTCOME,
    description="Sum of enrolled member-months in period and scope",
    required_for_cards=True,
)

METRIC_DICTIONARY["unique_members"] = MetricDefinition(
    name="unique_members",
    formula="count distinct member_id with ≥1 eligible day in period",
    unit="members",
    denominator="enrollment_table",
    scope="global",
    metric_type=MetricType.PRIMARY_OUTCOME,
    description="Unique members enrolled in period",
    required_for_cards=False,
)

METRIC_DICTIONARY["policy_eligible_member_months"] = MetricDefinition(
    name="policy_eligible_member_months",
    formula="member_months restricted to policy scope filters (LOB/market/plan/network)",
    unit="member-months",
    denominator="enrollment_table",
    scope="policy_target",
    metric_type=MetricType.PRIMARY_OUTCOME,
    description="Member-months eligible for policy (denominator for policy-scoped metrics)",
    required_for_cards=True,
)

# ============================================================================
# M1-M7: Primary Outcome Metrics (must be baseline + predicted + observed)
# ============================================================================
METRIC_DICTIONARY["util_rate_total_per_1000_mm"] = MetricDefinition(
    name="util_rate_total_per_1000_mm",
    formula="(total_claim_lines / member_months) * 1000",
    unit="claim_lines per 1,000 member-months",
    denominator="member_months",
    scope="global",
    metric_type=MetricType.PRIMARY_OUTCOME,
    description="Total utilization rate per 1,000 member-months",
    required_for_cards=False,
)

METRIC_DICTIONARY["util_rate_target_per_1000_mm"] = MetricDefinition(
    name="util_rate_target_per_1000_mm",
    formula="(target_claim_lines / policy_eligible_member_months) * 1000",
    unit="claim_lines per 1,000 member-months",
    denominator="policy_eligible_member_months",
    scope="policy_target",
    metric_type=MetricType.PRIMARY_OUTCOME,
    description="Policy-targeted utilization rate per 1,000 member-months",
    required_for_cards=True,
)

METRIC_DICTIONARY["allowed_pmpm_total"] = MetricDefinition(
    name="allowed_pmpm_total",
    formula="total_allowed_amount / member_months",
    unit="dollars PMPM",
    denominator="member_months",
    scope="global",
    metric_type=MetricType.PRIMARY_OUTCOME,
    description="Total allowed cost per member per month",
    required_for_cards=False,
)

METRIC_DICTIONARY["allowed_pmpm_target"] = MetricDefinition(
    name="allowed_pmpm_target",
    formula="target_allowed_amount / policy_eligible_member_months",
    unit="dollars PMPM",
    denominator="policy_eligible_member_months",
    scope="policy_target",
    metric_type=MetricType.PRIMARY_OUTCOME,
    description="Policy-targeted allowed cost per member per month",
    required_for_cards=True,
)

METRIC_DICTIONARY["paid_pmpm_total"] = MetricDefinition(
    name="paid_pmpm_total",
    formula="total_paid_amount / member_months",
    unit="dollars PMPM",
    denominator="member_months",
    scope="global",
    metric_type=MetricType.PRIMARY_OUTCOME,
    description="Total paid cost per member per month",
    required_for_cards=False,
)

METRIC_DICTIONARY["allowed_total_annualized"] = MetricDefinition(
    name="allowed_total_annualized",
    formula="(total_allowed_amount / months_in_period) * 12",
    unit="dollars per year",
    denominator="period_months",
    scope="policy_target",
    metric_type=MetricType.PRIMARY_OUTCOME,
    description="Total allowed cost annualized (for Total Cost Change card)",
    required_for_cards=True,
)

# ============================================================================
# M8-M13: Mix Metrics (needed for substitution/spillover/leakage)
# ============================================================================
METRIC_DICTIONARY["soc_share_target_ER"] = MetricDefinition(
    name="soc_share_target_ER",
    formula="(target_claim_lines where soc=ER / target_claim_lines total)",
    unit="percent (%)",
    denominator="target_claim_lines",
    scope="policy_target",
    metric_type=MetricType.MIX,
    description="ER share of targeted utilization",
    required_for_cards=False,
)

METRIC_DICTIONARY["soc_share_target_HOPD"] = MetricDefinition(
    name="soc_share_target_HOPD",
    formula="(target_claim_lines where soc=HOPD / target_claim_lines total)",
    unit="percent (%)",
    denominator="target_claim_lines",
    scope="policy_target",
    metric_type=MetricType.MIX,
    description="HOPD share of targeted utilization",
    required_for_cards=False,
)

METRIC_DICTIONARY["soc_share_target_ASC"] = MetricDefinition(
    name="soc_share_target_ASC",
    formula="(target_claim_lines where soc=ASC / target_claim_lines total)",
    unit="percent (%)",
    denominator="target_claim_lines",
    scope="policy_target",
    metric_type=MetricType.MIX,
    description="ASC share of targeted utilization",
    required_for_cards=False,
)

METRIC_DICTIONARY["inn_share_target"] = MetricDefinition(
    name="inn_share_target",
    formula="(target_claim_lines in_network / target_claim_lines total)",
    unit="percent (%)",
    denominator="target_claim_lines",
    scope="policy_target",
    metric_type=MetricType.MIX,
    description="In-network share of targeted utilization",
    required_for_cards=True,
)

METRIC_DICTIONARY["oon_leakage_rate_target_per_1000_mm"] = MetricDefinition(
    name="oon_leakage_rate_target_per_1000_mm",
    formula="(target_claim_lines oon / policy_eligible_member_months) * 1000",
    unit="claim_lines per 1,000 member-months",
    denominator="policy_eligible_member_months",
    scope="policy_target",
    metric_type=MetricType.MIX,
    description="OON leakage rate for targeted services",
    required_for_cards=False,
)

METRIC_DICTIONARY["top10_provider_share_target"] = MetricDefinition(
    name="top10_provider_share_target",
    formula="(sum target utilization for top10 providers / total target utilization)",
    unit="percent (%)",
    denominator="target_claim_lines",
    scope="policy_target",
    metric_type=MetricType.MIX,
    description="Concentration of targeted utilization in top 10 providers",
    required_for_cards=False,
)

METRIC_DICTIONARY["member_cost_share_pmpm"] = MetricDefinition(
    name="member_cost_share_pmpm",
    formula="total_member_cost_share / member_months",
    unit="dollars PMPM",
    denominator="member_months",
    scope="global",
    metric_type=MetricType.PRIMARY_OUTCOME,
    description="Member cost share per member per month (deductibles, copays, coinsurance)",
    required_for_cards=False,
)

METRIC_DICTIONARY["provider_hhi_target"] = MetricDefinition(
    name="provider_hhi_target",
    formula="HHI = Σ (provider_share_i^2) where provider_share based on target claim lines or allowed",
    unit="index (0-1)",
    denominator="target_claim_lines",
    scope="policy_target",
    metric_type=MetricType.MIX,
    description="Provider concentration (Herfindahl-Hirschman Index) for targeted services (0=perfect competition, 1=monopoly)",
    required_for_cards=False,
)

METRIC_DICTIONARY["service_share_target"] = MetricDefinition(
    name="service_share_target",
    formula="(target_claim_lines with code=c or group=g / target_claim_lines total)",
    unit="percent (%)",
    denominator="target_claim_lines",
    scope="policy_target",
    metric_type=MetricType.MIX,
    description="Service mix share within target (code or code group)",
    required_for_cards=False,
)

# ============================================================================
# M14-M16: Substitution, Spillover & Second-Order Metrics
# ============================================================================
METRIC_DICTIONARY["substitution_uplift_per_1000_mm"] = MetricDefinition(
    name="substitution_uplift_per_1000_mm",
    formula="(post_util_rate_candidate - expected_post_util_rate_candidate) where expected is baseline trend/counterfactual",
    unit="claim_lines per 1,000 member-months",
    denominator="policy_eligible_member_months",
    scope="policy_target",
    metric_type=MetricType.BEHAVIORAL,
    description="Substitution uplift rate for candidate service (observed - expected)",
    required_for_cards=False,
)

METRIC_DICTIONARY["soc_share_delta_target"] = MetricDefinition(
    name="soc_share_delta_target",
    formula="post_soc_share - baseline_soc_share",
    unit="percentage points (pp)",
    denominator="target_claim_lines",
    scope="policy_target",
    metric_type=MetricType.BEHAVIORAL,
    description="Site of care share change (delta between post and baseline)",
    required_for_cards=False,
)

METRIC_DICTIONARY["deferral_index_target"] = MetricDefinition(
    name="deferral_index_target",
    formula="(post_30d_util_rate_target / baseline_30d_util_rate_target) or time-to-service shift",
    unit="index (ratio)",
    denominator="target_claim_lines",
    scope="policy_target",
    metric_type=MetricType.BEHAVIORAL,
    description="Deferral/timing shift proxy (ratio of post to baseline utilization timing)",
    required_for_cards=False,
)

# ============================================================================
# M17-M19: Behavioral Attribution Metrics
# ============================================================================
METRIC_DICTIONARY["provider_archetype_share"] = MetricDefinition(
    name="provider_archetype_share",
    formula="(# providers classified as type / total providers in target scope)",
    unit="percent (%)",
    denominator="providers",
    scope="policy_target",
    metric_type=MetricType.BEHAVIORAL,
    description="Provider archetype distribution (compliant, adaptive, resistant, circumvention-prone)",
    required_for_cards=False,
)

METRIC_DICTIONARY["provider_ordering_intensity_target_per_1000_mm"] = MetricDefinition(
    name="provider_ordering_intensity_target_per_1000_mm",
    formula="(target_claim_lines attributed to provider / member_months of provider's attributed population) * 1000",
    unit="per 1,000 member-months",
    denominator="member_months",
    scope="policy_target",
    metric_type=MetricType.BEHAVIORAL,
    description="Provider ordering intensity for targeted services",
    required_for_cards=False,
)

METRIC_DICTIONARY["patient_response_share"] = MetricDefinition(
    name="patient_response_share",
    formula="(# member-months in segment exhibiting response / member-months in segment)",
    unit="percent (%)",
    denominator="member_months",
    scope="policy_target",
    metric_type=MetricType.BEHAVIORAL,
    description="Patient segment response share (comply, substitute, defer, ER_fallback)",
    required_for_cards=False,
)

# ============================================================================
# M20-M22: Prediction vs Observed & Learning Metrics
# ============================================================================
METRIC_DICTIONARY["prediction_error_util_pp"] = MetricDefinition(
    name="prediction_error_util_pp",
    formula="observed_delta_util_pct - predicted_delta_util_pct",
    unit="percentage points (pp)",
    denominator="percentage",
    scope="policy_target",
    metric_type=MetricType.LEARNING,
    description="Prediction error for utilization (observed - predicted percentage change)",
    required_for_cards=False,
)

METRIC_DICTIONARY["prediction_error_cost_pmpm"] = MetricDefinition(
    name="prediction_error_cost_pmpm",
    formula="observed_delta_cost_pmpm - predicted_delta_cost_pmpm",
    unit="dollars PMPM",
    denominator="PMPM",
    scope="policy_target",
    metric_type=MetricType.LEARNING,
    description="Prediction error for cost PMPM (observed - predicted change)",
    required_for_cards=False,
)

METRIC_DICTIONARY["confidence_score"] = MetricDefinition(
    name="confidence_score",
    formula="weighted composite of: data sufficiency, analog strength, uncertainty width",
    unit="score (0-100)",
    denominator="N/A",
    scope="policy_target",
    metric_type=MetricType.LEARNING,
    description="Model confidence score (0-100) with components: data sufficiency, analog strength, uncertainty",
    required_for_cards=True,
)

# Backward compatibility aliases
METRIC_DICTIONARY["utilization_per_1k"] = METRIC_DICTIONARY["util_rate_target_per_1000_mm"]
METRIC_DICTIONARY["cost_per_member"] = METRIC_DICTIONARY["allowed_pmpm_target"]


def get_metric_definition(metric_name: str) -> Optional[MetricDefinition]:
    """Get metric definition by name"""
    return METRIC_DICTIONARY.get(metric_name)


def get_all_metrics(metric_type: Optional[MetricType] = None, scope: Optional[str] = None) -> Dict[str, MetricDefinition]:
    """Get all metrics, optionally filtered by type and/or scope"""
    result = METRIC_DICTIONARY.copy()
    
    if metric_type:
        result = {k: v for k, v in result.items() if v.metric_type == metric_type}
    
    if scope:
        result = {k: v for k, v in result.items() if v.scope == scope}
    
    return result


def get_card_required_metrics() -> Dict[str, MetricDefinition]:
    """Get metrics required for Predicted/Observed Impact cards"""
    return {k: v for k, v in METRIC_DICTIONARY.items() if v.required_for_cards}


# Export metric names as constants for easy reference
METRIC_NAMES = {
    # Denominators
    "MEMBER_MONTHS": "member_months",
    "UNIQUE_MEMBERS": "unique_members",
    "POLICY_ELIGIBLE_MEMBER_MONTHS": "policy_eligible_member_months",
    
    # Primary outcomes
    "UTIL_RATE_TOTAL_PER_1000_MM": "util_rate_total_per_1000_mm",
    "UTIL_RATE_TARGET_PER_1000_MM": "util_rate_target_per_1000_mm",
    "ALLOWED_PMPM_TOTAL": "allowed_pmpm_total",
    "ALLOWED_PMPM_TARGET": "allowed_pmpm_target",
    "PAID_PMPM_TOTAL": "paid_pmpm_total",
    "MEMBER_COST_SHARE_PMPM": "member_cost_share_pmpm",
    "ALLOWED_TOTAL_ANNUALIZED": "allowed_total_annualized",
    
    # Mix metrics
    "SOC_SHARE_TARGET": "soc_share_target",  # Pattern - use with category suffix
    "INN_SHARE_TARGET": "inn_share_target",
    "OON_LEAKAGE_RATE_TARGET_PER_1000_MM": "oon_leakage_rate_target_per_1000_mm",
    "PROVIDER_HHI_TARGET": "provider_hhi_target",
    "TOP10_PROVIDER_SHARE_TARGET": "top10_provider_share_target",
    
    # Substitution/spillover metrics
    "SUBSTITUTION_UPLIFT_PER_1000_MM": "substitution_uplift_per_1000_mm",
    "SOC_SHARE_DELTA_TARGET": "soc_share_delta_target",
    "DEFERRAL_INDEX_TARGET": "deferral_index_target",
    
    # Behavioral attribution metrics
    "PROVIDER_ARCHETYPE_SHARE": "provider_archetype_share",
    "PROVIDER_ORDERING_INTENSITY_TARGET_PER_1000_MM": "provider_ordering_intensity_target_per_1000_mm",
    "PATIENT_RESPONSE_SHARE": "patient_response_share",
    
    # Learning metrics
    "PREDICTION_ERROR_UTIL_PP": "prediction_error_util_pp",
    "PREDICTION_ERROR_COST_PMPM": "prediction_error_cost_pmpm",
    "CONFIDENCE_SCORE": "confidence_score",
    
    # Backward compatibility
    "UTILIZATION_PER_1K": "utilization_per_1k",
    "COST_PER_MEMBER": "cost_per_member",
}
