#!/usr/bin/env python3
"""Generate mechanism-specific definition packages + optionally persist levers.

Accuracy rules:
- Uses representative_codeset_library (REPRESENTATIVE_DESIGN) or UNRESOLVED/NOT_APPLICABLE.
- Never claims proprietary Blue Cross NC operative status.
- Never clears OPERATIONALLY_APPROVED.
- Skips Dec4 nine frozen folders (mri/mppr/sos/ptp/mue/therapy/infusion/ncd_study/lcd_study).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from accuracy_validators import validate_package_required_sections, validate_scope_lever_alignment
from representative_codeset_library import lookup

API = "http://127.0.0.1:7867/api/v1"
EMAIL = "admin@healthforesight.com"
PASSWORD = "Swan@1234"

EVID = Path(__file__).resolve().parent
REPO = EVID.parents[4]
V12 = REPO / "docs" / "demo" / "bcbs-nc" / "policy_definitions" / "v1.2"
CATALOG = V12 / "catalog"
REGISTRY = V12 / "POLICY_PACKAGE_REGISTRY.json"
INV = EVID / "POLICY_289_MASTER_INVENTORY.json"
CFG_LEDGER = EVID / "POLICY_289_CONFIGURATION_LEDGER.json"

FROZEN_NINE = {
    "d403f101-08dd-45c9-ab83-d42e37c62018",
    "d0eeb370-df14-4478-8755-dad6c3a35a47",
    "d7441dd9-3bfe-405e-ae6c-0377204bbb7e",
    "58b839b5-b6e0-59e0-9406-d817877c3ce8",
    "e11b049d-fcce-55cc-bcd7-71329038383b",
    "f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b",
    "11218053-bdc0-569f-a415-fb61c5dcda37",
    "4f8c34e3-015b-509d-90ba-521261464258",
    "649b4ac8-ca82-5b84-aa87-84834490731a",
}

NINE_FOLDERS = {
    "d403f101-08dd-45c9-ab83-d42e37c62018": "mri",
    "d0eeb370-df14-4478-8755-dad6c3a35a47": "mppr",
    "d7441dd9-3bfe-405e-ae6c-0377204bbb7e": "sos",
    "58b839b5-b6e0-59e0-9406-d817877c3ce8": "ptp",
    "e11b049d-fcce-55cc-bcd7-71329038383b": "mue",
    "f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b": "therapy",
    "11218053-bdc0-569f-a415-fb61c5dcda37": "infusion",
    "4f8c34e3-015b-509d-90ba-521261464258": "ncd_study",
    "649b4ac8-ca82-5b84-aa87-84834490731a": "lcd_study",
}


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip()).strip("_").lower()
    return s[:80] or "policy"


def login() -> str:
    req = urllib.request.Request(
        f"{API}/auth/login",
        data=json.dumps({"email": EMAIL, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["access_token"]


def api_get(tok: str, path: str) -> Any:
    req = urllib.request.Request(f"{API}{path}", headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def api_put(tok: str, path: str, body: dict) -> Any:
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def load_registry() -> Dict[str, Any]:
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text())
    return {
        "document_id": "POLICY_PACKAGE_REGISTRY",
        "classification": "REPRESENTATIVE_PAYER_POLICY",
        "not_claiming": "Authoritative Blue Cross NC operative proprietary policy text",
        "packages": {**{pid: folder for pid, folder in NINE_FOLDERS.items()}},
    }


def save_registry(reg: Dict[str, Any]) -> None:
    REGISTRY.write_text(json.dumps(reg, indent=2) + "\n")


def build_package(row: Dict[str, Any], live: Optional[dict]) -> Dict[str, Any]:
    name = row["name"]
    pid = row["policy_id"]
    arch = row["archetype"]
    sched = lookup(name)
    scope = (live or {}).get("scope") or row.get("scope") or {}
    codes = list(sched["codes"])

    codeset_status = (
        "NOT_APPLICABLE"
        if sched["not_applicable"]
        else ("UNRESOLVED" if sched["unresolved"] else "CANDIDATE_SCHEDULE")
    )

    levers: List[Dict[str, Any]] = []
    if codeset_status == "CANDIDATE_SCHEDULE":
        levers.append(
            {
                "lever_type": row.get("policy_type") or "PRIOR_AUTH",
                "parameters": {
                    "codes": codes,
                    "requires_pa": arch in {"PRIOR_AUTH_UM", "THERAPY_REHAB", "SITE_OF_CARE"},
                    "evidence_class": "REPRESENTATIVE_DESIGN",
                },
                "units": None,
                "direction": "utilization_control",
                "evidence_class": "REPRESENTATIVE_DESIGN",
            }
        )
    elif codeset_status == "NOT_APPLICABLE":
        levers.append(
            {
                "lever_type": row.get("policy_type") or "ADMINISTRATIVE",
                "parameters": {
                    "codes": [],
                    "applicability": "NON_CODE",
                    "not_applicable_reason": sched.get("not_applicable_reason"),
                },
                "evidence_class": "NOT_APPLICABLE",
            }
        )
    else:
        levers.append(
            {
                "lever_type": row.get("policy_type") or "PRIOR_AUTH",
                "parameters": {
                    "codes": [],
                    "status": "UNRESOLVED",
                    "reason": sched.get("notes"),
                },
                "evidence_class": "UNRESOLVED",
            }
        )

    pkg = {
        "document_id": f"HF-RP-{slugify(name).upper()}-PACKAGE",
        "policy_id": pid,
        "policy_name": name,
        "archetype": arch,
        "package_version": "v1.2.0-representative-batch",
        "classification": "REPRESENTATIVE_PAYER_POLICY",
        "not_claiming": "Authoritative Blue Cross NC operative proprietary policy text",
        "generated_at": utc(),
        "identity": {
            "objective": f"Representative Payer configuration for catalog policy «{name}»",
            "mechanism": arch,
            "family": row.get("policy_type"),
            "owner_role": "DEFINITION_REVIEW",
        },
        "scope": {
            "lob": scope.get("lob") or ["COMMERCIAL"],
            "geography": {
                "states": scope.get("states") or ["NC"],
                "markets": scope.get("markets") or ["NC"],
                "market_claim_note": (
                    "Claim markets are for cohort matching in synthetic claims; "
                    "states define Representative NC jurisdiction. NC geography ≠ complete configuration."
                ),
            },
            "setting": ["OUTPATIENT"] if arch not in {"ADMINISTRATIVE", "PROVIDER_NETWORK"} else ["NOT_APPLICABLE"],
            "effective": {
                "start": ((row.get("effective_period") or {}).get("start_date")),
                "end": ((row.get("effective_period") or {}).get("end_date")),
            },
        },
        "applicability": {
            "inclusions": [
                f"Services matching candidate {sched['code_system']} schedule"
                if codes
                else "Mechanism-defined population / benefit applicability (see rules)"
            ],
            "exclusions": [
                "Emergency services where PA is prohibited by No Surprises / emergency rules",
                "Services outside candidate schedule",
                "Proprietary BCBS NC criteria not present in this Representative package",
            ],
        },
        "codeset": {
            "status": codeset_status,
            "not_applicable_reason": sched.get("not_applicable_reason"),
            "code_system": sched["code_system"],
            "notes": sched.get("notes"),
            "codes": [
                {
                    "code_system": sched["code_system"],
                    "code": c,
                    "description": "",
                    "inclusion_status": "CANDIDATE_INCLUDE",
                    "evidence_class": "REPRESENTATIVE_DESIGN",
                }
                for c in codes
            ],
        },
        "levers": levers,
        "rules": [
            {
                "id": "R1_APPLICABILITY",
                "text": (
                    "If request code ∈ candidate schedule and setting/LOB in scope → PA or mechanism review required"
                    if codeset_status == "CANDIDATE_SCHEDULE"
                    else "Rules pending resolved schedule or non-code applicability design"
                ),
                "evidence_class": "REPRESENTATIVE_DESIGN" if codes else "UNRESOLVED",
            },
            {
                "id": "R2_NO_AUTO_DENY",
                "text": "Do not auto-deny without clinical review pathway when PA applies",
                "evidence_class": "REPRESENTATIVE_DESIGN",
            },
        ],
        "exceptions": [
            {
                "id": "E1_EMERGENCY",
                "text": "Emergency / urgent exceptions per applicable federal/state emergency access rules",
                "evidence_class": "REPRESENTATIVE_DESIGN",
            }
        ],
        "precedence": [
            "Emergency exception > elective PA requirement",
            "Product benefit exclusions > utilization management",
            "Effective-dated schedule version > prior schedule",
        ],
        "assumptions": [
            {
                "id": "A1",
                "text": "Synthetic claims substrate used for demo analytics unless labeled empirical",
                "evidence_class": "SYNTHETIC_FIXTURE",
            },
            {
                "id": "A2",
                "text": "Candidate codes are industry-aligned Representative design, not verified payer operative schedule",
                "evidence_class": "REPRESENTATIVE_DESIGN",
            },
        ],
        "guardrails": [
            {"id": "G_ACCESS", "family": "access", "text": "Monitor inappropriate access barriers"},
            {"id": "G_FIN", "family": "financial", "text": "Do not present representative parameters as contracted rates"},
            {"id": "G_CLIN", "family": "clinical", "text": "Clinical thresholds remain unsigned until product approval"},
        ],
        "sources": [
            {
                "id": "S_CPT_PUBLIC",
                "citation": "Public CPT/HCPCS nomenclature for code identity",
                "applicability": "code_identity_only",
                "evidence_class": "VERIFIED_SOURCE" if codes else "UNRESOLVED",
                "does_not_establish": "Payer-specific coverage criteria or contracted rates",
            }
        ],
        "analytics": {
            "strategy": arch,
            "supported_stages": (
                ["definition", "applicability", "baseline", "predicted_impact", "observation", "causal_feasibility"]
                if codeset_status == "CANDIDATE_SCHEDULE"
                else ["definition", "applicability", "insufficiency_disclosure"]
            ),
            "insufficiency_stages": (
                []
                if codeset_status == "CANDIDATE_SCHEDULE"
                else ["baseline_numerical", "predicted_impact_numerical", "causal_estimate"]
            ),
        },
        "governance": {
            "definition_status": (
                "DEFINITION_COMPLETE_CANDIDATE"
                if codeset_status in {"CANDIDATE_SCHEDULE", "NOT_APPLICABLE"}
                else "DEFINITION_INCOMPLETE_UNRESOLVED_CODESET"
            ),
            "operational_activation": "PROHIBITED",
        },
        "acceptance_tests": [
            {
                "id": "T_SCOPE_PRESENT",
                "given": "package loaded",
                "expect": "states and markets non-empty",
            },
            {
                "id": "T_LEVER_IN_SCOPE",
                "given": "candidate codes present",
                "expect": "every lever code listed in codeset.codes",
            },
            {
                "id": "T_NO_BCBS_CLAIM",
                "given": "classification",
                "expect": "REPRESENTATIVE_PAYER_POLICY and not_claiming set",
            },
        ],
        "release_blockers": [
            {
                "id": "CLINICAL_PRODUCT_UNSIGNED",
                "severity": "RELEASE_BLOCKER",
                "blocks_operational_activation": True,
                "text": "Clinical/product schedule not signed for operative use",
            },
            {
                "id": "NOT_PROPRIETARY_BCBS_NC",
                "severity": "RELEASE_BLOCKER",
                "blocks_operational_activation": True,
                "text": "Package is Representative Payer design — not proprietary BCBS NC operative policy",
            },
        ]
        + (
            [
                {
                    "id": "CODESET_UNRESOLVED",
                    "severity": "RELEASE_BLOCKER",
                    "blocks_operational_activation": True,
                    "text": sched.get("notes") or "Required code schedule unresolved",
                }
            ]
            if codeset_status == "UNRESOLVED"
            else []
        ),
    }

    ok, missing = validate_package_required_sections(pkg)
    pkg["_validation"] = {"schema_sections_ok": ok, "missing": missing}
    fails = validate_scope_lever_alignment(
        {
            "name": name,
            "policy_type": row.get("policy_type"),
            "scope": {
                "markets": pkg["scope"]["geography"]["markets"],
                "states": pkg["scope"]["geography"]["states"],
            },
            "policy_levers": levers,
        },
        codes,
    )
    pkg["_validation"]["accuracy_failures"] = fails
    return pkg


def write_package_files(folder: Path, pkg: Dict[str, Any]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    prefix = slugify(pkg["policy_name"]).upper()
    (folder / f"{prefix}_PACKAGE.json").write_text(json.dumps(pkg, indent=2) + "\n")
    (folder / f"{prefix}_CODESET_AND_APPLICABILITY.json").write_text(
        json.dumps(
            {
                "document_id": f"{prefix}_CODESET",
                "policy_id": pkg["policy_id"],
                "package_version": pkg["package_version"],
                "intended_scope": pkg["identity"]["objective"],
                "status": pkg["codeset"]["status"],
                "candidate_codes": pkg["codeset"]["codes"],
                "notes": pkg["codeset"].get("notes"),
                "classification": pkg["classification"],
            },
            indent=2,
        )
        + "\n"
    )
    (folder / f"{prefix}_RELEASE_BLOCKERS.json").write_text(
        json.dumps(
            {
                "document_id": f"{prefix}_RELEASE_BLOCKERS",
                "package_version": pkg["package_version"],
                "blocks_operational_activation": True,
                "blocker_count": len(pkg["release_blockers"]),
                "blockers": pkg["release_blockers"],
            },
            indent=2,
        )
        + "\n"
    )
    (folder / f"{prefix}_POLICY_ACCEPTANCE_TESTS.json").write_text(
        json.dumps({"tests": pkg["acceptance_tests"]}, indent=2) + "\n"
    )
    (folder / f"{prefix}_DECISION_TABLES.json").write_text(
        json.dumps({"rules": pkg["rules"], "exceptions": pkg["exceptions"]}, indent=2) + "\n"
    )
    md = [
        f"# {pkg['policy_name']} — Representative Payer Definition",
        "",
        f"**Policy ID:** `{pkg['policy_id']}`  ",
        f"**Archetype:** `{pkg['archetype']}`  ",
        f"**Classification:** `{pkg['classification']}`  ",
        f"**Not claiming:** {pkg['not_claiming']}",
        "",
        "## Intent",
        "",
        pkg["identity"]["objective"],
        "",
        "## Scope",
        "",
        f"- LOB: {', '.join(pkg['scope']['lob'])}",
        f"- States: {', '.join(pkg['scope']['geography']['states'])}",
        f"- Markets: {', '.join(pkg['scope']['geography']['markets'])}",
        f"- Note: {pkg['scope']['geography']['market_claim_note']}",
        "",
        "## Codeset",
        "",
        f"- Status: **{pkg['codeset']['status']}**",
        f"- Notes: {pkg['codeset'].get('notes')}",
        "",
    ]
    if pkg["codeset"]["codes"]:
        md.append("| System | Code | Status | Evidence |")
        md.append("|---|---|---|---|")
        for c in pkg["codeset"]["codes"]:
            md.append(
                f"| {c['code_system']} | {c['code']} | {c['inclusion_status']} | {c['evidence_class']} |"
            )
    md += [
        "",
        "## Governance",
        "",
        f"- Definition status: `{pkg['governance']['definition_status']}`",
        f"- Operational activation: **{pkg['governance']['operational_activation']}**",
        "",
    ]
    (folder / f"{prefix}_POLICY_DEFINITION_v1.2.md").write_text("\n".join(md) + "\n")


def persist_levers(tok: str, live: dict, pkg: Dict[str, Any]) -> Dict[str, Any]:
    """Attach candidate codes to live policy_levers without inventing rates."""
    pid = pkg["policy_id"]
    if pid in FROZEN_NINE:
        return {"skipped": True, "reason": "frozen_dec4_nine"}
    codes = [c["code"] for c in pkg["codeset"]["codes"]]
    status = pkg["codeset"]["status"]
    levers = list(live.get("policy_levers") or [])
    if status == "CANDIDATE_SCHEDULE" and codes:
        if levers:
            params = dict(levers[0].get("parameters") or {})
            params["codes"] = codes
            params["evidence_class"] = "REPRESENTATIVE_DESIGN"
            params["requires_pa"] = params.get("requires_pa", True)
            levers[0] = {**levers[0], "parameters": params}
        else:
            levers = [
                {
                    "lever_type": live.get("policy_type") or "PRIOR_AUTH",
                    "parameters": {
                        "codes": codes,
                        "requires_pa": True,
                        "evidence_class": "REPRESENTATIVE_DESIGN",
                    },
                }
            ]
    body = {
        "name": live.get("name"),
        "description": live.get("description")
        or f"Representative Payer definition package {pkg['package_version']}",
        "policy_type": live.get("policy_type"),
        "scope": live.get("scope"),
        "policy_levers": levers,
        "status": live.get("status"),
        "effective_period": live.get("effective_period"),
        "enforcement": live.get("enforcement"),
    }
    # strip Nones that break validation
    body = {k: v for k, v in body.items() if v is not None}
    try:
        updated = api_put(tok, f"/policies/{pid}", body)
        return {
            "persisted": True,
            "code_count": len(codes),
            "codeset_status": status,
            "lever_codes": ((updated.get("policy_levers") or [{}])[0].get("parameters") or {}).get("codes"),
        }
    except Exception as e:
        return {"persisted": False, "error": str(e)[:300]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archetype", default="PRIOR_AUTH_UM")
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--persist", action="store_true", help="PUT levers to live API")
    ap.add_argument("--include-unresolved", action="store_true")
    args = ap.parse_args()

    inv = json.loads(INV.read_text())
    rows = [
        r
        for r in inv["policies"]
        if r["archetype"] == args.archetype and r["policy_id"] not in FROZEN_NINE
    ]
    rows = rows[args.offset : args.offset + args.limit]

    tok = login() if args.persist else None
    live_by_id = {}
    if args.persist:
        for p in api_get(tok, "/policies"):
            live_by_id[str(p["id"])] = p

    reg = load_registry()
    # ensure nine always registered
    for pid, folder in NINE_FOLDERS.items():
        reg.setdefault("packages", {})[pid] = folder

    CATALOG.mkdir(parents=True, exist_ok=True)
    results = []
    for row in rows:
        sched = lookup(row["name"])
        if sched["unresolved"] and not sched["not_applicable"] and not args.include_unresolved:
            # still generate package (honest UNRESOLVED) — always include
            pass
        live = live_by_id.get(row["policy_id"]) if args.persist else None
        pkg = build_package(row, live)
        folder_name = f"catalog/{slugify(row['name'])}"
        write_package_files(V12 / folder_name, pkg)
        reg["packages"][row["policy_id"]] = folder_name
        persist_result = None
        if args.persist and live:
            persist_result = persist_levers(tok, live, pkg)
        results.append(
            {
                "policy_id": row["policy_id"],
                "name": row["name"],
                "folder": folder_name,
                "codeset_status": pkg["codeset"]["status"],
                "code_count": len(pkg["codeset"]["codes"]),
                "definition_status": pkg["governance"]["definition_status"],
                "accuracy_failures": pkg["_validation"]["accuracy_failures"],
                "persist": persist_result,
            }
        )

    reg["updated_at"] = utc()
    reg["package_count"] = len(reg["packages"])
    save_registry(reg)

    out = EVID / f"BATCH_GEN_{args.archetype}_{args.offset}_{args.offset + len(rows)}.json"
    summary = {
        "archetype": args.archetype,
        "offset": args.offset,
        "count": len(results),
        "candidate_schedule": sum(1 for r in results if r["codeset_status"] == "CANDIDATE_SCHEDULE"),
        "unresolved": sum(1 for r in results if r["codeset_status"] == "UNRESOLVED"),
        "not_applicable": sum(1 for r in results if r["codeset_status"] == "NOT_APPLICABLE"),
        "persisted_ok": sum(1 for r in results if (r.get("persist") or {}).get("persisted")),
        "results": results,
    }
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in summary if k != "results"}, indent=2))
    print(f"Wrote {out}")
    print(f"Registry packages: {reg['package_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
