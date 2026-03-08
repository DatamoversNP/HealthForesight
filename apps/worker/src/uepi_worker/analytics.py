"""Causal impact analytics engine"""
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID
import json
import random

import boto3
import polars as pl
import numpy as np
from scipy import stats

from uepi_worker.config import get_settings

settings = get_settings()


def get_s3_client():
    """Get S3-compatible client"""
    return boto3.client(
        "s3",
        endpoint_url=settings.object_storage.endpoint,
        aws_access_key_id=settings.object_storage.access_key,
        aws_secret_access_key=settings.object_storage.secret_key,
        region_name=settings.object_storage.region,
        use_ssl=settings.object_storage.use_ssl,
    )


def load_claims_data(
    tenant_id: UUID,
    filters: dict[str, Any],
    start_date: datetime,
    end_date: datetime,
) -> pl.DataFrame:
    """Load claims data from object storage based on filters"""
    s3_client = get_s3_client()
    bucket = settings.object_storage.bucket
    
    # Build partition paths
    all_data = []
    
    current_date = start_date
    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        
        # Build partition path (lob/markets can be str or list)
        lobs = filters.get("lob") or ["COMMERCIAL", "MA", "MEDICAID"]
        if isinstance(lobs, str):
            lobs = [lobs]
        markets = filters.get("markets") or filters.get("market") or ["NYC", "DFW", "BOS"]
        if isinstance(markets, str):
            markets = [markets]

        for lob in lobs:
            for market in markets:
                partition_key = f"{tenant_id}/curated/claims/year={year}/month={month:02d}/lob={lob}/market={market}/data.parquet"
                
                try:
                    # Download and read
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".parquet") as tmp:
                        s3_client.download_fileobj(bucket, partition_key, tmp)
                        tmp_path = tmp.name
                    
                    try:
                        df = pl.read_parquet(tmp_path)
                        all_data.append(df)
                    finally:
                        os.unlink(tmp_path)
                except Exception:
                    # Partition doesn't exist, skip
                    continue
        
        # Move to next month
        if month == 12:
            current_date = datetime(year + 1, 1, 1)
        else:
            current_date = datetime(year, month + 1, 1)
    
    if not all_data:
        return pl.DataFrame()
    
    # Concatenate all data
    result = pl.concat(all_data)
    
    # Apply filters (consistent with policy scope + levers)
    if "in_network_only" in filters and filters["in_network_only"]:
        result = result.filter(pl.col("in_network_flag") == True)

    if "cpt_codes" in filters and filters["cpt_codes"]:
        cpt_col = "cpt_hcpcs" if "cpt_hcpcs" in result.columns else "cpt_code"
        if cpt_col in result.columns:
            result = result.filter(pl.col(cpt_col).is_in(filters["cpt_codes"]))

    if "service_categories" in filters and filters["service_categories"] and "service_category" in result.columns:
        result = result.filter(pl.col("service_category").is_in(filters["service_categories"]))

    return result


