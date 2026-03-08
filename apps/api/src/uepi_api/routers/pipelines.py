"""Pipeline routes using file storage (for local development)"""
from typing import Annotated, List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form
from pydantic import BaseModel
import tempfile
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_pipelines import (
    list_pipelines,
    get_pipeline,
    create_pipeline,
    update_pipeline,
    delete_pipeline,
    activate_pipeline,
)
from uepi_api.storage_pipeline_runs import (
    list_pipeline_runs,
    get_pipeline_run,
    create_pipeline_run,
    update_pipeline_run,
)

router = APIRouter()


class PipelineCreate(BaseModel):
    pipeline_name: str
    pipeline_description: Optional[str] = None
    source_type: str
    target_dataset_type: str
    target_model: str
    field_mappings: List[dict]
    mode: str = "APPEND"
    deduplication: dict = {"strategy": "HASH"}
    control_fields: Optional[dict] = None
    validation_rules: Optional[dict] = None
    required_fields: List[str] = []
    batch_size: int = 10000
    error_threshold: float = 0.05
    continue_on_error: bool = True
    tags: List[str] = []
    notes: Optional[str] = None


class PipelineUpdate(BaseModel):
    pipeline_name: Optional[str] = None
    pipeline_description: Optional[str] = None
    field_mappings: Optional[List[dict]] = None
    mode: Optional[str] = None
    deduplication: Optional[dict] = None
    control_fields: Optional[dict] = None
    validation_rules: Optional[dict] = None
    required_fields: Optional[List[str]] = None
    batch_size: Optional[int] = None
    error_threshold: Optional[float] = None
    continue_on_error: Optional[bool] = None
    active: Optional[bool] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


