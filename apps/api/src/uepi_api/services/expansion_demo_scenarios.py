"""P0 Dec 4 expansion scenarios — synthetic known-answer engines + policy IDs.

Frozen MRI/MPPR/SOS remain untouched. New scenarios are separately gated.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Sequence
from uuid import UUID, uuid5, NAMESPACE_URL

# Stable demo UUIDs (uuid5 of names) — do not collide with frozen three
PTP_POLICY_ID = str(uuid5(NAMESPACE_URL, "healthforesight:demo:ncci-ptp-bundling"))
MUE_POLICY_ID = str(uuid5(NAMESPACE_URL, "healthforesight:demo:ncci-mue-units"))
THERAPY_POLICY_ID = str(uuid5(NAMESPACE_URL, "healthforesight:demo:op-therapy-coverage"))
INFUSION_SOC_POLICY_ID = str(uuid5(NAMESPACE_URL, "healthforesight:demo:infusion-site-of-care"))
NCD_COVERAGE_POLICY_ID = str(uuid5(NAMESPACE_URL, "healthforesight:demo:ncd-mri-coverage-study"))
LCD_COVERAGE_POLICY_ID = str(uuid5(NAMESPACE_URL, "healthforesight:demo:lcd-jm-mri-coverage-study"))

# Standard product names — "(Demo)" is not part of the policy identity.
# Honesty lives in catalog_class / enterprise_classification, not the title.
PTP_NAME = "NCCI Procedure-to-Procedure Bundling"
MUE_NAME = "NCCI Medically Unlikely Units"
THERAPY_NAME = "Outpatient Therapy Coverage and Payment"
INFUSION_NAME = "Infusion Site-of-Care Optimization"
NCD_COV_NAME = "NCD 220.2 MRI Coverage Change Study"
LCD_COV_NAME = "LCD L34425 NC MRI Coverage Criteria"


# --- NCCI PTP mechanical engine -------------------------------------------------

PTP_CALC_VERSION = "reimbursement-ncci-ptp-v1"
# modifier_indicator semantics (CMS NCCI):
#   0 = not allowed even with modifier
#   1 = allowed if clinically appropriate modifier present (e.g. 59/XE/XP/XS/XU)
#   9 = not applicable
PTP_MODIFIER_INDICATOR = "1"

PTP_KNOWN_LINES = [
    # Claim A: column1+column2, no modifier → column2 denied
    {"claim_id": "ptp1", "claim_line_id": "ptp1a", "cpt_code": "70553", "allowed_amount": 800.0, "units": 1, "role": "column_one", "modifier": None},
    {"claim_id": "ptp1", "claim_line_id": "ptp1b", "cpt_code": "70551", "allowed_amount": 400.0, "units": 1, "role": "column_two", "modifier": None},
    # Claim B: same pair, no modifier → deny
    {"claim_id": "ptp2", "claim_line_id": "ptp2a", "cpt_code": "70553", "allowed_amount": 800.0, "units": 1, "role": "column_one", "modifier": None},
    {"claim_id": "ptp2", "claim_line_id": "ptp2b", "cpt_code": "70551", "allowed_amount": 400.0, "units": 1, "role": "column_two", "modifier": None},
    # Claim C: column1 only
    {"claim_id": "ptp3", "claim_line_id": "ptp3a", "cpt_code": "70553", "allowed_amount": 800.0, "units": 1, "role": "column_one_only", "modifier": None},
    # Claim D: pair WITH appropriate modifier under indicator 1 → column2 paid (bypass)
    {"claim_id": "ptp4", "claim_line_id": "ptp4a", "cpt_code": "70553", "allowed_amount": 800.0, "units": 1, "role": "column_one", "modifier": None},
    {"claim_id": "ptp4", "claim_line_id": "ptp4b", "cpt_code": "70551", "allowed_amount": 400.0, "units": 1, "role": "column_two", "modifier": "59"},
]


def apply_ncci_ptp(
    lines: Sequence[Mapping[str, Any]],
    *,
    modifier_indicator: str = PTP_MODIFIER_INDICATOR,
) -> Dict[str, Any]:
    """Mechanical PTP with modifier-indicator semantics (demo).

    indicator 1 + appropriate modifier on column_two → pay both.
    indicator 0 → always deny column_two when paired.
    """
    by_claim: Dict[str, List[Mapping[str, Any]]] = {}
    for raw in lines:
        by_claim.setdefault(str(raw.get("claim_id")), []).append(raw)

    baseline = 0.0
    post = 0.0
    pairs_hit = 0
    pairs_bypassed = 0
    out_lines: List[Dict[str, Any]] = []
    appropriate_modifiers = {"59", "XE", "XP", "XS", "XU"}

    for cid, clines in by_claim.items():
        roles = {str(x.get("role")) for x in clines}
        hit = "column_one" in roles and "column_two" in roles
        if hit:
            pairs_hit += 1
        col2_mod = None
        for x in clines:
            if str(x.get("role")) == "column_two":
                col2_mod = (str(x.get("modifier") or "").strip().upper() or None)
        bypass = (
            hit
            and modifier_indicator == "1"
            and col2_mod in appropriate_modifiers
        )
        if bypass:
            pairs_bypassed += 1
        for raw in clines:
            allowed = float(raw.get("allowed_amount") or 0)
            baseline += allowed
            role = str(raw.get("role") or "")
            deny = hit and (not bypass) and role == "column_two" and modifier_indicator in ("0", "1")
            paid = 0.0 if deny else allowed
            post += paid
            out_lines.append(
                {
                    "claim_id": cid,
                    "claim_line_id": raw.get("claim_line_id"),
                    "cpt_code": raw.get("cpt_code"),
                    "role": role,
                    "modifier": raw.get("modifier"),
                    "modifier_indicator": modifier_indicator,
                    "baseline_paid": allowed,
                    "post_policy_paid": paid,
                    "edit_applied": deny,
                    "modifier_bypass": bypass and role == "column_two",
                }
            )
    impact = round(baseline - post, 2)
    return {
        "calculation_version": PTP_CALC_VERSION,
        "mechanism": "CODING_EDIT_MODIFIER",
        "sub_mechanism": "NCCI_PTP",
        "catalog_class": "DEMO_SYNTHETIC",
        "modifier_semantics": {
            "indicator": modifier_indicator,
            "indicator_meaning": {
                "0": "Not allowed even with modifier",
                "1": "Allowed with clinically appropriate modifier",
                "9": "Modifier not applicable",
            }.get(modifier_indicator, "unknown"),
            "appropriate_modifiers_demo": sorted(appropriate_modifiers),
        },
        "totals": {
            "baseline_paid": round(baseline, 2),
            "post_policy_paid": round(post, 2),
            "payment_impact": impact,
            "payer_savings": impact,
            "provider_payment_change": round(-impact, 2),
            "ptp_pairs_hit": pairs_hit,
            "ptp_pairs_bypassed_with_modifier": pairs_bypassed,
            "volume_effect": 0.0,
            "mix_effect": 0.0,
            "price_effect": impact,
        },
        "lines": out_lines,
        "effect_layers": {
            "mechanical_payment_effect": impact,
            "predicted_behavioral_effect": None,
            "observed_descriptive_effect": None,
            "causal_effect": None,
            "note": "Mechanical ≠ causal. Causal status assessed separately; estimation remains eligible.",
        },
    }


def verify_ptp_known_answer() -> Dict[str, Any]:
    # Claims 1–2 deny $400 each = $800; claim3 unchanged; claim4 modifier bypass keeps $400
    # baseline = 800+400+800+400+800+800+400 = 4400
    # post = 800+0+800+0+800+800+400 = 3600; impact=800
    calc = apply_ncci_ptp(PTP_KNOWN_LINES)
    t = calc["totals"]
    checks = {
        "baseline_paid": t["baseline_paid"] == 4400.0,
        "post_policy_paid": t["post_policy_paid"] == 3600.0,
        "payment_impact": t["payment_impact"] == 800.0,
        "ptp_pairs_hit": t["ptp_pairs_hit"] == 3,
        "modifier_bypass": t["ptp_pairs_bypassed_with_modifier"] == 1,
    }
    return {"passed": all(checks.values()), "checks": checks, "actual_totals": t, "calculation_version": PTP_CALC_VERSION}


# --- NCCI MUE mechanical engine -------------------------------------------------

MUE_CALC_VERSION = "reimbursement-ncci-mue-v1"
MUE_KNOWN_LINES = [
    {"claim_line_id": "m1", "cpt_code": "97110", "units": 6, "allowed_per_unit": 50.0},
    {"claim_line_id": "m2", "cpt_code": "97110", "units": 3, "allowed_per_unit": 50.0},
    {"claim_line_id": "m3", "cpt_code": "97110", "units": 4, "allowed_per_unit": 50.0},
]
DEMO_MUE_VALUE = 4


def apply_ncci_mue(
    lines: Sequence[Mapping[str, Any]],
    *,
    mue_value: int = DEMO_MUE_VALUE,
) -> Dict[str, Any]:
    """Mechanical MUE: units above mue_value unpaid (demo MAI-style hard limit)."""
    baseline = 0.0
    post = 0.0
    capped = 0
    out = []
    for raw in lines:
        units = float(raw.get("units") or 0)
        apu = float(raw.get("allowed_per_unit") or raw.get("allowed_amount") or 0)
        if "allowed_per_unit" not in raw and raw.get("allowed_amount") and units:
            apu = float(raw["allowed_amount"]) / units
        pre = units * apu
        allowed_units = min(units, float(mue_value))
        paid = allowed_units * apu
        if units > mue_value:
            capped += 1
        baseline += pre
        post += paid
        out.append(
            {
                "claim_line_id": raw.get("claim_line_id"),
                "cpt_code": raw.get("cpt_code"),
                "units": units,
                "mue_value": mue_value,
                "units_paid": allowed_units,
                "baseline_paid": round(pre, 2),
                "post_policy_paid": round(paid, 2),
            }
        )
    impact = round(baseline - post, 2)
    return {
        "calculation_version": MUE_CALC_VERSION,
        "mechanism": "FEE_SCHEDULE_UNIT_PRICE",
        "sub_mechanism": "NCCI_MUE",
        "catalog_class": "DEMO_SYNTHETIC",
        "totals": {
            "baseline_paid": round(baseline, 2),
            "post_policy_paid": round(post, 2),
            "payment_impact": impact,
            "payer_savings": impact,
            "provider_payment_change": round(-impact, 2),
            "lines_capped": capped,
            "mue_value": mue_value,
            "volume_effect": 0.0,
            "price_effect": impact,
        },
        "lines": out,
        "effect_layers": {
            "mechanical_payment_effect": impact,
            "causal_effect": None,
            "note": "Synthetic MUE value — not an unpublished CMS confidential figure claimed as authoritative.",
        },
    }


def verify_mue_known_answer() -> Dict[str, Any]:
    # m1: 6→4 units @50 = save 100; m2: 3 ok; m3: 4 ok → impact 100
    calc = apply_ncci_mue(MUE_KNOWN_LINES)
    t = calc["totals"]
    checks = {
        "baseline_paid": t["baseline_paid"] == 650.0,
        "post_policy_paid": t["post_policy_paid"] == 550.0,
        "payment_impact": t["payment_impact"] == 100.0,
        "lines_capped": t["lines_capped"] == 1,
    }
    return {"passed": all(checks.values()), "checks": checks, "actual_totals": t, "calculation_version": MUE_CALC_VERSION}


# --- Outpatient therapy (coverage + unit payment hybrid) -----------------------

THERAPY_CALC_VERSION = "coverage-therapy-v1"
THERAPY_KNOWN = [
    {"claim_line_id": "t1", "cpt_code": "97110", "units": 5, "allowed_per_unit": 40.0, "medically_necessary_units": 3},
    {"claim_line_id": "t2", "cpt_code": "97140", "units": 4, "allowed_per_unit": 35.0, "medically_necessary_units": 4},
    {"claim_line_id": "t3", "cpt_code": "97110", "units": 2, "allowed_per_unit": 40.0, "medically_necessary_units": 2},
]


def apply_therapy_coverage(lines: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Pay only medically_necessary_units (synthetic coverage frequency rule)."""
    baseline = post = 0.0
    out = []
    for raw in lines:
        units = float(raw.get("units") or 0)
        apu = float(raw.get("allowed_per_unit") or 0)
        nec = float(raw.get("medically_necessary_units") or units)
        pre = units * apu
        paid = min(units, nec) * apu
        baseline += pre
        post += paid
        out.append({**dict(raw), "baseline_paid": round(pre, 2), "post_policy_paid": round(paid, 2)})
    impact = round(baseline - post, 2)
    return {
        "calculation_version": THERAPY_CALC_VERSION,
        "mechanism": "COVERAGE_DETERMINATION",
        "catalog_class": "DEMO_SYNTHETIC",
        "totals": {
            "baseline_paid": round(baseline, 2),
            "post_policy_paid": round(post, 2),
            "payment_impact": impact,
            "payer_savings": impact,
            "provider_payment_change": round(-impact, 2),
        },
        "lines": out,
        "linked_medicare_hint": {
            "prefer_lcd_articles_for_codes": True,
            "note": "Therapy LCD/article codes should come from verified MCD articles when activated.",
        },
    }


