"""File-based export storage - database only"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.export import Export as ExportDB
from sqlalchemy import desc


def list_exports(tenant_id: UUID) -> List[Dict[str, Any]]:
    """List all exports for a tenant - from database"""
    return _list_exports(tenant_id)


def _list_exports(tenant_id: UUID) -> List[Dict[str, Any]]:
    """List exports from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        exports_db = db.query(ExportDB).filter(
            ExportDB.tenant_id == tenant_id
        ).order_by(desc(ExportDB.created_at)).all()
        
        # Convert to dict format (same as file-based)
        result = []
        for export_db in exports_db:
            result.append({
                "id": str(export_db.id),
                "tenant_id": str(export_db.tenant_id),
                "analysis_id": str(export_db.analysis_id) if export_db.analysis_id else None,
                "export_type": export_db.export_type,
                "status": export_db.status,
                "file_uri": export_db.file_uri,
                "file_size_bytes": export_db.file_size_bytes,
                "download_count": export_db.download_count,
                "version_number": export_db.version_number,
                "parent_export_id": str(export_db.parent_export_id) if export_db.parent_export_id else None,
                "change_description": export_db.change_description,
                "created_by": str(export_db.created_by) if export_db.created_by else None,
                "created_at": export_db.created_at.isoformat() if export_db.created_at else None,
                "completed_at": export_db.completed_at.isoformat() if export_db.completed_at else None,
                "error_message": export_db.error_message,
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_exports (DB): {e}")
        return []
    finally:
        db.close()


def get_export(export_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get an export by ID - from database"""
    return _get_export(export_id, tenant_id)


def _get_export(export_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get export from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        export_db = db.query(ExportDB).filter(
            ExportDB.id == export_id,
            ExportDB.tenant_id == tenant_id
        ).first()
        
        if not export_db:
            return None
        
        # Return as dict (same format as file-based)
        return {
            "id": str(export_db.id),
            "tenant_id": str(export_db.tenant_id),
            "analysis_id": str(export_db.analysis_id) if export_db.analysis_id else None,
            "export_type": export_db.export_type,
            "status": export_db.status,
            "file_uri": export_db.file_uri,
            "file_size_bytes": export_db.file_size_bytes,
            "download_count": export_db.download_count,
            "version_number": export_db.version_number,
            "parent_export_id": str(export_db.parent_export_id) if export_db.parent_export_id else None,
            "change_description": export_db.change_description,
            "created_by": str(export_db.created_by) if export_db.created_by else None,
            "created_at": export_db.created_at.isoformat() if export_db.created_at else None,
            "completed_at": export_db.completed_at.isoformat() if export_db.completed_at else None,
            "error_message": export_db.error_message,
        }
        
    except Exception as e:
        print(f"ERROR get_export (DB): {e}")
        return None
    finally:
        db.close()


def create_export(
    tenant_id: UUID,
    export_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a new export - stored in database"""
    return _create_export(tenant_id, export_data)


def _create_export(
    tenant_id: UUID,
    export_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create export in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        export_db = ExportDB(
            tenant_id=tenant_id,
            analysis_id=UUID(export_data["analysis_id"]) if export_data.get("analysis_id") else None,
            export_type=export_data.get("export_type", "PDF"),
            status="PENDING",
            version_number=export_data.get("version_number", 1),
            parent_export_id=UUID(export_data["parent_export_id"]) if export_data.get("parent_export_id") else None,
            change_description=export_data.get("change_description"),
            created_by=UUID(export_data["created_by"]) if export_data.get("created_by") else None,
        )
        
        db.add(export_db)
        db.commit()
        db.refresh(export_db)
        
        # Return as dict (same format as file-based)
        return {
            "id": str(export_db.id),
            "tenant_id": str(export_db.tenant_id),
            "analysis_id": str(export_db.analysis_id) if export_db.analysis_id else None,
            "export_type": export_db.export_type,
            "status": export_db.status,
            "file_uri": export_db.file_uri,
            "file_size_bytes": export_db.file_size_bytes,
            "download_count": export_db.download_count,
            "version_number": export_db.version_number,
            "parent_export_id": str(export_db.parent_export_id) if export_db.parent_export_id else None,
            "change_description": export_db.change_description,
            "created_by": str(export_db.created_by) if export_db.created_by else None,
            "created_at": export_db.created_at.isoformat() if export_db.created_at else None,
            "completed_at": export_db.completed_at.isoformat() if export_db.completed_at else None,
            "error_message": export_db.error_message,
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create export: {e}")
    finally:
        db.close()


def update_export(
    export_id: UUID,
    tenant_id: UUID,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update an export - stored in database"""
    return _update_export(export_id, tenant_id, updates)


def _update_export(
    export_id: UUID,
    tenant_id: UUID,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update export in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        export_db = db.query(ExportDB).filter(
            ExportDB.id == export_id,
            ExportDB.tenant_id == tenant_id
        ).first()
        
        if not export_db:
            return None
        
        # Update fields
        if "analysis_id" in updates:
            export_db.analysis_id = UUID(updates["analysis_id"]) if isinstance(updates["analysis_id"], str) else updates["analysis_id"]
        if "export_type" in updates:
            export_db.export_type = updates["export_type"]
        if "status" in updates:
            export_db.status = updates["status"]
        if "file_uri" in updates:
            export_db.file_uri = updates["file_uri"]
        if "file_size_bytes" in updates:
            export_db.file_size_bytes = updates["file_size_bytes"]
        if "download_count" in updates:
            export_db.download_count = updates["download_count"]
        if "version_number" in updates:
            export_db.version_number = updates["version_number"]
        if "parent_export_id" in updates:
            export_db.parent_export_id = UUID(updates["parent_export_id"]) if isinstance(updates["parent_export_id"], str) else updates["parent_export_id"]
        if "change_description" in updates:
            export_db.change_description = updates["change_description"]
        if "completed_at" in updates:
            export_db.completed_at = datetime.fromisoformat(updates["completed_at"].replace("Z", "+00:00")) if isinstance(updates["completed_at"], str) else updates["completed_at"]
        elif "status" in updates and updates["status"] == "COMPLETED" and not export_db.completed_at:
            export_db.completed_at = datetime.utcnow()
        if "error_message" in updates:
            export_db.error_message = updates["error_message"]
        
        db.commit()
        db.refresh(export_db)
        
        # Return as dict (same format as file-based)
        return {
            "id": str(export_db.id),
            "tenant_id": str(export_db.tenant_id),
            "analysis_id": str(export_db.analysis_id) if export_db.analysis_id else None,
            "export_type": export_db.export_type,
            "status": export_db.status,
            "file_uri": export_db.file_uri,
            "file_size_bytes": export_db.file_size_bytes,
            "download_count": export_db.download_count,
            "version_number": export_db.version_number,
            "parent_export_id": str(export_db.parent_export_id) if export_db.parent_export_id else None,
            "change_description": export_db.change_description,
            "created_by": str(export_db.created_by) if export_db.created_by else None,
            "created_at": export_db.created_at.isoformat() if export_db.created_at else None,
            "completed_at": export_db.completed_at.isoformat() if export_db.completed_at else None,
            "error_message": export_db.error_message,
        }
        
    except Exception as e:
        db.rollback()
        print(f"ERROR update_export (DB): {e}")
        return None
    finally:
        db.close()


def get_export_versions(export_id: UUID, tenant_id: UUID) -> List[Dict[str, Any]]:
    """Get all versions of an export (including parent and children)"""
    all_exports = list_exports(tenant_id)
    
    # Find the export and all related versions
    versions = []
    root_export = None
    
    # Find root export (the one without parent_export_id or matches export_id)
    for exp in all_exports:
        if exp.get("id") == str(export_id):
            root_export = exp
            break
    
    if not root_export:
        return []
    
    # Add root export
    versions.append(root_export)
    
    # Find all child versions (exports with parent_export_id matching this or any child)
    root_id = root_export.get("id")
    version_ids = {root_id}
    changed = True
    
    while changed:
        changed = False
        for exp in all_exports:
            parent_id = exp.get("parent_export_id")
            if parent_id and parent_id in version_ids and exp.get("id") not in version_ids:
                versions.append(exp)
                version_ids.add(exp.get("id"))
                changed = True
    
    # Sort by version_number
    versions.sort(key=lambda x: x.get("version_number", 1))
    return versions
