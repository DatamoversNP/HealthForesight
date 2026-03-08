"""Pipeline run storage - database only"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.pipeline import PipelineRun
from sqlalchemy import desc


def list_pipeline_runs(tenant_id: UUID, pipeline_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
    """List all pipeline runs for a tenant - from database"""
    return _list_pipeline_runs(tenant_id, pipeline_id)


def _list_pipeline_runs(tenant_id: UUID, pipeline_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
    """List pipeline runs from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(PipelineRun).filter(PipelineRun.tenant_id == tenant_id)
        
        # Filter by pipeline_id if provided
        if pipeline_id:
            query = query.filter(PipelineRun.pipeline_id == str(pipeline_id))
        
        # Sort by started_at descending (newest first)
        runs = query.order_by(desc(PipelineRun.started_at)).all()
        
        # Convert to dict format (same as file-based)
        result = []
        for run in runs:
            result.append({
                "tenant_id": str(run.tenant_id),
                "run_id": run.run_id,
                "pipeline_id": run.pipeline_id,
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "records_processed": run.records_processed,
                "records_succeeded": run.records_succeeded,
                "records_failed": run.records_failed,
                "records_duplicated": run.records_duplicated,
                "errors": run.errors_json if run.errors_json else [],
                "source_uri": run.source_uri,
                "output_uri": run.output_uri,
                "created_at": run.created_at.isoformat() if run.created_at else None,
                "updated_at": run.updated_at.isoformat() if run.updated_at else None,
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_pipeline_runs (DB): {e}")
        return []
    finally:
        db.close()


def get_pipeline_run(run_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get a pipeline run by ID - from database"""
    return _get_pipeline_run(run_id, tenant_id)


def _get_pipeline_run(run_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get pipeline run from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        run = db.query(PipelineRun).filter(
            PipelineRun.tenant_id == tenant_id,
            PipelineRun.run_id == str(run_id)
        ).first()
        
        if not run:
            return None
        
        # Return as dict (same format as file-based)
        return {
            "tenant_id": str(run.tenant_id),
            "run_id": run.run_id,
            "pipeline_id": run.pipeline_id,
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "records_processed": run.records_processed,
            "records_succeeded": run.records_succeeded,
            "records_failed": run.records_failed,
            "records_duplicated": run.records_duplicated,
            "errors": run.errors_json if run.errors_json else [],
            "source_uri": run.source_uri,
            "output_uri": run.output_uri,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "updated_at": run.updated_at.isoformat() if run.updated_at else None,
        }
        
    except Exception as e:
        print(f"ERROR get_pipeline_run (DB): {e}")
        return None
    finally:
        db.close()


def create_pipeline_run(tenant_id: UUID, run_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new pipeline run - stored in database"""
    return _create_pipeline_run(tenant_id, run_data)


def _create_pipeline_run(tenant_id: UUID, run_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create pipeline run in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Generate run_id if not provided
        run_id = str(run_data.get("run_id") or uuid4())
        
        # Parse dates
        started_at = datetime.fromisoformat(run_data["started_at"].replace("Z", "+00:00")) if isinstance(run_data.get("started_at"), str) else run_data.get("started_at")
        completed_at = datetime.fromisoformat(run_data["completed_at"].replace("Z", "+00:00")) if isinstance(run_data.get("completed_at"), str) else run_data.get("completed_at")
        
        # Create pipeline run in database
        run = PipelineRun(
            tenant_id=tenant_id,
            run_id=run_id,
            pipeline_id=str(run_data.get("pipeline_id", "")),
            status=run_data.get("status", "PENDING"),
            started_at=started_at,
            completed_at=completed_at,
            records_processed=run_data.get("records_processed", 0),
            records_succeeded=run_data.get("records_succeeded", 0),
            records_failed=run_data.get("records_failed", 0),
            records_duplicated=run_data.get("records_duplicated", 0),
            errors_json=run_data.get("errors", []),
            source_uri=run_data.get("source_uri"),
            output_uri=run_data.get("output_uri"),
        )
        
        db.add(run)
        db.commit()
        db.refresh(run)
        
        # Return as dict (same format as file-based)
        return {
            "tenant_id": str(run.tenant_id),
            "run_id": run.run_id,
            "pipeline_id": run.pipeline_id,
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "records_processed": run.records_processed,
            "records_succeeded": run.records_succeeded,
            "records_failed": run.records_failed,
            "records_duplicated": run.records_duplicated,
            "errors": run.errors_json if run.errors_json else [],
            "source_uri": run.source_uri,
            "output_uri": run.output_uri,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "updated_at": run.updated_at.isoformat() if run.updated_at else None,
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create pipeline run: {e}")
    finally:
        db.close()


def update_pipeline_run(run_id: UUID, tenant_id: UUID, run_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a pipeline run - stored in database"""
    return _update_pipeline_run(run_id, tenant_id, run_data)


def _update_pipeline_run(run_id: UUID, tenant_id: UUID, run_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update pipeline run in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        run = db.query(PipelineRun).filter(
            PipelineRun.tenant_id == tenant_id,
            PipelineRun.run_id == str(run_id)
        ).first()
        
        if not run:
            return None
        
        # Update fields
        if "status" in run_data:
            run.status = run_data["status"]
        if "started_at" in run_data:
            run.started_at = datetime.fromisoformat(run_data["started_at"].replace("Z", "+00:00")) if isinstance(run_data["started_at"], str) else run_data["started_at"]
        if "completed_at" in run_data:
            run.completed_at = datetime.fromisoformat(run_data["completed_at"].replace("Z", "+00:00")) if isinstance(run_data["completed_at"], str) else run_data["completed_at"]
        if "records_processed" in run_data:
            run.records_processed = run_data["records_processed"]
        if "records_succeeded" in run_data:
            run.records_succeeded = run_data["records_succeeded"]
        if "records_failed" in run_data:
            run.records_failed = run_data["records_failed"]
        if "records_duplicated" in run_data:
            run.records_duplicated = run_data["records_duplicated"]
        if "errors" in run_data:
            run.errors_json = run_data["errors"]
        if "source_uri" in run_data:
            run.source_uri = run_data["source_uri"]
        if "output_uri" in run_data:
            run.output_uri = run_data["output_uri"]
        
        # updated_at is automatically updated by SQLAlchemy
        
        db.commit()
        db.refresh(run)
        
        # Return as dict (same format as file-based)
        return {
            "tenant_id": str(run.tenant_id),
            "run_id": run.run_id,
            "pipeline_id": run.pipeline_id,
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "records_processed": run.records_processed,
            "records_succeeded": run.records_succeeded,
            "records_failed": run.records_failed,
            "records_duplicated": run.records_duplicated,
            "errors": run.errors_json if run.errors_json else [],
            "source_uri": run.source_uri,
            "output_uri": run.output_uri,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "updated_at": run.updated_at.isoformat() if run.updated_at else None,
        }
        
    except Exception as e:
        db.rollback()
        print(f"ERROR update_pipeline_run (DB): {e}")
        return None
    finally:
        db.close()
