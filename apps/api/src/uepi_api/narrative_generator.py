"""
API-level narrative generator that integrates data-driven narratives
with baseline analysis results
"""

from typing import Dict, Any, List, Optional
from uuid import UUID

from uepi_common.narrative.data_driven_narrative import DataDrivenNarrativeGenerator
from uepi_common.narrative.calculation_validator import CalculationValidator


class BaselineNarrativeGenerator:
    """
    Generate narratives for baseline analysis results
    Uses data-driven approach without LLM
    """
    
    def __init__(self):
        """Initialize narrative generator"""
        self.narrative_gen = DataDrivenNarrativeGenerator()
        self.validator = CalculationValidator()
    
    def generate_archetype_narratives(
        self,
        provider_archetypes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate narratives for all provider archetypes
        
        Args:
            provider_archetypes: List of provider archetype dicts
            
        Returns:
            List of narrative dicts, one per archetype
        """
        if not provider_archetypes:
            return []
        
        total_providers = sum(a.get("provider_count", 0) for a in provider_archetypes)
        
        narratives = []
        for archetype in provider_archetypes:
            narrative = self.narrative_gen.generate_provider_archetype_narrative(
                archetype=archetype,
                all_archetypes=provider_archetypes,
                total_providers=total_providers,
            )
            narratives.append(narrative)
        
        return narratives
    
    def generate_baseline_summary(
        self,
        benchmarks: List[Dict[str, Any]],
        provider_archetypes: List[Dict[str, Any]],
        patient_segments: List[Dict[str, Any]],
        time_series: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate overall baseline summary narrative
        
        Args:
            benchmarks: List of benchmark metrics
            provider_archetypes: List of provider archetypes
            patient_segments: List of patient segments
            time_series: List of time series data points
            
        Returns:
            Summary narrative dict
        """
        return self.narrative_gen.generate_baseline_summary_narrative(
            benchmarks=benchmarks,
            provider_archetypes=provider_archetypes,
            patient_segments=patient_segments,
            time_series=time_series,
        )
    
    def validate_and_enhance_archetype(
        self,
        archetype: Dict[str, Any],
        all_providers_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Validate archetype calculations and add validation results
        
        Args:
            archetype: Archetype dict to validate
            all_providers_data: Optional provider-level data for validation
            
        Returns:
            Enhanced archetype with validation results
        """
        enhanced = archetype.copy()
        
        # Validate individual metrics
        characteristics = archetype.get("characteristics", {})
        validation_results = {}
        
        # Validate avg_cost_per_claim if we have the components
        if "avg_cost_per_claim" in characteristics and "total_cost" in characteristics and "total_claims" in characteristics:
            total_cost = characteristics.get("total_cost", 0)
            total_claims = characteristics.get("total_claims", 0)
            is_valid, error = self.validator.validate_avg_cost_per_claim(
                total_cost, int(total_claims), characteristics.get("avg_cost_per_claim", 0)
            )
            validation_results["avg_cost_per_claim"] = {
                "valid": is_valid,
                "error": error,
            }
        
        # Validate claims_per_member if we have the components
        if "claims_per_member" in characteristics and "total_claims" in characteristics:
            # Note: We'd need unique_members count, which may not be in characteristics
            # This is a simplified validation
            pass
        
        # If we have provider-level data, do full validation
        if all_providers_data:
            full_validation = self.validator.validate_provider_archetype_metrics(
                archetype, all_providers_data
            )
            for metric, (is_valid, error) in full_validation.items():
                validation_results[metric] = {
                    "valid": is_valid,
                    "error": error,
                }
        
        enhanced["validation"] = validation_results
        enhanced["validation_summary"] = {
            "total_metrics": len(validation_results),
            "passed": sum(1 for v in validation_results.values() if v.get("valid", False)),
            "failed": sum(1 for v in validation_results.values() if not v.get("valid", True)),
        }
        
        return enhanced

