#!/usr/bin/env python3
"""
Autonomous frontend-vs-PDF review for all 250 correction-register policies.

Reads what the staging frontend APIs return (catalog list + workspace
assumptions/guardrails) and scores each policy against the companion CSV/PDF
register. Does not invent codes or mark unresolved authority as PASS.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[1]
REGISTER = (
    REPO
    / "docs/production/releases/corrections/HealthForesight_250_Policy_Correction_Register.csv"
)
OUT_DIR = REPO / "docs/production/releases/corrections"
API = os.environ.get(
    "HF_QA_API",
    "https://hfleanstg-api.whiteplant-64737337.eastus2.azurecontainerapps.io/api/v1",
)
GENERIC_EM = {"99213", "99214", "99215", "99203", "99204"}
NC_AUTHORITY = {
    "LCD L34425 NC MRI Coverage Criteria",
    "North Carolina Mandated Benefit Administration",
}
FAKE_ASSUMPTION = re.compile(
    r"(8\s*%|elasticity|\$1\.50|\$4\s*PMPM|90[- ]day lag|pseudo[- ]?confidence)",
    re.I,
)

# Import lever mapping used at seed time for expected lever family.
sys.path.insert(0, str(REPO / "scripts"))
from lean_staging_apply_250_policy_corrections import _lever_type_from_mechanism  # noqa: E402


def _http(method: str, path: str, token: Optional[str] = None, body: Any = None) -> Any:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.load(resp)


def _fail(checks: list[dict], field: str, expected: str, actual: Any, severity: str = "FAIL") -> None:
    checks.append(
        {
            "field": field,
            "severity": severity,
            "result": severity,
            "expected": expected,
            "actual": actual if not isinstance(actual, (dict, list)) else json.dumps(actual)[:400],
        }
    )


def _pass(checks: list[dict], field: str, note: str = "") -> None:
    checks.append({"field": field, "severity": "INFO", "result": "PASS", "expected": note or "ok", "actual": "ok"})


def _codes(scope: Any, levers: Any) -> set[str]:
    out: set[str] = set()
    if isinstance(scope, dict):
        for c in scope.get("procedure_codes") or []:
            out.add(str(c).strip())
    if isinstance(levers, list):
        for lev in levers:
            if not isinstance(lev, dict):
                continue
            params = lev.get("parameters") or {}
            targets = lev.get("targets") or {}
            for c in list(params.get("codes") or []) + list(targets.get("codes") or []):
                out.add(str(c).strip())
    return {c for c in out if c}


def review_one(reg: dict[str, str], catalog: dict[str, Any], workspace: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict] = []
    name = reg["policy"].strip()
    policy = workspace.get("policy") if isinstance(workspace.get("policy"), dict) else {}
    # Prefer workspace raw definition; fall back to catalog list row.
    scope = policy.get("scope") if policy.get("scope") is not None else catalog.get("scope")
    levers = policy.get("policy_levers") if policy.get("policy_levers") is not None else catalog.get("policy_levers")
    enforcement = policy.get("enforcement") if policy.get("enforcement") is not None else catalog.get("enforcement")
    remediation = catalog.get("remediation") or policy.get("remediation") or (policy.get("metadata") or {}).get("remediation")
    exceptions = catalog.get("global_exceptions") or policy.get("global_exceptions") or []
    assumptions = workspace.get("assumptions") or []
    guardrails = workspace.get("guardrails") or []
    config_state = catalog.get("configuration_state") or policy.get("configuration_state")

    # 1) Presence / identity
    if not catalog:
        _fail(checks, "frontend_catalog_row", "Policy listed on /policies", "MISSING")
        return _rollup(reg, catalog, checks)
    _pass(checks, "frontend_catalog_row", "present on /policies")
    if (catalog.get("name") or "").strip() != name:
        _fail(checks, "name", name, catalog.get("name"))
    else:
        _pass(checks, "name")
    if (catalog.get("policy_type") or "").upper() != (reg.get("type") or "").upper():
        _fail(checks, "policy_type", reg.get("type"), catalog.get("policy_type"))
    else:
        _pass(checks, "policy_type")

    # 2) Definition surfaces must not be null on catalog after API fix
    if scope is None:
        _fail(checks, "scope_frontend", "scope object returned to frontend", None)
    else:
        _pass(checks, "scope_frontend")
    if not levers:
        _fail(checks, "levers_frontend", "non-empty policy_levers on frontend", levers)
    else:
        _pass(checks, "levers_frontend")
    if enforcement is None:
        _fail(checks, "enforcement_frontend", "enforcement object on frontend", None)
    else:
        _pass(checks, "enforcement_frontend")

    # 3) Scope rules from PDF
    if isinstance(scope, dict):
        states = scope.get("states")
        markets = scope.get("markets")
        retain_nc = name in NC_AUTHORITY
        if retain_nc:
            if states != ["NC"]:
                _fail(checks, "scope_nc_authority", "states=['NC'] for named NC authority", states)
            else:
                _pass(checks, "scope_nc_authority")
        else:
            if states == ["NC"] or markets == ["NC"]:
                _fail(checks, "scope_no_nc_default", "NC default removed for national policy", {"states": states, "markets": markets})
            else:
                _pass(checks, "scope_no_nc_default")
            if scope.get("jurisdiction_mode") != "JURISDICTION_NEUTRAL_BASE" and not retain_nc:
                _fail(
                    checks,
                    "scope_jurisdiction_mode",
                    "JURISDICTION_NEUTRAL_BASE",
                    scope.get("jurisdiction_mode"),
                    severity="FAIL",
                )
            else:
                _pass(checks, "scope_jurisdiction_mode")
        svc = scope.get("service_categories")
        exported = (reg.get("exported_service_category") or "").upper()
        if exported == "ED" and svc not in ([], None):
            _fail(checks, "scope_cleared_false_ed", "empty service_categories after ED export", svc)
        else:
            _pass(checks, "scope_service_category")
        codes = _codes(scope, levers)
        bad = sorted(codes & GENERIC_EM)
        if bad:
            _fail(checks, "codes_no_generic_em", "no 99213/99214/99215/99203 targets", bad)
        else:
            _pass(checks, "codes_no_generic_em")
        # PDF: do not fabricate substitutes — empty OK when remap pending
        if reg["status"] == "BLOCK_CLAIMS_EXECUTION_PENDING_REMAP" and not codes:
            _pass(checks, "codes_unverified_empty_allowed", "empty pending remap")
        elif codes:
            _pass(checks, "codes_retained_pending_authority", ",".join(sorted(codes))[:120])
    else:
        _fail(checks, "scope_rules", "dict scope", type(scope).__name__)

    # 4) Lever vs proposed mechanism
    expected_lever = _lever_type_from_mechanism(reg.get("proposed_mechanism") or "", reg.get("type") or "")
    actual_lever = None
    mechanism_note = None
    if isinstance(levers, list) and levers and isinstance(levers[0], dict):
        actual_lever = levers[0].get("lever_type")
        mechanism_note = (levers[0].get("parameters") or {}).get("mechanism_note")
    if actual_lever != expected_lever:
        _fail(checks, "lever_type", expected_lever, actual_lever)
    else:
        _pass(checks, "lever_type")
    proposed = (reg.get("proposed_mechanism") or "").strip()
    if proposed and mechanism_note and proposed not in str(mechanism_note):
        # description may carry it
        desc = catalog.get("description") or policy.get("description") or ""
        if proposed not in desc and proposed not in str(mechanism_note):
            _fail(checks, "proposed_mechanism_visible", proposed[:120], str(mechanism_note)[:120])
        else:
            _pass(checks, "proposed_mechanism_visible")
    elif proposed and (proposed in str(mechanism_note or "") or proposed in (catalog.get("description") or "")):
        _pass(checks, "proposed_mechanism_visible")
    else:
        _fail(checks, "proposed_mechanism_visible", proposed[:120], mechanism_note)

    # 5) Assumptions
    if len(assumptions) < 1:
        _fail(checks, "assumptions_present", ">=1 assumption via workspace", len(assumptions))
    else:
        _pass(checks, "assumptions_present")
    values = [str(a.get("value") or "") for a in assumptions if isinstance(a, dict)]
    texts = " ".join(
        f"{a.get('description','')} {a.get('value','')} {a.get('source','')}" for a in assumptions if isinstance(a, dict)
    )
    if any(v.upper() == "UNESTIMATED" for v in values) or "UNESTIMATED" in texts.upper():
        _pass(checks, "assumptions_unestimated")
    else:
        _fail(checks, "assumptions_unestimated", "UNESTIMATED impact/coding authority", values)
    if FAKE_ASSUMPTION.search(texts):
        _fail(checks, "assumptions_no_fake_defaults", "no 8% elasticity / $1.50-$4 PMPM defaults", texts[:200])
    else:
        _pass(checks, "assumptions_no_fake_defaults")
    req_coding = (reg.get("required_coding_domain") or "").strip()
    if req_coding and req_coding[:40].lower() not in texts.lower() and req_coding not in (catalog.get("description") or ""):
        _fail(checks, "assumptions_coding_domain", req_coding[:120], "not found in assumptions/description", severity="FAIL")
    else:
        _pass(checks, "assumptions_coding_domain")

    # 6) Guardrails — present, not blank PA-denial reuse on unrelated; mechanism templates
    if len(guardrails) < 1:
        _fail(checks, "guardrails_present", ">=1 guardrail via workspace", len(guardrails))
    else:
        _pass(checks, "guardrails_present")
    gtext = " ".join(f"{g.get('metric_name','')} {g.get('description','')}" for g in guardrails if isinstance(g, dict))
    if expected_lever != "PRIOR_AUTH" and re.search(r"\bpa_denial\b|pa-denial", gtext, re.I):
        _fail(checks, "guardrails_not_pa_blanket", "no PA-denial guardrails on non-PA policy", gtext[:200])
    else:
        _pass(checks, "guardrails_not_pa_blanket")

    # 7) Exceptions / enforcement — no blanket override=false
    if isinstance(enforcement, dict):
        if enforcement.get("override_allowed") is False and not enforcement.get("appeals_allowed"):
            _fail(checks, "enforcement_no_blanket_override_false", "override_allowed true or appeals modeled", enforcement)
        else:
            _pass(checks, "enforcement_no_blanket_override_false")
    if not exceptions:
        _fail(checks, "global_exceptions", "explicit exception/appeal block", exceptions)
    else:
        types = {e.get("exception_type") for e in exceptions if isinstance(e, dict)}
        needed = {"EMERGENCY", "APPEAL", "MEDICAL_NECESSITY_REVIEW"}
        if not needed.issubset(types):
            _fail(checks, "global_exceptions_types", sorted(needed), sorted(types))
        else:
            _pass(checks, "global_exceptions")

    # 8) Register disposition / claims block visible
    expected_state = (
        "BLOCKED"
        if reg["status"] == "BLOCK_CLAIMS_EXECUTION_PENDING_REMAP"
        else "REVIEW_ONLY"
        if reg["status"] == "REVIEW_REQUIRED_NO_AUTHORITY_CERTIFICATION"
        else None
    )
    if config_state != expected_state:
        _fail(checks, "configuration_state_frontend", expected_state, config_state)
    else:
        _pass(checks, "configuration_state_frontend")
    if not isinstance(remediation, dict):
        _fail(checks, "remediation_frontend", "remediation envelope on frontend", remediation)
    else:
        if remediation.get("register_status") != reg["status"]:
            _fail(checks, "remediation_register_status", reg["status"], remediation.get("register_status"))
        else:
            _pass(checks, "remediation_register_status")
        if remediation.get("claims_execution_blocked") is not True and remediation.get("execution_eligibility") != "BLOCKED":
            _fail(
                checks,
                "claims_execution_blocked",
                "BLOCKED",
                {
                    "claims_execution_blocked": remediation.get("claims_execution_blocked"),
                    "execution_eligibility": remediation.get("execution_eligibility"),
                },
            )
        else:
            _pass(checks, "claims_execution_blocked")
        if remediation.get("proposed_mechanism") != reg.get("proposed_mechanism"):
            _fail(
                checks,
                "remediation_proposed_mechanism",
                (reg.get("proposed_mechanism") or "")[:120],
                (remediation.get("proposed_mechanism") or "")[:120],
            )
        else:
            _pass(checks, "remediation_proposed_mechanism")

    return _rollup(reg, catalog, checks)


def _rollup(reg: dict, catalog: dict, checks: list[dict]) -> dict[str, Any]:
    fails = [c for c in checks if c["result"] == "FAIL"]
    passes = [c for c in checks if c["result"] == "PASS"]
    if not catalog:
        overall = "FAIL"
    elif fails:
        overall = "FAIL"
    else:
        overall = "PASS"
    return {
        "index": int(reg["index"]),
        "policy": reg["policy"],
        "register_type": reg.get("type"),
        "register_status": reg.get("status"),
        "frontend_policy_id": (catalog or {}).get("id"),
        "overall": overall,
        "pass_count": len(passes),
        "fail_count": len(fails),
        "failures": fails,
        "checks": checks,
    }


def main() -> int:
    email = os.environ.get("HF_QA_EMAIL", "synthetic.local@example.com")
    password = os.environ.get("HF_QA_PASSWORD", "synthetic-local-only")
    register = list(csv.DictReader(REGISTER.open(encoding="utf-8")))
    if len(register) != 250:
        raise SystemExit(f"Expected 250 register rows, got {len(register)}")

    token = _http("POST", "/auth/login", body={"email": email, "password": password})["access_token"]
    catalog_rows = _http("GET", "/policies?limit=500", token=token)
    if not isinstance(catalog_rows, list):
        catalog_rows = catalog_rows.get("items") or []
    by_name = {(p.get("name") or "").strip(): p for p in catalog_rows}

    results = []
    for reg in register:
        name = reg["policy"].strip()
        cat = by_name.get(name) or {}
        ws: dict[str, Any] = {}
        if cat.get("id"):
            try:
                ws = _http("GET", f"/policies/{cat['id']}/workspace", token=token)
            except Exception as e:
                ws = {"_error": str(e)}
        results.append(review_one(reg, cat, ws if isinstance(ws, dict) else {}))

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api": API,
        "register_rows": 250,
        "frontend_catalog_count": len(catalog_rows),
        "exact_name_match": sum(1 for r in results if r.get("frontend_policy_id")),
        "overall_pass": sum(1 for r in results if r["overall"] == "PASS"),
        "overall_fail": sum(1 for r in results if r["overall"] == "FAIL"),
        "failure_fields": dict(Counter(f["field"] for r in results for f in r["failures"])),
        "by_register_status": dict(Counter(r["register_status"] for r in results)),
        "acceptance": {
            "pdf_catalog_accounted": f"{sum(1 for r in results if r.get('frontend_policy_id'))}/250",
            "definition_parity_pass": sum(1 for r in results if r["overall"] == "PASS"),
            "definition_parity_fail": sum(1 for r in results if r["overall"] == "FAIL"),
            "claims_executable_certified": 0,
            "note": (
                "PASS means frontend-visible definition/scope/levers/assumptions/guardrails/"
                "exceptions/remediation match the correction register rules. "
                "It does NOT mean CLAIMS_EXECUTABLE or authority-certified coding."
            ),
        },
        "policies": results,
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = OUT_DIR / f"FRONTEND_PDF_POLICY_DEFINITION_REVIEW_{stamp}.json"
    md_path = OUT_DIR / f"FRONTEND_PDF_POLICY_DEFINITION_REVIEW_{stamp}.md"
    csv_path = OUT_DIR / f"FRONTEND_PDF_POLICY_DEFINITION_REVIEW_{stamp}.csv"
    latest_json = OUT_DIR / "FRONTEND_PDF_POLICY_DEFINITION_REVIEW.json"
    latest_md = OUT_DIR / "FRONTEND_PDF_POLICY_DEFINITION_REVIEW.md"
    latest_csv = OUT_DIR / "FRONTEND_PDF_POLICY_DEFINITION_REVIEW.csv"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(summary, indent=2)
    json_path.write_text(payload, encoding="utf-8")
    latest_json.write_text(payload, encoding="utf-8")

    lines = [
        "# Frontend vs PDF Policy Definition Review",
        "",
        f"Generated: `{summary['generated_at']}`",
        f"API: `{API}`",
        "",
        "## Verdict",
        "",
        f"- Register rows: **250**",
        f"- Frontend catalog rows: **{summary['frontend_catalog_count']}**",
        f"- Exact name match: **{summary['exact_name_match']}/250**",
        f"- Definition parity PASS: **{summary['overall_pass']}**",
        f"- Definition parity FAIL: **{summary['overall_fail']}**",
        f"- Claims-executable certified: **0** (correct; PDF forbids fabricating authority)",
        "",
        summary["acceptance"]["note"],
        "",
        "## Failure field totals",
        "",
    ]
    if summary["failure_fields"]:
        lines.append("| Field | Fail count |")
        lines.append("| --- | ---: |")
        for field, n in sorted(summary["failure_fields"].items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"| `{field}` | {n} |")
    else:
        lines.append("No field failures.")
    lines += ["", "## Policy results", "", "| # | Policy | Overall | Pass | Fail | Failed fields |", "| --- | --- | --- | ---: | ---: | --- |"]
    for r in results:
        fields = ", ".join(f["field"] for f in r["failures"]) or "—"
        lines.append(
            f"| {r['index']} | {r['policy']} | **{r['overall']}** | {r['pass_count']} | {r['fail_count']} | {fields} |"
        )
    md = "\n".join(lines) + "\n"
    md_path.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "index",
                "policy",
                "register_status",
                "overall",
                "pass_count",
                "fail_count",
                "failed_fields",
                "frontend_policy_id",
            ],
        )
        w.writeheader()
        for r in results:
            w.writerow(
                {
                    "index": r["index"],
                    "policy": r["policy"],
                    "register_status": r["register_status"],
                    "overall": r["overall"],
                    "pass_count": r["pass_count"],
                    "fail_count": r["fail_count"],
                    "failed_fields": ";".join(f["field"] for f in r["failures"]),
                    "frontend_policy_id": r.get("frontend_policy_id"),
                }
            )
    latest_csv.write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")

    print(
        json.dumps(
            {
                "overall_pass": summary["overall_pass"],
                "overall_fail": summary["overall_fail"],
                "failure_fields": summary["failure_fields"],
                "report_json": str(latest_json),
                "report_md": str(latest_md),
                "report_csv": str(latest_csv),
            },
            indent=2,
        )
    )
    return 0 if summary["overall_fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
