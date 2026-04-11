#!/usr/bin/env python3
"""
Compute tenant (and optionally policy-scoped) baselines from canonical claims in PostgreSQL
and persist via storage_baselines.create_baseline.

Run after load_synthetic_historical_to_postgres.py (or any canonical claims load).

  export DATABASE_URL='postgresql+psycopg2://...'
  export PYTHONPATH=apps/api/src:packages/common/src
  python3 scripts/refresh_baseline_from_canonical.py
  python3 scripts/refresh_baseline_from_canonical.py --policy-baselines
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from uuid import UUID

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
API_SRC = REPO_ROOT / "apps" / "api" / "src"
COMMON_SRC = REPO_ROOT / "packages" / "common" / "src"
for p in (str(API_SRC), str(COMMON_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.pop("CORS_ORIGINS", None)

_env = REPO_ROOT / "apps" / "api" / ".env"
if _env.exists():
    with open(_env) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                if k in ("CORS_ORIGINS",):
                    continue
                os.environ.setdefault(k, v.strip().replace('"', "").replace("'", ""))


def _calendar_months_inclusive(d0: date, d1: date) -> int:
    return max(1, (d1.year - d0.year) * 12 + (d1.month - d0.month) + 1)


def _enrich_metrics(
    m: Dict[str, Any],
    claims_df: pd.DataFrame,
    start_d: date,
    end_d: date,
) -> Dict[str, Any]:
    out = dict(m)
    months = _calendar_months_inclusive(start_d, end_d)
    out["calendar_months_in_window"] = float(months)
    out["util_rate_total_per_1000_mm"] = m.get("utilization_per_1k", 0.0)
    out["util_rate_target_per_1000_mm"] = m.get("utilization_per_1k", 0.0)
    out["allowed_pmpm_total"] = m.get("allowed_pmpm", 0.0)
    out["paid_pmpm_total"] = m.get("paid_pmpm", 0.0)
    out["allowed_pmpm_target"] = m.get("allowed_pmpm", 0.0)
    mm = float(m.get("member_months") or 0.0)
    if mm > 0:
        out["allowed_total_annualized"] = (float(m.get("allowed_pmpm", 0.0)) * mm / float(months)) * 12.0
    if not claims_df.empty:
        if "in_network" in claims_df.columns:
            try:
                out["in_network_claim_share"] = float(pd.to_numeric(claims_df["in_network"], errors="coerce").fillna(0).mean())
            except Exception:
                pass
        if "service_category" in claims_df.columns:
            try:
                top = claims_df["service_category"].value_counts(normalize=True).head(5)
                out["top_service_category_share"] = {str(k): float(v) for k, v in top.items()}
            except Exception:
                pass
        if "provider_id" in claims_df.columns:
            out["unique_providers"] = int(claims_df["provider_id"].nunique())
        from uepi_api.baseline_segmentation_from_claims import (
            patient_segments_from_claims_df,
            provider_archetypes_from_claims_df,
        )

        pa = provider_archetypes_from_claims_df(claims_df)
        ps = patient_segments_from_claims_df(claims_df)
        if pa:
            out["provider_archetypes"] = pa
        if ps:
            out["patient_segments"] = ps
    return out


def _filters_from_policy(policy: Dict[str, Any]) -> Dict[str, Any]:
    from uepi_api.services.policy_scoped_data_generation import build_policy_claims_filters

    pf = build_policy_claims_filters(policy)
    filters: Dict[str, Any] = {}
    if pf.get("lob"):
        filters["lob"] = pf["lob"]
    if pf.get("markets"):
        filters["markets"] = pf["markets"]
    elif pf.get("market"):
        filters["markets"] = [pf["market"]] if isinstance(pf["market"], str) else pf["market"]
    if pf.get("cpt_codes"):
        filters["cpt_codes"] = pf["cpt_codes"]
    if pf.get("service_categories"):
        filters["service_categories"] = pf["service_categories"]
    elif pf.get("service_category"):
        filters["service_category"] = pf["service_category"]
    if pf.get("diagnosis_codes"):
        filters["diagnosis_codes"] = pf["diagnosis_codes"]
    return filters


def _delete_all_baselines_for_tenant(tenant_id: UUID) -> int:
    from uepi_api.database import SessionLocal
    from uepi_api.models.baseline import Baseline

    db = SessionLocal()
    try:
        n = db.query(Baseline).filter(Baseline.tenant_id == tenant_id).delete()
        db.commit()
        return int(n or 0)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh baselines from canonical PostgreSQL claims")
    parser.add_argument("--tenant-id", type=str, default="00000000-0000-0000-0000-000000000001")
    parser.add_argument("--start", type=str, default="2023-01-01")
    parser.add_argument("--end", type=str, default="2025-12-31")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing baselines for this tenant before creating new ones",
    )
    parser.add_argument(
        "--policy-baselines",
        action="store_true",
        help="Also create one baseline per policy (scoped filters from policy definition)",
    )
    parser.add_argument("--computed-by", type=str, default="refresh_baseline_from_canonical")
    args = parser.parse_args()

    tenant_id = UUID(args.tenant_id)
    start_d = date.fromisoformat(args.start)
    end_d = date.fromisoformat(args.end)
    months = _calendar_months_inclusive(start_d, end_d)

    from uepi_api.database_claims_loader import compute_metrics_from_database_claims, load_claims_from_database
    from uepi_api.storage_baselines import create_baseline
    from uepi_api.storage_policies import get_policy, list_policies

    if args.replace:
        n = _delete_all_baselines_for_tenant(tenant_id)
        print(f"Deleted {n} existing baseline row(s) for tenant.")

    print(f"Loading claims {start_d} .. {end_d} ...")
    claims_df = load_claims_from_database(tenant_id, start_d, end_d, filters=None)
    if claims_df.empty:
        print("No claims in window; tenant baseline will be zeroed.")
        member_count = 1
        raw = compute_metrics_from_database_claims(claims_df, member_count=member_count, months=months)
    else:
        member_count = int(claims_df["member_id"].nunique()) if "member_id" in claims_df.columns else 1
        raw = compute_metrics_from_database_claims(claims_df, member_count=member_count, months=months)

    metrics = _enrich_metrics(raw, claims_df, start_d, end_d)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    win_start = datetime(start_d.year, start_d.month, start_d.day)
    win_end = datetime(end_d.year, end_d.month, end_d.day)

    baseline_data = {
        "window_start_date": win_start.isoformat() + "Z",
        "window_end_date": win_end.isoformat() + "Z",
        "computed_at": now.isoformat() + "Z",
        "baseline_type": "ROLLING",
        "data_period_ids": [],
        "baseline_metrics": metrics,
        "computed_by": args.computed_by,
        "refresh_reason": "NEW_DATA",
    }
    create_baseline(tenant_id, baseline_data)
    print(f"Created tenant baseline (metrics keys: {len(metrics)})")

    if args.policy_baselines:
        policies: List[Dict[str, Any]] = list_policies(tenant_id) or []
        print(f"Policy baselines for {len(policies)} policies...")
        for p in policies:
            pid_raw = p.get("id")
            if not pid_raw:
                continue
            pid = UUID(pid_raw) if isinstance(pid_raw, str) else pid_raw
            policy = get_policy(pid, tenant_id)
            if not policy:
                continue
            filters = _filters_from_policy(policy)
            pdf = load_claims_from_database(tenant_id, start_d, end_d, filters=filters or None)
            if pdf.empty:
                print(f"  skip (no claims in scope): {policy.get('name', pid)}")
                continue
            mc = int(pdf["member_id"].nunique()) if "member_id" in pdf.columns else 1
            praw = compute_metrics_from_database_claims(pdf, member_count=mc, months=months)
            pmetrics = _enrich_metrics(praw, pdf, start_d, end_d)
            pmetrics["policy_name"] = policy.get("name")
            pdata = {
                "window_start_date": baseline_data["window_start_date"],
                "window_end_date": baseline_data["window_end_date"],
                "computed_at": now.isoformat() + "Z",
                "baseline_type": "ROLLING",
                "data_period_ids": [],
                "baseline_metrics": pmetrics,
                "computed_by": args.computed_by,
                "refresh_reason": "NEW_DATA",
                "policy_id": str(pid),
            }
            create_baseline(tenant_id, pdata)
            print(f"  policy baseline: {policy.get('name', pid)}")

    print("Done.")


if __name__ == "__main__":
    main()
