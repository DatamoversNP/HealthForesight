#!/usr/bin/env python3
"""Policy-level lifecycle validation matrix — does NOT equate DB row presence with validity.

Classes:
  FULLY_VALIDATED_DEMO — independent calculation / lineage check passed for demo
  ARTIFACTS_PRESENT_UNVALIDATED — B+P+O rows exist; mechanism correctness not verified
  PARTIAL — some stages present
  INAPPLICABLE_STAGE — missing stage expected given mechanism/data (documented)
  BLOCKED — defect or data insufficiency preventing progress
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs" / "demo" / "bcbs-nc" / "evidence" / "POLICY_INVENTORY_283_AUDIT.json"
MPPR = ROOT / "docs" / "demo" / "bcbs-nc" / "evidence" / "MPPR_REIMBURSEMENT_VERTICAL.json"
SOS = ROOT / "docs" / "demo" / "bcbs-nc" / "evidence" / "SOS_REIMBURSEMENT_VERTICAL.json"
OUT_JSON = ROOT / "docs" / "demo" / "bcbs-nc" / "evidence" / "LIFECYCLE_VALIDATION_MATRIX.json"
OUT_MD = ROOT / "docs" / "demo" / "bcbs-nc" / "evidence" / "LIFECYCLE_VALIDATION_MATRIX.md"

# Policies with independent demo validation (expand only after real checks)
VALIDATED_BY_NAME = {
    "Outpatient MRI Prior Authorization": {
        "class": "FULLY_VALIDATED_DEMO",
        "notes": "MRI UM lifecycle: claims-backed baseline, elasticity prediction, observations, OH↔PV alignment evidence, browser gates.",
        "mechanism": "UTILIZATION_MANAGEMENT",
    },
    "Multiple Procedure Payment Reduction": {
        "class": "FULLY_VALIDATED_DEMO",
        "notes": "MPPR payment-rule vertical with known-answer financial checks (reimbursement-mppr-v1); not UM elasticity.",
        "mechanism": "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION",
        "requires_mppr_evidence": True,
    },
    "Freestanding Imaging Steerage": {
        "class": "FULLY_VALIDATED_DEMO",
        "notes": "Site-of-service payment differential known-answer (reimbursement-sos-v1); hospital OP % of allowed; not UM elasticity.",
        "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
        "requires_sos_evidence": True,
    },
}

# Heuristic: payment policies with only utilization elasticity predictions are unvalidated for reimbursement
REIMB_TYPES = {
    "PAYMENT_POLICY",
    "REIMBURSEMENT_METHODOLOGY",
    "CODING_AND_BILLING",
    "EPISODE_BUNDLED_PAYMENT",
    "VALUE_BASED_PAYMENT",
}


def classify(p: dict, mppr_ok: bool, sos_ok: bool = False) -> dict:
    name = p["name"]
    s = p["stages"]
    b, pr, o, v = s["has_baseline"], s["has_prediction"], s["has_observation"], s["verdict_ready"]
    ptype = p.get("policy_type") or ""
    method = (p.get("prediction_method") or "").upper()

    special = VALIDATED_BY_NAME.get(name)
    if special:
        cls = special["class"]
        if special.get("requires_mppr_evidence") and not mppr_ok:
            cls = "ARTIFACTS_PRESENT_UNVALIDATED"
            note = "MPPR artifacts present but known-answer vertical not yet seeded."
        elif special.get("requires_sos_evidence") and not sos_ok:
            cls = "ARTIFACTS_PRESENT_UNVALIDATED"
            note = "SOS artifacts present but known-answer vertical not yet seeded."
        else:
            note = special["notes"]
        return {
            "policy_id": p["policy_id"],
            "name": name,
            "policy_type": ptype,
            "validation_class": cls,
            "artifact_BPO": f"{b}/{pr}/{o}",
            "verdict_ready_flag": v,
            "prediction_method": p.get("prediction_method"),
            "root_cause": None,
            "notes": note,
            "mechanism_hint": special.get("mechanism"),
        }

    if b and pr and o:
        # Presence ≠ validity
        note = "B+P+O rows present; mechanism-specific calculation and lineage not independently verified."
        if ptype in REIMB_TYPES and method in ("ELASTICITY_MODEL", "ELASTICITY", ""):
            note = (
                "Reimbursement/payment-typed policy with utilization elasticity prediction — "
                "do not treat as validated payment-impact lifecycle."
            )
        return {
            "policy_id": p["policy_id"],
            "name": name,
            "policy_type": ptype,
            "validation_class": "ARTIFACTS_PRESENT_UNVALIDATED",
            "artifact_BPO": f"{b}/{pr}/{o}",
            "verdict_ready_flag": v,
            "prediction_method": p.get("prediction_method"),
            "root_cause": None,
            "notes": note,
            "mechanism_hint": "REIMBURSEMENT" if ptype in REIMB_TYPES else "UNSPECIFIED",
        }

    # Partial / gap analysis
    if (not b) and pr and o and v:
        return {
            "policy_id": p["policy_id"],
            "name": name,
            "policy_type": ptype,
            "validation_class": "PARTIAL",
            "artifact_BPO": f"{b}/{pr}/{o}",
            "verdict_ready_flag": v,
            "prediction_method": p.get("prediction_method"),
            "root_cause": "VERDICT_WITHOUT_BASELINE",
            "notes": (
                "Verdict/observation present without persisted baseline. "
                "May be evidence-limited verdict — must not be described as completed B+P+O lifecycle."
            ),
            "mechanism_hint": "UM_OR_COVERAGE",
        }

    if (not b) and pr and (not o) and (not v):
        return {
            "policy_id": p["policy_id"],
            "name": name,
            "policy_type": ptype,
            "validation_class": "PARTIAL",
            "artifact_BPO": f"{b}/{pr}/{o}",
            "verdict_ready_flag": v,
            "prediction_method": p.get("prediction_method"),
            "root_cause": "PREDICTION_ONLY_TEST_OR_ORPHAN",
            "notes": "Prediction without baseline/observation — likely test/orphan seed (e.g. UM Validation).",
            "mechanism_hint": "TEST",
        }

    if not b and not pr and not o:
        # Catalog-only — distinguish inapplicable vs blocked
        if ptype in REIMB_TYPES or "FEE" in name.upper() or "BUNDL" in name.upper():
            rc = "NO_MECHANISM_SPECIFIC_ANALYTICS"
            note = (
                "No B+P+O. Reimbursement/coding family — blocked for NCCI/modifier paths if schema lacks "
                "modifiers; otherwise awaiting mechanism-specific financial baseline (do not auto-fill)."
            )
            cls = "BLOCKED"
        elif ptype in ("DRUG_FORMULARY", "SPECIALTY_PHARMACY", "EXPERIMENTAL_INVESTIGATIONAL"):
            rc = "INSUFFICIENT_OR_OUT_OF_SCOPE_CLAIMS"
            note = "Catalog-only; pharmacy/experimental mechanisms may lack adequate claim fields — INAPPLICABLE until data exists."
            cls = "INAPPLICABLE_STAGE"
        else:
            rc = "CATALOG_ONLY_UNSEEDED"
            note = "Configured catalog row without analytical artifacts — not defects by itself; do not manufacture observations."
            cls = "INAPPLICABLE_STAGE"
        return {
            "policy_id": p["policy_id"],
            "name": name,
            "policy_type": ptype,
            "validation_class": cls,
            "artifact_BPO": f"{b}/{pr}/{o}",
            "verdict_ready_flag": v,
            "prediction_method": p.get("prediction_method"),
            "root_cause": rc,
            "notes": note,
            "mechanism_hint": ptype,
        }

    return {
        "policy_id": p["policy_id"],
        "name": name,
        "policy_type": ptype,
        "validation_class": "PARTIAL",
        "artifact_BPO": f"{b}/{pr}/{o}",
        "verdict_ready_flag": v,
        "prediction_method": p.get("prediction_method"),
        "root_cause": "MIXED_STAGE_PATTERN",
        "notes": "Unusual stage combination — investigate before seeding.",
        "mechanism_hint": ptype,
    }


def main() -> None:
    audit = json.loads(AUDIT.read_text())
    mppr_ok = False
    if MPPR.exists():
        mppr = json.loads(MPPR.read_text())
        mppr_ok = bool(mppr.get("known_answer", {}).get("passed")) and mppr.get(
            "validation_class"
        ) == "FULLY_VALIDATED_DEMO"
    sos_ok = False
    if SOS.exists():
        sos = json.loads(SOS.read_text())
        sos_ok = bool(sos.get("known_answer", {}).get("passed")) and sos.get(
            "validation_class"
        ) == "FULLY_VALIDATED_DEMO"

    rows = [classify(p, mppr_ok, sos_ok) for p in audit["policies"]]
    counts = Counter(r["validation_class"] for r in rows)
    gap = [r for r in rows if r["artifact_BPO"] != "True/True/True"]
    verdict_no_bpo = [
        r for r in rows if r["verdict_ready_flag"] and r["artifact_BPO"] != "True/True/True"
    ]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "definition": (
            "FULLY_VALIDATED_DEMO requires independent calculation/lineage checks. "
            "Artifact presence alone → ARTIFACTS_PRESENT_UNVALIDATED."
        ),
        "counts": dict(counts),
        "catalog_policies": len(rows),
        "artifact_full_bpo": sum(1 for r in rows if r["artifact_BPO"] == "True/True/True"),
        "incomplete_bpo": len(gap),
        "verdict_without_full_bpo": len(verdict_no_bpo),
        "mppr_vertical_seeded": mppr_ok,
        "sos_vertical_seeded": sos_ok,
        "dec4_readiness": {
            "claim": False,
            "reason": (
                "FULLY_VALIDATED_DEMO limited to MRI + seeded reimbursement engines "
                f"(MPPR={mppr_ok}, SOS={sos_ok}); "
                f"{counts.get('ARTIFACTS_PRESENT_UNVALIDATED', 0)} unvalidated artifact rows; "
                "browser gates required; portfolio causal IMPACT_ASSESSABLE remains 0."
            ),
        },
        "gap_root_causes": Counter(r["root_cause"] for r in gap if r.get("root_cause")),
        "verdict_without_bpo_policies": [
            {"name": r["name"], "root_cause": r["root_cause"]} for r in verdict_no_bpo
        ],
        "policies": rows,
    }
    # Counter not JSON serializable in nested
    payload["gap_root_causes"] = dict(payload["gap_root_causes"])

    OUT_JSON.write_text(json.dumps(payload, indent=2))

    lines = [
        "# Lifecycle Validation Matrix",
        "",
        f"**Generated:** {payload['generated_at']}",
        "",
        "## Rule",
        "",
        payload["definition"],
        "",
        "## Counts",
        "",
        "| Class | N |",
        "|-------|--:|",
    ]
    for k, v in sorted(counts.items()):
        lines.append(f"| {k} | {v} |")
    lines += [
        "",
        f"Artifact full B+P+O (presence only): **{payload['artifact_full_bpo']}** / {payload['catalog_policies']}",
        f"Verdict without full B+P+O: **{payload['verdict_without_full_bpo']}**",
        f"MPPR known-answer vertical seeded: **{mppr_ok}**",
        "",
        "## December 4 readiness",
        "",
        f"- Claim completion: **{payload['dec4_readiness']['claim']}**",
        f"- Reason: {payload['dec4_readiness']['reason']}",
        "",
        "## Gap root causes (26 incomplete B+P+O)",
        "",
    ]
    for k, v in sorted(payload["gap_root_causes"].items(), key=lambda x: -x[1]):
        lines.append(f"- `{k}`: {v}")
    lines += [
        "",
        "## Verdict-ready without complete B+P+O (8)",
        "",
    ]
    for r in verdict_no_bpo:
        lines.append(f"- {r['name']} — {r['root_cause']}")
    lines += [
        "",
        "## Fully validated demo policies",
        "",
    ]
    for r in rows:
        if r["validation_class"] == "FULLY_VALIDATED_DEMO":
            lines.append(f"- **{r['name']}** (`{r['policy_id']}`): {r['notes']}")
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps({"counts": dict(counts), "mppr_ok": mppr_ok, "out": str(OUT_JSON)}, indent=2))


if __name__ == "__main__":
    main()
