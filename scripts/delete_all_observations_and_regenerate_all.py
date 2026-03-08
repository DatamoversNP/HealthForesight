#!/usr/bin/env python3
"""
Delete all observations for a tenant and regenerate one observation per policy
using revised logic and filters (build_policy_claims_filters, policy-specific baselines,
predicted impact). Same filters as baseline and predicted impact.

Usage:
  python3 scripts/delete_all_observations_and_regenerate_all.py [--tenant-id UUID]
"""
import sys
from pathlib import Path
from uuid import UUID
from datetime import date, timedelta, datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Delete all observations and regenerate for all policies")
    parser.add_argument("--tenant-id", default=str(DEFAULT_TENANT_ID), help="Tenant UUID")
    args = parser.parse_args()

    tenant_id = UUID(args.tenant_id)

    from uepi_api.database import SessionLocal
    from uepi_api.storage_observations import delete_all_observations
    from uepi_api.storage_policies import list_policies, get_policy
    from uepi_api.services.database_baseline_computation import compute_policy_specific_baseline_from_database
    from uepi_api.observation_enhancement import create_observation_from_analysis

    print("=" * 70)
    print("DELETE ALL OBSERVATIONS AND REGENERATE ALL")
    print("=" * 70)

    # Step 1: Delete all observations for tenant
    print("\n1. Deleting all observations...")
    deleted = delete_all_observations(tenant_id)
    print(f"   Deleted {deleted} observations")

    # Step 2: Regenerate one observation per policy (same filters as baseline / predicted impact)
    print("\n2. Regenerating observations for all policies (revised filters, baselines, predicted impact)...")
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    period_start_iso = start_date.isoformat()
    period_end_iso = end_date.isoformat()

    policies_list = list_policies(tenant_id)
    created = 0
    skipped = 0
    errors = 0

    db = SessionLocal()
    try:
        for policy in policies_list:
            policy_id_str = policy.get("id") or policy.get("policy_id")
            policy_name = policy.get("name", "Unknown")
            if not policy_id_str:
                continue
            policy_id = UUID(str(policy_id_str)) if isinstance(policy_id_str, str) else policy_id_str

            try:
                # Compute observed metrics using same logic as baseline (build_policy_claims_filters + aggregate)
                baseline_metrics = compute_policy_specific_baseline_from_database(
                    tenant_id=tenant_id,
                    policy_id=policy_id,
                    start_date=start_date,
                    end_date=end_date,
                    policy_scope=policy.get("scope") or {},
                    db=db,
                    policy=policy,
                )
                if not baseline_metrics:
                    print(f"   Skip (no data): {policy_name}")
                    skipped += 1
                    continue

                # Build analysis_result shape expected by create_observation_from_analysis / extract_metrics_from_analysis_result
                utilization_per_1k = baseline_metrics.get("util_rate_target_per_1000_mm") or baseline_metrics.get("utilization_per_1k", 0.0)
                cost_pmpm = baseline_metrics.get("paid_pmpm_target") or baseline_metrics.get("allowed_pmpm_target") or baseline_metrics.get("cost_pmpm", 0.0)
                analysis_result = {
                    "metrics": {
                        "treatment_post": {
                            "utilization_per_1k": float(utilization_per_1k),
                            "util_rate_per_1k": float(utilization_per_1k),
                            "cost_pmpm": float(cost_pmpm),
                            "paid_pmpm": float(cost_pmpm),
                            "allowed_pmpm": float(baseline_metrics.get("allowed_pmpm_target", 0) or cost_pmpm),
                            "cost_per_member": float(cost_pmpm),
                            "total_claims": int(baseline_metrics.get("total_claims", 0)),
                            "total_paid": float(baseline_metrics.get("total_paid", 0)),
                            "total_allowed": float(baseline_metrics.get("total_allowed", 0)),
                            "member_months": float(baseline_metrics.get("member_months", 0)),
                            "unique_members": int(baseline_metrics.get("unique_members", 0)),
                        }
                    },
                    "post_period": {"start": period_start_iso, "end": period_end_iso},
                }

                obs = create_observation_from_analysis(
                    tenant_id=tenant_id,
                    policy_id=policy_id,
                    analysis_id=None,
                    analysis_result=analysis_result,
                    data_period_id=None,
                )
                if obs:
                    created += 1
                    print(f"   Observation: {policy_name} OK")
                else:
                    errors += 1
                    print(f"   Observation: {policy_name} (create returned None)")
            except Exception as e:
                errors += 1
                print(f"   Observation: {policy_name} ERROR: {e}")

        print(f"\n   Created {created}, skipped (no data) {skipped}, errors {errors} / {len(policies_list)} policies")
    finally:
        db.close()

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
