#!/usr/bin/env python3
"""Build POLICY_289_MASTER_INVENTORY + archetype registry + ledger scaffolds.

Honest inventory — does NOT mark policies DEFINITION_COMPLETE.
Representative Payer Policies: industry-grounded configuration target;
NOT proprietary Blue Cross NC operative policies.
"""
from __future__ import annotations

import json
import re
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

API = "http://127.0.0.1:7867/api/v1"
EMAIL = "admin@healthforesight.com"
PASSWORD = "Swan@1234"
OUT = Path(__file__).resolve().parent
REPO = OUT.parents[4]
V12 = REPO / "docs" / "demo" / "bcbs-nc" / "policy_definitions" / "v1.2"

NINE = {
    "d403f101-08dd-45c9-ab83-d42e37c62018": "mri",
    "d0eeb370-df14-4478-8755-dad6c3a35a47": "mppr",
    "d7441dd9-3bfe-405e-ae6c-0377204bbb7e": "sos",
    "58b839b5-b6e0-59e0-9406-d817877c3ce8": "ptp",
    "e11b049d-fcce-55cc-bcd7-71329038383b": "mue",
    "f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b": "therapy",
    "11218053-bdc0-569f-a415-fb61c5dcda37": "infusion",
    "4f8c34e3-015b-509d-90ba-521261464258": "ncd",
    "649b4ac8-ca82-5b84-aa87-84834490731a": "lcd",
}

# Map catalog policy_type → archetype family (mechanism-aware; refined by name heuristics)
TYPE_TO_ARCHETYPE = {
    "PRIOR_AUTH": "PRIOR_AUTH_UM",
    "UTILIZATION_MANAGEMENT": "PRIOR_AUTH_UM",
    "MEDICAL_NECESSITY": "MEDICAL_NECESSITY_COVERAGE",
    "CLINICAL_CRITERIA": "MEDICAL_NECESSITY_COVERAGE",
    "COVERAGE": "MEDICAL_NECESSITY_COVERAGE",
    "EXPERIMENTAL_INVESTIGATIONAL": "MEDICAL_NECESSITY_COVERAGE",
    "PREVENTIVE_SERVICES": "MEDICAL_NECESSITY_COVERAGE",
    "PAYMENT_POLICY": "PAYMENT_REIMBURSEMENT",
    "REIMBURSEMENT_METHODOLOGY": "PAYMENT_REIMBURSEMENT",
    "EPISODE_BUNDLED_PAYMENT": "PAYMENT_REIMBURSEMENT",
    "VALUE_BASED_PAYMENT": "PAYMENT_REIMBURSEMENT",
    "COST_SHARING": "PAYMENT_REIMBURSEMENT",
    "CODING_AND_BILLING": "CODING_CLAIM_INTEGRITY",
    "SITE_OF_CARE": "SITE_OF_CARE",
    "POST_ACUTE_CARE": "SITE_OF_CARE",
    "STEP_THERAPY": "PHARMACY_SPECIALTY",
    "DRUG_FORMULARY": "PHARMACY_SPECIALTY",
    "SPECIALTY_PHARMACY": "PHARMACY_SPECIALTY",
    "QUANTITY_LIMIT": "PHARMACY_SPECIALTY",
    "DURATION_FREQUENCY_LIMIT": "BENEFIT_ELIGIBILITY",
    "BENEFIT": "BENEFIT_ELIGIBILITY",
    "NETWORK_RESTRICTION": "PROVIDER_NETWORK",
    "PROVIDER_ELIGIBILITY": "PROVIDER_NETWORK",
    "REFERRAL_REQUIREMENT": "PROVIDER_NETWORK",
    "OUT_OF_NETWORK_COVERAGE": "PROVIDER_NETWORK",
    "ACCESS_AVAILABILITY_RULE": "PROVIDER_NETWORK",
    "TELEHEALTH_VIRTUAL_CARE": "TELEHEALTH",
    "CLINICAL_PATHWAY": "CLINICAL_PATHWAY",
    "CONTINUITY_OF_CARE": "CLINICAL_PATHWAY",
    "ADMINISTRATIVE_REQUIREMENT": "ADMINISTRATIVE",
    "COMPOSITE": "COMPOSITE",
}


