#!/usr/bin/env python3
"""
Nine-mock-policy lifecycle on lean staging, 5K measurement book.

For each of the nine policies:
  1. Use latest CY2025 5K baseline (preserves prior versions)
  2. Freeze historical-rate continuation for 2026-01..2026-10
  3. Keep policy-effect UNESTIMATED (no fabricated savings)
  4. Compute independent monthly observations from 2026 claims
  5. Reconcile vs frozen continuation; verdict from endpoint contract

Lean staging only. Does not touch Dec4 demo / production. Does not rewrite dollars.
"""
from __future__ import annotations

import calendar
import json
import subprocess
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import Json, RealDictCursor

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "packages" / "common" / "src"))

from uepi_common.lifecycle import (  # noqa: E402
    STATUS_UNESTIMATED,
    compute_continuation_forecast,
    compute_historical_rates,
    compute_observations,
    compute_policy_effect_prediction,
    compute_reconciliation,
    compute_verdict_prerequisites,
)

TENANT = "00000000-0000-0000-0000-000000000001"
MEASUREMENT_BOOK = "SYNTHETIC_NINE_POLICY_5K_V1"
OBS_START = date(2026, 1, 1)
OBS_END = date(2026, 10, 31)
OUT = (
    REPO
    / "docs/production/releases/corrections/nine_mock_policies/NINE_POLICY_LIFECYCLE_5K_REPORT.json"
)
METHOD = "HISTORICAL_RATE_CONTINUATION_V1"
MODEL = "historical_rate_continuation_v1"


def _database_url() -> str:
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
        raise SystemExit("Refusing: DATABASE_URL is not lean staging.")
    return url


def _as_list(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if x is not None and str(x).strip()]
    s = str(val).strip()
    return [s] if s else []


