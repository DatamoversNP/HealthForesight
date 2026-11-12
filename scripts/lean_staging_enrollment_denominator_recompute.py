#!/usr/bin/env python3
"""Recompute lean-stg baseline/observation rates onto enrollment member-months.

Keeps stored numerators (claims/allowed/paid); replaces claimant MM with
enrollment exposure and stamps denominator_basis=ENROLLMENT.
Refuses non-hfleanstg databases.
"""
from __future__ import annotations

import json
import subprocess
from calendar import monthrange
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import psycopg2
from psycopg2.extras import Json, RealDictCursor

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/production/releases/corrections/reviewed_248/ENROLLMENT_DENOM_RECOMPUTE_REPORT.json"
TENANT = "00000000-0000-0000-0000-000000000001"


def _db_url() -> str:
    import os

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
    return (delta / base) * 100.0


def _enrollment_mm(cur, start: date, end: date) -> Optional[float]:
    """Sum capped covered-day fractions for months overlapping [start, end]."""
    month_start = date(start.year, start.month, 1)
    month_end = date(end.year, end.month, 1)
    cur.execute(
        """
        SELECT COALESCE(SUM(
            LEAST(
                GREATEST(
                    (
                        LEAST(enrollment_end_date, (date_trunc('month', enrollment_month) + interval '1 month')::date)
                        - GREATEST(enrollment_start_date, enrollment_month)
                    )
                    + COALESCE(
                        CASE
                          WHEN segment ~ '^GAP_DAYS:' THEN NULLIF(substring(segment from 10), '')::int
                          ELSE 0
                        END,
                        0
                    ),
                    0
                )::numeric
                / EXTRACT(day FROM (date_trunc('month', enrollment_month) + interval '1 month' - date_trunc('month', enrollment_month)))::numeric,
                1.0
            )
        ), 0)
        FROM enrollment_records
        WHERE tenant_id = %s
          AND enrollment_month >= %s
          AND enrollment_month <= %s
          AND enrollment_start_date IS NOT NULL
          AND enrollment_end_date IS NOT NULL
        """,
        (TENANT, month_start, month_end),
    )
    row = cur.fetchone()
    if row is None:
        return None
    val = row[0] if not isinstance(row, dict) else next(iter(row.values()))
    if val is None or float(val) <= 0:
        return None
    return float(val)


def _rescale_metrics(metrics: Dict[str, Any], new_mm: float) -> Dict[str, Any]:
    m = dict(metrics)
    services = float(m.get("services") or m.get("total_claims") or 0)
    allowed = float(m.get("allowed_amount") or m.get("total_allowed") or 0)
    paid = float(m.get("paid_amount") or m.get("total_paid") or 0)
    m["member_months"] = new_mm
    m["eligible_member_months"] = new_mm
    m["denominator_basis"] = "ENROLLMENT"
    m["exposure_method"] = "ENROLLMENT_DISTINCT_COVERED_DAYS"
    m["enrollment_measured"] = True
    m["utilization_per_1k"] = (services / new_mm * 1000.0) if new_mm else None
    m["allowed_pmpm"] = (allowed / new_mm) if new_mm else None
    m["paid_pmpm"] = (paid / new_mm) if new_mm else None
    m["cost_pmpm"] = m["paid_pmpm"]
    m["prior_claimant_member_months"] = metrics.get("member_months")
    m["enrollment_recomputed_at"] = datetime.now(timezone.utc).isoformat()
    return m


