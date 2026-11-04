"""Cross-domain causal feasibility — eligibility for ALL policy types; estimation selective.

Statuses:
  CAUSAL_ESTIMATE_SUPPORTED
  CAUSAL_DESIGN_POSSIBLE_DATA_INSUFFICIENT
  DESCRIPTIVE_ONLY
  NOT_IDENTIFIABLE

Mechanical payment-rule savings must NEVER be labeled causal savings.

IMPORTANT: DESCRIPTIVE_ONLY is a *current-evidence* status, not a permanent exclusion.
Reimbursement and coding policies remain estimation_eligible when longitudinal data,
suitable comparisons, and defensible identification become available.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from uepi_api.services.analytical_strategy_registry import resolve_mechanism

FEASIBILITY_VERSION = "causal-feasibility-v2"

DOMAIN_GUIDANCE: Dict[str, Dict[str, Any]] = {
    "UTILIZATION_MANAGEMENT": {
        "outcomes": ["utilization_index", "cost", "access_delay"],
        "candidate_designs": ["difference_in_differences", "controlled_interrupted_time_series"],
        "estimation_eligible": True,
    },
    "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION": {
        "outcomes": ["paid_per_eligible_service", "net_spend", "coding_behavior"],
        "candidate_designs": ["controlled_interrupted_time_series", "difference_in_differences"],
        "estimation_eligible": True,
        "mechanical_vs_causal": (
            "Deterministic secondary-% reduction is a payment-rule effect; "
            "causal asks whether net payments/coding changed beyond the counterfactual."
        ),
    },
    "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL": {
        "outcomes": ["facility_mix", "episode_cost", "access"],
        "candidate_designs": ["difference_in_differences"],
        "estimation_eligible": True,
        "mechanical_vs_causal": (
            "Hospital % of allowed is mechanical; causal asks whether site mix and "
            "total spend shifted because of the policy."
        ),
    },
    "CODING_EDIT_MODIFIER": {
        "outcomes": ["code_pair_frequency", "payments", "modifier_use"],
        "candidate_designs": ["edit_change_analysis", "controlled_interrupted_time_series"],
        "estimation_eligible": True,
        "mechanical_vs_causal": (
            "PTP denial/modifier mechanics are payment-rule effects; "
            "causal asks whether coding behavior and net spend changed vs counterfactual."
        ),
    },
    "FEE_SCHEDULE_UNIT_PRICE": {
        "outcomes": ["units_per_service", "payments", "coding_shifts"],
        "candidate_designs": ["controlled_interrupted_time_series"],
        "estimation_eligible": True,
    },
    "COVERAGE_DETERMINATION": {
        "outcomes": ["service_uptake", "coverage_related_denials", "downstream_care"],
        "candidate_designs": ["staggered_adoption", "interrupted_time_series"],
        "estimation_eligible": True,
    },
    "DENIAL_ADJUSTMENT": {
        "outcomes": ["denial_rate", "rework", "net_paid"],
        "candidate_designs": ["controlled_interrupted_time_series"],
        "estimation_eligible": True,
    },
}


def assess_causal_feasibility(
    *,
    policy_id: str,
    policy_name: Optional[str] = None,
    policy_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    has_comparison_population: bool = False,
    has_pretrend_window: bool = False,
    has_post_window: bool = False,
    concurrent_interventions: bool = True,
    labeled_synthetic_series: bool = False,
    mechanism_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Assess causal feasibility for any policy domain. Does not fabricate estimates."""
    mechanism = (mechanism_override or "").upper() or resolve_mechanism(
        policy_type=policy_type,
        policy_name=policy_name,
        metadata=metadata,
        policy_id=policy_id,
    )
    guidance = DOMAIN_GUIDANCE.get(
        mechanism,
        {
            "outcomes": ["policy_specific_outcome"],
            "candidate_designs": ["difference_in_differences", "controlled_interrupted_time_series"],
            "estimation_eligible": True,
        },
    )
    estimation_eligible = bool(guidance.get("estimation_eligible", True))

    assumptions: List[str] = [
        "Stable unit treatment value (limited interference) unless otherwise diagnosed",
        "No unmeasured confounding of treatment assignment / timing",
        "Outcome definition and denominator stable across pre/post",
    ]
    diagnostics: List[Dict[str, Any]] = [
        {"check": "comparison_population", "pass": has_comparison_population},
        {"check": "pretrend_window", "pass": has_pretrend_window},
        {"check": "post_window", "pass": has_post_window},
        {
            "check": "concurrent_interventions_cleared",
            "pass": not concurrent_interventions,
            "flagged": concurrent_interventions,
        },
    ]
    blockers: List[str] = []
    upgrade_path: List[str] = [
        "Define intervention effective date and exposed services",
        "Identify untreated or staggered comparison population",
        "Assemble pretrend + post windows with stable denominators",
        "Test parallel trends / confounding / concurrent interventions",
        "Select justified design (DiD, ITS, edit-change, etc.) — not automatic",
    ]

    name_u = (policy_name or "").upper()
    is_mri = policy_id == "d403f101-08dd-45c9-ab83-d42e37c62018" or (
        "MRI" in name_u and ("PRIOR" in name_u or "AUTH" in name_u) and "NCD" not in name_u and "LCD" not in name_u
    )

    if is_mri and labeled_synthetic_series:
        status = "CAUSAL_ESTIMATE_SUPPORTED"
        method = "difference_in_differences"
        notes = [
            "Synthetic labeled DiD series with known-answer recovery (~−9.417 index points).",
            "Not empirical Blue Cross NC claims causal attribution.",
        ]
    elif estimation_eligible and has_comparison_population and has_pretrend_window and has_post_window:
        if concurrent_interventions:
            status = "CAUSAL_DESIGN_POSSIBLE_DATA_INSUFFICIENT"
            method = guidance["candidate_designs"][0]
            blockers.append(
                "Comparison windows present but concurrent interventions / confounding not cleared."
            )
        else:
            # Design gates pass but no validated estimate fixture for non-MRI yet
            status = "CAUSAL_DESIGN_POSSIBLE_DATA_INSUFFICIENT"
            method = guidance["candidate_designs"][0]
            blockers.append(
                "Identification design candidates exist; validated longitudinal estimate not yet shipped for this policy."
            )
        notes = [
            guidance.get("mechanical_vs_causal")
            or "Eligible for causal estimation; current build lacks a supported estimate.",
            "Not permanently excluded from causal analysis.",
        ]
    elif mechanism in (
        "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION",
        "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
        "CODING_EDIT_MODIFIER",
        "FEE_SCHEDULE_UNIT_PRICE",
    ):
        # Current demo has mechanical fixtures only — still estimation_eligible
        status = "CAUSAL_DESIGN_POSSIBLE_DATA_INSUFFICIENT"
        method = guidance["candidate_designs"][0]
        blockers.append(
            "Only deterministic mechanical payment fixtures are available today; "
            "longitudinal comparison design not yet configured for this policy."
        )
        notes = [
            guidance.get("mechanical_vs_causal")
            or "Separate mechanical payment-rule effect from causal behavioral/spend effect.",
            "DESCRIPTIVE mechanical results may be shown alongside this feasibility status.",
            "estimation_eligible=true — not a permanent exclusion from causal analysis.",
        ]
    elif mechanism in ("COVERAGE_DETERMINATION",) or "NCD" in name_u or "LCD" in name_u:
        status = "CAUSAL_DESIGN_POSSIBLE_DATA_INSUFFICIENT"
        method = "interrupted_time_series"
        blockers.append("Coverage-change comparison design not validated on demo data yet.")
        notes = [
            "Coverage applicability ≠ causal effect of the coverage change.",
            "estimation_eligible=true when staggered adoption / ITS inputs become available.",
        ]
    elif mechanism == "UTILIZATION_MANAGEMENT":
        status = "CAUSAL_DESIGN_POSSIBLE_DATA_INSUFFICIENT"
        method = "difference_in_differences"
        blockers.append("Non-MRI UM policies lack validated synthetic DiD fixtures in this build.")
        notes = ["Causal eligibility assessed; estimation only when design + data pass gates."]
    else:
        status = "NOT_IDENTIFIABLE"
        method = None
        estimation_eligible = False
        blockers.append(f"No causal adapter registered for mechanism={mechanism}.")
        notes = ["Feasibility assessed; estimate withheld."]

    # Companion descriptive layer for payment/coding (does not replace feasibility)
    descriptive_mechanical_available = mechanism in (
        "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION",
        "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
        "CODING_EDIT_MODIFIER",
        "FEE_SCHEDULE_UNIT_PRICE",
    )

    return {
        "feasibility_version": FEASIBILITY_VERSION,
        "policy_id": policy_id,
        "policy_name": policy_name,
        "policy_type": policy_type,
        "mechanism": mechanism,
        "status": status,
        "estimation_eligible": estimation_eligible,
        "permanent_exclusion": False if estimation_eligible else status == "NOT_IDENTIFIABLE",
        "candidate_outcomes": guidance.get("outcomes", []),
        "candidate_designs": guidance.get("candidate_designs", []),
        "selected_method": method,
        "assumptions": assumptions,
        "diagnostics": diagnostics,
        "blockers": blockers,
        "upgrade_path": upgrade_path if estimation_eligible else [],
        "notes": notes,
        "descriptive_mechanical_available": descriptive_mechanical_available,
        "estimate_emitted": status == "CAUSAL_ESTIMATE_SUPPORTED",
        "honesty": {
            "mechanical_payment_is_not_causal": True,
            "cross_domain_eligibility": True,
            "selective_estimation": True,
            "descriptive_only_is_not_permanent_ban": True,
            "not_blue_cross_nc_empirical": True,
        },
    }


def assess_for_demo_policy(
    policy_id: str,
    policy_name: str,
    policy_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convenience defaults for shipped demo policies."""
    from uepi_api.services.enterprise_intelligence_fixtures import (
        MRI_POLICY_ID,
        MPPR_POLICY_ID,
        SOS_POLICY_ID,
        _expansion_ids,
    )

    exp = _expansion_ids()
    is_mri = policy_id == MRI_POLICY_ID
    is_payment = policy_id in (MPPR_POLICY_ID, SOS_POLICY_ID, exp.get("infusion"))
    is_coding = policy_id in (exp.get("ptp"), exp.get("mue"))
    return assess_causal_feasibility(
        policy_id=policy_id,
        policy_name=policy_name,
        policy_type=policy_type,
        metadata=metadata,
        has_comparison_population=is_mri,
        has_pretrend_window=is_mri,
        has_post_window=is_mri,
        concurrent_interventions=not is_mri,
        labeled_synthetic_series=is_mri or is_coding or is_payment,
    )
