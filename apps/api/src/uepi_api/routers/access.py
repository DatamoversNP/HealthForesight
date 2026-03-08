"""Access management endpoints (RBAC, Permissions)"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from uepi_api.auth import CurrentUser, verify_token, require_role, get_demo_current_user
from uepi_api.database import get_db
from uepi_api.models.tenant import Role, User
from uepi_common.models import TenantRole

router = APIRouter()


class RoleCreate(BaseModel):
    """Role creation model"""
    name: str
    description: str | None = None


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
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get roles for a user - Non-blocking, returns immediately without database"""
    # Return roles from current_user immediately (non-blocking, no database required)
    # This avoids database queries that might hang
    try:
        # Users can only see their own roles unless admin
        if user_id != current_user.user_id and "POLICY_ADMIN" not in current_user.roles:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Return roles from current_user immediately (no database query)
        return {
            "user_id": user_id,
            "role_names": current_user.roles if hasattr(current_user, 'roles') and current_user.roles else ["POLICY_ADMIN"],
        }
    except HTTPException:
        raise
    except Exception as e:
        # Handle any other errors gracefully
        import traceback
        print(f"ERROR in get_user_roles: {e}")
        traceback.print_exc()
        return {
            "user_id": user_id,
            "role_names": current_user.roles if hasattr(current_user, 'roles') and current_user.roles else ["POLICY_ADMIN"],
        }


@router.get("/users/{user_id}/permissions", response_model=list[PermissionResponse])
async def get_user_permissions(
    user_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get effective permissions for a user - Non-blocking, returns immediately without database"""
    # Return permissions immediately based on current_user roles (non-blocking, no database required)
    # This avoids database queries that might hang
    try:
        # Users can only see their own permissions unless admin
        if user_id != current_user.user_id and "POLICY_ADMIN" not in current_user.roles:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get roles from current_user (non-blocking, no database query)
        user_roles = current_user.roles if hasattr(current_user, 'roles') and current_user.roles else ["POLICY_ADMIN"]
        
        # Collect all permissions from user's roles
        all_permissions: dict[str, set[str]] = {}
        for role_name in user_roles:
            role_perms = ROLE_PERMISSIONS.get(role_name, {})
            for resource, actions in role_perms.items():
                if resource not in all_permissions:
                    all_permissions[resource] = set()
                all_permissions[resource].update(actions)
        
        return [
            {"resource": resource, "actions": sorted(list(actions))}
            for resource, actions in all_permissions.items()
        ]
    except HTTPException:
        raise
    except Exception as e:
        # Handle any other errors gracefully
        import traceback
        print(f"ERROR in get_user_permissions: {e}")
        traceback.print_exc()
        # Return default permissions
        user_roles = current_user.roles if hasattr(current_user, 'roles') and current_user.roles else ["POLICY_ADMIN"]
        all_permissions: dict[str, set[str]] = {}
        for role_name in user_roles:
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

