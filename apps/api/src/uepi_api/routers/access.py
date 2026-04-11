"""Access management endpoints (RBAC, Permissions, User Management)"""
import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from uepi_api.auth import CurrentUser, verify_token, require_role
from uepi_api.database import get_db
from uepi_api.models.tenant import Role, User
from uepi_common.models import TenantRole

router = APIRouter()
logger = logging.getLogger(__name__)


class RoleCreate(BaseModel):
    """Role creation model"""
    name: str
    description: str | None = None


class UserCreate(BaseModel):
    """User creation model. For local users, optionally set password; for AD users, create with same email and they sign in via SSO."""
    email: str
    full_name: str | None = None
    role_names: list[str] = []
    password: str | None = None  # Optional; if set, user is local (email/password), else local without password until set


class UserUpdate(BaseModel):
    """User update model (partial). password: set new password for local users only."""
    full_name: str | None = None
    is_active: str | None = None
    role_names: list[str] | None = None
    password: str | None = None  # New password for local users; ignored for OIDC users


class UserResponse(BaseModel):
    """User response model"""
    id: UUID
    tenant_id: UUID
    email: str
    full_name: str | None
    is_active: str
    auth_source: str | None  # "oidc" (e.g. Azure AD) or "local"
    role_names: list[str]
    created_at: str | None

    class Config:
        from_attributes = True


class RoleResponse(BaseModel):
    """Role response model"""
    id: UUID
    name: str
    description: str | None
    created_at: str
    
    class Config:
        from_attributes = True


class PermissionResponse(BaseModel):
    """Permission response model"""
    resource: str
    actions: list[str]


class UserRoleAssignment(BaseModel):
    """User role assignment model"""
    user_id: UUID
    role_names: list[str]


# Define permissions per role
ROLE_PERMISSIONS = {
    "POLICY_ADMIN": {
        "policies": ["create", "read", "update", "delete"],
        "users": ["create", "read", "update", "delete"],
        "tenants": ["read", "update"],
        "analyses": ["create", "read", "update", "delete"],
        "exports": ["create", "read", "delete"],
        "decisions": ["create", "read", "update", "delete"],
        "scorecards": ["read"],
        "cohorts": ["create", "read", "update", "delete"],
    },
    "UM_LEADER": {
        "policies": ["create", "read", "update"],
        "analyses": ["create", "read"],
        "exports": ["create", "read"],
        "decisions": ["create", "read", "update"],
        "scorecards": ["read"],
        "cohorts": ["create", "read", "update"],
    },
    "ACTUARIAL": {
        "policies": ["read"],
        "analyses": ["create", "read"],
        "exports": ["create", "read"],
        "scorecards": ["read"],
        "cohorts": ["create", "read", "update"],
    },
    "STRATEGY": {
        "policies": ["read"],
        "analyses": ["read"],
        "exports": ["read"],
        "decisions": ["create", "read", "update"],
        "scorecards": ["read"],
        "cohorts": ["read"],
    },
    "COMPLIANCE": {
        "policies": ["read"],
        "analyses": ["read"],
        "exports": ["read"],
        "decisions": ["read"],
        "scorecards": ["read"],
        "cohorts": ["read"],
    },
    "EXEC_VIEWER": {
        "policies": ["read"],
        "analyses": ["read"],
        "exports": ["read"],
        "scorecards": ["read"],
        "decisions": ["read"],
    },
}


