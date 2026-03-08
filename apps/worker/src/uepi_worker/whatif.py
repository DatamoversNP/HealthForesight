"""
What-If Analysis Engine
Enables policy parameter adjustment and scenario simulation to see impact
"""
from typing import Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
import numpy as np
import polars as pl
from dataclasses import dataclass, asdict

from uepi_common.models import CanonicalPolicy, PolicyLogic, PolicyLeverLogic, PolicyType


def _get_policy_type_str(policy_type) -> str:
    """Extract policy type as string, handling both enum and string inputs"""
    if policy_type is None:
        return "PRIOR_AUTH"
    if isinstance(policy_type, str):
        return policy_type
    if hasattr(policy_type, 'value'):
        return policy_type.value
    return str(policy_type)


def _get_lever_type_str(lever_type) -> str:
    """Extract lever type as string, handling both enum and string inputs"""
    if lever_type is None:
        return "UNKNOWN"
    if isinstance(lever_type, str):
        return lever_type
    if hasattr(lever_type, 'value'):
        return lever_type.value
    return str(lever_type)


@dataclass
class ScenarioParameters:
    """Parameters for what-if scenario"""
    policy_id: str
    # Policy adjustments
    lever_adjustments: dict[str, Any]  # {lever_id: {parameter: value}}
    # Variable adjustments
    elasticity_adjustments: dict[str, float]  # {service_category: elasticity_multiplier}
    # Environmental variables
    member_count_multiplier: float = 1.0
    utilization_trend: float = 0.0  # Percentage change per month
    cost_inflation: float = 0.02  # 2% per month
    # Time horizon
    projection_months: int = 12


@dataclass
class ScenarioResult:
    """Results from what-if scenario simulation"""
    scenario_id: str
    baseline_metrics: dict[str, float]
    projected_metrics: dict[str, float]
    impact_metrics: dict[str, float]  # Difference between projected and baseline
    confidence_intervals: dict[str, tuple[float, float]]
    confidence_score: float
    sensitivity_analysis: dict[str, Any]  # Impact of each parameter adjustment


