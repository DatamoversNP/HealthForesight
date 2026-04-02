"""Tenant and user models"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Table
from sqlalchemy import select, delete, insert
from sqlalchemy import UUID as GenericUUID
# Use generic UUID that works with all databases
PGUUID = GenericUUID
from sqlalchemy.orm import relationship

from uepi_api.database import Base
from uepi_common.models import TenantRole

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# Many-to-many relationship between users and roles
# Using role name (String) to store TenantRole enum values directly
# The Role table is for reference/documentation, but user roles are stored as strings
# Note: Column is 'role' (not 'role_name') to match existing database schema
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role", String, primary_key=True),  # Stores TenantRole enum values as strings (e.g., "POLICY_ADMIN")
)


class Tenant(Base):
    """Tenant (organization) model"""
    __tablename__ = "tenants"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    users = relationship("User", back_populates="tenant")


class User(Base):
    """User model. Supports both OIDC (e.g. Azure AD) and local (email/password) users."""
    __tablename__ = "users"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    oidc_sub = Column(String, unique=True, nullable=True, index=True)  # Set for AD/OIDC users
    full_name = Column(String, nullable=True)
    is_active = Column(String, default="true", nullable=False)  # Using String for compatibility
    # auth_source: "oidc" (Azure AD / external IdP) or "local" (email/password)
    auth_source = Column(String(32), nullable=True, default="local")
    # password_hash: only set for local users; OIDC users authenticate via IdP
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    tenant = relationship("Tenant", back_populates="users")
    # Note: Roles are stored as strings in user_roles table (TenantRole enum values)
    # The Role relationship is removed to avoid SQLAlchemy join condition issues
    # Use get_user_roles() helper function to query roles
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def get_roles(self, db) -> list[str]:
        """Get user roles as list of role name strings"""
        result = db.execute(select(user_roles.c.role).where(user_roles.c.user_id == self.id))
        return [row[0] for row in result.all()]
    
    def get_role_objects(self, db) -> list:
        """Get user roles as Role model objects"""
        role_names = self.get_roles(db)
        if not role_names:
            return []
        return db.query(Role).filter(Role.name.in_(role_names)).all()
    
    def assign_roles(self, db, role_names: list[str]):
        """Assign roles to user (clears existing and assigns new)"""
        # Delete existing roles
        db.execute(delete(user_roles).where(user_roles.c.user_id == self.id))
        db.flush()
        
        # Insert new roles
        for role_name in role_names:
            # Verify role exists
            role = db.query(Role).filter(Role.name == role_name).first()
            if role:
                db.execute(insert(user_roles).values(user_id=self.id, role=role_name))
        db.flush()


class Role(Base):
    """Role model (for RBAC)"""
    __tablename__ = "roles"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Note: User relationship via user_roles is removed to avoid SQLAlchemy join condition issues
    # To query users with a role: db.execute(select(user_roles.c.user_id).where(user_roles.c.role == role.name)).scalars().all()


# User.notifications / User.notification_preferences use string refs to these classes; load the module
# so SQLAlchemy can configure the User mapper (otherwise db.query(User) raises InvalidRequestError).
import uepi_api.models.notification  # noqa: E402, F401

