"""RBAC endpoints for file-based storage"""
from typing import Annotated, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_roles import (
    create_role, get_role, list_roles, update_role, delete_role
)
from uepi_api.storage_user_roles import (
    assign_user_role, get_user_roles, remove_user_role, get_users_with_role
)
from uepi_common.models_enhanced import (
    Role, Permission, PersonaRole, ResourceType, ActionType, UserRole, ResourceScope
)

router = APIRouter()


class RoleCreate(BaseModel):
    """Role creation model"""
    name: str
    description: Optional[str] = None
    persona: Optional[PersonaRole] = None
    permissions: List[dict]  # Simplified for API - will convert to Permission objects


class RoleUpdate(BaseModel):
    """Role update model"""
    name: Optional[str] = None
    description: Optional[str] = None
    persona: Optional[PersonaRole] = None
    permissions: Optional[List[dict]] = None


class RoleResponse(BaseModel):
    """Role response model"""
    id: str
    name: str
    description: Optional[str]
    persona: Optional[str]
    permissions: List[dict]
    created_at: str
    updated_at: str


class UserRoleAssign(BaseModel):
    """User role assignment model"""
    role_id: UUID
    resource_scopes: Optional[List[dict]] = None


class PermissionCheck(BaseModel):
    """Permission check request"""
    resource: ResourceType
    action: ActionType
    resource_id: Optional[UUID] = None