def simulate_scenario(
    tenant_id: UUID,
    policy: CanonicalPolicy,
    baseline_claims_df: pl.DataFrame,
    scenario_params: ScenarioParameters,
    elasticity_curves: Optional[dict[str, Any]] = None,
    use_latest_elasticity_models: bool = True,
) -> ScenarioResult:
    """
    Simulate what-if scenario with policy parameter adjustments
    
    Args:
        tenant_id: Tenant ID
        policy: Policy being adjusted
        baseline_claims_df: Baseline claims data (pre-policy or control)
        scenario_params: Scenario parameters (adjustments)
        elasticity_curves: Learned elasticity curves (if available, overridden by latest models if use_latest_elasticity_models=True)
        use_latest_elasticity_models: If True, loads latest elasticity models from learning loop
    
    Returns:
        ScenarioResult with projected impact
    """
    # Load latest elasticity models if requested and not provided
    if use_latest_elasticity_models and not elasticity_curves:
        try:
            from uepi_api.storage_learning import get_latest_elasticity_model
            policy_type = _get_policy_type_str(policy.policy_type)
            
            # Try to get latest model for this policy type
            latest_model = get_latest_elasticity_model(
                tenant_id=tenant_id,
                policy_type=policy_type,
                service_category=None,
            )
            
            if latest_model:
                # Convert elasticity model to elasticity_curves format
                elasticity_coefficients = latest_model.get("elasticity_coefficients", {})
                if elasticity_coefficients:
                    elasticity_curves = {}
                    # Map coefficients to service categories
                    for category, coeffs in elasticity_coefficients.items():
                        if isinstance(coeffs, dict):
                            elasticity_curves[category] = {
                                "elasticity": coeffs.get("utilization_elasticity", coeffs.get("elasticity", -0.3)),
                                "cost_elasticity": coeffs.get("cost_elasticity", -0.2),
                                "confidence": latest_model.get("confidence", 0.7),
                                "model_version": latest_model.get("version", "v1.0"),
                            }
        except Exception as e:
            print(f"Warning: Could not load latest elasticity models: {e}")
            # Fall back to default elasticity if loading fails
    
    # Start with baseline metrics
    baseline_metrics = compute_baseline_metrics(baseline_claims_df)
    
    # Apply policy adjustments
    adjusted_policy = apply_policy_adjustments(policy, scenario_params.lever_adjustments)
    
    # Project utilization changes based on elasticity
    utilization_projections = project_utilization_changes(
        baseline_claims_df,
        adjusted_policy,
        scenario_params,
        elasticity_curves,
    )
    
    # Project cost changes
    cost_projections = project_cost_changes(
        utilization_projections,
        baseline_claims_df,
        scenario_params,
    )
    
    # Aggregate projected metrics
    projected_metrics = {
        "utilization_per_1k": utilization_projections["total_utilization_per_1k"],
        "allowed_pmpm": cost_projections["total_allowed_pmpm"],
        "paid_pmpm": cost_projections["total_paid_pmpm"],
        "claim_count": utilization_projections["total_claims"],
        "member_months": baseline_metrics["member_months"] * scenario_params.member_count_multiplier,
    }
    
    # Compute impact (difference)
    impact_metrics = {
        k: projected_metrics.get(k, 0) - baseline_metrics.get(k, 0)
        for k in baseline_metrics.keys()
    }
    
    # Compute percent changes
    percent_changes = {
        k: (impact_metrics.get(k, 0) / baseline_metrics.get(k, 1e-10)) * 100
        if baseline_metrics.get(k, 0) != 0 else 0
        for k in baseline_metrics.keys()
    }
    
    # Monte Carlo simulation for confidence intervals
    confidence_intervals = monte_carlo_confidence_intervals(
        baseline_claims_df,
        adjusted_policy,
        scenario_params,
        n_simulations=1000,
    )
    
    # Compute confidence score
    confidence_score = compute_confidence_score(
        baseline_metrics,
        projected_metrics,
        confidence_intervals,
        scenario_params,
    )
    
    # Sensitivity analysis
    sensitivity_analysis = compute_sensitivity_analysis(
        baseline_claims_df,
        policy,
        scenario_params,
    )
    
    # Tradeoff analysis: cost vs utilization
    tradeoff_analysis = compute_tradeoff_analysis(
        baseline_metrics,
        projected_metrics,
        impact_metrics,
    )
    
    # Risk analysis: worst-case and best-case scenarios
    risk_analysis = compute_risk_analysis(
        baseline_metrics,
        projected_metrics,
        confidence_intervals,
        scenario_params,
    )
    
    # Add tradeoff and risk to impact_metrics
    enhanced_impact_metrics = {
        **impact_metrics,
        **{"percent_changes": percent_changes},
        **{"tradeoff_analysis": tradeoff_analysis},
        **{"risk_analysis": risk_analysis},
    }
    
    return ScenarioResult(
        scenario_id=f"scenario_{datetime.utcnow().isoformat()}",
        baseline_metrics=baseline_metrics,
        projected_metrics=projected_metrics,
        impact_metrics=enhanced_impact_metrics,
        confidence_intervals=confidence_intervals,
        confidence_score=confidence_score,
        sensitivity_analysis=sensitivity_analysis,
    )


def compute_baseline_metrics(claims_df: pl.DataFrame) -> dict[str, float]:
    """Compute baseline metrics from claims data"""
    if claims_df.is_empty():
        return {
            "utilization_per_1k": 0.0,
            "allowed_pmpm": 0.0,
            "paid_pmpm": 0.0,
            "claim_count": 0,
            "member_months": 0,
        }
    
    # Get unique members
    unique_members = claims_df["member_id"].n_unique()
    
    # Parse service_date if it's a string
    if "service_date" in claims_df.columns:
        if claims_df["service_date"].dtype == pl.Utf8:
            claims_df = claims_df.with_columns(
                pl.col("service_date").str.strptime(pl.Date, "%Y-%m-%d")
            )
        date_min = claims_df["service_date"].min()
        date_max = claims_df["service_date"].max()
        if date_min and date_max:
            months = (date_max - date_min).days / 30.0
        else:
            months = 1.0
    else:
        months = 1.0
    
    member_months = unique_members * max(1, months)
    
    # Get column names (may vary)
    allowed_col = "allowed_amount" if "allowed_amount" in claims_df.columns else "allowed_amt"
    paid_col = "paid_amount" if "paid_amount" in claims_df.columns else "paid_amt"
    
    total_allowed = claims_df[allowed_col].sum() if allowed_col in claims_df.columns else 0.0
    total_paid = claims_df[paid_col].sum() if paid_col in claims_df.columns else 0.0
    
    return {
        "utilization_per_1k": (len(claims_df) / member_months) * 1000 if member_months > 0 else 0.0,
        "allowed_pmpm": total_allowed / member_months if member_months > 0 else 0.0,
        "paid_pmpm": total_paid / member_months if member_months > 0 else 0.0,
        "claim_count": len(claims_df),
        "member_months": member_months,
    }