def verify_therapy_known_answer() -> Dict[str, Any]:
    # t1: 5→3 @40 = save 80; t2/t3 unchanged → impact 80
    # baseline 5*40+4*35+2*40 = 200+140+80=420; post 3*40+4*35+2*40=120+140+80=340
    calc = apply_therapy_coverage(THERAPY_KNOWN)
    t = calc["totals"]
    checks = {
        "baseline_paid": t["baseline_paid"] == 420.0,
        "post_policy_paid": t["post_policy_paid"] == 340.0,
        "payment_impact": t["payment_impact"] == 80.0,
    }
    return {"passed": all(checks.values()), "checks": checks, "actual_totals": t}


# --- Infusion site-of-care -----------------------------------------------------

INFUSION_CALC_VERSION = "reimbursement-infusion-soc-v1"
INFUSION_KNOWN = [
    {"claim_line_id": "i1", "drug": "infliximab_demo", "site": "HOPD", "allowed_amount": 5000.0},
    {"claim_line_id": "i2", "drug": "infliximab_demo", "site": "HOPD", "allowed_amount": 5000.0},
    {"claim_line_id": "i3", "drug": "infliximab_demo", "site": "ASC_OR_OFFICE", "allowed_amount": 3200.0},
    {"claim_line_id": "i4", "drug": "infliximab_demo", "site": "HOPD", "allowed_amount": 5000.0},
]
# Policy steers 2 of 3 HOPD to office rate 3200 → save (5000-3200)*2 = 3600 on steered; keep 1 HOPD
INFUSION_STEER_FRACTION = 2 / 3


