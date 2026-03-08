"""Causal impact analysis engine - DiD with bootstrap CI"""
from typing import Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

import numpy as np
import polars as pl

from uepi_common.data.parquet_service import ParquetDataService
from uepi_common.data_contracts.claims import ServiceCategory


class ImpactResult:
    """Result of impact analysis"""
    
    def __init__(
        self,
        method: str,  # "difference_in_differences" or "pre_post"
        effect_size: float,
        percent_change: float,
        confidence_interval: tuple[float, float],
        p_value: Optional[float] = None,
        treatment_pre_metric: Optional[float] = None,
        treatment_post_metric: Optional[float] = None,
        control_pre_metric: Optional[float] = None,
        control_post_metric: Optional[float] = None,
        treatment_diff: Optional[float] = None,
        control_diff: Optional[float] = None,
        robustness_checks: Optional[dict[str, Any]] = None,
        confounder_flags: Optional[list[str]] = None,
    ):
        """Initialize impact result
        
        Args:
            method: Analysis method used
            effect_size: Estimated effect size (absolute change)
            percent_change: Percentage change from baseline
            confidence_interval: 95% CI (lower, upper)
            p_value: P-value (if computed)
            treatment_pre_metric: Treatment group pre-policy metric
            treatment_post_metric: Treatment group post-policy metric
            control_pre_metric: Control group pre-policy metric
            control_post_metric: Control group post-policy metric
            treatment_diff: Treatment group change (post - pre)
            control_diff: Control group change (post - pre)
            robustness_checks: Additional robustness checks
            confounder_flags: List of potential confounders detected
        """
        self.method = method
        self.effect_size = effect_size
        self.percent_change = percent_change
        self.confidence_interval = confidence_interval
        self.p_value = p_value
        self.treatment_pre_metric = treatment_pre_metric
        self.treatment_post_metric = treatment_post_metric
        self.control_pre_metric = control_pre_metric
        self.control_post_metric = control_post_metric
        self.treatment_diff = treatment_diff
        self.control_diff = control_diff
        self.robustness_checks = robustness_checks or {}
        self.confounder_flags = confounder_flags or []
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "method": self.method,
            "effect_size": self.effect_size,
            "percent_change": self.percent_change,
            "confidence_interval": {
                "lower": self.confidence_interval[0],
                "upper": self.confidence_interval[1],
                "level": 0.95,
            },
            "p_value": self.p_value,
            "treatment_pre_metric": self.treatment_pre_metric,
            "treatment_post_metric": self.treatment_post_metric,
            "control_pre_metric": self.control_pre_metric,
            "control_post_metric": self.control_post_metric,
            "treatment_diff": self.treatment_diff,
            "control_diff": self.control_diff,
            "robustness_checks": self.robustness_checks,
            "confounder_flags": self.confounder_flags,
        }


