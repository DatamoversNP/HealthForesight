"""Trust Panel - confidence scores, data sufficiency, validation checks"""
from typing import Any, Optional
from datetime import datetime
from decimal import Decimal


class ConfidenceScore:
    """Confidence score for analysis result"""
    
    def __init__(
        self,
        overall_score: float,  # 0.0-100.0
        method_confidence: float,  # Confidence in method choice
        data_quality_score: float,  # Data quality assessment
        sample_size_score: float,  # Sample size adequacy
        control_group_score: float,  # Control group quality (if applicable)
        methodology_score: float,  # Methodology appropriateness
    ):
        """Initialize confidence score
        
        Args:
            overall_score: Overall confidence score (0.0-100.0)
            method_confidence: Confidence in method choice (0.0-100.0)
            data_quality_score: Data quality score (0.0-100.0)
            sample_size_score: Sample size adequacy score (0.0-100.0)
            control_group_score: Control group quality score (0.0-100.0, 100 if N/A)
            methodology_score: Methodology appropriateness score (0.0-100.0)
        """
        self.overall_score = overall_score
        self.method_confidence = method_confidence
        self.data_quality_score = data_quality_score
        self.sample_size_score = sample_size_score
        self.control_group_score = control_group_score
        self.methodology_score = methodology_score
    
    def get_category(self) -> str:
        """Get confidence category (HIGH, MEDIUM, LOW)"""
        if self.overall_score >= 80:
            return "HIGH"
        elif self.overall_score >= 60:
            return "MEDIUM"
        else:
            return "LOW"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "overall_score": self.overall_score,
            "category": self.get_category(),
            "components": {
                "method_confidence": self.method_confidence,
                "data_quality_score": self.data_quality_score,
                "sample_size_score": self.sample_size_score,
                "control_group_score": self.control_group_score,
                "methodology_score": self.methodology_score,
            },
        }


class DataSufficiency:
    """Data sufficiency assessment"""
    
    def __init__(
        self,
        sufficient: bool,
        min_sample_size: int,
        actual_sample_size: int,
        data_window_months: int,
        coverage_score: float,  # 0.0-1.0, completeness of data window
        missing_data_flags: list[str] = None,
    ):
        """Initialize data sufficiency
        
        Args:
            sufficient: Whether data is sufficient for analysis
            min_sample_size: Minimum required sample size
            actual_sample_size: Actual sample size
            data_window_months: Number of months of data available
            coverage_score: Data coverage score (0.0-1.0)
            missing_data_flags: List of missing data issues
        """
        self.sufficient = sufficient
        self.min_sample_size = min_sample_size
        self.actual_sample_size = actual_sample_size
        self.data_window_months = data_window_months
        self.coverage_score = coverage_score
        self.missing_data_flags = missing_data_flags or []
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "sufficient": self.sufficient,
            "min_sample_size": self.min_sample_size,
            "actual_sample_size": self.actual_sample_size,
            "data_window_months": self.data_window_months,
            "coverage_score": self.coverage_score,
            "missing_data_flags": self.missing_data_flags,
        }


class ValidationCheck:
    """Validation check result"""
    
    def __init__(
        self,
        check_name: str,
        passed: bool,
        message: Optional[str] = None,
        severity: str = "INFO",  # "INFO", "WARNING", "ERROR"
    ):
        """Initialize validation check
        
        Args:
            check_name: Name of the check
            passed: Whether check passed
            message: Optional message
            severity: Severity level
        """
        self.check_name = check_name
        self.passed = passed
        self.message = message
        self.severity = severity
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "message": self.message,
            "severity": self.severity,
        }


class TrustPanel:
    """Trust Panel - comprehensive trust assessment for analysis results"""
    
    def __init__(
        self,
        confidence_score: ConfidenceScore,
        data_sufficiency: DataSufficiency,
        validation_checks: list[ValidationCheck],
        methodology: dict[str, Any],
        limitations: list[str] = None,
        data_used: dict[str, Any] = None,
        model_version: Optional[str] = None,
    ):
        """Initialize trust panel
        
        Args:
            confidence_score: Overall confidence score
            data_sufficiency: Data sufficiency assessment
            validation_checks: List of validation checks
            methodology: Methodology information (method, parameters, etc.)
            limitations: List of limitations and caveats
            data_used: Information about data used (window, filters, etc.)
            model_version: Model version identifier (if applicable)
        """
        self.confidence_score = confidence_score
        self.data_sufficiency = data_sufficiency
        self.validation_checks = validation_checks
        self.methodology = methodology
        self.limitations = limitations or []
        self.data_used = data_used or {}
        self.model_version = model_version
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "confidence_score": self.confidence_score.to_dict(),
            "data_sufficiency": self.data_sufficiency.to_dict(),
            "validation_checks": [check.to_dict() for check in self.validation_checks],
            "methodology": self.methodology,
            "limitations": self.limitations,
            "data_used": self.data_used,
            "model_version": self.model_version,
        }