def apply_infusion_soc(
    lines: Sequence[Mapping[str, Any]],
    *,
    office_allowed: float = 3200.0,
    steer_hopd_count: int = 2,
) -> Dict[str, Any]:
    baseline = post = 0.0
    steered = 0
    out = []
    hopd_seen = 0
    for raw in lines:
        allowed = float(raw.get("allowed_amount") or 0)
        site = str(raw.get("site") or "")
        baseline += allowed
        paid = allowed
        did_steer = False
        if site == "HOPD":
            hopd_seen += 1
            if hopd_seen <= steer_hopd_count:
                paid = office_allowed
                did_steer = True
                steered += 1
        post += paid
        out.append(
            {
                "claim_line_id": raw.get("claim_line_id"),
                "site": site,
                "baseline_paid": allowed,
                "post_policy_paid": paid,
                "steered": did_steer,
            }
        )
    impact = round(baseline - post, 2)
    return {
        "calculation_version": INFUSION_CALC_VERSION,
        "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
        "sub_mechanism": "INFUSION_SITE_OF_CARE",
        "catalog_class": "DEMO_SYNTHETIC",
        "totals": {
            "baseline_paid": round(baseline, 2),
            "post_policy_paid": round(post, 2),
            "payment_impact": impact,
            "payer_savings": impact,
            "provider_payment_change": round(-impact, 2),
            "episodes_steered": steered,
        },
        "lines": out,
        "effect_layers": {
            "mechanical_payment_effect": impact,
            "causal_effect": None,
            "note": "Steering assumption is synthetic; causal site-mix shift not estimated here.",
        },
    }


def verify_infusion_known_answer() -> Dict[str, Any]:
    # baseline 5000*3+3200=18200; post: 2 steered→3200, 1 HOPD 5000, 1 office 3200 = 3200*3+5000=14600; impact=3600
    calc = apply_infusion_soc(INFUSION_KNOWN)
    t = calc["totals"]
    checks = {
        "baseline_paid": t["baseline_paid"] == 18200.0,
        "post_policy_paid": t["post_policy_paid"] == 14600.0,
        "payment_impact": t["payment_impact"] == 3600.0,
        "episodes_steered": t["episodes_steered"] == 2,
    }
    return {"passed": all(checks.values()), "checks": checks, "actual_totals": t}


def all_known_answer_suite() -> Dict[str, Any]:
    return {
        "ptp": verify_ptp_known_answer(),
        "mue": verify_mue_known_answer(),
        "therapy": verify_therapy_known_answer(),
        "infusion": verify_infusion_known_answer(),
    }


def _nc_scope(*, procedure_codes: List[str], service_categories: List[str], **extra: Any) -> Dict[str, Any]:
    scope = {
        "lob": ["COMMERCIAL", "MA", "MEDICAID"],
        "states": ["NC"],
        "markets": ["NC"],
        "network": ["IN"],
        "applies_to_all": False,
        "procedure_codes": procedure_codes,
        "service_categories": service_categories,
        "plans": None,
        "regions": None,
    }
    scope.update(extra)
    return scope