# ----- User management (POLICY_ADMIN or UM_LEADER for list/get; POLICY_ADMIN for create/update) -----


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN", "UM_LEADER"))],
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List users in the current tenant. POLICY_ADMIN or UM_LEADER only."""
    try:
        users = (
            db.query(User)
            .filter(User.tenant_id == current_user.tenant_id)
            .order_by(User.email)
            .offset(skip)
            .limit(limit)
            .all()
        )
    except Exception as e:
        logger.exception("list_users: query failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to list users (database error)") from e

    out: list[UserResponse] = []
    for u in users:
        try:
            raw_roles = u.get_roles(db)
            role_names = [str(r) for r in (raw_roles or []) if r is not None]
            is_active = getattr(u, "is_active", None)
            if is_active is None:
                is_active_s = "true"
            else:
                is_active_s = str(is_active).lower() if isinstance(is_active, bool) else str(is_active)
            row = {
                "id": u.id,
                "tenant_id": u.tenant_id,
                "email": (u.email or "") if u.email is not None else "",
                "full_name": getattr(u, "full_name", None),
                "is_active": is_active_s or "true",
                "auth_source": getattr(u, "auth_source", None) or "local",
                "role_names": role_names,
                "created_at": u.created_at.isoformat() if getattr(u, "created_at", None) else None,
            }
            out.append(UserResponse.model_validate(row))
        except Exception as e:
            logger.warning("list_users: skip user id=%s: %s", getattr(u, "id", "?"), e, exc_info=True)
            continue
    return out


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Get one user. Users can read self; POLICY_ADMIN/UM_LEADER can read any user in tenant."""
    if user_id != current_user.user_id and "POLICY_ADMIN" not in current_user.roles and "UM_LEADER" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Access denied")
    user = db.query(User).filter(User.id == user_id, User.tenant_id == current_user.tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    role_names = user.get_roles(db)
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "email": user.email or "",
        "full_name": getattr(user, "full_name", None),
        "is_active": getattr(user, "is_active", "true") or "true",
        "auth_source": getattr(user, "auth_source", None) or "local",
        "role_names": role_names,
        "created_at": user.created_at.isoformat() if getattr(user, "created_at", None) else None,
    }


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN"))],
    db: Session = Depends(get_db),
):
    """Create a user in the current tenant. POLICY_ADMIN only. Set password for local login; omit for SSO-only or set later."""
    from uuid import uuid4
    from uepi_api.password_utils import hash_password
    existing = db.query(User).filter(User.email == body.email.strip(), User.tenant_id == current_user.tenant_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    password_hash = None
    if body.password:
        password_hash = hash_password(body.password)
    user = User(
        id=uuid4(),
        tenant_id=current_user.tenant_id,
        email=body.email.strip(),
        full_name=body.full_name or None,
        is_active="true",
        auth_source="local",
        password_hash=password_hash,
    )
    db.add(user)
    db.flush()
    if body.role_names:
        user.assign_roles(db, body.role_names)
    db.commit()
    db.refresh(user)
    role_names = user.get_roles(db)
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "email": user.email or "",
        "full_name": getattr(user, "full_name", None),
        "is_active": getattr(user, "is_active", "true") or "true",
        "auth_source": getattr(user, "auth_source", None) or "local",
        "role_names": role_names,
        "created_at": user.created_at.isoformat() if getattr(user, "created_at", None) else None,
    }


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN"))],
    db: Session = Depends(get_db),
):
    """Update a user. POLICY_ADMIN only. Set password only for local users."""
    from uepi_api.password_utils import hash_password
    user = db.query(User).filter(User.id == user_id, User.tenant_id == current_user.tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.role_names is not None:
        user.assign_roles(db, body.role_names)
    if body.password is not None:
        auth_src = getattr(user, "auth_source", None) or "local"
        if auth_src != "local":
            raise HTTPException(status_code=400, detail="Cannot set password for SSO users; they sign in via Active Directory.")
        user.password_hash = hash_password(body.password)
    db.commit()
    db.refresh(user)
    role_names = user.get_roles(db)
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "email": user.email or "",
        "full_name": getattr(user, "full_name", None),
        "is_active": getattr(user, "is_active", "true") or "true",
        "auth_source": getattr(user, "auth_source", None) or "local",
        "role_names": role_names,
        "created_at": user.created_at.isoformat() if getattr(user, "created_at", None) else None,
    }


# ----- Roles and permissions -----


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN"))],
    db: Session = Depends(get_db),
):
    """List all roles"""
    roles = db.query(Role).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "created_at": r.created_at.isoformat(),
        }
        for r in roles
    ]


