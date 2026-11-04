#!/usr/bin/env python3
"""
Monday demo seed — 5 spotlight policies, Jan–Jul 2026 claims + 7 incremental observations.

Policies:
  - Outpatient MRI Prior Authorization
  - Physical Therapy Visit Limit
  - Cardiac CT Angiography Prior Authorization
  - PCP Referral Requirement for Specialist Visits
  - Breast MRI Medical Necessity Criteria

Observation ends (cumulative from 2026-01-01):
  2026-01-31, 02-28, 03-31, 04-30, 05-31, 06-30, 07-31

Requires DATABASE_URL (Azure Postgres). Bypasses App Service.

  export DATABASE_URL='postgresql://...'
  /tmp/hf_seed_venv/bin/python scripts/demo/seed_monday_demo_5_policies.py
  /tmp/hf_seed_venv/bin/python scripts/demo/seed_monday_demo_5_policies.py --replace
"""
from __future__ import annotations

import hashlib
import os
import random
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "common" / "src"))

TENANT = UUID("00000000-0000-0000-0000-000000000001")
EFFECTIVE = date(2026, 1, 1)
SOURCE = "MONDAY_DEMO_5"
CLAIMS_PER_MONTH = 2500

POLICY_NAMES = [
    "Outpatient MRI Prior Authorization",
    "Physical Therapy Visit Limit",
    "Cardiac CT Angiography Prior Authorization",
    "PCP Referral Requirement for Specialist Visits",
    "Breast MRI Medical Necessity Criteria",
]

# 7 incremental month-ends Jan–Jul 2026
OBS_ENDS = [
    date(2026, 1, 31),
    date(2026, 2, 28),
    date(2026, 3, 31),
    date(2026, 4, 30),
    date(2026, 5, 31),
    date(2026, 6, 30),
    date(2026, 7, 31),
]


def _require_db() -> None:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url or "YOURSERVER" in url:
        raise SystemExit("Set DATABASE_URL to Azure Postgres connection string")
    os.environ["DATABASE_URL"] = url


def _set_timeout(db, ms: int = 900_000) -> None:
    from sqlalchemy import text

    try:
        db.execute(text(f"SET statement_timeout = {int(ms)}"))
        db.commit()
    except Exception:
        db.rollback()


def _month_days(year: int, month: int) -> list[date]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    days = []
    d = start
    while d < end:
        days.append(d)
        d += timedelta(days=1)
    return days


def _spread(policy_id: str, metrics: dict[str, Any], month_idx: int) -> dict[str, Any]:
    """Per-policy + progressive month drift for a visible 7-point trend."""
    digest = hashlib.sha256(policy_id.encode()).hexdigest()
    h = int(digest[:8], 16) % 100
    # Base trajectory: mild savings early → mixed mid → some drift late
    # month_idx 0..6
    drift = 0.97 - (month_idx * 0.01) + ((h % 7) * 0.002)  # ~0.97 → ~0.91
    if h >= 70:
        drift = 1.02 + (month_idx * 0.015)  # rising / at-risk story
    elif h >= 40:
        drift = 0.95 + (month_idx * 0.008)
    out = dict(metrics)
    for k in ("utilization_per_1k", "cost_pmpm", "cost_per_member", "paid_pmpm"):
        if out.get(k) is not None:
            out[k] = round(float(out[k]) * drift * (0.98 + (h % 5) * 0.005), 4 if "util" in k else 2)
    out["month_drift"] = round(drift, 4)
    return out


