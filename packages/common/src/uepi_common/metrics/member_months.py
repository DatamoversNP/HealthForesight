"""Standard payer member-month exposure.

MM(m, t) = distinct eligible covered days for member m in month t
           / calendar days in month t

Coverage intervals are half-open [start, end). Overlaps are merged so each
calendar day counts once. A member contributes at most 1.0 MM per month.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Iterable, List, Sequence, Tuple

CONVENTION = "DISTINCT_COVERED_DAYS_V1"
Interval = Tuple[date, date]


def days_in_month(day: date) -> int:
    return calendar.monthrange(day.year, day.month)[1]


def _month_start(day: date) -> date:
    return date(day.year, day.month, 1)


def _next_month(day: date) -> date:
    if day.month == 12:
        return date(day.year + 1, 1, 1)
    return date(day.year, day.month + 1, 1)


def merge_intervals(intervals: Sequence[Interval]) -> List[Interval]:
    """Merge overlapping/adjacent half-open intervals into distinct coverage."""
    cleaned = sorted((s, e) for s, e in intervals if s < e)
    if not cleaned:
        return []
    out: List[Interval] = [cleaned[0]]
    for start, end in cleaned[1:]:
        last_start, last_end = out[-1]
        if start <= last_end:
            out[-1] = (last_start, max(last_end, end))
        else:
            out.append((start, end))
    return out


def covers(intervals: Iterable[Interval], day: date) -> bool:
    return any(start <= day < end for start, end in intervals)


def clip_intervals(intervals: Sequence[Interval], window_start: date, window_end: date) -> List[Interval]:
    clipped: List[Interval] = []
    for start, end in intervals:
        left = max(start, window_start)
        right = min(end, window_end)
        if left < right:
            clipped.append((left, right))
    return clipped


def member_months_for_intervals(
    intervals: Sequence[Interval],
    window_start: date,
    window_end: date,
) -> float:
    """Sum MM over a half-open window using distinct covered days per month."""
    merged = merge_intervals(clip_intervals(intervals, window_start, window_end))
    total = 0.0
    for start, end in merged:
        cursor = start
        while cursor < end:
            month_end = _next_month(cursor)
            overlap_end = min(end, month_end)
            enrolled_days = (overlap_end - cursor).days
            dim = days_in_month(cursor)
            total += min(enrolled_days, dim) / dim
            cursor = overlap_end
    return total


def member_month_contribution(
    *,
    enrollment_start: date,
    enrollment_end: date,
    extra_covered_days: int = 0,
) -> float:
    """One stored month-row contribution under half-open + optional extra covered days.

    ``extra_covered_days`` reconstructs additional enrolled days from a second
    span in the same month (stored historically as segment GAP_DAYS:N). It is
    not uncovered time.
    """
    if enrollment_start >= enrollment_end and extra_covered_days <= 0:
        return 0.0
    dim = days_in_month(enrollment_start)
    primary = max(0, (enrollment_end - enrollment_start).days)
    covered = min(dim, primary + max(0, int(extra_covered_days)))
    return covered / dim


def parse_extra_covered_days(segment: str | None) -> int:
    """Decode GAP_DAYS:N as extra covered days; CONTIGUOUS/other => 0."""
    if not segment:
        return 0
    if segment.startswith("GAP_DAYS:"):
        try:
            return max(0, int(segment.split(":", 1)[1]))
        except ValueError:
            return 0
    return 0
