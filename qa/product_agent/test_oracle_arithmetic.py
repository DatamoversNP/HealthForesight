"""Offline regression for the QA oracle. Does not call the application."""
from decimal import Decimal

from qa.product_agent.oracle import (
    PAYMENT_FIXTURES,
    continuation_prediction,
    fixture_identity,
    per_member_month_difference,
    periods_are_directly_comparable,
    separate_rollup,
)


def test_continuation_scales_exposure():
    assert continuation_prediction(1000, 10, 4) == Decimal("400.00")


def test_per_member_month_difference():
    assert per_member_month_difference(800, 1000, 200) == Decimal("-1")


def test_unequal_windows_are_not_directly_comparable():
    assert periods_are_directly_comparable(18, 14) is False
    assert periods_are_directly_comparable(12, 12) is True


def test_payment_and_continuation_stay_separate():
    rolled = separate_rollup([
        {"cost_change_kind": "observed_post_period_allowed_difference_per_enrolled_member_month", "cost_change": -1.5},
        {"cost_change_kind": "observed_post_period_allowed_difference_per_enrolled_member_month", "cost_change": -0.54},
        {"cost_change_kind": "observed_versus_frozen_continuation_per_enrolled_member_month", "cost_change": -15.78},
    ])
    assert rolled["payment_sum"] == -2.04
    assert rolled["payment_count"] == 2
    assert rolled["continuation_sum"] == -15.78
    assert rolled["continuation_count"] == 1


def test_published_fixtures_hold():
    for name in PAYMENT_FIXTURES:
        assert fixture_identity(name)
    assert PAYMENT_FIXTURES["mue_demo_cap_4"]["cms_mue"] is False
