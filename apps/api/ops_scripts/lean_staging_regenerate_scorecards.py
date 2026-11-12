#!/usr/bin/env python3
"""Regenerate lean-staging scorecards from predicted impacts (null-safe / UNESTIMATED).

Refuses non-hfleanstg databases.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "docs/production/releases/corrections/reviewed_248/SCORECARD_REGEN_REPORT.json"
TENANT = UUID("00000000-0000-0000-0000-000000000001")
PERIOD = "2026-Q4"


def _db_url() -> str:
    env = os.environ.get("DATABASE_URL") or os.environ.get("LEAN_STAGING_DATABASE_URL")
    if env:
        url = env.replace("postgresql+psycopg2://", "postgresql://", 1)
        if "hfleanstg" not in url.lower():
            raise SystemExit("Refusing: DATABASE_URL is not lean staging")
        return url
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
        raise SystemExit("Refusing: not lean staging")
    return url


def main() -> int:
    os.environ["DATABASE_URL"] = _db_url()
    sys.path.insert(0, str(REPO / "apps/api/src"))

    from uepi_api.storage_policies import list_policies
    from uepi_api.storage_policy_predicted_impact import get_predicted_impact
    from uepi_api.storage_scorecards import generate_scorecard_from_predicted_impact, save_scorecard

    policies = list_policies(TENANT)
    generated = 0
    skipped_no_pi = 0
    unavailable = 0
    available = 0
    errors: list[dict] = []

    for policy in policies:
        pid = policy.get("id") or policy.get("policy_id")
        if not pid:
            continue
        try:
            pi = get_predicted_impact(pid, TENANT)
            if not pi:
                skipped_no_pi += 1
                continue
            card = generate_scorecard_from_predicted_impact(pid, pi, period=PERIOD)
            card["policy_id"] = str(pid)
            save_scorecard(card, TENANT)
            generated += 1
            if card.get("effectiveness_index") is None:
                unavailable += 1
            else:
                available += 1
        except Exception as exc:  # noqa: BLE001 — continue book-wide regen
            errors.append({"policy_id": str(pid), "error": str(exc)})

    report = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "period": PERIOD,
        "policies_seen": len(policies),
        "generated": generated,
        "available_index": available,
        "unavailable_index": unavailable,
        "skipped_no_predicted_impact": skipped_no_pi,
        "errors": errors[:20],
        "error_count": len(errors),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"Wrote {OUT}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