class TrustPanelBuilder:
    """Builder for Trust Panel from analysis results"""
    
    @staticmethod
    def build_trust_panel(
        impact_result: Any,  # ImpactResult
        method_checks: Any,  # MethodChecks
        data_window_months: int,
        actual_sample_size: int,
        methodology: dict[str, Any],
        data_used: dict[str, Any] = None,
    ) -> TrustPanel:
        """Build trust panel from analysis results
        
        Args:
            impact_result: ImpactResult from analysis
            method_checks: MethodChecks from diagnostics
            data_window_months: Number of months of data used
            actual_sample_size: Actual sample size
            methodology: Methodology information
            data_used: Information about data used
            
        Returns:
            TrustPanel with comprehensive trust assessment
        """
        # Compute confidence score components
        method_confidence = 90.0 if impact_result.method == "difference_in_differences" else 70.0
        data_quality_score = 85.0  # Simplified - would assess data quality
        sample_size_score = min(100.0, (actual_sample_size / 1000) * 100) if actual_sample_size > 0 else 0.0
        
        control_group_score = 100.0
        if method_checks.control_balance:
            if method_checks.control_balance.balanced:
                control_group_score = 90.0
            else:
                control_group_score = 60.0
        elif impact_result.method == "pre_post":
            control_group_score = 0.0  # No control group
        
        methodology_score = 85.0  # Simplified - would assess methodology appropriateness
        
        # Compute overall confidence score
        overall_score = (
            method_confidence * 0.3 +
            data_quality_score * 0.2 +
            sample_size_score * 0.2 +
            control_group_score * 0.15 +
            methodology_score * 0.15
        )
        
        confidence_score = ConfidenceScore(
            overall_score=overall_score,
            method_confidence=method_confidence,
            data_quality_score=data_quality_score,
            sample_size_score=sample_size_score,
            control_group_score=control_group_score,
            methodology_score=methodology_score,
        )
        
        # Data sufficiency
        min_sample_size = method_checks.min_sample_size
        sufficient = method_checks.sample_size_ok and data_window_months >= 6
        
        coverage_score = min(1.0, data_window_months / 12.0)  # Normalize to 12 months
        
        data_sufficiency = DataSufficiency(
            sufficient=sufficient,
            min_sample_size=min_sample_size,
            actual_sample_size=actual_sample_size,
            data_window_months=data_window_months,
            coverage_score=coverage_score,
            missing_data_flags=[],
        )
        
        # Validation checks
        validation_checks = []
        
        # Pre-trends check
        validation_checks.append(ValidationCheck(
            check_name="Parallel Trends",
            passed=method_checks.pre_trends.parallel_trends == "PASS",
            message=method_checks.pre_trends.warning,
            severity="WARNING" if method_checks.pre_trends.parallel_trends == "WARN" else "ERROR" if method_checks.pre_trends.parallel_trends == "FAIL" else "INFO",
        ))
        
        # Control balance check
        if method_checks.control_balance:
            validation_checks.append(ValidationCheck(
                check_name="Control Group Balance",
                passed=method_checks.control_balance.balanced,
                message=method_checks.control_balance.warning,
                severity="WARNING" if not method_checks.control_balance.balanced else "INFO",
            ))
        
        # Seasonality check
        if method_checks.seasonality:
            validation_checks.append(ValidationCheck(
                check_name="Seasonality",
                passed=method_checks.seasonality.seasonality_risk == "LOW",
                message=method_checks.seasonality.warning,
                severity="WARNING" if method_checks.seasonality.seasonality_risk == "MEDIUM" else "ERROR" if method_checks.seasonality.seasonality_risk == "HIGH" else "INFO",
            ))
        
        # Sample size check
        validation_checks.append(ValidationCheck(
            check_name="Sample Size",
            passed=method_checks.sample_size_ok,
            message=f"Sample size: {actual_sample_size} (minimum: {min_sample_size})",
            severity="WARNING" if not method_checks.sample_size_ok else "INFO",
        ))
        
        # Confidence interval check
        ci_lower, ci_upper = impact_result.confidence_interval
        ci_contains_zero = ci_lower <= 0 <= ci_upper
        validation_checks.append(ValidationCheck(
            check_name="Statistical Significance",
            passed=not ci_contains_zero,
            message="Confidence interval contains zero - effect may not be statistically significant" if ci_contains_zero else "Confidence interval does not contain zero - effect is statistically significant",
            severity="WARNING" if ci_contains_zero else "INFO",
        ))
        
        # Collect limitations
        limitations = []
        if impact_result.method == "pre_post":
            limitations.append("No control group - results may be confounded by time trends")
        if impact_result.confounder_flags:
            limitations.extend(impact_result.confounder_flags)
        if method_checks.pre_trends.parallel_trends != "PASS":
            limitations.append("Pre-trends may not be parallel - DiD assumption may be violated")
        if method_checks.seasonality and method_checks.seasonality.seasonality_risk in ["MEDIUM", "HIGH"]:
            limitations.append(f"Seasonal patterns detected - results may be affected by seasonality")
        if not method_checks.sample_size_ok:
            limitations.append(f"Sample size below minimum ({actual_sample_size} < {min_sample_size})")
        
        return TrustPanel(
            confidence_score=confidence_score,
            data_sufficiency=data_sufficiency,
            validation_checks=validation_checks,
            methodology=methodology,
            limitations=limitations,
            data_used=data_used or {},
            model_version="1.0.0",  # Would be versioned in production
        )

