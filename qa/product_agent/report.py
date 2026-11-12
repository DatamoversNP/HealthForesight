"""Write the QA report, defect ledger, policy matrix, JSON, and HTML."""
from __future__ import annotations

import csv
import json
from html import escape
from pathlib import Path
from typing import Any


def _write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_outputs(root: Path, payload: dict[str, Any]) -> None:
    releases = root / "docs/production/releases"
    releases.mkdir(parents=True, exist_ok=True)
    json_path = releases / "HEALTHFORESIGHT_QA_RESULTS.json"
    json_path.write_text(json.dumps(payload, indent=2, default=str))

    matrix = payload["policy_matrix"]
    matrix_fields = [
        "policy_id", "name", "policy_type", "configuration_state", "execution_class",
        "mechanism", "mechanism_executed", "blocked_reason", "required_parameter",
        "has_scope", "code_count", "lever_count", "baseline_months", "observation_months",
        "baseline_allowed", "observed_allowed", "predicted_allowed", "oracle_predicted",
        "prediction_delta", "claim_pre_delta", "claim_post_delta", "verdict",
        "data_result", "calculation_result", "browser_result", "data_failures",
    ]
    _write_csv(releases / "HEALTHFORESIGHT_QA_POLICY_MATRIX.csv", matrix, matrix_fields)

    defects = payload["defects"]
    defect_fields = [
        "defect_id", "severity", "feature", "policy_id", "expected", "actual",
        "reproduction", "screenshot", "root_cause", "status", "retest", "class",
    ]
    _write_csv(releases / "HEALTHFORESIGHT_QA_DEFECTS.csv", defects, defect_fields)

    report = _markdown(payload)
    (releases / "HEALTHFORESIGHT_AUTONOMOUS_PRODUCT_QA_REPORT.md").write_text(report)
    (releases / "HEALTHFORESIGHT_QA_REPORT.html").write_text(_html(payload))


