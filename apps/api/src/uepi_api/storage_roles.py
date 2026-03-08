"""File-based role storage - database only"""
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.tenant import Role as RoleDB
from uepi_common.models_enhanced import Role, Permission, PersonaRole, ResourceType, ActionType, ResourceScope


def create_role(role: Role) -> Role:
    """Create a new role - stored in database"""
    return _create_role(role)


def _create_role(role: Role) -> Role:
    """Create role in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        existing = db.query(RoleDB).filter(RoleDB.name == role.name).first()
        if existing:
            raise ValueError(f"Role with name '{role.name}' already exists")
        
        role_db = RoleDB(
            id=role.id,
            name=role.name,
            description=role.description if hasattr(role, 'description') else None,
        )
        
        db.add(role_db)
        db.commit()
        db.refresh(role_db)
        
        return Role(
            id=role_db.id,
            name=role_db.name,
            description=role_db.description or "",
            permissions=role.permissions if hasattr(role, 'permissions') else [],
            persona=role.persona if hasattr(role, 'persona') else None,
            created_at=role_db.created_at,
            updated_at=role_db.created_at,
        )
        
    except Exception as e:
        db.rollback()
        print(f"ERROR create_role (DB): {e}")
        raise ValueError(f"Failed to create role: {e}")
    finally:
        db.close()


def get_role(role_id: UUID) -> Optional[Role]:
    """Get role by ID - from database"""
    return _get_role(role_id)


def _get_role(role_id: UUID) -> Optional[Role]:
    """Get role from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        role_db = db.query(RoleDB).filter(RoleDB.id == role_id).first()
        
        if not role_db:
            return None
        
        return Role(
            id=role_db.id,
            name=role_db.name,
            description=role_db.description or "",
            permissions=[],
            persona=None,
            created_at=role_db.created_at,
            updated_at=role_db.created_at,
        )
        
    except Exception as e:
        print(f"ERROR get_role (DB): {e}")
        return None
    finally:
        db.close()


def list_roles() -> List[Role]:
    """List all roles - from database"""
    return _list_roles()


def _list_roles() -> List[Role]:
    """List all roles from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        roles_db = db.query(RoleDB).all()
        
        result = []
        for role_db in roles_db:
            result.append(Role(
                id=role_db.id,
                name=role_db.name,
                description=role_db.description or "",
                permissions=[],
                persona=None,
                created_at=role_db.created_at,
                updated_at=role_db.created_at,
            ))
        
        return result
        
    except Exception as e:
        print(f"ERROR list_roles (DB): {e}")
        return []
    finally:
        db.close()


def update_role(role_id: UUID, role_data: Dict[str, Any]) -> Optional[Role]:
    """Update role - in database"""
    return _update_role(role_id, role_data)


def _update_role(role_id: UUID, role_data: Dict[str, Any]) -> Optional[Role]:
    """Update role in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        role_db = db.query(RoleDB).filter(RoleDB.id == role_id).first()
        
        if not role_db:
            return None
        
        if 'name' in role_data:
            role_db.name = role_data['name']
        if 'description' in role_data:
            role_db.description = role_data['description']
        
        db.commit()
        db.refresh(role_db)
        
        permissions = role_data.get('permissions', [])
        if permissions:
            permissions = [
                Permission(
                    resource=ResourceType(p_data['resource']),
                    actions=[ActionType(a) for a in p_data['actions']],
                    scope=ResourceScope(**p_data['scope']) if p_data.get('scope') else None
                )
                for p_data in permissions
            ]
        
        return Role(
            id=role_db.id,
            name=role_db.name,
            description=role_db.description or "",
            permissions=permissions,
            persona=PersonaRole(role_data['persona']) if role_data.get('persona') else None,
            created_at=role_db.created_at,
            updated_at=role_db.created_at,
        )
        
    except Exception as e:
        db.rollback()
        print(f"ERROR update_role (DB): {e}")
        return None
    finally:
        db.close()


def delete_role(role_id: UUID) -> bool:
    """Delete role - from database"""
    return _delete_role(role_id)


def _delete_role(role_id: UUID) -> bool:
    """Delete role from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        role_db = db.query(RoleDB).filter(RoleDB.id == role_id).first()
        
        if not role_db:
            return False
        
        db.delete(role_db)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        print(f"ERROR delete_role (DB): {e}")
        return False
    finally:
        db.close()
