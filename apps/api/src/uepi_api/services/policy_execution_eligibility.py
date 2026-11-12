"""Policy execution eligibility — fail closed on unverified coding/authority.

Blocks code-dependent claims calculations when remediation marks a policy as
not claims-executable. Does not invent codes or certify payer authority.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


BLOCKING_STATUSES = {
    "BLOCK_CLAIMS_EXECUTION_PENDING_REMAP",
    "REVIEW_REQUIRED_NO_AUTHORITY_CERTIFICATION",
    "CODE_REVIEW_REQUIRED",
    "PROVENANCE_ONLY",
    "NOT_EXECUTABLE",
    "UNVERIFIED_CODE_MAPPING",
}

EXECUTABLE_STATUSES = {
    "CLAIMS_EXECUTABLE",
    "DIRECTIONALLY_VALID",
}


def _meta(policy: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(policy, dict):
        return {}
    meta = policy.get("policy_metadata_json") or policy.get("metadata") or {}
    return meta if isinstance(meta, dict) else {}


def get_remediation(policy: Dict[str, Any]) -> Dict[str, Any]:
    meta = _meta(policy)
    rem = meta.get("remediation") if isinstance(meta.get("remediation"), dict) else {}
    # Also allow remediation at top-level policy dict (already flattened)
    if not rem and isinstance(policy.get("remediation"), dict):
        rem = policy["remediation"]
    return rem


def claims_execution_allowed(policy: Dict[str, Any]) -> Tuple[bool, str]:
    """Return (allowed, reason). Fail closed when remediation is present and not executable."""
    rem = get_remediation(policy)
    if not rem:
        # No remediation envelope → legacy behavior (allowed). Staging remediation
        # always writes an envelope; absence means pre-remediation / other env.
        return True, "no_remediation_envelope"

    exec_state = str(rem.get("execution_eligibility") or "").upper()
    status = str(rem.get("register_status") or rem.get("status") or "").upper()
    code_state = str(rem.get("code_mapping_state") or "").upper()

    if exec_state in {"CLAIMS_EXECUTABLE", "DIRECTIONALLY_VALID", "ALLOWED"}:
        if code_state in {"UNVERIFIED_CODE_MAPPING", "CLEARED_PENDING_REMAP"}:
            return False, f"execution_blocked:code_mapping_state={code_state}"
        return True, f"execution_allowed:{exec_state}"

    if exec_state in {"BLOCKED", "NOT_EXECUTABLE", "PENDING_REMAP"} or status in BLOCKING_STATUSES:
        return False, f"execution_blocked:status={status or exec_state}"

    if code_state in {"UNVERIFIED_CODE_MAPPING", "CLEARED_PENDING_REMAP"}:
        return False, f"execution_blocked:code_mapping_state={code_state}"

    # Unknown remediation present → fail closed
    return False, f"execution_blocked:fail_closed:{exec_state or status or 'unknown'}"


def assert_claims_execution_allowed(policy: Dict[str, Any]) -> None:
    allowed, reason = claims_execution_allowed(policy)
    if not allowed:
        raise PermissionError(
            f"Claims calculation blocked for policy "
            f"{policy.get('id') or policy.get('name') or '?'}: {reason}"
        )
