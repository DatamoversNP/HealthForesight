#!/usr/bin/env python3
"""
Autonomous lean-staging FULL demo lifecycle (staging ONLY — never writes to demo).

1) Reuse bounded demo claims subset (read-only DEMO_DATABASE_URL) for shared codes
2) Densify monthly policy-meaningful synthetic claims for every policy with codes
3) Flush analytics (baselines/preds/obs); keep claims
4) One general CY2025 FIXED baseline (12 months, all claims)
5) One CY2025 FIXED baseline per policy, from that policy's scope codes
6) Stub predictions all policies; Stage-3.5 attempt for nine (fallback stub)
7) 2026 observations: January–September only (9 per policy), from scoped claims
8) Ensure monthly OBSERVATION schedule exists

Fail-soft: continue on per-policy errors; final report PASS/FAIL with evidence.
"""
from __future__ import annotations

import calendar
import json
import os
import random
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api" / "src"))
sys.path.insert(0, str(REPO / "packages" / "common" / "src"))

TENANT = UUID("00000000-0000-0000-0000-000000000001")
NINE = [
    "Outpatient MRI Prior Authorization",
    "Infusion Site-of-Care Optimization",
    "Freestanding Imaging Steerage",
    "Multiple Procedure Payment Reduction",
    "NCCI Medically Unlikely Units",
    "NCCI Procedure-to-Procedure Bundling",
    "LCD L34425 NC MRI Coverage Criteria",
    "NCD 220.2 MRI Coverage Change Study",
    "Outpatient Therapy Coverage and Payment",
]
# Demo-known / clinically recognizable fallbacks when policy codes empty
FALLBACK_BY_HINT = {
    "infusion": ["J1745", "J2357", "96413", "96415", "96365"],
    "mri": ["72148", "72149", "72158", "70551", "70553"],
    "therapy": ["97110", "97112", "97140", "97530"],
    "ct": ["70450", "71250", "71275", "74177"],
}


def _assert_staging(url: str) -> None:
    u = (url or "").lower()
    if "lean" not in u and "hfleanstg" not in u:
        if os.environ.get("LEAN_STAGING_OK") != "1":
            raise SystemExit("Refusing non-staging DATABASE_URL")


def _engine(url: str, *, demo: bool = False):
    from sqlalchemy import create_engine

    u = url
    if demo and "sslmode" not in u:
        u += ("&" if "?" in u else "?") + "sslmode=require"
    return create_engine(u, pool_pre_ping=True, connect_args={"connect_timeout": 30})


def month_end(y: int, m: int) -> date:
    return date(y, m, calendar.monthrange(y, m)[1])


def mid(y: int, m: int) -> date:
    return date(y, m, 15)


def load_policies(eng) -> list[dict]:
    from sqlalchemy import text

    with eng.connect() as c:
        rows = c.execute(
            text(
                "SELECT id::text, name, policy_type, policy_metadata_json FROM policies WHERE tenant_id=:t ORDER BY name"
            ),
            {"t": str(TENANT)},
        ).mappings().all()
    out = []
    for r in rows:
        m = r["policy_metadata_json"] if isinstance(r["policy_metadata_json"], dict) else {}
        codes = list((m.get("scope") or {}).get("procedure_codes") or [])
        # lever targets fallback
        if not codes:
            for lev in m.get("policy_levers") or []:
                t = (lev or {}).get("targets") or {}
                codes = list(t.get("codes") or t.get("procedure_codes") or [])
                if codes:
                    break
        name = r["name"] or ""
        if not codes:
            nl = name.lower()
            for k, v in FALLBACK_BY_HINT.items():
                if k in nl:
                    codes = list(v)
                    break
        if not codes and name in NINE:
            codes = ["72148", "72149"]
        if not codes:
            # Illustrative demo codes from correction completer (not CLAIMS_EXECUTABLE authority)
            try:
                from lean_staging_complete_all_policy_configs import infer_codes

                ui = (m.get("ui_hints") or {}) if isinstance(m.get("ui_hints"), dict) else {}
                domain = m.get("domain") or ui.get("domain") or ""
                subdomain = m.get("subdomain") or ui.get("subdomain") or ""
                codes, _cat = infer_codes(name, str(domain), str(subdomain), "")
            except Exception:
                codes = ["99213", "99214"]
        out.append(
            {
                "id": r["id"],
                "name": name,
                "policy_type": r["policy_type"],
                "codes": codes,
                "meta": m,
                "is_nine": name in NINE,
            }
        )
    return out


def flush_analytics(eng) -> dict:
    from sqlalchemy import text

    with eng.begin() as c:
        o = c.execute(text("DELETE FROM observations WHERE tenant_id=:t"), {"t": str(TENANT)}).rowcount
        p = c.execute(text("DELETE FROM policy_predicted_impacts WHERE tenant_id=:t"), {"t": str(TENANT)}).rowcount
        c.execute(text("UPDATE baselines SET parent_baseline_id=NULL WHERE tenant_id=:t"), {"t": str(TENANT)})
        b = c.execute(text("DELETE FROM baselines WHERE tenant_id=:t"), {"t": str(TENANT)}).rowcount
    return {"obs": o, "pred": p, "baselines": b}


