"""Substitution detection engine - rules + statistical ranking + lag analysis"""
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


# Code group mappings for substitution detection
CODE_GROUPS = {
    "MRI": ["72141", "72142", "72146", "72148"],
    "ER_IMAGING": ["70450", "70460", "72141", "70470"],
    "INFUSION": ["96413", "96415", "96417"],
    "PT": ["97110", "97112", "97140"],
    "SPECIALTY_VISIT": ["99213", "99214", "99215"],
    "URGENT_CARE": ["99281", "99282", "99283"],
    "ORTHOPEDIC_IMAGING": ["73040", "73050", "73060", "73070"],
}

# Site-of-care POS codes
POS_CODES = {
    "OFFICE": ["11"],
    "OUTPATIENT_HOSPITAL": ["22"],
    "EMERGENCY": ["23"],
    "FREESTANDING": ["19"],
    "URGENT_CARE": ["20"],
}


class SubstitutionResult:
    """Result of substitution detection"""
    
    def __init__(
        self,
        code: str,
        code_group: Optional[str],
        classification: str,  # "SITE_OF_CARE_SHIFT", "SERVICE_SUBSTITUTION", "UNKNOWN"
        pre_allowed: float,
        post_allowed: float,
        allowed_delta: float,
        allowed_pct_change: float,
        pre_claim_count: int,
        post_claim_count: int,
        claim_count_delta: int,
        lag_effects: dict[str, dict[str, float]],
        confidence_score: float,
        statistical_rank: Optional[int] = None,
        p_value: Optional[float] = None,
    ):
        """Initialize substitution result"""
        self.code = code
        self.code_group = code_group
        self.classification = classification
        self.pre_allowed = pre_allowed
        self.post_allowed = post_allowed
        self.allowed_delta = allowed_delta
        self.allowed_pct_change = allowed_pct_change
        self.pre_claim_count = pre_claim_count
        self.post_claim_count = post_claim_count
        self.claim_count_delta = claim_count_delta
        self.lag_effects = lag_effects
        self.confidence_score = confidence_score
        self.statistical_rank = statistical_rank
        self.p_value = p_value
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "code": self.code,
            "code_group": self.code_group,
            "classification": self.classification,
            "pre_allowed": self.pre_allowed,
            "post_allowed": self.post_allowed,
            "allowed_delta": self.allowed_delta,
            "allowed_pct_change": self.allowed_pct_change,
            "pre_claim_count": self.pre_claim_count,
            "post_claim_count": self.post_claim_count,
            "claim_count_delta": self.claim_count_delta,
            "lag_effects": self.lag_effects,
            "confidence_score": self.confidence_score,
            "statistical_rank": self.statistical_rank,
            "p_value": self.p_value,
        }


