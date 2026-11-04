"""Versioned analytical strategy registry — mechanism → calculation engine.

One common policy lifecycle; different engines by mechanism. Reimbursement
policies must never silently fall through to utilization elasticity (MRI UM).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Set


REGISTRY_VERSION = "analytical-strategy-registry-v1"

# Explicit sign convention for payment engines (API + UI must surface this).
PAYMENT_SIGN_CONVENTION = {
    "payment_impact": (
        "Payer savings = baseline_paid − post_policy_paid. "
        "Positive means the payer pays less (provider receives less)."
    ),
    "provider_payment_change": "Negative of payment_impact (provider perspective).",
    "delta_payment_impact": (
        "Incremental payer savings vs base scenario. "
        "Positive = additional payer savings (not increased provider payment)."
    ),
    "volume_effect": "Change attributable to units/volume; 0 when volume held constant.",
    "price_effect": "Change attributable to unit price / payment rules.",
    "mix_effect": "Change attributable to service/site mix shifts.",
}


@dataclass(frozen=True)
class StrategySpec:
    mechanism: str
    engine_id: str
    calculation_family: str  # UTILIZATION | REIMBURSEMENT | COVERAGE | BLOCKED
    calculation_version: str
    required_fields: Sequence[str]
    supports_whatif: bool
    notes: str = ""


# Available claim fields for demo synthetic substrate (claims_lines)
AVAILABLE_CLAIM_FIELDS: Set[str] = {
    "claim_id",
    "claim_line_id",
    "cpt_code",
    "hcpcs_code",
    "allowed_amount",
    "paid_amount",
    "units",
    "place_of_service",
    "facility_type",
    "service_date",
    "member_id",
    "provider_id",
    "lob",
}


def _strategies() -> Dict[str, StrategySpec]:
    return {
        "UTILIZATION_MANAGEMENT": StrategySpec(
            mechanism="UTILIZATION_MANAGEMENT",
            engine_id="um_elasticity_v1",
            calculation_family="UTILIZATION",
            calculation_version="um-elasticity-v1",
            required_fields=("cpt_code", "service_date", "allowed_amount", "paid_amount", "units"),
            supports_whatif=True,
            notes="MRI-style utilization / cost elasticity path.",
        ),
        "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION": StrategySpec(
            mechanism="MULTIPLE_PROCEDURE_PAYMENT_REDUCTION",
            engine_id="reimbursement_mppr_v1",
            calculation_family="REIMBURSEMENT",
            calculation_version="reimbursement-mppr-v1",
            required_fields=("claim_id", "claim_line_id", "cpt_code", "allowed_amount", "units"),
            supports_whatif=True,
            notes="MPPR secondary % of allowed; volume held constant.",
        ),
        "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL": StrategySpec(
            mechanism="SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
            engine_id="reimbursement_sos_v1",
            calculation_family="REIMBURSEMENT",
            calculation_version="reimbursement-sos-v1",
            required_fields=(
                "claim_line_id",
                "cpt_code",
                "allowed_amount",
                "place_of_service",
                "units",
            ),
            supports_whatif=True,
            notes="Hospital outpatient paid at reduced % of allowed vs freestanding.",
        ),
        "FEE_SCHEDULE_UNIT_PRICE": StrategySpec(
            mechanism="FEE_SCHEDULE_UNIT_PRICE",
            engine_id="reimbursement_fee_schedule_v1",
            calculation_family="REIMBURSEMENT",
            calculation_version="reimbursement-fee-schedule-v1",
            required_fields=("cpt_code", "allowed_amount", "units"),
            supports_whatif=True,
            notes="Unit allowed/price adjustment; not yet seeded as FULLY_VALIDATED_DEMO.",
        ),
        "CODING_EDIT_MODIFIER": StrategySpec(
            mechanism="CODING_EDIT_MODIFIER",
            engine_id="blocked_modifiers_missing",
            calculation_family="BLOCKED",
            calculation_version="blocked-v1",
            required_fields=("cpt_code", "modifier", "units"),
            supports_whatif=False,
            notes="Blocked on empirical claims_lines (no modifier column). Dec4 expansion PTP uses fixture engine via metadata stamp.",
        ),
        # Fixture-backed Dec 4 expansion PTP (not empirical claims_lines)
        "NCCI_PTP_FIXTURE": StrategySpec(
            mechanism="NCCI_PTP_FIXTURE",
            engine_id="reimbursement_ncci_ptp_v1",
            calculation_family="REIMBURSEMENT",
            calculation_version="reimbursement-ncci-ptp-v1",
            required_fields=("cpt_code", "allowed_amount", "units"),
            supports_whatif=True,
            notes="Synthetic known-answer PTP with modifier-indicator semantics; not a live quarterly CMS file.",
        ),
        "DENIAL_ADJUSTMENT": StrategySpec(
            mechanism="DENIAL_ADJUSTMENT",
            engine_id="blocked_denials_missing",
            calculation_family="BLOCKED",
            calculation_version="blocked-v1",
            required_fields=("claim_status", "denial_reason", "adjustment_amount"),
            supports_whatif=False,
            notes="Blocked: denial/adjustment/status columns absent.",
        ),
        "COVERAGE_DETERMINATION": StrategySpec(
            mechanism="COVERAGE_DETERMINATION",
            engine_id="coverage_criteria_v1",
            calculation_family="COVERAGE",
            calculation_version="coverage-criteria-v1",
            required_fields=("cpt_code", "service_date", "allowed_amount", "units"),
            supports_whatif=True,
            notes="NCD/LCD-linked coverage criteria; mechanical unit/necessity rules when configured.",
        ),
    }


def resolve_mechanism(
    *,
    policy_type: Optional[str] = None,
    policy_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    policy_id: Optional[str] = None,
) -> str:
    """Resolve mechanism from versioned metadata first, then typed heuristics.

    Name matching is a last-resort hint only for known demo titles already stamped
    with mechanism in metadata after seed; prefer enterprise_classification.mechanism.
    """
    meta = metadata or {}
    ec = meta.get("enterprise_classification") or {}
    # Dec 4 expansion PTP: fixture engine (do not use BLOCKED empirical modifier path)
    if ec.get("dec4_expansion") and (
        str(ec.get("mechanism") or "").upper() == "CODING_EDIT_MODIFIER"
        or str(meta.get("mechanism") or "").upper() == "CODING_EDIT_MODIFIER"
    ):
        return "NCCI_PTP_FIXTURE"
    if ec.get("sub_mechanism") == "NCCI_PTP" or meta.get("sub_mechanism") == "NCCI_PTP":
        return "NCCI_PTP_FIXTURE"

    explicit = (
        ec.get("mechanism")
        or meta.get("analytical_mechanism")
        or meta.get("mechanism")
    )
    if explicit:
        return str(explicit).upper()

    # Versioned strategy stamp from seed
    stamp = meta.get("analytical_strategy") or {}
    if isinstance(stamp, dict) and stamp.get("mechanism"):
        mech = str(stamp["mechanism"]).upper()
        if mech == "CODING_EDIT_MODIFIER" and (
            ec.get("dec4_expansion") or stamp.get("engine_id") == "reimbursement_ncci_ptp_v1"
        ):
            return "NCCI_PTP_FIXTURE"
        return mech

    t = (policy_type or "").upper()
    n = (policy_name or "").upper()

    # Name-based reimbursement demos before SITE_OF_CARE → UM (site-of-care UM ≠ SOS payment)
    if "MPPR" in n or "MULTIPLE PROCEDURE PAYMENT" in n:
        return "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION"
    if "INFUSION" in n and ("SITE" in n or "SOC" in n or "CARE" in n):
        return "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL"
    if (
        "FREESTANDING" in n
        or "SITE OF SERVICE" in n
        or "PAYMENT DIFFERENTIAL" in n
        or ("SITE" in n and "PAYMENT" in n)
        or ("SITE" in t and "PAYMENT" in n)
    ):
        return "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL"

    if "NCCI" in n and "MUE" in n:
        return "FEE_SCHEDULE_UNIT_PRICE"
    if "NCCI" in n and ("PTP" in n or "PROCEDURE-TO-PROCEDURE" in n or "BUNDL" in n):
        # Name-only without expansion stamp → keep empirical BLOCKED path honest
        if ec.get("dec4_expansion"):
            return "NCCI_PTP_FIXTURE"
        return "CODING_EDIT_MODIFIER"
    if "COVERAGE" in t or "NCD" in n or "LCD" in n or "THERAPY COVERAGE" in n:
        return "COVERAGE_DETERMINATION"

    if any(k in t for k in ("PRIOR_AUTH", "UM", "MEDICAL_NECESSITY", "SITE_OF_CARE", "STEP")):
        return "UTILIZATION_MANAGEMENT"
    if "MRI" in n and ("PRIOR" in n or "AUTH" in n or t == "PRIOR_AUTH"):
        return "UTILIZATION_MANAGEMENT"
    if any(k in t for k in ("PAYMENT_POLICY", "REIMBURSEMENT", "CODING", "FEE")):
        if "MODIFIER" in n or "NCCI" in n or "CODING" in t:
            return "CODING_EDIT_MODIFIER"
        if "FEE" in n or "FEE_SCHEDULE" in t or "REIMBURSEMENT_METHODOLOGY" in t:
            return "FEE_SCHEDULE_UNIT_PRICE"
        # Unspecified payment policy — do NOT default to UM elasticity
        return "FEE_SCHEDULE_UNIT_PRICE"
    return "UTILIZATION_MANAGEMENT"


def validate_required_fields(required: Sequence[str]) -> Dict[str, Any]:
    missing = [f for f in required if f not in AVAILABLE_CLAIM_FIELDS]
    return {
        "ok": len(missing) == 0,
        "missing_fields": missing,
        "available_claim_fields_sample": sorted(AVAILABLE_CLAIM_FIELDS),
    }


def get_strategy(mechanism: str) -> StrategySpec:
    specs = _strategies()
    key = (mechanism or "").upper()
    if key not in specs:
        raise KeyError(f"Unknown analytical mechanism: {mechanism}")
    return specs[key]


def resolve_strategy(
    *,
    policy_type: Optional[str] = None,
    policy_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    policy_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Full resolve + data-field gate + dispatch decision."""
    mechanism = resolve_mechanism(
        policy_type=policy_type,
        policy_name=policy_name,
        metadata=metadata,
        policy_id=policy_id,
    )
    try:
        spec = get_strategy(mechanism)
    except KeyError as e:
        return {
            "registry_version": REGISTRY_VERSION,
            "mechanism": mechanism,
            "dispatch": "REJECTED",
            "reason": str(e),
            "sign_convention": PAYMENT_SIGN_CONVENTION,
        }

    field_gate = validate_required_fields(spec.required_fields)
    if spec.calculation_family == "BLOCKED" or not field_gate["ok"]:
        return {
            "registry_version": REGISTRY_VERSION,
            "mechanism": mechanism,
            "engine_id": spec.engine_id,
            "calculation_family": spec.calculation_family,
            "calculation_version": spec.calculation_version,
            "dispatch": "REJECTED_UNSUPPORTED",
            "supports_whatif": False,
            "field_gate": field_gate,
            "notes": spec.notes,
            "sign_convention": PAYMENT_SIGN_CONVENTION,
            "forbid_utilization_elasticity": spec.calculation_family == "REIMBURSEMENT"
            or spec.calculation_family == "BLOCKED",
        }

    return {
        "registry_version": REGISTRY_VERSION,
        "mechanism": mechanism,
        "engine_id": spec.engine_id,
        "calculation_family": spec.calculation_family,
        "calculation_version": spec.calculation_version,
        "dispatch": "ENGINE",
        "supports_whatif": spec.supports_whatif,
        "field_gate": field_gate,
        "notes": spec.notes,
        "sign_convention": PAYMENT_SIGN_CONVENTION,
        "forbid_utilization_elasticity": spec.calculation_family == "REIMBURSEMENT",
    }


def list_strategies() -> List[Dict[str, Any]]:
    return [
        {
            "mechanism": s.mechanism,
            "engine_id": s.engine_id,
            "calculation_family": s.calculation_family,
            "calculation_version": s.calculation_version,
            "required_fields": list(s.required_fields),
            "supports_whatif": s.supports_whatif,
            "notes": s.notes,
        }
        for s in _strategies().values()
    ]
