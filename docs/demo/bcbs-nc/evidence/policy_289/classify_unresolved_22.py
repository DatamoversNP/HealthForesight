#!/usr/bin/env python3
"""Workstream B — classify remaining UNRESOLVED definitions by missing dependency."""
from __future__ import annotations

import json
from pathlib import Path

EVID = Path(__file__).resolve().parent
INV = EVID / "POLICY_289_MASTER_INVENTORY.json"
OUT = EVID / "UNRESOLVED_22_DEPENDENCY_CLASSIFICATION.json"

# Explicit mapping — do not invent NDC/MUE/MCG/rates
CLASSIFICATION = {
    "ADHD Stimulant Quantity Limits and Preferred Agents": {
        "dependency": "NDC_DRUG_PRODUCT",
        "action": "Retain blocker until preferred-agent NDC list provided; no invented NDCs",
        "synthetic_demo_allowed": False,
    },
    "Benzodiazepine Quantity Limits": {
        "dependency": "NDC_DRUG_PRODUCT",
        "action": "Retain blocker — NDC/days-supply schedule required",
        "synthetic_demo_allowed": False,
    },
    "Digital Therapeutics Coverage Criteria": {
        "dependency": "NDC_DRUG_PRODUCT",
        "action": "DTx HCPCS/NDC product list UNRESOLVED",
        "synthetic_demo_allowed": False,
    },
    "Facility Fee Schedule and Bundled Payment Adjustments": {
        "dependency": "REIMBURSEMENT_RATES",
        "action": "Do not invent fee schedule tables or contracted rates",
        "synthetic_demo_allowed": False,
    },
    "Hepatitis C Direct-Acting Antiviral Prior Authorization": {
        "dependency": "NDC_DRUG_PRODUCT",
        "action": "DAA NDC/formulary schedule required",
        "synthetic_demo_allowed": False,
    },
    "HIV Antiretroviral Formulary Management": {
        "dependency": "NDC_DRUG_PRODUCT",
        "action": "ARV NDC formulary UNRESOLVED",
        "synthetic_demo_allowed": False,
    },
    "MCG Clinical Criteria for Inpatient Admissions": {
        "dependency": "LICENSED_MCG_CRITERIA",
        "action": "Licensed MCG content not redistributed — retain blocker",
        "synthetic_demo_allowed": False,
    },
    "MCG-Style Clinical Criteria for Inpatient Admissions": {
        "dependency": "LICENSED_MCG_CRITERIA",
        "action": "Illustrative label only — do not invent MCG criteria",
        "synthetic_demo_allowed": False,
    },
    "Medical Oncology Regimen Prior Authorization": {
        "dependency": "NDC_DRUG_PRODUCT",
        "action": "Regimen J-code/NDC product schedule UNRESOLVED",
        "synthetic_demo_allowed": False,
    },
    "NCCI and MUE Claims Edit Policy": {
        "dependency": "MUE_SOURCE_AND_SEMANTICS",
        "action": "Authoritative NCCI/MUE files required — do not invent MUE values",
        "synthetic_demo_allowed": True,
        "synthetic_note": "Dec4 MUE fixture already isolates synthetic demo separately",
    },
    "Oncology Evidence-Based Clinical Pathway": {
        "dependency": "LICENSED_CLINICAL_PATHWAY",
        "action": "Pathway content licensed/product-specific",
        "synthetic_demo_allowed": False,
    },
    "Oncology Oral Specialty Prior Authorization": {
        "dependency": "NDC_DRUG_PRODUCT",
        "action": "Oral oncolytic NDCs required",
        "synthetic_demo_allowed": False,
    },
    "Opioid Quantity Limit - Chronic Pain": {
        "dependency": "NDC_DRUG_PRODUCT",
        "action": "MME/NDC schedule UNRESOLVED — do not invent MME thresholds as verified",
        "synthetic_demo_allowed": False,
    },
    "Opioid Quantity Limit — Acute Pain": {
        "dependency": "NDC_DRUG_PRODUCT",
        "action": "Acute opioid days-supply product rule UNRESOLVED",
        "synthetic_demo_allowed": False,
    },
    "Opioid Quantity Limit — Chronic Pain": {
        "dependency": "NDC_DRUG_PRODUCT",
        "action": "Chronic opioid MME/NDC UNRESOLVED",
        "synthetic_demo_allowed": False,
    },
    "Retransplant Prior Authorization": {
        "dependency": "TRANSPLANT_ORGAN_SCHEDULE",
        "action": "Organ-specific transplant CPT/DRG schedule required",
        "synthetic_demo_allowed": False,
    },
    "Specialty Drug Days’ Supply Limits": {
        "dependency": "NDC_DRUG_PRODUCT",
        "action": "Specialty NDC days-supply list UNRESOLVED",
        "synthetic_demo_allowed": False,
    },
    "Transplant Evaluation and Listing Authorization": {
        "dependency": "TRANSPLANT_ORGAN_SCHEDULE",
        "action": "Organ-specific evaluation CPT + network rules UNRESOLVED",
        "synthetic_demo_allowed": False,
    },
    "UM Reduction for under age 45 and B1C": {
        "dependency": "PLACEHOLDER_UM_RULES",
        "action": "Internal program label — product clarification required",
        "synthetic_demo_allowed": False,
    },
    "UM Validation ": {
        "dependency": "PLACEHOLDER_UM_RULES",
        "action": "Placeholder catalog name — rename/define before configuration",
        "synthetic_demo_allowed": False,
    },
    "Unbundling and Incidental Denial Policy": {
        "dependency": "MUE_SOURCE_AND_SEMANTICS",
        "action": "Requires versioned edit pairs — UNRESOLVED without source file",
        "synthetic_demo_allowed": True,
        "synthetic_note": "Only with isolated fixture; do not invent CMS edit pairs",
    },
}


def main() -> int:
    inv = json.loads(INV.read_text())
    unres = [r for r in inv["policies"] if r["gates"].get("DEFINITION_COMPLETE") != "PASS"]
    rows = []
    by_dep = {}
    for r in unres:
        name = r["name"]
        # strip duplicate trailing space variants
        info = CLASSIFICATION.get(name) or CLASSIFICATION.get(name.strip()) or {
            "dependency": "OTHER",
            "action": "Review ledger package for specific deficiency",
            "synthetic_demo_allowed": False,
        }
        row = {
            "policy_id": r["policy_id"],
            "name": name,
            "archetype": r["archetype"],
            **info,
            "status": "BLOCKER_RETAINED",
        }
        rows.append(row)
        by_dep.setdefault(info["dependency"], []).append(r["policy_id"])

    out = {
        "document_id": "UNRESOLVED_22_DEPENDENCY_CLASSIFICATION",
        "count": len(rows),
        "by_dependency": {k: len(v) for k, v in sorted(by_dep.items(), key=lambda x: -len(x[1]))},
        "rule": "Do not fabricate confidential MUE values, licensed MCG, negotiated rates, or operative clinical criteria",
        "policies": rows,
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"count": len(rows), "by_dependency": out["by_dependency"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
