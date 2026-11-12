"""Configurable policy execution contracts.

Engines read client-supplied policy configuration. They do not invent clinical
authority, procedure codes, or financial parameters that the configuration omits.
"""

from uepi_common.policy_execution.contract import resolve_execution_contract
from uepi_common.policy_execution.engine import execute_configured_policy

__all__ = ["execute_configured_policy", "resolve_execution_contract"]
