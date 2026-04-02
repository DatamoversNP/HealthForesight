#!/usr/bin/env python3
"""
Seed admin and sample users with password Swan@1234 and assign roles.
Run from repo root with DATABASE_URL set (or .env in apps/api):
  PYTHONPATH=apps/api/src:packages/common/src python3 scripts/seed_users.py
Or from apps/api:
  PYTHONPATH=src:../../packages/common/src python3 ../../scripts/seed_users.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import uuid4

# Ensure we can import uepi_api (run from repo root or apps/api)
REPO_ROOT = Path(__file__).resolve().parent.parent
API_SRC = REPO_ROOT / "apps" / "api" / "src"
COMMON_SRC = REPO_ROOT / "packages" / "common" / "src"
for p in (str(API_SRC), str(COMMON_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Unset env vars that pydantic-settings would JSON-parse and fail on (e.g. CORS_ORIGINS="http://...")
os.environ.pop("CORS_ORIGINS", None)

# Optional: load .env from apps/api (skip vars that break pydantic list parsing when run from CLI)
_env = REPO_ROOT / "apps" / "api" / ".env"
if _env.exists():
    with open(_env) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                # Avoid CORS_ORIGINS etc. as plain string so pydantic_settings doesn't JSON-parse and fail
                if k in ("CORS_ORIGINS",):
                    continue
                os.environ.setdefault(k, v.strip().replace('"', "").replace("'", ""))

from sqlalchemy import select, insert, delete
from uepi_api.database import SessionLocal
from uepi_api.models.tenant import Tenant, User, Role, user_roles
from uepi_api.storage_auth import DEFAULT_TENANT_ID, DEFAULT_USER_ID, ensure_roles_seeded
from uepi_api.password_utils import hash_password

# Detect placeholder URL (literal "host" / "dbname") and exit with a clear message
_db_url = os.environ.get("DATABASE_URL", "")
if "@host:" in _db_url or "@host/" in _db_url:
    print("ERROR: DATABASE_URL contains placeholder 'host'. Use your real database host.")
    print("Example (Azure): postgresql://USER:PASSWORD@YOUR-SERVER.postgres.database.azure.com:5432/yourdb?sslmode=require")
    print("Example (local): postgresql://postgres:postgres@localhost:5432/uepi_db")
    sys.exit(1)

SEED_PASSWORD = "Swan@1234"

# Email, full name, list of role names (all get password Swan@1234)
USERS_TO_SEED = [
    ("demo@example.com", "Demo User", ["POLICY_ADMIN", "UM_LEADER"]),
    ("admin@healthforesight.com", "Admin User", ["POLICY_ADMIN"]),
    ("sarah.analyst@healthforesight.com", "Sarah Analyst", ["ACTUARIAL"]),
    ("mike.leader@healthforesight.com", "Mike UM Leader", ["UM_LEADER"]),
    ("jane.exec@healthforesight.com", "Jane Executive", ["EXEC_VIEWER"]),
    ("david.compliance@healthforesight.com", "David Compliance", ["COMPLIANCE"]),
]


def ensure_tenant(db) -> None:
    tenant = db.query(Tenant).filter(Tenant.id == DEFAULT_TENANT_ID).first()
    if not tenant:
        tenant = Tenant(
            id=DEFAULT_TENANT_ID,
            name="Demo Tenant",
            domain="demo",
        )
        db.add(tenant)
        db.flush()


def seed_users() -> None:
    db = SessionLocal()
    try:
        ensure_roles_seeded(db)
        ensure_tenant(db)
        password_hash = hash_password(SEED_PASSWORD)
        created = 0
        for email, full_name, role_names in USERS_TO_SEED:
            existing = db.query(User).filter(
                User.email == email.strip(),
                User.tenant_id == DEFAULT_TENANT_ID,
            ).first()
            if existing:
                # Update password and roles so re-run is safe
                existing.password_hash = password_hash
                existing.auth_source = "local"
                existing.full_name = full_name
                existing.is_active = "true"
                db.flush()
                db.execute(delete(user_roles).where(user_roles.c.user_id == existing.id))
                user_id = existing.id
            else:
                # Use fixed ID for demo user so it matches app default
                user_id = DEFAULT_USER_ID if email.strip().lower() == "demo@example.com" else uuid4()
                user = User(
                    id=user_id,
                    tenant_id=DEFAULT_TENANT_ID,
                    email=email.strip(),
                    full_name=full_name,
                    is_active="true",
                    auth_source="local",
                    password_hash=password_hash,
                )
                db.add(user)
                db.flush()
                created += 1

            # Assign roles (role must exist in Role table)
            for rn in role_names:
                role = db.query(Role).filter(Role.name == rn).first()
                if role:
                    exists = db.execute(
                        select(user_roles.c.role).where(
                            user_roles.c.user_id == user_id,
                            user_roles.c.role == rn,
                        )
                    ).first()
                    if not exists:
                        db.execute(insert(user_roles).values(user_id=user_id, role=rn))
        db.commit()
        print(f"Seeded {len(USERS_TO_SEED)} users ({created} new). Password for all: {SEED_PASSWORD}")
        for email, full_name, roles in USERS_TO_SEED:
            print(f"  - {email} ({full_name}): {', '.join(roles)}")
    except Exception as e:
        db.rollback()
        raise SystemExit(f"Seed failed: {e}") from e
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
