"""Analysis storage - database only"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.analysis import Analysis, AnalysisResultIndex
from sqlalchemy import desc


def list_analyses(tenant_id: UUID, analysis_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all analyses for a tenant - from database"""
    return _list_analyses(tenant_id, analysis_type)


def _list_analyses(tenant_id: UUID, analysis_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """List analyses from database"""
    from uepi_api.database import SessionLocal
    from sqlalchemy import func, distinct, text
    
    db: Session = SessionLocal()
    try:
        # Test connection first
        try:
            db.execute(text("SELECT 1"))
        except Exception as conn_error:
            print(f"ERROR _list_analyses: Database connection failed: {conn_error}")
            return []
        
        # Check total analyses and tenant distribution
        total_analyses = db.query(Analysis).count()
        print(f"DEBUG _list_analyses: Total analyses in DB: {total_analyses}")
        
        tenant_ids_in_db = db.query(distinct(Analysis.tenant_id)).all()
        tenant_id_strings = [str(t[0]) for t in tenant_ids_in_db]
        print(f"DEBUG _list_analyses: Tenant IDs in DB: {tenant_id_strings}")
        print(f"DEBUG _list_analyses: Looking for tenant_id: {tenant_id} (type: {type(tenant_id)})")
        
        # If no analyses for this tenant but data exists, check if we should return all data
        if total_analyses > 0 and str(tenant_id) not in tenant_id_strings:
            print(f"WARNING: No analyses found for tenant {tenant_id}, but {total_analyses} analyses exist for other tenants")
            print(f"WARNING: Available tenant IDs: {tenant_id_strings}")
            # For demo/local dev, if only one tenant exists, use that tenant's data
            if len(tenant_id_strings) == 1:
                print(f"INFO: Only one tenant in DB, using that tenant's data: {tenant_id_strings[0]}")
                tenant_id = UUID(tenant_id_strings[0])
        
        query = db.query(Analysis).filter(Analysis.tenant_id == tenant_id)
        
        # Filter by analysis_type if provided
        if analysis_type:
            query = query.filter(Analysis.analysis_type == analysis_type)
        
        # Sort by created_at descending
        analyses_db = query.order_by(desc(Analysis.created_at)).all()
        
        print(f"DEBUG _list_analyses: Found {len(analyses_db)} analyses for tenant {tenant_id}")
        
        # Convert to dict format (same as file-based)
        result = []
        for analysis_db in analyses_db:
            result.append({
                "id": str(analysis_db.id),
                "tenant_id": str(analysis_db.tenant_id),
                "policy_id": str(analysis_db.policy_id) if analysis_db.policy_id else None,
                "analysis_type": analysis_db.analysis_type,
                "status": analysis_db.status,
                "created_by": str(analysis_db.created_by) if analysis_db.created_by else None,
                "created_at": analysis_db.created_at.isoformat() if analysis_db.created_at else None,
                "updated_at": analysis_db.updated_at.isoformat() if analysis_db.updated_at else None,
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_analyses (DB): {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        db.close()


def get_analysis(analysis_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get an analysis by ID - from database"""
    return _get_analysis(analysis_id, tenant_id)


def _get_analysis(analysis_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get analysis from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        analysis_db = db.query(Analysis).filter(
            Analysis.id == analysis_id,
            Analysis.tenant_id == tenant_id
        ).first()
        
        if not analysis_db:
            return None
        
        # Return as dict (same format as file-based)
        return {
            "id": str(analysis_db.id),
            "tenant_id": str(analysis_db.tenant_id),
            "policy_id": str(analysis_db.policy_id) if analysis_db.policy_id else None,
            "analysis_type": analysis_db.analysis_type,
            "status": analysis_db.status,
            "created_by": str(analysis_db.created_by) if analysis_db.created_by else None,
            "created_at": analysis_db.created_at.isoformat() if analysis_db.created_at else None,
            "updated_at": analysis_db.updated_at.isoformat() if analysis_db.updated_at else None,
        }
        
    except Exception as e:
        print(f"ERROR get_analysis (DB): {e}")
        return None
    finally:
        db.close()


def create_analysis(tenant_id: UUID, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new analysis - stored in database"""
    return _create_analysis(tenant_id, analysis_data)


def _create_analysis(tenant_id: UUID, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create analysis in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        analysis_id = uuid4()
        
        # Parse policy_id if provided
        policy_id = None
        if analysis_data.get("policy_id"):
            policy_id = UUID(analysis_data["policy_id"]) if isinstance(analysis_data["policy_id"], str) else analysis_data["policy_id"]
        
        # Parse created_by if provided
        created_by = None
        if analysis_data.get("created_by"):
            created_by = UUID(analysis_data["created_by"]) if isinstance(analysis_data["created_by"], str) else analysis_data["created_by"]
        
        # Create analysis in database
        analysis_db = Analysis(
            tenant_id=tenant_id,
            id=analysis_id,
            policy_id=policy_id,
            analysis_type=analysis_data.get("analysis_type", ""),
            status=analysis_data.get("status", "PENDING"),
            created_by=created_by,
        )
        
        db.add(analysis_db)
        db.commit()
        db.refresh(analysis_db)
        
        # Return as dict (same format as file-based)
        return {
            "id": str(analysis_db.id),
            "tenant_id": str(analysis_db.tenant_id),
            "policy_id": str(analysis_db.policy_id) if analysis_db.policy_id else None,
            "analysis_type": analysis_db.analysis_type,
            "status": analysis_db.status,
            "created_by": str(analysis_db.created_by) if analysis_db.created_by else None,
            "created_at": analysis_db.created_at.isoformat() if analysis_db.created_at else None,
            "updated_at": analysis_db.updated_at.isoformat() if analysis_db.updated_at else None,
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create analysis: {e}")
    finally:
        db.close()


def update_analysis(analysis_id: UUID, tenant_id: UUID, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an analysis - stored in database"""
    return _update_analysis(analysis_id, tenant_id, updates)


def _update_analysis(analysis_id: UUID, tenant_id: UUID, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update analysis in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        analysis_db = db.query(Analysis).filter(
            Analysis.id == analysis_id,
            Analysis.tenant_id == tenant_id
        ).first()
        
        if not analysis_db:
            return None
        
        # Update fields
        if "policy_id" in updates:
            analysis_db.policy_id = UUID(updates["policy_id"]) if isinstance(updates["policy_id"], str) else updates["policy_id"]
        if "analysis_type" in updates:
            analysis_db.analysis_type = updates["analysis_type"]
        if "status" in updates:
            analysis_db.status = updates["status"]
        if "created_by" in updates:
            analysis_db.created_by = UUID(updates["created_by"]) if isinstance(updates["created_by"], str) else updates["created_by"]
        
        # updated_at is automatically updated by SQLAlchemy
        
        db.commit()
        db.refresh(analysis_db)
        
        # Return as dict (same format as file-based)
        return {
            "id": str(analysis_db.id),
            "tenant_id": str(analysis_db.tenant_id),
            "policy_id": str(analysis_db.policy_id) if analysis_db.policy_id else None,
            "analysis_type": analysis_db.analysis_type,
            "status": analysis_db.status,
            "created_by": str(analysis_db.created_by) if analysis_db.created_by else None,
            "created_at": analysis_db.created_at.isoformat() if analysis_db.created_at else None,
            "updated_at": analysis_db.updated_at.isoformat() if analysis_db.updated_at else None,
        }
        
    except Exception as e:
        db.rollback()
        print(f"ERROR update_analysis (DB): {e}")
        return None
    finally:
        db.close()


def create_result_index(tenant_id: UUID, analysis_id: UUID, result_type: str, data_uri: str, schema_version: str = "1.0") -> Dict[str, Any]:
    """Create a result index entry - stored in database"""
    return _create_result_index(tenant_id, analysis_id, result_type, data_uri, schema_version)


def _create_result_index(tenant_id: UUID, analysis_id: UUID, result_type: str, data_uri: str, schema_version: str = "1.0") -> Dict[str, Any]:
    """Create result index in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        result_index_id = uuid4()
        
        # Parse analysis_id
        analysis_id_uuid = UUID(analysis_id) if isinstance(analysis_id, str) else analysis_id
        
        # Create result index in database
        result_index_db = AnalysisResultIndex(
            tenant_id=tenant_id,
            id=result_index_id,
            analysis_id=analysis_id_uuid,
            result_type=result_type,
            data_uri=data_uri,
            schema_version=schema_version,
        )
        
        db.add(result_index_db)
        db.commit()
        db.refresh(result_index_db)
        
        # Return as dict (same format as file-based)
        return {
            "id": str(result_index_db.id),
            "tenant_id": str(result_index_db.tenant_id),
            "analysis_id": str(result_index_db.analysis_id),
            "result_type": result_index_db.result_type,
            "data_uri": result_index_db.data_uri,
            "schema_version": result_index_db.schema_version,
            "created_at": result_index_db.created_at.isoformat() if result_index_db.created_at else None,
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create result index: {e}")
    finally:
        db.close()


def get_result_index(analysis_id: UUID, tenant_id: UUID, result_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get result index entry for an analysis - from database"""
    return _get_result_index(analysis_id, tenant_id, result_type)


def _get_result_index(analysis_id: UUID, tenant_id: UUID, result_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get result index from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(AnalysisResultIndex).filter(
            AnalysisResultIndex.analysis_id == analysis_id,
            AnalysisResultIndex.tenant_id == tenant_id
        )
        
        # Filter by result_type if provided
        if result_type:
            query = query.filter(AnalysisResultIndex.result_type == result_type)
        
        result_index_db = query.first()
        
        if not result_index_db:
            return None
        
        # Return as dict (same format as file-based)
        return {
            "id": str(result_index_db.id),
            "tenant_id": str(result_index_db.tenant_id),
            "analysis_id": str(result_index_db.analysis_id),
            "result_type": result_index_db.result_type,
            "data_uri": result_index_db.data_uri,
            "schema_version": result_index_db.schema_version,
            "created_at": result_index_db.created_at.isoformat() if result_index_db.created_at else None,
        }
        
    except Exception as e:
        print(f"ERROR get_result_index (DB): {e}")
        return None
    finally:
        db.close()


def list_result_indices(analysis_id: UUID, tenant_id: UUID, result_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all result index entries for an analysis - from database"""
    return _list_result_indices(analysis_id, tenant_id, result_type)


def _list_result_indices(analysis_id: UUID, tenant_id: UUID, result_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """List result indices from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(AnalysisResultIndex).filter(
            AnalysisResultIndex.analysis_id == analysis_id,
            AnalysisResultIndex.tenant_id == tenant_id
        )
        
        # Filter by result_type if provided
        if result_type:
            query = query.filter(AnalysisResultIndex.result_type == result_type)
        
        result_indices_db = query.all()
        
        # Convert to dict format (same as file-based)
        result = []
        for result_index_db in result_indices_db:
            result.append({
                "id": str(result_index_db.id),
                "tenant_id": str(result_index_db.tenant_id),
                "analysis_id": str(result_index_db.analysis_id),
                "result_type": result_index_db.result_type,
                "data_uri": result_index_db.data_uri,
                "schema_version": result_index_db.schema_version,
                "created_at": result_index_db.created_at.isoformat() if result_index_db.created_at else None,
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_result_indices (DB): {e}")
        return []
    finally:
        db.close()
