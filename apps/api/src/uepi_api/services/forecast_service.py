"""Forecast service - Database only"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, date, timedelta
import math

from uepi_api.storage_observations import get_observations_for_policy
from uepi_api.storage_policy_predicted_impact import get_predicted_impact
from uepi_api.storage_baselines import get_latest_baseline


def calculate_forecast(
    tenant_id: UUID,
    policy_id: UUID,
    observed_values: List[Dict[str, Any]],
    predicted_value: float,
    baseline_value: float,
    time_horizon_months: int = 12,
    metric_type: str = "utilization",
) -> Dict[str, Any]:
    """
    Calculate forecast based on observed trends and predicted target
    
    Args:
        tenant_id: Tenant ID
        policy_id: Policy ID
        observed_values: List of historical observations with metrics
        predicted_value: Original predicted value (utilization or cost)
        baseline_value: Baseline value
        time_horizon_months: Number of months to forecast ahead
        
    Returns:
        Forecast data with values, convergence metrics, and insights
    """
    if not observed_values:
        return {
            "forecast_values": [],
            "convergence_date": None,
            "convergence_rate": 0.0,
            "trend_direction": "insufficient_data",
            "forecast_accuracy_at_6m": None,
            "insights": ["Insufficient historical data for forecast"],
        }
    
    # Extract utilization and cost values from observations
    utilization_values = []
    cost_values = []
    observation_dates = []
    
    for obs in observed_values:
        metrics = obs.get("metrics", {})
        computed_at = obs.get("computed_at")
        
        util = metrics.get("utilization_per_1k", 0.0) or 0.0
        cost = metrics.get("cost_pmpm", 0.0) or metrics.get("cost_per_member", 0.0) or 0.0
        
        if util > 0 or cost > 0:  # Only include valid observations
            utilization_values.append(util)
            cost_values.append(cost)
            if computed_at:
                if isinstance(computed_at, str):
                    observation_dates.append(datetime.fromisoformat(computed_at.replace("Z", "+00:00")))
                else:
                    observation_dates.append(computed_at)
    
    # Use correct metric based on metric_type
    if metric_type == "cost":
        metric_values = cost_values
    else:
        metric_values = utilization_values
    
    if len(metric_values) < 2:
        return {
            "forecast_values": [],
            "convergence_date": None,
            "convergence_rate": 0.0,
            "trend_direction": "insufficient_data",
            "forecast_accuracy_at_6m": None,
            "insights": ["Need at least 2 observations for forecast"],
        }
    
    # Calculate trend from observed values (linear regression) using the selected metric
    n = len(metric_values)
    latest_value = metric_values[-1]
    
    # Simple linear trend: slope = (last - first) / (n - 1)
    if n >= 2:
        trend_slope = (metric_values[-1] - metric_values[0]) / (n - 1) if n > 1 else 0.0
    else:
        trend_slope = 0.0
    
    # Project forward using trend
    forecast_values = []
    current_date = datetime.now()
    
    for month in range(1, time_horizon_months + 1):
        # Trend projection
        trend_projection = latest_value + (trend_slope * month)
        
        # Blend with predicted target (weighted average)
        # More weight on trend early, more weight on prediction later
        trend_weight = max(0.0, 1.0 - (month / time_horizon_months))
        prediction_weight = 1.0 - trend_weight
        
        blended_forecast = (trend_projection * trend_weight) + (predicted_value * prediction_weight)
        forecast_values.append({
            "month": month,
            "forecast_value": blended_forecast,
            "trend_projection": trend_projection,
            "predicted_target": predicted_value,
            "trend_weight": trend_weight,
            "prediction_weight": prediction_weight,
        })
    
    # Calculate convergence metrics
    convergence_rate = abs(predicted_value - latest_value) / time_horizon_months if time_horizon_months > 0 else 0.0
    convergence_date = None
    trend_direction = "away_from_prediction"
    
    if trend_slope != 0:
        if (trend_slope > 0 and latest_value < predicted_value) or \
           (trend_slope < 0 and latest_value > predicted_value):
            # Trending toward prediction
            months_to_converge = abs(predicted_value - latest_value) / abs(trend_slope) if abs(trend_slope) > 0 else None
            if months_to_converge and months_to_converge <= time_horizon_months:
                convergence_date = (current_date + timedelta(days=months_to_converge * 30)).isoformat()
                trend_direction = "toward_prediction"
    
    # Calculate forecast accuracy at 6 months
    forecast_accuracy_at_6m = None
    if len(forecast_values) >= 6:
        forecast_6m = forecast_values[5]["forecast_value"]
        if predicted_value != 0:
            error_pct = abs(forecast_6m - predicted_value) / abs(predicted_value) * 100
            forecast_accuracy_at_6m = max(0.0, 100.0 - min(error_pct, 200.0))
    
    # Generate insights
    insights = []
    if trend_direction == "toward_prediction":
        insights.append("Observed values are trending toward predicted target")
        if convergence_date:
            insights.append(f"Expected convergence in approximately {math.ceil((datetime.fromisoformat(convergence_date.replace('Z', '+00:00')) - current_date).days / 30)} months")
    elif trend_direction == "away_from_prediction":
        insights.append("Observed values are diverging from predicted target")
        insights.append("Prediction may need review or policy adjustment")
    
    if abs(trend_slope) < 0.1:
        insights.append("Trend is relatively stable - policy effect may have stabilized")
    
    if forecast_accuracy_at_6m and forecast_accuracy_at_6m > 70:
        insights.append("Forecast indicates good alignment with prediction at 6 months")
    elif forecast_accuracy_at_6m and forecast_accuracy_at_6m < 50:
        insights.append("Forecast indicates significant deviation from prediction at 6 months")
    
    return {
        "forecast_values": forecast_values,
        "convergence_date": convergence_date,
        "convergence_rate": convergence_rate,
        "trend_direction": trend_direction,
        "forecast_accuracy_at_6m": forecast_accuracy_at_6m,
        "trend_slope": trend_slope,
        "latest_observed": latest_value,
        "predicted_target": predicted_value,
        "baseline_value": baseline_value,
        "insights": insights,
    }


def get_forecast_for_observation(
    tenant_id: UUID,
    policy_id: UUID,
    observation_id: str,
    metric_type: str = "utilization",  # "utilization" or "cost"
    time_horizon_months: int = 12,
) -> Dict[str, Any]:
    """
    Get forecast for a specific observation
    
    Args:
        tenant_id: Tenant ID
        policy_id: Policy ID
        observation_id: Observation ID
        metric_type: Type of metric to forecast ("utilization" or "cost")
        time_horizon_months: Number of months to forecast ahead
        
    Returns:
        Forecast data
    """
    from uepi_api.storage_observations import get_observation
    
    # Get current observation
    observation = get_observation(tenant_id, observation_id)
    if not observation:
        return {
            "error": "Observation not found",
        }
    
    # Get all observations for this policy (historical data)
    all_observations = get_observations_for_policy(tenant_id, policy_id)
    
    # Sort by computed_at date
    all_observations.sort(key=lambda x: x.get("computed_at", ""))
    
    # Get predicted impact
    predicted_impact = get_predicted_impact(policy_id, tenant_id)
    if not predicted_impact:
        return {
            "error": "Predicted impact not found",
        }
    
    # Get baseline
    baseline = get_latest_baseline(tenant_id, policy_id=policy_id)
    baseline_metrics = baseline.get("baseline_metrics", {}) if baseline else {}
    
    # Extract values based on metric type
    if metric_type == "utilization":
        predicted_value = None
        vs_predicted = observation.get("comparisons", {}).get("vs_predicted", {})
        if vs_predicted:
            predicted_value = vs_predicted.get("predicted_utilization_per_1k")
        
        if not predicted_value:
            # Calculate from predicted impact
            pred_metrics = predicted_impact.get("metrics", {})
            baseline_util = baseline_metrics.get("util_rate_target_per_1000_mm") or baseline_metrics.get("util_rate_total_per_1000_mm", 0.0)
            utilization_change = pred_metrics.get("utilization_change_per_1k", 0.0)
            predicted_value = baseline_util + utilization_change
        
        baseline_value = baseline_metrics.get("util_rate_target_per_1000_mm") or baseline_metrics.get("util_rate_total_per_1000_mm", 0.0)
    else:  # cost
        predicted_value = None
        vs_predicted = observation.get("comparisons", {}).get("vs_predicted", {})
        if vs_predicted:
            predicted_value = vs_predicted.get("predicted_cost_pmpm")
        
        if not predicted_value:
            # Calculate from predicted impact
            pred_metrics = predicted_impact.get("metrics", {})
            baseline_cost = baseline_metrics.get("paid_pmpm_target") or baseline_metrics.get("allowed_pmpm_target") or baseline_metrics.get("paid_pmpm_total") or baseline_metrics.get("allowed_pmpm_total", 0.0)
            cost_change = pred_metrics.get("cost_change_pmpm", 0.0)
            predicted_value = baseline_cost + cost_change
        
        baseline_value = baseline_metrics.get("paid_pmpm_target") or baseline_metrics.get("allowed_pmpm_target") or baseline_metrics.get("paid_pmpm_total") or baseline_metrics.get("allowed_pmpm_total", 0.0)
    
    if predicted_value is None:
        return {
            "error": "Could not determine predicted value",
        }
    
    # Calculate forecast
    forecast = calculate_forecast(
        tenant_id=tenant_id,
        policy_id=policy_id,
        observed_values=all_observations,
        predicted_value=predicted_value,
        baseline_value=baseline_value,
        time_horizon_months=time_horizon_months,
        metric_type=metric_type,
    )
    
    return forecast
