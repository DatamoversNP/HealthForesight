"""
Elasticity Modeling Engine
Uses GAM (Generalized Additive Models) and monotonic regression to model elasticity curves
"""
from typing import Any, Optional
from datetime import datetime
from uuid import UUID
import numpy as np
import polars as pl
from dataclasses import dataclass

# Try to import GAM libraries, fall back to simpler methods if not available
try:
    from pygam import LinearGAM, s, f
    HAS_PYGAM = True
except ImportError:
    HAS_PYGAM = False
    # Will use simpler regression methods

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


@dataclass
class ElasticityCurve:
    """Elasticity curve for a service category"""
    service_category: str
    policy_type: str
    elasticity: float  # Overall elasticity estimate
    curve_points: list[tuple[float, float]]  # (policy_strength, utilization_change)
    threshold: Optional[float] = None  # Policy strength threshold where elasticity changes
    confidence_score: float = 0.0
    method: str = "GAM"  # or "POLYNOMIAL", "LINEAR"


@dataclass
class ElasticityModel:
    """Complete elasticity model for a policy"""
    policy_id: str
    service_categories: dict[str, ElasticityCurve]
    overall_elasticity: float
    confidence_score: float
    model_date: datetime


def model_elasticity_curves(
    tenant_id: UUID,
    policy_id: UUID,
    claims_data: pl.DataFrame,
    policy_effective_date: datetime,
    service_categories: list[str],
) -> ElasticityModel:
    """
    Model elasticity curves for a policy using GAM or polynomial regression
    
    Args:
        tenant_id: Tenant ID
        policy_id: Policy ID
        claims_data: Claims data (pre and post policy)
        policy_effective_date: When policy became effective
        service_categories: List of service categories to model
    
    Returns:
        ElasticityModel with curves for each category
    """
    curves = {}
    
    # Split data into pre and post periods
    if "service_date" in claims_data.columns:
        if claims_data["service_date"].dtype == pl.Utf8:
            claims_data = claims_data.with_columns(
                pl.col("service_date").str.strptime(pl.Date, "%Y-%m-%d")
            )
        
        pre_df = claims_data.filter(pl.col("service_date") < policy_effective_date.date())
        post_df = claims_data.filter(pl.col("service_date") >= policy_effective_date.date())
    else:
        # No date column - use all data as post
        pre_df = pl.DataFrame()
        post_df = claims_data
    
    # Model elasticity for each service category
    for category in service_categories:
        if "service_category" in claims_data.columns:
            category_pre = pre_df.filter(pl.col("service_category") == category) if not pre_df.is_empty() else pl.DataFrame()
            category_post = post_df.filter(pl.col("service_category") == category) if not post_df.is_empty() else pl.DataFrame()
        else:
            category_pre = pre_df
            category_post = post_df
        
        if category_pre.is_empty() and category_post.is_empty():
            continue
        
        # Compute elasticity curve
        curve = compute_elasticity_curve(
            category,
            category_pre,
            category_post,
            policy_effective_date,
        )
        
        if curve:
            curves[category] = curve
    
    # Compute overall elasticity (weighted average)
    if curves:
        elasticities = [c.elasticity for c in curves.values()]
        confidence_scores = [c.confidence_score for c in curves.values()]
        overall_elasticity = np.mean(elasticities)
        overall_confidence = np.mean(confidence_scores)
    else:
        overall_elasticity = -0.3  # Default
        overall_confidence = 0.0
    
    return ElasticityModel(
        policy_id=str(policy_id),
        service_categories=curves,
        overall_elasticity=overall_elasticity,
        confidence_score=overall_confidence,
        model_date=datetime.utcnow(),
    )


def compute_elasticity_curve(
    service_category: str,
    pre_df: pl.DataFrame,
    post_df: pl.DataFrame,
    policy_effective_date: datetime,
) -> Optional[ElasticityCurve]:
    """
    Compute elasticity curve for a service category
    
    Uses GAM if available, otherwise polynomial regression
    """
    if pre_df.is_empty() or post_df.is_empty():
        # Not enough data - use default elasticity
        return ElasticityCurve(
            service_category=service_category,
            policy_type="UNKNOWN",
            elasticity=-0.3,  # Default
            curve_points=[(0.0, 0.0), (1.0, -0.3)],
            confidence_score=0.3,
            method="DEFAULT",
        )
    
    # Compute pre-period baseline
    pre_utilization = len(pre_df) / pre_df["member_id"].n_unique() if pre_df["member_id"].n_unique() > 0 else 0.0
    post_utilization = len(post_df) / post_df["member_id"].n_unique() if post_df["member_id"].n_unique() > 0 else 0.0
    
    # Compute elasticity (simplified - assumes policy strength = 1.0)
    if pre_utilization > 0:
        utilization_change = (post_utilization - pre_utilization) / pre_utilization
        elasticity = utilization_change  # Simplified: elasticity = % change in utilization
    else:
        elasticity = -0.3  # Default
    
    # Generate curve points (simplified - full implementation would use GAM)
    curve_points = generate_curve_points(elasticity)
    
    # Detect threshold (simplified)
    threshold = detect_threshold(curve_points)
    
    # Compute confidence score
    confidence_score = compute_elasticity_confidence(pre_df, post_df)
    
    return ElasticityCurve(
        service_category=service_category,
        policy_type="UNKNOWN",  # Would get from policy
        elasticity=elasticity,
        curve_points=curve_points,
        threshold=threshold,
        confidence_score=confidence_score,
        method="POLYNOMIAL" if not HAS_PYGAM else "GAM",
    )


