"""Worker entry for configured policy-mechanism execution.

Retries a failed attempt once. Does not invent a result when the contract is blocked
and does not treat a continuation forecast as execution.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional, Sequence

from uepi_common.policy_execution.engine import execute_configured_policy


def run_policy_execution(
    package: Mapping[str, Any],
    lines: Sequence[Mapping[str, Any]],
    execution_parameters: Optional[Mapping[str, Any]] = None,
    *,
    attempts: int = 2,
    execute: Callable = execute_configured_policy,
) -> dict[str, Any]:
    last_error: Optional[BaseException] = None
    for attempt in range(1, attempts + 1):
        try:
            result = dict(execute(package, lines, execution_parameters))
            result["worker"] = "uepi_worker.policy_mechanism_execution"
            result["attempt"] = attempt
            result["continuation_used_as_execution"] = False
            return result
        except Exception as exc:  # worker retry boundary
            last_error = exc
    return {
        "status": "FAILED",
        "mechanism_executed": False,
        "blocked_reason": "WORKER_FAILED",
        "error": str(last_error),
        "attempt": attempts,
        "financial_effect": None,
        "eligible_line_count": None,
        "worker": "uepi_worker.policy_mechanism_execution",
        "continuation_used_as_execution": False,
    }
