"""File-based auth storage (minimal viable version - demo user) - database only"""
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.tenant import Tenant, User

# Default demo tenant ID
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
DEFAULT_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def ensure_demo_tenant_and_user():
    """Ensure demo tenant and user exist in database - Non-blocking with timeout"""
    from uepi_api.database import SessionLocal
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
    import signal
    
    def _ensure():
        db: Session = SessionLocal()
        try:
            tenant = db.query(Tenant).filter(Tenant.id == DEFAULT_TENANT_ID).first()
            if not tenant:
                tenant = Tenant(
                    id=DEFAULT_TENANT_ID,
                    name="Demo Tenant",
                    domain="demo",
                )
                db.add(tenant)
                db.flush()  # Flush to get tenant ID available for user
            
            user = db.query(User).filter(User.id == DEFAULT_USER_ID).first()
            if not user:
                user = User(
                    id=DEFAULT_USER_ID,
                    tenant_id=DEFAULT_TENANT_ID,
                    email="demo@example.com",
                    full_name="Demo User",
                )
                db.add(user)
            
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