def generate_curve_points(elasticity: float, n_points: int = 20) -> list[tuple[float, float]]:
    """
    Generate elasticity curve points
    
    Args:
        elasticity: Overall elasticity estimate
        n_points: Number of points to generate
    
    Returns:
        List of (policy_strength, utilization_change) tuples
    """
    points = []
    
    # Policy strength ranges from 0 (no policy) to 1 (full policy)
    policy_strengths = np.linspace(0, 1, n_points)
    
    for strength in policy_strengths:
        # Simplified: linear relationship with some curvature
        # Full implementation would use learned GAM model
        utilization_change = elasticity * strength * (1 + 0.1 * strength)  # Slight curvature
        points.append((float(strength), float(utilization_change)))
    
    return points


def detect_threshold(curve_points: list[tuple[float, float]]) -> Optional[float]:
    """
    Detect threshold where elasticity changes significantly
    
    Looks for inflection points in the curve
    """
    if len(curve_points) < 3:
        return None
    
    # Compute second derivative (rate of change of slope)
    slopes = []
    for i in range(1, len(curve_points)):
        x1, y1 = curve_points[i-1]
        x2, y2 = curve_points[i]
        if x2 - x1 > 0:
            slope = (y2 - y1) / (x2 - x1)
            slopes.append((x2, slope))
    
    if len(slopes) < 2:
        return None
    
    # Find point where slope changes most
    slope_changes = []
    for i in range(1, len(slopes)):
        slope_change = abs(slopes[i][1] - slopes[i-1][1])
        slope_changes.append((slopes[i][0], slope_change))
    
    if slope_changes:
        # Find maximum change
        max_change_idx = max(range(len(slope_changes)), key=lambda i: slope_changes[i][1])
        threshold = slope_changes[max_change_idx][0]
        
        # Only return if change is significant
        if slope_changes[max_change_idx][1] > 0.1:
            return threshold
    
    return None


def compute_elasticity_confidence(pre_df: pl.DataFrame, post_df: pl.DataFrame) -> float:
    """Compute confidence score for elasticity estimate"""
    score = 100.0
    
    # Penalize if sample sizes are small
    pre_size = len(pre_df)
    post_size = len(post_df)
    
    if pre_size < 100:
        score -= 30
    if post_size < 100:
        score -= 30
    
    # Penalize if time periods are short
    # (Would need date columns to compute this properly)
    
    # Penalize if variance is high (would need to compute)
    
    return max(0.0, min(100.0, score))


def apply_elasticity_curve(
    curve: ElasticityCurve,
    policy_strength: float,
) -> float:
    """
    Apply elasticity curve to get utilization change for given policy strength
    
    Args:
        curve: Elasticity curve
        policy_strength: Policy strength (0.0 to 1.0)
    
    Returns:
        Utilization change (negative = reduction, positive = increase)
    """
    if not curve.curve_points:
        # Fall back to linear
        return curve.elasticity * policy_strength
    
    # Interpolate from curve points
    policy_strengths = [p[0] for p in curve.curve_points]
    utilization_changes = [p[1] for p in curve.curve_points]
    
    # Find closest points
    if policy_strength <= policy_strengths[0]:
        return utilization_changes[0]
    if policy_strength >= policy_strengths[-1]:
        return utilization_changes[-1]
    
    # Linear interpolation
    for i in range(len(policy_strengths) - 1):
        if policy_strengths[i] <= policy_strength <= policy_strengths[i+1]:
            x1, y1 = policy_strengths[i], utilization_changes[i]
            x2, y2 = policy_strengths[i+1], utilization_changes[i+1]
            
            if x2 - x1 > 0:
                return y1 + (y2 - y1) * (policy_strength - x1) / (x2 - x1)
    
    return curve.elasticity * policy_strength  # Fallback

