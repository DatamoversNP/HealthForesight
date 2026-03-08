"""Prediction enhancement service - Database only"""
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
import math

from uepi_api.storage_baselines import get_latest_baseline
from uepi_api.storage_policy_predicted_impact import get_predicted_impact


def calculate_confidence_intervals(
    predicted_value: float,
    confidence_score: float,
    baseline_value: float,
    prediction_method: str = "ELASTICITY_MODEL",
) -> Dict[str, Any]:
    """
    Calculate confidence intervals for a predicted value
    
    Args:
        predicted_value: Predicted value (utilization or cost)
        confidence_score: Confidence score (0.0-1.0 or 0-100)
        baseline_value: Baseline value for reference
        prediction_method: Method used for prediction
        
    Returns:
        Confidence interval data
    """
    # Normalize confidence score to 0-1 range
    if confidence_score > 1.0:
        confidence_score = confidence_score / 100.0
    
    # Calculate uncertainty based on confidence score
    # Lower confidence = wider interval
    uncertainty_factor = 1.0 - confidence_score
    
    # Base uncertainty percentage (adjust based on prediction method)
    base_uncertainty_pct = {
        "ELASTICITY_MODEL": 15.0,  # 15% base uncertainty for elasticity models
        "DEFAULT_MODEL": 25.0,     # 25% base uncertainty for default models
        "HISTORICAL": 20.0,        # 20% base uncertainty for historical models
        "ML": 12.0,                # 12% base uncertainty for ML models
    }.get(prediction_method, 20.0)
    
    # Calculate interval width
    interval_width_pct = base_uncertainty_pct * (1.0 + uncertainty_factor)
    
    # Calculate absolute interval
    interval_width = abs(predicted_value) * (interval_width_pct / 100.0)
    
    # Ensure minimum interval (at least 5% of baseline if baseline > 0)
    if baseline_value > 0:
        min_interval = baseline_value * 0.05
        interval_width = max(interval_width, min_interval)
    
    lower_bound = predicted_value - interval_width
    upper_bound = predicted_value + interval_width
    
    # Ensure non-negative for utilization/cost
    if lower_bound < 0:
        lower_bound = 0.0
    
    return {
        "predicted_value": predicted_value,
        "confidence_score": confidence_score,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "interval_width": interval_width,
        "interval_width_pct": interval_width_pct,
        "uncertainty_level": "low" if confidence_score > 0.8 else "medium" if confidence_score > 0.6 else "high",
    }


def calculate_time_based_ramp_up(
    baseline_value: float,
    full_effect_value: float,
    months: int = 12,
    metric_type: str = "level",
) -> Dict[str, Any]:
    """
    Calculate time-based ramp-up values for predictions.
    Industry standard: utilization (services per 1K member-months) and cost (PMPM) are non-negative.
    Values are clamped to >= 0 to avoid impossible negatives.

    Args:
        baseline_value: Baseline value before policy (services/1K or $ PMPM)
        full_effect_value: Predicted value at full effect (baseline + change)
        months: Number of months to project
        metric_type: "utilization" or "cost" - both require non-negative values

    Returns:
        Ramp-up values by month
    """
    full_effect_change = full_effect_value - baseline_value

    # Industry standard: utilization and cost levels cannot be negative
    # Clamp full_effect_value to non-negative (policy cannot create negative utilization/cost)
    full_effect_value_clamped = max(0.0, float(full_effect_value))
    baseline_value_safe = max(0.0, float(baseline_value))
    full_effect_change = full_effect_value_clamped - baseline_value_safe

    # Ramp-up curve: gradual effect over time (industry-standard adoption curve)
    # Month 1: 30% effect, Month 3: 70%, Month 6: 90%, Month 12+: 100%
    ramp_up_curve = {
        1: 0.3,
        2: 0.5,
        3: 0.7,
        4: 0.8,
        5: 0.85,
        6: 0.9,
        12: 1.0,
    }

    ramp_up_values = []
    for month in range(1, months + 1):
        if month <= 1:
            ramp_factor = ramp_up_curve[1]
        elif month <= 3:
            ramp_factor = ramp_up_curve[1] + (ramp_up_curve[3] - ramp_up_curve[1]) * ((month - 1) / 2.0)
        elif month <= 6:
            ramp_factor = ramp_up_curve[3] + (ramp_up_curve[6] - ramp_up_curve[3]) * ((month - 3) / 3.0)
        else:
            ramp_factor = ramp_up_curve[6] + (ramp_up_curve[12] - ramp_up_curve[6]) * ((month - 6) / 6.0) if month <= 12 else 1.0

        predicted_value_at_month = baseline_value_safe + (full_effect_change * ramp_factor)
        # Clamp to non-negative (industry standard for utilization and cost)
        predicted_value_at_month = max(0.0, predicted_value_at_month)

        ramp_up_values.append({
            "month": month,
            "ramp_factor": ramp_factor,
            "predicted_value": predicted_value_at_month,
            "effect_achieved_pct": ramp_factor * 100,
        })
    
    return {
        "baseline_value": baseline_value_safe,
        "full_effect_value": full_effect_value_clamped,
        "full_effect_change": full_effect_change,
        "ramp_up_values": ramp_up_values,
    }


