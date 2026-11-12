#!/usr/bin/env python3
"""
Authorized lean-staging re-baseline: nine mock policies, CY2025, 5K measurement book only.

- Numerator: claim lines with source_system = SYNTHETIC_NINE_POLICY_5K_V1
  AND policy codeset ∩ service_category (definition-driven)
- Denominator: enrollment MM from the same 5K source_system only (~60,000)
- Creates NEW baseline version rows; does NOT delete/overwrite v1 combined-book baselines
- Stamps explicit measurement_book on policy metadata (configured contract, not silent filter)
- Dec4 demo / production untouched
"""
from __future__ import annotations

import json
import subprocess
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import Json, RealDictCursor

REPO = Path(__file__).resolve().parents[1]
TENANT = "00000000-0000-0000-0000-000000000001"
BASELINE_START = date(2025, 1, 1)
BASELINE_END = date(2025, 12, 31)
MEASUREMENT_BOOK = "SYNTHETIC_NINE_POLICY_5K_V1"
OUT = (
    REPO
    / "docs/production/releases/corrections/nine_mock_policies/NINE_POLICY_BASELINE_2025_5K_REPORT.json"
)


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


def _stamp_measurement_book(meta: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(meta)
    out["measurement_book"] = {
        "source_system": MEASUREMENT_BOOK,
        "population_size": 5000,
        "baseline_window": [BASELINE_START.isoformat(), BASELINE_END.isoformat()],
        "exposure_basis": "ENROLLMENT_SAME_SOURCE_SYSTEM",
        "note": (
            "Authorized mock-client measurement book for the nine PDF policies. "
            "Definition-driven codesets still apply; 500K longitudinal rows are excluded "
            "from this measurement contract. Not a silent preferred_source hardcode in the engine."
        ),
        "authorized_at": datetime.now(timezone.utc).isoformat(),
        "authorization": "user_explicit_5k_only_rebaseline",
    }
    # Keep preferred_source_system aligned with the explicit contract for API consumers,
    # but baselines below filter via measurement_book.source_system.
    out["preferred_source_system"] = MEASUREMENT_BOOK
    rem = dict(out.get("remediation") or {})
    rem["execution_eligibility"] = rem.get("execution_eligibility") or "DIRECTIONALLY_VALID"
    rem["claims_execution_blocked"] = False
    rem["measurement_book"] = out["measurement_book"]
    out["remediation"] = rem
    return out


def main() -> int:
    conn = psycopg2.connect(_database_url())
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    report: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": "hfleanstg",
        "measurement_book": MEASUREMENT_BOOK,
        "window": [BASELINE_START.isoformat(), BASELINE_END.isoformat()],
        "preserves_prior_baselines": True,
        "baselines": [],
        "prior_baselines_left_in_place": [],
        "errors": [],
    }

    # 5K enrollment MM: distinct covered days / calendar days, capped at 1.0.
    # GAP_DAYS:N = extra covered days from another span in the month (not uncovered).
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
        ), 0)::float AS mm,
        count(*)::bigint AS rows,
        count(DISTINCT member_id)::bigint AS members
        FROM enrollment_records
        WHERE tenant_id = %s
          AND source_system = %s
          AND enrollment_month >= %s
          AND enrollment_month <= %s
          AND enrollment_start_date IS NOT NULL
          AND enrollment_end_date IS NOT NULL
        """,
        (TENANT, MEASUREMENT_BOOK, date(2025, 1, 1), date(2025, 12, 1)),
    )
    mm_row = dict(cur.fetchone())
    book_mm = float(mm_row["mm"] or 0)
    report["exposure"] = {
        "member_months": book_mm,
        "enrollment_rows": int(mm_row["rows"] or 0),
        "members": int(mm_row["members"] or 0),
        "method": "ENROLLMENT_PARTIAL_MONTH_SOURCE_SCOPED",
    }
    if book_mm <= 0:
        report["errors"].append("5K enrollment member-months are zero; aborting.")
        OUT.write_text(json.dumps(report, indent=2))
        return 2

    # Snapshot prior baselines (do not delete)
    cur.execute(
        """
        SELECT b.baseline_id, b.version, b.policy_id::text, p.name,
               b.baseline_metrics_json->>'total_claims' AS total_claims,
               b.baseline_metrics_json->>'total_allowed' AS total_allowed,
               b.baseline_metrics_json->>'allowed_pmpm_target' AS allowed_pmpm,
               b.baseline_metrics_json->>'member_months' AS member_months
        FROM baselines b
        JOIN policies p ON p.id = b.policy_id
        WHERE b.tenant_id = %s
        ORDER BY p.name, b.version
        """,
        (TENANT,),
    )
    priors = [dict(r) for r in cur.fetchall()]
    report["prior_baselines_left_in_place"] = priors
    prior_by_policy = {}
    for row in priors:
        prior_by_policy.setdefault(row["policy_id"], []).append(row)

    cur.execute(
        "SELECT id::text AS id, name, policy_metadata_json AS meta FROM policies WHERE tenant_id = %s ORDER BY name",
        (TENANT,),
    )
    policies = cur.fetchall()
    if len(policies) != 9:
        report["errors"].append("Expected 9 policies, found %s" % len(policies))

    for row in policies:
        meta = row["meta"] if isinstance(row["meta"], dict) else json.loads(row["meta"] or "{}")
        stamped = _stamp_measurement_book(meta)
        cur.execute(
            "UPDATE policies SET policy_metadata_json = %s, updated_at = NOW() WHERE id = %s::uuid",
            (Json(stamped), row["id"]),
        )

        codes, services = _extract_codes(stamped)
        if not codes:
            report["baselines"].append(
                {
                    "policy_id": row["id"],
                    "name": row["name"],
                    "status": "BLOCKED",
                    "reason": "missing_codeset",
                }
            )
            continue

        clauses = [
            "c.tenant_id = %s",
            "c.source_system = %s",
            "c.service_date BETWEEN %s AND %s",
            "(c.cpt_code = ANY(%s) OR c.hcpcs_code = ANY(%s))",
            # Valid financial lines only (synthetic status in record_hash).
            "(c.record_hash IS NULL OR ("
            "c.record_hash NOT LIKE '%%\"line_status\":\"REVERSAL\"%%' "
            "AND c.record_hash NOT LIKE '%%\"line_status\":\"VOID\"%%'))",
            # Member enrolled on service date (half-open coverage).
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
        params: List[Any] = [TENANT, MEASUREMENT_BOOK, BASELINE_START, BASELINE_END, codes, codes]
        if services:
            clauses.append("c.service_category = ANY(%s)")
            params.append(services)

        cur.execute(
            f"""
            SELECT count(*)::int AS total_claims,
                   count(DISTINCT claim_id)::int AS headers,
                   count(DISTINCT member_id)::int AS unique_members,
                   COALESCE(SUM(allowed_amount),0)::float AS total_allowed,
                   COALESCE(SUM(paid_amount),0)::float AS total_paid
            FROM claims_lines c
            WHERE {' AND '.join(clauses)}
            """,
            params,
        )
        agg = dict(cur.fetchone())
        total_claims = int(agg["total_claims"] or 0)
        if total_claims == 0:
            report["baselines"].append(
                {
                    "policy_id": row["id"],
                    "name": row["name"],
                    "status": "NO_DATA",
                    "filters": {"codes": codes, "service_categories": services, "source_system": MEASUREMENT_BOOK},
                }
            )
            continue

        unique_members = int(agg["unique_members"] or 0)
        total_allowed = float(agg["total_allowed"] or 0)
        total_paid = float(agg["total_paid"] or 0)
        headers = int(agg["headers"] or 0)
        allowed_pmpm = total_allowed / book_mm
        paid_pmpm = total_paid / book_mm
        util = (total_claims / book_mm) * 1000.0

        next_version = 1 + max((int(p["version"]) for p in prior_by_policy.get(row["id"], [])), default=0)
        baseline_id = str(uuid.uuid4())
        row_id = str(uuid.uuid4())
        now = datetime.utcnow()

        metrics = {
            "member_months": book_mm,
            "unique_members": unique_members,
            "total_claims": total_claims,
            "claim_headers": headers,
            "total_paid": total_paid,
            "total_allowed": total_allowed,
            "util_rate_target_per_1000_mm": util,
            "allowed_pmpm_target": allowed_pmpm,
            "paid_pmpm_target": paid_pmpm,
            "claims_per_member": (total_claims / unique_members) if unique_members else None,
            "cost_per_claim": (total_paid / total_claims) if total_claims else 0.0,
            "avg_allowed_per_line": (total_allowed / total_claims) if total_claims else None,
            "policy_id": row["id"],
            "cost_pmpm_meaning": "PAID",
            "exposure_method": "ENROLLMENT_DISTINCT_COVERED_DAYS",
            "denominator_basis": "ENROLLMENT",
            "enrolled_rate_status": "MEASURED",
            "measurement_status": "MEASURED",
            "claims_execution_blocked": False,
            "scope_resolution": "policy_definition_codesets",
            "measurement_book": MEASUREMENT_BOOK,
            "require_enrollment_on_service_date": True,
            "exclude_void_reversal": True,
            "util_rate_per_1000_member_years": (total_claims / book_mm) * 12.0 * 1000.0,
            "baseline_window": [BASELINE_START.isoformat(), BASELINE_END.isoformat()],
            "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
            "grain": "claim_line",
            "filters": {
                "codes": codes,
                "service_categories": services,
                "source_system": MEASUREMENT_BOOK,
                "lob": None,
                "markets": None,
            },
            "prior_combined_book_baseline_ids": [
                p["baseline_id"] for p in prior_by_policy.get(row["id"], [])
            ],
            "prediction_type_note": (
                "Historical descriptive baseline on the authorized 5K measurement book only. "
                "Continuation vs policy-effect remain separate."
            ),
        }

        cur.execute(
            """
            INSERT INTO baselines (
                id, tenant_id, baseline_id, version, baseline_type,
                window_start_date, window_end_date, policy_id,
                data_period_ids_json, baseline_metrics_json, computed_at, computed_by,
                shift_detected, refresh_reason, created_at, updated_at
            ) VALUES (
                %s::uuid, %s::uuid, %s, %s, %s,
                %s, %s, %s::uuid,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            """,
            (
                row_id,
                TENANT,
                baseline_id,
                next_version,
                "FIXED",
                datetime(2025, 1, 1),
                datetime(2025, 12, 31, 23, 59, 59),
                row["id"],
                Json([]),
                Json(metrics),
                now,
                "lean_staging_nine_policy_baselines_2025_5k",
                False,
                "NINE_POLICY_LIFECYCLE_CY2025_5K_MEASUREMENT_BOOK",
                now,
                now,
            ),
        )

        prior_pmpm = None
        if prior_by_policy.get(row["id"]):
            try:
                prior_pmpm = float(prior_by_policy[row["id"]][-1]["allowed_pmpm"])
            except (TypeError, ValueError):
                prior_pmpm = None

        report["baselines"].append(
            {
                "policy_id": row["id"],
                "name": row["name"],
                "policy_key": stamped.get("policy_key"),
                "status": "CREATED",
                "baseline_id": baseline_id,
                "version": next_version,
                "total_claims": total_claims,
                "claim_headers": headers,
                "unique_members": unique_members,
                "member_months": book_mm,
                "total_allowed": total_allowed,
                "avg_allowed_per_line": metrics["avg_allowed_per_line"],
                "allowed_pmpm_target": allowed_pmpm,
                "prior_combined_book_pmpm": prior_pmpm,
                "filters": metrics["filters"],
            }
        )
        print(
            "OK %s v%s claims=%s allowed_pmpm=%.4f (prior_combined=%.4f)"
            % (
                row["name"],
                next_version,
                total_claims,
                allowed_pmpm,
                prior_pmpm or 0.0,
            ),
            flush=True,
        )

    conn.commit()
    created = sum(1 for b in report["baselines"] if b.get("status") == "CREATED")
    report["summary"] = {
        "policies": len(policies),
        "created_5k_baselines": created,
        "prior_baselines_preserved": len(priors),
        "measurement_book_mm": book_mm,
        "success": created == 9 and not report["errors"],
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
