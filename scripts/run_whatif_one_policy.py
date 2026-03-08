#!/usr/bin/env python3
"""Run what-if analysis for one policy end-to-end (synchronously, no Celery)."""
import sys
import os
import argparse
from pathlib import Path
from uuid import UUID

# Project root and path setup
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "apps" / "worker" / "src"))

# Use same DB as API; avoid importing uepi_worker.tasks (circular import with main)

from uepi_api.database import SessionLocal
from uepi_api.models.analysis import (
    Analysis,
    AnalysisStatus,
    AnalysisType,
    AnalysisConfig,
    WhatIfScenarioResult,
)
from uepi_api.models.policy import Policy
from uepi_api.services.policy_scoped_data_generation import build_policy_claims_filters

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def run_whatif_sync(tenant_id: UUID, policy_id: UUID, scenario_params: dict | None = None):
    """Create a SIMULATE analysis for one policy and run whatif_scenario_job synchronously."""
    scenario_params = scenario_params or {
        "lever_adjustments": {},
        "elasticity_adjustments": {},
        "member_count_multiplier": 1.0,
        "utilization_trend": 0.0,
        "cost_inflation": 0.02,
        "projection_months": 12,
    }
    db = SessionLocal()
    try:
        policy = db.query(Policy).filter(
            Policy.id == policy_id,
            Policy.tenant_id == tenant_id,
        ).first()
        if not policy:
            print(f"   Policy {policy_id} not found for tenant {tenant_id}")
            return None

        meta = getattr(policy, "policy_metadata_json", None) or {}
        policy_dict = {
            "scope": meta.get("scope", {}),
            "policy_levers": meta.get("policy_levers", []),
            "logic": meta.get("logic", {}),
            "policy_logic": meta.get("policy_logic", {}),
        }
        baseline_filters = build_policy_claims_filters(policy_dict)
        worker_filters = {
            "lob": baseline_filters.get("lob"),
            "markets": baseline_filters.get("markets")
            or ([baseline_filters["market"]] if baseline_filters.get("market") else None),
            "market": baseline_filters.get("market"),
            "cpt_codes": baseline_filters.get("cpt_codes") or baseline_filters.get("procedure_codes"),
            "service_categories": baseline_filters.get("service_categories"),
            "diagnosis_codes": baseline_filters.get("diagnosis_codes"),
        }
        worker_filters = {k: v for k, v in worker_filters.items() if v is not None}

        analysis = Analysis(
            tenant_id=tenant_id,
            policy_id=policy_id,
            analysis_type=AnalysisType.SIMULATE.value,
            status=AnalysisStatus.PENDING.value,
            created_by=None,
        )
        db.add(analysis)
        db.flush()

        config = AnalysisConfig(
            tenant_id=tenant_id,
            analysis_id=analysis.id,
            treatment_filters=worker_filters,
            control_filters=None,
            matching_strategy=None,
            pre_window_months=0,
            post_window_months=0,
        )
        db.add(config)
        db.commit()
        db.refresh(analysis)

        analysis_id = analysis.id
        print(f"   Created analysis {analysis_id} (SIMULATE) for policy {policy.name[:50]}")

        # Run shared what-if logic (no Celery/worker import - avoids circular import)
        from uepi_api.services.whatif_runner import run_whatif_scenario_sync

        result = run_whatif_scenario_sync(
            tenant_id=str(tenant_id),
            analysis_id=str(analysis_id),
            policy_id=str(policy_id),
            scenario_params=scenario_params,
            baseline_filters=worker_filters,
            db=None,  # runner creates and closes its own session
        )

        # Task uses its own session; read result with a fresh session
        whatif_row = None
        db2 = SessionLocal()
        try:
            analysis = db2.query(Analysis).filter(Analysis.id == analysis_id).first()
            status = analysis.status if analysis else "UNKNOWN"
            err_msg = getattr(analysis, "error_message", None) if analysis else None

            if status == AnalysisStatus.COMPLETED.value:
                whatif_row = (
                    db2.query(WhatIfScenarioResult)
                    .filter(WhatIfScenarioResult.analysis_id == analysis_id)
                    .first()
                )
        finally:
            db2.close()
        if status == AnalysisStatus.COMPLETED.value:
            if whatif_row and whatif_row.result_data_json:
                data = whatif_row.result_data_json
                print(f"   Status: {status}")
                print(f"   Baseline metrics: {data.get('baseline_metrics', {})}")
                print(f"   Projected metrics: {data.get('projected_metrics', {})}")
                print(f"   Impact metrics: {data.get('impact_metrics', {})}")
                return {"analysis_id": str(analysis_id), "status": status, "result": data}
            print(f"   Status: {status} (no result row yet)")
            return {"analysis_id": str(analysis_id), "status": status}
        else:
            print(f"   Status: {status}")
            if err_msg:
                print(f"   Error: {err_msg}")
            return {"analysis_id": str(analysis_id), "status": status, "error_message": err_msg, "result": result}
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Run what-if analysis for one policy (e2e, sync)")
    parser.add_argument(
        "--tenant-id",
        type=str,
        default=str(DEFAULT_TENANT_ID),
        help="Tenant UUID",
    )
    parser.add_argument(
        "--policy-id",
        type=str,
        default=None,
        help="Policy UUID (default: first policy for tenant)",
    )
    args = parser.parse_args()

    tenant_id = UUID(args.tenant_id)
    db = SessionLocal()
    try:
        if args.policy_id:
            policy_id = UUID(args.policy_id)
            policy = db.query(Policy).filter(
                Policy.id == policy_id,
                Policy.tenant_id == tenant_id,
            ).first()
            if not policy:
                print(f"Policy {args.policy_id} not found")
                sys.exit(1)
        else:
            policy = db.query(Policy).filter(Policy.tenant_id == tenant_id).first()
            if not policy:
                print("No policies found for tenant. Create a policy first.")
                sys.exit(1)
            policy_id = policy.id

        print(f"Policy: {policy.name} ({policy_id})")
    finally:
        db.close()

    print("\n" + "=" * 60)
    print("What-If Analysis (one policy, end-to-end)")
    print("=" * 60 + "\n")

    out = run_whatif_sync(tenant_id, policy_id)
    print("\n" + "=" * 60)
    if out and out.get("status") == AnalysisStatus.COMPLETED.value:
        print("Done. What-if analysis completed successfully.")
    elif out:
        print(f"Done. Status: {out.get('status')}")
    else:
        print("Done. Run failed (see errors above).")
    print("=" * 60)


if __name__ == "__main__":
    main()
