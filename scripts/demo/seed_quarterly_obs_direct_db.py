#!/usr/bin/env python3
"""
Quarterly 2026 observations via direct Postgres (bypasses Azure App Service HTTP).

Why: daily-job API path loads 25k claims then creates ~265 observations inside the
same App Service process → ping/login timeouts and 60–90m wall clocks per quarter.

This script:
  - Uses DATABASE_URL (same as healthforesight-api)
  - Optionally inserts a *small* claim batch per missing quarter date (default 3k)
  - Creates one observation per ACTIVE policy per quarter end (skip if already present)
  - Computes window metrics once per date, then per-policy spread (same demo pattern
    as the daily job) so we do not re-scan claims 265 times

Usage (from repo root):
  export DATABASE_URL='postgresql://USER:PASS@HOST.postgres.database.azure.com:5432/DB?sslmode=require'
  # Allow your laptop IP on the Azure Postgres firewall first.

  python3 scripts/demo/seed_quarterly_obs_direct_db.py
  python3 scripts/demo/seed_quarterly_obs_direct_db.py --dates 2026-04-15,2026-07-15,2026-10-15
  python3 scripts/demo/seed_quarterly_obs_direct_db.py --limit-policies 40 --claims-per-date 2000
  python3 scripts/demo/seed_quarterly_obs_direct_db.py --observations-only
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "common" / "src"))

DEFAULT_TENANT = UUID("00000000-0000-0000-0000-000000000001")
QUARTERLY_DATES = ["2026-01-15", "2026-04-15", "2026-07-15", "2026-10-15"]
EFFECTIVE_FALLBACK = date(2026, 1, 1)
SOURCE_SYSTEM = "QUARTERLY_OBS_DIRECT"


def _require_database_url() -> str:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url or "YOURSERVER" in url or "@host:" in url:
        raise SystemExit(
            "Set DATABASE_URL to the Azure Postgres connection string "
            "(Portal → healthforesight-api → Configuration, or:\n"
            "  az webapp config appsettings list -g healthforesight-rg -n healthforesight-api "
            "--query \"[?name=='DATABASE_URL'].value\" -o tsv)"
        )
    return url


def _apply_policy_metric_spread(policy_id: str, post_metrics: dict[str, Any]) -> dict[str, Any]:
    digest = hashlib.sha256(policy_id.encode()).hexdigest()
    h = int(digest[:8], 16) % 100
    h2 = int(digest[8:16], 16) % 100
    if h < 50:
        mult_cost = 0.78 + (h / 50.0) * 0.14
        mult_util = 0.80 + (h2 / 100.0) * 0.14
    elif h < 85:
        mult_cost = 1.03 + ((h - 50) / 35.0) * 0.11
        mult_util = 1.02 + (h2 / 100.0) * 0.12
    else:
        mult_cost = 1.15 + ((h - 85) / 15.0) * 0.15
        mult_util = 1.12 + (h2 / 100.0) * 0.18
    out = dict(post_metrics)
    if post_metrics.get("utilization_per_1k") is not None:
        out["utilization_per_1k"] = round(float(post_metrics["utilization_per_1k"]) * mult_util, 4)
    if post_metrics.get("cost_pmpm") is not None:
        out["cost_pmpm"] = round(float(post_metrics["cost_pmpm"]) * mult_cost, 2)
    if post_metrics.get("cost_per_member") is not None:
        out["cost_per_member"] = round(float(post_metrics["cost_per_member"]) * mult_cost, 2)
    return out


def _set_long_timeout(db, ms: int = 600_000) -> None:
    from sqlalchemy import text

    try:
        # Session-level (not LOCAL) so it survives commits used by create_observation helpers
        db.execute(text(f"SET statement_timeout = {int(ms)}"))
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


def _count_claims(db, tenant_id: UUID, on_date: date) -> int:
    from sqlalchemy import func
    from uepi_api.models.canonical_data import ClaimsLineDB

    _set_long_timeout(db)
    return int(
        db.query(func.count(ClaimsLineDB.id))
        .filter(
            ClaimsLineDB.tenant_id == tenant_id,
            ClaimsLineDB.service_date == on_date,
        )
        .scalar()
        or 0
    )


def _ensure_small_claims(db, tenant_id: UUID, on_date: date, n: int) -> int:
    """Insert n synthetic claim lines for on_date if fewer than n/2 already exist."""
    existing = _count_claims(db, tenant_id, on_date)
    if existing >= max(100, n // 2):
        print(f"    claims on {on_date}: {existing} (skip generate)", flush=True)
        return 0

    from uepi_api.repositories.canonical_data import CanonicalDataRepository
    import random

    random.seed(int(on_date.strftime("%Y%m%d")))
    cats = {
        "PRIMARY_CARE": {"codes": ["99213", "99214"], "avg": 150.0},
        "SPECIALTY_CARE": {"codes": ["99243", "99244"], "avg": 300.0},
        "ADVANCED_IMAGING": {"codes": ["70450", "72141"], "avg": 800.0},
        "LABORATORY": {"codes": ["80053", "85025"], "avg": 50.0},
    }
    rows = []
    for i in range(n):
        cat = random.choice(list(cats.keys()))
        info = cats[cat]
        allowed = info["avg"] * random.uniform(0.7, 1.3)
        paid = allowed * random.uniform(0.8, 1.0)
        rows.append(
            {
                "tenant_id": tenant_id,
                "claim_id": f"QD_{on_date.strftime('%Y%m%d')}_{i:06d}",
                "claim_line_id": f"QD_{on_date.strftime('%Y%m%d')}_{i:06d}_01",
                "member_id": f"MEM_{(i % 5000):06d}",
                "provider_id": f"PROV_{(i % 200):05d}",
                "service_date": on_date,
                "paid_date": on_date + timedelta(days=random.randint(1, 20)),
                "lob": random.choice(["COMMERCIAL", "MEDICARE", "MEDICAID"]),
                "market": random.choice(["CA", "TX", "NY", "FL"]),
                "cpt_code": random.choice(info["codes"]),
                "hcpcs_code": "",
                "service_category": cat,
                "place_of_service": random.choice(["11", "22", "23"]),
                "units": 1.0,
                "allowed_amount": float(allowed),
                "paid_amount": float(paid),
                "member_cost_share": float(allowed - paid),
                "in_network": True,
                "system_affiliation": random.choice(["HOSPITAL_SYSTEM_A", "INDEPENDENT"]),
                "facility_type": "CLINIC",
                "source_system": SOURCE_SYSTEM,
                "source_file_id": f"quarterly_direct_{on_date.isoformat()}",
                "ingestion_id": UUID("00000000-0000-4000-8000-00000000qd01"),
            }
        )
    repo = CanonicalDataRepository(db)
    loaded = repo.bulk_insert_claims_lines(
        tenant_id=tenant_id,
        claims_data=rows,
        source_system=SOURCE_SYSTEM,
        source_file_id=f"quarterly_direct_{on_date.isoformat()}",
        ingestion_id=UUID("00000000-0000-4000-8000-00000000qd01"),
    )
    db.commit()
    print(f"    inserted {loaded} claims for {on_date} (had {existing})", flush=True)
    return int(loaded or 0)


def _window_metrics(db, tenant_id: UUID, start: date, end: date) -> dict[str, Any]:
    """SQL aggregates only — avoid loading 100k+ claim rows into pandas on a laptop."""
    from sqlalchemy import func
    from uepi_api.models.canonical_data import ClaimsLineDB

    _set_long_timeout(db, 900_000)
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
    total_allowed = float(row.total_allowed or 0)
    members = max(1, int(row.unique_members or 0))
    days = max(1, (end - start).days)
    months = max(1, round(days / 30.0))
    member_months = float(members * months)
    paid_pmpm = (total_paid / member_months) if member_months else 0.0
    util = (total_claims / member_months * 1000.0) if member_months else 0.0
    return {
        "utilization_per_1k": float(util),
        "cost_pmpm": float(paid_pmpm),
        "cost_per_member": float(paid_pmpm),
        "paid_pmpm": float(paid_pmpm),
        "allowed_pmpm": float(total_allowed / member_months) if member_months else 0.0,
        "total_claims": total_claims,
        "total_paid": total_paid,
        "total_allowed": total_allowed,
        "unique_members": members,
        "member_months": member_months,
    }


def _list_active_policies_light(db, tenant_id: UUID, limit: int = 0) -> list[dict]:
    """Avoid storage_policies.list_policies (opens nested sessions + heavy dict convert)."""
    from uepi_api.models.policy import Policy as PolicyDB, PolicyVersion as PolicyVersionDB
    from sqlalchemy import desc

    q = (
        db.query(PolicyDB.id, PolicyDB.name, PolicyDB.status, PolicyDB.policy_metadata_json)
        .filter(PolicyDB.tenant_id == tenant_id, PolicyDB.status == "ACTIVE")
        .order_by(desc(PolicyDB.created_at))
    )
    if limit > 0:
        q = q.limit(limit)
    rows = q.all()
    out = []
    for r in rows:
        # Prefer version effective_start when present
        ver = (
            db.query(PolicyVersionDB.effective_start_date)
            .filter(PolicyVersionDB.policy_id == r.id)
            .order_by(desc(PolicyVersionDB.version_number))
            .first()
        )
        eff = None
        if ver and ver[0]:
            eff = ver[0].date() if isinstance(ver[0], datetime) else ver[0]
        meta = r.policy_metadata_json or {}
        if not eff and isinstance(meta, dict):
            ep = meta.get("effective_period") or {}
            start = ep.get("start") if isinstance(ep, dict) else None
            if start:
                try:
                    eff = date.fromisoformat(str(start)[:10])
                except ValueError:
                    eff = None
        out.append(
            {
                "id": str(r.id),
                "name": r.name,
                "status": r.status,
                "effective_date": eff or EFFECTIVE_FALLBACK,
            }
        )
    return out


def _policy_effective(policy: dict) -> date:
    d = policy.get("effective_date")
    if isinstance(d, date) and not isinstance(d, datetime):
        return d
    if isinstance(d, datetime):
        return d.date()
    return EFFECTIVE_FALLBACK


def _existing_obs_ends(db, tenant_id: UUID) -> set[tuple[str, str]]:
    """Set of (policy_id, end_date_iso) for fast skip — one query."""
    from uepi_api.models.observation import Observation

    pairs: set[tuple[str, str]] = set()
    for pid, end_raw in (
        db.query(Observation.policy_id, Observation.observation_period_end)
        .filter(Observation.tenant_id == tenant_id)
        .all()
    ):
        if end_raw is None or pid is None:
            continue
        end_s = end_raw.date().isoformat() if isinstance(end_raw, datetime) else str(end_raw)[:10]
        pairs.add((str(pid), end_s))
    return pairs


def seed_date(
    db,
    tenant_id: UUID,
    target: date,
    policies: list[dict],
    existing: set[tuple[str, str]],
    *,
    claims_per_date: int,
    observations_only: bool,
) -> tuple[int, int, int]:
    from uepi_api.models.observation import Observation

    print(f"\n=== {target.isoformat()} ===", flush=True)
    if not observations_only:
        _ensure_small_claims(db, tenant_id, target, claims_per_date)
    else:
        print("    observations-only (skip claim count)", flush=True)

    window_start = EFFECTIVE_FALLBACK
    print(f"    computing shared metrics {window_start} .. {target} …", flush=True)
    t0 = time.time()
    base_metrics = _window_metrics(db, tenant_id, window_start, target)
    print(
        f"    metrics in {time.time() - t0:.1f}s — claims={base_metrics.get('total_claims')} "
        f"cost_pmpm={base_metrics.get('cost_pmpm')}",
        flush=True,
    )
    if int(base_metrics.get("total_claims") or 0) == 0:
        print("    no claims in window — skip observations for this date", flush=True)
        return 0, 0, len(policies)

    ok = skip = fail = 0
    end_iso = target.isoformat()
    base_util = float(base_metrics.get("utilization_per_1k") or 0)
    base_cost = float(base_metrics.get("cost_pmpm") or 0)
    pred_cost = base_cost * 0.92
    pred_util = base_util * 0.94
    batch: list = []
    now = datetime.utcnow()

    for i, policy in enumerate(policies, 1):
        pid_raw = policy.get("id")
        if not pid_raw:
            skip += 1
            continue
        try:
            pid = UUID(str(pid_raw))
        except ValueError:
            fail += 1
            continue

        eff = _policy_effective(policy)
        if eff > target:
            skip += 1
            continue
        if (str(pid), end_iso) in existing:
            skip += 1
            continue

        varied = _apply_policy_metric_spread(str(pid), base_metrics)
        obs_cost = float(varied.get("cost_pmpm") or 0)
        obs_util = float(varied.get("utilization_per_1k") or 0)
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
        metrics["demo_seed"] = "quarterly_obs_direct_db"
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
        }

        period_start_dt = datetime.combine(eff, datetime.min.time())
        period_end_dt = datetime.combine(target, datetime.max.time().replace(microsecond=0))
        obs_id = f"obs-qtr-{target.strftime('%Y%m%d')}-{pid.hex[:8]}"
        batch.append(
            Observation(
                id=uuid4(),
                tenant_id=tenant_id,
                observation_id=obs_id,
                policy_id=pid,
                observation_type="PERIODIC",
                observation_period_start=period_start_dt,
                observation_period_end=period_end_dt,
                metrics_json=metrics,
                comparisons_json={"vs_baseline": vs_baseline, "vs_predicted": vs_predicted},
                behavioral_explanation_json={
                    "summary": "Direct-DB quarterly seed (shared window metrics + policy spread).",
                    "source": SOURCE_SYSTEM,
                },
                verdict_status=verdict,
                computed_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        existing.add((str(pid), end_iso))
        ok += 1

        if len(batch) >= 50:
            try:
                db.bulk_save_objects(batch)
                db.commit()
                print(f"    … flushed {ok} created (skip={skip})", flush=True)
            except Exception as e:
                db.rollback()
                fail += len(batch)
                ok -= len(batch)
                print(f"    batch fail: {e}", flush=True)
            batch = []

    if batch:
        try:
            db.bulk_save_objects(batch)
            db.commit()
        except Exception as e:
            db.rollback()
            fail += len(batch)
            ok -= len(batch)
            print(f"    final batch fail: {e}", flush=True)

    print(f"    done {target}: created={ok} skip={skip} fail={fail}", flush=True)
    return ok, skip, fail


def main() -> None:
    ap = argparse.ArgumentParser(description="Direct-DB quarterly observations (no App Service)")
    ap.add_argument("--tenant-id", default=str(DEFAULT_TENANT))
    ap.add_argument("--dates", default=",".join(QUARTERLY_DATES))
    ap.add_argument("--limit-policies", type=int, default=0, help="0 = all ACTIVE policies")
    ap.add_argument("--claims-per-date", type=int, default=3000, help="Small claim batch if date thin")
    ap.add_argument("--observations-only", action="store_true", help="Do not generate claims")
    ap.add_argument("--status-only", action="store_true", help="Print claim/obs counts and exit")
    args = ap.parse_args()

    _require_database_url()
    # Ensure uepi_api picks up DATABASE_URL
    os.environ["DATABASE_URL"] = os.environ["DATABASE_URL"].strip()

    tenant_id = UUID(args.tenant_id)
    dates = [date.fromisoformat(d.strip()) for d in args.dates.split(",") if d.strip()]

    print("=" * 72, flush=True)
    print("Direct-DB quarterly observations (bypass App Service)", flush=True)
    print(f"  Tenant: {tenant_id}", flush=True)
    print(f"  Dates:  {[d.isoformat() for d in dates]}", flush=True)
    print("=" * 72, flush=True)

    from uepi_api.database import SessionLocal
    from uepi_api.models.observation import Observation
    from collections import Counter

    db = SessionLocal()
    try:
        # Quick connectivity
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        _set_long_timeout(db, 900_000)
        print("  DB ok", flush=True)

        if args.status_only:
            for d in dates:
                print(f"  claims {d}: {_count_claims(db, tenant_id, d)}", flush=True)
            ends: Counter[str] = Counter()
            for o in (
                db.query(Observation)
                .filter(Observation.tenant_id == tenant_id)
                .order_by(Observation.computed_at.desc())
                .limit(2000)
            ):
                e = o.observation_period_end
                key = e.date().isoformat() if isinstance(e, datetime) else str(e)[:10]
                ends[key] += 1
            print(f"  observation ends (sample): {ends.most_common(10)}", flush=True)
            return

        print("  loading ACTIVE policies (light)…", flush=True)
        policies = _list_active_policies_light(db, tenant_id, limit=args.limit_policies)
        print(f"  ACTIVE policies in scope: {len(policies)}", flush=True)
        print("  indexing existing observation ends…", flush=True)
        existing = _existing_obs_ends(db, tenant_id)
        print(f"  existing (policy,end) pairs: {len(existing)}", flush=True)

        total_ok = total_skip = total_fail = 0
        for d in dates:
            ok, skip, fail = seed_date(
                db,
                tenant_id,
                d,
                policies,
                existing,
                claims_per_date=args.claims_per_date,
                observations_only=args.observations_only,
            )
            total_ok += ok
            total_skip += skip
            total_fail += fail
        print(
            f"\nDone. created={total_ok} skipped={total_skip} failed={total_fail}",
            flush=True,
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
