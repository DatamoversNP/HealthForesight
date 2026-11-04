"""Enterprise intelligence APIs — composable policy, causal, behavior, cold-start, applicability.

Demonstration catalog: Representative Payer Policies (Blue Cross NC-like).
Authoritative catalog: public CMS NCD/LCD/articles/NCCI when acquired.
"""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from uepi_api.auth import CurrentUser, verify_token
from uepi_api.services import enterprise_intelligence_fixtures as fix
from uepi_api.storage_policies import get_policy, list_policies

router = APIRouter(prefix="/enterprise", tags=["Enterprise Intelligence"])


@router.get("/feasibility")
async def feasibility_summary(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Short feasibility snapshot for Dec 4 readiness (see docs/demo/bcbs-nc/DEC4_FEASIBILITY_AND_GAP.md)."""
    inv = fix.implementation_inventory()
    return {
        "demo_target": "2026-12-04",
        "p0": [
            "composable_policy",
            "causal_impact_workbench",
            "provider_behavior_explorer",
            "cold_start_forecast",
            "medicare_reimbursement_applicability",
            "unified_verdict_evidence",
        ],
        "production_qualified": inv["production_qualified"],
        "reason_not_production_qualified": inv["reason_not_production_qualified"],
        "capabilities": inv["capabilities"],
        "data_notes": {
            "behavior_profiles_rows": "often empty in demo DB — fixtures used",
            "claims_lines": "present but too large for interactive counts — use fixtures/aggregates",
            "causal_engine": "DiD available; workbench uses labeled synthetic validation series for MRI",
        },
        "rules": [
            "Never label naive pre/post as causal",
            "Never infer provider intent",
            "Never auto-adjudicate from NCD/LCD",
            "Label synthetic fixtures explicitly",
            "Do not collapse forecast / causal / governance into one opaque score",
        ],
    }


@router.get("/implementation-inventory")
async def get_implementation_inventory(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Honest real-vs-fixture inventory for Dec 4 validation gate."""
    return fix.implementation_inventory()


@router.get("/coverage-manifest")
async def get_coverage_manifest(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Reconciled-or-explicitly-incomplete policy inventory coverage manifest."""
    import asyncio
    from uepi_api.services.policy_inventory_manifest import load_coverage_manifest

    return await asyncio.to_thread(load_coverage_manifest, current_user.tenant_id)


@router.get("/analytical-strategies")
async def get_analytical_strategies(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Mechanism → engine registry (reimbursement must not default to UM elasticity)."""
    from uepi_api.services.analytical_strategy_registry import (
        PAYMENT_SIGN_CONVENTION,
        REGISTRY_VERSION,
        list_strategies,
    )

    return {
        "registry_version": REGISTRY_VERSION,
        "sign_convention": PAYMENT_SIGN_CONVENTION,
        "strategies": list_strategies(),
    }


@router.get("/medicare-rules")
async def list_medicare_rules(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    kind: str | None = Query(None),
    q: str | None = Query(None),
):
    """Independent Medicare NCD/LCD/article/NCCI/payment rule explorer feed."""
    import asyncio
    from uepi_api.services.medicare_rules import list_medicare_rules as _list

    return await asyncio.to_thread(_list, current_user.tenant_id, kind=kind, q=q)


@router.post("/medicare-rules/seed-mri-links")
async def seed_mri_medicare_links(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Link MRI Representative Payer policy to ingested public Medicare example docs."""
    import asyncio
    from uepi_api.services.medicare_rules import seed_mri_medicare_links as _seed

    return await asyncio.to_thread(_seed, current_user.tenant_id)


@router.get("/policies/{policy_id}/applicable-medicare-rules")
async def get_applicable_medicare_rules(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    program: str = Query("Original Medicare FFS"),
    state: str = Query("North Carolina"),
    as_of: str = Query("2024-06-01"),
):
    """Applicable Medicare rules for a payer policy + program/jurisdiction resolution."""
    import asyncio
    from uuid import UUID
    from uepi_api.services.medicare_rules import applicable_medicare_rules_for_policy

    return await asyncio.to_thread(
        applicable_medicare_rules_for_policy,
        current_user.tenant_id,
        UUID(policy_id),
        program=program,
        state=state,
        as_of=as_of,
    )


@router.get("/medicare-rules/mri-clinical-applicability")
async def get_mri_clinical_applicability(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    as_of: str = Query("2024-06-01"),
):
    """Clinical applicability of Medicare authorities to Outpatient MRI PA (beyond jurisdiction)."""
    import asyncio
    from uepi_api.services.clinical_applicability import mri_pa_clinical_bundle

    return await asyncio.to_thread(mri_pa_clinical_bundle, as_of)


@router.get("/policies/{policy_id}/causal-feasibility")
async def get_causal_feasibility(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Cross-domain causal feasibility (estimate only when identifiable)."""
    import asyncio
    from uuid import UUID
    from uepi_api.database import SessionLocal
    from uepi_api.models.policy import Policy
    from uepi_api.services.causal_feasibility import assess_for_demo_policy

    def _load():
        db = SessionLocal()
        try:
            pol = (
                db.query(Policy)
                .filter(Policy.id == UUID(policy_id), Policy.tenant_id == current_user.tenant_id)
                .first()
            )
            if not pol:
                raise HTTPException(status_code=404, detail="Policy not found")
            return assess_for_demo_policy(
                str(pol.id),
                pol.name,
                pol.policy_type,
                pol.policy_metadata_json,
            )
        finally:
            db.close()

    return await asyncio.to_thread(_load)


@router.post("/demo-expansion/seed")
async def seed_demo_expansion(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Seed P0 expansion scenarios (does not modify frozen MRI/MPPR/SOS)."""
    import asyncio
    from uepi_api.services.expansion_demo_scenarios import seed_expansion_policies

    return await asyncio.to_thread(seed_expansion_policies, current_user.tenant_id)


@router.get("/demo-expansion/verticals")
async def get_demo_expansion_verticals(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Known-answer suite for NCCI PTP/MUE, therapy, infusion SOC + NCD/LCD study cards."""
    import asyncio
    from uepi_api.services.expansion_demo_scenarios import (
        INFUSION_SOC_POLICY_ID,
        LCD_COVERAGE_POLICY_ID,
        MUE_POLICY_ID,
        NCD_COVERAGE_POLICY_ID,
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
        scenario_catalog,
    )
    from uepi_api.services.reimbursement_whatif import run_reimbursement_whatif
    from uepi_api.services.enterprise_intelligence_fixtures import policy_composition
    from uepi_api.services.causal_feasibility import assess_for_demo_policy

    def _whatif_summary(out: dict) -> dict:
        result = out.get("result") or {}
        impact = result.get("impact_metrics") or {}
        return {
            "status": out.get("status"),
            "message": out.get("message"),
            "delta_payer_savings": impact.get("delta_payer_savings"),
            "delta_payment_impact": impact.get("delta_payment_impact"),
            "baseline_metrics": result.get("baseline_metrics"),
            "projected_metrics": result.get("projected_metrics"),
            "impact_metrics": impact,
            "limitations": result.get("limitations"),
            "catalog_class": result.get("catalog_class"),
        }

    def _load():
        suite = all_known_answer_suite()
        ptp_wf = run_reimbursement_whatif(
            policy_type="CODING_AND_BILLING",
            policy_name="NCCI Procedure-to-Procedure Bundling",
            metadata={
                "enterprise_classification": {
                    "mechanism": "CODING_EDIT_MODIFIER",
                    "sub_mechanism": "NCCI_PTP",
                    "catalog_class": "DEMO_SYNTHETIC",
                }
            },
            policy_id=PTP_POLICY_ID,
            scenario_params={},
        )
        mue_wf = run_reimbursement_whatif(
            policy_type="CODING_AND_BILLING",
            policy_name="NCCI Medically Unlikely Units",
            metadata={
                "enterprise_classification": {
                    "mechanism": "FEE_SCHEDULE_UNIT_PRICE",
                    "sub_mechanism": "NCCI_MUE",
                    "catalog_class": "DEMO_SYNTHETIC",
                }
            },
            policy_id=MUE_POLICY_ID,
            scenario_params={"base_mue_value": 4, "mue_value": 3},
        )
        infusion_wf = run_reimbursement_whatif(
            policy_type="SITE_OF_CARE",
            policy_name="Infusion Site-of-Care Optimization",
            metadata={
                "enterprise_classification": {
                    "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
                    "catalog_class": "DEMO_SYNTHETIC",
                }
            },
            policy_id=INFUSION_SOC_POLICY_ID,
            scenario_params={"base_steer_hopd_count": 2, "steer_hopd_count": 3},
        )
        ncd_name = "NCD 220.2 MRI Coverage Change Study"
        lcd_name = "LCD L34425 NC MRI Coverage Criteria"
        return {
            "catalog_class": "DEMO_SYNTHETIC",
            "frozen_three_untouched": True,
            "scenarios": scenario_catalog(),
            "known_answers": suite,
            "mechanical_totals": {
                "ptp": apply_ncci_ptp(PTP_KNOWN_LINES)["totals"],
                "mue": apply_ncci_mue(MUE_KNOWN_LINES)["totals"],
                "therapy": apply_therapy_coverage(THERAPY_KNOWN)["totals"],
                "infusion": apply_infusion_soc(INFUSION_KNOWN)["totals"],
            },
            "what_ifs": {
                "ptp": {
                    **_whatif_summary(ptp_wf),
                    "label": "Modifier indicator 1→0 (no bypass)",
                    "expected_delta_payer_savings": 400.0,
                },
                "mue": {
                    **_whatif_summary(mue_wf),
                    "label": "Synthetic MUE threshold 4→3",
                    "expected_delta_payer_savings": 100.0,
                },
                "therapy": {
                    "status": "NOT_SUPPORTED_FOR_THIS_MECHANISM",
                    "message": "Coverage what-if is not reimbursement-dispatched; mechanical KA $80 is the supported demo stage.",
                    "delta_payer_savings": None,
                    "expected_delta_payer_savings": None,
                },
                "infusion": {
                    **_whatif_summary(infusion_wf),
                    "label": "Steer HOPD episodes 2→3",
                    "expected_delta_payer_savings": 1800.0,
                },
            },
            "studies": {
                "ncd": {
                    "policy_id": NCD_COVERAGE_POLICY_ID,
                    "study_class": "PROVENANCE_ONLY",
                    "financial_baseline": "N/A",
                    "causal_estimate": "N/A",
                    "composition": policy_composition(NCD_COVERAGE_POLICY_ID, ncd_name, "COVERAGE_STUDY"),
                    "causal_feasibility": assess_for_demo_policy(
                        NCD_COVERAGE_POLICY_ID, ncd_name, "COVERAGE_STUDY"
                    ),
                    "demo_talking_points": [
                        "Versioned NCD 220.2 source applicability for Medicare FFS reference",
                        "Commercial inheritance unsigned — study finding only",
                        "Do not manufacture financial or causal estimates",
                    ],
                },
                "lcd": {
                    "policy_id": LCD_COVERAGE_POLICY_ID,
                    "study_class": "PROVENANCE_ONLY",
                    "financial_baseline": "N/A",
                    "causal_estimate": "N/A",
                    "composition": policy_composition(LCD_COVERAGE_POLICY_ID, lcd_name, "COVERAGE_STUDY"),
                    "causal_feasibility": assess_for_demo_policy(
                        LCD_COVERAGE_POLICY_ID, lcd_name, "COVERAGE_STUDY"
                    ),
                    "demo_talking_points": [
                        "Palmetto JM LCD L34425 + article A56729 for orbit/face/neck only",
                        "Never apply to lumbar 72148/49/58",
                        "Do not manufacture financial impact",
                    ],
                },
            },
            "policy_ids": {
                "ptp": PTP_POLICY_ID,
                "mue": MUE_POLICY_ID,
                "therapy": THERAPY_POLICY_ID,
                "infusion": INFUSION_SOC_POLICY_ID,
                "ncd": NCD_COVERAGE_POLICY_ID,
                "lcd": LCD_COVERAGE_POLICY_ID,
            },
            "demo_expectations": {
                "ptp": {"payer_savings": 800.0, "whatif_delta": 400.0},
                "mue": {"payer_savings": 100.0, "whatif_delta": 100.0},
                "therapy": {"payer_savings": 80.0, "whatif_status": "NOT_SUPPORTED_FOR_THIS_MECHANISM"},
                "infusion": {"payer_savings": 3600.0, "whatif_delta": 1800.0},
                "ncd": {"study_class": "PROVENANCE_ONLY"},
                "lcd": {"study_class": "PROVENANCE_ONLY"},
            },
            "all_mechanical_passed": all(v.get("passed") for v in suite.values()),
        }

    return await asyncio.to_thread(_load)


@router.get("/reimbursement/sos-vertical")
async def get_sos_reimbursement_vertical(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Site-of-service payment differential known-answer vertical."""
    import asyncio
    import json
    from pathlib import Path
    from uepi_api.services.reimbursement_sos import (
        CALC_VERSION,
        KNOWN_ANSWER_LINES,
        apply_sos,
        verify_known_answer,
    )
    from uepi_api.services.analytical_strategy_registry import PAYMENT_SIGN_CONVENTION
    from uepi_api.services.reimbursement_whatif import run_reimbursement_whatif

    def _load():
        ka = verify_known_answer()
        calc = apply_sos(KNOWN_ANSWER_LINES)
        whatif = run_reimbursement_whatif(
            policy_type="SITE_OF_CARE",
            policy_name="Freestanding Imaging Steerage",
            metadata={
                "enterprise_classification": {
                    "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL"
                }
            },
            policy_id="d7441dd9-3bfe-405e-ae6c-0377204bbb7e",
            scenario_params={"base_hospital_pct": 0.80, "hospital_pct": 0.70},
        )
        evidence_path = (
            Path(__file__).resolve().parents[5]
            / "docs"
            / "demo"
            / "bcbs-nc"
            / "evidence"
            / "SOS_REIMBURSEMENT_VERTICAL.json"
        )
        seeded = None
        if evidence_path.exists():
            try:
                seeded = json.loads(evidence_path.read_text())
            except Exception:
                seeded = None
        return {
            "calculation_version": CALC_VERSION,
            "policy_id": "d7441dd9-3bfe-405e-ae6c-0377204bbb7e",
            "policy_name": "Freestanding Imaging Steerage",
            "sign_convention": PAYMENT_SIGN_CONVENTION,
            "known_answer_checks": ka,
            "totals": calc["totals"],
            "what_if_80_to_70": whatif.get("result"),
            "seeded_evidence": seeded,
            "fully_validated_demo": bool(ka.get("passed"))
            and bool(seeded and seeded.get("validation_class") == "FULLY_VALIDATED_DEMO"),
            "catalog_class": "DEMO_SYNTHETIC",
        }

    return await asyncio.to_thread(_load)


@router.get("/reimbursement/mppr-vertical")
async def get_mppr_reimbursement_vertical(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Deterministic MPPR payment-impact vertical (known-answer). Not UM elasticity."""
    import asyncio
    from pathlib import Path
    import json
    from uepi_api.services.reimbursement_mppr import (
        KNOWN_ANSWER_LINES,
        apply_mppr,
        verify_known_answer,
        CALC_VERSION,
    )
    from uepi_api.services.analytical_strategy_registry import PAYMENT_SIGN_CONVENTION
    from uepi_api.services.reimbursement_whatif import run_reimbursement_whatif

    def _load():
        ka = verify_known_answer()
        calc = apply_mppr(KNOWN_ANSWER_LINES)
        whatif = run_reimbursement_whatif(
            policy_type="PAYMENT_POLICY",
            policy_name=fix.REIMBURSEMENT_POLICY_NAME,
            metadata={
                "enterprise_classification": {
                    "mechanism": "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION"
                }
            },
            policy_id=fix.MPPR_POLICY_ID,
            scenario_params={"base_secondary_pct": 0.5, "secondary_pct": 0.4},
        )
        evidence_path = (
            Path(__file__).resolve().parents[5]
            / "docs"
            / "demo"
            / "bcbs-nc"
            / "evidence"
            / "MPPR_REIMBURSEMENT_VERTICAL.json"
        )
        seeded = None
        if evidence_path.exists():
            try:
                seeded = json.loads(evidence_path.read_text())
            except Exception:
                seeded = None
        return {
            "calculation_version": CALC_VERSION,
            "catalog_class": "DEMO_SYNTHETIC",
            "display_label": "Representative Payer Policies",
            "policy_id": fix.MPPR_POLICY_ID,
            "policy_name": fix.REIMBURSEMENT_POLICY_NAME,
            "sign_convention": PAYMENT_SIGN_CONVENTION,
            "known_answer_checks": ka,
            "totals": calc["totals"],
            "rule": calc["rule"],
            "not_claiming": calc["not_claiming"],
            "what_if_50_to_40": whatif.get("result"),
            "seeded_evidence": seeded,
            "fully_validated_demo": bool(ka.get("passed"))
            and bool(seeded and seeded.get("validation_class") == "FULLY_VALIDATED_DEMO"),
        }

    return await asyncio.to_thread(_load)


@router.post("/policy-sources/reconcile")
async def reconcile_policy_sources(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Run declared-family source adapters and persist inventory/documents.

    Representative Payer (Blue Cross NC-like) families load DEMO_SYNTHETIC catalog
    rows — not proprietary Blue Cross NC content. Authoritative CMS/NCCI families
    stay NOT_ATTEMPTED until exports/API pulls succeed. Creating workspace policies
    from ingested documents is a separate preconfigure step.
    """
    import asyncio
    from uepi_api.services.policy_sources import reconcile_all_families

    return await asyncio.to_thread(reconcile_all_families, current_user.tenant_id)


@router.get("/policy-sources/inventory")
async def get_policy_source_inventory(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Persisted source-family reconciliation rows (authoritative inventory status)."""
    import asyncio
    from uepi_api.database import SessionLocal
    from uepi_api.models.policy_source import PolicySourceDocument, PolicySourceInventory

    def _load():
        db = SessionLocal()
        try:
            rows = (
                db.query(PolicySourceInventory)
                .filter(PolicySourceInventory.tenant_id == current_user.tenant_id)
                .order_by(PolicySourceInventory.family_id)
                .all()
            )
            docs_n = (
                db.query(PolicySourceDocument)
                .filter(PolicySourceDocument.tenant_id == current_user.tenant_id)
                .count()
            )
            return {
                "tenant_id": str(current_user.tenant_id),
                "source_document_count": docs_n,
                "families": [
                    {
                        "family_id": r.family_id,
                        "adapter_status": r.adapter_status,
                        "discovered_count": r.discovered_count,
                        "ingested_count": r.ingested_count,
                        "excluded_count": r.excluded_count,
                        "inaccessible_count": r.inaccessible_count,
                        "failed_count": r.failed_count,
                        "last_reconciled_at": r.last_reconciled_at.isoformat()
                        if r.last_reconciled_at
                        else None,
                        "notes": r.notes,
                        "scope": r.scope_declaration_json,
                    }
                    for r in rows
                ],
                "complete": bool(rows)
                and all(
                    r.adapter_status in ("INGESTED_FROM_DROP", "INGESTED_FROM_API")
                    and (r.discovered_count or 0) > 0
                    for r in rows
                ),
            }
        finally:
            db.close()

    return await asyncio.to_thread(_load)


@router.get("/policy-population/coverage")
async def get_policy_population_coverage(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Enterprise coverage dashboard counts from DB + source inventory (no invented completeness)."""
    import asyncio
    import json
    from pathlib import Path
    from uepi_api.database import SessionLocal
    from uepi_api.models.policy import Policy
    from uepi_api.models.policy_source import PolicySourceInventory
    from sqlalchemy import func

    def _load():
        # routers/ → uepi_api → src → api → apps → repo root
        audit_path = (
            Path(__file__).resolve().parents[5]
            / "docs"
            / "demo"
            / "bcbs-nc"
            / "evidence"
            / "POLICY_INVENTORY_283_AUDIT.json"
        )
        audit_summary = None
        if audit_path.exists():
            try:
                audit_summary = json.loads(audit_path.read_text()).get("summary")
            except Exception:
                audit_summary = None

        db = SessionLocal()
        try:
            n_policies = (
                db.query(func.count(Policy.id))
                .filter(Policy.tenant_id == current_user.tenant_id)
                .scalar()
            )
            illustrative = 0
            for (meta,) in (
                db.query(Policy.policy_metadata_json)
                .filter(Policy.tenant_id == current_user.tenant_id)
                .all()
            ):
                if isinstance(meta, dict):
                    ec = meta.get("enterprise_classification") or {}
                    if ec.get("not_verbatim_bcbsnc_policy") or ec.get("data_classification") == "illustrative_catalog":
                        illustrative += 1
            inv_rows = (
                db.query(PolicySourceInventory)
                .filter(PolicySourceInventory.tenant_id == current_user.tenant_id)
                .all()
            )
            return {
                "catalog_policies": n_policies,
                "illustrative_catalog_flagged": illustrative,
                "authoritative_source_documents": sum(r.ingested_count or 0 for r in inv_rows),
                "source_families": [
                    {
                        "family_id": r.family_id,
                        "adapter_status": r.adapter_status,
                        "discovered": r.discovered_count,
                        "ingested": r.ingested_count,
                        "inaccessible": r.inaccessible_count,
                    }
                    for r in inv_rows
                ],
                "lifecycle_audit_summary": audit_summary,
                "catalog_views": {
                    "demonstration_policies_default": "Representative Payer Policies",
                    "demonstration_policies_contextual": "Representative Payer Policies (Blue Cross NC-like)",
                    "authoritative_policies": "Public CMS NCD/LCD/articles/NCCI when acquired",
                },
                "dec4_population_ready": False,
                "reason": (
                    "Demonstration uses Representative Payer Policies (Blue Cross NC-like synthetic); "
                    "authoritative public CMS/NCCI inventory not yet acquired/reconciled. "
                    "Does not require Blue Cross NC authorization."
                ),
            }
        finally:
            db.close()

    return await asyncio.to_thread(_load)


@router.get("/analytical-readiness")
async def get_analytical_readiness(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Portfolio analytical readiness flags — independent of catalog completeness."""
    import asyncio
    from uepi_api.services.policy_analytical_readiness import load_portfolio_readiness

    return await asyncio.to_thread(load_portfolio_readiness, current_user.tenant_id)


@router.get("/reconciliation-gate")
async def get_reconciliation_gate(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Per-policy coverage + analytical readiness explanations (no invented evidence)."""
    import asyncio
    from uepi_api.services.policy_reconciliation_gate import load_reconciliation_gate

    return await asyncio.to_thread(load_reconciliation_gate, current_user.tenant_id)


@router.get("/policies/{policy_id}/reconciliation-gate")
async def get_policy_reconciliation_gate(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    from uepi_api.services.policy_reconciliation_gate import load_reconciliation_gate

    gate = load_reconciliation_gate(current_user.tenant_id)
    for row in gate.get("policies") or []:
        if str(row.get("policy_id")) == str(policy_id):
            return row
    raise HTTPException(status_code=404, detail="Policy not found in reconciliation gate")


@router.get("/causal/validation-suite")
async def get_causal_validation_suite(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Known-effect / no-effect / confounded / parallel-trend-violation checks."""
    return fix.causal_validation_suite()


@router.get("/policies/{policy_id}/definition-package")
async def get_policy_definition_package(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Read-only v1.2 definition package (docs) — review surface, not activation."""
    from uepi_api.services.policy_definition_package import load_definition_package

    return load_definition_package(policy_id)


@router.get("/policies/{policy_id}/composition")
async def get_policy_composition(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    policy = get_policy(policy_id, current_user.tenant_id)
    if not policy:
        # Still return composition template for known demo IDs
        if policy_id != fix.MRI_POLICY_ID:
            raise HTTPException(status_code=404, detail="Policy not found")
        return fix.policy_composition(policy_id, "Outpatient MRI Prior Authorization", "PRIOR_AUTH")
    return fix.policy_composition(
        str(policy.get("id") or policy_id),
        policy.get("name") or policy.get("policy_name"),
        policy.get("policy_type"),
    )


@router.get("/policies/{policy_id}/causal-impact")
async def get_causal_impact(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Causal Impact Workbench payload. MRI uses validated synthetic DiD fixture."""
    if policy_id == fix.MRI_POLICY_ID:
        return fix.mri_causal_impact()
    # For other policies: descriptive-only until empirical design is available
    return {
        "policy_id": policy_id,
        "fixture_id": "descriptive_only",
        "labeled_synthetic": False,
        "method": "descriptive",
        "formula": "(Y_T,post - Y_T,pre) - (Y_C,post - Y_C,pre)",
        "unit": {
            "code": "UNSPECIFIED",
            "description": "No validated outcome unit until comparison design is configured.",
        },
        "outcome": "Utilization / cost (policy observation)",
        "denominator": "Policy-eligible membership",
        "treatment_definition": "Members/services under this policy",
        "comparison_population": "Not yet configured",
        "observed_change": None,
        "expected_change_without_policy": None,
        "estimated_incremental_effect": None,
        "uncertainty_interval": {},
        "diagnostics": {"status": "INSUFFICIENT_DESIGN"},
        "external_factors": [],
        "evidence_classification": "INCONCLUSIVE",
        "limitations": [
            "No validated comparison design for this policy yet.",
            "Do not interpret observation pre/post deltas as causal effects.",
        ],
        "series": [],
        "known_true_effect": None,
        "recovered_within_tolerance": None,
        "implementation_class": "NOT_ESTIMABLE",
    }


@router.get("/policies/{policy_id}/provider-behavior")
async def get_provider_behavior(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    return fix.provider_behavior_panel(policy_id)


@router.get("/policies/{policy_id}/cold-start")
async def get_cold_start(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    policy = get_policy(policy_id, current_user.tenant_id)
    name = (policy or {}).get("name") or (policy or {}).get("policy_name") or "New policy"
    return fix.cold_start_forecast(policy_id, name)


@router.get("/policies/{policy_id}/verdict-evidence")
async def get_verdict_evidence(
    policy_id: str,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    observation_verdict: Optional[str] = Query(None),
):
    """Unified policy impact verdict evidence — three independent assessments."""
    policy = get_policy(policy_id, current_user.tenant_id)
    if not policy and policy_id != fix.MRI_POLICY_ID:
        raise HTTPException(status_code=404, detail="Policy not found")
    name = None
    ctype = None
    if policy:
        name = policy.get("name") or policy.get("policy_name")
        ctype = policy.get("policy_type")
    elif policy_id == fix.MRI_POLICY_ID:
        name = "Outpatient MRI Prior Authorization"
        ctype = "PRIOR_AUTH"
    return fix.unified_verdict_evidence(
        policy_id,
        name,
        ctype,
        observation_verdict=observation_verdict,
    )


@router.get("/applicability/resolve")
async def resolve_applicability(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    program: str = Query("Original Medicare FFS"),
    state: str = Query("North Carolina"),
    service_category: Optional[str] = Query("Advanced imaging / MRI"),
    as_of: str = Query("2024-06-01"),
):
    """Jurisdiction / source applicability explorer — not claim adjudication."""
    return fix.resolve_applicability(
        program=program,
        state=state,
        service_category=service_category,
        as_of=as_of,
    )


@router.get("/demo-pack")
async def enterprise_demo_pack(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Bundle used by Dec 4 rehearsal — MRI causal + applicability + cold-start specialty + verdict."""
    policies = list_policies(current_user.tenant_id) or []
    specialty = next(
        (
            p
            for p in policies
            if "Specialty Drug Site-of-Administration" in str(p.get("name") or "")
        ),
        None,
    )
    coding = next(
        (p for p in policies if "Modifier and Code-Bundling" in str(p.get("name") or "")),
        None,
    )
    specialty_id = str((specialty or {}).get("id") or "specialty-demo")
    coding_id = str((coding or {}).get("id") or "coding-demo")
    return {
        "storyline": [
            "One platform, different policy shapes",
            "Did the policy cause the change?",
            "How did providers respond?",
            "What about a new policy?",
            "Medicare / local rules / NCCI",
            "Unified verdict evidence",
        ],
        "implementation_inventory": fix.implementation_inventory(),
        "causal_validation_suite": fix.causal_validation_suite(),
        "mri": {
            "policy_id": fix.MRI_POLICY_ID,
            "composition": fix.policy_composition(
                fix.MRI_POLICY_ID, "Outpatient MRI Prior Authorization", "PRIOR_AUTH"
            ),
            "causal": fix.mri_causal_impact(),
            "behavior": fix.provider_behavior_panel(fix.MRI_POLICY_ID),
            "verdict_evidence": fix.unified_verdict_evidence(
                fix.MRI_POLICY_ID,
                "Outpatient MRI Prior Authorization",
                "PRIOR_AUTH",
                observation_verdict="ON_TRACK",
            ),
        },
        "reimbursement_mppr": {
            "policy_id": getattr(fix, "MPPR_POLICY_ID", None) or coding_id,
            "policy_name": fix.REIMBURSEMENT_POLICY_NAME,
            "composition": fix.policy_composition(
                getattr(fix, "MPPR_POLICY_ID", coding_id),
                fix.REIMBURSEMENT_POLICY_NAME,
                getattr(fix, "REIMBURSEMENT_POLICY_TYPE", "PAYMENT_POLICY"),
            ),
            "verdict_evidence": fix.unified_verdict_evidence(
                getattr(fix, "MPPR_POLICY_ID", coding_id),
                fix.REIMBURSEMENT_POLICY_NAME,
                getattr(fix, "REIMBURSEMENT_POLICY_TYPE", "PAYMENT_POLICY"),
            ),
            "note": "Payment-rule vertical (not UM elasticity). Prefer seeded known-answer evidence.",
        },
        "reimbursement_coding": {
            "policy_id": coding_id,
            "composition": fix.policy_composition(
                coding_id, "Modifier and Code-Bundling Claim Edit Policy", "CODING_AND_BILLING"
            ),
            "verdict_evidence": fix.unified_verdict_evidence(
                coding_id, "Modifier and Code-Bundling Claim Edit Policy", "CODING_AND_BILLING"
            ),
            "note": "Schema lacks modifiers — coding-edit analytics blocked; use MPPR for Dec 4 reimbursement demo.",
        },
        "cold_start": fix.cold_start_forecast(specialty_id, fix.NEW_POLICY_NAME),
        "cold_start_verdict": fix.unified_verdict_evidence(
            specialty_id, fix.NEW_POLICY_NAME, "SPECIALTY_PHARMACY"
        ),
        "applicability": {
            "ffs_nc": fix.resolve_applicability("Original Medicare FFS", "North Carolina"),
            "ma": fix.resolve_applicability("Medicare Advantage", "North Carolina"),
            "commercial": fix.resolve_applicability("Commercial", "North Carolina"),
            "superseded": fix.resolve_applicability(
                "Original Medicare FFS", "North Carolina", as_of="2022-01-01"
            ),
            "no_match_state": fix.resolve_applicability("Original Medicare FFS", "California"),
        },
    }
