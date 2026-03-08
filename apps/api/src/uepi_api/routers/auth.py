"""Authentication endpoints - Database mode with non-blocking fallback"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, verify_token, get_demo_current_user

router = APIRouter()


class UserResponse(BaseModel):
    """User response model"""
    id: UUID
    email: str
    full_name: str | None
    tenant_id: UUID
    tenant_name: str | None
    roles: list[str]
    
    class Config:
        from_attributes = True


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get current user information - Uses demo user (non-blocking, no database required)"""
    # Return info from CurrentUser (non-blocking, doesn't require database)
    # Extract name from email or use "Demo User"
    name = current_user.email.split("@")[0] if "@" in current_user.email else "Demo User"
    if name == "demo":
        name = "Demo User"
    
    return UserResponse(
        id=current_user.user_id,
        email=current_user.email,
        full_name=name,
        tenant_id=current_user.tenant_id,
        tenant_name="Demo Tenant",
        roles=current_user.roles,
    )


@router.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
):
    """Get tenant information (admin only) - File storage only"""
    # Check if user is admin (simplified for MVP)
    if "POLICY_ADMIN" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # File storage mode - return demo tenant info
    if tenant_id == current_user.tenant_id:
        return {
            "id": tenant_id,
            "name": "Demo Tenant",
            "domain": None,
        }
    
    raise HTTPException(status_code=404, detail="Tenant not found")

