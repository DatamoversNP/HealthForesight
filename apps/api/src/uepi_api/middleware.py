"""Middleware for audit logging and tenant filtering"""
from typing import Callable
from uuid import UUID

from fastapi import Request, Response
from sqlalchemy.orm import Session

from uepi_api.auth import CurrentUser
from uepi_api.database import get_db
from uepi_api.models.audit import AuditAction, AuditEvent


async def audit_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware to log audit events"""
    # Skip audit for health checks and static files
    if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)
    
    response = await call_next(request)
    
    # Log mutations (POST, PUT, DELETE)
    if request.method in ["POST", "PUT", "DELETE"] and response.status_code < 400:
        # Try to get current user from request state (set by auth dependency)
        user: CurrentUser | None = getattr(request.state, "current_user", None)
        if user:
            db: Session = next(get_db())
            try:
                audit = AuditEvent(
                    tenant_id=user.tenant_id,
                    user_id=user.user_id,
                    action=AuditAction[request.method].value if request.method in ["POST", "PUT", "DELETE"] else AuditAction.VIEW.value,
                    object_type=request.url.path.split("/")[-2] if len(request.url.path.split("/")) > 2 else "unknown",
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )
                db.add(audit)
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()
    
    return response


def add_tenant_filter(query, model_class, tenant_id: UUID):
    """Add tenant_id filter to SQLAlchemy query"""
    if hasattr(model_class, "tenant_id"):
        return query.filter(model_class.tenant_id == tenant_id)
    return query

