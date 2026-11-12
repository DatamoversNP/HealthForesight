#!/usr/bin/env python3
"""
Lean-staging demo lifecycle (fail-safe; remediation-aware).

Narrative
  - CY2025 tenant-wide claims = pre-policy baseline era
  - Policies effective 2026-01-01
  - Stub predicted impacts for all policies
  - Monthly PERIODIC observations for each calendar month of 2026
  - Monthly OBSERVATION schedule registered for ongoing demos

Safeguards
  - Lean staging DB only (never Dec4 demo)
  - Does NOT use policy-scoped claims generation (remediation blocks unverified codes)
  - Tenant-wide synthetic claims only (not claims-executable authority)
  - Bulk SQL for predictions/observations to avoid learning-path timeouts
  - Continues on per-policy errors; final report lists failures
"""
from __future__ import annotations

import argparse
import calendar
import json
import os
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api" / "src"))
sys.path.insert(0, str(REPO / "packages" / "common" / "src"))

TENANT = UUID("00000000-0000-0000-0000-000000000001")
BASELINE_START = date(2025, 1, 1)
BASELINE_END = date(2025, 12, 31)
POLICY_EFFECTIVE = date(2026, 1, 1)


def _assert_lean() -> None:
    url = os.environ.get("DATABASE_URL") or ""
    if "lean" not in url.lower() and "hfleanstg" not in url.lower():
        if os.environ.get("LEAN_STAGING_OK") != "1":
            raise SystemExit("Refusing: not lean staging DATABASE_URL")


def flush_analytics(engine) -> dict:
    from sqlalchemy import text

    with engine.begin() as conn:
        obs = conn.execute(text("DELETE FROM observations WHERE tenant_id=:t"), {"t": str(TENANT)}).rowcount
        pred = conn.execute(text("DELETE FROM policy_predicted_impacts WHERE tenant_id=:t"), {"t": str(TENANT)}).rowcount
        # clear child baseline links first
        conn.execute(text("UPDATE baselines SET parent_baseline_id=NULL WHERE tenant_id=:t"), {"t": str(TENANT)})
        base = conn.execute(text("DELETE FROM baselines WHERE tenant_id=:t"), {"t": str(TENANT)}).rowcount
    return {"deleted_observations": obs, "deleted_predicted": pred, "deleted_baselines": base}


def seed_tenant_claims(mid_months: list[date], *, members: int, cpm: float) -> dict:
    from uepi_api.services.data_generation_service import generate_claims_data_for_date

    results = []
    for d in mid_months:
        print(f"  claims seed {d.isoformat()} …", flush=True)
        try:
            r = generate_claims_data_for_date(TENANT, d, member_count=members, claims_per_member=cpm)
            results.append({"date": d.isoformat(), "ok": True, "result": {k: r.get(k) for k in ("success", "claims_generated", "claims_loaded") if isinstance(r, dict)}})
        except Exception as e:
            results.append({"date": d.isoformat(), "ok": False, "error": str(e)})
            print(f"    FAIL {d}: {e}", flush=True)
    return {"seeded": results, "ok": sum(1 for x in results if x["ok"]), "fail": sum(1 for x in results if not x["ok"])}


def set_policy_effective(engine) -> int:
    from sqlalchemy import text

    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT id::text, policy_metadata_json FROM policies WHERE tenant_id=:t"),
            {"t": str(TENANT)},
        ).mappings().all()
        n = 0
        for r in rows:
            m = r["policy_metadata_json"] if isinstance(r["policy_metadata_json"], dict) else {}
            m = dict(m)
            m["effective_period"] = {
                "start_date": POLICY_EFFECTIVE.isoformat() + "T00:00:00",
                "end_date": None,
            }
            conn.execute(
                text("UPDATE policies SET policy_metadata_json=CAST(:m AS jsonb), updated_at=NOW() WHERE id=:id"),
                {"m": json.dumps(m), "id": r["id"]},
            )
            n += 1
    return n


