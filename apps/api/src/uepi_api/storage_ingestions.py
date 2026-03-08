"""File-based ingestion storage (for local development) - database only"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.ingestion import Ingestion as IngestionDB
from sqlalchemy import desc


def list_ingestions(tenant_id: UUID) -> List[Dict[str, Any]]:
    """List all ingestions for a tenant - from database"""
    return _list_ingestions(tenant_id)


def _list_ingestions(tenant_id: UUID) -> List[Dict[str, Any]]:
    """List ingestions from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        ingestions_db = db.query(IngestionDB).filter(
            IngestionDB.tenant_id == tenant_id
        ).order_by(desc(IngestionDB.created_at)).all()
        
        # Convert to dict format (same as file-based)
        result = []
        for ingestion_db in ingestions_db:
            metadata = ingestion_db.metadata_json if ingestion_db.metadata_json else {}
            result.append({
                "id": str(ingestion_db.id),
                "tenant_id": str(ingestion_db.tenant_id),
                "ingestion_type": ingestion_db.ingestion_type,
                "status": ingestion_db.status,
                "manifest_uri": ingestion_db.manifest_uri,
                "started_at": ingestion_db.started_at.isoformat() if ingestion_db.started_at else None,
                "completed_at": ingestion_db.completed_at.isoformat() if ingestion_db.completed_at else None,
                "metadata": metadata,
                "created_at": ingestion_db.created_at.isoformat() if ingestion_db.created_at else None,
                "updated_at": ingestion_db.updated_at.isoformat() if ingestion_db.updated_at else None,
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_ingestions (DB): {e}")
        return []
    finally:
        db.close()


def get_ingestion(ingestion_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get an ingestion by ID - from database"""
    return _get_ingestion(ingestion_id, tenant_id)


def _get_ingestion(ingestion_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get ingestion from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        ingestion_db = db.query(IngestionDB).filter(
            IngestionDB.id == ingestion_id,
            IngestionDB.tenant_id == tenant_id
        ).first()
        
        if not ingestion_db:
            return None
        
        # Return as dict (same format as file-based)
        metadata = ingestion_db.metadata_json if ingestion_db.metadata_json else {}
        return {
            "id": str(ingestion_db.id),
            "tenant_id": str(ingestion_db.tenant_id),
            "ingestion_type": ingestion_db.ingestion_type,
            "status": ingestion_db.status,
            "manifest_uri": ingestion_db.manifest_uri,
            "started_at": ingestion_db.started_at.isoformat() if ingestion_db.started_at else None,
            "completed_at": ingestion_db.completed_at.isoformat() if ingestion_db.completed_at else None,
            "metadata": metadata,
            "created_at": ingestion_db.created_at.isoformat() if ingestion_db.created_at else None,
            "updated_at": ingestion_db.updated_at.isoformat() if ingestion_db.updated_at else None,
        }
        
    except Exception as e:
        print(f"ERROR get_ingestion (DB): {e}")
        return None
    finally:
        db.close()


def create_ingestion(tenant_id: UUID, ingestion_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new ingestion - stored in database"""
    return _create_ingestion(tenant_id, ingestion_data)


def _create_ingestion(tenant_id: UUID, ingestion_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create ingestion in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        ingestion_id = uuid4()
        
        # Parse dates
        started_at = None
        if ingestion_data.get("started_at"):
            started_at = datetime.fromisoformat(ingestion_data["started_at"].replace("Z", "+00:00")) if isinstance(ingestion_data["started_at"], str) else ingestion_data["started_at"]
        
        completed_at = None
        if ingestion_data.get("completed_at"):
            completed_at = datetime.fromisoformat(ingestion_data["completed_at"].replace("Z", "+00:00")) if isinstance(ingestion_data["completed_at"], str) else ingestion_data["completed_at"]
        
        # Create ingestion in database
        ingestion_db = IngestionDB(
            tenant_id=tenant_id,
            id=ingestion_id,
            ingestion_type=ingestion_data.get("ingestion_type", "CLAIMS"),
            status=ingestion_data.get("status", "PENDING"),
            manifest_uri=ingestion_data.get("manifest_uri", ""),
            started_at=started_at,
            completed_at=completed_at,
            metadata_json=ingestion_data.get("metadata", {}),
        )
        
        db.add(ingestion_db)
        db.commit()
        db.refresh(ingestion_db)
        
        # Return as dict (same format as file-based)
        metadata = ingestion_db.metadata_json if ingestion_db.metadata_json else {}
        return {
            "id": str(ingestion_db.id),
            "tenant_id": str(ingestion_db.tenant_id),
            "ingestion_type": ingestion_db.ingestion_type,
            "status": ingestion_db.status,
            "manifest_uri": ingestion_db.manifest_uri,
            "started_at": ingestion_db.started_at.isoformat() if ingestion_db.started_at else None,
            "completed_at": ingestion_db.completed_at.isoformat() if ingestion_db.completed_at else None,
            "metadata": metadata,
            "created_at": ingestion_db.created_at.isoformat() if ingestion_db.created_at else None,
            "updated_at": ingestion_db.updated_at.isoformat() if ingestion_db.updated_at else None,
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create ingestion: {e}")
    finally:
        db.close()


def update_ingestion(ingestion_id: UUID, tenant_id: UUID, ingestion_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an ingestion - stored in database"""
    return _update_ingestion(ingestion_id, tenant_id, ingestion_data)


def _update_ingestion(ingestion_id: UUID, tenant_id: UUID, ingestion_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update ingestion in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        ingestion_db = db.query(IngestionDB).filter(
            IngestionDB.id == ingestion_id,
            IngestionDB.tenant_id == tenant_id
        ).first()
        
        if not ingestion_db:
            return None
        
        existing_status = ingestion_db.status
        
        # Update fields
        if "ingestion_type" in ingestion_data:
            ingestion_db.ingestion_type = ingestion_data["ingestion_type"]
        if "status" in ingestion_data:
            ingestion_db.status = ingestion_data["status"]
        if "manifest_uri" in ingestion_data:
            ingestion_db.manifest_uri = ingestion_data["manifest_uri"]
        if "started_at" in ingestion_data:
            ingestion_db.started_at = datetime.fromisoformat(ingestion_data["started_at"].replace("Z", "+00:00")) if isinstance(ingestion_data["started_at"], str) else ingestion_data["started_at"]
        if "completed_at" in ingestion_data:
            ingestion_db.completed_at = datetime.fromisoformat(ingestion_data["completed_at"].replace("Z", "+00:00")) if isinstance(ingestion_data["completed_at"], str) else ingestion_data["completed_at"]
        if "metadata" in ingestion_data:
            ingestion_db.metadata_json = ingestion_data["metadata"]
        
        # updated_at is automatically updated by SQLAlchemy
        
        db.commit()
        db.refresh(ingestion_db)
        
        # Integration: Create data period when ingestion status changes to COMPLETED
        new_status = ingestion_data.get("status", existing_status)
        if existing_status != "COMPLETED" and new_status == "COMPLETED":
            try:
                from uepi_api.integration_helpers import create_data_period_from_ingestion
                metadata = ingestion_db.metadata_json if ingestion_db.metadata_json else {}
                period = create_data_period_from_ingestion(
                    tenant_id=tenant_id,
                    ingestion_id=str(ingestion_id),
                    ingestion_metadata=metadata,
                )
                if period:
                    print(f"Created data period {period.get('period_id')} for ingestion {ingestion_id}")
            except Exception as e:
                # Don't fail ingestion update if data period creation fails
                print(f"Warning: Failed to create data period for ingestion {ingestion_id}: {e}")
        
        # Return as dict (same format as file-based)
        metadata = ingestion_db.metadata_json if ingestion_db.metadata_json else {}
        return {
            "id": str(ingestion_db.id),
            "tenant_id": str(ingestion_db.tenant_id),
            "ingestion_type": ingestion_db.ingestion_type,
            "status": ingestion_db.status,
            "manifest_uri": ingestion_db.manifest_uri,
            "started_at": ingestion_db.started_at.isoformat() if ingestion_db.started_at else None,
            "completed_at": ingestion_db.completed_at.isoformat() if ingestion_db.completed_at else None,
            "metadata": metadata,
            "created_at": ingestion_db.created_at.isoformat() if ingestion_db.created_at else None,
            "updated_at": ingestion_db.updated_at.isoformat() if ingestion_db.updated_at else None,
        }
        
    except Exception as e:
        db.rollback()
        print(f"ERROR update_ingestion (DB): {e}")
        return None
    finally:
        db.close()


def delete_ingestion(ingestion_id: UUID, tenant_id: UUID) -> bool:
    """Delete an ingestion - from database"""
    return _delete_ingestion(ingestion_id, tenant_id)


def _delete_ingestion(ingestion_id: UUID, tenant_id: UUID) -> bool:
    """Delete ingestion from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        ingestion_db = db.query(IngestionDB).filter(
            IngestionDB.id == ingestion_id,
            IngestionDB.tenant_id == tenant_id
        ).first()
        
        if not ingestion_db:
            return False
        
        db.delete(ingestion_db)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        print(f"ERROR delete_ingestion (DB): {e}")
        return False
    finally:
        db.close()
