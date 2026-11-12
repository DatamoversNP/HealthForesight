"""Independent payment-engine verification from claim lines.

Uses uepi_common.synthetic_payer.oracle only. Does not read stored payment totals
as expected answers, and does not call the application engine modules.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional

from uepi_common.synthetic_payer.oracle import (
    oracle_infusion_by_claim,
    oracle_mppr,
    oracle_mue,
    oracle_ptp,
    oracle_sos,
    oracle_therapy,
)

PAYMENT_KEYS = ("mppr", "sos", "ptp", "mue", "therapy", "infusion")
ORACLES: dict[str, Callable[[list[dict[str, Any]]], dict[str, Any]]] = {
    "mppr": lambda lines: oracle_mppr(lines, 0.5),
    "sos": lambda lines: oracle_sos(lines, 0.8),
    "ptp": lambda lines: oracle_ptp(lines, "1"),
    "mue": lambda lines: oracle_mue(lines, 4),
    "therapy": oracle_therapy,
    "infusion": lambda lines: oracle_infusion_by_claim(lines, office_allowed=3200.0, steer_hopd_count=1),
}


def load_period_lines(cur, tenant_id: str, policy_key: str, period: str) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT claim_id, claim_line_id, cpt_code, allowed_amount, paid_amount,
               member_cost_share, units, place_of_service, record_hash
        FROM claims_lines
        WHERE tenant_id = %s
          AND source_system = 'SYNTHETIC_LONGITUDINAL_V1'
          AND service_category = %s
        """,
        (tenant_id, policy_key),
    )
    out: list[dict[str, Any]] = []
    for row in cur.fetchall():
        extra = json.loads(row[8] or "{}")
        if extra.get("period") != period or extra.get("line_status") != "ACTIVE":
            continue
        if extra.get("policy_key") != policy_key:
            continue
        out.append(
            {
                "claim_id": row[0],
                "claim_line_id": row[1],
                "cpt_code": row[2],
                "allowed_amount": float(row[3]),
                "paid_amount": float(row[4]),
                "member_cost_share": float(row[5]),
                "units": float(row[6]),
                "place_of_service": row[7],
                **extra,
            }
        )
    return out


def verify_payment_simulations(
    cur,
    tenant_id: str,
    observations_by_key: dict[str, dict[str, Any]],
    *,
    tolerance: float = 0.02,
) -> list[dict[str, Any]]:
    """Compare independent oracle impacts to stored observation impacts."""
    rows = []
    for key in PAYMENT_KEYS:
        pre_lines = load_period_lines(cur, tenant_id, key, "PRE")
        post_lines = load_period_lines(cur, tenant_id, key, "POST")
        pre = ORACLES[key](pre_lines)
        post = ORACLES[key](post_lines)
        stored = observations_by_key.get(key) or {}
        vs_predicted = (stored.get("comparisons") or {}).get("vs_predicted") or {}
        stored_pre = vs_predicted.get("frozen_prediction_impact")
        stored_post = vs_predicted.get("observed_impact")
        pre_delta = None if stored_pre is None else float(pre["payment_impact"]) - float(stored_pre)
        post_delta = None if stored_post is None else float(post["payment_impact"]) - float(stored_post)
        ok = (
            stored_pre is not None
            and stored_post is not None
            and abs(pre_delta or 99) <= tolerance
            and abs(post_delta or 99) <= tolerance
        )
        rows.append(
            {
                "policy_key": key,
                "pre_lines": len(pre_lines),
                "post_lines": len(post_lines),
                "oracle_pre_impact": pre["payment_impact"],
                "oracle_post_impact": post["payment_impact"],
                "oracle_pre_baseline_allowed": pre["baseline_paid"],
                "oracle_post_baseline_allowed": post["baseline_paid"],
                "stored_frozen_prediction_impact": stored_pre,
                "stored_observed_impact": stored_post,
                "pre_delta": pre_delta,
                "post_delta": post_delta,
                "result": "pass" if ok else "fail",
                "expected_from_stored_totals": False,
            }
        )
    return rows
