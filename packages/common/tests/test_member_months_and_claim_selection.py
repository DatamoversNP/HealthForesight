"""Standard enrollment MM and claim-line selection."""

from datetime import date

from uepi_common.metrics.claim_selection import (
    is_financially_valid_line,
    select_claim_lines,
)
from uepi_common.metrics.member_months import (
    member_month_contribution,
    member_months_for_intervals,
    merge_intervals,
    parse_extra_covered_days,
)


def test_full_month_is_one():
    # Half-open January: [2025-01-01, 2025-02-01)
    assert member_month_contribution(
        enrollment_start=date(2025, 1, 1),
        enrollment_end=date(2025, 2, 1),
    ) == 1.0


def test_partial_month():
    # 10 covered days in January (31 days)
    mm = member_month_contribution(
        enrollment_start=date(2025, 1, 1),
        enrollment_end=date(2025, 1, 11),
    )
    assert abs(mm - (10 / 31)) < 1e-12


def test_overlap_merged_not_double_counted():
    intervals = [
        (date(2025, 1, 1), date(2025, 1, 20)),
        (date(2025, 1, 10), date(2025, 2, 1)),  # overlaps / extends through month end
    ]
    mm = member_months_for_intervals(intervals, date(2025, 1, 1), date(2025, 2, 1))
    assert abs(mm - 1.0) < 1e-12
    assert merge_intervals(intervals) == [(date(2025, 1, 1), date(2025, 2, 1))]


def test_true_gap_excludes_uncovered_days():
    intervals = [
        (date(2025, 1, 1), date(2025, 1, 11)),  # 10 days
        (date(2025, 1, 21), date(2025, 2, 1)),  # 11 days; gap 11-20 uncovered
    ]
    mm = member_months_for_intervals(intervals, date(2025, 1, 1), date(2025, 2, 1))
    assert abs(mm - (21 / 31)) < 1e-12


def test_gap_days_segment_means_extra_covered_days():
    assert parse_extra_covered_days("CONTIGUOUS") == 0
    assert parse_extra_covered_days("GAP_DAYS:5") == 5
    # Primary 20 days + 5 extra covered, January 31 → 25/31
    mm = member_month_contribution(
        enrollment_start=date(2025, 1, 1),
        enrollment_end=date(2025, 1, 21),
        extra_covered_days=5,
    )
    assert abs(mm - (25 / 31)) < 1e-12


def test_member_month_capped_at_one():
    mm = member_month_contribution(
        enrollment_start=date(2025, 1, 1),
        enrollment_end=date(2025, 2, 1),
        extra_covered_days=10,
    )
    assert mm == 1.0


def test_void_and_reversal_excluded():
    assert is_financially_valid_line({"line_status": "ACTIVE"}) is True
    assert is_financially_valid_line({"line_status": "VOID"}) is False
    assert is_financially_valid_line({"line_status": "REVERSAL"}) is False
    assert is_financially_valid_line(
        {"record_hash": '{"line_status":"REVERSAL"}'}
    ) is False


def test_claim_requires_enrollment_on_service_date():
    lines = [
        {
            "member_id": "M1",
            "service_date": "2025-03-15",
            "cpt_code": "72148",
            "service_category": "mri",
            "allowed_amount": 900,
            "paid_amount": 700,
            "line_status": "ACTIVE",
        },
        {
            "member_id": "M2",
            "service_date": "2025-03-15",
            "cpt_code": "72148",
            "service_category": "mri",
            "allowed_amount": 900,
            "paid_amount": 700,
            "line_status": "ACTIVE",
        },
        {
            "member_id": "M1",
            "service_date": "2025-03-15",
            "cpt_code": "72148",
            "service_category": "mri",
            "allowed_amount": -900,
            "paid_amount": -700,
            "line_status": "REVERSAL",
        },
    ]
    coverage = {
        "M1": [(date(2025, 3, 1), date(2025, 4, 1))],
        # M2 not enrolled in March
    }
    result = select_claim_lines(
        lines,
        coverage_by_member=coverage,
        procedure_codes={"72148"},
        service_categories={"mri"},
        window_start=date(2025, 1, 1),
        window_end=date(2025, 12, 31),
    )
    assert result["line_count"] == 1
    assert result["total_allowed"] == 900
    assert result["exclusions"]["not_enrolled_on_service_date"] == 1
    assert result["exclusions"]["invalid_line_status"] == 1
