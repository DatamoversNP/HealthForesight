#!/usr/bin/env python3
"""RETIRED as primary bulk path (2026-11-04).

Use:
  - run_claims_mechanism_preflight.py
  - policy_analytics_job_runner.py
  - Celery task uepi_worker.tasks.policy_analytics_lifecycle_job

See BULK_HTTP_RUNNER_RETIRED.md.
Interactive single-policy API endpoints remain for UI workflows.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "RETIRED: bulk HTTP lifecycle runner disabled.\n"
        "Use run_claims_mechanism_preflight.py and policy_analytics_job_runner.py.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
