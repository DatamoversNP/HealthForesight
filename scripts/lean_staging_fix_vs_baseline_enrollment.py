#!/usr/bin/env python3
"""Rebuild observation vs_baseline after enrollment denominator rescale.

Uses enrollment-scaled baseline metrics for the baseline side so measured %
are not claimant-vs-enrollment apples-to-oranges.
Refuses non-hfleanstg databases.
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import psycopg2
from psycopg2.extras import Json, RealDictCursor

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/production/releases/corrections/reviewed_248/VS_BASELINE_ENROLLMENT_FIX_REPORT.json"
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


def _pct(delta: Optional[float], base: Optional[float]) -> Optional[float]:
    if delta is None or base in (None, 0):
        return None
    return (delta / float(base)) * 100.0


def main() -> int:
    conn = psycopg2.connect(_db_url())
    conn.autocommit = False
    updated = 0
    skipped = 0
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, baseline_metrics_json
                FROM baselines
                WHERE tenant_id = %s
                """,
                (TENANT,),
            )
            baselines = {str(r["id"]): _as_dict(r["baseline_metrics_json"]) for r in cur.fetchall()}

            cur.execute(
                """
                SELECT id, baseline_version_id, metrics_json, comparisons_json
                FROM observations
                WHERE tenant_id = %s
                """,
                (TENANT,),
            )
            for row in cur.fetchall():
                metrics = _as_dict(row["metrics_json"])
                comparisons = _as_dict(row["comparisons_json"])
                bid = str(row["baseline_version_id"]) if row["baseline_version_id"] else None
                bmetrics = baselines.get(bid or "", {})
                if not bmetrics:
                    skipped += 1
                    continue

                obs_util = metrics.get("utilization_per_1k")
                obs_pmpm = metrics.get("allowed_pmpm")
                obs_paid = metrics.get("paid_pmpm")
                base_util = bmetrics.get("utilization_per_1k")
                base_pmpm = bmetrics.get("allowed_pmpm")
                base_paid = bmetrics.get("paid_pmpm") or bmetrics.get("cost_pmpm")
                base_mm = bmetrics.get("member_months")
                obs_mm = metrics.get("member_months")

                util_change = (
                    None
                    if obs_util is None or base_util is None
                    else float(obs_util) - float(base_util)
                )
                cost_change = (
                    None
                    if obs_pmpm is None or base_pmpm is None
                    else float(obs_pmpm) - float(base_pmpm)
                )
                vb = comparisons.get("vs_baseline") if isinstance(comparisons.get("vs_baseline"), dict) else {}
                vb = dict(vb)
                vb.update(
                    {
                        "observed_utilization_per_1k": obs_util,
                        "baseline_utilization_per_1k": base_util,
                        "utilization_change": util_change,
                        "utilization_change_pct": _pct(util_change, float(base_util) if base_util is not None else None),
                        "change_from_baseline": util_change,
                        "change_from_baseline_pct": _pct(util_change, float(base_util) if base_util is not None else None),
                        "observed_cost_pmpm": obs_pmpm,
                        "baseline_cost_pmpm": base_pmpm,
                        "cost_change_pmpm": cost_change,
                        "cost_change_pct": _pct(cost_change, float(base_pmpm) if base_pmpm is not None else None),
                        "baseline_member_months": obs_mm if obs_mm else base_mm,
                        "denominator_basis": "ENROLLMENT",
                        "note": (
                            "Observed vs CY baseline at enrollment member-months. "
                            "Not policy-attributable savings."
                        ),
                        "comparison_by_measure": {
                            "util_rate_total_per_1000_mm": {
                                "baseline": base_util,
                                "observed": obs_util,
                            },
                            "allowed_pmpm_total": {
                                "baseline": base_pmpm,
                                "observed": obs_pmpm,
                            },
                            "paid_pmpm_total": {
                                "baseline": base_paid,
                                "observed": obs_paid,
                            },
                            "member_months": {"baseline": base_mm, "observed": obs_mm},
                        },
                    }
                )
                comparisons = dict(comparisons)
                comparisons["vs_baseline"] = vb
                comparisons["policy_effect"] = comparisons.get("policy_effect") or "UNESTIMATED"
                comparisons["vs_baseline_enrollment_fixed_at"] = datetime.now(timezone.utc).isoformat()

                cur.execute(
                    """
                    UPDATE observations
                    SET comparisons_json = %s
                    WHERE id = %s AND tenant_id = %s
                    """,
                    (Json(comparisons), row["id"], TENANT),
                )
                updated += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    report = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "updated": updated,
        "skipped_no_baseline": skipped,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