def policy_definition(sc: Dict[str, Any]) -> Dict[str, Any]:
    """Complete standard policy structure (scope / levers / assumptions / guardrails)."""
    pid = sc["policy_id"]
    name = sc["name"]
    mech = sc["mechanism"]

    if pid == PTP_POLICY_ID:
        return {
            "description": (
                "Applies NCCI procedure-to-procedure bundling edits with modifier-indicator "
                "semantics (indicator 1 allows clinically appropriate modifiers such as 59/X{E,P,S,U}). "
                "Representative Payer coding-integrity policy for NC markets."
            ),
            "domain": "Payment",
            "subdomain": "Coding integrity",
            "jurisdiction": "NC",
            "standards_basis": [
                "CMS National Correct Coding Initiative (NCCI) PTP edit framework",
                "Modifier indicator 0/1/9 semantics",
            ],
            "scope": _nc_scope(
                procedure_codes=["70553", "70551"],
                service_categories=["ADVANCED_IMAGING"],
            ),
            "enforcement": {
                "mechanism": "HARD",
                "touchpoint": ["CLAIM_EDIT"],
                "override_allowed": True,
                "override_requires": "clinically_appropriate_modifier",
            },
            "policy_levers": [
                {
                    "lever_type": "CODING_EDIT",
                    "targets": {"code_type": "CPT", "codes": ["70553", "70551"]},
                    "parameters": {
                        "edit_type": "NCCI_PTP",
                        "column_one": "70553",
                        "column_two": "70551",
                        "modifier_indicator": "1",
                        "appropriate_modifiers": ["59", "XE", "XP", "XS", "XU"],
                    },
                }
            ],
            "assumptions": [
                {
                    "assumption_type": "COST",
                    "description": "Column-two denial under PTP reduces paid amount when no appropriate modifier is present",
                    "value": "price_effect_only",
                    "confidence": 0.9,
                    "source": "NCCI PTP mechanical known-answer fixture",
                },
                {
                    "assumption_type": "UTILIZATION",
                    "description": "Volume held constant — PTP is a payment edit, not utilization management",
                    "value": "0",
                    "confidence": 0.95,
                    "source": "Analytical strategy registry",
                },
                {
                    "assumption_type": "BEHAVIOR",
                    "description": "Some claims will bypass via clinically appropriate modifiers under indicator 1",
                    "value": "modifier_bypass_eligible",
                    "confidence": 0.7,
                    "source": "NCCI modifier-indicator guidance",
                },
            ],
            "guardrails": [
                {
                    "metric_name": "ptp_pair_hit_rate",
                    "threshold_type": "max",
                    "threshold_value": 0.35,
                    "action": "alert",
                    "description": "Alert if PTP pair hit rate exceeds 35% of eligible imaging claims",
                },
                {
                    "metric_name": "modifier_bypass_rate",
                    "threshold_type": "max",
                    "threshold_value": 0.50,
                    "action": "alert",
                    "description": "Alert if modifier-59/X{E,P,S,U} bypass exceeds 50% of PTP hits",
                },
                {
                    "metric_name": "payment_impact_pct",
                    "threshold_type": "max",
                    "threshold_value": 25.0,
                    "action": "alert",
                    "description": "Alert if payer savings exceed 25% of baseline paid on PTP-eligible claims",
                },
            ],
            "codes": [("CPT", "70553", "MRI_BRAIN"), ("CPT", "70551", "MRI_BRAIN")],
        }

    if pid == MUE_POLICY_ID:
        return {
            "description": (
                "Applies NCCI Medically Unlikely Edits (MUE) unit caps at the claim-line level. "
                "Synthetic published-style MUE value used for known-answer validation until "
                "authorized quarterly MUE files are reconciled."
            ),
            "domain": "Payment",
            "subdomain": "Coding integrity",
            "jurisdiction": "NC",
            "standards_basis": [
                "CMS NCCI Medically Unlikely Edits framework",
                "MUE adjudication indicator semantics",
            ],
            "scope": _nc_scope(
                procedure_codes=["97110"],
                service_categories=["THERAPY", "OUTPATIENT"],
            ),
            "enforcement": {
                "mechanism": "HARD",
                "touchpoint": ["CLAIM_EDIT"],
                "override_allowed": False,
            },
            "policy_levers": [
                {
                    "lever_type": "UNIT_LIMIT",
                    "targets": {"code_type": "CPT", "codes": ["97110"]},
                    "parameters": {
                        "edit_type": "NCCI_MUE",
                        "mue_value": 4,
                        "mue_adjudication_indicator": "2",
                        "synthetic_mue": True,
                    },
                }
            ],
            "assumptions": [
                {
                    "assumption_type": "COST",
                    "description": "Units above MUE are unpaid (hard MAI-style limit in fixture)",
                    "value": "unpaid_excess_units",
                    "confidence": 0.85,
                    "source": "NCCI MUE mechanical known-answer fixture",
                },
                {
                    "assumption_type": "DATA",
                    "description": "MUE value 4 for 97110 is SYNTHETIC — not asserted as live CMS confidential value",
                    "value": "4",
                    "confidence": 1.0,
                    "source": "Disclosed synthetic fixture",
                },
            ],
            "guardrails": [
                {
                    "metric_name": "mue_cap_rate",
                    "threshold_type": "max",
                    "threshold_value": 0.20,
                    "action": "alert",
                    "description": "Alert if more than 20% of 97110 lines are MUE-capped",
                },
                {
                    "metric_name": "avg_units_per_line",
                    "threshold_type": "max",
                    "threshold_value": 8.0,
                    "action": "alert",
                    "description": "Alert if average billed units per 97110 line exceed 8",
                },
            ],
            "codes": [("CPT", "97110", "THERAPY")],
        }

    if pid == THERAPY_POLICY_ID:
        return {
            "description": (
                "Outpatient physical therapy coverage and payment rules aligned to Palmetto JM "
                "LCD L34428 (Outpatient Physical Therapy). Pays only medically necessary units "
                "under the configured coverage frequency rule."
            ),
            "domain": "Coverage",
            "subdomain": "Outpatient therapy",
            "jurisdiction": "NC",
            "standards_basis": [
                "Palmetto GBA Jurisdiction M LCD L34428",
                "Medicare outpatient therapy coverage principles",
            ],
            "scope": _nc_scope(
                procedure_codes=["97110", "97140"],
                service_categories=["THERAPY", "OUTPATIENT"],
            ),
            "enforcement": {
                "mechanism": "HARD",
                "touchpoint": ["CLAIM_EDIT", "PA_WORKFLOW"],
                "override_allowed": True,
            },
            "policy_levers": [
                {
                    "lever_type": "COVERAGE_CRITERIA",
                    "targets": {"code_type": "CPT", "codes": ["97110", "97140"]},
                    "parameters": {
                        "lcd_id": "L34428",
                        "pay_medically_necessary_units_only": True,
                    },
                }
            ],
            "assumptions": [
                {
                    "assumption_type": "UTILIZATION",
                    "description": "Units billed above medically necessary threshold are non-payable",
                    "value": "medically_necessary_units_cap",
                    "confidence": 0.8,
                    "source": "Coverage frequency known-answer fixture",
                },
                {
                    "assumption_type": "COST",
                    "description": "Payment impact is price/unit effect with volume of necessary units held",
                    "value": "price_effect_only",
                    "confidence": 0.85,
                    "source": "coverage-therapy-v1",
                },
            ],
            "guardrails": [
                {
                    "metric_name": "therapy_units_denied_pct",
                    "threshold_type": "max",
                    "threshold_value": 40.0,
                    "action": "alert",
                    "description": "Alert if >40% of therapy units are denied as not medically necessary",
                },
                {
                    "metric_name": "member_access_complaints",
                    "threshold_type": "max",
                    "threshold_value": 25.0,
                    "action": "alert",
                    "description": "Alert if therapy access complaints exceed threshold",
                },
            ],
            "codes": [("CPT", "97110", "THERAPY"), ("CPT", "97140", "THERAPY")],
        }

    if pid == INFUSION_SOC_POLICY_ID:
        return {
            "description": (
                "Steers eligible specialty infusion episodes from hospital outpatient (HOPD) "
                "to lower-cost ASC/office sites when clinically appropriate."
            ),
            "domain": "Payment",
            "subdomain": "Site of care",
            "jurisdiction": "NC",
            "standards_basis": [
                "Payer site-of-care optimization common practice",
                "Hospital outpatient vs freestanding/office differential payment",
            ],
            "scope": _nc_scope(
                procedure_codes=[],
                service_categories=["INFUSION", "SPECIALTY_DRUG"],
                allowed_sites=["ASC_OR_OFFICE", "HOPD"],
            ),
            "enforcement": {
                "mechanism": "SOFT",
                "touchpoint": ["PA_WORKFLOW", "CARE_MANAGEMENT"],
                "override_allowed": True,
            },
            "policy_levers": [
                {
                    "lever_type": "SITE_OF_CARE",
                    "targets": {"code_groups": ["INFUSION_SPECIALTY"]},
                    "parameters": {
                        "preferred_sites": ["ASC_OR_OFFICE"],
                        "hospital_allowed_when": "clinical_exception",
                        "office_allowed_amount": 3200.0,
                    },
                }
            ],
            "assumptions": [
                {
                    "assumption_type": "COST",
                    "description": "HOPD to office steerage saves hospital−office differential per episode",
                    "value": "1800_per_steered_episode_fixture",
                    "confidence": 0.8,
                    "source": "Infusion SOC known-answer fixture",
                },
                {
                    "assumption_type": "QUALITY",
                    "description": "Quality outcomes maintained at preferred sites for eligible members",
                    "value": None,
                    "confidence": 0.7,
                    "source": "Site-of-care quality assumption",
                },
                {
                    "assumption_type": "BEHAVIOR",
                    "description": "Not all HOPD episodes are steerable; fixture steers 2 of 3 HOPD lines",
                    "value": "2/3",
                    "confidence": 0.75,
                    "source": "reimbursement-infusion-soc-v1",
                },
            ],
            "guardrails": [
                {
                    "metric_name": "site_of_care_redirect_rate",
                    "threshold_type": "min",
                    "threshold_value": 0.50,
                    "action": "alert",
                    "description": "Monitor successful infusion site-of-care redirections",
                },
                {
                    "metric_name": "hopd_infusion_share",
                    "threshold_type": "max",
                    "threshold_value": 0.40,
                    "action": "alert",
                    "description": "Alert if HOPD share of infusion episodes remains above 40%",
                },
            ],
            "codes": [],
        }

    if pid == NCD_COVERAGE_POLICY_ID:
        return {
            "description": (
                "Coverage change study keyed to CMS NCD 220.2 (Magnetic Resonance Imaging). "
                "Used for Medicare applicability / provenance analytics."
            ),
            "domain": "Coverage",
            "subdomain": "National coverage",
            "jurisdiction": "NATIONAL",
            "standards_basis": ["CMS NCD 220.2 Magnetic Resonance Imaging"],
            "scope": _nc_scope(
                procedure_codes=["70551", "70552", "70553", "72148", "72149", "72158"],
                service_categories=["ADVANCED_IMAGING"],
            ),
            "enforcement": {
                "mechanism": "HARD",
                "touchpoint": ["PA_WORKFLOW", "CLAIM_EDIT"],
                "override_allowed": False,
            },
            "policy_levers": [
                {
                    "lever_type": "COVERAGE_CRITERIA",
                    "targets": {
                        "code_type": "CPT",
                        "codes": ["70551", "70552", "70553", "72148", "72149", "72158"],
                    },
                    "parameters": {"ncd_id": "NCD220.2"},
                }
            ],
            "assumptions": [
                {
                    "assumption_type": "COVERAGE",
                    "description": "NCD 220.2 is the national Medicare coverage authority for MRI",
                    "value": "NCD220.2",
                    "confidence": 0.95,
                    "source": "CMS Coverage API national-coverage-ncd report",
                }
            ],
            "guardrails": [
                {
                    "metric_name": "noncovered_mri_claim_rate",
                    "threshold_type": "max",
                    "threshold_value": 0.05,
                    "action": "alert",
                    "description": "Alert if non-covered MRI claim rate exceeds 5%",
                }
            ],
            "codes": [
                ("CPT", "70551", "MRI"),
                ("CPT", "70552", "MRI"),
                ("CPT", "70553", "MRI"),
                ("CPT", "72148", "MRI"),
                ("CPT", "72149", "MRI"),
                ("CPT", "72158", "MRI"),
            ],
        }

    if pid == LCD_COVERAGE_POLICY_ID:
        return {
            "description": (
                "Local coverage criteria for MRI soft tissue of head and neck under Palmetto JM "
                "LCD L34425 with related billing/coding article A56729 (codes 70540/70542/70543)."
            ),
            "domain": "Coverage",
            "subdomain": "Local coverage",
            "jurisdiction": "NC",
            "standards_basis": [
                "Palmetto GBA Jurisdiction M LCD L34425",
                "Billing and Coding Article A56729",
            ],
            "scope": _nc_scope(
                procedure_codes=["70540", "70542", "70543"],
                service_categories=["ADVANCED_IMAGING"],
            ),
            "enforcement": {
                "mechanism": "HARD",
                "touchpoint": ["PA_WORKFLOW", "CLAIM_EDIT"],
                "override_allowed": False,
            },
            "policy_levers": [
                {
                    "lever_type": "COVERAGE_CRITERIA",
                    "targets": {"code_type": "CPT", "codes": ["70540", "70542", "70543"]},
                    "parameters": {"lcd_id": "L34425", "article_id": "A56729"},
                }
            ],
            "assumptions": [
                {
                    "assumption_type": "COVERAGE",
                    "description": "A56729 lists only 70540/70542/70543 — PARTIAL clinical match for broader MRI UM",
                    "value": "PARTIAL_CODE_OVERLAP",
                    "confidence": 0.95,
                    "source": "Coverage API article HCPCS enrichment",
                }
            ],
            "guardrails": [
                {
                    "metric_name": "lcd_denial_rate",
                    "threshold_type": "max",
                    "threshold_value": 0.15,
                    "action": "alert",
                    "description": "Alert if LCD L34425 denial rate exceeds 15%",
                }
            ],
            "codes": [
                ("CPT", "70540", "MRI_HEAD_NECK"),
                ("CPT", "70542", "MRI_HEAD_NECK"),
                ("CPT", "70543", "MRI_HEAD_NECK"),
            ],
        }

    return {
        "description": f"Representative Payer policy: {name}",
        "domain": "General",
        "subdomain": mech,
        "jurisdiction": "NC",
        "standards_basis": [],
        "scope": _nc_scope(procedure_codes=[], service_categories=[]),
        "enforcement": {"mechanism": "SOFT", "touchpoint": ["CLAIM_EDIT"], "override_allowed": True},
        "policy_levers": [],
        "assumptions": [],
        "guardrails": [],
        "codes": [],
    }


