#!/usr/bin/env python3
"""
Set all policies for a tenant to a single effective date (e.g. July 2025) so the demo
timeline is consistent: baseline = pre go-live, observations = post go-live.

  python3 scripts/set_demo_policy_effective_dates.py [--tenant-id ID] [--effective-date 2025-07-01]

Updates:
  - policy_versions.effective_start_date for every version of each policy
  - policy_metadata_json.effective_period.start_date (and end_date) for each policy

Run from repo root. Use before or as part of fresh demo so baselines use pre–July 2025
data and observations (July 2025–present) are post go-live.
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

DEFAULT_TENANT = "00000000-0000-0000-0000-000000000001"
DEFAULT_EFFECTIVE = "2025-07-01"


def main():
    parser = argparse.ArgumentParser(description="Set policy effective dates for demo timeline alignment")
    parser.add_argument("--tenant-id", default=DEFAULT_TENANT, help="Tenant UUID")
    parser.add_argument("--effective-date", default=DEFAULT_EFFECTIVE, help="Effective date YYYY-MM-DD (default: 2025-07-01)")
    args = parser.parse_args()

    tenant_id = UUID(args.tenant_id)
    effective_date = datetime.strptime(args.effective_date, "%Y-%m-%d")

    from uepi_api.database import SessionLocal
    from uepi_api.models.policy import Policy, PolicyVersion

    db = SessionLocal()
    try:
        policies = db.query(Policy).filter(Policy.tenant_id == tenant_id).all()
        if not policies:
            print(f"No policies found for tenant {tenant_id}. Nothing to update.")
            return 0

        # Update every policy version's effective_start_date
        versions_updated = 0
        for p in policies:
            for v in db.query(PolicyVersion).filter(
                PolicyVersion.tenant_id == tenant_id,
                PolicyVersion.policy_id == p.id,
            ).all():
                v.effective_start_date = effective_date
                versions_updated += 1

        # Update policy_metadata_json.effective_period for each policy
        from sqlalchemy.orm.attributes import flag_modified
        for p in policies:
            meta = dict(p.policy_metadata_json) if p.policy_metadata_json else {}
            if "effective_period" not in meta:
                meta["effective_period"] = {}
            ep = meta["effective_period"] if isinstance(meta["effective_period"], dict) else {}
            ep = dict(ep)
            ep["start_date"] = effective_date.date().isoformat()
            ep["end_date"] = None  # open-ended
            meta["effective_period"] = ep
            p.policy_metadata_json = meta
            flag_modified(p, "policy_metadata_json")

        db.commit()
        print(f"Updated {len(policies)} policies and {versions_updated} version(s) to effective date {args.effective_date}.")
        print("Baselines will use pre–go-live window; observations July 2025+ are post go-live.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}", file=sys.stderr)
        raise
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
