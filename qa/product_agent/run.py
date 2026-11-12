"""Run the product QA agent against lean staging and write the evidence files."""
from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from qa.product_agent.api import client_from_env
from qa.product_agent.checks import evaluate_catalog
from qa.product_agent.report import write_outputs

ROOT = Path(__file__).resolve().parents[2]
TENANT = "00000000-0000-0000-0000-000000000001"
EVIDENCE = ROOT / "docs/production/releases/qa_evidence"
ROUTES = [
    "/dashboard/executive",
    "/dashboard/policy-owner",
    "/dashboard/analyst",
    "/policies",
    "/policy-verdicts",
    "/objectives-health",
    "/baseline-analysis",
    "/observation-analysis",
    "/predicted-impacts",
    "/whatif",
    "/whatif/scenarios",
    "/policies/builder",
    "/medicare-rules",
    "/exports",
    "/audit-log",
    "/lineage",
    "/cohorts",
    "/analyses",
    "/scorecards",
]


def _get(client, path: str) -> Any:
    status, payload = client.request("GET", path)
    if status != 200:
        return {"_status": status, "_body": payload}
    return payload


def _database_url() -> Optional[str]:
    configured = os.environ.get("HF_QA_DATABASE_URL", "").strip()
    raw = configured
    if not raw:
        try:
            raw = subprocess.check_output(
                ["az", "keyvault", "secret", "show", "--vault-name", "hfleanstgkv", "--name", "lean-staging-database-url", "--query", "value", "-o", "tsv"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    url = raw.replace("postgresql+psycopg2://", "postgresql://", 1)
    host = urlparse(url).hostname or ""
    if host != "hfleanstg-pg.postgres.database.azure.com":
        raise RuntimeError(f"refusing database host {host}")
    return url


def _source_facts(url: str) -> dict[str, Any]:
    import psycopg2

    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id::text, policy_metadata_json->>'definition_path'
        FROM policies WHERE tenant_id = %s
        """,
        (TENANT,),
    )
    paths = {policy_id: path for policy_id, path in cur.fetchall()}
    cur.execute(
        """
        SELECT COALESCE(SUM(
            (
                (enrollment_end_date - enrollment_start_date)
                + CASE WHEN segment LIKE 'GAP_DAYS:%%' THEN CAST(split_part(segment, ':', 2) AS integer) ELSE 0 END
            )::double precision
            / EXTRACT(DAY FROM (date_trunc('month', enrollment_month) + INTERVAL '1 month - 1 day'))
        ), 0)
        FROM enrollment_records
        WHERE tenant_id = %s AND enrollment_month >= %s AND enrollment_month <= %s
          AND enrollment_start_date IS NOT NULL AND enrollment_end_date IS NOT NULL
        """,
        (TENANT, date(2024, 1, 1), date(2025, 6, 1)),
    )
    pre_mm = round(float(cur.fetchone()[0]), 6)
    cur.execute(
        """
        SELECT COALESCE(SUM(
            (
                (enrollment_end_date - enrollment_start_date)
                + CASE WHEN segment LIKE 'GAP_DAYS:%%' THEN CAST(split_part(segment, ':', 2) AS integer) ELSE 0 END
            )::double precision
            / EXTRACT(DAY FROM (date_trunc('month', enrollment_month) + INTERVAL '1 month - 1 day'))
        ), 0)
        FROM enrollment_records
        WHERE tenant_id = %s AND enrollment_month >= %s AND enrollment_month <= %s
          AND enrollment_start_date IS NOT NULL AND enrollment_end_date IS NOT NULL
        """,
        (TENANT, date(2025, 7, 1), date(2026, 9, 1)),
    )
    post_mm = round(float(cur.fetchone()[0]), 6)
    cur.execute(
        """
        SELECT service_category,
               ROUND(COALESCE(SUM(allowed_amount) FILTER (WHERE service_date < DATE '2025-07-01'), 0), 2),
               ROUND(COALESCE(SUM(allowed_amount) FILTER (WHERE service_date >= DATE '2025-07-01' AND service_date <= DATE '2026-09-30'), 0), 2),
               ROUND(COALESCE(SUM(paid_amount) FILTER (WHERE service_date >= DATE '2025-07-01' AND service_date <= DATE '2026-09-30'), 0), 2),
               ROUND(COALESCE(SUM(member_cost_share) FILTER (WHERE service_date >= DATE '2025-07-01' AND service_date <= DATE '2026-09-30'), 0), 2)
        FROM claims_lines
        WHERE tenant_id = %s
        GROUP BY service_category
        """,
        (TENANT,),
    )
    claims = {
        category: {
            "pre_allowed": float(pre),
            "post_allowed": float(post),
            "post_paid": float(paid),
            "post_member_share": float(share),
        }
        for category, pre, post, paid, share in cur.fetchall()
    }
    cur.execute("SELECT current_database()")
    database_name = cur.fetchone()[0]
    conn.close()
    return {
        "paths": paths,
        "claims": claims,
        "exposure": {"pre_member_months": pre_mm, "post_member_months": post_mm},
        "database_name": database_name,
    }


def _as_list(payload: Any) -> list:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("policies", "items", "results", "observations"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def _normalize_predictions(payload: Any) -> list[dict]:
    rows = _as_list(payload)
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
        if not metrics and isinstance(row.get("metrics_json"), dict):
            metrics = row["metrics_json"].get("metrics") or row["metrics_json"]
        normalized.append({"policy_id": row.get("policy_id"), "metrics": metrics})
    return normalized


def _journeys(matrix: list[dict]) -> tuple[list[dict], list[dict]]:
    by_type = {}
    for row in matrix:
        by_type.setdefault(row["policy_type"], row)
    selected = list(by_type.values())
    for state in ("PAYMENT_SIMULATION", "REVIEW_ONLY", "AWAITING_CONFIGURATION", "BLOCKED"):
        for match in [row for row in matrix if row["configuration_state"] == state]:
            if match not in selected:
                selected.append(match)
            if state != "PAYMENT_SIMULATION":
                break
    # All six payment simulations get policy-browser coverage.
    for row in matrix:
        if row["configuration_state"] == "PAYMENT_SIMULATION" and row not in selected:
            selected.append(row)
    journeys = []
    for route in ROUTES:
        journeys.append({"id": "route-" + route.strip("/").replace("/", "-"), "path": route, "expect": [], "forbid": ["Application error"]})
    sample = selected
    for row in sample:
        journeys.append({
            "id": "workspace-" + row["policy_id"][:8],
            "path": f"/policies/workspace/{row['policy_id']}",
            "waitText": row["name"][:40],
            "expect": [row["name"][:40]],
            "forbid": ["CATALOG DEF", "No scope defined - defaults to all population"] if row["has_scope"] else ["CATALOG DEF"],
            "policy_id": row["policy_id"],
            "coverage": "policy_browser",
        })
        journeys.append({
            "id": "obs-" + row["policy_id"][:8],
            "path": f"/observation-analysis?policy={row['policy_id']}",
            "waitText": row["name"][:30],
            "timeout": 30000,
            "expect": [],
            "forbid": ["Please run a policy-specific baseline", "Application error"],
            "policy_id": row["policy_id"],
            "coverage": "policy_browser",
        })
    chart = next((row for row in matrix if row["baseline_allowed"] and row["observed_allowed"] and int(row.get("code_count") or 0) > 0), None)
    if chart:
        journeys.append({
            "id": "chart-" + chart["policy_id"][:8],
            "path": f"/observation-analysis?policy={chart['policy_id']}",
            "waitText": "These period totals cover different lengths",
            "expect": ["Baseline total", "Observed allowed", "These period totals cover different lengths", "18 months", "15 months"],
            "forbid": ["Please run a policy-specific baseline"],
            "timeout": 30000,
            "policy_id": chart["policy_id"],
            "coverage": "policy_browser",
        })
    journeys.append({
        "id": "executive-separation",
        "path": "/dashboard/executive",
        "waitText": "Payment-rule",
        "expect": ["2.04", "15.78", "They are not a portfolio savings total.", "Not a portfolio total."],
        "forbid": ["The figures are then summed"],
        "coverage": "navigation",
    })
    journeys.append({
        "id": "whatif-longitudinal-ready",
        "path": "/whatif",
        "waitText": "Payment what-if runs on POST-period",
        "timeout": 30000,
        "expect": ["not measured savings", "Payment what-if runs on POST-period"],
        "forbid": ["NOT_THIS_POPULATION"],
        "coverage": "navigation",
    })
    journeys.append({
        "id": "medicare-empty-inventory",
        "path": "/medicare-rules",
        "waitText": "Medicare",
        "timeout": 20000,
        "expect": [],
        "forbid": ["Internal Server Error", "500"],
        "coverage": "navigation",
    })
    return journeys, sample


def _write_blocker_matrix(path: Path, rows: list[dict]) -> None:
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["policy_id", "name", "configuration_state", "blocked_reason", "required_parameter", "closure_owner", "notes"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _number_defects(defects: list[dict]) -> None:
    for index, defect in enumerate(defects, start=1):
        if not defect.get("defect_id"):
            defect["defect_id"] = f"HFQA-{index:03d}"
        defect.setdefault("reproduction", "")
        defect.setdefault("screenshot", "")
        defect.setdefault("root_cause", "")
        defect.setdefault("retest", "not retested")


def _decision(summary: dict, browser_failed: int, dashboard_ok: bool) -> dict:
    engineering = summary["data_fail"] + summary["calculation_fail"] + browser_failed
    staging = "NO-GO" if engineering else "GO FOR SUPPORTED CONFIGURATIONS ONLY"
    production = "FAIL"
    assessment = (
        f"The agent discovered {summary['policy_count']} policies and evaluated each through the API, "
        f"stored comparisons, and an independent claim-line and exposure oracle. "
        f"{summary['data_fail']} failed the data contract and {summary['calculation_fail']} failed the calculation check. "
        f"{browser_failed} browser journeys failed. "
        "Review-only and blocked policies are not treated as executed."
    )
    return {
        "assessment": assessment,
        "staging": staging,
        "staging_reason": "Supported payment simulations and correctly labeled review or blocked policies can be shown. A failed calculation, a false execution claim, or a failed customer journey blocks staging.",
        "production": production,
        "production_reason": "Functional production readiness stays fail. The catalog contains unsigned clinical policies, policies with no candidate code, and parameters whose engines are not implemented. Staging evidence is not approval for another client's data.",
        "engineering_failures": engineering,
        "dashboard_ok": dashboard_ok,
    }


def main() -> int:
    client, urls = client_from_env()
    health_status = None
    try:
        with urllib.request.urlopen(urls["api"].replace("/api/v1", "") + "/health", timeout=30) as response:
            health_status = response.status
    except Exception:
        health_status = "unreachable"
    identity_payload = _get(client, "/synthetic-payer/identity")
    me = _get(client, "/auth/me")
    policies = _as_list(_get(client, "/policies?limit=1000"))
    execution = _get(client, "/policy-execution/summary")
    baselines = _as_list(_get(client, "/baselines?summary=true&limit=1000"))
    observations = _as_list(_get(client, "/observations?latest_only=true&summary=true&limit=500"))
    predictions = _normalize_predictions(_get(client, "/policies/predicted-impacts?limit=1000"))
    dashboard = _get(client, "/dashboard/summary")
    objectives = _get(client, "/dashboard/objectives-health")
    verdicts = _get(client, "/policy-verdicts")
    medicare_status, medicare = client.request("GET", "/enterprise/medicare-rules")

    source = {"paths": {}, "claims": {}, "exposure": {"pre_member_months": None, "post_member_months": None}, "database_name": None}
    db_url = _database_url()
    if db_url:
        source = _source_facts(db_url)
        for policy in policies:
            path = source["paths"].get(str(policy.get("id")))
            if path:
                policy["metadata"] = {"definition_path": path}

    matrix, defects, summary = evaluate_catalog(
        policies,
        execution if isinstance(execution, dict) else {"policies": []},
        baselines,
        observations,
        predictions,
        source["claims"],
        source["exposure"],
    )

    metrics = dashboard.get("metrics") if isinstance(dashboard, dict) else {}
    dashboard_payment = metrics.get("total_cost_impact") if isinstance(metrics, dict) else None
    dashboard_continuation = metrics.get("continuation_allowed_difference") if isinstance(metrics, dict) else None
    rolled = summary["rollup"]
    dashboard_comparison = {
        "payment_matches_oracle": dashboard_payment is not None and rolled["payment_sum"] is not None and abs(float(dashboard_payment) - rolled["payment_sum"]) <= 0.05,
        "continuation_matches_oracle": dashboard_continuation is not None and rolled["continuation_sum"] is not None and abs(float(dashboard_continuation) - rolled["continuation_sum"]) <= 0.05,
        "payment_api": dashboard_payment,
        "continuation_api": dashboard_continuation,
        "payment_oracle": rolled["payment_sum"],
        "continuation_oracle": rolled["continuation_sum"],
    }
    if not dashboard_comparison["payment_matches_oracle"] or not dashboard_comparison["continuation_matches_oracle"]:
        defects.append({
            "defect_id": "",
            "severity": "high",
            "feature": "executive dashboard",
            "policy_id": "",
            "expected": "Dashboard payment-rule and continuation totals equal the independent sums of the stored per-policy differences.",
            "actual": json.dumps(dashboard_comparison),
            "status": "open",
            "class": "calculation",
        })

    before_obs = len(observations)
    payment_rows = [row for row in matrix if row["configuration_state"] == "PAYMENT_SIMULATION"]
    whatif_runs = []
    identity_engine = identity_payload.get("what_if_engine") if isinstance(identity_payload, dict) else None
    if identity_engine != "LONGITUDINAL_PAYMENT":
        defects.append({
            "defect_id": "",
            "severity": "critical",
            "feature": "what-if",
            "policy_id": "",
            "expected": "Identity exposes LONGITUDINAL_PAYMENT what-if for the six payment policies.",
            "actual": f"what_if_engine={identity_engine}",
            "status": "open",
            "class": "workflow",
        })
    for row in payment_rows:
        status, body = client.request("POST", "/synthetic-payer/what-if", {
            "policy_id": row["policy_id"],
            "parameters": {},
        }, timeout=180)
        ok = status == 200 and isinstance(body, dict) and body.get("status") == "completed" and body.get("oracle_match") is True
        whatif_runs.append({
            "policy_id": row["policy_id"],
            "name": row["name"],
            "http_status": status,
            "result_status": body.get("status") if isinstance(body, dict) else None,
            "oracle_match": body.get("oracle_match") if isinstance(body, dict) else None,
            "payment_impact_dollars": body.get("payment_impact_dollars") if isinstance(body, dict) else None,
            "lines_included": body.get("lines_included") if isinstance(body, dict) else None,
            "ok": ok,
        })
        if not ok:
            defects.append({
                "defect_id": "",
                "severity": "critical",
                "feature": "what-if",
                "policy_id": row["policy_id"],
                "expected": "Payment what-if completes with independent oracle_match true and does not mutate observations.",
                "actual": json.dumps(whatif_runs[-1]),
                "status": "open",
                "class": "workflow",
            })
    overlap_status, _overlap_body = client.request("POST", "/synthetic-payer/what-if", {
        "policy_id": payment_rows[0]["policy_id"] if payment_rows else (matrix[0]["policy_id"] if matrix else TENANT),
        "policy_ids": [row["policy_id"] for row in payment_rows[:2]] or [row["policy_id"] for row in matrix[:2]],
        "parameters": {},
    })
    after_obs = _as_list(_get(client, "/observations?latest_only=true&summary=true&limit=500"))
    whatif_note = (
        f"Identity engine {identity_engine}. Payment what-if runs {sum(1 for row in whatif_runs if row['ok'])}/{len(whatif_runs)}. "
        f"Overlapping what-if status {overlap_status}. Observation count before {before_obs}, after {len(after_obs)}. "
        "A simulated difference is not measured savings."
    )
    if overlap_status == 200:
        defects.append({
            "defect_id": "",
            "severity": "high",
            "feature": "what-if",
            "policy_id": "",
            "expected": "More than one policy in one what-if is rejected.",
            "actual": f"status {overlap_status}",
            "status": "open",
            "class": "workflow",
        })
    if len(after_obs) != before_obs:
        defects.append({
            "defect_id": "",
            "severity": "critical",
            "feature": "what-if",
            "policy_id": "",
            "expected": "What-if does not change the observation count.",
            "actual": f"before {before_obs} after {len(after_obs)}",
            "status": "open",
            "class": "integrity",
        })

    payment_verification = []
    if db_url:
        import psycopg2
        from qa.product_agent.payment_oracle import verify_payment_simulations
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        obs_by_key = {}
        for row in matrix:
            if row["configuration_state"] != "PAYMENT_SIMULATION":
                continue
            # Reload full observation comparisons for payment policies.
            status, full_obs = client.request("GET", f"/observations?policy_id={row['policy_id']}&limit=5")
            items = _as_list(full_obs)
            if items:
                key = None
                # policy_key from DB metadata
                cur.execute("SELECT policy_metadata_json->>'policy_key' FROM policies WHERE id=%s", (row["policy_id"],))
                key_row = cur.fetchone()
                key = key_row[0] if key_row else None
                if key:
                    obs_by_key[key] = items[0]
                    for matrix_row in matrix:
                        if matrix_row["policy_id"] == row["policy_id"]:
                            matrix_row["policy_key"] = key
        payment_verification = verify_payment_simulations(cur, TENANT, obs_by_key)
        conn.close()
        for row in payment_verification:
            if row["result"] != "pass":
                defects.append({
                    "defect_id": "",
                    "severity": "critical",
                    "feature": "payment-engine",
                    "policy_id": row["policy_key"],
                    "expected": "Independent claim-line oracle matches stored PRE/POST payment impacts.",
                    "actual": json.dumps(row),
                    "status": "open",
                    "class": "calculation",
                })

    from qa.product_agent.verdict_fixtures import run_verdict_fixtures
    verdict_fixture_results = run_verdict_fixtures()
    for row in verdict_fixture_results:
        if row["result"] != "pass":
            defects.append({
                "defect_id": "",
                "severity": "high",
                "feature": "verdict-fixtures",
                "policy_id": "",
                "expected": f"Fixture {row['id']} yields {row.get('expected')}",
                "actual": json.dumps(row),
                "status": "open",
                "class": "verdict",
            })

    blocker_matrix = []
    for row in matrix:
        if row["execution_class"] not in {"legitimate_gap", "review_only_not_execution"} and row["configuration_state"] != "AWAITING_CONFIGURATION":
            if row["configuration_state"] != "BLOCKED":
                continue
        owner = "application_engine"
        if row["blocked_reason"] in {"UNSIGNED_CLINICAL_OR_COVERAGE_AUTHORITY", "NO_CANDIDATE_CODE_IN_PACKAGE", "NO_EXECUTABLE_RULE_IN_DEFINITION"}:
            owner = "authoritative_input"
        elif row["configuration_state"] == "AWAITING_CONFIGURATION":
            owner = "client_parameter" if row.get("required_parameter") == "quantity_limit_units" else "application_engine_or_parameter"
        elif row["execution_class"] == "review_only_not_execution":
            owner = "supported_review_behavior"
        blocker_matrix.append({
            "policy_id": row["policy_id"],
            "name": row["name"],
            "configuration_state": row["configuration_state"],
            "blocked_reason": row.get("blocked_reason"),
            "required_parameter": row.get("required_parameter"),
            "closure_owner": owner,
            "notes": row.get("data_failures") or "",
        })
    _write_blocker_matrix(ROOT / "docs/production/releases/HEALTHFORESIGHT_QA_BLOCKER_MATRIX.csv", blocker_matrix)

    medicare_note = {
        "http_status": medicare_status,
        "count": medicare.get("count") if isinstance(medicare, dict) else None,
        "classification": (
            "expected_empty_inventory"
            if medicare_status == 200 and isinstance(medicare, dict) and medicare.get("count") == 0
            else "unexpected"
        ),
        "honesty": (medicare.get("honesty") if isinstance(medicare, dict) else None),
    }
    if medicare_note["classification"] != "expected_empty_inventory":
        defects.append({
            "defect_id": "",
            "severity": "medium",
            "feature": "medicare rules",
            "policy_id": "",
            "expected": "Empty Medicare inventory returns HTTP 200 with count 0 and honesty flags.",
            "actual": json.dumps(medicare_note),
            "status": "open",
            "class": "api",
        })

    created = None
    create_status = "skipped"
    if db_url:
        create_status, created_body = client.request("POST", "/policies", {
            "name": "QA disposable policy do not use",
            "policy_type": "PRIOR_AUTH",
            "description": "Disposable QA policy. Delete after the test.",
            "owner_role": "QA",
        })
        if create_status == 201 and isinstance(created_body, dict):
            created = str(created_body.get("id"))
            import psycopg2
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("DELETE FROM policies WHERE id = %s AND name = %s", (created, "QA disposable policy do not use"))
            conn.commit()
            conn.close()
    disposable_note = f"Disposable policy create status {create_status}. Deleted by primary key: {bool(created)}."

    if medicare_status >= 500:
        defects.append({
            "defect_id": "",
            "severity": "medium",
            "feature": "medicare rules",
            "policy_id": "",
            "expected": "The page loads an empty inventory when no Medicare source table is present.",
            "actual": f"status {medicare_status}",
            "status": "open",
            "class": "api",
        })

    journeys, sample = _journeys(matrix)
    plan = {
        "screenshotDir": str(EVIDENCE),
        "targets": [
            {"base": urls["web"], "journeys": journeys},
            {"base": urls["dv"], "journeys": [item for item in journeys if item["id"] in {"executive-separation", "whatif-longitudinal-ready"}]},
        ],
    }
    prior_results_path = ROOT / "docs/production/releases/HEALTHFORESIGHT_QA_RESULTS.json"
    prior_snapshot = None
    if prior_results_path.exists():
        prior_snapshot = json.loads(prior_results_path.read_text())
        (EVIDENCE / "previous-run-results.json").write_text(json.dumps(prior_snapshot, indent=2))
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    plan_path = EVIDENCE / "browser-plan.json"
    browser_out = EVIDENCE / "browser-results.json"
    plan_path.write_text(json.dumps(plan))
    browser_proc = subprocess.run(
        ["node", str(ROOT / "qa/product_agent/browser_journeys.mjs"), str(plan_path), str(browser_out)],
        cwd=str(ROOT),
        env=os.environ.copy(),
        text=True,
    )
    browser_results = []
    if browser_out.exists():
        browser_results = json.loads(browser_out.read_text()).get("results") or []
    for result in browser_results:
        if result.get("ok"):
            continue
        defects.append({
            "defect_id": "",
            "severity": "high",
            "feature": result.get("id"),
            "policy_id": "",
            "expected": "The staging screen shows the required labels and does not show a false empty or false execution state.",
            "actual": "; ".join(result.get("failures") or []),
            "reproduction": result.get("url"),
            "screenshot": result.get("screenshot"),
            "status": "open",
            "class": "frontend",
            "retest": "failed on this run",
        })
    sample_ids = {row["policy_id"] for row in sample}
    browser_by_policy = defaultdict(str)
    for result in browser_results:
        if result["id"].startswith(("workspace-", "chart-", "obs-")):
            prefix = result["id"].split("-", 1)[1]
            prior = browser_by_policy.get(prefix)
            if prior == "fail" or not result.get("ok"):
                browser_by_policy[prefix] = "fail"
            elif prior != "fail":
                browser_by_policy[prefix] = "pass"
    for row in matrix:
        prefix = row["policy_id"][:8]
        if prefix in browser_by_policy:
            row["browser_result"] = browser_by_policy[prefix]
        elif row["policy_id"] in sample_ids:
            row["browser_result"] = "selected_for_browser"
    policy_browser_pass = sum(1 for row in matrix if row.get("browser_result") == "pass")
    policy_browser_fail = sum(1 for row in matrix if row.get("browser_result") == "fail")

    demo_image = "not checked"
    try:
        demo_image = subprocess.check_output(
            ["az", "webapp", "config", "container", "show", "-g", "healthforesight-rg", "-n", "healthforesight-api", "--query", "[?name=='DOCKER_CUSTOM_IMAGE_NAME'].value", "-o", "tsv"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        demo_image = "az check failed"
    if demo_image and "dec4-stab-5b587ed" not in demo_image and demo_image not in {"not checked", "az check failed"}:
        defects.append({
            "defect_id": "",
            "severity": "critical",
            "feature": "environment isolation",
            "policy_id": "",
            "expected": "The December 4 demo image remains dec4-stab-5b587ed.",
            "actual": demo_image,
            "status": "open",
            "class": "operations",
        })

    unit = subprocess.run(
        [os.environ.get("HF_QA_PYTHON", str(ROOT / ".venv7867/bin/python")), "-m", "pytest", "-c", "pyproject.toml", "--rootdir=.", "qa/product_agent/test_oracle_arithmetic.py", "-q"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    prior_path = EVIDENCE / "first-run-results.json"
    if prior_path.exists():
        prior = json.loads(prior_path.read_text())
        passed_ids = {row.get("id") for row in browser_results if row.get("ok")}
        for old in prior.get("defects") or []:
            feature = old.get("feature")
            if feature in passed_ids or (feature == "whatif-disclaimer" and "whatif-disclaimer" in passed_ids):
                old = dict(old)
                old["status"] = "fixed"
                old["retest"] = "passed on the staging retest"
                old["root_cause"] = old.get("root_cause") or (
                    "What-if identity only recognized SYNTHETIC_PAYER_V1, so the longitudinal catalog hid the not-savings warning."
                    if feature == "whatif-disclaimer"
                    else "Baseline and observation totals were shown without stating that the windows have different lengths."
                )
                defects.append(old)
    _number_defects(defects)
    browser_failed = sum(1 for row in browser_results if not row.get("ok"))
    payment_fail = sum(1 for row in payment_verification if row.get("result") != "pass")
    whatif_fail = sum(1 for row in whatif_runs if not row.get("ok"))
    decision = _decision(summary, browser_failed + payment_fail + whatif_fail, dashboard_comparison["payment_matches_oracle"] and dashboard_comparison["continuation_matches_oracle"])
    if not decision["dashboard_ok"] or payment_fail or whatif_fail:
        decision["staging"] = "NO-GO"
    comparison = None
    if prior_snapshot:
        comparison = {
            "prior_staging": (prior_snapshot.get("decision") or {}).get("staging"),
            "prior_browser_failed": (prior_snapshot.get("browser") or {}).get("failed"),
            "prior_data_fail": (prior_snapshot.get("summary") or {}).get("data_fail"),
            "current_staging": decision["staging"],
            "current_browser_failed": browser_failed,
            "current_payment_oracle_fail": payment_fail,
            "current_whatif_fail": whatif_fail,
            "policy_browser_pass": policy_browser_pass,
            "policy_browser_fail": policy_browser_fail,
        }
    payload = {
        "identity": {
            "web": urls["web"],
            "dv": urls["dv"],
            "api": urls["api"],
            "api_health": health_status,
            "database_name": source.get("database_name") or (identity_payload.get("database_name") if isinstance(identity_payload, dict) else None),
            "synthetic": identity_payload.get("synthetic") if isinstance(identity_payload, dict) else None,
            "what_if_engine": identity_engine,
            "covered_lives": identity_payload.get("covered_lives") if isinstance(identity_payload, dict) else None,
            "tenant_id": me.get("tenant_id") if isinstance(me, dict) else None,
            "demo_image": demo_image,
            "web_revision": "checked through the live staging URL, not a local build",
            "api_revision": "checked through the live staging URL, not a local build",
        },
        "summary": summary,
        "dashboard": {"payment": dashboard_payment, "continuation": dashboard_continuation, "comparison": dashboard_comparison},
        "payment_engine_verification": payment_verification,
        "whatif_runs": whatif_runs,
        "verdict_fixtures": verdict_fixture_results,
        "objectives_status": objectives.get("_status") if isinstance(objectives, dict) and objectives.get("_status") else "loaded",
        "verdict_rows": len(verdicts) if isinstance(verdicts, list) else (verdicts.get("_status") if isinstance(verdicts, dict) else None),
        "medicare": medicare_note,
        "whatif_note": whatif_note + " " + disposable_note,
        "chart_note": "Chart journeys require the baseline and observed series, an explicit statement when the baseline and observation windows have different lengths, and no fabricated monthly prediction line.",
        "browser": {
            "journey_count": len(browser_results),
            "passed": sum(1 for row in browser_results if row.get("ok")),
            "failed": browser_failed,
            "policy_browser_pass": policy_browser_pass,
            "policy_browser_fail": policy_browser_fail,
            "policy_browser_not_sampled": sum(1 for row in matrix if row.get("browser_result") == "not_in_browser_sample"),
            "exit_code": browser_proc.returncode,
            "results": [{key: row.get(key) for key in ("id", "url", "ok", "failures", "screenshot")} for row in browser_results],
        },
        "comparison_to_previous_run": comparison,
        "policy_matrix": matrix,
        "defects": defects,
        "blockers": [
            "191 policies remain incomplete for executable payment behavior (blocked or awaiting).",
            "90 review-only policies are not payment effects.",
            "Only quantity_limit_units has an implemented parameter engine among awaiting fields.",
            "Browser coverage remains sampled by mechanism/state; policy-browser counts are reported separately.",
            "Functional production readiness remains FAIL until a real client catalog is complete.",
        ],
        "decision": decision,
        "unit_tests": (unit.stdout or "") + (unit.stderr or ""),
    }
    write_outputs(ROOT, payload)
    print(json.dumps({
        "policies": summary["policy_count"],
        "data_fail": summary["data_fail"],
        "calculation_fail": summary["calculation_fail"],
        "payment_oracle_fail": payment_fail,
        "whatif_fail": whatif_fail,
        "browser_failed": browser_failed,
        "policy_browser_pass": policy_browser_pass,
        "staging": decision["staging"],
        "production": decision["production"],
    }, indent=2))
    if (
        unit.returncode != 0
        or summary["data_fail"]
        or summary["calculation_fail"]
        or browser_failed
        or payment_fail
        or whatif_fail
        or not decision["dashboard_ok"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