def scenario_catalog() -> List[Dict[str, Any]]:
    return [
        {
            "policy_id": PTP_POLICY_ID,
            "name": PTP_NAME,
            "policy_type": "CODING_AND_BILLING",
            "mechanism": "CODING_EDIT_MODIFIER",
            "medicare_links": [("ncci_ptp", "NCCI-PTP-PAIR-70553-70551", "USES_CODING_EDIT")],
            "known_answer": verify_ptp_known_answer(),
            "validation_target": "FULLY_VALIDATED_DEMO",
        },
        {
            "policy_id": MUE_POLICY_ID,
            "name": MUE_NAME,
            "policy_type": "CODING_AND_BILLING",
            "mechanism": "FEE_SCHEDULE_UNIT_PRICE",
            "medicare_links": [("ncci_mue", "NCCI-MUE-97110-DEMO", "USES_CODING_EDIT")],
            "known_answer": verify_mue_known_answer(),
            "validation_target": "FULLY_VALIDATED_DEMO",
        },
        {
            "policy_id": THERAPY_POLICY_ID,
            "name": THERAPY_NAME,
            "policy_type": "COVERAGE",
            "mechanism": "COVERAGE_DETERMINATION",
            "medicare_links": [("mac_lcd_nc", "L34428", "REFERENCES_LCD")],
            "known_answer": verify_therapy_known_answer(),
            "validation_target": "FULLY_VALIDATED_DEMO",
            "notes": (
                "Linked to verified Palmetto JM LCD L34428 (Outpatient Physical Therapy) "
                "from Coverage API NC catalog. Mechanical known-answer is synthetic units rule."
            ),
        },
        {
            "policy_id": INFUSION_SOC_POLICY_ID,
            "name": INFUSION_NAME,
            "policy_type": "SITE_OF_CARE",
            "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
            "medicare_links": [],
            "known_answer": verify_infusion_known_answer(),
            "validation_target": "FULLY_VALIDATED_DEMO",
        },
        {
            "policy_id": NCD_COVERAGE_POLICY_ID,
            "name": NCD_COV_NAME,
            "policy_type": "COVERAGE",
            "mechanism": "COVERAGE_DETERMINATION",
            "medicare_links": [("cms_ncd", "NCD220.2", "REFERENCES_NCD")],
            "known_answer": {"passed": True, "note": "Applicability/provenance scenario; financial known-answer N/A"},
            "validation_target": "PROVENANCE_VALIDATED",
        },
        {
            "policy_id": LCD_COVERAGE_POLICY_ID,
            "name": LCD_COV_NAME,
            "policy_type": "COVERAGE",
            "mechanism": "COVERAGE_DETERMINATION",
            "medicare_links": [
                ("mac_lcd_nc", "L34425", "REFERENCES_LCD"),
                ("lcd_billing_coding_articles", "A56729", "HAS_RELATED_ARTICLE"),
            ],
            "known_answer": {"passed": True, "note": "NC JM LCD provenance scenario"},
            "validation_target": "PROVENANCE_VALIDATED",
        },
    ]