def _markdown(payload: dict[str, Any]) -> str:
    identity = payload["identity"]
    summary = payload["summary"]
    browser = payload["browser"]
    decision = payload["decision"]
    lines = [
        "# HealthForesight autonomous product QA",
        "",
        "## 1. Executive assessment",
        "",
        decision["assessment"],
        "",
        f"Mock-client staging: **{decision['staging']}**.",
        f"Functional production readiness: **{decision['production']}**.",
        "",
        "## 2. Environment",
        "",
        f"- Web: `{identity['web']}`",
        f"- Data Voyager: `{identity['dv']}`",
        f"- API: `{identity['api']}`",
        f"- API health: {identity.get('api_health')}",
        f"- Database name: {identity.get('database_name')}",
        f"- Synthetic: {identity.get('synthetic')}",
        f"- Covered lives: {identity.get('covered_lives')}",
        f"- Tenant: {identity.get('tenant_id')}",
        f"- Policies discovered: {summary['policy_count']}",
        f"- December 4 demo image check: {identity.get('demo_image')}",
        "",
        "The test target host is lean staging. The December 4 demo was not opened.",
        "",
        "## 3. Build and dataset",
        "",
        f"- Web revision evidence: {identity.get('web_revision')}",
        f"- Data Voyager revision evidence: {identity.get('dv_revision')}",
        f"- API revision evidence: {identity.get('api_revision')}",
        f"- Pre member-months recomputed by the QA oracle: {summary['exposure'].get('pre_member_months')}",
        f"- Post member-months recomputed by the QA oracle: {summary['exposure'].get('post_member_months')}",
        "",
        "## 4. Feature inventory",
        "",
        f"Browser journeys executed: **{browser['journey_count']}**. This is not 287 browser journeys.",
        f"Browser passes: {browser['passed']}. Browser failures: {browser['failed']}.",
        "",
        "| Journey | Result |",
        "| --- | --- |",
    ]
    for row in browser["results"]:
        lines.append(f"| {row['id']} | {'PASS' if row['ok'] else 'FAIL'} |")
    lines += [
        "",
        "## 5. Policy results",
        "",
        f"- Discovered: {summary['policy_count']}",
        f"- Data contract pass: {summary['data_pass']}",
        f"- Data contract fail: {summary['data_fail']}",
        f"- Calculation fail: {summary['calculation_fail']}",
        f"- Browser sample, not the full catalog: {browser['journey_count']}",
        "",
        "Execution classes:",
        "",
    ]
    for key, count in sorted(summary["execution_classes"].items()):
        lines.append(f"- {key}: {count}")
    lines += [
        "",
        "A review-only or blocked row is not counted as an executed mechanism.",
        "A continuation prediction is not counted as policy execution.",
        "",
        "## 6. Lifecycle",
        "",
        "Every discovered policy was checked for a baseline, an observation, a frozen prediction, a verdict, and an execution record.",
        "Payment-rule policies are excluded from the continuation formula.",
        f"Policies whose baseline or observation dollar total disagrees with claim lines by more than $1: {summary['calculation_fail']}.",
        "",
        "## 7. Calculation discrepancies",
        "",
        f"Independent continuation rollup: {summary['rollup']}",
        f"Dashboard payment figure: {payload.get('dashboard', {}).get('payment')}",
        f"Dashboard continuation figure: {payload.get('dashboard', {}).get('continuation')}",
        f"Dashboard comparison: {payload.get('dashboard', {}).get('comparison')}",
        "",
        "Population what-if dollar results were not recomputed claim by claim in this run.",
        "The published payment fixtures were checked only as offline arithmetic, not as the 500k population totals.",
        "",
        "## 8. Dashboard and charts",
        "",
        payload.get("chart_note", ""),
        "",
        "## 9. What-if",
        "",
        payload.get("whatif_note", ""),
        "",
        "## 10. Defects",
        "",
        "| ID | Severity | Status | Feature | Actual |",
        "| --- | --- | --- | --- | --- |",
    ]
    for defect in payload["defects"]:
        lines.append(
            f"| {defect.get('defect_id')} | {defect.get('severity')} | {defect.get('status')} | {defect.get('feature')} | {str(defect.get('actual', '')).replace('|', '/')} |"
        )
    if not payload["defects"]:
        lines.append("|  |  |  |  | No defects recorded |")
    lines += [
        "",
        "## 11. Evidence",
        "",
        "Policy matrix: `docs/production/releases/HEALTHFORESIGHT_QA_POLICY_MATRIX.csv`",
        "Defects: `docs/production/releases/HEALTHFORESIGHT_QA_DEFECTS.csv`",
        "Machine-readable results: `docs/production/releases/HEALTHFORESIGHT_QA_RESULTS.json`",
        "Screenshots are referenced from the browser results and contain no credentials.",
        "",
        "## 12. Regression tests",
        "",
        payload.get("unit_tests", "Offline oracle tests are in `qa/product_agent/test_oracle_arithmetic.py`."),
        "",
        "## 13. Remaining blockers",
        "",
    ]
    for item in payload.get("blockers") or ["None recorded beyond the open defects."]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## 14. Mock-client staging decision",
        "",
        f"**{decision['staging']}**. {decision['staging_reason']}",
        "",
        "## 15. Functional production readiness",
        "",
        f"**{decision['production']}**. {decision['production_reason']}",
        "",
        "This report was generated by `python -m qa.product_agent` after the checks in this file's JSON companion. It is not a manual claim that the backend passed.",
        "",
    ]
    return "\n".join(lines)


def _html(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    rows = []
    for defect in payload["defects"]:
        rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                escape(str(defect.get("defect_id"))),
                escape(str(defect.get("severity"))),
                escape(str(defect.get("status"))),
                escape(str(defect.get("actual"))),
            )
        )
    body = "".join(rows) or "<tr><td colspan='4'>No defects recorded</td></tr>"
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>HealthForesight QA</title>
<style>body{{font-family:sans-serif;margin:2rem}} table{{border-collapse:collapse}} td,th{{border:1px solid #ccc;padding:.4rem}}</style>
</head><body>
<h1>HealthForesight product QA</h1>
<p>Policies {summary['policy_count']}. Data failures {summary['data_fail']}. Calculation failures {summary['calculation_fail']}.</p>
<p>Staging decision: {escape(payload['decision']['staging'])}. Production readiness: {escape(payload['decision']['production'])}.</p>
<table><tr><th>ID</th><th>Severity</th><th>Status</th><th>Actual</th></tr>{body}</table>
</body></html>
"""