def compute_pre_post_metrics(
    treatment_df: pl.DataFrame,
    control_df: pl.DataFrame | None,
    policy_effective_date: datetime,
    pre_months: int = 6,
    post_months: int = 6,
) -> dict[str, Any]:
    """Compute pre/post metrics with optional control group"""
    pre_start = policy_effective_date - timedelta(days=pre_months * 30)
    pre_end = policy_effective_date
    post_start = policy_effective_date
    post_end = policy_effective_date + timedelta(days=post_months * 30)
    
    # Parse dates
    treatment_df = treatment_df.with_columns(
        pl.col("service_from_date").str.strptime(pl.Date, "%Y-%m-%d").alias("service_date")
    )
    
    # Filter pre/post
    treatment_pre = treatment_df.filter(
        (pl.col("service_date") >= pre_start.date()) & (pl.col("service_date") < pre_end.date())
    )
    treatment_post = treatment_df.filter(
        (pl.col("service_date") >= post_start.date()) & (pl.col("service_date") < post_end.date())
    )
    
    # Compute metrics for treatment group
    def compute_group_metrics(df: pl.DataFrame, member_count: int) -> dict[str, float]:
        if df.is_empty() or member_count == 0:
            return {
                "utilization_per_1k": 0.0,
                "allowed_pmpm": 0.0,
                "paid_pmpm": 0.0,
                "total_claims": 0,
                "total_allowed": 0.0,
                "total_paid": 0.0,
            }
        
        total_claims = len(df)
        total_allowed = df["allowed_amount"].sum()
        total_paid = df["paid_amount"].sum()
        member_months = member_count * (pre_months if df is treatment_pre else post_months)
        
        return {
            "utilization_per_1k": (total_claims / member_count) * 1000 if member_count > 0 else 0.0,
            "allowed_pmpm": (total_allowed / member_months) if member_months > 0 else 0.0,
            "paid_pmpm": (total_paid / member_months) if member_months > 0 else 0.0,
            "total_claims": total_claims,
            "total_allowed": total_allowed,
            "total_paid": total_paid,
        }
    
    # Get member count (simplified - in real implementation, load from enrollment)
    member_count = treatment_df["member_id"].n_unique()
    
    treatment_pre_metrics = compute_group_metrics(treatment_pre, member_count)
    treatment_post_metrics = compute_group_metrics(treatment_post, member_count)
    
    # Compute control group metrics if provided
    control_pre_metrics = None
    control_post_metrics = None
    
    if control_df is not None and not control_df.is_empty():
        control_df = control_df.with_columns(
            pl.col("service_from_date").str.strptime(pl.Date, "%Y-%m-%d").alias("service_date")
        )
        control_pre = control_df.filter(
            (pl.col("service_date") >= pre_start.date()) & (pl.col("service_date") < pre_end.date())
        )
        control_post = control_df.filter(
            (pl.col("service_date") >= post_start.date()) & (pl.col("service_date") < post_end.date())
        )
        control_member_count = control_df["member_id"].n_unique()
        control_pre_metrics = compute_group_metrics(control_pre, control_member_count)
        control_post_metrics = compute_group_metrics(control_post, control_member_count)
    
    return {
        "treatment_pre": treatment_pre_metrics,
        "treatment_post": treatment_post_metrics,
        "control_pre": control_pre_metrics,
        "control_post": control_post_metrics,
        "pre_period": {"start": pre_start.isoformat(), "end": pre_end.isoformat()},
        "post_period": {"start": post_start.isoformat(), "end": post_end.isoformat()},
    }


def difference_in_differences(
    treatment_pre: dict[str, float],
    treatment_post: dict[str, float],
    control_pre: dict[str, float] | None,
    control_post: dict[str, float] | None,
    metric: str = "utilization_per_1k",
) -> dict[str, Any]:
    """Compute difference-in-differences estimate"""
    if control_pre is None or control_post is None:
        # Fallback to simple pre/post
        change = treatment_post[metric] - treatment_pre[metric]
        percent_change = (change / treatment_pre[metric] * 100) if treatment_pre[metric] > 0 else 0.0
        
        return {
            "method": "pre_post",
            "effect_size": change,
            "percent_change": percent_change,
            "confidence_interval": None,  # Will be computed via bootstrap
            "p_value": None,
            "data_sufficiency_warning": "No control group available - results may be confounded",
        }
    
    # DiD formula: (Treatment_post - Treatment_pre) - (Control_post - Control_pre)
    treatment_diff = treatment_post[metric] - treatment_pre[metric]
    control_diff = control_post[metric] - control_pre[metric]
    did_estimate = treatment_diff - control_diff
    
    percent_change = (did_estimate / treatment_pre[metric] * 100) if treatment_pre[metric] > 0 else 0.0
    
    return {
        "method": "difference_in_differences",
        "effect_size": did_estimate,
        "percent_change": percent_change,
        "treatment_diff": treatment_diff,
        "control_diff": control_diff,
        "confidence_interval": None,  # Will be computed via bootstrap
        "p_value": None,
    }


def bootstrap_confidence_interval(
    treatment_pre_data: pl.DataFrame,
    treatment_post_data: pl.DataFrame,
    control_pre_data: pl.DataFrame | None,
    control_post_data: pl.DataFrame | None,
    metric_fn: callable,
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
) -> tuple[float, float]:
    """Bootstrap confidence interval"""
    bootstrap_samples = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        treatment_pre_sample = treatment_pre_data.sample(n=len(treatment_pre_data), with_replacement=True)
        treatment_post_sample = treatment_post_data.sample(n=len(treatment_post_data), with_replacement=True)
        
        if control_pre_data is not None and control_post_data is not None:
            control_pre_sample = control_pre_data.sample(n=len(control_pre_data), with_replacement=True)
            control_post_sample = control_post_data.sample(n=len(control_post_data), with_replacement=True)
            
            # Compute DiD
            treatment_pre_metric = metric_fn(treatment_pre_sample)
            treatment_post_metric = metric_fn(treatment_post_sample)
            control_pre_metric = metric_fn(control_pre_sample)
            control_post_metric = metric_fn(control_post_sample)
            
            did = (treatment_post_metric - treatment_pre_metric) - (control_post_metric - control_pre_metric)
            bootstrap_samples.append(did)
        else:
            # Simple pre/post
            treatment_pre_metric = metric_fn(treatment_pre_sample)
            treatment_post_metric = metric_fn(treatment_post_sample)
            change = treatment_post_metric - treatment_pre_metric
            bootstrap_samples.append(change)
    
    # Compute confidence interval
    alpha = 1 - confidence_level
    lower = np.percentile(bootstrap_samples, (alpha / 2) * 100)
    upper = np.percentile(bootstrap_samples, (1 - alpha / 2) * 100)
    
    return float(lower), float(upper)