def main() -> int:
    conn = psycopg2.connect(_db_url())
    conn.autocommit = False
    baselines_updated = 0
    observations_updated = 0
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Cache common windows
            mm_cache: Dict[Tuple[str, str], Optional[float]] = {}

            def mm_for(start: Optional[date], end: Optional[date]) -> Optional[float]:
                if not start or not end:
                    return None
                key = (start.isoformat(), end.isoformat())
                if key not in mm_cache:
                    mm_cache[key] = _enrollment_mm(cur, start, end)
                return mm_cache[key]

            cur.execute(
                """
                SELECT id, window_start_date, window_end_date, baseline_metrics_json
                FROM baselines
                WHERE tenant_id = %s
                """,
                (TENANT,),
            )
            for row in cur.fetchall():
                metrics = _as_dict(row["baseline_metrics_json"])
                if metrics.get("denominator_basis") == "ENROLLMENT" and metrics.get("enrollment_measured"):
                    continue
                start = row["window_start_date"]
                end = row["window_end_date"]
                if hasattr(start, "date"):
                    start = start.date()
                if hasattr(end, "date"):
                    end = end.date()
                if isinstance(start, datetime):
                    start = start.date()
                if isinstance(end, datetime):
                    end = end.date()
                new_mm = mm_for(start, end)
                if not new_mm:
                    continue
                new_metrics = _rescale_metrics(metrics, new_mm)
                cur.execute(
                    """
                    UPDATE baselines
                    SET baseline_metrics_json = %s
                    WHERE id = %s AND tenant_id = %s
                    """,
                    (Json(new_metrics), row["id"], TENANT),
                )
                baselines_updated += 1

            cur.execute(
                """
                SELECT id, observation_period_start, observation_period_end,
                       metrics_json, comparisons_json
                FROM observations
                WHERE tenant_id = %s
                """,
                (TENANT,),
            )
            for row in cur.fetchall():
                metrics = _as_dict(row["metrics_json"])
                if metrics.get("denominator_basis") == "ENROLLMENT" and metrics.get("enrollment_measured"):
                    continue
                start = row["observation_period_start"]
                end = row["observation_period_end"]
                if hasattr(start, "date"):
                    start = start.date()
                if hasattr(end, "date"):
                    end = end.date()
                new_mm = mm_for(start, end)
                if not new_mm:
                    continue
                new_metrics = _rescale_metrics(metrics, new_mm)
                comparisons = _as_dict(row["comparisons_json"])
                vb = comparisons.get("vs_baseline") if isinstance(comparisons.get("vs_baseline"), dict) else None
                if vb:
                    obs_util = new_metrics.get("utilization_per_1k")
                    obs_pmpm = new_metrics.get("allowed_pmpm")
                    base_util = vb.get("baseline_utilization_per_1k")
                    base_pmpm = vb.get("baseline_cost_pmpm")
                    util_change = (
                        None if obs_util is None or base_util is None else float(obs_util) - float(base_util)
                    )
                    cost_change = (
                        None if obs_pmpm is None or base_pmpm is None else float(obs_pmpm) - float(base_pmpm)
                    )
                    vb = dict(vb)
                    vb["observed_utilization_per_1k"] = obs_util
                    vb["observed_cost_pmpm"] = obs_pmpm
                    vb["utilization_change"] = util_change
                    vb["utilization_change_pct"] = _pct(util_change, float(base_util) if base_util is not None else None)
                    vb["cost_change_pmpm"] = cost_change
                    vb["cost_change_pct"] = _pct(cost_change, float(base_pmpm) if base_pmpm is not None else None)
                    vb["baseline_member_months"] = new_mm
                    vb["denominator_basis"] = "ENROLLMENT"
                    vb["note"] = (
                        "Observed vs baseline at enrollment member-months. "
                        "Not policy-attributable savings."
                    )
                    comparisons = dict(comparisons)
                    comparisons["vs_baseline"] = vb
                cur.execute(
                    """
                    UPDATE observations
                    SET metrics_json = %s, comparisons_json = %s
                    WHERE id = %s AND tenant_id = %s
                    """,
                    (Json(new_metrics), Json(comparisons), row["id"], TENANT),
                )
                observations_updated += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    report = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "baselines_updated": baselines_updated,
        "observations_updated": observations_updated,
        "denominator_basis": "ENROLLMENT",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