def _ensure_demo_ncci_link_docs(db, tenant_id: UUID) -> List[Dict[str, Any]]:
    """Upsert DEMO_SYNTHETIC NCCI pair/MUE rows for expansion links.

    Full quarterly NCCI inventory remains ACCESS_BLOCKED separately — these rows are
    not promoted as authoritative public inventory.
    """
    from uepi_api.models.policy_source import PolicySourceDocument
    from uuid import uuid4

    stubs = [
        {
            "family_id": "ncci_ptp",
            "source_document_id": "NCCI-PTP-PAIR-70553-70551",
            "title": "Demo PTP pair 70553/70551 (synthetic edit illustration)",
            "source_version": "2024Q4-demo-subset",
            "authority": "CMS NCCI",
            "raw": {
                "catalog_class": "DEMO_SYNTHETIC",
                "column_one": "70553",
                "column_two": "70551",
                "modifier_indicator": "1",
                "verified": False,
            },
        },
        {
            "family_id": "ncci_mue",
            "source_document_id": "NCCI-MUE-97110-DEMO",
            "title": "Demo MUE for 97110 (synthetic published-style value)",
            "source_version": "2024Q4-demo-subset",
            "authority": "CMS NCCI",
            "raw": {
                "catalog_class": "DEMO_SYNTHETIC",
                "hcpcs": "97110",
                "mue_value": 4,
                "verified": False,
            },
        },
    ]
    out = []
    now = datetime.utcnow()
    for s in stubs:
        existing = (
            db.query(PolicySourceDocument)
            .filter(
                PolicySourceDocument.tenant_id == tenant_id,
                PolicySourceDocument.family_id == s["family_id"],
                PolicySourceDocument.source_document_id == s["source_document_id"],
            )
            .first()
        )
        if existing:
            existing.title = s["title"]
            existing.raw_payload_json = s["raw"]
            existing.updated_at = now
            out.append({"source_document_id": s["source_document_id"], "status": "updated"})
        else:
            db.add(
                PolicySourceDocument(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    family_id=s["family_id"],
                    authority=s["authority"],
                    source_document_id=s["source_document_id"],
                    source_version=s["source_version"],
                    title=s["title"],
                    program="ORIGINAL_MEDICARE_FFS",
                    raw_payload_json=s["raw"],
                    ingest_batch_id="demo-ncci-link-stubs",
                    created_at=now,
                    updated_at=now,
                )
            )
            out.append({"source_document_id": s["source_document_id"], "status": "created"})
    return out


