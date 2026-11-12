"""Oracle and exposure checks. These tests do not call the payment engines."""

from datetime import date

from uepi_common.synthetic_payer.exposure import member_months
from uepi_common.synthetic_payer.oracle import (
    oracle_infusion,
    oracle_mppr,
    oracle_mue,
    oracle_ptp,
    oracle_sos,
    oracle_therapy,
    percent_change,
    rate_per_exposure,
)
from uepi_common.synthetic_payer.pilot import run_pilot


def test_enrollment_rows_match_an_independent_day_walk():
    """The month-row total is the same number as walking each coverage date."""
    import calendar
    from uepi_common.synthetic_payer.enrollment_rows import iter_enrollment_month_rows, member_months_from_rows
    from uepi_common.synthetic_payer.exposure import member_months
    from uepi_common.synthetic_payer.generate import WINDOW_END, WINDOW_START, generate_population

    population = generate_population(200, 20261106)
    independent = 0.0
    for row in population["coverage"]:
        cursor = date.fromisoformat(row["start_date"])
        stop = date.fromisoformat(row["end_date"])
        while cursor < stop:
            if cursor.month == 12:
                month_end = date(cursor.year + 1, 1, 1)
            else:
                month_end = date(cursor.year, cursor.month + 1, 1)
            overlap_end = min(stop, month_end)
            independent += (overlap_end - cursor).days / calendar.monthrange(cursor.year, cursor.month)[1]
            cursor = overlap_end
    from_rows = member_months_from_rows(list(iter_enrollment_month_rows(population)))
    from_helper = 0.0
    by_member = {}
    for row in population["coverage"]:
        by_member.setdefault(row["member_id"], []).append(
            (date.fromisoformat(row["start_date"]), date.fromisoformat(row["end_date"]))
        )
    for intervals in by_member.values():
        from_helper += member_months(intervals, WINDOW_START, WINDOW_END)
    assert abs(independent - from_rows) < 1e-6
    assert abs(independent - from_helper) < 1e-6
    lives = len(population["members"])
    equivalent_months = independent / lives
    assert 10 < equivalent_months < 24


def test_generated_claims_are_a_policy_extract():
    from collections import Counter
    from uepi_common.synthetic_payer.generate import generate_events, generate_population

    population = generate_population(1000, 20261106)
    lines = generate_events(population, 20261106)
    cohorts = Counter(row["cohort"] for row in population["members"])
    assert cohorts["none"] == 600
    assert len(lines) < 1000
    assert all(row.get("policy_key") != "pharmacy" for row in lines)
    assert all(row["pharmacy_benefit"] is False for row in population["members"])


def test_partial_month_counts_days_over_days_in_month():
    january = member_months([(date(2025, 1, 1), date(2025, 2, 1))], date(2025, 1, 1), date(2025, 2, 1))
    half = member_months([(date(2025, 1, 1), date(2025, 1, 16))], date(2025, 1, 1), date(2025, 2, 1))
    assert january == 1
    assert abs(half - (15 / 31)) < 1e-12


def test_full_calendar_year_is_twelve_member_months():
    total = member_months([(date(2025, 1, 1), date(2026, 1, 1))], date(2025, 1, 1), date(2026, 1, 1))
    assert abs(total - 12) < 1e-9


