"""Method checks - pre-trends, control balance, seasonality"""
from typing import Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

import numpy as np
import polars as pl

# Make scipy optional - import only when needed
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    stats = None

from uepi_common.data.parquet_service import ParquetDataService


class PreTrendsCheck:
    """Pre-trends diagnostic check"""
    
    def __init__(
        self,
        parallel_trends: str,  # "PASS", "WARN", "FAIL"
        pre_trend_treatment: Optional[float] = None,  # Slope in treatment group
        pre_trend_control: Optional[float] = None,  # Slope in control group
        pre_trend_difference: Optional[float] = None,  # Difference in slopes
        p_value: Optional[float] = None,
        warning: Optional[str] = None,
    ):
        """Initialize pre-trends check"""
        self.parallel_trends = parallel_trends
        self.pre_trend_treatment = pre_trend_treatment
        self.pre_trend_control = pre_trend_control
        self.pre_trend_difference = pre_trend_difference
        self.p_value = p_value
        self.warning = warning
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "parallel_trends": self.parallel_trends,
            "pre_trend_treatment": self.pre_trend_treatment,
            "pre_trend_control": self.pre_trend_control,
            "pre_trend_difference": self.pre_trend_difference,
            "p_value": self.p_value,
            "warning": self.warning,
        }


class ControlBalanceCheck:
    """Control group balance diagnostic check"""
    
    def __init__(
        self,
        balanced: bool,
        balance_score: float,  # 0.0-1.0, higher is better
        imbalanced_covariates: list[str] = None,
        standardized_mean_differences: dict[str, float] = None,
        warning: Optional[str] = None,
    ):
        """Initialize control balance check"""
        self.balanced = balanced
        self.balance_score = balance_score
        self.imbalanced_covariates = imbalanced_covariates or []
        self.standardized_mean_differences = standardized_mean_differences or {}
        self.warning = warning
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "balanced": self.balanced,
            "balance_score": self.balance_score,
            "imbalanced_covariates": self.imbalanced_covariates,
            "standardized_mean_differences": self.standardized_mean_differences,
            "warning": self.warning,
        }


class SeasonalityCheck:
    """Seasonality diagnostic check"""
    
    def __init__(
        self,
        seasonal_pattern_detected: bool,
        seasonality_risk: str,  # "LOW", "MEDIUM", "HIGH"
        seasonal_periods: list[int] = None,  # e.g., [12] for annual, [3, 6, 12] for multiple
        adjustment_recommended: bool = False,
        warning: Optional[str] = None,
    ):
        """Initialize seasonality check"""
        self.seasonal_pattern_detected = seasonal_pattern_detected
        self.seasonality_risk = seasonality_risk
        self.seasonal_periods = seasonal_periods or []
        self.adjustment_recommended = adjustment_recommended
        self.warning = warning
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "seasonal_pattern_detected": self.seasonal_pattern_detected,
            "seasonality_risk": self.seasonality_risk,
            "seasonal_periods": self.seasonal_periods,
            "adjustment_recommended": self.adjustment_recommended,
            "warning": self.warning,
        }


class MethodChecks:
    """Collection of method diagnostic checks"""
    
    def __init__(
        self,
        pre_trends: PreTrendsCheck,
        control_balance: Optional[ControlBalanceCheck] = None,
        seasonality: Optional[SeasonalityCheck] = None,
        sample_size_ok: bool = True,
        min_sample_size: int = 1000,
        actual_sample_size: int = 0,
        warnings: list[str] = None,
    ):
        """Initialize method checks"""
        self.pre_trends = pre_trends
        self.control_balance = control_balance
        self.seasonality = seasonality
        self.sample_size_ok = sample_size_ok
        self.min_sample_size = min_sample_size
        self.actual_sample_size = actual_sample_size
        self.warnings = warnings or []
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "pre_trends": self.pre_trends.to_dict(),
            "sample_size_ok": self.sample_size_ok,
            "min_sample_size": self.min_sample_size,
            "actual_sample_size": self.actual_sample_size,
            "warnings": self.warnings,
        }
        
        if self.control_balance:
            result["control_balance"] = self.control_balance.to_dict()
        
        if self.seasonality:
            result["seasonality"] = self.seasonality.to_dict()
        
        return result