@router.get("/pipelines", response_model=List[dict])
async def get_pipelines(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False, description="Filter to active pipelines only"),
):
    """List all pipelines for the current tenant"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        print(f"[PIPELINES] Listing pipelines for tenant: {current_user.tenant_id}")
        pipelines = list_pipelines(current_user.tenant_id)
        print(f"[PIPELINES] Storage returned {len(pipelines)} pipelines")
        logger.info(f"Found {len(pipelines)} pipelines for tenant {current_user.tenant_id}")
        
        # Debug: Show first few pipeline IDs if any
        if pipelines:
            print(f"[PIPELINES] Sample pipeline IDs: {[p.get('pipeline_id') or p.get('id') for p in pipelines[:3]]}")
        else:
            print(f"[PIPELINES] No pipelines returned from storage!")
        
        if active_only:
            pipelines = [p for p in pipelines if p.get("active", True)]
        
        # Sort by created_at descending
        pipelines_sorted = sorted(
            pipelines,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        return pipelines_sorted[skip:skip + limit]
    except Exception as e:
        logger.error(f"Error listing pipelines: {e}", exc_info=True)
        raise


@router.get("/pipelines/{pipeline_id}", response_model=dict)
async def get_pipeline_by_id(
    pipeline_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get a pipeline by ID"""
    pipeline = get_pipeline(pipeline_id, current_user.tenant_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@router.post("/pipelines", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_pipeline_route(
    pipeline_data: PipelineCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create a new pipeline"""
    pipeline = create_pipeline(
        current_user.tenant_id,
        {
            **pipeline_data.model_dump(),
            "created_by": current_user.email,
        }
    )
    return pipeline


@router.put("/pipelines/{pipeline_id}", response_model=dict)
async def update_pipeline_route(
    pipeline_id: UUID,
    pipeline_data: PipelineUpdate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Update a pipeline"""
    pipeline = update_pipeline(
        pipeline_id,
        current_user.tenant_id,
        pipeline_data.model_dump(exclude_unset=True)
    )
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@router.delete("/pipelines/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline_route(
    pipeline_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Delete a pipeline"""
    success = delete_pipeline(pipeline_id, current_user.tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pipeline not found")


@router.post("/pipelines/{pipeline_id}/activate", response_model=dict)
async def activate_pipeline_route(
    pipeline_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    active: bool = Query(..., description="Activate (true) or deactivate (false)"),
):
    """Activate or deactivate a pipeline"""
    pipeline = activate_pipeline(pipeline_id, current_user.tenant_id, active)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@router.post("/pipelines/{pipeline_id}/run", response_model=dict)
async def run_pipeline_route(
    pipeline_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    source_uri: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """Run a pipeline"""
    pipeline = get_pipeline(pipeline_id, current_user.tenant_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    if not pipeline.get("active", True):
        raise HTTPException(status_code=400, detail="Pipeline is not active")
    
    # Create run record
    run = create_pipeline_run(
        current_user.tenant_id,
        {
            "pipeline_id": str(pipeline_id),
            "status": "PROCESSING",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "source_uri": source_uri or (file.filename if file else None),
        }
    )
    
    try:
        # Execute pipeline
        from uepi_common.ingestion.pipeline_engine import PipelineEngine
        from uepi_common.ingestion.pipeline_metadata import PipelineMetadata, FieldMapping, DeduplicationConfig, PipelineMode, DeduplicationStrategy
        from uepi_common.ingestion.monitoring import MonitoringService
        
        # Convert pipeline dict to PipelineMetadata
        # Convert string UUIDs to UUID objects
        pipeline_data = pipeline.copy()
        if isinstance(pipeline_data.get("pipeline_id"), str):
            pipeline_data["pipeline_id"] = UUID(pipeline_data["pipeline_id"])
        
        # Convert field_mappings to FieldMapping objects
        if "field_mappings" in pipeline_data:
            pipeline_data["field_mappings"] = [
                FieldMapping(**m) if isinstance(m, dict) else m
                for m in pipeline_data["field_mappings"]
            ]
        
        # Convert deduplication config
        if "deduplication" in pipeline_data and isinstance(pipeline_data["deduplication"], dict):
            dedup_dict = pipeline_data["deduplication"]
            if "strategy" in dedup_dict:
                dedup_dict["strategy"] = DeduplicationStrategy(dedup_dict["strategy"])
            pipeline_data["deduplication"] = DeduplicationConfig(**dedup_dict)
        
        # Convert mode
        if "mode" in pipeline_data and isinstance(pipeline_data["mode"], str):
            pipeline_data["mode"] = PipelineMode(pipeline_data["mode"])
        
        pipeline_metadata = PipelineMetadata(**pipeline_data)
        
        # Use database service instead of file-based execution
        from uepi_api.services.pipeline_database_service import PipelineDatabaseService
        from uepi_api.database import get_db
        
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            pipeline_service = PipelineDatabaseService(db, current_user.tenant_id)
            
            # Handle file upload or source URI
            if file:
                original_filename = file.filename or "unknown"
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(original_filename).suffix) as tmp:
                    content = await file.read()
                    tmp.write(content)
                    tmp_path = tmp.name
                
                try:
                    original_filename_stem = Path(original_filename).stem
                    result = pipeline_service.execute_pipeline_to_database(
                        pipeline_metadata=pipeline_metadata,
                        source_file_path=tmp_path,
                        source_file_id=original_filename_stem,
                        ingestion_id=UUID(run["run_id"]),
                        source_system="PIPELINE",
                    )
                
                    # Update run record with quality report and metrics
                    completed_at = datetime.now(timezone.utc)
                    run_update = {
                        "status": "COMPLETED" if result.get("success", False) else "FAILED",
                        "completed_at": completed_at.isoformat(),
                        "records_processed": result.get("records_processed", 0),
                        "records_succeeded": result.get("records_succeeded", 0),
                        "records_failed": result.get("records_failed", 0),
                        "records_duplicated": result.get("records_duplicated", 0),
                        "errors": result.get("errors", []),
                        "output_uri": f"database://{pipeline_metadata.target_dataset_type}",  # Database URI instead of file path
                        "metadata": {
                            "quality_report": result.get("quality_report"),
                            "records_inserted": result.get("records_inserted", 0),
                            "storage": "database",
                        },
                    }
                    update_pipeline_run(
                        UUID(run["run_id"]),
                        current_user.tenant_id,
                        run_update
                    )
                    
                    # Create ingestion record for successful pipeline runs
                    if result.get("success", False):
                        ingestion_data = {
                            "ingestion_type": pipeline_metadata.target_dataset_type,
                            "status": "COMPLETED",
                            "manifest_uri": f"database://{pipeline_metadata.target_dataset_type}",
                            "started_at": run.get("started_at"),
                            "completed_at": completed_at.isoformat(),
                            "metadata": {
                                "pipeline_id": str(pipeline_metadata.pipeline_id),
                                "pipeline_name": pipeline_metadata.pipeline_name,
                                "run_id": str(run["run_id"]),
                                "records_processed": result.get("records_processed", 0),
                                "records_succeeded": result.get("records_succeeded", 0),
                                "records_inserted": result.get("records_inserted", 0),
                                "records_failed": result.get("records_failed", 0),
                                "quality_report": result.get("quality_report"),
                                "source_file": file.filename if file else None,
                                "storage": "database",
                            },
                        }
                        try:
                            create_ingestion(current_user.tenant_id, ingestion_data)
                        except Exception as e:
                            print(f"Warning: Failed to create ingestion record: {e}")
                    
                    return {**run, **result}
                finally:
                    os.unlink(tmp_path)
                    db.close()
            else:
                raise HTTPException(status_code=400, detail="Either file or source_uri must be provided")
        except Exception as e:
            update_pipeline_run(
                UUID(run["run_id"]),
                current_user.tenant_id,
                {
                    "status": "FAILED",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "errors": [{"error": str(e)}],
                    "metadata": {
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                }
            )
            raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")
    except Exception as outer_e:
        # Catch any errors from the outer try block (e.g., during setup)
        if "run" in locals():
            update_pipeline_run(
                UUID(run["run_id"]),
                current_user.tenant_id,
                {
                    "status": "FAILED",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "errors": [{"error": str(outer_e)}],
                    "metadata": {
                        "error": str(outer_e),
                        "error_type": type(outer_e).__name__,
                    },
                }
            )
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(outer_e)}")


@router.get("/pipelines/{pipeline_id}/runs", response_model=List[dict])
async def get_pipeline_runs(
    pipeline_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get runs for a pipeline"""
    runs = list_pipeline_runs(current_user.tenant_id, pipeline_id)
    return runs[skip:skip + limit]


@router.get("/pipelines/{pipeline_id}/runs/{run_id}", response_model=dict)
async def get_pipeline_run_by_id(
    pipeline_id: UUID,
    run_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get a pipeline run by ID"""
    run = get_pipeline_run(run_id, current_user.tenant_id)
    if not run or UUID(run.get("pipeline_id", "")) != pipeline_id:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return run

