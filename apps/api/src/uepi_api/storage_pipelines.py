"""Pipeline storage - database only"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from uepi_api.models.pipeline import Pipeline


def list_pipelines(tenant_id: UUID) -> List[Dict[str, Any]]:
    """List all pipelines for a tenant - from database"""
    return _list_pipelines(tenant_id)


def _list_pipelines(tenant_id: UUID) -> List[Dict[str, Any]]:
    """List pipelines from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        pipelines = db.query(Pipeline).filter(
            Pipeline.tenant_id == tenant_id
        ).all()
        
        # Convert to dict format (same as file-based)
        result = []
        for pipeline in pipelines:
            steps = pipeline.steps_json if pipeline.steps_json else {}
            result.append({
                "tenant_id": str(pipeline.tenant_id),
                "pipeline_id": pipeline.pipeline_id,
                "pipeline_name": pipeline.name,
                "pipeline_description": pipeline.description,
                "version": pipeline.version,
                "source_type": steps.get("source_type", ""),
                "source_format": steps.get("source_format"),
                "source_schema": steps.get("source_schema"),
                "target_dataset_type": steps.get("target_dataset_type", ""),
                "target_model": steps.get("target_model", ""),
                "field_mappings": steps.get("field_mappings", []),
                "mode": steps.get("mode", "APPEND"),
                "deduplication": steps.get("deduplication", {"strategy": "HASH"}),
                "control_fields": steps.get("control_fields", {}),
                "validation_rules": steps.get("validation_rules"),
                "required_fields": steps.get("required_fields", []),
                "batch_size": steps.get("batch_size", 10000),
                "error_threshold": steps.get("error_threshold", 0.05),
                "continue_on_error": steps.get("continue_on_error", True),
                "active": pipeline.enabled,
                "created_at": pipeline.created_at.isoformat() if pipeline.created_at else None,
                "updated_at": pipeline.updated_at.isoformat() if pipeline.updated_at else None,
                "created_by": None,
                "tags": steps.get("tags", []),  # Read tags from steps_json
                "notes": steps.get("notes"),  # Read notes from steps_json
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_pipelines (DB): {e}")
        return []
    finally:
        db.close()


def get_pipeline(pipeline_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get a pipeline by ID - from database"""
    return _get_pipeline(pipeline_id, tenant_id)


def _get_pipeline(pipeline_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get pipeline from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        pipeline = db.query(Pipeline).filter(
            Pipeline.tenant_id == tenant_id,
            Pipeline.pipeline_id == str(pipeline_id)
        ).first()
        
        if not pipeline:
            return None
        
        # Return as dict (same format as file-based)
        steps = pipeline.steps_json if pipeline.steps_json else {}
        return {
            "tenant_id": str(pipeline.tenant_id),
            "pipeline_id": pipeline.pipeline_id,
            "pipeline_name": pipeline.name,
            "pipeline_description": pipeline.description,
            "version": pipeline.version,
            "source_type": steps.get("source_type", ""),
            "source_format": steps.get("source_format"),
            "source_schema": steps.get("source_schema"),
            "target_dataset_type": steps.get("target_dataset_type", ""),
            "target_model": steps.get("target_model", ""),
            "field_mappings": steps.get("field_mappings", []),
            "mode": steps.get("mode", "APPEND"),
            "deduplication": steps.get("deduplication", {"strategy": "HASH"}),
            "control_fields": steps.get("control_fields", {}),
            "validation_rules": steps.get("validation_rules"),
            "required_fields": steps.get("required_fields", []),
            "batch_size": steps.get("batch_size", 10000),
            "error_threshold": steps.get("error_threshold", 0.05),
            "continue_on_error": steps.get("continue_on_error", True),
            "active": pipeline.enabled,
            "created_at": pipeline.created_at.isoformat() if pipeline.created_at else None,
            "updated_at": pipeline.updated_at.isoformat() if pipeline.updated_at else None,
            "created_by": None,
            "tags": steps.get("tags", []),  # Read tags from steps_json
            "notes": steps.get("notes"),  # Read notes from steps_json
        }
        
    except Exception as e:
        print(f"ERROR get_pipeline (DB): {e}")
        return None
    finally:
        db.close()


def create_pipeline(tenant_id: UUID, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new pipeline - stored in database"""
    return _create_pipeline(tenant_id, pipeline_data)


def _create_pipeline(tenant_id: UUID, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create pipeline in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Generate pipeline_id if not provided
        pipeline_id = str(pipeline_data.get("pipeline_id") or uuid4())
        
        # Check if pipeline already exists
        existing = db.query(Pipeline).filter(
            Pipeline.tenant_id == tenant_id,
            Pipeline.pipeline_id == pipeline_id
        ).first()
        
        if existing:
            # Pipeline already exists, return it instead of creating
            steps = existing.steps_json if existing.steps_json else {}
            return {
                "tenant_id": str(existing.tenant_id),
                "pipeline_id": existing.pipeline_id,
                "pipeline_name": existing.name,
                "pipeline_description": existing.description,
                "version": existing.version,
                "source_type": steps.get("source_type", ""),
                "source_format": steps.get("source_format"),
                "source_schema": steps.get("source_schema"),
                "target_dataset_type": steps.get("target_dataset_type", ""),
                "target_model": steps.get("target_model", ""),
                "field_mappings": steps.get("field_mappings", []),
                "mode": steps.get("mode", "APPEND"),
                "deduplication": steps.get("deduplication", {"strategy": "HASH"}),
                "control_fields": steps.get("control_fields", {}),
                "validation_rules": steps.get("validation_rules"),
                "required_fields": steps.get("required_fields", []),
                "batch_size": steps.get("batch_size", 10000),
                "error_threshold": steps.get("error_threshold", 0.05),
                "continue_on_error": steps.get("continue_on_error", True),
                "active": existing.enabled,
                "created_at": existing.created_at.isoformat() if existing.created_at else None,
                "updated_at": existing.updated_at.isoformat() if existing.updated_at else None,
                "created_by": None,
                "tags": steps.get("tags", []),  # Read tags from steps_json
                "notes": steps.get("notes"),  # Read notes from steps_json
            }
        
        # Create pipeline in database
        pipeline = Pipeline(
            tenant_id=tenant_id,
            pipeline_id=pipeline_id,
            name=pipeline_data.get("pipeline_name", pipeline_data.get("name", "")),
            description=pipeline_data.get("pipeline_description", pipeline_data.get("description")),
            steps_json={
                "source_type": pipeline_data.get("source_type", ""),
                "source_format": pipeline_data.get("source_format"),
                "source_schema": pipeline_data.get("source_schema"),
                "target_dataset_type": pipeline_data.get("target_dataset_type", ""),
                "target_model": pipeline_data.get("target_model", ""),
                "field_mappings": pipeline_data.get("field_mappings", []),
                "mode": pipeline_data.get("mode", "APPEND"),
                "deduplication": pipeline_data.get("deduplication", {"strategy": "HASH"}),
                "control_fields": pipeline_data.get("control_fields", {
                    "created_at": "CURRENT_TIMESTAMP",
                    "updated_at": "CURRENT_TIMESTAMP",
                    "active_flag": True,
                }),
                "validation_rules": pipeline_data.get("validation_rules"),
                "required_fields": pipeline_data.get("required_fields", []),
                "batch_size": pipeline_data.get("batch_size", 10000),
                "error_threshold": pipeline_data.get("error_threshold", 0.05),
                "continue_on_error": pipeline_data.get("continue_on_error", True),
                "tags": pipeline_data.get("tags", []),  # Store tags in steps_json
                "notes": pipeline_data.get("notes"),  # Store notes in steps_json
            },
            schedule_json=pipeline_data.get("schedule"),
            status=pipeline_data.get("status", "ACTIVE"),
            enabled=pipeline_data.get("active", pipeline_data.get("enabled", True)),
            pipeline_type=pipeline_data.get("pipeline_type"),
            version=pipeline_data.get("version", "1.0"),
        )
        
        db.add(pipeline)
        db.commit()
        db.refresh(pipeline)
        
        # Return as dict (same format as file-based)
        steps = pipeline.steps_json if pipeline.steps_json else {}
        return {
            "tenant_id": str(pipeline.tenant_id),
            "pipeline_id": pipeline.pipeline_id,
            "pipeline_name": pipeline.name,
            "pipeline_description": pipeline.description,
            "version": pipeline.version,
            "source_type": steps.get("source_type", ""),
            "source_format": steps.get("source_format"),
            "source_schema": steps.get("source_schema"),
            "target_dataset_type": steps.get("target_dataset_type", ""),
            "target_model": steps.get("target_model", ""),
            "field_mappings": steps.get("field_mappings", []),
            "mode": steps.get("mode", "APPEND"),
            "deduplication": steps.get("deduplication", {"strategy": "HASH"}),
            "control_fields": steps.get("control_fields", {}),
            "validation_rules": steps.get("validation_rules"),
            "required_fields": steps.get("required_fields", []),
            "batch_size": steps.get("batch_size", 10000),
            "error_threshold": steps.get("error_threshold", 0.05),
            "continue_on_error": steps.get("continue_on_error", True),
            "active": pipeline.enabled,
            "created_at": pipeline.created_at.isoformat() if pipeline.created_at else None,
            "updated_at": pipeline.updated_at.isoformat() if pipeline.updated_at else None,
            "created_by": None,
            "tags": steps.get("tags", []),  # Read tags from steps_json
            "notes": steps.get("notes"),  # Read notes from steps_json
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create pipeline: {e}")
    finally:
        db.close()


def update_pipeline(pipeline_id: UUID, tenant_id: UUID, pipeline_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a pipeline - stored in database"""
    return _update_pipeline(pipeline_id, tenant_id, pipeline_data)


def _update_pipeline(pipeline_id: UUID, tenant_id: UUID, pipeline_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update pipeline in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        pipeline = db.query(Pipeline).filter(
            Pipeline.tenant_id == tenant_id,
            Pipeline.pipeline_id == str(pipeline_id)
        ).first()
        
        if not pipeline:
            return None
        
        # Update fields
        if "pipeline_name" in pipeline_data or "name" in pipeline_data:
            pipeline.name = pipeline_data.get("pipeline_name") or pipeline_data.get("name", pipeline.name)
        if "pipeline_description" in pipeline_data or "description" in pipeline_data:
            pipeline.description = pipeline_data.get("pipeline_description") or pipeline_data.get("description", pipeline.description)
        if "version" in pipeline_data:
            pipeline.version = pipeline_data["version"]
        if "status" in pipeline_data:
            pipeline.status = pipeline_data["status"]
        if "active" in pipeline_data or "enabled" in pipeline_data:
            pipeline.enabled = pipeline_data.get("active", pipeline_data.get("enabled", pipeline.enabled))
        
        # Update steps_json if any step-related fields are provided
        if any(k in pipeline_data for k in ["source_type", "field_mappings", "mode", "validation_rules", "tags", "notes"]):
            from sqlalchemy.orm.attributes import flag_modified
            steps = dict(pipeline.steps_json) if pipeline.steps_json else {}
            steps.update({
                k: pipeline_data[k] for k in ["source_type", "source_format", "source_schema", 
                                                "target_dataset_type", "target_model", "field_mappings",
                                                "mode", "deduplication", "control_fields", "validation_rules",
                                                "required_fields", "batch_size", "error_threshold", 
                                                "continue_on_error", "tags", "notes"] if k in pipeline_data
            })
            pipeline.steps_json = steps
            flag_modified(pipeline, "steps_json")
        
        # updated_at is automatically updated by SQLAlchemy due to onupdate=datetime.utcnow
        
        db.commit()
        db.refresh(pipeline)
        
        # Return as dict (same format as file-based)
        steps = pipeline.steps_json if pipeline.steps_json else {}
        return {
            "tenant_id": str(pipeline.tenant_id),
            "pipeline_id": pipeline.pipeline_id,
            "pipeline_name": pipeline.name,
            "pipeline_description": pipeline.description,
            "version": pipeline.version,
            "source_type": steps.get("source_type", ""),
            "source_format": steps.get("source_format"),
            "source_schema": steps.get("source_schema"),
            "target_dataset_type": steps.get("target_dataset_type", ""),
            "target_model": steps.get("target_model", ""),
            "field_mappings": steps.get("field_mappings", []),
            "mode": steps.get("mode", "APPEND"),
            "deduplication": steps.get("deduplication", {"strategy": "HASH"}),
            "control_fields": steps.get("control_fields", {}),
            "validation_rules": steps.get("validation_rules"),
            "required_fields": steps.get("required_fields", []),
            "batch_size": steps.get("batch_size", 10000),
            "error_threshold": steps.get("error_threshold", 0.05),
            "continue_on_error": steps.get("continue_on_error", True),
            "active": pipeline.enabled,
            "created_at": pipeline.created_at.isoformat() if pipeline.created_at else None,
            "updated_at": pipeline.updated_at.isoformat() if pipeline.updated_at else None,
            "created_by": None,
            "tags": steps.get("tags", []),  # Read tags from steps_json
            "notes": steps.get("notes"),  # Read notes from steps_json
        }
        
    except Exception as e:
        db.rollback()
        print(f"ERROR update_pipeline (DB): {e}")
        return None
    finally:
        db.close()


def delete_pipeline(pipeline_id: UUID, tenant_id: UUID) -> bool:
    """Delete a pipeline from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        pipeline = db.query(Pipeline).filter(
            Pipeline.tenant_id == tenant_id,
            Pipeline.pipeline_id == str(pipeline_id)
        ).first()
        
        if not pipeline:
            return False
        
        db.delete(pipeline)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        print(f"ERROR delete_pipeline (DB): {e}")
        return False
    finally:
        db.close()


def activate_pipeline(pipeline_id: UUID, tenant_id: UUID, active: bool) -> Optional[Dict[str, Any]]:
    """Activate or deactivate a pipeline"""
    return update_pipeline(pipeline_id, tenant_id, {"active": active})
