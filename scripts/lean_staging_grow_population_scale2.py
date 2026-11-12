#!/usr/bin/env python3
"""Grow lean-staging synthetic population by cloning claims + enrollment (scale +1 cohort).

Also scales observation / baseline exposure fields so absolute period-$ rollups grow with
the book. Rates (ΔPMPM, util %) stay unchanged.

Refuses non-hfleanstg databases. Idempotent via member_id suffix _G2.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import psycopg2
from psycopg2.extras import Json, RealDictCursor

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/production/releases/corrections/reviewed_248/POPULATION_SCALE2_REPORT.json"
TENANT = "00000000-0000-0000-0000-000000000001"
SUFFIX = "_G2"
SCALE = 2  # original + one clone cohort


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


def _scale_numeric_fields(obj: Dict[str, Any], keys: tuple[str, ...], factor: float) -> int:
    n = 0
    for k in keys:
        if k in obj and obj[k] is not None:
            try:
                obj[k] = float(obj[k]) * factor
                n += 1
            except (TypeError, ValueError):
                pass
    return n


def main() -> None:
    report: Dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "scale": SCALE,
        "suffix": SUFFIX,
    }
    conn = psycopg2.connect(_db_url())
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT count(*) AS n FROM claims_lines WHERE member_id LIKE %s", (f"%{SUFFIX}",))
    already_claims = cur.fetchone()["n"]
    cur.execute(
        "SELECT count(*) AS n FROM enrollment_records WHERE member_id LIKE %s",
        (f"%{SUFFIX}",),
    )
    already_enroll = cur.fetchone()["n"]
    report["already_cloned"] = {"claims": already_claims, "enrollment": already_enroll}

    if already_claims == 0:
        print("Cloning claims_lines (+1 cohort)…", flush=True)
        cur.execute(
            f"""
            INSERT INTO claims_lines (
              id, tenant_id, claim_id, claim_line_id, member_id, provider_id,
              service_date, paid_date, adjudication_date, lob, market,
              cpt_code, hcpcs_code, drg_code, icd10_diagnosis_codes, icd10_procedure_codes,
              service_category, place_of_service, units, allowed_amount, paid_amount,
              member_cost_share, in_network, requires_prior_auth, prior_auth_approved,
              prior_auth_id, facility_type, system_affiliation,
              rendering_provider_id, billing_provider_id, referring_provider_id,
              source_system, source_file_id, ingestion_id, record_hash, created_at, updated_at
            )
            SELECT
              gen_random_uuid(), tenant_id,
              claim_id || '{SUFFIX}', claim_line_id || '{SUFFIX}',
              member_id || '{SUFFIX}',
              CASE WHEN provider_id IS NULL THEN NULL ELSE provider_id || '{SUFFIX}' END,
              service_date, paid_date, adjudication_date, lob, market,
              cpt_code, hcpcs_code, drg_code, icd10_diagnosis_codes, icd10_procedure_codes,
              service_category, place_of_service, units, allowed_amount, paid_amount,
              member_cost_share, in_network, requires_prior_auth, prior_auth_approved,
              prior_auth_id, facility_type, system_affiliation,
              rendering_provider_id, billing_provider_id, referring_provider_id,
              coalesce(source_system, 'SYNTHETIC') || '{SUFFIX}',
              source_file_id, ingestion_id,
              md5(coalesce(record_hash, claim_line_id) || '{SUFFIX}'),
              now(), now()
            FROM claims_lines
            WHERE member_id NOT LIKE '%{SUFFIX}'
            """
        )
        report["claims_inserted"] = cur.rowcount
        conn.commit()
        print(f"  inserted {report['claims_inserted']} claim lines", flush=True)
    else:
        report["claims_inserted"] = 0
        print(f"Claims already cloned ({already_claims}); skipping.", flush=True)

    if already_enroll == 0:
        print("Cloning enrollment_records (+1 cohort)…", flush=True)
        cur.execute(
            f"""
            INSERT INTO enrollment_records (
              id, tenant_id, member_id, enrollment_month, lob, market, age_band, gender,
              risk_score, network_tier, enrolled_flag, enrollment_start_date, enrollment_end_date,
              product_type, segment, source_system, source_file_id, ingestion_id, record_hash,
              created_at, updated_at
            )
            SELECT
              gen_random_uuid(), tenant_id, member_id || '{SUFFIX}', enrollment_month,
              lob, market, age_band, gender, risk_score, network_tier, enrolled_flag,
              enrollment_start_date, enrollment_end_date, product_type, segment,
              coalesce(source_system, 'SYNTHETIC') || '{SUFFIX}',
              source_file_id, ingestion_id,
              md5(coalesce(record_hash, member_id::text) || '{SUFFIX}'),
              now(), now()
            FROM enrollment_records
            WHERE member_id NOT LIKE '%{SUFFIX}'
            """
        )
        report["enrollment_inserted"] = cur.rowcount
        conn.commit()
        print(f"  inserted {report['enrollment_inserted']} enrollment rows", flush=True)
    else:
        report["enrollment_inserted"] = 0
        print(f"Enrollment already cloned ({already_enroll}); skipping.", flush=True)

    # Scale observation exposures once (marker on metrics)
    print("Scaling observation exposures ×2 where not yet scaled…", flush=True)
    cur.execute(
        """
        SELECT id, metrics_json, comparisons_json
        FROM observations
        WHERE tenant_id=%s::uuid
          AND coalesce(metrics_json->>'population_scale_factor','1') = '1'
        """,
        (TENANT,),
    )
    rows = cur.fetchall()
    exposure_keys = (
        "member_months",
        "eligible_member_months",
        "total_allowed",
        "total_paid",
        "allowed_amount",
        "paid_amount",
        "total_claims",
        "services",
        "unique_members",
        "distinct_members",
    )
    updated = 0
    for row in rows:
        metrics = dict(row["metrics_json"] or {})
        comparisons = dict(row["comparisons_json"] or {})
        _scale_numeric_fields(metrics, exposure_keys, SCALE)
        metrics["population_scale_factor"] = SCALE
        metrics["population_scale_note"] = (
            f"Exposure scaled ×{SCALE} after synthetic population cohort clone {SUFFIX}."
        )
        for block_name in ("vs_baseline", "vs_policy_baseline", "vs_predicted", "vs_continuation"):
            block = comparisons.get(block_name)
            if not isinstance(block, dict):
                continue
            block = dict(block)
            for k in (
                "baseline_member_months",
                "observed_member_months",
                "baseline_allowed",
                "observed_allowed",
            ):
                if block.get(k) is not None:
                    try:
                        block[k] = float(block[k]) * SCALE
                    except (TypeError, ValueError):
                        pass
            mm = block.get("member_months")
            if isinstance(mm, dict):
                mm = dict(mm)
                for mk in ("baseline", "observed", "predicted"):
                    if mm.get(mk) is not None:
                        try:
                            mm[mk] = float(mm[mk]) * SCALE
                        except (TypeError, ValueError):
                            pass
                block["member_months"] = mm
            # Keep rate fields (cost_change_pmpm, utilization_change_pct) unchanged.
            comparisons[block_name] = block
        cur.execute(
            """
            UPDATE observations
            SET metrics_json=%s, comparisons_json=%s, updated_at=now()
            WHERE id=%s::uuid
            """,
            (Json(metrics), Json(comparisons), str(row["id"])),
        )
        updated += 1
        if updated % 500 == 0:
            conn.commit()
            print(f"  observations {updated}/{len(rows)}", flush=True)
    conn.commit()
    report["observations_scaled"] = updated

    print("Scaling baseline exposures ×2 where not yet scaled…", flush=True)
    cur.execute(
        """
        SELECT id, baseline_metrics_json
        FROM baselines
        WHERE tenant_id=%s::uuid
          AND coalesce(baseline_metrics_json->>'population_scale_factor','1') = '1'
        """,
        (TENANT,),
    )
    brows = cur.fetchall()
    b_updated = 0
    for row in brows:
        metrics = dict(row["baseline_metrics_json"] or {})
        _scale_numeric_fields(
            metrics,
            (
                "member_months",
                "unique_members",
                "total_claims",
                "total_allowed",
                "total_paid",
            ),
            SCALE,
        )
        metrics["population_scale_factor"] = SCALE
        cur.execute(
            "UPDATE baselines SET baseline_metrics_json=%s, updated_at=now() WHERE id=%s::uuid",
            (Json(metrics), str(row["id"])),
        )
        b_updated += 1
    conn.commit()
    report["baselines_scaled"] = b_updated

    cur.execute(
        """
        SELECT
          (SELECT count(*) FROM claims_lines) AS claim_lines,
          (SELECT count(distinct member_id) FROM claims_lines) AS claim_members,
          (SELECT coalesce(sum(allowed_amount),0) FROM claims_lines) AS allowed,
          (SELECT count(*) FROM enrollment_records) AS enroll_rows,
          (SELECT count(distinct member_id) FROM enrollment_records) AS enroll_members
        """
    )
    report["after_counts"] = {k: float(v) if hasattr(v, "as_tuple") else v for k, v in dict(cur.fetchone()).items()}
    # Absolute $ estimate after scale
    cur.execute(
        """
        WITH latest AS (
          SELECT DISTINCT ON (policy_id)
            (metrics_json->>'cost_change_pmpm')::float AS d,
            coalesce((metrics_json->>'member_months')::float, 0) AS mm
          FROM observations
          WHERE metrics_json ? 'cost_change_pmpm'
          ORDER BY policy_id, updated_at DESC
        )
        SELECT count(*) AS n, sum(d*mm) AS period_abs, sum(d*mm*12) AS ann_abs
        FROM latest
        """
    )
    report["executive_period_dollar_estimate"] = dict(cur.fetchone())
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report, indent=2, default=str), flush=True)
    print("Wrote", OUT, flush=True)
    conn.close()


if __name__ == "__main__":
    main()