def seed_expansion_policies(tenant_id: UUID) -> Dict[str, Any]:
    """Upsert expansion policies as complete standard policies + medicare links.

    Does not modify frozen MRI/MPPR/SOS IDs. Policies are first-class catalog
    objects (scope, levers, assumptions, guardrails). catalog_class remains
    DEMO_SYNTHETIC to disclose Representative Payer / fixture honesty — that is
    not a reason to omit workspace completeness.
    """
    from uuid import uuid4

    from uepi_api.database import SessionLocal
    from uepi_api.models.policy import (
        Policy,
        PolicyAssumption,
        PolicyCodeSet,
        PolicyGuardrail,
        PolicyVersion,
    )
    from uepi_api.models.policy_source import PolicySourceDocument, PolicySourceLink

    db = SessionLocal()
    created = []
    try:
        created.extend(_ensure_demo_ncci_link_docs(db, tenant_id))
        for sc in scenario_catalog():
            pid = UUID(sc["policy_id"])
            pol = db.query(Policy).filter(Policy.id == pid).one_or_none()
            definition = policy_definition(sc)
            ec_mech = sc["mechanism"]
            analytical_mech = (
                "NCCI_PTP_FIXTURE" if sc["mechanism"] == "CODING_EDIT_MODIFIER" else sc["mechanism"]
            )
            meta = {
                "policy_id": sc["policy_id"],
                "domain": definition["domain"],
                "subdomain": definition["subdomain"],
                "jurisdiction": definition["jurisdiction"],
                "standards_basis": definition["standards_basis"],
                "scope": definition["scope"],
                "enforcement": definition["enforcement"],
                "policy_levers": definition["policy_levers"],
                "assumptions": definition["assumptions"],
                "guardrails": definition["guardrails"],
                "apply_when": [],
                "global_exceptions": [],
                "effective_period": {
                    "start_date": "2024-01-01T00:00:00",
                    "end_date": None,
                },
                "enterprise_classification": {
                    "mechanism": ec_mech,
                    "sub_mechanism": (
                        "NCCI_PTP"
                        if sc["mechanism"] == "CODING_EDIT_MODIFIER"
                        else ("NCCI_MUE" if "MUE" in sc["name"].upper() else None)
                    ),
                    "catalog_class": "DEMO_SYNTHETIC",
                    "validation_target": sc["validation_target"],
                    "dec4_expansion": True,
                    "not_blue_cross_nc_proprietary": True,
                    "representative_payer": True,
                },
                "analytical_strategy": {
                    "mechanism": analytical_mech,
                    "engine_id": (
                        "reimbursement_ncci_ptp_v1"
                        if sc["mechanism"] == "CODING_EDIT_MODIFIER"
                        else None
                    ),
                },
                "display_label": "Representative Payer Policies",
            }
            now = datetime.utcnow()
            if pol is None:
                pol = Policy(
                    id=pid,
                    tenant_id=tenant_id,
                    name=sc["name"],
                    policy_type=sc["policy_type"],
                    status="ACTIVE",
                    description=definition["description"],
                    policy_metadata_json=meta,
                    created_at=now,
                    updated_at=now,
                )
                db.add(pol)
                created.append({"policy_id": sc["policy_id"], "status": "created", "name": sc["name"]})
            else:
                pol.name = sc["name"]
                pol.description = definition["description"]
                pol.policy_type = sc["policy_type"]
                pol.status = "ACTIVE"
                existing_meta = dict(pol.policy_metadata_json or {})
                existing_meta.update(meta)
                pol.policy_metadata_json = existing_meta
                pol.updated_at = now
                created.append({"policy_id": sc["policy_id"], "status": "completed", "name": sc["name"]})

            ver = (
                db.query(PolicyVersion)
                .filter(PolicyVersion.policy_id == pid, PolicyVersion.tenant_id == tenant_id)
                .order_by(PolicyVersion.version_number.desc())
                .first()
            )
            enf = definition.get("enforcement") or {}
            strength = "STRONG" if enf.get("mechanism") == "HARD" else "MODERATE"
            if ver is None:
                ver = PolicyVersion(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    policy_id=pid,
                    version_number=1,
                    effective_start_date=datetime(2024, 1, 1),
                    effective_end_date=None,
                    change_type="INITIAL",
                    enforcement_strength=strength,
                    justification="Initial complete expansion policy version",
                    version_metadata_json={
                        "catalog_class": "DEMO_SYNTHETIC",
                        "mechanism": sc["mechanism"],
                        "scope": definition["scope"],
                        "enforcement": definition["enforcement"],
                        "policy_levers": definition["policy_levers"],
                        "state": "ACTIVE",
                    },
                    created_at=now,
                    updated_at=now,
                )
                db.add(ver)
                db.flush()
                created.append({"policy_id": sc["policy_id"], "version": "v1_created"})
            else:
                ver.enforcement_strength = strength
                ver.justification = ver.justification or "Complete expansion policy version"
                vm = dict(ver.version_metadata_json or {})
                vm.update(
                    {
                        "catalog_class": "DEMO_SYNTHETIC",
                        "mechanism": sc["mechanism"],
                        "scope": definition["scope"],
                        "enforcement": definition["enforcement"],
                        "policy_levers": definition["policy_levers"],
                        "state": "ACTIVE",
                    }
                )
                ver.version_metadata_json = vm
                ver.updated_at = now

            # Replace code sets for this version
            db.query(PolicyCodeSet).filter(PolicyCodeSet.version_id == ver.id).delete()
            for code_type, code, group in definition.get("codes") or []:
                db.add(
                    PolicyCodeSet(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        version_id=ver.id,
                        code_type=code_type,
                        code=code,
                        code_group=group,
                        created_at=now,
                    )
                )

            # Replace assumptions / guardrails so policies are workspace-complete
            db.query(PolicyAssumption).filter(
                PolicyAssumption.tenant_id == tenant_id,
                PolicyAssumption.policy_id == pid,
            ).delete()
            for a in definition.get("assumptions") or []:
                db.add(
                    PolicyAssumption(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        policy_id=pid,
                        assumption_type=a["assumption_type"],
                        description=a.get("description"),
                        value=str(a["value"]) if a.get("value") is not None else None,
                        source=a.get("source"),
                        confidence=float(a.get("confidence") or 0.5),
                        created_at=now,
                        updated_at=now,
                    )
                )
            db.query(PolicyGuardrail).filter(
                PolicyGuardrail.tenant_id == tenant_id,
                PolicyGuardrail.policy_id == pid,
            ).delete()
            for g in definition.get("guardrails") or []:
                db.add(
                    PolicyGuardrail(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        policy_id=pid,
                        metric_name=g["metric_name"],
                        threshold_type=g["threshold_type"],
                        threshold_value=float(g["threshold_value"]),
                        action=g.get("action") or "alert",
                        description=g.get("description"),
                        triggered=False,
                        created_at=now,
                        updated_at=now,
                    )
                )

            for family, sid, role in sc.get("medicare_links") or []:
                doc = (
                    db.query(PolicySourceDocument)
                    .filter(
                        PolicySourceDocument.tenant_id == tenant_id,
                        PolicySourceDocument.family_id == family,
                        PolicySourceDocument.source_document_id == sid,
                    )
                    .order_by(PolicySourceDocument.created_at.desc())
                    .first()
                )
                if not doc:
                    created.append({"link": sid, "status": "source_missing"})
                    continue
                existing = (
                    db.query(PolicySourceLink)
                    .filter(
                        PolicySourceLink.policy_id == pid,
                        PolicySourceLink.source_document_id == doc.id,
                        PolicySourceLink.link_role == role,
                    )
                    .first()
                )
                if existing:
                    continue
                db.add(
                    PolicySourceLink(
                        tenant_id=tenant_id,
                        policy_id=pid,
                        source_document_id=doc.id,
                        link_role=role,
                        created_at=now,
                    )
                )
            created.append(
                {
                    "policy_id": sc["policy_id"],
                    "completeness": {
                        "assumptions": len(definition.get("assumptions") or []),
                        "guardrails": len(definition.get("guardrails") or []),
                        "codes": len(definition.get("codes") or []),
                        "has_scope": True,
                        "has_enforcement": True,
                        "has_levers": bool(definition.get("policy_levers")),
                    },
                }
            )
        db.commit()
        return {
            "seeded": created,
            "known_answers": all_known_answer_suite(),
            "catalog_class": "DEMO_SYNTHETIC",
            "policy_structure": "complete_standard",
            "frozen_policies_untouched": [
                "d403f101-08dd-45c9-ab83-d42e37c62018",
                "d0eeb370-df14-4478-8755-dad6c3a35a47",
                "d7441dd9-3bfe-405e-ae6c-0377204bbb7e",
            ],
        }
    finally:
        db.close()
