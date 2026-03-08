#!/usr/bin/env python3
"""
Phase 1b: Ensure DB is at a known revision then run alembic upgrade head.

If the DB has a revision from another codebase (e.g. 012_create_jobs) that doesn't
exist in this repo, we set alembic_version directly via SQL to 004_elasticity_results,
then run upgrade head so 005 runs (creates analytics_runs, baselines.analytics_run_id).

Invoke with cwd=apps/api (the master script does this).
"""
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

# When run by run_fresh_demo_setup.py, cwd is apps/api
API_DIR = Path(os.getcwd())
if not (API_DIR / "alembic.ini").exists():
    API_DIR = PROJECT_ROOT / "apps" / "api"
os.chdir(API_DIR)

py = sys.executable

# Revisions in this repo (001 -> 005)
KNOWN_HEAD = "005_analytics_runs_verdict"
STAMP_REVISION = "004_elasticity_results"


def set_alembic_version_direct(revision: str) -> bool:
    """Set alembic_version table directly so alembic can run. Returns True on success."""
    from sqlalchemy import text
    from uepi_api.database import engine
    try:
        with engine.begin() as conn:
            # Force one row so alembic can run (handles unknown revision e.g. 012_create_jobs)
            conn.execute(text("DELETE FROM alembic_version"))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:rev)"), {"rev": revision})
        return True
    except Exception as e:
        print(f"Failed to set alembic_version to {revision}: {e}", file=sys.stderr)
        return False


def main():
    # 1. Try normal upgrade
    r = subprocess.run(
        [py, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        cwd=API_DIR,
    )
    if r.returncode == 0:
        print("Migrations applied successfully (alembic upgrade head).")
        return 0

    out = (r.stdout or "") + (r.stderr or "")
    if "Can't locate revision" not in out and "can't locate revision" not in out.lower():
        if r.stderr:
            print(r.stderr, file=sys.stderr)
        if r.stdout:
            print(r.stdout)
        return r.returncode

    # 2. DB has unknown revision (e.g. 012_create_jobs). Set version directly then upgrade.
    print("Database has a revision from another codebase; setting alembic_version to", STAMP_REVISION, "then upgrading.")
    if not set_alembic_version_direct(STAMP_REVISION):
        return 1
    r2 = subprocess.run(
        [py, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        cwd=API_DIR,
    )
    if r2.returncode == 0:
        print("Migrations applied successfully after re-stamp.")
    return r2.returncode


if __name__ == "__main__":
    sys.exit(main())