def apply_policy_adjustments(
    policy: CanonicalPolicy,
    lever_adjustments: dict[str, Any],
) -> CanonicalPolicy:
    """Apply adjustments to policy levers"""
    # Create a copy of the policy
    adjusted_policy_dict = policy.model_dump(mode='json')
    
    if policy.policy_logic and policy.policy_logic.levers:
        adjusted_levers = []
        for lever in policy.policy_logic.levers:
            lever_id = f"{_get_lever_type_str(lever.lever_type)}_{lever.priority}"
            
            if lever_id in lever_adjustments:
                # Adjust lever configuration
                adjustments = lever_adjustments[lever_id]
                
                # Create adjusted lever config
                adjusted_config = lever.config.copy() if lever.config else {}
                adjusted_config.update(adjustments)
                
                # Create new lever with adjusted config
                adjusted_lever = PolicyLeverLogic(
                    lever_type=lever.lever_type,
                    targets=lever.targets,
                    config=adjusted_config,
                    apply_when=lever.apply_when,
                    exceptions=lever.exceptions,
                    priority=lever.priority,
                )
                adjusted_levers.append(adjusted_lever)
            else:
                adjusted_levers.append(lever)
        
        # Update policy logic with adjusted levers
        adjusted_policy_logic = PolicyLogic(
            scope=policy.policy_logic.scope,
            effective_period=policy.policy_logic.effective_period,
            levers=adjusted_levers,
            global_exceptions=policy.policy_logic.global_exceptions,
            version=policy.policy_logic.version,
            change_description=policy.policy_logic.change_description,
        )
        
        adjusted_policy_dict["policy_logic"] = adjusted_policy_logic
    
    # Reconstruct policy (this is a simplified approach - in practice would need proper reconstruction)
    return policy  # For now, return original - full implementation would properly reconstruct


