"""Observation enhancement logic - Create and enhance observed impacts"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
from uuid import UUID as UUIDType

from uepi_api.storage_observations import create_observation, update_observation
from uepi_api.storage_baselines import get_latest_baseline, get_baseline
from uepi_api.storage_policies import get_policy
from uepi_api.storage_policy_versions import get_latest_version
from uepi_api.storage_data_periods import get_data_period

try:
    from uepi_common.metrics import (
        get_unified_measure_keys,
        get_measure_display,
        normalize_to_canonical_key,
    )
except ImportError:
    get_unified_measure_keys = None
    get_measure_display = None
    normalize_to_canonical_key = None


def _build_observed_measures(observation_metrics: Dict[str, Any]) -> Dict[str, float]:
    """Build flat observed_measures keyed by canonical measure keys (unified measure framework)."""
    out = {}
    if not observation_metrics:
        return out
    # Map from observation_metrics keys to canonical keys and extract value
    obs = observation_metrics
    mapping = [
        ("utilization_per_1k", "util_rate_target_per_1000_mm"),
        ("util_rate_per_1k", "util_rate_total_per_1000_mm"),
        ("cost_pmpm", "allowed_pmpm_target"),
        ("cost_per_member", "allowed_pmpm_target"),
        ("member_months", "member_months"),
        ("unique_members", "unique_members"),
    ]
    for src_key, canon_key in mapping:
        val = obs.get(src_key)
        if val is not None and (isinstance(val, (int, float)) or (isinstance(val, str) and val.replace(".", "").replace("-", "").isdigit())):
            try:
                out[canon_key] = float(val)
            except (TypeError, ValueError):
                pass
    # If we have util but not util_rate_target, use utilization_per_1k for util_rate_target
    if "util_rate_target_per_1000_mm" not in out and "utilization_per_1k" in obs:
        try:
            out["util_rate_target_per_1000_mm"] = float(obs.get("utilization_per_1k") or 0)
        except (TypeError, ValueError):
            pass
    if "allowed_pmpm_target" not in out and ("cost_pmpm" in obs or "cost_per_member" in obs):
        try:
            out["allowed_pmpm_target"] = float(obs.get("cost_pmpm") or obs.get("cost_per_member") or 0)
        except (TypeError, ValueError):
            pass
    return out


def _build_baseline_measures(baseline_metrics: Dict[str, Any], baseline: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """Build flat baseline_measures keyed by canonical measure keys."""
    out = {}
    if not isinstance(baseline_metrics, dict):
        return out
    bm = baseline_metrics
    mapping = [
        ("util_rate_target_per_1000_mm", "util_rate_target_per_1000_mm"),
        ("util_rate_total_per_1000_mm", "util_rate_total_per_1000_mm"),
        ("utilization_per_1k", "util_rate_target_per_1000_mm"),
        ("allowed_pmpm_target", "allowed_pmpm_target"),
        ("paid_pmpm_target", "allowed_pmpm_target"),
        ("allowed_pmpm_total", "allowed_pmpm_total"),
        ("paid_pmpm_total", "paid_pmpm_total"),
        ("cost_pmpm", "allowed_pmpm_target"),
        ("member_months", "member_months"),
        ("policy_eligible_member_months", "policy_eligible_member_months"),
        ("unique_members", "unique_members"),
    ]
    for bm_key, canon_key in mapping:
        val = bm.get(bm_key)
        if val is not None and canon_key not in out:
            try:
                out[canon_key] = float(val)
            except (TypeError, ValueError):
                pass
    return out


def _build_comparison_by_measure_baseline(
    baseline_measures: Dict[str, float],
    observed_measures: Dict[str, float],
    baseline_utilization: float,
    observed_utilization: float,
    baseline_cost_pmpm: float,
    observed_cost_pmpm: float,
    utilization_change: float,
    utilization_change_pct: float,
    cost_change_pmpm: float,
    cost_change_pct: float,
) -> Dict[str, Dict[str, Any]]:
    """Build comparison_by_measure for vs_baseline (canonical key -> baseline, observed, change, change_pct)."""
    by_measure = {}
    # Utilization
    by_measure["util_rate_target_per_1000_mm"] = {
        "baseline": baseline_utilization,
        "observed": observed_utilization,
        "change": utilization_change,
        "change_pct": utilization_change_pct,
    }
    # Cost
    by_measure["allowed_pmpm_target"] = {
        "baseline": baseline_cost_pmpm,
        "observed": observed_cost_pmpm,
        "change": cost_change_pmpm,
        "change_pct": cost_change_pct,
    }
    # Optional: add others from baseline_measures/observed_measures if present
    for key in ("member_months", "unique_members", "util_rate_total_per_1000_mm", "allowed_pmpm_total", "paid_pmpm_total"):
        base_val = baseline_measures.get(key)
        obs_val = observed_measures.get(key)
        if base_val is not None or obs_val is not None:
            base_val = float(base_val) if base_val is not None else None
            obs_val = float(obs_val) if obs_val is not None else None
            change = (obs_val - base_val) if (obs_val is not None and base_val is not None) else None
            change_pct = (change / base_val * 100) if (base_val and change is not None) else None
            by_measure[key] = {
                "baseline": base_val,
                "observed": obs_val,
                "change": change,
                "change_pct": change_pct,
            }
    return by_measure


def extract_metrics_from_analysis_result(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metrics from impact analysis result
    
    Args:
        analysis_result: Result from impact analysis (Stage 4)
        
    Returns:
        Dictionary of metrics with all required fields
    """
    # Extract metrics from analysis result
    # Structure depends on impact analysis output
    metrics = {}
    
    # Extract from treatment_post metrics if available (for observed values)
    # This is the PRIMARY source for observed metrics
    treatment_post = None
    if "metrics" in analysis_result and "treatment_post" in analysis_result["metrics"]:
        treatment_post = analysis_result["metrics"]["treatment_post"]
    elif "post_period" in analysis_result:
        # Alternative structure from database computation
        treatment_post = analysis_result["post_period"]
    
    if treatment_post:
        # Extract utilization
        metrics["utilization_per_1k"] = float(
            treatment_post.get("utilization_per_1k", 0.0) or 
            treatment_post.get("util_rate_per_1k", 0.0) or
            0.0
        )
        
        # Extract cost - try multiple field names
        cost_pmpm = float(
            treatment_post.get("cost_pmpm", 0.0) or
            treatment_post.get("paid_pmpm", 0.0) or 
            treatment_post.get("allowed_pmpm", 0.0) or
            treatment_post.get("cost_per_member", 0.0) or
            0.0
        )
        metrics["cost_per_member"] = cost_pmpm
        metrics["cost_pmpm"] = cost_pmpm  # Also store as cost_pmpm for frontend compatibility
        
        # Extract other metrics
        metrics["total_claims"] = int(treatment_post.get("total_claims", 0) or 0)
        metrics["total_paid"] = float(treatment_post.get("total_paid", 0.0) or 0.0)
        metrics["total_allowed"] = float(treatment_post.get("total_allowed", 0.0) or 0.0)
        metrics["member_months"] = float(treatment_post.get("member_months", 0.0) or 0.0)
        metrics["unique_members"] = int(treatment_post.get("unique_members", 0) or 0)
    
    # When daily job passes reference_baseline (unvaried metrics), use it so vs_baseline cost_change_pct = (varied - ref)/ref
    if "metrics" in analysis_result and analysis_result["metrics"].get("reference_baseline"):
        metrics["_reference_baseline"] = analysis_result["metrics"]["reference_baseline"]
    
    # Extract effect size from impact_estimate, did_result, or impact_summary
    if "impact_estimate" in analysis_result:
        impact_estimate = analysis_result["impact_estimate"]
        metrics["observed_effect_size"] = float(impact_estimate.get("effect_size", 0.0) or 0.0)
        metrics["observed_percent_change"] = float(impact_estimate.get("percent_change", 0.0) or 0.0)
        ci = impact_estimate.get("confidence_interval", [0.0, 0.0])
        if isinstance(ci, list) and len(ci) >= 2:
            metrics["confidence_interval"] = [float(ci[0] or 0.0), float(ci[1] or 0.0)]
        metrics["p_value"] = float(impact_estimate.get("p_value", 1.0) or 1.0)
    elif "did_result" in analysis_result:
        did_result = analysis_result["did_result"]
        metrics["observed_effect_size"] = float(did_result.get("effect_size", 0.0) or 0.0)
        metrics["observed_percent_change"] = float(did_result.get("percent_change", 0.0) or 0.0)
        ci = did_result.get("confidence_interval", [0.0, 0.0])
        if isinstance(ci, list) and len(ci) >= 2:
            metrics["confidence_interval"] = [float(ci[0] or 0.0), float(ci[1] or 0.0)]
        metrics["p_value"] = float(did_result.get("p_value", 1.0) or 1.0)
    elif "impact_summary" in analysis_result:
        # Database-computed structure
        impact_summary = analysis_result["impact_summary"]
        metrics["observed_effect_size"] = float(impact_summary.get("observed_effect_size", 0.0) or 0.0)
        metrics["observed_percent_change"] = float(impact_summary.get("observed_percent_change", 0.0) or 0.0)
        ci_lower = float(impact_summary.get("confidence_interval_lower", 0.0) or 0.0)
        ci_upper = float(impact_summary.get("confidence_interval_upper", 0.0) or 0.0)
        metrics["confidence_interval"] = [ci_lower, ci_upper]
        metrics["p_value"] = float(impact_summary.get("p_value", 1.0) or 1.0)
    
    # Extract confidence score if available
    if "confidence_score" in analysis_result:
        metrics["confidence_score"] = float(analysis_result.get("confidence_score", 0.0) or 0.0)
    elif "trust_panel" in analysis_result:
        trust_panel = analysis_result.get("trust_panel", {})
        if "confidence_score" in trust_panel:
            metrics["confidence_score"] = float(trust_panel.get("confidence_score", 0.0) or 0.0)
    
    # Ensure all required fields are present (no None values)
    required_fields = {
        "utilization_per_1k": 0.0,
        "cost_per_member": 0.0,
        "cost_pmpm": 0.0,
        "total_claims": 0,
        "total_paid": 0.0,
        "total_allowed": 0.0,
        "observed_effect_size": 0.0,
        "observed_percent_change": 0.0,
    }
    
    for field, default_value in required_fields.items():
        if field not in metrics or metrics[field] is None:
            metrics[field] = default_value
        else:
            # Ensure it's the right type
            if field in ["total_claims"]:
                metrics[field] = int(metrics[field] or 0)
            else:
                metrics[field] = float(metrics[field] or 0.0)
    
    print(f"DEBUG: Extracted metrics - utilization_per_1k: {metrics.get('utilization_per_1k')}, cost_pmpm: {metrics.get('cost_pmpm')}, effect_size: {metrics.get('observed_effect_size')}")
    
    return metrics


