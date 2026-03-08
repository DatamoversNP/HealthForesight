"""Administrative endpoints"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from uepi_api.auth import CurrentUser, verify_token, require_role
from uepi_api.database import get_db
from uepi_api.models.tenant import Tenant, User, Role
from uepi_common.models import TenantRole

router = APIRouter()


class UserCreate(BaseModel):
    """User creation model"""
    email: EmailStr
    full_name: str | None = None
    oidc_sub: str | None = None
    roles: list[str] = []
    is_active: bool = True


class UserUpdate(BaseModel):
    """User update model"""
    full_name: str | None = None
    roles: list[str] | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    """User response model"""
    id: UUID
    email: str
    full_name: str | None
    is_active: bool
    roles: list[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class TenantCreate(BaseModel):
    """Tenant creation model"""
    name: str
    domain: str | None = None


class TenantUpdate(BaseModel):
    """Tenant update model"""
    name: str | None = None
    domain: str | None = None


class TenantResponse(BaseModel):
    """Tenant response model"""
    id: UUID
    name: str
    domain: str | None
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN"))],
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List users (admin only)"""
    query = db.query(User)
    
    # If tenant_id provided, filter by tenant (super admin can see all)
    if tenant_id:
        query = query.filter(User.tenant_id == tenant_id)
    else:
        # Regular admin can only see their tenant
        query = query.filter(User.tenant_id == current_user.tenant_id)
    
    users = query.offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        user_role_names = user.get_roles(db)  # Use helper method instead of relationship
        result.append({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active == "true" if isinstance(user.is_active, str) else user.is_active,
            "roles": user_role_names,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        })
    
    return result


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN"))],
    db: Session = Depends(get_db),
):
    """Get user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check tenant access
    if user.tenant_id != current_user.tenant_id and "POLICY_ADMIN" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Access denied")
    
    user_role_names = user.get_roles(db)  # Use helper method instead of relationship
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active == "true" if isinstance(user.is_active, str) else user.is_active,
        "roles": user_role_names,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN"))],
    db: Session = Depends(get_db),
):
    """Create user (admin only)"""
    # Check if user already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create user
    user = User(
        tenant_id=current_user.tenant_id,
        email=user_data.email,
        full_name=user_data.full_name,
        oidc_sub=user_data.oidc_sub,
        is_active="true" if user_data.is_active else "false",
    )
    db.add(user)
    db.flush()
    
    # Assign roles
    if user_data.roles:
        user.assign_roles(db, user_data.roles)  # Use helper method instead of relationship
    
    db.commit()
    db.refresh(user)
    
    user_role_names = user.get_roles(db)  # Use helper method instead of relationship
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active == "true" if isinstance(user.is_active, str) else user.is_active,
        "roles": user_role_names,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN"))],
    db: Session = Depends(get_db),
):
    """Update user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check tenant access
    if user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.is_active is not None:
        user.is_active = "true" if user_data.is_active else "false"
    
    # Update roles
    if user_data.roles is not None:
        user.assign_roles(db, user_data.roles)  # Use helper method instead of relationship
    
    from datetime import datetime
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    user_role_names = user.get_roles(db)  # Use helper method instead of relationship
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active == "true" if isinstance(user.is_active, str) else user.is_active,
        "roles": user_role_names,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN"))],
    db: Session = Depends(get_db),
):
    """Delete user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check tenant access
    if user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Prevent deleting yourself
    if user.id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    db.delete(user)
    db.commit()


@router.get("/tenants", response_model=list[TenantResponse])
async def list_tenants(
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN"))],
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List tenants (super admin only)"""
    # For now, regular admins can only see their tenant
    query = db.query(Tenant).filter(Tenant.id == current_user.tenant_id)
    
    tenants = query.offset(skip).limit(limit).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "domain": t.domain,
            "created_at": t.created_at.isoformat(),
        }
        for t in tenants
    ]


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN"))],
    db: Session = Depends(get_db),
):
    """Get tenant (admin only)"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check access
    if tenant.id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": tenant.id,
        "name": tenant.name,
        "domain": tenant.domain,
        "created_at": tenant.created_at.isoformat(),
    }


@router.post("/tenants", response_model=TenantResponse, status_code=201)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN"))],
    db: Session = Depends(get_db),
):
    """Create tenant (super admin only - placeholder)"""
    # For MVP, only allow creating within same tenant context
    raise HTTPException(status_code=501, detail="Tenant creation not yet implemented")


@router.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    tenant_data: TenantUpdate,
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN"))],
    db: Session = Depends(get_db),
):
    """Update tenant (admin only)"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check access
    if tenant.id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if tenant_data.name is not None:
        tenant.name = tenant_data.name
    if tenant_data.domain is not None:
        tenant.domain = tenant_data.domain
    
    db.commit()
    db.refresh(tenant)
    
    return {
        "id": tenant.id,
        "name": tenant.name,
        "domain": tenant.domain,
        "created_at": tenant.created_at.isoformat(),
    }

