"""Authentication endpoints - Database mode with non-blocking fallback. Supports AD (OIDC) and local (email/password) login."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, verify_token, create_local_jwt
from uepi_api.database import get_db
from uepi_api.models.tenant import User, Tenant
from uepi_api.password_utils import verify_password
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()


class LoginRequest(BaseModel):
    """Email/password login for local users."""
    email: str
    password: str


class LoginResponse(BaseModel):
    """JWT and user info after successful login."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    roles: list[str]


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


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    """Log in with email and password (local users only). Returns JWT for Authorization header."""
    from sqlalchemy import func
    from uepi_api.storage_auth import DEFAULT_TENANT_ID

    email_clean = body.email.strip().lower()
    try:
        user = (
            db.query(User)
            .filter(func.lower(User.email) == email_clean, User.tenant_id == DEFAULT_TENANT_ID)
            .first()
        )
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        auth_source = getattr(user, "auth_source", None) or "local"
        if auth_source != "local":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This account uses single sign-on (SSO). Please sign in with your organization login.",
            )
        password_hash = getattr(user, "password_hash", None)
        if not password_hash or not verify_password(body.password, password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        if (getattr(user, "is_active", "true") or "true") != "true":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
        roles = user.get_roles(db)
        if not roles:
            roles = ["POLICY_ADMIN"]
        token = create_local_jwt(user.id, user.tenant_id, user.email, roles)
        return LoginResponse(
            access_token=token,
            user_id=str(user.id),
            email=user.email,
            roles=roles,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Database unavailable (login requires PostgreSQL). "
                "On Azure: set DATABASE_URL on healthforesight-api, allow App Service outbound IPs "
                "on PostgreSQL firewall, and run DB migrations/seed. "
                f"Error: {str(e)[:200]}"
            ),
        ) from e


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Return the authenticated user (same JWT rules as the rest of the API)."""
    name = current_user.email.split("@")[0] if "@" in current_user.email else "User"
    if name.lower() == "demo":
        name = "Demo User"
    tenant_name = "Demo Tenant"
    try:
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if tenant and getattr(tenant, "name", None):
            tenant_name = tenant.name
    except Exception:
        pass
    return UserResponse(
        id=current_user.user_id,
        email=current_user.email,
        full_name=name,
        tenant_id=current_user.tenant_id,
        tenant_name=tenant_name,
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

