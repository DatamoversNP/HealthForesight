"""
Unified measure list for Baseline, Prediction, Observation, and What-If.
Single source of truth for canonical measure keys and display so all modules
expose the same measures and the UI can show one comparison table.
"""

from typing import Dict, List, Any, Optional

from .metric_dictionary import METRIC_DICTIONARY, get_metric_definition


# Ordered list of measure keys for the comparison table (Phase 1: core + primary outcome).
# Expand with layer_a, layer_b, etc. in later phases.
UNIFIED_MEASURE_KEYS: List[str] = [
    # Core denominators
    "member_months",
    "unique_members",
    "policy_eligible_member_months",
    # Primary outcome (M1–M7) – must align baseline, predicted, observed
    "util_rate_total_per_1000_mm",
    "util_rate_target_per_1000_mm",
    "allowed_pmpm_total",
    "allowed_pmpm_target",
    "paid_pmpm_total",
    "allowed_total_annualized",
]

# Aliases: map from keys used in baseline_metrics / observation to canonical key
# so we can normalize when building observed_measures and comparison_by_measure.
BASELINE_KEY_ALIASES: Dict[str, str] = {
    "utilization_per_1k": "util_rate_target_per_1000_mm",
    "util_rate_per_1k": "util_rate_total_per_1000_mm",
    "cost_pmpm": "allowed_pmpm_target",
    "cost_per_member": "allowed_pmpm_target",
}


def get_measure_display(metric_key: str) -> Dict[str, Any]:
    """Return display name and unit for a canonical measure key."""
    # Prefer metric dictionary
    defin = get_metric_definition(metric_key)
    if defin:
        return {
            "name": defin.name.replace("_", " ").title(),
            "unit": defin.unit,
            "formula": getattr(defin, "formula", None) or "",
        }
    # Fallback for aliases
    if metric_key == "util_rate_target_per_1000_mm":
        return {"name": "Utilization (per 1K)", "unit": "per 1,000 member-months", "formula": ""}
    if metric_key == "allowed_pmpm_target" or metric_key == "paid_pmpm_total":
        return {"name": "Cost PMPM", "unit": "dollars PMPM", "formula": ""}
    if metric_key == "util_rate_total_per_1000_mm":
        return {"name": "Utilization total (per 1K)", "unit": "per 1,000 member-months", "formula": ""}
    if metric_key == "allowed_pmpm_total":
        return {"name": "Cost total PMPM", "unit": "dollars PMPM", "formula": ""}
    return {"name": metric_key.replace("_", " ").title(), "unit": "", "formula": ""}


def get_unified_measure_keys(include_optional: bool = True) -> List[str]:
    """Return ordered list of canonical measure keys for the comparison table."""
    return list(UNIFIED_MEASURE_KEYS)


def normalize_to_canonical_key(key: str) -> Optional[str]:
    """Map a key from baseline_metrics or observation to canonical key, or None."""
    if key in UNIFIED_MEASURE_KEYS:
        return key
    return BASELINE_KEY_ALIASES.get(key)
