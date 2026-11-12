"""Post-period claims are a separate stream from the pre-period claims."""

from datetime import date

from uepi_common.synthetic_payer.generate import generate_population
from uepi_common.synthetic_payer.longitudinal import (
    HYPOTHETICAL_EFFECTIVE,
    generate_period_claims,
    period_bounds_hold,
)


def test_periods_do_not_overlap_and_are_not_copies():
    population = generate_population(400, seed=20261106)
    pre = generate_period_claims(population, "PRE")
    post = generate_period_claims(population, "POST")
    assert period_bounds_hold(pre, "PRE")
    assert period_bounds_hold(post, "POST")
    assert all(date.fromisoformat(row["service_date"]) < HYPOTHETICAL_EFFECTIVE for row in pre)
    assert all(date.fromisoformat(row["service_date"]) >= HYPOTHETICAL_EFFECTIVE for row in post)
    assert len(post) != len(pre)
    pre_allowed = round(sum(row["allowed_amount"] for row in pre), 2)
    post_allowed = round(sum(row["allowed_amount"] for row in post), 2)
    assert post_allowed != pre_allowed
    assert any(row["service_category"] == "PHARMACY" for row in pre + post)
    assert any(row["service_category"] == "INPATIENT" for row in pre + post)
    assert any(row["service_category"] == "EMERGENCY" for row in pre + post)
