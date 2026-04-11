#!/usr/bin/env python3
"""
Report row counts for canonical / source tables (PostgreSQL).

Uses DATABASE_URL. Optional DEMO_TENANT_ID (default: demo tenant UUID).

Exit code 0 always (informational). Use in setup-complete-azure-demo.sh footer.

  DATABASE_URL='postgresql+psycopg2://...' python3 scripts/check_canonical_source_data.py
"""
from __future__ import annotations

import os
import sys


DEFAULT_DEMO_TENANT = "00000000-0000-0000-0000-000000000001"

# Canonical fact tables + ingestion metadata (no separate "members" table).
TABLES: list[tuple[str, str | None]] = [
    ("claims_lines", "tenant_id"),
    ("enrollment_records", "tenant_id"),
    ("provider_records", "tenant_id"),
    ("ingestions", "tenant_id"),
    ("datasets", "tenant_id"),
]


def _table_exists(conn, table: str) -> bool:
    from sqlalchemy import text

    r = conn.execute(
        text(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = :t
            """
        ),
        {"t": table},
    )
    return r.first() is not None


def _column_exists(conn, table: str, column: str) -> bool:
    from sqlalchemy import text

    r = conn.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :t AND column_name = :c
            """
        ),
        {"t": table, "c": column},
    )
    return r.first() is not None


def main() -> int:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        print("DATABASE_URL is not set.", file=sys.stderr)
        return 1

    tenant = (os.environ.get("DEMO_TENANT_ID") or DEFAULT_DEMO_TENANT).strip()

    from sqlalchemy import create_engine, text

    engine = create_engine(url)

    print("")
    print("==========================================")
    print("Canonical / source data (PostgreSQL)")
    print("==========================================")
    print(f"Demo tenant filter: {tenant}")
    print("")
    print(f"{'Table':<24} {'Total':>12} {'Demo tenant':>14}  Notes")
    print("-" * 60)

    fact_tables = frozenset({"claims_lines", "enrollment_records", "provider_records"})
    demo_has_facts = False
    global_fact_rows = 0
    with engine.connect() as conn:
        for table, tenant_col in TABLES:
            if not _table_exists(conn, table):
                print(f"{table:<24} {'(missing)':>12} {'—':>14}  Table not in DB / not migrated")
                continue

            total = int(conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar() or 0)
            demo = "—"
            demo_n = 0
            if tenant_col and _column_exists(conn, table, tenant_col):
                demo_n = int(
                    conn.execute(
                        text(
                            f'SELECT COUNT(*) FROM "{table}" WHERE "{tenant_col}" = CAST(:tid AS uuid)'
                        ),
                        {"tid": tenant},
                    ).scalar()
                    or 0
                )
                demo = str(demo_n)
            if table in fact_tables:
                global_fact_rows += total
                if demo_n > 0:
                    demo_has_facts = True
            notes = {
                "claims_lines": "claim line facts",
                "enrollment_records": "coverage / eligibility by member-month",
                "provider_records": "provider dimension",
                "ingestions": "ingestion jobs",
                "datasets": "curated dataset slices",
            }
            note = notes.get(table, "")
            print(f"{table:<24} {total:>12} {demo:>14}  {note}")

    print("-" * 60)
    if not demo_has_facts:
        print(
            "No canonical rows detected for the demo tenant in claims_lines / "
            "enrollment_records / provider_records (or tables empty)."
        )
        print(
            "This is expected after setup-complete-azure-demo.sh alone — it seeds "
            "policies, pipelines, baselines, and demo observations, not bulk claims/CSV."
        )
        print(
            "Load files via product ingestion / pipelines or "
            "scripts/run_complete_product_flow.py (local synthetic data)."
        )
        if global_fact_rows > 0:
            print(
                f"Note: {global_fact_rows} total rows exist across fact tables but none for demo "
                f"tenant {tenant} (check tenant_id on ingestions)."
            )
    else:
        print(
            "Demo tenant has rows in at least one of: claims_lines, enrollment_records, "
            "provider_records."
        )
    print("==========================================")
    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
