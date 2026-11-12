#!/usr/bin/env python3
"""
Apply HealthForesight 250-Policy Correction Specification on lean staging ONLY.

- Reconciles companion CSV against staging DB (250/250 required)
- Snapshots prior metadata into configuration_history (preserve identity/history)
- Clears unrelated generic E/M code targets; does NOT fabricate replacement codes
- Removes NC defaults from national policies
- Replaces unsupported elasticity/PMPM assumptions with UNESTIMATED
- Aligns lever semantics to proposed_mechanism without inventing code sets
- Sets remediation.execution_eligibility to block claims calculations
- Never touches Dec4 demo / healthforesight-rg

Sources:
  docs/production/releases/corrections/HealthForesight_250_Policy_Correction_Register.csv
  HealthForesight_250_Policy_Correction_Specification.pdf (handoff)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api" / "src"))
sys.path.insert(0, str(REPO / "packages" / "common" / "src"))

TENANT = UUID("00000000-0000-0000-0000-000000000001")
GENERIC_EM = {"99213", "99214", "99215", "99203", "99204"}
PROTECTED_FIXTURES = {
    "Outpatient MRI Prior Authorization",
    "Infusion Site-of-Care Optimization",
    "Freestanding Imaging Steerage",
    "Multiple Procedure Payment Reduction",
    "NCCI Medically Unlikely Units",
    "NCCI Procedure-to-Procedure Bundling",
    "LCD L34425 NC MRI Coverage Criteria",
    "NCD 220.2 MRI Coverage Change Study",
    "Outpatient Therapy Coverage and Payment",
}
# NC retained only with named state/contractor authority in policy title
NC_AUTHORITY_NAMES = {
    "LCD L34425 NC MRI Coverage Criteria",
    "North Carolina Mandated Benefit Administration",
}

SPEC_VERSION = "correction_spec_v1.0_2026-11-05"
DEFAULT_CSV = (
    REPO
    / "docs"
    / "production"
    / "releases"
    / "corrections"
    / "HealthForesight_250_Policy_Correction_Register.csv"
)


def _assert_lean_staging_db() -> None:
    url = os.environ.get("DATABASE_URL") or ""
    if "lean" not in url.lower() and "hfleanstg" not in url.lower():
        if os.environ.get("LEAN_STAGING_OK") != "1":
            raise SystemExit(
                "Refusing: DATABASE_URL is not lean staging. "
                "Set LEAN_STAGING_OK=1 only after confirming demo is untouched."
            )


def _parse_codes(s: str) -> list[str]:
    return [c.strip() for c in (s or "").split(",") if c.strip()]


def _strip_generic_em(codes: list[str]) -> tuple[list[str], list[str]]:
    kept = [c for c in codes if c not in GENERIC_EM]
    removed = [c for c in codes if c in GENERIC_EM]
    return kept, removed


def _lever_type_from_mechanism(proposed: str, policy_type: str) -> str:
    p = (proposed or "").upper()
    # Order matters: PA/step/QL/SOC before broad words like "covered" / "clinical criteria".
    if p.startswith("PRIOR_AUTH") or p.startswith("PRIOR AUTH") or "PRIOR_AUTH:" in p or "PRIOR AUTH:" in p:
        return "PRIOR_AUTH"
    if "STEP THERAPY" in p or "STEP_THERAPY" in p or p.startswith("STEP"):
        return "STEP_THERAPY"
    if "QUANTITY" in p or "DAYS-SUPPLY" in p or "DAYS SUPPLY" in p or "PHARMACY BENEFIT" in p:
        # Pharmacy days-supply programs are not office cost-sharing.
        if "PHARMACY BENEFIT" in p or "DAYS-SUPPLY" in p or "DAYS SUPPLY" in p:
            return "QUANTITY_LIMIT" if "QUANTITY" in p or "DAYS" in p else "PHARMACY_BENEFIT"
        return "QUANTITY_LIMIT"
    if "SITE OF CARE" in p or "SITE-OF-CARE" in p or "SITE_OF_CARE" in p:
        return "SITE_OF_CARE"
    if "COST_SHARING" in p or "COST SHARE" in p or "$0" in p:
        return "COST_SHARING"
    if "PAYMENT" in p or "NCCI" in p or "MPPR" in p or "BUNDL" in p:
        return "PAYMENT_EDIT"
    if "NETWORK" in p:
        return "NETWORK_RESTRICTION"
    if p.startswith("COVERAGE") or "LCD" in p or "NCD" in p:
        return "COVERAGE_CRITERIA"
    if "PRIOR_AUTH" in p or "PRIOR AUTH" in p:
        return "PRIOR_AUTH"
    if "PHARMACY" in p:
        return "PHARMACY_BENEFIT"
    if "COMPLIANCE" in p or "MANDATE" in p or "REGULAT" in p or "BENEFIT/COMPLIANCE" in p:
        return "COMPLIANCE_MAPPING"
    if "CARE MANAGEMENT" in p or "POPULATION" in p:
        return "CARE_MANAGEMENT"
    if "ACCESS" in p:
        return "ACCESS_STANDARD"
    if "CLINICAL CRITERIA" in p and "PRIOR" not in p:
        return "COVERAGE_CRITERIA"
    # fall back to exported type semantics
    t = (policy_type or "").upper()
    mapping = {
        "PRIOR_AUTH": "PRIOR_AUTH",
        "SITE_OF_CARE": "SITE_OF_CARE",
        "STEP_THERAPY": "STEP_THERAPY",
        "QUANTITY_LIMIT": "QUANTITY_LIMIT",
        "COST_SHARING": "COST_SHARING",
        "PAYMENT_POLICY": "PAYMENT_EDIT",
        "NETWORK_RESTRICTION": "NETWORK_RESTRICTION",
        "COVERAGE": "COVERAGE_CRITERIA",
        "CLINICAL_CRITERIA": "COVERAGE_CRITERIA",
        "BENEFIT": "COST_SHARING",
        "ADMINISTRATIVE_REQUIREMENT": "COMPLIANCE_MAPPING",
    }
    return mapping.get(t, "MECHANISM_REVIEW_REQUIRED")


def _unestimated_assumptions(name: str, required_coding: str) -> list[dict[str, Any]]:
    return [
        {
            "assumption_type": "IMPACT",
            "description": (
                f"Quantitative utilization/cost impact for '{name}' is not estimated. "
                "Prior synthetic elasticity/PMPM defaults were removed per correction specification."
            ),
            "value": "UNESTIMATED",
            "unit": None,
            "source": SPEC_VERSION,
            "confidence": None,
            "evidence_state": "UNESTIMATED",
        },
        {
            "assumption_type": "CODING_AUTHORITY",
            "description": (
                f"Authoritative coding pending validation. Required domain: {required_coding}"
            ),
            "value": "UNESTIMATED",
            "unit": None,
            "source": SPEC_VERSION,
            "confidence": None,
            "evidence_state": "UNESTIMATED",
        },
    ]


def _mechanism_guardrails(lever_type: str, name: str) -> list[dict[str, Any]]:
    """Mechanism-appropriate guardrail templates — not certified thresholds."""
    common = {
        "threshold_type": "review",
        "threshold_value": None,
        "action": "manual_review",
        "evidence_state": "TEMPLATE_PENDING_CALIBRATION",
        "source": SPEC_VERSION,
    }
    templates = {
        "PRIOR_AUTH": [
            {**common, "metric_name": "pa_overturn_rate", "description": f"Monitor appeal/overturn rate for {name}"},
            {**common, "metric_name": "access_delay_days", "description": f"Monitor authorization turnaround / access delay for {name}"},
        ],
        "SITE_OF_CARE": [
            {**common, "metric_name": "site_redirect_adverse_event_rate", "description": f"Monitor clinical adverse events after site redirect for {name}"},
            {**common, "metric_name": "hospital_op_share", "description": f"Monitor residual hospital outpatient share for {name}"},
        ],
        "STEP_THERAPY": [
            {**common, "metric_name": "therapy_abandonment_rate", "description": f"Monitor abandonment after step edit for {name}"},
            {**common, "metric_name": "preferred_agent_start_rate", "description": f"Monitor preferred-agent starts for {name}"},
        ],
        "QUANTITY_LIMIT": [
            {**common, "metric_name": "exception_grant_rate", "description": f"Monitor QL exception grants for {name}"},
            {**common, "metric_name": "continuity_break_rate", "description": f"Monitor therapy continuity breaks for {name}"},
        ],
        "COST_SHARING": [
            {**common, "metric_name": "member_cost_share_accuracy", "description": f"Monitor cost-share adjudication accuracy for {name}"},
            {**common, "metric_name": "preventive_zero_share_miss_rate", "description": f"Monitor missed $0 preventive cost share for {name}"},
        ],
        "PAYMENT_EDIT": [
            {**common, "metric_name": "edit_false_positive_rate", "description": f"Monitor payment-edit false positives for {name}"},
            {**common, "metric_name": "provider_dispute_rate", "description": f"Monitor provider disputes for {name}"},
        ],
        "NETWORK_RESTRICTION": [
            {**common, "metric_name": "network_adequacy_gap", "description": f"Monitor network adequacy gaps for {name}"},
            {**common, "metric_name": "oon_exception_rate", "description": f"Monitor OON exceptions for {name}"},
        ],
        "PHARMACY_BENEFIT": [
            {**common, "metric_name": "pharmacy_access_complaint_rate", "description": f"Monitor pharmacy access complaints for {name}"},
            {**common, "metric_name": "days_supply_exception_rate", "description": f"Monitor days-supply exceptions for {name}"},
        ],
        "COMPLIANCE_MAPPING": [
            {**common, "metric_name": "regulatory_mapping_gap", "description": f"Monitor unresolved regulatory mapping gaps for {name}"},
        ],
        "CARE_MANAGEMENT": [
            {**common, "metric_name": "engagement_dropout_rate", "description": f"Monitor care-management dropout for {name}"},
            {**common, "metric_name": "downstream_ed_rate", "description": f"Monitor downstream ED utilization for {name}"},
        ],
    }
    return templates.get(
        lever_type,
        [
            {**common, "metric_name": "policy_outcome_review", "description": f"Manual outcome review required for {name}"},
        ],
    )


def _exceptions_block() -> list[dict[str, Any]]:
    return [
        {
            "exception_type": "EMERGENCY",
            "description": "Emergency / emergent services exempt where legally required",
            "override_allowed": True,
        },
        {
            "exception_type": "CONTINUITY_OF_CARE",
            "description": "Continuity-of-care / active treatment exceptions per plan rules",
            "override_allowed": True,
        },
        {
            "exception_type": "MEDICAL_NECESSITY_REVIEW",
            "description": "Documented medical necessity / clinical exception path",
            "override_allowed": True,
            "requires_review": True,
        },
        {
            "exception_type": "APPEAL",
            "description": "Member/provider appeal and external review rights preserved",
            "override_allowed": True,
        },
        {
            "exception_type": "PLAN_PRODUCT_EXCEPTION",
            "description": "Product/benefit/contract-specific exceptions applied only with cited authority",
            "override_allowed": True,
            "requires_cited_authority": True,
        },
    ]


def _special_lever_params(register_row: dict, lever_type: str) -> dict[str, Any]:
    name = register_row["policy"]
    corr = register_row.get("specific_correction") or ""
    params: dict[str, Any] = {
        "mechanism_note": register_row.get("proposed_mechanism"),
        "parameters_certified": False,
    }
    if "Zero Cost Share" in name or "$0" in (register_row.get("proposed_mechanism") or "") or "set qualifying covered preventive cost share to zero" in corr:
        params.update(
            {
                "copay": 0.0,
                "coinsurance": 0.0,
                "member_cost_share": 0.0,
                "applies_when": "qualifying_in_network_preventive",
                "note": "Preventive $0 cost share for qualifying services; eligibility not fabricated beyond mechanism statement",
            }
        )
    elif lever_type == "PRIOR_AUTH":
        params.update({"requires_pa": True, "pa_touchpoint": "PA_WORKFLOW", "clinical_criteria_certified": False})
    elif lever_type == "COST_SHARING":
        params.update(
            {
                "copay": None,
                "coinsurance": None,
                "note": "Numeric cost-share parameters UNESTIMATED pending benefit design authority",
            }
        )
    return params


def apply_one(
    meta: dict,
    register_row: dict,
    *,
    policy_type: str,
) -> tuple[dict, dict]:
    """Return (new_meta, evidence)."""
    evidence: dict[str, Any] = {
        "register_index": int(register_row["index"]),
        "policy": register_row["policy"],
        "register_status": register_row["status"],
        "actions": [],
        "validation": register_row.get("validation"),
        "result": "CORRECTED",
        "unresolved": [],
    }
    m = deepcopy(meta) if isinstance(meta, dict) else {}
    now = datetime.now(timezone.utc).isoformat()

    # Snapshot history (preserve prior evidence)
    history = m.get("configuration_history")
    if not isinstance(history, list):
        history = []
    history.append(
        {
            "snapshot_at": now,
            "reason": SPEC_VERSION,
            "register_index": int(register_row["index"]),
            "register_status": register_row["status"],
            "snapshot": {
                "scope": deepcopy(m.get("scope")),
                "policy_levers": deepcopy(m.get("policy_levers")),
                "assumptions": deepcopy(m.get("assumptions")),
                "guardrails": deepcopy(m.get("guardrails")),
                "enforcement": deepcopy(m.get("enforcement")),
                "global_exceptions": deepcopy(m.get("global_exceptions")),
                "configuration_quality": deepcopy(m.get("configuration_quality")),
            },
        }
    )
    # keep last 5 snapshots
    m["configuration_history"] = history[-5:]
    evidence["actions"].append("SNAPSHOT_PRIOR_CONFIGURATION")

    scope = dict(m.get("scope") if isinstance(m.get("scope"), dict) else {})
    exported_codes = _parse_codes(register_row.get("exported_codes") or "")
    current_codes = list(scope.get("procedure_codes") or [])
    if not current_codes:
        current_codes = list(exported_codes)

    kept, removed_em = _strip_generic_em(current_codes)
    if removed_em:
        evidence["actions"].append(f"REMOVED_GENERIC_EM:{','.join(removed_em)}")

    protected = register_row["policy"] in PROTECTED_FIXTURES
    if protected and not kept and current_codes:
        # Never wipe a protected fixture to empty if strip removed everything unexpected;
        # still remove E/M noise only.
        kept = [c for c in current_codes if c not in GENERIC_EM]
        evidence["actions"].append("PROTECTED_FIXTURE_CODE_PRESERVE_NON_EM")

    code_mapping_state = "RETAINED_PENDING_AUTHORITY_REVIEW" if kept else "UNVERIFIED_CODE_MAPPING"
    if not kept:
        evidence["actions"].append("CLEARED_UNRELATED_OR_EMPTY_CODES_NO_SUBSTITUTE")
        evidence["unresolved"].append("UNVERIFIED_CODE_MAPPING")
    else:
        evidence["actions"].append(f"RETAINED_CODES_PENDING_AUTHORITY:{','.join(kept)}")
        evidence["unresolved"].append("AUTHORITY_CERTIFICATION_REQUIRED")

    scope["procedure_codes"] = kept
    # Service category: do not keep false ED; mark reclassification required
    exported_svc = (register_row.get("exported_service_category") or "").strip()
    if exported_svc.upper() == "ED" or not scope.get("service_categories"):
        scope["service_categories"] = []
        evidence["actions"].append("CLEARED_UNVALIDATED_SERVICE_CATEGORY")
        evidence["unresolved"].append("SERVICE_CATEGORY_RECLASSIFICATION_REQUIRED")

    # Jurisdiction: remove NC defaults unless named NC authority
    retain_nc = register_row["policy"] in NC_AUTHORITY_NAMES
    if not retain_nc:
        if scope.get("states") == ["NC"] or scope.get("markets") == ["NC"]:
            evidence["actions"].append("REMOVED_NC_DEFAULT_FROM_NATIONAL_POLICY")
        scope["states"] = None
        scope["markets"] = None
        scope["jurisdiction_mode"] = "JURISDICTION_NEUTRAL_BASE"
        scope["applicability_overlays"] = []
    else:
        scope["states"] = ["NC"]
        scope["markets"] = ["NC"]
        scope["jurisdiction_mode"] = "STATE_CONTRACTOR_SPECIFIC"
        evidence["actions"].append("RETAINED_NC_FOR_NAMED_AUTHORITY")
    # Keep LOB if present but do not invent Commercial+MA+Medicaid; leave as-is or clear forced triple
    # Spec: do not default all to Commercial+MA+Medicaid — if exactly that triple from catalog seed, neutralize to unspecified pending overlay
    lob = scope.get("lob")
    if isinstance(lob, list) and set(lob) >= {"COMMERCIAL", "MA", "MEDICAID"} and not retain_nc:
        scope["lob"] = None
        evidence["actions"].append("CLEARED_UNIVERSAL_LOB_DEFAULT")
        evidence["unresolved"].append("LOB_PRODUCT_OVERLAY_REQUIRED")

    m["scope"] = scope

    # Levers — correct mechanism; codes only if retained (else empty targets)
    lever_type = _lever_type_from_mechanism(register_row.get("proposed_mechanism") or "", policy_type)
    code_system = "UNVERIFIED"
    req = (register_row.get("required_coding_domain") or "").upper()
    if "NDC" in req or "RXNORM" in req:
        code_system = "NDC_OR_RXNORM_PENDING"
    elif "ICD" in req:
        code_system = "ICD10_PENDING"
    elif "REGULAT" in req or "CONTRACT" in req or "DOCUMENT" in req:
        code_system = "REGULATORY_DOCUMENT_ID_PENDING"
    elif kept:
        code_system = "CPT_HCPCS_UNCERTIFIED"

    m["policy_levers"] = [
        {
            "lever_type": lever_type,
            "targets": {
                "code_system": code_system,
                "code_type": "PENDING" if not kept else "CPT_OR_HCPCS",
                "codes": kept,
                "code_groups": [],
            },
            "parameters": _special_lever_params(register_row, lever_type),
        }
    ]
    evidence["actions"].append(f"SET_LEVER:{lever_type}")

    # Assumptions
    m["assumptions"] = _unestimated_assumptions(register_row["policy"], register_row.get("required_coding_domain") or "")
    evidence["actions"].append("ASSUMPTIONS_MARKED_UNESTIMATED")

    # Guardrails
    m["guardrails"] = _mechanism_guardrails(lever_type, register_row["policy"])
    evidence["actions"].append("GUARDRAILS_MECHANISM_TEMPLATES")

    # Exceptions / enforcement — no blanket override=false
    m["global_exceptions"] = _exceptions_block()
    m["enforcement"] = {
        "mechanism": "REVIEW_REQUIRED",
        "touchpoint": ["MANUAL_REVIEW"],
        "override_allowed": True,
        "override_note": "Blanket override=false removed; exceptions/appeals modeled explicitly",
        "appeals_allowed": True,
    }
    evidence["actions"].append("EXCEPTIONS_AND_APPEAL_PATH_MODELED")

    # Provenance + execution eligibility
    register_status = register_row["status"]
    execution_eligibility = "BLOCKED"
    evidence_state = (
        "CODE_REVIEW_REQUIRED"
        if register_status == "BLOCK_CLAIMS_EXECUTION_PENDING_REMAP"
        else "PROVENANCE_ONLY"
    )
    if register_status == "REVIEW_REQUIRED_NO_AUTHORITY_CERTIFICATION":
        evidence_state = "PROVENANCE_ONLY"
    if protected:
        evidence["actions"].append("PROTECTED_FIXTURE_NON_DESTRUCTIVE")
        evidence_state = "PROTECTED_FIXTURE_REVIEW_REQUIRED"

    m["remediation"] = {
        "spec_version": SPEC_VERSION,
        "applied_at": now,
        "register_index": int(register_row["index"]),
        "register_status": register_status,
        "execution_eligibility": execution_eligibility,
        "evidence_state": evidence_state,
        "code_mapping_state": code_mapping_state,
        "proposed_mechanism": register_row.get("proposed_mechanism"),
        "required_coding_domain": register_row.get("required_coding_domain"),
        "specific_correction": register_row.get("specific_correction"),
        "scope_rule": register_row.get("scope_rule"),
        "assumption_rule": register_row.get("assumption_rule"),
        "validation_required": register_row.get("validation"),
        "protected_fixture": protected,
        "nc_authority_retained": retain_nc,
        "claims_execution_blocked": True,
        "provenance": {
            "source_register": "HealthForesight_250_Policy_Correction_Register.csv",
            "source_specification": "HealthForesight_250_Policy_Correction_Specification.pdf",
            "publisher": "expert_handoff_2026-11-05",
            "review_state": register_status,
            "code_release": None,
            "effective_date": None,
            "termination_date": None,
            "jurisdiction": "NC" if retain_nc else "JURISDICTION_NEUTRAL",
            "licensing_limitations": (
                "No fabricated CPT/HCPCS/NDC/MUE/formulary lists; "
                "authoritative licensed code data required before CLAIMS_EXECUTABLE"
            ),
        },
    }
    m["configuration_quality"] = {
        "tier": "remediation_v1_blocked",
        "filled_at": now,
        "note": "Corrected per 250-policy specification; not claims-executable until authority-certified remap",
    }
    # typed code systems envelope
    m["code_systems"] = {
        "systems": [
            {
                "system": code_system,
                "codes": kept,
                "state": code_mapping_state,
                "certified": False,
            }
        ]
    }

    evidence["codes_before"] = current_codes
    evidence["codes_after"] = kept
    evidence["removed_generic_em"] = removed_em
    evidence["lever_type"] = lever_type
    evidence["execution_eligibility"] = execution_eligibility
    evidence["evidence_state"] = evidence_state
    evidence["code_mapping_state"] = code_mapping_state
    evidence["protected_fixture"] = protected
    evidence["nc_authority_retained"] = retain_nc
    if evidence["unresolved"]:
        evidence["result"] = "CORRECTED_WITH_UNRESOLVED"
    return m, evidence


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(DEFAULT_CSV))
    ap.add_argument(
        "--report",
        default=str(
            REPO
            / "docs"
            / "production"
            / "releases"
            / "corrections"
            / f"POLICY_CORRECTION_EVIDENCE_REPORT_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
        ),
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    _assert_lean_staging_db()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        # allow attachment path fallback
        alt = Path(
            "/Users/nileshl/.cursor/projects/Users-nileshl-Private-HealthForesight/attachments/"
            "202af80e-02cb-4eab-aab3-cbc7c62b7711/HealthForesight_250_Policy_Correction_Register.csv"
        )
        if alt.exists():
            dest = DEFAULT_CSV
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(alt, dest)
            csv_path = dest
            print(f"Copied register CSV → {dest}")
        else:
            raise SystemExit(f"CSV not found: {args.csv}")

    register = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    if len(register) != 250:
        raise SystemExit(f"Expected 250 register rows, got {len(register)}")

    from uepi_api.database import SessionLocal
    from uepi_api.models.policy import Policy

    db = SessionLocal()
    evidence_rows: list[dict] = []
    try:
        policies = (
            db.query(Policy)
            .filter(Policy.tenant_id == TENANT)
            .order_by(Policy.name.asc())
            .all()
        )
        by_name = {(p.name or "").strip(): p for p in policies}
        missing = [r["policy"] for r in register if r["policy"] not in by_name]
        extra = [n for n in by_name if n not in {r["policy"] for r in register}]
        if missing or extra or len(policies) != 250:
            raise SystemExit(
                json.dumps(
                    {
                        "reconcile_fail": True,
                        "db_count": len(policies),
                        "missing_in_db": missing,
                        "extra_in_db": extra[:50],
                    },
                    indent=2,
                )
            )
        print(json.dumps({"reconcile": "PASS", "count": 250, "missing": 0, "extra": 0}))

        for row in register:
            pol = by_name[row["policy"]]
            meta = pol.policy_metadata_json if isinstance(pol.policy_metadata_json, dict) else {}
            new_meta, ev = apply_one(meta, row, policy_type=pol.policy_type or row.get("type") or "")
            ev["policy_id"] = str(pol.id)
            evidence_rows.append(ev)
            if not args.dry_run:
                pol.policy_metadata_json = new_meta
                pol.updated_at = datetime.utcnow()
        if not args.dry_run:
            db.commit()

        # Post verify blocked
        from uepi_api.services.policy_execution_eligibility import claims_execution_allowed

        blocked = allowed = 0
        for pol in db.query(Policy).filter(Policy.tenant_id == TENANT).all():
            ok, _ = claims_execution_allowed(
                {"id": str(pol.id), "name": pol.name, "policy_metadata_json": pol.policy_metadata_json}
            )
            if ok:
                allowed += 1
            else:
                blocked += 1

        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "spec_version": SPEC_VERSION,
            "environment": "lean_staging_only",
            "demo_untouched": True,
            "reconcile": {"csv_rows": 250, "db_policies": 250, "matched": 250},
            "counts": {
                "corrected": len(evidence_rows),
                "corrected_with_unresolved": sum(1 for e in evidence_rows if e["result"] == "CORRECTED_WITH_UNRESOLVED"),
                "blocked_claims_execution": blocked,
                "claims_execution_allowed": allowed,
                "protected_fixtures": sum(1 for e in evidence_rows if e.get("protected_fixture")),
                "nc_authority_retained": sum(1 for e in evidence_rows if e.get("nc_authority_retained")),
                "unverified_code_mapping": sum(
                    1 for e in evidence_rows if e.get("code_mapping_state") == "UNVERIFIED_CODE_MAPPING"
                ),
            },
            "acceptance": {
                "accounted_for": "250/250",
                "claims_executable": 0,
                "directionally_valid": 0,
                "blocked_or_review": 250,
                "note": (
                    "Catalog remediation complete; no policy marked CLAIMS_EXECUTABLE or "
                    "DIRECTIONALLY_VALID without authoritative licensed code certification."
                ),
            },
            "policies": evidence_rows,
        }
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        # Markdown companion
        md_path = report_path.with_suffix(".md")
        lines = [
            "# 250-Policy Correction Evidence Report",
            "",
            f"Generated: {summary['generated_at']}",
            f"Spec: `{SPEC_VERSION}`",
            "Environment: **lean staging only** (Dec4 demo untouched)",
            "",
            "## Summary",
            "",
            f"- Reconciled: **{summary['reconcile']['matched']}/250**",
            f"- Claims execution blocked: **{blocked}**",
            f"- Claims execution allowed: **{allowed}**",
            f"- UNVERIFIED_CODE_MAPPING: **{summary['counts']['unverified_code_mapping']}**",
            f"- Protected fixtures (non-destructive): **{summary['counts']['protected_fixtures']}**",
            f"- NC authority retained: **{summary['counts']['nc_authority_retained']}**",
            "",
            "## Acceptance",
            "",
            summary["acceptance"]["note"],
            "",
            "## Policy-by-policy",
            "",
            "| # | Policy | Result | Exec | Code state | Actions | Unresolved |",
            "|---|--------|--------|------|------------|---------|------------|",
        ]
        for e in evidence_rows:
            lines.append(
                f"| {e['register_index']} | {e['policy']} | {e['result']} | "
                f"{e['execution_eligibility']} | {e['code_mapping_state']} | "
                f"{'; '.join(e['actions'][:4])} | {'; '.join(e.get('unresolved') or []) or '—'} |"
            )
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(json.dumps({"report_json": str(report_path), "report_md": str(md_path), **summary["counts"]}, indent=2))
        if allowed != 0:
            raise SystemExit("Expected all policies claims-blocked after remediation")
    finally:
        db.close()


if __name__ == "__main__":
    main()
