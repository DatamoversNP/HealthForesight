#!/usr/bin/env python3
"""
Seed Q1 2026 demo data: policy-scoped claims (Jan 1 – Mar 31, 2026) + weekly PERIODIC observations.

- Claims use source_system=Q1_2026_DEMO and align LOB/market/CPT with each policy (plus policy_code_sets).
- Markets default to the same concrete set as baseline aggregation (NYC, CHICAGO, LA, DFW).
- Weekly observations aggregate real claims per ISO week via compute_policy_specific_baseline_from_database,
  then enhance_comparisons_with_baseline / enhance_comparisons_with_predicted (same path as run_demo_day).

Run from repo root with DATABASE_URL set (macOS/Linux: use python3):

  python3 scripts/seed_q1_2026_observations_demo.py --tenant-id 00000000-0000-0000-0000-000000000001

Options:
  --purge           Remove prior Q1 demo claims + observations (obs-q1-2026-*) for this tenant/range
  --clear-all-observations-first  Delete ALL observations for the tenant (e.g. after one-per-policy regenerate)
  --claims-only     Load claims only
  --observations-only  Use existing Q1 demo claims; create weekly observations only
  --dry-run         Print plan only

Typical “replace rolling 32 with Q1 weekly” (Azure DB from laptop):
  export DATABASE_URL='postgresql://...'
  python3 scripts/seed_q1_2026_observations_demo.py --tenant-id ... --purge --clear-all-observations-first
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

RANGE_START = date(2026, 1, 1)
RANGE_END = date(2026, 3, 31)
DEMO_INGESTION_ID = UUID("a0000000-0000-4000-8000-000000000126")


def _purge_demo_data(tenant_id: UUID) -> None:
    from uepi_api.database import SessionLocal
    from uepi_api.models.canonical_data import ClaimsLineDB
    from uepi_api.models.observation import Observation

    db = SessionLocal()
    try:
        o_del = (
            db.query(Observation)
            .filter(
                Observation.tenant_id == tenant_id,
                Observation.observation_id.like("obs-q1-2026-%"),
            )
            .delete(synchronize_session=False)
        )
        c_del = (
            db.query(ClaimsLineDB)
            .filter(
                ClaimsLineDB.tenant_id == tenant_id,
                ClaimsLineDB.source_system == "Q1_2026_DEMO",
                ClaimsLineDB.service_date >= RANGE_START,
                ClaimsLineDB.service_date <= RANGE_END,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        print(f"  Purged observations: {o_del}, claims_lines: {c_del}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Q1 2026 demo claims + weekly observations")
    parser.add_argument("--tenant-id", type=str, default="00000000-0000-0000-0000-000000000001")
    parser.add_argument("--purge", action="store_true", help="Delete prior Q1 demo rows then load")
    parser.add_argument(
        "--clear-all-observations-first",
        action="store_true",
        help="Delete every observation for this tenant before seeding (use after one-per-policy regenerate)",
    )
    parser.add_argument("--claims-only", action="store_true")
    parser.add_argument("--observations-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--members", type=int, default=4000, help="Synthetic members in shared pool")
    parser.add_argument("--providers", type=int, default=120, help="Synthetic providers")
    parser.add_argument("--base-claims-per-day", type=int, default=14, help="Scale per policy per day before narrative multiplier")
    args = parser.parse_args()
    tenant_id = UUID(args.tenant_id)

    if args.claims_only and args.observations_only:
        print("Choose at most one of --claims-only / --observations-only")
        sys.exit(1)

    print("=" * 72)
    print("Q1 2026 demo seed")
    print(f"  Tenant: {tenant_id}")
    print(f"  Range:  {RANGE_START} .. {RANGE_END} (weekly observations)")
    print("=" * 72)

    if args.dry_run:
        print("Dry run — no database changes.")
        return

    if args.clear_all_observations_first:
        print("\nDeleting all observations for tenant (clear-all-observations-first)...")
        from uepi_api.storage_observations import delete_all_observations

        n = delete_all_observations(tenant_id)
        print(f"  Deleted {n} observation(s).")

    if args.purge:
        print("\nPurging prior Q1 demo data...")
        _purge_demo_data(tenant_id)

    from uepi_api.database import SessionLocal
    from uepi_api.services.database_baseline_computation import compute_policy_specific_baseline_from_database
    from uepi_api.services.q1_demo_observations import (
        behavioral_hint_for_week,
        enrich_policy_dict_with_code_sets,
        generate_claims_for_policy_date_range,
        iter_iso_week_slices,
        narrative_volume_multiplier,
    )
    from uepi_api.observation_enhancement import (
        enhance_comparisons_with_baseline,
        enhance_comparisons_with_predicted,
    )
    from uepi_api.storage_observations import create_observation
    from uepi_api.storage_policies import get_policy, list_policies
    from uepi_api.storage_policy_predicted_impact import get_predicted_impact

    policies = list_policies(tenant_id) or []
    if not policies:
        print("No policies for tenant. Abort.")
        sys.exit(1)

    member_ids = [f"MEM_Q1_{i:06d}" for i in range(args.members)]
    provider_ids = [f"PROV_Q1_{i:05d}" for i in range(args.providers)]

    db = SessionLocal()
    try:
        if not args.observations_only:
            print("\n--- Loading claims (Q1_2026_DEMO) ---")
            total_claims = 0
            skipped = 0
            for pi, p in enumerate(policies):
                pid = UUID(str(p["id"]))
                raw = get_policy(pid, tenant_id)
                if not raw:
                    skipped += 1
                    continue
                pol = enrich_policy_dict_with_code_sets(db, tenant_id, pid, raw)
                n = generate_claims_for_policy_date_range(
                    db=db,
                    tenant_id=tenant_id,
                    policy_id=pid,
                    policy_dict=pol,
                    range_start=RANGE_START,
                    range_end=RANGE_END,
                    policy_index=pi,
                    member_ids=member_ids,
                    provider_ids=provider_ids,
                    ingestion_id=DEMO_INGESTION_ID,
                    base_claims_per_day=args.base_claims_per_day,
                )
                if n == 0:
                    print(f"  [{pi + 1}/{len(policies)}] {p.get('name', pid)} — skip (no scoping codes)")
                    skipped += 1
                else:
                    total_claims += n
                    print(f"  [{pi + 1}/{len(policies)}] {p.get('name', pid)} — inserted ~{n} claim lines")
            print(f"Done claims. Rows inserted (reported): {total_claims}, policies skipped: {skipped}")

        if args.claims_only:
            return

        print("\n--- Weekly PERIODIC observations ---")
        weeks = list(iter_iso_week_slices(RANGE_START, RANGE_END))
        obs_ok = 0
        obs_skip = 0
        for pi, p in enumerate(policies):
            pid = UUID(str(p["id"]))
            raw = get_policy(pid, tenant_id)
            if not raw:
                continue
            pol = enrich_policy_dict_with_code_sets(db, tenant_id, pid, raw)
            pred = get_predicted_impact(pid, tenant_id)
            if not pred or not (pred.get("metrics") or {}):
                print(f"  {p.get('name', pid)} — skip observations (no predicted impact)")
                obs_skip += len(weeks)
                continue

            scope = pol.get("scope") or (pol.get("metadata") or {}).get("scope") or {}
            from uepi_api.storage_baselines import get_latest_baseline

            baseline_row = get_latest_baseline(tenant_id, policy_id=pid) or get_latest_baseline(
                tenant_id, policy_id=None
            )
            baseline_id = None
            if baseline_row:
                baseline_id = baseline_row.get("id") or baseline_row.get("baseline_id")

            for ws, we, widx in weeks:
                metrics_computed = compute_policy_specific_baseline_from_database(
                    tenant_id=tenant_id,
                    policy_id=pid,
                    start_date=ws,
                    end_date=we,
                    policy_scope=scope if isinstance(scope, dict) else {},
                    db=db,
                    policy=pol,
                )
                if not metrics_computed or int(metrics_computed.get("total_claims") or 0) == 0:
                    obs_skip += 1
                    continue

                observed_util = float(metrics_computed["util_rate_target_per_1000_mm"])
                observed_cost = float(
                    metrics_computed.get("paid_pmpm_target")
                    or metrics_computed.get("allowed_pmpm_target")
                    or 0.0
                )
                bm = baseline_row.get("baseline_metrics", {}) or baseline_row.get("metrics", {}) if baseline_row else {}
                baseline_util = float(
                    bm.get("util_rate_total_per_1000_mm") or bm.get("utilization_per_1k") or 0.0
                )
                baseline_cost = float(
                    bm.get("allowed_pmpm_total") or bm.get("cost_pmpm") or 0.0
                )

                metrics = {
                    "utilization_per_1k": observed_util,
                    "cost_pmpm": observed_cost,
                    "cost_per_member": observed_cost,
                    "baseline_utilization_per_1k": baseline_util,
                    "baseline_cost_pmpm": baseline_cost,
                    "unique_members": metrics_computed.get("unique_members"),
                    "member_months": metrics_computed.get("member_months"),
                    "total_claims": metrics_computed.get("total_claims"),
                    "demo_seed": "q1_2026",
                    "narrative_week_multiplier": narrative_volume_multiplier(pi, widx),
                }

                vs_baseline = enhance_comparisons_with_baseline(
                    tenant_id=tenant_id,
                    observation_metrics=metrics,
                )
                metrics2 = dict(metrics)
                metrics2["baseline_utilization_per_1k"] = vs_baseline.get("baseline_utilization_per_1k")
                metrics2["baseline_cost_pmpm"] = vs_baseline.get("baseline_cost_pmpm")
                vs_predicted = enhance_comparisons_with_predicted(
                    tenant_id=tenant_id,
                    policy_id=pid,
                    observation_metrics=metrics2,
                    prediction_id=None,
                )
                if not vs_predicted:
                    obs_skip += 1
                    continue

                mult = narrative_volume_multiplier(pi, widx)
                behavioral = behavioral_hint_for_week(mult)

                iso = ws.isocalendar()
                obs_id = f"obs-q1-2026-W{iso[1]:02d}-y{iso[0]}-{pid.hex[:8]}"
                period_end_dt = datetime.combine(we, datetime.max.time().replace(microsecond=0))
                period_start_dt = datetime.combine(ws, datetime.min.time())
                computed_at = datetime.now(timezone.utc).replace(tzinfo=None)

                observation_data = {
                    "observation_id": obs_id,
                    "policy_id": str(pid),
                    "policy_version_id": None,
                    "baseline_version_id": str(baseline_id) if baseline_id else None,
                    "prediction_id": None,
                    "analysis_id": None,
                    "data_period_id": None,
                    "data_period_ids": [],
                    "observation_type": "PERIODIC",
                    "observation_period_start": period_start_dt.isoformat() + "Z",
                    "observation_period_end": period_end_dt.isoformat() + "Z",
                    "computed_at": computed_at.isoformat() + "Z",
                    "metrics": metrics2,
                    "comparisons": {"vs_baseline": vs_baseline, "vs_predicted": vs_predicted},
                    "behavioral_explanation": behavioral,
                }
                try:
                    create_observation(tenant_id=tenant_id, observation_data=observation_data)
                    obs_ok += 1
                except Exception as ex:
                    if "unique" in str(ex).lower() or "duplicate" in str(ex).lower():
                        obs_skip += 1
                    else:
                        raise

        print(f"Observations created: {obs_ok}, skipped: {obs_skip}")
    finally:
        db.close()

    print("\nDone. Use GET /observations with date filters or the observation-analysis UI for Q1 2026.")


if __name__ == "__main__":
    main()