def extract_comparisons_from_analysis_result(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract comparisons from impact analysis result
    
    Args:
        analysis_result: Result from impact analysis
        
    Returns:
        Dictionary with vs_baseline and vs_predicted comparisons
    """
    comparisons = {
        "vs_baseline": {},
        "vs_predicted": {},
    }
    
    # Extract comparisons if they exist in analysis result
    if "comparisons" in analysis_result:
        comparisons = analysis_result["comparisons"].copy()
    elif "comparison" in analysis_result:
        # Handle singular form
        comparison = analysis_result["comparison"]
        if "vs_baseline" in comparison:
            comparisons["vs_baseline"] = comparison["vs_baseline"]
        if "vs_predicted" in comparison:
            comparisons["vs_predicted"] = comparison["vs_predicted"]
    
    return comparisons


def extract_behavioral_explanation_from_analysis_result(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and enhance behavioral explanation from impact analysis result
    
    Includes all behavioral attribution metrics (M17-M19) plus detailed analysis:
    - M17: Provider Archetype Distribution (provider_archetype_share_{type})
    - M18: Provider Ordering Intensity (provider_ordering_intensity_target_per_1000_mm)
    - M19: Patient Segment Response Share (patient_response_share_{segment}_{response})
    - Detailed provider response analysis
    - Detailed patient response analysis
    - Cost impact analysis
    - Utilization trend analysis
    - Actionable insights
    
    Args:
        analysis_result: Result from impact analysis
        
    Returns:
        Dictionary with comprehensive behavioral explanation
    """
    behavioral_explanation = {}
    
    # Extract behavioral explanation if it exists
    if "behavioral_explanation" in analysis_result:
        behavioral_explanation = analysis_result["behavioral_explanation"].copy()
    elif "behavioral_analysis" in analysis_result:
        behavioral_explanation = analysis_result["behavioral_analysis"].copy()
    
    # Extract substitution patterns
    substitution_data = analysis_result.get("substitution") or analysis_result.get("substitution_patterns") or {}
    if substitution_data:
        if isinstance(substitution_data, dict):
            behavioral_explanation["substitution_patterns"] = substitution_data.get("substitutions", []) or substitution_data.get("patterns", [])
        elif isinstance(substitution_data, list):
            behavioral_explanation["substitution_patterns"] = substitution_data
    
    # Extract key metrics for comprehensive analysis
    impact_estimate = analysis_result.get("impact_estimate") or analysis_result.get("did_result") or {}
    metrics = analysis_result.get("metrics", {})
    treatment_pre = metrics.get("treatment_pre", {})
    treatment_post = metrics.get("treatment_post", {})
    
    # ============================================================================
    # M17: Provider Archetype Distribution (provider_archetype_share_{type})
    # ============================================================================
    provider_segmentation = analysis_result.get("provider_segmentation") or analysis_result.get("provider_archetypes") or {}
    if provider_segmentation:
        behavioral_explanation["provider_segmentation"] = provider_segmentation
        
        # Compute provider archetype shares (M17)
        archetypes = provider_segmentation.get("archetypes", [])
        provider_assignments = provider_segmentation.get("provider_assignments", [])
        total_providers = provider_segmentation.get("total_providers") or len(provider_assignments)
        
        if archetypes and total_providers > 0:
            provider_archetype_shares = {}
            for archetype in archetypes:
                archetype_label = archetype.get("archetype_label", "").upper()
                provider_count = archetype.get("provider_count", 0)
                
                # Map to standard types: compliant, adaptive, resistant, circumvention-prone
                type_mapping = {
                    "COMPLIERS": "compliant",
                    "COMPLIANT": "compliant",
                    "NEUTRAL": "adaptive",
                    "ADAPTIVE": "adaptive",
                    "SUBSTITUTORS": "resistant",
                    "RESISTANT": "resistant",
                    "CIRCUMVENTERS": "circumvention-prone",
                    "CIRCUMVENTION-PRONE": "circumvention-prone",
                    "CIRCUMVENTION": "circumvention-prone",
                }
                
                metric_type = type_mapping.get(archetype_label, archetype_label.lower().replace(" ", "_"))
                share_pct = (provider_count / total_providers * 100) if total_providers > 0 else 0.0
                
                provider_archetype_shares[f"provider_archetype_share_{metric_type}"] = float(share_pct)
            
            if provider_archetype_shares:
                behavioral_explanation["provider_archetype_shares"] = provider_archetype_shares
                behavioral_explanation["provider_response_source"] = "observed"

    # Fallback: If no provider segmentation, infer archetype distribution from impact estimate
    model_inferred_sections = []
    if "provider_archetype_shares" not in behavioral_explanation:
        percent_change = impact_estimate.get("percent_change", 0.0)

        # Infer archetype distribution from policy impact (model-inferred, not from provider data)
        provider_archetype_shares = {}

        if percent_change < -30.0:
            # Strong reduction - majority compliant
            provider_archetype_shares["provider_archetype_share_compliant"] = 60.0
            provider_archetype_shares["provider_archetype_share_adaptive"] = 25.0
            provider_archetype_shares["provider_archetype_share_resistant"] = 10.0
            provider_archetype_shares["provider_archetype_share_circumvention-prone"] = 5.0
        elif percent_change < -10.0:
            # Moderate reduction - mix of compliant and adaptive
            provider_archetype_shares["provider_archetype_share_compliant"] = 40.0
            provider_archetype_shares["provider_archetype_share_adaptive"] = 35.0
            provider_archetype_shares["provider_archetype_share_resistant"] = 20.0
            provider_archetype_shares["provider_archetype_share_circumvention-prone"] = 5.0
        else:
            # Minimal reduction or increase - more resistant/circumvention-prone
            provider_archetype_shares["provider_archetype_share_compliant"] = 20.0
            provider_archetype_shares["provider_archetype_share_adaptive"] = 30.0
            provider_archetype_shares["provider_archetype_share_resistant"] = 35.0
            provider_archetype_shares["provider_archetype_share_circumvention-prone"] = 15.0

        behavioral_explanation["provider_archetype_shares"] = provider_archetype_shares
        behavioral_explanation["provider_response_source"] = "model_inferred"
        model_inferred_sections.append("provider_response")
    
    # ============================================================================
    # M18: Provider Ordering Intensity (provider_ordering_intensity_target_per_1000_mm)
    # ============================================================================
    if treatment_post and provider_segmentation:
        provider_assignments = provider_segmentation.get("provider_assignments", [])
        if provider_assignments:
            total_target_claims = treatment_post.get("total_claims", 0)
            member_months_approx = treatment_post.get("member_months") or (treatment_post.get("total_claims", 0) * 12)
            
            if member_months_approx > 0:
                avg_ordering_intensity = (total_target_claims / member_months_approx) * 1000
                behavioral_explanation["provider_ordering_intensity_target_per_1000_mm"] = float(avg_ordering_intensity)
    
    # Fallback: compute from treatment_post metrics if provider_segmentation not available
    if "provider_ordering_intensity_target_per_1000_mm" not in behavioral_explanation and treatment_post:
        total_target_claims = treatment_post.get("total_claims", 0)
        member_count = treatment_post.get("member_count") or metrics.get("member_count") or 1000
        post_months = analysis_result.get("methodology", {}).get("post_months", 6)
        member_months_approx = member_count * post_months
        
        if member_months_approx > 0:
            avg_ordering_intensity = (total_target_claims / member_months_approx) * 1000
            behavioral_explanation["provider_ordering_intensity_target_per_1000_mm"] = float(avg_ordering_intensity)
    
    # ============================================================================
    # M19: Patient Segment Response Share (patient_response_share_{segment}_{response})
    # ============================================================================
    patient_responses = {}
    
    # Infer from substitution patterns (substitute response)
    substitution_patterns = behavioral_explanation.get("substitution_patterns")
    if substitution_patterns and len(substitution_patterns) > 0:
        substitution_count = len(substitution_patterns)
        patient_responses["patient_response_share_overall_substitute"] = min(50.0, substitution_count * 5.0)
    
    # Infer from deferral/timing shifts (defer response)
    percent_change = impact_estimate.get("percent_change", 0.0)
    
    if percent_change < -20.0:
        defer_pct = min(40.0, abs(percent_change) * 0.5)
        patient_responses["patient_response_share_overall_defer"] = float(defer_pct)
    
    # Infer from ER/urgent care shifts (ER_fallback response)
    mix_shifts = analysis_result.get("mix_analysis") or analysis_result.get("mix_shifts") or {}
    if mix_shifts:
        er_shift = mix_shifts.get("er_share_change") or mix_shifts.get("urgent_care_increase")
        if er_shift and er_shift > 0:
            patient_responses["patient_response_share_overall_ER_fallback"] = float(er_shift * 10)
    elif percent_change < -10.0:
        patient_responses["patient_response_share_overall_ER_fallback"] = min(15.0, abs(percent_change) * 0.3)
    
    # Comply response (complement - those who followed policy)
    total_other_responses = sum(patient_responses.values())
    comply_share = max(0.0, 100.0 - total_other_responses)
    patient_responses["patient_response_share_overall_comply"] = comply_share
    
    behavioral_explanation["patient_response_shares"] = patient_responses
    # Patient response shares are model-inferred from impact/substitution (no patient-level segmentation)
    behavioral_explanation["patient_response_source"] = "model_inferred"
    model_inferred_sections.append("patient_response")

    # Top-level interpretation note for transparency (industry standard: disclose model-inferred content)
    if model_inferred_sections:
        behavioral_explanation["interpretation_note"] = (
            "Provider and/or patient response distributions are model-inferred from impact estimates. "
            "For evidence-based attribution, use provider segmentation and patient-level analysis."
        )
        behavioral_explanation["model_inferred_sections"] = model_inferred_sections

    # Extract mix shifts
    if mix_shifts:
        behavioral_explanation["mix_shifts"] = mix_shifts
    
    # Extract pathway changes
    pathway_analysis = analysis_result.get("pathway_analysis") or analysis_result.get("pathway_changes") or {}
    if pathway_analysis:
        behavioral_explanation["pathway_changes"] = pathway_analysis
    
    # ============================================================================
    # ENHANCED BEHAVIORAL EXPLANATION - Detailed Analysis
    # ============================================================================
    
    # Build comprehensive, detailed summary with multiple aspects
    if not behavioral_explanation.get("summary") or behavioral_explanation.get("summary") == "":
        effect_size = impact_estimate.get("effect_size", 0.0)
        p_value = impact_estimate.get("p_value", 1.0)
        confidence_interval = impact_estimate.get("confidence_interval", [0.0, 0.0])
        
        # Build a comprehensive, multi-paragraph summary
        summary_parts = []
        detailed_analysis = []
        
        # Primary impact statement
        if percent_change != 0:
            direction = "reduction" if percent_change < 0 else "increase"
            magnitude = abs(percent_change)
            impact_strength = "substantial" if magnitude > 20 else "moderate" if magnitude > 10 else "modest"
            summary_parts.append(f"Policy implementation resulted in a {impact_strength} {magnitude:.1f}% {direction} in target service utilization")
        
        # Statistical significance
        if effect_size != 0:
            effect_magnitude = abs(effect_size)
            effect_desc = "strong" if effect_magnitude > 0.5 else "moderate" if effect_magnitude > 0.2 else "weak"
            summary_parts.append(f"with a {effect_desc} effect size of {effect_size:.3f}")
        
        # Statistical significance details
        if p_value < 0.05:
            summary_parts.append("(statistically significant, p < 0.05)")
            detailed_analysis.append("The observed changes are statistically significant, indicating a high degree of confidence that the policy is driving the observed outcomes rather than random variation.")
        elif p_value < 0.10:
            summary_parts.append("(marginally significant, p < 0.10)")
            detailed_analysis.append("The observed changes show marginal statistical significance, suggesting the policy impact is likely real but requires continued monitoring.")
        else:
            detailed_analysis.append("While the observed changes may be meaningful, they do not meet traditional statistical significance thresholds. Additional data collection may be needed to confirm policy effectiveness.")
        
        # Confidence interval
        if len(confidence_interval) == 2 and confidence_interval[0] != confidence_interval[1]:
            ci_lower = confidence_interval[0]
            ci_upper = confidence_interval[1]
            summary_parts.append(f"95% CI: [{ci_lower:.3f}, {ci_upper:.3f}]")
            detailed_analysis.append(f"The 95% confidence interval [{ci_lower:.3f}, {ci_upper:.3f}] provides a range of plausible effect sizes, indicating the true impact likely falls within this range.")
        
        # Combine summary
        main_summary = " ".join(summary_parts) if summary_parts else "Policy implementation shows expected reduction in utilization"
        
        # Add detailed context
        if treatment_pre and treatment_post:
            pre_util = treatment_pre.get("utilization_per_1k", 0.0)
            post_util = treatment_post.get("utilization_per_1k", 0.0)
            if pre_util > 0:
                detailed_analysis.append(f"Utilization decreased from {pre_util:.1f} to {post_util:.1f} services per 1,000 members, representing a meaningful shift in care patterns.")
        
        # Add provider behavior context
        if "provider_archetype_shares" in behavioral_explanation:
            compliant_pct = behavioral_explanation["provider_archetype_shares"].get("provider_archetype_share_compliant", 0.0)
            if compliant_pct > 0:
                detailed_analysis.append(f"Provider behavior analysis indicates {compliant_pct:.1f}% of providers are demonstrating compliant behavior with the policy.")
        
        # Add patient response context
        if "patient_response_shares" in behavioral_explanation:
            comply_pct = behavioral_explanation["patient_response_shares"].get("patient_response_share_overall_comply", 0.0)
            if comply_pct > 0:
                detailed_analysis.append(f"Patient response analysis shows {comply_pct:.1f}% of patients are following the policy as intended.")
        
        behavioral_explanation["summary"] = main_summary
        if detailed_analysis:
            behavioral_explanation["detailed_analysis"] = detailed_analysis
    
    # Add detailed provider response analysis
    if "provider_archetype_shares" in behavioral_explanation:
        archetype_shares = behavioral_explanation["provider_archetype_shares"]
        compliant_pct = archetype_shares.get("provider_archetype_share_compliant", 0.0)
        resistant_pct = archetype_shares.get("provider_archetype_share_resistant", 0.0)
        circumvention_pct = archetype_shares.get("provider_archetype_share_circumvention-prone", 0.0)
        adaptive_pct = archetype_shares.get("provider_archetype_share_adaptive", 0.0)
        
        provider_response = {
            "compliant_providers_pct": compliant_pct,
            "adaptive_providers_pct": adaptive_pct,
            "resistant_providers_pct": resistant_pct,
            "circumvention_prone_pct": circumvention_pct,
            "total_providers": archetype_shares.get("total_providers", 0),
            "analysis": [],
            "recommendations": []
        }
        
        if compliant_pct > 50:
            provider_response["analysis"].append(f"Majority of providers ({compliant_pct:.1f}%) are compliant with the policy, indicating strong policy acceptance.")
        elif compliant_pct > 30:
            provider_response["analysis"].append(f"Moderate provider compliance ({compliant_pct:.1f}%) observed, with room for improvement.")
        else:
            provider_response["analysis"].append(f"Low provider compliance ({compliant_pct:.1f}%) suggests policy may need refinement or additional provider engagement.")
        
        if adaptive_pct > 30:
            provider_response["analysis"].append(f"Significant adaptive behavior ({adaptive_pct:.1f}%) - providers are adjusting workflows to accommodate policy.")
        
        if resistant_pct > 30:
            provider_response["analysis"].append(f"High provider resistance ({resistant_pct:.1f}%) detected - consider provider education and support programs.")
            provider_response["recommendations"].append("Implement provider training and support to address resistance")
        
        if circumvention_pct > 15:
            provider_response["analysis"].append(f"Notable circumvention risk ({circumvention_pct:.1f}%) - monitor for policy workarounds.")
            provider_response["recommendations"].append("Enhance policy enforcement mechanisms to reduce circumvention")
        
        behavioral_explanation["provider_response"] = provider_response
    
    # Add detailed patient response analysis
    if "patient_response_shares" in behavioral_explanation:
        patient_responses_data = behavioral_explanation["patient_response_shares"]
        comply_pct = patient_responses_data.get("patient_response_share_overall_comply", 0.0)
        substitute_pct = patient_responses_data.get("patient_response_share_overall_substitute", 0.0)
        defer_pct = patient_responses_data.get("patient_response_share_overall_defer", 0.0)
        er_fallback_pct = patient_responses_data.get("patient_response_share_overall_ER_fallback", 0.0)
        
        patient_response_analysis = {
            "comply_pct": comply_pct,
            "substitute_pct": substitute_pct,
            "defer_pct": defer_pct,
            "er_fallback_pct": er_fallback_pct,
            "analysis": [],
            "recommendations": []
        }
        
        if comply_pct > 60:
            patient_response_analysis["analysis"].append(f"Most patients ({comply_pct:.1f}%) are following the policy, indicating good patient understanding and acceptance.")
        elif comply_pct > 40:
            patient_response_analysis["analysis"].append(f"Moderate patient compliance ({comply_pct:.1f}%) - consider patient education initiatives.")
        else:
            patient_response_analysis["analysis"].append(f"Low patient compliance ({comply_pct:.1f}%) suggests policy may be too restrictive or unclear.")
            patient_response_analysis["recommendations"].append("Review policy communication and patient education materials")
        
        if substitute_pct > 20:
            patient_response_analysis["analysis"].append(f"Significant substitution behavior ({substitute_pct:.1f}%) - patients are finding alternative services.")
            patient_response_analysis["recommendations"].append("Monitor substitution patterns to ensure appropriate care delivery")
        
        if defer_pct > 20:
            patient_response_analysis["analysis"].append(f"Notable deferral behavior ({defer_pct:.1f}%) - patients are delaying care.")
            patient_response_analysis["recommendations"].append("Assess impact of care deferral on patient outcomes")
        
        if er_fallback_pct > 10:
            patient_response_analysis["analysis"].append(f"ER fallback observed ({er_fallback_pct:.1f}%) - patients using emergency services as alternative.")
            patient_response_analysis["recommendations"].append("Monitor emergency department utilization and consider urgent care alternatives")
        
        behavioral_explanation["patient_response"] = patient_response_analysis
    
    # Add cost impact analysis
    if treatment_pre and treatment_post:
        pre_cost = treatment_pre.get("paid_pmpm") or treatment_pre.get("allowed_pmpm") or treatment_pre.get("cost_pmpm") or 0.0
        post_cost = treatment_post.get("paid_pmpm") or treatment_post.get("allowed_pmpm") or treatment_post.get("cost_pmpm") or 0.0
        
        if pre_cost > 0:
            cost_change_pct = ((post_cost - pre_cost) / pre_cost) * 100
            cost_change_abs = post_cost - pre_cost
            cost_impact = {
                "pre_cost_pmpm": pre_cost,
                "post_cost_pmpm": post_cost,
                "cost_change_pmpm": cost_change_abs,
                "cost_change_pct": cost_change_pct,
                "analysis": [],
                "financial_impact": {}
            }
            
            if cost_change_pct < -10:
                cost_impact["analysis"].append(f"Significant cost reduction ({abs(cost_change_pct):.1f}%) - policy is achieving cost savings goals.")
                cost_impact["financial_impact"]["savings_category"] = "HIGH"
            elif cost_change_pct < -5:
                cost_impact["analysis"].append(f"Moderate cost reduction ({abs(cost_change_pct):.1f}%) - policy shows positive cost impact.")
                cost_impact["financial_impact"]["savings_category"] = "MEDIUM"
            elif cost_change_pct > 5:
                cost_impact["analysis"].append(f"Cost increase observed ({cost_change_pct:.1f}%) - review policy cost-effectiveness.")
                cost_impact["financial_impact"]["savings_category"] = "NEGATIVE"
            else:
                cost_impact["analysis"].append("Minimal cost impact - policy maintains cost neutrality.")
                cost_impact["financial_impact"]["savings_category"] = "LOW"
            
            # Estimate annual savings for 10k members
            annual_savings_10k = cost_change_abs * 10000 * 12
            cost_impact["financial_impact"]["annual_savings_per_10k_members"] = annual_savings_10k
            
            behavioral_explanation["cost_impact"] = cost_impact
    
    # Add utilization trend analysis
    if treatment_pre and treatment_post:
        pre_util = treatment_pre.get("utilization_per_1k") or 0.0
        post_util = treatment_post.get("utilization_per_1k") or 0.0
        
        if pre_util > 0:
            util_change_pct = ((post_util - pre_util) / pre_util) * 100
            util_change_abs = post_util - pre_util
            utilization_trend = {
                "pre_utilization_per_1k": pre_util,
                "post_utilization_per_1k": post_util,
                "utilization_change": util_change_abs,
                "utilization_change_pct": util_change_pct,
                "analysis": [],
                "trend_category": ""
            }
            
            if util_change_pct < -20:
                utilization_trend["analysis"].append(f"Strong utilization reduction ({abs(util_change_pct):.1f}%) - policy is highly effective in reducing utilization.")
                utilization_trend["trend_category"] = "STRONG_REDUCTION"
            elif util_change_pct < -10:
                utilization_trend["analysis"].append(f"Moderate utilization reduction ({abs(util_change_pct):.1f}%) - policy shows positive impact.")
                utilization_trend["trend_category"] = "MODERATE_REDUCTION"
            elif util_change_pct < -5:
                utilization_trend["analysis"].append(f"Mild utilization reduction ({abs(util_change_pct):.1f}%) - policy has modest impact.")
                utilization_trend["trend_category"] = "MILD_REDUCTION"
            elif util_change_pct > 5:
                utilization_trend["analysis"].append(f"Utilization increase observed ({util_change_pct:.1f}%) - policy may not be effective.")
                utilization_trend["trend_category"] = "INCREASE"
            else:
                utilization_trend["analysis"].append("Minimal utilization change - policy impact is neutral.")
                utilization_trend["trend_category"] = "NEUTRAL"
            
            behavioral_explanation["utilization_trend"] = utilization_trend
    
    # Add confidence and reliability indicators
    confidence_score = impact_estimate.get("confidence_score") or metrics.get("confidence_score")
    if confidence_score:
        if isinstance(confidence_score, (int, float)):
            if confidence_score > 0.8:
                behavioral_explanation["confidence"] = "HIGH"
            elif confidence_score > 0.6:
                behavioral_explanation["confidence"] = "MEDIUM"
            else:
                behavioral_explanation["confidence"] = "LOW"
            behavioral_explanation["confidence_score"] = float(confidence_score)
        else:
            behavioral_explanation["confidence"] = str(confidence_score).upper()
    
    # Add comprehensive actionable insights with business context
    insights = []
    recommendations = []
    strategic_considerations = []
    
    # Primary policy effectiveness insights
    if percent_change < -20:
        insights.append("Policy is achieving strong reduction in utilization. Consider maintaining current approach.")
        strategic_considerations.append("Strong policy performance suggests the intervention is well-designed and effectively implemented. Consider expanding to similar service categories or member populations.")
    elif percent_change < -10:
        insights.append("Policy shows moderate effectiveness. Review provider engagement and patient education.")
        strategic_considerations.append("Moderate effectiveness indicates policy is working but has room for improvement. Focus on areas with lower compliance rates.")
        recommendations.append("Enhance provider communication and training")
        recommendations.append("Improve patient education materials")
    elif percent_change < -5:
        insights.append("Policy shows mild effectiveness. Consider policy adjustments or enhanced enforcement.")
        strategic_considerations.append("Mild effectiveness suggests policy may need refinement. Review policy design, communication strategy, and enforcement mechanisms.")
        recommendations.append("Review policy design and enforcement mechanisms")
    elif percent_change > 5:
        insights.append("Policy may not be effective. Review policy design and implementation.")
        strategic_considerations.append("Policy is not achieving desired outcomes. Conduct comprehensive review of policy design, implementation barriers, and stakeholder engagement.")
        recommendations.append("Conduct policy review and redesign if necessary")
    else:
        insights.append("Policy impact is neutral. Monitor for longer-term effects or consider policy adjustments.")
        strategic_considerations.append("Neutral impact may indicate policy needs more time to take effect, or that design adjustments are needed.")
    
    # Add timing and trend insights
    if treatment_pre and treatment_post:
        pre_util = treatment_pre.get("utilization_per_1k", 0.0)
        post_util = treatment_post.get("utilization_per_1k", 0.0)
        if pre_util > 0 and post_util < pre_util:
            reduction_rate = ((pre_util - post_util) / pre_util) * 100
            if reduction_rate > 15:
                insights.append(f"Rapid utilization reduction ({reduction_rate:.1f}%) observed, suggesting strong initial policy impact.")
            elif reduction_rate > 5:
                insights.append(f"Steady utilization reduction ({reduction_rate:.1f}%) indicates policy is gradually taking effect.")
    
    # Add cost-effectiveness insights
    if "cost_impact" in behavioral_explanation:
        cost_impact_data = behavioral_explanation["cost_impact"]
        savings_category = cost_impact_data.get("financial_impact", {}).get("savings_category", "")
        if savings_category == "HIGH":
            insights.append("Policy demonstrates high cost-effectiveness with significant savings potential.")
            strategic_considerations.append("High cost savings justify continued investment in this policy. Consider scaling to additional populations or service categories.")
        elif savings_category == "MEDIUM":
            insights.append("Policy shows positive cost impact with moderate savings.")
            strategic_considerations.append("Moderate cost savings support policy continuation. Focus on optimizing implementation to maximize savings.")
        elif savings_category == "NEGATIVE":
            insights.append("Policy cost impact is negative - review cost-effectiveness assumptions.")
            strategic_considerations.append("Negative cost impact requires immediate review. Consider policy redesign or discontinuation if cost concerns persist.")
    
    # Add provider network insights
    if "provider_response" in behavioral_explanation:
        provider_resp = behavioral_explanation["provider_response"]
        if provider_resp.get("compliant_providers_pct", 0) > 50:
            insights.append("Strong provider network compliance indicates effective policy communication and acceptance.")
        elif provider_resp.get("resistant_providers_pct", 0) > 30:
            insights.append("Significant provider resistance detected - targeted engagement may be needed.")
            recommendations.append("Develop provider-specific engagement strategies for resistant segments")
    
    # Add patient access insights
    if "patient_response" in behavioral_explanation:
        patient_resp = behavioral_explanation["patient_response"]
        if patient_resp.get("er_fallback_pct", 0) > 15:
            insights.append("Elevated ER utilization suggests potential access barriers - monitor patient outcomes closely.")
            recommendations.append("Assess patient access barriers and consider care navigation support")
        if patient_resp.get("defer_pct", 0) > 20:
            insights.append("Significant care deferral observed - evaluate impact on patient health outcomes.")
            recommendations.append("Monitor patient outcomes for deferred care and consider care coordination interventions")
    
    if "provider_archetype_shares" in behavioral_explanation:
        resistant_pct = behavioral_explanation["provider_archetype_shares"].get("provider_archetype_share_resistant", 0.0)
        if resistant_pct > 30:
            insights.append(f"High provider resistance ({resistant_pct:.1f}%) detected. Consider provider education and support programs.")
            recommendations.append("Implement provider training and support initiatives")
    
    if "patient_response_shares" in behavioral_explanation:
        er_fallback_pct = behavioral_explanation["patient_response_shares"].get("patient_response_share_overall_ER_fallback", 0.0)
        if er_fallback_pct > 15:
            insights.append(f"ER fallback observed ({er_fallback_pct:.1f}%). Monitor emergency department utilization closely.")
            recommendations.append("Monitor ER utilization and consider urgent care alternatives")
    
    # Add substitution insights
    if substitution_patterns and len(substitution_patterns) > 0:
        insights.append(f"{len(substitution_patterns)} substitution pattern(s) detected, indicating service substitution behavior.")
        recommendations.append("Review substitution patterns to ensure appropriate care delivery")
    
    if insights:
        behavioral_explanation["actionable_insights"] = insights
    
    if recommendations:
        behavioral_explanation["recommendations"] = recommendations
    
    if strategic_considerations:
        behavioral_explanation["strategic_considerations"] = strategic_considerations
    
    # Add comprehensive policy performance narrative
    performance_narrative = []
    
    # Overall performance assessment
    if percent_change < -15:
        performance_narrative.append({
            "aspect": "Overall Performance",
            "assessment": "EXCELLENT",
            "description": f"Policy demonstrates excellent performance with {abs(percent_change):.1f}% utilization reduction. The intervention is achieving its primary objectives effectively.",
            "evidence": f"Statistical analysis shows {abs(effect_size):.3f} effect size with {'statistically significant' if p_value < 0.05 else 'marginally significant'} results (p={p_value:.3f})"
        })
    elif percent_change < -8:
        performance_narrative.append({
            "aspect": "Overall Performance",
            "assessment": "GOOD",
            "description": f"Policy shows good performance with {abs(percent_change):.1f}% utilization reduction. The intervention is meeting expectations with room for optimization.",
            "evidence": f"Effect size of {abs(effect_size):.3f} indicates meaningful impact"
        })
    elif percent_change < -3:
        performance_narrative.append({
            "aspect": "Overall Performance",
            "assessment": "MODERATE",
            "description": f"Policy demonstrates moderate performance with {abs(percent_change):.1f}% utilization reduction. Consider targeted improvements to enhance effectiveness.",
            "evidence": "Policy is having some impact but may benefit from refinement"
        })
    else:
        performance_narrative.append({
            "aspect": "Overall Performance",
            "assessment": "NEEDS IMPROVEMENT",
            "description": f"Policy shows limited impact ({abs(percent_change):.1f}% change). Review policy design, implementation, and stakeholder engagement.",
            "evidence": "Current results suggest policy may need significant adjustments"
        })
    
    # Provider engagement assessment
    if "provider_archetype_shares" in behavioral_explanation:
        archetype_shares = behavioral_explanation["provider_archetype_shares"]
        compliant_pct = archetype_shares.get("provider_archetype_share_compliant", 0.0)
        adaptive_pct = archetype_shares.get("provider_archetype_share_adaptive", 0.0)
        resistant_pct = archetype_shares.get("provider_archetype_share_resistant", 0.0)
        
        if compliant_pct + adaptive_pct > 70:
            performance_narrative.append({
                "aspect": "Provider Engagement",
                "assessment": "STRONG",
                "description": f"Strong provider engagement with {compliant_pct + adaptive_pct:.1f}% of providers demonstrating compliant or adaptive behavior.",
                "evidence": f"Provider network shows {compliant_pct:.1f}% compliant and {adaptive_pct:.1f}% adaptive providers"
            })
        elif compliant_pct + adaptive_pct > 50:
            performance_narrative.append({
                "aspect": "Provider Engagement",
                "assessment": "MODERATE",
                "description": f"Moderate provider engagement with {compliant_pct + adaptive_pct:.1f}% of providers demonstrating compliant or adaptive behavior.",
                "evidence": f"Provider network shows {compliant_pct:.1f}% compliant and {adaptive_pct:.1f}% adaptive providers, with {resistant_pct:.1f}% showing resistance"
            })
        else:
            performance_narrative.append({
                "aspect": "Provider Engagement",
                "assessment": "NEEDS ATTENTION",
                "description": f"Provider engagement is below optimal levels with only {compliant_pct + adaptive_pct:.1f}% demonstrating compliant or adaptive behavior.",
                "evidence": f"Significant provider resistance ({resistant_pct:.1f}%) suggests need for enhanced engagement strategies"
            })
    
    # Patient response assessment
    if "patient_response_shares" in behavioral_explanation:
        patient_resp = behavioral_explanation["patient_response_shares"]
        comply_pct = patient_resp.get("patient_response_share_overall_comply", 0.0)
        substitute_pct = patient_resp.get("patient_response_share_overall_substitute", 0.0)
        defer_pct = patient_resp.get("patient_response_share_overall_defer", 0.0)
        
        if comply_pct > 60:
            performance_narrative.append({
                "aspect": "Patient Response",
                "assessment": "POSITIVE",
                "description": f"Strong patient compliance with {comply_pct:.1f}% of patients following the policy as intended.",
                "evidence": f"Patient behavior analysis shows high compliance with minimal substitution ({substitute_pct:.1f}%) or deferral ({defer_pct:.1f}%)"
            })
        elif comply_pct > 40:
            performance_narrative.append({
                "aspect": "Patient Response",
                "assessment": "MIXED",
                "description": f"Mixed patient response with {comply_pct:.1f}% compliance, but notable substitution ({substitute_pct:.1f}%) or deferral ({defer_pct:.1f}%) patterns.",
                "evidence": "Patient behavior suggests policy may need clearer communication or alternative care pathways"
            })
        else:
            performance_narrative.append({
                "aspect": "Patient Response",
                "assessment": "CONCERNING",
                "description": f"Low patient compliance ({comply_pct:.1f}%) with significant alternative behaviors observed.",
                "evidence": f"High rates of substitution ({substitute_pct:.1f}%) and/or deferral ({defer_pct:.1f}%) suggest policy may be creating access barriers"
            })
    
    # Cost impact assessment
    if "cost_impact" in behavioral_explanation:
        cost_impact_data = behavioral_explanation["cost_impact"]
        cost_change_pct = cost_impact_data.get("cost_change_pct", 0.0)
        annual_savings = cost_impact_data.get("financial_impact", {}).get("annual_savings_per_10k_members", 0.0)
        
        if cost_change_pct < -10:
            performance_narrative.append({
                "aspect": "Cost Impact",
                "assessment": "HIGHLY FAVORABLE",
                "description": f"Significant cost reduction of {abs(cost_change_pct):.1f}% demonstrates strong financial value.",
                "evidence": f"Estimated annual savings of ${annual_savings:,.0f} per 10,000 members"
            })
        elif cost_change_pct < -5:
            performance_narrative.append({
                "aspect": "Cost Impact",
                "assessment": "FAVORABLE",
                "description": f"Moderate cost reduction of {abs(cost_change_pct):.1f}% shows positive financial impact.",
                "evidence": f"Estimated annual savings of ${annual_savings:,.0f} per 10,000 members"
            })
        elif cost_change_pct > 5:
            performance_narrative.append({
                "aspect": "Cost Impact",
                "assessment": "UNFAVORABLE",
                "description": f"Cost increase of {cost_change_pct:.1f}% requires immediate review of policy cost-effectiveness.",
                "evidence": "Policy is not achieving cost savings objectives"
            })
    
    if performance_narrative:
        behavioral_explanation["performance_narrative"] = performance_narrative
    
    # Add key success factors
    success_factors = []
    if percent_change < -10:
        success_factors.append("Effective policy design aligned with clinical best practices")
        success_factors.append("Strong stakeholder communication and engagement")
    if "provider_archetype_shares" in behavioral_explanation:
        compliant_pct = behavioral_explanation["provider_archetype_shares"].get("provider_archetype_share_compliant", 0.0)
        if compliant_pct > 50:
            success_factors.append("High provider network compliance and acceptance")
    if "patient_response_shares" in behavioral_explanation:
        comply_pct = behavioral_explanation["patient_response_shares"].get("patient_response_share_overall_comply", 0.0)
        if comply_pct > 60:
            success_factors.append("Strong patient understanding and adherence")
    
    if success_factors:
        behavioral_explanation["key_success_factors"] = success_factors
    
    # Add risk factors
    risk_factors = []
    if "provider_archetype_shares" in behavioral_explanation:
        resistant_pct = behavioral_explanation["provider_archetype_shares"].get("provider_archetype_share_resistant", 0.0)
        circumvention_pct = behavioral_explanation["provider_archetype_shares"].get("provider_archetype_share_circumvention-prone", 0.0)
        if resistant_pct > 30:
            risk_factors.append(f"High provider resistance ({resistant_pct:.1f}%) may limit long-term policy effectiveness")
        if circumvention_pct > 15:
            risk_factors.append(f"Notable circumvention risk ({circumvention_pct:.1f}%) requires enhanced monitoring and enforcement")
    
    if "patient_response_shares" in behavioral_explanation:
        er_fallback_pct = behavioral_explanation["patient_response_shares"].get("patient_response_share_overall_ER_fallback", 0.0)
        if er_fallback_pct > 15:
            risk_factors.append(f"Elevated ER utilization ({er_fallback_pct:.1f}%) suggests potential access barriers or care gaps")
    
    if risk_factors:
        behavioral_explanation["risk_factors"] = risk_factors
    
    # Add statistical significance information
    if impact_estimate:
        p_value = impact_estimate.get("p_value")
        if p_value is not None:
            behavioral_explanation["statistical_significance"] = {
                "p_value": p_value,
                "significant": p_value < 0.05,
                "marginally_significant": 0.05 <= p_value < 0.10,
                "interpretation": "Statistically significant" if p_value < 0.05 else "Marginally significant" if p_value < 0.10 else "Not statistically significant"
            }
    
    # If still empty, create a basic explanation from available data
    if not behavioral_explanation or (len(behavioral_explanation) == 0 or all(not v for v in behavioral_explanation.values() if not isinstance(v, dict) and not isinstance(v, list))):
        if impact_estimate:
            effect_size = impact_estimate.get("effect_size", 0.0)
            percent_change = impact_estimate.get("percent_change", 0.0)
            
            if effect_size != 0 or percent_change != 0:
                behavioral_explanation = {
                    "summary": f"Observed {abs(percent_change):.1f}% {'reduction' if percent_change < 0 else 'increase'} in utilization",
                    "effect_size": effect_size,
                    "percent_change": percent_change,
                    "source": "inferred_from_impact_estimate",
                }
    
    return behavioral_explanation if behavioral_explanation else {}


def enhance_comparisons_with_baseline(
    tenant_id: UUID,
    observation_metrics: Dict[str, Any],
    baseline_version_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Enhance comparisons with baseline metrics
    
    Args:
        tenant_id: Tenant ID
        observation_metrics: Observation metrics (may include _reference_baseline from daily job for spread)
        baseline_version_id: Optional baseline version ID (if None, uses latest)
        
    Returns:
        Enhanced vs_baseline comparison
    """
    vs_baseline = {}
    ref_baseline = observation_metrics.get("_reference_baseline")
    
    # When daily job provides reference_baseline (unvaried metrics), compare observed to it so cost_change_pct = (mult-1)*100
    if ref_baseline:
        observed_utilization = float(observation_metrics.get("utilization_per_1k", 0.0) or 0.0)
        observed_cost_pmpm = float(
            observation_metrics.get("cost_pmpm", 0.0) or
            observation_metrics.get("cost_per_member", 0.0) or
            observation_metrics.get("paid_pmpm", 0.0) or
            observation_metrics.get("allowed_pmpm", 0.0) or 0.0
        )
        base_util = float(ref_baseline.get("utilization_per_1k", 0.0) or 0.0)
        base_cost = float(ref_baseline.get("cost_pmpm", 0.0) or ref_baseline.get("cost_per_member", 0.0) or 0.0)
        util_change_pct = ((observed_utilization - base_util) / base_util * 100) if base_util else 0.0
        cost_change_pct = ((observed_cost_pmpm - base_cost) / base_cost * 100) if base_cost else 0.0
        cost_change_pmpm = observed_cost_pmpm - base_cost
        utilization_change = observed_utilization - base_util
        return {
            "baseline_utilization_per_1k": base_util,
            "observed_utilization_per_1k": observed_utilization,
            "change_from_baseline": utilization_change,
            "change_from_baseline_pct": util_change_pct,
            "utilization_change": utilization_change,
            "utilization_change_pct": util_change_pct,
            "baseline_cost_pmpm": base_cost,
            "observed_cost_pmpm": observed_cost_pmpm,
            "cost_change": cost_change_pmpm,
            "cost_change_pmpm": cost_change_pmpm,
            "cost_change_pct": cost_change_pct,
            "baseline_member_months": ref_baseline.get("member_months"),
            "baseline_version_id": None,
        }
    
    # Get baseline from DB
    baseline = None
    if baseline_version_id:
        baseline = get_baseline(tenant_id, baseline_version_id)
    else:
        baseline = get_latest_baseline(tenant_id)
    
    if not baseline:
        print(f"WARNING: No baseline found for tenant {tenant_id}")
        # Still return a structure with 0 values so UI can display them
        observed_utilization = float(observation_metrics.get("utilization_per_1k", 0.0) or 0.0)
        observed_cost_pmpm = float(
            observation_metrics.get("cost_pmpm", 0.0) or 
            observation_metrics.get("cost_per_member", 0.0) or 
            observation_metrics.get("paid_pmpm", 0.0) or
            observation_metrics.get("allowed_pmpm", 0.0) or
            0.0
        )
        return {
            "baseline_utilization_per_1k": 0.0,
            "observed_utilization_per_1k": observed_utilization,
            "change_from_baseline": 0.0,
            "change_from_baseline_pct": 0.0,
            "utilization_change": 0.0,
            "utilization_change_pct": 0.0,
            "baseline_cost_pmpm": 0.0,
            "observed_cost_pmpm": observed_cost_pmpm,
            "cost_change_pmpm": 0.0,
            "cost_change_pct": 0.0,
            "baseline_member_months": None,
            "baseline_version_id": None,  # baseline is None here, so return None
        }
    
    # Try multiple locations for baseline metrics
    baseline_metrics = baseline.get("baseline_metrics", {}) or baseline.get("metrics", {})
    
    # Extract baseline metrics using metric dictionary names (consistent with baseline computation)
    baseline_utilization = None
    baseline_cost_pmpm = None
    baseline_member_months = None
    
    if isinstance(baseline_metrics, dict):
        # Check if this is a policy-specific baseline (has policy_id)
        is_policy_specific = baseline.get("policy_id") is not None
        
        if is_policy_specific:
            # Policy-specific baseline: use target metrics
            baseline_utilization = baseline_metrics.get("util_rate_target_per_1000_mm")
            baseline_cost_pmpm = baseline_metrics.get("paid_pmpm_target") or baseline_metrics.get("allowed_pmpm_target")
            
            # Fallback to alternative field names
            if baseline_utilization is None:
                baseline_utilization = baseline_metrics.get("utilization_per_1k")
            if baseline_cost_pmpm is None:
                baseline_cost_pmpm = baseline_metrics.get("cost_pmpm") or baseline_metrics.get("allowed_pmpm")
        else:
            # General baseline: use total metrics
            baseline_utilization = baseline_metrics.get("util_rate_total_per_1000_mm")
            baseline_cost_pmpm = baseline_metrics.get("allowed_pmpm_total")
            
            # Fallback to alternative field names
            if baseline_utilization is None:
                baseline_utilization = baseline_metrics.get("utilization_per_1k")
            if baseline_cost_pmpm is None:
                baseline_cost_pmpm = baseline_metrics.get("cost_pmpm") or baseline_metrics.get("allowed_pmpm")
        
        # Get member months for context
        baseline_member_months = baseline_metrics.get("member_months") or baseline_metrics.get("policy_eligible_member_months")
        
        print(f"DEBUG: Baseline extraction - is_policy_specific: {is_policy_specific}, util: {baseline_utilization}, cost: {baseline_cost_pmpm}")
    
    # Convert to float, defaulting to 0.0 if None
    if baseline_utilization is None:
        baseline_utilization = 0.0
    else:
        baseline_utilization = float(baseline_utilization)
    
    if baseline_cost_pmpm is None:
        baseline_cost_pmpm = 0.0
    else:
        baseline_cost_pmpm = float(baseline_cost_pmpm)
    
    # Extract observed metrics - try multiple field names
    observed_utilization = float(observation_metrics.get("utilization_per_1k", 0.0) or 0.0)
    observed_cost_pmpm = float(
        observation_metrics.get("cost_pmpm", 0.0) or 
        observation_metrics.get("cost_per_member", 0.0) or 
        observation_metrics.get("paid_pmpm", 0.0) or
        observation_metrics.get("allowed_pmpm", 0.0) or
        0.0
    )
    
    # Calculate cost comparison
    cost_change = observed_cost_pmpm - baseline_cost_pmpm
    cost_change_pct = 0.0
    if baseline_cost_pmpm > 0:
        cost_change_pct = (cost_change / baseline_cost_pmpm) * 100
    elif observed_cost_pmpm > 0:
        cost_change_pct = 999.0  # Infinite change if going from 0 to non-zero
    
    # Calculate utilization comparison
    utilization_change = observed_utilization - baseline_utilization
    if baseline_utilization > 0:
        utilization_change_pct = (utilization_change / baseline_utilization) * 100
    elif observed_utilization > 0:
        utilization_change_pct = 999.0 if utilization_change > 0 else -999.0
    else:
        utilization_change_pct = 0.0
    
    # Calculate cost comparison
    cost_change_pmpm = observed_cost_pmpm - baseline_cost_pmpm
    if baseline_cost_pmpm > 0:
        cost_change_pct = (cost_change_pmpm / baseline_cost_pmpm) * 100
    elif observed_cost_pmpm > 0:
        cost_change_pct = 999.0 if cost_change_pmpm > 0 else -999.0
    else:
        cost_change_pct = 0.0
    
    # Unified measure framework: flat measures and comparison_by_measure for single comparison table
    observed_measures = _build_observed_measures(observation_metrics)
    baseline_measures = _build_baseline_measures(baseline_metrics, baseline)
    comparison_by_measure = _build_comparison_by_measure_baseline(
        baseline_measures,
        observed_measures,
        baseline_utilization,
        observed_utilization,
        baseline_cost_pmpm,
        observed_cost_pmpm,
        utilization_change,
        utilization_change_pct,
        cost_change_pmpm,
        cost_change_pct,
    )
    
    # Build comprehensive comparison (even if some values are 0)
    vs_baseline = {
        # Utilization metrics
        "baseline_utilization_per_1k": baseline_utilization,
        "observed_utilization_per_1k": observed_utilization,
        "change_from_baseline": utilization_change,  # Keep for backward compatibility
        "change_from_baseline_pct": utilization_change_pct,  # Keep for backward compatibility
        "utilization_change": utilization_change,
        "utilization_change_pct": utilization_change_pct,
        
        # Cost metrics
        "baseline_cost_pmpm": baseline_cost_pmpm,
        "observed_cost_pmpm": observed_cost_pmpm,
        "cost_change": cost_change_pmpm,  # Absolute cost change (alias for cost_change_pmpm)
        "cost_change_pmpm": cost_change_pmpm,  # PMPM cost change
        "cost_change_pct": cost_change_pct,
        
        # Unified measure framework (same measures everywhere)
        "baseline_measures": baseline_measures,
        "comparison_by_measure": comparison_by_measure,
        
        # Context
        "baseline_member_months": float(baseline_member_months) if baseline_member_months else None,
        "baseline_version_id": str(baseline.get("id")) if baseline and baseline.get("id") else (baseline.get("baseline_id") if baseline else None),
    }
    
    return vs_baseline


def enhance_comparisons_with_predicted(
    tenant_id: UUID,
    policy_id: UUID,
    observation_metrics: Dict[str, Any],
    prediction_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Enhance comparisons with predicted impact
    
    Args:
        tenant_id: Tenant ID
        policy_id: Policy ID
        observation_metrics: Observation metrics
        prediction_id: Optional prediction ID (if None, tries to get from policy)
        
    Returns:
        Enhanced vs_predicted comparison
    """
    vs_predicted = {}
    
    # Get predicted impact from database first
    predicted_impact = None
    prediction_id_from_db = None
    try:
        from uepi_api.storage_policy_predicted_impact import get_predicted_impact
        predicted_impact_db = get_predicted_impact(policy_id, tenant_id)
        
        if predicted_impact_db and isinstance(predicted_impact_db, dict):
            if not prediction_id:
                from uepi_api.database import SessionLocal
                from uepi_api.models.predicted_impact import PolicyPredictedImpact
                from sqlalchemy import desc
                db = SessionLocal()
                try:
                    policy_id_uuid = policy_id if isinstance(policy_id, UUID) else UUID(str(policy_id))
                    pi_record = db.query(PolicyPredictedImpact).filter(
                        PolicyPredictedImpact.tenant_id == tenant_id,
                        PolicyPredictedImpact.policy_id == policy_id_uuid
                    ).order_by(desc(PolicyPredictedImpact.predicted_at)).first()
                    if pi_record:
                        prediction_id_from_db = str(pi_record.id)
                except Exception:
                    pass
                finally:
                    db.close()
            
            predicted_impact = predicted_impact_db
            if not prediction_id:
                prediction_id = prediction_id_from_db
    except Exception as e:
        print(f"WARNING: Could not load predicted impact from database: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to policy metadata
        policy = get_policy(policy_id, tenant_id)
        if policy:
            metadata = policy.get("metadata", {})
            logic = policy.get("logic", {})
            predicted_impact = metadata.get("predicted_impact") or logic.get("predicted_impact") or policy.get("predicted_impact")
    
    if predicted_impact and isinstance(predicted_impact, dict):
        pred_metrics = predicted_impact.get("metrics", {})
        
        predicted_utilization_change = (
            pred_metrics.get("utilization_change_per_1k") or
            pred_metrics.get("utilization_change") or
            pred_metrics.get("estimated_utilization_change") or
            0.0
        )
        predicted_utilization_change_pct = (
            pred_metrics.get("estimated_utilization_reduction_percent") or
            pred_metrics.get("utilization_change_pct") or
            pred_metrics.get("utilization_reduction_percent") or
            pred_metrics.get("estimated_utilization_reduction_pct") or
            None
        )
        
        predicted_cost_change_pmpm = (
            pred_metrics.get("cost_change_pmpm") or
            pred_metrics.get("estimated_cost_reduction_pmpm") or
            pred_metrics.get("cost_change") or
            pred_metrics.get("estimated_cost_change_pmpm") or
            0.0
        )
        predicted_cost_change_pct = (
            pred_metrics.get("estimated_cost_reduction_percent") or
            pred_metrics.get("cost_change_pct") or
            pred_metrics.get("cost_reduction_percent") or
            pred_metrics.get("estimated_cost_reduction_pct") or
            None
        )
        
        predicted_effect_size = (
            pred_metrics.get("effect_size") or
            pred_metrics.get("predicted_effect_size") or
            pred_metrics.get("estimated_effect_size") or
            pred_metrics.get("overall_effect_size") or
            (predicted_utilization_change / 100.0 if predicted_utilization_change != 0 else 0.0)
        )
        
        # Get observed metrics
        observed_utilization = float(observation_metrics.get("utilization_per_1k", 0.0) or 0.0)
        observed_cost_pmpm = float(observation_metrics.get("cost_pmpm", 0.0) or observation_metrics.get("cost_per_member", 0.0) or 0.0)
        observed_effect_size = float(observation_metrics.get("observed_effect_size", 0.0) or observation_metrics.get("effect_size", 0.0) or 0.0)
        
        # Get baseline for comparison
        baseline_utilization = observation_metrics.get("baseline_utilization_per_1k")
        baseline_cost_pmpm = observation_metrics.get("baseline_cost_pmpm")
        
        if baseline_utilization is None:
            baseline_obj = get_latest_baseline(tenant_id)
            if baseline_obj:
                baseline_metrics_dict = baseline_obj.get("baseline_metrics", {}) or baseline_obj.get("metrics", {})
                baseline_utilization = baseline_metrics_dict.get("util_rate_total_per_1000_mm") or baseline_metrics_dict.get("utilization_per_1k", 0.0)
                baseline_cost_pmpm = baseline_metrics_dict.get("allowed_pmpm_total") or baseline_metrics_dict.get("cost_pmpm", 0.0)
        
        baseline_utilization = float(baseline_utilization or 0.0)
        baseline_cost_pmpm = float(baseline_cost_pmpm or 0.0)
        
        # Calculate predicted utilization and cost (predicted = baseline + predicted_change)
        predicted_utilization = baseline_utilization + predicted_utilization_change if baseline_utilization > 0 else observed_utilization
        predicted_cost_pmpm = baseline_cost_pmpm + predicted_cost_change_pmpm if baseline_cost_pmpm > 0 else observed_cost_pmpm
        
        # Calculate prediction errors
        utilization_prediction_error = observed_utilization - predicted_utilization
        cost_prediction_error = observed_cost_pmpm - predicted_cost_pmpm
        effect_size_prediction_error = observed_effect_size - predicted_effect_size
        
        # Calculate percentage errors
        utilization_prediction_error_pct = 0.0
        if predicted_utilization != 0:
            utilization_prediction_error_pct = (utilization_prediction_error / abs(predicted_utilization)) * 100
        
        cost_prediction_error_pct = 0.0
        if predicted_cost_pmpm != 0:
            cost_prediction_error_pct = (cost_prediction_error / abs(predicted_cost_pmpm)) * 100
        
        effect_size_prediction_error_pct = 0.0
        if predicted_effect_size != 0:
            effect_size_prediction_error_pct = (effect_size_prediction_error / abs(predicted_effect_size)) * 100
        
        # Overall prediction accuracy (clamped to 0-100% range)
        # Accuracy = 100% - absolute error percentage, but cap error at 200% to prevent negative accuracy
        utilization_accuracy = 0.0
        if predicted_utilization > 0:
            error_pct = abs(utilization_prediction_error_pct)
            utilization_accuracy = max(0.0, min(100.0, 100.0 - min(error_pct, 200.0)))
        
        cost_accuracy = 0.0
        if predicted_cost_pmpm > 0:
            error_pct = abs(cost_prediction_error_pct)
            cost_accuracy = max(0.0, min(100.0, 100.0 - min(error_pct, 200.0)))
        
        if predicted_utilization > 0 and predicted_cost_pmpm > 0:
            prediction_accuracy_pct = (utilization_accuracy + cost_accuracy) / 2.0
        elif predicted_utilization > 0:
            prediction_accuracy_pct = utilization_accuracy
        elif predicted_cost_pmpm > 0:
            prediction_accuracy_pct = cost_accuracy
        else:
            prediction_accuracy_pct = 0.0
        
        # Unified measure framework: comparison_by_measure for same table (predicted | observed | error | error_pct)
        comparison_by_measure_pred = {
            "util_rate_target_per_1000_mm": {
                "predicted": predicted_utilization,
                "observed": observed_utilization,
                "error": utilization_prediction_error,
                "error_pct": utilization_prediction_error_pct,
            },
            "allowed_pmpm_target": {
                "predicted": predicted_cost_pmpm,
                "observed": observed_cost_pmpm,
                "error": cost_prediction_error,
                "error_pct": cost_prediction_error_pct,
            },
        }
        predicted_measures = {
            "util_rate_target_per_1000_mm": predicted_utilization,
            "allowed_pmpm_target": predicted_cost_pmpm,
        }
        
        vs_predicted = {
            # Reference levels used to derive predicted (also chart baseline when vs_baseline is empty)
            "baseline_utilization_per_1k": baseline_utilization,
            "baseline_cost_pmpm": baseline_cost_pmpm,
            # Utilization metrics (ensure both formats are present)
            "predicted_utilization": predicted_utilization,
            "predicted_utilization_per_1k": predicted_utilization,  # Alias for consistency
            "observed_utilization": observed_utilization,
            "observed_utilization_per_1k": observed_utilization,  # Alias for consistency
            "predicted_utilization_change": predicted_utilization_change,
            "predicted_utilization_change_pct": predicted_utilization_change_pct,
            "utilization_prediction_error": utilization_prediction_error,
            "utilization_prediction_error_pct": utilization_prediction_error_pct,
            
            # Cost metrics
            "predicted_cost_pmpm": predicted_cost_pmpm,
            "observed_cost_pmpm": observed_cost_pmpm,
            "predicted_cost_change_pmpm": predicted_cost_change_pmpm,
            "predicted_cost_change_pct": predicted_cost_change_pct,
            "cost_prediction_error": cost_prediction_error,
            "cost_prediction_error_pct": cost_prediction_error_pct,
            
            # Effect size (overall impact)
            "predicted_effect_size": predicted_effect_size,
            "observed_effect_size": observed_effect_size,
            "prediction_error": effect_size_prediction_error,
            "prediction_error_pct": effect_size_prediction_error_pct,
            "prediction_accuracy_pct": prediction_accuracy_pct,
            "prediction_id": prediction_id or prediction_id_from_db,
            
            # Unified measure framework
            "predicted_measures": predicted_measures,
            "comparison_by_measure": comparison_by_measure_pred,
        }
        
        # Include confidence intervals and ramp-up projections from predicted impact for frontend display
        if predicted_impact.get("confidence_intervals"):
            vs_predicted["confidence_intervals"] = predicted_impact["confidence_intervals"]
        if predicted_impact.get("ramp_up_projections"):
            vs_predicted["ramp_up_projections"] = predicted_impact["ramp_up_projections"]
    
    return vs_predicted


def create_observation_from_analysis(
    tenant_id: UUID,
    policy_id: UUID,
    analysis_id: Optional[UUID],
    analysis_result: Dict[str, Any],
    data_period_id: Optional[str] = None,
    observation_period_start: Optional[str] = None,
    observation_period_end: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Create observation from impact analysis result (or from policy metrics when analysis_id is None).
    
    Observation period: when provided, use observation_period_start and observation_period_end (e.g. policy
    effective date through run date). Otherwise infer from data_period or analysis_result post_period.
    
    Args:
        tenant_id: Tenant ID
        policy_id: Policy ID
        analysis_id: Impact analysis ID, or None when creating from policy metrics (e.g. regenerate-all)
        analysis_result: Result from impact analysis (or metrics dict with metrics.treatment_post / post_period)
        data_period_id: Optional data period ID
        observation_period_start: Optional period start (e.g. policy effective date); when set with end, used as observation window
        observation_period_end: Optional period end (e.g. run date); when set with start, used as observation window
        
    Returns:
        Created observation document or None if creation failed
    """
    try:
        # Get policy and policy version
        policy = get_policy(policy_id, tenant_id)
        if not policy:
            print(f"Warning: Policy {policy_id} not found for observation creation")
            return None
        
        policy_version = get_latest_version(tenant_id, policy_id)
        # Get the database PolicyVersion ID (UUID) if version exists
        policy_version_id = None
        if policy_version:
            # Query database to get the actual PolicyVersion.id (UUID)
            from uepi_api.database import SessionLocal
            from uepi_api.models.policy import PolicyVersion as PolicyVersionDB
            from sqlalchemy import desc
            db = SessionLocal()
            try:
                version_db = db.query(PolicyVersionDB).filter(
                    PolicyVersionDB.tenant_id == tenant_id,
                    PolicyVersionDB.policy_id == policy_id,
                    PolicyVersionDB.version_number == policy_version.version_number
                ).first()
                if version_db:
                    policy_version_id = str(version_db.id)
            except Exception as e:
                print(f"WARNING: Could not get PolicyVersion ID: {e}")
            finally:
                db.close()
        
        # Determine observation period: explicit override (effective_date → run_date) > data_period > post_period
        _period_start = observation_period_start
        _period_end = observation_period_end
        
        if not _period_start or not _period_end:
            if data_period_id:
                # data_period_id may be UUID (DB id) or string period_id; try both
                data_period = None
                try:
                    from uepi_api.storage_data_periods import get_data_period_by_id
                    if len(str(data_period_id)) == 36 and str(data_period_id).count("-") == 4:
                        data_period = get_data_period_by_id(tenant_id, data_period_id)
                    if not data_period:
                        data_period = get_data_period(tenant_id, str(data_period_id))
                except Exception:
                    data_period = get_data_period(tenant_id, str(data_period_id))
                if data_period:
                    _period_start = _period_start or data_period.get("start_date")
                    _period_end = _period_end or data_period.get("end_date")
            if (not _period_start or not _period_end) and "post_period" in analysis_result:
                post_period = analysis_result["post_period"]
                _period_start = _period_start or post_period.get("start")
                _period_end = _period_end or post_period.get("end")
        
        observation_period_start = _period_start
        observation_period_end = _period_end
        
        # Extract metrics
        metrics = extract_metrics_from_analysis_result(analysis_result)
        
        # Extract existing comparisons (if any)
        comparisons = extract_comparisons_from_analysis_result(analysis_result)
        
        # Enhance with baseline comparison if not already present
        if not comparisons.get("vs_baseline"):
            baseline_version_id = None
            if "baseline_version_id" in analysis_result:
                baseline_version_id = analysis_result["baseline_version_id"]
            comparisons["vs_baseline"] = enhance_comparisons_with_baseline(
                tenant_id=tenant_id,
                observation_metrics=metrics,
                baseline_version_id=baseline_version_id,
            )
        
        # Always add policy-specific baseline comparison if available
        policy_baseline = None
        try:
            from uepi_api.storage_baselines import get_latest_baseline
            # Policy baselines are stored with baseline_type=ROLLING; look by policy_id only
            policy_baseline = get_latest_baseline(tenant_id, policy_id=policy_id, baseline_type=None)
        except Exception as e:
            print(f"WARNING: Could not get policy-specific baseline: {e}")
            policy_baseline = None
        
        if policy_baseline:
            print(f"✅ Found policy-specific baseline: {policy_baseline.get('id', policy_baseline.get('baseline_id', 'N/A'))[:8]}...")
            comparisons["vs_policy_baseline"] = enhance_comparisons_with_baseline(
                tenant_id=tenant_id,
                observation_metrics=metrics,
                baseline_version_id=str(policy_baseline.get("id")) if policy_baseline.get("id") else policy_baseline.get("baseline_id"),
            )
        else:
            print(f"⚠️  No policy-specific baseline found for policy {policy_id}")
            # Still create vs_policy_baseline with 0 values so UI can display it
            comparisons["vs_policy_baseline"] = {
                "baseline_utilization_per_1k": 0.0,
                "baseline_cost_pmpm": 0.0,
                "observed_utilization_per_1k": metrics.get("utilization_per_1k", 0.0),
                "observed_cost_pmpm": metrics.get("cost_pmpm", 0.0),
                "utilization_change": 0.0,
                "utilization_change_pct": 0.0,
                "cost_change": 0.0,
                "cost_change_pct": 0.0,
            }
        
        # Enhance with predicted comparison if not already present
        # Phase 3.1: Pass baseline into observation_metrics so enhance_comparisons_with_predicted can compute predictions
        if not comparisons.get("vs_predicted"):
            prediction_id = analysis_result.get("prediction_id")
            metrics_with_baseline = dict(metrics)
            vb = comparisons.get("vs_baseline") or {}
            if vb.get("baseline_utilization_per_1k") is not None:
                metrics_with_baseline["baseline_utilization_per_1k"] = vb["baseline_utilization_per_1k"]
            if vb.get("baseline_cost_pmpm") is not None:
                metrics_with_baseline["baseline_cost_pmpm"] = vb["baseline_cost_pmpm"]
            comparisons["vs_predicted"] = enhance_comparisons_with_predicted(
                tenant_id=tenant_id,
                policy_id=policy_id,
                observation_metrics=metrics_with_baseline,
                prediction_id=prediction_id,
            )
        
        # Extract behavioral explanation
        behavioral_explanation = extract_behavioral_explanation_from_analysis_result(analysis_result)
        
        # Unified measure framework: observed_measures (same canonical keys as baseline/prediction)
        observed_measures = _build_observed_measures(metrics)
        
        # Create observation
        observation_data = {
            "policy_id": str(policy_id),
            "policy_version_id": policy_version_id,
            "data_period_id": data_period_id,
            "data_period_ids": [data_period_id] if data_period_id else [],
            "observation_type": "PERIODIC",
            "observation_period_start": observation_period_start,
            "observation_period_end": observation_period_end,
            "baseline_version_id": comparisons.get("vs_baseline", {}).get("baseline_version_id"),
            "prediction_id": comparisons.get("vs_predicted", {}).get("prediction_id"),
            "metrics": metrics,
            "observed_measures": observed_measures,
            "comparisons": comparisons,
            "behavioral_explanation": behavioral_explanation,
            "metadata": {
                "created_from": "impact_analysis" if analysis_id else "policy_metrics",
            },
        }
        if analysis_id:
            observation_data["analysis_id"] = str(analysis_id)
            observation_data["metadata"]["analysis_id"] = str(analysis_id)
        
        observation = create_observation(tenant_id=tenant_id, observation_data=observation_data)
        
        if observation:
            print(f"✅ Successfully created observation {observation.get('observation_id')} for policy {policy_id}")
        else:
            print(f"⚠️  Observation creation returned None for policy {policy_id}")
        
        return observation
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error creating observation from analysis {analysis_id}: {error_msg}")
        import traceback
        error_trace = traceback.format_exc()
        print(f"Full traceback:\n{error_trace}")
        # Return None instead of raising - let caller handle it
        return None
