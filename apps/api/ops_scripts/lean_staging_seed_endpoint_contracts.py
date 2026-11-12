#!/usr/bin/env python3
"""Seed measurement.required_endpoints on lean-stg policies and recompute verdicts.

Nine mock policies get decrease endpoints for util + cost. Other active policies
get the same default decrease contract so stored verdicts are not all
INCONCLUSIVE for lack of a contract.
Refuses non-hfleanstg databases.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import UUID

import psycopg2
from psycopg2.extras import Json, RealDictCursor

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "docs/production/releases/corrections/reviewed_248/ENDPOINT_CONTRACT_SEED_REPORT.json"
TENANT = "00000000-0000-0000-0000-000000000001"

DEFAULT_ENDPOINTS = [
    {
        "metric_id": "utilization_per_1k",
        "direction": "decrease",
        "label": "Utilization per 1k (enrollment MM when measured)",
    },
    {
        "metric_id": "allowed_pmpm",
        "direction": "decrease",
        "label": "Allowed PMPM (enrollment MM when measured)",
    },
]

# Policy-name heuristics for non-decrease objectives (access / screening style)
INCREASE_NAME_HINTS = (
    "screening",
    "preventive",
    "vaccine",
    "immunization",
    "colonoscopy access",
)


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


def _endpoints_for(name: str) -> list:
    lower = (name or "").lower()
    if any(h in lower for h in INCREASE_NAME_HINTS):
        return [
            {
                "metric_id": "utilization_per_1k",
                "direction": "increase",
                "label": "Utilization per 1k (access/screening objective)",
            },
            {
                "metric_id": "allowed_pmpm",
                "direction": "monitor_only",
                "label": "Allowed PMPM monitored only",
            },
        ]
    return list(DEFAULT_ENDPOINTS)


def main() -> int:
    import sys

    sys.path.insert(0, str(REPO / "apps/api/src"))
    from uepi_api.verdict import compute_verdict

    conn = psycopg2.connect(_db_url())
    conn.autocommit = False
    policies_seeded = 0
    verdicts_updated = 0
    verdict_counts: Dict[str, int] = {}
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, name, policy_metadata_json
                FROM policies
                WHERE tenant_id = %s
                  AND COALESCE(status, 'ACTIVE') <> 'RETIRED'
                """,
                (TENANT,),
            )
            policies = cur.fetchall()
            for row in policies:
                meta = _as_dict(row["policy_metadata_json"])
                measurement = meta.get("measurement") if isinstance(meta.get("measurement"), dict) else {}
                existing = measurement.get("required_endpoints") or meta.get("required_endpoints")
                if isinstance(existing, list) and existing:
                    endpoints = existing
                else:
                    endpoints = _endpoints_for(row["name"] or "")
                    measurement = dict(measurement)
                    measurement["required_endpoints"] = endpoints
                    meta = dict(meta)
                    meta["measurement"] = measurement
                    meta["required_endpoints"] = endpoints
                    cur.execute(
                        """
                        UPDATE policies
                        SET policy_metadata_json = %s
                        WHERE id = %s AND tenant_id = %s
                        """,
                        (Json(meta), row["id"], TENANT),
                    )
                    policies_seeded += 1

                cur.execute(
                    """
                    SELECT id, comparisons_json, behavioral_explanation_json
                    FROM observations
                    WHERE tenant_id = %s AND policy_id = %s
                    """,
                    (TENANT, row["id"]),
                )
                for obs in cur.fetchall():
                    comparisons = _as_dict(obs["comparisons_json"])
                    behavioral = _as_dict(obs.get("behavioral_explanation_json"))
                    status, reason, recommendation = compute_verdict(
                        comparisons,
                        behavioral,
                        required_endpoints=endpoints,
                    )
                    verdict_counts[status] = verdict_counts.get(status, 0) + 1
                    cur.execute(
                        """
                        UPDATE observations
                        SET verdict_status = %s,
                            verdict_reason = %s,
                            recommendation = %s,
                            verdict_rule_version = %s
                        WHERE id = %s AND tenant_id = %s
                        """,
                        (status, reason, recommendation, "v1.1-endpoints", obs["id"], TENANT),
                    )
                    verdicts_updated += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    report = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "policies_seeded": policies_seeded,
        "verdicts_updated": verdicts_updated,
        "verdict_counts": verdict_counts,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