def _window_metrics(db, tenant_id: UUID, start: date, end: date) -> dict[str, Any]:
    from sqlalchemy import func
    from uepi_api.models.canonical_data import ClaimsLineDB

    _set_timeout(db)
    row = (
        db.query(
            func.count(ClaimsLineDB.id).label("total_claims"),
            func.coalesce(func.sum(ClaimsLineDB.paid_amount), 0).label("total_paid"),
            func.coalesce(func.sum(ClaimsLineDB.allowed_amount), 0).label("total_allowed"),
            func.count(func.distinct(ClaimsLineDB.member_id)).label("unique_members"),
        )
        .filter(
            ClaimsLineDB.tenant_id == tenant_id,
            ClaimsLineDB.service_date >= start,
            ClaimsLineDB.service_date <= end,
        )
        .one()
    )
    total_claims = int(row.total_claims or 0)
    total_paid = float(row.total_paid or 0)
    members = max(1, int(row.unique_members or 0))
    months = max(1, round(max(1, (end - start).days) / 30.0))
    mm = float(members * months)
    paid_pmpm = total_paid / mm if mm else 0.0
    util = (total_claims / mm * 1000.0) if mm else 0.0
    return {
        "utilization_per_1k": float(util),
        "cost_pmpm": float(paid_pmpm),
        "cost_per_member": float(paid_pmpm),
        "paid_pmpm": float(paid_pmpm),
        "total_claims": total_claims,
        "unique_members": members,
        "member_months": mm,
    }


def _ensure_month_claims(db, tenant_id: UUID, year: int, month: int, n: int) -> int:
    """Spread ~n claims across days in the month (idempotent-ish via SOURCE + month tag)."""
    from sqlalchemy import func
    from uepi_api.models.canonical_data import ClaimsLineDB
    from uepi_api.repositories.canonical_data import CanonicalDataRepository

    days = _month_days(year, month)
    start, end = days[0], days[-1]
    existing = (
        db.query(func.count(ClaimsLineDB.id))
        .filter(
            ClaimsLineDB.tenant_id == tenant_id,
            ClaimsLineDB.source_system == SOURCE,
            ClaimsLineDB.service_date >= start,
            ClaimsLineDB.service_date <= end,
        )
        .scalar()
        or 0
    )
    if int(existing) >= n // 2:
        print(f"    claims {start}..{end}: {existing} (skip generate)", flush=True)
        return 0

    random.seed(year * 100 + month)
    cats = {
        "PRIMARY_CARE": {"codes": ["99213", "99214"], "avg": 150.0},
        "SPECIALTY_CARE": {"codes": ["99243", "99244"], "avg": 300.0},
        "ADVANCED_IMAGING": {"codes": ["70450", "72141", "77046", "77047"], "avg": 900.0},
        "REHAB": {"codes": ["97110", "97140"], "avg": 120.0},
        "LABORATORY": {"codes": ["80053", "85025"], "avg": 50.0},
    }
    rows = []
    for i in range(n):
        svc = random.choice(days)
        cat = random.choice(list(cats.keys()))
        info = cats[cat]
        allowed = info["avg"] * random.uniform(0.75, 1.35)
        paid = allowed * random.uniform(0.82, 0.98)
        rows.append(
            {
                "tenant_id": tenant_id,
                "claim_id": f"MD5_{year}{month:02d}_{i:06d}",
                "claim_line_id": f"MD5_{year}{month:02d}_{i:06d}_01",
                "member_id": f"MEM_{(i % 4000):06d}",
                "provider_id": f"PROV_{(i % 180):05d}",
                "service_date": svc,
                "paid_date": svc + timedelta(days=random.randint(3, 25)),
                "lob": random.choice(["COMMERCIAL", "MEDICARE", "MEDICAID"]),
                "market": random.choice(["CA", "TX", "NY", "FL", "NC"]),
                "cpt_code": random.choice(info["codes"]),
                "hcpcs_code": "",
                "service_category": cat,
                "place_of_service": random.choice(["11", "22", "23"]),
                "units": 1.0,
                "allowed_amount": float(allowed),
                "paid_amount": float(paid),
                "member_cost_share": float(max(0.0, allowed - paid)),
                "in_network": True,
                "system_affiliation": random.choice(["HOSPITAL_SYSTEM_A", "INDEPENDENT"]),
                "facility_type": "CLINIC",
                "source_system": SOURCE,
                "source_file_id": f"monday_demo_{year}_{month:02d}",
                "ingestion_id": UUID("00000000-0000-4000-8000-0000000000d5"),
            }
        )
    repo = CanonicalDataRepository(db)
    loaded = repo.bulk_insert_claims_lines(
        tenant_id=tenant_id,
        claims_data=rows,
        source_system=SOURCE,
        source_file_id=f"monday_demo_{year}_{month:02d}",
        ingestion_id=UUID("00000000-0000-4000-8000-0000000000d5"),
    )
    db.commit()
    print(f"    inserted {loaded} claims for {start}..{end}", flush=True)
    return int(loaded or 0)


