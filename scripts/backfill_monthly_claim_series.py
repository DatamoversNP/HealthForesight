"""Attach monthly allowed series that reconcile to stored period totals.

Reads claims_lines on the staging database only. A series is written only when
the monthly sum matches the stored baseline total or the stored observed allowed.
No monthly prediction path is created.
"""
from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from decimal import Decimal
from urllib.parse import urlparse

TENANT = "00000000-0000-0000-0000-000000000001"
CUTOFF = "2025-07-01"
TOLERANCE = Decimal("1.00")


def _database_url() -> str:
    raw = subprocess.check_output(
        [
            "az", "keyvault", "secret", "show",
            "--vault-name", "hfleanstgkv",
            "--name", "lean-staging-database-url",
            "--query", "value", "-o", "tsv",
        ],
        text=True,
    ).strip()
    url = raw.replace("postgresql+psycopg2://", "postgresql://", 1)
    host = urlparse(url).hostname or ""
    if host != "hfleanstg-pg.postgres.database.azure.com":
        raise SystemExit(f"refusing host {host}")
    return url


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def main() -> None:
    import psycopg2
    from psycopg2.extras import Json

    conn = psycopg2.connect(_database_url())
    cur = conn.cursor()
    cur.execute(
        """
        SELECT service_category,
               to_char(date_trunc('month', service_date), 'YYYY-MM-DD'),
               COUNT(*)::int,
               ROUND(COALESCE(SUM(allowed_amount), 0)::numeric, 2)
        FROM claims_lines
        WHERE tenant_id = %s AND service_category IS NOT NULL
        GROUP BY 1, 2
        """,
        (TENANT,),
    )
    by_category: dict[str, list[tuple[str, int, Decimal]]] = defaultdict(list)
    for category, month, lines, allowed in cur.fetchall():
        by_category[category].append((month, int(lines), _money(allowed)))

    cur.execute(
        """
        SELECT baseline_id, policy_id::text, baseline_metrics_json
        FROM baselines
        WHERE tenant_id = %s
        """,
        (TENANT,),
    )
    baselines = cur.fetchall()
    cur.execute(
        """
        SELECT observation_id, policy_id::text, metrics_json, comparisons_json
        FROM observations
        WHERE tenant_id = %s
        """,
        (TENANT,),
    )
    observations = {
        policy_id: (observation_id, metrics if isinstance(metrics, dict) else {}, comparisons if isinstance(comparisons, dict) else {})
        for observation_id, policy_id, metrics, comparisons in cur.fetchall()
    }

    baseline_updated = 0
    observation_updated = 0
    baseline_mismatch = 0
    observation_mismatch = 0
    missing_category = 0
    for baseline_id, policy_id, metrics in baselines:
        if not isinstance(metrics, dict):
            continue
        key = metrics.get("policy_key")
        if not key or key not in by_category:
            missing_category += 1
            continue
        months = by_category[key]
        pre = [row for row in months if row[0] < CUTOFF]
        post = [row for row in months if row[0] >= CUTOFF]
        pre_sum = sum((row[2] for row in pre), Decimal("0.00"))
        stored = _money(metrics.get("total_allowed"))
        if abs(pre_sum - stored) > TOLERANCE:
            baseline_mismatch += 1
            continue
        metrics = dict(metrics)
        metrics["time_series"] = [
            {"date": month, "observed": float(allowed), "line_count": lines}
            for month, lines, allowed in pre
        ]
        metrics["time_series_method"] = "MONTHLY_ALLOWED_BY_SERVICE_CATEGORY"
        metrics["time_series_reconciled_to"] = "total_allowed"
        cur.execute(
            "UPDATE baselines SET baseline_metrics_json = %s WHERE baseline_id = %s",
            (Json(metrics), baseline_id),
        )
        baseline_updated += 1
        obs = observations.get(policy_id)
        if not obs:
            continue
        observation_id, obs_metrics, comparisons = obs
        observed = _money(((comparisons.get("vs_predicted") or {}).get("observed_allowed")))
        post_sum = sum((row[2] for row in post), Decimal("0.00"))
        if abs(post_sum - observed) > TOLERANCE:
            observation_mismatch += 1
            continue
        obs_metrics = dict(obs_metrics)
        obs_metrics["time_series"] = [
            {"date": month, "observed": float(allowed), "line_count": lines}
            for month, lines, allowed in post
        ]
        obs_metrics["time_series_method"] = "MONTHLY_ALLOWED_BY_SERVICE_CATEGORY"
        obs_metrics["time_series_reconciled_to"] = "observed_allowed"
        cur.execute(
            "UPDATE observations SET metrics_json = %s WHERE observation_id = %s",
            (Json(obs_metrics), observation_id),
        )
        observation_updated += 1

    cur.execute(
        """
        UPDATE policy_predicted_impacts
        SET metrics_json = jsonb_set(
              metrics_json,
              '{metrics,monthly_series_status}',
              %s::jsonb,
              true
            )
        WHERE tenant_id = %s
          AND metrics_json->'metrics'->>'method' = 'SYNTHETIC_EXPOSURE_CONTINUATION_PRE_FREEZE'
          AND NOT (metrics_json->'metrics' ? 'monthly_series')
        """,
        (json.dumps("NOT_CALCULATED"), TENANT),
    )
    prediction_marked = cur.rowcount
    conn.commit()
    print(json.dumps({
        "categories": len(by_category),
        "baselines": len(baselines),
        "baseline_updated": baseline_updated,
        "observation_updated": observation_updated,
        "baseline_mismatch": baseline_mismatch,
        "observation_mismatch": observation_mismatch,
        "missing_category": missing_category,
        "prediction_marked_not_monthly": prediction_marked,
    }))
    conn.close()


if __name__ == "__main__":
    main()
