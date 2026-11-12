"""Standard claim-line selection for baseline / observation numerators.

Include a claim line when:
- it matches the configured codeset / service filters
- the member is enrolled on the service date (half-open coverage)
- the line is financially valid (not void/reversal; replacements net correctly)

Does not invent clinical decisions or policy-effect savings.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Set

from uepi_common.metrics.member_months import Interval, covers, merge_intervals

ACTIVE_STATUSES = {"ACTIVE", "FINAL", "PAID", ""}
EXCLUDED_STATUSES = {"VOID", "REVERSAL", "REVERSED", "CANCELLED", "CANCELED", "DELETED"}


def line_status_from_record(record: Mapping[str, Any]) -> str:
    direct = record.get("line_status") or record.get("claim_line_status") or record.get("status")
    if direct:
        return str(direct).upper().strip()
    meta = record.get("record_hash") or record.get("metadata") or {}
    if isinstance(meta, str):
        # Lightweight parse for synthetic JSON hash payloads.
        if '"line_status":"REVERSAL"' in meta or '"line_status": "REVERSAL"' in meta:
            return "REVERSAL"
        if '"line_status":"VOID"' in meta or '"line_status": "VOID"' in meta:
            return "VOID"
        if '"line_status":"ACTIVE"' in meta or '"line_status": "ACTIVE"' in meta:
            return "ACTIVE"
        return "ACTIVE"
    if isinstance(meta, dict):
        return str(meta.get("line_status") or meta.get("status") or "ACTIVE").upper().strip()
    return "ACTIVE"


def is_financially_valid_line(record: Mapping[str, Any]) -> bool:
    status = line_status_from_record(record)
    if status in EXCLUDED_STATUSES:
        return False
    if status and status not in ACTIVE_STATUSES and status not in {"ADJUSTMENT", "REPLACEMENT", "CORRECTED"}:
        # Unknown non-active statuses are excluded fail-closed for measurement.
        return False
    return True


def member_enrolled_on_service_date(
    service_date: date,
    coverage_intervals: Sequence[Interval],
) -> bool:
    return covers(merge_intervals(coverage_intervals), service_date)


def select_claim_lines(
    lines: Iterable[Mapping[str, Any]],
    *,
    coverage_by_member: Mapping[str, Sequence[Interval]],
    procedure_codes: Optional[Set[str]] = None,
    service_categories: Optional[Set[str]] = None,
    window_start: Optional[date] = None,
    window_end: Optional[date] = None,
    require_enrollment: bool = True,
) -> Dict[str, Any]:
    """Filter claim lines to the measurement numerator set.

    ``window_end`` is inclusive for claim service dates (calendar window).
    """
    selected = []
    excluded = {
        "out_of_window": 0,
        "procedure_out_of_scope": 0,
        "service_category_out_of_scope": 0,
        "not_enrolled_on_service_date": 0,
        "invalid_line_status": 0,
    }
    codes = {str(c).strip() for c in (procedure_codes or set()) if c}
    cats = {str(c).strip() for c in (service_categories or set()) if c}

    for row in lines:
        svc = row.get("service_date")
        if isinstance(svc, str):
            svc = date.fromisoformat(svc[:10])
        if not isinstance(svc, date):
            excluded["out_of_window"] += 1
            continue
        if window_start and svc < window_start:
            excluded["out_of_window"] += 1
            continue
        if window_end and svc > window_end:
            excluded["out_of_window"] += 1
            continue

        code = str(row.get("cpt_code") or row.get("hcpcs_code") or "").strip()
        if codes and code not in codes:
            excluded["procedure_out_of_scope"] += 1
            continue

        cat = str(row.get("service_category") or "").strip()
        if cats and cat not in cats:
            excluded["service_category_out_of_scope"] += 1
            continue

        if not is_financially_valid_line(row):
            excluded["invalid_line_status"] += 1
            continue

        member_id = str(row.get("member_id") or "")
        if require_enrollment:
            intervals = coverage_by_member.get(member_id) or []
            if not member_enrolled_on_service_date(svc, intervals):
                excluded["not_enrolled_on_service_date"] += 1
                continue

        selected.append(row)

    total_allowed = sum(float(r.get("allowed_amount") or 0) for r in selected)
    total_paid = sum(float(r.get("paid_amount") or 0) for r in selected)
    return {
        "lines": selected,
        "line_count": len(selected),
        "total_allowed": total_allowed,
        "total_paid": total_paid,
        "unique_members": len({str(r.get("member_id")) for r in selected}),
        "exclusions": excluded,
    }
