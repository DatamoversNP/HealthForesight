#!/usr/bin/env python3
"""
Autonomous batch lifecycle for reviewed-248 PDF policies (lean staging only).

Per batch of 10:
  1. Configure policies from PDF definitions (additive; keeps nine-mock policies)
  2. Ensure synthetic population book covers candidate codes (12k lives)
  3. Validate data alignment / realism for the batch
  4. Baseline CY2025 → continuation prediction → 2026 observations → next stages
  5. Write batch validation report

Does not invent certified codesets (rejects bad E/M dumps).
Does not fabricate policy-effect savings. Does not touch Dec4 demo / production.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import Json, RealDictCursor, execute_batch

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
    compute_whatif_continuation,
)
from uepi_common.synthetic_payer.reviewed_248_book import (  # noqa: E402
    DEFAULT_N_MEMBERS,
    PRE_END,
    PRE_START,
    POST_END,
    POST_START,
    SOURCE_SYSTEM,
    generate_book_for_policies,
    write_entity_pack,
)
from uepi_common.synthetic_payer.reviewed_248_manifest import (  # noqa: E402
    batch_slice,
    build_manifest,
)

TENANT = "00000000-0000-0000-0000-000000000001"
PACK = REPO / "data" / "synthetic" / "reviewed_248_pdfs"
MANIFEST_PATH = (
    REPO / "docs/production/releases/corrections/reviewed_248/REVIEWED_248_MANIFEST.json"
)
OUT_DIR = REPO / "docs/production/releases/corrections/reviewed_248"
BOOK_DIR = REPO / "data" / "synthetic" / "reviewed_248_book"
SPEC = "reviewed_248_pdfs_2026-11-07"


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


def _load_or_build_manifest() -> Dict[str, Any]:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    print("Building manifest from PDFs…", flush=True)
    man = build_manifest(PACK)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(man, indent=2))
    print("Manifest", man["summary"], flush=True)
    return man


def _ensure_population(cur, conn, manifest: Dict[str, Any]) -> Dict[str, Any]:
    cur.execute(
        "SELECT count(*)::bigint AS n FROM claims_lines WHERE source_system=%s",
        (SOURCE_SYSTEM,),
    )
    existing = int(cur.fetchone()["n"] or 0)
    if existing > 0:
        cur.execute(
            "SELECT count(DISTINCT member_id)::bigint AS m FROM enrollment_records WHERE source_system=%s",
            (SOURCE_SYSTEM,),
        )
        members = int(cur.fetchone()["m"] or 0)
        return {"loaded": False, "claims": existing, "members": members, "source_system": SOURCE_SYSTEM}

    # Clear any partial prior load for this source only.
    cur.execute("DELETE FROM claims_lines WHERE source_system=%s OR member_id LIKE 'R248_%%'", (SOURCE_SYSTEM,))
    cur.execute(
        "DELETE FROM enrollment_records WHERE source_system=%s OR member_id LIKE 'R248_%%'",
        (SOURCE_SYSTEM,),
    )
    conn.commit()

    meta_path = BOOK_DIR / "meta.json"
    claims_path = BOOK_DIR / "claims_lines.jsonl"
    enroll_path = BOOK_DIR / "enrollment_records.jsonl"
    if meta_path.exists() and claims_path.exists() and enroll_path.exists():
        print("Reusing entity pack on disk…", flush=True)
        meta = json.loads(meta_path.read_text())

        def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
            rows = []
            with path.open() as f:
                for line in f:
                    rows.append(json.loads(line))
            return rows

        book = {
            "meta": meta,
            "enrollment_records": _load_jsonl(enroll_path),
            "claims_lines": _load_jsonl(claims_path),
        }
        # Coerce date fields
        for e in book["enrollment_records"]:
            for k in ("enrollment_month", "enrollment_start_date", "enrollment_end_date"):
                if isinstance(e.get(k), str):
                    e[k] = date.fromisoformat(e[k][:10])
        for c in book["claims_lines"]:
            if isinstance(c.get("service_date"), str):
                c["service_date"] = date.fromisoformat(c["service_date"][:10])
        counts = {
            "enrollment_records": len(book["enrollment_records"]),
            "claims_lines": len(book["claims_lines"]),
        }
    else:
        print(f"Generating {DEFAULT_N_MEMBERS}-member book for all candidate policies…", flush=True)
        book = generate_book_for_policies(manifest["policies"], n_members=DEFAULT_N_MEMBERS)
        counts = write_entity_pack(book, BOOK_DIR)
    print("entity pack", counts, flush=True)

    ingestion_id = book["meta"]["ingestion_id"]
    source_file = f"reviewed-248-{book['meta']['seed']}"

    enroll_sql = """
        INSERT INTO enrollment_records (
            id, tenant_id, member_id, enrollment_month, lob, market,
            age_band, gender, risk_score, network_tier, enrolled_flag,
            enrollment_start_date, enrollment_end_date, product_type, segment,
            source_system, source_file_id, ingestion_id, record_hash,
            created_at, updated_at
        ) VALUES (
            %s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,
            %s,%s,%s,%s,
            NOW(), NOW()
        )
    """
    enroll_rows = []
    for e in book["enrollment_records"]:
        enroll_rows.append(
            (
                str(uuid.uuid4()),
                TENANT,
                e["member_id"],
                e["enrollment_month"],
                e["lob"],
                e.get("market") or "SYNTHETIC",
                e.get("age_band") or "45-64",
                e.get("gender") or "F",
                e.get("risk_score") or 1.0,
                e.get("network_tier") or "STANDARD",
                True,
                e["enrollment_start_date"],
                e["enrollment_end_date"],
                e.get("product_type"),
                e.get("segment"),
                SOURCE_SYSTEM,
                source_file,
                ingestion_id,
                None,
            )
        )
    print(f"Inserting {len(enroll_rows)} enrollment rows…", flush=True)
    for offset in range(0, len(enroll_rows), 5000):
        execute_batch(cur, enroll_sql, enroll_rows[offset : offset + 5000], page_size=500)
        print(f"  enrollment {min(offset + 5000, len(enroll_rows))}/{len(enroll_rows)}", flush=True)

    claim_sql = """
        INSERT INTO claims_lines (
            id, tenant_id, claim_id, claim_line_id, member_id, provider_id,
            service_date, paid_date, adjudication_date, lob, market,
            cpt_code, hcpcs_code, service_category, place_of_service, units,
            allowed_amount, paid_amount, member_cost_share, in_network,
            requires_prior_auth, prior_auth_approved, facility_type,
            source_system, source_file_id, ingestion_id, record_hash,
            created_at, updated_at
        ) VALUES (
            %s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,
            %s,%s,%s,
            %s,%s,%s,%s,
            NOW(), NOW()
        )
    """
    claim_rows = []
    for c in book["claims_lines"]:
        claim_rows.append(
            (
                str(uuid.uuid4()),
                TENANT,
                c["claim_id"],
                c["claim_line_id"],
                c["member_id"],
                c.get("provider_id") or "R248_PRV_0000",
                c["service_date"],
                c["service_date"],
                c["service_date"],
                c.get("lob") or "COMMERCIAL",
                c.get("market") or "SYNTHETIC",
                c.get("cpt_code"),
                c.get("hcpcs_code"),
                c.get("service_category") or "general",
                c.get("place_of_service") or "11",
                c.get("units") or 1,
                c.get("allowed_amount") or 0,
                c.get("paid_amount") or 0,
                c.get("member_cost_share") or 0,
                bool(c.get("in_network", True)),
                bool(c.get("requires_prior_auth", False)),
                None,
                c.get("facility_type"),
                SOURCE_SYSTEM,
                source_file,
                ingestion_id,
                c.get("record_hash"),
            )
        )
    print(f"Inserting {len(claim_rows)} claim lines…", flush=True)
    for offset in range(0, len(claim_rows), 5000):
        execute_batch(cur, claim_sql, claim_rows[offset : offset + 5000], page_size=500)
        print(f"  claims {min(offset + 5000, len(claim_rows))}/{len(claim_rows)}", flush=True)
    conn.commit()
    return {
        "loaded": True,
        "claims": len(claim_rows),
        "enrollment": len(enroll_rows),
        "members": DEFAULT_N_MEMBERS,
        "source_system": SOURCE_SYSTEM,
        "entity_counts": counts,
    }


def _configure_policy(cur, spec: Dict[str, Any]) -> str:
    pid = spec["policy_id"]
    codes = list(spec.get("candidate_codes") or [])
    decision = spec["decision"]
    measurable = decision == "CANDIDATE_MEASURE" and bool(codes)
    config_state = "REVIEW_ONLY" if measurable else "BLOCKED"
    now = datetime.utcnow()
    meta = {
        "mock_client_seed": "reviewed_248_pdfs",
        "pdf_filename": spec.get("filename"),
        "register_index": spec["register_index"],
        "family": spec.get("family"),
        "mechanism": spec.get("mechanism"),
        "configuration_state": config_state,
        "blocked_reason": None if measurable else spec.get("source_status") or decision,
        "evidence_class": "SYNTHETIC_ILLUSTRATIVE" if measurable else "DEFINITION_ONLY",
        "measurement_book": {
            "source_system": SOURCE_SYSTEM,
            "population_size": DEFAULT_N_MEMBERS,
            "baseline_window": [PRE_START.isoformat(), PRE_END.isoformat()],
            "authorized_at": datetime.now(timezone.utc).isoformat(),
        }
        if measurable
        else None,
        "scope": {
            "procedure_codes": codes,
            "service_categories": [spec.get("service_category")] if measurable else [],
            "exported_codes_rejected": spec.get("exported_codes_raw") if decision == "CONFIG_ONLY_BAD_EXPORT" else [],
        },
        "policy_levers": [
            {
                "lever_type": spec.get("exported_lever") or "REVIEW",
                "targets": {"codes": codes, "code_system": "CPT_OR_HCPCS" if codes else "PENDING"},
                "parameters": {
                    "mechanism_note": spec.get("mechanism"),
                    "parameters_certified": False,
                    "candidate_only": True,
                },
            }
        ],
        "assumptions": [
            {
                "assumption_type": "IMPACT",
                "description": "Policy-effect UNESTIMATED.",
                "value": "UNESTIMATED",
                "evidence_state": "UNESTIMATED",
                "source": SPEC,
            },
            {
                "assumption_type": "CODING_AUTHORITY",
                "description": (
                    "Candidate codes after removing known-bad E/M dump; not certified edition."
                    if measurable
                    else "No executable codeset — bad export removed and not auto-substituted."
                ),
                "value": "UNESTIMATED",
                "evidence_state": "UNESTIMATED",
                "source": SPEC,
            },
        ],
        "code_systems": {
            "systems": [
                {
                    "system": "CPT_OR_HCPCS" if codes else "PENDING",
                    "codes": codes,
                    "state": "CANDIDATE_UNVERIFIED" if codes else "UNVERIFIED_CODE_MAPPING",
                    "certified": False,
                }
            ]
        },
        "remediation": {
            "spec_version": SPEC,
            "decision": decision,
            "source_status": spec.get("source_status"),
        },
        "seed": {"source": SPEC, "seeded_at": datetime.now(timezone.utc).isoformat()},
    }
    cur.execute("SELECT id::text FROM policies WHERE tenant_id=%s::uuid AND id=%s::uuid", (TENANT, pid))
    exists = cur.fetchone()
    desc = f"{spec.get('mechanism') or ''}\n\nReviewed PDF config. Decision={decision}."
    if exists:
        cur.execute(
            """
            UPDATE policies SET
              name=%s, policy_type=%s, description=%s, status='ACTIVE',
              policy_metadata_json=%s::jsonb, updated_at=%s
            WHERE id=%s::uuid AND tenant_id=%s::uuid
            """,
            (
                spec["name"],
                spec.get("policy_type") or "ADMINISTRATIVE_REQUIREMENT",
                desc,
                json.dumps(meta),
                now,
                pid,
                TENANT,
            ),
        )
    else:
        cur.execute(
            """
            INSERT INTO policies (
                id, tenant_id, name, policy_type, owner_role, description,
                status, policy_metadata_json, created_at, updated_at
            ) VALUES (
                %s::uuid, %s::uuid, %s, %s, %s, %s, 'ACTIVE', %s::jsonb, %s, %s
            )
            """,
            (
                pid,
                TENANT,
                spec["name"],
                spec.get("policy_type") or "ADMINISTRATIVE_REQUIREMENT",
                "Policy Catalog",
                desc,
                json.dumps(meta),
                now,
                now,
            ),
        )
    # refresh assumptions (simple replace)
    cur.execute("DELETE FROM policy_assumptions WHERE tenant_id=%s::uuid AND policy_id=%s::uuid", (TENANT, pid))
    for a in meta["assumptions"]:
        cur.execute(
            """
            INSERT INTO policy_assumptions (
                id, tenant_id, policy_id, assumption_type, description,
                value, source, confidence, range_json, created_at, updated_at
            ) VALUES (%s::uuid,%s::uuid,%s::uuid,%s,%s,%s,%s,%s,%s::jsonb,%s,%s)
            """,
            (
                str(uuid.uuid4()),
                TENANT,
                pid,
                a["assumption_type"],
                a["description"],
                a["value"],
                a["source"],
                None,
                json.dumps({}),
                now,
                now,
            ),
        )
    return pid


def _book_mm(cur, start: date, end: date) -> float:
    cur.execute(
        """
        SELECT COALESCE(SUM(
            LEAST(1.0, (
                GREATEST(0,(enrollment_end_date-enrollment_start_date))
                + CASE WHEN segment LIKE 'GAP_DAYS:%%'
                       THEN GREATEST(0, CAST(split_part(segment,':',2) AS integer)) ELSE 0 END
            )::float / EXTRACT(DAY FROM (date_trunc('month', enrollment_month)+INTERVAL '1 month - 1 day')))
        ),0)::float AS mm
        FROM enrollment_records
        WHERE tenant_id=%s::uuid AND source_system=%s
          AND enrollment_month >= %s AND enrollment_month <= %s
        """,
        (TENANT, SOURCE_SYSTEM, date(start.year, start.month, 1), date(end.year, end.month, 1)),
    )
    return float(cur.fetchone()["mm"] or 0)


def _claim_agg(cur, codes: List[str], services: List[str], start: date, end: date) -> Dict[str, Any]:
    clauses = [
        "c.tenant_id=%s",
        "c.source_system=%s",
        "c.service_date BETWEEN %s AND %s",
        "(c.cpt_code = ANY(%s) OR c.hcpcs_code = ANY(%s))",
        "(c.record_hash IS NULL OR (c.record_hash NOT LIKE '%%\"line_status\":\"VOID\"%%' AND c.record_hash NOT LIKE '%%\"line_status\":\"REVERSAL\"%%'))",
        """EXISTS (
            SELECT 1 FROM enrollment_records e
            WHERE e.tenant_id=c.tenant_id AND e.member_id=c.member_id AND e.source_system=c.source_system
              AND e.enrollment_start_date <= c.service_date AND c.service_date < e.enrollment_end_date
        )""",
    ]
    params: List[Any] = [TENANT, SOURCE_SYSTEM, start, end, codes, codes]
    if services:
        clauses.append("c.service_category = ANY(%s)")
        params.append(services)
    cur.execute(
        f"""
        SELECT count(*)::int AS total_claims,
               count(DISTINCT member_id)::int AS unique_members,
               COALESCE(SUM(allowed_amount),0)::float AS total_allowed,
               COALESCE(SUM(paid_amount),0)::float AS total_paid
        FROM claims_lines c WHERE {' AND '.join(clauses)}
        """,
        params,
    )
    return dict(cur.fetchone())


def _validate_alignment(cur, spec: Dict[str, Any], book_mm_2025: float) -> Dict[str, Any]:
    codes = list(spec.get("candidate_codes") or [])
    services = [spec["service_category"]] if spec.get("service_category") else []
    if spec["decision"] != "CANDIDATE_MEASURE":
        return {
            "aligned": False,
            "status": "CONFIG_ONLY",
            "reason": spec["decision"],
            "note": "No claims measurement — bad/missing codeset not auto-substituted.",
        }
    agg = _claim_agg(cur, codes, services, PRE_START, PRE_END)
    post = _claim_agg(cur, codes, services, POST_START, POST_END)
    lines = int(agg["total_claims"] or 0)
    members = int(agg["unique_members"] or 0)
    avg = (float(agg["total_allowed"]) / lines) if lines else None
    issues = []
    if lines < 50:
        issues.append("thin_baseline_claims")
    if members < 20:
        issues.append("thin_unique_members")
    if book_mm_2025 <= 0:
        issues.append("missing_enrollment_mm")
    if int(post["total_claims"] or 0) < 30:
        issues.append("thin_observation_claims")
    # realism: allowed per line within expected band
    bands = list((spec.get("allowed_bands") or {}).values())
    if avg and bands:
        lo = min(b[0] for b in bands)
        hi = max(b[1] for b in bands)
        if avg < lo * 0.5 or avg > hi * 2.0:
            issues.append(f"avg_allowed_out_of_band:{avg:.1f}_vs_{lo}-{hi}")
    status = "ALIGNED" if not issues else ("THIN" if lines > 0 else "NOT_ALIGNED")
    return {
        "aligned": status == "ALIGNED",
        "status": status,
        "issues": issues,
        "baseline_claims": lines,
        "baseline_members": members,
        "baseline_allowed": float(agg["total_allowed"] or 0),
        "avg_allowed_per_line": avg,
        "observation_claims": int(post["total_claims"] or 0),
        "book_mm_2025": book_mm_2025,
        "codes": codes,
        "service_category": spec.get("service_category"),
    }


def _run_lifecycle_for_measurable(cur, spec: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
    pid = spec["policy_id"]
    codes = list(spec["candidate_codes"])
    services = [spec["service_category"]] if spec.get("service_category") else []
    book_mm = float(validation["book_mm_2025"])
    agg = {
        "total_claims": validation["baseline_claims"],
        "unique_members": validation["baseline_members"],
        "total_allowed": validation["baseline_allowed"],
        "total_paid": validation["baseline_allowed"] * 0.8,
    }
    # re-query paid accurately
    paid_agg = _claim_agg(cur, codes, services, PRE_START, PRE_END)
    total_paid = float(paid_agg["total_paid"] or 0)
    total_allowed = float(paid_agg["total_allowed"] or 0)
    total_claims = int(paid_agg["total_claims"] or 0)
    unique_members = int(paid_agg["unique_members"] or 0)
    if total_claims == 0 or book_mm <= 0:
        return {"status": "SKIPPED_NO_DATA"}

    allowed_pmpm = total_allowed / book_mm
    paid_pmpm = total_paid / book_mm
    util = (total_claims / book_mm) * 1000.0
    next_version = 1
    cur.execute(
        "SELECT COALESCE(max(version),0)::int AS v FROM baselines WHERE tenant_id=%s::uuid AND policy_id=%s::uuid",
        (TENANT, pid),
    )
    next_version = int(cur.fetchone()["v"] or 0) + 1
    baseline_id = str(uuid.uuid4())
    row_id = str(uuid.uuid4())
    now = datetime.utcnow()
    metrics = {
        "member_months": book_mm,
        "unique_members": unique_members,
        "total_claims": total_claims,
        "total_paid": total_paid,
        "total_allowed": total_allowed,
        "allowed_pmpm_target": allowed_pmpm,
        "paid_pmpm_target": paid_pmpm,
        "util_rate_target_per_1000_mm": util,
        "exposure_method": "ENROLLMENT_DISTINCT_COVERED_DAYS",
        "denominator_basis": "ENROLLMENT",
        "measurement_book": SOURCE_SYSTEM,
        "require_enrollment_on_service_date": True,
        "exclude_void_reversal": True,
        "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
        "grain": "claim_line",
        "filters": {"codes": codes, "service_categories": services, "source_system": SOURCE_SYSTEM},
        "cost_pmpm_meaning": "PAID",
        "measurement_status": "MEASURED",
    }
    cur.execute(
        """
        INSERT INTO baselines (
            id, tenant_id, baseline_id, version, baseline_type,
            window_start_date, window_end_date, policy_id,
            data_period_ids_json, baseline_metrics_json, computed_at, computed_by,
            shift_detected, refresh_reason, created_at, updated_at
        ) VALUES (
            %s::uuid,%s::uuid,%s,%s,'FIXED',
            %s,%s,%s::uuid,
            %s,%s,%s,%s,
            false,%s,%s,%s
        )
        """,
        (
            row_id,
            TENANT,
            baseline_id,
            next_version,
            datetime(2025, 1, 1),
            datetime(2025, 12, 31, 23, 59, 59),
            pid,
            Json([]),
            Json(metrics),
            now,
            "lean_staging_reviewed_248_batch",
            f"REVIEWED_248_BATCH_CY2025_{SOURCE_SYSTEM}",
            now,
            now,
        ),
    )

    # forecast MM by month 2026-01..10
    months = []
    forecast_mm = []
    y, m = 2026, 1
    while date(y, m, 1) <= date(2026, 10, 1):
        months.append(date(y, m, 1))
        forecast_mm.append(_book_mm(cur, date(y, m, 1), date(y, m, 1)))
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1

    rates = compute_historical_rates(
        eligible_services=float(total_claims),
        eligible_member_months=book_mm,
        total_allowed=total_allowed,
    )
    freeze_ts = datetime.now(timezone.utc).replace(microsecond=0)
    continuation = compute_continuation_forecast(
        historical_rates=rates,
        forecast_member_months_by_month=forecast_mm,
        freeze_timestamp=freeze_ts.isoformat(),
    )
    effect = compute_policy_effect_prediction(intervention_model=None)
    pred_id = str(uuid.uuid4())
    pred_metrics = {
        "prediction_type": "CONTINUATION",
        "historical_rates": rates,
        "continuation": continuation,
        "policy_effect": effect,
        "measurement_book": SOURCE_SYSTEM,
        "baseline_version": next_version,
        "invariants": {"continuation_is_not_policy_effect": True},
        "allowed_pmpm_target": rates.get("allowed_pmpm"),
        "cost_change_pmpm": None,
        "cost_change_meaning": "UNESTIMATED_POLICY_EFFECT",
        "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
    }
    cur.execute(
        """
        INSERT INTO policy_predicted_impacts (
            id, tenant_id, policy_id, metrics_json, model_version, confidence,
            predicted_at, prediction_method, baseline_id, created_at, updated_at
        ) VALUES (
            %s::uuid,%s::uuid,%s::uuid,%s,'historical_rate_continuation_v1',NULL,
            %s,'HISTORICAL_RATE_CONTINUATION_V1',%s::uuid,%s,%s
        )
        """,
        (
            pred_id,
            TENANT,
            pid,
            Json(pred_metrics),
            freeze_ts.replace(tzinfo=None) + timedelta(seconds=spec["register_index"] % 50),
            row_id,
            now,
            now,
        ),
    )

    obs_count = 0
    for idx, month in enumerate(months):
        import calendar as cal

        end = date(month.year, month.month, cal.monthrange(month.year, month.month)[1])
        actual_mm = forecast_mm[idx]
        oagg = _claim_agg(cur, codes, services, month, end)
        obs = compute_observations(
            eligible_member_months=actual_mm,
            services=float(oagg["total_claims"] or 0),
            allowed_amount=float(oagg["total_allowed"] or 0),
            paid_amount=float(oagg["total_paid"] or 0),
            distinct_members=float(oagg["unique_members"] or 0),
        )
        series = continuation.get("series") or []
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
                observed_services=float(oagg["total_claims"] or 0),
                observed_allowed=float(oagg["total_allowed"] or 0),
                actual_member_months=actual_mm,
            )
        verdict = compute_verdict_prerequisites(
            endpoint_contract=None,
            policy_effect_status=STATUS_UNESTIMATED,
            observations_available=True,
            continuation_available=continuation.get("status") == "AVAILABLE",
        )
        oid = f"r248-{pid[:8]}-{month.strftime('%Y%m')}-{uuid.uuid4().hex[:6]}"
        cur.execute(
            """
            INSERT INTO observations (
                id, tenant_id, observation_id, policy_id, baseline_version_id, prediction_id,
                observation_type, observation_period_start, observation_period_end,
                metrics_json, comparisons_json, verdict_status, verdict_reason,
                recommendation, verdict_rule_version, computed_at, created_at, updated_at
            ) VALUES (
                %s::uuid,%s::uuid,%s,%s::uuid,%s::uuid,%s::uuid,
                'PERIODIC',%s,%s,
                %s,%s,'INCONCLUSIVE',%s,
                %s,'lifecycle-continuation-v1',%s,%s,%s
            )
            """,
            (
                str(uuid.uuid4()),
                TENANT,
                oid,
                pid,
                row_id,
                pred_id,
                datetime(month.year, month.month, month.day),
                datetime(end.year, end.month, end.day, 23, 59, 59),
                Json(
                    {
                        **obs,
                        "total_claims": int(oagg["total_claims"] or 0),
                        "total_allowed": float(oagg["total_allowed"] or 0),
                        "total_paid": float(oagg["total_paid"] or 0),
                        "member_months": actual_mm,
                        "measurement_book": SOURCE_SYSTEM,
                    }
                ),
                Json({"vs_continuation": recon, "policy_effect": STATUS_UNESTIMATED}),
                "; ".join(verdict.get("reason_codes") or []),
                "Keep policy-effect UNESTIMATED until supported model exists.",
                now,
                now,
                now,
            ),
        )
        obs_count += 1

    # what-if ±10%
    base_mm = float((continuation.get("horizon_totals") or {}).get("forecast_member_months") or 0)
    for sid, mm in (("plus10pct_mm", base_mm * 1.1), ("minus10pct_mm", base_mm * 0.9)):
        wi = compute_whatif_continuation(
            frozen_continuation=continuation, scenario_member_months=mm, scenario_id=sid
        )
        aid = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO analyses (id, tenant_id, policy_id, analysis_type, name, status, created_at, updated_at)
            VALUES (%s::uuid,%s::uuid,%s::uuid,'WHATIF',%s,'COMPLETED',%s,%s)
            """,
            (
                aid,
                TENANT,
                pid,
                f"R248 continuation What-If · {spec['name'][:80]} · {sid}",
                now,
                now,
            ),
        )
        cur.execute(
            """
            INSERT INTO whatif_scenario_results (
                id, tenant_id, analysis_id, policy_id, result_data_json, schema_version, created_at, updated_at
            ) VALUES (%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s,'continuation-whatif-v1',%s,%s)
            """,
            (
                str(uuid.uuid4()),
                TENANT,
                aid,
                pid,
                Json({"scenario": wi, "measurement_book": SOURCE_SYSTEM}),
                now,
                now,
            ),
        )

    return {
        "status": "COMPLETED",
        "baseline_version": next_version,
        "baseline_id": baseline_id,
        "prediction_id": pred_id,
        "observations": obs_count,
        "allowed_pmpm": allowed_pmpm,
        "continuation_status": continuation.get("status"),
        "policy_effect": effect.get("status"),
    }