def enhance_prediction_with_confidence_and_ramp_up(
    tenant_id: UUID,
    policy_id: UUID,
    predicted_impact: Dict[str, Any],
    baseline_metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Enhance predicted impact with confidence intervals and time-based ramp-up
    
    Args:
        tenant_id: Tenant ID
        policy_id: Policy ID
        predicted_impact: Predicted impact data
        baseline_metrics: Optional baseline metrics (if None, will fetch)
        
    Returns:
        Enhanced predicted impact with confidence intervals and ramp-up
    """
    # Get baseline if not provided (policy baselines are stored as ROLLING; look by policy_id only)
    if not baseline_metrics:
        baseline = get_latest_baseline(tenant_id, policy_id=policy_id, baseline_type=None)
        if not baseline:
            baseline = get_latest_baseline(tenant_id, policy_id=None)
        if baseline:
            baseline_metrics = baseline.get("baseline_metrics", {}) or baseline.get("metrics", {})
    
    if not baseline_metrics:
        baseline_metrics = {}
    
    pred_metrics = predicted_impact.get("metrics", {})
    confidence_score = predicted_impact.get("confidence", 0.7)  # Default 70% if not provided
    prediction_method = predicted_impact.get("prediction_method", "ELASTICITY_MODEL")
    
    # Get baseline values (industry standard: services per 1K member-months, $ PMPM)
    baseline_utilization = baseline_metrics.get("util_rate_target_per_1000_mm") or baseline_metrics.get("util_rate_total_per_1000_mm") or baseline_metrics.get("utilization_per_1k", 0.0)
    baseline_utilization = float(baseline_utilization or 0.0)
    baseline_cost_pmpm = baseline_metrics.get("paid_pmpm_target") or baseline_metrics.get("allowed_pmpm_target") or baseline_metrics.get("paid_pmpm_total") or baseline_metrics.get("allowed_pmpm_total") or baseline_metrics.get("cost_pmpm", 0.0)
    baseline_cost_pmpm = float(baseline_cost_pmpm or 0.0)

    # Industry-standard fallbacks when baseline is missing (HEDIS/NQF reference ranges)
    # Avoids division-by-zero and impossible negative predictions
    warnings_list = list(predicted_impact.get("warnings", []) or [])
    if baseline_utilization <= 0:
        baseline_utilization = max(baseline_utilization, 50.0)  # Fallback: ~50 services/1K (imaging typical)
        warnings_list.append("Baseline utilization was missing or zero; used industry fallback for ramp-up.")
    if baseline_cost_pmpm <= 0:
        baseline_cost_pmpm = max(baseline_cost_pmpm, 50.0)  # Fallback: $50 PMPM (imaging typical)
        warnings_list.append("Baseline cost PMPM was missing or zero; used industry fallback for ramp-up.")

    # Get predicted changes
    utilization_change = float(pred_metrics.get("utilization_change_per_1k", 0.0) or 0.0)
    cost_change_pmpm = float(pred_metrics.get("cost_change_pmpm", 0.0) or 0.0)

    # Calculate predicted values; clamp to non-negative (industry standard)
    predicted_utilization = max(0.0, baseline_utilization + utilization_change)
    predicted_cost_pmpm = max(0.0, baseline_cost_pmpm + cost_change_pmpm)
    
    # Calculate confidence intervals
    utilization_confidence = calculate_confidence_intervals(
        predicted_value=predicted_utilization,
        confidence_score=confidence_score,
        baseline_value=baseline_utilization,
        prediction_method=prediction_method,
    )
    
    cost_confidence = calculate_confidence_intervals(
        predicted_value=predicted_cost_pmpm,
        confidence_score=confidence_score,
        baseline_value=baseline_cost_pmpm,
        prediction_method=prediction_method,
    )
    
    # Calculate time-based ramp-up
    utilization_ramp_up = calculate_time_based_ramp_up(
        baseline_value=baseline_utilization,
        full_effect_value=predicted_utilization,
        months=12,
    )
    
    cost_ramp_up = calculate_time_based_ramp_up(
        baseline_value=baseline_cost_pmpm,
        full_effect_value=predicted_cost_pmpm,
        months=12,
    )
    
    # Enhance predicted impact
    enhanced = predicted_impact.copy()
    if warnings_list:
        existing = enhanced.get("warnings") or []
        enhanced["warnings"] = list(dict.fromkeys((existing if isinstance(existing, list) else []) + warnings_list))
    enhanced["confidence_intervals"] = {
        "utilization": utilization_confidence,
        "cost": cost_confidence,
    }
    enhanced["ramp_up_projections"] = {
        "utilization": utilization_ramp_up,
        "cost": cost_ramp_up,
    }
    
    return enhanced
