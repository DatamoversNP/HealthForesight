#!/usr/bin/env python3
"""
Lean staging ONLY: delete policy lifecycle, keep 500k population, seed 250 policies
exactly from HealthForesight_250_Policy_Correction_Register.csv / PDF spec.

Does NOT:
  - touch claims_lines / enrollment_records / member population tables
  - invent CPT/HCPCS/NDC codes
  - create baselines, predictions, observations, or payment simulations
  - touch December 4 demo (healthforesight-rg)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4, uuid5

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api" / "src"))
sys.path.insert(0, str(REPO / "packages" / "common" / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from lean_staging_apply_250_policy_corrections import (  # noqa: E402
    DEFAULT_CSV,
    SPEC_VERSION,
    apply_one,
)

TENANT = UUID("00000000-0000-0000-0000-000000000001")
NAMESPACE = UUID("a7b3c1d0-2500-4000-9e01-c0ffe7100250")

# Population tables that must remain unchanged.
POPULATION_TABLES = (
    "claims_lines",
    "enrollment_records",
)

# Delete order: dependents first. Policies last.
LIFECYCLE_DELETE_ORDER = (
    "scorecard_entries",
    "scorecards",
    "scenario_accuracy",
    "whatif_scenario_results",
    "observations",
    "policy_predicted_impacts",
    "baselines",
    "analyses",
    "elasticity_analysis_results",
    "impact_analysis_results",
    "elasticity_models",
    "forecasts",
    "risks",
    "alert_events",
    "policy_assumptions",
    "policy_guardrails",
    "policy_changelog",
    "policy_decisions",
    "policy_code_sets",
    "policy_versions",
    "scenarios",
    "policies",
)


def _assert_lean_staging(url: str) -> None:
    low = url.lower()
    if "hfleanstg" not in low and "lean" not in low:
        raise SystemExit("Refusing: DATABASE_URL is not lean staging.")
    if "healthforesight-pg" in low and "hfleanstg" not in low:
        raise SystemExit("Refusing: looks like demo/production DB.")


def _counts(cur, tables: tuple[str, ...]) -> dict[str, int]:
    out: dict[str, int] = {}
    for t in tables:
        cur.execute("SELECT to_regclass(%s)", (t,))
        if not cur.fetchone()[0]:
            continue
        cur.execute(f"SELECT count(*) FROM {t}")
        out[t] = int(cur.fetchone()[0])
    return out


def _configuration_state(register_status: str) -> str:
    if register_status == "BLOCK_CLAIMS_EXECUTION_PENDING_REMAP":
        return "BLOCKED"
    if register_status == "REVIEW_REQUIRED_NO_AUTHORITY_CERTIFICATION":
        return "REVIEW_ONLY"
    return "NOT_EXECUTABLE"


def _policy_status(register_status: str) -> str:
    # Catalog-visible, but not implying claims execution.
    if register_status == "REVIEW_REQUIRED_NO_AUTHORITY_CERTIFICATION":
        return "ACTIVE"
    return "ACTIVE"


def seed_policies(cur, register: list[dict[str, str]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    now = datetime.utcnow()
    for row in register:
        idx = int(row["index"])
        name = row["policy"].strip()
        policy_type = (row.get("type") or "ADMINISTRATIVE_REQUIREMENT").strip()
        policy_id = uuid5(NAMESPACE, f"{idx}:{name}")
        empty_meta: dict[str, Any] = {
            "exported_service_category": row.get("exported_service_category"),
            "exported_codes": row.get("exported_codes"),
            "exported_lever": row.get("exported_lever"),
            "scope": {
                "procedure_codes": [],
                "states": None,
                "markets": None,
                "lob": None,
            },
            "policy_levers": [],
            "mock_execution_v1": False,
            "mechanism_executed": False,
            "result_class": "NOT_EXECUTED",
            "evidence_class": "DEFINITION_ONLY",
            "execution": "NOT_IMPLEMENTED",
        }
        meta, ev = apply_one(empty_meta, row, policy_type=policy_type)
        # Honest catalog fields for frontend (no payment/continuation fiction).
        meta["configuration_state"] = _configuration_state(row["status"])
        meta["blocked_reason"] = row["status"]
        meta["mechanism_executed"] = False
        meta["result_class"] = "NOT_EXECUTED"
        meta["evidence_class"] = meta.get("remediation", {}).get("evidence_state") or "DEFINITION_ONLY"
        meta["execution"] = "NOT_IMPLEMENTED"
        meta["mock_execution_v1"] = False
        meta["seed"] = {
            "source": "HealthForesight_250_Policy_Correction_Register.csv",
            "spec_version": SPEC_VERSION,
            "register_index": idx,
            "seeded_at": datetime.now(timezone.utc).isoformat(),
            "lifecycle_seeded": False,
        }
        description = (
            f"{row.get('proposed_mechanism') or ''}\n\n"
            f"Register status: {row['status']}. "
            f"Required coding: {row.get('required_coding_domain') or 'pending'}. "
            "Not claims-executable until authoritative remap."
        ).strip()
        cur.execute(
            """
            INSERT INTO policies (
                id, tenant_id, name, policy_type, owner_role, description,
                status, policy_metadata_json, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s
            )
            """,
            (
                str(policy_id),
                str(TENANT),
                name,
                policy_type,
                "Policy Catalog",
                description,
                _policy_status(row["status"]),
                json.dumps(meta),
                now,
                now,
            ),
        )
        # Assumptions / guardrails tables (workspace reads these).
        for a in meta.get("assumptions") or []:
            cur.execute(
                """
                INSERT INTO policy_assumptions (
                    id, tenant_id, policy_id, assumption_type, description,
                    value, source, confidence, range_json, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s
                )
                """,
                (
                    str(uuid4()),
                    str(TENANT),
                    str(policy_id),
                    a.get("assumption_type") or "IMPACT",
                    a.get("description"),
                    str(a.get("value")) if a.get("value") is not None else None,
                    a.get("source"),
                    a.get("confidence"),
                    json.dumps({"evidence_state": a.get("evidence_state")}),
                    now,
                    now,
                ),
            )
        for g in meta.get("guardrails") or []:
            cur.execute(
                """
                INSERT INTO policy_guardrails (
                    id, tenant_id, policy_id, metric_name, description,
                    threshold_type, threshold_value, action, triggered,
                    last_checked_at, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    str(uuid4()),
                    str(TENANT),
                    str(policy_id),
                    g.get("metric_name"),
                    g.get("description"),
                    g.get("threshold_type") or "review",
                    float(g["threshold_value"]) if g.get("threshold_value") is not None else 0.0,
                    g.get("action") or "manual_review",
                    False,
                    None,
                    now,
                    now,
                ),
            )
        ev["policy_id"] = str(policy_id)
        evidence.append(ev)
    return evidence


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(DEFAULT_CSV))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--report",
        default=str(
            REPO
            / "docs"
            / "production"
            / "releases"
            / "corrections"
            / f"POLICY_RESET_SEED_250_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        ),
    )
    args = ap.parse_args()

    url = os.environ.get("DATABASE_URL") or ""
    _assert_lean_staging(url)

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")
    register = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    if len(register) != 250:
        raise SystemExit(f"Expected 250 register rows, got {len(register)}")
    names = [r["policy"].strip() for r in register]
    if len(set(names)) != 250:
        raise SystemExit("Register has duplicate policy names")

    import psycopg2

    conn = psycopg2.connect(url.replace("postgresql+psycopg2://", "postgresql://", 1))
    conn.autocommit = False
    cur = conn.cursor()
    try:
        cur.execute("SELECT current_database()")
        dbname = cur.fetchone()[0]
        if dbname != "hfleanstg":
            raise SystemExit(f"Refusing unexpected database name: {dbname}")

        before_pop = _counts(cur, POPULATION_TABLES)
        before_life = _counts(cur, LIFECYCLE_DELETE_ORDER)
        print(json.dumps({"phase": "before", "population": before_pop, "lifecycle": before_life}, indent=2))

        if args.dry_run:
            print(json.dumps({"dry_run": True, "would_seed": 250}, indent=2))
            conn.rollback()
            return

        for table in LIFECYCLE_DELETE_ORDER:
            cur.execute("SELECT to_regclass(%s)", (table,))
            if not cur.fetchone()[0]:
                continue
            if table == "baselines":
                # Clear self-FK first.
                cur.execute("UPDATE baselines SET parent_baseline_id = NULL")
            if table == "observations":
                cur.execute(
                    "UPDATE observations SET baseline_version_id = NULL, prediction_id = NULL"
                )
            cur.execute(f"DELETE FROM {table}")
            print(f"deleted {table}: {cur.rowcount}")

        evidence = seed_policies(cur, register)

        after_pop = _counts(cur, POPULATION_TABLES)
        after_life = _counts(cur, ("policies", "policy_assumptions", "policy_guardrails", "observations", "baselines", "policy_predicted_impacts"))
        if after_pop != before_pop:
            raise SystemExit(
                json.dumps(
                    {"population_changed": True, "before": before_pop, "after": after_pop},
                    indent=2,
                )
            )
        if after_life.get("policies") != 250:
            raise SystemExit(f"Expected 250 policies, got {after_life.get('policies')}")
        if after_life.get("observations", 0) != 0 or after_life.get("baselines", 0) != 0:
            raise SystemExit("Lifecycle leftovers remain after seed")

        # Fail closed: no claims execution allowed.
        from uepi_api.services.policy_execution_eligibility import claims_execution_allowed

        allowed = 0
        cur.execute(
            "SELECT id::text, name, policy_metadata_json FROM policies WHERE tenant_id = %s",
            (str(TENANT),),
        )
        for pid, name, meta in cur.fetchall():
            ok, _ = claims_execution_allowed(
                {"id": pid, "name": name, "policy_metadata_json": meta}
            )
            if ok:
                allowed += 1
        if allowed != 0:
            raise SystemExit(f"Expected 0 claims-executable policies, got {allowed}")

        conn.commit()

        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "spec_version": SPEC_VERSION,
            "database": dbname,
            "population_preserved": before_pop,
            "deleted_lifecycle_before": before_life,
            "after": after_life,
            "seeded_policies": 250,
            "claims_execution_allowed": allowed,
            "acceptance": {
                "accounted_for": "250/250",
                "claims_executable": 0,
                "lifecycle_present": False,
                "note": (
                    "Policies seeded from correction register only. "
                    "No baselines/observations/predictions. "
                    "No fabricated codes. Population (500k) untouched."
                ),
            },
            "by_register_status": {},
            "policies": [
                {
                    "register_index": e["register_index"],
                    "policy": e["policy"],
                    "policy_id": e["policy_id"],
                    "register_status": e["register_status"],
                    "code_mapping_state": e["code_mapping_state"],
                    "lever_type": e["lever_type"],
                    "result": e["result"],
                    "unresolved": e.get("unresolved"),
                }
                for e in evidence
            ],
        }
        from collections import Counter

        summary["by_register_status"] = dict(Counter(e["register_status"] for e in evidence))
        report = Path(args.report)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps({k: summary[k] for k in summary if k != "policies"}, indent=2))
        print(f"report={report}")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
