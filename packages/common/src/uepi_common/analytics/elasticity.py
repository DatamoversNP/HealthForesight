"""
Elasticity Model - Estimates utilization sensitivity to policy friction
Uses interpretable ML (GAM/monotonic regression) to model elasticity curves
"""
from typing import Any, Optional
from datetime import datetime
from uuid import UUID
import numpy as np
import polars as pl
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field

from uepi_common.analytics.impact import ImpactAnalysisEngine


class ElasticityCurve(BaseModel):
    """Elasticity curve for a service category"""
    service_category: str
    elasticity_coefficient: float = Field(..., description="Overall elasticity coefficient (negative = demand decreases with friction)")
    elasticity_function: dict[str, float] = Field(default_factory=dict, description="Elasticity at different friction levels")
    threshold_friction: Optional[float] = Field(None, description="Friction level where elasticity changes significantly")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence in elasticity estimate (0-100)")
    data_points: int = Field(..., ge=0, description="Number of data points used for estimation")
    model_version: str = Field(default="1.0", description="Model version")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ElasticityResult(BaseModel):
    """Results from elasticity modeling"""
    policy_id: UUID
    service_categories: dict[str, ElasticityCurve] = Field(default_factory=dict)
    overall_elasticity: float = Field(..., description="Average elasticity across categories")
    model_quality: str = Field(..., description="GOOD/FAIR/POOR based on data sufficiency")
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ElasticityModeler:
    """
    Models utilization elasticity to policy friction using interpretable ML
    
    Approach (MVP):
    - Simplified regression-based elasticity estimation
    - Uses historical policy changes to estimate elasticity
    - Falls back to default elasticity if insufficient data
    - Full implementation would use GAM/monotonic regression
    """
    
    def __init__(self, storage_client, bucket: str):
        self.impact_engine = ImpactAnalysisEngine(storage_client, bucket)
        self.storage_client = storage_client
        self.bucket = bucket
    
    def estimate_elasticity(
        self,
        tenant_id: UUID,
        policy_id: UUID,
        service_categories: Optional[list[str]] = None,
    ) -> ElasticityResult:
        """
        Estimate elasticity curves for a policy
        
        Args:
            tenant_id: Tenant ID
            policy_id: Policy ID to model elasticity for
            service_categories: Optional list of service categories to model
        
        Returns:
            ElasticityResult with elasticity curves
        """
        # For MVP, use simplified approach based on historical impact analyses
        # Full implementation would:
        # 1. Load historical policy changes and their impacts
        # 2. Fit GAM/monotonic regression model
        # 3. Extract elasticity curves
        # 4. Estimate thresholds
        
        # Load historical impact analyses for this policy
        historical_analyses = self._load_historical_analyses(tenant_id, policy_id)
        
        if not historical_analyses or len(historical_analyses) < 2:
            # Insufficient data - use default elasticity
            return self._get_default_elasticity(policy_id, service_categories)
        
        # Estimate elasticity from historical impacts
        elasticity_curves = {}
        overall_elasticities = []
        
        for category in service_categories or ["ALL"]:
            category_elasticity = self._estimate_category_elasticity(
                historical_analyses,
                category,
            )
            elasticity_curves[category] = category_elasticity
            overall_elasticities.append(category_elasticity.elasticity_coefficient)
        
        overall_elasticity = np.mean(overall_elasticities) if overall_elasticities else -0.3
        
        # Determine model quality
        model_quality = "GOOD" if len(historical_analyses) >= 5 else "FAIR" if len(historical_analyses) >= 2 else "POOR"
        
        warnings = []
        if len(historical_analyses) < 5:
            warnings.append("Limited historical data - elasticity estimates may be less reliable")
        
        return ElasticityResult(
            policy_id=policy_id,
            service_categories=elasticity_curves,
            overall_elasticity=overall_elasticity,
            model_quality=model_quality,
            warnings=warnings,
        )
    
    def _load_historical_analyses(
        self,
        tenant_id: UUID,
        policy_id: UUID,
    ) -> list[dict[str, Any]]:
        """Load historical impact analyses for this policy"""
        # For MVP, return empty list - would load from database/storage
        # Full implementation would query Analysis table filtered by policy_id
        return []
    
    def _estimate_category_elasticity(
        self,
        historical_analyses: list[dict[str, Any]],
        category: str,
    ) -> ElasticityCurve:
        """Estimate elasticity for a specific category from historical analyses"""
        # For MVP, use default elasticity
        # Full implementation would:
        # 1. Extract policy friction levels from historical analyses
        # 2. Extract utilization changes
        # 3. Fit regression: utilization_change ~ friction_level
        # 4. Extract elasticity coefficient
        
        # Default elasticity based on category
        default_elasticity = {
            "IMAGING": -0.35,
            "LABORATORY": -0.25,
            "PHYSICAL_THERAPY": -0.40,
            "SPECIALTY_CARE": -0.30,
            "URGENT_CARE": -0.25,
            "ALL": -0.30,
        }
        
        elasticity_coef = default_elasticity.get(category, -0.30)
        
        # Build elasticity function (linear for MVP)
        elasticity_function = {
            "0.0": elasticity_coef * 0.0,
            "0.25": elasticity_coef * 0.25,
            "0.5": elasticity_coef * 0.5,
            "0.75": elasticity_coef * 0.75,
            "1.0": elasticity_coef,
        }
        
        # Estimate threshold (friction level where elasticity changes)
        # For MVP, use 0.5 (moderate friction)
        threshold_friction = 0.5
        
        # Confidence score based on data availability
        confidence_score = 70.0 if len(historical_analyses) >= 5 else 50.0 if len(historical_analyses) >= 2 else 30.0
        
        return ElasticityCurve(
            service_category=category,
            elasticity_coefficient=elasticity_coef,
            elasticity_function=elasticity_function,
            threshold_friction=threshold_friction,
            confidence_score=confidence_score,
            data_points=len(historical_analyses),
        )
    
    def _get_default_elasticity(
        self,
        policy_id: UUID,
        service_categories: Optional[list[str]] = None,
    ) -> ElasticityResult:
        """Get default elasticity when insufficient data"""
        categories = service_categories or ["ALL"]
        
        elasticity_curves = {}
        for category in categories:
            default_elasticity = {
                "IMAGING": -0.35,
                "LABORATORY": -0.25,
                "PHYSICAL_THERAPY": -0.40,
                "SPECIALTY_CARE": -0.30,
                "URGENT_CARE": -0.25,
                "ALL": -0.30,
            }
            
            elasticity_coef = default_elasticity.get(category, -0.30)
            
            elasticity_function = {
                "0.0": elasticity_coef * 0.0,
                "0.25": elasticity_coef * 0.25,
                "0.5": elasticity_coef * 0.5,
                "0.75": elasticity_coef * 0.75,
                "1.0": elasticity_coef,
            }
            
            elasticity_curves[category] = ElasticityCurve(
                service_category=category,
                elasticity_coefficient=elasticity_coef,
                elasticity_function=elasticity_function,
                threshold_friction=0.5,
                confidence_score=50.0,  # Lower confidence for defaults
                data_points=0,
            )
        
        overall_elasticity = np.mean([c.elasticity_coefficient for c in elasticity_curves.values()])
        
        return ElasticityResult(
            policy_id=policy_id,
            service_categories=elasticity_curves,
            overall_elasticity=overall_elasticity,
            model_quality="POOR",
            warnings=["Insufficient historical data - using default elasticity estimates"],
        )
    
    def get_elasticity_for_friction(
        self,
        elasticity_curve: ElasticityCurve,
        friction_level: float,
    ) -> float:
        """
        Get elasticity at a specific friction level
        
        Args:
            elasticity_curve: Elasticity curve for category
            friction_level: Friction level (0.0-1.0)
        
        Returns:
            Elasticity at this friction level
        """
        # For MVP, use linear interpolation
        # Full implementation would use the learned elasticity function
        
        if friction_level <= 0.0:
            return 0.0
        
        if friction_level >= 1.0:
            return elasticity_curve.elasticity_coefficient
        
        # Linear interpolation
        elasticity_func = elasticity_curve.elasticity_function
        if not elasticity_func:
            # Fallback to linear
            return elasticity_curve.elasticity_coefficient * friction_level
        
        # Find closest points for interpolation
        friction_levels = sorted([float(k) for k in elasticity_func.keys()])
        
        if friction_level <= friction_levels[0]:
            return elasticity_func[str(friction_levels[0])]
        
        if friction_level >= friction_levels[-1]:
            return elasticity_func[str(friction_levels[-1])]
        
        # Interpolate
        for i in range(len(friction_levels) - 1):
            if friction_levels[i] <= friction_level <= friction_levels[i + 1]:
                x0, x1 = friction_levels[i], friction_levels[i + 1]
                y0 = elasticity_func[str(x0)]
                y1 = elasticity_func[str(x1)]
                
                # Linear interpolation
                t = (friction_level - x0) / (x1 - x0) if x1 != x0 else 0.0
                return y0 + t * (y1 - y0)
        
        # Fallback
        return elasticity_curve.elasticity_coefficient * friction_level

