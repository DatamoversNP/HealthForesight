"""Member-month exposure from coverage intervals.

Convention SYNTHETIC_PARTIAL_MONTH_V1:
a coverage interval is half-open, [start, end).
Inside each calendar month, exposure is enrolled days divided by the
number of days in that month. A member enrolled every day of the month
contributes 1. A day on the end date is not enrolled.
This is a synthetic accounting convention, not a filed actuarial memo.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Iterable, Sequence, Tuple

CONVENTION = "SYNTHETIC_PARTIAL_MONTH_V1"
Interval = Tuple[date, date]


def _month_start(day: date) -> date:
    return date(day.year, day.month, 1)


def _next_month(day: date) -> date:
    if day.month == 12:
        return date(day.year + 1, 1, 1)
    return date(day.year, day.month + 1, 1)


def days_in_month(day: date) -> int:
    return calendar.monthrange(day.year, day.month)[1]


def member_months(intervals: Sequence[Interval], window_start: date, window_end: date) -> float:
    """Sum partial months. Window is half-open. Overlaps are merged (distinct days)."""
    from uepi_common.metrics.member_months import member_months_for_intervals

    return member_months_for_intervals(intervals, window_start, window_end)


def covers(intervals: Iterable[Interval], day: date) -> bool:
    return any(start <= day < end for start, end in intervals)


def clip_intervals(intervals: Sequence[Interval], window_start: date, window_end: date) -> list[Interval]:
    clipped = []
    for start, end in intervals:
        left = max(start, window_start)
        right = min(end, window_end)
        if left < right:
            clipped.append((left, right))
    return clipped


def add_days(day: date, count: int) -> date:
    return day + timedelta(days=count)