def test_oracle_known_answers_do_not_use_the_engines():
    mppr = oracle_mppr(
        [
            {"claim_id": "KA-A", "claim_line_id": "A1", "allowed_amount": 1000},
            {"claim_id": "KA-A", "claim_line_id": "A2", "allowed_amount": 400},
            {"claim_id": "KA-B", "claim_line_id": "B1", "allowed_amount": 800},
            {"claim_id": "KA-B", "claim_line_id": "B2", "allowed_amount": 500},
            {"claim_id": "KA-B", "claim_line_id": "B3", "allowed_amount": 300},
            {"claim_id": "KA-C", "claim_line_id": "C1", "allowed_amount": 150},
        ]
    )
    assert (mppr["baseline_paid"], mppr["post_policy_paid"], mppr["payment_impact"]) == (3150, 2550, 600)

    sos = oracle_sos(
        [
            {"allowed_amount": 800, "place_of_service": "11"},
            {"allowed_amount": 600, "place_of_service": "11"},
            {"allowed_amount": 1200, "place_of_service": "22"},
            {"allowed_amount": 900, "place_of_service": "22"},
            {"allowed_amount": 500, "place_of_service": "19"},
        ]
    )
    assert (sos["baseline_paid"], sos["post_policy_paid"], sos["payment_impact"]) == (4000, 3480, 520)

    ptp = oracle_ptp(
        [
            {"claim_id": "ptp1", "role": "column_one", "allowed_amount": 800, "modifier": None},
            {"claim_id": "ptp1", "role": "column_two", "allowed_amount": 400, "modifier": None},
            {"claim_id": "ptp2", "role": "column_one", "allowed_amount": 800, "modifier": None},
            {"claim_id": "ptp2", "role": "column_two", "allowed_amount": 400, "modifier": None},
            {"claim_id": "ptp3", "role": "column_one_only", "allowed_amount": 800, "modifier": None},
            {"claim_id": "ptp4", "role": "column_one", "allowed_amount": 800, "modifier": None},
            {"claim_id": "ptp4", "role": "column_two", "allowed_amount": 400, "modifier": "59"},
        ]
    )
    assert (ptp["baseline_paid"], ptp["post_policy_paid"], ptp["payment_impact"]) == (4400, 3600, 800)
    assert ptp["ptp_pairs_hit"] == 3
    assert ptp["ptp_pairs_bypassed_with_modifier"] == 1

    mue = oracle_mue(
        [
            {"units": 6, "allowed_per_unit": 50},
            {"units": 3, "allowed_per_unit": 50},
            {"units": 4, "allowed_per_unit": 50},
        ]
    )
    assert (mue["baseline_paid"], mue["post_policy_paid"], mue["payment_impact"]) == (650, 550, 100)
    assert "Not a CMS MUE" in mue["mue_value_note"]

    therapy = oracle_therapy(
        [
            {"units": 5, "allowed_per_unit": 40, "medically_necessary_units": 3},
            {"units": 4, "allowed_per_unit": 35, "medically_necessary_units": 4},
            {"units": 2, "allowed_per_unit": 40, "medically_necessary_units": 2},
        ]
    )
    assert (therapy["baseline_paid"], therapy["post_policy_paid"], therapy["payment_impact"]) == (420, 340, 80)

    infusion = oracle_infusion(
        [
            {"site": "HOPD", "allowed_amount": 5000},
            {"site": "HOPD", "allowed_amount": 5000},
            {"site": "ASC_OR_OFFICE", "allowed_amount": 3200},
            {"site": "HOPD", "allowed_amount": 5000},
        ]
    )
    assert (infusion["baseline_paid"], infusion["post_policy_paid"], infusion["payment_impact"]) == (18200, 14600, 3600)


def test_missing_denominator_and_nonpositive_baseline_stay_null():
    assert rate_per_exposure(100, 0) is None
    assert rate_per_exposure(None, 12) is None
    assert percent_change(0, 10) is None
    assert percent_change(None, 10) is None


def test_scenarios_cover_favorable_neutral_and_adverse():
    lines = [
        {"allowed_amount": 1000, "place_of_service": "22"},
        {"allowed_amount": 500, "place_of_service": "11"},
    ]
    assert oracle_sos(lines, hospital_pct=0.8)["payment_impact"] > 0
    assert oracle_sos(lines, hospital_pct=1.0)["payment_impact"] == 0
    assert oracle_sos(lines, hospital_pct=1.1)["payment_impact"] < 0


def test_small_pilot_reconciles_exposure_and_does_not_score_a_verdict():
    report = run_pilot(200, seed=20261106)
    assert report["status"] == "PASS", report["failures"]
    assert report["lives_enrolled_on_reference_date"] == 200
    assert report["exposure"]["member_months"] != 200 * 33
    assert report["non_user_members"] > 0
    for journey in report["journeys"]:
        assert journey["screen_verdict"] == "INCONCLUSIVE"
        assert journey["real_world_savings"] is False
        assert journey["evidence_class"] == "SYNTHETIC_ILLUSTRATIVE"
    assert report["oracle"]["mri"]["execution_status"] == "NOT_MEASURABLE"
    assert report["oracle"]["mri"]["payment_impact"] is None
    assert report["oracle"]["ncd"]["execution_status"] == "NOT_MEASURABLE"
    assert report["oracle"]["lcd"]["execution_status"] == "NOT_MEASURABLE"
    assert report["oracle"]["sos_neutral"]["payment_impact"] == 0
    assert report["oracle"]["sos_adverse"]["payment_impact"] < 0
    assert report["oracle"]["mppr_favorable"]["payment_impact"] > 0
