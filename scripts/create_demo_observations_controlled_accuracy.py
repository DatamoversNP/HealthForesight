#!/usr/bin/env python3
"""
Phase 4.1: Demo mode - create observations with controlled prediction accuracy (e.g. 75-95%).
Given policy, baseline, and predicted impact, computes target observed values that yield
the desired accuracy, then creates observations with vs_predicted and prediction_accuracy_pct.
"""
import argparse
import sys
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timedelta

# Add project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def main():
    parser = argparse.ArgumentParser(description="Create demo observations with controlled prediction accuracy")
    parser.add_argument("--tenant-id", type=str, default=str(DEFAULT_TENANT_ID))
    parser.add_argument("--target-accuracy", type=float, default=85.0, help="Target prediction accuracy 75-95")
    parser.add_argument("--limit", type=int, default=10, help="Max policies to create observations for")
    args = parser.parse_args()
    tenant_id = UUID(args.tenant_id)
    target_acc = max(75.0, min(95.0, args.target_accuracy))
    # Error pct that yields this accuracy: accuracy = 100 - |error_pct| => error_pct = 100 - target_acc
    error_pct = 100.0 - target_acc
    # observed = predicted * (1 + error_pct/100) gives positive error; (1 - error_pct/100) gives negative
    # We use (1 - error_pct/100) so observed is slightly below predicted (e.g. 0.85 for 85% acc)
    factor = 1.0 - (error_pct / 100.0)

    from uepi_api.storage_policy_predicted_impact import get_predicted_impact
    from uepi_api.storage_baselines import get_latest_baseline
    from uepi_api.storage_policies import list_policies
    from uepi_api.observation_enhancement import enhance_comparisons_with_baseline, enhance_comparisons_with_predicted
    from uepi_api.storage_observations import create_observation

    # Get policies from DB (only those we will try - we skip without predicted impact/baseline)
    from uepi_api.database import SessionLocal
    from uepi_api.models.policy import Policy
    db = SessionLocal()
    try:
        policy_rows = db.query(Policy).filter(Policy.tenant_id == tenant_id).limit(args.limit * 3).all()
        policies = [{"id": str(p.id), "policy_id": str(p.id)} for p in policy_rows]
    finally:
        db.close()

    created = 0
    for p in policies[: args.limit]:
        policy_id = UUID(p["id"])
        predicted_impact = get_predicted_impact(policy_id, tenant_id)
        if not predicted_impact or not predicted_impact.get("metrics"):
            continue
        baseline = get_latest_baseline(tenant_id, policy_id=policy_id)
        if not baseline:
            baseline = get_latest_baseline(tenant_id, policy_id=None)
        if not baseline:
            continue
        bm = baseline.get("baseline_metrics") or baseline.get("metrics") or {}
        baseline_util = float(bm.get("util_rate_total_per_1000_mm") or bm.get("utilization_per_1k") or 80.0)
        baseline_cost = float(bm.get("allowed_pmpm_total") or bm.get("cost_pmpm") or 50.0)
        pred_metrics = predicted_impact.get("metrics") or {}
        util_change = float(pred_metrics.get("utilization_change_per_1k") or pred_metrics.get("utilization_change") or -5.0)
        cost_change = float(pred_metrics.get("cost_change_pmpm") or pred_metrics.get("cost_change") or -2.0)
        predicted_util = max(0.0, baseline_util + util_change)
        predicted_cost = max(0.0, baseline_cost + cost_change)
        observed_util = predicted_util * factor if predicted_util > 0 else baseline_util
        observed_cost = predicted_cost * factor if predicted_cost > 0 else baseline_cost

        metrics = {
            "utilization_per_1k": observed_util,
            "cost_pmpm": observed_cost,
            "cost_per_member": observed_cost,
            "baseline_utilization_per_1k": baseline_util,
            "baseline_cost_pmpm": baseline_cost,
        }
        vs_baseline = enhance_comparisons_with_baseline(tenant_id=tenant_id, observation_metrics=metrics)
        metrics_with_baseline = dict(metrics)
        metrics_with_baseline["baseline_utilization_per_1k"] = vs_baseline.get("baseline_utilization_per_1k")
        metrics_with_baseline["baseline_cost_pmpm"] = vs_baseline.get("baseline_cost_pmpm")
        vs_predicted = enhance_comparisons_with_predicted(
            tenant_id=tenant_id, policy_id=policy_id, observation_metrics=metrics_with_baseline, prediction_id=None
        )
        if not vs_predicted:
            continue
        now = datetime.utcnow()
        start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        observation_data = {
            "observation_id": str(uuid4()),
            "policy_id": str(policy_id),
            "policy_version_id": None,
            "baseline_version_id": str(baseline.get("id")) if baseline.get("id") else None,
            "prediction_id": None,
            "analysis_id": None,
            "data_period_id": None,
            "data_period_ids": [],
            "observation_type": "PERIODIC",
            "observation_period_start": start.isoformat() + "Z",
            "observation_period_end": end.isoformat() + "Z",
            "computed_at": now.isoformat() + "Z",
            "metrics": metrics,
            "comparisons": {"vs_baseline": vs_baseline, "vs_predicted": vs_predicted},
            "behavioral_explanation": {},
        }
        try:
            create_observation(tenant_id=tenant_id, observation_data=observation_data)
            acc = vs_predicted.get("prediction_accuracy_pct")
            print(f"   Created observation for policy {str(policy_id)[:8]}... accuracy={acc}%")
            created += 1
        except Exception as e:
            print(f"   Error: {e}")

    print(f"\nCreated {created} demo observations with target accuracy ~{target_acc}%")


if __name__ == "__main__":
    main()
