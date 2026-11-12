#!/usr/bin/env python3
"""Read-only nine-policy CY2025 baseline financial reconciliation (lean staging).

Does not mutate claims, enrollment, policies, or baselines.
"""
from __future__ import annotations

import json
import subprocess
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

TENANT = "00000000-0000-0000-0000-000000000001"
S, E = date(2025, 1, 1), date(2025, 12, 31)
OUT = Path("docs/production/releases/corrections/nine_mock_policies/NINE_POLICY_AUDIT_RESULTS.json")


def _url() -> str:
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
        raise SystemExit("Refusing non-lean staging URL")
    return url


def money(x: Any) -> float:
    return float(Decimal(str(x or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def main() -> int:
    conn = psycopg2.connect(_url())
    conn.set_session(readonly=True, autocommit=True)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Official enrollment exposure formula used by product (enrollment_month window).
    cur.execute(
        """
        SELECT COALESCE(SUM(
            (
                (enrollment_end_date - enrollment_start_date)
                + CASE
                    WHEN segment LIKE 'GAP_DAYS:%%'
                    THEN CAST(split_part(segment, ':', 2) AS integer)
                    ELSE 0
                  END
            )::double precision
            / EXTRACT(DAY FROM (date_trunc('month', enrollment_month) + INTERVAL '1 month - 1 day'))
        ), 0)::float AS mm,
        count(*)::bigint AS rows,
        count(DISTINCT member_id)::bigint AS members
        FROM enrollment_records
        WHERE tenant_id = %s
          AND enrollment_month >= %s
          AND enrollment_month <= %s
          AND enrollment_start_date IS NOT NULL
          AND enrollment_end_date IS NOT NULL
        """,
        (TENANT, date(2025, 1, 1), date(2025, 12, 1)),
    )
    product_mm = dict(cur.fetchone())

    # Script formula used when creating the nine FIXED baselines.
    cur.execute(
        """
        SELECT COALESCE(SUM(
          GREATEST(0, (
            LEAST(COALESCE(enrollment_end_date, %s), %s)::date
            - GREATEST(COALESCE(enrollment_start_date, enrollment_month, %s), %s)::date
            + 1
          )::numeric / 30.4375)
        ),0)::float AS mm
        FROM enrollment_records
        WHERE tenant_id = %s
          AND COALESCE(enrollment_start_date, enrollment_month) <= %s
          AND COALESCE(enrollment_end_date, %s) >= %s
        """,
        (E, E, S, S, TENANT, E, E, S),
    )
    script_mm = float(cur.fetchone()["mm"])

    cur.execute(
        """
        SELECT source_system,
               count(*)::bigint AS rows,
               count(DISTINCT member_id)::bigint AS members
        FROM enrollment_records WHERE tenant_id=%s
        GROUP BY 1 ORDER BY 2 DESC
        """,
        (TENANT,),
    )
    enroll_by_src = [dict(r) for r in cur.fetchall()]

    cur.execute(
        """
        SELECT source_system,
               count(*)::bigint AS lines,
               count(DISTINCT member_id)::bigint AS members,
               count(DISTINCT claim_id)::bigint AS headers,
               COALESCE(SUM(allowed_amount),0)::float AS allowed,
               COALESCE(SUM(paid_amount),0)::float AS paid,
               COALESCE(AVG(allowed_amount),0)::float AS avg_allowed,
               COALESCE(percentile_cont(0.5) WITHIN GROUP (ORDER BY allowed_amount),0)::float AS med_allowed
        FROM claims_lines
        WHERE tenant_id=%s AND service_date BETWEEN %s AND %s
        GROUP BY 1 ORDER BY 2 DESC
        """,
        (TENANT, S, E),
    )
    claims_by_src = [dict(r) for r in cur.fetchall()]

    cur.execute(
        """
        SELECT service_category,
               count(*)::bigint AS lines,
               COALESCE(SUM(allowed_amount),0)::float AS allowed,
               COALESCE(AVG(allowed_amount),0)::float AS avg_allowed,
               COALESCE(percentile_cont(0.1) WITHIN GROUP (ORDER BY allowed_amount),0)::float AS p10,
               COALESCE(percentile_cont(0.5) WITHIN GROUP (ORDER BY allowed_amount),0)::float AS p50,
               COALESCE(percentile_cont(0.9) WITHIN GROUP (ORDER BY allowed_amount),0)::float AS p90,
               count(*) FILTER (WHERE allowed_amount < 0)::bigint AS neg,
               count(*) FILTER (WHERE allowed_amount = 0)::bigint AS zero,
               count(*) FILTER (WHERE allowed_amount > 50000)::bigint AS gt50k
        FROM claims_lines
        WHERE tenant_id=%s AND service_date BETWEEN %s AND %s
          AND service_category IS NOT NULL
        GROUP BY 1
        ORDER BY allowed DESC
        LIMIT 40
        """,
        (TENANT, S, E),
    )
    by_cat = [dict(r) for r in cur.fetchall()]

    cur.execute(
        """
        SELECT count(*) FILTER (WHERE allowed_amount < 0) AS neg,
               count(*) FILTER (WHERE allowed_amount = 0) AS zero,
               count(*) FILTER (WHERE allowed_amount > 100000) AS gt100k,
               COALESCE(percentile_cont(0.5) WITHIN GROUP (ORDER BY allowed_amount),0)::float AS med,
               COALESCE(AVG(allowed_amount),0)::float AS avg,
               COALESCE(MAX(allowed_amount),0)::float AS max_allowed,
               count(*)::bigint AS lines
        FROM claims_lines
        WHERE tenant_id=%s AND service_date BETWEEN %s AND %s
        """,
        (TENANT, S, E),
    )
    overall = dict(cur.fetchone())

    # Procedure-specific prices for key codes (realism)
    cur.execute(
        """
        SELECT COALESCE(cpt_code, hcpcs_code) AS code,
               count(*)::bigint AS lines,
               COALESCE(AVG(allowed_amount),0)::float AS avg_allowed,
               COALESCE(percentile_cont(0.5) WITHIN GROUP (ORDER BY allowed_amount),0)::float AS p50,
               COALESCE(percentile_cont(0.1) WITHIN GROUP (ORDER BY allowed_amount),0)::float AS p10,
               COALESCE(percentile_cont(0.9) WITHIN GROUP (ORDER BY allowed_amount),0)::float AS p90
        FROM claims_lines
        WHERE tenant_id=%s AND service_date BETWEEN %s AND %s
          AND COALESCE(cpt_code, hcpcs_code) = ANY(%s)
        GROUP BY 1 ORDER BY 1
        """,
        (
            TENANT,
            S,
            E,
            [
                "72148",
                "72149",
                "70551",
                "70553",
                "70540",
                "70542",
                "96413",
                "J1745",
                "97110",
                "97112",
                "97140",
                "27447",
                "64483",
            ],
        ),
    )
    code_prices = [dict(r) for r in cur.fetchall()]

    cur.execute(
        """
        SELECT b.baseline_id, b.policy_id::text, p.name, b.baseline_type,
               b.window_start_date::text, b.window_end_date::text,
               b.baseline_metrics_json AS m, p.policy_metadata_json AS meta
        FROM baselines b
        JOIN policies p ON p.id = b.policy_id
        WHERE b.tenant_id = %s
        ORDER BY p.name
        """,
        (TENANT,),
    )
    baselines = cur.fetchall()

    audit: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": "hfleanstg",
        "window": [str(S), str(E)],
        "read_only": True,
        "mutations": "none",
        "grain_definition": {
            "selected_claims_in_report": "claims_lines rows (claim lines), not claim headers",
            "stored_pmpm_formula": "sum(allowed_amount on selected claim lines) / member_months",
            "stored_member_months_source": (
                "Single tenant-wide enrollment member-month total reused for every policy "
                "(lean_staging_nine_policy_baselines_2025.py)."
            ),
        },
        "tenant_exposure": {
            "enrollment_by_source": enroll_by_src,
            "product_enrollment_mm_cy2025": product_mm,
            "script_tenant_wide_mm_cy2025": script_mm,
        },
        "cy2025_claims_by_source": claims_by_src,
        "realism": {
            "overall_allowed": overall,
            "allowed_by_service_category_top40": by_cat,
            "key_procedure_allowed_distributions": code_prices,
        },
        "policies": [],
    }

    for b in baselines:
        meta = b["meta"] if isinstance(b["meta"], dict) else json.loads(b["meta"] or "{}")
        m = b["m"] if isinstance(b["m"], dict) else json.loads(b["m"] or "{}")
        filters = m.get("filters") or {}
        codes = list(filters.get("codes") or (meta.get("scope") or {}).get("procedure_codes") or [])
        services = list(
            filters.get("service_categories")
            if filters.get("service_categories") is not None
            else ((meta.get("scope") or {}).get("service_categories") or [])
        )
        codes = [str(c) for c in codes]
        services = [str(s) for s in services]
        lob = filters.get("lob")
        markets = filters.get("markets")

        clauses = ["tenant_id=%s", "service_date BETWEEN %s AND %s"]
        params: List[Any] = [TENANT, S, E]
        if codes:
            clauses.append("(cpt_code = ANY(%s) OR hcpcs_code = ANY(%s))")
            params.extend([codes, codes])
        if services:
            clauses.append("service_category = ANY(%s)")
            params.append(services)
        where = " AND ".join(clauses)

        cur.execute(
            f"""
            SELECT count(*)::bigint AS lines,
                   count(DISTINCT claim_id)::bigint AS headers,
                   count(DISTINCT member_id)::bigint AS members,
                   COALESCE(SUM(allowed_amount),0)::float AS allowed,
                   COALESCE(SUM(paid_amount),0)::float AS paid,
                   COALESCE(SUM(COALESCE(units,1)),0)::float AS units,
                   COALESCE(AVG(allowed_amount),0)::float AS avg_allowed,
                   COALESCE(percentile_cont(0.1) WITHIN GROUP (ORDER BY allowed_amount),0)::float AS p10,
                   COALESCE(percentile_cont(0.5) WITHIN GROUP (ORDER BY allowed_amount),0)::float AS p50,
                   COALESCE(percentile_cont(0.9) WITHIN GROUP (ORDER BY allowed_amount),0)::float AS p90,
                   count(*) FILTER (WHERE source_system='SYNTHETIC_NINE_POLICY_5K_V1')::bigint AS lines_5k,
                   count(*) FILTER (WHERE source_system='SYNTHETIC_LONGITUDINAL_V1')::bigint AS lines_500k,
                   count(DISTINCT member_id) FILTER (WHERE source_system='SYNTHETIC_NINE_POLICY_5K_V1')::bigint AS members_5k,
                   count(DISTINCT member_id) FILTER (WHERE source_system='SYNTHETIC_LONGITUDINAL_V1')::bigint AS members_500k,
                   count(*) FILTER (WHERE allowed_amount < 0)::bigint AS neg_allowed,
                   count(*) FILTER (WHERE allowed_amount = 0)::bigint AS zero_allowed
            FROM claims_lines WHERE {where}
            """,
            params,
        )
        agg = dict(cur.fetchone())
        lines = int(agg["lines"] or 0)
        allowed = float(agg["allowed"] or 0)
        paid = float(agg["paid"] or 0)
        claimants = int(agg["members"] or 0)
        claimant_mm = float(claimants * 12)

        cur.execute(
            f"""
            SELECT COALESCE(cpt_code, hcpcs_code) AS code,
                   count(*)::bigint AS lines,
                   COALESCE(SUM(allowed_amount),0)::float AS allowed,
                   COALESCE(AVG(allowed_amount),0)::float AS avg_allowed
            FROM claims_lines WHERE {where}
            GROUP BY 1 ORDER BY lines DESC
            """,
            params,
        )
        by_code = [dict(r) for r in cur.fetchall()]

        cur.execute(
            f"""
            SELECT source_system, lob, market, count(*)::bigint AS lines,
                   COALESCE(SUM(allowed_amount),0)::float AS allowed
            FROM claims_lines WHERE {where}
            GROUP BY 1,2,3 ORDER BY lines DESC LIMIT 12
            """,
            params,
        )
        by_src = [dict(r) for r in cur.fetchall()]

        # Enrollment MM only for members appearing on selected claims.
        cur.execute(
            f"""
            WITH sel AS (
              SELECT DISTINCT member_id FROM claims_lines WHERE {where}
            )
            SELECT COALESCE(SUM(
                (
                    (e.enrollment_end_date - e.enrollment_start_date)
                    + CASE
                        WHEN e.segment LIKE 'GAP_DAYS:%%'
                        THEN CAST(split_part(e.segment, ':', 2) AS integer)
                        ELSE 0
                      END
                )::double precision
                / EXTRACT(DAY FROM (date_trunc('month', e.enrollment_month) + INTERVAL '1 month - 1 day'))
            ), 0)::float AS mm,
            count(DISTINCT e.member_id)::bigint AS enrolled_members
            FROM enrollment_records e
            JOIN sel ON sel.member_id = e.member_id
            WHERE e.tenant_id = %s
              AND e.enrollment_month >= %s
              AND e.enrollment_month <= %s
              AND e.enrollment_start_date IS NOT NULL
              AND e.enrollment_end_date IS NOT NULL
            """,
            params + [TENANT, date(2025, 1, 1), date(2025, 12, 1)],
        )
        elig = dict(cur.fetchone())
        elig_mm = float(elig["mm"] or 0)

        excluded: Dict[str, Any] = {}
        if codes:
            cur.execute(
                """
                SELECT count(*)::bigint AS lines_code_only,
                       COALESCE(SUM(allowed_amount),0)::float AS allowed_code_only
                FROM claims_lines
                WHERE tenant_id=%s AND service_date BETWEEN %s AND %s
                  AND (cpt_code = ANY(%s) OR hcpcs_code = ANY(%s))
                """,
                (TENANT, S, E, codes, codes),
            )
            code_only = dict(cur.fetchone())
            excluded = {
                "code_match_any_category": code_only,
                "excluded_by_service_category_filter": {
                    "lines": int(code_only["lines_code_only"]) - lines,
                    "allowed": float(code_only["allowed_code_only"]) - allowed,
                    "reason": "AND filter: codeset ∩ service_category",
                },
            }

        em_check = None
        if meta.get("policy_key") == "mri":
            cur.execute(
                """
                SELECT count(*)::bigint AS n FROM claims_lines
                WHERE tenant_id=%s AND service_date BETWEEN %s AND %s
                  AND (cpt_code IN ('99213','99214') OR hcpcs_code IN ('99213','99214'))
                  AND service_category = ANY(%s)
                """,
                (TENANT, S, E, services or ["mri"]),
            )
            em_check = {"em_in_selected_mri_population": int(cur.fetchone()["n"])}

        stored_mm = float(m.get("member_months") or 0)
        stored_pmpm = m.get("allowed_pmpm_target")
        stored_allowed = m.get("total_allowed")
        stored_claims = m.get("total_claims")

        pmpm_script = (allowed / script_mm) if script_mm else None
        pmpm_product = (allowed / float(product_mm["mm"])) if product_mm["mm"] else None
        pmpm_claimant = (allowed / claimant_mm) if claimant_mm else None
        pmpm_elig = (allowed / elig_mm) if elig_mm else None
        avg_line = (allowed / lines) if lines else None
        util_elig = ((lines / elig_mm) * 12.0 * 1000.0) if elig_mm else None

        scope_meta = meta.get("scope") or {}
        rem = meta.get("remediation") or {}

        rec = {
            "policy_id": b["policy_id"],
            "name": b["name"],
            "policy_key": meta.get("policy_key"),
            "baseline_id": b["baseline_id"],
            "configuration": {
                "codes": codes,
                "service_categories": services,
                "lob_in_current_scope": scope_meta.get("lob"),
                "markets_in_current_scope": scope_meta.get("markets"),
                "lob_used_in_stored_filters": lob,
                "markets_used_in_stored_filters": markets,
                "synthetic_scope_alignment": scope_meta.get("synthetic_scope_alignment"),
                "execution_eligibility": rem.get("execution_eligibility"),
                "register_status": rem.get("register_status"),
                "code_mapping_state": rem.get("code_mapping_state"),
                "mechanism": meta.get("mechanism"),
                "effective_period": meta.get("effective_period"),
            },
            "stored_baseline": {
                "total_claims": stored_claims,
                "unique_members": m.get("unique_members"),
                "member_months": stored_mm,
                "total_allowed": stored_allowed,
                "total_paid": m.get("total_paid"),
                "allowed_pmpm_target": stored_pmpm,
                "exposure_method": m.get("exposure_method"),
                "denominator_basis": m.get("denominator_basis"),
                "scope_resolution": m.get("scope_resolution"),
            },
            "independent": {
                "grain": "claim_line",
                "lines": lines,
                "headers": int(agg["headers"] or 0),
                "distinct_members_on_selected_claims": claimants,
                "units_sum": float(agg["units"] or 0),
                "total_allowed": money(allowed),
                "total_paid": money(paid),
                "avg_allowed_per_line": money(avg_line) if avg_line is not None else None,
                "p10_allowed_per_line": money(agg["p10"]),
                "p50_allowed_per_line": money(agg["p50"]),
                "p90_allowed_per_line": money(agg["p90"]),
                "neg_allowed_lines": int(agg["neg_allowed"] or 0),
                "zero_allowed_lines": int(agg["zero_allowed"] or 0),
                "source_mix": {
                    "lines_5k": int(agg["lines_5k"] or 0),
                    "lines_500k": int(agg["lines_500k"] or 0),
                    "members_5k": int(agg["members_5k"] or 0),
                    "members_500k": int(agg["members_500k"] or 0),
                    "population": (
                        "COMBINED"
                        if (agg["lines_5k"] and agg["lines_500k"])
                        else ("5K" if agg["lines_5k"] else ("500K" if agg["lines_500k"] else "UNKNOWN"))
                    ),
                },
                "denominators": {
                    "script_tenant_wide_mm": script_mm,
                    "product_enrollment_mm": float(product_mm["mm"]),
                    "claimant_times_12": claimant_mm,
                    "enrollment_mm_for_selected_claimants": elig_mm,
                    "enrolled_members_among_selected_claimants": int(elig["enrolled_members"] or 0),
                },
                "pmpm_variants": {
                    "using_script_tenant_wide_mm": pmpm_script,
                    "using_product_enrollment_mm": pmpm_product,
                    "using_claimant_x12": pmpm_claimant,
                    "using_selected_claimant_enrollment_mm": pmpm_elig,
                },
                "util_lines_per_1k_member_years_using_selected_claimant_mm": util_elig,
                "by_code": by_code,
                "by_source_lob_market": by_src,
                "exclusions": excluded,
                "em_check": em_check,
            },
            "reconciliation": {
                "claims_delta_indep_minus_stored": None
                if stored_claims is None
                else lines - int(stored_claims),
                "allowed_delta_indep_minus_stored": None
                if stored_allowed is None
                else allowed - float(stored_allowed),
                "numerator_match": stored_allowed is not None and abs(allowed - float(stored_allowed)) < 1.0,
                "claims_match": stored_claims is not None and lines == int(stored_claims),
                "stored_denominator_equals_script_tenant_mm": abs(stored_mm - script_mm) < 1.0,
                "stored_pmpm_reproducible_from_script_mm": (
                    stored_pmpm is not None
                    and pmpm_script is not None
                    and abs(float(stored_pmpm) - pmpm_script) < 0.01
                ),
            },
        }
        audit["policies"].append(rec)
        print(
            "%s lines=%s allowed=%s stored_pmpm=%s script_pmpm=%s elig_pmpm=%s claimant_pmpm=%s"
            % (
                (b["name"] or "")[:42],
                lines,
                money(allowed),
                stored_pmpm,
                None if pmpm_script is None else round(pmpm_script, 4),
                None if pmpm_elig is None else round(pmpm_elig, 4),
                None if pmpm_claimant is None else round(pmpm_claimant, 4),
            ),
            flush=True,
        )

    # Root-cause draft classifications (evidence-based; finalized in markdown).
    findings = []
    for p in audit["policies"]:
        stored = p["stored_baseline"]
        indep = p["independent"]
        recon = p["reconciliation"]
        primary = "EXPECTED_LOW_PMPM"
        notes = []
        if recon.get("stored_denominator_equals_script_tenant_mm") and indep["source_mix"]["population"] in {
            "COMBINED",
            "5K",
            "500K",
        }:
            # Narrow service numerator over whole-book denominator is expected to look "low".
            primary = "EXPECTED_LOW_PMPM"
            notes.append(
                "Allowed PMPM uses tenant-wide enrollment MM as denominator while numerator is "
                "policy-selected service spending only."
            )
        if p["configuration"].get("synthetic_scope_alignment") or (
            p["policy_key"] in {"ncd", "lcd"} and not p["configuration"].get("lob_used_in_stored_filters")
        ):
            notes.append(
                "NCD/LCD measurement used commercial/synthetic proxy after clearing MEDICARE/NC filters."
            )
            if primary == "EXPECTED_LOW_PMPM":
                # dual finding: keep primary on denominator semantics; flag config in notes
                pass
        if not recon.get("numerator_match"):
            primary = "INSUFFICIENT_EVIDENCE"
            notes.append("Independent allowed total did not match stored baseline.")
        # avg allowed sanity vs generator anchors
        avg = indep.get("avg_allowed_per_line")
        if avg is not None and avg <= 0:
            primary = "DATA_REALISM_ISSUE"
            notes.append("Non-positive average allowed on selected lines.")
        findings.append(
            {
                "policy_key": p["policy_key"],
                "name": p["name"],
                "primary_classification": primary,
                "notes": notes,
                "result": "PASS"
                if primary == "EXPECTED_LOW_PMPM" and recon.get("numerator_match")
                else ("REVIEW_REQUIRED" if primary != "CALCULATION_DEFECT" else "FAIL"),
            }
        )
    audit["preliminary_findings"] = findings

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(audit, indent=2, default=str))
    print("tenant_script_mm", script_mm)
    print("product_mm", product_mm)
    print("wrote", OUT)
    cur.close()
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
