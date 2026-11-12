"""Enrollment member-months from stored coverage spans.

Standard definition:
  MM(m, t) = distinct eligible covered days / calendar days in month t

Stored rows use half-open [enrollment_start_date, enrollment_end_date).
segment GAP_DAYS:N means N additional covered days from another span in the
same month (not uncovered time). Each member-month is capped at 1.0.
"""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

_CACHE: dict = {}


def clear_enrollment_cache() -> None:
    _CACHE.clear()


def measured_enrollment_member_months(
    db: Session,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
    source_system: Optional[str] = None,
    product_type: Optional[str] = None,
) -> Optional[float]:
    """Partial-month exposure. None means enrollment was not loaded."""
    key = (
        str(tenant_id),
        start_date.isoformat(),
        end_date.isoformat(),
        source_system or "",
        product_type or "",
    )
    if key in _CACHE:
        return _CACHE[key]
    month_start = date(start_date.year, start_date.month, 1)
    month_end = date(end_date.year, end_date.month, 1)
    clauses = [
        "tenant_id = :tenant_id",
        "enrollment_month >= :month_start",
        "enrollment_month <= :month_end",
        "enrollment_start_date IS NOT NULL",
        "enrollment_end_date IS NOT NULL",
    ]
    params = {
        "tenant_id": tenant_id,
        "month_start": month_start,
        "month_end": month_end,
    }
    if source_system:
        clauses.append("source_system = :source_system")
        params["source_system"] = source_system
    if product_type:
        clauses.append("product_type = :product_type")
        params["product_type"] = product_type
    where = " AND ".join(clauses)

    count = db.execute(
        text(f"SELECT COUNT(*) FROM enrollment_records WHERE {where}"),
        params,
    ).scalar()
    if not count:
        _CACHE[key] = None
        return None

    # Half-open primary span + optional extra covered days, capped at month length.
    value = db.execute(
        text(
            f"""
            SELECT COALESCE(SUM(
                LEAST(
                    1.0,
                    (
                        GREATEST(0, (enrollment_end_date - enrollment_start_date))
                        + CASE
                            WHEN segment LIKE 'GAP_DAYS:%%'
                            THEN GREATEST(0, CAST(split_part(segment, ':', 2) AS integer))
                            ELSE 0
                          END
                    )::double precision
                    / EXTRACT(
                        DAY FROM (
                            date_trunc('month', enrollment_month)
                            + INTERVAL '1 month - 1 day'
                        )
                    )
                )
            ), 0)
            FROM enrollment_records
            WHERE {where}
            """
        ),
        params,
    ).scalar()
    measured = round(float(value or 0), 6)
    _CACHE[key] = measured
    return measured