def _post_batch_validate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    measurable = [r for r in results if r.get("lifecycle", {}).get("status") == "COMPLETED"]
    config_only = [r for r in results if r.get("validation", {}).get("status") == "CONFIG_ONLY"]
    thin = [r for r in results if r.get("validation", {}).get("status") == "THIN"]
    failed = [r for r in results if r.get("error")]
    # rate continuity check
    rate_ok = 0
    for r in measurable:
        b = r.get("lifecycle", {})
        v = r.get("validation", {})
        if b.get("allowed_pmpm") and v.get("book_mm_2025"):
            rate_ok += 1
    return {
        "policies_in_batch": len(results),
        "configured": len(results) - len(failed),
        "measurable_completed": len(measurable),
        "config_only": len(config_only),
        "thin_but_measured": len(thin),
        "failed": len(failed),
        "rate_continuity_checked": rate_ok,
        "pass": len(failed) == 0 and (len(measurable) + len(config_only) + len(thin) == len(results)),
    }


def run_batch(batch_num: int, batch_size: int = 10) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = _load_or_build_manifest()
    specs = batch_slice(manifest, batch_num, batch_size)
    if not specs:
        print(f"No policies for batch {batch_num}")
        return 1

    report: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "batch": batch_num,
        "batch_size": batch_size,
        "source_system": SOURCE_SYSTEM,
        "policies": [],
        "population": {},
        "validation_summary": {},
    }

    conn = psycopg2.connect(_db_url())
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        report["population"] = _ensure_population(cur, conn, manifest)
        book_mm_2025 = _book_mm(cur, PRE_START, PRE_END)
        report["population"]["book_mm_2025"] = book_mm_2025

        for spec in specs:
            print(f"BATCH {batch_num} · #{spec['register_index']} {spec['name']} [{spec['decision']}]", flush=True)
            item: Dict[str, Any] = {"register_index": spec["register_index"], "name": spec["name"], "decision": spec["decision"]}
            try:
                _configure_policy(cur, spec)
                conn.commit()
                item["configured"] = True
                validation = _validate_alignment(cur, spec, book_mm_2025)
                item["validation"] = validation
                if validation.get("status") in {"ALIGNED", "THIN"} and spec["decision"] == "CANDIDATE_MEASURE":
                    # clear prior r248 obs/pred for idempotent re-run of this policy
                    cur.execute(
                        "DELETE FROM observations WHERE tenant_id=%s::uuid AND policy_id=%s::uuid AND observation_id LIKE 'r248-%%'",
                        (TENANT, spec["policy_id"]),
                    )
                    cur.execute(
                        """
                        DELETE FROM whatif_scenario_results WHERE tenant_id=%s::uuid AND analysis_id IN (
                          SELECT id FROM analyses WHERE tenant_id=%s::uuid AND policy_id=%s::uuid
                            AND name LIKE 'R248 continuation What-If%%'
                        )
                        """,
                        (TENANT, TENANT, spec["policy_id"]),
                    )
                    cur.execute(
                        "DELETE FROM analyses WHERE tenant_id=%s::uuid AND policy_id=%s::uuid AND name LIKE 'R248 continuation What-If%%'",
                        (TENANT, spec["policy_id"]),
                    )
                    item["lifecycle"] = _run_lifecycle_for_measurable(cur, spec, validation)
                    conn.commit()
                else:
                    item["lifecycle"] = {"status": "SKIPPED_CONFIG_ONLY"}
                    conn.commit()
            except Exception as e:
                conn.rollback()
                item["error"] = str(e)
                print("  ERROR", e, flush=True)
            report["policies"].append(item)

        report["validation_summary"] = _post_batch_validate(report["policies"])
    finally:
        cur.close()
        conn.close()

    out = OUT_DIR / f"BATCH_{batch_num:02d}_REPORT.json"
    out.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report["validation_summary"], indent=2))
    print("Wrote", out)
    return 0 if report["validation_summary"].get("pass") else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=None, help="1-indexed batch number")
    ap.add_argument("--batch-size", type=int, default=10)
    ap.add_argument("--build-manifest-only", action="store_true")
    args = ap.parse_args()
    if args.build_manifest_only:
        man = build_manifest(PACK)
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text(json.dumps(man, indent=2))
        print(json.dumps(man["summary"], indent=2))
        print("Wrote", MANIFEST_PATH)
        return 0
    if not args.batch:
        raise SystemExit("--batch is required unless --build-manifest-only")
    return run_batch(args.batch, args.batch_size)


if __name__ == "__main__":
    raise SystemExit(main())
