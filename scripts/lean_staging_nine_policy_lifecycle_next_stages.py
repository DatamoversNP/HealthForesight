#!/usr/bin/env python3
"""
Next lifecycle stages for the nine mock policies on lean staging (5K book).

Already complete: baseline v3, continuation freeze, monthly observations,
embedded reconciliation, INCONCLUSIVE verdicts (no endpoint contract).

This step advances:
  5b. Formal audit of reconciliation/verdict stage
  6. Objectives-health snapshot from persisted rows (no fabricated ON_TRACK)
  7. Evidence packs linking baseline → prediction → observations
  8. What-If continuation exposure sensitivity (does not mutate frozen rows)
  9. Monthly observation schedules for ongoing runs

Does NOT invent endpoints, policy-effect savings, or clinical authority.
Lean staging only. Dec4 demo / production untouched.
"""
from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import Json, RealDictCursor

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "packages" / "common" / "src"))

from uepi_common.lifecycle import (  # noqa: E402
    STATUS_UNESTIMATED,
    compute_whatif_continuation,
)

TENANT = "00000000-0000-0000-0000-000000000001"
BOOK = "SYNTHETIC_NINE_POLICY_5K_V1"
OUT = (
    REPO
    / "docs/production/releases/corrections/nine_mock_policies/NINE_POLICY_LIFECYCLE_NEXT_STAGES_REPORT.json"
)
POLICY_NAMES = [
    "Outpatient MRI Prior Authorization",
    "National Coverage Determination Study — MRI (NCD 220.2)",
    "Local Coverage Determination Study — LCD L34425",
    "Imaging Site-of-Service Policy",
    "Infusion Site-of-Care and Reimbursement Policy",
    "Outpatient Therapy Utilization and Payment Policy",
    "Medically Unlikely Edit (MUE) / Unit Cap",
    "Procedure-to-Procedure (PTP) Coding Edit",
    "Multiple Procedure Payment Reduction (MPPR)",
]


def _database_url() -> str:
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
        raise SystemExit("Refusing: DATABASE_URL is not lean staging.")
    return url