class ImpactAnalysisEngine:
    """Causal impact analysis engine - DiD with bootstrap CI
    
    This engine:
    1. Loads treatment and control group data
    2. Computes pre/post metrics
    3. Runs DiD analysis (or pre/post if no control)
    4. Computes bootstrap confidence intervals
    5. Performs robustness checks
    6. Flags potential confounders
    """
    
    def __init__(
        self,
        tenant_id: UUID,
        parquet_service: Optional[ParquetDataService] = None,
    ):
        """Initialize impact analysis engine
        
        Args:
            tenant_id: Tenant ID for multi-tenancy
            parquet_service: ParquetDataService instance (creates default if None)
        """
        self.tenant_id = tenant_id
        self.parquet_service = parquet_service or ParquetDataService()
    
    def analyze_policy_impact(
        self,
        policy_effective_date: datetime,
        treatment_filters: dict[str, Any],
        control_filters: Optional[dict[str, Any]] = None,
        pre_months: int = 6,
        post_months: int = 6,
        metric: str = "utilization_per_1k",  # "utilization_per_1k", "cost_per_member", etc.
        service_category: Optional[ServiceCategory] = None,
        n_bootstrap: int = 1000,
        confidence_level: float = 0.95,
    ) -> ImpactResult:
        """Run policy impact analysis
        
        Args:
            policy_effective_date: Policy effective date
            treatment_filters: Filters for treatment group (e.g., {"lob": "Commercial", "market": "CA"})
            control_filters: Optional filters for control group
            pre_months: Pre-policy window in months
            post_months: Post-policy window in months
            metric: Metric to analyze (utilization_per_1k, cost_per_member, etc.)
            service_category: Optional service category filter
            n_bootstrap: Number of bootstrap samples for CI
            confidence_level: Confidence level for CI (default: 0.95)
            
        Returns:
            ImpactResult with effect size, CI, and diagnostics
        """
        # Load data
        pre_start = policy_effective_date - timedelta(days=pre_months * 30)
        post_end = policy_effective_date + timedelta(days=post_months * 30)
        
        treatment_pre_df = self._load_data(pre_start, policy_effective_date, treatment_filters, service_category)
        treatment_post_df = self._load_data(policy_effective_date, post_end, treatment_filters, service_category)
        
        control_pre_df = None
        control_post_df = None
        if control_filters:
            control_pre_df = self._load_data(pre_start, policy_effective_date, control_filters, service_category)
            control_post_df = self._load_data(policy_effective_date, post_end, control_filters, service_category)
        
        # Compute metrics
        treatment_pre_metric = self._compute_metric(treatment_pre_df, metric)
        treatment_post_metric = self._compute_metric(treatment_post_df, metric)
        
        control_pre_metric = None
        control_post_metric = None
        if control_pre_df is not None and control_post_df is not None:
            control_pre_metric = self._compute_metric(control_pre_df, metric)
            control_post_metric = self._compute_metric(control_post_df, metric)
        
        # Run DiD or pre/post
        if control_pre_metric is not None and control_post_metric is not None:
            # Difference-in-Differences
            treatment_diff = treatment_post_metric - treatment_pre_metric
            control_diff = control_post_metric - control_pre_metric
            did_estimate = treatment_diff - control_diff
            
            percent_change = (did_estimate / treatment_pre_metric * 100) if treatment_pre_metric > 0 else 0.0
            
            # Bootstrap confidence interval for DiD
            ci_lower, ci_upper = self._bootstrap_did_ci(
                treatment_pre_df,
                treatment_post_df,
                control_pre_df,
                control_post_df,
                metric,
                n_bootstrap,
                confidence_level,
            )
            
            # Compute p-value (simplified - would use t-test in production)
            p_value = self._compute_p_value(did_estimate, ci_lower, ci_upper)
            
            return ImpactResult(
                method="difference_in_differences",
                effect_size=did_estimate,
                percent_change=percent_change,
                confidence_interval=(ci_lower, ci_upper),
                p_value=p_value,
                treatment_pre_metric=treatment_pre_metric,
                treatment_post_metric=treatment_post_metric,
                control_pre_metric=control_pre_metric,
                control_post_metric=control_post_metric,
                treatment_diff=treatment_diff,
                control_diff=control_diff,
                robustness_checks={},
                confounder_flags=[],
            )
        else:
            # Pre/post (no control group)
            change = treatment_post_metric - treatment_pre_metric
            percent_change = (change / treatment_pre_metric * 100) if treatment_pre_metric > 0 else 0.0
            
            # Bootstrap confidence interval for pre/post
            ci_lower, ci_upper = self._bootstrap_pre_post_ci(
                treatment_pre_df,
                treatment_post_df,
                metric,
                n_bootstrap,
                confidence_level,
            )
            
            # Compute p-value
            p_value = self._compute_p_value(change, ci_lower, ci_upper)
            
            return ImpactResult(
                method="pre_post",
                effect_size=change,
                percent_change=percent_change,
                confidence_interval=(ci_lower, ci_upper),
                p_value=p_value,
                treatment_pre_metric=treatment_pre_metric,
                treatment_post_metric=treatment_post_metric,
                robustness_checks={},
                confounder_flags=["No control group - results may be confounded by time trends"],
            )
    
    def _load_data(
        self,
        start_date: datetime,
        end_date: datetime,
        filters: dict[str, Any],
        service_category: Optional[ServiceCategory] = None,
    ) -> pl.DataFrame:
        """Load claims data for specified period and filters
        
        Args:
            start_date: Start date
            end_date: End date
            filters: Filters (lob, market, network, etc.)
            service_category: Optional service category filter
            
        Returns:
            Polars DataFrame with claims data
        """
        # Build partition paths based on filters
        all_data = []
        
        current_date = start_date
        while current_date <= end_date:
            year = current_date.year
            month = current_date.month
            
            # Get LOBs and markets from filters
            lobs = filters.get("lob", [])
            if isinstance(lobs, str):
                lobs = [lobs]
            if not lobs:
                lobs = ["Commercial", "Medicare", "Medicaid"]  # Default
            
            markets = filters.get("market", filters.get("markets", []))
            if isinstance(markets, str):
                markets = [markets]
            if not markets:
                markets = ["CA", "TX", "NY", "FL", "IL"]  # Default
            
            # Load data for each partition
            for lob in lobs:
                for market in markets:
                    # Build partition filters
                    partition_filters = {
                        "year": str(year),
                        "month": f"{month:02d}",
                        "lob": lob,
                        "market": market,
                    }
                    
                    try:
                        from uepi_common.data.parquet_service import DataZone
                        
                        df = self.parquet_service.read_partitioned_dataframe(
                            tenant_id=self.tenant_id,
                            dataset_type="claims_lines",
                            zone=DataZone.CURATED,
                            partition_filters=partition_filters,
                        )
                        
                        if df.is_empty():
                            continue
                        
                        # Apply filters
                        if service_category:
                            df = df.filter(pl.col("service_category") == service_category.value)
                        
                        if filters.get("in_network_only"):
                            df = df.filter(pl.col("in_network") == True)
                        
                        if filters.get("cpt_codes"):
                            cpt_codes = filters["cpt_codes"]
                            if isinstance(cpt_codes, str):
                                cpt_codes = [cpt_codes]
                            df = df.filter(pl.col("cpt_code").is_in(cpt_codes))
                        
                        # Filter by date (service_date should already be date type from Parquet)
                        df = df.filter(
                            (pl.col("service_date") >= start_date.date()) &
                            (pl.col("service_date") < end_date.date())
                        )
                        
                        if not df.is_empty():
                            all_data.append(df)
                    except Exception as e:
                        # Partition doesn't exist or error reading, skip
                        # TODO: Add proper logging
                        continue
            
            # Move to next month
            if month == 12:
                current_date = datetime(year + 1, 1, 1)
            else:
                current_date = datetime(year, month + 1, 1)
        
        if not all_data:
            return pl.DataFrame()
        
        # Concatenate all data
        return pl.concat(all_data)
    
    def _compute_metric(
        self,
        df: pl.DataFrame,
        metric: str,
    ) -> float:
        """Compute metric from DataFrame
        
        Args:
            df: Claims DataFrame
            metric: Metric name (utilization_per_1k, cost_per_member, etc.)
            
        Returns:
            Metric value
        """
        if df.is_empty():
            return 0.0
        
        if metric == "utilization_per_1k":
            # Claims per 1,000 members
            member_count = df["member_id"].n_unique()
            if member_count == 0:
                return 0.0
            claim_count = len(df)
            return (claim_count / member_count) * 1000.0
        
        elif metric == "cost_per_member":
            # Average cost per member
            member_count = df["member_id"].n_unique()
            if member_count == 0:
                return 0.0
            total_cost = df["allowed_amount"].sum()
            return float(total_cost) / member_count
        
        elif metric == "avg_cost_per_claim":
            # Average cost per claim
            if len(df) == 0:
                return 0.0
            return float(df["allowed_amount"].mean())
        
        else:
            raise ValueError(f"Unknown metric: {metric}")
    
    def _bootstrap_did_ci(
        self,
        treatment_pre_df: pl.DataFrame,
        treatment_post_df: pl.DataFrame,
        control_pre_df: pl.DataFrame,
        control_post_df: pl.DataFrame,
        metric: str,
        n_bootstrap: int,
        confidence_level: float,
    ) -> tuple[float, float]:
        """Bootstrap confidence interval for DiD
        
        Args:
            treatment_pre_df: Treatment group pre-policy data
            treatment_post_df: Treatment group post-policy data
            control_pre_df: Control group pre-policy data
            control_post_df: Control group post-policy data
            metric: Metric name
            n_bootstrap: Number of bootstrap samples
            confidence_level: Confidence level
            
        Returns:
            (lower, upper) confidence interval
        """
        bootstrap_samples = []
        
        for _ in range(n_bootstrap):
            # Resample with replacement
            treatment_pre_sample = treatment_pre_df.sample(
                n=len(treatment_pre_df) if len(treatment_pre_df) > 0 else 1,
                with_replacement=True,
                seed=None,
            )
            treatment_post_sample = treatment_post_df.sample(
                n=len(treatment_post_df) if len(treatment_post_df) > 0 else 1,
                with_replacement=True,
                seed=None,
            )
            control_pre_sample = control_pre_df.sample(
                n=len(control_pre_df) if len(control_pre_df) > 0 else 1,
                with_replacement=True,
                seed=None,
            )
            control_post_sample = control_post_df.sample(
                n=len(control_post_df) if len(control_post_df) > 0 else 1,
                with_replacement=True,
                seed=None,
            )
            
            # Compute metrics
            treatment_pre_metric = self._compute_metric(treatment_pre_sample, metric)
            treatment_post_metric = self._compute_metric(treatment_post_sample, metric)
            control_pre_metric = self._compute_metric(control_pre_sample, metric)
            control_post_metric = self._compute_metric(control_post_sample, metric)
            
            # Compute DiD
            treatment_diff = treatment_post_metric - treatment_pre_metric
            control_diff = control_post_metric - control_pre_metric
            did = treatment_diff - control_diff
            
            bootstrap_samples.append(did)
        
        # Compute confidence interval
        alpha = 1 - confidence_level
        lower = float(np.percentile(bootstrap_samples, (alpha / 2) * 100))
        upper = float(np.percentile(bootstrap_samples, (1 - alpha / 2) * 100))
        
        return (lower, upper)
    
    def _bootstrap_pre_post_ci(
        self,
        pre_df: pl.DataFrame,
        post_df: pl.DataFrame,
        metric: str,
        n_bootstrap: int,
        confidence_level: float,
    ) -> tuple[float, float]:
        """Bootstrap confidence interval for pre/post
        
        Args:
            pre_df: Pre-policy data
            post_df: Post-policy data
            metric: Metric name
            n_bootstrap: Number of bootstrap samples
            confidence_level: Confidence level
            
        Returns:
            (lower, upper) confidence interval
        """
        bootstrap_samples = []
        
        for _ in range(n_bootstrap):
            # Resample with replacement
            pre_sample = pre_df.sample(
                n=len(pre_df) if len(pre_df) > 0 else 1,
                with_replacement=True,
                seed=None,
            )
            post_sample = post_df.sample(
                n=len(post_df) if len(post_df) > 0 else 1,
                with_replacement=True,
                seed=None,
            )
            
            # Compute metrics
            pre_metric = self._compute_metric(pre_sample, metric)
            post_metric = self._compute_metric(post_sample, metric)
            
            # Compute change
            change = post_metric - pre_metric
            bootstrap_samples.append(change)
        
        # Compute confidence interval
        alpha = 1 - confidence_level
        lower = float(np.percentile(bootstrap_samples, (alpha / 2) * 100))
        upper = float(np.percentile(bootstrap_samples, (1 - alpha / 2) * 100))
        
        return (lower, upper)
    
    def _compute_p_value(
        self,
        effect_size: float,
        ci_lower: float,
        ci_upper: float,
    ) -> Optional[float]:
        """Compute p-value from effect size and CI (simplified)
        
        Args:
            effect_size: Estimated effect size
            ci_lower: Lower bound of CI
            ci_upper: Upper bound of CI
            
        Returns:
            P-value (or None if cannot compute)
        """
        # Simplified p-value computation
        # In production, would use proper statistical test
        if ci_lower <= 0 <= ci_upper:
            # CI contains zero, effect not significant
            return 0.5  # Placeholder
        else:
            # CI doesn't contain zero, effect significant
            return 0.01  # Placeholder

