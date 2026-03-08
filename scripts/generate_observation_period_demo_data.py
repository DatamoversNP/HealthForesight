#!/usr/bin/env python3
"""
Phase 5: Generate observation-period source data (July 2025 – present) for the same 1000 members.

Uses the same generator as Phase 2 so member IDs match (MEM_000000 … MEM_000999). Output goes to
observation_period/ so it can be loaded after historical data without overwriting.

Run from repo root:
  python3 scripts/generate_observation_period_demo_data.py [--end YYYY-MM-DD]
Then load with: python3 scripts/load_fresh_demo_historical.py --input-dir data/source_data/<tenant>/observation_period
"""
import argparse
import sys
from pathlib import Path
from datetime import date, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Run Phase 2 generator with observation-period defaults
SCRIPT = PROJECT_ROOT / "scripts" / "generate_24mo_historical_demo_data.py"


def main():
    parser = argparse.ArgumentParser(description="Generate observation-period demo data (July 2025 - present)")
    parser.add_argument("--tenant-id", type=str, default="00000000-0000-0000-0000-000000000001")
    parser.add_argument("--end", type=str, default=None, help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--members", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    end = date.fromisoformat(args.end) if args.end else date.today()
    start = date(2025, 7, 1)
    if end < start:
        print("End date is before 2025-07-01; using 2025-07-01 as end.")
        end = start
    output_dir = PROJECT_ROOT / "data" / "source_data" / args.tenant_id / "observation_period"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Invoke Phase 2 script with observation-period range and output dir
    argv = [
        sys.executable,
        str(SCRIPT),
        "--start", start.isoformat(),
        "--end", end.isoformat(),
        "--output-dir", str(output_dir),
        "--tenant-id", args.tenant_id,
        "--members", str(args.members),
        "--seed", str(args.seed),
    ]
    print("=" * 60)
    print("PHASE 5: Generate observation-period demo data")
    print("=" * 60)
    print(f"Start: {start}, End: {end}, Members: {args.members}")
    print(f"Output: {output_dir}")
    print("Calling generate_24mo_historical_demo_data.py ...")
    print()

    import subprocess
    r = subprocess.run(argv)
    if r.returncode != 0:
        sys.exit(r.returncode)
    print()
    print("Phase 5 complete. Load with: python3 scripts/load_fresh_demo_historical.py --input-dir " + str(output_dir))


if __name__ == "__main__":
    main()
