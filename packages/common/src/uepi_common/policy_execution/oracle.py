"""Independent expected values for configured policy execution.

This module must not import the production engine.
"""
from __future__ import annotations

from typing import Mapping, Sequence


def expected_review_from_lines(lines: Sequence[Mapping], codes: Sequence[str]) -> dict:
    wanted = {str(code) for code in codes}
    matched = [
        line
        for line in lines
        if str(line.get("cpt_code") or line.get("hcpcs_code") or line.get("code") or "") in wanted
    ]
    allowed = 0.0
    paid = 0.0
    members = set()
    for line in matched:
        allowed += float(line.get("allowed_amount") or 0)
        paid += float(line.get("paid_amount") or 0)
        if line.get("member_id"):
            members.add(str(line["member_id"]))
    return {
        "eligible_line_count": len(matched),
        "excluded_line_count": len(lines) - len(matched),
        "eligible_member_count": len(members),
        "eligible_allowed": round(allowed, 2),
        "eligible_paid": round(paid, 2),
        "financial_effect": None,
    }


def expected_quantity_from_lines(lines: Sequence[Mapping], codes: Sequence[str], limit_units: float) -> dict:
    wanted = {str(code) for code in codes}
    limit = float(limit_units)
    before = 0.0
    after = 0.0
    eligible = 0
    exceeds = 0
    for line in lines:
        code = str(line.get("cpt_code") or line.get("hcpcs_code") or line.get("code") or "")
        if code not in wanted:
            continue
        eligible += 1
        units = float(line.get("units") or 0)
        allowed = float(line.get("allowed_amount") or 0)
        before += allowed
        if units > limit and units > 0:
            exceeds += 1
            after += round(allowed * (limit / units), 2)
        else:
            after += allowed
    return {
        "eligible_line_count": eligible,
        "exceeds_limit_count": exceeds,
        "financial_effect": round(before - after, 2),
        "eligible_allowed_before": round(before, 2),
        "eligible_allowed_after": round(after, 2),
    }


def expected_review_from_code_totals(code_totals: Mapping[str, Mapping], codes: Sequence[str]) -> dict:
    """Sum per-code buckets. A code listed twice is counted once."""
    lines = 0
    allowed = 0.0
    paid = 0.0
    for code in dict.fromkeys(str(item) for item in codes):
        bucket = code_totals.get(code)
        if not bucket:
            continue
        lines += int(bucket["lines"])
        allowed += float(bucket["allowed"])
        paid += float(bucket["paid"])
    return {
        "eligible_line_count": lines,
        "eligible_allowed": round(allowed, 2),
        "eligible_paid": round(paid, 2),
        "financial_effect": None,
    }
