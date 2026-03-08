"""
Scorecard Generation - Computes policy effectiveness index and detailed breakdowns
Aggregates impact analysis results to create quarterly/annual scorecards
"""
from typing import Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
import polars as pl
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field

from uepi_common.analytics.impact import ImpactAnalysisEngine
from uepi_common.analytics.substitution import SubstitutionDetector
from uepi_common.analytics.provider_segmentation import ProviderSegmentation


class ScorecardMetrics(BaseModel):
    """Scorecard metrics for a policy"""
    policy_id: UUID
    period: str  # e.g., "2026-Q1", "2026"
    effectiveness_index: float = Field(..., ge=0, le=100, description="Composite score 0-100")
    cost_impact_score: float = Field(..., ge=0, le=100, description="Cost impact score (0-100, higher = better cost reduction)")
    behavioral_risk_score: float = Field(..., ge=0, le=100, description="Behavioral risk score (0-100, higher = higher risk)")
    access_impact_score: float = Field(..., ge=0, le=100, description="Access impact score (0-100, higher = better access)")
    regulatory_defensibility_score: float = Field(..., ge=0, le=100, description="Regulatory defensibility (0-100, higher = more defensible)")
    entries: list[dict[str, Any]] = Field(default_factory=list, description="Detailed breakdown entries")
    trends: dict[str, str] = Field(default_factory=dict, description="Trend indicators (UP/DOWN/STABLE)")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScorecardGenerator:
    """
    Generates policy scorecards by aggregating impact analysis results
    
    Effectiveness Index = weighted combination of:
    - Cost Impact Score (weight: 0.4)
    - Behavioral Risk Score (weight: 0.3) - inverted (higher substitution = lower score
    - Access Impact Score (weight: 0.2) - inverted (higher restriction = lower score)
    - Regulatory Defensibility Score (weight: 0.1) - based on method checks, confidence, documentation
    """
    
    def __init__(self, storage_client, bucket: str):
        self.storage_client = storage_client
        self.bucket = bucket
        self.impact_engine = ImpactAnalysisEngine(storage_client, bucket)
        self.substitution_detector = SubstitutionDetector(storage_client, bucket)
        self.provider_segmentation = ProviderSegmentation(storage_client, bucket)
    
    def generate_scorecard(
        self,
        tenant_id: UUID,
        policy_id: UUID,
        period: str,
        analysis_ids: Optional[list[UUID]] = None,
        weights: Optional[dict[str, float]] = None,
    ) -> ScorecardMetrics:
        """
        Generate scorecard for a policy for a given period
        
        Args:
            tenant_id: Tenant ID
            policy_id: Policy ID
            period: Period string (e.g., "2026-Q1", "2026")
            analysis_ids: Optional list of analysis IDs to aggregate. If None, finds analyses for this policy in this period
            weights: Optional custom weights for score components. Default weights:
                - cost_impact: 0.4
                - behavioral_risk: 0.3
                - access_impact: 0.2
                - regulatory_defensibility: 0.1
        
        Returns:
            ScorecardMetrics with effectiveness index and detailed breakdown
        """
        # Default weights
        default_weights = {
            "cost_impact": 0.4,
            "behavioral_risk": 0.3,
            "access_impact": 0.2,
            "regulatory_defensibility": 0.1,
        }
        weights = weights or default_weights
        
        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
        
        # Find impact analyses for this policy in this period
        if not analysis_ids:
            analysis_ids = self._find_analyses_for_period(tenant_id, policy_id, period)
        
        if not analysis_ids:
            # No analyses found - return default scorecard
            return self._get_default_scorecard(policy_id, period)
        
        # Aggregate impact results
        impact_results = self._aggregate_impact_results(tenant_id, analysis_ids)
        
        # Aggregate substitution results
        substitution_results = self._aggregate_substitution_results(tenant_id, analysis_ids)
        
        # Aggregate provider segmentation results
        segmentation_results = self._aggregate_segmentation_results(tenant_id, analysis_ids)
        
        # Compute component scores
        cost_impact_score = self._compute_cost_impact_score(impact_results)
        behavioral_risk_score = self._compute_behavioral_risk_score(substitution_results, segmentation_results)
        access_impact_score = self._compute_access_impact_score(impact_results, substitution_results)
        regulatory_defensibility_score = self._compute_regulatory_defensibility_score(tenant_id, analysis_ids)
        
        # Compute effectiveness index (weighted combination)
        effectiveness_index = (
            cost_impact_score * weights["cost_impact"] +
            (100 - behavioral_risk_score) * weights["behavioral_risk"] +  # Invert behavioral risk
            access_impact_score * weights["access_impact"] +
            regulatory_defensibility_score * weights["regulatory_defensibility"]
        )
        
        # Build entries (detailed breakdown)
        entries = self._build_scorecard_entries(
            impact_results,
            substitution_results,
            segmentation_results,
        )
        
        # Compute trends
        trends = self._compute_trends(tenant_id, policy_id, period)
        
        return ScorecardMetrics(
            policy_id=policy_id,
            period=period,
            effectiveness_index=effectiveness_index,
            cost_impact_score=cost_impact_score,
            behavioral_risk_score=behavioral_risk_score,
            access_impact_score=access_impact_score,
            regulatory_defensibility_score=regulatory_defensibility_score,
            entries=entries,
            trends=trends,
        )
    
    def _find_analyses_for_period(
        self,
        tenant_id: UUID,
        policy_id: UUID,
        period: str,
    ) -> list[UUID]:
        """Find impact analyses for this policy in this period"""
        # For MVP, return empty list - would query Analysis table filtered by policy_id and period
        # Full implementation would:
        # 1. Parse period (e.g., "2026-Q1" -> start_date=2026-01-01, end_date=2026-03-31)
        # 2. Query Analysis table where:
        #    - tenant_id = tenant_id
        #    - policy_id = policy_id
        #    - analysis_type = 'IMPACT'
        #    - created_at between start_date and end_date
        # 3. Return list of analysis IDs
        return []
    
    def _aggregate_impact_results(
        self,
        tenant_id: UUID,
        analysis_ids: list[UUID],
    ) -> dict[str, Any]:
        """Aggregate impact analysis results"""
        # For MVP, return default structure
        # Full implementation would:
        # 1. Load impact results from each analysis_id
        # 2. Aggregate effect sizes, confidence intervals, percent changes
        # 3. Compute averages, medians, ranges
        return {
            "avg_effect_size": -15.5,
            "avg_percent_change": -12.5,
            "avg_allowed_pmpm_delta": -5.50,
            "total_analyses": len(analysis_ids),
            "confidence_score_avg": 85.0,
        }
    
    def _aggregate_substitution_results(
        self,
        tenant_id: UUID,
        analysis_ids: list[UUID],
    ) -> dict[str, Any]:
        """Aggregate substitution detection results"""
        # For MVP, return default structure
        return {
            "total_substitutions": 5,
            "high_confidence_count": 3,
            "site_of_care_shifts": 2,
            "service_substitutions": 3,
            "avg_confidence": 75.0,
        }
    
    def _aggregate_segmentation_results(
        self,
        tenant_id: UUID,
        analysis_ids: list[UUID],
    ) -> dict[str, Any]:
        """Aggregate provider segmentation results"""
        # For MVP, return default structure
        return {
            "total_providers": 250,
            "circumventers_count": 50,
            "compliers_count": 200,
            "circumvention_rate": 0.2,  # 20% of providers circumvent
        }
    
    def _compute_cost_impact_score(self, impact_results: dict[str, Any]) -> float:
        """Compute cost impact score (0-100, higher = better cost reduction)"""
        # Based on allowed PMPM delta and percent change
        avg_delta = impact_results.get("avg_allowed_pmpm_delta", 0.0)
        avg_pct_change = impact_results.get("avg_percent_change", 0.0)
        
        # Score: 0-100 based on cost reduction
        # Negative delta = cost reduction = higher score
        # Positive delta = cost increase = lower score
        if avg_delta < -10:
            return 90.0  # Strong cost reduction
        elif avg_delta < -5:
            return 75.0  # Moderate cost reduction
        elif avg_delta < 0:
            return 60.0  # Mild cost reduction
        elif avg_delta < 5:
            return 40.0  # Mild cost increase
        else:
            return 20.0  # Strong cost increase
    
    def _compute_behavioral_risk_score(
        self,
        substitution_results: dict[str, Any],
        segmentation_results: dict[str, Any],
    ) -> float:
        """Compute behavioral risk score (0-100, higher = higher risk of substitution/circumvention)"""
        # Based on substitution count, circumventer rate
        total_substitutions = substitution_results.get("total_substitutions", 0)
        circumventer_rate = segmentation_results.get("circumvention_rate", 0.0)
        
        # Score: 0-100 based on behavioral risk
        substitution_score = min(100, total_substitutions * 10)  # 10 points per substitution, capped at 100
        circumvention_score = circumventer_rate * 100  # 0-100 based on circumventer rate
        
        # Combine scores (weighted average)
        return (substitution_score * 0.6 + circumvention_score * 0.4)
    
    def _compute_access_impact_score(
        self,
        impact_results: dict[str, Any],
        substitution_results: dict[str, Any],
    ) -> float:
        """Compute access impact score (0-100, higher = better access maintained)"""
        # Based on utilization change and substitution patterns
        utilization_change = impact_results.get("avg_percent_change", 0.0)
        service_substitutions = substitution_results.get("service_substitutions", 0)
        
        # Negative utilization change = utilization decrease = potential access restriction
        # Service substitutions = members finding alternatives = access maintained
        
        # Score: 0-100 based on access impact
        if utilization_change > -5 and service_substitutions == 0:
            return 90.0  # Good access maintained, no substitution needed
        elif utilization_change > -10 and service_substitutions < 3:
            return 75.0  # Moderate access restriction, some substitution
        elif utilization_change > -20 and service_substitutions >= 3:
            return 60.0  # Access restriction but members found alternatives
        else:
            return 40.0  # Significant access restriction
    
    def _compute_regulatory_defensibility_score(
        self,
        tenant_id: UUID,
        analysis_ids: list[UUID],
    ) -> float:
        """Compute regulatory defensibility score (0-100, higher = more defensible)"""
        # Based on method checks, confidence scores, documentation quality
        # For MVP, return default score based on confidence
        # Full implementation would:
        # 1. Load method checks for each analysis
        # 2. Check pre-trends, control balance, seasonality
        # 3. Check confidence scores
        # 4. Check documentation completeness
        # 5. Combine into defensibility score
        
        # Default: assume good defensibility if analyses exist
        if len(analysis_ids) > 0:
            return 80.0  # Good defensibility with impact analyses
        else:
            return 50.0  # Moderate defensibility without analyses
    
    def _build_scorecard_entries(
        self,
        impact_results: dict[str, Any],
        substitution_results: dict[str, Any],
        segmentation_results: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Build detailed scorecard entries"""
        entries = []
        
        # Cost dimension entries
        entries.append({
            "dimension": "COST",
            "metric_name": "Allowed PMPM Delta",
            "metric_value": impact_results.get("avg_allowed_pmpm_delta", 0.0),
            "metric_unit": "$",
            "trend": "DOWN" if impact_results.get("avg_allowed_pmpm_delta", 0.0) < 0 else "UP",
        })
        entries.append({
            "dimension": "COST",
            "metric_name": "Utilization Change",
            "metric_value": impact_results.get("avg_percent_change", 0.0),
            "metric_unit": "%",
            "trend": "DOWN" if impact_results.get("avg_percent_change", 0.0) < 0 else "UP",
        })
        
        # Behavioral dimension entries
        entries.append({
            "dimension": "BEHAVIORAL",
            "metric_name": "Total Substitutions",
            "metric_value": float(substitution_results.get("total_substitutions", 0)),
            "metric_unit": "count",
            "trend": "UP" if substitution_results.get("total_substitutions", 0) > 0 else "STABLE",
        })
        entries.append({
            "dimension": "BEHAVIORAL",
            "metric_name": "Circumvention Rate",
            "metric_value": segmentation_results.get("circumvention_rate", 0.0) * 100,
            "metric_unit": "%",
            "trend": "UP" if segmentation_results.get("circumvention_rate", 0.0) > 0.2 else "STABLE",
        })
        
        # Access dimension entries
        entries.append({
            "dimension": "ACCESS",
            "metric_name": "Service Substitutions",
            "metric_value": float(substitution_results.get("service_substitutions", 0)),
            "metric_unit": "count",
            "trend": "UP" if substitution_results.get("service_substitutions", 0) > 0 else "STABLE",
        })
        
        # Regulatory dimension entries
        entries.append({
            "dimension": "REGULATORY",
            "metric_name": "Confidence Score",
            "metric_value": impact_results.get("confidence_score_avg", 0.0),
            "metric_unit": "points",
            "trend": "STABLE",
        })
        
        return entries
    
    def _compute_trends(
        self,
        tenant_id: UUID,
        policy_id: UUID,
        period: str,
    ) -> dict[str, str]:
        """Compute trend indicators by comparing with previous period"""
        # For MVP, return default trends
        # Full implementation would:
        # 1. Find previous period (e.g., "2026-Q1" -> "2025-Q4")
        # 2. Load scorecards for previous period
        # 3. Compare metrics (UP/DOWN/STABLE)
        return {
            "effectiveness_index": "STABLE",
            "cost_impact": "DOWN",
            "behavioral_risk": "STABLE",
            "access_impact": "STABLE",
        }
    
    def _get_default_scorecard(self, policy_id: UUID, period: str) -> ScorecardMetrics:
        """Get default scorecard when no analyses exist"""
        return ScorecardMetrics(
            policy_id=policy_id,
            period=period,
            effectiveness_index=50.0,  # Neutral score
            cost_impact_score=50.0,
            behavioral_risk_score=50.0,
            access_impact_score=50.0,
            regulatory_defensibility_score=50.0,
            entries=[],
            trends={},
        )