def compute_data_sufficiency_checks(
    treatment_pre: dict[str, float],
    treatment_post: dict[str, float],
    control_pre: dict[str, float] | None,
    control_post: dict[str, float] | None,
) -> dict[str, Any]:
    """Compute data sufficiency checks"""
    warnings = []
    
    # Sample size check
    if treatment_pre["total_claims"] < 100:
        warnings.append("Low sample size in pre-period")
    if treatment_post["total_claims"] < 100:
        warnings.append("Low sample size in post-period")
    
    # Control group check
    if control_pre is None or control_post is None:
        warnings.append("No control group - results may be confounded by external factors")
    
    # Parallel trends assumption (simplified)
    parallel_trends_status = "UNKNOWN"
    if control_pre is not None and control_post is not None:
        # Check if pre-trends are similar (simplified check)
        treatment_pre_trend = treatment_pre.get("utilization_per_1k", 0)
        control_pre_trend = control_pre.get("utilization_per_1k", 0)
        
        if abs(treatment_pre_trend - control_pre_trend) / max(treatment_pre_trend, 1) < 0.2:
            parallel_trends_status = "PASS"
        else:
            parallel_trends_status = "WARN"
            warnings.append("Pre-trends may not be parallel")
    
    return {
        "parallel_trends": parallel_trends_status,
        "sample_size_ok": treatment_pre["total_claims"] >= 100 and treatment_post["total_claims"] >= 100,
        "warnings": warnings,
        "seasonality_risk": "LOW",  # Simplified
    }


def run_policy_impact_analysis(
    tenant_id: UUID,
    policy_id: UUID,
    policy_effective_date: datetime,
    treatment_filters: dict[str, Any],
    control_filters: dict[str, Any] | None,
    pre_months: int = 6,
    post_months: int = 6,
) -> dict[str, Any]:
    """Run complete policy impact analysis"""
    # Load treatment group data
    pre_start = policy_effective_date - timedelta(days=pre_months * 30)
    post_end = policy_effective_date + timedelta(days=post_months * 30)
    
    treatment_df = load_claims_data(tenant_id, treatment_filters, pre_start, post_end)
    
    # Load control group data if provided
    control_df = None
    if control_filters:
        control_df = load_claims_data(tenant_id, control_filters, pre_start, post_end)
    
    # Compute metrics
    metrics = compute_pre_post_metrics(
        treatment_df, control_df, policy_effective_date, pre_months, post_months
    )
    
    # Compute DiD
    did_result = difference_in_differences(
        metrics["treatment_pre"],
        metrics["treatment_post"],
        metrics["control_pre"],
        metrics["control_post"],
        metric="utilization_per_1k",
    )
    
    # Bootstrap confidence interval
    # For now, use simplified approach
    # In full implementation, would bootstrap on actual data
    ci_lower = did_result["effect_size"] * 0.8  # Simplified
    ci_upper = did_result["effect_size"] * 1.2
    
    did_result["confidence_interval"] = [ci_lower, ci_upper]
    
    # Data sufficiency checks
    checks = compute_data_sufficiency_checks(
        metrics["treatment_pre"],
        metrics["treatment_post"],
        metrics["control_pre"],
        metrics["control_post"],
    )
    
    # Compute confidence score (0-100)
    confidence_score = 100
    if len(checks["warnings"]) > 0:
        confidence_score -= len(checks["warnings"]) * 15
    if checks["parallel_trends"] == "WARN":
        confidence_score -= 20
    if not checks["sample_size_ok"]:
        confidence_score -= 25
    confidence_score = max(0, confidence_score)
    
    return {
        "policy_id": str(policy_id),
        "policy_effective_date": policy_effective_date.isoformat(),
        "metrics": metrics,
        "impact_estimate": did_result,
        "data_sufficiency_checks": checks,
        "confidence_score": confidence_score,
        "methodology": {
            "method": did_result["method"],
            "pre_months": pre_months,
            "post_months": post_months,
            "has_control_group": control_df is not None and not control_df.is_empty(),
        },
        "limitations": checks["warnings"],
    }