def _audit(cur, *, action: str, object_type: str, object_id: str, diff: Dict[str, Any], meta: Dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO audit_events (
            id, tenant_id, action, object_type, object_id,
            diff_summary, metadata_json, created_at
        ) VALUES (
            %s::uuid, %s::uuid, %s, %s, %s::uuid, %s, %s, %s
        )
        """,
        (
            str(uuid.uuid4()),
            TENANT,
            action,
            object_type,
            object_id,
            Json(diff),
            Json(meta),
            datetime.utcnow(),
        ),
    )


def main() -> int:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    report: Dict[str, Any] = {
        "generated_at": now.isoformat(),
        "database": "hfleanstg",
        "measurement_book": BOOK,
        "stages": {},
        "policies": [],
        "errors": [],
    }

    conn = psycopg2.connect(_database_url())
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT id::text, name, policy_metadata_json AS meta
        FROM policies
        WHERE tenant_id = %s::uuid AND name = ANY(%s)
        ORDER BY name
        """,
        (TENANT, POLICY_NAMES),
    )
    policies = [dict(r) for r in cur.fetchall()]
    if len(policies) != 9:
        report["errors"].append(f"expected_9_got_{len(policies)}")
        OUT.write_text(json.dumps(report, indent=2, default=str))
        return 1

    # Idempotent cleanup of prior next-stage artifacts from this script.
    cur.execute(
        """
        DELETE FROM whatif_scenario_results
        WHERE tenant_id = %s::uuid
          AND analysis_id IN (
            SELECT id FROM analyses
            WHERE tenant_id = %s::uuid
              AND analysis_type = 'WHATIF'
              AND name LIKE 'Nine5K continuation What-If%%'
          )
        """,
        (TENANT, TENANT),
    )
    cur.execute(
        """
        DELETE FROM analyses
        WHERE tenant_id = %s::uuid
          AND analysis_type = 'WHATIF'
          AND name LIKE 'Nine5K continuation What-If%%'
        """,
        (TENANT,),
    )
    cur.execute(
        """
        DELETE FROM evidence
        WHERE tenant_id = %s::uuid
          AND evidence_type = 'POLICY_LIFECYCLE_PACK'
          AND metadata_json->>'measurement_book' = %s
        """,
        (TENANT, BOOK),
    )
    cur.execute(
        """
        DELETE FROM schedules
        WHERE tenant_id = %s::uuid
          AND name LIKE 'Nine5K Monthly Observation%%'
        """,
        (TENANT,),
    )

    whatif_count = 0
    evidence_count = 0
    schedule_count = 0
    objectives_rows: List[Dict[str, Any]] = []

    for row in policies:
        pid = row["id"]
        name = row["name"]

        cur.execute(
            """
            SELECT id::text AS row_id, baseline_id, version, baseline_metrics_json AS metrics
            FROM baselines
            WHERE tenant_id = %s::uuid AND policy_id = %s::uuid
              AND baseline_metrics_json->>'measurement_book' = %s
            ORDER BY version DESC LIMIT 1
            """,
            (TENANT, pid, BOOK),
        )
        baseline = cur.fetchone()
        cur.execute(
            """
            SELECT id::text AS prediction_id, metrics_json AS metrics, prediction_method, predicted_at
            FROM policy_predicted_impacts
            WHERE tenant_id = %s::uuid AND policy_id = %s::uuid
            ORDER BY predicted_at DESC LIMIT 1
            """,
            (TENANT, pid),
        )
        pred = cur.fetchone()
        cur.execute(
            """
            SELECT observation_id,
                   observation_period_start::date AS start,
                   observation_period_end::date AS end,
                   metrics_json AS metrics,
                   comparisons_json AS comparisons,
                   verdict_status
            FROM observations
            WHERE tenant_id = %s::uuid AND policy_id = %s::uuid
              AND observation_id LIKE 'nine5k-%%'
            ORDER BY observation_period_start
            """,
            (TENANT, pid),
        )
        obs_rows = [dict(r) for r in cur.fetchall()]
        if not baseline or not pred or len(obs_rows) != 10:
            report["errors"].append(
                {
                    "policy": name,
                    "error": "incomplete_prior_stages",
                    "baseline": bool(baseline),
                    "prediction": bool(pred),
                    "observations": len(obs_rows),
                }
            )
            continue

        pred_metrics = pred["metrics"] if isinstance(pred["metrics"], dict) else {}
        continuation = pred_metrics.get("continuation") or {}
        effect = pred_metrics.get("policy_effect") or {}
        bmetrics = baseline["metrics"] if isinstance(baseline["metrics"], dict) else {}

        # --- Stage audit: reconciliation + verdict already persisted on observations ---
        _audit(
            cur,
            action="LIFECYCLE_STAGE",
            object_type="POLICY",
            object_id=pid,
            diff={
                "stage": "reconciliation",
                "status": "EXECUTED",
                "observation_months": len(obs_rows),
                "note": "vs_continuation stored on observation.comparisons_json",
            },
            meta={"worker": "lean_staging_nine_policy_lifecycle_next_stages.py", "book": BOOK},
        )
        _audit(
            cur,
            action="LIFECYCLE_STAGE",
            object_type="POLICY",
            object_id=pid,
            diff={
                "stage": "verdict",
                "status": "INCONCLUSIVE",
                "reason": "missing_approved_endpoint_contract",
                "policy_effect": effect.get("status") or STATUS_UNESTIMATED,
            },
            meta={"worker": "lean_staging_nine_policy_lifecycle_next_stages.py", "book": BOOK},
        )

        # --- What-If continuation exposure sensitivity (does not mutate frozen rows) ---
        base_mm = float((continuation.get("horizon_totals") or {}).get("forecast_member_months") or 50000.0)
        scenarios = [
            ("plus10pct_mm", base_mm * 1.10),
            ("minus10pct_mm", base_mm * 0.90),
        ]
        whatif_results = []
        for scenario_id, mm in scenarios:
            wi = compute_whatif_continuation(
                frozen_continuation=continuation,
                scenario_member_months=mm,
                scenario_id=scenario_id,
            )
            analysis_id = str(uuid.uuid4())
            analysis_name = f"Nine5K continuation What-If · {name} · {scenario_id}"
            cur.execute(
                """
                INSERT INTO analyses (
                    id, tenant_id, policy_id, analysis_type, name, status,
                    created_at, updated_at
                ) VALUES (
                    %s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s, %s
                )
                """,
                (
                    analysis_id,
                    TENANT,
                    pid,
                    "WHATIF",
                    analysis_name,
                    "COMPLETED",
                    datetime.utcnow(),
                    datetime.utcnow(),
                ),
            )
            result_payload = {
                "scenario": wi,
                "parent_prediction_id": pred["prediction_id"],
                "parent_prediction_method": pred["prediction_method"],
                "measurement_book": BOOK,
                "invariants": {
                    "mutates_frozen_prediction": False,
                    "mutates_observation": False,
                    "policy_effect": STATUS_UNESTIMATED,
                },
            }
            cur.execute(
                """
                INSERT INTO whatif_scenario_results (
                    id, tenant_id, analysis_id, policy_id,
                    result_data_json, schema_version, created_at, updated_at
                ) VALUES (
                    %s::uuid, %s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s
                )
                """,
                (
                    str(uuid.uuid4()),
                    TENANT,
                    analysis_id,
                    pid,
                    Json(result_payload),
                    "continuation-whatif-v1",
                    datetime.utcnow(),
                    datetime.utcnow(),
                ),
            )
            whatif_results.append(
                {
                    "scenario_id": scenario_id,
                    "analysis_id": analysis_id,
                    "status": wi.get("status"),
                    "scenario_member_months": wi.get("scenario_member_months"),
                    "scenario_continuation_allowed": wi.get("scenario_continuation_allowed"),
                }
            )
            whatif_count += 1

        _audit(
            cur,
            action="LIFECYCLE_STAGE",
            object_type="POLICY",
            object_id=pid,
            diff={"stage": "whatif_continuation", "status": "EXECUTED", "scenarios": len(whatif_results)},
            meta={"worker": "lean_staging_nine_policy_lifecycle_next_stages.py", "book": BOOK},
        )

        # --- Evidence pack ---
        obs_allowed = sum(float((o["metrics"] or {}).get("total_allowed") or 0) for o in obs_rows)
        obs_claims = sum(int((o["metrics"] or {}).get("total_claims") or 0) for o in obs_rows)
        pack = {
            "measurement_book": BOOK,
            "policy_id": pid,
            "policy_name": name,
            "baseline": {
                "row_id": baseline["row_id"],
                "baseline_id": baseline["baseline_id"],
                "version": baseline["version"],
                "member_months": bmetrics.get("member_months"),
                "total_claims": bmetrics.get("total_claims"),
                "total_allowed": bmetrics.get("total_allowed"),
                "allowed_pmpm_target": bmetrics.get("allowed_pmpm_target"),
            },
            "prediction": {
                "prediction_id": pred["prediction_id"],
                "method": pred["prediction_method"],
                "continuation_status": continuation.get("status"),
                "policy_effect_status": effect.get("status") or STATUS_UNESTIMATED,
                "predicted_allowed": (continuation.get("horizon_totals") or {}).get("predicted_allowed"),
                "predicted_services": (continuation.get("horizon_totals") or {}).get("predicted_services"),
            },
            "observations": {
                "count": len(obs_rows),
                "window": [str(obs_rows[0]["start"]), str(obs_rows[-1]["end"])],
                "total_claims": obs_claims,
                "total_allowed": obs_allowed,
                "verdict_status": sorted({o["verdict_status"] for o in obs_rows}),
            },
            "whatif": whatif_results,
            "invariants": {
                "continuation_is_not_policy_effect": True,
                "no_fabricated_endpoints": True,
                "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
            },
        }
        evidence_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO evidence (
                id, tenant_id, resource_type, resource_id, evidence_id,
                evidence_type, uri, metadata_json, created_at, updated_at
            ) VALUES (
                %s::uuid, %s::uuid, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            """,
            (
                str(uuid.uuid4()),
                TENANT,
                "POLICY",
                pid,
                evidence_id,
                "POLICY_LIFECYCLE_PACK",
                f"internal://nine5k/lifecycle/{pid}",
                Json(pack),
                datetime.utcnow(),
                datetime.utcnow(),
            ),
        )
        evidence_count += 1
        _audit(
            cur,
            action="LIFECYCLE_STAGE",
            object_type="POLICY",
            object_id=pid,
            diff={"stage": "evidence", "status": "EXECUTED", "evidence_id": evidence_id},
            meta={"worker": "lean_staging_nine_policy_lifecycle_next_stages.py", "book": BOOK},
        )

        # --- Monthly observation schedule ---
        schedule_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO schedules (
                id, tenant_id, schedule_id, name, description,
                schedule_type, cron_expression, target_type, target_id,
                enabled, next_run_at, created_at, updated_at
            ) VALUES (
                %s::uuid, %s::uuid, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            """,
            (
                str(uuid.uuid4()),
                TENANT,
                schedule_id,
                f"Nine5K Monthly Observation · {name}",
                "Periodic observation for authorized 5K measurement book. Not Dec4 demo.",
                "CRON",
                "0 6 2 * *",  # 06:00 on day 2 each month
                "OBSERVATION",
                pid,
                True,
                datetime(2026, 11, 2, 6, 0, 0),
                datetime.utcnow(),
                datetime.utcnow(),
            ),
        )
        schedule_count += 1

        # Objectives health row (honest: no_data / inconclusive without endpoints)
        objectives_rows.append(
            {
                "policy_id": pid,
                "policy_name": name,
                "objective_health": "no_data",
                "verdict_status": "INCONCLUSIVE",
                "reason": "missing_approved_endpoint_contract",
                "continuation_available": continuation.get("status") == "AVAILABLE",
                "observations_available": True,
                "policy_effect": effect.get("status") or STATUS_UNESTIMATED,
            }
        )
        _audit(
            cur,
            action="LIFECYCLE_STAGE",
            object_type="POLICY",
            object_id=pid,
            diff={
                "stage": "objectives_health",
                "status": "NO_DATA",
                "note": "Objectives remain no_data until an approved endpoint contract exists.",
            },
            meta={"worker": "lean_staging_nine_policy_lifecycle_next_stages.py", "book": BOOK},
        )

        report["policies"].append(
            {
                "policy_id": pid,
                "name": name,
                "baseline_version": baseline["version"],
                "prediction_id": pred["prediction_id"],
                "observations": len(obs_rows),
                "whatif_scenarios": whatif_results,
                "evidence_id": evidence_id,
                "schedule_id": schedule_id,
                "verdict": "INCONCLUSIVE",
                "objectives_health": "no_data",
            }
        )
        print(
            "OK %s whatif=%s evidence=%s schedule=%s"
            % (name, len(whatif_results), evidence_id[:8], schedule_id[:8]),
            flush=True,
        )

    # Tenant-level objectives snapshot as evidence
    obj_evidence_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO evidence (
            id, tenant_id, resource_type, resource_id, evidence_id,
            evidence_type, uri, metadata_json, created_at, updated_at
        ) VALUES (
            %s::uuid, %s::uuid, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
        """,
        (
            str(uuid.uuid4()),
            TENANT,
            "TENANT",
            TENANT,
            obj_evidence_id,
            "OBJECTIVES_HEALTH_SNAPSHOT",
            "internal://nine5k/objectives-health",
            Json(
                {
                    "measurement_book": BOOK,
                    "calculation_version": "objectives-health-v1",
                    "generated_at": now.isoformat(),
                    "policies": objectives_rows,
                    "summary": {
                        "policies": len(objectives_rows),
                        "on_track": 0,
                        "at_risk": 0,
                        "no_data": len(objectives_rows),
                        "note": "INCONCLUSIVE without endpoint contracts; not invented on_track.",
                    },
                }
            ),
            datetime.utcnow(),
            datetime.utcnow(),
        ),
    )

    conn.commit()
    report["stages"] = {
        "reconciliation_audit": len(report["policies"]),
        "verdict_audit": len(report["policies"]),
        "whatif_continuation": whatif_count,
        "evidence_packs": evidence_count,
        "objectives_health_snapshot": obj_evidence_id,
        "observation_schedules": schedule_count,
    }
    report["summary"] = {
        "policies": len(report["policies"]),
        "errors": len(report["errors"]),
        "success": len(report["policies"]) == 9 and not report["errors"],
        "intentionally_not_done": [
            "policy_effect_estimation",
            "endpoint_contract_fabrication",
            "ON_TRACK_verdicts_without_endpoints",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report["summary"], indent=2))
    print("Wrote", OUT)
    cur.close()
    conn.close()
    return 0 if report["summary"]["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
