"""Read persisted configured-policy execution results.

Results are written by the policy execution worker. This route does not calculate
a fallback amount when no result is stored.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from uepi_api.auth import CurrentUser, verify_token
from uepi_api.database import get_db
from uepi_api.models.policy import Policy

router = APIRouter()


def _summary_row(policy: Policy) -> dict[str, Any]:
    meta = policy.policy_metadata_json if isinstance(policy.policy_metadata_json, dict) else {}
    execution = meta.get("mock_execution_v1") if isinstance(meta.get("mock_execution_v1"), dict) else None
    if not execution:
        return {
            "policy_id": str(policy.id),
            "name": policy.name,
            "status": "NOT_RUN",
            "mechanism": None,
            "mechanism_executed": False,
            "blocked_reason": None,
            "financial_effect_status": "UNAVAILABLE",
            "eligible_line_count": None,
            "oracle_match": None,
            "required_parameter": None,
            "configuration_state": "NOT_RUN",
            "parameter_engine_implemented": False,
            "result_label": "No execution result is stored for this policy.",
        }
    required = execution.get("required_parameter")
    mechanism = execution.get("mechanism")
    status = execution.get("status")
    if status == "EXECUTABLE" and mechanism == "VALIDATED_PAYMENT_ENGINE":
        configuration_state = "PAYMENT_SIMULATION"
    elif status == "EXECUTABLE" and mechanism == "CONFIGURED_RULE_REVIEW_REQUIRED_NO_AUTO_DENY":
        configuration_state = "REVIEW_ONLY"
    elif status == "EXECUTABLE":
        configuration_state = "EXECUTABLE"
    elif required:
        configuration_state = "AWAITING_CONFIGURATION"
    else:
        configuration_state = "BLOCKED"
    return {
        "policy_id": str(policy.id),
        "name": policy.name,
        "status": status,
        "mechanism": mechanism,
        "mechanism_executed": bool(execution.get("mechanism_executed")),
        "blocked_reason": execution.get("blocked_reason"),
        "required_parameter": required,
        "configuration_state": configuration_state,
        "parameter_engine_implemented": required == "quantity_limit_units",
        "financial_effect_status": execution.get("financial_effect_status") or "UNAVAILABLE",
        "eligible_line_count": execution.get("eligible_line_count"),
        "oracle_match": execution.get("oracle_match"),
        "result_label": execution.get("result_label"),
    }


@router.get("/policy-execution/summary")
async def policy_execution_summary(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    policies = (
        db.query(Policy)
        .filter(Policy.tenant_id == current_user.tenant_id)
        .order_by(Policy.name.asc())
        .all()
    )
    rows = [_summary_row(policy) for policy in policies]
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row["status"] or "UNKNOWN")
        counts[key] = counts.get(key, 0) + 1
    executed = sum(1 for row in rows if row["mechanism_executed"])
    configuration_counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get("configuration_state") or "UNKNOWN")
        configuration_counts[key] = configuration_counts.get(key, 0) + 1
    return {
        "contract_version": "mock-client-exec-v1",
        "policy_count": len(rows),
        "mechanism_executed_count": executed,
        "status_counts": counts,
        "configuration_counts": configuration_counts,
        "financial_note": (
            "Review-only results are not payment changes. Blocked policies have no financial result. "
            "Validated payment simulations stay separate from review results and are not portfolio savings."
        ),
        "policies": rows,
    }
