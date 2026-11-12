#!/usr/bin/env python3
"""
Generate the additive 5k nine-policy book and load operational rows into lean staging.

- Does NOT delete SYNTHETIC_LONGITUDINAL_V1 (500k) rows
- Writes entity pack under data/synthetic/nine_policy_5k/
- Inserts claims_lines + enrollment_records under SYNTHETIC_NINE_POLICY_5K_V1
- Refuses non-lean-staging databases
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import UUID, uuid4

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "packages" / "common" / "src"))
sys.path.insert(0, str(REPO / "apps" / "api" / "src"))

from uepi_common.synthetic_payer.nine_policy_5k import (  # noqa: E402
    SOURCE_SYSTEM,
    generate_book,
    write_entity_pack,
)

TENANT = UUID("00000000-0000-0000-0000-000000000001")
LONGITUDINAL = "SYNTHETIC_LONGITUDINAL_V1"
OUT_DIR = REPO / "data" / "synthetic" / "nine_policy_5k"
REPORT = (
    REPO
    / "docs"
    / "production"
    / "releases"
    / "corrections"
    / "nine_mock_policies"
    / "NINE_POLICY_5K_POPULATION_REPORT.json"
)


def _assert_lean(url: str) -> None:
    low = (url or "").lower()
    if "hfleanstg" not in low:
        raise SystemExit("Refusing: DATABASE_URL is not lean staging.")
    if "healthforesight-pg" in low and "hfleanstg" not in low:
        raise SystemExit("Refusing: looks like demo/production DB.")


def _source_counts(cur) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    for table in ("claims_lines", "enrollment_records"):
        cur.execute(f"SELECT source_system, count(*) FROM {table} GROUP BY 1")
        out[table] = {row[0]: int(row[1]) for row in cur.fetchall()}
    return out


def main() -> int:
    url = os.environ.get("DATABASE_URL") or ""
    _assert_lean(url)

    print("Generating 5k book...")
    book = generate_book()
    counts = write_entity_pack(book, OUT_DIR)
    print(json.dumps({"entity_counts": counts}, indent=2))

    import psycopg2
    from psycopg2.extras import execute_batch

    conn = psycopg2.connect(url.replace("postgresql+psycopg2://", "postgresql://", 1))
    conn.autocommit = False
    cur = conn.cursor()
    try:
        cur.execute("SELECT current_database()")
        dbname = cur.fetchone()[0]
        if dbname != "hfleanstg":
            raise SystemExit(f"Refusing unexpected database: {dbname}")

        before = _source_counts(cur)
        long_claims_before = before.get("claims_lines", {}).get(LONGITUDINAL, 0)
        long_enroll_before = before.get("enrollment_records", {}).get(LONGITUDINAL, 0)
        if long_claims_before <= 0 or long_enroll_before <= 0:
            raise SystemExit("Expected existing longitudinal 500k rows; aborting additive load.")

        # Idempotent: remove prior 5k book only (never longitudinal).
        # Also clear any partial failed inserts from a previous attempt.
        cur.execute("DELETE FROM claims_lines WHERE source_system = %s OR member_id LIKE 'N5K_%%'", (SOURCE_SYSTEM,))
        deleted_claims = cur.rowcount
        cur.execute(
            "DELETE FROM enrollment_records WHERE source_system = %s OR member_id LIKE 'N5K_%%'",
            (SOURCE_SYSTEM,),
        )
        deleted_enroll = cur.rowcount
        print(json.dumps({"cleared_prior_5k": {"claims": deleted_claims, "enrollment": deleted_enroll}}))
        # Re-check longitudinal after cleanup
        mid = _source_counts(cur)
        if mid.get("claims_lines", {}).get(LONGITUDINAL, 0) != long_claims_before:
            raise SystemExit("Cleanup changed longitudinal claims — abort")
        if mid.get("enrollment_records", {}).get(LONGITUDINAL, 0) != long_enroll_before:
            raise SystemExit("Cleanup changed longitudinal enrollment — abort")

        ingestion_id = book["meta"]["ingestion_id"]
        source_file = f"nine-policy-5k-{book['meta']['seed']}"

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
        for line in book["operational"]["claims_lines"]:
            claim_rows.append(
                (
                    str(uuid4()),
                    str(TENANT),
                    line["claim_id"],
                    line["claim_line_id"],
                    line["member_id"],
                    line["provider_id"],
                    line["service_date"],
                    line.get("paid_date"),
                    line.get("adjudication_date"),
                    line.get("lob") or "COMMERCIAL",
                    line.get("market") or "SYNTHETIC",
                    line.get("cpt_code"),
                    line.get("hcpcs_code"),
                    line.get("service_category"),
                    line.get("place_of_service"),
                    line.get("units") or 1,
                    line.get("allowed_amount") or 0,
                    line.get("paid_amount") or 0,
                    line.get("member_cost_share") or 0,
                    bool(line.get("in_network", True)),
                    bool(line.get("requires_prior_auth", False)),
                    line.get("prior_auth_approved"),
                    line.get("facility_type"),
                    SOURCE_SYSTEM,
                    source_file,
                    ingestion_id,
                    line.get("record_hash"),
                )
            )
        print(f"Inserting {len(claim_rows)} claim lines...")
        for offset in range(0, len(claim_rows), 2000):
            execute_batch(cur, claim_sql, claim_rows[offset : offset + 2000], page_size=500)
            print(f"  claims {min(offset + 2000, len(claim_rows))}/{len(claim_rows)}")

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
        for row in book["operational"]["enrollment_records"]:
            enroll_rows.append(
                (
                    str(uuid4()),
                    str(TENANT),
                    row["member_id"],
                    row["enrollment_month"],
                    row["lob"],
                    row["market"],
                    row["age_band"],
                    row["gender"],
                    row.get("risk_score") or 0,
                    row["network_tier"],
                    True,
                    row["enrollment_start_date"],
                    row["enrollment_end_date"],
                    row.get("product_type"),
                    row.get("segment"),
                    SOURCE_SYSTEM,
                    source_file,
                    ingestion_id,
                    row.get("record_hash"),
                )
            )
        print(f"Inserting {len(enroll_rows)} enrollment rows...")
        for offset in range(0, len(enroll_rows), 2000):
            execute_batch(cur, enroll_sql, enroll_rows[offset : offset + 2000], page_size=500)
            print(f"  enrollment {min(offset + 2000, len(enroll_rows))}/{len(enroll_rows)}")

        after = _source_counts(cur)
        long_claims_after = after.get("claims_lines", {}).get(LONGITUDINAL, 0)
        long_enroll_after = after.get("enrollment_records", {}).get(LONGITUDINAL, 0)
        if long_claims_after != long_claims_before or long_enroll_after != long_enroll_before:
            raise SystemExit(
                json.dumps(
                    {
                        "longitudinal_changed": True,
                        "claims": [long_claims_before, long_claims_after],
                        "enrollment": [long_enroll_before, long_enroll_after],
                    },
                    indent=2,
                )
            )

        new_claims = after.get("claims_lines", {}).get(SOURCE_SYSTEM, 0)
        new_enroll = after.get("enrollment_records", {}).get(SOURCE_SYSTEM, 0)
        if new_claims != len(claim_rows) or new_enroll != len(enroll_rows):
            raise SystemExit(
                f"Insert count mismatch claims {new_claims}/{len(claim_rows)} enroll {new_enroll}/{len(enroll_rows)}"
            )

        # Policy count must remain 9
        cur.execute("SELECT count(*) FROM policies")
        policy_count = int(cur.fetchone()[0])

        conn.commit()

        report: Dict[str, Any] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "database": dbname,
            "source_system": SOURCE_SYSTEM,
            "meta": book["meta"],
            "entity_file_counts": counts,
            "entity_pack_dir": str(OUT_DIR),
            "longitudinal_preserved": {
                "claims_lines": long_claims_after,
                "enrollment_records": long_enroll_after,
            },
            "additive_loaded": {
                "claims_lines": new_claims,
                "enrollment_records": new_enroll,
                "distinct_members_claims": len({r["member_id"] for r in book["operational"]["claims_lines"]}),
                "distinct_members_enrollment": len({r["member_id"] for r in book["operational"]["enrollment_records"]}),
            },
            "periods": {
                "baseline": book["meta"]["baseline_window"],
                "observation": book["meta"]["observation_window"],
            },
            "policy_definitions_unchanged_count": policy_count,
            "claims_by_policy_key": {},
            "success": True,
            "note": (
                "Additive 5k full target-model book loaded. "
                "500k longitudinal source_system counts unchanged. "
                "No baselines/observations generated in this step."
            ),
        }
        from collections import Counter

        report["claims_by_policy_key"] = dict(
            Counter(r.get("policy_key") for r in book["operational"]["claims_lines"])
        )
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({k: report[k] for k in report if k not in {"meta"}}, indent=2))
        print(f"report={REPORT}")
        return 0
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