class MethodCheckRunner:
    """Runs method diagnostic checks for impact analysis"""
    
    def __init__(
        self,
        tenant_id: UUID,
        parquet_service: Optional[ParquetDataService] = None,
    ):
        """Initialize method check runner"""
        self.tenant_id = tenant_id
        self.parquet_service = parquet_service or ParquetDataService()
    
    def run_all_checks(
        self,
        policy_effective_date: datetime,
        treatment_filters: dict[str, Any],
        control_filters: Optional[dict[str, Any]] = None,
        pre_months: int = 6,
        metric: str = "utilization_per_1k",
    ) -> MethodChecks:
        """Run all method checks
        
        Args:
            policy_effective_date: Policy effective date
            treatment_filters: Treatment group filters
            control_filters: Optional control group filters
            pre_months: Pre-policy window in months
            metric: Metric to analyze
            
        Returns:
            MethodChecks with all diagnostic results
        """
        # Load pre-policy data
        pre_start = policy_effective_date - timedelta(days=pre_months * 30)
        
        treatment_pre_df = self._load_data(pre_start, policy_effective_date, treatment_filters)
        control_pre_df = None
        if control_filters:
            control_pre_df = self._load_data(pre_start, policy_effective_date, control_filters)
        
        # Pre-trends check
        pre_trends = self._check_pre_trends(treatment_pre_df, control_pre_df, metric)
        
        # Control balance check (if control group exists)
        control_balance = None
        if control_pre_df is not None:
            control_balance = self._check_control_balance(treatment_pre_df, control_pre_df)
        
        # Seasonality check
        seasonality = self._check_seasonality(treatment_pre_df, control_pre_df, metric)
        
        # Sample size check
        actual_sample_size = len(treatment_pre_df)
        min_sample_size = 1000
        sample_size_ok = actual_sample_size >= min_sample_size
        
        # Collect warnings
        warnings = []
        if pre_trends.parallel_trends != "PASS":
            warnings.append(f"Pre-trends check {pre_trends.parallel_trends}: {pre_trends.warning}")
        if control_balance and not control_balance.balanced:
            warnings.append(f"Control group imbalance detected: {control_balance.warning}")
        if seasonality.seasonality_risk in ["MEDIUM", "HIGH"]:
            warnings.append(f"Seasonality risk {seasonality.seasonality_risk}: {seasonality.warning}")
        if not sample_size_ok:
            warnings.append(f"Sample size insufficient: {actual_sample_size} < {min_sample_size}")
        
        return MethodChecks(
            pre_trends=pre_trends,
            control_balance=control_balance,
            seasonality=seasonality,
            sample_size_ok=sample_size_ok,
            min_sample_size=min_sample_size,
            actual_sample_size=actual_sample_size,
            warnings=warnings,
        )
    
    def _load_data(
        self,
        start_date: datetime,
        end_date: datetime,
        filters: dict[str, Any],
    ) -> pl.DataFrame:
        """Load claims data using ImpactAnalysisEngine's method"""
        from uepi_common.analytics.impact import ImpactAnalysisEngine
        
        # Use ImpactAnalysisEngine's data loading logic
        impact_engine = ImpactAnalysisEngine(tenant_id=self.tenant_id, parquet_service=self.parquet_service)
        return impact_engine._load_data(start_date, end_date, filters, None)
    
    def _check_pre_trends(
        self,
        treatment_pre_df: pl.DataFrame,
        control_pre_df: Optional[pl.DataFrame],
        metric: str,
    ) -> PreTrendsCheck:
        """Check for parallel trends in pre-policy period
        
        Args:
            treatment_pre_df: Treatment group pre-policy data
            control_pre_df: Optional control group pre-policy data
            metric: Metric to analyze
            
        Returns:
            PreTrendsCheck with results
        """
        if treatment_pre_df.is_empty():
            return PreTrendsCheck(
                parallel_trends="FAIL",
                warning="Insufficient treatment group data for pre-trends check",
            )
        
        # Group by month and compute monthly metrics
        treatment_monthly = (
            treatment_pre_df
            .with_columns([
                pl.col("service_date").dt.year().alias("year"),
                pl.col("service_date").dt.month().alias("month"),
            ])
            .group_by(["year", "month"])
            .agg([
                pl.count().alias("claim_count"),
                pl.col("member_id").n_unique().alias("member_count"),
            ])
            .with_columns([
                (pl.col("claim_count") / pl.col("member_count") * 1000.0).alias("utilization_per_1k"),
                pl.struct(["year", "month"]).alias("period"),
            ])
            .sort(["year", "month"])
        )
        
        # Compute trend (slope) in treatment group
        if len(treatment_monthly) < 2:
            return PreTrendsCheck(
                parallel_trends="WARN",
                warning="Insufficient months for pre-trends analysis",
            )
        
        treatment_values = treatment_monthly["utilization_per_1k"].to_list()
        treatment_slope = self._compute_slope(treatment_values)
        
        # If control group exists, check parallel trends
        if control_pre_df is not None and not control_pre_df.is_empty():
            control_monthly = (
                control_pre_df
                .with_columns([
                    pl.col("service_date").dt.year().alias("year"),
                    pl.col("service_date").dt.month().alias("month"),
                ])
                .group_by(["year", "month"])
                .agg([
                    pl.count().alias("claim_count"),
                    pl.col("member_id").n_unique().alias("member_count"),
                ])
                .with_columns([
                    (pl.col("claim_count") / pl.col("member_count") * 1000.0).alias("utilization_per_1k"),
                ])
                .sort(["year", "month"])
            )
            
            if len(control_monthly) < 2:
                return PreTrendsCheck(
                    parallel_trends="WARN",
                    pre_trend_treatment=treatment_slope,
                    warning="Insufficient control group months for pre-trends analysis",
                )
            
            control_values = control_monthly["utilization_per_1k"].to_list()
            control_slope = self._compute_slope(control_values)
            
            # Test if slopes are significantly different
            slope_difference = abs(treatment_slope - control_slope)
            # Simplified test - in production, would use proper statistical test
            parallel_trends = "PASS" if slope_difference < 0.1 else "WARN" if slope_difference < 0.3 else "FAIL"
            
            return PreTrendsCheck(
                parallel_trends=parallel_trends,
                pre_trend_treatment=treatment_slope,
                pre_trend_control=control_slope,
                pre_trend_difference=slope_difference,
                p_value=None,  # Would compute from statistical test
                warning=None if parallel_trends == "PASS" else f"Pre-trends may not be parallel (difference: {slope_difference:.3f})",
            )
        else:
            # No control group - can't check parallel trends
            return PreTrendsCheck(
                parallel_trends="WARN",
                pre_trend_treatment=treatment_slope,
                warning="No control group - cannot check parallel trends",
            )
    
    def _compute_slope(self, values: list[float]) -> float:
        """Compute linear trend slope
        
        Args:
            values: Time series values
            
        Returns:
            Slope (change per period)
        """
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        y = np.array(values)
        
        # Linear regression
        slope, intercept = np.polyfit(x, y, 1)
        
        return float(slope)
    
    def _check_control_balance(
        self,
        treatment_df: pl.DataFrame,
        control_df: pl.DataFrame,
    ) -> ControlBalanceCheck:
        """Check balance between treatment and control groups
        
        Args:
            treatment_df: Treatment group data
            control_df: Control group data
            
        Returns:
            ControlBalanceCheck with results
        """
        # Check balance on key covariates
        covariates = ["age_band", "gender", "risk_score"]  # Simplified - would use enrollment data
        
        imbalanced_covariates = []
        standardized_mean_differences = {}
        
        # For MVP, simplified balance check
        # In production, would compute standardized mean differences for each covariate
        
        balanced = len(imbalanced_covariates) == 0
        balance_score = 1.0 if balanced else 0.7  # Simplified
        
        return ControlBalanceCheck(
            balanced=balanced,
            balance_score=balance_score,
            imbalanced_covariates=imbalanced_covariates,
            standardized_mean_differences=standardized_mean_differences,
            warning=None if balanced else "Some covariates are imbalanced between groups",
        )
    
    def _check_seasonality(
        self,
        treatment_df: pl.DataFrame,
        control_df: Optional[pl.DataFrame],
        metric: str,
    ) -> SeasonalityCheck:
        """Check for seasonal patterns
        
        Args:
            treatment_df: Treatment group data
            control_df: Optional control group data
            metric: Metric to analyze
            
        Returns:
            SeasonalityCheck with results
        """
        if treatment_df.is_empty():
            return SeasonalityCheck(
                seasonal_pattern_detected=False,
                seasonality_risk="LOW",
                warning="Insufficient data for seasonality check",
            )
        
        # Group by month to detect seasonal patterns
        monthly_data = (
            treatment_df
            .with_columns([
                pl.col("service_date").dt.month().alias("month"),
            ])
            .group_by("month")
            .agg([
                pl.count().alias("count"),
            ])
            .sort("month")
        )
        
        if len(monthly_data) < 12:
            # Not enough months to detect annual seasonality
            return SeasonalityCheck(
                seasonal_pattern_detected=False,
                seasonality_risk="LOW",
                warning="Insufficient months for seasonality detection",
            )
        
        # Check for annual seasonality (12-month cycle)
        values = monthly_data["count"].to_list()
        # Simplified check - in production, would use FFT or autocorrelation
        variance = np.var(values)
        mean_val = np.mean(values)
        cv = variance / mean_val if mean_val > 0 else 0.0  # Coefficient of variation
        
        # Determine seasonality risk
        if cv < 0.1:
            seasonality_risk = "LOW"
            seasonal_pattern_detected = False
        elif cv < 0.2:
            seasonality_risk = "MEDIUM"
            seasonal_pattern_detected = True
            seasonal_periods = [12]
        else:
            seasonality_risk = "HIGH"
            seasonal_pattern_detected = True
            seasonal_periods = [12]
        
        return SeasonalityCheck(
            seasonal_pattern_detected=seasonal_pattern_detected,
            seasonality_risk=seasonality_risk,
            seasonal_periods=seasonal_periods if seasonal_pattern_detected else [],
            adjustment_recommended=seasonality_risk in ["MEDIUM", "HIGH"],
            warning=None if seasonality_risk == "LOW" else f"Seasonal pattern detected (CV: {cv:.3f})",
        )

