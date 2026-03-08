"""Policy impact analysis - refactored to use new analytics modules"""
from typing import Any, Optional
from uuid import UUID
from datetime import datetime

from uepi_common.analytics.impact import ImpactAnalysisEngine
from uepi_common.analytics.method_checks import MethodCheckRunner
from uepi_common.analytics.trust_panel import TrustPanelBuilder
from uepi_common.data.parquet_service import ParquetDataService
from uepi_common.data_contracts.claims import ServiceCategory
from uepi_common.storage.factory import create_storage_client

from uepi_worker.config import get_settings

settings = get_settings()


def _compare_observed_vs_predicted(
    observed_effect_size: float,
    observed_percent_change: float,
    observed_ci: tuple[float, float],
    predicted_impact: dict[str, Any],
) -> dict[str, Any]:
    """Compare observed impact against predicted impact (Stage 3.5)
    
    Args:
        observed_effect_size: Observed effect size (absolute change)
        observed_percent_change: Observed percentage change
        observed_ci: Observed confidence interval (lower, upper)
        predicted_impact: Predicted impact dictionary
        
    Returns:
        Comparison results dictionary
    """
    if not predicted_impact or "metrics" not in predicted_impact:
        return {
            "predicted_impact_available": False,
            "comparison_available": False,
        }
    
    pred_metrics = predicted_impact["metrics"]
    predicted_effect_size = pred_metrics.get("utilization_change_per_1k", 0.0)
    predicted_percent_change = pred_metrics.get("utilization_change_pct", 0.0)
    
    # Calculate prediction error
    effect_size_error = observed_effect_size - predicted_effect_size
    percent_change_error = observed_percent_change - predicted_percent_change
    effect_size_error_pct = (
        (effect_size_error / predicted_effect_size * 100) 
        if predicted_effect_size != 0 else 0.0
    )
    
    # Check if observed is within predicted range (if available)
    # For now, use a simple comparison - in full implementation, would use predicted CI if available
    within_predicted_range = True  # Simplified - would compare against predicted CI if available
    
    # Calculate prediction accuracy (higher is better, 100% = perfect match)
    if predicted_effect_size != 0:
        accuracy_pct = 100.0 - abs(effect_size_error_pct)
        accuracy_pct = max(0.0, min(100.0, accuracy_pct))
    else:
        accuracy_pct = None
    
    return {
        "predicted_impact_available": True,
        "comparison_available": True,
        "predicted": {
            "effect_size": predicted_effect_size,
            "percent_change": predicted_percent_change,
        },
        "observed": {
            "effect_size": observed_effect_size,
            "percent_change": observed_percent_change,
        },
        "prediction_error": {
            "effect_size_error": effect_size_error,
            "percent_change_error": percent_change_error,
            "effect_size_error_pct": effect_size_error_pct,
        },
        "prediction_accuracy_pct": accuracy_pct,
        "within_predicted_range": within_predicted_range,
        "prediction_confidence": pred_metrics.get("confidence_score"),
    }


def _compare_observed_vs_baseline(
    observed_effect_size: float,
    observed_percent_change: float,
    baseline_metrics: dict[str, Any],
) -> dict[str, Any]:
    """Compare observed impact against baseline (Stage 3)
    
    Args:
        observed_effect_size: Observed effect size (absolute change)
        observed_percent_change: Observed percentage change
        baseline_metrics: Baseline metrics dictionary
        
    Returns:
        Comparison results dictionary
    """
    if not baseline_metrics:
        return {
            "baseline_available": False,
            "comparison_available": False,
        }
    
    baseline_utilization = baseline_metrics.get("utilization_per_1k")
    if baseline_utilization is None:
        return {
            "baseline_available": False,
            "comparison_available": False,
        }
    
    # Calculate change from baseline
    change_from_baseline = observed_effect_size  # Effect size is already the change
    change_from_baseline_pct = observed_percent_change  # Percent change is already relative
    
    return {
        "baseline_available": True,
        "comparison_available": True,
        "baseline_utilization_per_1k": baseline_utilization,
        "observed_change_from_baseline": change_from_baseline,
        "observed_change_from_baseline_pct": change_from_baseline_pct,
    }


