"""Read predicted impact from policy metadata — no heavy analytics imports (numpy/scipy)."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional, Union


def _coerce_dict(value: Union[None, str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else None
        except (json.JSONDecodeError, TypeError):
            return None
    return None


def get_predicted_impact_from_metadata(
    policy_metadata: Optional[Any],
) -> Optional[Dict[str, Any]]:
    """
    Extract predicted impact from policy metadata.
    Tolerates double-encoded JSON or string metadata (avoids 500s on bad rows).
    """
    meta = policy_metadata if isinstance(policy_metadata, dict) else _coerce_dict(policy_metadata)
    if not meta:
        return None
    raw = meta.get("predicted_impact")
    if raw is None:
        return None
    if isinstance(raw, str):
        raw = _coerce_dict(raw)
    return raw if isinstance(raw, dict) else None
