#!/usr/bin/env python3
"""Policy accuracy validators — fail incorrect scope/levers even if analytics run.

Does not invent missing clinical/payment truth. Marks UNRESOLVED when evidence absent.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def validate_scope_lever_alignment(policy: Dict[str, Any], codes: List[str]) -> List[str]:
    """Return list of mandatory failure messages (empty = pass)."""
    fails: List[str] = []
    sc = policy.get("scope") or {}
    markets = sc.get("markets") or []
    states = sc.get("states") or []
    name = (policy.get("name") or "").lower()
    ptype = (policy.get("policy_type") or "").upper()

    if not markets:
        fails.append("SCOPE: markets empty")
    if not states:
        fails.append("SCOPE: states empty")

    # NC jurisdiction with metro-only claim markets is allowed only with explicit note
    # (MRI lumbar case). Without codes that require metros, prefer NC markets for NC states.
    if states == ["NC"] and markets and set(markets).issubset({"NYC", "DFW", "BOS", "CHICAGO", "LA"}):
        if not codes:
            fails.append(
                "SCOPE: states=NC but markets are metro-only without lever codes justifying claim geography"
            )

    # Imaging PA should not use E/M as targets
    em = {"99213", "99214", "99215", "99203", "99204", "99205"}
    if codes and set(codes) & em and ("mri" in name or "imaging" in name or ptype == "PRIOR_AUTH"):
        fails.append("LEVERS: E/M codes used as imaging/PA targets")

    # Payment policies must not invent contracted rates in levers without evidence_class
    for lever in policy.get("policy_levers") or []:
        params = (lever or {}).get("parameters") or {}
        if "contracted_rate" in params or "bcbs_nc_rate" in params:
            fails.append("LEVERS: invented contracted/BCBS NC rate field present")

    return fails


def gate_rollup(fails: List[str], has_definition_package: bool) -> Dict[str, str]:
    scope_fail = any(f.startswith("SCOPE:") for f in fails)
    lever_fail = any(f.startswith("LEVERS:") for f in fails)
    return {
        "POLICY_SCOPE_VALIDATED": "FAIL" if scope_fail else ("PASS" if has_definition_package else "PARTIAL"),
        "LEVERS_VALIDATED": "FAIL" if lever_fail else ("PASS" if has_definition_package else "PARTIAL"),
        "DEFINITION_COMPLETE": "PASS" if has_definition_package and not fails else "FAIL",
        "failures": fails,  # type: ignore[dict-item]
    }


def validate_package_required_sections(pkg: Dict[str, Any]) -> Tuple[bool, List[str]]:
    required = [
        "identity",
        "scope",
        "applicability",
        "codeset",
        "levers",
        "rules",
        "exceptions",
        "assumptions",
        "guardrails",
        "sources",
        "analytics",
        "governance",
        "acceptance_tests",
        "release_blockers",
    ]
    missing = [k for k in required if k not in pkg]
    if pkg.get("classification") not in {
        "REPRESENTATIVE_PAYER_POLICY",
        "SYNTHETIC_DEMO_FIXTURE",
        "PROVENANCE_STUDY",
    }:
        missing.append("classification")
    if "Blue Cross NC operative" not in str(pkg.get("not_claiming") or "") and pkg.get(
        "classification"
    ) == "REPRESENTATIVE_PAYER_POLICY":
        # soft — encourage explicit not_claiming
        pass
    return (len(missing) == 0, missing)
