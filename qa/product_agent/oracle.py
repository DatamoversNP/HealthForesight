"""Independent measurement checks.

These functions do not import the application calculation modules. They restate
the published contracts: exposure-scaled continuation, separate payment-rule and
continuation sums, and the small payment-rule fixtures.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional


def money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def continuation_prediction(pre_allowed: float, pre_member_months: float, post_member_months: float) -> Optional[Decimal]:
    """Frozen continuation: pre-period allowed times post exposure over pre exposure."""
    if not pre_member_months:
        return None
    return money(float(pre_allowed) * float(post_member_months) / float(pre_member_months))


def per_member_month_difference(observed_allowed: float, predicted_allowed: float, post_member_months: float) -> Optional[Decimal]:
    if not post_member_months:
        return None
    return (Decimal(str(observed_allowed)) - Decimal(str(predicted_allowed))) / Decimal(str(post_member_months))


def periods_are_directly_comparable(baseline_months: Optional[int], observation_months: Optional[int]) -> bool:
    return baseline_months is not None and observation_months is not None and baseline_months == observation_months


def separate_rollup(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Sum stored per-policy differences without mixing continuation and payment rules."""
    payment = []
    continuation = []
    for row in rows:
        kind = row.get("cost_change_kind")
        amount = row.get("cost_change")
        if amount is None:
            continue
        if kind == "observed_post_period_allowed_difference_per_enrolled_member_month":
            payment.append(float(amount))
        elif kind == "observed_versus_frozen_continuation_per_enrolled_member_month":
            continuation.append(float(amount))
    return {
        "payment_sum": None if not payment else float(money(sum(payment))),
        "payment_count": len(payment),
        "continuation_sum": None if not continuation else float(money(sum(continuation))),
        "continuation_count": len(continuation),
    }


# Published fixture answers. These are not the 500k population totals.
PAYMENT_FIXTURES = {
    "mppr": {"baseline_allowed": 3150, "post_allowed": 2550, "impact": 600},
    "sos": {"baseline_allowed": 4000, "post_allowed": 3480, "impact": 520},
    "infusion": {"baseline_allowed": 18200, "post_allowed": 14600, "impact": 3600},
    "ptp": {"baseline_allowed": 4400, "post_allowed": 3600, "impact": 800},
    "mue_demo_cap_4": {"baseline_allowed": 650, "post_allowed": 550, "impact": 100, "cms_mue": False},
    "therapy": {"baseline_allowed": 420, "post_allowed": 340, "impact": 80},
    "dictionary_util_change": {"utilization": 120, "change_pct": -25, "allowed_pmpm": 100, "paid_pmpm": 75, "annualized": 120000},
}


def fixture_identity(name: str) -> bool:
    row = PAYMENT_FIXTURES[name]
    if "impact" in row:
        return row["baseline_allowed"] - row["post_allowed"] == row["impact"]
    return row["allowed_pmpm"] * (1 + row["change_pct"] / 100) == row["paid_pmpm"]
