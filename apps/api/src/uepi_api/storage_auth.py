"""File-based auth storage (minimal viable version - demo user) - database only"""
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import insert, select
from uepi_api.models.tenant import Tenant, User, Role, user_roles

# Default demo tenant ID
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
DEFAULT_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

# Roles to seed and assign to demo user
DEFAULT_ROLES = [
    ("POLICY_ADMIN", "Policy administrator; full access to policies, users, analyses."),
    ("UM_LEADER", "Utilization management leader; create/read policies and analyses."),
    ("ACTUARIAL", "Actuarial; read policies, analyses, scorecards."),
    ("STRATEGY", "Strategy; read policies and analyses."),
    ("COMPLIANCE", "Compliance; read-only access."),
    ("EXEC_VIEWER", "Executive viewer; read-only dashboards."),
]


def ensure_roles_seeded(db: Session) -> None:
    """Ensure Role table has standard roles. Idempotent."""
    for name, description in DEFAULT_ROLES:
        if db.query(Role).filter(Role.name == name).first():
            continue
        db.add(Role(name=name, description=description))
    db.flush()


def ensure_demo_tenant_and_user():
    """Ensure demo tenant and user exist in database - Non-blocking with timeout"""
    from uepi_api.database import SessionLocal
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
    import signal
    
    def _ensure():
        db: Session = SessionLocal()
        try:
            ensure_roles_seeded(db)
            tenant = db.query(Tenant).filter(Tenant.id == DEFAULT_TENANT_ID).first()
            if not tenant:
                tenant = Tenant(
                    id=DEFAULT_TENANT_ID,
                    name="Demo Tenant",
                    domain="demo",
                )
                db.add(tenant)
                db.flush()
            user = db.query(User).filter(User.id == DEFAULT_USER_ID).first()
            if not user:
                user = User(
                    id=DEFAULT_USER_ID,
                    tenant_id=DEFAULT_TENANT_ID,
                    email="demo@example.com",
                    full_name="Demo User",
                    auth_source="local",
                )
                db.add(user)
                db.flush()
            # Assign POLICY_ADMIN and UM_LEADER to demo user if not already
            existing_roles = db.execute(
                select(user_roles.c.role).where(user_roles.c.user_id == DEFAULT_USER_ID)
            ).all()
            existing_role_names = {r[0] for r in existing_roles}
            for role_name in ("POLICY_ADMIN", "UM_LEADER"):
                if role_name not in existing_role_names:
                    db.execute(insert(user_roles).values(user_id=DEFAULT_USER_ID, role=role_name))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"ERROR ensure_demo_tenant_and_user (DB): {e}")
            raise  # Re-raise to allow caller to handle
        finally:
            db.close()
    
    # Run with 5 second timeout to prevent hanging
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(_ensure)
        future.result(timeout=5)
    except FutureTimeoutError:
        print("WARNING: ensure_demo_tenant_and_user timed out after 5 seconds - skipping")
        return  # Don't raise, just skip
    except Exception as e:
        print(f"WARNING: ensure_demo_tenant_and_user failed: {e} - continuing anyway")
        return  # Don't raise, just skip
    finally:
        executor.shutdown(wait=False)


def get_demo_user() -> Dict[str, Any]:
    """Get demo user (for local development) - from database"""
    ensure_demo_tenant_and_user()
    
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == DEFAULT_USER_ID).first()
        tenant = db.query(Tenant).filter(Tenant.id == DEFAULT_TENANT_ID).first()
        
        if not user or not tenant:
            return {
                "user_id": DEFAULT_USER_ID,
                "tenant_id": DEFAULT_TENANT_ID,
                "email": "demo@example.com",
                "name": "Demo User",
                "roles": ["admin"],
            }
        
        from uepi_api.storage_user_roles import get_user_roles
        user_roles = get_user_roles(DEFAULT_USER_ID)
        roles = [ur.role_id for ur in user_roles] if user_roles else ["admin"]
        
        return {
            "user_id": DEFAULT_USER_ID,
            "tenant_id": DEFAULT_TENANT_ID,
            "email": user.email or "demo@example.com",
            "name": user.full_name or "Demo User",
            "roles": roles,
        }
        
    except Exception as e:
        print(f"ERROR get_demo_user (DB): {e}")
        return {
            "user_id": DEFAULT_USER_ID,
            "tenant_id": DEFAULT_TENANT_ID,
            "email": "demo@example.com",
            "name": "Demo User",
            "roles": ["admin"],
        }
    finally:
        db.close()