def _load_policies(db, tenant_id: UUID, *, all_policies: bool) -> list[dict]:
    from uepi_api.models.policy import Policy as PolicyDB

    rows = (
        db.query(PolicyDB.id, PolicyDB.name, PolicyDB.status)
        .filter(PolicyDB.tenant_id == tenant_id, PolicyDB.status == "ACTIVE")
        .all()
    )
    if all_policies:
        return [
            {"id": str(r.id), "name": r.name, "effective_date": EFFECTIVE}
            for r in sorted(rows, key=lambda x: (x.name or "").lower())
        ]

    out = []
    for r in rows:
        if any(n.lower() in (r.name or "").lower() for n in POLICY_NAMES):
            for n in POLICY_NAMES:
                if (r.name or "").strip().lower() == n.lower() or n.lower() in (r.name or "").lower():
                    out.append({"id": str(r.id), "name": r.name, "effective_date": EFFECTIVE})
                    break
    by_id = {p["id"]: p for p in out}
    ordered = []
    for n in POLICY_NAMES:
        hit = next((p for p in by_id.values() if n.lower() in p["name"].lower()), None)
        if hit and hit not in ordered:
            ordered.append(hit)
    return ordered


def _load_predicted_pcts(db, tenant_id: UUID) -> dict[str, tuple[float, float]]:
    """One query for all predicted impacts — avoid N× get_predicted_impact round-trips."""
    out: dict[str, tuple[float, float]] = {}
    try:
        from uepi_api.models.predicted_impact import PolicyPredictedImpact

        rows = (
            db.query(PolicyPredictedImpact)
            .filter(PolicyPredictedImpact.tenant_id == tenant_id)
            .all()
        )
        for r in rows:
            m = getattr(r, "metrics_json", None) or getattr(r, "result_json", None) or {}
            if not isinstance(m, dict):
                continue
            inner = m.get("metrics") if isinstance(m.get("metrics"), dict) else m
            cost_pct = float(inner.get("cost_change_pct") or -8.0)
            util_pct = float(inner.get("utilization_change_pct") or -6.0)
            pid = str(getattr(r, "policy_id", "") or "")
            if pid:
                out[pid] = (cost_pct, util_pct)
    except Exception as e:
        print(f"  warn: predicted cache load failed ({e}); using defaults", flush=True)
    print(f"  predicted-impact cache: {len(out)} policies", flush=True)
    return out


def _predicted_levels(
    cache: dict[str, tuple[float, float]],
    policy_id: UUID,
    base_cost: float,
    base_util: float,
) -> tuple[float, float]:
    cost_pct, util_pct = cache.get(str(policy_id), (-8.0, -6.0))
    return base_cost * (1.0 + cost_pct / 100.0), base_util * (1.0 + util_pct / 100.0)