@router.get("/roles", response_model=List[RoleResponse])
async def list_all_roles(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """List all roles"""
    roles = list_roles()
    return [
        RoleResponse(
            id=str(r.id),
            name=r.name,
            description=r.description,
            persona=r.persona.value if r.persona else None,
            permissions=[
                {
                    "resource": p.resource.value,
                    "actions": [a.value for a in p.actions],
                    "scope": p.scope.model_dump(mode='json') if p.scope else None
                }
                for p in r.permissions
            ],
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat()
        )
        for r in roles
    ]


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role_by_id(
    role_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get role by ID"""
    role = get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return RoleResponse(
        id=str(role.id),
        name=role.name,
        description=role.description,
        persona=role.persona.value if role.persona else None,
        permissions=[
            {
                "resource": p.resource.value,
                "actions": [a.value for a in p.actions],
                "scope": p.scope.model_dump(mode='json') if p.scope else None
            }
            for p in role.permissions
        ],
        created_at=role.created_at.isoformat(),
        updated_at=role.updated_at.isoformat()
    )


@router.post("/roles", response_model=RoleResponse, status_code=201)
async def create_new_role(
    role_data: RoleCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create a new role"""
    # Convert permissions from dict to Permission objects
    permissions = []
    for p_data in role_data.permissions:
        permissions.append(Permission(
            resource=ResourceType(p_data['resource']),
            actions=[ActionType(a) for a in p_data['actions']],
            scope=ResourceScope(**p_data['scope']) if p_data.get('scope') else None
        ))
    
    role = Role(
        name=role_data.name,
        description=role_data.description,
        persona=role_data.persona,
        permissions=permissions
    )
    
    created_role = create_role(role)
    
    return RoleResponse(
        id=str(created_role.id),
        name=created_role.name,
        description=created_role.description,
        persona=created_role.persona.value if created_role.persona else None,
        permissions=[
            {
                "resource": p.resource.value,
                "actions": [a.value for a in p.actions],
                "scope": p.scope.model_dump(mode='json') if p.scope else None
            }
            for p in created_role.permissions
        ],
        created_at=created_role.created_at.isoformat(),
        updated_at=created_role.updated_at.isoformat()
    )


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role_by_id(
    role_id: UUID,
    role_data: RoleUpdate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Update role"""
    existing = get_role(role_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")
    
    update_dict = {}
    if role_data.name is not None:
        update_dict['name'] = role_data.name
    if role_data.description is not None:
        update_dict['description'] = role_data.description
    if role_data.persona is not None:
        update_dict['persona'] = role_data.persona.value
    
    if role_data.permissions is not None:
        permissions = []
        for p_data in role_data.permissions:
            permissions.append({
                'resource': p_data['resource'],
                'actions': p_data['actions'],
                'scope': p_data.get('scope')
            })
        update_dict['permissions'] = permissions
    
    updated = update_role(role_id, update_dict)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update role")
    
    return RoleResponse(
        id=str(updated.id),
        name=updated.name,
        description=updated.description,
        persona=updated.persona.value if updated.persona else None,
        permissions=[
            {
                "resource": p.resource.value,
                "actions": [a.value for a in p.actions],
                "scope": p.scope.model_dump(mode='json') if p.scope else None
            }
            for p in updated.permissions
        ],
        created_at=updated.created_at.isoformat(),
        updated_at=updated.updated_at.isoformat()
    )


@router.delete("/roles/{role_id}", status_code=204)
async def delete_role_by_id(
    role_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Delete role"""
    if not delete_role(role_id):
        raise HTTPException(status_code=404, detail="Role not found")
    return None


@router.get("/users/{user_id}/roles", response_model=List[dict])
async def get_user_role_assignments(
    user_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get all role assignments for a user"""
    user_roles = get_user_roles(user_id)
    return [
        {
            "user_id": str(ur.user_id),
            "role_id": str(ur.role_id),
            "resource_scopes": [rs.model_dump(mode='json') for rs in ur.resource_scopes] if ur.resource_scopes else [],
            "assigned_at": ur.assigned_at.isoformat(),
            "assigned_by": str(ur.assigned_by)
        }
        for ur in user_roles
    ]


@router.post("/users/{user_id}/roles", response_model=dict, status_code=201)
async def assign_role_to_user(
    user_id: UUID,
    assignment: UserRoleAssign,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Assign role to user"""
    resource_scopes = None
    if assignment.resource_scopes:
        resource_scopes = [ResourceScope(**rs) for rs in assignment.resource_scopes]
    
    user_role = assign_user_role(
        user_id=user_id,
        role_id=assignment.role_id,
        assigned_by=current_user.user_id,
        resource_scopes=resource_scopes
    )
    
    return {
        "user_id": str(user_role.user_id),
        "role_id": str(user_role.role_id),
        "resource_scopes": [rs.model_dump(mode='json') for rs in user_role.resource_scopes] if user_role.resource_scopes else [],
        "assigned_at": user_role.assigned_at.isoformat(),
        "assigned_by": str(user_role.assigned_by)
    }


@router.delete("/users/{user_id}/roles/{role_id}", status_code=204)
async def remove_role_from_user(
    user_id: UUID,
    role_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Remove role from user"""
    if not remove_user_role(user_id, role_id):
        raise HTTPException(status_code=404, detail="Role assignment not found")
    return None


@router.get("/permissions/check")
async def check_user_permission(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    resource: ResourceType = Query(...),
    action: ActionType = Query(...),
    resource_id: Optional[UUID] = Query(None),
):
    """Check if current user has permission"""
    # Get user's roles
    user_roles = get_user_roles(current_user.user_id)
    
    # Check permissions from all roles
    has_permission = False
    matching_roles = []
    
    for user_role in user_roles:
        role = get_role(user_role.role_id)
        if not role:
            continue
        
        # Check if role has permission
        for permission in role.permissions:
            if permission.resource == resource and action in permission.actions:
                # Check resource scope if resource_id provided
                if resource_id and permission.scope:
                    # TODO: Implement scope checking logic
                    pass
                has_permission = True
                matching_roles.append(role.name)
                break
    
    return {
        "has_permission": has_permission,
        "resource": resource.value,
        "action": action.value,
        "resource_id": str(resource_id) if resource_id else None,
        "matching_roles": matching_roles,
        "user_id": str(current_user.user_id)
    }


@router.get("/users/{user_id}/permissions", response_model=List[dict])
async def get_user_effective_permissions(
    user_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get effective permissions for a user"""
    user_roles = get_user_roles(user_id)
    
    # Collect all permissions
    all_permissions: dict[str, set[str]] = {}
    
    for user_role in user_roles:
        role = get_role(user_role.role_id)
        if not role:
            continue
        
        for permission in role.permissions:
            resource_key = permission.resource.value
            if resource_key not in all_permissions:
                all_permissions[resource_key] = set()
            all_permissions[resource_key].update([a.value for a in permission.actions])
    
    return [
        {
            "resource": resource,
            "actions": sorted(list(actions))
        }
        for resource, actions in all_permissions.items()
    ]


