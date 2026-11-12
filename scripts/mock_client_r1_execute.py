"""Execute configured mock-client policy contracts against the longitudinal database.

Refuses every database except the local disposable longitudinal synthetic database.
Does not rewrite observations, predictions, baselines, or staging data.
"""
from __future__ import annotations

import json
import os
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

from uepi_common.policy_execution.contract import resolve_execution_contract
from uepi_common.policy_execution.engine import execute_configured_policy
from uepi_common.policy_execution.oracle import expected_review_from_code_totals
from uepi_worker.policy_mechanism_execution import run_policy_execution

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs/demo/bcbs-nc/policy_definitions/v1.2/catalog"
TENANT = "00000000-0000-0000-0000-000000000001"
REQUIRED_DB = "synthetic_payer_500k_longitudinal"
OUT = ROOT / "data/synthetic/mock_client_r1_execution.json"


def _connect():
    url = os.environ.get("DATABASE_URL", "")
    if REQUIRED_DB not in url or "55434" not in url or "azure" in url.lower() or "windows.net" in url.lower():
        raise SystemExit(f"Refusing execution against an unapproved database: {url}")
    dsn = url.replace("postgresql+psycopg2://", "postgresql://")
    return psycopg2.connect(dsn)


def _packages() -> dict[str, dict]:
    found = {}
    for path in sorted(CATALOG.glob("*/*PACKAGE.json")):
        package = json.loads(path.read_text())
        package["_key"] = path.parent.name
        package["_path"] = str(path.relative_to(ROOT))
        found[path.parent.name] = package
    return found


def _policy_key(meta: dict) -> str | None:
    path = str(meta.get("definition_path") or "")
    if "/catalog/" in path:
        parts = path.split("/")
        if "catalog" in parts:
            index = parts.index("catalog")
            if index + 1 < len(parts):
                return parts[index + 1]
    if meta.get("policy_key"):
        return str(meta["policy_key"])
    return None


