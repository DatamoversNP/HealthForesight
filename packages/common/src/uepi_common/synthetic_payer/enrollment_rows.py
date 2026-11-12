"""Month rows for the canonical enrollment table.

Each row is one member and one calendar month. The stored span is half-open.
When two coverage intervals touch the same month, the first span is stored in
the dates and the other enrolled days are stored as GAP_DAYS on segment.
That keeps the unique (member, month) key and the partial-month total exact.
"""

from __future__ import annotations

import calendar
from datetime import date
from typing import Any, Dict, Iterator, List, Tuple

from uepi_common.synthetic_payer.exposure import CONVENTION
from uepi_common.synthetic_payer.generate import WINDOW_END, WINDOW_START


def _next_month(day: date) -> date:
    if day.month == 12:
        return date(day.year + 1, 1, 1)
    return date(day.year, day.month + 1, 1)


def _age_band(age: int) -> str:
    if age < 18:
        return "0-17"
    if age < 45:
        return "18-44"
    if age < 65:
        return "45-64"
    return "65+"


def iter_enrollment_month_rows(population: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    spans: Dict[Tuple[str, date], List[Tuple[date, date]]] = {}
    for row in population["coverage"]:
        start = date.fromisoformat(row["start_date"])
        end = date.fromisoformat(row["end_date"])
        cursor = max(start, WINDOW_START)
        stop = min(end, WINDOW_END)
        member_id = row["member_id"]
        while cursor < stop:
            month_end = _next_month(cursor)
            overlap_end = min(stop, month_end)
            key = (member_id, date(cursor.year, cursor.month, 1))
            spans.setdefault(key, []).append((cursor, overlap_end))
            cursor = overlap_end
    members = {row["member_id"]: row for row in population["members"]}
    for (member_id, month), ranges in spans.items():
        ranges.sort()
        first_start, first_end = ranges[0]
        extra_days = sum((right - left).days for left, right in ranges[1:])
        member = members[member_id]
        yield {
            "member_id": member_id,
            "enrollment_month": month.isoformat(),
            "lob": "COMMERCIAL",
            "market": "SYNTHETIC",
            "age_band": _age_band(int(member["age_years"])),
            "gender": member["sex"],
            "risk_score": 0,
            "network_tier": "SYNTHETIC",
            "enrolled_flag": True,
            "enrollment_start_date": first_start.isoformat(),
            "enrollment_end_date": first_end.isoformat(),
            "product_type": "COMMERCIAL_SYNTHETIC",
            "segment": f"GAP_DAYS:{extra_days}" if extra_days else "CONTIGUOUS",
            "partial_month_convention": CONVENTION,
            "risk_score_meaning": "NOT_A_RISK_MODEL",
        }


def member_months_from_rows(rows: List[Dict[str, Any]]) -> float:
    """Same partial-month total the database summer applies to stored spans."""
    total = 0.0
    for row in rows:
        start = date.fromisoformat(row["enrollment_start_date"])
        end = date.fromisoformat(row["enrollment_end_date"])
        extra = 0
        segment = row.get("segment") or ""
        if segment.startswith("GAP_DAYS:"):
            extra = int(segment.split(":", 1)[1])
        dim = calendar.monthrange(start.year, start.month)[1]
        total += ((end - start).days + extra) / dim
    return total