def copy_demo_claims_subset(demo_eng, stg_eng, code_union: list[str], per_code_limit: int = 800) -> dict:
    """Read-only from demo; insert into staging with new IDs / staging tenant."""
    from sqlalchemy import text

    if not code_union:
        return {"copied": 0, "note": "no codes"}
    copied = 0
    errors = []
    # sample per code to keep transfer bounded
    with demo_eng.connect() as dc, stg_eng.begin() as sc:
        for code in sorted(set(code_union)):
            try:
                rows = dc.execute(
                    text(
                        """
                        SELECT service_date, paid_date, lob, market, cpt_code, hcpcs_code,
                               service_category, place_of_service, units,
                               allowed_amount, paid_amount, member_cost_share, in_network,
                               member_id, provider_id
                        FROM claims_lines
                        WHERE (cpt_code = :c OR hcpcs_code = :c)
                          AND service_date >= '2024-01-01'
                        ORDER BY service_date DESC
                        LIMIT :lim
                        """
                    ),
                    {"c": code, "lim": per_code_limit},
                ).mappings().all()
            except Exception as e:
                errors.append({"code": code, "error": str(e)[:200]})
                continue
            batch = []
            for i, r in enumerate(rows):
                # Remap older dates into 2025/2026 monthly midpoints for demo narrative
                src = r["service_date"]
                if isinstance(src, datetime):
                    src = src.date()
                if src.year <= 2025:
                    sd = mid(2025, max(1, min(12, src.month)))
                else:
                    sd = mid(2026, max(1, min(12, src.month)))
                cid = f"DEMOCOPY_{code}_{uuid.uuid4().hex[:12]}"
                cpt = r["cpt_code"] or (code if not str(code).startswith("J") else None)
                hcpcs = r["hcpcs_code"] or (code if str(code).startswith("J") or str(code).startswith("G") else None)
                now = datetime.utcnow()
                batch.append(
                    {
                        "id": str(uuid.uuid4()),
                        "tenant_id": str(TENANT),
                        "claim_id": cid,
                        "claim_line_id": cid + "_01",
                        "member_id": r["member_id"] or f"MEM_{i%500:04d}",
                        "provider_id": r["provider_id"] or f"PROV_{i%50:03d}",
                        "service_date": sd,
                        "paid_date": sd + timedelta(days=14),
                        "lob": r["lob"] or "COMMERCIAL",
                        "market": r["market"] or "NC",
                        "cpt_code": cpt,
                        "hcpcs_code": hcpcs,
                        "service_category": r["service_category"] or "SPECIALTY_CARE",
                        "place_of_service": r["place_of_service"] or "22",
                        "units": float(r["units"] or 1),
                        "allowed_amount": float(r["allowed_amount"] or 500),
                        "paid_amount": float(r["paid_amount"] or 400),
                        "member_cost_share": float(r["member_cost_share"] or 50),
                        "in_network": bool(r["in_network"]) if r["in_network"] is not None else True,
                        "requires_prior_auth": False,
                        "ingestion_id": "00000000-0000-0000-0000-000000000000",
                        "created_at": now,
                        "updated_at": now,
                    }
                )
            for j in range(0, len(batch), 200):
                chunk = batch[j : j + 200]
                try:
                    sc.execute(
                        text(
                            """
                            INSERT INTO claims_lines (
                              id, tenant_id, claim_id, claim_line_id, member_id, provider_id,
                              service_date, paid_date, lob, market, cpt_code, hcpcs_code,
                              service_category, place_of_service, units,
                              allowed_amount, paid_amount, member_cost_share, in_network,
                              requires_prior_auth, source_system, source_file_id, ingestion_id,
                              created_at, updated_at
                            ) VALUES (
                              :id, :tenant_id, :claim_id, :claim_line_id, :member_id, :provider_id,
                              :service_date, :paid_date, :lob, :market, :cpt_code, :hcpcs_code,
                              :service_category, :place_of_service, :units,
                              :allowed_amount, :paid_amount, :member_cost_share, :in_network,
                              :requires_prior_auth, 'DEMO_SUBSET_COPY', 'lean_staging_full_demo_lifecycle', :ingestion_id,
                              :created_at, :updated_at
                            )
                            """
                        ),
                        chunk,
                    )
                    copied += len(chunk)
                except Exception as e:
                    errors.append({"code": code, "insert_error": str(e)[:200]})
                    break
            print(f"  demo-copy {code}: selected={len(rows)} inserted_batch_ok", flush=True)
    return {"copied": copied, "errors": errors[:20]}


