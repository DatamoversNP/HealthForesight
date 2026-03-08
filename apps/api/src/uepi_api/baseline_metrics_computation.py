"""Enhanced baseline metrics computation using metric dictionary and policy scoping"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, date
import pandas as pd
import polars as pl

from uepi_common.metrics import METRIC_DICTIONARY, get_card_required_metrics, METRIC_NAMES
from uepi_api.policy_scoping import compute_policy_scope, PolicyScopeResult
from uepi_api.policy_scoping_enhanced import compute_comprehensive_policy_scope


def compute_baseline_metrics_from_analysis_result(
    result_dict: Dict[str, Any],
    tenant_id: UUID,
    policy_id: Optional[UUID] = None,
    policy: Optional[Dict[str, Any]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Compute comprehensive baseline metrics using metric dictionary
    
    This function extracts metrics from baseline analysis results and computes
    policy-scoped metrics if a policy is provided.
    
    Returns:
        Dictionary with baseline_metrics containing all metrics from metric dictionary
    """
    baseline_metrics = {}
    
    # Extract global baseline metrics from analysis result
    benchmarks = result_dict.get("benchmarks", [])
    time_series = result_dict.get("time_series", [])
    
    # Extract member-months (denominator)
    member_months = _extract_member_months_from_benchmarks(benchmarks)
    baseline_metrics["member_months"] = member_months
    baseline_metrics["unique_members"] = _extract_unique_members_from_benchmarks(benchmarks)
    
    # Extract global utilization rate
    util_rate_total = _extract_metric_from_benchmarks(benchmarks, "total_claims_per_1k", "per_1k")
    if util_rate_total is not None:
        baseline_metrics["util_rate_total_per_1000_mm"] = util_rate_total
    
    # Extract global cost PMPM
    cost_pmpm = _extract_metric_from_benchmarks(benchmarks, "cost_pmpm", "PMPM")
    if cost_pmpm is not None:
        baseline_metrics["allowed_pmpm_total"] = cost_pmpm
    
    # Extract from time series if available
    if time_series and util_rate_total is None:
        observed_values = [ts.get("observed", 0.0) for ts in time_series if isinstance(ts, dict) and ts.get("observed") is not None]
        if observed_values:
            avg_util = sum(observed_values) / len(observed_values)
            baseline_metrics["util_rate_total_per_1000_mm"] = avg_util
    
    # Compute policy-scoped metrics if policy is provided
    if policy_id and policy:
        policy_scoped_metrics = _compute_policy_scoped_baseline_metrics(
            policy, tenant_id, benchmarks, time_series, start_date, end_date
        )
        baseline_metrics.update(policy_scoped_metrics)
    
    # Compute mix baselines from analysis result
    mix_metrics = _compute_mix_baseline_metrics(result_dict, policy, tenant_id, start_date, end_date)
    baseline_metrics.update(mix_metrics)
    
    # Compute allowed_total_annualized (M7) if we have allowed_pmpm_target or allowed_pmpm_total
    if "allowed_pmpm_target" in baseline_metrics and "policy_eligible_member_months" in baseline_metrics:
        # Annualize: (pmpm * member_months / months_in_period) * 12
        policy_eligible_mm = baseline_metrics["policy_eligible_member_months"]
        if policy_eligible_mm > 0 and start_date and end_date:
            months_in_period = max(1, (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1)
            allowed_pmpm_target = baseline_metrics["allowed_pmpm_target"]
            baseline_metrics["allowed_total_annualized"] = (allowed_pmpm_target * policy_eligible_mm / months_in_period) * 12
    elif "allowed_pmpm_total" in baseline_metrics and "member_months" in baseline_metrics:
        # Fallback to global metrics
        member_months = baseline_metrics["member_months"]
        if member_months > 0 and start_date and end_date:
            months_in_period = max(1, (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1)
            allowed_pmpm_total = baseline_metrics["allowed_pmpm_total"]
            baseline_metrics["allowed_total_annualized"] = (allowed_pmpm_total * member_months / months_in_period) * 12
    
    # Backward compatibility aliases
    if "util_rate_total_per_1000_mm" in baseline_metrics:
        baseline_metrics["utilization_per_1k"] = baseline_metrics["util_rate_total_per_1000_mm"]
    if "util_rate_target_per_1000_mm" in baseline_metrics:
        baseline_metrics["utilization_per_1k"] = baseline_metrics["util_rate_target_per_1000_mm"]
    if "allowed_pmpm_total" in baseline_metrics:
        baseline_metrics["cost_per_1k"] = baseline_metrics["allowed_pmpm_total"] * 12 / 1000  # Rough conversion
    
    return baseline_metrics


def _compute_policy_scoped_baseline_metrics(
    policy: Dict[str, Any],
    tenant_id: UUID,
    benchmarks: List[Dict[str, Any]],
    time_series: List[Dict[str, Any]],
    start_date: Optional[date],
    end_date: Optional[date],
) -> Dict[str, Any]:
    """Compute policy-scoped baseline metrics using policy scoping algorithm"""
    try:
        # Compute comprehensive policy scope (uses ALL policy components)
        scope_result = compute_comprehensive_policy_scope(
            tenant_id=tenant_id,
            policy=policy,
            pre_window_months=12,
        )
        
        policy_metrics = {}
        
        # Policy-eligible member-months
        policy_metrics["policy_eligible_member_months"] = scope_result.total_eligible_member_months
        
        # Target utilization rate (if we can compute from scope)
        # In a full implementation, we'd filter claims by target codes and compute
        # For now, we'll use a proxy based on the ratio of target to total
        if scope_result.total_eligible_member_months > 0 and scope_result.final_target_claim_lines_count > 0:
            # Estimate target utilization per 1k
            # This is simplified - in production would compute from actual target claims
            policy_metrics["util_rate_target_per_1000_mm"] = (
                (scope_result.final_target_claim_lines_count / scope_result.total_eligible_member_months) * 1000
            )
        
        # Target PMPM (simplified - would need to sum target allowed amounts)
        # For now, we'll leave this as None and it will need to be computed in impact analysis
        
        return policy_metrics
    except Exception as e:
        print(f"WARNING: Could not compute policy-scoped metrics: {e}")
        import traceback
        traceback.print_exc()
        return {}


def _compute_mix_baseline_metrics(
    result_dict: Dict[str, Any],
    policy: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> Dict[str, Any]:
    """Compute mix baseline metrics (site of care, provider, network, OON leakage, HHI)"""
    mix_metrics = {}
    
    # Extract site of care mix if available in provider archetypes or network features
    provider_archetypes = result_dict.get("provider_archetypes", [])
    network_features = result_dict.get("network_features", {})
    
    # Network mix (in-network share)
    if isinstance(network_features, dict):
        inn_share = network_features.get("in_network_share")
        if inn_share is not None:
            mix_metrics["inn_share_target"] = float(inn_share) * 100  # Convert to percentage
    
    # Provider concentration (from archetypes) - Top 10 share
    if provider_archetypes:
        total_providers = len(provider_archetypes)
        if total_providers > 0:
            # Top 10 provider share (simplified - based on archetype count)
            # In production, this would be based on actual utilization share
            top_10_count = min(10, total_providers)
            mix_metrics["top10_provider_share_target"] = (top_10_count / total_providers) * 100
    
    # Compute additional mix metrics from claims data if available
    if tenant_id and policy:
        try:
            additional_mix = _compute_mix_metrics_from_claims(
                tenant_id, policy, start_date, end_date
            )
            mix_metrics.update(additional_mix)
        except Exception as e:
            print(f"WARNING: Could not compute mix metrics from claims: {e}")
            # Continue without failing
    
    return mix_metrics


def _compute_mix_metrics_from_claims(
    tenant_id: UUID,
    policy: Dict[str, Any],
    start_date: Optional[date],
    end_date: Optional[date],
) -> Dict[str, Any]:
    """Compute mix metrics (OON leakage, HHI, SOC shares) from claims data"""
    from pathlib import Path
    import polars as pl
    
    mix_metrics = {}
    
    # Find claims data file
    project_root = Path(__file__).parent.parent.parent.parent.parent
    target_data_root = project_root / "apps" / "data" / "target_data_model" / str(tenant_id) / "CLAIMS_LINES"
    claims_file = target_data_root / "claims_lines.csv"
    
    if not claims_file.exists():
        return mix_metrics
    
    try:
        # Load claims data (limit columns for efficiency)
        # Use in_network_flag (schema) not in_network
        df = pl.scan_csv(str(claims_file), try_parse_dates=True).select([
            "member_id",
            "cpt_hcpcs",
            "place_of_service",
            "in_network_flag",
            "rendering_npi",
            "allowed_amount",
            "service_date_from",
        ]).collect()
        
        if df.is_empty():
            return mix_metrics
        
        # Filter by date range if provided
        if start_date and end_date:
            df = df.filter(
                (pl.col("service_date_from") >= pl.date(start_date.year, start_date.month, start_date.day)) &
                (pl.col("service_date_from") <= pl.date(end_date.year, end_date.month, end_date.day))
            )
        
        # Apply policy scope filters if available
        policy_scope = policy.get("scope", {})
        if policy_scope:
            if policy_scope.get("lob"):
                # Filter by LOB if available in claims
                pass  # LOB filtering would require LOB column in claims
            if policy_scope.get("markets"):
                # Filter by market if available
                pass  # Market filtering would require market column in claims
        
        # Filter to target codes if policy has target codes
        policy_levers = policy.get("policy_levers", [])
        target_codes = []
        for lever in policy_levers:
            if isinstance(lever, dict):
                target = lever.get("target") or lever.get("target_codes") or []
                if isinstance(target, list):
                    target_codes.extend(target)
                elif isinstance(target, str):
                    target_codes.append(target)
        
        if target_codes:
            target_df = df.filter(pl.col("cpt_hcpcs").is_in(target_codes))
        else:
            target_df = df  # Use all claims if no target specified
        
        if target_df.is_empty():
            return mix_metrics
        
        total_target_claims = len(target_df)
        if total_target_claims == 0:
            return mix_metrics
        
        # OON Leakage Rate (M13) — use in_network_flag (may be bool or string Y/N)
        oon_expr = (pl.col("in_network_flag") == False) | (pl.col("in_network_flag").cast(pl.Utf8).str.to_lowercase().is_in(["n", "no", "0"]))
        oon_claims = target_df.filter(oon_expr)
        oon_count = len(oon_claims)
        oon_share = (oon_count / total_target_claims) if total_target_claims > 0 else 0.0
        
        # Get policy-eligible member-months (simplified - approximate from unique members)
        unique_members = target_df["member_id"].n_unique()
        # Approximate member-months (assuming all members enrolled for full period)
        if start_date and end_date:
            months_in_period = max(1, (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1)
            policy_eligible_mm = unique_members * months_in_period
        else:
            policy_eligible_mm = unique_members * 12  # Default to 12 months
        
        if policy_eligible_mm > 0:
            mix_metrics["oon_leakage_rate_target_per_1000_mm"] = (oon_count / policy_eligible_mm) * 1000
        
        # Provider HHI (M10) - Herfindahl-Hirschman Index
        provider_shares = (
            target_df.group_by("rendering_npi")
            .agg(pl.count().alias("claim_count"))
            .with_columns((pl.col("claim_count") / total_target_claims).alias("share"))
            .select("share")
        )
        
        if len(provider_shares) > 0:
            shares_list = provider_shares["share"].to_list()
            hhi = sum(s ** 2 for s in shares_list)  # HHI = Σ(share_i^2)
            mix_metrics["provider_hhi_target"] = float(hhi)
        
        # In-network share (if not already set)
        if "inn_share_target" not in mix_metrics:
            inn_expr = (pl.col("in_network_flag") == True) | (pl.col("in_network_flag").cast(pl.Utf8).str.to_lowercase().is_in(["y", "yes", "1"]))
            inn_claims = target_df.filter(inn_expr)
            inn_count = len(inn_claims)
            inn_share = (inn_count / total_target_claims) * 100 if total_target_claims > 0 else 0.0
            mix_metrics["inn_share_target"] = float(inn_share)
        
        # Site of Care shares (M8) - compute for common POS codes
        pos_map = {
            "11": "Office",
            "19": "Off_Campus",
            "20": "Urgent_Care",
            "21": "Inpatient",
            "22": "HOPD",
            "23": "ER",
            "24": "ASC",
        }
        
        for pos_code, soc_name in pos_map.items():
            soc_claims = target_df.filter(pl.col("place_of_service") == pos_code)
            soc_count = len(soc_claims)
            soc_share = (soc_count / total_target_claims) * 100 if total_target_claims > 0 else 0.0
            metric_name = f"soc_share_target_{soc_name.upper()}"
            mix_metrics[metric_name] = float(soc_share)
        
    except Exception as e:
        print(f"Error computing mix metrics from claims: {e}")
        import traceback
        traceback.print_exc()
    
    return mix_metrics


def _extract_member_months_from_benchmarks(benchmarks: List[Dict[str, Any]]) -> float:
    """Extract member-months from benchmarks"""
    for benchmark in benchmarks:
        if isinstance(benchmark, dict):
            metric_name = benchmark.get("metric_name", "")
            if "member_months" in metric_name.lower() or "member_months" in benchmark.get("denominator", ""):
                return float(benchmark.get("metric_value", 0.0))
    return 0.0


def _extract_unique_members_from_benchmarks(benchmarks: List[Dict[str, Any]]) -> int:
    """Extract unique member count from benchmarks"""
    for benchmark in benchmarks:
        if isinstance(benchmark, dict):
            metric_name = benchmark.get("metric_name", "")
            if "unique_members" in metric_name.lower() or "member_count" in metric_name.lower():
                return int(benchmark.get("metric_value", 0))
    return 0


def _extract_metric_from_benchmarks(
    benchmarks: List[Dict[str, Any]],
    metric_name_pattern: str,
    unit_pattern: str,
) -> Optional[float]:
    """Extract metric value from benchmarks by name and unit pattern"""
    for benchmark in benchmarks:
        if isinstance(benchmark, dict):
            metric_name = benchmark.get("metric_name", "")
            unit = benchmark.get("unit", "")
            
            if metric_name_pattern.lower() in metric_name.lower() and unit_pattern.lower() in unit.lower():
                value = benchmark.get("metric_value")
                if value is not None:
                    return float(value)
    return None
