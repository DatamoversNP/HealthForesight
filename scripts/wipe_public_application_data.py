#!/usr/bin/env python3
"""
Remove all row data from public-schema application tables (PostgreSQL).

Keeps alembic_version so ``alembic upgrade head`` does not replay migrations
against existing tables. Skips PostGIS system tables if present.

Run only with --force or when env SETUP_COMPLETE_AZURE_DEMO_WIPE=1 (set by
setup-complete-azure-demo.sh).

  DATABASE_URL='postgresql://...' python3 scripts/wipe_public_application_data.py --force
"""
from __future__ import annotations

import os
import sys


def main() -> None:
    force = "--force" in sys.argv or "-f" in sys.argv
    if not force and os.environ.get("SETUP_COMPLETE_AZURE_DEMO_WIPE") != "1":
        print(
            "Refusing to wipe: run with --force, or use scripts/azure/setup-complete-azure-demo.sh",
            file=sys.stderr,
        )
        sys.exit(2)

    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        print("DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(1)

    from sqlalchemy import create_engine, text

    engine = create_engine(url)
    skip = {
        "alembic_version",
        "spatial_ref_sys",
        "geography_columns",
        "geometry_columns",
    }

    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
                """
            )
        ).fetchall()
        tables = [r[0] for r in rows if r[0] not in skip]

        if not tables:
            print("No public tables to truncate (run migrations first).")
            return

        # Single TRUNCATE lists all tables; CASCADE clears FK-linked rows.
        ident_list = ", ".join(f'"{t}"' for t in tables)
        sql = f"TRUNCATE {ident_list} RESTART IDENTITY CASCADE"
        conn.execute(text(sql))

    print(f"Wiped {len(tables)} public tables (alembic_version preserved).")


if __name__ == "__main__":
    main()
