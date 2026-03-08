"""Authentication and authorization"""
from typing import Annotated
from uuid import UUID, uuid4
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import text

from uepi_api.config import get_settings
from uepi_api.database import get_db
from uepi_api.storage_auth import get_demo_user
from uepi_api.models.tenant import User, Tenant
from uepi_common.models import TenantRole as CommonTenantRole

security = HTTPBearer(auto_error=False)  # Don't auto-error, handle manually

# Thread pool for database operations with timeout
_db_executor = ThreadPoolExecutor(max_workers=5)


class CurrentUser:
    """Current authenticated user"""
    def __init__(
        self,
        user_id: UUID,
        tenant_id: UUID,
        email: str,
        roles: list[str],
        oidc_sub: str | None = None,
    ):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.email = email
        self.roles = roles
        self.oidc_sub = oidc_sub


async def get_jwks(issuer: str) -> dict:
    """Fetch JWKS from OIDC issuer"""
    jwks_url = f"{issuer}/.well-known/openid-configuration"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(jwks_url)
            response.raise_for_status()
            config = response.json()
            jwks_uri = config.get("jwks_uri")
            if not jwks_uri:
                raise ValueError("No jwks_uri in OIDC config")
            
            jwks_response = await client.get(jwks_uri)
            jwks_response.raise_for_status()
            return jwks_response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to fetch JWKS: {str(e)}",
            )


async def get_demo_current_user(db=None) -> CurrentUser:
    """Get demo user as CurrentUser - database only"""
    # Database mode - Fixed UUIDs for demo user/tenant (consistent across calls)
    # Use same tenant ID as DEFAULT_TENANT_ID for consistency with seeding scripts
    demo_user_id = UUID("00000000-0000-0000-0000-000000000001")
    demo_tenant_id = UUID("00000000-0000-0000-0000-000000000001")  # Match DEFAULT_TENANT_ID
    
    # Try to get/create from database if available, but don't fail if DB is unavailable
    if db:
        try:
            # Test database connection first with timeout protection (5 second timeout)
            def test_connection():
                try:
                    db.execute(text("SELECT 1"))
                    return True
                except Exception:
                    return False
            
            try:
                # Run connection test with 5 second timeout
                future = _db_executor.submit(test_connection)
                connection_ok = future.result(timeout=5)
                if not connection_ok:
                    raise Exception("Connection test failed")
            except (FutureTimeoutError, Exception) as conn_error:
                # Database connection failed or timed out - skip DB queries
                print(f"WARNING: Database connection failed/timed out in get_demo_current_user: {conn_error}")
                db = None  # Skip all database operations
            
            if db:
                # Try to get existing demo user from DB
                demo_user = db.query(User).filter(User.email == "demo@example.com").first()
                if demo_user:
                    return CurrentUser(
                        user_id=demo_user.id,
                        tenant_id=demo_user.tenant_id,
                        email=demo_user.email,
                        roles=["POLICY_ADMIN", "UM_LEADER"],
                    )
                
                # Try to create demo tenant and user
                demo_tenant = db.query(Tenant).filter(Tenant.id == demo_tenant_id).first()
                if not demo_tenant:
                    demo_tenant = Tenant(id=demo_tenant_id, name="Demo Tenant", domain="demo")
                    db.add(demo_tenant)
                
                demo_user = User(
                    id=demo_user_id,
                    tenant_id=demo_tenant_id,
                    email="demo@example.com",
                    full_name="Demo User",
                    is_active="true",
                    is_admin="true",
                    is_tenant_admin="true",
                )
                db.add(demo_user)
                db.commit()
                db.refresh(demo_user)
                
                return CurrentUser(
                    user_id=demo_user.id,
                    tenant_id=demo_user.tenant_id,
                    email=demo_user.email,
                    roles=["POLICY_ADMIN", "UM_LEADER"],
                )
        except Exception as e:
            # Database unavailable or error - use fixed UUIDs without DB
            print(f"WARNING: Database error in get_demo_current_user: {e}")
            if db:
                try:
                    db.rollback()
                except:
                    pass
    
    # Return CurrentUser with fixed UUIDs (no database required)
    return CurrentUser(
        user_id=demo_user_id,
        tenant_id=demo_tenant_id,
        email="demo@example.com",
        roles=["POLICY_ADMIN", "UM_LEADER"],
    )


