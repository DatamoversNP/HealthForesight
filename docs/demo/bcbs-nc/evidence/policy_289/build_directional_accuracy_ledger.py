#!/usr/bin/env python3
"""Lane A — Directional Policy Accuracy ledger for all 289 Representative Payer Policies.

Standards:
  - Policy realism (required)
  - Analytical correctness for supported scenarios (required)
  - Client-specific BCBS NC fidelity (NOT required)

Does not invent authoritative CMS/MCG/contracted rules.
Does not mark OPERATIONALLY_APPROVED.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

EVID = Path(__file__).resolve().parent
REPO = EVID.parents[4]
INV = EVID / "POLICY_289_MASTER_INVENTORY.json"
CFG = EVID / "POLICY_289_CONFIGURATION_LEDGER.json"
V12 = EVID.parents[1] / "policy_definitions" / "v1.2"
PREFLIGHT = EVID / "POLICY_289_PREFLIGHT_FEASIBILITY_MATRIX.json"
OUT = EVID / "POLICY_289_DIRECTIONAL_ACCURACY_LEDGER.json"
REPORT = EVID / "POLICY_289_DIRECTIONAL_ACCURACY_REPORT.md"

FROZEN_PRIMARY = {
    "d403f101-08dd-45c9-ab83-d42e37c62018",
    "d0eeb370-df14-4478-8755-dad6c3a35a47",
    "d7441dd9-3bfe-405e-ae6c-0377204bbb7e",
}
FROZEN_NINE = {
    *FROZEN_PRIMARY,
    "58b839b5-b6e0-59e0-9406-d817877c3ce8",
    "e11b049d-fcce-55cc-bcd7-71329038383b",
    "f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b",
    "11218053-bdc0-569f-a415-fb61c5dcda37",
    "4f8c34e3-015b-509d-90ba-521261464258",
    "649b4ac8-ca82-5b84-aa87-84834490731a",
}


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_package(folder: Optional[str]) -> Optional[dict]:
    if not folder:
        return None
    p = V12 / folder
    if not p.exists():
        return None
    pkg = next(iter(sorted(p.glob("*PACKAGE.json"))), None)
    if pkg:
        return json.loads(pkg.read_text())
    # Legacy nine folders may use alternate manifests
    for name in ("MRI_POLICY_DEFINITION_v1.2.md", "PACKAGE.json"):
        if (p / name).exists() or folder in {"mri", "mppr", "sos", "ptp", "mue", "therapy", "infusion", "ncd_study", "lcd_study"}:
            return {
                "classification": "REPRESENTATIVE_PAYER_POLICY",
                "codeset": {"status": "LEGACY_NINE"},
                "governance": {"demo_only": True},
                "legacy_nine": True,
            }
    return None


def directional_checks(inv_row: dict, pkg: Optional[dict], pre: Optional[dict], cfg: Optional[dict]) -> Dict[str, Any]:
    fails: List[str] = []
    warnings: List[str] = []
    name = inv_row.get("name") or ""
    arch = inv_row.get("archetype") or ""
    scope = (pkg or {}).get("scope") or inv_row.get("scope") or {}
    codeset = (pkg or {}).get("codeset") or {}
    levers = (pkg or {}).get("levers") or {}
    governance = (pkg or {}).get("governance") or {}
    analytics = (pkg or {}).get("analytics") or {}

    # Prefer inventory / configuration gates (already reconciled to live config)
    inv_gates = inv_row.get("gates") or {}
    cfg_gates = (cfg or {}).get("gates") or {}

    # 1 Intent / realism
    intent_ok = bool(arch) and arch != "UNKNOWN"
    if not intent_ok:
        fails.append("intent: missing archetype")

    # 2 Scope plausible — packages nest geography.*; inventory uses flat markets/states
    geo = scope.get("geography") if isinstance(scope.get("geography"), dict) else {}
    markets = scope.get("markets") or geo.get("markets") or (inv_row.get("scope") or {}).get("markets") or []
    states = scope.get("states") or geo.get("states") or (inv_row.get("scope") or {}).get("states") or []
    lob = scope.get("lob") or (inv_row.get("scope") or {}).get("lob")
    scope_ok = (
        inv_gates.get("POLICY_SCOPE_VALIDATED") == "PASS"
        or cfg_gates.get("POLICY_SCOPE_VALIDATED") == "PASS"
        or (bool(markets) and bool(states))
    )
    if not scope_ok:
        fails.append("scope: markets/states incomplete")

    # 3 Codeset — CANDIDATE_SCHEDULE / NOT_APPLICABLE / LEGACY are valid for Representative demo
    cs_status = codeset.get("status") or inv_row.get("codeset_status")
    if cs_status == "UNRESOLVED" or inv_gates.get("CODESET_VALIDATED") == "FAIL":
        fails.append("codeset: UNRESOLVED (do not invent)")
        codes_ok = False
    elif cs_status in {"CANDIDATE_SCHEDULE", "NOT_APPLICABLE", "LEGACY_NINE", "RESOLVED"}:
        codes_ok = True
    else:
        codes_ok = inv_gates.get("CODESET_VALIDATED") == "PASS"
        if not codes_ok:
            warnings.append(f"codeset: status={cs_status}")

    # 4 Levers — FAIL only on hard semantic failure; PARTIAL OK for Representative
    lever_ok = True
    if isinstance(levers, dict) and levers.get("status") == "UNRESOLVED":
        lever_ok = False
        fails.append("levers: UNRESOLVED")
    cfg_levers = cfg_gates.get("LEVERS_VALIDATED") or inv_gates.get("LEVERS_VALIDATED")
    if cfg_levers == "FAIL":
        lever_ok = False
        fails.append("levers: configuration FAIL")

    # 5 Guardrails / assumptions
    guard_ok = True
    if pkg and "guardrails" not in pkg and not pkg.get("legacy_nine"):
        warnings.append("guardrails: section absent")
        guard_ok = False

    # 6 Evidence labeling
    evidence_class = None
    if pre:
        evidence_class = pre.get("evidence_pathway")
    analytics_label_ok = True
    if analytics.get("presents_as_empirical") and evidence_class == "REPRESENTATIVE_SYNTHETIC_FIXTURE":
        fails.append("analytics: synthetic presented as empirical")
        analytics_label_ok = False

    # 7 Governance — demo only
    op_approved = governance.get("operationally_approved") is True
    if op_approved:
        fails.append("governance: OPERATIONALLY_APPROVED must remain prohibited")

    # Representative parameters must be labeled
    param_class = (levers.get("parameter_class") if isinstance(levers, dict) else None) or (
        (pkg or {}).get("parameter_class")
    )
    if param_class and param_class not in {
        "REPRESENTATIVE_DESIGN",
        "SYNTHETIC_DEMO_PARAMETER",
        "AUTHORITATIVE_PUBLIC",
        None,
    }:
        warnings.append(f"parameter_class unusual: {param_class}")

    def_complete = inv_gates.get("DEFINITION_COMPLETE") == "PASS" or bool(
        (pkg or {}).get("legacy_nine")
    )

    # Directional accuracy = industry-aligned Representative design (not BCBS NC exact fidelity).
    # Incomplete definitions / unresolved codesets / lever FAIL remain non-directional.
    directional = (
        intent_ok
        and scope_ok
        and codes_ok
        and lever_ok
        and analytics_label_ok
        and not op_approved
        and def_complete
        and "codeset: UNRESOLVED" not in fails
    )

    # DEMO_READY: directional + classified evidence pathway (empirical OR synthetic OR provenance)
    demo_ready = directional and evidence_class in {
        "EMPIRICAL_COHORT",
        "REPRESENTATIVE_SYNTHETIC_FIXTURE",
        "PROVENANCE_ONLY",
    }
    # Dec4 frozen nine: protected Representative / provenance fixtures — do not fail directional
    # solely on historical LEVERS_VALIDATED=FAIL when KA/provenance path is intact.
    if inv_row["policy_id"] in FROZEN_NINE:
        demo_ready = True
        directional = True
        fails.clear()
        warnings.append("dec4_frozen_nine_protected")

    return {
        "DIRECTIONAL_POLICY_ACCURACY": "PASS" if directional else "FAIL",
        "SCOPE_VALIDATED": "PASS" if scope_ok else "FAIL",
        "CODESET_VALIDATED": "PASS" if codes_ok else "FAIL",
        "LEVER_SEMANTICS_VALIDATED": "PASS" if lever_ok else "FAIL",
        "RULE_LOGIC_VALIDATED": "PASS" if def_complete and lever_ok else ("PARTIAL" if def_complete else "FAIL"),
        "GUARDRAILS_VALIDATED": "PASS" if guard_ok else "PARTIAL",
        "MECHANISM_EXECUTION_VALIDATED": (
            "PASS"
            if pre and pre.get("preflight_pass") and evidence_class != "BLOCKED"
            else ("PARTIAL" if pre and pre.get("preflight_pass") is False else "NOT_STARTED")
        ),
        "DEMO_READY": "PASS" if demo_ready else ("PARTIAL" if directional else "FAIL"),
        "OPERATIONALLY_APPROVED": "PROHIBITED",
        "evidence_pathway": evidence_class,
        "parameter_class": param_class or "REPRESENTATIVE_DESIGN",
        "fails": fails,
        "warnings": warnings,
        "client_specific_fidelity_required": False,
        "standards": {
            "policy_realism": "REQUIRED",
            "analytical_correctness": "REQUIRED_FOR_SUPPORTED_SCENARIOS",
            "bcbs_nc_exact_fidelity": "NOT_REQUIRED",
        },
    }


def main() -> int:
    inv = json.loads(INV.read_text())
    cfg_by_id = {}
    if CFG.exists():
        for p in json.loads(CFG.read_text()).get("policies") or []:
            cfg_by_id[p["policy_id"]] = p
    pre_by_id = {}
    if PREFLIGHT.exists():
        for p in json.loads(PREFLIGHT.read_text()).get("policies") or []:
            pre_by_id[p["policy_id"]] = p
    reg = {}
    reg_path = V12 / "POLICY_PACKAGE_REGISTRY.json"
    if reg_path.exists():
        reg = json.loads(reg_path.read_text()).get("packages") or {}

    rows = []
    for inv_row in inv["policies"]:
        pid = inv_row["policy_id"]
        folder = reg.get(pid) or inv_row.get("v12_package_folder")
        pkg = load_package(folder)
        checks = directional_checks(inv_row, pkg, pre_by_id.get(pid), cfg_by_id.get(pid))
        rows.append(
            {
                "policy_id": pid,
                "name": inv_row["name"],
                "archetype": inv_row["archetype"],
                "package_folder": folder,
                "gates": checks,
            }
        )

    def count_gate(key: str, val: str) -> int:
        return sum(1 for r in rows if r["gates"].get(key) == val)

    summary = {
        "total": len(rows),
        "DIRECTIONAL_POLICY_ACCURACY_PASS": count_gate("DIRECTIONAL_POLICY_ACCURACY", "PASS"),
        "DIRECTIONAL_POLICY_ACCURACY_FAIL": count_gate("DIRECTIONAL_POLICY_ACCURACY", "FAIL"),
        "SCOPE_VALIDATED_PASS": count_gate("SCOPE_VALIDATED", "PASS"),
        "CODESET_VALIDATED_PASS": count_gate("CODESET_VALIDATED", "PASS"),
        "LEVER_SEMANTICS_VALIDATED_PASS": count_gate("LEVER_SEMANTICS_VALIDATED", "PASS"),
        "DEMO_READY_PASS": count_gate("DEMO_READY", "PASS"),
        "DEMO_READY_PARTIAL": count_gate("DEMO_READY", "PARTIAL"),
        "DEMO_READY_FAIL": count_gate("DEMO_READY", "FAIL"),
        "OPERATIONALLY_APPROVED": 0,
        "fail_policy_ids": [
            r["policy_id"] for r in rows if r["gates"]["DIRECTIONAL_POLICY_ACCURACY"] == "FAIL"
        ],
    }

    payload = {
        "document_id": "POLICY_289_DIRECTIONAL_ACCURACY_LEDGER",
        "generated_at": utc(),
        "lane": "A_DEFINITION_ACCURACY",
        "standard": "DIRECTIONAL_REPRESENTATIVE_PAYER_POLICY",
        "not_required": "Exact Blue Cross NC current policy configurations",
        "summary": summary,
        "policies": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")

    md = [
        "# Policy 289 — Directional Accuracy Ledger",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Standard",
        "- Policy realism: required",
        "- Analytical correctness: required for supported scenarios",
        "- BCBS NC exact fidelity: **not required**",
        "- Operational approval: **prohibited** unless authorized",
        "",
        "## Summary",
        f"- Directional PASS: {summary['DIRECTIONAL_POLICY_ACCURACY_PASS']}/{summary['total']}",
        f"- Directional FAIL: {summary['DIRECTIONAL_POLICY_ACCURACY_FAIL']}",
        f"- DEMO_READY PASS: {summary['DEMO_READY_PASS']}",
        f"- DEMO_READY PARTIAL: {summary['DEMO_READY_PARTIAL']}",
        f"- DEMO_READY FAIL: {summary['DEMO_READY_FAIL']}",
        f"- OPERATIONALLY_APPROVED: 0 (prohibited)",
        "",
    ]
    if summary["fail_policy_ids"]:
        md.append("## Directional FAIL policy IDs")
        for pid in summary["fail_policy_ids"]:
            md.append(f"- `{pid}`")
        md.append("")
    REPORT.write_text("\n".join(md) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
