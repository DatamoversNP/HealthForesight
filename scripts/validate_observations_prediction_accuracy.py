#!/usr/bin/env python3
"""
Phase 5.2: Validation script for observation prediction accuracy.
Lists policies with observations; for each observation checks:
- Predicted impact exists for policy
- Baseline exists and is non-zero
- vs_predicted and prediction_accuracy_pct are present
Outputs a report and list of failing policies/observations.
"""
import os
import sys
from pathlib import Path
from uuid import UUID

# Add project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def main():
    from uepi_api.storage_observations import list_observations
    from uepi_api.storage_policy_predicted_impact import get_predicted_impact
    from uepi_api.storage_baselines import get_latest_baseline

    tenant_id = DEFAULT_TENANT_ID
    print("=" * 60)
    print("Phase 5.2: Validation - Observation Prediction Accuracy")
    print("=" * 60)

    observations = list_observations(tenant_id=tenant_id)
    if not observations:
        print("No observations found.")
        return

    report = {
        "total_observations": len(observations),
        "ok": 0,
        "missing_vs_predicted": [],
        "missing_prediction_accuracy_pct": [],
        "missing_predicted_impact": [],
        "missing_baseline": [],
        "zero_baseline": [],
    }

    for obs in observations:
        observation_id = obs.get("observation_id")
        policy_id_raw = obs.get("policy_id")
        policy_id = None
        if policy_id_raw:
            try:
                policy_id = UUID(policy_id_raw) if isinstance(policy_id_raw, str) else policy_id_raw
            except Exception:
                pass

        comparisons = obs.get("comparisons") or {}
        vs_predicted = comparisons.get("vs_predicted") or {}
        vs_baseline = comparisons.get("vs_baseline") or {}

        fail = False
        if not vs_predicted:
            report["missing_vs_predicted"].append({"observation_id": observation_id, "policy_id": policy_id_raw})
            fail = True
        elif vs_predicted.get("prediction_accuracy_pct") is None:
            report["missing_prediction_accuracy_pct"].append({"observation_id": observation_id, "policy_id": policy_id_raw})
            fail = True

        if policy_id:
            predicted_impact = get_predicted_impact(policy_id, tenant_id)
            if not predicted_impact or not predicted_impact.get("metrics"):
                report["missing_predicted_impact"].append({"observation_id": observation_id, "policy_id": str(policy_id)})
                fail = True

        baseline = get_latest_baseline(tenant_id, policy_id=policy_id)
        if not baseline:
            baseline = get_latest_baseline(tenant_id, policy_id=None)
        if not baseline:
            report["missing_baseline"].append({"observation_id": observation_id, "policy_id": policy_id_raw})
            fail = True
        else:
            bm = baseline.get("baseline_metrics") or baseline.get("metrics") or {}
            # Align with storage keys: policy-specific (target) and tenant-level (total)
            util = (
                bm.get("util_rate_target_per_1000_mm")
                or bm.get("util_rate_total_per_1000_mm")
                or bm.get("utilization_per_1k")
                or 0
            )
            cost = (
                bm.get("allowed_pmpm_target")
                or bm.get("paid_pmpm_target")
                or bm.get("allowed_pmpm_total")
                or bm.get("paid_pmpm_total")
                or bm.get("cost_pmpm")
                or bm.get("allowed_pmpm")
                or 0
            )
            try:
                util = float(util) if util is not None else 0.0
            except (TypeError, ValueError):
                util = 0.0
            try:
                cost = float(cost) if cost is not None else 0.0
            except (TypeError, ValueError):
                cost = 0.0
            if util == 0 and cost == 0:
                report["zero_baseline"].append({"observation_id": observation_id, "policy_id": policy_id_raw})
                fail = True

        if not fail:
            report["ok"] += 1

    print(f"\nTotal observations: {report['total_observations']}")
    print(f"OK (all checks passed): {report['ok']}")
    print(f"Missing vs_predicted: {len(report['missing_vs_predicted'])}")
    print(f"Missing prediction_accuracy_pct: {len(report['missing_prediction_accuracy_pct'])}")
    print(f"Missing predicted impact for policy: {len(report['missing_predicted_impact'])}")
    print(f"Missing baseline: {len(report['missing_baseline'])}")
    print(f"Zero baseline: {len(report['zero_baseline'])}")

    if report["missing_vs_predicted"]:
        print("\n--- Observations missing vs_predicted ---")
        for x in report["missing_vs_predicted"][:20]:
            print(f"  {x['observation_id']} (policy {x['policy_id']})")
        if len(report["missing_vs_predicted"]) > 20:
            print(f"  ... and {len(report['missing_vs_predicted']) - 20} more")
    if report["missing_prediction_accuracy_pct"]:
        print("\n--- Observations missing prediction_accuracy_pct ---")
        for x in report["missing_prediction_accuracy_pct"][:20]:
            print(f"  {x['observation_id']} (policy {x['policy_id']})")
        if len(report["missing_prediction_accuracy_pct"]) > 20:
            print(f"  ... and {len(report['missing_prediction_accuracy_pct']) - 20} more")
    if report["missing_predicted_impact"]:
        print("\n--- Policies missing predicted impact ---")
        seen = set()
        for x in report["missing_predicted_impact"]:
            if x["policy_id"] not in seen:
                seen.add(x["policy_id"])
                print(f"  policy_id: {x['policy_id']}")
    if report["missing_baseline"]:
        print("\n--- Observations with missing baseline ---")
        for x in report["missing_baseline"][:10]:
            print(f"  {x['observation_id']}")
    if report["zero_baseline"]:
        print("\n--- Observations with zero baseline ---")
        for x in report["zero_baseline"][:10]:
            print(f"  {x['observation_id']}")

    print("\n" + "=" * 60)
    if report["ok"] == report["total_observations"]:
        print("All observations passed validation.")
    else:
        print(f"Validation complete. {report['total_observations'] - report['ok']} observation(s) have issues.")
    print("=" * 60)


if __name__ == "__main__":
    main()
