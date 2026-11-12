#!/usr/bin/env python3
"""Backfill measured-vs-baseline descriptive % onto lean-stg predicted impacts.

Does NOT set policy-effect cost_change_pct / utilization_change_pct.
Meaning: OBSERVED_VS_BASELINE_NOT_ATTRIBUTED. Policy effect stays UNESTIMATED.
Refuses non-hfleanstg databases.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID

import psycopg2
from psycopg2.extras import Json, RealDictCursor

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "docs/production/releases/corrections/reviewed_248/MEASURED_PI_BACKFILL_REPORT.json"
TENANT = "00000000-0000-0000-0000-000000000001"


def _db_url() -> str:
    env = os.environ.get("DATABASE_URL") or os.environ.get("LEAN_STAGING_DATABASE_URL")
    if env:
        url = env.replace("postgresql+psycopg2://", "postgresql://", 1)
        if "hfleanstg" not in url.lower():
            raise SystemExit("Refusing: DATABASE_URL is not lean staging")
        return url
    raw = subprocess.check_output(
        [
            "az",
            "keyvault",
            "secret",
            "show",
            "--vault-name",
            "hfleanstgkv",
            "--name",
            "lean-staging-database-url",
            "--query",
            "value",
            "-o",
            "tsv",
        ],
        text=True,
    ).strip()
    url = raw.replace("postgresql+psycopg2://", "postgresql://", 1)
    if "hfleanstg" not in url.lower():
        raise SystemExit("Refusing: not lean staging")
    return url


def _as_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
    return value if isinstance(value, dict) else {}


def _mean(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def main() -> int:
    url = _db_url()
    conn = psycopg2.connect(url)
    conn.autocommit = False
    updated = 0
    skipped = 0
    with_meas = 0
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (o.policy_id)
                  o.policy_id,
                  o.comparisons_json,
                  o.metrics_json
                FROM observations o
                WHERE o.tenant_id = %s
                ORDER BY o.policy_id, o.observation_period_end DESC NULLS LAST, o.created_at DESC NULLS LAST
                """,
                (TENANT,),
            )
            obs_by_policy = {str(r["policy_id"]): r for r in cur.fetchall()}

            cur.execute(
                """
                SELECT DISTINCT ON (pi.policy_id)
                  pi.id, pi.policy_id, pi.metrics_json
                FROM policy_predicted_impacts pi
                JOIN policies p ON p.id = pi.policy_id AND p.tenant_id = pi.tenant_id
                WHERE pi.tenant_id = %s
                  AND COALESCE(p.status, 'ACTIVE') <> 'RETIRED'
                ORDER BY pi.policy_id, pi.predicted_at DESC NULLS LAST
                """,
                (TENANT,),
            )
            pis = cur.fetchall()

            for row in pis:
                pid = str(row["policy_id"])
                metrics_root = _as_dict(row["metrics_json"])
                # Normalize to nested metrics bag
                if "metrics" in metrics_root and isinstance(metrics_root["metrics"], dict):
                    bag = dict(metrics_root["metrics"])
                    wrap = True
                else:
                    bag = dict(metrics_root)
                    wrap = False

                obs = obs_by_policy.get(pid)
                util_pcts: list[float] = []
                cost_pcts: list[float] = []
                cost_pmpms: list[float] = []
                if obs:
                    comparisons = _as_dict(obs.get("comparisons_json"))
                    vb = comparisons.get("vs_baseline") if isinstance(comparisons.get("vs_baseline"), dict) else {}
                    # Also scan recent observations for a more stable mean
                    cur.execute(
                        """
                        SELECT comparisons_json
                        FROM observations
                        WHERE tenant_id = %s AND policy_id = %s
                        ORDER BY observation_period_end DESC NULLS LAST
                        LIMIT 12
                        """,
                        (TENANT, row["policy_id"]),
                    )
                    for obs_row in cur.fetchall():
                        cmp = _as_dict(obs_row["comparisons_json"])
                        vsb = cmp.get("vs_baseline") if isinstance(cmp.get("vs_baseline"), dict) else {}
                        if vsb.get("utilization_change_pct") is not None:
                            util_pcts.append(float(vsb["utilization_change_pct"]))
                        if vsb.get("cost_change_pct") is not None:
                            cost_pcts.append(float(vsb["cost_change_pct"]))
                        if vsb.get("cost_change_pmpm") is not None:
                            cost_pmpms.append(float(vsb["cost_change_pmpm"]))
                    # Prefer latest if means empty but vb present
                    if not util_pcts and vb.get("utilization_change_pct") is not None:
                        util_pcts.append(float(vb["utilization_change_pct"]))
                    if not cost_pcts and vb.get("cost_change_pct") is not None:
                        cost_pcts.append(float(vb["cost_change_pct"]))
                    if not cost_pmpms and vb.get("cost_change_pmpm") is not None:
                        cost_pmpms.append(float(vb["cost_change_pmpm"]))

                measured_util = _mean(util_pcts)
                measured_cost = _mean(cost_pcts)
                measured_pmpm = _mean(cost_pmpms)

                if measured_util is None and measured_cost is None and measured_pmpm is None:
                    skipped += 1
                    continue

                bag["measured_vs_baseline_utilization_change_pct"] = measured_util
                bag["measured_vs_baseline_cost_change_pct"] = measured_cost
                bag["measured_vs_baseline_cost_change_pmpm"] = measured_pmpm
                bag["measured_vs_baseline_meaning"] = "OBSERVED_VS_BASELINE_NOT_ATTRIBUTED"
                bag["measured_vs_baseline_note"] = (
                    "Descriptive observed-vs-baseline rate change. Not policy-attributable savings."
                )
                bag["measured_vs_baseline_backfilled_at"] = datetime.now(timezone.utc).isoformat()
                # Keep policy-effect fields honest
                bag.setdefault("cost_change_meaning", "UNESTIMATED_POLICY_EFFECT")
                bag.setdefault("utilization_change_meaning", "UNESTIMATED_POLICY_EFFECT")
                bag["policy_effect_status"] = bag.get("policy_effect_status") or "UNESTIMATED"

                if wrap:
                    metrics_root["metrics"] = bag
                    # Also mirror measured_* at root for older readers.
                    for _mk in (
                        "measured_vs_baseline_utilization_change_pct",
                        "measured_vs_baseline_cost_change_pct",
                        "measured_vs_baseline_cost_change_pmpm",
                        "measured_vs_baseline_meaning",
                        "measured_vs_baseline_note",
                        "measured_vs_baseline_backfilled_at",
                        "policy_effect_status",
                    ):
                        if bag.get(_mk) is not None:
                            metrics_root[_mk] = bag[_mk]
                    payload = metrics_root
                else:
                    # Promote into nested metrics for scorecard/get_predicted_impact.
                    payload = {
                        "metrics": bag,
                        **{k: bag[k] for k in bag if k.startswith("measured_") or k == "policy_effect_status"},
                    }

                cur.execute(
                    """
                    UPDATE policy_predicted_impacts
                    SET metrics_json = %s
                    WHERE id = %s AND tenant_id = %s
                    """,
                    (Json(payload), row["id"], TENANT),
                )
                updated += 1
                with_meas += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    report = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "updated": updated,
        "with_measured_fields": with_meas,
        "skipped_no_obs_delta": skipped,
        "note": "Policy-effect % left null/UNESTIMATED; measured_* are descriptive only.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