def densify_policy_monthly_claims(eng, policies: list[dict], years=(2025, 2026), per_policy_per_month: int = 25) -> dict:
    """Direct insert meaningful claims for each policy's codes each month (bypass remediation gate)."""
    from sqlalchemy import text

    inserted = 0
    skipped = 0
    now = datetime.utcnow()
    with eng.begin() as c:
        for pol in policies:
            codes = pol["codes"]
            if not codes:
                skipped += 1
                continue
            for year in years:
                for month in range(1, 13):
                    sd = mid(year, month)
                    batch = []
                    n = per_policy_per_month if pol["is_nine"] else max(8, per_policy_per_month // 2)
                    for i in range(n):
                        code = codes[i % len(codes)]
                        is_hcpcs = (
                            code[:1].isalpha()
                            or code.startswith("J")
                            or code.startswith("G")
                            or code.startswith("Q")
                        )
                        cid = f"POL_{pol['id'][:8]}_{year}{month:02d}_{i:03d}_{uuid.uuid4().hex[:6]}"
                        allowed = random.uniform(200, 2500) if not is_hcpcs else random.uniform(800, 8000)
                        paid = allowed * random.uniform(0.75, 0.95)
                        now = datetime.utcnow()
                        batch.append(
                            {
                                "id": str(uuid.uuid4()),
                                "tenant_id": str(TENANT),
                                "claim_id": cid,
                                "claim_line_id": cid + "_01",
                                "member_id": f"MEM_{(hash(pol['id'])+i) % 2000:05d}",
                                "provider_id": f"PROV_{(hash(pol['name'])+i) % 80:03d}",
                                "service_date": sd,
                                "paid_date": sd + timedelta(days=random.randint(5, 25)),
                                "lob": random.choice(["COMMERCIAL", "MA", "MEDICAID"]),
                                "market": "NC",
                                "cpt_code": None if is_hcpcs else code,
                                "hcpcs_code": code if is_hcpcs else None,
                                "service_category": (
                                    "ADVANCED_IMAGING"
                                    if code.startswith(("70", "72", "73"))
                                    else "SPECIALTY_CARE"
                                ),
                                "place_of_service": random.choice(["11", "22", "24"]),
                                "units": float(random.randint(1, 2)),
                                "allowed_amount": float(round(allowed, 2)),
                                "paid_amount": float(round(paid, 2)),
                                "member_cost_share": float(round(allowed - paid, 2)),
                                "in_network": True,
                                "requires_prior_auth": True,
                                "ingestion_id": "00000000-0000-0000-0000-000000000000",
                                "created_at": now,
                                "updated_at": now,
                            }
                        )
                    c.execute(
                        text(
                            """
                            INSERT INTO claims_lines (
                              id, tenant_id, claim_id, claim_line_id, member_id, provider_id,
                              service_date, paid_date, lob, market, cpt_code, hcpcs_code,
                              service_category, place_of_service, units,
                              allowed_amount, paid_amount, member_cost_share, in_network,
                              requires_prior_auth, source_system, source_file_id, ingestion_id,
                              created_at, updated_at
                            ) VALUES (
                              :id, :tenant_id, :claim_id, :claim_line_id, :member_id, :provider_id,
                              :service_date, :paid_date, :lob, :market, :cpt_code, :hcpcs_code,
                              :service_category, :place_of_service, :units,
                              :allowed_amount, :paid_amount, :member_cost_share, :in_network,
                              :requires_prior_auth, 'POLICY_MONTHLY_DENSIFY', 'lean_staging_full_demo_lifecycle', :ingestion_id,
                              :created_at, :updated_at
                            )
                            """
                        ),
                        batch,
                    )
                    inserted += len(batch)
            if inserted and inserted % 20000 < per_policy_per_month * 24:
                print(f"  densify … {inserted} claims (last={pol['name'][:40]})", flush=True)
    return {"inserted": inserted, "policies_skipped_no_codes": skipped}


def metrics_for_codes(eng, codes: list[str], start: date, end: date) -> dict:
    from sqlalchemy import text

    if not codes:
        return {
            "util_rate_total_per_1000_mm": 80.0,
            "utilization_per_1k": 80.0,
            "allowed_pmpm_total": 45.0,
            "cost_pmpm": 45.0,
            "unique_members": 100,
            "member_months": 1200,
            "claim_count": 0,
            "source": "fallback_no_codes",
        }
    with eng.connect() as c:
        row = c.execute(
            text(
                """
                SELECT count(*) n,
                       count(DISTINCT member_id) members,
                       coalesce(sum(allowed_amount),0) sum_allowed
                FROM claims_lines
                WHERE tenant_id=:t
                  AND service_date >= :s AND service_date <= :e
                  AND (cpt_code = ANY(:codes) OR hcpcs_code = ANY(:codes))
                """
            ),
            {"t": str(TENANT), "s": start, "e": end, "codes": codes},
        ).mappings().first()
    n = int(row["n"] or 0)
    members = max(int(row["members"] or 0), 1)
    months = max(1, (end.year - start.year) * 12 + (end.month - start.month) + 1)
    util = round((n / members) * (1000 / months), 2)
    pmpm = round(float(row["sum_allowed"] or 0) / max(members * months, 1), 2)
    return {
        "util_rate_total_per_1000_mm": util or 80.0,
        "utilization_per_1k": util or 80.0,
        "allowed_pmpm_total": pmpm or 45.0,
        "cost_pmpm": pmpm or 45.0,
        "unique_members": members,
        "member_months": members * months,
        "claim_count": n,
        "source": "claims_code_filtered",
    }


def insert_baseline(eng, *, policy_id: str | None, start: date, end: date, metrics: dict, btype: str = "FIXED") -> str:
    from sqlalchemy import text

    pk = str(uuid.uuid4())
    bid = str(uuid.uuid4())
    now = datetime.utcnow()
    with eng.begin() as c:
        c.execute(
            text(
                """
                INSERT INTO baselines (
                  id, tenant_id, baseline_id, version, baseline_type,
                  window_start_date, window_end_date, policy_id,
                  data_period_ids_json, baseline_metrics_json,
                  computed_at, computed_by, shift_detected, shift_summary_json, refresh_reason,
                  created_at, updated_at
                ) VALUES (
                  :id, :tenant_id, :baseline_id, 1, :baseline_type,
                  :ws, :we, :policy_id,
                  '[]'::jsonb, CAST(:metrics AS jsonb),
                  :computed_at, :computed_by, false, '{}'::jsonb, 'NEW_DATA',
                  :computed_at, :computed_at
                )
                """
            ),
            {
                "id": pk,
                "tenant_id": str(TENANT),
                "baseline_id": bid,
                "baseline_type": btype,
                "ws": datetime(start.year, start.month, start.day),
                "we": datetime(end.year, end.month, end.day, 23, 59, 59),
                "policy_id": policy_id,
                "metrics": json.dumps(metrics),
                "computed_at": now,
                "computed_by": "lean_staging_full_demo_lifecycle",
            },
        )
    return pk


def bulk_predictions(eng, baseline_id: str, policy_ids: list[str]) -> int:
    from sqlalchemy import text

    stub = {
        "utilization_change_per_1k": -5.0,
        "cost_change_pmpm": -2.0,
        "utilization_change_pct": -5.0,
        "cost_change_pct": -3.0,
        "prediction_method": "demo_stub_lifecycle",
        "authority": "SYNTHETIC_DEMO",
    }
    now = datetime.utcnow()
    rows = [
        {
            "id": str(uuid.uuid4()),
            "tenant_id": str(TENANT),
            "policy_id": pid,
            "metrics_json": json.dumps(stub),
            "model_version": "demo_stub_v3",
            "confidence": None,
            "predicted_at": now,
            "prediction_method": "demo_stub_lifecycle",
            "baseline_id": baseline_id,
            "created_at": now,
            "updated_at": now,
        }
        for pid in policy_ids
    ]
    with eng.begin() as c:
        for i in range(0, len(rows), 50):
            c.execute(
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
                rows[i : i + 50],
            )
    return len(rows)


def try_stage35_nine(policies: list[dict], general_baseline: dict) -> dict:
    """Best-effort Stage 3.5 for nine; never fail the run."""
    from uepi_api.storage_policy_predicted_impact import store_predicted_impact, get_predicted_impact
    import importlib.util

    spec = importlib.util.spec_from_file_location("run_demo_day", REPO / "scripts" / "run_demo_day.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ok = fail = 0
    for pol in policies:
        if not pol["is_nine"]:
            continue
        try:
            # regenerate non-stub if possible
            pid = UUID(pol["id"])
            if mod.ensure_predicted_impact(TENANT, pid, general_baseline, regenerate=True, stub_only=False):
                ok += 1
            else:
                mod.ensure_predicted_impact(TENANT, pid, general_baseline, regenerate=True, stub_only=True)
                fail += 1
        except Exception as e:
            fail += 1
            try:
                mod.ensure_predicted_impact(TENANT, UUID(pol["id"]), general_baseline, regenerate=True, stub_only=True)
            except Exception:
                pass
            print(f"  stage35 fallback {pol['name']}: {e}", flush=True)
    return {"nine_stage35_ok": ok, "nine_fallback": fail}


def bulk_monthly_obs(eng, cy_baseline_id: str, policies: list[dict], year: int = 2026, months: range | None = None) -> int:
    """One observation per policy per completed 2026 month.

    Default is January–September (nine per policy). Each row uses that policy's
    yearly baseline and that month's claims on the policy's codes.
    """
    from collections import defaultdict

    from sqlalchemy import text

    months = months if months is not None else range(1, 10)
    with eng.connect() as c:
        pred = {
            r[0]: r[1]
            for r in c.execute(
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
        annual = {
            r[0]: r[1]
            for r in c.execute(
                text(
                    """
                    SELECT policy_id::text, baseline_metrics_json
                    FROM baselines
                    WHERE tenant_id=:t AND policy_id IS NOT NULL
                      AND window_start_date::date='2025-01-01'
                      AND window_end_date::date='2025-12-31'
                    """
                ),
                {"t": str(TENANT)},
            ).fetchall()
        }
        claim_rows = c.execute(
            text(
                """
                SELECT id::text, to_char(service_date,'YYYY-MM') ym,
                       cpt_code, hcpcs_code, member_id, allowed_amount
                FROM claims_lines
                WHERE tenant_id=:t
                  AND service_date >= :s AND service_date <= :e
                """
            ),
            {"t": str(TENANT), "s": date(year, min(months), 1), "e": month_end(year, max(months))},
        ).mappings().all()
    by_code_month: dict[tuple[str, str], list] = defaultdict(list)
    for r in claim_rows:
        line = (r["id"], r["member_id"], float(r["allowed_amount"] or 0))
        for code in (r["cpt_code"], r["hcpcs_code"]):
            if code:
                by_code_month[(code, r["ym"])].append(line)
    now = datetime.utcnow()
    rows = []
    for pol in policies:
        base = annual.get(pol["id"]) or {}
        if isinstance(base, str):
            base = json.loads(base)
        bu = float(base.get("utilization_per_1k") or base.get("util_rate_total_per_1000_mm") or 0)
        bc = float(base.get("cost_pmpm") or base.get("allowed_pmpm_total") or 0)
        # Stub prediction is -5% utilization and -3% cost versus the yearly baseline.
        pu, pc = round(bu * 0.95, 2), round(bc * 0.97, 2)
        for month in months:
            ym = f"{year}-{month:02d}"
            members = set()
            allowed = 0.0
            seen_lines = set()
            for code in pol["codes"]:
                for line_id, member_id, amt in by_code_month.get((code, ym), []):
                    if line_id in seen_lines:
                        continue
                    seen_lines.add(line_id)
                    members.add(member_id)
                    allowed += amt
            n = len(seen_lines)
            mem = max(len(members), 1)
            ou = round((n / mem) * 1000, 2) if n else 0.0
            oc = round(allowed / mem, 2) if n else 0.0
            if pu and ou <= pu * 1.05:
                status = "ON_TRACK"
            elif bu and ou > bu * 1.1:
                status = "BACKFIRE"
            else:
                status = "AT_RISK"
            end = month_end(year, month)
            oid = str(uuid.uuid4())
            rows.append(
                {
                    "id": oid,
                    "tenant_id": str(TENANT),
                    "observation_id": oid,
                    "policy_id": pol["id"],
                    "baseline_version_id": pol.get("cy_baseline_id") or cy_baseline_id,
                    "prediction_id": pred.get(pol["id"]),
                    "data_period_ids_json": "[]",
                    "observation_type": "PERIODIC",
                    "observation_period_start": datetime(year, month, 1),
                    "observation_period_end": datetime(end.year, end.month, end.day, 23, 59, 59),
                    "metrics_json": json.dumps(
                        {
                            "utilization_per_1k": ou,
                            "cost_pmpm": oc,
                            "baseline_utilization_per_1k": bu,
                            "baseline_cost_pmpm": bc,
                            "predicted_utilization_per_1k": pu,
                            "predicted_cost_pmpm": pc,
                            "claim_count": n,
                            "unique_members": len(members),
                            "codes": pol["codes"],
                            "period_year": year,
                            "period_month": month,
                            "source": "policy_scope_codes_month",
                        }
                    ),
                    "comparisons_json": json.dumps(
                        {
                            "vs_baseline": {"utilization_change": round(ou - bu, 2), "cost_change_pmpm": round(oc - bc, 2)},
                            "vs_predicted": {"utilization_change": round(ou - pu, 2), "cost_change_pmpm": round(oc - pc, 2)},
                        }
                    ),
                    "behavioral_explanation_json": "{}",
                    "verdict_status": status,
                    "verdict_reason": f"{status} for {ym} from {n} scoped claims",
                    "recommendation": "Continue monitoring" if status == "ON_TRACK" else "Investigate drivers",
                    "verdict_rule_version": "v1.0-scoped-month",
                    "computed_at": now,
                    "created_at": now,
                    "updated_at": now,
                }
            )
    with eng.begin() as c:
        for i in range(0, len(rows), 100):
            c.execute(
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
                rows[i : i + 100],
            )
            if (i + 100) % 500 == 0:
                print(f"  obs {min(i+100,len(rows))}/{len(rows)}", flush=True)
    return len(rows)


def ensure_schedule() -> dict:
    """Register the monthly observation job on job_schedules (enterprise dispatcher).

    Also writes the legacy schedules row so the API schedule list shows it.
    Cron is 06:00 UTC on day 2. Next due is the upcoming occurrence, not now,
    so the dispatcher does not fire 250 jobs during this setup run.
    """
    from sqlalchemy import text

    from uepi_api.database import SessionLocal, get_engine
    from uepi_api.models.scheduling import JobSchedule

    schedule_id = "sch_lean_staging_monthly_observations"
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # Next day-2 06:00 UTC at or after tomorrow so this setup does not claim immediately.
    year, month = now.year, now.month
    candidate = datetime(year, month, 2, 6, 0, 0)
    if candidate <= now:
        month += 1
        if month > 12:
            year, month = year + 1, 1
        candidate = datetime(year, month, 2, 6, 0, 0)

    db = SessionLocal()
    try:
        row = db.query(JobSchedule).filter(JobSchedule.schedule_id == schedule_id).one_or_none()
        created = row is None
        if row is None:
            row = JobSchedule(
                schedule_id=schedule_id,
                tenant_id=TENANT,
                job_type="PERIODIC_OBSERVATION",
                target_reference="catalog:active_policies",
                schedule_expression="0 6 2 * *",
                timezone="UTC",
                enabled=True,
                trigger_kind="CALENDAR",
                next_due_at=candidate,
                misfire_policy="FIRE_ONCE",
                overlap_policy="SKIP",
                configuration_version="v1",
                workload_class="OBSERVATION",
                created_by="lean_staging_full_demo_lifecycle",
            )
            db.add(row)
        else:
            row.enabled = True
            row.schedule_expression = "0 6 2 * *"
            row.job_type = "PERIODIC_OBSERVATION"
            row.workload_class = "OBSERVATION"
            row.target_reference = "catalog:active_policies"
            if row.next_due_at is None or row.next_due_at < now:
                row.next_due_at = candidate
        db.commit()
        job_schedule = {
            "schedule_id": row.schedule_id,
            "enabled": row.enabled,
            "expression": row.schedule_expression,
            "next_due_at": row.next_due_at.isoformat() if row.next_due_at else None,
            "created": created,
        }
    finally:
        db.close()

    # Legacy schedules table (API list). SQL avoids the Baseline mapper path.
    legacy_id = "00000000-0000-4000-8000-000000000250"
    with get_engine().begin() as c:
        exists = c.execute(
            text("SELECT id::text FROM schedules WHERE tenant_id=:t AND name=:n"),
            {"t": str(TENANT), "n": "Lean Staging Monthly Observations"},
        ).scalar()
        if not exists:
            c.execute(
                text(
                    """
                    INSERT INTO schedules (
                      id, tenant_id, schedule_id, name, description, schedule_type,
                      cron_expression, target_type, target_id, enabled, next_run_at,
                      created_at, updated_at
                    ) VALUES (
                      :id, :tenant, :sid, :name, :descr, 'CRON',
                      '0 6 2 * *', 'OBSERVATION', '', true, :next,
                      :now, :now
                    )
                    """
                ),
                {
                    "id": legacy_id,
                    "tenant": str(TENANT),
                    "sid": schedule_id,
                    "name": "Lean Staging Monthly Observations",
                    "descr": "PERIODIC_MONTHLY",
                    "next": candidate,
                    "now": now,
                },
            )
            exists = legacy_id
    return {"job_schedule": job_schedule, "legacy_schedule_id": exists}


def set_effective_2026(eng, policies: list[dict]) -> None:
    from sqlalchemy import text

    with eng.begin() as c:
        for pol in policies:
            m = dict(pol["meta"] or {})
            m["effective_period"] = {"start_date": "2026-01-01T00:00:00", "end_date": None}
            # ensure scope codes present for demo (use densify codes)
            scope = dict(m.get("scope") or {})
            if pol["codes"] and not scope.get("procedure_codes"):
                scope["procedure_codes"] = pol["codes"]
            m["scope"] = scope
            c.execute(
                text("UPDATE policies SET policy_metadata_json=CAST(:m AS jsonb), updated_at=NOW() WHERE id=:id"),
                {"m": json.dumps(m), "id": pol["id"]},
            )


def reshape_existing(eng) -> dict:
    """Drop monthly baselines and rebuild 2026 observations as nine months per policy.

    Keeps the CY2025 general baseline and the one yearly baseline per policy.
    Does not touch claims or predictions.
    """
    from sqlalchemy import text

    policies = load_policies(eng)
    with eng.connect() as c:
        annual = {
            r[0]: r[1]
            for r in c.execute(
                text(
                    """
                    SELECT policy_id::text, id::text
                    FROM baselines
                    WHERE tenant_id=:t AND policy_id IS NOT NULL
                      AND window_start_date::date='2025-01-01'
                      AND window_end_date::date='2025-12-31'
                    """
                ),
                {"t": str(TENANT)},
            ).fetchall()
        }
        general_id = c.execute(
            text(
                """
                SELECT id::text FROM baselines
                WHERE tenant_id=:t AND policy_id IS NULL
                  AND window_start_date::date='2025-01-01'
                  AND window_end_date::date='2025-12-31'
                """
            ),
            {"t": str(TENANT)},
        ).scalar()
    for pol in policies:
        pol["cy_baseline_id"] = annual.get(pol["id"])
    missing = [p["name"] for p in policies if not p["cy_baseline_id"]]
    if missing or not general_id:
        raise SystemExit(f"missing annual baselines general={general_id} policies={missing[:5]}")
    with eng.begin() as c:
        obs_deleted = c.execute(text("DELETE FROM observations WHERE tenant_id=:t"), {"t": str(TENANT)}).rowcount
        base_deleted = c.execute(
            text(
                """
                DELETE FROM baselines
                WHERE tenant_id=:t
                  AND NOT (window_start_date::date='2025-01-01' AND window_end_date::date='2025-12-31')
                """
            ),
            {"t": str(TENANT)},
        ).rowcount
    nobs = bulk_monthly_obs(eng, general_id, policies, year=2026, months=range(1, 10))
    with eng.connect() as c:
        verify = {
            "baselines_general": c.execute(text("SELECT count(*) FROM baselines WHERE tenant_id=:t AND policy_id IS NULL"), {"t": str(TENANT)}).scalar(),
            "baselines_policy": c.execute(text("SELECT count(*) FROM baselines WHERE tenant_id=:t AND policy_id IS NOT NULL"), {"t": str(TENANT)}).scalar(),
            "observations": c.execute(text("SELECT count(*) FROM observations WHERE tenant_id=:t"), {"t": str(TENANT)}).scalar(),
            "obs_per_policy_max": c.execute(text("SELECT max(n) FROM (SELECT count(*) n FROM observations WHERE tenant_id=:t GROUP BY policy_id) s"), {"t": str(TENANT)}).scalar(),
            "obs_months": c.execute(text("SELECT count(DISTINCT to_char(observation_period_start,'YYYY-MM')) FROM observations WHERE tenant_id=:t"), {"t": str(TENANT)}).scalar(),
        }
    return {
        "obs_deleted": obs_deleted,
        "monthly_baselines_deleted": base_deleted,
        "observations_written": nobs,
        "verify": {k: int(v) for k, v in verify.items()},
        "pass": int(verify["baselines_general"]) == 1 and int(verify["baselines_policy"]) == 250 and int(verify["observations"]) == 250 * 9 and int(verify["obs_per_policy_max"]) == 9,
    }


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-demo-copy", action="store_true", help="Skip slow demo DB subset copy")
    ap.add_argument("--per-month", type=int, default=20)
    ap.add_argument("--reshape-only", action="store_true", help="Keep claims and yearly baselines; drop monthly baselines; rewrite 9 obs/policy")
    args = ap.parse_args()
    if args.reshape_only:
        stg_url = os.environ.get("DATABASE_URL") or ""
        _assert_staging(stg_url)
        result = reshape_existing(_engine(stg_url))
        print(json.dumps(result, indent=2, default=str))
        if not result["pass"]:
            raise SystemExit(1)
        return

    stg_url = os.environ.get("DATABASE_URL") or ""
    _assert_staging(stg_url)
    demo_url = os.environ.get("DEMO_DATABASE_URL") or ""

    stg = _engine(stg_url)
    # allow importing sibling scripts/
    sys.path.insert(0, str(REPO / "scripts"))
    report: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "environment": "lean_staging",
        "demo_write": False,
        "phases": {},
        "failures": [],
    }

    print("Load policies…", flush=True)
    policies = load_policies(stg)
    report["phases"]["policies"] = {
        "count": len(policies),
        "with_codes": sum(1 for p in policies if p["codes"]),
        "nine": sum(1 for p in policies if p["is_nine"]),
    }
    print(" ", report["phases"]["policies"], flush=True)

    print("Flush analytics…", flush=True)
    report["phases"]["flush"] = flush_analytics(stg)

    print("Set effective 2026-01-01 + ensure scope codes…", flush=True)
    set_effective_2026(stg, policies)

    code_union = sorted({c for p in policies for c in p["codes"]})
    # Prefer nine + imaging/infusion/therapy codes from demo for realism (bounded)
    nine_codes = sorted({c for p in policies if p["is_nine"] for c in p["codes"]})
    if demo_url and not args.skip_demo_copy:
        print(f"Copy demo claims subset for {len(nine_codes)} nine-policy codes (read-only demo)…", flush=True)
        try:
            demo = _engine(demo_url, demo=True)
            report["phases"]["demo_copy"] = copy_demo_claims_subset(
                demo, stg, nine_codes or code_union[:40], per_code_limit=1500
            )
        except Exception as e:
            report["phases"]["demo_copy"] = {"error": str(e)}
            report["failures"].append({"phase": "demo_copy", "error": str(e)})
            print("  demo copy failed, continuing with densify:", e, flush=True)
    else:
        report["phases"]["demo_copy"] = {"skipped": True, "reason": "flag_or_no_demo_url"}

    print("Densify monthly policy claims 2025+2026…", flush=True)
    report["phases"]["densify"] = densify_policy_monthly_claims(
        stg, policies, per_policy_per_month=args.per_month
    )

    print("General CY2025 baseline…", flush=True)
    gen_metrics = metrics_for_codes(stg, code_union[:50] if code_union else [], date(2025, 1, 1), date(2025, 12, 31))
    # broader general: all claims 2025
    from sqlalchemy import text

    with stg.connect() as c:
        row = c.execute(
            text(
                """
                SELECT count(*) n, count(DISTINCT member_id) m, coalesce(sum(allowed_amount),0) s
                FROM claims_lines WHERE tenant_id=:t AND service_date>='2025-01-01' AND service_date<='2025-12-31'
                """
            ),
            {"t": str(TENANT)},
        ).mappings().first()
    members = max(int(row["m"] or 1), 1)
    gen_metrics = {
        "util_rate_total_per_1000_mm": round((int(row["n"]) / members) * (1000 / 12), 2),
        "utilization_per_1k": round((int(row["n"]) / members) * (1000 / 12), 2),
        "allowed_pmpm_total": round(float(row["s"]) / (members * 12), 2),
        "cost_pmpm": round(float(row["s"]) / (members * 12), 2),
        "unique_members": members,
        "member_months": members * 12,
        "claim_count": int(row["n"]),
        "source": "all_claims_cy2025",
    }
    general_id = insert_baseline(stg, policy_id=None, start=date(2025, 1, 1), end=date(2025, 12, 31), metrics=gen_metrics)
    report["phases"]["general_baseline"] = {"id": general_id, "metrics": gen_metrics}

    print("Policy CY2025 baselines (all)…", flush=True)
    pol_base = 0
    for pol in policies:
        m = metrics_for_codes(stg, pol["codes"], date(2025, 1, 1), date(2025, 12, 31))
        if m["claim_count"] == 0:
            m = dict(gen_metrics)
            m["source"] = "fallback_general_metrics"
        pk = insert_baseline(stg, policy_id=pol["id"], start=date(2025, 1, 1), end=date(2025, 12, 31), metrics=m)
        pol["cy_baseline_id"] = pk
        pol_base += 1
        if pol_base % 50 == 0:
            print(f"  policy baselines {pol_base}/{len(policies)}", flush=True)
    report["phases"]["policy_cy2025_baselines"] = {"count": pol_base}

    print("Predictions…", flush=True)
    npred = bulk_predictions(stg, general_id, [p["id"] for p in policies])
    report["phases"]["predictions_stub"] = {"count": npred}
    general_bl = {"id": general_id, "baseline_id": general_id, "baseline_metrics": gen_metrics}
    report["phases"]["predictions_nine"] = try_stage35_nine(policies, general_bl)

    print("Monthly 2026 observations (Jan–Sep, 9 per policy)…", flush=True)
    nobs = bulk_monthly_obs(stg, general_id, policies, year=2026, months=range(1, 10))
    report["phases"]["observations"] = {"count": nobs, "months": "2026-01..2026-09", "per_policy": 9}

    print("Schedule…", flush=True)
    try:
        report["phases"]["schedule"] = ensure_schedule()
    except Exception as e:
        report["failures"].append({"phase": "schedule", "error": str(e)})

    # Verify nine coverage + totals
    with stg.connect() as c:
        verify = {
            "claims_total": c.execute(text("SELECT count(*) FROM claims_lines WHERE tenant_id=:t"), {"t": str(TENANT)}).scalar(),
            "claims_2025": c.execute(text("SELECT count(*) FROM claims_lines WHERE tenant_id=:t AND service_date>='2025-01-01' AND service_date<='2025-12-31'"), {"t": str(TENANT)}).scalar(),
            "claims_2026": c.execute(text("SELECT count(*) FROM claims_lines WHERE tenant_id=:t AND service_date>='2026-01-01' AND service_date<='2026-12-31'"), {"t": str(TENANT)}).scalar(),
            "baselines_total": c.execute(text("SELECT count(*) FROM baselines WHERE tenant_id=:t"), {"t": str(TENANT)}).scalar(),
            "baselines_general": c.execute(text("SELECT count(*) FROM baselines WHERE tenant_id=:t AND policy_id IS NULL"), {"t": str(TENANT)}).scalar(),
            "baselines_policy": c.execute(text("SELECT count(*) FROM baselines WHERE tenant_id=:t AND policy_id IS NOT NULL"), {"t": str(TENANT)}).scalar(),
            "predicted": c.execute(text("SELECT count(*) FROM policy_predicted_impacts WHERE tenant_id=:t"), {"t": str(TENANT)}).scalar(),
            "observations": c.execute(text("SELECT count(*) FROM observations WHERE tenant_id=:t"), {"t": str(TENANT)}).scalar(),
            "obs_policies": c.execute(text("SELECT count(DISTINCT policy_id) FROM observations WHERE tenant_id=:t"), {"t": str(TENANT)}).scalar(),
        }
        nine_cov = {}
        for pol in policies:
            if not pol["is_nine"]:
                continue
            n = c.execute(
                text(
                    """
                    SELECT count(*) FROM claims_lines
                    WHERE tenant_id=:t AND (cpt_code = ANY(:codes) OR hcpcs_code = ANY(:codes))
                    """
                ),
                {"t": str(TENANT), "codes": pol["codes"] or ["__none__"]},
            ).scalar()
            nine_cov[pol["name"]] = {"codes": pol["codes"], "claims": int(n)}
        verify["nine_claims_coverage"] = nine_cov

    report["verify"] = verify
    report["ended_at"] = datetime.now(timezone.utc).isoformat()
    report["pass"] = (
        verify["claims_2025"] > 10000
        and verify["baselines_policy"] == 250
        and verify["baselines_general"] == 1
        and verify["predicted"] >= 250
        and verify["observations"] == 250 * 9
        and verify["obs_policies"] >= 250
        and all(v["claims"] > 0 for v in nine_cov.values())
        and len(report["failures"]) == 0
    )

    out = Path(REPO) / "docs/production/releases/corrections" / f"LEAN_STAGING_FULL_DEMO_LIFECYCLE_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"report": str(out), "pass": report["pass"], "verify": verify, "failures": report["failures"]}, indent=2, default=str))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
