"""Resolve a versioned execution contract from a client policy definition.

A contract is executable only when the definition already contains the fields
the mechanism needs. Missing codes, unsigned clinical criteria, and missing
numeric parameters stay blocked.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

CONTRACT_VERSION = "mock-client-exec-v1"
NOT_CLAIMING = (
    "Synthetic mock-client configuration. Does not establish CMS, NCD, LCD, "
    "medical-necessity, or contracted payment authority."
)

VALIDATED_PAYMENT_KEYS = frozenset({"mppr", "sos", "ptp", "mue", "therapy", "infusion"})

CLINICAL_MECHANISMS = frozenset({
    "MEDICAL_NECESSITY_COVERAGE",
    "CLINICAL_PATHWAY",
    "MEDICARE_NCD_LCD_STUDY",
})
CLINICAL_FAMILIES = frozenset({
    "CLINICAL_CRITERIA",
    "MEDICAL_NECESSITY",
    "CLINICAL_PATHWAY",
    "EXPERIMENTAL_INVESTIGATIONAL",
})

# family -> (required configuration key, blocked reason)
PARAMETER_GATES = {
    "QUANTITY_LIMIT": ("quantity_limit_units", "MISSING_QUANTITY_LIMIT"),
    "DURATION_FREQUENCY_LIMIT": ("frequency_limit", "MISSING_FREQUENCY_LIMIT"),
    "COST_SHARING": ("member_cost_share_fraction", "MISSING_COST_SHARE_PARAMETER"),
    "PAYMENT_POLICY": ("allowed_reduction_fraction", "MISSING_PAYMENT_PARAMETER"),
    "REIMBURSEMENT_METHODOLOGY": ("allowed_reduction_fraction", "MISSING_PAYMENT_PARAMETER"),
    "EPISODE_BUNDLED_PAYMENT": ("episode_allowed_amount", "MISSING_EPISODE_PARAMETER"),
    "VALUE_BASED_PAYMENT": ("shared_savings_fraction", "MISSING_VALUE_BASED_PARAMETER"),
    "STEP_THERAPY": ("required_prior_step_codes", "MISSING_STEP_THERAPY_PROTOCOL"),
    "SITE_OF_CARE": ("preferred_place_of_service", "MISSING_SITE_OF_CARE_PARAMETER"),
    "CODING_AND_BILLING": ("edit_pairs", "MISSING_CODING_EDIT"),
    "DRUG_FORMULARY": ("formulary_tier", "MISSING_FORMULARY_PARAMETER"),
    "SPECIALTY_PHARMACY": ("product_identifier", "MISSING_PRODUCT_IDENTIFIER"),
}


def _codes(package: Mapping[str, Any]) -> list[str]:
    codeset = package.get("codeset") or {}
    found: list[str] = []
    for row in codeset.get("codes") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("inclusion_status") or "").upper() == "EXCLUDE":
            continue
        code = str(row.get("code") or "").strip()
        if code and code not in found:
            found.append(code)
    return found


def _parameters(package: Mapping[str, Any], overlay: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for lever in package.get("levers") or []:
        if isinstance(lever, dict) and isinstance(lever.get("parameters"), dict):
            merged.update(lever["parameters"])
    if overlay:
        merged.update(dict(overlay))
    return merged


def _has_rule(package: Mapping[str, Any], rule_id: str) -> bool:
    for rule in package.get("rules") or []:
        if isinstance(rule, dict) and rule.get("id") == rule_id:
            return True
    return False


def resolve_execution_contract(
    package: Mapping[str, Any],
    execution_parameters: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Return a versioned contract. Status is EXECUTABLE or BLOCKED."""
    identity = package.get("identity") or {}
    mechanism = str(identity.get("mechanism") or package.get("mechanism") or "").upper()
    family = str(identity.get("family") or package.get("family") or "").upper()
    policy_key = str(package.get("policy_key") or package.get("_key") or "").lower()
    codes = _codes(package)
    codeset = package.get("codeset") or {}
    code_status = str(codeset.get("status") or "").upper()
    parameters = _parameters(package, execution_parameters)
    base = {
        "contract_version": CONTRACT_VERSION,
        "evidence_class": "SYNTHETIC_MOCK_CONTRACT",
        "not_claiming": NOT_CLAIMING,
        "policy_key": policy_key or None,
        "policy_name": package.get("policy_name") or package.get("name"),
        "package_version": package.get("package_version"),
        "mechanism_family": mechanism or None,
        "policy_family": family or None,
        "candidate_codes": codes,
        "code_status": code_status or None,
        "parameters_used": {},
        "financial_effect_status": "UNAVAILABLE",
        "mechanism_executed": False,
    }

    if policy_key in VALIDATED_PAYMENT_KEYS:
        return {
            **base,
            "status": "EXECUTABLE",
            "mechanism": "VALIDATED_PAYMENT_ENGINE",
            "blocked_reason": None,
            "mechanism_executed": True,
            "financial_effect_status": "MECHANISM_SIMULATION",
            "result_label": "Validated payment-rule simulation. Not an observed payer saving.",
        }

    if mechanism in CLINICAL_MECHANISMS or family in CLINICAL_FAMILIES:
        return {
            **base,
            "status": "BLOCKED",
            "mechanism": None,
            "blocked_reason": "UNSIGNED_CLINICAL_OR_COVERAGE_AUTHORITY",
            "result_label": "Clinical or coverage criteria are not signed in the mock definition.",
        }

    if code_status != "CANDIDATE_SCHEDULE" or not codes:
        reason = codeset.get("not_applicable_reason") or "NO_CANDIDATE_CODE_IN_PACKAGE"
        return {
            **base,
            "status": "BLOCKED",
            "mechanism": None,
            "blocked_reason": "NO_CANDIDATE_CODE_IN_PACKAGE",
            "blocked_detail": str(reason),
            "result_label": "No candidate procedure code is configured. Eligibility was not invented.",
        }

    gate = PARAMETER_GATES.get(family)
    if gate:
        key, missing = gate
        value = parameters.get(key)
        if value is None or value == "" or value == []:
            return {
                **base,
                "status": "BLOCKED",
                "mechanism": None,
                "blocked_reason": missing,
                "required_parameter": key,
                "result_label": "The mechanism family requires a client-configured parameter that this definition does not provide.",
            }
        return {
            **base,
            "status": "EXECUTABLE",
            "mechanism": family,
            "blocked_reason": None,
            "parameters_used": {key: value},
            "financial_effect_status": "CONFIGURED_PARAMETER_RESULT",
            "result_label": "Result uses the client-configured parameter. It is not contracted payment authority.",
        }

    prior_auth = mechanism == "PRIOR_AUTH_UM" or family == "PRIOR_AUTH"
    if prior_auth and _has_rule(package, "R2_NO_AUTO_DENY"):
        return {
            **base,
            "status": "EXECUTABLE",
            "mechanism": "CONFIGURED_RULE_REVIEW_REQUIRED_NO_AUTO_DENY",
            "blocked_reason": None,
            "financial_effect_status": "UNAVAILABLE",
            "result_label": (
                "Configured rule selects in-scope claims for review and does not auto-deny. "
                "No payment change is calculated."
            ),
        }

    return {
        **base,
        "status": "BLOCKED",
        "mechanism": None,
        "blocked_reason": "NO_EXECUTABLE_RULE_IN_DEFINITION",
        "result_label": "The definition names a mechanism but does not contain an executable rule or parameter.",
    }
