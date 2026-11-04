#!/usr/bin/env python3
"""One-off: apply Phase A performance indexes on Azure Postgres (CONCURRENTLY)."""
import sys
from pathlib import Path

url_file = Path("/tmp/hf_db_url.txt")
if not url_file.exists():
    print("Missing /tmp/hf_db_url.txt", file=sys.stderr)
    sys.exit(1)

try:
    import psycopg2
except ImportError:
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "-q", "psycopg2-binary"])
    import psycopg2

url = url_file.read_text().strip()
if "sslmode=" not in url:
    url += ("&" if "?" in url else "?") + "sslmode=require"

print("connecting...")
conn = psycopg2.connect(url)
conn.autocommit = True
cur = conn.cursor()


def index_exists(name: str) -> bool:
    cur.execute("SELECT 1 FROM pg_indexes WHERE indexname=%s", (name,))
    return cur.fetchone() is not None


stmts = [
    (
        "ix_claims_lines_tenant_service_date",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_claims_lines_tenant_service_date "
        "ON claims_lines (tenant_id, service_date)",
    ),
    (
        "ix_observations_tenant_policy_period_end",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_observations_tenant_policy_period_end "
        "ON observations (tenant_id, policy_id, observation_period_end DESC, computed_at DESC)",
    ),
]

for name, sql in stmts:
    if index_exists(name):
        print(f"OK exists: {name}")
        continue
    print(f"Creating {name}...")
    cur.execute(sql)
    print(f"OK created: {name}")

cur.execute("SELECT to_regclass('public.alembic_version')")
if cur.fetchone()[0]:
    cur.execute("SELECT version_num FROM alembic_version")
    vers = [r[0] for r in cur.fetchall()]
    print("alembic_version:", vers)
    cur.execute(
        "SELECT 1 FROM alembic_version WHERE version_num=%s",
        ("011_perf_claims_obs_indexes",),
    )
    if cur.fetchone():
        print("Already stamped 011")
    elif len(vers) == 1 and str(vers[0]).startswith("010"):
        cur.execute(
            "UPDATE alembic_version SET version_num=%s",
            ("011_perf_claims_obs_indexes",),
        )
        print("Stamped 011")
    elif not vers:
        cur.execute(
            "INSERT INTO alembic_version(version_num) VALUES (%s)",
            ("011_perf_claims_obs_indexes",),
        )
        print("Stamped 011 insert")
    else:
        print("Left stamp unchanged")

cur.close()
conn.close()
print("DONE")