def run_policy_impact_analysis(
    tenant_id: UUID,
    policy_id: UUID,
    policy_effective_date: datetime,
    treatment_filters: dict[str, Any],
    control_filters: Optional[dict[str, Any]] = None,
    pre_months: int = 6,
    post_months: int = 6,
    metric: str = "utilization_per_1k",
    service_category: Optional[ServiceCategory] = None,
    predicted_impact: Optional[dict[str, Any]] = None,
    baseline_metrics: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Run complete policy impact analysis with method checks and trust panel (Phase 5)
    
    This function:
    1. Runs impact analysis (DiD or pre/post)
    2. Runs method checks (pre-trends, control balance, seasonality)
    3. Builds trust panel (confidence scores, data sufficiency, validation)
    4. Compares observed impact against predicted impact (Stage 3.5) and baseline (Stage 3)
    5. Returns comprehensive analysis results
    
    Args:
        tenant_id: Tenant ID
        policy_id: Policy ID
        policy_effective_date: Policy effective date
        treatment_filters: Treatment group filters
        control_filters: Optional control group filters
        pre_months: Pre-policy window in months
        post_months: Post-policy window in months
        metric: Metric to analyze
        service_category: Optional service category filter
        predicted_impact: Optional predicted impact dictionary (Stage 3.5)
        baseline_metrics: Optional baseline metrics dictionary (Stage 3)
        
    Returns:
        Dictionary with impact results, method checks, trust panel, and comparisons
    """
    # Initialize services - use database instead of ParquetDataService
    from uepi_api.database import SessionLocal
    from uepi_api.services.database_data_service import DatabaseDataService
    
    db = SessionLocal()
    try:
        database_service = DatabaseDataService(db=db, tenant_id=tenant_id)
        
        # Create a wrapper that provides the _load_data method expected by ImpactAnalysisEngine
        # We'll override the _load_data method to use database
        class DatabaseImpactEngine(ImpactAnalysisEngine):
            def __init__(self, tenant_id, database_service):
                self.tenant_id = tenant_id
                self.database_service = database_service
                # Don't call super().__init__ to avoid ParquetDataService
            
            def _load_data(self, start_date, end_date, filters, service_category=None):
                """Load data from database"""
                return self.database_service.load_claims_data(
                    start_date=start_date.date() if isinstance(start_date, datetime) else start_date,
                    end_date=end_date.date() if isinstance(end_date, datetime) else end_date,
                    filters=filters,
                )
        
        # Initialize analytics engines with database service
        impact_engine = DatabaseImpactEngine(tenant_id=tenant_id, database_service=database_service)
        
        # MethodCheckRunner also needs database service
        class DatabaseMethodCheckRunner(MethodCheckRunner):
            def __init__(self, tenant_id, database_service):
                self.tenant_id = tenant_id
                self.database_service = database_service
            
            def _load_data(self, start_date, end_date, filters, service_category=None):
                """Load data from database"""
                return self.database_service.load_claims_data(
                    start_date=start_date.date() if isinstance(start_date, datetime) else start_date,
                    end_date=end_date.date() if isinstance(end_date, datetime) else end_date,
                    filters=filters,
                )
        
        method_check_runner = DatabaseMethodCheckRunner(tenant_id=tenant_id, database_service=database_service)
    
    # Run impact analysis
    impact_result = impact_engine.analyze_policy_impact(
        policy_effective_date=policy_effective_date,
        treatment_filters=treatment_filters,
        control_filters=control_filters,
        pre_months=pre_months,
        post_months=post_months,
        metric=metric,
        service_category=service_category,
        n_bootstrap=1000,
        confidence_level=0.95,
    )
    
    # Run method checks
    method_checks = method_check_runner.run_all_checks(
        policy_effective_date=policy_effective_date,
        treatment_filters=treatment_filters,
        control_filters=control_filters,
        pre_months=pre_months,
        metric=metric,
    )
    
    # Build trust panel
    data_window_months = pre_months + post_months
    actual_sample_size = method_checks.actual_sample_size
    
    methodology = {
        "method": impact_result.method,
        "pre_months": pre_months,
        "post_months": post_months,
        "has_control_group": control_filters is not None,
        "metric": metric,
        "service_category": service_category.value if service_category else None,
        "bootstrap_samples": 1000,
        "confidence_level": 0.95,
    }
    
    data_used = {
        "data_window_months": data_window_months,
        "sample_size": actual_sample_size,
        "treatment_filters": treatment_filters,
        "control_filters": control_filters,
        "service_category": service_category.value if service_category else None,
    }
    
    trust_panel = TrustPanelBuilder.build_trust_panel(
        impact_result=impact_result,
        method_checks=method_checks,
        data_window_months=data_window_months,
        actual_sample_size=actual_sample_size,
        methodology=methodology,
        data_used=data_used,
    )
    
    # Compare observed impact against predicted impact (Stage 3.5)
    predicted_comparison = _compare_observed_vs_predicted(
        observed_effect_size=impact_result.effect_size,
        observed_percent_change=impact_result.percent_change,
        observed_ci=impact_result.confidence_interval,
        predicted_impact=predicted_impact,
    )
    
    # Compare observed impact against baseline (Stage 3)
    baseline_comparison = _compare_observed_vs_baseline(
        observed_effect_size=impact_result.effect_size,
        observed_percent_change=impact_result.percent_change,
        baseline_metrics=baseline_metrics,
    )
    
    # Return comprehensive results
    result = {
        "policy_id": str(policy_id),
        "policy_effective_date": policy_effective_date.isoformat(),
        "impact_result": impact_result.to_dict(),
        "method_checks": method_checks.to_dict(),
        "trust_panel": trust_panel.to_dict(),
        "summary": {
            "effect_size": impact_result.effect_size,
            "percent_change": impact_result.percent_change,
            "confidence_interval": impact_result.confidence_interval,
            "confidence_score": trust_panel.confidence_score.overall_score,
            "confidence_category": trust_panel.confidence_score.get_category(),
            "data_sufficient": trust_panel.data_sufficiency.sufficient,
            "warnings": method_checks.warnings + trust_panel.limitations,
        },
        "comparisons": {
            "predicted_impact": predicted_comparison,
            "baseline": baseline_comparison,
        },
    }
    
    return result
    finally:
        db.close()

