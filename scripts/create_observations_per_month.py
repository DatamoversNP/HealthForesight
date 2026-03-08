#!/usr/bin/env python3
"""
Phase 6: Create one observation per policy per month for the observation period (July 2025 – present).

Uses the same logic as run_demo_day (create_observation_with_verdict) with configurable period.
Generates a mix of ON_TRACK / AT_RISK / BACKFIRE by (policy_index + month_index) % 3.

Run from repo root:
  python3 scripts/create_observations_per_month.py [--tenant-id UUID] [--start 2025-07-01] [--end YYYY-MM-DD]
"""
import argparse
import sys
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timedelta, date, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
VERDICT_KINDS = ["ON_TRACK", "AT_RISK", "BACKFIRE"]


def create_observation_for_month(
    tenant_id: UUID,
    policy_id: UUID,
    policy_name: str,
    period_start: date,
    period_end: date,
    verdict_kind: str,
) -> bool:
    """Create one observation for a policy for the given month (period_start..period_end)."""
    from uepi_api.storage_policy_predicted_impact import get_predicted_impact
    from uepi_api.storage_baselines import get_latest_baseline
    from uepi_api.observation_enhancement import enhance_comparisons_with_baseline, enhance_comparisons_with_predicted
    from uepi_api.storage_observations import create_observation

    baseline = get_latest_baseline(tenant_id, policy_id=policy_id, baseline_type=None)
    if not baseline:
        baseline = get_latest_baseline(tenant_id, policy_id=None)
    if not baseline:
        return False
    predicted_impact = get_predicted_impact(policy_id, tenant_id)
    if not predicted_impact or not predicted_impact.get("metrics"):
        return False

    bm = baseline.get("baseline_metrics") or baseline.get("metrics") or {}
    baseline_util = float(bm.get("util_rate_total_per_1000_mm") or bm.get("utilization_per_1k") or 80.0)
    baseline_cost = float(bm.get("allowed_pmpm_total") or bm.get("cost_pmpm") or 50.0)
    pred_metrics = predicted_impact.get("metrics") or {}
    util_change = float(pred_metrics.get("utilization_change_per_1k") or pred_metrics.get("utilization_change") or -5.0)
    cost_change = float(pred_metrics.get("cost_change_pmpm") or pred_metrics.get("cost_change") or -2.0)
    predicted_util = max(0.0, baseline_util + util_change)
    predicted_cost = max(0.0, baseline_cost + cost_change)

    if verdict_kind == "ON_TRACK":
        factor = 1.0
        behavioral = {}
    elif verdict_kind == "AT_RISK":
        factor = 1.18
        behavioral = {}
    else:
        factor = 1.25
        behavioral = {
            "risk_factors": ["Provider substitution to unmanaged settings", "Patient delay in seeking care"],
            "recommendations": ["Review prior auth criteria", "Monitor ED utilization"],
        }

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
        tenant_id=tenant_id,
        policy_id=policy_id,
        observation_metrics=metrics_with_baseline,
        prediction_id=None,
    )
    if not vs_predicted:
        return False

    now = datetime.now(timezone.utc)
    # Use isoformat() only; do not append "Z" or storage's replace("Z","+00:00") produces ...+00:00+00:00
    computed_at_str = now.isoformat()
    observation_data = {
        "observation_id": str(uuid4()),
        "policy_id": str(policy_id),
        "policy_version_id": None,
        "baseline_version_id": baseline.get("id") or baseline.get("baseline_id"),
        "prediction_id": None,
        "analysis_id": None,
        "data_period_id": None,
        "data_period_ids": [],
        "observation_type": "PERIODIC",
        "observation_period_start": period_start.isoformat() + "T00:00:00Z",
        "observation_period_end": period_end.isoformat() + "T23:59:59Z",
        "computed_at": computed_at_str,
        "metrics": metrics,
        "comparisons": {"vs_baseline": vs_baseline, "vs_predicted": vs_predicted},
        "behavioral_explanation": behavioral,
    }
    try:
        create_observation(tenant_id=tenant_id, observation_data=observation_data)
        return True
    except Exception as e:
        print(f"    Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Create one observation per policy per month (July 2025 - present)")
    parser.add_argument("--tenant-id", type=str, default=str(DEFAULT_TENANT_ID))
    parser.add_argument("--start", type=str, default="2025-07-01", help="First month YYYY-MM-DD (first day of month)")
    parser.add_argument("--end", type=str, default=None, help="Last month YYYY-MM-DD (default: current month)")
    args = parser.parse_args()
    tenant_id = UUID(args.tenant_id)
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end) if args.end else date.today()
    # Normalize to first day of month
    start = start.replace(day=1)
    end = end.replace(day=1)

    from uepi_api.storage_policies import list_policies

    policies = list_policies(tenant_id) or []
    if not policies:
        print("No policies found. Run Phase 4 first.")
        sys.exit(1)

    print("=" * 60)
    print("PHASE 6: Create observations per month")
    print("=" * 60)
    print(f"Tenant: {tenant_id}")
    print(f"Months: {start} to {end}")
    print(f"Policies: {len(policies)}")
    print()

    months = []
    d = start
    while d <= end:
        months.append(d)
        if d.month == 12:
            d = d.replace(year=d.year + 1, month=1)
        else:
            d = d.replace(month=d.month + 1)

    total = 0
    for mi, month_start in enumerate(months):
        last_day = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        period_end = last_day
        print(f"Month {month_start.strftime('%Y-%m')} ({period_end})...")
        for pi, policy in enumerate(policies):
            pid = policy.get("id") or policy.get("policy_id")
            if not pid:
                continue
            if isinstance(pid, str):
                try:
                    pid = UUID(pid)
                except ValueError:
                    continue
            name = (policy.get("name") or policy.get("policy_name") or str(pid))[:40]
            verdict_kind = VERDICT_KINDS[(pi + mi) % len(VERDICT_KINDS)]
            if create_observation_for_month(tenant_id, pid, name, month_start, period_end, verdict_kind):
                total += 1
        print(f"  Created observations for {len(policies)} policies")
    print()
    print("=" * 60)
    print(f"Phase 6 complete. Total observations created: {total}")
    print("=" * 60)


if __name__ == "__main__":
    main()
