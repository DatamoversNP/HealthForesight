"""File-based user role assignment storage - database only"""
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.tenant import User, Role, user_roles
from sqlalchemy import select, insert, delete
from uepi_common.models_enhanced import UserRole, ResourceScope


def assign_user_role(user_id: UUID, role_id: UUID, assigned_by: UUID, resource_scopes: Optional[List[ResourceScope]] = None) -> UserRole:
    """Assign role to user - stored in database"""
    return _assign_user_role(user_id, role_id, assigned_by, resource_scopes)


def _assign_user_role(user_id: UUID, role_id: UUID, assigned_by: UUID, resource_scopes: Optional[List[ResourceScope]] = None) -> UserRole:
    """Assign role to user in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise ValueError(f"Role {role_id} not found")
        
        existing = db.execute(select(user_roles.c.role).where(
            user_roles.c.user_id == user_id,
            user_roles.c.role == role.name
        )).first()
        
        if not existing:
            db.execute(insert(user_roles).values(user_id=user_id, role=role.name))
            db.commit()
        
        return UserRole(
            user_id=user_id,
            role_id=role_id,
            resource_scopes=resource_scopes,
            assigned_at=datetime.utcnow(),
            assigned_by=assigned_by
        )
        
    except Exception as e:
        db.rollback()
        print(f"ERROR assign_user_role (DB): {e}")
        raise ValueError(f"Failed to assign user role: {e}")
    finally:
        db.close()


def get_user_roles(user_id: UUID) -> List[UserRole]:
    """Get all role assignments for user - from database"""
    return _get_user_roles(user_id)


def _get_user_roles(user_id: UUID) -> List[UserRole]:
    """Get all role assignments for user from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        role_names = db.execute(select(user_roles.c.role).where(user_roles.c.user_id == user_id)).scalars().all()
        roles = db.query(Role).filter(Role.name.in_(role_names)).all()
        
        result = []
        for role in roles:
            result.append(UserRole(
                user_id=user_id,
                role_id=role.id,
                resource_scopes=None,
                assigned_at=datetime.utcnow(),
                assigned_by=uuid4(),
            ))
        
        return result
        
    except Exception as e:
        print(f"ERROR get_user_roles (DB): {e}")
        return []
    finally:
        db.close()


def remove_user_role(user_id: UUID, role_id: UUID) -> bool:
    """Remove role assignment from user - from database"""
    return _remove_user_role(user_id, role_id)


def _remove_user_role(user_id: UUID, role_id: UUID) -> bool:
    """Remove role assignment from user in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return False
        
        result = db.execute(delete(user_roles).where(
            user_roles.c.user_id == user_id,
            user_roles.c.role == role.name
        ))
        db.commit()
        
        return result.rowcount > 0
        
    except Exception as e:
        db.rollback()
        print(f"ERROR remove_user_role (DB): {e}")
        return False
    finally:
        db.close()


def get_users_with_role(role_id: UUID) -> List[UUID]:
    """Get all users with a specific role - from database"""
    return _get_users_with_role(role_id)


def _get_users_with_role(role_id: UUID) -> List[UUID]:
    """Get all users with a specific role from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return []
        
        user_ids = db.execute(select(user_roles.c.user_id).where(user_roles.c.role == role.name)).scalars().all()
        return list(user_ids)
        
    except Exception as e:
        print(f"ERROR get_users_with_role (DB): {e}")
        return []
    finally:
        db.close()