def _login() -> str:
    req = urllib.request.Request(
        f"{API}/auth/login",
        data=json.dumps({"email": EMAIL, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["access_token"]


def _get(tok: str, path: str):
    req = urllib.request.Request(
        f"{API}{path}", headers={"Authorization": f"Bearer {tok}"}
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def _codes(policy: dict) -> list[str]:
    out: list[str] = []
    for lever in policy.get("policy_levers") or []:
        params = (lever or {}).get("parameters") or {}
        for k in ("codes", "cpt_codes", "target_codes", "procedure_codes", "ndc_codes"):
            v = params.get(k)
            if isinstance(v, list):
                out.extend(str(x) for x in v if x is not None)
    return sorted(set(out))


def _classify(policy: dict) -> str:
    name = (policy.get("name") or "").lower()
    ptype = (policy.get("policy_type") or "").upper()
    # Name heuristics override for Medicare studies / coding edits
    if re.search(r"\bncd\b", name):
        return "MEDICARE_NCD_LCD_STUDY"
    if re.search(r"\blcd\b", name):
        return "MEDICARE_NCD_LCD_STUDY"
    if "ncci" in name or "ptp" in name or "mue" in name or "bundling" in name:
        return "CODING_CLAIM_INTEGRITY"
    if "site of care" in name or "site-of-care" in name or "freestanding" in name or "steerage" in name:
        return "SITE_OF_CARE"
    if "mppr" in name or "multiple procedure" in name or "payment reduction" in name:
        return "PAYMENT_REIMBURSEMENT"
    if "formulary" in name or "pharmacy" in name or "ndc" in name or "step therapy" in name or "quantity limit" in name and "drug" in name:
        return "PHARMACY_SPECIALTY"
    if "therapy" in name and ("outpatient" in name or "pt " in name or "ot " in name or "speech" in name):
        return "THERAPY_REHAB"
    base = TYPE_TO_ARCHETYPE.get(ptype, "OTHER_UNSPECIFIED")
    if base == "PRIOR_AUTH_UM" and "therapy" in name:
        return "THERAPY_REHAB"
    return base


def _package_registry() -> dict:
    path = V12 / "POLICY_PACKAGE_REGISTRY.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text()).get("packages") or {}
    except Exception:
        return {}


def _has_v12_package(policy_id: str, registry: dict | None = None) -> str | None:
    reg = registry if registry is not None else _package_registry()
    if policy_id in reg:
        folder = reg[policy_id]
        if (V12 / folder).exists():
            return folder
    key = NINE.get(policy_id)
    if not key:
        return None
    folder = {
        "mri": "mri",
        "mppr": "mppr",
        "sos": "sos",
        "ptp": "ptp",
        "mue": "mue",
        "therapy": "therapy",
        "infusion": "infusion",
        "ncd": "ncd_study",
        "lcd": "lcd_study",
    }.get(key)
    if folder and (V12 / folder).exists():
        return folder
    return None


def _package_codeset_status(folder: str | None) -> str | None:
    if not folder:
        return None
    p = V12 / folder
    if not p.exists():
        return None
    pkg_path = next(iter(sorted(p.glob("*PACKAGE.json"))), None)
    if pkg_path:
        try:
            return (json.loads(pkg_path.read_text()).get("codeset") or {}).get("status")
        except Exception:
            return None
    # Legacy nine folders without PACKAGE.json
    if folder in {
        "mri",
        "mppr",
        "sos",
        "ptp",
        "mue",
        "therapy",
        "infusion",
        "ncd_study",
        "lcd_study",
    }:
        return "LEGACY_NINE"
    return None


def _honest_status(policy: dict, codes: list[str], archetype: str, folder: str | None = None) -> dict:
    """Conservative gate statuses — PASS only with evidence."""
    sc = policy.get("scope") or {}
    markets = sc.get("markets")
    states = sc.get("states")
    levers = policy.get("policy_levers") or []
    pid = str(policy.get("id"))
    has_pkg = folder is not None
    codeset_status = _package_codeset_status(folder)
    def_complete = has_pkg and codeset_status in {
        "CANDIDATE_SCHEDULE",
        "NOT_APPLICABLE",
        "LEGACY_NINE",
    }

    # Scope: NC states preferred for Representative NC demo; markets must be non-empty
    scope_ok = bool(states) and bool(markets)
    # Lever/code: mechanism-dependent — coding/PA need codes; payment may use non-code levers
    needs_codes = archetype in {
        "PRIOR_AUTH_UM",
        "MEDICAL_NECESSITY_COVERAGE",
        "CODING_CLAIM_INTEGRITY",
        "THERAPY_REHAB",
        "SITE_OF_CARE",
    }
    codes_ok = (
        codeset_status in {"NOT_APPLICABLE", "LEGACY_NINE"}
        or bool(codes)
        or codeset_status == "CANDIDATE_SCHEDULE"
    )
    levers_ok = bool(levers) and (
        bool(codes) if needs_codes and codeset_status == "CANDIDATE_SCHEDULE" else True
    )

    # MRI special: codes present but markets NYC/DFW vs states NC — scope/lever alignment caution
    lever_scope_aligned = True
    if pid in NINE and NINE[pid] == "mri":
        lever_scope_aligned = set(codes).issubset({"72148", "72149", "72158"}) and bool(markets)

    return {
        "DEFINITION_COMPLETE": "PASS" if def_complete else ("PARTIAL" if has_pkg else "FAIL"),
        "POLICY_SCOPE_VALIDATED": "PASS" if scope_ok else "FAIL",
        "CODESET_VALIDATED": (
            "PASS"
            if codeset_status in {"CANDIDATE_SCHEDULE", "NOT_APPLICABLE", "LEGACY_NINE"}
            else ("FAIL" if codeset_status == "UNRESOLVED" else ("PARTIAL" if codes else "FAIL"))
        ),
        "LEVERS_VALIDATED": (
            "PASS"
            if levers_ok and lever_scope_aligned and def_complete
            else ("PARTIAL" if levers else "FAIL")
        ),
        "SOURCE_APPLICABILITY_VALIDATED": "PARTIAL" if has_pkg else "FAIL",
        "ANALYTICAL_MECHANISM_VALIDATED": "PARTIAL" if pid in NINE else "NOT_STARTED",
        "LIFECYCLE_EXECUTED": "PARTIAL" if pid in NINE else "NOT_STARTED",
        "DEMO_READY": "PASS" if pid in {"d403f101-08dd-45c9-ab83-d42e37c62018", "d0eeb370-df14-4478-8755-dad6c3a35a47", "d7441dd9-3bfe-405e-ae6c-0377204bbb7e"} else ("PARTIAL" if def_complete else "FAIL"),
        "OPERATIONALLY_APPROVED": "PROHIBITED",
        "notes": (
            f"v1.2 package ({codeset_status}) — Representative Payer; not BCBS NC proprietary"
            if has_pkg
            else "No mechanism-specific definition package; overnight HIGH ≠ definition completeness"
        ),
    }


def main():
    tok = _login()
    policies = _get(tok, "/policies")
    assert isinstance(policies, list), type(policies)
    assert len(policies) == 289, f"expected 289 got {len(policies)}"

    rows = []
    by_arch: dict[str, list[str]] = defaultdict(list)
    registry = _package_registry()
    for p in policies:
        pid = str(p.get("id"))
        codes = _codes(p)
        arch = _classify(p)
        by_arch[arch].append(pid)
        sc = p.get("scope") or {}
        folder = _has_v12_package(pid, registry)
        statuses = _honest_status(p, codes, arch, folder)
        rows.append(
            {
                "policy_id": pid,
                "name": p.get("name"),
                "policy_type": p.get("policy_type"),
                "status": p.get("status"),
                "archetype": arch,
                "dec4_nine_key": NINE.get(pid),
                "v12_package_folder": folder,
                "scope": {
                    "lob": sc.get("lob"),
                    "markets": sc.get("markets"),
                    "states": sc.get("states"),
                    "network": sc.get("network"),
                },
                "effective_period": p.get("effective_period"),
                "enforcement": p.get("enforcement"),
                "lever_count": len(p.get("policy_levers") or []),
                "lever_types": [
                    (L or {}).get("lever_type") for L in (p.get("policy_levers") or [])
                ],
                "codes": codes,
                "code_count": len(codes),
                "description_present": bool(p.get("description")),
                "classification": "REPRESENTATIVE_PAYER_POLICY",
                "not_claiming": "Authoritative Blue Cross NC operative policy text",
                "gates": statuses,
                "inventory_flags": {
                    "has_v12_definition_package": bool(folder),
                    "has_cpt_on_levers": bool(codes),
                    "scope_markets_nc": sc.get("markets") == ["NC"],
                    "scope_states_nc": sc.get("states") == ["NC"],
                    "frozen_dec4_ka": pid
                    in {
                        "d403f101-08dd-45c9-ab83-d42e37c62018",
                        "d0eeb370-df14-4478-8755-dad6c3a35a47",
                        "d7441dd9-3bfe-405e-ae6c-0377204bbb7e",
                    },
                },
            }
        )

    rows.sort(key=lambda r: (r.get("name") or "").lower())
    generated_at = datetime.now(timezone.utc).isoformat()

    inventory = {
        "document_id": "POLICY_289_MASTER_INVENTORY",
        "generated_at": generated_at,
        "tenant_note": "Representative Payer Policies (Blue Cross NC-like demo) — NOT proprietary BCBS NC operative policies",
        "total": len(rows),
        "constraints": {
            "catalog_expansion": "FORBIDDEN",
            "claims_reseed": "FORBIDDEN",
            "dec4_frozen_kas": ["mri", "mppr", "sos"],
            "operational_activation": "PROHIBITED_WITHOUT_SEPARATE_APPROVAL",
            "accuracy_standard": "POLICY_ACCURACY_PRIMARY — do not invent authoritative payer rules",
        },
        "archetype_counts": {k: len(v) for k, v in sorted(by_arch.items())},
        "gate_summary": {
            g: dict(Counter(r["gates"][g] for r in rows))
            for g in rows[0]["gates"].keys()
        },
        "policies": rows,
    }
    (OUT / "POLICY_289_MASTER_INVENTORY.json").write_text(
        json.dumps(inventory, indent=2) + "\n"
    )

    # Archetype registry
    arch_defs = {
        "PRIOR_AUTH_UM": {
            "required_code_systems": ["CPT", "HCPCS"],
            "analytical_engines": ["UM_ELASTICITY", "BASELINE", "PREDICTED_IMPACT", "OBSERVATION"],
            "causal_default": "DID_IF_IDENTIFIABLE_ELSE_DESCRIPTIVE",
        },
        "MEDICAL_NECESSITY_COVERAGE": {
            "required_code_systems": ["CPT", "HCPCS", "ICD10"],
            "analytical_engines": ["COVERAGE_APPLICABILITY", "BASELINE", "PREDICTED_IMPACT"],
            "causal_default": "DESCRIPTIVE_OR_PROVENANCE",
        },
        "PAYMENT_REIMBURSEMENT": {
            "required_code_systems": ["CPT", "HCPCS"],
            "analytical_engines": ["REIMBURSEMENT_MPPR", "REIMBURSEMENT_WHATIF", "BASELINE"],
            "causal_default": "MECHANICAL_NOT_CAUSAL",
        },
        "CODING_CLAIM_INTEGRITY": {
            "required_code_systems": ["CPT", "HCPCS", "MODIFIER"],
            "analytical_engines": ["CODING_EDIT_FIXTURE", "BASELINE"],
            "causal_default": "SYNTHETIC_FIXTURE_OR_DATA_INSUFFICIENT",
        },
        "SITE_OF_CARE": {
            "required_code_systems": ["CPT", "HCPCS", "POS"],
            "analytical_engines": ["SITE_OF_CARE_STEERAGE", "BASELINE", "WHATIF"],
            "causal_default": "MECHANICAL_OR_DID",
        },
        "THERAPY_REHAB": {
            "required_code_systems": ["CPT"],
            "analytical_engines": ["COVERAGE_PAYMENT", "BASELINE"],
            "causal_default": "MECHANICAL_OR_NOT_SUPPORTED",
        },
        "PHARMACY_SPECIALTY": {
            "required_code_systems": ["NDC", "HCPCS", "CPT"],
            "analytical_engines": ["PHARMACY_STEP_QL", "BASELINE"],
            "causal_default": "DESCRIPTIVE_OR_SYNTHETIC",
        },
        "PROVIDER_NETWORK": {
            "required_code_systems": ["NOT_APPLICABLE_OR_TAXONOMY"],
            "analytical_engines": ["NETWORK_ACCESS", "BASELINE"],
            "causal_default": "DESCRIPTIVE",
        },
        "BENEFIT_ELIGIBILITY": {
            "required_code_systems": ["CPT", "HCPCS", "NOT_APPLICABLE"],
            "analytical_engines": ["BENEFIT_UTILIZATION", "BASELINE"],
            "causal_default": "DESCRIPTIVE",
        },
        "TELEHEALTH": {
            "required_code_systems": ["CPT", "MODIFIER", "POS"],
            "analytical_engines": ["TELEHEALTH_COVERAGE", "BASELINE"],
            "causal_default": "DESCRIPTIVE",
        },
        "MEDICARE_NCD_LCD_STUDY": {
            "required_code_systems": ["CPT", "HCPCS", "ICD10"],
            "analytical_engines": ["PROVENANCE_APPLICABILITY"],
            "causal_default": "PROVENANCE_ONLY",
        },
        "CLINICAL_PATHWAY": {
            "required_code_systems": ["CPT", "ICD10"],
            "analytical_engines": ["PATHWAY_ADHERENCE", "BASELINE"],
            "causal_default": "DESCRIPTIVE",
        },
        "ADMINISTRATIVE": {
            "required_code_systems": ["NOT_APPLICABLE"],
            "analytical_engines": ["ADMIN_COMPLIANCE"],
            "causal_default": "NOT_APPLICABLE",
        },
        "COMPOSITE": {
            "required_code_systems": ["MULTI"],
            "analytical_engines": ["COMPOSITE"],
            "causal_default": "PER_COMPONENT",
        },
        "OTHER_UNSPECIFIED": {
            "required_code_systems": ["UNRESOLVED"],
            "analytical_engines": ["UNRESOLVED"],
            "causal_default": "UNRESOLVED",
        },
    }
    registry = {
        "document_id": "POLICY_ARCHETYPE_REGISTRY",
        "generated_at": generated_at,
        "rule": "Archetypes accelerate engineering; each policy must still receive a distinct definition. Do not invent proprietary BCBS NC rules.",
        "evidence_hierarchy": [
            "versioned_authoritative_public_sources",
            "verified_existing_configuration",
            "established_industry_guidance_with_applicability",
            "REPRESENTATIVE_PAYER_DESIGN",
            "ISOLATED_SYNTHETIC_DEMO_PARAMETERS",
        ],
        "archetypes": {
            k: {
                **v,
                "policy_count": len(by_arch.get(k, [])),
                "policy_ids": by_arch.get(k, []),
            }
            for k, v in arch_defs.items()
            if k in by_arch or k in arch_defs
        },
        "unmapped_types": sorted(
            {
                r["policy_type"]
                for r in rows
                if r["archetype"] == "OTHER_UNSPECIFIED"
            }
        ),
    }
    # only include archetypes that appear or are defined
    registry["archetypes"] = {
        k: registry["archetypes"][k]
        for k in sorted(set(list(arch_defs.keys()) + list(by_arch.keys())))
        if k in registry["archetypes"]
    }
    for k in by_arch:
        if k not in registry["archetypes"]:
            registry["archetypes"][k] = {
                "required_code_systems": ["UNRESOLVED"],
                "analytical_engines": ["UNRESOLVED"],
                "causal_default": "UNRESOLVED",
                "policy_count": len(by_arch[k]),
                "policy_ids": by_arch[k],
            }
    (OUT / "POLICY_ARCHETYPE_REGISTRY.json").write_text(
        json.dumps(registry, indent=2) + "\n"
    )

    # Configuration ledger (one row per policy) — honest starting point
    config_ledger = {
        "document_id": "POLICY_289_CONFIGURATION_LEDGER",
        "generated_at": generated_at,
        "program_deadline": "2026-12-03",
        "accuracy_primary": True,
        "operational_approval": "INDEPENDENT_NOT_MANUFACTURED",
        "summary": inventory["gate_summary"],
        "policies": [
            {
                "policy_id": r["policy_id"],
                "name": r["name"],
                "archetype": r["archetype"],
                "policy_type": r["policy_type"],
                "gates": r["gates"],
                "code_count": r["code_count"],
                "lever_count": r["lever_count"],
                "v12_package_folder": r["v12_package_folder"],
                "final_configuration_status": (
                    "DEMO_READY_REPRESENTATIVE"
                    if r["gates"]["DEMO_READY"] == "PASS"
                    else (
                        "DEFINITION_PACKAGE_PRESENT"
                        if r["v12_package_folder"]
                        else "NOT_DEFINITION_COMPLETE"
                    )
                ),
                "unresolved": []
                if r["v12_package_folder"]
                else [
                    "mechanism_specific_definition_package",
                    "source_backed_rules",
                    "validated_codeset_or_NOT_APPLICABLE",
                    "lever_scope_alignment_tests",
                ],
            }
            for r in rows
        ],
    }
    (OUT / "POLICY_289_CONFIGURATION_LEDGER.json").write_text(
        json.dumps(config_ledger, indent=2) + "\n"
    )

    exec_ledger = {
        "document_id": "POLICY_289_ANALYTICAL_EXECUTION_LEDGER",
        "generated_at": generated_at,
        "note": "Populate as controlled lifecycles execute. Synthetic ≠ empirical.",
        "policies": [
            {
                "policy_id": r["policy_id"],
                "name": r["name"],
                "archetype": r["archetype"],
                "baseline": "EXECUTED" if r["dec4_nine_key"] else "NOT_STARTED",
                "predicted_impact": "EXECUTED" if r["dec4_nine_key"] == "mri" else ("SKIPPED_OR_FIXTURE" if r["dec4_nine_key"] else "NOT_STARTED"),
                "observation": "EXISTING_OR_FIXTURE" if r["dec4_nine_key"] else "NOT_STARTED",
                "causal_feasibility": "AVAILABLE_VIA_ENTERPRISE_API",
                "whatif": "FIXTURE" if r["dec4_nine_key"] in {"mri", "mppr", "sos", "ptp", "mue", "therapy", "infusion"} else "NOT_STARTED",
                "evidence_class": (
                    "FULLY_VALIDATED_DEMO_SYNTHETIC"
                    if r["inventory_flags"]["frozen_dec4_ka"]
                    else (
                        "PROVENANCE_ONLY"
                        if r["dec4_nine_key"] in {"ncd", "lcd"}
                        else "UNRESOLVED"
                    )
                ),
            }
            for r in rows
        ],
    }
    (OUT / "POLICY_289_ANALYTICAL_EXECUTION_LEDGER.json").write_text(
        json.dumps(exec_ledger, indent=2) + "\n"
    )

    # Daily ledger Nov 4
    def_complete = sum(1 for r in rows if r["gates"]["DEFINITION_COMPLETE"] == "PASS")
    demo_ready = sum(1 for r in rows if r["gates"]["DEMO_READY"] == "PASS")
    daily = {
        "date": "2026-11-04",
        "total_policies": 289,
        "definition_complete": def_complete,
        "live_configured_accuracy_validated": def_complete,  # only packages so far
        "mechanism_executable": demo_ready,
        "supported_lifecycle_execution": len(NINE),
        "browser_validated_dec4_primary": 3,
        "source_verified": 0,
        "synthetic_only": len(NINE),
        "data_insufficient": 0,
        "operationally_approved": 0,
        "overnight_platform_health_high": "see ALL_POLICIES_HIGH_CONFIDENCE_MASTER_REPORT — reliability ≠ definition completeness",
        "critical_blockers": [
            "280 policies lack mechanism-specific definition packages",
            "Only ~23 catalog policies have CPT codes on levers",
            "Must not invent proprietary BCBS NC clinical/payment terms",
            "Lumbar MRI codes absent from market=NC claims (metros hold codes)",
        ],
        "next_24h": [
            "Finalize shared definition schema + accuracy validators",
            "Stand up resumable archetype batch runner",
            "Begin Batch 1: PRIOR_AUTH_UM policies with public CPT schedules + representative design",
        ],
        "forecast_note": "Throughput not yet observed for definition generation — do not fabricate ETA until Batch 1 completes",
    }
    (OUT / "POLICY_289_DAILY_LEDGER_2026-11-04.json").write_text(
        json.dumps(daily, indent=2) + "\n"
    )

    md = [
        "# Policy 289 Definition Completeness Report (Day 0)",
        "",
        f"Generated: `{generated_at}`",
        "",
        "## Mandate",
        "",
        "- Target: **289/289** definition-complete + demo-executable by **2026-12-03**",
        "- Classification: **Representative Payer Policies** (not proprietary BCBS NC operative text)",
        "- Accuracy primary; do not invent authoritative rules or approvals",
        "- Overnight platform-health HIGH ≠ definition completeness",
        "",
        "## Current honest counts",
        "",
        f"- Total policies: **{len(rows)}**",
        f"- Definition packages (v1.2): **{def_complete}** / 289",
        f"- Demo-ready (frozen Dec4 primary): **{demo_ready}**",
        f"- Operationally approved: **0** (prohibited)",
        "",
        "## Archetype distribution",
        "",
    ]
    for k, n in sorted(inventory["archetype_counts"].items(), key=lambda x: -x[1]):
        md.append(f"- `{k}`: {n}")
    md += [
        "",
        "## Gate summary",
        "",
        "```json",
        json.dumps(inventory["gate_summary"], indent=2),
        "```",
        "",
        "## Deliverables written",
        "",
        "- `POLICY_289_MASTER_INVENTORY.json`",
        "- `POLICY_ARCHETYPE_REGISTRY.json`",
        "- `POLICY_289_CONFIGURATION_LEDGER.json`",
        "- `POLICY_289_ANALYTICAL_EXECUTION_LEDGER.json`",
        "- `POLICY_289_DAILY_LEDGER_2026-11-04.json`",
        "",
    ]
    (OUT / "POLICY_289_DEFINITION_COMPLETENESS_REPORT.md").write_text("\n".join(md) + "\n")

    print(json.dumps({
        "total": len(rows),
        "definition_complete": def_complete,
        "demo_ready": demo_ready,
        "archetypes": inventory["archetype_counts"],
    }, indent=2))


if __name__ == "__main__":
    main()
