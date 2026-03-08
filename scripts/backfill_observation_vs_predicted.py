#!/usr/bin/env python3
"""
Phase 3.2: Backfill vs_predicted and prediction_accuracy_pct for existing observations.
Loads all observations, for each calls enhance_comparisons_with_predicted with
observation_metrics (including baseline from vs_baseline), writes updated comparisons_json to DB.
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
    from uepi_api.storage_observations import list_observations, update_observation
    from uepi_api.observation_enhancement import enhance_comparisons_with_predicted

    tenant_id = DEFAULT_TENANT_ID
    print("=" * 60)
    print("Phase 3.2: Backfill vs_predicted for existing observations")
    print("=" * 60)

    observations = list_observations(tenant_id=tenant_id)
    if not observations:
        print("No observations found.")
        return

    print(f"Found {len(observations)} observations")
    updated = 0
    skipped = 0
    errors = 0

    for i, obs in enumerate(observations):
        observation_id = obs.get("observation_id")
        policy_id_raw = obs.get("policy_id")
        if not policy_id_raw:
            print(f"   [{i+1}] Skip {observation_id}: no policy_id")
            skipped += 1
            continue
        try:
            policy_id = UUID(policy_id_raw) if isinstance(policy_id_raw, str) else policy_id_raw
        except Exception:
            print(f"   [{i+1}] Skip {observation_id}: invalid policy_id")
            skipped += 1
            continue

        metrics = obs.get("metrics") or {}
        comparisons = dict(obs.get("comparisons") or {})

        # If vs_predicted already has prediction_accuracy_pct, optionally skip
        existing_vp = comparisons.get("vs_predicted") or {}
        if existing_vp and existing_vp.get("prediction_accuracy_pct") is not None:
            skipped += 1
            continue

        # Build observation_metrics with baseline so enhance_comparisons_with_predicted can compute
        metrics_with_baseline = dict(metrics)
        vb = comparisons.get("vs_baseline") or {}
        if vb.get("baseline_utilization_per_1k") is not None:
            metrics_with_baseline["baseline_utilization_per_1k"] = vb["baseline_utilization_per_1k"]
        if vb.get("baseline_cost_pmpm") is not None:
            metrics_with_baseline["baseline_cost_pmpm"] = vb["baseline_cost_pmpm"]

        vs_predicted = enhance_comparisons_with_predicted(
            tenant_id=tenant_id,
            policy_id=policy_id,
            observation_metrics=metrics_with_baseline,
            prediction_id=None,
        )
        if not vs_predicted:
            print(f"   [{i+1}] No vs_predicted for {observation_id} (policy {policy_id_raw[:8]}...)")
            errors += 1
            continue

        comparisons["vs_predicted"] = vs_predicted
        result = update_observation(tenant_id=tenant_id, observation_id=observation_id, updates={"comparisons": comparisons})
        if result:
            acc = vs_predicted.get("prediction_accuracy_pct")
            print(f"   [{i+1}] Updated {observation_id[:8]}... accuracy={acc}")
            updated += 1
        else:
            errors += 1

    print()
    print("=" * 60)
    print(f"Updated: {updated}, Skipped: {skipped}, Errors: {errors}")
    print("=" * 60)


if __name__ == "__main__":
    main()
