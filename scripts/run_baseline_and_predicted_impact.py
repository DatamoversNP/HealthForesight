#!/usr/bin/env python3
"""
Phase 4: Run baseline refresh and predicted impact for all policies (fresh demo).

After historical data is loaded (Phase 3), run this to:
1. Create general (tenant-level) baseline first
2. Create policy-specific baselines (one per policy)
3. Using each policy’s baseline, generate and store predicted impact for all policies

Observations (Phase 7) use these baselines and predicted impacts.

Run from repo root:
  python3 scripts/run_baseline_and_predicted_impact.py [--tenant-id UUID]
"""
import argparse
import sys
from pathlib import Path
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def main():
    parser = argparse.ArgumentParser(description="Run baseline refresh and predicted impact for all policies")
    parser.add_argument("--tenant-id", type=str, default=str(DEFAULT_TENANT_ID))
    args = parser.parse_args()
    tenant_id = UUID(args.tenant_id)

    from uepi_api.database import SessionLocal
    from uepi_api.storage_policies import list_policies, get_policy
    from uepi_api.baseline_refresh import refresh_baseline
    from uepi_api.storage_baselines import get_latest_baseline
    from uepi_api.routers.policy_predicted_impact import generate_predicted_impact_for_policy
    from uepi_api.storage_policy_predicted_impact import store_predicted_impact

    db = SessionLocal()
    print("=" * 60)
    print("PHASE 4: Baseline refresh + Predicted impact")
    print("=" * 60)
    print(f"Tenant: {tenant_id}")
    print()

    policies = list_policies(tenant_id)
    if not policies:
        print("No policies found. Creating tenant-level baseline only.")
        baseline = refresh_baseline(
            tenant_id=tenant_id,
            policy_id=None,
            baseline_type="ROLLING",
            window_months=12,
            refresh_reason="FRESH_DEMO",
            db=db,
        )
        if baseline:
            print(f"  Tenant baseline created: {baseline.get('baseline_id')}")
        else:
            print("  Tenant baseline creation returned None (no data periods or DB compute failed)")
        db.close()
        print()
        print("Phase 4 complete (tenant baseline only).")
        return

    # 0. General (tenant-level) baseline first
    print("0. Creating general (tenant-level) baseline...")
    general_b = refresh_baseline(
        tenant_id=tenant_id,
        policy_id=None,
        baseline_type="ROLLING",
        window_months=12,
        refresh_reason="FRESH_DEMO",
        db=db,
    )
    if general_b:
        print(f"   General baseline created: {general_b.get('baseline_id', 'ok')}")
    else:
        print("   General baseline: none (no data or compute failed)")

    # 1. Policy-specific baselines (one per policy)
    print()
    print("1. Refreshing policy-specific baselines (one per policy)...")
    for i, policy in enumerate(policies):
        pid = policy.get("id") or policy.get("policy_id")
        if not pid:
            continue
        if isinstance(pid, str):
            try:
                pid = UUID(pid)
            except ValueError:
                continue
        name = (policy.get("name") or policy.get("policy_name") or str(pid))[:40]
        b = refresh_baseline(
            tenant_id=tenant_id,
            policy_id=pid,
            baseline_type="ROLLING",
            window_months=12,
            refresh_reason="FRESH_DEMO",
            db=db,
        )
        if b:
            print(f"   [{i+1}/{len(policies)}] {name}: baseline {b.get('baseline_id', 'ok')}")
        else:
            print(f"   [{i+1}/{len(policies)}] {name}: no baseline (no data or error)")

    # 2. Predicted impact per policy
    print()
    print("2. Generating and storing predicted impact per policy...")
    for i, policy in enumerate(policies):
        pid = policy.get("id") or policy.get("policy_id")
        if not pid:
            continue
        name = (policy.get("name") or policy.get("policy_name") or str(pid))[:40]
        policy_levers = policy.get("policy_levers") or policy.get("metadata", {}).get("policy_levers") or []
        if not policy_levers and policy.get("policy_type"):
            policy_levers = [{"type": policy.get("policy_type"), "parameters": {}}]
        if not policy_levers:
            policy_levers = [{"type": "PRIOR_AUTH", "parameters": {}}]
        policy_scope = policy.get("scope") or {}
        try:
            result = generate_predicted_impact_for_policy(
                tenant_id=tenant_id,
                policy_id=pid,
                policy_levers=policy_levers,
                policy_scope=policy_scope,
                baseline_metrics=None,
            )
        except Exception as e:
            print(f"   [{i+1}/{len(policies)}] {name}: generate failed – {e}")
            continue
        result_dict = result.model_dump(mode="json") if hasattr(result, "model_dump") else {}
        if not result_dict:
            print(f"   [{i+1}/{len(policies)}] {name}: no result dict")
            continue
        baseline = get_latest_baseline(tenant_id, policy_id=pid if isinstance(pid, UUID) else UUID(str(pid)), baseline_type=None)
        if baseline:
            result_dict["baseline_id"] = baseline.get("id") or baseline.get("baseline_id")
        stored = store_predicted_impact(pid, tenant_id, result_dict)
        if stored:
            print(f"   [{i+1}/{len(policies)}] {name}: stored predicted impact")
        else:
            print(f"   [{i+1}/{len(policies)}] {name}: store failed")

    db.close()
    print()
    print("=" * 60)
    print("Phase 4 complete: general baseline, policy baselines, predicted impact.")
    print("Next: Phase 5 (observation-period data), Phase 6 (load it), Phase 7 (run observations).")
    print("=" * 60)


if __name__ == "__main__":
    main()
