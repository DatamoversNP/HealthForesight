"""
Data-driven narrative generation for baseline analysis results
No LLM - purely rule-based based on actual data metrics
"""

from typing import Dict, Any, List, Optional
from datetime import date, datetime
import math


class DataDrivenNarrativeGenerator:
    """
    Generate narratives based on actual data metrics
    Uses rule-based templates with actual values
    """
    
    def __init__(self):
        """Initialize narrative generator"""
        pass
    
    def generate_provider_archetype_narrative(
        self,
        archetype: Dict[str, Any],
        all_archetypes: List[Dict[str, Any]],
        total_providers: int,
    ) -> Dict[str, Any]:
        """
        Generate narrative for a provider archetype based on actual metrics
        
        Args:
            archetype: Single archetype with characteristics
            all_archetypes: All archetypes for comparison
            total_providers: Total number of providers
            
        Returns:
            Narrative dict with interpretation, key_insights, and recommendations
        """
        characteristics = archetype.get("characteristics", {})
        provider_count = archetype.get("provider_count", 0)
        archetype_id = archetype.get("archetype_id", 0)
        
        # Extract metrics with validation
        # Note: "total_claims" in characteristics is actually the MEAN (average) of total_claims
        # across all providers in the archetype, not a sum. It's calculated as:
        # mean(total_claims for each provider in cluster)
        avg_claims_per_provider = characteristics.get("total_claims", 0.0)  # Renamed for clarity
        avg_total_cost_per_provider = characteristics.get("total_cost", 0.0)  # Also an average
        avg_cost_per_claim = characteristics.get("avg_cost_per_claim", 0.0)
        claims_per_member = characteristics.get("claims_per_member", 0.0)
        
        # Calculate relative metrics
        provider_share = (provider_count / total_providers * 100) if total_providers > 0 else 0.0
        
        # Compare to other archetypes
        avg_total_claims = sum(a.get("characteristics", {}).get("total_claims", 0) for a in all_archetypes) / len(all_archetypes) if all_archetypes else 0
        avg_total_cost = sum(a.get("characteristics", {}).get("total_cost", 0) for a in all_archetypes) / len(all_archetypes) if all_archetypes else 0
        avg_cost_per_claim_all = sum(a.get("characteristics", {}).get("avg_cost_per_claim", 0) for a in all_archetypes) / len(all_archetypes) if all_archetypes else 0
        
        # Generate interpretation
        interpretation = self._interpret_archetype(
            avg_claims_per_provider, avg_total_cost_per_provider, avg_cost_per_claim, claims_per_member,
            provider_share, avg_total_claims, avg_total_cost, avg_cost_per_claim_all
        )
        
        # Key insights
        key_insights = self._extract_key_insights(
            characteristics, provider_count, provider_share,
            avg_claims_per_provider, avg_total_cost_per_provider, avg_cost_per_claim, claims_per_member
        )
        
        # Recommendations
        recommendations = self._generate_recommendations(
            characteristics, provider_share, avg_claims_per_provider, avg_total_cost_per_provider, avg_cost_per_claim
        )
        
        return {
            "archetype_id": archetype_id,
            "archetype_name": archetype.get("archetype_name", f"Archetype {archetype_id + 1}"),
            "provider_count": provider_count,
            "provider_share_pct": round(provider_share, 2),
            "interpretation": interpretation,
            "key_insights": key_insights,
            "recommendations": recommendations,
            "calculation_notes": self._generate_calculation_notes(characteristics),
        }
    
    def _interpret_archetype(
        self,
        avg_claims_per_provider: float,
        avg_total_cost_per_provider: float,
        avg_cost_per_claim: float,
        claims_per_member: float,
        provider_share: float,
        avg_total_claims: float,
        avg_total_cost: float,
        avg_cost_per_claim_all: float,
    ) -> str:
        """Interpret archetype characteristics
        
        Note: avg_claims_per_provider is the mean of total_claims across all providers
        in the archetype. It represents the average number of claim lines per provider.
        """
        parts = []
        
        # Provider share interpretation
        if provider_share > 30:
            parts.append(f"This archetype represents {provider_share:.1f}% of all providers ({provider_share:.1f}% of provider population), indicating a dominant segment.")
        elif provider_share > 15:
            parts.append(f"This archetype represents {provider_share:.1f}% of all providers ({provider_share:.1f}% of provider population), representing a significant segment.")
        else:
            parts.append(f"This archetype represents {provider_share:.1f}% of all providers ({provider_share:.1f}% of provider population), a smaller but distinct segment.")
        
        # Volume interpretation - clarify this is average per provider
        if avg_total_claims > 0:
            claims_ratio = avg_claims_per_provider / avg_total_claims if avg_total_claims > 0 else 1.0
            if claims_ratio > 1.5:
                parts.append(f"Providers in this archetype average {avg_claims_per_provider:.2f} claim lines per provider, which is {claims_ratio:.1f}x higher than the overall average of {avg_total_claims:.2f} claim lines per provider, indicating high-volume providers.")
            elif claims_ratio < 0.5:
                parts.append(f"Providers in this archetype average {avg_claims_per_provider:.2f} claim lines per provider, which is {claims_ratio:.1f}x lower than the overall average of {avg_total_claims:.2f} claim lines per provider, indicating low-volume providers.")
            else:
                parts.append(f"Providers in this archetype average {avg_claims_per_provider:.2f} claim lines per provider, similar to the overall average of {avg_total_claims:.2f} claim lines per provider.")
        
        # Cost interpretation - clarify this is average per provider
        if avg_total_cost > 0:
            cost_ratio = avg_total_cost_per_provider / avg_total_cost if avg_total_cost > 0 else 1.0
            if cost_ratio > 1.5:
                parts.append(f"Average total cost per provider is ${avg_total_cost_per_provider:,.2f}, which is {cost_ratio:.1f}x higher than the overall average of ${avg_total_cost:,.2f} per provider.")
            elif cost_ratio < 0.5:
                parts.append(f"Average total cost per provider is ${avg_total_cost_per_provider:,.2f}, which is {cost_ratio:.1f}x lower than the overall average of ${avg_total_cost:,.2f} per provider.")
        
        # Cost per claim interpretation
        if avg_cost_per_claim_all > 0:
            cost_per_claim_ratio = avg_cost_per_claim / avg_cost_per_claim_all if avg_cost_per_claim_all > 0 else 1.0
            if cost_per_claim_ratio > 1.3:
                parts.append(f"Average cost per claim line is ${avg_cost_per_claim:.2f}, which is {cost_per_claim_ratio:.1f}x higher than the overall average of ${avg_cost_per_claim_all:.2f}, suggesting higher-cost services or intensity.")
            elif cost_per_claim_ratio < 0.7:
                parts.append(f"Average cost per claim line is ${avg_cost_per_claim:.2f}, which is {cost_per_claim_ratio:.1f}x lower than the overall average of ${avg_cost_per_claim_all:.2f}, suggesting lower-cost services or efficiency.")
        
        # Claims per member interpretation
        if claims_per_member > 0:
            if claims_per_member > 2.0:
                parts.append(f"Providers in this archetype average {claims_per_member:.2f} claims per member, indicating high utilization intensity.")
            elif claims_per_member < 0.5:
                parts.append(f"Providers in this archetype average {claims_per_member:.2f} claims per member, indicating low utilization intensity.")
        
        return " ".join(parts) if parts else "No significant patterns identified."
    
    def _extract_key_insights(
        self,
        characteristics: Dict[str, float],
        provider_count: int,
        provider_share: float,
        avg_claims_per_provider: float,
        avg_total_cost_per_provider: float,
        avg_cost_per_claim: float,
        claims_per_member: float,
    ) -> List[str]:
        """Extract key insights from metrics"""
        insights = []
        
        # Volume insight - clarify this is average per provider
        if avg_claims_per_provider > 1000:
            insights.append(f"High-volume segment: {avg_claims_per_provider:.2f} average claim lines per provider")
        elif avg_claims_per_provider < 50:
            insights.append(f"Low-volume segment: {avg_claims_per_provider:.2f} average claim lines per provider")
        else:
            insights.append(f"Moderate-volume segment: {avg_claims_per_provider:.2f} average claim lines per provider")
        
        # Cost insight - clarify this is average per provider
        if avg_total_cost_per_provider > 500000:
            insights.append(f"High-cost segment: ${avg_total_cost_per_provider:,.2f} average total cost per provider")
        elif avg_total_cost_per_provider < 10000:
            insights.append(f"Low-cost segment: ${avg_total_cost_per_provider:,.2f} average total cost per provider")
        
        # Efficiency insight
        if avg_cost_per_claim > 500:
            insights.append(f"Higher-cost services: ${avg_cost_per_claim:.2f} average cost per claim")
        elif avg_cost_per_claim < 100:
            insights.append(f"Lower-cost services: ${avg_cost_per_claim:.2f} average cost per claim")
        
        # Utilization pattern
        if claims_per_member > 1.5:
            insights.append(f"High utilization intensity: {claims_per_member:.2f} claims per member")
        elif claims_per_member < 0.3:
            insights.append(f"Low utilization intensity: {claims_per_member:.2f} claims per member")
        
        # Population share
        if provider_share > 25:
            insights.append(f"Represents {provider_share:.1f}% of provider population ({provider_count:,} providers)")
        
        return insights
    
    def _generate_recommendations(
        self,
        characteristics: Dict[str, float],
        provider_share: float,
        avg_claims_per_provider: float,
        avg_total_cost_per_provider: float,
        avg_cost_per_claim: float,
    ) -> List[str]:
        """Generate data-driven recommendations"""
        recommendations = []
        
        # High-cost, high-volume recommendations
        if avg_total_cost_per_provider > 500000 and avg_claims_per_provider > 500:
            recommendations.append("Consider utilization review programs for high-volume, high-cost providers")
            recommendations.append("Evaluate cost management opportunities through care coordination")
        
        # High cost per claim recommendations
        if avg_cost_per_claim > 500:
            recommendations.append("Review service mix and site-of-care patterns for cost optimization")
            recommendations.append("Assess appropriateness of high-cost services")
        
        # Large segment recommendations
        if provider_share > 25:
            recommendations.append("This segment represents a significant portion of providers - prioritize engagement strategies")
            recommendations.append("Consider segment-specific policy interventions given the population size")
        
        # Low utilization recommendations
        if avg_claims_per_provider < 50:
            recommendations.append("Low-volume segment may benefit from network optimization")
            recommendations.append("Assess whether low utilization indicates access barriers or efficiency")
        
        return recommendations
    
    def _generate_calculation_notes(self, characteristics: Dict[str, float]) -> Dict[str, str]:
        """Generate calculation notes for validation"""
        notes = {}
        
        if "total_claims" in characteristics:
            notes["total_claims"] = (
                "MEAN (average) of total_claims across all providers in this archetype. "
                "For each provider, total_claims = count of claim lines. "
                "Then: mean(total_claims for each provider in cluster). "
                "This represents average claim lines per provider, not a total sum."
            )
        
        if "total_cost" in characteristics:
            notes["total_cost"] = (
                "MEAN (average) of total_cost across all providers in this archetype. "
                "For each provider, total_cost = sum of allowed_amount (or paid_amount) for their claim lines. "
                "Then: mean(total_cost for each provider in cluster). "
                "This represents average total cost per provider, not a total sum."
            )
        
        if "avg_cost_per_claim" in characteristics:
            notes["avg_cost_per_claim"] = (
                "MEAN (average) of avg_cost_per_claim across all providers in this archetype. "
                "For each provider, avg_cost_per_claim = total_cost / total_claims. "
                "Then: mean(avg_cost_per_claim for each provider in cluster). "
                "This represents average cost per claim line."
            )
        
        if "claims_per_member" in characteristics:
            notes["claims_per_member"] = (
                "MEAN (average) of claims_per_member across all providers in this archetype. "
                "For each provider, claims_per_member = total_claims / unique_members. "
                "Then: mean(claims_per_member for each provider in cluster). "
                "This represents average claims per unique member."
            )
        
        return notes
    
    def generate_baseline_summary_narrative(
        self,
        benchmarks: List[Dict[str, Any]],
        provider_archetypes: List[Dict[str, Any]],
        patient_segments: List[Dict[str, Any]],
        time_series: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate overall baseline summary narrative"""
        # Extract key metrics
        util_rate = next((b.get("metric_value") for b in benchmarks if b.get("metric_name") == "util_rate_total_per_1000_mm"), None)
        cost_pmpm = next((b.get("metric_value") for b in benchmarks if b.get("metric_name") == "allowed_pmpm_total"), None)
        
        total_providers = sum(a.get("provider_count", 0) for a in provider_archetypes)
        total_members = sum(s.get("member_count", 0) for s in patient_segments)
        
        summary = {
            "overview": self._generate_overview(util_rate, cost_pmpm, total_providers, total_members),
            "provider_landscape": self._summarize_provider_landscape(provider_archetypes),
            "patient_landscape": self._summarize_patient_landscape(patient_segments),
            "utilization_patterns": self._summarize_utilization(benchmarks, time_series),
            "calculation_methodology": self._document_methodology(),
        }
        
        return summary
    
    def _generate_overview(
        self,
        util_rate: Optional[float],
        cost_pmpm: Optional[float],
        total_providers: int,
        total_members: int,
    ) -> str:
        """Generate overview narrative"""
        parts = []
        
        if util_rate is not None:
            parts.append(f"Baseline utilization rate: {util_rate:.2f} claims per 1,000 member-months.")
        
        if cost_pmpm is not None:
            parts.append(f"Baseline cost: ${cost_pmpm:.2f} per member per month (PMPM).")
        
        if total_providers > 0:
            parts.append(f"Analysis includes {total_providers:,} providers across {len([a for a in []])} distinct archetypes.")
        
        if total_members > 0:
            parts.append(f"Patient population: {total_members:,} members across {len([s for s in []])} risk segments.")
        
        return " ".join(parts) if parts else "Baseline analysis completed."
    
    def _summarize_provider_landscape(self, archetypes: List[Dict[str, Any]]) -> str:
        """Summarize provider landscape"""
        if not archetypes:
            return "No provider archetypes identified."
        
        total = sum(a.get("provider_count", 0) for a in archetypes)
        if total == 0:
            return "No provider data available."
        
        parts = [f"Provider landscape includes {len(archetypes)} distinct archetypes:"]
        
        for archetype in archetypes[:5]:  # Top 5
            count = archetype.get("provider_count", 0)
            share = (count / total * 100) if total > 0 else 0
            name = archetype.get("archetype_name", "Unknown")
            parts.append(f"- {name}: {count:,} providers ({share:.1f}%)")
        
        return " ".join(parts)
    
    def _summarize_patient_landscape(self, segments: List[Dict[str, Any]]) -> str:
        """Summarize patient landscape"""
        if not segments:
            return "No patient segments identified."
        
        total = sum(s.get("member_count", 0) for s in segments)
        if total == 0:
            return "No patient data available."
        
        parts = [f"Patient population segmented into {len(segments)} risk-based groups:"]
        
        for segment in segments:
            count = segment.get("member_count", 0)
            share = (count / total * 100) if total > 0 else 0
            name = segment.get("segment_name", "Unknown")
            parts.append(f"- {name}: {count:,} members ({share:.1f}%)")
        
        return " ".join(parts)
    
    def _summarize_utilization(
        self,
        benchmarks: List[Dict[str, Any]],
        time_series: List[Dict[str, Any]],
    ) -> str:
        """Summarize utilization patterns"""
        parts = []
        
        if benchmarks:
            parts.append(f"Calculated {len(benchmarks)} baseline benchmarks across multiple dimensions.")
        
        if time_series:
            parts.append(f"Time series analysis includes {len(time_series)} data points.")
            # Add trend if available
            if len(time_series) > 1:
                first_val = time_series[0].get("value", 0)
                last_val = time_series[-1].get("value", 0)
                if first_val > 0:
                    trend_pct = ((last_val - first_val) / first_val * 100) if first_val > 0 else 0
                    if abs(trend_pct) > 5:
                        direction = "increased" if trend_pct > 0 else "decreased"
                        parts.append(f"Utilization {direction} by {abs(trend_pct):.1f}% over the analysis period.")
        
        return " ".join(parts) if parts else "Utilization patterns analyzed."
    
    def _document_methodology(self) -> Dict[str, str]:
        """Document calculation methodology"""
        return {
            "utilization_rate": "Claims per 1,000 member-months = (Total claim lines / Member-months) × 1,000",
            "cost_pmpm": "Cost per member per month = Total allowed amount / Member-months",
            "provider_archetypes": "K-means clustering on: total_claims, total_cost, avg_cost_per_claim, claims_per_member. StandardScaler normalization applied.",
            "patient_segments": "Risk-based stratification using total_cost thresholds: HIGH (>$10,000), MEDIUM ($2,000-$10,000), LOW (<$2,000)",
            "validation": "All calculations use standard healthcare analytics formulas. Member-months calculated from enrollment data when available, otherwise estimated from unique members × 12.",
        }

