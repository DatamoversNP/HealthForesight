#!/usr/bin/env python3
"""
Lean staging ONLY: delete ALL policies + lifecycle, seed the nine mock-client
policy definition PDFs, then smoke-check the frontend API catalog.

Does not touch claims_lines / enrollment_records / Dec4 demo.
Does not invent payment factors, clinical criteria, or lifecycle runs.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4, uuid5

REPO = Path(__file__).resolve().parents[1]
ATTACH = Path(
    "/Users/nileshl/.cursor/projects/Users-nileshl-Private-HealthForesight/attachments/"
    "202af80e-02cb-4eab-aab3-cbc7c62b7711"
)
DOCS = REPO / "docs/production/releases/corrections/nine_mock_policies"
SPEC_VERSION = "nine_mock_policy_pdfs_2026-11-07"
TENANT = UUID("00000000-0000-0000-0000-000000000001")
NAMESPACE = UUID("b19e0009-0000-4000-9000-a0c49a01c1e5")
API = os.environ.get(
    "HF_QA_API",
    "https://hfleanstg-api.whiteplant-64737337.eastus2.azurecontainerapps.io/api/v1",
)

POPULATION_TABLES = ("claims_lines", "enrollment_records")
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

# Exact nine mock policies from uploaded PDFs. Types map to platform PolicyType.
NINE: list[dict[str, Any]] = [
    {
        "index": 1,
        "name": "Outpatient MRI Prior Authorization",
        "policy_type": "PRIOR_AUTH",
        "mechanism": "OUTPATIENT_MRI_PRIOR_AUTH",
        "configuration_state": "REVIEW_ONLY",
        "pdf": "HealthForesight_Outpatient_MRI_Prior_Authorization_Mock_Policy__1_.pdf",
        "purpose": (
            "Prospective authorization-review workflow for specified outpatient lumbar spine MRI "
            "services; no automatic denial."
        ),
        "proposed_mechanism": "PRIOR AUTH: prospective review routing; no automatic denial",
        "candidate_codes": ["72148", "72149"],
        "excluded_codes": ["99213", "99214"],
        "lever_type": "PRIOR_AUTH",
        "required_coding_domain": "CPT lumbar MRI targets with verified edition; ICD-10-CM pending",
        "jurisdiction_mode": "EXPLICIT_PRODUCT_REQUIRED",
        "register_status": "REVIEW_REQUIRED_NO_AUTHORITY_CERTIFICATION",
    },
    {
        "index": 2,
        "name": "National Coverage Determination Study — MRI (NCD 220.2)",
        "policy_type": "COVERAGE",
        "mechanism": "NCD_COVERAGE_STUDY",
        "configuration_state": "REVIEW_ONLY",
        "pdf": "HealthForesight_NCD_220_2_MRI_Mock_Policy.pdf",
        "purpose": (
            "Evaluate Medicare NCD 220.2 coverage applicability for MRI-related claims; "
            "not automatic clinical adjudication."
        ),
        "proposed_mechanism": "COVERAGE: NCD applicability and documentation review",
        "candidate_codes": [],
        "excluded_codes": [],
        "lever_type": "COVERAGE",
        "required_coding_domain": "CMS NCD 220.2 source text, version, effective dates, Medicare coding maps",
        "jurisdiction_mode": "MEDICARE_NATIONAL",
        "register_status": "REVIEW_REQUIRED_NO_AUTHORITY_CERTIFICATION",
        "source_authority": "NCD 220.2",
    },
    {
        "index": 3,
        "name": "Local Coverage Determination Study — LCD L34425",
        "policy_type": "COVERAGE",
        "mechanism": "LCD_COVERAGE_STUDY",
        "configuration_state": "REVIEW_ONLY",
        "pdf": "HealthForesight_LCD_L34425_Study_Mock_Policy.pdf",
        "purpose": (
            "Evaluate coverage applicability for LCD L34425 within verified contractor and "
            "jurisdiction boundaries."
        ),
        "proposed_mechanism": "COVERAGE: LCD applicability and documentation review",
        "candidate_codes": [],
        "excluded_codes": [],
        "lever_type": "COVERAGE",
        "required_coding_domain": "LCD L34425 + linked coding articles, MAC/contractor, effective dates",
        "jurisdiction_mode": "STATE_CONTRACTOR_SPECIFIC",
        "register_status": "REVIEW_REQUIRED_NO_AUTHORITY_CERTIFICATION",
        "source_authority": "LCD L34425",
        "retain_nc": True,
    },
    {
        "index": 4,
        "name": "Infusion Site-of-Care and Reimbursement Policy",
        "policy_type": "SITE_OF_CARE",
        "mechanism": "INFUSION_SITE_OF_CARE",
        "configuration_state": "BLOCKED",
        "pdf": "HealthForesight_Infusion_Site_of_Care_Mock_Policy.pdf",
        "purpose": (
            "Evaluate eligible infusion therapies across HOPD, office and home/ambulatory settings; "
            "payment simulation requires verified rate schedules."
        ),
        "proposed_mechanism": "SITE OF CARE: infusion site differential and/or alternate-site routing",
        "candidate_codes": [],
        "excluded_codes": [],
        "lever_type": "SITE_OF_CARE",
        "required_coding_domain": "HCPCS/J-codes or NDC, dose/units, site, rate schedule",
        "jurisdiction_mode": "EXPLICIT_PRODUCT_REQUIRED",
        "register_status": "BLOCK_CLAIMS_EXECUTION_PENDING_REMAP",
    },
    {
        "index": 5,
        "name": "Outpatient Therapy Utilization and Payment Policy",
        "policy_type": "COVERAGE",
        "mechanism": "THERAPY",
        "configuration_state": "REVIEW_ONLY",
        "pdf": "HealthForesight_Therapy_Outpatient_Therapy_Mock_Policy.pdf",
        "purpose": (
            "Evaluate outpatient PT/OT/speech therapy for coverage, utilization and payment rules; "
            "no blanket visit reduction assumed."
        ),
        "proposed_mechanism": "COVERAGE: therapy utilization monitoring / review; payment edit only if parameterized",
        "candidate_codes": [],
        "excluded_codes": [],
        "lever_type": "COVERAGE",
        "required_coding_domain": "Therapy CPT/HCPCS by discipline, modifiers, visit/unit grain, benefit rules",
        "jurisdiction_mode": "EXPLICIT_PRODUCT_REQUIRED",
        "register_status": "REVIEW_REQUIRED_NO_AUTHORITY_CERTIFICATION",
    },
    {
        "index": 6,
        "name": "Medically Unlikely Edit (MUE) / Unit Cap",
        "policy_type": "CODING_AND_BILLING",
        "mechanism": "UNIT_CAP",
        "configuration_state": "BLOCKED",
        "pdf": "HealthForesight_MUE_Medically_Unlikely_Edit_Mock_Policy.pdf",
        "purpose": (
            "Test configured maximum units for eligible services at the correct adjudication grain."
        ),
        "proposed_mechanism": "PAYMENT EDIT: code-specific unit cap / MUE",
        "candidate_codes": [],
        "excluded_codes": [],
        "lever_type": "QUANTITY_LIMIT",
        "required_coding_domain": "CPT/HCPCS, code-specific unit thresholds, adjudication indicator, unit price basis",
        "jurisdiction_mode": "EXPLICIT_PRODUCT_REQUIRED",
        "register_status": "BLOCK_CLAIMS_EXECUTION_PENDING_REMAP",
    },
    {
        "index": 7,
        "name": "Procedure-to-Procedure (PTP) Coding Edit",
        "policy_type": "CODING_AND_BILLING",
        "mechanism": "PTP_EDIT",
        "configuration_state": "BLOCKED",
        "pdf": "HealthForesight_PTP_Procedure_to_Procedure_Edit_Mock_Policy.pdf",
        "purpose": (
            "Identify configured procedure-code pairs that cannot both be reimbursed under the edit."
        ),
        "proposed_mechanism": "PAYMENT EDIT: procedure-to-procedure coding edit",
        "candidate_codes": [],
        "excluded_codes": [],
        "lever_type": "PAYMENT_POLICY",
        "required_coding_domain": "PTP edit-table edition, pair direction, modifier indicator, grouping keys",
        "jurisdiction_mode": "EXPLICIT_PRODUCT_REQUIRED",
        "register_status": "BLOCK_CLAIMS_EXECUTION_PENDING_REMAP",
    },
    {
        "index": 8,
        "name": "Imaging Site-of-Service Policy",
        "policy_type": "SITE_OF_CARE",
        "mechanism": "SITE_OF_SERVICE",
        "configuration_state": "BLOCKED",
        "pdf": "HealthForesight_SOS_Imaging_Site_of_Service_Mock_Policy.pdf",
        "purpose": (
            "Evaluate imaging across hospital outpatient and freestanding/office sites using an "
            "explicit site-of-service payment or steerage rule."
        ),
        "proposed_mechanism": "SITE OF CARE: imaging site differential and/or steerage",
        "candidate_codes": [],
        "excluded_codes": [],
        "lever_type": "SITE_OF_CARE",
        "required_coding_domain": "Imaging CPT/HCPCS, POS/facility class, rate schedule or steerage assumptions",
        "jurisdiction_mode": "EXPLICIT_PRODUCT_REQUIRED",
        "register_status": "BLOCK_CLAIMS_EXECUTION_PENDING_REMAP",
    },
    {
        "index": 9,
        "name": "Multiple Procedure Payment Reduction (MPPR)",
        "policy_type": "PAYMENT_POLICY",
        "mechanism": "PAYMENT_EDIT",
        "configuration_state": "BLOCKED",
        "pdf": "HealthForesight_MPPR_Multiple_Procedure_Payment_Reduction_Mock_Policy.pdf",
        "purpose": (
            "Apply a configurable multiple-procedure payment adjustment to eligible secondary "
            "procedures; mock repricing, not payer adjudication."
        ),
        "proposed_mechanism": "PAYMENT EDIT: multiple procedure payment reduction",
        "candidate_codes": [],
        "excluded_codes": [],
        "lever_type": "PAYMENT_POLICY",
        "required_coding_domain": "Code family, secondary reduction factor(s), grouping keys, fee/allowed precedence",
        "jurisdiction_mode": "EXPLICIT_PRODUCT_REQUIRED",
        "register_status": "BLOCK_CLAIMS_EXECUTION_PENDING_REMAP",
    },
]


def _assert_lean(url: str) -> None:
    low = url.lower()
    if "hfleanstg" not in low:
        raise SystemExit("Refusing: DATABASE_URL is not lean staging.")


def _counts(cur, tables: tuple[str, ...]) -> dict[str, int]:
    out: dict[str, int] = {}
    for t in tables:
        cur.execute("SELECT to_regclass(%s)", (t,))
        if not cur.fetchone()[0]:
            continue
        cur.execute(f"SELECT count(*) FROM {t}")
        out[t] = int(cur.fetchone()[0])
    return out


def _exceptions() -> list[dict[str, Any]]:
    return [
        {"exception_type": "EMERGENCY", "description": "Emergency / emergent services exempt where legally required", "override_allowed": True},
        {"exception_type": "CONTINUITY_OF_CARE", "description": "Continuity-of-care / active treatment exceptions", "override_allowed": True},
        {"exception_type": "MEDICAL_NECESSITY_REVIEW", "description": "Documented medical necessity / clinical exception path", "override_allowed": True, "requires_review": True},
        {"exception_type": "APPEAL", "description": "Member/provider appeal and external review rights preserved", "override_allowed": True},
    ]


def _meta(row: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    retain_nc = bool(row.get("retain_nc"))
    codes = list(row.get("candidate_codes") or [])
    code_state = "CANDIDATE_PENDING_EDITION_VERIFY" if codes else "UNVERIFIED_CODE_MAPPING"
    scope = {
        "procedure_codes": codes,
        "excluded_procedure_codes": list(row.get("excluded_codes") or []),
        "service_categories": [],
        "lob": ["MEDICARE"] if "NCD" in row["mechanism"] or "LCD" in row["mechanism"] else None,
        "states": ["NC"] if retain_nc else None,
        "markets": ["NC"] if retain_nc else None,
        "setting": ["OUTPATIENT"],
        "jurisdiction_mode": row["jurisdiction_mode"],
        "applicability_overlays": [],
        "source_authority": row.get("source_authority"),
    }
    return {
        "mock_execution_v1": False,
        "mechanism_executed": False,
        "result_class": "NOT_EXECUTED",
        "evidence_class": "DEFINITION_ONLY",
        "execution": "NOT_IMPLEMENTED",
        "configuration_state": row["configuration_state"],
        "blocked_reason": row["register_status"],
        "mechanism": row["mechanism"],
        "scope": scope,
        "policy_levers": [
            {
                "lever_type": row["lever_type"],
                "targets": {
                    "code_system": "CPT_OR_HCPCS" if codes else "PENDING",
                    "code_type": "CPT" if codes else "PENDING",
                    "codes": codes,
                    "code_groups": [],
                    "excluded_codes": list(row.get("excluded_codes") or []),
                },
                "parameters": {
                    "mechanism_note": row["proposed_mechanism"],
                    "parameters_certified": False,
                    "requires_pa": row["lever_type"] == "PRIOR_AUTH",
                    "clinical_criteria_certified": False,
                },
            }
        ],
        "assumptions": [
            {
                "assumption_type": "IMPACT",
                "description": (
                    f"Quantitative intervention impact for '{row['name']}' is UNESTIMATED. "
                    "Continuation forecast only when cohort/exposure are valid."
                ),
                "value": "UNESTIMATED",
                "source": SPEC_VERSION,
                "evidence_state": "UNESTIMATED",
            },
            {
                "assumption_type": "CODING_AUTHORITY",
                "description": f"Authoritative coding pending validation. Required domain: {row['required_coding_domain']}",
                "value": "UNESTIMATED",
                "source": SPEC_VERSION,
                "evidence_state": "UNESTIMATED",
            },
        ],
        "guardrails": [
            {
                "metric_name": "policy_outcome_review",
                "threshold_type": "review",
                "threshold_value": None,
                "action": "manual_review",
                "description": f"Manual outcome review required for {row['name']}",
                "evidence_state": "TEMPLATE_PENDING_CALIBRATION",
                "source": SPEC_VERSION,
            },
            {
                "metric_name": "measurement_integrity",
                "threshold_type": "review",
                "threshold_value": None,
                "action": "manual_review",
                "description": (
                    "Do not label continuation as causal impact; unequal periods must be explicit; "
                    "missing auth/edit events are NOT_MEASURABLE."
                ),
                "evidence_state": "TEMPLATE_PENDING_CALIBRATION",
                "source": SPEC_VERSION,
            },
        ],
        "global_exceptions": _exceptions(),
        "enforcement": {
            "mechanism": "REVIEW_REQUIRED",
            "touchpoint": ["MANUAL_REVIEW"],
            "override_allowed": True,
            "appeals_allowed": True,
            "override_note": "No blanket override=false; exceptions/appeals modeled explicitly",
        },
        "code_systems": {
            "systems": [
                {
                    "system": "CPT_OR_HCPCS" if codes else "PENDING",
                    "codes": codes,
                    "excluded_codes": list(row.get("excluded_codes") or []),
                    "state": code_state,
                    "certified": False,
                }
            ]
        },
        "remediation": {
            "spec_version": SPEC_VERSION,
            "applied_at": now,
            "register_index": row["index"],
            "register_status": row["register_status"],
            "execution_eligibility": "BLOCKED",
            "evidence_state": "PROVENANCE_ONLY" if row["configuration_state"] == "REVIEW_ONLY" else "CODE_REVIEW_REQUIRED",
            "code_mapping_state": code_state,
            "proposed_mechanism": row["proposed_mechanism"],
            "required_coding_domain": row["required_coding_domain"],
            "claims_execution_blocked": True,
            "source_pdf": row["pdf"],
            "provenance": {
                "source_specification": row["pdf"],
                "publisher": "mock_client_nine_policy_pack_2026-11-07",
                "review_state": row["register_status"],
                "jurisdiction": "NC" if retain_nc else row["jurisdiction_mode"],
                "licensing_limitations": "No fabricated CPT/HCPCS/NDC/MUE/formulary lists or payment factors",
            },
        },
        "seed": {
            "source": "nine_mock_policy_pdfs",
            "spec_version": SPEC_VERSION,
            "seeded_at": now,
            "lifecycle_seeded": False,
        },
    }


def _copy_pdfs() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    for row in NINE:
        src = ATTACH / row["pdf"]
        if not src.exists():
            # MRI may also exist without __1_
            alt = ATTACH / row["pdf"].replace("__1_", "")
            if alt.exists():
                src = alt
            else:
                raise SystemExit(f"Missing PDF: {row['pdf']}")
        shutil.copy2(src, DOCS / row["pdf"].replace("__1_", ""))


def _http(method: str, path: str, token: str | None = None, body: Any = None) -> Any:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def main() -> int:
    url = os.environ.get("DATABASE_URL") or ""
    _assert_lean(url)
    _copy_pdfs()

    import psycopg2

    conn = psycopg2.connect(url.replace("postgresql+psycopg2://", "postgresql://", 1))
    conn.autocommit = False
    cur = conn.cursor()
    try:
        cur.execute("SELECT current_database()")
        dbname = cur.fetchone()[0]
        if dbname != "hfleanstg":
            raise SystemExit(f"Refusing unexpected database: {dbname}")

        before_pop = _counts(cur, POPULATION_TABLES)
        before_life = _counts(cur, ("policies", "observations", "baselines", "policy_predicted_impacts"))
        print(json.dumps({"phase": "before", "population": before_pop, "lifecycle": before_life}, indent=2))

        for table in LIFECYCLE_DELETE_ORDER:
            cur.execute("SELECT to_regclass(%s)", (table,))
            if not cur.fetchone()[0]:
                continue
            if table == "baselines":
                cur.execute("UPDATE baselines SET parent_baseline_id = NULL")
            if table == "observations":
                cur.execute("UPDATE observations SET baseline_version_id = NULL, prediction_id = NULL")
            cur.execute(f"DELETE FROM {table}")
            print(f"deleted {table}: {cur.rowcount}")

        now = datetime.utcnow()
        seeded = []
        for row in NINE:
            pid = uuid5(NAMESPACE, f"{row['index']}:{row['name']}")
            meta = _meta(row)
            description = (
                f"{row['purpose']}\n\n"
                f"Mechanism: {row['mechanism']}. "
                f"Register status: {row['register_status']}. "
                f"Required coding: {row['required_coding_domain']}. "
                "Not claims-executable until authority-certified remap. "
                f"Source PDF: {row['pdf']}."
            )
            cur.execute(
                """
                INSERT INTO policies (
                    id, tenant_id, name, policy_type, owner_role, description,
                    status, policy_metadata_json, created_at, updated_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s)
                """,
                (
                    str(pid),
                    str(TENANT),
                    row["name"],
                    row["policy_type"],
                    "Mock Client",
                    description,
                    "ACTIVE",
                    json.dumps(meta),
                    now,
                    now,
                ),
            )
            for a in meta["assumptions"]:
                cur.execute(
                    """
                    INSERT INTO policy_assumptions (
                        id, tenant_id, policy_id, assumption_type, description,
                        value, source, confidence, range_json, created_at, updated_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s)
                    """,
                    (
                        str(uuid4()),
                        str(TENANT),
                        str(pid),
                        a["assumption_type"],
                        a["description"],
                        str(a.get("value")),
                        a.get("source"),
                        None,
                        json.dumps({"evidence_state": a.get("evidence_state")}),
                        now,
                        now,
                    ),
                )
            for g in meta["guardrails"]:
                cur.execute(
                    """
                    INSERT INTO policy_guardrails (
                        id, tenant_id, policy_id, metric_name, description,
                        threshold_type, threshold_value, action, triggered,
                        last_checked_at, created_at, updated_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        str(uuid4()),
                        str(TENANT),
                        str(pid),
                        g["metric_name"],
                        g["description"],
                        g.get("threshold_type") or "review",
                        0.0,
                        g.get("action") or "manual_review",
                        False,
                        None,
                        now,
                        now,
                    ),
                )
            seeded.append(
                {
                    "index": row["index"],
                    "policy_id": str(pid),
                    "name": row["name"],
                    "policy_type": row["policy_type"],
                    "mechanism": row["mechanism"],
                    "configuration_state": row["configuration_state"],
                    "pdf": row["pdf"],
                }
            )

        after_pop = _counts(cur, POPULATION_TABLES)
        after_life = _counts(cur, ("policies", "observations", "baselines", "policy_predicted_impacts", "policy_assumptions", "policy_guardrails"))
        if after_pop != before_pop:
            raise SystemExit(json.dumps({"population_changed": True, "before": before_pop, "after": after_pop}, indent=2))
        if after_life.get("policies") != 9:
            raise SystemExit(f"Expected 9 policies, got {after_life.get('policies')}")
        if after_life.get("observations", 0) or after_life.get("baselines", 0):
            raise SystemExit("Lifecycle leftovers remain")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    # Frontend / API validation
    email = os.environ.get("HF_QA_EMAIL", "synthetic.local@example.com")
    password = os.environ.get("HF_QA_PASSWORD", "synthetic-local-only")
    token = _http("POST", "/auth/login", body={"email": email, "password": password})["access_token"]
    catalog = _http("GET", "/policies?limit=100", token=token)
    if not isinstance(catalog, list):
        catalog = catalog.get("items") or []
    by_name = {(p.get("name") or "").strip(): p for p in catalog}
    frontend_checks = []
    for row in NINE:
        p = by_name.get(row["name"])
        ok = bool(p)
        detail = {}
        if p:
            detail = {
                "id": p.get("id"),
                "policy_type": p.get("policy_type"),
                "type_match": p.get("policy_type") == row["policy_type"],
                "has_scope": p.get("scope") is not None,
                "has_levers": bool(p.get("policy_levers")),
                "configuration_state": p.get("configuration_state"),
                "remediation_status": (p.get("remediation") or {}).get("register_status"),
            }
            try:
                ws = _http("GET", f"/policies/{p['id']}/workspace", token=token)
                detail["workspace_assumptions"] = len(ws.get("assumptions") or [])
                detail["workspace_guardrails"] = len(ws.get("guardrails") or [])
            except Exception as e:
                detail["workspace_error"] = str(e)[:200]
                ok = False
            if p.get("policy_type") != row["policy_type"]:
                ok = False
            if p.get("scope") is None or not p.get("policy_levers"):
                # Older API revision may strip; still report
                detail["definition_surface"] = "partial_or_stripped"
        frontend_checks.append({"name": row["name"], "ok": ok, **detail})

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": "hfleanstg",
        "population_preserved": before_pop,
        "seeded": seeded,
        "after_counts": after_life,
        "frontend_catalog_count": len(catalog),
        "frontend_expected_9": len(catalog) == 9,
        "frontend_all_named": all(c["ok"] for c in frontend_checks),
        "frontend_checks": frontend_checks,
        "pdf_dir": str(DOCS),
    }
    out = DOCS / "NINE_MOCK_POLICY_SEED_REPORT.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k not in {"seeded", "frontend_checks"}}, indent=2))
    print(json.dumps({"frontend_checks": frontend_checks}, indent=2))
    print(f"report={out}")
    if not report["frontend_expected_9"] or not report["frontend_all_named"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