class SubstitutionDetector:
    """Substitution detection engine with rules + statistical ranking + lag analysis"""
    
    def __init__(
        self,
        tenant_id: UUID,
        parquet_service: Optional[ParquetDataService] = None,
    ):
        """Initialize substitution detector"""
        self.tenant_id = tenant_id
        self.parquet_service = parquet_service or ParquetDataService()
    
    def detect_substitution(
        self,
        policy_effective_date: datetime,
        affected_codes: list[str],
        treatment_filters: dict[str, Any],
        pre_months: int = 6,
        post_months: int = 6,
        lag_windows: list[int] = [30, 60, 90],
    ) -> dict[str, Any]:
        """Detect substitution patterns after policy change
        
        Args:
            policy_effective_date: Policy effective date
            affected_codes: List of CPT/HCPCS codes affected by policy
            treatment_filters: Treatment group filters
            pre_months: Pre-policy window in months
            post_months: Post-policy window in months
            lag_windows: Lag windows in days for detecting delayed substitution
            
        Returns:
            Dictionary with substitutions, ranking, and diagnostics
        """
        # Import ImpactAnalysisEngine for data loading
        # We use it here to reuse the data loading logic
        from uepi_common.analytics.impact import ImpactAnalysisEngine
        
        # Load data using ImpactAnalysisEngine's data loading method
        impact_engine = ImpactAnalysisEngine(tenant_id=self.tenant_id, parquet_service=self.parquet_service)
        
        pre_start = policy_effective_date - timedelta(days=pre_months * 30)
        pre_end = policy_effective_date
        post_start = policy_effective_date
        post_end = policy_effective_date + timedelta(days=post_months * 30)
        
        # Load all claims data (broader scope for substitution detection)
        pre_df = impact_engine._load_data(pre_start, pre_end, treatment_filters, None)
        post_df = impact_engine._load_data(post_start, post_end, treatment_filters, None)
        
        if pre_df.is_empty() or post_df.is_empty():
            return {
                "substitutions": [],
                "total_substitutions_detected": 0,
                "warnings": ["No data available for substitution analysis"],
            }
        
        # Compute baseline metrics per code
        pre_metrics = (
            pre_df.group_by("cpt_code")
            .agg([
                pl.sum("allowed_amount").alias("total_allowed"),
                pl.sum("units").alias("total_units"),
                pl.count().alias("claim_count"),
                pl.col("allowed_amount").std().alias("allowed_std"),
            ])
            .with_columns([
                (pl.col("total_allowed") / pl.col("claim_count")).alias("avg_allowed_per_claim"),
            ])
        )
        
        post_metrics = (
            post_df.group_by("cpt_code")
            .agg([
                pl.sum("allowed_amount").alias("total_allowed"),
                pl.sum("units").alias("total_units"),
                pl.count().alias("claim_count"),
                pl.col("allowed_amount").std().alias("allowed_std"),
            ])
            .with_columns([
                (pl.col("total_allowed") / pl.col("claim_count")).alias("avg_allowed_per_claim"),
            ])
        )
        
        # Join to compute changes
        changes = (
            pre_metrics.join(
                post_metrics,
                on="cpt_code",
                how="outer",
                suffix="_post",
            )
            .with_columns([
                (pl.col("total_allowed_post").fill_null(0) - pl.col("total_allowed").fill_null(0)).alias("allowed_delta"),
                (pl.col("claim_count_post").fill_null(0) - pl.col("claim_count").fill_null(0)).alias("claim_count_delta"),
                ((pl.col("total_allowed_post").fill_null(0) - pl.col("total_allowed").fill_null(0)) / 
                 pl.col("total_allowed").fill_null(1) * 100).alias("allowed_pct_change"),
            ])
            .filter(
                (pl.col("allowed_delta") > 0) &  # Only increased services
                (pl.col("claim_count_post").fill_null(0) >= 10)  # Minimum post count for statistical validity
            )
            .sort("allowed_delta", descending=True)
        )
        
        # Classify substitutions and compute statistical significance
        substitutions = []
        for row in changes.iter_rows(named=True):
            code = row["cpt_code"]
            
            # Rule-based classification
            classification, code_group = self._classify_substitution(
                code, affected_codes, pre_df, post_df
            )
            
            # Compute lag effects
            lag_effects = self._compute_lag_effects(
                code, post_df, post_start, lag_windows
            )
            
            # Statistical significance test (chi-square or t-test)
            p_value = self._compute_statistical_significance(
                code, pre_df, post_df, row
            )
            
            # Compute confidence score (combines rules + statistics)
            confidence_score = self._compute_confidence_score(
                classification, allowed_pct_change=row["allowed_pct_change"],
                p_value=p_value, lag_effects=lag_effects
            )
            
            substitutions.append(SubstitutionResult(
                code=code,
                code_group=code_group,
                classification=classification,
                pre_allowed=row.get("total_allowed", 0),
                post_allowed=row.get("total_allowed_post", 0),
                allowed_delta=row["allowed_delta"],
                allowed_pct_change=row["allowed_pct_change"],
                pre_claim_count=row.get("claim_count", 0),
                post_claim_count=row.get("claim_count_post", 0),
                claim_count_delta=row["claim_count_delta"],
                lag_effects=lag_effects,
                confidence_score=confidence_score,
                p_value=p_value,
            ))
        
        # Statistical ranking (rank by statistical significance and magnitude)
        substitutions = self._statistical_ranking(substitutions)
        
        # Add rank to each substitution
        for idx, sub in enumerate(substitutions):
            sub.statistical_rank = idx + 1
        
        return {
            "substitutions": [s.to_dict() for s in substitutions[:20]],  # Top 20
            "total_substitutions_detected": len(substitutions),
            "top_pathways": self._identify_top_pathways(substitutions, affected_codes),
            "policy_effective_date": policy_effective_date.isoformat(),
            "analysis_period": {
                "pre_start": pre_start.isoformat(),
                "pre_end": pre_end.isoformat(),
                "post_start": post_start.isoformat(),
                "post_end": post_end.isoformat(),
            },
        }
    
    def _classify_substitution(
        self,
        code: str,
        affected_codes: list[str],
        pre_df: pl.DataFrame,
        post_df: pl.DataFrame,
    ) -> tuple[str, Optional[str]]:
        """Classify substitution type (rule-based)
        
        Returns:
            (classification, code_group)
        """
        # Check if this is a site-of-care shift
        pre_pos_df = pre_df.filter(pl.col("cpt_code") == code)
        post_pos_df = post_df.filter(pl.col("cpt_code") == code)
        
        if not pre_pos_df.is_empty() and not post_pos_df.is_empty():
            pre_pos_mode = pre_pos_df["place_of_service"].mode()
            post_pos_mode = post_pos_df["place_of_service"].mode()
            
            if len(pre_pos_mode) > 0 and len(post_pos_mode) > 0:
                if pre_pos_mode[0] != post_pos_mode[0]:
                    return ("SITE_OF_CARE_SHIFT", None)
        
        # Check if this is service substitution (related to affected codes)
        code_group = None
        for group_name, group_codes in CODE_GROUPS.items():
            if code in group_codes:
                code_group = group_name
                # Check if any affected code is in the same group
                if any(ac in group_codes for ac in affected_codes):
                    return ("SERVICE_SUBSTITUTION", code_group)
                break
        
        # Default: unknown but significant increase
        return ("UNKNOWN", code_group)
    
    def _compute_lag_effects(
        self,
        code: str,
        post_df: pl.DataFrame,
        post_start: datetime,
        lag_windows: list[int],
    ) -> dict[str, dict[str, float]]:
        """Compute lag effects at different time windows"""
        lag_effects = {}
        
        for lag_days in lag_windows:
            lag_start = post_start + timedelta(days=lag_days)
            lag_end = lag_start + timedelta(days=30)
            
            lag_df = post_df.filter(
                (pl.col("service_date") >= lag_start.date()) &
                (pl.col("service_date") < lag_end.date())
            )
            lag_code_df = lag_df.filter(pl.col("cpt_code") == code)
            
            lag_effects[f"{lag_days}_day"] = {
                "claim_count": len(lag_code_df) if not lag_code_df.is_empty() else 0,
                "total_allowed": float(lag_code_df["allowed_amount"].sum()) if not lag_code_df.is_empty() else 0.0,
            }
        
        return lag_effects
    
    def _compute_statistical_significance(
        self,
        code: str,
        pre_df: pl.DataFrame,
        post_df: pl.DataFrame,
        row: dict,
    ) -> Optional[float]:
        """Compute statistical significance (p-value) using chi-square test"""
        pre_code_df = pre_df.filter(pl.col("cpt_code") == code)
        post_code_df = post_df.filter(pl.col("cpt_code") == code)
        
        if pre_code_df.is_empty() or post_code_df.is_empty():
            return None
        
        # Chi-square test: compare claim counts
        pre_count = len(pre_code_df)
        post_count = len(post_code_df)
        
        # Total counts for normalization
        pre_total = len(pre_df)
        post_total = len(post_df)
        
        if pre_total == 0 or post_total == 0:
            return None
        
        # Create contingency table
        observed = np.array([
            [pre_count, pre_total - pre_count],
            [post_count, post_total - post_count],
        ])
        
        try:
            if SCIPY_AVAILABLE and stats is not None:
                chi2, p_value = stats.chi2_contingency(observed)[:2]
                return float(p_value)
            else:
                # Fallback: scipy not available
                return None
        except Exception:
            return None
    
    def _compute_confidence_score(
        self,
        classification: str,
        allowed_pct_change: float,
        p_value: Optional[float],
        lag_effects: dict[str, dict[str, float]],
    ) -> float:
        """Compute confidence score (0-100)"""
        score = 50  # Base
        
        # Classification bonus
        if classification == "SITE_OF_CARE_SHIFT":
            score += 25
        elif classification == "SERVICE_SUBSTITUTION":
            score += 20
        
        # Magnitude bonus
        if allowed_pct_change > 100:
            score += 20
        elif allowed_pct_change > 50:
            score += 10
        elif allowed_pct_change > 25:
            score += 5
        
        # Statistical significance bonus
        if p_value is not None:
            if p_value < 0.001:
                score += 15
            elif p_value < 0.01:
                score += 10
            elif p_value < 0.05:
                score += 5
        
        # Lag effects bonus (consistent lag pattern)
        if len(lag_effects) >= 2:
            lag_values = [v["claim_count"] for v in lag_effects.values()]
            if all(v > 0 for v in lag_values):
                score += 5
        
        return min(100.0, score)
    
    def _statistical_ranking(
        self,
        substitutions: list[SubstitutionResult],
    ) -> list[SubstitutionResult]:
        """Rank substitutions by statistical significance and magnitude"""
        # Sort by: (1) p-value (lower is better), (2) confidence_score, (3) allowed_delta
        def rank_key(sub: SubstitutionResult) -> tuple:
            p_val = sub.p_value if sub.p_value is not None else 1.0
            return (p_val, -sub.confidence_score, -sub.allowed_delta)
        
        return sorted(substitutions, key=rank_key)
    
    def _identify_top_pathways(
        self,
        substitutions: list[SubstitutionResult],
        affected_codes: list[str],
    ) -> list[dict[str, Any]]:
        """Identify top substitution pathways"""
        pathways = {}
        
        for sub in substitutions[:10]:  # Top 10
            if sub.classification == "SERVICE_SUBSTITUTION" and sub.code_group:
                if sub.code_group not in pathways:
                    pathways[sub.code_group] = {
                        "from_code": affected_codes[0] if affected_codes else "UNKNOWN",
                        "to_code": sub.code,
                        "to_code_group": sub.code_group,
                        "count": 0,
                        "total_delta": 0.0,
                        "avg_confidence": 0.0,
                    }
                
                pathways[sub.code_group]["count"] += 1
                pathways[sub.code_group]["total_delta"] += sub.allowed_delta
                pathways[sub.code_group]["avg_confidence"] = (
                    (pathways[sub.code_group]["avg_confidence"] * (pathways[sub.code_group]["count"] - 1) +
                     sub.confidence_score) / pathways[sub.code_group]["count"]
                )
        
        # Sort by total delta
        top_pathways = sorted(
            pathways.values(),
            key=lambda x: x["total_delta"],
            reverse=True
        )
        
        return top_pathways[:5]  # Top 5 pathways

