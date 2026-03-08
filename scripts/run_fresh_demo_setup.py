#!/usr/bin/env python3
"""
Fresh demo script: one command to set up a full demo from scratch.

  python3 scripts/run_fresh_demo_setup.py

Runs all 7 phases in order (1, 1b, 2, 3, 4, 5, 6, 7). Historical data is 2022-01-01
to 2025-06-30 so policy baseline windows fall inside the data range. Data coverage is
~3x (1.5–3 claims per member per month); policies drive LOB/market/CPT so baselines
find relevant claims.

Options:
  --phase N       Run only phase N (1, 1b, 2, 3, 4, 5, 6, 7)
  --tenant-id ID  Tenant UUID (default: demo tenant)
  --dry-run       Phase 1 only, no deletes

Phases (all run in sequence when no --phase is given):
  1   Clean: remove all demo raw + derived data
  1b  Migrations: analytics_runs, baselines.analytics_run_id (run from apps/api)
  2   Generate historical CSVs (2022-01 to 2025-06, policy-aligned, ~3x claims)
  3   Load historical CSVs into DB
  3b  Set policy effective dates to July 2025 (so baseline = pre go-live, observations = post go-live)
  4   General baseline, policy baselines, predicted impact
  5   Generate observation-period CSVs (July 2025–present)
  6   Load observation-period (skip providers)
  7   Create observations per policy per month
"""
import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"
TENANT_ID = "00000000-0000-0000-0000-000000000001"
HISTORICAL_DIR = PROJECT_ROOT / "data" / "source_data" / TENANT_ID / "historical"
OBS_PERIOD_DIR = PROJECT_ROOT / "data" / "source_data" / TENANT_ID / "observation_period"


def run(cmd: list, phase_name: str, cwd: Path = None) -> bool:
    print()
    print("=" * 60)
    print(phase_name)
    print("=" * 60)
    r = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT)
    if r.returncode != 0:
        print(f"Failed: {phase_name}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Run fresh demo setup (all phases or a single phase)")
    parser.add_argument("--phase", default=None, help="Run only this phase (1, 1b, 2, 3, 3b, 4, 5, 6, 7)")
    parser.add_argument("--tenant-id", type=str, default=TENANT_ID)
    parser.add_argument("--dry-run", action="store_true", help="Phase 1 only, with --dry-run (no deletes)")
    args = parser.parse_args()
    py = sys.executable
    tenant = args.tenant_id

    if args.dry_run:
        if not run([py, str(SCRIPTS / "fresh_demo_clean.py"), "--tenant-id", tenant, "--dry-run"], "Phase 1 (dry-run)"):
            sys.exit(1)
        print("\nDry-run done. Run without --dry-run to execute full setup.")
        return

    api_dir = PROJECT_ROOT / "apps" / "api"
    phase_list = [
        (1, [py, str(SCRIPTS / "fresh_demo_clean.py"), "--tenant-id", tenant], "Phase 1: Clean", None),
        ("1b", [py, str(SCRIPTS / "run_migrations_fresh_demo.py")], "Phase 1b: Run DB migrations (analytics_runs, baselines.analytics_run_id)", api_dir),
        (2, [py, str(SCRIPTS / "generate_24mo_historical_demo_data.py"), "--tenant-id", tenant, "--output-dir", str(HISTORICAL_DIR)], "Phase 2: Generate historical data", None),
        (3, [py, str(SCRIPTS / "load_fresh_demo_historical.py"), "--tenant-id", tenant, "--input-dir", str(HISTORICAL_DIR)], "Phase 3: Load historical", None),
        ("3b", [py, str(SCRIPTS / "set_demo_policy_effective_dates.py"), "--tenant-id", tenant, "--effective-date", "2025-07-01"], "Phase 3b: Set policy effective dates to July 2025", None),
        (4, [py, str(SCRIPTS / "run_baseline_and_predicted_impact.py"), "--tenant-id", tenant], "Phase 4: Baseline + predicted impact", None),
        (5, [py, str(SCRIPTS / "generate_observation_period_demo_data.py"), "--tenant-id", tenant], "Phase 5: Generate observation-period data", None),
        (6, [py, str(SCRIPTS / "load_fresh_demo_historical.py"), "--tenant-id", tenant, "--input-dir", str(OBS_PERIOD_DIR), "--skip-providers"], "Phase 6: Load observation-period", None),
        (7, [py, str(SCRIPTS / "create_observations_per_month.py"), "--tenant-id", tenant], "Phase 7: Observations per month", None),
    ]

    to_run = phase_list
    if args.phase is not None:
        to_run = [t for t in phase_list if str(t[0]) == str(args.phase)]
        if not to_run:
            print(f"Unknown phase {args.phase}. Use 1, 1b, 2, 3, 3b, 4, 5, 6, 7.")
            sys.exit(1)

    ran = []
    for item in to_run:
        num, cmd, label = item[0], item[1], item[2]
        cwd = item[3] if len(item) > 3 else None
        if not run(cmd, label, cwd=cwd):
            sys.exit(1)
        ran.append(str(num))

    print()
    print("=" * 60)
    print("Fresh demo setup complete.")
    if ran:
        print("Phases run: " + ", ".join(ran))
    print("Refresh dashboards and Policy Verdicts in the UI.")
    print("=" * 60)


if __name__ == "__main__":
    main()