def compute_2025_metrics(engine) -> dict:
    from sqlalchemy import text

    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT
                  count(*) AS n_claims,
                  count(DISTINCT member_id) AS members,
                  coalesce(avg(allowed_amount), 0) AS avg_allowed,
                  coalesce(sum(allowed_amount), 0) AS sum_allowed,
                  coalesce(avg(units), 1) AS avg_units
                FROM claims_lines
                WHERE tenant_id=:t
                  AND service_date >= :s AND service_date <= :e
                """
            ),
            {"t": str(TENANT), "s": BASELINE_START, "e": BASELINE_END},
        ).mappings().first()
    n = int(row["n_claims"] or 0)
    members = max(int(row["members"] or 0), 1)
    # rough util per 1k and PMPM for demo metrics
    util = round((n / members) * (1000 / 12), 2) if members else 80.0
    pmpm = round(float(row["sum_allowed"] or 0) / max(members * 12, 1), 2)
    return {
        "util_rate_total_per_1000_mm": util or 82.0,
        "utilization_per_1k": util or 82.0,
        "allowed_pmpm_total": pmpm or 48.0,
        "cost_pmpm": pmpm or 48.0,
        "unique_members": members,
        "member_months": members * 12,
        "claim_count": n,
        "source": "tenant_wide_cy2025_claims_aggregate",
        "authority": "SYNTHETIC_DEMO_NOT_CLAIMS_EXECUTABLE",
    }


def create_cy2025_baseline(engine, metrics: dict) -> dict:
    from uepi_api.storage_baselines import create_baseline
    from sqlalchemy import text

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    data = {
        "window_start_date": datetime(2025, 1, 1).isoformat() + "Z",
        "window_end_date": datetime(2025, 12, 31, 23, 59, 59).isoformat() + "Z",
        "computed_at": now.isoformat() + "Z",
        "baseline_type": "FIXED",
        "data_period_ids": [],
        "baseline_metrics": metrics,
        "computed_by": "lean_staging_demo_lifecycle_2025",
        "refresh_reason": "NEW_DATA",
    }
    created = create_baseline(TENANT, data)
    # FK targets use baselines.id (UUID PK), not baseline_id string
    with engine.connect() as conn:
        pk = conn.execute(
            text(
                """
                SELECT id::text FROM baselines
                WHERE tenant_id=:t
                ORDER BY created_at DESC NULLS LAST
                LIMIT 1
                """
            ),
            {"t": str(TENANT)},
        ).scalar()
    created = dict(created or {})
    created["id"] = pk
    created["baseline_db_id"] = pk
    return created


def bulk_stub_predictions(engine, baseline_id: str, policy_ids: list[str]) -> int:
    from sqlalchemy import text

    stub_metrics = {
        "utilization_change_per_1k": -5.0,
        "cost_change_pmpm": -2.0,
        "utilization_change": -5.0,
        "cost_change": -2.0,
        "utilization_change_pct": -5.0,
        "cost_change_pct": -3.0,
        "cost_change_total": -60000.0,
        "confidence_score": None,
        "prediction_method": "demo_stub_unestimated",
        "authority": "SYNTHETIC_DEMO_NOT_CLAIMS_EXECUTABLE",
        "note": "Stub pending authority-certified elasticity; not calibrated impact",
    }
    now = datetime.utcnow()
    rows = []
    for pid in policy_ids:
        rows.append(
            {
                "id": str(uuid.uuid4()),
                "tenant_id": str(TENANT),
                "policy_id": pid,
                "metrics_json": json.dumps(stub_metrics),
                "model_version": "demo_stub_v2",
                "confidence": None,
                "predicted_at": now,
                "prediction_method": "demo_stub_unestimated",
                "baseline_id": baseline_id,
                "created_at": now,
                "updated_at": now,
            }
        )
    with engine.begin() as conn:
        for i in range(0, len(rows), 50):
            batch = rows[i : i + 50]
            conn.execute(
                text(
                    """
                    INSERT INTO policy_predicted_impacts
                      (id, tenant_id, policy_id, metrics_json, model_version, confidence,
                       predicted_at, prediction_method, baseline_id, created_at, updated_at)
                    VALUES
                      (:id, :tenant_id, :policy_id, CAST(:metrics_json AS jsonb), :model_version, :confidence,
                       :predicted_at, :prediction_method, :baseline_id, :created_at, :updated_at)
                    """
                ),
                batch,
            )
    return len(rows)


def month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def bulk_monthly_observations(engine, baseline_id: str, policies: list[dict], year: int = 2026) -> dict:
    from sqlalchemy import text

    # pred map
    with engine.connect() as conn:
        pred_map = {
            r[0]: r[1]
            for r in conn.execute(
                text(
                    """
                    SELECT DISTINCT ON (policy_id) policy_id::text, id::text
                    FROM policy_predicted_impacts WHERE tenant_id=:t
                    ORDER BY policy_id, predicted_at DESC NULLS LAST
                    """
                ),
                {"t": str(TENANT)},
            ).fetchall()
        }

    verdicts = [
        ("ON_TRACK", "Observed metrics aligned with predicted direction for period.", "Continue monitoring."),
        ("ON_TRACK", "Observed metrics aligned with predicted direction for period.", "Continue monitoring."),
        ("AT_RISK", "Observed metrics exceed predicted tolerance for period.", "Investigate drivers."),
        ("AT_RISK", "Observed metrics exceed predicted tolerance for period.", "Investigate drivers."),
        ("BACKFIRE", "Observed direction opposite of predicted impact for period.", "Escalate clinical/ops review."),
    ]
    baseline_util, baseline_cost = 82.0, 48.0
    predicted_util, predicted_cost = 77.0, 46.0
    now = datetime.utcnow()
    rows = []
    for i, pol in enumerate(policies):
        status, reason, rec = verdicts[i % len(verdicts)][:3]
        factor = {"ON_TRACK": 1.0, "AT_RISK": 1.18, "BACKFIRE": 1.25}[status]
        for month in range(1, 13):
            start = date(year, month, 1)
            end = month_end(year, month)
            observed_util = predicted_util * factor
            observed_cost = predicted_cost * factor
            metrics = {
                "utilization_per_1k": observed_util,
                "cost_pmpm": observed_cost,
                "cost_per_member": observed_cost,
                "baseline_utilization_per_1k": baseline_util,
                "baseline_cost_pmpm": baseline_cost,
                "predicted_utilization_per_1k": predicted_util,
                "predicted_cost_pmpm": predicted_cost,
                "period_year": year,
                "period_month": month,
                "authority": "SYNTHETIC_DEMO_NOT_CLAIMS_EXECUTABLE",
            }
            comparisons = {
                "vs_baseline": {
                    "utilization_change": observed_util - baseline_util,
                    "cost_change_pmpm": observed_cost - baseline_cost,
                },
                "vs_predicted": {
                    "utilization_change": observed_util - predicted_util,
                    "cost_change_pmpm": observed_cost - predicted_cost,
                    "accuracy_pct": max(0.0, 100.0 - abs((observed_util - predicted_util) / predicted_util) * 100),
                },
            }
            oid = str(uuid.uuid4())
            rows.append(
                {
                    "id": oid,
                    "tenant_id": str(TENANT),
                    "observation_id": oid,
                    "policy_id": pol["id"],
                    "baseline_version_id": baseline_id,
                    "prediction_id": pred_map.get(pol["id"]),
                    "data_period_ids_json": json.dumps([]),
                    "observation_type": "PERIODIC",
                    "observation_period_start": datetime(year, month, 1),
                    "observation_period_end": datetime(end.year, end.month, end.day, 23, 59, 59),
                    "metrics_json": json.dumps(metrics),
                    "comparisons_json": json.dumps(comparisons),
                    "behavioral_explanation_json": json.dumps({}),
                    "verdict_status": status,
                    "verdict_reason": reason,
                    "recommendation": rec,
                    "verdict_rule_version": "v1.0-demo",
                    "computed_at": now,
                    "created_at": now,
                    "updated_at": now,
                }
            )

    inserted = 0
    with engine.begin() as conn:
        for i in range(0, len(rows), 100):
            batch = rows[i : i + 100]
            conn.execute(
                text(
                    """
                    INSERT INTO observations (
                      id, tenant_id, observation_id, policy_id, baseline_version_id, prediction_id,
                      data_period_ids_json, observation_type, observation_period_start, observation_period_end,
                      metrics_json, comparisons_json, behavioral_explanation_json,
                      verdict_status, verdict_reason, recommendation, verdict_rule_version,
                      computed_at, created_at, updated_at
                    ) VALUES (
                      :id, :tenant_id, :observation_id, :policy_id, :baseline_version_id, :prediction_id,
                      CAST(:data_period_ids_json AS jsonb), :observation_type, :observation_period_start, :observation_period_end,
                      CAST(:metrics_json AS jsonb), CAST(:comparisons_json AS jsonb), CAST(:behavioral_explanation_json AS jsonb),
                      :verdict_status, :verdict_reason, :recommendation, :verdict_rule_version,
                      :computed_at, :created_at, :updated_at
                    )
                    """
                ),
                batch,
            )
            inserted += len(batch)
            if inserted % 500 == 0:
                print(f"  … observations {inserted}/{len(rows)}", flush=True)
    return {"inserted": inserted, "policies": len(policies), "months": 12}


def ensure_monthly_schedule() -> dict:
    from uepi_api.storage_schedules import create_schedule, list_schedules

    existing = list_schedules(TENANT) or []
    for s in existing:
        if (s.get("name") or "").startswith("Lean Staging Monthly Observations"):
            return {"created": False, "schedule": s}
    sched = create_schedule(
        TENANT,
        {
            "name": "Lean Staging Monthly Observations",
            "schedule_type": "OBSERVATION",
            "frequency": "MONTHLY",
            "time": "06:00",
            "day_of_month": 2,
            "enabled": True,
            "config": {
                "mode": "PERIODIC_MONTHLY",
                "source": "lean_staging_demo_lifecycle_2025",
                "note": "Synthetic demo observations; not claims-executable authority",
                "skip_if_remediation_blocks_claims": True,
            },
        },
    )
    return {"created": True, "schedule": sched}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-flush", action="store_true")
    ap.add_argument("--skip-claims", action="store_true")
    ap.add_argument("--members", type=int, default=400)
    ap.add_argument("--claims-per-member", type=float, default=0.4)
    ap.add_argument(
        "--report",
        default=str(
            REPO
            / "docs"
            / "production"
            / "releases"
            / "corrections"
            / f"LEAN_STAGING_LIFECYCLE_2025_REPORT_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
        ),
    )
    args = ap.parse_args()
    _assert_lean()

    from sqlalchemy import create_engine, text

    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    report: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "environment": "lean_staging_only",
        "demo_untouched": True,
        "phases": {},
        "failures": [],
    }

    if not args.skip_flush:
        print("PHASE flush analytics…", flush=True)
        report["phases"]["flush"] = flush_analytics(engine)
        print(" ", report["phases"]["flush"], flush=True)

    print("PHASE set policy effective_period → 2026-01-01…", flush=True)
    report["phases"]["effective"] = {"updated": set_policy_effective(engine)}

    if not args.skip_claims:
        print("PHASE seed CY2025 tenant-wide claims (not policy-scoped)…", flush=True)
        dates_2025 = [date(2025, m, 15) for m in range(1, 13)]
        # top-up 2026 Apr–Dec (Q1 already present)
        dates_2026 = [date(2026, m, 15) for m in range(4, 13)]
        s1 = seed_tenant_claims(dates_2025, members=args.members, cpm=args.claims_per_member)
        s2 = seed_tenant_claims(dates_2026, members=args.members, cpm=args.claims_per_member)
        report["phases"]["claims_2025"] = s1
        report["phases"]["claims_2026_topup"] = s2
        if s1["fail"] or s2["fail"]:
            report["failures"].append({"phase": "claims", "detail": {"2025_fail": s1["fail"], "2026_fail": s2["fail"]}})

    print("PHASE CY2025 FIXED baseline…", flush=True)
    metrics = compute_2025_metrics(engine)
    if metrics.get("claim_count", 0) < 100:
        report["failures"].append({"phase": "baseline", "detail": f"insufficient_2025_claims:{metrics.get('claim_count')}"})
        # still create baseline with fallback metrics so demos work
        metrics.setdefault("util_rate_total_per_1000_mm", 82.0)
        metrics.setdefault("allowed_pmpm_total", 48.0)
    baseline = create_cy2025_baseline(engine, metrics)
    baseline_id = baseline.get("id") or baseline.get("baseline_db_id")
    if not baseline_id:
        raise SystemExit(f"baseline PK missing: {baseline}")
    report["phases"]["baseline"] = {
        "baseline_id": baseline_id,
        "metrics": metrics,
        "window": "2025-01-01..2025-12-31",
    }
    print("  baseline", baseline_id, "claims", metrics.get("claim_count"), flush=True)

    with engine.connect() as conn:
        policies = [
            {"id": r[0], "name": r[1]}
            for r in conn.execute(
                text("SELECT id::text, name FROM policies WHERE tenant_id=:t ORDER BY name"),
                {"t": str(TENANT)},
            ).fetchall()
        ]
    print(f"PHASE stub predictions for {len(policies)} policies…", flush=True)
    n_pred = bulk_stub_predictions(engine, str(baseline_id), [p["id"] for p in policies])
    report["phases"]["predictions"] = {"inserted": n_pred}

    print(f"PHASE monthly 2026 observations ({len(policies)} × 12)…", flush=True)
    obs = bulk_monthly_observations(engine, str(baseline_id), policies, year=2026)
    report["phases"]["observations"] = obs

    print("PHASE monthly schedule…", flush=True)
    try:
        report["phases"]["schedule"] = ensure_monthly_schedule()
    except Exception as e:
        report["failures"].append({"phase": "schedule", "detail": str(e)})
        report["phases"]["schedule"] = {"error": str(e)}

    # verify
    with engine.connect() as conn:
        verify = {
            "baselines": conn.execute(text("SELECT count(*) FROM baselines WHERE tenant_id=:t"), {"t": str(TENANT)}).scalar(),
            "predicted": conn.execute(text("SELECT count(*) FROM policy_predicted_impacts WHERE tenant_id=:t"), {"t": str(TENANT)}).scalar(),
            "observations": conn.execute(text("SELECT count(*) FROM observations WHERE tenant_id=:t"), {"t": str(TENANT)}).scalar(),
            "obs_policies": conn.execute(text("SELECT count(DISTINCT policy_id) FROM observations WHERE tenant_id=:t"), {"t": str(TENANT)}).scalar(),
            "claims_2025": conn.execute(
                text("SELECT count(*) FROM claims_lines WHERE tenant_id=:t AND service_date>='2025-01-01' AND service_date<='2025-12-31'"),
                {"t": str(TENANT)},
            ).scalar(),
            "claims_2026": conn.execute(
                text("SELECT count(*) FROM claims_lines WHERE tenant_id=:t AND service_date>='2026-01-01' AND service_date<='2026-12-31'"),
                {"t": str(TENANT)},
            ).scalar(),
        }
    report["verify"] = verify
    report["ended_at"] = datetime.now(timezone.utc).isoformat()
    report["pass"] = (
        verify["baselines"] >= 1
        and verify["predicted"] >= len(policies)
        and verify["obs_policies"] >= len(policies)
        and verify["claims_2025"] > 0
        and len(report["failures"]) == 0
    )

    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    md = out.with_suffix(".md")
    md.write_text(
        "\n".join(
            [
                "# Lean Staging Lifecycle 2025/2026 Report",
                "",
                f"Generated: {report['ended_at']}",
                f"PASS: **{report['pass']}**",
                "",
                "## Verify",
                "",
                "```json",
                json.dumps(verify, indent=2),
                "```",
                "",
                "## Failures",
                "",
                json.dumps(report["failures"], indent=2) if report["failures"] else "_none_",
                "",
                "## Recommendation — monthly process",
                "",
                "1. **Monthly observation job** (registered): day-2 06:00 — create PERIODIC obs for prior month (synthetic demo path).",
                "2. **Monthly claims top-up** (optional): mid-month tenant-wide seed only — do **not** policy-scope until CLAIMS_EXECUTABLE.",
                "3. **Quarterly baseline refresh** of trailing FIXED/ROLLING window after authority-certified codes exist.",
                "4. Keep remediation fail-closed: no unverified code-driven claims calc.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"report": str(out), "pass": report["pass"], "verify": verify, "failures": report["failures"]}, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
