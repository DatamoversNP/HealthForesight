#!/usr/bin/env python3
"""
Lean staging ONLY: validate the nine mock policies, align synthetic scope where
configured product filters cannot match the loaded book, then compute FIXED
baselines for 2025-01-01 .. 2025-12-31.

Eligibility is definition-driven (codesets / scope / levers). Does not filter by
preferred_source_system. Does not invent policy-effect savings or verdicts.
Preserves Dec4 demo / production.
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
POLICY_START = date(2026, 1, 1)
OUT = REPO / "docs/production/releases/corrections/nine_mock_policies/NINE_POLICY_BASELINE_2025_REPORT.json"


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


def _unrestricted(val: Any) -> bool:
    if val is None:
        return True
    items = _as_list(val)
    if not items:
        return True
    return bool({x.upper() for x in items} & {"ALL", "*", "ANY"})


def _extract_codes(meta: Dict[str, Any]) -> Tuple[List[str], List[str], List[str]]:
    scope = meta.get("scope") if isinstance(meta.get("scope"), dict) else {}
    levers = meta.get("policy_levers") if isinstance(meta.get("policy_levers"), list) else []
    procedure = _as_list(scope.get("procedure_codes"))
    diagnosis = _as_list(scope.get("diagnosis_codes"))
    services = _as_list(scope.get("service_categories") or scope.get("service_category"))
    for lever in levers:
        if not isinstance(lever, dict):
            continue
        blob: Dict[str, Any] = {}
        blob.update(lever.get("targets") or {})
        blob.update(lever.get("parameters") or {})
        for key in ("procedure_codes", "cpt_codes", "hcpcs_codes", "codes", "target_codes"):
            procedure.extend(_as_list(blob.get(key)))
        for key in ("diagnosis_codes", "icd_codes", "diagnosis"):
            diagnosis.extend(_as_list(blob.get(key)))
        for key in ("service_categories", "service_category", "categories"):
            services.extend(_as_list(blob.get(key)))
    return (
        sorted(set(procedure)),
        sorted(set(diagnosis)),
        sorted(set(services)),
    )


def _validate_policy(name: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    scope = meta.get("scope") if isinstance(meta.get("scope"), dict) else {}
    levers = meta.get("policy_levers") if isinstance(meta.get("policy_levers"), list) else []
    rem = meta.get("remediation") if isinstance(meta.get("remediation"), dict) else {}
    procedure, diagnosis, services = _extract_codes(meta)
    issues: List[str] = []
    if not procedure:
        issues.append("missing_procedure_codeset")
    if not scope:
        issues.append("missing_scope")
    if not levers:
        issues.append("missing_levers")
    lob = scope.get("lob")
    markets = scope.get("markets")
    synthetic_product_mismatch = False
    if not _unrestricted(lob) and any(x.upper() == "MEDICARE" for x in _as_list(lob)):
        synthetic_product_mismatch = True
        issues.append("scope_lob_medicare_vs_synthetic_commercial_book")
    if not _unrestricted(markets) and any(x.upper() == "NC" for x in _as_list(markets)):
        synthetic_product_mismatch = True
        issues.append("scope_market_nc_vs_synthetic_market")
    return {
        "name": name,
        "codes": procedure,
        "diagnosis_codes": diagnosis,
        "service_categories": services,
        "lob": lob,
        "markets": markets,
        "execution_eligibility": rem.get("execution_eligibility"),
        "register_status": rem.get("register_status"),
        "code_mapping_state": rem.get("code_mapping_state"),
        "policy_key": meta.get("policy_key"),
        "issues": issues,
        "structurally_configured": bool(procedure and scope and levers),
        "synthetic_product_mismatch": synthetic_product_mismatch,
    }


def _align_meta(meta: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(meta)
    rem = dict(out.get("remediation") or {})
    rem["execution_eligibility"] = "DIRECTIONALLY_VALID"
    rem["claims_execution_blocked"] = False
    rem["baseline_measurement"] = {
        "mode": "DIRECTIONAL_SYNTHETIC_HISTORICAL",
        "window": [BASELINE_START.isoformat(), BASELINE_END.isoformat()],
        "note": (
            "Historical descriptive baseline from configured codesets. "
            "Not authority-certified adjudication and not a policy-effect estimate."
        ),
        "aligned_at": datetime.now(timezone.utc).isoformat(),
    }
    out["remediation"] = rem
    scope = dict(out.get("scope") or {})
    if validation.get("synthetic_product_mismatch"):
        scope["lob"] = None
        scope["markets"] = None
        scope["states"] = None
        scope["synthetic_scope_alignment"] = {
            "cleared_lob_markets": True,
            "reason": "Configured Medicare/NC filters do not match loaded COMMERCIAL/SYNTHETIC claims.",
            "authority_labels_retained": scope.get("source_authority"),
        }
    out["scope"] = scope
    out["effective_period"] = {
        "start_date": POLICY_START.isoformat() + "T00:00:00",
        "end_date": None,
    }
    out.pop("preferred_source_system", None)
    return out


def _member_months(cur, start: date, end: date) -> Tuple[Optional[float], str]:
    cur.execute(
        """
        SELECT COALESCE(SUM(
            GREATEST(
                0,
                (
                    LEAST(
                        COALESCE(enrollment_end_date, %s),
                        %s
                    )::date
                    - GREATEST(
                        COALESCE(enrollment_start_date, enrollment_month, %s),
                        %s
                    )::date
                    + 1
                )::numeric / 30.4375
            )
        ), 0) AS mm
        FROM enrollment_records
        WHERE tenant_id = %s
          AND COALESCE(enrollment_start_date, enrollment_month) <= %s
          AND COALESCE(enrollment_end_date, %s) >= %s
        """,
        (end, end, start, start, TENANT, end, end, start),
    )
    mm = float(cur.fetchone()["mm"] or 0)
    if mm > 0:
        return mm, "ENROLLMENT_PARTIAL_MONTH"
    return None, "CLAIMANT_TIMES_CALENDAR_MONTHS"


def _aggregate(cur, codes: List[str], services: List[str], lob: Any, markets: Any) -> Optional[Dict[str, Any]]:
    clauses = [
        "tenant_id = %s",
        "service_date >= %s",
        "service_date <= %s",
    ]
    params: List[Any] = [TENANT, BASELINE_START, BASELINE_END]
    if codes:
        clauses.append("(cpt_code = ANY(%s) OR hcpcs_code = ANY(%s))")
        params.extend([codes, codes])
    if services:
        clauses.append("service_category = ANY(%s)")
        params.append(services)
    if lob and not _unrestricted(lob):
        clauses.append("lob = ANY(%s)")
        params.append(_as_list(lob))
    if markets and not _unrestricted(markets):
        clauses.append("market = ANY(%s)")
        params.append(_as_list(markets))
    sql = f"""
        SELECT count(*)::int AS total_claims,
               count(DISTINCT member_id)::int AS unique_members,
               COALESCE(SUM(allowed_amount), 0)::float AS total_allowed,
               COALESCE(SUM(paid_amount), 0)::float AS total_paid
        FROM claims_lines
        WHERE {' AND '.join(clauses)}
    """
    cur.execute(sql, params)
    row = cur.fetchone()
    if not row or int(row["total_claims"] or 0) == 0:
        return None
    return dict(row)


def main() -> int:
    conn = psycopg2.connect(_database_url())
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)
    report: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": "hfleanstg",
        "window": [BASELINE_START.isoformat(), BASELINE_END.isoformat()],
        "policy_start": POLICY_START.isoformat(),
        "validation": [],
        "data_check": {},
        "baselines": [],
        "errors": [],
    }

    cur.execute(
        """
        SELECT count(*)::int AS n,
               count(*) FILTER (WHERE source_system = 'SYNTHETIC_NINE_POLICY_5K_V1')::int AS n_5k,
               count(*) FILTER (WHERE source_system = 'SYNTHETIC_LONGITUDINAL_V1')::int AS n_500k
        FROM claims_lines
        WHERE tenant_id = %s
          AND service_date >= %s AND service_date <= %s
        """,
        (TENANT, BASELINE_START, BASELINE_END),
    )
    cov = cur.fetchone()
    report["data_check"] = {
        "claims_cy2025": int(cov["n"]),
        "claims_cy2025_5k": int(cov["n_5k"]),
        "claims_cy2025_500k": int(cov["n_500k"]),
        "load_required": int(cov["n"]) == 0,
    }
    if report["data_check"]["load_required"]:
        report["errors"].append("No CY2025 claims present; load data before baseline.")
        OUT.write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return 2

    measured_mm, exposure_method = _member_months(cur, BASELINE_START, BASELINE_END)

    cur.execute(
        "SELECT id::text AS id, name, policy_metadata_json AS meta FROM policies WHERE tenant_id = %s ORDER BY name",
        (TENANT,),
    )
    rows = cur.fetchall()
    if len(rows) != 9:
        report["errors"].append("Expected 9 policies, found %s" % len(rows))

    for row in rows:
        meta = row["meta"] if isinstance(row["meta"], dict) else json.loads(row["meta"] or "{}")
        validation = _validate_policy(row["name"], meta)
        report["validation"].append(validation)
        if not validation["structurally_configured"]:
            report["baselines"].append(
                {
                    "policy_id": row["id"],
                    "name": row["name"],
                    "status": "BLOCKED",
                    "reason": "policy_configuration_incomplete",
                    "issues": validation["issues"],
                }
            )
            continue

        aligned = _align_meta(meta, validation)
        cur.execute(
            "UPDATE policies SET policy_metadata_json = %s, updated_at = NOW() WHERE id = %s::uuid",
            (Json(aligned), row["id"]),
        )

        procedure, _diagnosis, services = _extract_codes(aligned)
        scope = aligned.get("scope") or {}
        lob = scope.get("lob")
        markets = scope.get("markets")
        agg = _aggregate(cur, procedure, services, lob, markets)
        if not agg:
            report["baselines"].append(
                {
                    "policy_id": row["id"],
                    "name": row["name"],
                    "status": "NO_DATA",
                    "filters": {
                        "codes": procedure,
                        "service_categories": services,
                        "lob": lob,
                        "markets": markets,
                    },
                    "validation_issues": validation["issues"],
                }
            )
            continue

        unique_members = int(agg["unique_members"])
        if measured_mm and measured_mm > 0:
            member_months = float(measured_mm)
            enrollment_measured = True
            method = exposure_method
        else:
            member_months = float(unique_members * 12)
            enrollment_measured = False
            method = "CLAIMANT_TIMES_CALENDAR_MONTHS"

        total_claims = int(agg["total_claims"])
        total_allowed = float(agg["total_allowed"])
        total_paid = float(agg["total_paid"])
        allowed_pmpm = (total_allowed / member_months) if member_months > 0 else None
        paid_pmpm = (total_paid / member_months) if member_months > 0 else None
        util = (total_claims / member_months * 1000.0) if member_months > 0 else None

        metrics = {
            "member_months": member_months,
            "unique_members": unique_members,
            "total_claims": total_claims,
            "total_paid": total_paid,
            "total_allowed": total_allowed,
            "util_rate_target_per_1000_mm": util,
            "allowed_pmpm_target": allowed_pmpm,
            "paid_pmpm_target": paid_pmpm,
            "claims_per_member": (total_claims / unique_members) if unique_members else None,
            "cost_per_claim": (total_paid / total_claims) if total_claims else 0.0,
            "policy_id": row["id"],
            "cost_pmpm_meaning": "PAID",
            "exposure_method": method,
            "claims_execution_blocked": False,
            "scope_resolution": "policy_definition_codesets",
            "denominator_basis": "ENROLLMENT" if enrollment_measured else "CLAIMANT",
            "enrolled_rate_status": "MEASURED" if enrollment_measured else "NOT_MEASURABLE",
            "measurement_status": "MEASURED",
            "baseline_window": [BASELINE_START.isoformat(), BASELINE_END.isoformat()],
            "evidence_class": "SYNTHETIC_ILLUSTRATIVE",
            "prediction_type_note": (
                "Historical descriptive baseline only. Continuation vs policy-effect remain separate."
            ),
            "filters": {
                "codes": procedure,
                "service_categories": services,
                "lob": lob,
                "markets": markets,
            },
        }

        baseline_id = str(uuid.uuid4())
        row_id = str(uuid.uuid4())
        now = datetime.utcnow()
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
                1,
                "FIXED",
                datetime(2025, 1, 1),
                datetime(2025, 12, 31, 23, 59, 59),
                row["id"],
                Json([]),
                Json(metrics),
                now,
                "lean_staging_nine_policy_baselines_2025",
                False,
                "NINE_POLICY_LIFECYCLE_CY2025",
                now,
                now,
            ),
        )
        report["baselines"].append(
            {
                "policy_id": row["id"],
                "name": row["name"],
                "status": "CREATED",
                "baseline_id": baseline_id,
                "total_claims": total_claims,
                "unique_members": unique_members,
                "member_months": member_months,
                "total_allowed": total_allowed,
                "allowed_pmpm_target": allowed_pmpm,
                "util_rate_target_per_1000_mm": util,
                "exposure_method": method,
                "denominator_basis": metrics["denominator_basis"],
                "filters": metrics["filters"],
                "validation_issues": validation["issues"],
            }
        )
        print(
            "OK %s: claims=%s allowed_pmpm=%s"
            % (row["name"], total_claims, None if allowed_pmpm is None else round(allowed_pmpm, 4)),
            flush=True,
        )

    conn.commit()
    created = sum(1 for b in report["baselines"] if b.get("status") == "CREATED")
    report["summary"] = {
        "policies": len(rows),
        "created": created,
        "blocked_or_empty": len(rows) - created,
        "success": created == 9 and not report["errors"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report["summary"], indent=2))
    print("Wrote %s" % OUT)
    cur.close()
    conn.close()
    return 0 if report["summary"]["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
