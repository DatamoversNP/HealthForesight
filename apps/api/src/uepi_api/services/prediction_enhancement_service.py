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
    
    pred_metrics = predicted_impact.get("metrics") or {}
    raw_confidence = predicted_impact.get("confidence")
    confidence_score = None if raw_confidence is None else float(raw_confidence)
    prediction_method = predicted_impact.get("prediction_method") or "UNAVAILABLE"

    def _present_float(source: Dict[str, Any], *keys: str) -> Optional[float]:
        for key in keys:
            if key in source and source.get(key) is not None:
                return float(source[key])
        return None

    baseline_utilization = _present_float(
        baseline_metrics,
        "util_rate_target_per_1000_mm",
        "util_rate_total_per_1000_mm",
        "utilization_per_1k",
    )
    baseline_cost_pmpm = _present_float(
        baseline_metrics,
        "paid_pmpm_target",
        "allowed_pmpm_target",
        "paid_pmpm_total",
        "allowed_pmpm_total",
        "cost_pmpm",
    )
    utilization_change = _present_float(pred_metrics, "utilization_change_per_1k", "utilization_change")
    cost_change_pmpm = _present_float(pred_metrics, "cost_change_pmpm", "cost_change")
    unavailable = {
        "status": "UNAVAILABLE",
        "reason": "Baseline, predicted change, or confidence is missing. No stand-in rate or confidence is used.",
    }
    enhanced = predicted_impact.copy()
    enhanced["confidence"] = confidence_score
    if baseline_utilization is None or utilization_change is None or confidence_score is None:
        enhanced["confidence_intervals"] = {"utilization": unavailable, "cost": unavailable}
        enhanced["ramp_up_projections"] = {"utilization": unavailable, "cost": unavailable}
        return enhanced
    if baseline_cost_pmpm is None or cost_change_pmpm is None:
        cost_confidence = unavailable
        cost_ramp_up = unavailable
    else:
        predicted_cost_pmpm = baseline_cost_pmpm + cost_change_pmpm
        cost_confidence = calculate_confidence_intervals(
            predicted_value=predicted_cost_pmpm,
            confidence_score=confidence_score,
            baseline_value=baseline_cost_pmpm,
            prediction_method=prediction_method,
        )
        cost_ramp_up = calculate_time_based_ramp_up(
            baseline_value=baseline_cost_pmpm,
            full_effect_value=predicted_cost_pmpm,
            months=12,
        )
    predicted_utilization = baseline_utilization + utilization_change
    enhanced["confidence_intervals"] = {
        "utilization": calculate_confidence_intervals(
            predicted_value=predicted_utilization,
            confidence_score=confidence_score,
            baseline_value=baseline_utilization,
            prediction_method=prediction_method,
        ),
        "cost": cost_confidence,
    }
    enhanced["ramp_up_projections"] = {
        "utilization": calculate_time_based_ramp_up(
            baseline_value=baseline_utilization,
            full_effect_value=predicted_utilization,
            months=12,
        ),
        "cost": cost_ramp_up,
    }
    return enhanced
