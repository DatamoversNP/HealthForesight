"""Complete the local synthetic payment lifecycle on the disposable 500k database.

Refuses any URL that is not the local synthetic payer database. Does not deploy.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "apps/api/src"), str(ROOT / "packages/common/src")]

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://synthetic:synthetic@127.0.0.1:55434/synthetic_payer_500k",
)
os.environ["DATABASE_URL"] = DATABASE_URL


def main() -> None:
    from uepi_api.database import SessionLocal
    from uepi_api.services.synthetic_lifecycle import persist_synthetic_lifecycle
    from uepi_api.services.synthetic_payer_integration import assert_disposable_database
    from uepi_api.storage_auth import DEFAULT_TENANT_ID

    assert_disposable_database(DATABASE_URL)
    if "synthetic_payer_500k" not in DATABASE_URL:
        raise SystemExit("This lifecycle close-out runs only on the local synthetic_payer_500k database")
    db = SessionLocal()
    try:
        result = persist_synthetic_lifecycle(db, DEFAULT_TENANT_ID)
    finally:
        db.close()
    out = ROOT / "data" / "synthetic" / "lifecycle_500000.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