async def verify_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
    db: Session = Depends(get_db),
) -> CurrentUser:
    """Verify JWT token and return current user"""
    settings = get_settings()
    
    # Check OIDC configuration (properly handle None/empty values)
    try:
        oidc_issuer = settings.oidc.issuer if hasattr(settings, 'oidc') and hasattr(settings.oidc, 'issuer') else None
    except Exception:
        oidc_issuer = None
    
    if not oidc_issuer:
        oidc_issuer = ""
    oidc_issuer = str(oidc_issuer).strip()
    
    # Consider OIDC configured only if it's a real URL (not localhost/default)
    oidc_configured = bool(
        oidc_issuer 
        and oidc_issuer != "" 
        and oidc_issuer != "http://localhost:8080/auth/realms/uepi"
        and not oidc_issuer.startswith("http://localhost")
        and ("https://" in oidc_issuer or "http://" in oidc_issuer)
    )
    is_dev_mode = settings.environment in ("development", "dev", "test")
    
    # Handle missing credentials
    if not credentials or not credentials.credentials:
        # In dev mode or if OIDC not configured, allow no credentials
        if is_dev_mode or not oidc_configured:
            return await get_demo_current_user(db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    
    token = credentials.credentials
    
    # ALWAYS check for mock tokens FIRST (before environment/OIDC checks)
    # This allows testing in any environment
    if token.startswith("dev-token-") or token.startswith("mock-") or (len(token) < 50 and not token.count(".") >= 2):
        # Mock token - fallback to demo user
        return await get_demo_current_user(db)
    
    try:
        # Try to decode token without verification first to check if it's a JWT
        try:
            unverified = jwt.get_unverified_claims(token)
            issuer = unverified.get("iss")
        except Exception:
            # Not a valid JWT format - in dev mode or if OIDC not configured, treat as mock token
            if is_dev_mode or not oidc_configured:
                return await get_demo_current_user(db)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
            )
        
        if not issuer:
            # No issuer - in dev mode or if OIDC not configured, use demo user
            if is_dev_mode or not oidc_configured:
                return await get_demo_current_user(db)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no issuer",
            )
        
        # Verify issuer matches (if OIDC is configured)
        if oidc_configured and issuer != settings.oidc.issuer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: issuer mismatch",
            )
        
        # Get JWKS and verify token (if OIDC is configured)
        if oidc_configured:
            try:
                jwks = await get_jwks(settings.oidc.issuer)
                # For MVP, use simple verification
                decoded = jwt.decode(
                    token,
                    options={"verify_signature": False},  # Simplified for MVP
                )
            except Exception as e:
                # If JWKS fetch fails, fall back to demo user in dev mode
                if is_dev_mode or not oidc_configured:
                    return await get_demo_current_user(db)
                raise
        else:
            # No OIDC configured - decode without verification
            decoded = jwt.decode(token, options={"verify_signature": False})
        
        # Extract user info
        oidc_sub = decoded.get("sub")
        email = decoded.get("email") or decoded.get("preferred_username") or decoded.get("email")
        tenant_id_str = decoded.get("tenant_id") or decoded.get("org_id")
        token_roles = decoded.get("roles", [])
        
        if not email:
            # Fallback to demo user in dev mode or if OIDC not configured
            if is_dev_mode or not oidc_configured:
                return await get_demo_current_user(db)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing required claims",
            )
        
        # Get or create user from database (only if DB is available)
        try:
            # Test database connection first with timeout protection (5 second timeout)
            def test_connection():
                try:
                    db.execute(text("SELECT 1"))
                    return True
                except Exception:
                    return False
            
            try:
                # Run connection test with 5 second timeout
                future = _db_executor.submit(test_connection)
                connection_ok = future.result(timeout=5)
                if not connection_ok:
                    raise Exception("Connection test failed")
            except (FutureTimeoutError, Exception) as conn_error:
                # Database connection failed or timed out - skip DB queries
                print(f"WARNING: Database connection failed/timed out in verify_token: {conn_error}")
                if is_dev_mode or not oidc_configured:
                    return await get_demo_current_user(None)  # Pass None to skip DB
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Database connection failed: {str(conn_error)}",
                )
            
            if oidc_sub:
                user = db.query(User).filter(User.oidc_sub == oidc_sub).first()
            else:
                user = db.query(User).filter(User.email == email).first()
            
            tenant_id = UUID(tenant_id_str) if tenant_id_str else None
            
            if not user:
                # Create user (first login)
                if not tenant_id:
                    # In dev mode or if OIDC not configured, use demo tenant ID
                    if is_dev_mode or not oidc_configured:
                        tenant_id = UUID("00000000-0000-0000-0000-000000000001")  # Demo tenant ID (match DEFAULT_TENANT_ID)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No tenant_id in token",
                        )
                user = User(
                    oidc_sub=oidc_sub,
                    email=email,
                    tenant_id=tenant_id,
                    full_name=decoded.get("name"),
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            # Extract roles from token
            roles = decoded.get("roles", []) or decoded.get("groups", [])
            if isinstance(roles, str):
                roles = [roles]
            if not roles:
                roles = ["POLICY_ADMIN"]  # Default role
            
            return CurrentUser(
                user_id=user.id,
                tenant_id=user.tenant_id,
                email=user.email,
                roles=roles,
                oidc_sub=user.oidc_sub,
            )
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as db_error:
            # Database unavailable - fall back to demo user
            print(f"WARNING: Database error in verify_token: {db_error}")
            if is_dev_mode or not oidc_configured:
                return await get_demo_current_user(None)  # Pass None to skip DB
            # In production with OIDC, this is a real error
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database unavailable: {str(db_error)}",
            )
        
    except JWTError as e:
        # JWT error - in dev mode or if OIDC not configured, fallback to demo user
        if is_dev_mode or not oidc_configured:
            return await get_demo_current_user(db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Any other error - in dev mode or if OIDC not configured, fallback to demo user
        if is_dev_mode or not oidc_configured:
            return await get_demo_current_user(db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


def require_role(*allowed_roles: str):
    """Dependency to require specific role"""
    def role_checker(current_user: Annotated[CurrentUser, Depends(verify_token)]) -> CurrentUser:
        user_roles = set(current_user.roles)
        allowed = set(allowed_roles)
        
        if not user_roles.intersection(allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(allowed_roles)}",
            )
        return current_user
    
    return role_checker


def require_tenant_access(
    tenant_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
) -> CurrentUser:
    """Ensure user can access the specified tenant"""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: tenant mismatch",
        )
    return current_user