@router.get("/roles/{role_name}/permissions", response_model=list[PermissionResponse])
async def get_role_permissions(
    role_name: str,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Get permissions for a role"""
    # Check if role exists
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Get permissions from mapping
    permissions = ROLE_PERMISSIONS.get(role_name, {})
    
    return [
        {"resource": resource, "actions": actions}
        for resource, actions in permissions.items()
    ]


@router.get("/users/{user_id}/roles", response_model=UserRoleAssignment)
async def get_user_roles(
    user_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Optional[Session] = Depends(get_db),
):
    """Get roles for a user. For self or when no DB: returns current_user roles (fast). For POLICY_ADMIN viewing another user: optional DB lookup."""
    if user_id != current_user.user_id and "POLICY_ADMIN" not in current_user.roles and "UM_LEADER" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Access denied")
    # Same user: return from current_user (no DB)
    if user_id == current_user.user_id:
        return {
            "user_id": user_id,
            "role_names": current_user.roles if hasattr(current_user, "roles") and current_user.roles else ["POLICY_ADMIN"],
        }
    # Admin viewing another user: optional DB lookup for stored roles
    if db:
        try:
            user = db.query(User).filter(User.id == user_id, User.tenant_id == current_user.tenant_id).first()
            if user:
                return {"user_id": user_id, "role_names": user.get_roles(db)}
        except Exception:
            pass
    return {
        "user_id": user_id,
        "role_names": current_user.roles if hasattr(current_user, "roles") and current_user.roles else ["POLICY_ADMIN"],
    }


@router.get("/users/{user_id}/permissions", response_model=list[PermissionResponse])
async def get_user_permissions(
    user_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Optional[Session] = Depends(get_db),
):
    """Get effective permissions for a user. Uses current_user roles for self; optional DB for admin viewing another user."""
    if user_id != current_user.user_id and "POLICY_ADMIN" not in current_user.roles and "UM_LEADER" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Access denied")
    role_names = current_user.roles if hasattr(current_user, "roles") and current_user.roles else ["POLICY_ADMIN"]
    if user_id != current_user.user_id and db:
        try:
            user = db.query(User).filter(User.id == user_id, User.tenant_id == current_user.tenant_id).first()
            if user:
                role_names = user.get_roles(db)
        except Exception:
            pass
    all_permissions: dict[str, set[str]] = {}
    for role_name in role_names:
        role_perms = ROLE_PERMISSIONS.get(role_name, {})
        for resource, actions in role_perms.items():
            if resource not in all_permissions:
                all_permissions[resource] = set()
            all_permissions[resource].update(actions)
    return [
        {"resource": resource, "actions": sorted(list(actions))}
        for resource, actions in all_permissions.items()
    ]


@router.post("/users/{user_id}/roles", response_model=UserRoleAssignment)
async def assign_user_roles(
    user_id: UUID,
    assignment: UserRoleAssignment,
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN"))],
    db: Session = Depends(get_db),
):
    """Assign roles to user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check tenant access
    if user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Assign roles using helper method
    user.assign_roles(db, assignment.role_names)
    
    db.commit()
    db.refresh(user)
    
    user_role_names = user.get_roles(db)  # Use helper method instead of relationship
    
    return {
        "user_id": user.id,
        "role_names": user_role_names,
    }


@router.get("/check-permission")
async def check_permission(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    resource: str = Query(...),
    action: str = Query(...),
    db: Session = Depends(get_db),
):
    """Check if current user has permission - Database-only"""
    # Database mode - query user roles
    user = db.query(User).filter(User.id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_role_names = user.get_roles(db)
    
    # Check permissions from all roles
    has_permission = False
    for role_name in user_role_names:
        role_perms = ROLE_PERMISSIONS.get(role_name, {})
        if resource in role_perms and action in role_perms[resource]:
            has_permission = True
            break
    
    return {
        "has_permission": has_permission,
        "resource": resource,
        "action": action,
        "user_roles": user_role_names,
    }

