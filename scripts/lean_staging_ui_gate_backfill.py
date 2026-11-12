#!/usr/bin/env python3
"""Backfill lean-staging rows so the product UI can pass a manual review gate.

Fixes (no fabricated policy savings):
1) predicted impacts — surface CONTINUATION forecasts (continuation_allowed_change=0 rate freeze,
   predicted_allowed from horizon totals)
2) observations — UI aliases + vs_baseline / vs_predicted from stored vs_continuation + baseline
3) baselines — provider_archetypes + patient_segments from scoped claims

Refuses any database that is not hfleanstg.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import psycopg2
from psycopg2.extras import Json, RealDictCursor, execute_batch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api" / "src"))
sys.path.insert(0, str(REPO / "packages" / "common" / "src"))

from uepi_api.baseline_segmentation_from_claims import (  # noqa: E402
    patient_segments_from_claims_df,
    provider_archetypes_from_claims_df,
    provider_archetypes_volume_bands_from_claims_df,
)

TENANT = "00000000-0000-0000-0000-000000000001"
OUT = REPO / "docs/production/releases/corrections/reviewed_248/UI_GATE_BACKFILL_REPORT.json"


def _db_url() -> str:
    raw = subprocess.check_output(
        [
            "az",
            "keyvault",
            "secret",
            "show",
            "--vault-name",
            "hfleanstgkv",
            "--name",
            "lean-staging-database-url",
            "--query",
            "value",
            "-o",
            "tsv",
        ],
        text=True,
    ).strip()
    url = raw.replace("postgresql+psycopg2://", "postgresql://", 1)
    if "hfleanstg" not in url.lower():
        raise SystemExit("Refusing: not lean staging")
    return url


def _pct(numer: Optional[float], denom: Optional[float]) -> Optional[float]:
    if numer is None or denom is None or denom == 0:
        return None
    return (float(numer) / float(denom)) * 100.0


def _backfill_predictions(cur) -> Dict[str, Any]:
    cur.execute(
        """
        SELECT id, metrics_json, prediction_method
        FROM policy_predicted_impacts
        WHERE tenant_id = %s::uuid
        """,
        (TENANT,),
    )
    rows = cur.fetchall()
    updated = 0
    for row in rows:
        metrics = row["metrics_json"] or {}
        if isinstance(metrics, str):
            metrics = json.loads(metrics)
        if not isinstance(metrics, dict):
            metrics = {}
        # Unwrap accidental nesting
        inner = metrics.get("metrics") if isinstance(metrics.get("metrics"), dict) else None
        work = dict(inner) if inner else dict(metrics)
        continuation = work.get("continuation") if isinstance(work.get("continuation"), dict) else {}
        horizon = continuation.get("horizon_totals") if isinstance(continuation.get("horizon_totals"), dict) else {}

        changed = False
        if work.get("predicted_allowed") is None and horizon.get("predicted_allowed") is not None:
            work["predicted_allowed"] = float(horizon["predicted_allowed"])
            changed = True
        if work.get("predicted_services") is None and horizon.get("predicted_services") is not None:
            work["predicted_services"] = float(horizon["predicted_services"])
            changed = True
        # Rate-freeze continuation: allowed change from rates is 0 (not policy savings).
        is_continuation = (
            str(work.get("prediction_type") or "").upper() == "CONTINUATION"
            or str(row["prediction_method"] or "").upper().startswith("HISTORICAL_RATE_CONTINUATION")
            or continuation.get("status") == "AVAILABLE"
        )
        if is_continuation and work.get("continuation_allowed_change") is None:
            work["continuation_allowed_change"] = 0.0
            changed = True
        if is_continuation and not work.get("prediction_type"):
            work["prediction_type"] = "CONTINUATION"
            changed = True
        if work.get("cost_change_meaning") is None and is_continuation:
            work["cost_change_meaning"] = "UNESTIMATED_POLICY_EFFECT"
            changed = True

        if not changed:
            continue

        # Preserve top-level shape used by writers (flat CONTINUATION payload).
        if inner is not None:
            metrics["metrics"] = work
            new_metrics = metrics
        else:
            new_metrics = work
        cur.execute(
            """
            UPDATE policy_predicted_impacts
            SET metrics_json = %s, updated_at = %s
            WHERE id = %s::uuid
            """,
            (Json(new_metrics), datetime.utcnow(), str(row["id"])),
        )
        updated += 1
    return {"predicted_impacts_scanned": len(rows), "predicted_impacts_updated": updated}


def _policy_codes(cur, policy_id: str) -> List[str]:
    cur.execute(
        "SELECT policy_metadata_json FROM policies WHERE id = %s::uuid",
        (policy_id,),
    )
    row = cur.fetchone()
    if not row:
        return []
    meta = row["policy_metadata_json"] or {}
    if isinstance(meta, str):
        meta = json.loads(meta)
    if not isinstance(meta, dict):
        return []
    codes: List[str] = []
    scope = meta.get("scope") or {}
    if isinstance(scope, dict):
        for c in scope.get("procedure_codes") or []:
            if c:
                codes.append(str(c))
    levers = meta.get("policy_levers") or []
    if isinstance(levers, list):
        for lever in levers:
            if not isinstance(lever, dict):
                continue
            targets = lever.get("targets") or {}
            for c in targets.get("codes") or []:
                if c:
                    codes.append(str(c))
    seen = set()
    out = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _claims_df(
    cur,
    *,
    codes: List[str],
    start,
    end,
    source_system: Optional[str],
) -> pd.DataFrame:
    params: List[Any] = [TENANT, start, end]
    clauses = [
        "tenant_id = %s::uuid",
        "service_date >= %s",
        "service_date <= %s",
    ]
    if codes:
        clauses.append("(cpt_code = ANY(%s) OR hcpcs_code = ANY(%s))")
        params.append(codes)
        params.append(codes)
    if source_system:
        clauses.append("source_system = %s")
        params.append(source_system)
    sql = f"""
        SELECT member_id,
               COALESCE(provider_id, rendering_provider_id, billing_provider_id) AS provider_id,
               COALESCE(cpt_code, hcpcs_code) AS procedure_code,
               service_category,
               allowed_amount, paid_amount, service_date, lob, market
        FROM claims_lines
        WHERE {' AND '.join(clauses)}
    """
    cur.execute(sql, params)
    rows = cur.fetchall()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


def _backfill_baselines(cur) -> Dict[str, Any]:
    cur.execute(
        """
        SELECT DISTINCT ON (b.policy_id)
          b.id, b.policy_id, b.baseline_metrics_json, b.window_start_date, b.window_end_date
        FROM baselines b
        WHERE b.tenant_id = %s::uuid
          AND b.policy_id IS NOT NULL
        ORDER BY b.policy_id, b.version DESC NULLS LAST, b.computed_at DESC NULLS LAST
        """,
        (TENANT,),
    )
    rows = cur.fetchall()
    updated = 0
    empty_claims = 0
    for row in rows:
        metrics = row["baseline_metrics_json"] or {}
        if isinstance(metrics, str):
            metrics = json.loads(metrics)
        if not isinstance(metrics, dict):
            metrics = {}
        force_segments = bool(globals().get("_FORCE_SEGMENT_REFRESH"))
        if (
            metrics.get("provider_archetypes")
            and metrics.get("patient_segments")
            and not force_segments
        ):
            continue
        codes = _policy_codes(cur, str(row["policy_id"]))
        book = metrics.get("measurement_book")
        df = _claims_df(
            cur,
            codes=codes,
            start=row["window_start_date"],
            end=row["window_end_date"],
            source_system=str(book) if book else None,
        )
        if df.empty and book:
            # fall back: same codes any book in window
            df = _claims_df(
                cur,
                codes=codes,
                start=row["window_start_date"],
                end=row["window_end_date"],
                source_system=None,
            )
        if df.empty:
            empty_claims += 1
            continue
        pa = provider_archetypes_volume_bands_from_claims_df(df, n_bands=6)
        if not pa:
            pa = provider_archetypes_from_claims_df(df, max_archetypes=8)
        ps = patient_segments_from_claims_df(df)
        if not pa and not ps:
            empty_claims += 1
            continue
        metrics = dict(metrics)
        if pa and (force_segments or not metrics.get("provider_archetypes")):
            metrics["provider_archetypes"] = pa
        if ps:
            metrics["patient_segments"] = ps
        metrics["segmentation_source"] = "claims_volume_bands_ui_gate_backfill"
        metrics["segmentation_backfilled_at"] = datetime.utcnow().isoformat() + "Z"
        cur.execute(
            """
            UPDATE baselines
            SET baseline_metrics_json = %s, updated_at = %s
            WHERE id = %s::uuid
            """,
            (Json(metrics), datetime.utcnow(), str(row["id"])),
        )
        updated += 1
    return {
        "baselines_scanned": len(rows),
        "baselines_updated": updated,
        "baselines_empty_claims": empty_claims,
    }


def _build_obs_comparisons(
    *,
    metrics: Dict[str, Any],
    baseline_metrics: Dict[str, Any],
    existing: Dict[str, Any],
) -> Dict[str, Any]:
    mm = float(metrics.get("member_months") or metrics.get("eligible_member_months") or 0)
    services = float(metrics.get("services") or metrics.get("total_claims") or 0)
    allowed = float(metrics.get("allowed_amount") or metrics.get("total_allowed") or 0)
    paid = float(metrics.get("paid_amount") or metrics.get("total_paid") or 0)
    obs_util_1k = (services / mm * 1000.0) if mm else None
    obs_allowed_pmpm = (allowed / mm) if mm else None
    obs_paid_pmpm = (paid / mm) if mm else None

    b_mm = float(baseline_metrics.get("member_months") or 0)
    b_claims = float(baseline_metrics.get("total_claims") or 0)
    b_allowed = float(baseline_metrics.get("total_allowed") or 0)
    b_paid = float(baseline_metrics.get("total_paid") or 0)
    # Annual baseline → monthly rate expectation at observed exposure
    base_util_1k = (b_claims / b_mm * 1000.0) if b_mm else None
    base_allowed_pmpm = (b_allowed / b_mm) if b_mm else None
    base_paid_pmpm = (b_paid / b_mm) if b_mm else None
    expected_base_services = (b_claims / b_mm * mm) if b_mm else None
    expected_base_allowed = (b_allowed / b_mm * mm) if b_mm else None

    util_change = (
        None if obs_util_1k is None or base_util_1k is None else obs_util_1k - base_util_1k
    )
    util_change_pct = _pct(util_change, base_util_1k)
    cost_change_pmpm = (
        None
        if obs_allowed_pmpm is None or base_allowed_pmpm is None
        else obs_allowed_pmpm - base_allowed_pmpm
    )
    cost_change_pct = _pct(cost_change_pmpm, base_allowed_pmpm)

    vs_cont = existing.get("vs_continuation") if isinstance(existing.get("vs_continuation"), dict) else {}
    frozen = vs_cont.get("frozen_prediction") if isinstance(vs_cont.get("frozen_prediction"), dict) else {}
    adj = vs_cont.get("exposure_adjusted") if isinstance(vs_cont.get("exposure_adjusted"), dict) else {}
    pred_services = frozen.get("services")
    if pred_services is None:
        pred_services = adj.get("expected_services")
    pred_allowed = frozen.get("allowed")
    if pred_allowed is None:
        pred_allowed = adj.get("expected_allowed")
    pred_mm = float(frozen.get("member_months") or mm or 0)
    pred_pmpm = frozen.get("allowed_pmpm")
    if pred_pmpm is None and pred_allowed is not None and pred_mm:
        pred_pmpm = float(pred_allowed) / pred_mm
    pred_util_1k = (float(pred_services) / pred_mm * 1000.0) if pred_services is not None and pred_mm else None

    pred_util_err = (
        None if obs_util_1k is None or pred_util_1k is None else obs_util_1k - pred_util_1k
    )
    pred_util_err_pct = _pct(pred_util_err, pred_util_1k)
    pred_cost_err = (
        None
        if obs_allowed_pmpm is None or pred_pmpm is None
        else float(obs_allowed_pmpm) - float(pred_pmpm)
    )
    accuracy = None
    if pred_allowed not in (None, 0) and allowed is not None:
        accuracy = max(0.0, 100.0 - abs((allowed - float(pred_allowed)) / float(pred_allowed) * 100.0))

    vs_baseline = {
        "observed_utilization_per_1k": obs_util_1k,
        "baseline_utilization_per_1k": base_util_1k,
        "utilization_change": util_change,
        "utilization_change_pct": util_change_pct,
        "change_from_baseline": util_change,
        "change_from_baseline_pct": util_change_pct,
        "observed_cost_pmpm": obs_allowed_pmpm,
        "baseline_cost_pmpm": base_allowed_pmpm,
        "cost_change_pmpm": cost_change_pmpm,
        "cost_change_pct": cost_change_pct,
        # Executive dashboard scales ΔPMPM by this exposure (policy-scoped books have no tenant-wide baseline).
        "baseline_member_months": mm if mm else (b_mm / 12.0 if b_mm else None),
        "note": "Observed vs CY baseline rate at actual exposure. Not policy-attributable savings.",
        "comparison_by_measure": {
            "util_rate_total_per_1000_mm": {
                "baseline": base_util_1k,
                "observed": obs_util_1k,
            },
            "allowed_pmpm_total": {
                "baseline": base_allowed_pmpm,
                "observed": obs_allowed_pmpm,
            },
            "paid_pmpm_total": {
                "baseline": base_paid_pmpm,
                "observed": obs_paid_pmpm,
            },
            "member_months": {"baseline": b_mm / 12.0 if b_mm else None, "observed": mm},
        },
    }
    vs_predicted = {
        "observed_utilization_per_1k": obs_util_1k,
        "predicted_utilization_per_1k": pred_util_1k,
        "utilization_change": pred_util_err,
        "utilization_change_pct": pred_util_err_pct,
        "prediction_error": pred_util_err,
        "prediction_error_pct": pred_util_err_pct,
        "prediction_accuracy_pct": accuracy,
        "observed_cost_pmpm": obs_allowed_pmpm,
        "predicted_cost_pmpm": pred_pmpm,
        "cost_change_pmpm": pred_cost_err,
        "frozen_predicted_services": pred_services,
        "frozen_predicted_allowed": pred_allowed,
        "note": "Observed vs frozen historical-rate continuation. Variance is not attributed policy savings.",
        "comparison_by_measure": {
            "util_rate_total_per_1000_mm": {
                "predicted": pred_util_1k,
                "observed": obs_util_1k,
            },
            "allowed_pmpm_total": {
                "predicted": pred_pmpm,
                "observed": obs_allowed_pmpm,
            },
            "paid_pmpm_total": {
                "predicted": None,
                "observed": obs_paid_pmpm,
            },
            "member_months": {"predicted": pred_mm, "observed": mm},
        },
    }

    out = dict(existing) if isinstance(existing, dict) else {}
    out["vs_baseline"] = vs_baseline
    out["vs_predicted"] = vs_predicted
    if "vs_continuation" not in out and vs_cont:
        out["vs_continuation"] = vs_cont
    out["policy_effect"] = out.get("policy_effect") or "UNESTIMATED"
    out["ui_gate_backfilled_at"] = datetime.utcnow().isoformat() + "Z"
    # silence unused
    _ = expected_base_services, expected_base_allowed
    return out


def _alias_obs_metrics(metrics: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    m = dict(metrics)
    changed = False
    mm = float(m.get("member_months") or m.get("eligible_member_months") or 0)
    services = float(m.get("services") or m.get("total_claims") or 0)
    allowed = float(m.get("allowed_amount") or m.get("total_allowed") or 0)
    paid = float(m.get("paid_amount") or m.get("total_paid") or 0)
    util = (services / mm * 1000.0) if mm else None
    if m.get("utilization_per_1k") is None and util is not None:
        m["utilization_per_1k"] = util
        changed = True
    if m.get("services_per_1k_member_years") is None and util is not None:
        m["services_per_1k_member_years"] = util
        changed = True
    if m.get("cost_per_member") is None and mm:
        m["cost_per_member"] = paid / mm
        changed = True
    if m.get("cost_pmpm") is None and mm:
        m["cost_pmpm"] = allowed / mm
        changed = True
    if m.get("allowed_pmpm") is None and mm:
        m["allowed_pmpm"] = allowed / mm
        changed = True
    if m.get("services") is None and m.get("total_claims") is not None:
        m["services"] = float(m["total_claims"])
        changed = True
    return m, changed


def _alias_obs_metrics_from_comparisons(
    metrics: Dict[str, Any], comparisons: Dict[str, Any]
) -> Tuple[Dict[str, Any], bool]:
    """Copy comparison deltas onto metrics so summary list + older dashboard paths see them."""
    m = dict(metrics)
    changed = False
    vb = comparisons.get("vs_baseline") if isinstance(comparisons.get("vs_baseline"), dict) else {}
    for src, dest in (
        ("utilization_change_pct", "utilization_change_pct"),
        ("utilization_change_pct", "observed_percent_change"),
        ("cost_change_pmpm", "cost_change_pmpm"),
    ):
        if m.get(dest) is None and vb.get(src) is not None:
            m[dest] = vb.get(src)
            changed = True
    return m, changed


def _backfill_observations(cur, conn) -> Dict[str, Any]:
    cur.execute(
        """
        SELECT o.id, o.policy_id, o.metrics_json, o.comparisons_json, o.baseline_version_id
        FROM observations o
        WHERE o.tenant_id = %s::uuid
        """,
        (TENANT,),
    )
    rows = cur.fetchall()
    cur.execute(
        """
        SELECT id, baseline_metrics_json FROM baselines WHERE tenant_id = %s::uuid
        """,
        (TENANT,),
    )
    basemap = {str(r["id"]): (r["baseline_metrics_json"] or {}) for r in cur.fetchall()}
    batch: List[Tuple[Any, ...]] = []
    updated = 0
    now = datetime.utcnow()
    for row in rows:
        metrics = row["metrics_json"] or {}
        if isinstance(metrics, str):
            metrics = json.loads(metrics)
        comparisons = row["comparisons_json"] or {}
        if isinstance(comparisons, str):
            comparisons = json.loads(comparisons)
        if not isinstance(metrics, dict):
            metrics = {}
        if not isinstance(comparisons, dict):
            comparisons = {}

        baseline_metrics = {}
        bid = row["baseline_version_id"]
        if bid and str(bid) in basemap:
            bm = basemap[str(bid)]
            if isinstance(bm, str):
                bm = json.loads(bm)
            if isinstance(bm, dict):
                baseline_metrics = bm

        new_metrics, m_changed = _alias_obs_metrics(metrics)
        vb_existing = comparisons.get("vs_baseline") if isinstance(comparisons.get("vs_baseline"), dict) else {}
        need_cmp = not (
            isinstance(comparisons.get("vs_baseline"), dict)
            and isinstance(comparisons.get("vs_predicted"), dict)
            and comparisons["vs_baseline"].get("utilization_change_pct") is not None
            and comparisons["vs_baseline"].get("baseline_member_months") is not None
            and comparisons["vs_baseline"].get("cost_change_pmpm") is not None
        )
        if need_cmp:
            new_cmp = _build_obs_comparisons(
                metrics=new_metrics,
                baseline_metrics=baseline_metrics,
                existing=comparisons,
            )
        else:
            new_cmp = comparisons
            # Ensure exposure present even when comparisons already exist
            if isinstance(vb_existing, dict) and vb_existing.get("baseline_member_months") is None:
                mm = float(new_metrics.get("member_months") or new_metrics.get("eligible_member_months") or 0)
                if mm:
                    new_cmp = dict(comparisons)
                    vb2 = dict(vb_existing)
                    vb2["baseline_member_months"] = mm
                    new_cmp["vs_baseline"] = vb2
                    need_cmp = True
        new_metrics, m2 = _alias_obs_metrics_from_comparisons(new_metrics, new_cmp)
        m_changed = m_changed or m2
        if not m_changed and not need_cmp:
            continue
        batch.append((Json(new_metrics), Json(new_cmp), now, str(row["id"])))
        updated += 1
        if len(batch) >= 200:
            execute_batch(
                cur,
                """
                UPDATE observations
                SET metrics_json = %s, comparisons_json = %s, updated_at = %s
                WHERE id = %s::uuid
                """,
                batch,
                page_size=200,
            )
            conn.commit()
            print(f"  observations committed {updated}/{len(rows)}", flush=True)
            batch = []
    if batch:
        execute_batch(
            cur,
            """
            UPDATE observations
            SET metrics_json = %s, comparisons_json = %s, updated_at = %s
            WHERE id = %s::uuid
            """,
            batch,
            page_size=200,
        )
        conn.commit()
        print(f"  observations committed {updated}/{len(rows)}", flush=True)
    return {"observations_scanned": len(rows), "observations_updated": updated}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        choices=("all", "predictions", "baselines", "observations"),
        default="all",
    )
    parser.add_argument(
        "--force-segments",
        action="store_true",
        help="Rebuild patient_segments (and refresh archetypes if missing) even when already present.",
    )
    args = parser.parse_args()
    globals()["_FORCE_SEGMENT_REFRESH"] = bool(args.force_segments)
    conn = psycopg2.connect(_db_url())
    conn.autocommit = False
    report: Dict[str, Any] = {
        "database": "hfleanstg",
        "started_at": datetime.utcnow().isoformat() + "Z",
        "only": args.only,
        "force_segments": bool(args.force_segments),
    }
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if args.only in ("all", "predictions"):
                print("Backfilling predicted impacts…", flush=True)
                report["predictions"] = _backfill_predictions(cur)
                print(report["predictions"], flush=True)
                conn.commit()

            if args.only in ("all", "baselines"):
                print("Backfilling baselines (archetypes/segments)…", flush=True)
                report["baselines"] = _backfill_baselines(cur)
                print(report["baselines"], flush=True)
                conn.commit()

            if args.only in ("all", "observations"):
                print("Backfilling observations (aliases + comparisons)…", flush=True)
                report["observations"] = _backfill_observations(cur, conn)
                print(report["observations"], flush=True)

            report["finished_at"] = datetime.utcnow().isoformat() + "Z"
            report["status"] = "OK"
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(report, indent=2))
            print("Wrote", OUT, flush=True)
    except Exception as exc:
        conn.rollback()
        report["status"] = "FAILED"
        report["error"] = str(exc)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2))
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
