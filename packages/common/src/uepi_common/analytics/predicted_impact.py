"""
Predicted Impact Model (Stage 3.5)
Generates predictive "expected impact" when a policy is created, before implementation.
Uses elasticity models, behavioral models, provider compliance probabilities, patient sensitivity, and substitution patterns.
"""
from typing import Any, Optional, Dict
from datetime import datetime
from uuid import UUID
from dataclasses import dataclass
from pydantic import BaseModel, Field

import numpy as np


class PredictedImpactMetrics(BaseModel):
    """Predicted impact metrics"""
    utilization_change_per_1k: float = Field(..., description="Predicted change in utilization per 1,000 members")
    cost_change_pmpm: float = Field(..., description="Predicted change in cost per member per month ($)")
    cost_change_total: float = Field(..., description="Predicted total cost change")
    utilization_change_pct: float = Field(..., description="Predicted percentage change in utilization")
    cost_change_pct: float = Field(..., description="Predicted percentage change in cost")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence score (0-100)")
    prediction_method: str = Field(..., description="Method used for prediction (e.g., 'ELASTICITY_MODEL', 'BEHAVIORAL_MODEL')")


class PredictedSubstitutionEffect(BaseModel):
    """Predicted substitution effects"""
    service_category: str
    predicted_substitution_rate: float = Field(..., ge=0, le=1, description="Predicted rate of substitution (0-1)")
    predicted_substitute_services: list[str] = Field(default_factory=list, description="List of predicted substitute services")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence in substitution prediction")


class PredictedProviderResponse(BaseModel):
    """Predicted provider response distribution"""
    compliant_pct: float = Field(..., ge=0, le=100, description="Percentage of providers predicted to be compliant")
    adaptive_pct: float = Field(..., ge=0, le=100, description="Percentage predicted to adapt")
    resistant_pct: float = Field(..., ge=0, le=100, description="Percentage predicted to resist")
    circumvention_pct: float = Field(..., ge=0, le=100, description="Percentage predicted to circumvent")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence in provider response prediction")


class PredictedPatientResponse(BaseModel):
    """Predicted patient response signals"""
    defer_rate: float = Field(..., ge=0, le=1, description="Predicted rate of care deferral")
    substitute_rate: float = Field(..., ge=0, le=1, description="Predicted rate of service substitution")
    er_fallback_rate: float = Field(..., ge=0, le=1, description="Predicted ER fallback rate (adverse effect)")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence in patient response prediction")


class PredictedImpactResult(BaseModel):
    """Complete predicted impact result (Stage 3.5)"""
    policy_id: UUID
    predicted_at: datetime = Field(default_factory=datetime.utcnow, description="When prediction was generated")
    metrics: PredictedImpactMetrics
    substitution_effects: list[PredictedSubstitutionEffect] = Field(default_factory=list)
    provider_response: Optional[PredictedProviderResponse] = None
    patient_response: Optional[PredictedPatientResponse] = None
    baseline_reference: Optional[Dict[str, Any]] = Field(None, description="Reference to baseline data used")
    model_versions: Dict[str, str] = Field(default_factory=dict, description="Versions of models used")
    warnings: list[str] = Field(default_factory=list, description="Warnings about prediction quality")
    limitations: list[str] = Field(default_factory=list, description="Limitations of the prediction")


