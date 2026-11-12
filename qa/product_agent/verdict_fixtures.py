"""Controlled endpoint-contract verdict fixtures.

Offline only. Does not write staging or production verdicts.
"""
from __future__ import annotations

from uepi_api.verdict import compute_verdict


def run_verdict_fixtures() -> list[dict]:
    cases = [
        {
            "id": "no-endpoints-inconclusive",
            "comparisons": {"vs_baseline": {"utilization_change_pct": -20, "cost_change_pct": -5}},
            "endpoints": None,
            "expect": "INCONCLUSIVE",
        },
        {
            "id": "empty-endpoints-inconclusive",
            "comparisons": {"vs_baseline": {"utilization_change_pct": -20}},
            "endpoints": [],
            "expect": "INCONCLUSIVE",
        },
        {
            "id": "endpoint-met-on-track",
            "comparisons": {
                "vs_baseline": {
                    "utilization_change_pct": -20,
                    "cost_change_pct": -8,
                }
            },
            "endpoints": [
                {"metric_id": "utilization_per_1k", "direction": "decrease"},
                {"metric_id": "allowed_pmpm", "direction": "decrease"},
            ],
            "expect": "ON_TRACK",
        },
        {
            "id": "endpoint-missed-at-risk-or-backfire",
            "comparisons": {
                "vs_baseline": {
                    "utilization_change_pct": 12,
                    "cost_change_pct": 4,
                }
            },
            "endpoints": [
                {"metric_id": "utilization_per_1k", "direction": "decrease"},
            ],
            "behavioral": {"risk_factors": ["access complaint"]},
            "expect_in": {"AT_RISK", "BACKFIRE"},
        },
        {
            "id": "endpoint-missing-measure-inconclusive",
            "comparisons": {"vs_baseline": {}},
            "endpoints": [{"metric_id": "utilization_per_1k", "direction": "decrease"}],
            "expect": "INCONCLUSIVE",
        },
    ]
    results = []
    for case in cases:
        status, reason, recommendation = compute_verdict(
            case["comparisons"],
            case.get("behavioral") or {},
            required_endpoints=case["endpoints"],
        )
        if "expect_in" in case:
            ok = status in case["expect_in"]
            expected = sorted(case["expect_in"])
        else:
            ok = status == case["expect"]
            expected = case["expect"]
        results.append(
            {
                "id": case["id"],
                "status": status,
                "expected": expected,
                "result": "pass" if ok else "fail",
                "reason": reason,
                "recommendation": recommendation,
            }
        )
    return results
