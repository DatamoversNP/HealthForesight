#!/usr/bin/env python3
"""
Delete all observations and run the daily job to generate observations with
cumulative periods (effective date → run date). When the job builds observations
from claims (no stored impact analysis), it applies per-policy metric variation
so verdicts naturally spread (ON_TRACK / AT_RISK / BACKFIRE) without hardcoding.

Usage:
  # Jan, Feb, then March 6 (delete all, then run for each date in order):
  python3 scripts/reset_observations_and_run_daily_jobs.py --dates 2026-01-31,2026-02-28,2026-03-06

  # Single run for a given date:
  python3 scripts/reset_observations_and_run_daily_jobs.py --runs 1 --base-date 2026-03-06

  # Three runs (base_date-2, base_date-1, base_date):
  python3 scripts/reset_observations_and_run_daily_jobs.py [--runs 3] [--base-date YYYY-MM-DD]

Requires API running at http://localhost:8000 (or set API_BASE_URL).
"""
import argparse
import os
import sys
import time

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_PREFIX = f"{API_BASE}/api/v1"


def delete_all_observations():
    """DELETE /observations/all (uses demo auth)."""
    r = requests.delete(f"{API_PREFIX}/observations/all", timeout=30)
    if r.status_code != 200:
        print(f"  Delete observations failed: {r.status_code} {r.text}")
        return False
    data = r.json()
    print(f"  Deleted {data.get('deleted', 0)} observations.")
    return True


def trigger_daily_job(target_date: str, run_observations: bool = True):
    """POST daily job; returns job_id or None."""
    r = requests.post(
        f"{API_PREFIX}/jobs/daily-data-and-observations",
        params={"run_observations": "true" if run_observations else "false", "target_date": target_date},
        timeout=10,
    )
    if r.status_code != 202:
        print(f"  Trigger job failed: {r.status_code} {r.text}")
        return None
    return r.json().get("job_id")


def get_job_status(job_id: str, timeout: int = 120):
    """GET job status; returns status string or None. Uses long timeout so a busy API can respond."""
    try:
        r = requests.get(f"{API_PREFIX}/jobs/daily-data-and-observations/status/{job_id}", timeout=timeout)
        if r.status_code != 200:
            return None
        return r.json().get("status")
    except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
        return None
    except requests.exceptions.RequestException:
        return None


def wait_for_job(job_id: str, poll_interval: int = 15, max_wait: int = 7200):
    """Poll until job completes or max_wait seconds. Retries on timeout so a busy API doesn't kill the script."""
    start = time.time()
    poll_count = 0
    while time.time() - start < max_wait:
        poll_count += 1
        status = get_job_status(job_id)
        if status in ("COMPLETED", "FAILED"):
            return status
        if status is None:
            print("   (status check timed out or failed; retrying in {}s...)".format(poll_interval))
        elif poll_count % 4 == 0:
            elapsed = int(time.time() - start)
            print("   Still running... ({}s elapsed, max wait {} min)".format(elapsed, max_wait // 60))
        time.sleep(poll_interval)
    return None


def main():
    parser = argparse.ArgumentParser(description="Delete observations and run daily job multiple times")
    parser.add_argument("--dates", type=str, default=None, help="Comma-separated target dates YYYY-MM-DD (e.g. 2026-01-31,2026-02-28,2026-03-06). If set, overrides --runs and --base-date.")
    parser.add_argument("--runs", type=int, default=3, help="Number of daily job runs (default 3); ignored if --dates is set")
    parser.add_argument("--base-date", type=str, default=None, help="Base date YYYY-MM-DD (default: today); ignored if --dates is set")
    parser.add_argument("--max-wait", type=int, default=7200, help="Max seconds to wait per job (default 7200 = 2 hours)")
    parser.add_argument("--dry-run", action="store_true", help="Only print what would be done")
    args = parser.parse_args()

    from datetime import date, timedelta

    if args.dates:
        run_dates_str = [d.strip() for d in args.dates.split(",") if d.strip()]
        for d in run_dates_str:
            try:
                date.fromisoformat(d)
            except ValueError:
                print(f"Invalid date in --dates: {d}")
                sys.exit(1)
        num_runs = len(run_dates_str)
    else:
        base = args.base_date
        if base:
            try:
                base_date = date.fromisoformat(base)
            except ValueError:
                print(f"Invalid --base-date: {base}")
                sys.exit(1)
        else:
            base_date = date.today()
        run_dates = [base_date - timedelta(days=(args.runs - 1 - i)) for i in range(args.runs)]
        run_dates_str = [d.isoformat() for d in run_dates]
        num_runs = args.runs

    print("Reset observations and run daily jobs")
    print("=" * 50)
    print(f"  API: {API_BASE}")
    print(f"  Runs: {num_runs}")
    print(f"  Target dates: {run_dates_str}")
    print(f"  Max wait per job: {args.max_wait}s ({args.max_wait // 60} min)")
    if args.dry_run:
        print("  [DRY RUN] Would delete all observations and trigger jobs for the above dates.")
        return

    print("\n1. Deleting all observations...")
    if not delete_all_observations():
        sys.exit(1)

    print("\n2. Running daily job for each target date...")
    for i, target_date in enumerate(run_dates_str, 1):
        print(f"   Run {i}/{num_runs}: target_date={target_date}")
        job_id = trigger_daily_job(target_date, run_observations=True)
        if not job_id:
            print("   Failed to trigger job.")
            sys.exit(1)
        print(f"   Job id: {job_id}; waiting for completion (up to {args.max_wait // 60} min)...")
        status = wait_for_job(job_id, max_wait=args.max_wait)
        if status == "COMPLETED":
            print(f"   Completed.")
        elif status == "FAILED":
            print("   Job failed. Check API logs.")
            sys.exit(1)
        else:
            print("   Timeout waiting for job.")
            sys.exit(1)

    print("\nDone. Open Observation Analysis to see Run History and timeline (filter by policy for trend).")


if __name__ == "__main__":
    main()