class PredictedImpactGenerator:
    """
    Generates predictive expected impact for a policy (Stage 3.5)
    
    Uses:
    - Elasticity models (from elasticity.py)
    - Behavioral models
    - Provider compliance probabilities
    - Patient sensitivity
    - Substitution patterns
    """
    
    def __init__(self, tenant_id: UUID):
        """Initialize predicted impact generator"""
        self.tenant_id = tenant_id
    
    def generate_predicted_impact(
        self,
        policy_id: UUID,
        policy_levers: list[Dict[str, Any]],
        policy_scope: Optional[Dict[str, Any]] = None,
        baseline_metrics: Optional[Dict[str, Any]] = None,
        elasticity_data: Optional[Dict[str, Any]] = None,
    ) -> PredictedImpactResult:
        """
        Generate predicted impact for a policy
        
        Args:
            policy_id: Policy ID
            policy_levers: List of policy levers (from policy definition)
            policy_scope: Policy scope (lob, markets, network)
            baseline_metrics: Optional baseline metrics (if available)
            elasticity_data: Optional elasticity data (if available)
            
        Returns:
            PredictedImpactResult with predicted metrics and behavioral responses
        """
        # For MVP, use simplified prediction model
        # Full implementation would:
        # 1. Load elasticity models for affected services
        # 2. Apply provider compliance probabilities
        # 3. Apply patient sensitivity models
        # 4. Predict substitution patterns
        # 5. Aggregate to overall impact
        
        # Extract affected services from policy levers
        affected_services = self._extract_affected_services(policy_levers)
        
        # Estimate policy "friction" level (simplified)
        friction_level = self._estimate_friction_level(policy_levers)
        
        # Use default elasticity if not provided
        if not elasticity_data:
            elasticity_data = self._get_default_elasticity(affected_services)
        
        # Predict utilization change using elasticity
        utilization_change_pct = self._predict_utilization_change(
            friction_level, elasticity_data
        )
        
        # Predict cost change (simplified - assumes cost changes proportionally)
        cost_change_pct = utilization_change_pct * 0.9  # Slight cost reduction per unit due to selection
        
        # Get baseline metrics (if provided, otherwise use defaults)
        baseline_utilization = baseline_metrics.get("utilization_per_1k", 100.0) if baseline_metrics else 100.0
        baseline_cost_pmpm = baseline_metrics.get("cost_pmpm", 500.0) if baseline_metrics else 500.0
        member_count = baseline_metrics.get("member_count", 10000) if baseline_metrics else 10000
        
        # Calculate predicted changes
        utilization_change_per_1k = baseline_utilization * (utilization_change_pct / 100)
        cost_change_pmpm = baseline_cost_pmpm * (cost_change_pct / 100)
        cost_change_total = cost_change_pmpm * member_count * 12  # Annual cost change
        
        # Predict substitution effects
        substitution_effects = self._predict_substitution_effects(
            affected_services, friction_level
        )
        
        # Predict provider response
        provider_response = self._predict_provider_response(policy_levers, friction_level)
        
        # Predict patient response
        patient_response = self._predict_patient_response(policy_levers, friction_level)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            elasticity_data, baseline_metrics, policy_levers
        )
        
        # Determine prediction method
        prediction_method = "ELASTICITY_MODEL" if elasticity_data else "DEFAULT_MODEL"
        
        # Collect warnings and limitations
        warnings = []
        limitations = []
        if not elasticity_data:
            warnings.append("Using default elasticity estimates - prediction may be less accurate")
            limitations.append("No historical elasticity data available")
        if not baseline_metrics:
            warnings.append("Using default baseline metrics - prediction accuracy may be reduced")
            limitations.append("Baseline metrics not available")
        if friction_level < 0.3:
            warnings.append("Low policy friction - impact may be minimal")
        
        return PredictedImpactResult(
            policy_id=policy_id,
            predicted_at=datetime.utcnow(),
            metrics=PredictedImpactMetrics(
                utilization_change_per_1k=utilization_change_per_1k,
                cost_change_pmpm=cost_change_pmpm,
                cost_change_total=cost_change_total,
                utilization_change_pct=utilization_change_pct,
                cost_change_pct=cost_change_pct,
                confidence_score=confidence_score,
                prediction_method=prediction_method,
            ),
            substitution_effects=substitution_effects,
            provider_response=provider_response,
            patient_response=patient_response,
            baseline_reference=baseline_metrics,
            model_versions={
                "elasticity": "1.0",
                "behavioral": "1.0",
                "provider_response": "1.0",
                "patient_response": "1.0",
            },
            warnings=warnings,
            limitations=limitations,
        )
    
    def _extract_affected_services(self, policy_levers: list[Dict[str, Any]]) -> list[str]:
        """Extract affected service categories from policy levers"""
        services = set()
        for lever in policy_levers:
            lever_type = lever.get("lever_type", "")
            # Map lever types to service categories
            if lever_type in ["PRIOR_AUTH", "CLINICAL_CRITERIA"]:
                codes = lever.get("parameters", {}).get("codes", [])
                # Determine service category from codes (simplified)
                if any("721" in str(c) for c in codes):  # MRI codes
                    services.add("IMAGING")
                elif any("971" in str(c) for c in codes):  # PT codes
                    services.add("PHYSICAL_THERAPY")
                elif any("992" in str(c) for c in codes):  # Office visit codes
                    services.add("SPECIALTY_CARE")
                else:
                    services.add("OTHER")
            elif lever_type == "SITE_OF_CARE":
                services.add("FACILITY_CARE")
            elif lever_type in ["QUANTITY_LIMIT", "DURATION_FREQUENCY_LIMIT"]:
                services.add("THERAPY_SERVICES")
            else:
                services.add("GENERAL")
        return list(services) if services else ["GENERAL"]
    
    def _estimate_friction_level(self, policy_levers: list[Dict[str, Any]]) -> float:
        """
        Estimate policy friction level (0-1, where 1 = highest friction)
        
        Simplified: Based on lever types and enforcement strength
        """
        friction = 0.0
        for lever in policy_levers:
            lever_type = lever.get("lever_type", "")
            enforcement = lever.get("enforcement_strength", "SOFT")
            
            # Base friction by lever type
            lever_friction = {
                "PRIOR_AUTH": 0.6,
                "CLINICAL_CRITERIA": 0.5,
                "SITE_OF_CARE": 0.4,
                "QUANTITY_LIMIT": 0.3,
                "DURATION_FREQUENCY_LIMIT": 0.3,
                "COST_SHARING": 0.5,
                "NETWORK_RESTRICTION": 0.4,
                "REFERRAL_REQUIREMENT": 0.3,
            }.get(lever_type, 0.3)
            
            # Adjust by enforcement
            if enforcement == "HARD":
                lever_friction *= 1.2
            elif enforcement == "SOFT":
                lever_friction *= 0.8
            
            friction = max(friction, lever_friction)  # Use maximum friction
        
        return min(1.0, friction)
    
    def _get_default_elasticity(self, service_categories: list[str]) -> Dict[str, float]:
        """Get default elasticity coefficients by service category"""
        default_elasticity = {
            "IMAGING": -0.35,
            "PHYSICAL_THERAPY": -0.40,
            "SPECIALTY_CARE": -0.30,
            "FACILITY_CARE": -0.25,
            "THERAPY_SERVICES": -0.35,
            "GENERAL": -0.30,
            "OTHER": -0.30,
        }
        # Return average elasticity for affected services
        elasticities = [default_elasticity.get(cat, -0.30) for cat in service_categories]
        return {
            "overall_elasticity": np.mean(elasticities) if elasticities else -0.30,
            "service_elasticities": {cat: default_elasticity.get(cat, -0.30) for cat in service_categories},
        }
    
    def _predict_utilization_change(
        self, friction_level: float, elasticity_data: Dict[str, Any]
    ) -> float:
        """
        Predict utilization change percentage using elasticity
        
        Simplified: utilization_change = friction_level * elasticity_coefficient * 100
        """
        elasticity = elasticity_data.get("overall_elasticity", -0.30)
        # Negative elasticity means utilization decreases with friction
        utilization_change_pct = friction_level * elasticity * 100
        return utilization_change_pct
    
    def _predict_substitution_effects(
        self, affected_services: list[str], friction_level: float
    ) -> list[PredictedSubstitutionEffect]:
        """Predict substitution effects"""
        effects = []
        
        # Simplified substitution patterns
        substitution_patterns = {
            "IMAGING": {
                "substitute_services": ["URGENT_CARE", "OFFICE_VISIT"],
                "base_rate": 0.15,
            },
            "PHYSICAL_THERAPY": {
                "substitute_services": ["HOME_HEALTH", "SELF_CARE"],
                "base_rate": 0.20,
            },
            "SPECIALTY_CARE": {
                "substitute_services": ["PRIMARY_CARE", "URGENT_CARE"],
                "base_rate": 0.25,
            },
        }
        
        for service in affected_services:
            pattern = substitution_patterns.get(service, {
                "substitute_services": [],
                "base_rate": 0.10,
            })
            substitution_rate = pattern["base_rate"] * friction_level
            
            effects.append(PredictedSubstitutionEffect(
                service_category=service,
                predicted_substitution_rate=substitution_rate,
                predicted_substitute_services=pattern["substitute_services"],
                confidence_score=70.0,  # Moderate confidence for MVP
            ))
        
        return effects
    
    def _predict_provider_response(
        self, policy_levers: list[Dict[str, Any]], friction_level: float
    ) -> PredictedProviderResponse:
        """Predict provider response distribution"""
        # Simplified: Based on friction level
        # Higher friction -> more resistance/circumvention
        
        if friction_level < 0.3:
            # Low friction - mostly compliant
            compliant = 70
            adaptive = 20
            resistant = 8
            circumvention = 2
        elif friction_level < 0.6:
            # Medium friction - mixed response
            compliant = 50
            adaptive = 30
            resistant = 15
            circumvention = 5
        else:
            # High friction - more resistance
            compliant = 35
            adaptive = 30
            resistant = 25
            circumvention = 10
        
        return PredictedProviderResponse(
            compliant_pct=compliant,
            adaptive_pct=adaptive,
            resistant_pct=resistant,
            circumvention_pct=circumvention,
            confidence_score=75.0,  # Moderate confidence for MVP
        )
    
    def _predict_patient_response(
        self, policy_levers: list[Dict[str, Any]], friction_level: float
    ) -> PredictedPatientResponse:
        """Predict patient response signals"""
        # Simplified: Based on friction level
        # Higher friction -> more deferral, substitution, ER fallback
        
        defer_rate = 0.10 * friction_level
        substitute_rate = 0.15 * friction_level
        er_fallback_rate = 0.05 * friction_level  # Adverse effect
        
        return PredictedPatientResponse(
            defer_rate=defer_rate,
            substitute_rate=substitute_rate,
            er_fallback_rate=er_fallback_rate,
            confidence_score=70.0,  # Moderate confidence for MVP
        )
    
    def _calculate_confidence_score(
        self,
        elasticity_data: Optional[Dict[str, Any]],
        baseline_metrics: Optional[Dict[str, Any]],
        policy_levers: list[Dict[str, Any]],
    ) -> float:
        """Calculate confidence score for prediction (0-100)"""
        score = 100.0
        
        # Reduce confidence if using default elasticity
        if not elasticity_data or elasticity_data.get("model_quality") == "POOR":
            score -= 30
        elif elasticity_data.get("model_quality") == "FAIR":
            score -= 15
        
        # Reduce confidence if baseline metrics not available
        if not baseline_metrics:
            score -= 20
        
        # Reduce confidence for complex policies (many levers)
        if len(policy_levers) > 3:
            score -= 10
        
        return max(0.0, min(100.0, score))