def main() -> None:
    packages = _packages()
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SET statement_timeout = '10min'")
    cur.execute(
        """
        SELECT id::text, name, policy_metadata_json
        FROM policies
        WHERE tenant_id = %s
        """,
        (TENANT,),
    )
    policies = []
    for policy_id, name, meta in cur.fetchall():
        if isinstance(meta, str):
            meta = json.loads(meta)
        meta = meta or {}
        policies.append({"id": policy_id, "name": name, "meta": meta, "key": _policy_key(meta)})

    review_codes: dict[str, list[str]] = {}
    contracts: dict[str, dict] = {}
    for policy in policies:
        package = packages.get(policy["key"] or "")
        if package is None and policy["key"] in {"mppr", "sos", "ptp", "mue", "therapy", "infusion", "mri", "ncd", "lcd"}:
            package = {
                "policy_name": policy["name"],
                "_key": policy["key"],
                "package_version": "validated-payment-or-clinical-v1",
                "identity": {
                    "mechanism": "MEDICAL_NECESSITY_COVERAGE" if policy["key"] in {"mri", "ncd", "lcd"} else "PAYMENT_REIMBURSEMENT",
                    "family": "MEDICAL_NECESSITY" if policy["key"] in {"mri", "ncd", "lcd"} else "PAYMENT_POLICY",
                },
                "codeset": {"status": "CANDIDATE_SCHEDULE", "codes": [{"code": "UNRESOLVED", "inclusion_status": "CANDIDATE_INCLUDE"}]},
                "rules": [],
                "levers": [],
            }
        if package is None:
            contract = {
                "status": "BLOCKED",
                "mechanism": None,
                "mechanism_executed": False,
                "blocked_reason": "DEFINITION_PACKAGE_NOT_FOUND",
                "financial_effect_status": "UNAVAILABLE",
                "financial_effect": None,
                "eligible_line_count": None,
                "result_label": "No authoritative package was found for this policy.",
                "not_claiming": "Synthetic mock-client configuration. Does not establish CMS, NCD, LCD, medical-necessity, or contracted payment authority.",
                "contract_version": "mock-client-exec-v1",
            }
        else:
            contract = resolve_execution_contract(package)
        contracts[policy["id"]] = contract
        if contract.get("mechanism") == "CONFIGURED_RULE_REVIEW_REQUIRED_NO_AUTO_DENY":
            review_codes[policy["key"]] = list(contract["candidate_codes"])

    keys: list[str] = []
    codes: list[str] = []
    for key, values in review_codes.items():
        for code in values:
            keys.append(key)
            codes.append(code)
    engine_rows: dict[str, dict] = {}
    if codes:
        cur.execute(
            """
            WITH configured(policy_key, code) AS (
                SELECT * FROM unnest(%s::text[], %s::text[])
            )
            SELECT c.policy_key,
                   count(*)::int,
                   count(DISTINCT l.member_id)::int,
                   coalesce(sum(l.allowed_amount), 0)::float,
                   coalesce(sum(l.paid_amount), 0)::float
            FROM configured c
            JOIN claims_lines l
              ON l.tenant_id = %s
             AND l.cpt_code = c.code
            GROUP BY c.policy_key
            """,
            (keys, codes, TENANT),
        )
        for policy_key, lines, members, allowed, paid in cur.fetchall():
            engine_rows[policy_key] = {
                "eligible_line_count": int(lines),
                "eligible_member_count": int(members),
                "eligible_allowed": round(float(allowed), 2),
                "eligible_paid": round(float(paid), 2),
            }
        cur.execute(
            """
            SELECT cpt_code, count(*)::int, coalesce(sum(allowed_amount), 0)::float, coalesce(sum(paid_amount), 0)::float
            FROM claims_lines
            WHERE tenant_id = %s AND cpt_code = ANY(%s)
            GROUP BY cpt_code
            """,
            (TENANT, list(dict.fromkeys(codes))),
        )
        totals = {
            code: {"lines": int(lines), "allowed": float(allowed), "paid": float(paid)}
            for code, lines, allowed, paid in cur.fetchall()
        }
    else:
        totals = {}

    mismatches = []
    matrix = []
    for policy in policies:
        contract = dict(contracts[policy["id"]])
        record = {
            "policy_id": policy["id"],
            "policy_key": policy["key"],
            "name": policy["name"],
            "worker": "uepi_worker.policy_mechanism_execution",
            "attempt": 1,
            "oracle_match": None,
            "eligible_line_count": None,
            "eligible_member_count": None,
            "eligible_allowed": None,
            "eligible_paid": None,
            "financial_effect": None,
            "payment_changed": False,
            "continuation_used_as_execution": False,
        }
        record.update({k: contract.get(k) for k in (
            "contract_version", "status", "mechanism", "mechanism_executed", "blocked_reason",
            "blocked_detail", "financial_effect_status", "result_label", "not_claiming",
            "package_version", "candidate_codes", "required_parameter",
        )})
        if contract.get("mechanism") == "CONFIGURED_RULE_REVIEW_REQUIRED_NO_AUTO_DENY":
            engine = engine_rows.get(policy["key"], {
                "eligible_line_count": 0,
                "eligible_member_count": 0,
                "eligible_allowed": 0.0,
                "eligible_paid": 0.0,
            })
            expected = expected_review_from_code_totals(totals, contract["candidate_codes"])
            match = (
                engine["eligible_line_count"] == expected["eligible_line_count"]
                and engine["eligible_allowed"] == expected["eligible_allowed"]
                and engine["eligible_paid"] == expected["eligible_paid"]
            )
            if not match:
                mismatches.append({
                    "policy_key": policy["key"],
                    "engine": engine,
                    "oracle": expected,
                })
            record.update(engine)
            record["oracle_match"] = match
            record["financial_effect"] = None
            record["financial_effect_status"] = "UNAVAILABLE"
            record["mechanism_executed"] = True
        elif contract.get("mechanism") == "VALIDATED_PAYMENT_ENGINE":
            meta = policy["meta"]
            record["oracle_match"] = meta.get("oracle_match")
            record["result_class"] = meta.get("result_class")
            record["result_label"] = "Validated payment-rule simulation already stored. Not recomputed and not an observed payer saving."
            record["financial_effect_status"] = "MECHANISM_SIMULATION"
            record["mechanism_executed"] = meta.get("mechanism_executed") is True and meta.get("result_class") == "MECHANISM_SIMULATION"
            if not record["mechanism_executed"]:
                record["status"] = "BLOCKED"
                record["blocked_reason"] = "VALIDATED_ENGINE_EVIDENCE_MISSING"
        matrix.append(record)

    if mismatches:
        conn.rollback()
        raise SystemExit(f"Oracle mismatch for {len(mismatches)} policies: {mismatches[:3]}")

    spot_key = next(iter(review_codes), None)
    spot = None
    if spot_key:
        spot_codes = review_codes[spot_key]
        cur.execute(
            """
            SELECT cpt_code, member_id, allowed_amount::float, paid_amount::float, units::float
            FROM claims_lines
            WHERE tenant_id = %s AND cpt_code = ANY(%s)
            """,
            (TENANT, spot_codes),
        )
        lines = [
            {"cpt_code": code, "member_id": member, "allowed_amount": allowed, "paid_amount": paid, "units": units}
            for code, member, allowed, paid, units in cur.fetchall()
        ]
        package = packages[spot_key]
        produced = run_policy_execution(package, lines)
        expected_lines = engine_rows.get(spot_key, {}).get("eligible_line_count")
        if produced["eligible_line_count"] != expected_lines:
            conn.rollback()
            raise SystemExit(f"Line-level worker result {produced['eligible_line_count']} != SQL {expected_lines} for {spot_key}")
        spot = {"policy_key": spot_key, "lines": produced["eligible_line_count"], "attempt": produced["attempt"]}

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for record in matrix:
        stored = {
            "contract_version": record.get("contract_version"),
            "status": record.get("status"),
            "mechanism": record.get("mechanism"),
            "mechanism_executed": record.get("mechanism_executed"),
            "blocked_reason": record.get("blocked_reason"),
            "blocked_detail": record.get("blocked_detail"),
            "financial_effect_status": record.get("financial_effect_status"),
            "financial_effect": None,
            "eligible_line_count": record.get("eligible_line_count"),
            "eligible_member_count": record.get("eligible_member_count"),
            "eligible_allowed": record.get("eligible_allowed"),
            "eligible_paid": record.get("eligible_paid"),
            "oracle_match": record.get("oracle_match"),
            "result_label": record.get("result_label"),
            "not_claiming": record.get("not_claiming"),
            "package_version": record.get("package_version"),
            "worker": record.get("worker"),
            "attempt": record.get("attempt"),
            "executed_at": now.isoformat(),
        }
        cur.execute(
            """
            UPDATE policies
            SET policy_metadata_json = coalesce(policy_metadata_json, '{}'::jsonb) || %s::jsonb,
                updated_at = %s
            WHERE id = %s AND tenant_id = %s
            """,
            (Json({"mock_execution_v1": stored}), now, record["policy_id"], TENANT),
        )
    cur.execute(
        """
        INSERT INTO audit_events (
            id, tenant_id, action, object_type, object_id, diff_summary, created_at, metadata_json
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            str(uuid.uuid4()),
            TENANT,
            "POLICY_EXECUTION",
            "POLICY_CATALOG",
            None,
            Json({"policies": len(matrix), "mismatches": 0}),
            now,
            Json({"worker": "uepi_worker.policy_mechanism_execution", "contract_version": "mock-client-exec-v1", "spot_check": spot}),
        ),
    )
    conn.commit()

    code_owners = defaultdict(list)
    for key, values in review_codes.items():
        for code in values:
            code_owners[code].append(key)
    shared = {code: owners for code, owners in code_owners.items() if len(owners) > 1}
    counts = Counter(record["status"] for record in matrix)
    reasons = Counter(record.get("blocked_reason") or "NONE" for record in matrix)
    executed = sum(1 for record in matrix if record.get("mechanism_executed"))
    summary = {
        "database": REQUIRED_DB,
        "generated_at": now.isoformat(),
        "policy_count": len(matrix),
        "package_count": len(packages),
        "status_counts": dict(counts),
        "blocked_reasons": dict(reasons),
        "mechanism_executed_count": executed,
        "review_policy_count": len(review_codes),
        "oracle_mismatches": 0,
        "shared_candidate_codes": shared,
        "spot_check": spot,
        "observations_rewritten": False,
        "staging_written": False,
        "policies": matrix,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps({k: summary[k] for k in summary if k != "policies"}, indent=2, default=str))
    conn.close()


if __name__ == "__main__":
    main()
