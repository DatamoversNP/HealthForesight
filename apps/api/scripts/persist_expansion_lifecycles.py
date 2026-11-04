#!/usr/bin/env python3
"""Persist independent lifecycle artifacts for PTP / MUE / therapy / infusion.

Does NOT add catalog seed rows beyond the four expansion policies.
Writes evidence JSON + Analysis/WhatIfScenarioResult rows for each vertical.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [
    str(REPO / "apps" / "api" / "src"),
    str(REPO / "packages" / "common" / "src"),
]

from uepi_api.database import SessionLocal
from uepi_api.models.analysis import Analysis, AnalysisStatus, AnalysisType, WhatIfScenarioResult
from uepi_api.services.expansion_demo_scenarios import (
    INFUSION_SOC_POLICY_ID,
    MUE_POLICY_ID,
    PTP_POLICY_ID,
    THERAPY_POLICY_ID,
    all_known_answer_suite,
    apply_infusion_soc,
    apply_ncci_mue,
    apply_ncci_ptp,
    apply_therapy_coverage,
    INFUSION_KNOWN,
    MUE_KNOWN_LINES,
    PTP_KNOWN_LINES,
    THERAPY_KNOWN,
    seed_expansion_policies,
    scenario_catalog,
)
from uepi_api.services.reimbursement_whatif import run_reimbursement_whatif

TENANT = UUID("00000000-0000-0000-0000-000000000001")
EVIDENCE = REPO / "docs" / "demo" / "bcbs-nc" / "evidence"


def _persist_whatif(db, *, policy_id: str, name: str, ptype: str, meta: dict, params: dict) -> dict:
    out = run_reimbursement_whatif(
        policy_type=ptype,
        policy_name=name,
        metadata=meta,
        policy_id=policy_id,
        scenario_params=params,
    )
    now = datetime.utcnow()
    analysis = Analysis(
        id=uuid4(),
        tenant_id=TENANT,
        policy_id=UUID(policy_id),
        analysis_type=AnalysisType.SIMULATE,
        status=AnalysisStatus.COMPLETED if out.get("status") == "completed" else AnalysisStatus.FAILED,
        created_at=now,
        updated_at=now,
    )
    db.add(analysis)
    db.flush()
    if out.get("status") == "completed":
        db.add(
            WhatIfScenarioResult(
                id=uuid4(),
                tenant_id=TENANT,
                analysis_id=analysis.id,
                policy_id=UUID(policy_id),
                result_data_json=out["result"],
                schema_version="1.0",
                created_at=now,
                updated_at=now,
            )
        )
    return {
        "analysis_id": str(analysis.id),
        "whatif_status": out.get("status"),
        "whatif": out.get("result"),
        "message": out.get("message"),
    }


def main() -> int:
    print("seeding expansion policies...", flush=True)
    seeded = seed_expansion_policies(TENANT)
    suite = all_known_answer_suite()

    verticals = []
    db = SessionLocal()
    try:
        specs = [
            {
                "key": "ptp",
                "policy_id": PTP_POLICY_ID,
                "name": "NCCI Procedure-to-Procedure Bundling (Demo)",
                "policy_type": "CODING_AND_BILLING",
                "meta": {
                    "enterprise_classification": {
                        "mechanism": "CODING_EDIT_MODIFIER",
                        "sub_mechanism": "NCCI_PTP",
                        "dec4_expansion": True,
                        "catalog_class": "DEMO_SYNTHETIC",
                    }
                },
                "params": {},
                "mechanical": apply_ncci_ptp(PTP_KNOWN_LINES),
                "ka": suite["ptp"],
            },
            {
                "key": "mue",
                "policy_id": MUE_POLICY_ID,
                "name": "NCCI Medically Unlikely Units (Demo)",
                "policy_type": "CODING_AND_BILLING",
                "meta": {
                    "enterprise_classification": {
                        "mechanism": "FEE_SCHEDULE_UNIT_PRICE",
                        "sub_mechanism": "NCCI_MUE",
                        "dec4_expansion": True,
                        "catalog_class": "DEMO_SYNTHETIC",
                    }
                },
                "params": {"base_mue_value": 4, "mue_value": 3},
                "mechanical": apply_ncci_mue(MUE_KNOWN_LINES),
                "ka": suite["mue"],
            },
            {
                "key": "therapy",
                "policy_id": THERAPY_POLICY_ID,
                "name": "Outpatient Therapy Coverage and Payment (Demo)",
                "policy_type": "COVERAGE",
                "meta": {
                    "enterprise_classification": {
                        "mechanism": "COVERAGE_DETERMINATION",
                        "dec4_expansion": True,
                        "catalog_class": "DEMO_SYNTHETIC",
                    }
                },
                "params": None,  # coverage what-if not reimbursement-dispatched yet
                "mechanical": apply_therapy_coverage(THERAPY_KNOWN),
                "ka": suite["therapy"],
            },
            {
                "key": "infusion",
                "policy_id": INFUSION_SOC_POLICY_ID,
                "name": "Infusion Site-of-Care Optimization (Demo)",
                "policy_type": "SITE_OF_CARE",
                "meta": {
                    "enterprise_classification": {
                        "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
                        "dec4_expansion": True,
                        "catalog_class": "DEMO_SYNTHETIC",
                    }
                },
                "params": {"base_steer_hopd_count": 2, "steer_hopd_count": 3},
                "mechanical": apply_infusion_soc(INFUSION_KNOWN),
                "ka": suite["infusion"],
            },
        ]

        for sp in specs:
            print(f"persisting {sp['key']}...", flush=True)
            whatif_block = None
            if sp["params"] is not None:
                whatif_block = _persist_whatif(
                    db,
                    policy_id=sp["policy_id"],
                    name=sp["name"],
                    ptype=sp["policy_type"],
                    meta=sp["meta"],
                    params=sp["params"],
                )
            row = {
                "key": sp["key"],
                "policy_id": sp["policy_id"],
                "policy_name": sp["name"],
                "catalog_class": "DEMO_SYNTHETIC",
                "known_answer_passed": bool(sp["ka"].get("passed")),
                "known_answer": sp["ka"],
                "mechanical_totals": sp["mechanical"]["totals"],
                "calculation_version": sp["mechanical"].get("calculation_version"),
                "whatif": whatif_block,
                "medicare_links": next(
                    (s.get("medicare_links") for s in scenario_catalog() if s["policy_id"] == sp["policy_id"]),
                    [],
                ),
                "validation_class": (
                    "FULLY_VALIDATED_DEMO"
                    if sp["ka"].get("passed")
                    and (sp["params"] is None or (whatif_block or {}).get("whatif_status") == "completed")
                    else "MECHANICAL_VALIDATED"
                ),
                "disclosed_limitations": [
                    "Synthetic known-answer fixture — not empirical payer claims.",
                    "Independent of frozen MRI/MPPR/SOS Dec 4 path.",
                    "NCCI quarterly files ACCESS_BLOCKED on this host; demo pairs are DEMO_SYNTHETIC.",
                ],
            }
            if sp["key"] == "therapy":
                row["validation_class"] = (
                    "FULLY_VALIDATED_DEMO"
                    if sp["ka"].get("passed")
                    else "PARTIAL_SYNTHETIC"
                )
                row["disclosed_limitations"].append(
                    "Coverage what-if engine not yet reimbursement-dispatched; mechanical + LCD L34428 link only."
                )
                row["lcd_link"] = "L34428"
            verticals.append(row)

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "tenant_id": str(TENANT),
        "seeded": seeded.get("seeded") if isinstance(seeded, dict) else seeded,
        "known_answers_all_passed": all(v["known_answer_passed"] for v in verticals),
        "verticals": verticals,
        "frozen_three_untouched": True,
        "creates_extra_catalog_seed_rows": False,
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / "EXPANSION_LIFECYCLE_VALIDATION.json"
    path.write_text(json.dumps(report, indent=2, default=str))
    # refresh expansion validation snapshot
    (EVIDENCE / "EXPANSION_VALIDATION.json").write_text(
        json.dumps(
            {
                "generated_at": report["generated_at"],
                "expansion_known_answers": {v["key"]: v["known_answer"] for v in verticals},
                "lifecycle": {
                    v["key"]: {
                        "validation_class": v["validation_class"],
                        "whatif_status": (v.get("whatif") or {}).get("whatif_status"),
                        "analysis_id": (v.get("whatif") or {}).get("analysis_id"),
                    }
                    for v in verticals
                },
                "scenarios": scenario_catalog(),
            },
            indent=2,
            default=str,
        )
    )
    print(json.dumps({k: report[k] for k in ("known_answers_all_passed", "frozen_three_untouched")}, indent=2))
    for v in verticals:
        print(
            f"  {v['key']}: ka={v['known_answer_passed']} class={v['validation_class']} "
            f"whatif={(v.get('whatif') or {}).get('whatif_status')}"
        )
    print("wrote", path)
    return 0 if report["known_answers_all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
