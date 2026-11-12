"""Apply a resolved execution contract to claim lines.

This module is the production execution implementation. The independent oracle
must not import it.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from uepi_common.policy_execution.contract import resolve_execution_contract


def _line_code(line: Mapping[str, Any]) -> Optional[str]:
    for key in ("cpt_code", "hcpcs_code", "code"):
        value = line.get(key)
        if value is not None and str(value).strip() and str(value).strip() != "\\N":
            return str(value).strip()
    return None


def _money(line: Mapping[str, Any], key: str) -> float:
    value = line.get(key)
    if value is None:
        return 0.0
    return float(value)


def execute_review_required(lines: Sequence[Mapping[str, Any]], codes: Sequence[str]) -> dict[str, Any]:
    """Select configured codes. Do not change allowed or paid amounts."""
    selected = set(codes)
    eligible_lines = 0
    excluded_lines = 0
    allowed = 0.0
    paid = 0.0
    members: set[str] = set()
    for line in lines:
        code = _line_code(line)
        if code not in selected:
            excluded_lines += 1
            continue
        eligible_lines += 1
        allowed += _money(line, "allowed_amount")
        paid += _money(line, "paid_amount")
        member = line.get("member_id")
        if member:
            members.add(str(member))
    return {
        "mechanism": "CONFIGURED_RULE_REVIEW_REQUIRED_NO_AUTO_DENY",
        "decision": "REVIEW_REQUIRED",
        "payment_changed": False,
        "financial_effect": None,
        "financial_effect_status": "UNAVAILABLE",
        "eligible_line_count": eligible_lines,
        "excluded_line_count": excluded_lines,
        "eligible_member_count": len(members),
        "eligible_allowed": round(allowed, 2),
        "eligible_paid": round(paid, 2),
        "not_a_savings_result": True,
    }


def execute_quantity_limit(
    lines: Sequence[Mapping[str, Any]],
    codes: Sequence[str],
    limit_units: float,
) -> dict[str, Any]:
    """Cap units at a client-configured limit. Lines at or under the limit are unchanged."""
    selected = set(codes)
    limit = float(limit_units)
    eligible_lines = 0
    excluded_lines = 0
    within = 0
    exceeds = 0
    allowed_before = 0.0
    allowed_after = 0.0
    members: set[str] = set()
    for line in lines:
        code = _line_code(line)
        if code not in selected:
            excluded_lines += 1
            continue
        eligible_lines += 1
        units = float(line.get("units") or 0)
        allowed = _money(line, "allowed_amount")
        allowed_before += allowed
        member = line.get("member_id")
        if member:
            members.add(str(member))
        if units > limit and units > 0:
            exceeds += 1
            allowed_after += round(allowed * (limit / units), 2)
        else:
            within += 1
            allowed_after += allowed
    effect = round(allowed_before - allowed_after, 2)
    return {
        "mechanism": "QUANTITY_LIMIT",
        "decision": "CONFIGURED_QUANTITY_CAP",
        "payment_changed": effect != 0,
        "financial_effect": effect,
        "financial_effect_status": "CONFIGURED_PARAMETER_RESULT",
        "financial_effect_label": "Synthetic configured quantity cap. Not a contracted payer saving.",
        "eligible_line_count": eligible_lines,
        "excluded_line_count": excluded_lines,
        "within_limit_count": within,
        "exceeds_limit_count": exceeds,
        "eligible_member_count": len(members),
        "eligible_allowed_before": round(allowed_before, 2),
        "eligible_allowed_after": round(allowed_after, 2),
        "not_a_savings_result": True,
    }


def execute_configured_policy(
    package: Mapping[str, Any],
    lines: Sequence[Mapping[str, Any]],
    execution_parameters: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Worker entry: resolve the contract, then apply only a supported mechanism."""
    contract = resolve_execution_contract(package, execution_parameters)
    if contract["status"] != "EXECUTABLE":
        return {
            **contract,
            "eligible_line_count": None,
            "eligible_allowed": None,
            "eligible_paid": None,
            "financial_effect": None,
            "payment_changed": False,
        }
    mechanism = contract["mechanism"]
    if mechanism == "CONFIGURED_RULE_REVIEW_REQUIRED_NO_AUTO_DENY":
        result = execute_review_required(lines, contract["candidate_codes"])
    elif mechanism == "QUANTITY_LIMIT":
        result = execute_quantity_limit(
            lines,
            contract["candidate_codes"],
            float(contract["parameters_used"]["quantity_limit_units"]),
        )
    elif mechanism == "VALIDATED_PAYMENT_ENGINE":
        result = {
            "mechanism": mechanism,
            "decision": "USE_VALIDATED_PAYMENT_ENGINE",
            "payment_changed": None,
            "financial_effect": None,
            "financial_effect_status": "MECHANISM_SIMULATION",
            "eligible_line_count": None,
            "eligible_allowed": None,
            "eligible_paid": None,
            "not_a_savings_result": True,
            "note": "Dollar results stay on the validated payment engine. This path does not recompute them.",
        }
    else:
        return {
            **contract,
            "status": "BLOCKED",
            "mechanism_executed": False,
            "blocked_reason": "MECHANISM_ENGINE_NOT_IMPLEMENTED",
            "eligible_line_count": None,
            "financial_effect": None,
            "payment_changed": False,
        }
    return {**contract, **result, "mechanism_executed": True}