def _replace_obs(db, tenant_id: UUID, policy_ids: list[UUID], ends: list[date]) -> int:
    from uepi_api.models.observation import Observation

    deleted = 0
    for pid in policy_ids:
        for end in ends:
            start_dt = datetime.combine(end, datetime.min.time())
            end_dt = datetime.combine(end, datetime.max.time().replace(microsecond=0))
            q = db.query(Observation).filter(
                Observation.tenant_id == tenant_id,
                Observation.policy_id == pid,
                Observation.observation_period_end >= start_dt,
                Observation.observation_period_end <= end_dt,
            )
            # also monday demo ids
            n = q.delete(synchronize_session=False)
            deleted += int(n or 0)
            n2 = (
                db.query(Observation)
                .filter(
                    Observation.tenant_id == tenant_id,
                    Observation.policy_id == pid,
                    Observation.observation_id.like(f"obs-mon-{end.strftime('%Y%m%d')}-%"),
                )
                .delete(synchronize_session=False)
            )
            deleted += int(n2 or 0)
    db.commit()
    return deleted


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--replace", action="store_true", help="Delete existing obs on these ends for selected policies first")
    ap.add_argument("--all-policies", action="store_true", help="Seed every ACTIVE policy (not just the 5 spotlight ones)")
    ap.add_argument("--claims-per-month", type=int, default=CLAIMS_PER_MONTH)
    ap.add_argument("--observations-only", action="store_true")
    args = ap.parse_args()

    _require_db()
    from uepi_api.database import SessionLocal
    from uepi_api.models.observation import Observation

    print("=" * 72, flush=True)
    scope = "ALL ACTIVE policies" if args.all_policies else "5 spotlight policies"
    print(f"Monday demo — {scope} × 7 monthly observations (Jan–Jul 2026)", flush=True)
    print(f"  Ends: {[d.isoformat() for d in OBS_ENDS]}", flush=True)
    print("=" * 72, flush=True)

    db = SessionLocal()
    try:
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        _set_timeout(db)
        print("  DB ok", flush=True)

        policies = _load_policies(db, TENANT, all_policies=args.all_policies)
        print(f"  Matched policies: {len(policies)}", flush=True)
        if not args.all_policies:
            for p in policies:
                print(f"    - {p['name']} ({p['id']})", flush=True)
            if len(policies) < 5:
                raise SystemExit(f"Expected 5 policies, found {len(policies)}")
        else:
            for p in policies[:8]:
                print(f"    - {p['name']} ({p['id']})", flush=True)
            if len(policies) > 8:
                print(f"    … and {len(policies) - 8} more", flush=True)
            if not policies:
                raise SystemExit("No ACTIVE policies found")

        pids = [UUID(p["id"]) for p in policies]

        if not args.observations_only:
            print("\n--- Claims Jan–Jul 2026 ---", flush=True)
            for m in range(1, 8):
                _ensure_month_claims(db, TENANT, 2026, m, args.claims_per_month)

        if args.replace:
            n = _replace_obs(db, TENANT, pids, OBS_ENDS)
            print(f"\n  replaced/deleted prior obs rows: {n}", flush=True)

        print("\n--- Observations (incremental) ---", flush=True)
        pred_cache = _load_predicted_pcts(db, TENANT)
        # Preload existing monday-demo observation ids for fast skip
        existing_ids = {
            r[0]
            for r in db.query(Observation.observation_id)
            .filter(
                Observation.tenant_id == TENANT,
                Observation.observation_id.like("obs-mon-%"),
            )
            .all()
        }
        print(f"  existing monday obs ids: {len(existing_ids)}", flush=True)

        created = skipped = failed = 0
        for month_idx, end in enumerate(OBS_ENDS):
            print(f"\n=== through {end.isoformat()} ===", flush=True)
            t0 = time.time()
            base = _window_metrics(db, TENANT, EFFECTIVE, end)
            print(
                f"    metrics {time.time()-t0:.1f}s claims={base.get('total_claims')} "
                f"cost_pmpm={base.get('cost_pmpm')}",
                flush=True,
            )
            if int(base.get("total_claims") or 0) == 0:
                print("    no claims — skip", flush=True)
                failed += len(policies)
                continue

            base_cost = float(base.get("cost_pmpm") or 0)
            base_util = float(base.get("utilization_per_1k") or 0)
            batch = []
            now = datetime.utcnow()

            for p in policies:
                pid = UUID(p["id"])
                obs_id = f"obs-mon-{end.strftime('%Y%m%d')}-{pid.hex[:8]}"
                if obs_id in existing_ids:
                    skipped += 1
                    continue

                varied = _spread(str(pid), base, month_idx)
                obs_cost = float(varied.get("cost_pmpm") or 0)
                obs_util = float(varied.get("utilization_per_1k") or 0)
                pred_cost, pred_util = _predicted_levels(pred_cache, pid, base_cost, base_util)

                cost_vs_base = ((obs_cost - base_cost) / base_cost * 100) if base_cost else 0.0
                util_vs_base = ((obs_util - base_util) / base_util * 100) if base_util else 0.0
                cost_vs_pred = ((obs_cost - pred_cost) / pred_cost * 100) if pred_cost else 0.0
                util_vs_pred = ((obs_util - pred_util) / pred_util * 100) if pred_util else 0.0
                if cost_vs_pred <= 5:
                    verdict = "ON_TRACK"
                elif cost_vs_pred <= 15:
                    verdict = "AT_RISK"
                else:
                    verdict = "BACKFIRE"

                metrics = dict(varied)
                metrics["demo_seed"] = "monday_demo_5"
                metrics["baseline_utilization_per_1k"] = base_util
                metrics["baseline_cost_pmpm"] = base_cost

                vs_baseline = {
                    "baseline_utilization_per_1k": base_util,
                    "observed_utilization_per_1k": obs_util,
                    "change_from_baseline_pct": util_vs_base,
                    "utilization_change_pct": util_vs_base,
                    "baseline_cost_pmpm": base_cost,
                    "observed_cost_pmpm": obs_cost,
                    "cost_change_pct": cost_vs_base,
                    "cost_change_pmpm": obs_cost - base_cost,
                }
                vs_predicted = {
                    "predicted_cost_pmpm": round(pred_cost, 2),
                    "observed_cost_pmpm": round(obs_cost, 2),
                    "cost_change_pct": round(cost_vs_pred, 2),
                    "predicted_utilization_per_1k": round(pred_util, 4),
                    "observed_utilization_per_1k": round(obs_util, 4),
                    "utilization_change_pct": round(util_vs_pred, 2),
                    "verdict": verdict,
                    "prediction_accuracy_pct": round(max(0.0, 100.0 - abs(cost_vs_pred)), 1),
                }

                batch.append(
                    Observation(
                        id=uuid4(),
                        tenant_id=TENANT,
                        observation_id=obs_id,
                        policy_id=pid,
                        observation_type="PERIODIC",
                        observation_period_start=datetime.combine(EFFECTIVE, datetime.min.time()),
                        observation_period_end=datetime.combine(end, datetime.max.time().replace(microsecond=0)),
                        metrics_json=metrics,
                        comparisons_json={"vs_baseline": vs_baseline, "vs_predicted": vs_predicted},
                        behavioral_explanation_json={
                            "summary": f"Monday demo incremental observation through {end.isoformat()}.",
                            "source": SOURCE,
                        },
                        verdict_status=verdict,
                        computed_at=now,
                        created_at=now,
                        updated_at=now,
                    )
                )
                existing_ids.add(obs_id)
                created += 1

            if batch:
                try:
                    db.bulk_save_objects(batch)
                    db.commit()
                    print(f"    created {len(batch)} observations", flush=True)
                except Exception as e:
                    db.rollback()
                    failed += len(batch)
                    created -= len(batch)
                    print(f"    FAIL batch: {e}", flush=True)

        print(f"\nDone. created={created} skipped={skipped} failed={failed}", flush=True)
        print("Open Observation Analysis → filter one of the 5 policies → Overview should show 7 month-end points.", flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