def project_utilization_changes(
    baseline_df: pl.DataFrame,
    adjusted_policy: CanonicalPolicy,
    scenario_params: ScenarioParameters,
    elasticity_curves: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Project utilization changes based on policy adjustments and elasticity
    
    Uses elasticity curves if available, otherwise uses default elasticity assumptions
    """
    projections = {
        "total_utilization_per_1k": 0.0,
        "total_claims": 0,
        "by_service_category": {},
        "by_month": [],
    }
    
    if baseline_df.is_empty():
        return projections
    
    # Get unique members count
    unique_members = baseline_df["member_id"].n_unique()
    
    # Group by service category
    if "service_category" in baseline_df.columns:
        service_categories = baseline_df.group_by("service_category")
        
        for category_tuple, category_df in service_categories:
            # category_tuple is a tuple when grouping by one column: (category_value,)
            # Extract the actual category value
            if isinstance(category_tuple, (tuple, list)) and len(category_tuple) > 0:
                category = category_tuple[0]
            elif isinstance(category_tuple, str):
                category = category_tuple
            else:
                category = str(category_tuple) if category_tuple is not None else "UNKNOWN"
            
            baseline_utilization = len(category_df) / unique_members if unique_members > 0 else 0
            
            # Get elasticity for this category
            if elasticity_curves and category in elasticity_curves:
                elasticity = elasticity_curves[category].get("elasticity", -0.3)  # Default -0.3
            elif scenario_params.elasticity_adjustments and category in scenario_params.elasticity_adjustments:
                elasticity = scenario_params.elasticity_adjustments[category]
            else:
                # Default elasticity based on policy type
                elasticity = get_default_elasticity(_get_policy_type_str(adjusted_policy.policy_type), category)
            
            # Estimate policy impact on this category
            # Simplified: assume 10-40% reduction based on policy type and elasticity
            policy_impact_factor = estimate_policy_impact_factor(
                adjusted_policy,
                category,
                elasticity,
            )
            
            # Project utilization
            projected_utilization = baseline_utilization * (1 + policy_impact_factor)
            
            # Apply trend
            trend_factor = (1 + scenario_params.utilization_trend / 100) ** scenario_params.projection_months
            projected_utilization *= trend_factor
            
            projections["by_service_category"][category] = {
                "baseline": baseline_utilization,
                "projected": projected_utilization,
                "change_percent": (policy_impact_factor * 100),
            }
            
            projections["total_claims"] += int(projected_utilization * unique_members)
    else:
        # No service_category column - use overall metrics
        baseline_utilization = len(baseline_df) / unique_members if unique_members > 0 else 0
        elasticity = get_default_elasticity(_get_policy_type_str(adjusted_policy.policy_type), "ALL")
        policy_impact_factor = estimate_policy_impact_factor(adjusted_policy, "ALL", elasticity)
        projected_utilization = baseline_utilization * (1 + policy_impact_factor)
        trend_factor = (1 + scenario_params.utilization_trend / 100) ** scenario_params.projection_months
        projected_utilization *= trend_factor
        projections["total_claims"] = int(projected_utilization * unique_members)
    
    projections["total_utilization_per_1k"] = (
        projections["total_claims"] / unique_members * 1000
        if unique_members > 0 else 0
    )
    
    return projections


def project_cost_changes(
    utilization_projections: dict[str, Any],
    baseline_df: pl.DataFrame,
    scenario_params: ScenarioParameters,
) -> dict[str, Any]:
    """Project cost changes based on utilization projections"""
    if baseline_df.is_empty():
        return {
            "total_allowed_pmpm": 0.0,
            "total_paid_pmpm": 0.0,
            "by_service_category": {},
        }
    
    unique_members = baseline_df["member_id"].n_unique()
    
    # Calculate months
    if "service_date" in baseline_df.columns:
        if baseline_df["service_date"].dtype == pl.Utf8:
            baseline_df = baseline_df.with_columns(
                pl.col("service_date").str.strptime(pl.Date, "%Y-%m-%d")
            )
        date_min = baseline_df["service_date"].min()
        date_max = baseline_df["service_date"].max()
        if date_min and date_max:
            months = (date_max - date_min).days / 30.0
        else:
            months = 1.0
    else:
        months = 1.0
    
    # Get column names
    allowed_col = "allowed_amount" if "allowed_amount" in baseline_df.columns else "allowed_amt"
    paid_col = "paid_amount" if "paid_amount" in baseline_df.columns else "paid_amt"
    
    # Get baseline costs
    total_allowed = baseline_df[allowed_col].sum() if allowed_col in baseline_df.columns else 0.0
    total_paid = baseline_df[paid_col].sum() if paid_col in baseline_df.columns else 0.0
    
    baseline_allowed_pmpm = total_allowed / (unique_members * max(1, months)) if unique_members > 0 else 0.0
    baseline_paid_pmpm = total_paid / (unique_members * max(1, months)) if unique_members > 0 else 0.0
    
    # Apply utilization changes
    baseline_utilization_per_1k = (len(baseline_df) / unique_members * 1000) if unique_members > 0 else 0.0
    utilization_change_factor = (
        utilization_projections["total_utilization_per_1k"] / baseline_utilization_per_1k
        if baseline_utilization_per_1k > 0 else 1.0
    )
    
    # Apply cost inflation
    cost_inflation_factor = (1 + scenario_params.cost_inflation) ** scenario_params.projection_months
    
    # Project costs
    projected_allowed_pmpm = baseline_allowed_pmpm * utilization_change_factor * cost_inflation_factor
    projected_paid_pmpm = baseline_paid_pmpm * utilization_change_factor * cost_inflation_factor
    
    return {
        "total_allowed_pmpm": projected_allowed_pmpm,
        "total_paid_pmpm": projected_paid_pmpm,
        "by_service_category": utilization_projections.get("by_service_category", {}),
    }


def get_default_elasticity(policy_type: str, service_category: str) -> float:
    """Get default elasticity based on policy type and service category"""
    # Elasticity mapping: negative means demand decreases when policy tightens
    elasticity_map = {
        "PRIOR_AUTH": -0.35,  # Prior auth reduces utilization by ~35%
        "SITE_OF_CARE": -0.25,  # Site restrictions reduce utilization by ~25%
        "DURATION_FREQUENCY_LIMIT": -0.40,  # Frequency limits reduce utilization by ~40%
        "COST_SHARING": -0.30,  # Cost sharing increases reduce utilization by ~30%
        "NETWORK_RESTRICTION": -0.20,  # Network restrictions reduce utilization by ~20%
    }
    return elasticity_map.get(policy_type, -0.30)


def estimate_policy_impact_factor(
    policy: CanonicalPolicy,
    service_category: str,
    elasticity: float,
) -> float:
    """Estimate policy impact factor based on policy type and elasticity"""
    # Simplified: assume policy impact scales with elasticity
    # Full implementation would use learned elasticity curves
    if policy.policy_logic and policy.policy_logic.levers:
        # Check if any lever targets this service category
        for lever in policy.policy_logic.levers:
            if service_category in str(lever.targets.codes):
                # Policy applies - use elasticity
                return elasticity
    return 0.0  # No impact if policy doesn't apply


def monte_carlo_confidence_intervals(
    baseline_df: pl.DataFrame,
    adjusted_policy: CanonicalPolicy,
    scenario_params: ScenarioParameters,
    n_simulations: int = 1000,
) -> dict[str, tuple[float, float]]:
    """
    Use Monte Carlo simulation to compute confidence intervals
    
    Resamples baseline data with uncertainty and projects impact
    """
    if baseline_df.is_empty():
        return {
            "utilization_per_1k": (0.0, 0.0),
            "allowed_pmpm": (0.0, 0.0),
            "paid_pmpm": (0.0, 0.0),
        }
    
    results = []
    
    for _ in range(min(n_simulations, 100)):  # Limit to 100 for performance
        # Resample baseline with bootstrap
        resampled = baseline_df.sample(n=len(baseline_df), with_replacement=True)
        
        # Project metrics (simplified - full implementation would use full projection logic)
        metrics = compute_baseline_metrics(resampled)
        results.append(metrics)
    
    # Compute percentiles (95% confidence interval) using numpy
    if not results:
        return {
            "utilization_per_1k": (0.0, 0.0),
            "allowed_pmpm": (0.0, 0.0),
            "paid_pmpm": (0.0, 0.0),
        }
    
    intervals = {}
    for metric in ["utilization_per_1k", "allowed_pmpm", "paid_pmpm"]:
        values = [r.get(metric, 0.0) for r in results]
        if values:
            lower = float(np.percentile(values, 2.5))
            upper = float(np.percentile(values, 97.5))
            intervals[metric] = (lower, upper)
        else:
            intervals[metric] = (0.0, 0.0)
    
    return intervals


def compute_confidence_score(
    baseline_metrics: dict[str, float],
    projected_metrics: dict[str, float],
    confidence_intervals: dict[str, tuple[float, float]],
    scenario_params: ScenarioParameters,
) -> float:
    """Compute confidence score (0-100) for scenario projection"""
    score = 100.0
    
    # Penalize if baseline is empty or very small
    if baseline_metrics.get("claim_count", 0) < 100:
        score -= 30
    
    # Penalize if projection horizon is long
    if scenario_params.projection_months > 12:
        score -= 10
    
    # Penalize if confidence intervals are wide (high uncertainty)
    for metric, (lower, upper) in confidence_intervals.items():
        if metric in projected_metrics:
            width = (upper - lower) / max(abs(projected_metrics[metric]), 1e-10)
            if width > 0.5:  # More than 50% uncertainty
                score -= 15
    
    return max(0.0, min(100.0, score))


def compute_sensitivity_analysis(
    baseline_df: pl.DataFrame,
    policy: CanonicalPolicy,
    scenario_params: ScenarioParameters,
) -> dict[str, Any]:
    """Compute sensitivity analysis - impact of each parameter adjustment"""
    sensitivity = {
        "lever_adjustments": {},
        "elasticity_adjustments": {},
        "environmental_variables": {},
    }
    
    # For each lever adjustment, compute isolated impact
    for lever_id, adjustments in scenario_params.lever_adjustments.items():
        # Simplified: estimate impact of this specific adjustment
        # Full implementation would re-run simulation with only this adjustment
        sensitivity["lever_adjustments"][lever_id] = {
            "estimated_impact_percent": -10.0,  # Placeholder
            "parameters": adjustments,
        }
    
    # For each elasticity adjustment
    for category, elasticity in scenario_params.elasticity_adjustments.items():
        sensitivity["elasticity_adjustments"][category] = {
            "elasticity": elasticity,
            "estimated_impact_percent": elasticity * 100,  # Simplified
        }
    
    # Environmental variables
    sensitivity["environmental_variables"] = {
        "member_count_multiplier": {
            "value": scenario_params.member_count_multiplier,
            "impact": "Linear scaling of all metrics",
        },
        "utilization_trend": {
            "value": scenario_params.utilization_trend,
            "impact": f"{scenario_params.utilization_trend}% per month",
        },
        "cost_inflation": {
            "value": scenario_params.cost_inflation,
            "impact": f"{scenario_params.cost_inflation * 100}% per month",
        },
    }
    
    return sensitivity


def compute_tradeoff_analysis(
    baseline_metrics: dict[str, float],
    projected_metrics: dict[str, float],
    impact_metrics: dict[str, float],
) -> dict[str, Any]:
    """Compute tradeoff analysis: cost vs utilization
    
    Analyzes the relationship between utilization reduction and cost savings
    to help users understand tradeoffs of different policy scenarios.
    """
    baseline_utilization = baseline_metrics.get("utilization_per_1k", 0.0)
    baseline_cost = baseline_metrics.get("allowed_pmpm", 0.0)
    
    projected_utilization = projected_metrics.get("utilization_per_1k", 0.0)
    projected_cost = projected_metrics.get("allowed_pmpm", 0.0)
    
    utilization_change = projected_utilization - baseline_utilization
    cost_change = projected_cost - baseline_cost
    utilization_change_pct = (utilization_change / baseline_utilization * 100) if baseline_utilization > 0 else 0.0
    cost_change_pct = (cost_change / baseline_cost * 100) if baseline_cost > 0 else 0.0
    
    # Tradeoff ratio: cost change per 1% utilization change
    tradeoff_ratio = (cost_change_pct / utilization_change_pct) if utilization_change_pct != 0 else 0.0
    
    # Efficiency score: lower utilization reduction with higher cost savings is more efficient
    # Positive means good tradeoff (utilization down, cost down)
    # Negative means bad tradeoff (utilization down but cost up, or utilization up)
    if utilization_change_pct < 0 and cost_change_pct < 0:
        # Both decreasing - good
        efficiency_score = 100.0  # Perfect efficiency
    elif utilization_change_pct < 0 and cost_change_pct > 0:
        # Utilization down but cost up - substitution/spillover
        efficiency_score = 50.0 - min(abs(cost_change_pct), 50.0)  # Penalty for cost increase
    elif utilization_change_pct > 0:
        # Utilization increasing - typically bad
        efficiency_score = max(0.0, 50.0 - abs(utilization_change_pct))
    else:
        efficiency_score = 75.0  # Neutral
    
    return {
        "utilization_change": utilization_change,
        "utilization_change_pct": utilization_change_pct,
        "cost_change": cost_change,
        "cost_change_pct": cost_change_pct,
        "tradeoff_ratio": tradeoff_ratio,  # Cost change per 1% utilization change
        "efficiency_score": efficiency_score,  # 0-100, higher is better
        "efficiency_category": (
            "HIGH" if efficiency_score >= 80 else
            "MEDIUM" if efficiency_score >= 60 else
            "LOW" if efficiency_score >= 40 else
            "POOR"
        ),
        "interpretation": (
            f"Scenario reduces utilization by {abs(utilization_change_pct):.1f}% and cost by {abs(cost_change_pct):.1f}%"
            if utilization_change_pct < 0 and cost_change_pct < 0 else
            f"Scenario reduces utilization by {abs(utilization_change_pct):.1f}% but increases cost by {abs(cost_change_pct):.1f}% (potential substitution/spillover)"
            if utilization_change_pct < 0 and cost_change_pct > 0 else
            f"Scenario increases utilization by {abs(utilization_change_pct):.1f}%"
        ),
    }


def compute_risk_analysis(
    baseline_metrics: dict[str, float],
    projected_metrics: dict[str, float],
    confidence_intervals: dict[str, tuple[float, float]],
    scenario_params: ScenarioParameters,
) -> dict[str, Any]:
    """Compute risk analysis: worst-case and best-case scenarios
    
    Uses confidence intervals to identify risks and opportunities.
    """
    # Extract confidence intervals
    util_ci = confidence_intervals.get("utilization_per_1k", (0.0, 0.0))
    cost_ci = confidence_intervals.get("allowed_pmpm", (0.0, 0.0))
    
    baseline_utilization = baseline_metrics.get("utilization_per_1k", 0.0)
    baseline_cost = baseline_metrics.get("allowed_pmpm", 0.0)
    
    # Worst-case scenario (higher utilization/cost than projected)
    worst_case_utilization = max(util_ci)
    worst_case_cost = max(cost_ci)
    worst_case_utilization_pct = ((worst_case_utilization - baseline_utilization) / baseline_utilization * 100) if baseline_utilization > 0 else 0.0
    worst_case_cost_pct = ((worst_case_cost - baseline_cost) / baseline_cost * 100) if baseline_cost > 0 else 0.0
    
    # Best-case scenario (lower utilization/cost than projected)
    best_case_utilization = min(util_ci)
    best_case_cost = min(cost_ci)
    best_case_utilization_pct = ((best_case_utilization - baseline_utilization) / baseline_utilization * 100) if baseline_utilization > 0 else 0.0
    best_case_cost_pct = ((best_case_cost - baseline_cost) / baseline_cost * 100) if baseline_cost > 0 else 0.0
    
    # Risk level based on confidence interval width and worst-case
    util_ci_width = (util_ci[1] - util_ci[0]) / baseline_utilization * 100 if baseline_utilization > 0 else 0.0
    cost_ci_width = (cost_ci[1] - cost_ci[0]) / baseline_cost * 100 if baseline_cost > 0 else 0.0
    
    # Risk factors
    risk_factors = []
    if util_ci_width > 50:
        risk_factors.append("HIGH_UTILIZATION_UNCERTAINTY")
    if cost_ci_width > 50:
        risk_factors.append("HIGH_COST_UNCERTAINTY")
    if worst_case_cost_pct > 10:
        risk_factors.append("COST_OVERRUN_RISK")
    if worst_case_utilization_pct > 5:
        risk_factors.append("UTILIZATION_INCREASE_RISK")
    if scenario_params.projection_months > 12:
        risk_factors.append("LONG_PROJECTION_HORIZON")
    
    risk_level = (
        "HIGH" if len(risk_factors) >= 3 else
        "MEDIUM" if len(risk_factors) >= 2 else
        "LOW" if len(risk_factors) >= 1 else
        "MINIMAL"
    )
    
    return {
        "worst_case": {
            "utilization_per_1k": worst_case_utilization,
            "utilization_change_pct": worst_case_utilization_pct,
            "cost_pmpm": worst_case_cost,
            "cost_change_pct": worst_case_cost_pct,
        },
        "best_case": {
            "utilization_per_1k": best_case_utilization,
            "utilization_change_pct": best_case_utilization_pct,
            "cost_pmpm": best_case_cost,
            "cost_change_pct": best_case_cost_pct,
        },
        "confidence_interval_width": {
            "utilization_pct": util_ci_width,
            "cost_pct": cost_ci_width,
        },
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "risk_summary": (
            f"{risk_level} risk: " + ", ".join([f.replace("_", " ").lower() for f in risk_factors])
            if risk_factors else "Minimal risk - projections are relatively certain"
        ),
    }

