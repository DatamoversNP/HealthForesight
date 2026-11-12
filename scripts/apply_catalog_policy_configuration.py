"""Copy v1.2 package scope, type, levers, assumptions, and guardrails onto policies.

Does not change claim lines, baselines, predictions, or observation amounts.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs/demo/bcbs-nc/policy_definitions/v1.2/catalog"
TENANT = "00000000-0000-0000-0000-000000000001"


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


def _codes(package: dict) -> list[str]:
    found = []
    for row in (package.get("codeset") or {}).get("codes") or []:
        if not isinstance(row, dict):
            continue
        if "EXCLUDE" in str(row.get("inclusion_status") or "").upper():
            continue
        code = str(row.get("code") or "").strip()
        if code and code not in found:
            found.append(code)
    return found


def _scope(package: dict) -> dict:
    scope = package.get("scope") or {}
    geography = scope.get("geography") or {}
    effective = scope.get("effective") or {}
    return {
        "lob": scope.get("lob") or [],
        "markets": geography.get("markets") or [],
        "states": geography.get("states") or [],
        "setting": scope.get("setting") or [],
        "procedure_codes": _codes(package),
        "effective_start": effective.get("start"),
        "effective_end": effective.get("end"),
    }


def _levers(package: dict) -> list[dict]:
    levers = []
    for lever in package.get("levers") or []:
        if not isinstance(lever, dict):
            continue
        levers.append({
            "lever_type": lever.get("lever_type"),
            "parameters": lever.get("parameters") or {},
            "description": lever.get("direction"),
            "evidence_class": lever.get("evidence_class"),
        })
    return levers


def main() -> None:
    import psycopg2
    from psycopg2.extras import Json

    packages = {}
    for path in CATALOG.glob("*/*PACKAGE.json"):
        data = json.loads(path.read_text())
        packages[path.parent.name] = data

    conn = psycopg2.connect(_database_url())
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id::text, name, policy_type, description, policy_metadata_json
        FROM policies WHERE tenant_id = %s
        """,
        (TENANT,),
    )
    updated = 0
    assumptions = 0
    guardrails = 0
    unmatched = []
    for policy_id, name, policy_type, description, meta in cur.fetchall():
        if not isinstance(meta, dict):
            meta = {}
        path = str(meta.get("definition_path") or "")
        key = path.split("/")[-2] if "/" in path else meta.get("policy_key")
        package = packages.get(key) if key else None
        if not package:
            unmatched.append(name)
            continue
        identity = package.get("identity") or {}
        family = str(identity.get("family") or identity.get("mechanism") or policy_type or "PRIOR_AUTH")
        meta = dict(meta)
        meta["scope"] = _scope(package)
        meta["policy_levers"] = _levers(package)
        meta["package_rules"] = package.get("rules") or []
        meta["configured_from"] = "v1.2 package"
        cur.execute(
            """
            UPDATE policies
            SET name = %s,
                policy_type = %s,
                owner_role = %s,
                description = %s,
                policy_metadata_json = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (
                package.get("policy_name") or name,
                family,
                identity.get("owner_role") or "DEFINITION_REVIEW",
                identity.get("objective") or description,
                Json(meta),
                policy_id,
            ),
        )
        updated += 1
        cur.execute("SELECT COUNT(*) FROM policy_assumptions WHERE policy_id = %s", (policy_id,))
        if cur.fetchone()[0] == 0:
            for item in package.get("assumptions") or []:
                if not isinstance(item, dict):
                    continue
                cur.execute(
                    """
                    INSERT INTO policy_assumptions
                      (id, tenant_id, policy_id, assumption_type, description, source, confidence, created_at, updated_at)
                    VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, NULL, NOW(), NOW())
                    """,
                    (TENANT, policy_id, item.get("id") or "DEFINITION", item.get("text"), item.get("evidence_class")),
                )
                assumptions += 1
        cur.execute("SELECT COUNT(*) FROM policy_guardrails WHERE policy_id = %s", (policy_id,))
        if cur.fetchone()[0] == 0:
            for item in package.get("guardrails") or []:
                if not isinstance(item, dict):
                    continue
                cur.execute(
                    """
                    INSERT INTO policy_guardrails
                      (id, tenant_id, policy_id, metric_name, threshold_type, threshold_value, action, description, triggered, created_at, updated_at)
                    VALUES (gen_random_uuid(), %s, %s, %s, 'definition', 0, 'monitor', %s, false, NOW(), NOW())
                    """,
                    (TENANT, policy_id, item.get("id") or item.get("family") or "GUARDRAIL", item.get("text")),
                )
                guardrails += 1

    cur.execute(
        """
        UPDATE observations o
        SET comparisons_json = jsonb_set(
              COALESCE(o.comparisons_json, '{}'::jsonb),
              '{vs_baseline,baseline_allowed}',
              to_jsonb((b.baseline_metrics_json->>'total_allowed')::numeric),
              true
            )
        FROM baselines b
        WHERE o.policy_id = b.policy_id
          AND o.tenant_id = %s
          AND b.baseline_metrics_json ? 'total_allowed'
          AND (o.comparisons_json->'vs_baseline'->>'baseline_allowed') IS NULL
        """,
        (TENANT,),
    )
    linked = cur.rowcount
    conn.commit()
    print(json.dumps({
        "packages": len(packages),
        "policies_updated": updated,
        "assumptions_inserted": assumptions,
        "guardrails_inserted": guardrails,
        "observations_linked_to_baseline_allowed": linked,
        "unmatched": unmatched,
    }, indent=2))
    conn.close()


if __name__ == "__main__":
    main()
