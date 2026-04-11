"""Traceability records for API routes — in-memory store keyed by tenant.

The HTTP router expects tenant-scoped CRUD and refresh checks. The legacy
``uepi_api.traceability`` module operates on in-memory insight dicts with a
different signature; this module implements the contract used by
``routers/traceability.py``.
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

_lock = threading.Lock()
_records: List[Dict[str, Any]] = []


def _uuid_str(v: Optional[UUID]) -> Optional[str]:
    return str(v) if v is not None else None


def add_traceability(
    tenant_id: UUID,
    entity_type: str,
    entity_id: UUID,
    data_period_id: Optional[UUID] = None,
    policy_id: Optional[UUID] = None,
    policy_version_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    trace_id = uuid4()
    now = datetime.now(timezone.utc).isoformat()
    rec: Dict[str, Any] = {
        "trace_id": str(trace_id),
        "tenant_id": tenant_id,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "data_period_id": _uuid_str(data_period_id),
        "policy_id": _uuid_str(policy_id),
        "policy_version_id": _uuid_str(policy_version_id),
        "created_at": now,
        "metadata": dict(metadata or {}),
    }
    with _lock:
        _records.append(rec)
    return rec.copy()


def get_traceability(tenant_id: UUID, trace_id: UUID) -> Optional[Dict[str, Any]]:
    sid = str(trace_id)
    with _lock:
        for r in _records:
            if r["tenant_id"] == tenant_id and r["trace_id"] == sid:
                return r.copy()
    return None


def query_by_traceability(
    tenant_id: UUID,
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    data_period_id: Optional[UUID] = None,
    policy_id: Optional[UUID] = None,
    policy_version_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    want_dp = _uuid_str(data_period_id)
    want_pid = _uuid_str(policy_id)
    want_pvid = _uuid_str(policy_version_id)
    want_eid = str(entity_id) if entity_id is not None else None
    with _lock:
        out: List[Dict[str, Any]] = []
        for r in _records:
            if r["tenant_id"] != tenant_id:
                continue
            if entity_type is not None and r["entity_type"] != entity_type:
                continue
            if want_eid is not None and r["entity_id"] != want_eid:
                continue
            if want_dp is not None and r.get("data_period_id") != want_dp:
                continue
            if want_pid is not None and r.get("policy_id") != want_pid:
                continue
            if want_pvid is not None and r.get("policy_version_id") != want_pvid:
                continue
            out.append(r.copy())
        return out


def detect_refresh_triggers(
    tenant_id: UUID,
    entity_type: str,
    entity_id: UUID,
    last_refresh_timestamp: datetime,
) -> bool:
    """Return whether the entity should be refreshed.

    Stored trace rows are optional; without dependency metadata we default to
    ``False`` so the UI can load predictions without error. When trace rows
    exist, ``metadata`` may set ``needs_refresh`` or dependency version hints.
    """
    _ = tenant_id, last_refresh_timestamp
    rows = query_by_traceability(tenant_id, entity_type=entity_type, entity_id=entity_id)
    for r in rows:
        meta = r.get("metadata") or {}
        if isinstance(meta, dict) and meta.get("needs_refresh") is True:
            return True
    return False


def generate_audit_trail(
    tenant_id: UUID,
    entity_type: str,
    entity_id: UUID,
) -> List[Dict[str, Any]]:
    return query_by_traceability(tenant_id, entity_type=entity_type, entity_id=entity_id)
