"""Load the synthetic payer into the disposable local database and calculate.

Refuses any URL that is not 127.0.0.1:55434 and a synthetic_payer database.
"""

from __future__ import annotations

import json
import os
import resource
import sys
from pathlib import Path

URL_TEMPLATE = "postgresql+psycopg2://synthetic:synthetic@127.0.0.1:55434/{name}"


def main() -> None:
    import shutil

    lives = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
    database = sys.argv[2] if len(sys.argv) > 2 else "synthetic_payer"
    if lives >= 500_000 and database == "synthetic_payer":
        raise SystemExit("Refusing to overwrite the 10,000-life reference database")
    free_bytes = shutil.disk_usage("/").free
    if free_bytes < 20 * 1024 ** 3:
        raise SystemExit(f"Stopping: free disk {free_bytes} bytes is below the 20 GB limit")
    url = URL_TEMPLATE.format(name=database)
    os.environ["DATABASE_URL"] = url
    os.environ["PG_STATEMENT_TIMEOUT_MS"] = "600000"
    from uepi_api.services.synthetic_payer_integration import (
        assert_disposable_database,
        integrate_synthetic_payer,
    )

    assert_disposable_database(url)
    from sqlalchemy import create_engine, text

    if database != "synthetic_payer":
        admin = create_engine(URL_TEMPLATE.format(name="synthetic_payer"), isolation_level="AUTOCOMMIT")
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": database},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{database}"'))
        admin.dispose()

    from uepi_api.config import get_settings
    from uepi_api.database import SessionLocal, init_db
    import uepi_api.database as database_module

    get_settings.cache_clear()
    database_module._engine = None
    database_module._SessionLocal = None
    init_db()
    db = SessionLocal()
    try:
        db.execute(text("DROP SCHEMA public CASCADE"))
        db.execute(text("CREATE SCHEMA public"))
        db.commit()
    finally:
        db.close()
    init_db()
    db = SessionLocal()
    try:
        report = integrate_synthetic_payer(db, lives)
    finally:
        db.close()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    report["peak_rss_mb"] = round(usage.ru_maxrss / (1024 * 1024), 1)
    out = Path("data/synthetic") / f"integration_{lives}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps({k: report[k] for k in report if k != "realism"}, indent=2, default=str))
    print("realism", json.dumps(report["realism"], indent=2))
    print("wrote", out)


if __name__ == "__main__":
    main()