def _extract_codes(meta: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    scope = meta.get("scope") if isinstance(meta.get("scope"), dict) else {}
    levers = meta.get("policy_levers") if isinstance(meta.get("policy_levers"), list) else []
    procedure = _as_list(scope.get("procedure_codes"))
    services = _as_list(scope.get("service_categories") or scope.get("service_category"))
    for lever in levers:
        if not isinstance(lever, dict):
            continue
        blob: Dict[str, Any] = {}
        blob.update(lever.get("targets") or {})
        blob.update(lever.get("parameters") or {})
        for key in ("procedure_codes", "cpt_codes", "hcpcs_codes", "codes", "target_codes"):
            procedure.extend(_as_list(blob.get(key)))
        for key in ("service_categories", "service_category", "categories"):
            services.extend(_as_list(blob.get(key)))
    return sorted(set(procedure)), sorted(set(services))


def _endpoint_contract(meta: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    direct = meta.get("required_endpoints")
    measurement = meta.get("measurement") if isinstance(meta.get("measurement"), dict) else {}
    contract = direct or measurement.get("required_endpoints")
    if isinstance(contract, list) and contract:
        return [c for c in contract if isinstance(c, dict)]
    return None


def _month_range(start: date, end: date) -> List[date]:
    out = []
    cur = date(start.year, start.month, 1)
    last = date(end.year, end.month, 1)
    while cur <= last:
        out.append(cur)
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)
    return out


def _month_end(month: date) -> date:
    return date(month.year, month.month, calendar.monthrange(month.year, month.month)[1])


def _book_mm_for_month(cur, month: date) -> float:
    cur.execute(
        """
        SELECT COALESCE(SUM(
            LEAST(
                1.0,
                (
                    GREATEST(0, (enrollment_end_date - enrollment_start_date))
                    + CASE
                        WHEN segment LIKE 'GAP_DAYS:%%'
                        THEN GREATEST(0, CAST(split_part(segment, ':', 2) AS integer))
                        ELSE 0
                      END
                )::double precision
                / EXTRACT(DAY FROM (date_trunc('month', enrollment_month) + INTERVAL '1 month - 1 day'))
            )
        ), 0)::float AS mm
        FROM enrollment_records
        WHERE tenant_id = %s
          AND source_system = %s
          AND enrollment_month = %s
          AND enrollment_start_date IS NOT NULL
          AND enrollment_end_date IS NOT NULL
        """,
        (TENANT, MEASUREMENT_BOOK, month),
    )
    return float(cur.fetchone()["mm"] or 0.0)


def _claim_agg(cur, codes: List[str], services: List[str], start: date, end: date) -> Dict[str, Any]:
    clauses = [
        "c.tenant_id = %s",
        "c.source_system = %s",
        "c.service_date BETWEEN %s AND %s",
        "(c.cpt_code = ANY(%s) OR c.hcpcs_code = ANY(%s))",
        "(c.record_hash IS NULL OR ("
        "c.record_hash NOT LIKE '%%\"line_status\":\"REVERSAL\"%%' "
        "AND c.record_hash NOT LIKE '%%\"line_status\":\"VOID\"%%'))",
        """EXISTS (
            SELECT 1 FROM enrollment_records e
            WHERE e.tenant_id = c.tenant_id
              AND e.member_id = c.member_id
              AND e.source_system = c.source_system
              AND e.enrollment_start_date IS NOT NULL
              AND e.enrollment_end_date IS NOT NULL
              AND e.enrollment_start_date <= c.service_date
              AND c.service_date < e.enrollment_end_date
        )""",
    ]
    params: List[Any] = [TENANT, MEASUREMENT_BOOK, start, end, codes, codes]
    if services:
        clauses.append("c.service_category = ANY(%s)")
        params.append(services)
    cur.execute(
        f"""
        SELECT count(*)::int AS total_claims,
               count(DISTINCT member_id)::int AS unique_members,
               COALESCE(SUM(allowed_amount),0)::float AS total_allowed,
               COALESCE(SUM(paid_amount),0)::float AS total_paid
        FROM claims_lines c
        WHERE {' AND '.join(clauses)}
        """,
        params,
    )
    return dict(cur.fetchone())


def main() -> int:
    freeze_ts = datetime.now(timezone.utc).replace(microsecond=0)
    months = _month_range(OBS_START, OBS_END)
    report: Dict[str, Any] = {
        "generated_at": freeze_ts.isoformat(),
        "database": "hfleanstg",
        "measurement_book": MEASUREMENT_BOOK,
        "observation_window": [OBS_START.isoformat(), OBS_END.isoformat()],
        "policies": [],
        "errors": [],
    }

    conn = psycopg2.connect(_database_url())
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT id::text, name, policy_metadata_json AS meta
        FROM policies
        WHERE tenant_id = %s::uuid
          AND (
            policy_metadata_json->>'mock_client_seed' = 'nine_pdf_policies_v1'
            OR name = ANY(%s)
          )
        ORDER BY name
        """,
        (
            TENANT,
            [
                "Outpatient MRI Prior Authorization",
                "National Coverage Determination Study — MRI (NCD 220.2)",
                "Local Coverage Determination Study — LCD L34425",
                "Imaging Site-of-Service Policy",
                "Infusion Site-of-Care and Reimbursement Policy",
                "Outpatient Therapy Utilization and Payment Policy",
                "Medically Unlikely Edit (MUE) / Unit Cap",
                "Procedure-to-Procedure (PTP) Coding Edit",
                "Multiple Procedure Payment Reduction (MPPR)",
            ],
        ),
    )
    policies = [dict(r) for r in cur.fetchall()]
    if len(policies) != 9:
        report["errors"].append(f"expected_9_policies_got_{len(policies)}")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2, default=str))
        cur.close()
        conn.close()
        return 1

    # Forecast exposure from book enrollment by month (continuation uses this, not post claims).
    forecast_mm = [_book_mm_for_month(cur, m) for m in months]
    report["forecast_member_months_by_month"] = {
        m.isoformat(): mm for m, mm in zip(months, forecast_mm)
    }

    for policy_idx, row in enumerate(policies):
        meta = row["meta"] if isinstance(row["meta"], dict) else {}
        codes, services = _extract_codes(meta)
        endpoints = _endpoint_contract(meta)
        if not codes:
            report["errors"].append({"policy": row["name"], "error": "no_codeset"})
            continue

        cur.execute(
            """
            SELECT id::text AS row_id, baseline_id, version, baseline_metrics_json AS metrics
            FROM baselines
            WHERE tenant_id = %s::uuid
              AND policy_id = %s::uuid
              AND baseline_metrics_json->>'measurement_book' = %s
            ORDER BY version DESC
            LIMIT 1
            """,
            (TENANT, row["id"], MEASUREMENT_BOOK),
        )
        baseline = cur.fetchone()
        if not baseline:
            report["errors"].append({"policy": row["name"], "error": "missing_5k_baseline"})
            continue
        metrics = baseline["metrics"] if isinstance(baseline["metrics"], dict) else {}
        eligible_services = float(metrics.get("total_claims") or 0)
        eligible_mm = float(metrics.get("member_months") or 0)
        total_allowed = float(metrics.get("total_allowed") or 0)

        rates = compute_historical_rates(
            eligible_services=eligible_services,
            eligible_member_months=eligible_mm,
            total_allowed=total_allowed,
        )
        continuation = compute_continuation_forecast(
            historical_rates=rates,
            forecast_member_months_by_month=forecast_mm,
            freeze_timestamp=freeze_ts.isoformat(),
            model_id=MODEL,
        )
        policy_effect = compute_policy_effect_prediction(
            intervention_model=None,
            clinical_criteria_supported=False,
        )

        pred_id = str(uuid.uuid4())
        pred_metrics = {
            "prediction_type": "CONTINUATION",
            "historical_rates": rates,
            "continuation": continuation,
            "policy_effect": policy_effect,
            "measurement_book": MEASUREMENT_BOOK,
            "baseline_version": baseline["version"],
            "baseline_id": baseline["baseline_id"],
            "invariants": {
                "continuation_is_not_policy_effect": True,
                "zero_not_substituted_for_unestimated": True,
                "policy_effect_status": STATUS_UNESTIMATED,
            },
            "horizon": {
                "start": OBS_START.isoformat(),
                "end": OBS_END.isoformat(),
                "months": len(months),
            },
            # Flat fields for existing UI consumers (continuation, not causal savings).
            "allowed_pmpm_target": rates.get("allowed_pmpm"),
            "util_rate_target_per_1000_mm": (
                (eligible_services / eligible_mm) * 1000.0 if eligible_mm else None
            ),
            "cost_change_pmpm": None,
            "cost_change_meaning": "UNESTIMATED_POLICY_EFFECT",
            "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
        }
        # Offset predicted_at per policy to satisfy unique (tenant, policy, predicted_at).
        predicted_at = (freeze_ts + timedelta(seconds=policy_idx)).replace(tzinfo=None)

        cur.execute(
            """
            INSERT INTO policy_predicted_impacts (
                id, tenant_id, policy_id, metrics_json,
                model_version, confidence, predicted_at, prediction_method,
                baseline_id, created_at, updated_at
            ) VALUES (
                %s::uuid, %s::uuid, %s::uuid, %s,
                %s, %s, %s, %s,
                %s::uuid, %s, %s
            )
            """,
            (
                pred_id,
                TENANT,
                row["id"],
                Json(pred_metrics),
                MODEL,
                None,
                predicted_at,
                METHOD,
                baseline["row_id"],
                predicted_at,
                predicted_at,
            ),
        )

        obs_rows = []
        for idx, month in enumerate(months):
            start = month
            end = _month_end(month)
            actual_mm = forecast_mm[idx]  # same book enrollment; independent of claim counts
            agg = _claim_agg(cur, codes, services, start, end)
            obs = compute_observations(
                eligible_member_months=actual_mm,
                services=float(agg["total_claims"] or 0),
                allowed_amount=float(agg["total_allowed"] or 0),
                paid_amount=float(agg["total_paid"] or 0),
                distinct_members=float(agg["unique_members"] or 0),
                authorization_events_present=False,
            )
            series = (continuation.get("series") or [])
            month_pred = series[idx] if idx < len(series) else None
            recon = None
            if month_pred and continuation.get("status") == "AVAILABLE":
                recon = compute_reconciliation(
                    frozen_predicted_services=month_pred["predicted_services"],
                    frozen_predicted_allowed=month_pred["predicted_allowed"],
                    forecast_member_months=month_pred["forecast_member_months"],
                    frozen_allowed_pmpm=continuation["historical_allowed_pmpm"],
                    frozen_service_rate_per_member_month=continuation[
                        "historical_service_rate_per_member_month"
                    ],
                    observed_services=float(agg["total_claims"] or 0),
                    observed_allowed=float(agg["total_allowed"] or 0),
                    actual_member_months=actual_mm,
                )
            verdict = compute_verdict_prerequisites(
                endpoint_contract=endpoints,
                authorization_events_present=False,
                policy_effect_status=STATUS_UNESTIMATED,
                clinical_criteria_supported=False,
                observations_available=obs.get("status") == "AVAILABLE",
                continuation_available=continuation.get("status") == "AVAILABLE",
            )
            # Product verdict column: INCONCLUSIVE without endpoint contract.
            verdict_status = (
                "INCONCLUSIVE"
                if verdict.get("verdict") == "INCONCLUSIVE"
                else "INCONCLUSIVE"  # effect UNESTIMATED → do not claim ON_TRACK
            )
            if verdict.get("verdict") == "EVALUATION_PERMITTED" and endpoints:
                # Still inconclusive until directional endpoints are scored with effect model.
                verdict_status = "INCONCLUSIVE"

            observation_id = f"nine5k-{row['id'][:8]}-{month.strftime('%Y%m')}-{uuid.uuid4().hex[:8]}"
            obs_pk = str(uuid.uuid4())
            obs_metrics = {
                **obs,
                "measurement_book": MEASUREMENT_BOOK,
                "grain": "claim_line",
                "require_enrollment_on_service_date": True,
                "exclude_void_reversal": True,
                "total_claims": int(agg["total_claims"] or 0),
                "total_allowed": float(agg["total_allowed"] or 0),
                "total_paid": float(agg["total_paid"] or 0),
                "unique_members": int(agg["unique_members"] or 0),
                "member_months": actual_mm,
                "allowed_pmpm_total": obs.get("allowed_pmpm"),
                "util_rate_total_per_1000_mm": (
                    (float(agg["total_claims"] or 0) / actual_mm) * 1000.0 if actual_mm else None
                ),
            }
            comparisons = {
                "vs_continuation": recon,
                "policy_effect": STATUS_UNESTIMATED,
                "note": (
                    "Observation is independent of the frozen continuation. "
                    "Variance is not attributed policy savings."
                ),
            }
            now = datetime.utcnow()
            cur.execute(
                """
                INSERT INTO observations (
                    id, tenant_id, observation_id, policy_id,
                    baseline_version_id, prediction_id,
                    observation_type, observation_period_start, observation_period_end,
                    metrics_json, comparisons_json,
                    verdict_status, verdict_reason, recommendation, verdict_rule_version,
                    computed_at, created_at, updated_at
                ) VALUES (
                    %s::uuid, %s::uuid, %s, %s::uuid,
                    %s::uuid, %s::uuid,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s
                )
                """,
                (
                    obs_pk,
                    TENANT,
                    observation_id,
                    row["id"],
                    baseline["row_id"],
                    pred_id,
                    "PERIODIC",
                    datetime(start.year, start.month, start.day),
                    datetime(end.year, end.month, end.day, 23, 59, 59),
                    Json(obs_metrics),
                    Json(comparisons),
                    verdict_status,
                    "; ".join(verdict.get("reason_codes") or []) or verdict.get("note"),
                    "Keep policy-effect UNESTIMATED until a supported intervention model exists.",
                    "lifecycle-continuation-v1",
                    now,
                    now,
                    now,
                ),
            )
            obs_rows.append(
                {
                    "month": month.isoformat(),
                    "observation_id": observation_id,
                    "claims": int(agg["total_claims"] or 0),
                    "allowed": float(agg["total_allowed"] or 0),
                    "member_months": actual_mm,
                    "verdict_status": verdict_status,
                }
            )

        report["policies"].append(
            {
                "policy_id": row["id"],
                "name": row["name"],
                "baseline_version": baseline["version"],
                "prediction_id": pred_id,
                "continuation_status": continuation.get("status"),
                "policy_effect_status": policy_effect.get("status"),
                "allowed_pmpm": rates.get("allowed_pmpm"),
                "observations": len(obs_rows),
                "months": obs_rows,
            }
        )
        print(
            "OK %s continuation=%s effect=%s obs=%s"
            % (
                row["name"],
                continuation.get("status"),
                policy_effect.get("status"),
                len(obs_rows),
            ),
            flush=True,
        )

    conn.commit()
    report["summary"] = {
        "policies": len(report["policies"]),
        "predictions": len(report["policies"]),
        "observations": sum(p["observations"] for p in report["policies"]),
        "errors": len(report["errors"]),
        "success": len(report["policies"]) == 9 and not report["errors"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report["summary"], indent=2))
    print("Wrote", OUT)
    cur.close()
    conn.close()
    return 0 if report["summary"]["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
